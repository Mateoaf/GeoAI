"""Label and covariate audits for NB27; no new observations are manufactured."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from scipy.ndimage import gaussian_filter
from sklearn.base import BaseEstimator, TransformerMixin


ELEMENTS = ("as", "sb", "bi", "hg", "cu", "w", "pb", "zn")
GEOCHEMICAL = [f"geoq_{e}_representante_intervalo_log" for e in ELEMENTS]
DIAGNOSTIC = ["trampa_valle_aluvial", "vector_epitermal_hidrotermal"]
EPITHERMAL_DEPOSITS = {"dep_rodalquilar_cinto", "dep_rodalquilar_santa_josefa"}


def audit_systems(records, positives):
    """Conservative operational labels from reviewed type and documented deposits.

    Primary is deliberately broader than orogenic. Unresolved records are never
    sent to primary by default. Mixed cells keep their multiple documented flags.
    The Rodalquilar assignment is an explicit inventory-based rule, not a new
    geological certification and not a rule based on province or proximity.
    """
    rec = records.copy()
    typology = rec.tipo_au_revisado.fillna("").str.lower()
    epithermal = rec.deposit_id.isin(EPITHERMAL_DEPOSITS)
    rec["primario"] = typology.isin(["roca", "mixto"]) | epithermal
    rec["aluvial"] = typology.isin(["aluvial", "mixto"])
    rec["epitermal"] = epithermal
    rec["primario_otro"] = rec.primario & ~epithermal
    rec["sin_tipo_documentado"] = ~rec[["primario", "aluvial"]].any(axis=1)
    rec["regla_sistema"] = np.where(epithermal, "deposito_documentado_Rodalquilar",
        np.where(typology.eq("mixto"), "tipo_revisado_mixto",
        np.where(typology.isin(["roca", "aluvial"]), "tipo_revisado", "no_resuelto")))
    cells = positives.merge(rec.groupby("cell_id")[["primario", "aluvial", "epitermal", "primario_otro"]].max(),
                            on="cell_id", validate="one_to_one")
    cells["no_resuelto"] = ~cells[["primario", "aluvial"]].any(axis=1)
    cells["mixto"] = cells.primario & cells.aluvial
    cells["epitermal_y_aluvial"] = cells.epitermal & cells.aluvial
    summary = pd.DataFrame([{"grupo": name, "celdas_P": int(cells[name].sum())}
                           for name in ["primario", "primario_otro", "aluvial", "epitermal", "no_resuelto", "mixto"]])
    return rec, cells, summary


def local_residual(values, shape, rows, cols, sigma=25):
    """A fixed, label-free spatial covariate, not statistics fitted to labels."""
    field = np.full(shape, np.nan, dtype=np.float32)
    field[rows, cols] = values
    valid = np.isfinite(field)
    den = gaussian_filter(valid.astype(float), sigma=sigma)
    mean = np.divide(gaussian_filter(np.where(valid, field, 0.), sigma=sigma), den,
                     out=np.full(shape, np.nan), where=den > .01)
    variance = np.divide(gaussian_filter(np.where(valid, (field-mean)**2, 0.), sigma=sigma), den,
                         out=np.full(shape, np.nan), where=den > .01)
    residual = np.divide(field-mean, np.sqrt(np.maximum(variance, 1e-4)))
    return np.clip(residual[rows, cols], -4., 4.).astype("float32")


def satellite_from_cached_tiles(root, spec, rows, cols):
    """Rebuild the existing MODIS covariates without their global median fill.

    No new imagery is downloaded; upgrading sensors or adding a campaign is
    outside NB27. The absence of explicit QA selection remains documented.
    """
    shape = (spec["height"], spec["width"])
    transform = from_origin(spec["origin_x"], spec["origin_y"], 1000, 1000)
    bands, inputs = {}, []
    for band in [1, 2, 3, 6, 7]:
        total, count = np.zeros(shape), np.zeros(shape)
        for tile in ["h17v04", "h17v05", "h18v04", "h18v05"]:
            path = root / "data/raw/satelite_mcd43a4" / f"{tile}_Band{band}.tif"
            inputs.append(path)
            with rasterio.open(path) as src:
                raw = src.read(1).astype("float32")
                raw[(raw >= 32760) | (raw < 0) | (raw == src.nodata)] = np.nan
                raw *= .0001
                target = np.full(shape, np.nan, dtype="float32")
                reproject(raw, target, src_transform=src.transform, src_crs=src.crs,
                          dst_transform=transform, dst_crs=spec["crs"],
                          src_nodata=np.nan, dst_nodata=np.nan, resampling=Resampling.bilinear)
            good = np.isfinite(target)
            total[good] += target[good]
            count[good] += 1
        bands[band] = np.divide(total, count, out=np.full(shape, np.nan), where=count > 0)
    def ratio(a, b, minimum=.01):
        return np.divide(a, b, out=np.full(shape, np.nan), where=(a > minimum) & (b > minimum))
    swir = ratio(bands[6], bands[7])
    iron = ratio(bands[1], bands[3])
    ndvi = np.divide(bands[2]-bands[1], bands[2]+bands[1], out=np.full(shape, np.nan),
                     where=(bands[2]+bands[1]) > .02)
    z_swir = local_residual(swir[rows, cols], shape, rows, cols)
    z_iron = local_residual(iron[rows, cols], shape, rows, cols)
    z_ndvi = local_residual(ndvi[rows, cols], shape, rows, cols)
    return {"ratio_alteracion_filica_swir": swir[rows, cols],
            "ratio_gossan_oxidos_hierro": iron[rows, cols],
            "ndvi_cobertura_vegetal": ndvi[rows, cols],
            "anomalia_hidrotermal_multiespectral_zscore": z_swir+z_iron-.5*z_ndvi}, inputs


def build_features(data, output):
    root, spec = data.root, data.grid_spec
    x = data.features.copy()
    rows = data.grid.set_index("cell_id").loc[x.index, "row"].to_numpy(dtype=int)
    cols = data.grid.set_index("cell_id").loc[x.index, "col"].to_numpy(dtype=int)
    shape = (spec["height"], spec["width"])
    weights = {0: 0, 1: 1, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: .5, 8: 2, 9: 0,
               10: 3, 11: 2.5, 12: 0, 13: 2, 14: 3, 15: 2.5, 16: 1.5, 18: 1.5, 19: 1}
    x["grado_metamorfico"] = sum(x[f"litologia_u{k:03d}_fraccion"] * v for k, v in weights.items())
    x["afinidad_esquistos_verdes"] = np.exp(-(x.grado_metamorfico-2)**2/(2*.5**2))
    herc = x.edades_u000_fraccion+x.edades_u001_fraccion+x.edades_u008_fraccion
    granite = x.litologia_u011_fraccion+x.litologia_u015_fraccion+x.litologia_u014_fraccion
    x["plutonismo_varisco"] = granite*herc
    x["prox_termica_varisca"] = np.exp(-x.dist_contacto_intrusivo_cartografiada_m/15000)*(herc+x.edades_u013_fraccion)
    neo = x.edades_u011_fraccion+x.edades_u012_fraccion+x.edades_u016_fraccion
    x["volcanismo_neogeno"] = x.litologia_u019_fraccion*neo
    competent = sum(x[f"litologia_u{k:03d}_fraccion"] for k in [8, 10, 11, 15, 0])
    incompetent = sum(x[f"litologia_u{k:03d}_fraccion"] for k in [16, 13, 1])
    x["contraste_reologico"] = 4*competent*incompetent
    x["trampa_estructural_reologica"] = np.exp(-x.dist_falla_cartografiada_m/5000)*x.contraste_reologico
    inputs = []
    for directory, selected in [
        ("reentrenamiento_gravimetria_20261021/favorabilidad_nacional_gravimetria.parquet",
         {"bouguer_gradiente_mgal_km": "bouguer_gradiente", "bouguer_residual_local_zscore": "bouguer_residual_local_zscore"}),
        ("reentrenamiento_aeromagnetometria_20261021/favorabilidad_nacional_aeromagnetometria.parquet",
         {"magnetometria_gradiente_nt_km": "magnetometria_gradiente", "magnetometria_residual_local_zscore": "magnetometria_residual_local_zscore"})]:
        path = root / "reports" / directory
        inputs.append(path)
        frame = pd.read_parquet(path, columns=["cell_id"]+list(selected)).set_index("cell_id")
        for original, new in selected.items():
            x[new] = frame.loc[x.index, original]
    density_path = root / data.config["phase_d_run"] / "X_features.parquet"
    density = pd.read_parquet(density_path, columns=["cell_id", "dens_aprox_falla_cartografiada_1000m_km_km2"]).set_index("cell_id")
    x["dens_falla_1000m"] = density.loc[x.index, "dens_aprox_falla_cartografiada_1000m_km_km2"]
    fault = np.exp(-x.dist_falla_cartografiada_m.fillna(15000)/3000)
    thrust = np.exp(-x.dist_cabalgamiento_cartografiada_m.fillna(15000)/3000)
    x["nodo_dilatacion_falla_cabalgamiento"] = fault*thrust
    x["trampa_dilatacional_reologica"] = x.dens_falla_1000m*x.contraste_reologico
    x["acoplamiento_sutura_falla"] = x.bouguer_gradiente*fault
    sat, sat_inputs = satellite_from_cached_tiles(root, spec, rows, cols)
    inputs += sat_inputs
    for name, values in sat.items():
        x[name] = values
    audit, representatives = [], []
    for element in ELEMENTS:
        path = root / f"AtlasGeoquimico_{element.title() if element != 'as' else 'As'}_Sedimentos_2012.tif"
        # Chemical symbols have one initial capital: Sb, Bi, Cu, Hg, W, Pb, Zn.
        inputs.append(path)
        with rasterio.open(path) as src:
            expected = from_origin(spec["origin_x"], spec["origin_y"], 500, 500)
            if src.shape != (shape[0]*2, shape[1]*2) or src.transform != expected or str(src.crs) != spec["crs"]:
                raise ValueError(f"Ráster geoquímico no alineado: {path.name}")
            category, value, lower, upper = [src.read(b) for b in range(1, 5)]
            good = np.isfinite(value) & (value > 0) & (category >= 0) & (category <= 7)
            pairs = np.unique(np.column_stack([category[good], value[good]]), axis=0)
            one_per_class = len(pairs) == len(np.unique(category[good]))
            audit.append({"elemento": element.upper(), "banda": src.descriptions[1],
                "unidades_etiquetadas": src.tags().get("UNITS", "no documentadas"),
                "valores_distintos_500m": int(len(np.unique(value[good]))),
                "un_valor_por_clase": one_per_class,
                "mediciones_analiticas_continuas": False,
                "fraccion_ausente_500m": float(1-good.mean())})
            for category_value, representative in pairs:
                representatives.append({"elemento": element.upper(), "clase": int(category_value),
                                         "representante_intervalo": float(representative)})
        value[~good] = np.nan
        blocks = np.stack([value[0::2, 0::2], value[1::2, 0::2], value[0::2, 1::2], value[1::2, 1::2]])
        n = np.isfinite(blocks).sum(axis=0)
        mean = np.divide(np.nansum(blocks, axis=0), n, out=np.full(shape, np.nan), where=n > 0)
        x[f"geoq_{element}_representante_intervalo_log"] = np.log1p(mean[rows, cols])
    # This column is computed inside each fitted Pipeline, using its training statistics.
    x["indice_pathfinders_oro"] = np.nan
    raw_as_sb = x[GEOCHEMICAL[0]]+x[GEOCHEMICAL[1]]
    x["anomalia_local_as_sb_zscore"] = local_residual(raw_as_sb.to_numpy(), shape, rows, cols)
    x["trampa_valle_aluvial"] = np.exp(-x.dist_cauce_m/300)*np.exp(-x.pendiente_grados/6)
    x["vector_epitermal_hidrotermal"] = np.maximum(x.volcanismo_neogeno, .1)*x.ratio_alteracion_filica_swir*x.ratio_gossan_oxidos_hierro
    x = x.replace([np.inf, -np.inf], np.nan).astype("float32")
    if len(x.columns) != 95:
        raise AssertionError(f"Se esperaban 95 covariables: {len(x.columns)}")
    pd.DataFrame(audit).to_csv(output / "auditoria_geoquimica.csv", index=False)
    pd.DataFrame(representatives).to_csv(output / "representantes_clases_geoquimicas.csv", index=False)
    schema = pd.DataFrame({"variable": x.columns, "incluida_93": [c not in DIAGNOSTIC for c in x.columns],
        "interpretacion": ["representante de intervalo; no analítica continua" if c in GEOCHEMICAL else
                           "estadísticas aprendidas dentro de cada entrenamiento" if c == "indice_pathfinders_oro" else
                           "proxy litológico heurístico; no grado metamórfico medido" if c in ["grado_metamorfico", "afinidad_esquistos_verdes"] else
                           "covariable cartográfica; no etiqueta ni predicción" for c in x.columns]})
    schema.to_csv(output / "contrato_variables.csv", index=False)
    x.to_parquet(output / "X_nb27.parquet")
    return x, inputs


class FoldPathfinders(TransformerMixin, BaseEstimator):
    """Learn all empirical global statistics only from this member's fit rows."""
    def fit(self, X, y=None):
        self.columns_ = [f"geoq_{e}_representante_intervalo_log" for e in ["as", "sb", "bi", "w"]]
        self.mean_ = X[self.columns_].mean().fillna(0.)
        self.std_ = X[self.columns_].std(ddof=0).replace(0., 1.).fillna(1.)
        return self

    def transform(self, X):
        result = X.copy()
        z = (result[self.columns_]-self.mean_)/self.std_
        result["indice_pathfinders_oro"] = z.to_numpy() @ np.array([1., 1., .8, .5])
        return result


def geological_rule(X):
    """Predeclared simple physical baseline, no fit and no test normalization."""
    valley = X.trampa_valle_aluvial.fillna(0).clip(0, 1).to_numpy()
    volcanic = X.volcanismo_neogeno.fillna(0).clip(0, 1).to_numpy()
    swir = X.ratio_alteracion_filica_swir.fillna(0).to_numpy()
    iron = X.ratio_gossan_oxidos_hierro.fillna(0).to_numpy()
    epithermal = volcanic*np.clip((swir-1.)/2., 0, 1)*np.clip((iron-1.)/3., 0, 1)
    host = X[[f"litologia_u{k:03d}_fraccion" for k in [8, 11, 14, 15, 16]]].sum(axis=1).clip(0, 1)
    primary = np.exp(-X.dist_falla_cartografiada_m.fillna(15000)/5000)*host
    return np.maximum.reduce([valley, epithermal, primary.to_numpy()])
