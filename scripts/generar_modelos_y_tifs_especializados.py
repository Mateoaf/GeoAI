#!/usr/bin/env python3
"""
Generador de Mapas Ráster Especializados (Roca, Aluvial y Global v2):
Entrena los modelos finales especializados de LightGBM/XGBoost y exporta los COGs ráster
a reports/experimento_600_indicios/maps/ para su consumo directo en apps/api y apps/web.
"""
from pathlib import Path
import time
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import Affine
import lightgbm as lgb
import xgboost as xgb
import joblib

ROOT = Path(__file__).resolve().parents[1]

def main():
    print("=" * 80)
    print("GENERANDO MODELOS Y MAPAS RÁSTER ESPECIALIZADOS (ROCA, ALUVIAL, GLOBAL V2)")
    print("=" * 80)

    out_dir = ROOT / 'reports/experimento_600_indicios'
    maps_dir = out_dir / 'maps'
    maps_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    # 1. Cargar celdas elegibles
    print("1. Cargando rejilla territorial y covariables geológicas...")
    grid = pd.read_parquet(
        ROOT / 'reports/fase_d/20260927T135413_959884Z/calidad_y_soporte.parquet',
        columns=['cell_id', 'eligible_approved_features', 'row', 'col', 'x_center', 'y_center']
    )
    grid_elig = grid[grid.eligible_approved_features == True].copy().reset_index(drop=True)
    elig_cells = set(grid_elig.cell_id)

    coefs_v1 = pd.read_csv(ROOT / 'reports/fase_h/20260927T142549_961719Z/interpretability/coeficientes_estandarizados.csv')
    base_features = coefs_v1['variable'].tolist()

    extra_cols = [
        'dens_aprox_falla_cartografiada_5000m_km_km2',
        'dens_aprox_contacto_intrusivo_cartografiada_5000m_km_km2',
        'dens_aprox_cabalgamiento_cartografiada_5000m_km_km2',
        'dens_aprox_cauce_5000m_km_km2'
    ]

    all_cols = list(set(['cell_id'] + base_features + extra_cols))
    X_raw = pd.read_parquet(ROOT / 'reports/fase_d/20260927T135413_959884Z/X_features.parquet', columns=all_cols)
    X_elig = X_raw[X_raw.cell_id.isin(elig_cells)].set_index('cell_id').reindex(grid_elig.cell_id).fillna(0)

    # Variables geológicas avanzadas
    X_elig['trampa_falla_contacto'] = (
        (1.0 / (1.0 + X_elig['dist_falla_cartografiada_m'] / 1000.0)) *
        (1.0 / (1.0 + X_elig['dist_contacto_intrusivo_cartografiada_m'] / 1000.0))
    )
    X_elig['trampa_aluvial_valle'] = (
        (1.0 / (1.0 + X_elig['dist_cauce_m'] / 250.0)) *
        (1.0 / (1.0 + X_elig['pendiente_grados'] / 5.0))
    )
    X_elig['energia_relieve'] = (X_elig['desv_elevacion_1000m_m'] * X_elig['pendiente_grados']) / 100.0
    X_elig['densidad_estructural_total_5km'] = (
        X_elig['dens_aprox_falla_cartografiada_5000m_km_km2'] + 
        X_elig['dens_aprox_contacto_intrusivo_cartografiada_5000m_km_km2']
    )

    feature_cols = [c for c in X_elig.columns]
    print(f"Total variables empleadas: {len(feature_cols)}")

    # 2. Cargar etiquetas
    df_b = pd.read_csv(ROOT / 'data/review/revision_au_fase_b.csv')
    df_c = pd.read_csv(ROOT / 'reports/fase_c/20260926T175114_459406Z/indicios_celda_cobertura.csv')
    merged = df_b.merge(df_c[['record_id', 'cell_id']], on='record_id', how='left')
    merged_elig = merged[(merged.estado_presencia.isin(['confirmada', 'pendiente'])) & (merged.cell_id.isin(elig_cells))]

    pos_all = list(set(merged_elig.cell_id))
    pos_roca = list(set(merged_elig.loc[merged_elig.tipo_au_revisado == 'roca', 'cell_id']))
    pos_aluvial = list(set(merged_elig.loc[merged_elig.tipo_au_revisado == 'aluvial', 'cell_id']))

    # 3. Reliable Negatives (Two-Step PU Learning)
    print("\n2. Extrayendo pseudo-ausencias purificadas (Reliable Negatives)...")
    neg_candidates = list(elig_cells - set(pos_all))
    sample_neg_init = np.random.RandomState(42).choice(neg_candidates, size=len(pos_all) * 5, replace=False)
    
    init_cells = pos_all + list(sample_neg_init)
    y_init = np.array([1] * len(pos_all) + [0] * len(sample_neg_init))
    
    prelim = lgb.LGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.05, random_state=42, verbose=-1, n_jobs=-1)
    prelim.fit(X_elig.loc[init_cells].values, y_init)
    neg_scores = prelim.predict_proba(X_elig.loc[neg_candidates].values)[:, 1]
    
    reliable_negatives = [neg_candidates[i] for i in range(len(neg_candidates)) if neg_scores[i] < 0.10]
    print(f"Total Reliable Negatives purificados: {len(reliable_negatives):,}")

    X_mat_all = X_elig.values

    # 4. Entrenar y predecir los 3 modelos
    def train_and_predict(pos_subset, name, n_estimators=200):
        print(f"\nEntrenando modelo especializado: {name} ({len(pos_subset)} positivos)...")
        rng = np.random.RandomState(42)
        sample_neg = rng.choice(reliable_negatives, size=len(pos_subset) * 3, replace=False).tolist()
        
        cells = pos_subset + sample_neg
        y = np.array([1] * len(pos_subset) + [0] * len(sample_neg))
        X = X_elig.loc[cells].values
        
        clf = lgb.LGBMClassifier(n_estimators=n_estimators, max_depth=6, learning_rate=0.04, random_state=42, verbose=-1, n_jobs=-1)
        clf.fit(X, y)
        scores = clf.predict_proba(X_mat_all)[:, 1]
        return clf, scores

    # 4.1 Modelo Oro Global v2
    model_global, scores_global = train_and_predict(pos_all, "Oro Global v2 (787 indicios)")
    # 4.2 Modelo Oro en Roca (Primario)
    model_roca, scores_roca = train_and_predict(pos_roca, "Oro en Roca (Primario / Orogénico)")
    # 4.3 Modelo Oro Aluvial (Placeres)
    model_aluvial, scores_aluvial = train_and_predict(pos_aluvial, "Oro Aluvial (Placeres Fluviales)")

    # Guardar estimadores
    joblib.dump(model_global, out_dir / 'modelo_lgb_global_v2.joblib')
    joblib.dump(model_roca, out_dir / 'modelo_lgb_oro_roca.joblib')
    joblib.dump(model_aluvial, out_dir / 'modelo_lgb_oro_aluvial.joblib')

    # 5. Generar Rásteres COG
    print("\n3. Escribiendo rásteres COG en EPSG:25830...")
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

    rows = grid_elig.row.values
    cols = grid_elig.col.values

    tifs = {
        'mapa_nacional_oro_global_score.tif': scores_global,
        'mapa_nacional_oro_roca_score.tif': scores_roca,
        'mapa_nacional_oro_aluvial_score.tif': scores_aluvial
    }

    for filename, score_arr in tifs.items():
        arr = np.full((910, 1100), -9999.0, dtype=np.float32)
        arr[rows, cols] = score_arr
        filepath = maps_dir / filename
        with rasterio.open(filepath, 'w', **profile) as dst:
            dst.write(arr, 1)
        print(f"  -> Guardado: {filepath.relative_to(ROOT)} (Score medio: {score_arr.mean():.4f}, máx: {score_arr.max():.4f})")

    print(f"\n¡Todos los modelos y rásteres especializados completados en {time.time()-t0:.1f}s!")

if __name__ == '__main__':
    main()
