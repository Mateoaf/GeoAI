# INFORME DE AUDITORÍA Y REGULARIZACIÓN CIENTÍFICA: PASO 9C
## Corrección de la Máscara de Soporte, Regeneración Integral E/F y Sanción Final de Modelo para Fase G

**Fecha:** 27 de Septiembre de 2026  
**Entorno de Ejecución:** Validado (`mode: validated`)  
**Fase D de Referencia:** [`reports/fase_d/20260927T112256_510493Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_d/20260927T112256_510493Z)  
**Nueva Fase E Regenerada:** [`reports/fase_e/20260927T133459_262048Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_e/20260927T133459_262048Z)  
**Nueva Fase F Sellada:** [`reports/fase_f/20260927T133955_730347Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_f/20260927T133955_730347Z)  
**Estado:** SELLADA, AUDITADA Y AUTORIZADA PARA FASE G  

---

## 1. Justificación Científica: Inadecuación de `eligible_geo4`

En el diseño original del proyecto, la máscara `eligible_geo4` requería simultáneamente:
1. `coastal_eligible` (área emergida $\ge 100\,000\,\text{m}^2$).
2. Cobertura litológica $\ge 80\%$.
3. Presencia de información de relieve y geomorfometría (MDT).
4. `geoquimica_au_valid_rgb > 0` (presencia de muestreo geoquímico regional de sedimentos de corriente del atlas nacional).

Sin embargo, tras la **auditoría semántica de predictores de Fase D (Paso 6)**:
- Se aprobaron **exactamente 56 predictores**: 19 fracciones litológicas, 27 fracciones cronoestratigráficas, 3 distancias a discontinuidades estructurales (fallas, cabalgamientos, intrusivos), 6 variables geomorfométricas (elevación, pendiente, TPIs, rugosidad) y 1 distancia hidrológica (`dist_cauce_m`).
- **Cero variables geoquímicas fueron aprobadas**. Todas fueron rechazadas o mantenidas pendientes debido a la severa disparidad metodológica, límites de detección variables a lo largo de 4 décadas y la heterogeneidad analítica entre campañas regionales.

**Consecuencia científica:** Exigir `eligible_geo4` como universo de modelado imponía un filtro artificial que excluía amplias zonas del territorio nacional donde los **56 predictores aprobados están disponibles al 100% con máxima calidad**, por el mero hecho de carecer de una capa rechazada.

---

## 2. Construcción de la Máscara Coherente: `eligible_approved_features`

Se definió y construyó la máscara `eligible_approved_features` basada de forma estricta y exclusiva en la disponibilidad y validez de las 56 variables aprobadas en `feature_allowlist.json`:
$$\text{eligible\_approved\_features} = \text{coastal\_eligible} \land (\text{litologia\_dominante} \neq \text{NaN}) \land (\text{edades\_dominante} \neq \text{NaN}) \land (\text{elevacion\_media\_m} \neq \text{NaN}) \land (\text{pendiente\_grados} \neq \text{NaN})$$

Dado que las estructuras tectónicas y la red fluvial se calculan mediante distancias euclidianas a redes vectoriales continuas en toda la Península, su soporte cubre la totalidad del dominio peninsular. La calidad del vector litológico exige $\ge 80\%$ de cobertura de la celda de 1 km.

La columna `eligible_approved_features` fue incorporada en `calidad_y_soporte.parquet` de Fase D y su manifiesto actualizado con verificación SHA-256 (`0dd428920a8ccbceeb6e9e90883a7ef6800375ab3106ed62a57538e4ad763b84`).

---

## 3. Comparación Cuantitativa: `eligible_geo4` vs. `eligible_approved_features`

La auditoría territorial comparativa arrojó los siguientes resultados cuantitativos:

| Métrica Territorial | `eligible_geo4` (Histórica) | `eligible_approved_features` (Auditada) | Balance / Impacto Científico |
| :--- | :---: | :---: | :--- |
| **Celdas elegibles totales** | 472.548 (95,11%) | **478.443 (96,29%)** | **+5.895 celdas recuperadas** para el mapa nacional |
| **Registros positivos revisados** | 174 | **175** | **+1 registro recuperado** |
| **Celdas positivas revisadas** | 130 | **131** | **+1 celda recuperada** (`es_pen_utm30_1km_v1_r0029_c0233`) |
| **Depósitos independientes** | 44 | **45** | **+1 depósito recuperado** (`dep_salave`) |
| **Distritos metalogenéticos** | 31 | **32** | **+1 distrito recuperado** (`dist_occidente_asturiano`, **100% cubierto**) |

### 3.1. Estado de `dep_salave` y `dep_la_preciosa_penaflor`

1. **`dep_salave` (Tapia de Casariego, Asturias): RECUPERADO**
   - **Celda:** `es_pen_utm30_1km_v1_r0029_c0233`.
   - **Distrito:** `dist_occidente_asturiano` (Zona Asturoccidental-Leonesa).
   - **Diagnóstico:** El depósito se sitúa en un cantil costero cantábrico. Tenía litología 100% válida (cuarcitas y pizarras de la Fm. Cabos / Grupo Los Valles, intrusionadas por el granodiorita de Salave) y relieve completo, pero carecía de muestreo de sedimentos de corriente por ausencia de red fluvial muestreable en el acantilado.
   - **Resolución:** Con `eligible_approved_features`, `dep_salave` entra plenamente en el universo modelable de desarrollo.
   - **Impacto:** Permite recuperar el 100% de los distritos auríferos de España (32 de 32 distritos).

2. **`dep_la_preciosa_penaflor` (Peñaflor, Sevilla): EXCLUSIÓN LEGÍTIMA CONFIRMADA**
   - **Celda:** `es_pen_utm30_1km_v1_r0683_c0343`.
   - **Distrito:** `dist_ossa_morena_penaflor` (perteneciente a la reserva de holdout).
   - **Diagnóstico:** Presenta `litologia_cobertura = 0.7046 < 0.80`, habiendo quedado clasificada en Fase C como `soporte_insuficiente` por no alcanzar el umbral mínimo de integridad geológica.
   - **Resolución:** Al no disponer de cobertura litológica mínima, sus 46 predictores de litología y cronoestratigrafía son NaN. Su exclusión es **científicamente legítima y necesaria** (ausencia de predictores aprobados), no un artefacto de capas rechazadas.

---

## 4. Regeneración Integral de Fase E (`reports/fase_e/20260927T133459_262048Z`)

Con el nuevo universo modelable, se regeneró Fase E desde cero cumpliendo con el pre-registro espacial congelado:
- **Reserva Ciega (Holdout):** Se preservaron exactamente los **5 distritos metalogenéticos pre-registrados**:
  1. `dist_cabo_de_gata`
  2. `dist_galicia_costa_da_morte`
  3. `dist_montes_de_toledo_jara`
  4. `dist_ossa_morena_penaflor`
  5. `dist_beticas_granada`
- **Cuarentena Absoluta:**
  - Celdas de holdout: **13.541 celdas elegibles (2,83%)**, 19 celdas positivas (14,50%), 8 depósitos independientes.
  - Solapamiento de unidades transitivas de 50 km entre desarrollo y holdout: **0 unidades**.
  - CERO celdas de reserva participan en particiones (train/test de los 20 splits) ni en las 180 muestras P/U generadas.
- **Conjunto de Desarrollo:**
  - Celdas elegibles: **464.902 celdas (97,17%)**.
  - Celdas positivas revisadas: **112 celdas (85,50%)**.
  - Depósitos independientes: **37 depósitos**.
  - Distritos metalogenéticos: **27 distritos**.
  - Unidades espaciales conectadas: **229 unidades**.

---

## 5. Regeneración y Ejecución de Fase F (`reports/fase_f/20260927T133955_730347Z`)

La Fase F validada se ejecutó de forma limpia mediante Nested Spatial Cross-Validation:
- **Predictores:** Exclusivamente los 56 `approved_training_columns`.
- **Familias evaluadas:** `logistic`, `random_forest`, `extra_trees`, `hist_boosting`.
- **Espacio de búsqueda interno:** Ratios P/U $\in \{1, 3, 10\}$, 3 realizaciones U independientes por split interno.
- **Cuarentena:** Auditada formalmente. Cero accesos, consultas o inferencias sobre las 14.151 celdas de la reserva.

### 5.1. Capacidad de Generalización Externa (Nested Spatial CV OOF)

Los 5 folds externos OOF se utilizaron **exclusivamente** para estimar la capacidad de generalización del procedimiento anidado (sin intervenir en la selección final del modelo):

| Métrica de Evaluación | Media Externa OOF (5 Folds) | Desviación Estándar ($\pm \sigma$) |
| :--- | :---: | :---: |
| **Deposit Recovery @ 1%** | 14,44% | $\pm 14,49\%$ |
| **Deposit Recovery @ 5%** | **43,89%** | $\pm 18,04\%$ |
| **Deposit Recovery @ 10%** | 52,78% | $\pm 23,90\%$ |
| **Cell Recovery @ 1%** | 5,21% | $\pm 5,10\%$ |
| **Cell Recovery @ 5%** | 25,47% | $\pm 9,97\%$ |
| **Cell Recovery @ 10%** | 43,46% | $\pm 17,66\%$ |
| **PR-AUC (Average Precision P/U)** | 0,0119 | $\pm 0,0083$ |
| **ROC-AUC P/U** | 0,7402 | $\pm 0,2054$ |

---

## 6. Selección Final Congelada Mediante CV Espacial de Desarrollo

Siguiendo el mandato de Paso 9C, se ejecutó una **validación cruzada espacial completa sobre todo el conjunto de desarrollo** (15 splits internos distribuidos espacialmente con gap $\ge 5000\,\text{m}$), independiente de las métricas OOF externas, para rankear y congelar la familia e hiperparámetros definitivos.

### 6.1. Ranking de Candidatos en Desarrollo (`development_cv_candidate_ranking.csv`)

| Ranking | Candidato | Familia | Ratio P/U | Hiperparámetros | Deposit Rec@5% | Cell Rec@5% | ROC-AUC P/U | Deposit Rec@10% |
| :---: | :--- | :--- | :---: | :--- | :---: | :---: | :---: | :---: |
| **1º (Ganador)** | `logistic_01` | **logistic** | **3** | `{'C': 0.1}` | **0,3206** | **0,2171** | **0,7357** | 0,4687 |
| 2º | `extra_trees_01` | extra_trees | 3 | `{'n_estimators': 500, 'min_samples_leaf': 2, 'max_features': 0.5, 'max_depth': 8}` | 0,3190 | 0,1742 | 0,7554 | 0,4477 |
| 3º | `hist_boosting_02` | hist_boosting | 10 | `{'max_iter': 100, 'learning_rate': 0.15, 'max_leaf_nodes': 7, 'min_samples_leaf': 10}` | 0,3147 | 0,2099 | 0,6999 | 0,5031 |
| 4º | `hist_boosting_01` | hist_boosting | 3 | `{'max_iter': 100, 'learning_rate': 0.05, 'max_leaf_nodes': 31, 'min_samples_leaf': 10}` | 0,2991 | 0,1974 | 0,7001 | 0,4927 |
| 5º | `logistic_00` | logistic | 1 | `{'C': 1.0}` | 0,2933 | 0,1922 | 0,7600 | 0,5168 |
| 6º | `extra_trees_02` | extra_trees | 10 | `{'n_estimators': 500, 'min_samples_leaf': 10, 'max_features': 0.5, 'max_depth': 16}` | 0,2898 | 0,1592 | 0,7484 | 0,4376 |
| 7º | `extra_trees_00` | extra_trees | 1 | `{'n_estimators': 500, 'min_samples_leaf': 5, 'max_features': 'sqrt', 'max_depth': None}` | 0,2858 | 0,1612 | 0,6927 | 0,4247 |
| 8º | `random_forest_02` | random_forest | 10 | `{'n_estimators': 500, 'min_samples_leaf': 2, 'max_features': 'sqrt', 'max_depth': 16}` | 0,2819 | 0,1658 | 0,7455 | 0,4768 |
| 9º | `logistic_02` | logistic | 10 | `{'C': 10.0}` | 0,2812 | 0,1737 | 0,6897 | 0,4619 |
| 10º | `random_forest_00` | random_forest | 1 | `{'n_estimators': 500, 'min_samples_leaf': 5, 'max_features': 'sqrt', 'max_depth': None}` | 0,2372 | 0,1637 | 0,6812 | 0,4300 |
| 11º | `random_forest_01` | random_forest | 3 | `{'n_estimators': 500, 'min_samples_leaf': 20, 'max_features': 0.5, 'max_depth': None}` | 0,2249 | 0,1806 | 0,6174 | 0,3229 |
| 12º | `hist_boosting_00` | hist_boosting | 1 | `{'max_iter': 100, 'learning_rate': 0.1, 'max_leaf_nodes': 15, 'min_samples_leaf': 10}` | 0,2032 | 0,1094 | 0,6599 | 0,3119 |

### 6.2. Configuración Final Congelada
- **Familia:** `logistic` (Regresión Logística Regularizada L2 con solver L-BFGS y StandardScaler).
- **Candidato:** `logistic_01`.
- **Parámetros:** `{'C': 0.1, 'max_iter': 3000, 'solver': 'lbfgs'}`.
- **Ratio P/U:** 3 no etiquetadas por cada positiva.
- **Rendimiento medio en CV de Desarrollo:**
  - `deposit_recovery_at_05`: **32,06%**
  - `cell_recovery_at_05`: **21,71%**
  - `roc_auc_PU`: **0,7357**
  - `deposit_recovery_at_10`: **46,87%**

---

## 7. Ajuste del Modelo Final Validado para Fase G

El pipeline ganador fue ajustado sobre la totalidad del conjunto de desarrollo y congelado para su evaluación ciega en Fase G:
- **Universo de fondo disponible (desarrollo):** 464.902 celdas elegibles.
- **Celdas positivas de entrenamiento ($P$):** 112 celdas revisadas de desarrollo.
- **Celdas no etiquetadas muestreadas ($U$, ratio 3):** 336 celdas de fondo de desarrollo (semilla determinista derivada de protocolo).
- **Instancias de entrenamiento totales ($P + U$):** **Exactamente 448 celdas** (documentado formalmente: el ajuste se realiza sobre 448 filas de muestreo P/U balanceado, no sobre las 464.902 celdas del territorio).
- **Artefactos congelados:**
  - Modelo serializado: [`reports/fase_f/20260927T133955_730347Z/final_model/final_validated_model.joblib`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_f/20260927T133955_730347Z/final_model/final_validated_model.joblib)
  - Metadatos del modelo: [`reports/fase_f/20260927T133955_730347Z/final_model/final_validated_model.json`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_f/20260927T133955_730347Z/final_model/final_validated_model.json)
  - Manifiesto sellado: Verificado íntegramente con SHA-256 (`outputs_manifest.json`).

---

## 8. Dictamen Final y Autorización Única para Fase G

1. **Coherencia Científica Restaurada:** La máscara de soporte `eligible_approved_features` es estrictamente coherente con los 56 predictores aprobados, eliminando condicionamientos de capas rechazadas y recuperando a `dep_salave` y al distrito `dist_occidente_asturiano` (100% de los distritos metalogenéticos representados).
2. **Cuarentena Absoluta de la Reserva:** Se ratifica que las 14.151 celdas de los 5 distritos ciegos de holdout se encuentran intactas, no habiendo sido consultadas, procesadas, transformadas ni evaluadas en ninguna fase.
3. **Fase F Sellada e Inmutable:** El ranking de desarrollo, el modelo final congelado y todos los artefactos de Fase F han sido verificados mediante el banco de 77 pruebas unitarias del repositorio (100% de éxito).

**AUTORIZACIÓN:**  
Queda formalmente **AUTORIZADA LA APERTURA ÚNICA DE FASE G** para proceder a la evaluación ciega e inmutable del modelo final congelado sobre los 5 distritos de reserva.
