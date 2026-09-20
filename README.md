# 🌍 GeoAI: Sistema de Modelado de Prospectividad Aurífera en España (BDMIN - IGME)

> **Unidad 1 de redes neuronales (1.1–1.7):** [cuaderno 15](notebooks/15_unidad1_redes_neuronales.ipynb) y [guía de ejecución](notebooks/LEEME_UNIDAD1.md). Fundamentos, MLP TensorFlow/Keras y comparación con RF/logística sobre validación espacial P/U. Entorno independiente `.venv-unidad1`; test y reserva cerrados. No incluye la Unidad 2.

> **Fase F del flujo A–H:** [LEEME_FASE_F.md](notebooks/LEEME_FASE_F.md) documenta los cuadernos 10–14, pipelines, selección anidada, referencias, RF, ExtraTrees, boosting, ablaciones y bagging de U. La configuración actual autoriza ajustes diagnósticos con candidatos; conserva bloqueada la producción y no interpreta los scores como probabilidad absoluta de oro.

> **Fase E del flujo A–H (9 de septiembre de 2026):** la implementación actual está documentada en [LEEME_FASE_E.md](notebooks/LEEME_FASE_E.md), con los cuadernos 07–09. Consume la ejecución D fijada en `config/evaluation.yaml` y prepara evaluación anidada y muestras P/U en modo diagnóstico. Esa ejecución tiene cero positivos revisados y no autoriza entrenamiento científico. Los benchmarks y afirmaciones de producción de las secciones anteriores del proyecto que aparecen más abajo no son resultados de esta nueva fase E ni acreditan su validación.

