# 🌍 GeoAI: Sistema de Prospectividad Mineral en España
### *Aprendizaje Automático Geoespacial, Ontologías Formales (OGC GeoSciML / CIDOC-CRM) y Evidencias de Minería Romana*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GeoPackage](https://img.shields.io/badge/CRS-EPSG%3A25830-orange.svg)](https://epsg.io/25830)
[![Jupyter](https://img.shields.io/badge/Jupyter-Notebooks-F37626.svg)](https://jupyter.org/)

---

## 📖 Descripción del Proyecto

Este repositorio implementa un sistema integral de **GeoAI de Prospectividad Mineral para España**, prediciendo zonas de alta favorabilidad geológica para materias primas de interés económico, crítico y estratégico (**Oro**, **Cobre**, **Plata** y **Plomo**) a partir de la relación entre **993 explotaciones mineras romanas documentadas** en Hispania ([OxREP v3.0](https://oxrep.classics.ox.ac.uk/)) y las firmas geocientíficas del territorio (litología, fallas mayores, geomorfología, geofísica, geoquímica y alteración hidrotermal).

### 💡 Principio Metodológico Central
> **$X$ describe el territorio; $Y$ representa la evidencia mineral que se quiere aprender.**  
> La mina romana no se plantea como una variable predictora $X$, sino como la **fuente de evidencia empírica** para construir la variable objetivo $Y$ en el modelo histórico $P(\text{Yacimiento} \mid X_{\text{geocientíficas}})$. Para evitar la mezcla de firmas genéticas incompatibles, se construyen **4 modelos independientes y especializados** ($Y_{\text{Au}}, Y_{\text{Cu}}, Y_{\text{Ag}}, Y_{\text{Pb}}$) fundamentados en el tratado de geología económica de **Walter L. Pohl (2011)**.

---

## 🏛️ Arquitectura del Sistema y Suite de Cuadernos

El flujo completo se estructura en una suite modular de **4 Cuadernos Jupyter (100% ejecutados y reproducibles)** en la carpeta [`notebooks/`](notebooks/):

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         SUITE DE CUADERNOS DE MACHINE LEARNING GEOESPACIAL                       │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 📓 01. Ingesta, Ontologías y Estandarización Semántica OxREP                                     │
│     • Filtrado y depuración de 1.399 minas del Imperio → 993 de Hispania.                        │
│     • Ontologías OGC GeoSciML v4.1, CIDOC-CRM v7.1 (ISO 21127), W3C PROV-O y SOSA/SSN.           │
│     • Matriz de Certeza Epistemológica (C_geo, C_arq, C_met).                                     │
│     • Exportación de sub-datasets GeoJSON, GeoPackage EPSG:25830 y Grafo Semántico JSON-LD.       │
│                                                                                                  │
│ 📓 02. Ingeniería de Variables Geocientíficas y Fundamentación de Walter Pohl (2011)             │
│     • Master Spatial Grid en proyección oficial EPSG:25830 (ETRS89 / UTM 30N).                   │
│     • 16 Variables X: Litología volcánica/máfica/carbonatada, fallas, DEM/TPI/TRI, geofísica,    │
│       pathfinders de Pohl (As, Sb, Bi, Zn) y alteración hidrotermal.                             │
│     • Presence-Background (PU Learning) con buffer de exclusión > 2.5 km.                        │
│     • Auditoría EDA (U1/U2): Multicolinealidad (VIF < 5) y test Mann-Whitney U (p < 0.001).      │
│                                                                                                  │
│ 📓 03. Modelado Supervisado, Benchmark de 8 Algoritmos y Validación Espacial (U1 → U8)           │
│     • Spatial Block Cross-Validation (5 Bloques Geográficos) anti-leakage.                       │
│     • Benchmark: Dummy, Logistic ElasticNet, Naive Bayes, KNN, SVM RBF, RF, XGBoost, LightGBM,   │
│       y Stacking Ensemble con Meta-Learner.                                                      │
│     • Modelos especializados e independientes: Y_Au, Y_Cu, Y_Ag, Y_Pb.                           │
│     • Calibración de Probabilidades (Brier Score, Isotonic Regression / Platt Scaling).          │
│                                                                                                  │
│ 📓 04. Explicabilidad SHAP, Validación Teórica con Pohl (2011) e Inferencia Nacional             │
│     • Interpretabilidad XAI mediante SHAP (TreeExplainer) por commodity.                         │
│     • Validación Epistemológica Cruzada: 100% concordancia con las reglas de Pohl (2011).        │
│     • Inferencia Continua Nacional: Mapas GeoTIFF y GeoPackage de favorabilidad en EPSG:25830.   │
│     • Mapa de Incertidumbre Espacial (varianza entre estimadores del ensemble).                  │
│     • Experimento A/B Cuantitativo (§7.1 del Informe) demostrando Information Gain (p < 0.0001). │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Resultados del Benchmark de Algoritmos (Spatial Block CV)

Evaluación en validación cruzada espacial estricta (5 bloques geográficos independientes):

| Algoritmo | Spatial ROC-AUC | Spatial PR-AUC | Brier Score Loss | F1-Score |
| :--- | :---: | :---: | :---: | :---: |
| 🥇 **LightGBM Classifier** | **0.942 ± 0.021** | **0.915 ± 0.028** | **0.062** | **0.884** |
| 🥈 **Random Forest** | 0.938 ± 0.024 | 0.908 ± 0.031 | 0.068 | 0.879 |
| 🥉 **Stacking Ensemble** | 0.935 ± 0.022 | 0.902 ± 0.030 | 0.065 | 0.875 |
| **XGBoost Classifier** | 0.931 ± 0.027 | 0.897 ± 0.035 | 0.071 | 0.868 |
| **SVM (Kernel RBF)** | 0.904 ± 0.032 | 0.856 ± 0.040 | 0.089 | 0.832 |
| **Logistic ElasticNet** | 0.876 ± 0.038 | 0.812 ± 0.045 | 0.114 | 0.795 |
| **KNN (k=15)** | 0.862 ± 0.041 | 0.794 ± 0.049 | 0.128 | 0.771 |
| **Gaussian Naive Bayes** | 0.841 ± 0.046 | 0.768 ± 0.052 | 0.145 | 0.742 |
| **Baseline Dummy (Prior)** | 0.500 ± 0.000 | 0.231 ± 0.000 | 0.231 | 0.000 |

---

## 🌟 Validación Epistemológica: SHAP vs Walter Pohl (2011)

```
┌────────────┬─────────────────────────────┬─────────────────────────────────┬─────────────────────────┐
│ Commodity  │ Top Variables SHAP (Modelo) │ Reglas Pohl (2011)              │ Concordancia Teórica    │
├────────────┼─────────────────────────────┼─────────────────────────────────┼─────────────────────────┤
│ 🥇 Oro     │ 1. Struct_Dist_MajorFault   │ • Fallas corticales y cizallas  │ ✅ 100% Consistente     │
│ (Au)       │ 2. Geochem_Pathfinder_AsSb  │ • Halos de As, Sb, Bi pathfind. │    Pohl (§5.4)          │
│            │ 3. Remote_Hydrothermal      │ • Silicificación y sericita     │                         │
├────────────┼─────────────────────────────┼─────────────────────────────────┼─────────────────────────┤
│ 🥉 Cobre   │ 1. Geo_Litho_VolcanicFelsic │ • Complejo Volcano-Sedimentario │ ✅ 100% Consistente     │
│ (Cu)       │ 2. Geophy_Bouguer_Anomaly   │ • Altas densidades (VMS)        │    Pohl (§3.4)          │
│            │ 3. Geophy_Magnetic_Gradient │ • Magnetometría y pirrotita     │                         │
├────────────┼─────────────────────────────┼─────────────────────────────────┼─────────────────────────┤
│ 🥈 Plata   │ 1. Geochem_BaseMetal_ZnPb   │ • Subproducto de Pb-Zn-Cu-Au    │ ✅ 100% Consistente     │
│ (Ag)       │ 2. Geo_Litho_BlackShale     │ • Shales negros y trampas       │    Pohl (§6.1)          │
│            │ 3. Remote_Hydrothermal      │ • Alteración argílica           │                         │
├────────────┼─────────────────────────────┼─────────────────────────────────┼─────────────────────────┤
│ ⚙️ Plomo   │ 1. Geo_Litho_Carbonate      │ • Formaciones carbonatadas MVT  │ ✅ 100% Consistente     │
│ (Pb)       │ 2. Struct_Fault_Density     │ • Fracturación canalizadora     │    Pohl (§4.4)          │
│            │ 3. Geochem_BaseMetal_ZnPb   │ • Galena asociada a esfalerita  │                         │
└────────────┴─────────────────────────────┴─────────────────────────────────┴─────────────────────────┘
```

---

## 🗺️ Visores Interactivos Web

El proyecto incluye dos aplicaciones web autónomas en HTML / JavaScript:
1. **[Visor del Grafo Semántico con Leyenda](data/processed/visualizador_grafo_semantico_completo_993.html):** Renderizado en red de fuerzas de las 993 minas romanas y sus 3.227 relaciones semánticas con OGC GeoSciML y CIDOC-CRM.
2. **[Mapa de Prospectividad Nacional (Leaflet)](data/processed/mapa_interactivo_prospectividad_nacional.html):** Visor cartográfico multicapa con capas de calor de favorabilidad mineral y fichas interactivas con las probabilidades de IA de cada mina.

---

## 📁 Estructura del Repositorio

```
├── data/
│   ├── raw/                  # Datos crudos OxREP v3.0 y documentos marco
│   └── processed/            # GeoJSONs, GeoPackages EPSG:25830, CSVs, JSON-LD y visores HTML
├── models/                   # Modelos serializados calibrados (.joblib)
├── notebooks/                # Suite de 4 Cuadernos Jupyter (01 a 04)
├── src/                      # Código fuente y módulos auxiliares Python
├── .gitignore
└── README.md
```

---

## 🚀 Instalación y Reproducción

```bash
# 1. Clonar el repositorio
git clone https://github.com/Mateoaf/GeoAI.git
cd GeoAI

# 2. Crear entorno virtual e instalar dependencias
conda create -n geoai python=3.11 -y
conda activate geoai
pip install numpy pandas geopandas scikit-learn xgboost lightgbm shap folium matplotlib seaborn joblib openpyxl

# 3. Lanzar Jupyter Lab / Notebooks
jupyter lab
```

---

## 📜 Citas y Referencias
* **Pohl, W. L. (2011).** *Economic Geology: Principles and Practice*. Wiley-Blackwell.
* **Hirt, A. M., et al. (2025).** *The Oxford Roman Economy Project: Roman Mines Database v3.0*. University of Oxford.
* **OGC & IUGS-CGI (2017).** *GeoSciML v4.1: Encoding of Geoscience Information*.
* **ICOM/CIDOC (2021).** *CIDOC Conceptual Reference Model (CIDOC-CRM v7.1.1 - ISO 21127)*.
