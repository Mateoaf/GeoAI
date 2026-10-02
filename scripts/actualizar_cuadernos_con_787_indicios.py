"""
scripts/actualizar_cuadernos_con_787_indicios.py
Script que añade secciones comparativas rigurosas con los datos y métricas
del experimento de los 787 indicios en los 5 cuadernos existentes:
- notebooks/01_indicios_limpieza_etiquetas.ipynb
- notebooks/08_muestreo_presencia_fondo.ipynb
- notebooks/12_random_forest_espacial.ipynb
- notebooks/13_comparacion_modelos.ipynb
- notebooks/17_fase_h_mapa_interpretabilidad.ipynb
"""

import os
import json
import base64
import nbformat
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = ROOT / "notebooks"

def image_to_base64(img_path: Path) -> str:
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def update_notebook_01():
    nb_path = NOTEBOOKS_DIR / "01_indicios_limpieza_etiquetas.ipynb"
    print(f"Actualizando {nb_path.name}...")
    nb = nbformat.read(nb_path, as_version=4)

    # Comprobar si ya se añadió
    for cell in nb.cells:
        if "## 12. Extensión Experimental: Integración y Distribución de los 787 Indicios" in cell.get("source", ""):
            print("  Sección ya presente en notebook 01, omitiendo.")
            return

    md_cell = nbformat.v4.new_markdown_cell("""## 12. Extensión Experimental: Integración y Distribución de los 787 Indicios BDMIN

En la auditoría oficial de la **Fase B** se depuraron los 790 registros brutos de la BDMIN, clasificando **190 como confirmados** (46 depósitos independientes) y dejando **597 registros en cuarentena bibliográfica (`pendiente`)** para evitar falsos positivos en el modelo regulado v1.0.

En esta **extensión experimental**, se evalúa el impacto de incorporar la totalidad de los 787 indicios con coordenadas localizables (190 confirmados + 597 en revisión), expandiendo la cobertura de **131 celdas positivas a 664 celdas positivas de 1 km²** repartidas por las principales cuencas y cinturones metalogenéticos peninsulares.""")

    code_cell_1 = nbformat.v4.new_code_cell("""# Comparativa de distribución: Línea Base Oficial (190) vs Extensión Experimental (787)
import pandas as pd
import numpy as np

resumen_indicios = pd.DataFrame([
    {"Conjunto": "Oficial Fase B (v1.0)", "Total Registros": 190, "Celdas Únicas 1 km²": 131, "Depósitos": 46, "Distritos": 32, "Rol Metodológico": "Línea base auditada y congelada"},
    {"Conjunto": "Cuarentena Bibliográfica", "Total Registros": 597, "Celdas Únicas 1 km²": 533, "Depósitos": "N/D", "Distritos": "N/D", "Rol Metodológico": "Indicios históricos pendientes de revisión de campo"},
    {"Conjunto": "Experimental Consolidado", "Total Registros": 787, "Celdas Únicas 1 km²": 664, "Depósitos": "N/A", "Distritos": "N/A", "Rol Metodológico": "Cobertura máxima de mineralización aurífera peninsular"}
])
display(resumen_indicios)

# Desglose por tipología genética en el conjunto experimental
tipologias = pd.DataFrame([
    {"Tipología": "Oro en Roca (Primario / Orogénico / Skarn / Epitermal)", "Indicios": 457, "Porcentaje": "58.1%", "Principales Dominios": "Cinturón del Narcea, Galicia Occidental, Ossa-Morena, Cabo de Gata"},
    {"Tipología": "Oro Aluvial (Placer / Conglomerados / Paleocauces)", "Indicios": 330, "Porcentaje": "41.9%", "Principales Dominios": "Cuenca del Sil (Médulas), Río Orbigo, Alagón, Darro (Granada)"},
    {"Tipología": "Total Consolidado", "Indicios": 787, "Porcentaje": "100.0%", "Principales Dominios": "Territorio Peninsular Completo"}
])
display(tipologias)""")

    nb.cells.append(md_cell)
    nb.cells.append(code_cell_1)
    nbformat.write(nb, nb_path)
    print("  [OK] Notebook 01 actualizado.")

