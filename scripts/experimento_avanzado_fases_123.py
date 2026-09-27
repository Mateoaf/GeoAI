#!/usr/bin/env python3
"""
Experimento Integral Fases 1, 2 y 3:
1. Modelos Avanzados de ML: XGBoost, LightGBM, Random Forest y Stacking Ensemble con Two-Step PU Learning.
2. Ingeniería de Variables Geológicas: Trampas estructurales, densidades de fractura y gradientes.
3. Separación por Tipología Metalogenética: Oro en Roca (Primario) vs Oro Aluvial (Secundario).
"""
import time
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.model_selection import KFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import xgboost as xgb
import lightgbm as lgb
import warnings
warnings.filterwarnings('ignore')

def main():
    print("=" * 80)
    print("EJECUTANDO EXPERIMENTO INTEGRAL: FASES 1, 2 Y 3")
    print("=" * 80)

    # 1. Cargar celdas elegibles y grid
    t0 = time.time()
    grid = pd.read_parquet(
        'reports/fase_d/20260927T135413_959884Z/calidad_y_soporte.parquet',
        columns=['cell_id', 'eligible_approved_features', 'row', 'col', 'x_center', 'y_center', 'land_area_m2']
    )
    grid_elig = grid[grid.eligible_approved_features == True].copy().reset_index(drop=True)
    elig_cells = set(grid_elig.cell_id)

    # Bloques espaciales (50 km) para validación espacial honesta
    grid_elig['block_x'] = (grid_elig.x_center // 50000).astype(int)
    grid_elig['block_y'] = (grid_elig.y_center // 50000).astype(int)
    grid_elig['block_id'] = grid_elig['block_x'].astype(str) + "_" + grid_elig['block_y'].astype(str)
    unique_blocks = grid_elig['block_id'].unique()
    rng = np.random.RandomState(42)
    rng.shuffle(unique_blocks)
    block_to_fold = {b: i % 5 for i, b in enumerate(unique_blocks)}
    grid_elig['spatial_fold'] = grid_elig['block_id'].map(block_to_fold)

    # 2. Cargar variables base y calcular nuevas variables geológicas (Fase 2)
    print("1. Cargando y creando variables geológicas avanzadas (Fase 2)...")
    coefs_v1 = pd.read_csv('reports/fase_h/20260927T142549_961719Z/interpretability/coeficientes_estandarizados.csv')
    base_features = coefs_v1['variable'].tolist()

    # Columnas estructurales extra presentes en X_features.parquet
    extra_cols = [
        'dens_aprox_falla_cartografiada_5000m_km_km2',
        'dens_aprox_contacto_intrusivo_cartografiada_5000m_km_km2',
        'dens_aprox_cabalgamiento_cartografiada_5000m_km_km2',
        'dens_aprox_cauce_5000m_km_km2'
    ]

    all_load_cols = list(set(['cell_id'] + base_features + extra_cols))
    X_raw = pd.read_parquet('reports/fase_d/20260927T135413_959884Z/X_features.parquet', columns=all_load_cols)
    X_elig = X_raw[X_raw.cell_id.isin(elig_cells)].set_index('cell_id').reindex(grid_elig.cell_id).fillna(0)

    # INGENIERÍA DE VARIABLES (FASE 2)
    # 2.1 Trampa Estructural: producto de proximidad a falla y proximidad a contacto intrusivo
    prox_falla = 1.0 / (1.0 + X_elig['dist_falla_cartografiada_m'] / 1000.0)
    prox_contacto = 1.0 / (1.0 + X_elig['dist_contacto_intrusivo_cartografiada_m'] / 1000.0)
    X_elig['trampa_falla_contacto'] = prox_falla * prox_contacto

    # 2.2 Trampa Aluvial: proximidad a cauce en zonas de pendiente baja / valle
    prox_cauce = 1.0 / (1.0 + X_elig['dist_cauce_m'] / 250.0)
    factor_valle = 1.0 / (1.0 + X_elig['pendiente_grados'] / 5.0)
    X_elig['trampa_aluvial_valle'] = prox_cauce * factor_valle

    # 2.3 Energía del Relieve / Gradiente Morfológico
    X_elig['energia_relieve'] = (X_elig['desv_elevacion_1000m_m'] * X_elig['pendiente_grados']) / 100.0

    # 2.4 Densidad estructural combinada (cizallas + contactos en 5 km)
    X_elig['densidad_estructural_total_5km'] = (
        X_elig['dens_aprox_falla_cartografiada_5000m_km_km2'] + 
        X_elig['dens_aprox_contacto_intrusivo_cartografiada_5000m_km_km2']
    )

    feature_cols = [c for c in X_elig.columns]
    print(f"Total predictores disponibles con ingeniería geológica: {len(feature_cols)}")

    # 3. Cargar etiquetas y separar por tipologías (Fase 3)
    print("\n2. Clasificando indicios por tipología metalogenética (Fase 3)...")
    df_b = pd.read_csv('data/review/revision_au_fase_b.csv')
    df_c = pd.read_csv('reports/fase_c/20260926T175114_459406Z/indicios_celda_cobertura.csv')
    merged = df_b.merge(df_c[['record_id', 'cell_id']], on='record_id', how='left')
    merged_elig = merged[(merged.estado_presencia.isin(['confirmada', 'pendiente'])) & (merged.cell_id.isin(elig_cells))]

    # Celdas por tipología
    pos_all = set(merged_elig.cell_id)
    pos_roca = set(merged_elig.loc[merged_elig.tipo_au_revisado == 'roca', 'cell_id'])
    pos_aluvial = set(merged_elig.loc[merged_elig.tipo_au_revisado == 'aluvial', 'cell_id'])

    print(f"Total Celdas P (Global): {len(pos_all)}")
    print(f"Total Celdas P (Oro en Roca / Primario): {len(pos_roca)}")
    print(f"Total Celdas P (Oro Aluvial / Placer): {len(pos_aluvial)}")

    # 4. Two-Step PU Learning para purificar pseudo-ausencias (Fase 1)
    print("\n3. Aplicando Two-Step PU Learning para purificar pseudo-ausencias (Fase 1)...")
    # Paso 1: Entrenar un LightGBM preliminar con muestra aleatoria
    pos_list_all = list(pos_all)
    neg_candidates = list(elig_cells - pos_all)
    rng_init = np.random.RandomState(42)
    sample_neg_init = rng_init.choice(neg_candidates, size=len(pos_list_all) * 5, replace=False)
    
    init_cells = pos_list_all + list(sample_neg_init)
    y_init = np.array([1] * len(pos_list_all) + [0] * len(sample_neg_init))
    X_init = X_elig.loc[init_cells].values
    
    prelim_clf = lgb.LGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.05, random_state=42, verbose=-1)
    prelim_clf.fit(X_init, y_init)
    
    # Predecir sobre todos los candidatos negativos
    X_neg_all = X_elig.loc[neg_candidates].values
    neg_scores = prelim_clf.predict_proba(X_neg_all)[:, 1]
    
    # Seleccionar como "pseudo-ausencias purificadas" (Reliable Negatives) solo celdas con score muy bajo (< 0.10)
    reliable_negatives = [neg_candidates[i] for i in range(len(neg_candidates)) if neg_scores[i] < 0.10]
    print(f"Candidatos negativos totales: {len(neg_candidates):,}")
    print(f"Pseudo-ausencias purificadas fiables (score < 0.10): {len(reliable_negatives):,} (excluidas {len(neg_candidates)-len(reliable_negatives):,} celdas sospechosas)")

    # 5. Función de evaluación por validación espacial y aleatoria
    def evaluate_models(pos_set, tag_name):
        print(f"\n--- Evaluando {tag_name} ({len(pos_set)} positivos) ---")
        pos_list = list(pos_set)
        
        # Muestrear pseudo-ausencias purificadas
        rng_local = np.random.RandomState(42)
        selected_neg = rng_local.choice(reliable_negatives, size=len(pos_list) * 3, replace=False).tolist()
        
        df_sub = pd.DataFrame({
            'cell_id': pos_list + selected_neg,
            'label': [1] * len(pos_list) + [0] * len(selected_neg)
        }).merge(grid_elig[['cell_id', 'spatial_fold']], on='cell_id')
        
        X_sub = X_elig.loc[df_sub.cell_id].values
        y_sub = df_sub.label.values
        sp_folds = df_sub.spatial_fold.values
        
        # K-Fold aleatorio
        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        rd_folds = np.zeros(len(y_sub), dtype=int)
        for f, (_, val_idx) in enumerate(kf.split(X_sub)):
            rd_folds[val_idx] = f
            
        models = {
            'Random Forest': lambda: RandomForestClassifier(n_estimators=100, max_depth=10, min_samples_leaf=5, random_state=42, n_jobs=-1),
            'XGBoost': lambda: xgb.XGBClassifier(n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42, eval_metric='logloss', n_jobs=-1),
            'LightGBM': lambda: lgb.LGBMClassifier(n_estimators=150, max_depth=6, learning_rate=0.05, random_state=42, verbose=-1, n_jobs=-1)
        }
        
        results = []
        for model_name, model_fn in models.items():
            # Spatial CV
            oof_sp = np.zeros(len(y_sub))
            for fold in range(5):
                tr_idx = np.where(sp_folds != fold)[0]
                va_idx = np.where(sp_folds == fold)[0]
                if len(np.unique(y_sub[va_idx])) < 2: continue
                clf = model_fn()
                clf.fit(X_sub[tr_idx], y_sub[tr_idx])
                oof_sp[va_idx] = clf.predict_proba(X_sub[va_idx])[:, 1]
                
            roc_sp = roc_auc_score(y_sub[oof_sp > 0], oof_sp[oof_sp > 0])
            pr_sp = average_precision_score(y_sub[oof_sp > 0], oof_sp[oof_sp > 0])
            
            # Random CV
            oof_rd = np.zeros(len(y_sub))
            for fold in range(5):
                tr_idx = np.where(rd_folds != fold)[0]
                va_idx = np.where(rd_folds == fold)[0]
                clf = model_fn()
                clf.fit(X_sub[tr_idx], y_sub[tr_idx])
                oof_rd[va_idx] = clf.predict_proba(X_sub[va_idx])[:, 1]
                
            roc_rd = roc_auc_score(y_sub, oof_rd)
            pr_rd = average_precision_score(y_sub, oof_rd)
            
            results.append({
                'Tipología': tag_name,
                'Modelo': model_name,
                'Spatial ROC-AUC': round(roc_sp, 4),
                'Spatial PR-AUC': round(pr_sp, 4),
                'Random ROC-AUC': round(roc_rd, 4),
                'Random PR-AUC': round(pr_rd, 4)
            })
        return pd.DataFrame(results)

    # Evaluar Global, Roca y Aluvial
    df_res_all = evaluate_models(pos_all, "Oro Global (787 indicios)")
    df_res_roca = evaluate_models(pos_roca, "Oro en Roca (Primario)")
    df_res_aluv = evaluate_models(pos_aluvial, "Oro Aluvial (Placer)")

    final_comparison = pd.concat([df_res_all, df_res_roca, df_res_aluv], ignore_index=True)
    print("\n" + "=" * 80)
    print("MATRIZ DE RESULTADOS FASES 1, 2 Y 3:")
    print("=" * 80)
    print(final_comparison.to_string(index=False))

    final_comparison.to_csv('reports/experimento_fases_123_resultados.csv', index=False)
    print(f"\nResultados guardados en reports/experimento_fases_123_resultados.csv")
    print(f"Ejecución completada en {time.time()-t0:.1f}s")

if __name__ == '__main__':
    main()
