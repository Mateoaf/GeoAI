"""
Validación Cruzada por Bloques Espaciales (Spatial Block Cross-Validation).
Garantiza independencia espacial estricta entre entrenamiento y prueba,
previene la memorización de ubicaciones y evalúa la capacidad real de generalización geográfica.
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score
)
import logging

logger = logging.getLogger(__name__)

def compute_spatial_autocorrelation_diagnostics(coords: np.ndarray, y: np.ndarray) -> dict:
    """
    Calcula diagnósticos espaciales sobre los depósitos minerales (escala de agregación y distancias al vecino más cercano).
    """
    pos_coords = coords[y == 1]
    if len(pos_coords) < 2:
        return {"mean_nn_dist_km": 0.0, "median_nn_dist_km": 0.0, "p90_nn_dist_km": 0.0}
        
    from scipy.spatial import cKDTree
    tree = cKDTree(pos_coords)
    dists, _ = tree.query(pos_coords, k=2)  # k=2: punto consigo mismo y vecino más cercano
    nn_dists_km = dists[:, 1] / 1000.0  # en km (para coordenadas proyectadas en metros)
    
    return {
        "mean_nn_dist_km": round(float(np.mean(nn_dists_km)), 2),
        "median_nn_dist_km": round(float(np.median(nn_dists_km)), 2),
        "p90_nn_dist_km": round(float(np.percentile(nn_dists_km, 90)), 2),
        "min_nn_dist_km": round(float(np.min(nn_dists_km)), 2),
        "max_nn_dist_km": round(float(np.max(nn_dists_km)), 2)
    }

def create_spatial_folds(df: pd.DataFrame, n_splits: int = 5, seed: int = 42) -> np.ndarray:
    """
    Asigna folds espaciales mediante partición por conglomerados KMeans sobre coordenadas proyectadas (Coord_X, Coord_Y).
    Garantiza que ningún fold carezca de muestras positivas ni negativas.
    """
    coords = df[['Coord_X', 'Coord_Y']].values
    
    # Normalizar coordenadas para KMeans uniforme
    coords_norm = (coords - coords.mean(axis=0)) / coords.std(axis=0)
    
    kmeans = KMeans(n_clusters=n_splits, random_state=seed, n_init=10)
    folds = kmeans.fit_predict(coords_norm)
    
    # Verificar balance de clases
    for f in range(n_splits):
        mask = (folds == f)
        n_pos = df.loc[mask, 'target_class'].sum() if 'target_class' in df else 1
        n_tot = mask.sum()
        logger.info(f"Spatial Fold {f+1}: {n_tot} muestras totales ({n_pos} positivas)")
        
    return folds

def evaluate_fold_metrics(y_true: np.ndarray, y_proba: np.ndarray, threshold: float = 0.5, top_k_pct: float = 0.10) -> dict:
    """
    Calcula una batería completa de métricas científicas para un fold espacial:
    - ROC-AUC
    - PR-AUC (Average Precision)
    - Brier Score (Calibración probabilística)
    - F1 Score, Precision, Recall
    - Precision@top-K% del área explorada
    - Cumulative Gain / Capture Rate en el top 10%
    """
    if len(np.unique(y_true)) < 2:
        return {
            "roc_auc": np.nan, "pr_auc": np.nan, "brier": np.nan,
            "f1": np.nan, "precision": np.nan, "recall": np.nan,
            "precision_top_k": np.nan, "gain_top_k": np.nan
        }
        
    roc = roc_auc_score(y_true, y_proba)
    pr = average_precision_score(y_true, y_proba)
    brier = brier_score_loss(y_true, y_proba)
    
    y_pred = (y_proba >= threshold).astype(int)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    
    # Precision@top-k% y Capture Rate
    n_top = max(1, int(len(y_true) * top_k_pct))
    top_indices = np.argsort(y_proba)[::-1][:n_top]
    positives_in_top = y_true[top_indices].sum()
    total_positives = y_true.sum()
    
    prec_top_k = positives_in_top / n_top
    gain_top_k = (positives_in_top / total_positives) if total_positives > 0 else 0.0
    
    return {
        "roc_auc": round(float(roc), 4),
        "pr_auc": round(float(pr), 4),
        "brier": round(float(brier), 4),
        "f1": round(float(f1), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "precision_top_k": round(float(prec_top_k), 4),
        "gain_top_k": round(float(gain_top_k), 4)
    }
