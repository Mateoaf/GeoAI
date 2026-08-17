"""
Módulo de Ablation Test de Coordenadas (Coordinate Ablation Study).
Compara rigurosamente el rendimiento de los modelos con y sin coordenadas métricas (Coord_X, Coord_Y)
para verificar que el sistema aprende firmas geológicas transferibles y no memorización espacial.
"""
import pandas as pd
from .spatial_cv import evaluate_spatial_block_cv

def run_coordinate_ablation_study(
    df: pd.DataFrame,
    features_num_base: list,
    features_cat: list,
    target_col: str,
    n_blocks: int = 5,
    random_state: int = 42
) -> dict:
    """
    Ejecuta el experimento de ablación:
    - Modelo A: Incluye Coord_X y Coord_Y
    - Modelo B: Sin coordenadas (solo características geocientíficas intrínsecas)
    """
    # Modelo A: Con coordenadas
    features_num_with_coords = list(set(features_num_base + ['Coord_X', 'Coord_Y']))
    res_a = evaluate_spatial_block_cv(
        df=df,
        features_num=features_num_with_coords,
        features_cat=features_cat,
        target_col=target_col,
        n_blocks=n_blocks,
        random_state=random_state
    )
    
    # Modelo B: Sin coordenadas
    features_num_no_coords = [f for f in features_num_base if f not in ['Coord_X', 'Coord_Y']]
    res_b = evaluate_spatial_block_cv(
        df=df,
        features_num=features_num_no_coords,
        features_cat=features_cat,
        target_col=target_col,
        n_blocks=n_blocks,
        random_state=random_state
    )
    
    summary = [
        {
            'Configuracion': 'Modelo A (Con Coordenadas XY)',
            'N_Features': len(features_num_with_coords) + len(features_cat),
            'Spatial_ROC_AUC': f"{res_a['mean_roc_auc']:.4f} ± {res_a['std_roc_auc']:.4f}",
            'Spatial_PR_AUC': f"{res_a['mean_pr_auc']:.4f} ± {res_a['std_pr_auc']:.4f}",
            'Brier_Score': f"{res_a['mean_brier']:.4f} ± {res_a['std_brier']:.4f}",
            'F1_Score': f"{res_a['mean_f1']:.4f}"
        },
        {
            'Configuracion': 'Modelo B (Sin Coordenadas - Geología Pura)',
            'N_Features': len(features_num_no_coords) + len(features_cat),
            'Spatial_ROC_AUC': f"{res_b['mean_roc_auc']:.4f} ± {res_b['std_roc_auc']:.4f}",
            'Spatial_PR_AUC': f"{res_b['mean_pr_auc']:.4f} ± {res_b['std_pr_auc']:.4f}",
            'Brier_Score': f"{res_b['mean_brier']:.4f} ± {res_b['std_brier']:.4f}",
            'F1_Score': f"{res_b['mean_f1']:.4f}"
        }
    ]
    
    return {
        'summary_df': pd.DataFrame(summary),
        'res_with_coords': res_a,
        'res_no_coords': res_b
    }
