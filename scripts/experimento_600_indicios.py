#!/usr/bin/env python3
"""
Experimento 600 Indicios:
Comparativa cuantitativa entre el modelo oficial v1.0 (190 confirmados, 131 celdas P)
y el modelo ampliado con los ~600 indicios pendientes (787 indicios, 664 celdas P).

Evalúa:
1. Validación espacial por bloques (honesta, sin autocorrelación).
2. Validación aleatoria K-Fold (estándar ingenua, con fuga espacial).
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.model_selection import KFold
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import time

def main():
    print("=" * 80)
    print("EJECUTANDO EXPERIMENTO: MODELO CON 190 VS 787 INDICIOS")
    print("=" * 80)

    # 1. Cargar celdas elegibles y covariables
    t0 = time.time()
    print("Cargando datos territoriales y covariables...")
    grid = pd.read_parquet(
        'reports/fase_d/20260927T135413_959884Z/calidad_y_soporte.parquet',
        columns=['cell_id', 'eligible_approved_features', 'x_center', 'y_center']
    )
    grid_elig = grid[grid.eligible_approved_features == True].copy()
    elig_cells = set(grid_elig.cell_id)

    coefs = pd.read_csv('reports/fase_h/20260927T142549_961719Z/interpretability/coeficientes_estandarizados.csv')
    features = coefs['variable'].tolist()

    X_all = pd.read_parquet('reports/fase_d/20260927T135413_959884Z/X_features.parquet', columns=['cell_id'] + features)
    X_elig = X_all[X_all.cell_id.isin(elig_cells)].set_index('cell_id').reindex(grid_elig.cell_id)

    # 2. Cargar etiquetas
    df_b = pd.read_csv('data/review/revision_au_fase_b.csv')
    df_c = pd.read_csv('reports/fase_c/20260926T175114_459406Z/indicios_celda_cobertura.csv')
    merged = df_b.merge(df_c[['record_id', 'cell_id']], on='record_id', how='left')

    pos_v1 = set(merged.loc[(merged.estado_presencia == 'confirmada') & (merged.cell_id.isin(elig_cells)), 'cell_id'])
    pos_all = set(merged.loc[(merged.estado_presencia.isin(['confirmada', 'pendiente'])) & (merged.cell_id.isin(elig_cells)), 'cell_id'])

    print(f"Celdas elegibles totales: {len(X_elig):,}")
    print(f"Celdas P Oficial v1.0 (190 confirmados): {len(pos_v1)}")
    print(f"Celdas P Experimental (787 indicios): {len(pos_all)}")
    print(f"Tiempo de carga: {time.time()-t0:.1f}s\n")

    # 3. Bloques espaciales (50 km) para validación espacial
    grid_elig['block_x'] = (grid_elig.x_center // 50000).astype(int)
    grid_elig['block_y'] = (grid_elig.y_center // 50000).astype(int)
    grid_elig['block_id'] = grid_elig['block_x'].astype(str) + "_" + grid_elig['block_y'].astype(str)
    
    unique_blocks = grid_elig['block_id'].unique()
    rng = np.random.RandomState(42)
    rng.shuffle(unique_blocks)
    block_to_fold = {b: i % 5 for i, b in enumerate(unique_blocks)}
    grid_elig['spatial_fold'] = grid_elig['block_id'].map(block_to_fold)

    # Función para muestrear PU (ratio 3:1 de pseudo-ausencias)
    def create_pu_dataset(pos_set, ratio=3, seed=42):
        pos_list = list(pos_set)
        neg_candidates = list(elig_cells - pos_set)
        rng_local = np.random.RandomState(seed)
        neg_sample = rng_local.choice(neg_candidates, size=len(pos_list) * ratio, replace=False).tolist()
        
        df_sample = pd.DataFrame({
            'cell_id': pos_list + neg_sample,
            'label': [1] * len(pos_list) + [0] * len(neg_sample)
        })
        df_sample = df_sample.merge(grid_elig[['cell_id', 'spatial_fold', 'x_center', 'y_center']], on='cell_id')
        X_sample = X_elig.loc[df_sample.cell_id].values
        y_sample = df_sample.label.values
        return df_sample, X_sample, y_sample

    def evaluate_cv(X_mat, y_vec, folds, model_type='logistic'):
        oof_preds = np.zeros(len(y_vec))
        for fold in range(5):
            train_idx = np.where(folds != fold)[0]
            val_idx = np.where(folds == fold)[0]
            
            if len(np.unique(y_vec[val_idx])) < 2:
                continue
                
            if model_type == 'logistic':
                clf = Pipeline([
                    ('imputer', SimpleImputer(strategy='median')),
                    ('scaler', StandardScaler()),
                    ('lr', LogisticRegression(C=0.1, penalty='l2', max_iter=500, random_state=42))
                ])
            elif model_type == 'rf':
                clf = Pipeline([
                    ('imputer', SimpleImputer(strategy='median')),
                    ('rf', RandomForestClassifier(n_estimators=100, max_depth=10, min_samples_leaf=5, random_state=42, n_jobs=-1))
                ])
            
            clf.fit(X_mat[train_idx], y_vec[train_idx])
            oof_preds[val_idx] = clf.predict_proba(X_mat[val_idx])[:, 1]
            
        valid = oof_preds > 0
        roc = roc_auc_score(y_vec[valid], oof_preds[valid])
        pr = average_precision_score(y_vec[valid], oof_preds[valid])
        return roc, pr

    results = []

    for name, p_set in [('Oficial v1.0 (131 P)', pos_v1), ('Experimental (664 P - Todos)', pos_all)]:
        df_s, X_s, y_s = create_pu_dataset(p_set, ratio=3, seed=42)
        
        # 1. Validación Espacial (Spatial Blocks 50 km)
        roc_sp_lr, pr_sp_lr = evaluate_cv(X_s, y_s, df_s.spatial_fold.values, model_type='logistic')
        roc_sp_rf, pr_sp_rf = evaluate_cv(X_s, y_s, df_s.spatial_fold.values, model_type='rf')
        
        # 2. Validación Aleatoria K-Fold (Sin bloqueo espacial - Fuga de datos)
        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        rand_folds = np.zeros(len(y_s), dtype=int)
        for f, (_, val_idx) in enumerate(kf.split(X_s)):
            rand_folds[val_idx] = f
            
        roc_rd_lr, pr_rd_lr = evaluate_cv(X_s, y_s, rand_folds, model_type='logistic')
        roc_rd_rf, pr_rd_rf = evaluate_cv(X_s, y_s, rand_folds, model_type='rf')
        
        results.append({
            'Configuración': name,
            'Total P': len(p_set),
            'Total U (1:3)': len(p_set) * 3,
            'Spatial ROC-AUC (LR)': f"{roc_sp_lr:.4f}",
            'Spatial ROC-AUC (RF)': f"{roc_sp_rf:.4f}",
            'Random ROC-AUC (LR - Fuga)': f"{roc_rd_lr:.4f}",
            'Random ROC-AUC (RF - Fuga)': f"{roc_rd_rf:.4f}",
        })

    res_df = pd.DataFrame(results)
    print("\n" + "=" * 80)
    print("RESULTADOS COMPARATIVOS EXPERIMENTALES:")
    print("=" * 80)
    print(res_df.to_string(index=False))
    
    res_df.to_csv('reports/comparativa_experimento_600_indicios.csv', index=False)
    print(f"\nResultados guardados en reports/comparativa_experimento_600_indicios.csv")

if __name__ == '__main__':
    main()