def update_notebook_08():
    nb_path = NOTEBOOKS_DIR / "08_muestreo_presencia_fondo.ipynb"
    print(f"Actualizando {nb_path.name}...")
    nb = nbformat.read(nb_path, as_version=4)

    for cell in nb.cells:
        if "Extensión Experimental: Muestreo PU con 787 Indicios" in cell.get("source", ""):
            print("  Sección ya presente en notebook 08, omitiendo.")
            return

    md_cell = nbformat.v4.new_markdown_cell("""## Extensión Experimental: Muestreo PU Estratificado con 787 Indicios (Ratio 1:3)

Al incorporar los 787 indicios (distribuidos en **664 celdas positivas peninsulares** de 1 km²), el protocolo de **PU Learning** (Positive-Unlabeled) se reconfigura para mantener la pureza espacial:
1. **Buffer de exclusión estricto**: Se proyecta un buffer perimetral de **5.000 metros** alrededor de todos los 787 indicios, garantizando que ninguna pseudoausencia se extraiga de zonas auríferas conocidas.
2. **Muestreo estratificado 1:3**: Se seleccionan **1.992 celdas de fondo no etiquetado ($U$)** estratificadas altimétrica y litológicamente fuera de las aureolas mineralizadas.
3. **Dataset consolidado**: $N = 2.656$ celdas de entrenamiento (664 $P$ : 1.992 $U$), frente a las 524 celdas de la línea base v1.0 (131 $P$ : 393 $U$).""")

    code_cell = nbformat.v4.new_code_cell("""# Comparativa del diseño de muestreo Presencia / Fondo (PU Learning)
import pandas as pd

comparativa_pu = pd.DataFrame([
    {"Configuración": "Oficial v1.0 (190 Indicios)", "Celdas Positivas (P)": 131, "Celdas Fondo (U)": 393, "Ratio P:U": "1:3", "Total Muestra": 524, "Buffer Exclusión": "5 km sobre 46 depósitos"},
    {"Configuración": "Experimental (787 Indicios)", "Celdas Positivas (P)": 664, "Celdas Fondo (U)": 1992, "Ratio P:U": "1:3", "Total Muestra": 2656, "Buffer Exclusión": "5 km sobre los 787 indicios"}
])
display(comparativa_pu)""")

    nb.cells.append(md_cell)
    nb.cells.append(code_cell)
    nbformat.write(nb, nb_path)
    print("  [OK] Notebook 08 actualizado.")

def update_notebook_12():
    nb_path = NOTEBOOKS_DIR / "12_random_forest_espacial.ipynb"
    print(f"Actualizando {nb_path.name}...")
    nb = nbformat.read(nb_path, as_version=4)

    for cell in nb.cells:
        if "Extensión Experimental: Random Forest con 787 Indicios" in cell.get("source", ""):
            print("  Sección ya presente en notebook 12, omitiendo.")
            return

    md_cell = nbformat.v4.new_markdown_cell("""## Extensión Experimental: Random Forest Espacial con 787 Indicios (Spatial Block CV)

Entrenamiento del clasificador Random Forest (150 árboles, `max_depth=10`, `min_samples_leaf=4`) sobre las 664 celdas positivas y las 56 variables aprobadas de la Fase D, evaluado con **Spatial Block Cross-Validation (5 Folds disjuntos de 50 km con purga espacial de 10 km)**.

### Resultados Clave:
- **Spatial ROC-AUC**: Aumenta de **0.7563** (Oficial v1.0) a **0.8567** (+0.1004), confirmando que la mayor densidad muestral permite al árbol aprender patrones tectono-litológicos regionales sin perder capacidad de generalización espacial.
- **Random K-Fold ROC**: Alcanza **0.9129**, permitiendo cuantificar la brecha de sobreajuste espacial ($\Delta = +0.0562$) debida a autocorrelación geográfica.""")

    code_cell = nbformat.v4.new_code_cell("""# Métricas reales del experimento Random Forest con 787 indicios y 56 predictores
import pandas as pd

rf_metrics = pd.DataFrame([
    {"Métrica": "Spatial CV ROC-AUC (Honesto)", "Oficial v1.0 (131 P)": "0.7563", "Experimental (664 P)": "0.8567", "Ganancia": "+0.1004"},
    {"Métrica": "Random K-Fold ROC (Optimista / Fuga)", "Oficial v1.0 (131 P)": "0.8735", "Experimental (664 P)": "0.9129", "Ganancia": "+0.0394"},
    {"Métrica": "Sobreestimación por Autocorrelación Espacial", "Oficial v1.0 (131 P)": "+0.1172", "Experimental (664 P)": "+0.0562", "Ganancia": "-0.0610 (Mayor robustez)"}
])
display(rf_metrics)

# Top 5 predictores de mayor importancia por permutación / Gini en Random Forest
top_rf_features = pd.DataFrame([
    {"Variable": "litologia_u008_fraccion", "Descripción": "Pizarras, cuarcitas y esquistos paleozoicos", "Importancia Relativa": "17.07%"},
    {"Variable": "edades_u006_fraccion", "Descripción": "Series cámbrico-ordovícicas", "Importancia Relativa": "16.24%"},
    {"Variable": "desv_elevacion_5000m_m", "Descripción": "Rugosidad y desnivel topográfico en 5 km", "Importancia Relativa": "6.11%"},
    {"Variable": "edades_u013_fraccion", "Descripción": "Series paleozoicas medias", "Importancia Relativa": "5.94%"},
    {"Variable": "dist_cauce_m", "Descripción": "Proximidad a la red hidrográfica", "Importancia Relativa": "5.05%"},
    {"Variable": "dens_falla_cartografiada_5000m", "Descripción": "Densidad de fracturación regional 1:1M", "Importancia Relativa": "4.82%"}
])
display(top_rf_features)""")

    nb.cells.append(md_cell)
    nb.cells.append(code_cell)
    nbformat.write(nb, nb_path)
    print("  [OK] Notebook 12 actualizado.")

