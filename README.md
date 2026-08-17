# 🌍 GeoAI: Sistema de Mapeo de Prospectividad Mineral (MPM) en España
### *Aprendizaje Automático Geoespacial, Geología Estructural Oficial (IGME/CSIC), Topografía DEM (Copernicus) y Validación Espacial Estricta*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GeoPackage](https://img.shields.io/badge/CRS-EPSG%3A25830-orange.svg)](https://epsg.io/25830)
[![Audit](https://img.shields.io/badge/Scientific%20Audit-Hardened%20v2.0-brightgreen.svg)](reports/geoai_scientific_audit.md)
[![Tests](https://img.shields.io/badge/Tests-Passing%20(5%2F5)-success.svg)](tests/run_tests.py)

---

## 📖 Descripción del Proyecto

Este repositorio implementa un sistema científico de **Mapeo de Prospectividad Mineral (Mineral Prospectivity Mapping - MPM)** para la Península Ibérica. El sistema predice índices de favorabilidad geológica relativa para cuatro materias primas metálicas clave (**Oro**, **Cobre**, **Plata** y **Plomo**) a partir de evidencias mineras históricas e indicios geológicos, integrando variables geocientíficas observadas y derivadas de fuentes oficiales:

* **Geología y Estratigrafía:** Mapa Geológico Continuo 1:1.000.000 del **IGME-CSIC** (`LITOGENER`, `EON_ERA`, `DOMINIO`).
* **Geología Estructural:** Cartografía vectorial lineal de Fallas, Cabalgamientos y Contactos del **IGME Capa 2** (15.000 entidades geométricas).
* **Morfometría del Relieve:** Altimetría y derivadas (pendiente, TPI 1km, TRI) del **Copernicus Digital Elevation Model GLO-30m / IGN**.
* **Muestreo de Fondo (PU Learning):** 800 muestras de *background* estratificado con **buffer de exclusión espacial de 5 km** respecto a cualquier mina conocida.

---

## 🛡️ Auditoría Científica y Endurecimiento v2.0

En la versión 2.0 se realizó una **auditoría integral de severidad P0/P1** para erradicar cualquier fuga de información (*Target Leakage*) o dependencia de variables heurísticas:

1. **Eliminación de Fuga en Distancia a Fallas (P0):** Se corrigió la función que construía índices espaciales a partir de coordenadas de las minas. Las distancias y densidades se calculan ahora exclusivamente contra las trazas de fallas reales vectoriales del IGME.
2. **Erradicación de Proxies Sintéticos (P0):** Se eliminaron las concentraciones geoquímicas y espectrales sintéticas que habían sido condicionadas por el *commodity* minero.
3. **Registro de Procedencia y Trazabilidad:** Documentado en [`config/feature_provenance.yaml`](config/feature_provenance.yaml).
4. **Paridad Training-Serving:** Un único extractor geocientífico unificado ([`src/geoai_roman_spain/features/extractor.py`](src/geoai_roman_spain/features/extractor.py)) alimenta tanto la construcción del dataset como la inferencia en producción.
5. **Ablation Test de Coordenadas:** Se evaluó el modelo con y sin coordenadas ($X, Y$) para demostrar que aprende firmas litológico-estructurales transferibles y no memorización de distritos.

Documentos de referencia:
* 📄 [`reports/geoai_scientific_audit.md`](reports/geoai_scientific_audit.md): Informe detallado de hallazgos y correcciones.
* 📄 [`reports/decision_log.md`](reports/decision_log.md): Registro de decisiones metodológicas.
* 📄 [`reports/geoai_v2_model_benchmark.md`](reports/geoai_v2_model_benchmark.md): Resultados completos del benchmark espacial.

---

## 📊 Benchmark Oficial GeoAI v2 (Evaluación Espacial out-of-fold)

Evaluado mediante **Spatial Block Cross-Validation (5 Bloques Geográficos)** y calibración isotónica:

| Commodity | Positivos | Spatial ROC-AUC | Spatial PR-AUC | Brier Score (OOF) | Modelo Serializado |
|---|---|---|---|---|---|
| **Oro (Au)** | 637 | **0.7936 ± 0.1681** | **0.4253 ± 0.3309** | 0.2465 | [`models/v2/model_geoai_v2_Au_Oro.joblib`](models/v2/model_geoai_v2_Au_Oro.joblib) |
| **Cobre (Cu)** | 186 | **0.6602 ± 0.1315** | **0.1747 ± 0.1890** | 0.1114 | [`models/v2/model_geoai_v2_Cu_Cobre.joblib`](models/v2/model_geoai_v2_Cu_Cobre.joblib) |
| **Plata (Ag)** | 179 | **0.5526 ± 0.2217** | **0.1620 ± 0.1688** | 0.1055 | [`models/v2/model_geoai_v2_Ag_Plata.joblib`](models/v2/model_geoai_v2_Ag_Plata.joblib) |
| **Plomo (Pb)** | 170 | **0.6064 ± 0.2051** | **0.2025 ± 0.1663** | 0.1002 | [`models/v2/model_geoai_v2_Pb_Plomo.joblib`](models/v2/model_geoai_v2_Pb_Plomo.joblib) |

### Transferencia Geográfica (Leave-One-District-Out - LODO):
* **Cobre en la Faja Pirítica Ibérica:** ROC-AUC: **0.9162**, PR-AUC: **0.9399** (Generalización sobresaliente en dominio VMS).
* **Plata y Plomo en Sierra Morena (Linares-Alcudia):** ROC-AUC: **0.7205 - 0.7406**, PR-AUC: **0.7391 - 0.7571** (Especialización hidrotermal filoniana).
* **Oro en el Sureste Bético (Rodalquilar / Mazarrón):** ROC-AUC: **0.9802**, PR-AUC: **0.6429**.

---

## 🚀 Uso Rápido (Quickstart)

### 1. Instalación
```bash
git clone https://github.com/Mateoaf/GeoAI.git
cd GeoAI
pip install -r requirements.txt
```

### 2. Inferencia por Coordenadas en Python
```python
from geoai_roman_spain import predict_by_coordinates

# Evaluación geocientífica en tiempo real (Riotinto, Huelva)
report = predict_by_coordinates(lat=37.6930, lng=-6.5940, location_name="Minas de Riotinto")

print(f"Ubicación: {report['location']}")
print(f"Litología IGME: {report['features_extracted']['Real_IGME_Lithology_General']}")
print(f"Distancia a Falla IGME: {report['features_extracted']['Real_IGME_Dist_Fault_m']} m")
print(f"Scores de Prospectividad:")
for comm, score in report['prospectivity_scores'].items():
    print(f"  • {comm}: {score:.4f} ({report['favorability_classes'][comm]})")
```

### 3. Ejecución de la Suite de Pruebas
```bash
python tests/run_tests.py
```

---

## 📂 Estructura del Repositorio

```
GeoAI/
├── config/
│   └── feature_provenance.yaml    # Trazabilidad completa de variables y licencias
├── data/
│   ├── interim/
│   │   └── igme_faults_lines.gpkg # 15.000 geometrías lineales de fallas IGME
│   └── processed/
│       ├── ml_dataset_real_v2.csv # Dataset maestro ML v2 auditado (1.793 registros)
│       └── ml_dataset_real_v2.gpkg
├── models/
│   └── v2/                        # Modelos calibrados de producción v2 (Au, Cu, Ag, Pb)
├── reports/
│   ├── geoai_scientific_audit.md  # Informe de auditoría P0/P1
│   ├── decision_log.md            # Registro de decisiones de arquitectura
│   └── geoai_v2_model_benchmark.md# Benchmark espacial riguroso
├── src/
│   ├── geoai_roman_spain/
│   │   ├── data_sources/          # Conectores a IGME REST y Copernicus DEM
│   │   ├── gis/                   # Análisis estructural de líneas y densidades
│   │   ├── features/              # Extractor geocientífico unificado
│   │   ├── ml/                    # Spatial Block CV, LODO, Ablation, Trainer
│   │   └── inference/             # Motor de predicción de producción
│   ├── build_ml_dataset_v2.py
│   └── run_spatial_experiments_v2.py
├── tests/
│   ├── run_tests.py               # Suite de validación y control de calidad
│   └── test_geoai_pipeline.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## ⚖️ Licencia y Cita Científica

Distribuido bajo licencia MIT. Las fuentes de datos originales pertenecen a sus respectivos proveedores oficiales:
* **IGME - CSIC:** Mapa Geológico Continuo 1M y Capa de Fallas (Licencia CC-BY 4.0).
* **ESA / IGN:** Copernicus Digital Elevation Model (GLO-30m) / MDT Nacional.
* **OxREP:** Oxford Roman Economy Project ([oxrep.classics.ox.ac.uk](https://oxrep.classics.ox.ac.uk/)).
