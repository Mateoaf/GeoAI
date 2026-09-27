"""Generador y ejecutor de los dos notebooks finales para GeoAI-Au v1.0:
- notebooks/07_fase_g_evaluacion_holdout.ipynb
- notebooks/08_fase_h_mapa_interpretabilidad.ipynb

Ambos notebooks operan en modo estrictamente read-only, validan la integridad
criptográfica de los artefactos sellados y reconstruyen visualmente los resultados
de las Fases G y H.
"""
from pathlib import Path
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

ROOT = Path(__file__).resolve().parents[1] if '__file__' in locals() else Path('.').resolve()

def build_notebook_07_g():
    nb = nbformat.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.14"
        }
    }

    # Cell 1: Markdown Title
    nb.cells.append(nbformat.v4.new_markdown_cell("""# 07 · Fase G: Evaluación Ciega en Reserva Espacial Independiente (Holdout)

**Proyecto:** GeoAI-Au v1.0 · Cierre Científico  
**Pipeline Evaluado:** `logistic_01` (Regresión Logística L2 regularizada, balance P/U 1:1, estandarización `StandardScaler`)  
**Ejecución Sellada de Fase G:** `reports/fase_g/20260927T141408_460613Z`  
**Modo Operativo:** **Estrictamente Read-Only** (sin reentrenamiento, sin optimización de hiperparámetros, sin alteración de artefactos).

---

## 🎯 Contexto Científico y Protocolo de Validación

La **Fase G** constituye la evaluación ciega, única e irreversible del pipeline congelado de prospección aurífera sobre el conjunto de reserva espacial pre-registrado. 

### Principios Metodológicos del Pre-registro
1. **Reserva Espacial Ciega:** 5 distritos metalogenéticos completos fueron excluidos de todo el desarrollo previo (Fases D, E y F):
   - `dist_cabo_de_gata` (Andalucía oriental, vulcanismo neógeno calcualcalino / epitermal)
   - `dist_montes_de_toledo_jara` (Zona Centroibérica, filones orogénicos en pizarras/cuarcitas)
   - `dist_beticas_granada` (Cordilleras Béticas, complejos metamórficos / aluviales)
   - `dist_ossa_morena_penaflor` (Zona Ossa-Morena, intrusiones plutónicas y skarns)
   - `dist_galicia_costa_da_morte` (Zona Galicia-Trás-os-Montes, orogenia hercínica tardía)
2. **Buffer de Amortiguamiento Espacial:** Se aplicó una partición en bloques de **50 km × 50 km** con un gap de exclusión de **5 km** perimetral para erradicar cualquier fuga de información por autocorrelación espacial (*spatial leakage*).
3. **Inmutabilidad:** Ni los predictores, ni los hiperparámetros ($C = 1.0$), ni el umbral de corte, ni el ratio de muestreo P/U fueron modificados tras observar el holdout.
4. **Declaración de Transparencia:** Conforme a la auditoría del proyecto, se declara que existieron accesos exploratorios al contenido y distribución del holdout con posterioridad al congelamiento del modelo en Fase F pero con anterioridad a la formalización de la ejecución canónica; en consecuencia, las métricas reflejan una evaluación rigurosa del modelo congelado sin ajustes ulteriores, evitando denominarla \"primera apertura estricta\".
"""))

    # Cell 2: Code Setup & Imports
    nb.cells.append(nbformat.v4.new_code_cell("""import sys
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from sklearn.metrics import roc_curve, precision_recall_curve, auc

# Localizar la raíz del proyecto GeoAI
ROOT = Path.cwd()
if ROOT.name == 'notebooks':
    ROOT = ROOT.parent

RUN_ID_G = "20260927T141408_460613Z"
RUN_DIR_G = ROOT / "reports" / "fase_g" / RUN_ID_G

print(f"Raíz del repositorio: {ROOT}")
print(f"Directorio de Fase G: {RUN_DIR_G}")

# Configuración visual
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['figure.dpi'] = 120
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8
"""))

    # Cell 3: Markdown Validation
    nb.cells.append(nbformat.v4.new_markdown_cell("""## 1. Validación Previa de Integridad Criptográfica y Run ID

Antes de cargar o visualizar cualquier resultado, se auditan criptográficamente los artefactos de la ejecución sellada contra el manifiesto oficial `outputs_manifest.json` mediante hash SHA-256.
"""))

    # Cell 4: Code Validation
    nb.cells.append(nbformat.v4.new_code_cell("""# 1. Comprobar existencia del directorio de ejecución
assert RUN_DIR_G.exists(), f"ERROR: No se encuentra la ejecución canónica de Fase G en {RUN_DIR_G}"

# 2. Cargar outputs_manifest.json
manifest_path = RUN_DIR_G / "outputs_manifest.json"
assert manifest_path.exists(), f"ERROR: Falta el manifiesto en {manifest_path}"

with open(manifest_path, "r", encoding="utf-8") as f:
    manifest = json.load(f)

print(f"=== AUDITORÍA CRIPTOGRÁFICA DE INTEGRIDAD (SHA-256) — FASE G ===")
print(f"Run ID verificado: {RUN_ID_G}")
print(f"Total artefactos auditados: {len(manifest)}\\n")

hashes_ok = True
for item in manifest:
    file_path = RUN_DIR_G / item["path"]
    assert file_path.exists(), f"ERROR: Falta archivo auditado: {file_path}"
    
    sha256 = hashlib.sha256(file_path.read_bytes()).hexdigest()
    expected_sha = item["sha256"]
    is_valid = (sha256 == expected_sha)
    status_icon = "✅" if is_valid else "❌"
    print(f" {status_icon} {item['path']:<45} {sha256[:16]}... [esperado: {expected_sha[:16]}...]")
    if not is_valid:
        hashes_ok = False

assert hashes_ok, "ERROR: Discrepancia criptográfica en uno o más artefactos de Fase G."

# 3. Comprobar control_cierre.json
with open(RUN_DIR_G / "control_cierre.json", "r", encoding="utf-8") as f:
    control = json.load(f)

assert control.get("estado_ejecucion") == "completada", "ERROR: control_cierre.json no indica estado_ejecucion='completada'"
assert control.get("mode") == "validated", "ERROR: control_cierre.json no está en mode=validated"
assert control.get("opened_once") is True, "ERROR: opened_once debe ser True"
assert control.get("reproducible") is True, "ERROR: reproducible debe ser True"

print("\\n[AUDITORÍA SUPERADA]: Todos los artefactos de Fase G están íntegros, sellados e inmutables.")
"""))

    # Cell 5: Markdown Global Metrics
    nb.cells.append(nbformat.v4.new_markdown_cell("""## 2. Métricas Globales de Rendimiento en Holdout Ciego

Se evalúa la capacidad de recuperación del modelo frozen `logistic_01` en las **13.541 celdas** de la reserva independiente:
- **`deposit_recovery@k%`**: Fracción de depósitos independientes únicos ($N=8$) cuyos contornos contienen al menos una celda clasificada dentro del top $k\\%$ de favorabilidad territorial del holdout.
- **`cell_recovery@k%`**: Fracción de celdas positivas revisadas ($N=19$) recuperadas dentro del top $k\\%$ de favorabilidad.
- **PR-AUC P/U**: Área bajo la curva Precision-Recall calculada entre presencias auditadas ($P$) y fondo no etiquetado ($U$).
- **ROC-AUC P/U**: Área bajo la curva ROC de discriminación entre $P$ y $U$.
"""))

    # Cell 6: Code Global Metrics
    nb.cells.append(nbformat.v4.new_code_cell("""# Cargar métricas globales
with open(RUN_DIR_G / "metrics" / "holdout_overall_metrics.json", "r", encoding="utf-8") as f:
    global_metrics = json.load(f)

df_global = pd.DataFrame([
    {"Métrica": "Celdas Totales Holdout", "Valor": f"{global_metrics['holdout_cells']:,}", "Interpretación": "Universo territorial del holdout (1 km² / celda)"},
    {"Métrica": "Área Total (km²)", "Valor": f"{global_metrics['total_area_km2']:,.2f} km²", "Interpretación": "Superficie de los 5 distritos ciegos"},
    {"Métrica": "Celdas Positivas (P)", "Valor": f"{global_metrics['observed_P_cells']}", "Interpretación": "Celdas con labores/indicios auríferos auditados"},
    {"Métrica": "Depósitos Únicos Test", "Valor": f"{global_metrics['observed_deposits']}", "Interpretación": "Depósitos minerales independientes (N=8)"},
    {"Métrica": "Distritos de Test", "Valor": f"{global_metrics['districts_count']}", "Interpretación": "Dominios metalogenéticos independientes (N=5)"},
    {"Métrica": "Deposit Recovery @ 1%", "Valor": f"{global_metrics['deposit_recovery_at_01'] * 100:.2f}%", "Interpretación": f"{global_metrics['deposit_hits_at_01']} de 8 depósitos en el 1% de área"},
    {"Métrica": "Deposit Recovery @ 5%", "Valor": f"{global_metrics['deposit_recovery_at_05'] * 100:.2f}%", "Interpretación": f"{global_metrics['deposit_hits_at_05']} de 8 depósitos en el 5% de área"},
    {"Métrica": "Deposit Recovery @ 10%", "Valor": f"{global_metrics['deposit_recovery_at_10'] * 100:.2f}%", "Interpretación": f"{global_metrics['deposit_hits_at_10']} de 8 depósitos en el 10% de área"},
    {"Métrica": "Cell Recovery @ 1%", "Valor": f"{global_metrics['cell_recovery_at_01'] * 100:.2f}%", "Interpretación": f"{global_metrics['cell_hits_at_01']} de 19 celdas P recuperadas"},
    {"Métrica": "Cell Recovery @ 5%", "Valor": f"{global_metrics['cell_recovery_at_05'] * 100:.2f}%", "Interpretación": f"{global_metrics['cell_hits_at_05']} de 19 celdas P recuperadas"},
    {"Métrica": "Cell Recovery @ 10%", "Valor": f"{global_metrics['cell_recovery_at_10'] * 100:.2f}%", "Interpretación": f"{global_metrics['cell_hits_at_10']} de 19 celdas P recuperadas"},
    {"Métrica": "PR-AUC (P vs U)", "Valor": f"{global_metrics['average_precision_PU']:.5f}", "Interpretación": f"Frente a prevalencia basal P de {global_metrics['observed_P_cells']/global_metrics['holdout_cells']:.5f}"},
    {"Métrica": "ROC-AUC (P vs U)", "Valor": f"{global_metrics['roc_auc_PU']:.4f}", "Interpretación": "Discriminación global en territorio no visto"},
])

df_global
"""))

    # Cell 7: Markdown Performance Curves
    nb.cells.append(nbformat.v4.new_markdown_cell("""## 3. Curvas de Rendimiento Espacial: Recuperación Acumulada, ROC y Precision-Recall

En exploración geológica minera, la curva de **recuperación acumulada (*recovery vs area fraction*)** es el estándar de referencia: ilustra qué porcentaje de yacimientos o indicios conocidos se descubren a medida que se incrementa el presupuesto de superficie explorada ($k\\%$ del territorio priorizado por el modelo), en comparación con un muestreo ciego o aleatorio ($y = x$).
"""))

    # Cell 8: Code Performance Curves
    nb.cells.append(nbformat.v4.new_code_cell("""# Cargar predicciones completas a nivel de celda en holdout
pred_path = RUN_DIR_G / "predictions" / "holdout_predictions.parquet"
df_preds = pd.read_parquet(pred_path)

# Ordenar de mayor a menor favorabilidad
df_sorted = df_preds.sort_values(by="score", ascending=False).reset_index(drop=True)
n_total = len(df_sorted)
n_deposits = global_metrics['observed_deposits']
n_p_cells = global_metrics['observed_P_cells']

# Calcular curvas de recuperación acumulada
area_pct = np.linspace(0.001, 1.0, 1000)
dep_rec_curve = []
cell_rec_curve = []

for f in area_pct:
    k_cells = int(np.ceil(f * n_total))
    subset = df_sorted.iloc[:k_cells]
    
    # Celdas recuperadas
    cells_hit = subset['is_P'].sum()
    cell_rec_curve.append(cells_hit / n_p_cells)
    
    # Depósitos recuperados
    deps_hit = subset.loc[subset['is_P'] & subset['deposit_id'].notna(), 'deposit_id'].nunique()
    dep_rec_curve.append(deps_hit / n_deposits)

# Curvas ROC y PR
y_true = df_preds['is_P'].astype(int)
y_scores = df_preds['score']

fpr, tpr, _ = roc_curve(y_true, y_scores)
roc_auc_val = auc(fpr, tpr)

prec, rec, _ = precision_recall_curve(y_true, y_scores)
pr_auc_val = auc(rec, prec)

# Visualización en 3 paneles
fig, axes = plt.subplots(1, 3, figsize=(18, 5.2))

# Panel 1: Recovery vs Budget (Zoom a 20% de área)
ax1 = axes[0]
ax1.plot(area_pct * 100, [r * 100 for r in dep_rec_curve], color='#b8860b', lw=2.5, label='Depósitos (N=8)')
ax1.plot(area_pct * 100, [r * 100 for r in cell_rec_curve], color='#2e8b57', lw=2.0, ls='--', label='Celdas P (N=19)')
ax1.plot([0, 20], [0, 20], color='#888888', ls=':', label='Muestreo Aleatorio (y=x)')

# Marcar puntos canónicos
for k, col, label in [(1, '#d9534f', 'Top 1%'), (5, '#f0ad4e', 'Top 5%'), (10, '#5bc0de', 'Top 10%')]:
    idx = (np.abs(area_pct * 100 - k)).argmin()
    ax1.scatter([k], [dep_rec_curve[idx] * 100], color=col, s=80, zorder=5)
    ax1.axvline(k, color=col, ls='--', alpha=0.5)

ax1.set_xlim(0, 20)
ax1.set_ylim(0, 60)
ax1.set_xlabel('Fracción de Área del Holdout Priorizada (%)', fontweight='bold')
ax1.set_ylabel('Recuperación Acumulada (%)', fontweight='bold')
ax1.set_title('A. Curva de Recuperación vs Presupuesto de Área', fontweight='bold', pad=12)
ax1.legend(loc='upper left', frameon=True)

# Panel 2: Curva ROC
ax2 = axes[1]
ax2.plot(fpr, tpr, color='#1f77b4', lw=2.2, label=f'ROC Pipeline logistic_01 (AUC = {roc_auc_val:.3f})')
ax2.plot([0, 1], [0, 1], color='#888888', ls='--', label='Línea de Azar')
ax2.set_xlabel('Tasa de Falsos Positivos (FPR)', fontweight='bold')
ax2.set_ylabel('Tasa de Verdaderos Positivos (TPR)', fontweight='bold')
ax2.set_title('B. Curva ROC en Holdout Ciego', fontweight='bold', pad=12)
ax2.legend(loc='lower right', frameon=True)

# Panel 3: Curva Precision-Recall
ax3 = axes[2]
ax3.plot(rec, prec, color='#9467bd', lw=2.2, label=f'Curva PR (PR-AUC = {pr_auc_val:.5f})')
base_prevalence = y_true.mean()
ax3.axhline(base_prevalence, color='#888888', ls=':', label=f'Prevalencia Base ({base_prevalence:.4f})')
ax3.set_xlabel('Exhaustividad / Recall', fontweight='bold')
ax3.set_ylabel('Precisión (P / (P+U))', fontweight='bold')
ax3.set_title('C. Curva Precision-Recall en Holdout', fontweight='bold', pad=12)
ax3.legend(loc='upper right', frameon=True)

plt.tight_layout()
plt.show()
"""))

    # Cell 9: Markdown Deposit Breakdown
    nb.cells.append(nbformat.v4.new_markdown_cell("""## 4. Desglose Detallado por Depósito Aurífero (N = 8)

El conjunto de test ciego comprende exactamente **8 depósitos minerales independientes** distribuidos en los 5 distritos de reserva. Analizar el percentil de favorabilidad alcanzado por cada depósito permite entender la naturaleza geológica de los éxitos y las discrepancias del modelo lineal regularizado.
"""))

    # Cell 10: Code Deposit Breakdown
    nb.cells.append(nbformat.v4.new_code_cell("""# Cargar métricas por depósito
df_deposits = pd.read_csv(RUN_DIR_G / "metrics" / "holdout_by_deposit.csv")
df_deposits = df_deposits.sort_values(by="best_percentile_favorability", ascending=True).reset_index(drop=True)

# Gráfico de barras horizontales
fig, ax = plt.subplots(figsize=(10, 5.5))
colors = ['#2ca02c' if r10 else '#d62728' for r10 in df_deposits['recovered_at_10']]
bars = ax.barh(df_deposits['deposit_id'], df_deposits['best_percentile_favorability'], color=colors, alpha=0.85, edgecolor='black', height=0.6)

# Líneas de referencia para Top 1%, Top 5% y Top 10%
ax.axvline(99.0, color='#d9534f', ls='--', lw=1.5, label='Top 1% (Percentil ≥ 99.0)')
ax.axvline(95.0, color='#f0ad4e', ls='--', lw=1.5, label='Top 5% (Percentil ≥ 95.0)')
ax.axvline(90.0, color='#5bc0de', ls='--', lw=1.5, label='Top 10% (Percentil ≥ 90.0)')

for bar, pct in zip(bars, df_deposits['best_percentile_favorability']):
    ax.text(pct + 1.0, bar.get_y() + bar.get_height()/2, f"{pct:.2f}%", va='center', ha='left', fontsize=9, fontweight='bold')

ax.set_xlim(0, 110)
ax.set_xlabel('Percentil Territorial de Favorabilidad Máxima en el Holdout (%)', fontweight='bold')
ax.set_title('Percentil Territorial Máximo por Depósito en Test Ciego (N = 8)', fontweight='bold', pad=12)
ax.legend(loc='lower right', frameon=True)
plt.tight_layout()
plt.show()

# Mostrar tabla descriptiva completa
df_deposits[['deposit_id', 'district_id', 'p_cells_count', 'max_score', 'best_percentile_favorability', 'recovered_at_01', 'recovered_at_05', 'recovered_at_10']]
"""))

    # Cell 11: Markdown District Breakdown
    nb.cells.append(nbformat.v4.new_markdown_cell("""## 5. Rendimiento Desagregado por Distrito Metalogenético (N = 5)

La evaluación ciega demuestra una marcada heterogeneidad espacial entre los dominios metalogenéticos:
- **Cabo de Gata (`dist_cabo_de_gata`):** Fuerte éxito predictivo en *Rodalquilar Cinto* (percentil 99.65%, detectado en Top 1%), impulsado por la firma litológica y estructural de vulcanismo cenozoico.
- **Montes de Toledo - La Jara (`dist_montes_de_toledo_jara`):** Éxito en *La Oriental* (percentil 93.07%, detectado en Top 10%), consistente con la favorabilidad de formaciones paleozoicas y gradientes geomórficos.
- **Béticas Granada (`dist_beticas_granada`):** *Darro* se ubica en el percentil 83.70% (top 16.3%), no alcanzando el corte del top 10%.
- **Ossa-Morena Peñaflor (`dist_ossa_morena_penaflor`):** *Navalmedio* (55.95%) y *La Almenara* (52.11%) se ubican en torno a la mediana del distrito.
- **Galicia Costa da Morte (`dist_galicia_costa_da_morte`):** *Corcoesto* (37.05%) y *Santa Comba* (39.80%) obtienen percentiles modestos, revelando la brecha de transferencia hacia yacimientos orogénicos hercínicos en zócalos metamórficos con poca impronta en la cartografía regional 1:50.000.
"""))

    # Cell 12: Code District Breakdown
    nb.cells.append(nbformat.v4.new_code_cell("""# Cargar tabla por distrito
df_districts = pd.read_csv(RUN_DIR_G / "metrics" / "holdout_by_district.csv")

# Distribución de scores por distrito (Boxplot con las 13.541 celdas)
fig, ax = plt.subplots(figsize=(11, 4.8))
dist_ids = df_districts['district_id'].tolist()
data_by_dist = [df_preds.loc[df_preds['district_id'] == d, 'score'].values for d in dist_ids]

bplot = ax.boxplot(data_by_dist, tick_labels=[d.replace('dist_', '') for d in dist_ids], patch_artist=True,
                    boxprops=dict(facecolor='#aec7e8', color='#1f77b4'),
                    medianprops=dict(color='#d62728', lw=2),
                    whiskerprops=dict(color='#1f77b4', lw=1.2),
                    capprops=dict(color='#1f77b4', lw=1.2),
                    flierprops=dict(marker='o', markersize=3, alpha=0.3))

ax.set_ylabel('Score de Favorabilidad en $(0, 1)$', fontweight='bold')
ax.set_title('Distribución Territorial de Scores por Distrito en Holdout Ciego', fontweight='bold', pad=12)
plt.xticks(rotation=15, ha='right')
plt.tight_layout()
plt.show()

df_districts[['district_id', 'total_cells', 'p_cells', 'n_deposits', 'deposits_list', 'score_mean', 'deposits_recovered_at_01', 'deposits_recovered_at_05', 'deposits_recovered_at_10']]
"""))

    # Cell 13: Markdown Bootstrap
    nb.cells.append(nbformat.v4.new_markdown_cell("""## 6. Análisis de Incertidumbre Bootstrap a Nivel de Depósito (N = 8)

Dado que el conjunto de test ciego comprende únicamente **8 depósitos auríferos**, cualquier métrica de recuperación se encuentra sujeta a una **fuerte granularidad discreta**: cada depósito recuperado representa un salto exacto del $1/8 = 12.5\\%$ en la tasa global.

Para estimar rigurosamente la incertidumbre muestral sin suposiciones paramétricas asintóticas, se ejecutó un procedimiento **Bootstrap con 2.000 replicaciones** remuestreando con reemplazo a nivel de `deposit_id`.
"""))

    # Cell 14: Code Bootstrap
    nb.cells.append(nbformat.v4.new_code_cell("""# Cargar bootstrap de incertidumbre
with open(RUN_DIR_G / "metrics" / "bootstrap_deposit_uncertainty.json", "r", encoding="utf-8") as f:
    boot_data = json.load(f)

boot_rows = []
for k in ["01", "05", "10"]:
    key = f"recovery_at_{k}"
    entry = boot_data[key]
    boot_rows.append({
        "Umbral": f"Top {int(k)}% Área",
        "Estimación Puntual": f"{entry['point_estimate'] * 100:.2f}%",
        "Media Bootstrap": f"{entry['bootstrap_mean'] * 100:.2f}%",
        "Desv. Estándar Bootstrap": f"{entry['bootstrap_std'] * 100:.2f}%",
        "IC 95% Percentil (Low)": f"{entry['ci_95_percentile_low'] * 100:.2f}%",
        "IC 95% Percentil (High)": f"{entry['ci_95_percentile_high'] * 100:.2f}%",
        "Rango IC 95%": f"[{entry['ci_95_percentile_low'] * 100:.1f}%, {entry['ci_95_percentile_high'] * 100:.1f}%]"
    })

df_boot = pd.DataFrame(boot_rows)

# Visualización de barras con error
fig, ax = plt.subplots(figsize=(8, 4.5))
x_pos = np.arange(len(boot_rows))
point_vals = [boot_data[f"recovery_at_{k}"]['point_estimate'] * 100 for k in ["01", "05", "10"]]
err_low = [point_vals[i] - boot_data[f"recovery_at_{k}"]['ci_95_percentile_low'] * 100 for i, k in enumerate(["01", "05", "10"])]
err_high = [boot_data[f"recovery_at_{k}"]['ci_95_percentile_high'] * 100 - point_vals[i] for i, k in enumerate(["01", "05", "10"])]

ax.bar(x_pos, point_vals, color='#4682b4', alpha=0.8, edgecolor='black', width=0.45, label='Estimación Puntual Holdout')
ax.errorbar(x_pos, point_vals, yerr=[err_low, err_high], fmt='none', ecolor='#d9534f', elinewidth=2.5, capsize=8, capthick=2, label='IC 95% Bootstrap (N=8 depósitos)')

ax.set_xticks(x_pos)
ax.set_xticklabels([b['Umbral'] for b in boot_rows], fontweight='bold')
ax.set_ylabel('Deposit Recovery (%)', fontweight='bold')
ax.set_ylim(0, 65)
ax.set_title('Incertidumbre Bootstrap (2.000 Replicaciones) en Test Ciego (N = 8)', fontweight='bold', pad=12)
ax.legend(loc='upper left', frameon=True)

for i, v in enumerate(point_vals):
    ax.text(i, v + 2.5, f"{v:.1f}%", ha='center', fontweight='bold')

plt.tight_layout()
plt.show()

df_boot[['Umbral', 'Estimación Puntual', 'Media Bootstrap', 'Desv. Estándar Bootstrap', 'Rango IC 95%']]
"""))

    # Cell 15: Markdown Comparison Dev vs Holdout
    nb.cells.append(nbformat.v4.new_markdown_cell("""## 7. Comparación Desarrollo (Nested CV OOF) vs Holdout Ciego: Brecha de Transferencia

Al comparar las estimaciones fuera de pliegue (*out-of-fold*, OOF) obtenidas durante la validación cruzada anidada en el conjunto de desarrollo con los resultados del holdout ciego, se observa una **brecha de transferencia (*transfer gap*)**:
- La recuperación a 1% se mantiene comparable ($14.4\\%$ en OOF vs $12.5\\%$ en holdout; $\\Delta = -1.9\\%$).
- La recuperación a 5% y 10% exhibe una reducción significativa (de $43.9\\%$ a $12.5\\%$ en top 5%, y de $52.8\\%$ a $25.0\\%$ en top 10%).
- Esta diferencia refleja la penalización en distritos ciegos cuyas asociaciones metalogenéticas locales (como la mineralización en Galicia) difieren sustancialmente del promedio capturado en el conjunto de desarrollo, confirmando la necesidad de reportar intervalos de transferencia territorial realistas.
"""))

    # Cell 16: Code Comparison Dev vs Holdout
    nb.cells.append(nbformat.v4.new_code_cell("""df_comp = pd.read_csv(RUN_DIR_G / "metrics" / "development_vs_holdout_comparison.csv")

# Gráfico comparativo de barras
fig, ax = plt.subplots(figsize=(10, 4.8))
metrics_plot = df_comp['metric'].tolist()
x = np.arange(len(metrics_plot))
width = 0.35

rects1 = ax.bar(x - width/2, df_comp['nested_spatial_cv_oof_mean'], width, label='Desarrollo (Nested CV OOF Mean)', color='#2b5c8f', alpha=0.85)
rects2 = ax.bar(x + width/2, df_comp['holdout_blind_evaluation'], width, label='Test Ciego (Holdout)', color='#d95f02', alpha=0.85)

ax.set_ylabel('Valor de la Métrica', fontweight='bold')
ax.set_title('Brecha de Transferencia Observada: Desarrollo OOF vs Holdout Ciego', fontweight='bold', pad=12)
ax.set_xticks(x)
ax.set_xticklabels(metrics_plot, rotation=20, ha='right', fontweight='bold')
ax.legend(frameon=True)

plt.tight_layout()
plt.show()

df_comp
"""))

    # Cell 17: Markdown Conclusions
    nb.cells.append(nbformat.v4.new_markdown_cell("""## 8. Conclusiones y Guardarraíles de la Fase G

1. **Protocolo Sellado:** La evaluación ciega se completó rigurosamente sin alteración de hiperparámetros, umbrales ni variables tras la observación del holdout.
2. **Capacidad Predictiva:** El modelo es capaz de priorizar yacimientos de clase mundial en dominios no vistos (percentil 99.65% en Rodalquilar Cinto, 93.07% en La Oriental), mientras que revela limitaciones en dominios metamórficos orogénicos como Galicia.
3. **Guardarraíl Terminológico:** Los scores calculados representan **favorabilidad relativa** (*prospectivity score* en $(0, 1)$), no probabilidades absolutas de existencia de yacimientos comerciales.
"""))

    return nb


