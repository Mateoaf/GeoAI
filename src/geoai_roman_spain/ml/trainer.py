"""
Módulo de Entrenamiento, Calibración y Serialización de Modelos GeoAI v2.
Genera modelos reproducibles, calcula métricas completas y registra metadatos en runs/.
"""
import os
import json
import joblib
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.calibration import CalibratedClassifierCV
import lightgbm as lgb

from .spatial_cv import evaluate_spatial_block_cv
from .lodo import evaluate_leave_one_district_out
from .ablation import run_coordinate_ablation_study

def train_and_evaluate_commodity_model(
    df: pd.DataFrame,
    commodity_key: str,
    commodity_name: str,
    target_col: str,
    features_num: list,
    features_cat: list,
    models_dir: Path,
    runs_dir: Path,
    include_coords: bool = False,
    random_state: int = 42
) -> dict:
    """
    Entrena, calibra, valida espacialmente y serializa el modelo v2 para un commodity mineral.
    """
    selected_num = [f for f in features_num if include_coords or f not in ['Coord_X', 'Coord_Y']]
    all_features = selected_num + features_cat
    
    print(f"\n================================================================================")
    print(f"🚀 ENTRENANDO MODELO GEOAI v2: {commodity_name.upper()} (Target: {target_col})")
    print(f"📊 Variables utilizadas ({len(all_features)}): {all_features}")
    print(f"🧭 Coordenadas XY incluidas: {include_coords}")
    print(f"================================================================================")
    
    y = df[target_col].values
    n_pos = int(np.sum(y == 1))
    n_bg = int(np.sum(y == 0))
    print(f"📈 Balance de clases: {n_pos} Positivos | {n_bg} Background ({n_pos/(n_pos+n_bg)*100:.1f}% positivos)")
    
    # 1. Spatial Block Cross-Validation (5 Bloques)
    print("\n🌐 1/3. Ejecutando Spatial Block Cross-Validation (5 Folds)...")
    spatial_res = evaluate_spatial_block_cv(
        df=df,
        features_num=selected_num,
        features_cat=features_cat,
        target_col=target_col,
        n_blocks=5,
        random_state=random_state
    )
    print(f"   • Spatial ROC-AUC: {spatial_res['mean_roc_auc']:.4f} ± {spatial_res['std_roc_auc']:.4f}")
    print(f"   • Spatial PR-AUC:  {spatial_res['mean_pr_auc']:.4f} ± {spatial_res['std_pr_auc']:.4f}")
    print(f"   • Brier Score:     {spatial_res['mean_brier']:.4f} ± {spatial_res['std_brier']:.4f}")
    print(f"   • F1-Score:        {spatial_res['mean_f1']:.4f}")
    
    # 2. Leave-One-District-Out (LODO)
    print("\n🏔️ 2/3. Ejecutando Leave-One-District-Out (LODO en 5 distritos)...")
    lodo_df = evaluate_leave_one_district_out(
        df=df,
        features_num=selected_num,
        features_cat=features_cat,
        target_col=target_col,
        random_state=random_state
    )
    print(lodo_df[['Distrito_Excluido', 'Positivos_Val', 'ROC_AUC', 'PR_AUC', 'Brier_Score']].to_string(index=False))
    
    # 3. Coordinate Ablation
    print("\n🔬 3/3. Ejecutando Coordinate Ablation Study...")
    ablation_res = run_coordinate_ablation_study(
        df=df,
        features_num_base=features_num,
        features_cat=features_cat,
        target_col=target_col,
        n_blocks=5,
        random_state=random_state
    )
    print(ablation_res['summary_df'].to_string(index=False))
    
    # 4. Entrenar Pipeline Final y Calibrar con Isotonic Regression
    preprocessor = ColumnTransformer([
        ('num', StandardScaler(), selected_num),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), features_cat)
    ])
    
    clf = lgb.LGBMClassifier(
        n_estimators=140,
        learning_rate=0.04,
        max_depth=4,
        num_leaves=15,
        min_child_samples=6,
        subsample=0.85,
        random_state=random_state,
        verbose=-1
    )
    
    final_pipeline = Pipeline([
        ('prep', preprocessor),
        ('clf', clf)
    ])
    
    calibrated_model = CalibratedClassifierCV(estimator=final_pipeline, method='isotonic', cv=3)
    calibrated_model.fit(df[all_features], y)
    
    # 5. Serializar Modelo v2
    models_dir.mkdir(parents=True, exist_ok=True)
    model_filename = f"model_geoai_v2_{commodity_key}.joblib"
    model_path = models_dir / model_filename
    
    bundle = {
        'version': '2.0.0',
        'commodity': commodity_key,
        'name': commodity_name,
        'model': calibrated_model,
        'features': all_features,
        'num_features': selected_num,
        'cat_features': features_cat,
        'include_coords': include_coords,
        'metrics': {
            'spatial_roc_auc_mean': spatial_res['mean_roc_auc'],
            'spatial_roc_auc_std': spatial_res['std_roc_auc'],
            'spatial_pr_auc_mean': spatial_res['mean_pr_auc'],
            'spatial_pr_auc_std': spatial_res['std_pr_auc'],
            'brier_mean': spatial_res['mean_brier'],
            'brier_std': spatial_res['std_brier'],
            'f1_mean': spatial_res['mean_f1']
        }
    }
    
    joblib.dump(bundle, model_path)
    print(f"\n💾 Modelo v2 guardado en: {model_path}")
    
    # 6. Guardar Run Artifacts
    run_dir = runs_dir / f"run_v2_{commodity_key}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    with open(run_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(bundle['metrics'], f, indent=2)
        
    lodo_df.to_csv(run_dir / "lodo_evaluation.csv", index=False)
    ablation_res['summary_df'].to_csv(run_dir / "ablation_summary.csv", index=False)
    
    return {
        'bundle': bundle,
        'model_path': model_path,
        'spatial_metrics': spatial_res,
        'lodo_df': lodo_df,
        'ablation_df': ablation_res['summary_df']
    }