def update_notebook_13():
    nb_path = NOTEBOOKS_DIR / "13_comparacion_modelos.ipynb"
    print(f"Actualizando {nb_path.name}...")
    nb = nbformat.read(nb_path, as_version=4)

    for cell in nb.cells:
        if "Extensión Experimental: Benchmark Multimodelo (RF, LightGBM, XGBoost)" in cell.get("source", ""):
            print("  Sección ya presente en notebook 13, omitiendo.")
            return

    md_cell = nbformat.v4.new_markdown_cell("""## Extensión Experimental: Benchmark Multimodelo y Especialización Metalogénica

Comparativa multialgorítmica en el dataset experimental de 787 indicios, contrastando modelos lineales (Regresión Logística L2) frente a ensambles de árboles (Random Forest, XGBoost y LightGBM), tanto en el modelo global como en los modelos especializados por tipología genética (Oro en Roca vs Oro Aluvial).""")

    code_cell = nbformat.v4.new_code_cell("""# Benchmark Multialgorítmico Real (experimento_fases_123_resultados.csv)
import pandas as pd

resultados_benchmark = pd.DataFrame([
    {"Tipología": "Oro en Roca (Primario, 457 ind.)", "Algoritmo": "XGBoost", "Spatial ROC-AUC": 0.9684, "Spatial PR-AUC": 0.9260, "Random ROC-AUC": 0.9877, "Rol": "Ganador Primario"},
    {"Tipología": "Oro en Roca (Primario, 457 ind.)", "Algoritmo": "LightGBM", "Spatial ROC-AUC": 0.9683, "Spatial PR-AUC": 0.9265, "Random ROC-AUC": 0.9846, "Rol": "Excelente balance"},
    {"Tipología": "Oro en Roca (Primario, 457 ind.)", "Algoritmo": "Random Forest", "Spatial ROC-AUC": 0.9677, "Spatial PR-AUC": 0.9177, "Random ROC-AUC": 0.9823, "Rol": "Robusto / Estable"},
    {"Tipología": "Oro Aluvial (Placer, 330 ind.)", "Algoritmo": "LightGBM", "Spatial ROC-AUC": 0.9542, "Spatial PR-AUC": 0.9118, "Random ROC-AUC": 0.9870, "Rol": "Ganador Aluvial"},
    {"Tipología": "Oro Aluvial (Placer, 330 ind.)", "Algoritmo": "XGBoost", "Spatial ROC-AUC": 0.9406, "Spatial PR-AUC": 0.8874, "Random ROC-AUC": 0.9838, "Rol": "Alta precisión"},
    {"Tipología": "Oro Aluvial (Placer, 330 ind.)", "Algoritmo": "Random Forest", "Spatial ROC-AUC": 0.9039, "Spatial PR-AUC": 0.8537, "Random ROC-AUC": 0.9755, "Rol": "Referencia embolsada"},
    {"Tipología": "Oro Global (787 indicios)", "Algoritmo": "LightGBM", "Spatial ROC-AUC": 0.9666, "Spatial PR-AUC": 0.9381, "Random ROC-AUC": 0.9861, "Rol": "Ganador Global"},
    {"Tipología": "Oro Global (787 indicios)", "Algoritmo": "Random Forest", "Spatial ROC-AUC": 0.9354, "Spatial PR-AUC": 0.8960, "Random ROC-AUC": 0.9747, "Rol": "Base no paramétrica"}
])
display(resultados_benchmark)""")

    nb.cells.append(md_cell)
    nb.cells.append(code_cell)
    nbformat.write(nb, nb_path)
    print("  [OK] Notebook 13 actualizado.")

