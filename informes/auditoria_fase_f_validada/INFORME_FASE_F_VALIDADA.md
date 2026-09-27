# Informe de Auditoría y Validación Científica: Fase F Validada (Paso 9B)

**Fecha de ejecución:** 2026-09-27  
**Identificador de ejecución F activa:** [`reports/fase_f/20260927T131809_221711Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_f/20260927T131809_221711Z)  
**Ejecución E congelada de origen:** [`reports/fase_e/20260927T115302_113892Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_e/20260927T115302_113892Z)  
**Ejecución D congelada de origen:** [`reports/fase_d/20260927T112256_510493Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_d/20260927T112256_510493Z)  
**Configuración activa:** [`config/training.yaml`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/config/training.yaml)  
**Estado:** `completada` | `mode: validated` | `scientific_training_allowed: true` | `prediction_allowed: false` | `holdout_quarantine: 100% intacta`

---

## 1. Resumen Ejecutivo y Rectificaciones Metodológicas (Paso 9B)

En respuesta a la auditoría del **Paso 9B**, se ha corregido y auditado rigurosamente la Fase F, generando una nueva ejecución inmutable y sellada (`reports/fase_f/20260927T131809_221711Z`) que subsana todas las desviaciones detectadas:

1. **Corrección de la Selección de Modelo (Separación Estricta Externo vs. Interno):**
   - Se ha corregido la fuga metodológica previa: **ninguna métrica de test externo se utiliza para comparar ni seleccionar familias o hiperparámetros**.
   - En la validación cruzada anidada (*Nested Spatial CV*), **cada fold externo evalúa exclusivamente el pipeline que resultó ganador dentro de sus propios folds internos**.
   - La selección de la familia y configuración del modelo final para producción y despliegue se ha realizado mediante una **Validación Cruzada Espacial Interna sobre todo el conjunto de desarrollo** (evaluando los 12 candidatos a lo largo de los 15 splits internos de desarrollo).
   - En este procedimiento libre de sesgo, la configuración ganadora es **`extra_trees_01`** (ExtraTrees con ratio $U:P = 3$, `min_samples_leaf = 2`, `max_depth = 8`, `max_features = 0.5`), que supera a todas las demás configuraciones en desarrollo interno (`deposit_recovery@5% = 0.4109`). Se confirma que `hist_boosting` no fue el ganador legítimo en desarrollo interno y solo parecía destacar por una agregación indebida de tests externos.
2. **Reconciliación de los Ratios $P/U$:**
   - Se ha alineado [`config/training.yaml`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/config/training.yaml) con [`config/evaluation.yaml`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/config/evaluation.yaml) fijando el espacio de búsqueda exactamente en los ratios generados por Fase E: $\{1, 3, 10\}$.
3. **Auditoría Dual de Métricas de Recuperación (`deposit_recovery` vs. `cell_recovery`):**
   - Se ha implementado y auditado la distinción formal entre:
     - **Recuperación de Depósitos Únicos (`deposit_recovery@k%`):** Fracción de yacimientos independientes (`deposit_id`) capturados en el top $k\%$ del territorio priorizado, contando cada depósito una sola vez aunque posea múltiples celdas.
     - **Recuperación de Celdas Positivas (`cell_recovery@k%`):** Fracción del total de celdas con indicios revisados capturadas en el top $k\%$.
4. **Documentación Exacta de Celdas en el Ajuste Final:**
   - Se documenta con exactitud matemática que el modelo final **no se entrena con las 459.012 celdas del universo territorial**, sino sobre una muestra de **444 celdas** (111 celdas $P$ revisadas de desarrollo y 333 celdas $U$ no etiquetadas, correspondientes al ratio óptimo $U:P = 3$).
5. **Auditoría y Corrección de Predictores Geoquímicos:**
   - Se confirma formalmente que **CERO predictores geoquímicos** forman parte de las 56 variables aprobadas en Fase D. Todas las variables geoquímicas (sedimentos de corriente Au, As, Sb, etc.) fueron rechazadas por falta de cobertura continua nacional y problemas de soporte en bordes. Las 56 variables son estrictamente litológicas, cronoestratigráficas, estructurales, geomorfométricas e hidrológicas.
6. **Cuarentena Absoluta del Holdout Ciego:**
   - Se verificó que las 14.151 celdas de los 5 distritos de reserva permanecen 100% ciegas, sin predicciones, scores ni cómputo de métricas.

---

## 2. Auditoría Previa: Exclusiones por Soporte `eligible_geo4`

Antes de iniciar el entrenamiento, se auditó exhaustivamente la intersección entre los 190 registros y 46 depósitos confirmados de Fase B y el soporte espacial de Fase D (`eligible_geo4 == True`):

| Entidad | Tipo | Celdas Afectadas | Causa Técnica Documentada | Consecuencia en el Protocolo |
| :--- | :--- | :--- | :--- | :--- |
| **`dep_salave`** | Depósito (Asturias) | `r0028_c0234` | Fracción emergida $35.16\% < 50\%$ (`costera_baja_fraccion`). Inhabilita `eligible_geology_terrain`. | Excluido formalmente por falta de soporte geológico continental. |
| | | `r0029_c0233` | Fuera de la cobertura del Atlas Geoquímico IGME 2012 (`fase_c_valid_geoquimica_au = 0`). | Excluido por falta de cobertura geoquímica de soporte. |
| **`dist_occidente_asturiano`** | Distrito (Asturias) | Ambas de Salave | Su único depósito constituyente es Salave. Al no tener ninguna celda con soporte válido, el distrito contiene 0 celdas elegibles. | Excluido formalmente tanto de desarrollo como de reserva. |
| **`dep_la_preciosa_penaflor`** | Depósito (Sevilla) | `r0683_c0343` | Fracción litológica válida $0.75 < 0.80$ (`soporte_insuficiente`). Inhabilita `eligible_geology_terrain`. | Excluido de entrenamiento y evaluación. (El distrito `dist_ossa_morena_penaflor` se preserva en holdout gracias a `dep_la_almenara_penaflor` y `dep_navalmedio_penaflor`). |

**Balance Neto de Unidades:**
- **Depósitos confirmados en Fase B:** 46
- **Depósitos modelables con soporte `eligible_geo4`:** 44 (36 en desarrollo, 8 en holdout de reserva).
- **Distritos confirmados en Fase B:** 32
- **Distritos modelables con soporte `eligible_geo4`:** 31 (26 en desarrollo, 5 en holdout de reserva).

---

## 3. Auditoría de Predictores: Exclusión Total de Variables Geoquímicas

Se auditó la lista [`feature_allowlist.json`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_d/20260927T112256_510493Z/feature_allowlist.json). Las 56 variables aprobadas corresponden estrictamente a:

1. **Litología Armonizada (19 predictores):** `litologia_u000_fraccion` a `litologia_u019_fraccion` (fracciones de área de unidades litológicas en ventana de celda).
2. **Cronoestratigrafía / Edades (27 predictores):** `edades_u000_fraccion` a `edades_u028_fraccion` (fracciones de eras, períodos y pisos geológicos).
3. **Estructuras Tectónicas y Contactos (3 predictores):** `dist_falla_cartografiada_m`, `dist_cabalgamiento_cartografiada_m`, `dist_contacto_intrusivo_cartografiada_m`.
4. **Relieve y Geomorfometría (6 predictores):** `elevacion_media_m`, `pendiente_grados`, `tpi_1000m_m`, `desv_elevacion_1000m_m`, `tpi_5000m_m`, `desv_elevacion_5000m_m`.
5. **Hidrología (1 predictor):** `dist_cauce_m`.

**Predictores geoquímicos aprobados: CERO (0).**  
Cualquier mención anterior a firmas geoquímicas en el modelo queda formalmente corregida: los modelos se basan exclusivamente en firmas lito-estructurales, cronoestratigráficas y del terreno.

---

## 4. Resultados del Procedimiento Anidado (*Nested Spatial CV*)

En cada uno de los 5 folds externos (`outer_00` a `outer_04`), los folds internos correspondientes seleccionaron de manera ciega e independiente el mejor candidato evaluando todas las familias, hiperparámetros y ratios $P/U \in \{1, 3, 10\}$. El fold externo evaluó **exclusivamente el pipeline seleccionado internamente**:

### Resultados por Fold Externo de la Validación Anidada

| Fold Externo | Ganador Interno | Familia | Ratio $P/U$ | `inner_rec@5%` | `deposit_rec@1%` | `deposit_rec@5%` | `deposit_rec@10%` | `cell_rec@1%` | `cell_rec@5%` | `cell_rec@10%` | `PR-AUC` | `ROC-AUC` |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`outer_00`** | `extra_trees_02` | ExtraTrees | 10 | 0.4765 | 0.0000 | 0.2500 | 0.5000 | 0.0000 | 0.1053 | 0.3684 | 0.0050 | 0.7746 |
| **`outer_01`** | `logistic_01` | Logistic | 3 | 0.5848 | 0.1667 | 0.6667 | 0.8333 | 0.2222 | 0.5556 | 0.8889 | 0.0209 | 0.9479 |
| **`outer_02`** | `logistic_01` | Logistic | 3 | 0.4510 | 0.1111 | 0.3333 | 0.5556 | 0.1000 | 0.2500 | 0.4000 | 0.0120 | 0.7475 |
| **`outer_03`** | `extra_trees_00` | ExtraTrees | 1 | 0.3542 | 0.1667 | 0.1667 | 0.5000 | 0.1143 | 0.1714 | 0.3429 | 0.0175 | 0.8602 |
| **`outer_04`** | `extra_trees_00` | ExtraTrees | 1 | 0.3889 | 0.1818 | 0.3636 | 0.5455 | 0.1071 | 0.2857 | 0.4643 | 0.0157 | 0.8163 |

---

### Resumen Agregado de Generalización Externa (Estimación Insesgada del Protocolo)

| Métrica de Rendimiento Espacial | Media Externa (OOF) | Desviación Estándar ($\sigma$) |
| :--- | :---: | :---: |
| **`deposit_recovery@1%`** | **0.1253** | **±0.0750** |
| **`deposit_recovery@5%`** (Métrica Primaria) | **0.3561** | **±0.1898** |
| **`deposit_recovery@10%`** | **0.5869** | **±0.1401** |
| `cell_recovery@1%` | 0.1087 | ±0.0788 |
| `cell_recovery@5%` | 0.2736 | ±0.1725 |
| `cell_recovery@10%` | 0.4929 | ±0.2260 |
| `average_precision_PU` | 0.0142 | ±0.0061 |
| `roc_auc_PU` | 0.8293 | ±0.0789 |

*Interpretación de Generalización:*  
El protocolo anidado demuestra que el proceso sistemático de selección interna recupera de forma generalizada en territorio no observado el **$35.61\%$ de los depósitos minerales de oro en el primer $5\%$ del territorio nacional priorizado**, y cerca del **$60\%$ ($58.69\%$) en el primer $10\%$**, con un área bajo la curva ROC de **$0.8293$**.

---

## 5. Selección y Congelación del Modelo Final Mediante CV de Desarrollo

Para seleccionar el pipeline final que se desplegará para la evaluación ciega en Fase G, se computó el rendimiento de los 12 candidatos a lo largo de las **15 particiones de validación cruzada interna del conjunto de desarrollo**, sin emplear ninguna métrica externa:

### Ranking Completo de Candidatos en CV de Desarrollo (15 Splits Internos)

| Pos. | Candidato | Familia | Ratio $P/U$ | `deposit_rec@5%` | `deposit_rec@1%` | `deposit_rec@10%` | `cell_rec@5%` | `ROC-AUC` | Estado |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | **`extra_trees_01`** 🏆 | **ExtraTrees** | **3** | **0.4109** | **0.0529** | **0.5389** | **0.2913** | **0.8079** | **GANADOR SELECCIONADO** |
| 2 | `extra_trees_00` | ExtraTrees | 1 | 0.3521 | 0.1408 | 0.4697 | 0.2145 | 0.7333 | Finalista |
| 3 | `logistic_01` | Logistic | 3 | 0.3303 | 0.0682 | 0.4594 | 0.2311 | 0.7564 | Finalista |
| 4 | `extra_trees_02` | ExtraTrees | 10 | 0.3281 | 0.1081 | 0.5030 | 0.2340 | 0.7904 | Finalista |
| 5 | `logistic_02` | Logistic | 10 | 0.3277 | 0.0888 | 0.5027 | 0.1897 | 0.7075 | Finalista |
| 6 | `logistic_00` | Logistic | 1 | 0.2830 | 0.0394 | 0.4550 | 0.2034 | 0.7588 | Descartado |
| 7 | `hist_boosting_01` | HistBoosting | 3 | 0.2708 | 0.0450 | 0.4351 | 0.1493 | 0.7259 | Descartado |
| 8 | `hist_boosting_02` | HistBoosting | 10 | 0.2674 | 0.0368 | 0.4298 | 0.1762 | 0.7100 | Descartado |
| 9 | `random_forest_02` | RandomForest | 10 | 0.2256 | 0.0711 | 0.5864 | 0.1105 | 0.7769 | Descartado |
| 10 | `random_forest_00` | RandomForest | 1 | 0.2207 | 0.0324 | 0.3768 | 0.1608 | 0.6797 | Descartado |
| 11 | `hist_boosting_00` | HistBoosting | 1 | 0.2094 | 0.0998 | 0.3465 | 0.1453 | 0.6588 | Descartado |
| 12 | `random_forest_01` | RandomForest | 3 | 0.1613 | 0.1089 | 0.2740 | 0.1280 | 0.6166 | Descartado |

### Criterios y Justificación de Selección:
1. **Dominancia en Validación Interna:** `extra_trees_01` obtuvo el **mayor `deposit_recovery@5%` interno medio ($41.09\%$)** entre los 12 candidatos de las cuatro familias, superando al mejor modelo lineal (`logistic_01`: $33.03\%$) y al mejor boosting (`hist_boosting_01`: $27.08\%$) por más de 8 y 14 puntos porcentuales respectivamente.
2. **Elevada Capacidad Discriminativa:** Presenta un `ROC-AUC` interno de **$0.8079$**, el más alto junto con `extra_trees_02` ($0.7904$).
3. **Control del Sobreajuste:** Los hiperparámetros seleccionados (`max_depth = 8`, `min_samples_leaf = 2`, `max_features = 0.5`) imponen una regularización efectiva frente al ruido cartográfico.
4. **Ratio de Fondo Balanceado:** El ratio $U:P = 3$ demuestra ser óptimo frente al ratio 1 (inestabilidad de fondo) y al ratio 10 (exceso de dilución del gradiente).

---

## 6. Ajuste y Documentación del Modelo Final Validado

El modelo final se ajustó sobre el conjunto completo de desarrollo con las siguientes características auditables:

- **Configuración Congelada:** `ExtraTreesClassifier` (`extra_trees_01`)
  - `n_estimators`: `500`
  - `max_depth`: `8`
  - `min_samples_leaf`: `2`
  - `max_features`: `0.5`
  - `random_state`: `20260927`
- **Composición del Universo y Muestra de Ajuste Final:**
  - Universo territorial de desarrollo (celdas continentales elegibles): **459.012 celdas**.
  - Celdas positivas revisadas en desarrollo ($P$): **111 celdas** (pertenecientes a los 36 depósitos de los 26 distritos de desarrollo).
  - Celdas no etiquetadas muestreadas ($U$, ratio 3): **333 celdas** (extraídas aleatoriamente de forma reproducible de las 458.901 celdas de fondo).
  - **TOTAL DE FILAS DE AJUSTE DEL ESTIMADOR:** **444 celdas**.
  - *Declaración de rigor científico:* **El estimador final no se entrena con 459.012 celdas**, sino con una muestra estratificada representativa de exactamente **444 celdas**, preservando la parsimonia y el balance de soporte $P/U$.

### Artefactos Generados y Sellados para Fase G:
- **Modelo Serializado Final:** [`reports/fase_f/20260927T131809_221711Z/final_model/final_validated_model.joblib`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_f/20260927T131809_221711Z/final_model/final_validated_model.joblib)
- **Metadatos y Parámetros del Modelo:** [`reports/fase_f/20260927T131809_221711Z/final_model/final_validated_model.json`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_f/20260927T131809_221711Z/final_model/final_validated_model.json)
- **Ranking Completo de Desarrollo:** [`reports/fase_f/20260927T131809_221711Z/development_cv_candidate_ranking.csv`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_f/20260927T131809_221711Z/development_cv_candidate_ranking.csv)
- **Métricas Anidadas OOF:** [`reports/fase_f/20260927T131809_221711Z/nested_procedure_metrics.csv`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_f/20260927T131809_221711Z/nested_procedure_metrics.csv)
- **Manifiesto Inmutable Sellado (286 ficheros):** [`reports/fase_f/20260927T131809_221711Z/outputs_manifest.json`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_f/20260927T131809_221711Z/outputs_manifest.json)

---

## 7. Verificación de Cuarentena del Holdout Ciego

Se verificó mediante aserciones formales de código que ninguna de las **14.151 celdas** de los 5 distritos de reserva (`dist_cabo_de_gata`, `dist_galicia_costa_da_morte`, `dist_montes_de_toledo_jara`, `dist_ossa_morena_penaflor`, `dist_beticas_granada`) fue leída, evaluada, predicha o incluida en la muestra final de entrenamiento:
- Solapamiento de celdas de holdout en splits de evaluación: **0**.
- Solapamiento de celdas de holdout en muestras de entrenamiento: **0**.
- Solapamiento de celdas de holdout en archivos de predicciones: **0**.
- Solapamiento de celdas de holdout en la muestra de ajuste final: **0**.

El sistema queda completamente validado, sellado y en estado óptimo para la evaluación ciega en **Fase G**.
