"""Paso 11 — Fase H: Cierre científico, interpretabilidad y mapa nacional final.

- No reentrena ni evalúa nuevos modelos sobre el holdout.
- Utiliza el pipeline congelado logistic_01 para inferir sobre las 478.443 celdas eligible_approved_features.
- Exporta cartografía continua y percentiles en GeoPackage, GeoParquet y COG.
- Deriva zonas de prospectividad/priorización al 1%, 5% y 10% (nunca 'yacimientos predichos').
- Analiza coeficientes estandarizados y contribuciones locales para Rodalquilar, La Jara, Corcoesto y Santa Comba.
- Añade sensibilidad de incertidumbre por distrito sobre predicciones selladas de Fase G.
- Sella la Fase H con manifiesto SHA-256.
"""
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import shutil
import time

import geopandas as gpd
import joblib
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import shapes
from rasterio.transform import Affine
import scipy.ndimage as ndi
from shapely.geometry import Point, shape
from sklearn.metrics import average_precision_score, roc_auc_score

from geoau import evaluation as ev
from geoau.local_sources import sha256_file, write_json
from geoau.training import FeatureGuard, SafeOneHot  # Requeridos para unpickle del pipeline


def ejecutar_fase_h():
    print("=" * 80)
    print("PASO 11 — FASE H: CIERRE CIENTÍFICO, INTERPRETABILIDAD Y MAPA FINAL")
    print("=" * 80)
    t_start = time.time()

    root = Path(__file__).resolve().parents[1]

    # 1. Rutas de procedencia inmutables
    f_run = "reports/fase_f/20260927T135750_819061Z"
    g_run = "reports/fase_g/20260927T141408_460613Z"
    model_path = root / f_run / "final_model/final_validated_model.joblib"
    meta_path = root / f_run / "final_model/final_validated_model.json"
    
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    d_run = meta["phase_d_run"]
    e_run = meta["phase_e_run"]
    cols = meta["columns"]
    seed = 42

    print(f"Modelo congelado: {meta['candidate_id']} ({meta['family']}, ratio={meta['ratio']}, C={meta['params'].get('C')})")
    print(f"Procedencia verificada: D={d_run}, E={e_run}, F={f_run}, G={g_run}")

    # Verificar integridad SHA-256 de todas las fases previas
    for run_dir in [d_run, e_run, f_run, g_run]:
        ev.verify(root / run_dir, ev.read_json(root / run_dir / "outputs_manifest.json"))
    print("Integridad criptográfica SHA-256 de Fases D, E, F y G verificada al 100%.")

    # 2. Crear directorio sellado de Fase H
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    out = root / "reports/fase_h" / stamp
    out.mkdir(parents=True, exist_ok=False)
    for sub in ["maps", "interpretability", "uncertainty", "targets"]:
        (out / sub).mkdir()
    print(f"Directorio Fase H: {out}")

    # 3. Predicción Nacional sobre las 478.443 celdas eligible_approved_features
    print("\n--- Generación del Mapa Nacional de Prospectividad (478.443 celdas) ---")
    supp = pd.read_parquet(root / d_run / "calidad_y_soporte.parquet")
    mask_el = supp.eligible_approved_features.eq(True)
    el_cells = supp.loc[mask_el, ["cell_id", "row", "col", "x_center", "y_center", "land_area_m2"]].copy().reset_index(drop=True)
    
    n_cells = len(el_cells)
    if n_cells != 478443:
        raise ValueError(f"Se esperaban 478.443 celdas elegibles, encontradas {n_cells}")
    print(f"Celdas elegibles cargadas: {n_cells}")

    pipeline = joblib.load(model_path)
    X_all = pd.read_parquet(root / d_run / "X_features.parquet", columns=["cell_id"] + cols).set_index("cell_id")
    X_el = X_all.loc[el_cells.cell_id, cols]

    t_inf = time.time()
    scores = pipeline.predict_proba(X_el)[:, 1]
    print(f"Inferencia nacional completada en {time.time() - t_inf:.2f}s.")
    print(f"Rango de scores nacionales: min={scores.min():.4f}, media={scores.mean():.4f}, mediana={np.median(scores):.4f}, max={scores.max():.4f}")

    el_cells["score"] = scores
    el_cells["tie_key"] = [ev.seed_for(seed, "ties_national", cid) for cid in el_cells.cell_id]

    # Ordenamiento nacional determinista por área
    order = np.lexsort((el_cells["tie_key"].to_numpy(), -scores))
    ranked = el_cells.iloc[order].copy().reset_index(drop=True)
    ranked["rank"] = np.arange(1, len(ranked) + 1)
    
    total_national_area = float(ranked["land_area_m2"].sum())
    ranked["cumulative_area_m2"] = ranked["land_area_m2"].cumsum()
    ranked["cumulative_area_fraction"] = ranked["cumulative_area_m2"] / total_national_area
    ranked["percentile_favorabilidad"] = 100.0 * (1.0 - (ranked["rank"] - 0.5) / len(ranked))

    # Definir bandas de priorización territorial
    # Top 1% (área <= 0.01), Top 5% (0.01 < área <= 0.05), Top 10% (0.05 < área <= 0.10), Base (> 0.10)
    conditions = [
        ranked["cumulative_area_fraction"] <= 0.01,
        ranked["cumulative_area_fraction"] <= 0.05,
        ranked["cumulative_area_fraction"] <= 0.10
    ]
    choices = ["top_01", "top_05", "top_10"]
    ranked["prioridad_banda"] = np.select(conditions, choices, default="fondo_no_priorizado")

    threshold_01 = float(ranked.loc[ranked["prioridad_banda"] == "top_01", "score"].min())
    threshold_05 = float(ranked.loc[ranked["prioridad_banda"].isin(["top_01", "top_05"]), "score"].min())
    threshold_10 = float(ranked.loc[ranked["prioridad_banda"].isin(["top_01", "top_05", "top_10"]), "score"].min())

    print(f"Umbral Score Top 1% de área nacional:  >= {threshold_01:.4f} (área: {ranked.loc[ranked['prioridad_banda']=='top_01', 'land_area_m2'].sum()/1e6:.1f} km²)")
    print(f"Umbral Score Top 5% de área nacional:  >= {threshold_05:.4f} (área: {ranked.loc[ranked['prioridad_banda'].isin(['top_01','top_05']), 'land_area_m2'].sum()/1e6:.1f} km²)")
    print(f"Umbral Score Top 10% de área nacional: >= {threshold_10:.4f} (área: {ranked.loc[ranked['prioridad_banda'].isin(['top_01','top_05','top_10']), 'land_area_m2'].sum()/1e6:.1f} km²)")

    # 4. Exportación de Rásteres COG (EPSG:25830)
    print("\n--- Exportando Cartografía Raster (COG EPSG:25830) ---")
    grid_spec = json.loads((root / d_run / "grid_spec.json").read_text(encoding="utf-8"))
    width, height = grid_spec["width"], grid_spec["height"]
    transform = Affine.from_gdal(*grid_spec["transform_gdal"])
    crs_str = grid_spec["crs"]

    # Ráster continuo de Score
    arr_score = np.full((height, width), -9999.0, dtype=np.float32)
    arr_score[ranked["row"].to_numpy(), ranked["col"].to_numpy()] = ranked["score"].to_numpy()

    score_cog_path = out / "maps/mapa_nacional_favorabilidad_score.tif"
    with rasterio.open(
        score_cog_path, "w",
        driver="COG", width=width, height=height, count=1,
        dtype="float32", nodata=-9999.0, crs=crs_str, transform=transform,
        compress="deflate"
    ) as dst:
        dst.write(arr_score, 1)
        dst.set_band_description(1, "Score de Favorabilidad Aurifera (logistic_01)")

    # Ráster continuo de Percentil Nacional (0 a 100)
    arr_pct = np.full((height, width), -9999.0, dtype=np.float32)
    arr_pct[ranked["row"].to_numpy(), ranked["col"].to_numpy()] = ranked["percentile_favorabilidad"].to_numpy()

    pct_cog_path = out / "maps/mapa_nacional_favorabilidad_percentil.tif"
    with rasterio.open(
        pct_cog_path, "w",
        driver="COG", width=width, height=height, count=1,
        dtype="float32", nodata=-9999.0, crs=crs_str, transform=transform,
        compress="deflate"
    ) as dst:
        dst.write(arr_pct, 1)
        dst.set_band_description(1, "Percentil Nacional de Favorabilidad (0-100%)")

    # Ráster categórico de Bandas Prioritarias
    # 1: top_01, 2: top_05, 3: top_10, 0: fondo, 255: nodata
    arr_bandas = np.full((height, width), 255, dtype=np.uint8)
    band_code_map = {"top_01": 1, "top_05": 2, "top_10": 3, "fondo_no_priorizado": 0}
    codes = ranked["prioridad_banda"].map(band_code_map).to_numpy(dtype=np.uint8)
    arr_bandas[ranked["row"].to_numpy(), ranked["col"].to_numpy()] = codes

    bandas_cog_path = out / "maps/mapa_nacional_bandas_prioritarias.tif"
    with rasterio.open(
        bandas_cog_path, "w",
        driver="COG", width=width, height=height, count=1,
        dtype="uint8", nodata=255, crs=crs_str, transform=transform,
        compress="deflate"
    ) as dst:
        dst.write(arr_bandas, 1)
        dst.set_band_description(1, "Bandas Prioritarias de Prospectividad (1=Top1%, 2=Top1-5%, 3=Top5-10%, 0=Fondo)")

    print(f"Rásteres COG generados con éxito en {out / 'maps'}")

    # 5. Exportación Vectorial (GeoParquet y GeoPackage)
    print("\n--- Exportando Cartografía Vectorial (GeoParquet y GeoPackage) ---")
    # Construcción de GeoDataFrame con centroides
    gdf_cells = gpd.GeoDataFrame(
        ranked[["cell_id", "row", "col", "score", "percentile_favorabilidad", "prioridad_banda", "land_area_m2"]],
        geometry=[Point(xy) for xy in zip(ranked["x_center"], ranked["y_center"])],
        crs=crs_str
    )

    # GeoParquet completo (todas las 478.443 celdas)
    geoparquet_path = out / "maps/mapa_nacional_prospectividad.geoparquet"
    gdf_cells.to_parquet(geoparquet_path, index=False)
    print(f"GeoParquet nacional guardado ({len(gdf_cells)} celdas)")

    # GeoPackage: Capa de Celdas Priorizadas Top 10% (47.844 celdas)
    gpkg_path = out / "maps/mapa_nacional_prospectividad.gpkg"
    gdf_top10 = gdf_cells[gdf_cells["prioridad_banda"].isin(["top_01", "top_05", "top_10"])].copy()
    gdf_top10.to_file(gpkg_path, layer="celdas_priorizadas_top10", driver="GPKG")
    print(f"GeoPackage capa 'celdas_priorizadas_top10' guardada ({len(gdf_top10)} celdas)")

    # 6. Extracción y Ranking Espacial de Zonas de Prospectividad/Priorización
    print("\n--- Delineación y Ranking de Zonas de Prospectividad/Priorización ---")
    # Agrupación espacial contigua en Top 1% y Top 5%
    mask_top05 = (arr_bandas == 1) | (arr_bandas == 2)
    labeled_top05, num_features = ndi.label(mask_top05)
    
    # Vectorización de clusters contiguos a polígonos
    shapes_gen = shapes(labeled_top05.astype(np.int32), mask=labeled_top05 > 0, transform=transform)
    
    zones_list = []
    zone_idx = 1
    
    # Cargar indicios revisados para calcular cercanía a depósitos/distritos conocidos
    rel = pd.read_parquet(root / d_run / "relacion_indicios_celda.parquet")
    p_rev = rel[rel.elegible_general_revisada.eq(True)].drop_duplicates(subset=["cell_id"])
    p_rev = p_rev.merge(supp[["cell_id", "x_center", "y_center"]], on="cell_id", how="left")

    for geom_dict, label_val in shapes_gen:
        poly = shape(geom_dict)
        if poly.area < 1e6:  # Mínimo 1 celda (1 km²)
            continue
            
        # Celdas que caen en este polígono
        # Usamos coordenadas de bounding box y máscara rápida
        centroid = poly.centroid
        area_km2 = float(poly.area / 1e6)
        
        # Encontrar celdas dentro del cluster
        sub_cells = ranked[(arr_bandas[ranked["row"].to_numpy(), ranked["col"].to_numpy()] > 0) & 
                           (labeled_top05[ranked["row"].to_numpy(), ranked["col"].to_numpy()] == int(label_val))]
        
        if len(sub_cells) == 0:
            continue
            
        max_score = float(sub_cells["score"].max())
        mean_score = float(sub_cells["score"].mean())
        has_top01 = any(sub_cells["prioridad_banda"] == "top_01")
        priority_class = "prioridad_muy_alta_top01" if has_top01 else "prioridad_alta_top05"
        
        # Depósito o distrito conocido más próximo
        dists_to_p = np.hypot(p_rev["x_center"] - centroid.x, p_rev["y_center"] - centroid.y)
        min_idx = dists_to_p.argmin()
        nearest_dep = p_rev.iloc[min_idx]["deposit_id"]
        nearest_dist = p_rev.iloc[min_idx]["district_id"]
        dist_to_nearest_km = float(dists_to_p.iloc[min_idx] / 1000.0)

        zones_list.append({
            "zona_id": f"zona_priorizacion_{zone_idx:03d}",
            "denominacion": f"Zona de Prospectividad/Priorización {zone_idx:03d}",
            "categoria_prioridad": priority_class,
            "area_km2": area_km2,
            "celdas_count": len(sub_cells),
            "score_maximo": max_score,
            "score_medio": mean_score,
            "centroide_x": float(centroid.x),
            "centroide_y": float(centroid.y),
            "deposito_conocido_proximo": nearest_dep,
            "distrito_conocido_proximo": nearest_dist,
            "distancia_deposito_proximo_km": dist_to_nearest_km,
            "geometry": poly
        })
        zone_idx += 1

    gdf_zones = gpd.GeoDataFrame(zones_list, crs=crs_str)
    # Ordenar ranking por score máximo y área
    gdf_zones = gdf_zones.sort_values(by=["score_maximo", "area_km2"], ascending=[False, False]).reset_index(drop=True)
    gdf_zones["ranking_nacional"] = np.arange(1, len(gdf_zones) + 1)
    
    # Exportar tabla de ranking y capa al GeoPackage
    df_zones_export = gdf_zones.drop(columns=["geometry"])
    df_zones_export.to_csv(out / "targets/zonas_prospectividad_ranking.csv", index=False, encoding="utf-8-sig")
    gdf_zones.to_file(gpkg_path, layer="zonas_prospectividad", driver="GPKG")
    print(f"Identificadas {len(gdf_zones)} zonas de prospectividad/priorización. Exportadas a GeoPackage y CSV.")

    print("\nTop 10 Zonas de Prospectividad/Priorización Identificadas:")
    for _, r in df_zones_export.head(10).iterrows():
        print(f"  #{r['ranking_nacional']:02d} | {r['denominacion']} ({r['categoria_prioridad']}) | Área: {r['area_km2']:.0f} km² | Score Máx: {r['score_maximo']:.4f} | Próximo a: {r['deposito_conocido_proximo']} ({r['distrito_conocido_proximo']}, {r['distancia_deposito_proximo_km']:.1f} km)")

    # 7. Análisis de Coeficientes Estandarizados e Interpretabilidad
    print("\n--- Análisis de Interpretabilidad y Coeficientes Estandarizados ---")
    dict_245 = pd.read_csv(root / "informes/variables_grid_master_au_20260925/diccionario_245_variables.csv").set_index("variable")
    clf = pipeline.named_steps["model"]
    coefs = clf.coef_[0]
    intercept = float(clf.intercept_[0])
    
    coef_rows = []
    for col_name, c_val in zip(cols, coefs):
        sig = dict_245.loc[col_name, "significado"] if col_name in dict_245.index else ""
        fam = dict_245.loc[col_name, "familia"] if col_name in dict_245.index else ""
        coef_rows.append({
            "variable": col_name,
            "familia": fam,
            "coeficiente_estandarizado": float(c_val),
            "abs_coeficiente": float(abs(c_val)),
            "odds_ratio": float(np.exp(c_val)),
            "impacto_modelo": "positivo (aumenta favorabilidad)" if c_val > 0 else "negativo (reduce favorabilidad)",
            "significado_geologico": sig
        })
    df_coef = pd.DataFrame(coef_rows).sort_values(by="abs_coeficiente", ascending=False).reset_index(drop=True)
    df_coef.to_csv(out / "interpretability/coeficientes_estandarizados.csv", index=False, encoding="utf-8-sig")

    # Contribuciones locales para Rodalquilar, La Jara, Corcoesto y Santa Comba
    guard = pipeline.named_steps["guard"]
    pre = pipeline.named_steps["preprocess"]
    
    target_case_deps = ["dep_rodalquilar_cinto", "dep_la_oriental_la_jara", "dep_corcoesto", "dep_santa_comba_zas"]
    local_contrib_rows = []
    
    for dep_name in target_case_deps:
        dep_cells = p_rev[p_rev.deposit_id == dep_name]["cell_id"].unique()
        x_dep = X_all.loc[dep_cells, cols]
        
        # Transformar features exactamente como en pipeline
        x_guarded = guard.transform(x_dep)
        x_trans = pre.transform(x_guarded)  # Array escalado
        contrib_matrix = x_trans * coefs   # (n_cells, n_features)
        mean_contribs = np.mean(contrib_matrix, axis=0)
        dep_scores = pipeline.predict_proba(x_dep)[:, 1]
        
        for c_name, c_mean, val_scaled in zip(cols, mean_contribs, np.mean(x_trans, axis=0)):
            sig = dict_245.loc[c_name, "significado"] if c_name in dict_245.index else ""
            local_contrib_rows.append({
                "deposito_id": dep_name,
                "n_celdas": len(dep_cells),
                "score_medio": float(np.mean(dep_scores)),
                "score_maximo": float(np.max(dep_scores)),
                "variable": c_name,
                "valor_medio_escalado": float(val_scaled),
                "coeficiente": float(df_coef.set_index("variable").loc[c_name, "coeficiente_estandarizado"]),
                "contribucion_log_odds": float(c_mean),
                "abs_contribucion": float(abs(c_mean)),
                "significado_geologico": sig
            })
            
    df_local_contrib = pd.DataFrame(local_contrib_rows)
    df_local_contrib = df_local_contrib.sort_values(by=["deposito_id", "abs_contribucion"], ascending=[True, False]).reset_index(drop=True)
    df_local_contrib.to_csv(out / "interpretability/contribuciones_locales_casos_estudio.csv", index=False, encoding="utf-8-sig")
    print(f"Análisis de coeficientes y contribuciones locales guardado en {out / 'interpretability'}")

    # 8. Sensibilidad de Incertidumbre utilizando predicciones selladas de Fase G
    print("\n--- Sensibilidad de Incertidumbre sobre Predicciones de Fase G ---")
    g_preds = pd.read_parquet(root / g_run / "predictions/holdout_predictions.parquet")
    df_dep_g = pd.read_csv(root / g_run / "metrics/holdout_by_deposit.csv")
    df_dist_g = pd.read_csv(root / g_run / "metrics/holdout_by_district.csv")

    # A) Sensibilidad Leave-One-District-Out en Holdout
    lodo_rows = []
    districts_in_g = sorted(df_dist_g["district_id"].unique())
    
    for omit_dist in districts_in_g:
        # Filtrar holdout excluyendo el distrito
        sub_preds = g_preds[g_preds["district_id"] != omit_dist].copy()
        sub_deps = df_dep_g[df_dep_g["district_id"] != omit_dist]
        
        n_sub_deps = len(sub_deps)
        sub_total_area = sub_preds["land_area_m2"].sum()
        
        # Recalcular ranking en el subconjunto
        sub_preds = sub_preds.sort_values(by=["score", "tie_key"], ascending=[False, True]).reset_index(drop=True)
        sub_preds["sub_cum_area"] = sub_preds["land_area_m2"].cumsum()
        sub_preds["sub_cum_frac"] = sub_preds["sub_cum_area"] / sub_total_area
        
        # Métricas de recuperación
        sel_01 = set(sub_preds.loc[sub_preds["sub_cum_frac"] <= 0.01, "cell_id"])
        sel_05 = set(sub_preds.loc[sub_preds["sub_cum_frac"] <= 0.05, "cell_id"])
        sel_10 = set(sub_preds.loc[sub_preds["sub_cum_frac"] <= 0.10, "cell_id"])
        
        # Depósitos recuperados
        p_sub = sub_preds[sub_preds["is_P"]]
        dep_cell_map = p_sub.groupby("deposit_id")["cell_id"].unique().to_dict()
        
        rec_01 = sum(any(c in sel_01 for c in clist) for clist in dep_cell_map.values())
        rec_05 = sum(any(c in sel_05 for c in clist) for clist in dep_cell_map.values())
        rec_10 = sum(any(c in sel_10 for c in clist) for clist in dep_cell_map.values())
        
        # ROC-AUC en subconjunto
        y_sub = sub_preds["is_P"].astype(int).to_numpy()
        roc_sub = float(roc_auc_score(y_sub, sub_preds["score"])) if len(np.unique(y_sub)) == 2 else np.nan

        lodo_rows.append({
            "distrito_omitido": omit_dist,
            "distritos_evaluados": len(districts_in_g) - 1,
            "depositos_evaluados": n_sub_deps,
            "celdas_evaluadas": len(sub_preds),
            "deposit_recovery_at_01": float(rec_01 / n_sub_deps),
            "deposit_recovery_at_05": float(rec_05 / n_sub_deps),
            "deposit_recovery_at_10": float(rec_10 / n_sub_deps),
            "roc_auc_PU": roc_sub
        })
    df_lodo = pd.DataFrame(lodo_rows)
    df_lodo.to_csv(out / "uncertainty/sensibilidad_leave_one_district_out.csv", index=False, encoding="utf-8-sig")

    # B) Curva de Sensibilidad a Umbrales de Área (f = 0.005 a 0.20)
    curve_rows = []
    dep_cell_map_full = g_preds[g_preds["is_P"]].groupby("deposit_id")["cell_id"].unique().to_dict()
    total_holdout_p_cells = int(g_preds["is_P"].sum())
    total_holdout_deps = len(dep_cell_map_full)
    
    fractions_to_test = [0.005, 0.01, 0.015, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.12, 0.15, 0.20]
    for frac in fractions_to_test:
        sel_cells = set(g_preds.loc[g_preds["cumulative_area_fraction"] <= frac, "cell_id"])
        c_hits = sum(1 for cid in sel_cells if cid in g_preds.loc[g_preds["is_P"], "cell_id"].values)
        d_hits = sum(1 for clist in dep_cell_map_full.values() if any(c in sel_cells for c in clist))
        
        curve_rows.append({
            "fraccion_area_presupuesto": frac,
            "area_km2": frac * float(total_national_area if False else g_preds["land_area_m2"].sum() / 1e6),
            "deposit_recovery": float(d_hits / total_holdout_deps),
            "depositos_recuperados": d_hits,
            "cell_recovery": float(c_hits / total_holdout_p_cells),
            "celdas_recuperadas": c_hits
        })
    df_curve = pd.DataFrame(curve_rows)
    df_curve.to_csv(out / "uncertainty/curva_sensibilidad_umbrales_holdout.csv", index=False, encoding="utf-8-sig")

    # C) Dispersión y Estadísticas por Distrito en Holdout
    dist_stats_rows = []
    for dist_id, grp in g_preds.groupby("district_id"):
        scores_d = grp["score"].to_numpy()
        dist_stats_rows.append({
            "district_id": dist_id,
            "celdas": len(scores_d),
            "celdas_p": int(grp["is_P"].sum()),
            "score_min": float(np.min(scores_d)),
            "score_p05": float(np.percentile(scores_d, 5)),
            "score_p25": float(np.percentile(scores_d, 25)),
            "score_mediana": float(np.median(scores_d)),
            "score_p75": float(np.percentile(scores_d, 75)),
            "score_p95": float(np.percentile(scores_d, 95)),
            "score_max": float(np.max(scores_d)),
            "score_media": float(np.mean(scores_d)),
            "score_desvest": float(np.std(scores_d)),
            "rango_intercuartilico": float(np.percentile(scores_d, 75) - np.percentile(scores_d, 25))
        })
    df_dist_stats = pd.DataFrame(dist_stats_rows)
    df_dist_stats.to_csv(out / "uncertainty/dispersion_scores_por_distrito.csv", index=False, encoding="utf-8-sig")
    print(f"Sensibilidad por distrito y umbrales guardada en {out / 'uncertainty'}")

    # 9. Control de Cierre y Manifiesto SHA-256 de Fase H
    control_cierre = {
        "estado_ejecucion": "completada",
        "phase": "fase_h",
        "mode": "validated",
        "model_frozen_source": f"{f_run}/final_model/final_validated_model.joblib",
        "holdout_frozen_source": g_run,
        "national_cells_inferred": n_cells,
        "total_national_area_km2": float(total_national_area / 1e6),
        "zones_prioritized_count": len(gdf_zones),
        "threshold_score_top01": threshold_01,
        "threshold_score_top05": threshold_05,
        "threshold_score_top10": threshold_10,
        "duration_seconds": float(time.time() - t_start),
        "reproducible": True,
        "scientific_integrity_statement": "Fase H representa el cierre analítico final. No se han reentrenado modelos ni reajustado umbrales tras conocer los resultados del holdout en Fase G."
    }
    write_json(out / "control_cierre.json", control_cierre)

    frozen_inputs = [
        model_path, meta_path,
        root / g_run / "predictions/holdout_predictions.parquet",
        root / g_run / "control_cierre.json",
        root / d_run / "calidad_y_soporte.parquet",
        root / d_run / "X_features.parquet",
        root / d_run / "grid_spec.json"
    ]
    write_json(out / "inputs.json", {"frozen_inputs": ev.records(root, frozen_inputs)})

    write_json(out / "environment.json", {
        n: importlib.metadata.version(n) for n in ("scikit-learn", "numpy", "pandas", "scipy", "rasterio", "geopandas", "shapely", "joblib", "pyarrow")
    })

    # Sellar manifiesto de salidas
    files = sorted(p for p in out.rglob("*") if p.is_file() and p.name != "outputs_manifest.json" and not p.name.startswith("."))
    manifest = ev.records(out, files)
    write_json(out / "outputs_manifest.json", manifest)
    ev.verify(out, manifest)
    print(f"\nFase H sellada con éxito: {len(manifest)} ficheros verificados con SHA-256.")

    # Actualizar puntero de ejecución actual de Fase H
    write_json(root / "reports/fase_h/current_run.json", {"run": out.relative_to(root).as_posix()})

    total_time = time.time() - t_start
    print(f"Ejecución completa de Fase H finalizada en {total_time:.2f}s.")
    return out.relative_to(root).as_posix()


if __name__ == "__main__":
    ejecutar_fase_h()
