"""
Pipeline Oficial de Validación Espacial, Ablación, Calibración, LODO y Entrenamiento de GeoAI v2.
Ejecuta la batería completa de experimentos científicos sobre el dataset maestro 100% observado.
"""
import os
import sys
import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import shap
import joblib

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from lightgbm import LGBMClassifier

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_spatial_experiments")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_V2_DIR = PROJECT_ROOT / "models" / "v2"
REPORTS_DIR = PROJECT_ROOT / "reports"

MODELS_V2_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from geoai_roman_spain.ml.spatial_cv import (
    create_spatial_folds,
    evaluate_fold_metrics,
    compute_spatial_autocorrelation_diagnostics
)
from geoai_roman_spain.ml.ablation import run_coordinate_ablation_study
from geoai_roman_spain.ml.lodo import run_lodo_benchmark
from geoai_roman_spain.ml.calibration import evaluate_calibration_methods

print("=" * 80, flush=True)
print("🚀 EJECUTANDO PIPELINE CIENTÍFICO DE VALIDACIÓN ESPACIAL Y MODELADO GeoAI v2", flush=True)
print("=" * 80, flush=True)

# 1. Cargar Dataset Maestro v2
csv_file = PROCESSED_DIR / "ml_dataset_real_v2.csv"
df = pd.read_csv(csv_file)
print(f"📊 Dataset cargado: {len(df)} registros ({int(df['target_class'].sum())} positivos | {(df['target_class']==0).sum()} fondo)", flush=True)

# Seleccionar dinámicamente características numéricas observadas con 100% de cobertura (sin riesgo de fugas por nulos)
candidate_num_features = [
    'Real_Elevation_MDT_m', 'Real_Slope_Deg', 'Real_TPI_1km', 'Real_TRI_Roughness',
    'Real_IGME_Dist_Fault_m', 'Real_IGME_Dist_Contact_m', 'Real_IGME_Fault_Length_Density_5km'
]
features_num = [col for col in candidate_num_features if col in df.columns and df[col].notna().sum() == len(df)]
features_cat = ['Real_IGME_Lithology_General', 'Real_IGME_Era', 'Real_IGME_Dominio']
all_features = features_num + features_cat

print(f"🔬 Características numéricas observadas activas ({len(features_num)}): {features_num}", flush=True)
print(f"🏛️ Características categóricas IGME activas ({len(features_cat)}): {features_cat}", flush=True)

# Diagnóstico de autocorrelación espacial
coords_utm = df[['Coord_X', 'Coord_Y']].values
spatial_diag = compute_spatial_autocorrelation_diagnostics(coords_utm, df['target_class'].values)
print(f"📐 Diagnóstico de Agregación Espacial:")
print(f"   • Distancia media al vecino más cercano:   {spatial_diag['mean_nn_dist_km']} km")
print(f"   • Distancia mediana al vecino más cercano: {spatial_diag['median_nn_dist_km']} km")
print(f"   • Percentil 90 de distancia entre minas:   {spatial_diag['p90_nn_dist_km']} km")

# Preprocesador con Imputación Mediana (para manejar ausencias de datos observados sin inventar)
preprocessor = ColumnTransformer(
    transformers=[
        ('num', Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ]), features_num),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), features_cat)
    ]
)

# 2. Estudio Formal de Ablación de Coordenadas
print("\n🔬 1/4. Ejecutando Estudio de Ablación de Coordenadas (Coordinate Memorization Test)...", flush=True)
ablation_results = run_coordinate_ablation_study(df, target_col='target_class', n_splits=5, seed=42)
print(f"   • Modelo A (Oficial - Solo Geociencia):  ROC-AUC = {ablation_results['model_A_geoscientific_no_coords']['overall']['roc_auc']:.4f} | PR-AUC = {ablation_results['model_A_geoscientific_no_coords']['overall']['pr_auc']:.4f}")
print(f"   • Modelo B (Con Coordenadas X/Y):       ROC-AUC = {ablation_results['model_B_with_coords_leakage']['overall']['roc_auc']:.4f} | PR-AUC = {ablation_results['model_B_with_coords_leakage']['overall']['pr_auc']:.4f}")
print(f"   • Δ ROC-AUC por coordenadas: {ablation_results['delta_roc_auc']:+.4f} ({ablation_results['interpretation']})")

with open(REPORTS_DIR / "coordinate_ablation_study.json", "w", encoding="utf-8") as f:
    json.dump(ablation_results, f, indent=2)

