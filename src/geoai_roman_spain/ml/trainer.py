"""
Entrenador de Modelos de Producción GeoAI v2.
Entrena mediante Spatial Block CV, calibra out-of-fold y serializa los artefactos finales.
"""
from pathlib import Path
import logging
import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.isotonic import IsotonicRegression

from .spatial_cv import create_spatial_folds, evaluate_fold_metrics
from .calibration import evaluate_calibration_methods

logger = logging.getLogger(__name__)

COMMODITY_SPECS = [
    {"target_col": "flag_Au", "name": "Au_Oro", "label": "Oro"},
    {"target_col": "flag_Cu", "name": "Cu_Cobre", "label": "Cobre"},
    {"target_col": "flag_Ag", "name": "Ag_Plata", "label": "Plata"},
    {"target_col": "flag_Pb", "name": "Pb_Plomo", "label": "Plomo"}
]

def train_production_models_v2(df: pd.DataFrame, output_dir: Path, n_splits: int = 5, seed: int = 42) -> dict:
    """
    Entrena, valida espacialmente y serializa los 4 modelos de producción v2.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    features_num = [
        'Real_Elevation_MDT_m', 'Real_Slope_Deg', 'Real_TPI_1km', 'Real_TRI_Roughness',
        'Real_IGME_Dist_Fault_m', 'Real_IGME_Dist_Contact_m', 'Real_IGME_Fault_Length_Density_5km'
    ]
    features_cat = ['Real_IGME_Lithology_General', 'Real_IGME_Era', 'Real_IGME_Dominio']
    all_features = features_num + features_cat
    
    folds = create_spatial_folds(df, n_splits=n_splits, seed=seed)
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), features_num),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), features_cat)
        ]
    )
    
    results = {}
    
    for spec in COMMODITY_SPECS:
        target_col = spec["target_col"]
        target_name = spec["name"]
        
        y = df[target_col].values
        n_pos = int(y.sum())
        
        if n_pos < 10:
            logger.warning(f"Insuficientes positivos para {target_name} ({n_pos}). Saltando.")
            continue
            
        oof_raw_probs = np.zeros(len(df))
        fold_metrics = []
        
        for f in range(n_splits):
            train_idx = (folds != f)
            test_idx = (folds == f)
            
            X_train = df.loc[train_idx, all_features]
            y_train = y[train_idx]
            X_test = df.loc[test_idx, all_features]
            y_test = y[test_idx]
            
            pipe = Pipeline([
                ('prep', preprocessor),
                ('clf', LGBMClassifier(n_estimators=120, max_depth=4, learning_rate=0.04, random_state=seed, verbose=-1))
            ])
            
            pipe.fit(X_train, y_train)
            probs = pipe.predict_proba(X_test)[:, 1]
            oof_raw_probs[test_idx] = probs
            
            m = evaluate_fold_metrics(y_test, probs)
            fold_metrics.append(m)
            
        # Calibración Out-Of-Fold (Isotonic)
        calib_eval = evaluate_calibration_methods(y, oof_raw_probs)
        iso_calibrator = calib_eval["isotonic"]["calibrator"]
        
        # Evaluar modelo completo con calibración
        oof_calib_probs = iso_calibrator.predict(oof_raw_probs)
        overall_metrics = evaluate_fold_metrics(y, oof_calib_probs)
        
        # Ajustar modelo final sobre el dataset completo
        final_pipe = Pipeline([
            ('prep', preprocessor),
            ('clf', LGBMClassifier(n_estimators=120, max_depth=4, learning_rate=0.04, random_state=seed, verbose=-1))
        ])
        final_pipe.fit(df[all_features], y)
        
        bundle = {
            "model": final_pipe,
            "calibrator": iso_calibrator,
            "features": all_features,
            "features_num": features_num,
            "features_cat": features_cat,
            "target_commodity": target_name,
            "overall_metrics": overall_metrics,
            "fold_metrics": fold_metrics,
            "n_positives": n_pos,
            "total_samples": len(df),
            "seed": seed
        }
        
        out_path = output_dir / f"model_geoai_v2_{target_name}.joblib"
        joblib.dump(bundle, out_path)
        logger.info(f"Modelo serializado: {out_path}")
        
        results[target_name] = {
            "path": str(out_path),
            "overall_metrics": overall_metrics,
            "n_positives": n_pos
        }
        
    return results
