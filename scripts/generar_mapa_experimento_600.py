#!/usr/bin/env python3
"""
Generador del Mapa Nacional y Productos Geoespaciales para el Experimento de 600 Indicios (787 en total).
Entrena con 664 celdas positivas y genera la cartografía completa en reports/experimento_600_indicios/.
"""
from pathlib import Path
import json
import time
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import Affine
from scipy.ndimage import label as nd_label
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib

ROOT = Path(__file__).resolve().parents[1]

def run():
    print("=" * 80)
    print("GENERANDO MAPA NACIONAL Y PRODUCTOS: EXPERIMENTO 787 INDICIOS")
    print("=" * 80)

    out_dir = ROOT / 'reports/experimento_600_indicios'
    maps_dir = out_dir / 'maps'
    targets_dir = out_dir / 'targets'
    interp_dir = out_dir / 'interpretability'
    for d in [maps_dir, targets_dir, interp_dir]:
        d.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    print("1. Cargando datos territoriales y covariables...")
    grid = pd.read_parquet(
        ROOT / 'reports/fase_d/20260927T135413_959884Z/calidad_y_soporte.parquet',
        columns=['cell_id', 'eligible_approved_features', 'row', 'col', 'x_center', 'y_center', 'land_area_m2']
    )
    grid_elig = grid[grid.eligible_approved_features == True].copy().reset_index(drop=True)
    elig_cells = set(grid_elig.cell_id)

    coefs_v1 = pd.read_csv(ROOT / 'reports/fase_h/20260927T142549_961719Z/interpretability/coeficientes_estandarizados.csv')
    features = coefs_v1['variable'].tolist()

    X_all = pd.read_parquet(ROOT / 'reports/fase_d/20260927T135413_959884Z/X_features.parquet', columns=['cell_id'] + features)
    X_elig = X_all[X_all.cell_id.isin(elig_cells)].set_index('cell_id').reindex(grid_elig.cell_id)

    # 2. Cargar etiquetas
    df_b = pd.read_csv(ROOT / 'data/review/revision_au_fase_b.csv')
    df_c = pd.read_csv(ROOT / 'reports/fase_c/20260926T175114_459406Z/indicios_celda_cobertura.csv')
    merged = df_b.merge(df_c[['record_id', 'cell_id']], on='record_id', how='left')

    pos_all = set(merged.loc[(merged.estado_presencia.isin(['confirmada', 'pendiente'])) & (merged.cell_id.isin(elig_cells)), 'cell_id'])
    print(f"Celdas elegibles totales: {len(X_elig):,}")
    print(f"Celdas positivas experimentales (787 indicios): {len(pos_all):,}")

    # 3. Construir muestra de entrenamiento PU (ratio 1:3)
    pos_list = list(pos_all)
    neg_candidates = list(elig_cells - pos_all)
    rng = np.random.RandomState(42)
    neg_sample = rng.choice(neg_candidates, size=len(pos_list) * 3, replace=False).tolist()

    train_cells = pos_list + neg_sample
    y_train = np.array([1] * len(pos_list) + [0] * len(neg_sample))
    X_train = X_elig.loc[train_cells].values

    # 4. Ajustar Modelos (Random Forest y Regresión Logística)
    print("\n2. Entrenando modelos sobre las 664 celdas P + 1.992 pseudo-ausencias...")
    # Pipeline Regresión Logística
    pipe_lr = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
        ('lr', LogisticRegression(C=0.1, penalty='l2', max_iter=500, random_state=42))
    ])
    pipe_lr.fit(X_train, y_train)

    # Pipeline Random Forest
    pipe_rf = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('rf', RandomForestClassifier(n_estimators=100, max_depth=10, min_samples_leaf=5, random_state=42, n_jobs=-1))
    ])
    pipe_rf.fit(X_train, y_train)

    # Guardar modelos
    joblib.dump(pipe_lr, out_dir / 'modelo_experimental_logistic.joblib')
    joblib.dump(pipe_rf, out_dir / 'modelo_experimental_random_forest.joblib')

    # 5. Predecir sobre todas las 478.443 celdas elegibles
    print("\n3. Prediciendo scores de favorabilidad para las 478.443 celdas...")
    X_mat_all = X_elig.values
    scores_lr = pipe_lr.predict_proba(X_mat_all)[:, 1]
    scores_rf = pipe_rf.predict_proba(X_mat_all)[:, 1]

    grid_elig['score_lr'] = scores_lr
    grid_elig['score_rf'] = scores_rf

    # Percentil territorial (usando Random Forest como score principal)
    scores_rf_series = pd.Series(scores_rf)
    pcts_rf = scores_rf_series.rank(pct=True).values * 100.0
    grid_elig['percentil_rf'] = pcts_rf

    # Umbrales Top 10, 5, 1%
    th_top10 = float(np.percentile(scores_rf, 90))
    th_top05 = float(np.percentile(scores_rf, 95))
    th_top01 = float(np.percentile(scores_rf, 99))

    print(f"Umbrales RF: Top 10% >= {th_top10:.4f} | Top 5% >= {th_top05:.4f} | Top 1% >= {th_top01:.4f}")

    # Bandas prioritarias: 1: Top 1%, 2: Top 1-5%, 3: Top 5-10%, 0: Fondo
    bandas = np.zeros(len(grid_elig), dtype=np.uint8)
    bandas[scores_rf >= th_top10] = 3
    bandas[scores_rf >= th_top05] = 2
    bandas[scores_rf >= th_top01] = 1
    grid_elig['banda_prioridad'] = bandas

    # 6. Exportar GeoParquet
    parquet_path = maps_dir / 'mapa_nacional_prospectividad_experimental.geoparquet'
    grid_elig[['cell_id', 'row', 'col', 'x_center', 'y_center', 'score_lr', 'score_rf', 'percentil_rf', 'banda_prioridad', 'land_area_m2']].to_parquet(parquet_path, index=False)
    print(f"GeoParquet exportado: {parquet_path.relative_to(ROOT)}")

    # 7. Generar y exportar Rásteres COG
    print("\n4. Generando rásteres cartográficos COG (1.100 x 910 píxeles)...")
    profile = {
        'driver': 'GTiff',
        'dtype': 'float32',
        'nodata': -9999.0,
        'width': 1100,
        'height': 910,
        'count': 1,
        'crs': 'EPSG:25830',
        'transform': Affine(1000.0, 0.0, -50000.0, 0.0, -1000.0, 4860000.0),
        'blockxsize': 512,
        'blockysize': 512,
        'tiled': True,
        'compress': 'deflate'
    }

    # Matrices ráster
    arr_score_rf = np.full((910, 1100), -9999.0, dtype=np.float32)
    arr_score_lr = np.full((910, 1100), -9999.0, dtype=np.float32)
    arr_pct_rf = np.full((910, 1100), -9999.0, dtype=np.float32)
    arr_bandas = np.full((910, 1100), 255, dtype=np.uint8)

    rows = grid_elig.row.values
    cols = grid_elig.col.values
    arr_score_rf[rows, cols] = scores_rf
    arr_score_lr[rows, cols] = scores_lr
    arr_pct_rf[rows, cols] = pcts_rf
    arr_bandas[rows, cols] = bandas

    # Escribir TIFs
    with rasterio.open(maps_dir / 'mapa_nacional_favorabilidad_score_rf.tif', 'w', **profile) as dst:
        dst.write(arr_score_rf, 1)

    with rasterio.open(maps_dir / 'mapa_nacional_favorabilidad_score_lr.tif', 'w', **profile) as dst:
        dst.write(arr_score_lr, 1)

    with rasterio.open(maps_dir / 'mapa_nacional_percentil_rf.tif', 'w', **profile) as dst:
        dst.write(arr_pct_rf, 1)

    profile_bandas = profile.copy()
    profile_bandas['dtype'] = 'uint8'
    profile_bandas['nodata'] = 255
    with rasterio.open(maps_dir / 'mapa_nacional_bandas_prioritarias_rf.tif', 'w', **profile_bandas) as dst:
        dst.write(arr_bandas, 1)

    print("Rásteres COG guardados con éxito en reports/experimento_600_indicios/maps/")

    # 8. Delineación de Zonas Prioritarias (Top 5%)
    print("\n5. Delineando zonas de prospectividad conectadas (Top 5%)...")
    mask_top05 = (arr_bandas == 1) | (arr_bandas == 2)
    labeled_matrix, num_features = nd_label(mask_top05, structure=np.ones((3, 3)))
    print(f"Total de zonas conexas identificadas: {num_features:,}")

    # Extraer métricas por zona
    zone_stats = []
    cell_zone_labels = labeled_matrix[rows, cols]
    grid_elig['zone_id'] = cell_zone_labels

    for zid, group in grid_elig[grid_elig.zone_id > 0].groupby('zone_id'):
        top1_count = (group.banda_prioridad == 1).sum()
        zone_stats.append({
            'zone_id': f"zona_exp_{zid:04d}",
            'superficie_km2': len(group),
            'prioridad': 'Top 1%' if top1_count > 0 else 'Top 1-5%',
            'score_max': round(float(group.score_rf.max()), 4),
            'score_mean': round(float(group.score_rf.mean()), 4),
            'celdas_top1': int(top1_count),
            'x_center_mean': round(float(group.x_center.mean()), 1),
            'y_center_mean': round(float(group.y_center.mean()), 1)
        })

    df_zones = pd.DataFrame(zone_stats).sort_values(by=['score_max', 'superficie_km2'], ascending=[False, False]).reset_index(drop=True)
    df_zones['ranking'] = np.arange(1, len(df_zones) + 1)
    zones_path = targets_dir / 'zonas_prospectividad_ranking_rf.csv'
    df_zones.to_csv(zones_path, index=False)
    print(f"Ranking de {len(df_zones):,} zonas guardado en: {zones_path.relative_to(ROOT)}")

    # 9. Interpretabilidad: Importancia de variables
    print("\n6. Analizando interpretabilidad del modelo experimental...")
    rf_est = pipe_rf.named_steps['rf']
    importances = pd.DataFrame({
        'variable': features,
        'importancia_rf': rf_est.feature_importances_
    }).sort_values(by='importancia_rf', ascending=False).reset_index(drop=True)
    importances.to_csv(interp_dir / 'importancia_variables_rf.csv', index=False)

    lr_est = pipe_lr.named_steps['lr']
    coef_df = pd.DataFrame({
        'variable': features,
        'coeficiente_estandarizado': lr_est.coef_[0],
        'odds_ratio_1std': np.exp(lr_est.coef_[0])
    }).sort_values(by='coeficiente_estandarizado', ascending=False).reset_index(drop=True)
    coef_df.to_csv(interp_dir / 'coeficientes_estandarizados_lr.csv', index=False)

    # 10. Resumen de Métricas
    metrics_summary = {
        'total_indicios_bdmin': len(merged),
        'indicios_confirmados': 190,
        'indicios_pendientes_incorporados': 597,
        'total_indicios_utilizados': len(merged[merged.estado_presencia.isin(['confirmada', 'pendiente'])]),
        'celdas_positivas_peninsulares': len(pos_all),
        'celdas_pseudoausencias': len(neg_sample),
        'ratio_pu': 3,
        'threshold_top10': th_top10,
        'threshold_top05': th_top05,
        'threshold_top01': th_top01,
        'total_zonas_prioritarias': len(df_zones),
        'top_5_variables_rf': importances.head(5).to_dict(orient='records'),
        'top_5_coeficientes_positivos_lr': coef_df.head(5).to_dict(orient='records'),
        'top_5_coeficientes_negativos_lr': coef_df.tail(5).to_dict(orient='records'),
        'duracion_segundos': round(time.time() - t0, 1)
    }

    with open(out_dir / 'metricas_resumen_experimento.json', 'w', encoding='utf-8') as f:
        json.dump(metrics_summary, f, indent=2, ensure_ascii=False)

    print(f"\nResumen de métricas guardado en: {out_dir / 'metricas_resumen_experimento.json'}")
    print(f"Todo el proceso completado con éxito en {time.time()-t0:.1f} segundos.")

if __name__ == '__main__':
    run()