# 3. Validación Leave-One-District-Out (LODO)
print("\n🏛️ 2/4. Ejecutando Validación Leave-One-District-Out (LODO) por Provincias Metalogénicas...", flush=True)
lodo_results = run_lodo_benchmark(df, target_col='target_class', seed=42)
for dist_id, res in lodo_results.items():
    if res['metrics']:
        print(f"   • {res['district_name']} [{res['status']} | N_test={res['n_test_pos']}]: ROC-AUC = {res['metrics']['roc_auc']:.4f} | PR-AUC = {res['metrics']['pr_auc']:.4f}")
    else:
        print(f"   • {res['district_name']}: {res['status']}")

with open(REPORTS_DIR / "lodo_validation_results.json", "w", encoding="utf-8") as f:
    json.dump(lodo_results, f, indent=2)

# 4. Entrenamiento y Calibración Espacial de los Modelos de Producción v2
print("\n⚙️ 3/4. Entrenando y Calibrando los Modelos de Producción v2...", flush=True)
COMMODITY_SPECS = [
    {"target_col": "target_class", "name": "General_Mining", "label": "Explotación Minera General"},
    {"target_col": "flag_Au", "name": "Au_Oro", "label": "Oro"},
    {"target_col": "flag_Cu", "name": "Cu_Cobre", "label": "Cobre"},
    {"target_col": "flag_Ag", "name": "Ag_Plata", "label": "Plata"},
    {"target_col": "flag_Pb", "name": "Pb_Plomo", "label": "Plomo"}
]

folds = create_spatial_folds(df, n_splits=5, seed=42)
trained_models = {}

for spec in COMMODITY_SPECS:
    target_col = spec["target_col"]
    target_name = spec["name"]
    y = df[target_col].values
    n_pos = int(y.sum())
    
    oof_raw = np.zeros(len(df))
    fold_metrics = []
    
    for f in range(5):
        train_idx = (folds != f)
        test_idx = (folds == f)
        
        X_train = df.loc[train_idx, all_features]
        y_train = y[train_idx]
        X_test = df.loc[test_idx, all_features]
        y_test = y[test_idx]
        
        pipe = Pipeline([
            ('prep', preprocessor),
            ('clf', LGBMClassifier(n_estimators=120, max_depth=4, learning_rate=0.04, random_state=42, verbose=-1))
        ])
        pipe.fit(X_train, y_train)
        probs = pipe.predict_proba(X_test)[:, 1]
        oof_raw[test_idx] = probs
        
        m = evaluate_fold_metrics(y_test, probs)
        fold_metrics.append(m)
        
    # Calibración Out-Of-Fold
    calib_eval = evaluate_calibration_methods(y, oof_raw)
    iso_cal = calib_eval["isotonic"]["calibrator"]
    oof_calib = iso_cal.predict(oof_raw)
    overall_m = evaluate_fold_metrics(y, oof_calib)
    
    # Entrenar pipeline final
    final_pipe = Pipeline([
        ('prep', preprocessor),
        ('clf', LGBMClassifier(n_estimators=120, max_depth=4, learning_rate=0.04, random_state=42, verbose=-1))
    ])
    final_pipe.fit(df[all_features], y)
    
    bundle = {
        "model": final_pipe,
        "calibrator": iso_cal,
        "features": all_features,
        "features_num": features_num,
        "features_cat": features_cat,
        "target_commodity": target_name,
        "overall_metrics": overall_m,
        "fold_metrics": fold_metrics,
        "calibration_comparison": {
            "uncalibrated": calib_eval["uncalibrated"],
            "platt_sigmoid": {"brier": calib_eval["platt_sigmoid"]["brier"], "ece": calib_eval["platt_sigmoid"]["ece"]},
            "isotonic": {"brier": calib_eval["isotonic"]["brier"], "ece": calib_eval["isotonic"]["ece"]}
        },
        "n_positives": n_pos,
        "total_samples": len(df)
    }
    
    out_model_path = MODELS_V2_DIR / f"model_geoai_v2_{target_name}.joblib"
    joblib.dump(bundle, out_model_path)
    trained_models[target_name] = bundle
    
    print(f"   • [{target_name}] Positivos={n_pos}: Spatial ROC-AUC = {overall_m['roc_auc']:.4f} | PR-AUC = {overall_m['pr_auc']:.4f} | Brier = {overall_m['brier']:.4f} | F1 = {overall_m['f1']:.4f}")

# 5. Generación de Explicabilidad SHAP v2
print("\n📊 4/4. Calculando Explicabilidad e Importancia de Características SHAP v2...", flush=True)
au_model = trained_models["Au_Oro"]["model"]
X_trans = au_model.named_steps['prep'].transform(df[all_features])
feature_names = au_model.named_steps['prep'].get_feature_names_out()

