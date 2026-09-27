# Auditoría de Saneamiento Final de Procedencia y Regeneración de Cadena D → E → F (Paso 9D)

## 1. Resumen Ejecutivo

En cumplimiento estricto del protocolo científico y de las directrices del **Paso 9D**, se ha llevado a cabo el saneamiento integral de procedencia de la cadena predictiva antes de abrir la Fase G:
1. **Regeneración nativa de Fase D desde cero**: Se ha incorporado en el motor de ensamblado ([`src/geoau/features.py`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/src/geoau/features.py)) la máscara de soporte canónica `eligible_approved_features` (idéntica a `eligible_geology_terrain`), derivada formalmente de los 56 predictores aprobados. La ejecución previa (`reports/fase_d/20260927T112256_510493Z`) se ha mantenido intacta e inmutable, sellándose la nueva Fase D en [`reports/fase_d/20260927T135413_959884Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_d/20260927T135413_959884Z) con manifiesto SHA-256 verificado.
2. **Regeneración de Fase E validada**: Se ha generado la nueva Fase E en [`reports/fase_e/20260927T135620_576911Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_e/20260927T135620_576911Z) apoyada exclusivamente en la nueva D, con los 5 distritos de reserva ciega congelados, bloques espaciales de 50 km y gap de 5 km.
3. **Regeneración de Fase F validada**: Se ha ejecutado el protocolo nested spatial cross-validation completo en [`reports/fase_f/20260927T135750_819061Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_f/20260927T135750_819061Z), evaluando internamente las 4 familias (`logistic`, `random_forest`, `extra_trees`, `hist_boosting`), seleccionando el modelo final mediante CV espacial de desarrollo y ajustándolo sobre la muestra global de desarrollo.
4. **Cuarentena absoluta del holdout**: Se certifica que **cero** celdas de la reserva ciega han sido consultadas, evaluadas o filtradas.
5. **Verificación de invariantes**: Se han reproducido con exactitud determinista las **478.443 celdas elegibles**, **131 celdas P** (175 indicios revisados), **45 depósitos independientes** (con `dep_salave` recuperado y `dep_la_preciosa_penaflor` legítimamente excluido por falta de datos) y **32 distritos metalogenéticos** (100% de la cobertura de distritos de España).
6. **Confirmación del modelo final**: El procedimiento predefinido de selección confirma a `logistic_01` (Regresión Logística L2, C=0.1, ratio P/U = 3) como el modelo superior en generalización espacial de depósitos (`deposit_recovery@5%` = 0.3206, `roc_auc_PU` = 0.7357).
7. **Autorización formal**: Con la cadena D → E → F completamente nueva, inmutable, trazable y reproducible, se autoriza la apertura y evaluación de la **Fase G**.

---

## 2. Trazabilidad y Sellado de la Nueva Cadena D → E → F

| Fase | Identificador de Ejecución (run_id) | Ruta Canónica | Estado | Manifiesto Verificado |
| :--- | :--- | :--- | :--- | :--- |
| **Fase D (Nueva)** | `20260927T135413_959884Z` | [`reports/fase_d/20260927T135413_959884Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_d/20260927T135413_959884Z) | `completada` | 71 ficheros con hash SHA-256 |
| **Fase D (Anterior preservada)** | `20260927T112256_510493Z` | [`reports/fase_d/20260927T112256_510493Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_d/20260927T112256_510493Z) | `completada` | Intacta (no modificada ni sobrescrita) |
| **Fase E (Nueva)** | `20260927T135620_576911Z` | [`reports/fase_e/20260927T135620_576911Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_e/20260927T135620_576911Z) | `completada` | `splits_manifest.json` y `samples_manifest.json` |
| **Fase F (Nueva)** | `20260927T135750_819061Z` | [`reports/fase_f/20260927T135750_819061Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_f/20260927T135750_819061Z) | `completada` | 55 ficheros ajustados + manifiesto SHA-256 |

### Configuración Activa Actualizada
- [`config/evaluation.yaml`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/config/evaluation.yaml):
  - `phase_d_run`: `reports/fase_d/20260927T135413_959884Z`
  - `support_column`: `eligible_approved_features`
  - `mode`: `validated`
- [`config/training.yaml`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/config/training.yaml):
  - `phase_e_run`: `reports/fase_e/20260927T135620_576911Z`
  - `feature_set`: `geology_terrain_geo4_hydro` (56 predictores aprobados)
  - `mode`: `validated`

---

## 3. Verificación de Invariantes Cuantitativas

| Métrica / Invariante | Valor Requerido | Valor Obtenido en Cadena Saneada | Estado | Justificación Geológica |
| :--- | :--- | :--- | :--- | :--- |
| **Celdas Elegibles Totales** | 478.443 | **478.443** (96,29% territorio) | Exacto | Definida por disponibilidad completa de los 56 predictores litológicos, estructurales, MDT e hidrológicos. |
| **Celdas Positivas Únicas (P)** | 131 | **131** celdas (175 indicios) | Exacto | Concuerda al 100% con `revision_au_fase_b.csv` auditada y `territorial_groups.csv`. |
| **Depósitos Independientes** | 45 | **45** depósitos | Exacto | `dep_salave` recuperado; `dep_la_preciosa_penaflor` legítimamente excluido por falta de datos litológicos. |
| **Distritos Metalogenéticos** | 32 | **32** distritos (100%) | Exacto | Todos los distritos auríferos de España representados en la rejilla. |
| **Depósito Salave** | Recuperado | **Recuperado** | Confirmado | Celda `c233152`, `deposit_id = dep_salave`, `district_id = dist_occidente_asturiano`. |
| **Cuarentena de Holdout** | 0 celdas consultadas | **0 celdas consultadas** | Confirmado | 5 distritos de reserva ciega (13.541 celdas elegibles, 19 celdas P, 8 depósitos) estrictamente aislados. |

---

## 4. Comparación de Rendimiento y Selección del Modelo Final

El procedimiento predefinido de selección evalúa los 12 candidatos (4 familias × 3 configuraciones) en los **15 splits internos de desarrollo**, utilizando como criterio primario la tasa de captura de depósitos espaciales independientes en el percentil 5% superior de favorabilidad (`deposit_recovery_at_05`), y como criterio secundario el área bajo la curva ROC respecto al fondo no etiquetado (`roc_auc_PU`).

### Ranking Oficial en CV Espacial Interna de Desarrollo (15 splits)

| Ranking | Candidato ID | Familia | Ratio P/U | deposit_recovery@5% | deposit_recovery@1% | deposit_recovery@10% | cell_recovery@5% | ROC-AUC |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1 (Ganador)** | `logistic_01` | **logistic** | **3** | **0.320585** | **0.090175** | **0.468670** | **0.217080** | **0.735681** |
| 2 | `extra_trees_01` | `extra_trees` | 3 | 0.319027 | 0.058637 | 0.447667 | 0.174153 | 0.755432 |
| 3 | `hist_boosting_02` | `hist_boosting` | 10 | 0.314728 | 0.090304 | 0.503131 | 0.209897 | 0.699910 |
| 4 | `hist_boosting_01` | `hist_boosting` | 3 | 0.299101 | 0.074620 | 0.492724 | 0.197383 | 0.700101 |
| 5 | `logistic_00` | `logistic` | 1 | 0.293296 | 0.065432 | 0.516764 | 0.192164 | 0.759970 |
| 6 | `extra_trees_02` | `extra_trees` | 10 | 0.289807 | 0.097578 | 0.437588 | 0.159249 | 0.748407 |
| 7 | `extra_trees_00` | `extra_trees` | 1 | 0.285821 | 0.088309 | 0.424670 | 0.161200 | 0.692691 |
| 8 | `random_forest_02` | `random_forest` | 10 | 0.281889 | 0.084546 | 0.476813 | 0.165844 | 0.745467 |
| 9 | `logistic_02` | `logistic` | 10 | 0.281220 | 0.040625 | 0.461907 | 0.173654 | 0.689748 |
| 10 | `random_forest_00` | `random_forest` | 1 | 0.237216 | 0.081798 | 0.430050 | 0.163710 | 0.681207 |
| 11 | `random_forest_01` | `random_forest` | 3 | 0.224881 | 0.092906 | 0.322918 | 0.180572 | 0.617371 |
| 12 | `hist_boosting_00` | `hist_boosting` | 1 | 0.203214 | 0.093893 | 0.311883 | 0.109446 | 0.659919 |

### Especificación del Modelo Final Ajustado
- **Familia**: `logistic` (`LogisticRegression(C=0.1, max_iter=2000, random_state=42)` con preprocesamiento `StandardScaler(with_mean=False)` e imputación mediana).
- **Muestra de entrenamiento**:
  - Positivos revisados de desarrollo: **112 celdas P**
  - Fondo pseudo-ausencia estratificado: **336 celdas U** (ratio 3:1)
  - Filas totales ajustadas: **448 observaciones**
- **Artefactos serializados**:
  - [`final_model/final_pipeline.joblib`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_f/20260927T135750_819061Z/final_model/final_pipeline.joblib)
  - [`final_model/final_validated_model.json`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_f/20260927T135750_819061Z/final_model/final_validated_model.json)

---

## 5. Auditoría de Gate y Readiness Científico

La función de verificación formal `readiness()` sobre el entorno de producción valida:
```json
{
  "ready_for_scientific_training": true,
  "reasons": [],
  "reviewed_positive_cells": 131,
  "diagnostic_or_selected_positive_cells": 131,
  "selected_role": "P_reviewed"
}
```
Todos los tests unitarios del proyecto (77 tests, 75 OK y 2 omitidos por requerir entorno TensorFlow) se ejecutan con éxito.

---

## 6. Dictamen y Autorización de Fase G

Habiendo obtenido una cadena de modelado **$D \rightarrow E \rightarrow F$ completamente nueva, inmutable, trazable, verificada mediante hashes criptográficos SHA-256**, sin que haya existido acceso alguno ni predicción sobre los 5 distritos de reserva ciega:

> **AUTORIZACIÓN FORMAL**: Queda formalmente **AUTORIZADA** la apertura y ejecución de la **Fase G** (evaluación ciega final sobre los 5 distritos de holdout congelados).