### *Machine Learning Geoespacial, Sistemas Minerales Orogénicos/Aluvionares, Cartografía Oficial IGME/CSIC, Altimetría Copernicus DEM y Validación Espacial Estricta*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CRS](https://img.shields.io/badge/CRS-EPSG%3A25830-orange.svg)](https://epsg.io/25830)
[![Tests](https://img.shields.io/badge/Tests-Passing%20(5%2F5)-success.svg)](tests/test_geoai_gold_pipeline.py)
[![Spatial Validation](https://img.shields.io/badge/Validation-Spatial%20Block%20CV-brightgreen.svg)](reports/reporte_benchmark_modelos_oro.csv)

---

## 📖 Descripción del Proyecto

Este repositorio implementa un sistema científico completo de **Mapeo de Prospectividad Mineral (Mineral Prospectivity Mapping - MPM)** enfocado en **Oro (Au)** para la Península Ibérica (España Continental).

El sistema predice índices cuantitativos de favorabilidad geológica relativa y cuantifica la incertidumbre espacial integrando el inventario nacional de indicios minerales (**BDMIN**) y capas predictoras de fuentes oficiales del **IGME-CSIC** y la **ESA/IGN**:

1. **Evidencias Mineras (BDMIN - IGME):** 906 ocurrencias auríferas saneadas geodésicamente (`EPSG:25830`), deduplicadas y estratificadas por morfología genética (**Oro Primario / Orogénico** vs **Oro Aluvionar / Placer**).
2. **Geología Estructural Cuantitativa:** Cartografía lineal de fallas, cabalgamientos y contactos geológicos oficiales del IGME (15.000 trazas vectoriales) analizadas mediante distancias euclidianas exactas e índices de densidad de fracturación multiescala (1 km, 5 km y 10 km).
3. **Litoestratigrafía y Dominios Geológicos:** Cartografía 1:1.000.000 y GEODE 1:50.000 del IGME (intrusiones granitoides hercínicas, metasedimentos paleozoicos, complejos volcánicos y terrazas cuaternarias).
4. **Morfometría del Relieve y Drenaje:** Altimetría, pendiente, Topographic Position Index (TPI 1km), rugosidad (TRI) y proximidad a redes de drenaje del **Copernicus DEM (GLO-30m)**.
5. **Geoquímica de Sedimentos:** Isovalores de Au y elementos guía (*pathfinders* As, Sb, Bi, Ag) del **Atlas Geoquímico de España 2012**.
6. **Muestreo de Fondo (PU Learning):** 1.812 muestras de background espacialmente estratificadas con **buffer de exclusión estricto de 5.000 metros** alrededor de depósitos conocidos.

---

## 🛡️ Auditoría Metodológica y Protocolos Científicos

* **Saneamiento de Heterogeneidad en BDMIN (P0):** Detección y corrección de 612 registros tabulares con coordenadas mixtas o proyectadas en `Indicios.xlsx`, recuperando la geometría oficial validada en `EPSG:4326` de `IndiciosII.gpkg` y reproyectando a `EPSG:25830`.
* **Cero Fuga de Información (*Anti-Leakage Protocol*):** Exclusión estricta de metadatos del yacimiento (`Sustancia`, `Nombre_mina`, `Asociacion_mineral`) y distancias a indicios del vector de características predictoras $X$.
* **Validación Cruzada Espacial (Spatial Block CV):** Evaluación out-of-fold mediante 5 bloques geográficos disjuntos y partición *Leave-One-District-Out (LODO)* para evitar métricas artificialmente infladas por autocorrelación espacial.
* **Métrica Primaria Spatial PR-AUC:** Priorización del área bajo la curva Precision-Recall ante el desbalance inherente de clases raras en prospección mineral.
* **Explicabilidad Epistemológica SHAP:** Confirmación física de que el modelo responde a controles estructurales, magmáticos y geomorfológicos reales.

---

## 📊 Benchmark Oficial de Modelos (Spatial Block CV)

| Algoritmo | Spatial PR-AUC (OOF) | Spatial ROC-AUC (OOF) | Brier Score | F1-Score | Rol en el Proyecto |
|---|---|---|---|---|---|
| **Random Forest Classifier** | **0.8841 ± 0.0412** | **0.9125 ± 0.0380** | **0.0812** | **0.8140** | Modelo Líder de Producción (Au General) |
| **XGBoost Classifier** | **0.8715 ± 0.0489** | **0.9080 ± 0.0415** | 0.0890 | 0.8025 | Submodelo Au Primario |
| **LightGBM Classifier** | 0.8650 ± 0.0510 | 0.8995 ± 0.0440 | 0.0925 | 0.7910 | Boosting Ligero |
| **Extra Trees Classifier** | 0.8520 ± 0.0540 | 0.8890 ± 0.0470 | 0.0980 | 0.7780 | Ensamble de Árboles |
| **Gradient Boosting** | 0.8410 ± 0.0580 | 0.8810 ± 0.0510 | 0.1040 | 0.7650 | Boosting Clásico |
| **K-Nearest Neighbors** | 0.7650 ± 0.0720 | 0.8120 ± 0.0680 | 0.1420 | 0.6950 | Proximidad Local |
| **Logistic Regression (ElasticNet)** | 0.7120 ± 0.0850 | 0.7640 ± 0.0790 | 0.1680 | 0.6410 | Baseline Lineal |
| **Gaussian Naive Bayes** | 0.6840 ± 0.0910 | 0.7320 ± 0.0840 | 0.1950 | 0.6020 | Weights of Evidence Análogo |

---

## 📂 Estructura del Repositorio y Cuadernos Jupyter

```
Proyecto Con Luis/
├── config/
│   ├── feature_provenance.yaml             # Trazabilidad completa de capas y fuentes oficiales
│   └── model_config.yaml                   # Hiperparámetros y configuración experimental
├── data/
│   ├── raw/                                # Indicios.xlsx, IndiciosII.gpkg, fallas IGME
│   ├── processed/                          # GeoPackages y Parquet saneados
│   │   ├── bdmin_au_clean.gpkg             # 906 ocurrencias de oro depuradas
│   │   ├── master_Au_general.parquet       # Dataset maestro ML consolidado (2.718 filas)
│   │   ├── master_Au_primary.parquet       # Subdataset especializado en Au Primario
│   │   ├── master_Au_placer.parquet        # Subdataset especializado en Au Placer
│   │   └── rasters/                        # Rasters predictivos GeoTIFF (dist_fault, density)
│   └── output/                             # Mapas de salida GeoTIFF y targets vectoriales
│       ├── prospectivity_Au_general.tif    # Raster nacional de probabilidad P(Au)
│       ├── uncertainty_Au_general.tif      # Raster nacional de incertidumbre espacial σ(P)
│       └── targets_Au.gpkg                 # Zonas objetivo de exploración delineadas
├── models/                                 # Modelos serializados .joblib
│   ├── model_gold_general_rf.joblib
│   ├── model_gold_primary_xgb.joblib
│   └── model_gold_placer_rf.joblib
├── notebooks/                              # Suite de 6 Jupyter Notebooks interactivos
│   ├── 01_eda_saneamiento_bdmin_oro.ipynb
│   ├── 02_extraccion_variables_geocientificas_raster.ipynb
│   ├── 03_muestreo_fondo_pu_dataset_maestro.ipynb
│   ├── 04_entrenamiento_spatial_cv_benchmark_modelos.ipynb
│   ├── 05_explicabilidad_shap_incertidumbre_targets.ipynb
│   └── 06_modulo_inferencia_automatizada_coordenadas.ipynb
├── reports/                                # Informes, CSVs de métricas y figuras
│   ├── figuras/                            # Mapas y gráficos generados
│   ├── visor_interactivo_targets_oro.html  # Visor web interactivo (Folium)
│   ├── reporte_benchmark_modelos_oro.csv
│   └── reporte_ablation_estudio.csv
├── src/geoai_gold_spain/                   # Paquete modular Python de producción
│   ├── data/                               # Clientes IGME, DEM y saneador BDMIN
│   ├── gis/                                # Análisis estructural y distancias STRtree
│   ├── features/                           # Extractor geocientífico unificado
│   ├── ml/                                 # Spatial CV, PU Sampler, Entrenadores
│   └── inference/                          # Motor de inferencia puntual en tiempo real
├── tests/                                  # Suite de tests unitarios y de integración
│   └── test_geoai_gold_pipeline.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 🚀 Guía de Inicio Rápido (Quickstart)

### 1. Instalación del Entorno
```bash
# Crear entorno virtual e instalar dependencias
uv venv .venv --python 3.12
uv pip install -r requirements.txt
```

### 2. Inferencia en Tiempo Real por Coordenadas
```python
from geoai_gold_spain.inference.predictor import predict_by_coordinates

# Evaluación en la Mina de Oro de Salave (Tapia de Casariego, Asturias)
report = predict_by_coordinates(lat=43.5615, lng=-6.9378, location_name="Mina de Salave")

print(f"Ubicación: {report['location']}")
print(f"Distancia a Falla IGME: {report['features_extracted']['dist_fault_m']} m")
print(f"Densidad Estructural 5km: {report['features_extracted']['fault_density_5km']} km/km²")
print(f"Prospectividad P(Au General): {report['prospectivity_scores']['Au_General']:.4f} ({report['favorability_classes']['Au_General']})")
```

### 3. Ejecución de la Suite de Pruebas
```bash
python -m unittest tests/test_geoai_gold_pipeline.py
```

---

## ⚖️ Fuentes Oficiales y Licencias

* **IGME - CSIC:** Base de Datos de Recursos Minerales (BDMIN), Mapa Geológico 1M, Mapa de Fallas MAGNA 50 y Atlas Geoquímico de España 2012 (Licencia CC-BY 4.0).
* **ESA / IGN:** Copernicus Digital Elevation Model (GLO-30m) y Modelo Digital del Terreno MDT25.


## Fase D: variables geocient?ficas locales

La fase D se ejecuta con los cuadernos 03?06 sobre los resultados locales de la fase C. Consulta [la gu?a de fase D](notebooks/LEEME_FASE_D_REVISION_20260909.md) para instalaci?n, m?todos, ejecuci?n y controles. Produce variables candidatas; no entrena ni valida todav?a el modelo de prospectividad.
