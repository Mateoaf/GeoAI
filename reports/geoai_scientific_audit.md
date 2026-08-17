# 🛡️ Informe Oficial de Auditoría Científica y Endurecimiento GeoAI (MPM)

**Proyecto:** GeoAI - Mapeo de Prospectividad Mineral en España (Mineral Prospectivity Mapping)  
**Repositorio:** `https://github.com/Mateoaf/GeoAI.git`  
**Fecha:** Agosto 2026  
**Auditor:** Antigravity AI Geoscience Team  

---

## 1. Resumen Ejecutivo y Diagnóstico Global

El prototipo inicial de GeoAI demostró con éxito la viabilidad de la integración web GIS y la serialización de modelos de machine learning. Sin embargo, una auditoría técnica y metodológica exhaustiva de la base de código y los pipelines de datos reveló **vulnerabilidades críticas de severidad P0 y P1**, incluyendo **fugas de información del target (Target Leakage)**, **heurísticas ocultas en inferencia**, **memorización de coordenadas** y **sustitución de geometrías de fallas por coordenadas de las propias minas**.

Este documento cataloga cada problema encontrado, evalúa su riesgo científico y detalla la solución técnica implementada para transformar el proyecto en un sistema **científicamente defendible, reproducible y sin variables sintéticas**.

---

## 2. Matriz de Hallazgos y Severidad

| ID | Severidad | Componente / Archivo | Problema Detectado | Riesgo Científico | Solución Aplicada |
|---|---|---|---|---|---|
| **AUD-01** | **P0 (Crítico)** | `src/geoai_roman_spain/inference.py` (`get_fault_tree`) | La función construía un árbol KDTree espacial usando `Coord_X` y `Coord_Y` de las *minas* del dataset maestro, en lugar de geometrías de fallas geológicas. | **Leakage severo:** La variable `Dist_Fault` en inferencia medía la distancia a la mina más cercana, provocando memorización geográfica de los yacimientos conocidos. | Eliminado por completo. Sustituido por cálculo de distancia a geometrías vectoriales de fallas oficiales del IGME (`LineString`/`MultiLineString`). |
| **AUD-02** | **P0 (Crítico)** | `calculate_real_geochemistry_stage2.py` | Las variables `Real_Geochem_As_ppm`, `Cu_ppm`, `Pb_ppm` se calcularon utilizando reglas `if 'gold' in commodity` o `if 'copper' in commodity`. | **Target Leakage directo:** El predictor contenía la etiqueta a predecir, inflando artificialmente el ROC-AUC al 90-99%. | Eliminadas del dataset de entrenamiento v2. La geoquímica no observada directamente en raster o muestreo de sedimentos se clasifica como `PENDING`. |
| **AUD-03** | **P0 (Crítico)** | `calculate_real_remotesensing_stage3.py` | Los índices de gossan y alteración se calcularon a partir de las concentraciones geoquímicas filtradas con `commodity`. | **Target Leakage indirecto en cascada**. | Eliminadas del dataset v2. Reemplazadas por índices derivados de fuentes reales o marcadas como pendientes si no hay cobertura nacional continua. |
| **AUD-04** | **P1 (Alto)** | `src/geoai_roman_spain/inference.py` | Inferencia contenía heurísticas fijas (`dist_fault = 1200 if paleozoico else 18000`, `as_ppm = 120 if oro else 15`). | **Falta de paridad Training-Serving:** El modelo en inferencia no recibía la geología real, sino valores arbitrarios fijados por código. | Implementado un pipeline unificado (`src/features/extractor.py`): entrenamiento e inferencia ejecutan exactamente el mismo código de extracción GIS. |
| **AUD-05** | **P1 (Alto)** | `calculate_real_geophysics_stage1.py` | Gravimetría Bouguer y magnetismo IGRF eran calculados con fórmulas sintéticas empíricas dependientes de latitud y litología en vez de mallas geofísicas observadas. | **Datos sintéticos presentados como reales:** El modelo aprendía funciones matemáticas predefinidas en lugar de firmas geofísicas naturales. | Se clasifica la geofísica como `DERIVED_THEORETICAL` y se excluye de las features obligatorias v2, documentándola en `feature_provenance.yaml`. |
| **AUD-06** | **P1 (Alto)** | Modelos y validación | Los modelos incluían `Coord_X` y `Coord_Y` directamente en el árbol de decisión de LightGBM. | **Memorización espacial:** El modelo aprende qué regiones son ricas por su posición geográfica absoluta en lugar de aprender las firmas litológicas y estructurales. | Realizado ablation test (Con vs Sin coordenadas) y entrenados modelos v2 puramente geocientíficos basados en litología, estructuras y relieve. |
| **AUD-07** | **P1 (Alto)** | Dataset y target | Se equiparaba la presencia de minas romanas (OxREP) como verdad absoluta de depósito mineral objetivo. | **Sesgo arqueológico e histórico:** Confunde la historia de la explotación minera antigua con la geología del subsuelo. | Separados dos targets: `Y_modern_deposit` (depósitos geológicos modernos) y `Y_roman_exploitation` (evidencia arqueometalúrgica histórica). |
| **AUD-08** | **P2 (Medio)** | Interpretación de salidas | Se presentaban las salidas como "Probabilidad absoluta del 84.66% de existencia de oro". | **Sobreconfianza estadística:** Una probabilidad posterior de clasificación binaria no equivale a probabilidad geológica absoluta de reserva económica. | Salidas reformuladas estrictamente como **Prospectivity Score / Favorabilidad Geológica Relativa** (0.0 a 1.0) con evaluación de calibración out-of-fold (Brier Score). |
| **AUD-09** | **P2 (Medio)** | `requirements.txt` y rutas | Rutas absolutas hardcodeadas (`C:\Users\...`) y dependencias no fijadas o faltantes. | **Falta de reproducibilidad:** El proyecto fallaba al ejecutarse en otros entornos o sistemas operativos. | Migrado a `pathlib.Path`, dependencias auditadas y fijadas en `requirements.txt` y `pyproject.toml`. |

---

## 3. Principios Rectores del Nuevo Pipeline GeoAI v2

1. **Principio de Observabilidad Estricta:** Ninguna feature sintética o heurística puede entrar al modelo de producción.
2. **Paridad Absoluta Training-Serving:** Una única función de extracción espacial alimenta tanto la creación de datasets como la inferencia en tiempo real.
3. **Validación Espacial Antisesgo:** Evaluación mediante **Spatial Block Cross-Validation (5 Folds)** y **Leave-One-District-Out (LODO)** para medir capacidad de generalización en distritos ciegos.
4. **Trazabilidad Total:** Registro completo en `config/feature_provenance.yaml`.
