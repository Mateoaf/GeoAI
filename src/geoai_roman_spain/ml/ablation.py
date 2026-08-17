"""
Estudio de Ablación de Coordenadas Espaciales (Coordinate Leakage / Memorization Test).
Evalúa formalmente la diferencia de generalización entre el Modelo Oficial (sin coordenadas)
y el Modelo con Coordenadas (experimento de memorización territorial).
"""
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

from .spatial_cv import create_spatial_folds, evaluate_fold_metrics

def run_coordinate_ablation_study(df: pd.DataFrame, target_col: str = 'target_class', n_splits: int = 5, seed: int = 42) -> dict:
    """
    Ejecuta el experimento comparativo de ablación espacial:
    - Modelo A (Científicamente Defendible): Excluye Coord_X y Coord_Y.
    - Modelo B (Experimento de Fuga): Incluye Coord_X y Coord_Y como predictores.
    """
    candidate_num_base = [
        'Real_Elevation_MDT_m', 'Real_Slope_Deg', 'Real_TPI_1km', 'Real_TRI_Roughness',
        'Real_IGME_Dist_Fault_m', 'Real_IGME_Dist_Contact_m', 'Real_IGME_Fault_Length_Density_5km'
    ]
    features_num_base = [c for c in candidate_num_base if c in df.columns and df[c].notna().sum() == len(df)]
    features_cat = ['Real_IGME_Lithology_General', 'Real_IGME_Era', 'Real_IGME_Dominio']
    
    # Modelo A: Sin coordenadas
    features_A = features_num_base + features_cat
    
    # Modelo B: Con coordenadas
    features_B = features_num_base + ['Coord_X', 'Coord_Y'] + features_cat
    
    folds = create_spatial_folds(df, n_splits=n_splits, seed=seed)
    
    def evaluate_feature_set(feat_num, feat_cat):
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), feat_num),
                ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), feat_cat)
            ]
        )
        
        oof_preds = np.zeros(len(df))
        fold_metrics_list = []
        
        for f in range(n_splits):
            train_idx = (folds != f)
            test_idx = (folds == f)
            
            X_train = df.loc[train_idx, feat_num + feat_cat]
            y_train = df.loc[train_idx, target_col].values
            X_test = df.loc[test_idx, feat_num + feat_cat]
            y_test = df.loc[test_idx, target_col].values
            
            pipe = Pipeline([
                ('prep', preprocessor),
                ('clf', LGBMClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=seed, verbose=-1))
            ])
            
            pipe.fit(X_train, y_train)
            probs = pipe.predict_proba(X_test)[:, 1]
            oof_preds[test_idx] = probs
            
            m = evaluate_fold_metrics(y_test, probs)
            fold_metrics_list.append(m)
            
        overall_metrics = evaluate_fold_metrics(df[target_col].values, oof_preds)
        return overall_metrics, fold_metrics_list
        
    metrics_A, folds_A = evaluate_feature_set(features_num_base, features_cat)
    metrics_B, folds_B = evaluate_feature_set(features_num_base + ['Coord_X', 'Coord_Y'], features_cat)
    
    return {
        "model_A_geoscientific_no_coords": {
            "overall": metrics_A,
            "folds": folds_A,
            "features_used": features_A
        },
        "model_B_with_coords_leakage": {
            "overall": metrics_B,
            "folds": folds_B,
            "features_used": features_B
        },
        "delta_roc_auc": round(metrics_B['roc_auc'] - metrics_A['roc_auc'], 4),
        "delta_pr_auc": round(metrics_B['pr_auc'] - metrics_A['pr_auc'], 4),
        "interpretation": (
            "Un incremento desproporcionado en el Modelo B confirma que las coordenadas X/Y "
            "inducen memorización espacial en lugar de aprendizaje de procesos geológicos."
        )
    }