def build_notebook_08_h():
    nb = nbformat.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.14"
        }
    }

    # Cell 1: Markdown Title
    nb.cells.append(nbformat.v4.new_markdown_cell("""# 08 · Fase H: Cartografía Predictiva Nacional, Interpretabilidad y Priorización

**Proyecto:** GeoAI-Au v1.0 · Cierre Científico  
**Pipeline Inmutable:** `logistic_01` (Regresión Logística L2 regularizada, balance P/U 1:1, `StandardScaler`)  
**Ejecución Sellada de Fase H:** `reports/fase_h/20260927T142549_961719Z`  
**Ámbito Territorial:** **España peninsular** / dominio peninsular modelado (478.443 celdas de 1 km²)  
**Modo Operativo:** **Estrictamente Read-Only** (sin reentrenamiento, visualización y análisis de artefactos inmutables).

---

## 🗺️ Alcance Metodológico de la Fase H

La **Fase H** culmina el ciclo científico de **GeoAI-Au v1.0**:
1. **Cartografía Continua y Categórica:** Inferencia espacial completa sobre las **478.443 celdas elegibles** (`eligible_approved_features`), exportando rásteres Cloud-Optimized GeoTIFF (COG), GeoPackage y GeoParquet con score continuo en $(0, 1)$, percentil territorial [0, 100] y bandas prioritarias (Top 1%, Top 5%, Top 10%).
2. **Priorización Espacial de Zonas:** Segmentación y delimitación de **1.529 zonas de prospectividad/priorización**, estructuradas en un ranking territorial ordenado por favorabilidad decreciente.
3. **Interpretabilidad Metrológica:** Análisis de los **56 coeficientes estandarizados** del modelo, explicitando que $\\exp(\\beta)$ representa el cambio en *odds* por incremento de **$+1\\sigma$** tras estandarización con `StandardScaler`.
4. **Hipótesis Geológica de Falla:** Formulación rigurosa del coeficiente positivo de `dist_falla_cartografiada_m` ($\beta = +0{,}2122$) como **hipótesis de escala y sesgo cartográfico**, y no como mecanismo genético demostrado.
5. **Explicabilidad Local:** Desglose de contribuciones aditivas en escala log-odds para depósitos emblemáticos (*Rodalquilar, La Oriental, Navalmedio, Corcoesto*).
"""))

    # Cell 2: Code Setup & Imports
    nb.cells.append(nbformat.v4.new_code_cell("""import sys
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import rasterio

# Localizar la raíz del proyecto GeoAI
ROOT = Path.cwd()
if ROOT.name == 'notebooks':
    ROOT = ROOT.parent

RUN_ID_H = "20260927T142549_961719Z"
RUN_DIR_H = ROOT / "reports" / "fase_h" / RUN_ID_H

print(f"Raíz del repositorio: {ROOT}")
print(f"Directorio de Fase H: {RUN_DIR_H}")

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['figure.dpi'] = 120
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
"""))

    # Cell 3: Markdown Validation
    nb.cells.append(nbformat.v4.new_markdown_cell("""## 1. Validación Previa de Integridad Criptográfica y Run ID

Se verifica que la ejecución canónica `reports/fase_h/20260927T142549_961719Z` se encuentra presente y que todos sus artefactos cumplen de forma estricta los hashes SHA-256 pre-registrados en `outputs_manifest.json`.
"""))

    # Cell 4: Code Validation
    nb.cells.append(nbformat.v4.new_code_cell("""assert RUN_DIR_H.exists(), f"ERROR: No se encuentra la ejecución canónica de Fase H en {RUN_DIR_H}"

manifest_path = RUN_DIR_H / "outputs_manifest.json"
assert manifest_path.exists(), f"ERROR: Falta el manifiesto en {manifest_path}"

with open(manifest_path, "r", encoding="utf-8") as f:
    manifest = json.load(f)

print(f"=== AUDITORÍA CRIPTOGRÁFICA DE INTEGRIDAD (SHA-256) — FASE H ===")
print(f"Run ID verificado: {RUN_ID_H}")
print(f"Total artefactos auditados: {len(manifest)}\\n")

hashes_ok = True
for item in manifest:
    file_path = RUN_DIR_H / item["path"]
    assert file_path.exists(), f"ERROR: Falta archivo auditado: {file_path}"
    
    sha256 = hashlib.sha256(file_path.read_bytes()).hexdigest()
    expected_sha = item["sha256"]
    is_valid = (sha256 == expected_sha)
    status_icon = "✅" if is_valid else "❌"
    print(f" {status_icon} {item['path']:<55} {sha256[:16]}... [esperado: {expected_sha[:16]}...]")
    if not is_valid:
        hashes_ok = False

assert hashes_ok, "ERROR: Discrepancia criptográfica en uno o más artefactos de Fase H."

with open(RUN_DIR_H / "control_cierre.json", "r", encoding="utf-8") as f:
    control = json.load(f)

assert control.get("estado_ejecucion") == "completada", "ERROR: control_cierre.json no indica estado_ejecucion='completada'"
assert control.get("mode") == "validated", "ERROR: control_cierre.json no está en mode=validated"
assert control.get("national_cells_inferred") == 478443, "ERROR: national_cells_inferred debe ser 478443"
assert control.get("zones_prioritized_count") == 1529, "ERROR: zones_prioritized_count debe ser 1529"
assert control.get("reproducible") is True, "ERROR: reproducible debe ser True"
print("\\n[AUDITORÍA SUPERADA]: Todos los artefactos de Fase H están íntegros, sellados e inmutables.")
"""))

    # Cell 5: Markdown National Cartography
    nb.cells.append(nbformat.v4.new_markdown_cell("""## 2. Cartografía Predictiva Nacional (España Peninsular)

Se cargan y visualizan los rásteres COG generados para las **478.443 celdas elegibles** del dominio peninsular modelado:
1. **Score Continuo de Favorabilidad:** Predicciones en $(0, 1)$ del pipeline congelado.
2. **Percentil Nacional de Favorabilidad:** Posición percentil de cada celda respecto a la distribución peninsular completa [0, 100].
3. **Bandas Prioritarias Discretizadas:** Categorización operativa para exploración:
   - **Banda 1 (Top 1%):** 4.787 celdas (percentil $\\ge 99.0$)
   - **Banda 2 (Top 1-5%):** 19.137 celdas (percentil $95.0 - 99.0$)
   - **Banda 3 (Top 5-10%):** 23.921 celdas (percentil $90.0 - 95.0$)
   - **Banda 0 (Resto):** 430.598 celdas (percentil $< 90.0$)
"""))

    # Cell 6: Code National Cartography
    nb.cells.append(nbformat.v4.new_code_cell("""path_score = RUN_DIR_H / "maps" / "mapa_nacional_favorabilidad_score.tif"
path_pct = RUN_DIR_H / "maps" / "mapa_nacional_favorabilidad_percentil.tif"
path_bandas = RUN_DIR_H / "maps" / "mapa_nacional_bandas_prioritarias.tif"

fig, axes = plt.subplots(1, 3, figsize=(18, 6.0))

# 1. Mapa de Score
with rasterio.open(path_score) as src:
    arr_score = src.read(1)
    nodata_score = src.nodata
    mask_valid = (arr_score != nodata_score)
    arr_score_masked = np.where(mask_valid, arr_score, np.nan)
    
    im1 = axes[0].imshow(arr_score_masked, cmap='viridis', vmin=0, vmax=1)
    axes[0].set_title('A. Score Continuo de Favorabilidad', fontweight='bold', pad=10)
    axes[0].axis('off')
    cbar1 = fig.colorbar(im1, ax=axes[0], orientation='horizontal', fraction=0.046, pad=0.04)
    cbar1.set_label('Score en $(0, 1)$', fontweight='bold')

# 2. Mapa de Percentil
with rasterio.open(path_pct) as src:
    arr_pct = src.read(1)
    arr_pct_masked = np.where(mask_valid, arr_pct, np.nan)
    
    im2 = axes[1].imshow(arr_pct_masked, cmap='plasma', vmin=0, vmax=100)
    axes[1].set_title('B. Percentil Territorial Nacional', fontweight='bold', pad=10)
    axes[1].axis('off')
    cbar2 = fig.colorbar(im2, ax=axes[1], orientation='horizontal', fraction=0.046, pad=0.04)
    cbar2.set_label('Percentil [0, 100]', fontweight='bold')

# 3. Mapa de Bandas Prioritarias
with rasterio.open(path_bandas) as src:
    arr_bandas = src.read(1)
    # 0: Resto, 1: Top 1%, 2: Top 1-5%, 3: Top 5-10%, 255: NoData
    cmap_bandas = mcolors.ListedColormap(['#e0e0e0', '#d9534f', '#f0ad4e', '#5bc0de'])
    bounds = [-0.5, 0.5, 1.5, 2.5, 3.5]
    norm_bandas = mcolors.BoundaryNorm(bounds, cmap_bandas.N)
    
    arr_bandas_plot = np.where(arr_bandas == 255, np.nan, arr_bandas)
    im3 = axes[2].imshow(arr_bandas_plot, cmap=cmap_bandas, norm=norm_bandas)
    axes[2].set_title('C. Bandas Prioritarias para Exploración', fontweight='bold', pad=10)
    axes[2].axis('off')
    
    cbar3 = fig.colorbar(im3, ax=axes[2], orientation='horizontal', fraction=0.046, pad=0.04, ticks=[0, 1, 2, 3])
    cbar3.ax.set_xticklabels(['Resto', 'Top 1%', 'Top 1-5%', 'Top 5-10%'], fontweight='bold', fontsize=8)

plt.suptitle('Cartografía Predictiva Aurífera Nacional — GeoAI-Au v1.0 (España Peninsular)', fontsize=14, fontweight='bold', y=0.98)
plt.tight_layout()
plt.show()

# Estadísticos descriptivos
scores_valid = arr_score[mask_valid]
pcts = [50, 75, 90, 95, 99]
pct_vals = np.percentile(scores_valid, pcts)

df_dist_scores = pd.DataFrame([
    {"Estadístico": "Total Celdas Elegibles", "Valor": f"{len(scores_valid):,}"},
    {"Estadístico": "Score Mínimo", "Valor": f"{scores_valid.min():.5f}"},
    {"Estadístico": "Score Mediana (p50)", "Valor": f"{pct_vals[0]:.5f}"},
    {"Estadístico": "Score Cuartil 3 (p75)", "Valor": f"{pct_vals[1]:.5f}"},
    {"Estadístico": "Umbral Top 10% (p90)", "Valor": f"{pct_vals[2]:.5f}"},
    {"Estadístico": "Umbral Top 5% (p95)", "Valor": f"{pct_vals[3]:.5f}"},
    {"Estadístico": "Umbral Top 1% (p99)", "Valor": f"{pct_vals[4]:.5f}"},
    {"Estadístico": "Score Máximo Nacional", "Valor": f"{scores_valid.max():.5f}"},
])
df_dist_scores
"""))

    # Cell 7: Markdown Target Zones
    nb.cells.append(nbformat.v4.new_markdown_cell("""## 3. Delimitación y Priorización de Zonas Objetivo (Ranking Nacional)

A partir de la cartografía de favorabilidad, se agrupan las celdas adyacentes de alta favorabilidad en **1.529 zonas de prospectividad/priorización**.

> **⚠️ Guardarraíl Metodológico:** La distancia al depósito o distrito histórico más próximo (`distancia_deposito_proximo_km`) constituye una **anotación cartográfica post-hoc** incorporada para orientar la planificación logística en campo; en ningún caso intervino como variable predictora del modelo.
"""))

    # Cell 8: Code Target Zones
    nb.cells.append(nbformat.v4.new_code_cell("""df_zonas = pd.read_csv(RUN_DIR_H / "targets" / "zonas_prospectividad_ranking.csv")

# Resumen por categoría de prioridad
resumen_cat = df_zonas.groupby('categoria_prioridad').agg(
    zonas_count=('zona_id', 'count'),
    area_km2_total=('area_km2', 'sum'),
    celdas_total=('celdas_count', 'sum'),
    score_medio=('score_medio', 'mean'),
    score_maximo=('score_maximo', 'max')
).reset_index()

# Gráfico de dispersión y distribución
fig, axes = plt.subplots(1, 2, figsize=(14, 4.8))

# Panel 1: Scatter Score Máximo vs Área
colors_palette = ['#d9534f', '#f0ad4e', '#5bc0de', '#2ca02c']
for idx, (cat, sub) in enumerate(df_zonas.groupby('categoria_prioridad')):
    col = colors_palette[idx % len(colors_palette)]
    axes[0].scatter(sub['area_km2'], sub['score_maximo'], color=col, alpha=0.6, s=25, label=f"{cat}")

axes[0].set_xscale('log')
axes[0].set_xlabel('Área de la Zona (km², escala log)', fontweight='bold')
axes[0].set_ylabel('Score Máximo en la Zona', fontweight='bold')
axes[0].set_title('A. Score Máximo vs Tamaño de Zona', fontweight='bold', pad=10)
axes[0].legend(frameon=True)

# Panel 2: Histograma de Áreas
axes[1].hist(df_zonas['area_km2'], bins=np.logspace(0, 3.5, 30), color='#4682b4', edgecolor='black', alpha=0.75)
axes[1].set_xscale('log')
axes[1].set_xlabel('Área de la Zona (km², escala log)', fontweight='bold')
axes[1].set_ylabel('Frecuencia (Nº de Zonas)', fontweight='bold')
axes[1].set_title('B. Distribución de Superficie de Zonas Priorizadas', fontweight='bold', pad=10)

plt.tight_layout()
plt.show()

# Mostrar Top 10 Zonas del Ranking Nacional
print("=== TOP 10 ZONAS DE PROSPECTIVIDAD AURÍFERA (RANKING NACIONAL) ===")
cols_show = ['ranking_nacional', 'zona_id', 'categoria_prioridad', 'area_km2', 'score_maximo', 'score_medio', 'deposito_conocido_proximo', 'distancia_deposito_proximo_km']
df_zonas.sort_values(by='ranking_nacional').head(10)[cols_show]
"""))

    # Cell 9: Markdown Standardized Coefficients
    nb.cells.append(nbformat.v4.new_markdown_cell("""## 4. Interpretabilidad Global: Coeficientes Estandarizados

El modelo congelado `logistic_01` es un clasificador lineal regularizado ($L_2$) entrenado sobre variables escaladas mediante `StandardScaler` (media 0, varianza 1).

### Significado Metrológico de los Coeficientes
- **Coeficiente $\\beta$:** Variación en el logit o log-odds de favorabilidad por cada incremento de **$+1$ desviación estándar ($+1\\sigma$)** en la variable original una vez imputada y escalada.
- **Odds Ratio $\\exp(\\beta)$:** Cambio multiplicativo en los momios (odds $=\\frac{p}{1-p}$) asociado a dicho incremento de $+1\\sigma$. Si $\\exp(\\beta) = 1{,}5$, un aumento de $1\\sigma$ incrementa los momios en un $50\\%$.

### 🔍 Hipótesis Geológica para `dist_falla_cartografiada_m` ($\\beta = +0{,}2122$, $\\exp(\\beta) = 1{,}2364$)
> **Hipótesis de Trabajo (no mecanismo causal demostrado):**  
> El coeficiente positivo indica que a nivel de celda de 1 km², una mayor distancia a las fallas cartografiadas en el mapa geológico nacional 1:50.000 se asocia con un mayor score predictivo. Esta observación no contradice el control estructural del oro, sino que responde a:
> 1. **Resolución y escala cartográfica:** Los yacimientos auríferos suelen alojarse en fallas y zonas de cizalla de 2.º y 3.er orden que no aparecen en la cartografía regional 1:50.000.
> 2. **Sesgo litológico y de alteración:** Los bloques adyacentes a las grandes fallas regionales a menudo exhiben coberturas o cizallas estériles, concentrándose las labores históricas en rocas competentes distales a la falla maestra.
"""))

    # Cell 10: Code Standardized Coefficients
    nb.cells.append(nbformat.v4.new_code_cell("""df_coef = pd.read_csv(RUN_DIR_H / "interpretability" / "coeficientes_estandarizados.csv")

# Seleccionar Top 12 positivos y Top 12 negativos
top_pos = df_coef.sort_values(by="coeficiente_estandarizado", ascending=False).head(12)
top_neg = df_coef.sort_values(by="coeficiente_estandarizado", ascending=True).head(12)
df_plot = pd.concat([top_neg, top_pos]).sort_values(by="coeficiente_estandarizado")

fig, ax = plt.subplots(figsize=(12, 7.5))
colors = ['#d9534f' if c < 0 else '#2ca02c' for c in df_plot['coeficiente_estandarizado']]
bars = ax.barh(df_plot['variable'], df_plot['coeficiente_estandarizado'], color=colors, alpha=0.85, edgecolor='black', height=0.6)

ax.axvline(0, color='black', lw=1.2)
ax.set_xlabel('Coeficiente Estandarizado (β por +1σ tras StandardScaler)', fontweight='bold')
ax.set_title('Top Predictores de Favorabilidad Aurífera — Coeficientes del Pipeline logistic_01', fontweight='bold', pad=12)

for bar, val, or_val in zip(bars, df_plot['coeficiente_estandarizado'], df_plot['odds_ratio']):
    offset = 0.02 if val >= 0 else -0.02
    ha = 'left' if val >= 0 else 'right'
    ax.text(val + offset, bar.get_y() + bar.get_height()/2, f"β={val:+.3f} (OR={or_val:.2f})", va='center', ha=ha, fontsize=8, fontweight='bold')

plt.tight_layout()
plt.show()

# Mostrar tabla descriptiva con significado geológico
print("=== PREDICTORES CLAVE Y SIGNIFICADO GEOLÓGICO ===")
df_coef.sort_values(by="abs_coeficiente", ascending=False).head(10)[['variable', 'familia', 'coeficiente_estandarizado', 'odds_ratio', 'impacto_modelo', 'significado_geologico']]
"""))

    # Cell 11: Markdown Local Contributions
    nb.cells.append(nbformat.v4.new_markdown_cell("""## 5. Explicabilidad Local: Contribuciones Aditivas por Depósito

Dado que el modelo es lineal en escala log-odds, la contribución local de cada predictor $j$ para la celda $i$ se expresa directamente como:
$$\\text{Contribución}_j = \\beta_j \\cdot z_{i,j}$$
donde $z_{i,j}$ es el valor estandarizado de la variable. Analizar la suma de contribuciones permite desentrañar qué factores geológicos explican el score asignado a depósitos en diferentes marcos estructurales.
"""))

    # Cell 12: Code Local Contributions
    nb.cells.append(nbformat.v4.new_code_cell("""df_local = pd.read_csv(RUN_DIR_H / "interpretability" / "contribuciones_locales_casos_estudio.csv")

# Casos de estudio emblemáticos presentes en el artefacto
casos = df_local['deposito_id'].unique().tolist()

fig, axes = plt.subplots(2, 2, figsize=(16, 9.5))
axes = axes.flatten()

for idx, dep in enumerate(casos):
    ax = axes[idx]
    sub = df_local[df_local['deposito_id'] == dep].sort_values(by='abs_contribucion', ascending=False).head(8)
    sub = sub.sort_values(by='contribucion_log_odds', ascending=True)
    
    colors_c = ['#d9534f' if c < 0 else '#2ca02c' for c in sub['contribucion_log_odds']]
    ax.barh(sub['variable'], sub['contribucion_log_odds'], color=colors_c, alpha=0.85, edgecolor='black', height=0.6)
    ax.axvline(0, color='black', lw=1.0)
    
    score_medio = sub['score_medio'].iloc[0]
    ax.set_title(f"{dep.replace('dep_', '').upper()} (Score Medio: {score_medio:.4f})", fontweight='bold', pad=8)
    ax.set_xlabel('Contribución a Log-Odds (β · z)', fontweight='bold', fontsize=9)

plt.suptitle('Explicabilidad Local en Casos de Estudio Emblemáticos (Descomposición Log-Odds)', fontsize=13, fontweight='bold', y=0.99)
plt.tight_layout()
plt.show()
"""))

    # Cell 13: Markdown Sensitivity & Uncertainty
    nb.cells.append(nbformat.v4.new_markdown_cell("""## 6. Análisis de Sensibilidad e Incertidumbre

Se examina la estabilidad del modelo frente a variaciones en el presupuesto de exploración territorial y frente a la omisión de distritos completos (*Leave-One-District-Out*):
1. **Sensibilidad a Umbrales:** Relación entre el área explorada (km²) y la tasa de yacimientos recuperados.
2. **Estabilidad Leave-One-District-Out:** Evalúa cómo se comporta el pipeline al omitir secuencialmente cada uno de los 5 distritos ciegos.
"""))

    # Cell 14: Code Sensitivity & Uncertainty
    nb.cells.append(nbformat.v4.new_code_cell("""df_sens_presupuesto = pd.read_csv(RUN_DIR_H / "uncertainty" / "curva_sensibilidad_umbrales_holdout.csv")
df_sens_lodo = pd.read_csv(RUN_DIR_H / "uncertainty" / "sensibilidad_leave_one_district_out.csv")

fig, axes = plt.subplots(1, 2, figsize=(15, 4.8))

# Panel 1: Sensibilidad de Recuperación vs Área Asignada
axes[0].plot(df_sens_presupuesto['area_km2'], df_sens_presupuesto['deposit_recovery'] * 100, marker='o', color='#b8860b', lw=2.2, label='Depósitos Recuperados (%)')
axes[0].plot(df_sens_presupuesto['area_km2'], df_sens_presupuesto['cell_recovery'] * 100, marker='s', color='#2e8b57', lw=2.0, ls='--', label='Celdas P Recuperadas (%)')
axes[0].set_xlabel('Superficie Explorada en Holdout (km²)', fontweight='bold')
axes[0].set_ylabel('Recuperación (%)', fontweight='bold')
axes[0].set_title('A. Sensibilidad al Presupuesto Territorial en Holdout', fontweight='bold', pad=10)
axes[0].legend(frameon=True)

# Panel 2: Sensibilidad Leave-One-District-Out
x_lodo = np.arange(len(df_sens_lodo))
width_lodo = 0.35
axes[1].bar(x_lodo - width_lodo/2, df_sens_lodo['roc_auc_PU'], width_lodo, label='ROC-AUC (P vs U)', color='#1f77b4', alpha=0.85)
axes[1].bar(x_lodo + width_lodo/2, df_sens_lodo['deposit_recovery_at_10'], width_lodo, label='Recovery @ 10%', color='#d95f02', alpha=0.85)
axes[1].set_xticks(x_lodo)
axes[1].set_xticklabels([d.replace('dist_', '') for d in df_sens_lodo['distrito_omitido']], rotation=20, ha='right', fontweight='bold')
axes[1].set_ylabel('Métrica', fontweight='bold')
axes[1].set_title('B. Sensibilidad Leave-One-District-Out en Holdout', fontweight='bold', pad=10)
axes[1].legend(frameon=True)

plt.tight_layout()
plt.show()

print("=== SENSIBILIDAD LEAVE-ONE-DISTRICT-OUT ===")
df_sens_lodo[['distrito_omitido', 'depositos_evaluados', 'deposit_recovery_at_01', 'deposit_recovery_at_05', 'deposit_recovery_at_10', 'roc_auc_PU']]
"""))

    # Cell 15: Markdown Final Conclusions
    nb.cells.append(nbformat.v4.new_markdown_cell("""## 7. Conclusiones Finales y Directrices para la Exploración en Campo

1. **Cierre Metodológico Completo:** La cartografía predictiva nacional y el ranking de zonas representan la síntesis de un flujo completamente auditable desde la conciliación geológica inicial (Fase B) hasta la inferencia sellada (Fase H).
2. **Dominio Territorial:** Los resultados aplican estrictamente a la **España peninsular** (478.443 celdas elegibles), excluyendo archipiélagos y zonas sin cobertura completa de las 56 capas aprobadas.
3. **Uso Responsable:**
   - Los valores calculados son **índices de favorabilidad/prospectividad relativa**, no estimaciones de probabilidad de depósito ni cálculo de leyes o tonelaje.
   - Las zonas priorizadas son guías para orientar campañas de campo, geofísica detallada y muestreo geoquímico, no sustitutos de la validación geológica *in situ*.
"""))

    return nb


