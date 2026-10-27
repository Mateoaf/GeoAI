"""Predeclared, label-free covariates and a matched prospective pilot for NB29."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ALLUVIAL = "trampa_aluvial_contextual_nb29"
SPECTRAL = "alteracion_suelo_expuesto_nb29"
NEW_FEATURES = [ALLUVIAL, SPECTRAL]
FEATURE_PARAMETERS = {"channel_scale_m": 300., "slope_scale_deg": 6.,
    "positive_tpi_scale_m": 50., "sedimentary_floor": .25,
    "swir_clip": 4., "iron_clip": 5., "vegetation_exponent": 2.}


def add_descriptors(X):
    """Interactions, not additional analytical observations or mineral diagnoses.

    u012 is the documented gravel/conglomerate/sand/silt unit. TPI>0 penalizes
    positions above the local mean gently; it is not upstream hydraulic energy.
    The spectral interaction attenuates vegetation without claiming MODIS QA.
    Missing inputs remain missing for each member's training-only imputer.
    """
    x = X.copy()
    sediment = x.litologia_u012_fraccion.clip(0, 1)
    valley = np.exp(-x.dist_cauce_m.clip(lower=0)/300.) * np.exp(-x.pendiente_grados.clip(lower=0)/6.)
    topographic = np.exp(-x.tpi_1000m_m.clip(lower=0)/50.)
    x[ALLUVIAL] = valley*(.25+.75*sediment)*topographic
    swir = (x.ratio_alteracion_filica_swir.clip(0, 4)-1.).clip(lower=0)
    iron = (x.ratio_gossan_oxidos_hierro.clip(0, 5)-1.).clip(lower=0)
    exposure = (1.-x.ndvi_cobertura_vegetal.clip(0, 1))**2
    x[SPECTRAL] = np.log1p(swir)*np.log1p(iron)*exposure
    x[NEW_FEATURES] = x[NEW_FEATURES].replace([np.inf, -np.inf], np.nan).astype("float32")
    return x


def audit_sources(data, X, output):
    """Resolve category meanings from their dictionaries; reject uninformative layers."""
    folder = data.root / data.config["phase_d_run"]
    lithology = pd.read_csv(folder / "dictionaries/litologia.csv").set_index("category_id")
    ages = pd.read_csv(folder / "dictionaries/edades.csv").set_index("category_id")
    if lithology.loc["litologia_u012", "description"] != "Gravas, conglomerados, arenas y limos":
        raise ValueError("La unidad u012 ha cambiado de significado; revisar antes de entrenar.")
    if ages.loc["edades_u004", "description"] != "CUATERNARIO":
        raise ValueError("La unidad de edad cuaternaria ha cambiado.")
    age = pd.read_parquet(folder / "X_features.parquet", columns=["cell_id", "edades_u004_fraccion"]).set_index("cell_id")
    duplicated = np.allclose(age.loc[X.index, "edades_u004_fraccion"], X.litologia_u012_fraccion, equal_nan=True, atol=0, rtol=0)
    rows = [dict(source="litologia_u000", interpretation=lithology.loc["litologia_u000", "description"],
                 decision="No se utiliza como sinónimo de terraza ni de sedimento cuaternario"),
            dict(source="litologia_u012", interpretation=lithology.loc["litologia_u012", "description"],
                 decision="Contexto sedimentario amplio; no certifica terraza fluvial"),
            dict(source="edades_u004", interpretation=ages.loc["edades_u004", "description"],
                 decision=f"Duplicación exacta de u012 en el dominio: {duplicated}; no se añade otra columna")]
    path = data.root / "cuaternariorecintos.gpkg"
    uri = path.resolve().as_uri()+"?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        count = connection.execute("SELECT COUNT(*) FROM cuaternariorecintos").fetchone()[0]
        descriptions = connection.execute("SELECT DESC_UNIT,COUNT(*) FROM cuaternariorecintos GROUP BY DESC_UNIT").fetchall()
        codes = connection.execute("SELECT CODE_GEOM,COUNT(*) FROM cuaternariorecintos GROUP BY CODE_GEOM").fetchall()
    rows.append(dict(source=path.name,
        interpretation=json.dumps({"n": count, "descriptions": descriptions, "geomorphology_codes": codes}, ensure_ascii=False),
        decision="No se añade: no distingue terrazas/aluviales con atributos documentados suficientes"))
    frame = pd.DataFrame(rows)
    frame.to_csv(output / "auditoria_semantica_fuentes.csv", index=False)
    pd.DataFrame([
        {"variable": ALLUVIAL, "formula": "exp(-dist_cauce/300)*exp(-pendiente/6)*(0.25+0.75*u012)*exp(-max(TPI1000,0)/50)",
         "meaning": "Interacción de contexto sedimentario y posición topográfica; no energía hidráulica ni terraza observada"},
        {"variable": SPECTRAL, "formula": "log1p(max(clip(SWIR,0,4)-1,0))*log1p(max(clip(Fe,0,5)-1,0))*(1-clip(NDVI,0,1))**2",
         "meaning": "Proxy regional MODIS con atenuación vegetal; sin Sentinel-2 nuevo, máscara QA o diagnóstico mineral"}
    ]).to_csv(output / "contrato_descriptores_nb29.csv", index=False)
    return frame


def match_pilot(candidates, target_pairs=12, separation_m=10000., radius_m=75000., seed=42):
    """Choose complete high/mid/low triplets in the same 100 km region and lithology.

    Input already excludes all recorded cells and their 15 km neighborhoods.
    Strict constraints are never relaxed to fill the requested sample size.
    """
    frame = candidates.copy()
    frame["region"] = ((frame.x_center//100000).astype(int).astype(str)+"_"+(frame.y_center//100000).astype(int).astype(str))
    bins = {"alta": frame.percentile.ge(.995),
            "media": frame.percentile.between(.80, .85),
            "baja": frame.percentile.between(.20, .25)}
    high = frame.loc[bins["alta"]].sort_values(["score", "cell_id"], ascending=[False, True])
    pools = {label: {key: g.copy() for key, g in frame.loc[bins[label]].groupby(["region", "substrate"])}
             for label in ["media", "baja"]}
    rng = np.random.default_rng(seed)
    selected, rejections, used_high_blocks = [], [], set()
    def separated(points, others):
        if not others:
            return np.ones(len(points), dtype=bool)
        return cKDTree(np.asarray(others)).query(points)[0] >= separation_m
    for row in high.itertuples(index=False):
        if len(selected)//3 >= target_pairs:
            break
        high_xy = [row.x_center, row.y_center]
        existing = [[r["x_center"], r["y_center"]] for r in selected]
        if row.block_id in used_high_blocks or not separated(np.array([high_xy]), existing)[0]:
            continue
        tentative = [row._asdict() | {"stratum": "alta"}]
        reason = None
        for label in ["media", "baja"]:
            group = pools[label].get((row.region, row.substrate))
            if group is None:
                reason = f"sin_control_{label}_misma_region_y_litologia"
                break
            xy = group[["x_center", "y_center"]].to_numpy()
            distance = np.linalg.norm(xy-np.asarray(high_xy), axis=1)
            forbidden = existing+[[r["x_center"], r["y_center"]] for r in tentative]
            ok = (distance <= radius_m) & separated(xy, forbidden)
            valid = np.flatnonzero(ok)
            if not len(valid):
                reason = f"sin_control_{label}_con_distancias_admisibles"
                break
            # Random tie-break at equal spatial match quality, fixed before field work.
            priority = np.lexsort((rng.random(len(valid)), distance[valid]))
            control = group.iloc[valid[priority[0]]].to_dict()
            tentative.append(control | {"stratum": label})
        if reason:
            rejections.append({"cell_id": row.cell_id, "reason": reason})
            continue
        pair_id = f"NB29_T{len(selected)//3+1:02d}"
        selected.extend([r | {"triplet_id": pair_id} for r in tentative])
        used_high_blocks.add(row.block_id)
    result = pd.DataFrame(selected)
    return result, pd.DataFrame(rejections, columns=["cell_id", "reason"])