explainer = shap.TreeExplainer(au_model.named_steps['clf'])
shap_values = explainer.shap_values(X_trans)
if isinstance(shap_values, list):
    shap_vals_au = shap_values[1]
else:
    shap_vals_au = shap_values

# Guardar Gráfico SHAP Summary Beeswarm
plt.figure(figsize=(10, 6))
shap.summary_plot(shap_vals_au, X_trans, feature_names=feature_names, show=False, max_display=12)
plt.title("GeoAI v2: SHAP Summary (Modelo Oficial Au_Oro)", fontsize=12, fontweight='bold')
plt.tight_layout()
shap_png = REPORTS_DIR / "shap_summary_v2_gold.png"
plt.savefig(shap_png, dpi=200)
plt.close()
print(f"   • Gráfico SHAP guardado: {shap_png}")

# 6. Escribir Informe Markdown Oficial de Benchmarks
benchmark_md = REPORTS_DIR / "geoai_v2_model_benchmark.md"
with open(benchmark_md, "w", encoding="utf-8") as f:
    f.write("# 📊 Benchmark Científico Oficial de Modelos GeoAI v2\n\n")
    f.write("## 1. Resumen Metodológico\n")
    f.write("* **Estrategia de Validación:** Spatial Block Cross-Validation (5 folds espaciales basados en coordenadas métricas EPSG:25830).\n")
    f.write("* **Calibración Probabilística:** Out-of-fold Isotonic Regression para mapeo de Prospectivity / Favorability Score (0.0 a 1.0).\n")
    f.write("* **Datos de Entrada:** 100% observables y derivados de cartografía oficial (IGME 1M + Copernicus DEM).\n")
    f.write("* **Exclusión de Coordenadas:** Coord_X y Coord_Y han sido estrictamente excluidas del vector predictor oficial.\n\n")
    
    f.write("## 2. Rendimiento Global por Commodity Mineral\n\n")
    f.write("| Commodity | Positivos | Spatial ROC-AUC | Spatial PR-AUC | Brier Score | F1 Score | Precision@Top10% | Capture Rate (Top 10%) |\n")
    f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")
    for spec in COMMODITY_SPECS:
        name = spec["name"]
        m = trained_models[name]["overall_metrics"]
        n_p = trained_models[name]["n_positives"]
        f.write(f"| **{spec['label']} ({name})** | {n_p} | {m['roc_auc']:.4f} | {m['pr_auc']:.4f} | {m['brier']:.4f} | {m['f1']:.4f} | {m['precision_top_k']:.4f} | {m['gain_top_k']*100:.1f}% |\n")
        
    f.write("\n## 3. Estudio de Ablación de Coordenadas\n\n")
    f.write("| Modelo | Predictors | Spatial ROC-AUC | Spatial PR-AUC | Brier Score | Interpretación |\n")
    f.write("| :--- | :--- | :---: | :---: | :---: | :--- |\n")
    mA = ablation_results['model_A_geoscientific_no_coords']['overall']
    mB = ablation_results['model_B_with_coords_leakage']['overall']
    f.write(f"| **Modelo A (Oficial)** | 7 Numéricos + 3 Categóricos IGME | **{mA['roc_auc']:.4f}** | **{mA['pr_auc']:.4f}** | {mA['brier']:.4f} | Modelo generalizable sin memorización espacial |\n")
    f.write(f"| **Modelo B (Ablation)** | Numéricos + Categóricos + Coord_X/Y | {mB['roc_auc']:.4f} | {mB['pr_auc']:.4f} | {mB['brier']:.4f} | Memorización espacial de latitud/longitud |\n\n")
    
    f.write("## 4. Resultados Leave-One-District-Out (LODO)\n\n")
    f.write("| Distrito / Provincia Metalogénica | Estado Muestral | N Train Pos | N Test Pos | N Test Fondo | ROC-AUC | PR-AUC |\n")
    f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
    for dist_id, res in lodo_results.items():
        if res['metrics']:
            f.write(f"| **{res['district_name']}** | `{res['status']}` | {res['n_train_pos']} | {res['n_test_pos']} | {res['n_test_bg']} | {res['metrics']['roc_auc']:.4f} | {res['metrics']['pr_auc']:.4f} |\n")
        else:
            f.write(f"| **{res['district_name']}** | `{res['status']}` | {res['n_train_pos']} | {res['n_test_pos']} | {res['n_test_bg']} | N/D | N/D |\n")

print(f"\n📄 Informe de Benchmark generado: {benchmark_md}")
print("=" * 80)
print("🎉 ¡PIPELINE DE MODELADO GeoAI v2 EJECUTADO CON ÉXITO!")
print("=" * 80)
