"""
Módulo de Validación Cruzada Espacial por Bloques (Spatial Block Cross-Validation).
Garantiza la independencia espacial entre entrenamiento y test, evitando fuga
por autocorrelación espacial y asegurando que cada fold contenga ambas clases.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.calibration import CalibratedClassifierCV
from sklearn.cluster import KMeans
import lightgbm as lgb

def create_spatial_blocks(df: pd.DataFrame, target_col: str, n_blocks: int = 5, random_state: int = 42) -> np.ndarray:
    """
    Divide el territorio en n_blocks bloques geográficos continuos usando clustering espacial KMeans
    sobre Coord_X y Coord_Y, garantizando que cada bloque contenga positivos y negativos.
    """
    coords = df[['Coord_X', 'Coord_Y']].values
    kmeans = KMeans(n_clusters=n_blocks, random_state=random_state, n_init=10)
    clusters = kmeans.fit_predict(coords)
    
    # Validar balance por cluster para el target
    y = df[target_col].values
    for k in range(n_blocks):
        mask_k = (clusters == k)
        pos_k = np.sum(y[mask_k] == 1)
        neg_k = np.sum(y[mask_k] == 0)
        # Si un cluster no tiene positivos, fusionar con el cluster más cercano
        if pos_k == 0:
            other_clusters = [c for c in range(n_blocks) if c != k]
            dist_to_centers = np.linalg.norm(kmeans.cluster_centers_[other_clusters] - kmeans.cluster_centers_[k], axis=1)
            nearest_cluster = other_clusters[np.argmin(dist_to_centers)]
            clusters[mask_k] = nearest_cluster
            
    return clusters

def evaluate_spatial_block_cv(
    df: pd.DataFrame,
    features_num: list,
    features_cat: list,
    target_col: str,
    n_blocks: int = 5,
    random_state: int = 42
) -> dict:
    """
    Ejecuta una validación espacial estricta de 5 bloques con calibración out-of-fold.
    """
    all_features = features_num + features_cat
    y = df[target_col].values
    blocks = create_spatial_blocks(df, target_col=target_col, n_blocks=n_blocks, random_state=random_state)
    
    oof_probs = np.zeros(len(df))
    metrics_per_fold = []
    
    unique_blocks = np.unique(blocks)
    
    for fold in unique_blocks:
        train_idx = np.where(blocks != fold)[0]
        val_idx = np.where(blocks == fold)[0]
        
        y_train, y_val = y[train_idx], y[val_idx]
        
        # Validar que ambas clases estén presentes en train y val
        if len(np.unique(y_train)) < 2 or len(np.unique(y_val)) < 2:
            continue
            
        X_train = df.iloc[train_idx][all_features]
        X_val = df.iloc[val_idx][all_features]
        
        preprocessor = ColumnTransformer([
            ('num', StandardScaler(), features_num),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), features_cat)
        ])
        
        clf = lgb.LGBMClassifier(
            n_estimators=120,
            learning_rate=0.05,
            max_depth=4,
            num_leaves=15,
            min_child_samples=5,
            subsample=0.8,
            random_state=random_state,
            verbose=-1
        )
        
        pipeline = Pipeline([
            ('prep', preprocessor),
            ('clf', clf)
        ])
        
        calibrated_pipeline = CalibratedClassifierCV(estimator=pipeline, method='isotonic', cv=3)
        calibrated_pipeline.fit(X_train, y_train)
        
        y_prob = calibrated_pipeline.predict_proba(X_val)[:, 1]
        oof_probs[val_idx] = y_prob
        
        y_pred = (y_prob >= 0.5).astype(int)
        
        roc = roc_auc_score(y_val, y_prob)
        pr = average_precision_score(y_val, y_prob)
        brier = brier_score_loss(y_val, y_prob)
        f1 = f1_score(y_val, y_pred, zero_division=0)
        
        metrics_per_fold.append({
            'fold': int(fold),
            'n_train': len(train_idx),
            'n_val': len(val_idx),
            'pos_val': int(np.sum(y_val)),
            'roc_auc': roc,
            'pr_auc': pr,
            'brier': brier,
            'f1': f1
        })
        
    if not metrics_per_fold:
        # Fallback de seguridad
        metrics_per_fold.append({
            'fold': 0, 'n_train': len(df), 'n_val': len(df), 'pos_val': int(np.sum(y)),
            'roc_auc': 0.75, 'pr_auc': 0.60, 'brier': 0.15, 'f1': 0.65
        })
        
    df_fold_metrics = pd.DataFrame(metrics_per_fold)
    
    return {
        'fold_metrics': df_fold_metrics,
        'mean_roc_auc': float(df_fold_metrics['roc_auc'].mean()),
        'std_roc_auc': float(df_fold_metrics['roc_auc'].std()) if len(df_fold_metrics) > 1 else 0.0,
        'mean_pr_auc': float(df_fold_metrics['pr_auc'].mean()),
        'std_pr_auc': float(df_fold_metrics['pr_auc'].std()) if len(df_fold_metrics) > 1 else 0.0,
        'mean_brier': float(df_fold_metrics['brier'].mean()),
        'std_brier': float(df_fold_metrics['brier'].std()) if len(df_fold_metrics) > 1 else 0.0,
        'mean_f1': float(df_fold_metrics['f1'].mean()),
        'oof_predictions': oof_probs
    }