def generate_and_execute_all():
    print("================================================================================")
    print("GENERADOR Y EJECUTOR DE NOTEBOOKS FINALES — GeoAI-Au v1.0")
    print("================================================================================\\n")

    notebooks_dir = ROOT / "notebooks"
    notebooks_dir.mkdir(parents=True, exist_ok=True)

    # 1. Construir Notebook G
    path_nb_g = notebooks_dir / "07_fase_g_evaluacion_holdout.ipynb"
    print(f"1. Generando estructura de {path_nb_g.name}...")
    nb_g = build_notebook_07_g()
    with open(path_nb_g, "w", encoding="utf-8") as f:
        nbformat.write(nb_g, f)
    print(f"   [OK] Guardado borrador de {path_nb_g.name} ({len(nb_g.cells)} celdas)")

    # 2. Ejecutar Notebook G
    print(f"2. Ejecutando {path_nb_g.name} de principio a fin (read-only)...")
    ep_g = ExecutePreprocessor(timeout=600, kernel_name='python3')
    ep_g.preprocess(nb_g, {'metadata': {'path': str(notebooks_dir)}})
    with open(path_nb_g, "w", encoding="utf-8") as f:
        nbformat.write(nb_g, f)
    print(f"   [OK] Ejecución completada exitosamente y salidas integradas en {path_nb_g.name}\\n")

    # 3. Construir Notebook H
    path_nb_h = notebooks_dir / "08_fase_h_mapa_interpretabilidad.ipynb"
    print(f"3. Generando estructura de {path_nb_h.name}...")
    nb_h = build_notebook_08_h()
    with open(path_nb_h, "w", encoding="utf-8") as f:
        nbformat.write(nb_h, f)
    print(f"   [OK] Guardado borrador de {path_nb_h.name} ({len(nb_h.cells)} celdas)")

    # 4. Ejecutar Notebook H
    print(f"4. Ejecutando {path_nb_h.name} de principio a fin (read-only)...")
    ep_h = ExecutePreprocessor(timeout=600, kernel_name='python3')
    ep_h.preprocess(nb_h, {'metadata': {'path': str(notebooks_dir)}})
    with open(path_nb_h, "w", encoding="utf-8") as f:
        nbformat.write(nb_h, f)
    print(f"   [OK] Ejecución completada exitosamente y salidas integradas en {path_nb_h.name}\\n")

    print("================================================================================")
    print("NOTEBOOKS FINALES GENERADOS Y EJECUTADOS SATISFACTORIAMENTE:")
    print(f"  - {path_nb_g}")
    print(f"  - {path_nb_h}")
    print("================================================================================")

if __name__ == "__main__":
    generate_and_execute_all()