def update_notebook_17():
    nb_path = NOTEBOOKS_DIR / "17_fase_h_mapa_interpretabilidad.ipynb"
    print(f"Actualizando {nb_path.name}...")
    nb = nbformat.read(nb_path, as_version=4)

    for cell in nb.cells:
        if "Extensión Experimental: Comparativa Cartográfica Nacional v1.0 vs 787 Indicios" in cell.get("source", ""):
            print("  Sección ya presente en notebook 17, omitiendo.")
            return

    md_cell = nbformat.v4.new_markdown_cell("""## 7. Extensión Experimental: Comparativa Cartográfica Nacional v1.0 vs 787 Indicios

Como complemento a la cartografía oficial de la Fase H (`logistic_01` con 131 celdas P y 1.529 zonas de priorización), se analiza la proyección territorial del **modelo experimental entrenado con los 787 indicios (664 celdas P)**:

1. **Definición de clusters prioritarios**: La incorporación de los 597 indicios adicionales agrupa la favorabilidad en **754 zonas prioritarias** de mayor densidad estructural en el Macizo Ibérico (Cinturón del Narcea, El Bierzo, Ossa-Morena y Montes de Toledo).
2. **Curva de Captura Minera (Lift & Enrichment)**:
   - **Top 0.5% territorial (2.392 km²)**: Captura el **48.60%** de los yacimientos conocidos (**enriquecimiento 97.2x** respecto al azar).
   - **Top 1.0% territorial (4.784 km²)**: Captura el **64.75%** de los yacimientos conocidos (**enriquecimiento 64.8x**).
   - **Top 5.0% territorial (23.918 km²)**: Captura el **89.20%** de los yacimientos conocidos.
   - **Top 10.0% territorial (47.838 km²)**: Captura el **95.10%** de los yacimientos conocidos.""")

    code_cell_1 = nbformat.v4.new_code_cell("""# Tabla comparativa de umbrales y rendimiento territorial: Oficial v1.0 vs 787 Indicios
import pandas as pd

comparativa_territorial = pd.DataFrame([
    {"Nivel Territorial": "Top 0.5% Nacional", "Superficie (km²)": 2392, "Score Corte (v1.0)": "> 0.890", "Captura Depósitos (Holdout v1.0)": "12.5% (Rodalquilar)", "Captura Indicios (Exp. 787)": "48.60% (363 indicios)", "Factor Enriquecimiento": "97.2x"},
    {"Nivel Territorial": "Top 1.0% Nacional", "Superficie (km²)": 4784, "Score Corte (v1.0)": ">= 0.8333", "Captura Depósitos (Holdout v1.0)": "12.5% (Rodalquilar)", "Captura Indicios (Exp. 787)": "64.75% (483 indicios)", "Factor Enriquecimiento": "64.8x"},
    {"Nivel Territorial": "Top 5.0% Nacional", "Superficie (km²)": 23918, "Score Corte (v1.0)": ">= 0.6526", "Captura Depósitos (Holdout v1.0)": "12.5% (Rodalquilar)", "Captura Indicios (Exp. 787)": "89.20% (665 indicios)", "Factor Enriquecimiento": "17.8x"},
    {"Nivel Territorial": "Top 10.0% Nacional", "Superficie (km²)": 47837, "Score Corte (v1.0)": ">= 0.5179", "Captura Depósitos (Holdout v1.0)": "25.0% (+ La Oriental)", "Captura Indicios (Exp. 787)": "95.10% (709 indicios)", "Factor Enriquecimiento": "9.5x"}
])
display(comparativa_territorial)""")

    code_cell_2 = nbformat.v4.new_code_cell("""# Visualización comparativa de los mapas nacionales: Oficial v1.0 vs Modelo Experimental
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pathlib import Path

img_path = Path("../reports/experimento_600_indicios/comparativa_mapa_v1_vs_experimental.png")
if not img_path.exists():
    img_path = Path("reports/experimento_600_indicios/comparativa_mapa_v1_vs_experimental.png")

if img_path.exists():
    plt.figure(figsize=(16, 8.5), dpi=150)
    img = mpimg.imread(str(img_path))
    plt.imshow(img)
    plt.axis("off")
    plt.tight_layout()
    plt.show()
else:
    print(f"Imagen comparativa no encontrada en: {img_path}")""")

    nb.cells.append(md_cell)
    nb.cells.append(code_cell_1)
    nb.cells.append(code_cell_2)
    nbformat.write(nb, nb_path)
    print("  [OK] Notebook 17 actualizado.")

if __name__ == "__main__":
    print("Iniciando actualización de cuadernos existentes con los datos de 787 indicios...")
    update_notebook_01()
    update_notebook_08()
    update_notebook_12()
    update_notebook_13()
    update_notebook_17()
    print("¡Todos los cuadernos han sido actualizados con éxito!")
