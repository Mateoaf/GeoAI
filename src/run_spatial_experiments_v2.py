"""
Pipeline de Entrenamiento, Validación Espacial y Ablación GeoAI v2.
Ejecuta Spatial Block CV, LODO y Coordinate Ablation para Au, Cu, Ag, Pb
y genera el informe de métricas científicamente defendibles.
"""
import os
import sys
from pathlib import Path
import json
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_V2_DIR = PROJECT_ROOT / "models" / "v2"
REPORTS_DIR = PROJECT_ROOT / "reports"
RUNS_DIR = PROJECT_ROOT / "runs"

MODELS_V2_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
RUNS_DIR.mkdir(parents=True, exist_ok=True)

from geoai_roman_spain.ml.trainer import train_and_evaluate_commodity_model

print("🚀 INICIANDO PIPELINE DE ENTRENAMIENTO Y VALIDACIÓN ESPACIAL GEOAI v2")
print("=" * 80)

# Cargar dataset v2
csv_v2 = PROCESSED_DIR / "ml_dataset_real_v2.csv"
if not csv_v2.exists():
    print(f"❌ Error: Dataset no encontrado en {csv_v2}. Ejecute build_ml_dataset_v2.py primero.")
    sys.exit(1)
    
df = pd.read_csv(csv_v2)
print(f"📊 Dataset ML v2 cargado: {len(df)} registros ({len(df.columns)} columnas)")

# Definición estricta de variables (SOLO OBSERVADAS Y DERIVADAS REALES)
FEATURES_NUM = [
    'Real_Elevation_MDT_m',
    'Real_Slope_Deg',
    'Real_TPI_1km',
    'Real_TRI_Roughness',
    'Real_IGME_Dist_Fault_m',
    'Real_IGME_Dist_Contact_m',
    'Real_IGME_Fault_Density_5km',
    'Real_IGME_Fault_Density_2_5km',
    'Coord_X',
    'Coord_Y'
]

FEATURES_CAT = [
    'Real_IGME_Lithology_General',
    'Real_IGME_Era',
    'Real_IGME_Dominio'
]

COMMODITIES = [
    {'key': 'Au_Oro', 'name': 'Oro (Au)', 'target': 'flag_Au'},
    {'key': 'Cu_Cobre', 'name': 'Cobre (Cu)', 'target': 'flag_Cu'},
    {'key': 'Ag_Plata', 'name': 'Plata (Ag)', 'target': 'flag_Ag'},
    {'key': 'Pb_Plomo', 'name': 'Plomo (Pb)', 'target': 'flag_Pb'}
]

all_results = []
all_lodo_results = []
all_ablation_results = []

for comm in COMMODITIES:
    # Entrenar modelo principal SIN coordenadas para máxima transferabilidad geocientífica (Greenfield)
    res = train_and_evaluate_commodity_model(
        df=df,
        commodity_key=comm['key'],
        commodity_name=comm['name'],
        target_col=comm['target'],
        features_num=FEATURES_NUM,
        features_cat=FEATURES_CAT,
        models_dir=MODELS_V2_DIR,
        runs_dir=RUNS_DIR,
        include_coords=False,
        random_state=42
    )
    
    m = res['bundle']['metrics']
    all_results.append({
        'Commodity': comm['name'],
        'Target': comm['target'],
        'N_Positivos': int(np.sum(df[comm['target']] == 1)),
        'Spatial_ROC_AUC': f"{m['spatial_roc_auc_mean']:.4f} ± {m['spatial_roc_auc_std']:.4f}",
        'Spatial_PR_AUC': f"{m['spatial_pr_auc_mean']:.4f} ± {m['spatial_pr_auc_std']:.4f}",
        'Brier_Score': f"{m['brier_mean']:.4f} ± {m['brier_std']:.4f}",
        'F1_Score': f"{m['f1_mean']:.4f}",
        'Archivo': f"models/v2/model_geoai_v2_{comm['key']}.joblib"
    })
    
    l_df = res['lodo_df'].copy()
    l_df['Commodity'] = comm['name']
    all_lodo_results.append(l_df)
    
    a_df = res['ablation_df'].copy()
    a_df['Commodity'] = comm['name']
    all_ablation_results.append(a_df)

df_summary = pd.DataFrame(all_results)
df_lodo_all = pd.concat(all_lodo_results, ignore_index=True)
df_ablation_all = pd.concat(all_ablation_results, ignore_index=True)

# Guardar Informe en reports/geoai_v2_model_benchmark.md
benchmark_md = REPORTS_DIR / "geoai_v2_model_benchmark.md"
with open(benchmark_md, "w", encoding="utf-8") as f:
    f.write("# 📊 Benchmark Oficial GeoAI v2: Validación Espacial y Evaluación Científica\n\n")
    f.write("Validación espacial estricta sin target leakage, sin variables sintéticas y evaluada out-of-fold.\n\n")
    f.write("## 1. Resumen de Métricas (Spatial Block Cross-Validation - 5 Folds)\n\n")
    
    table_str = "| Commodity | Positivos | Spatial ROC-AUC | Spatial PR-AUC | Brier Score (OOF) | F1-Score | Archivo Serializado |\n"
    table_str += "|---|---|---|---|---|---|---|\n"
    for _, r in df_summary.iterrows():
        table_str += f"| **{r['Commodity']}** | {r['N_Positivos']} | {r['Spatial_ROC_AUC']} | {r['Spatial_PR_AUC']} | {r['Brier_Score']} | {r['F1_Score']} | `{r['Archivo']}` |\n"
    f.write(table_str)
    
    f.write("\n\n## 2. Evaluación Leave-One-District-Out (LODO)\n\n")
    f.write("Capacidad de generalización en distritos mineros completamente ciegos:\n\n")
    lodo_table = "| Commodity | Distrito Excluido | Positivos Val | ROC-AUC | PR-AUC | Brier Score |\n|---|---|---|---|---|---|\n"
    for _, r in df_lodo_all.iterrows():
        lodo_table += f"| {r['Commodity']} | {r['Distrito_Excluido']} | {r['Positivos_Val']} | {r['ROC_AUC']} | {r['PR_AUC']} | {r['Brier_Score']} |\n"
    f.write(lodo_table)
    
    f.write("\n\n## 3. Coordinate Ablation Study (Con vs. Sin Coordenadas XY)\n\n")
    ab_table = "| Commodity | Configuración | Features | Spatial ROC-AUC | Spatial PR-AUC | Brier Score |\n|---|---|---|---|---|---|\n"
    for _, r in df_ablation_all.iterrows():
        ab_table += f"| {r['Commodity']} | {r['Configuracion']} | {r['N_Features']} | {r['Spatial_ROC_AUC']} | {r['Spatial_PR_AUC']} | {r['Brier_Score']} |\n"
    f.write(ab_table)
    
    f.write("\n\n---\n*Generado automáticamente por el Pipeline Científico GeoAI v2.*")

print("\n" + "=" * 80)
print("🎉 ¡TODOS LOS EXPERIMENTOS Y MODELOS v2 COMPLETADOS CON ÉXITO!")
print(f"📁 Informe guardado en: {benchmark_md}")
print("=" * 80)
