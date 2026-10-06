# Contrato de Datos de la Aplicación: GeoAI-Au Explorer

## 1. Principio Rector de Gobernanza e Inmutabilidad

La aplicación **GeoAI-Au Explorer** opera estrictamente como una capa de producto, visualización e inteligencia territorial sobre los resultados del experimento **GeoAI-Au v1.0**. Todos los artefactos de las Fases B a H son **de solo lectura (READ-ONLY)**. Queda prohibida la modificación, sobreescritura o recalibración de cualquier fuente científica.

Cualquier producto intermedio generado para optimizar el rendimiento web (índices espaciales en memoria, vistas agregadas o GeoJSON reducidos) se almacenará en directorios de caché derivados (`apps/api/data_cache/`, `apps/web/public/generated/` o `web_data/`) y estará catalogado explícitamente como derivado secundario, nunca como fuente científica canónica.

---

## 2. Catálogo Canónico de Artefactos Científicos Consumidos

### 2.1. Fase H — Cartografía Nacional, Interpretabilidad y Targets de Priorización

- **Run Canónico**: `reports/fase_h/20260927T142549_961719Z`
- **Manifiesto**: [`reports/fase_h/20260927T142549_961719Z/outputs_manifest.json`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_h/20260927T142549_961719Z/outputs_manifest.json)

| Artefacto / Archivo | Tipo de Datos | CRS | Campos / Estructura | Uso en Frontend / Backend | SHA-256 Canónico |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `maps/mapa_nacional_favorabilidad_score.tif` | Cloud Optimized GeoTIFF (COG), Float32 | `EPSG:25830` | 1 banda continua (Score en $(0, 1)$), $910 \times 1.100$, NoData: `-9999.0`, Overviews: $[2, 4]$ | Backend tile server (`/api/tiles/score/{z}/{x}/{y}.png`). Capa raster principal en MapLibre. | `bf5d9f77b63ef728901513967e52bcaa5f3c2d3a18ca4aa46fad7c298bd51a22` |
| `maps/mapa_nacional_favorabilidad_percentil.tif` | COG, Float32 | `EPSG:25830` | 1 banda continua (Percentil territorial $[0, 100]$), $910 \times 1.100$, NoData: `-9999.0`, Overviews: $[2, 4]$ | Backend tile server (`/api/tiles/percentile/{z}/{x}/{y}.png`). Visualización de rangos relativos. | `8ca249fd628d5803b15a8a71a6a460b535aa5aa24b0b7ed360fee1ee8231c4fe` |
| `maps/mapa_nacional_bandas_prioritarias.tif` | COG, Byte (Uint8) | `EPSG:25830` | 1 banda categórica: `0`: Resto, `1`: Top 1%, `2`: Top 1-5%, `3`: Top 5-10%, NoData: `255` | Backend tile server (`/api/tiles/priority/{z}/{x}/{y}.png`). Capa de bandas de exploración. | `5421652eec4071918c3f0eb352f1c781fec8d9fdd1f280bbfac7ffcc4f914c3d` |
| `maps/mapa_nacional_prospectividad.geoparquet` | GeoParquet (PyArrow) | `EPSG:25830` | 478.443 filas. Campos: `cell_id` (str), `row` (int), `col` (int), `score` (float64), `percentile_favorabilidad` (float64), `prioridad_banda` (str), `land_area_m2` (float64), `geometry` (Point) | Backend FastAPI. Consulta directa y ultrarrápida ($<1$ ms) por `cell_id` y por coordenadas EPSG:25830/4326. | `cee41a38004bfb44db72ef42d1479fe5fe7268cba0b42c9d6a38e8845271b984` |
| `maps/mapa_nacional_prospectividad.gpkg` | GeoPackage (OGC) | `EPSG:25830` | 2 capas vectoriales: `celdas_priorizadas_top10` (Point, 47.845 celdas) y `zonas_prospectividad` (Polygon, 1.529 zonas contiguas) | Backend y generación de vector tiles / GeoJSON derivado de polígonos de zonas para MapLibre. | `443427a953a135dbfe2ff1c0d4522625c11ca676104f6161fe4b84b88237f8e9` |
| `targets/zonas_prospectividad_ranking.csv` | CSV tabular (UTF-8) | N/A | 1.529 filas. Campos: `zona_id`, `denominacion`, `categoria_prioridad`, `area_km2`, `celdas_count`, `score_maximo`, `score_medio`, `centroide_x`, `centroide_y`, `deposito_conocido_proximo`, `distrito_conocido_proximo`, `distancia_deposito_proximo_km`, `ranking_nacional` | Backend endpoint `/api/targets`. Tabla interactiva en panel derecho (filtrado, ordenación, zoom al centroide). | `a20970fd8e34c7ab828991611a31c5e5f8ab00834f314a1cee17ba9c350b3efc` |
| `interpretability/coeficientes_estandarizados.csv` | CSV tabular (UTF-8) | N/A | 56 filas (56 predictores aprobados). Campos: `variable`, `familia`, `coeficiente_estandarizado`, `abs_coeficiente`, `odds_ratio`, `impacto_modelo`, `significado_geologico` | Backend endpoint `/api/model/coefficients`. Gráficos de coeficientes globales en pestaña de explicabilidad. | `3b96632f4055065173db972d03024bd6b350743b55a1ca0375d6242ac5bacbf9` |
| `interpretability/contribuciones_locales_casos_estudio.csv` | CSV tabular (UTF-8) | N/A | Casos de estudio auditados (Rodalquilar, La Jara, Corcoesto, etc.) con sus descomposiciones $\beta \cdot z$. | Benchmark de test unitario para verificar la consistencia de la función de explicabilidad en runtime. | `393ec6cecb568e7e67ee0182fd65e6a8aa3b0614e1a5fad97c6d843b7d0065dd` |
| `control_cierre.json` | JSON | N/A | Metadatos de cierre: umbrales canónicos (`threshold_score_top01`: 0,833276, `threshold_score_top05`: 0,652645, `threshold_score_top10`: 0,517859), celdas (478.443), superficie ($478.378,57\text{ km}^2$), duración. | Backend endpoint `/api/project/summary`. Indicadores dinámicos del header en frontend. | `2add5133bfff556886563ba7b00b9a806df0648c8b4470e0658bdcc249345eed` |

---

### 2.2. Fase G — Evaluación Ciega en Holdout Territorial

- **Run Canónico**: `reports/fase_g/20260927T141408_460613Z`
- **Manifiesto**: [`reports/fase_g/20260927T141408_460613Z/outputs_manifest.json`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_g/20260927T141408_460613Z/outputs_manifest.json)

| Artefacto / Archivo | Tipo de Datos | Estructura / Campos Clave | Uso en Frontend / Backend | SHA-256 Canónico |
| :--- | :--- | :--- | :--- | :--- |
| `metrics/holdout_overall_metrics.json` | JSON | Métricas ciegas globales: `holdout_cells`: 13.541, `observed_P_cells`: 19, `observed_deposits`: 8, `districts_count`: 5, `deposit_recovery_at_01`: 0,125, `deposit_recovery_at_05`: 0,125, `deposit_recovery_at_10`: 0,250, `roc_auc_PU`: 0,5807, `average_precision_PU`: 0,0065. | Backend `/api/validation/summary`. Tarjetas de métricas en tab Validación. | `c14a8c2903039ecff7e61328f4e6fd353d753b74a8459a91a7969620b690507e` |
| `metrics/holdout_by_deposit.csv` | CSV tabular | 8 depósitos del holdout (`deposit_id`, `district_id`, `tipo_au`, `score_max`, `hit_at_01`, `hit_at_05`, `hit_at_10`). | Backend `/api/validation/deposits`. Tabla interactiva de depósitos en tab Validación. | `94e6b582eb52b8b049ea9c12749c1384515283f62e70c4b74da7a242594aacca` |
| `metrics/holdout_by_district.csv` | CSV tabular | 5 distritos del holdout (`district_id`, `celdas_count`, `observed_P`, `observed_deposits`, `score_mean`, `recovery_rates`). | Backend `/api/validation/districts`. Desglose por distrito reservado. | `746724bad9642dd40753cbb54dd1634a7991221cab84dd96c807ed0686a204f5` |
| `metrics/development_vs_holdout_comparison.csv` | CSV tabular | Comparativa métrica desarrollo (Nested CV) vs holdout ciego (brecha de transferencia observada). | Gráfico comparativo de desempeño F vs G en tab Validación. | `b7a2910ffe7728bac8e78314bddb8676b0968809ac49ba9ffd58467afc2b4d89` |
| `metrics/bootstrap_deposit_uncertainty.json` | JSON | Intervalos de confianza bootstrap al 95% para `deposit_recovery@1%`, `@5%`, `@10%`. | Visualización de barras de error e incertidumbre $N=8$. | `5718bcfadc252ca41b50da3eb4e3ae284ea418fa7f713d5ea6b93c086f688c75` |

---

### 2.3. Fase F — Modelo Congelado de Producción

- **Run Canónico**: `reports/fase_f/20260927T135750_819061Z`
- **Manifiesto**: [`reports/fase_f/20260927T135750_819061Z/outputs_manifest.json`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_f/20260927T135750_819061Z/outputs_manifest.json)

| Artefacto / Archivo | Tipo de Datos | Estructura / Parámetros | Uso en Frontend / Backend | SHA-256 Canónico |
| :--- | :--- | :--- | :--- | :--- |
| `final_model/final_validated_model.joblib` | Scikit-learn Pipeline serializado | Steps: `guard` (`FeatureGuard`), `preprocess` (`ColumnTransformer` con `SimpleImputer` y `StandardScaler`), `model` (`LogisticRegression(C=0.1, penalty='l2')`). | Backend FastAPI. Explicabilidad aditiva local exacta: $logit(x) = \text{intercept} + \sum \beta_i \cdot z_i$. Verificación matemática continua frente a `decision_function`. | `b65c3574c3992210bff99888a3c3c4206e41e25e0d9340c952119f7b31491723` |
| `final_model/final_validated_model.json` | JSON | Hiperparámetros, intercepto ($-1,880934$), nombres de columnas en orden y metadatos de entrenamiento. | Backend `/api/model/summary`. Documentación de la arquitectura del modelo. | `331fc21fdebcd9662d8ec313a685a5c86484159f09bf348a1e7b7f320a6a4cee` |

---

### 2.4. Fase D — Predictores, Soporte Territorial y Relaciones Espaciales

- **Run Canónico**: `reports/fase_d/20260927T135413_959884Z`
- **Manifiesto**: [`reports/fase_d/20260927T135413_959884Z/outputs_manifest.json`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_d/20260927T135413_959884Z/outputs_manifest.json)

| Artefacto / Archivo | Tipo de Datos | Estructura / Campos Clave | Uso en Frontend / Backend | SHA-256 Canónico |
| :--- | :--- | :--- | :--- | :--- |
| `grid_spec.json` | JSON | Definición de la rejilla territorial: `crs`: `EPSG:25830`, `origin_x`: $-50.000$, `origin_y`: $4.860.000$, `width`: $1.100$, `height`: $910$, `resolution_m`: $1.000$, `transform_gdal`. | Backend FastAPI. Conversión matemática determinista $O(1)$ entre coordenadas $(x, y) \leftrightarrow (\text{row}, \text{col}) \leftrightarrow \text{cell\_id}$. | `f6cf5258049d5a9b50a859d071db4963deefd93d48aa6fb0b29e277e9164197d` |
| `feature_allowlist.json` | JSON | `approved_training_columns`: Lista ordenada de los 56 nombres exactos de variables autorizadas. | Backend FastAPI. Validación y orden estricto de columnas en inferencia y explicación local. | `abd445b251af9553e3f9b2235976d68ab40c7f39be88061ac0e63ec4970f1b4a` |
| `feature_dictionary.csv` | CSV | Metadatos de las variables (fuente, unidades, método de agregación, decisión de auditoría). | Tooltips y explicaciones semánticas en la interfaz de usuario. | `5a2fa0d98dec301302f9591103abf5b2060e295fd14fec4485d384e36440e142` |
| `X_features.parquet` | Parquet tabular | 496.855 filas $\times$ 169 columnas. (Contiene los 56 predictores aprobados para todo el dominio). | Backend FastAPI. Fuente de los valores brutos de las 56 variables para la celda inspeccionada en `/api/cell/{cell_id}/explain`. | Consumido en modo streaming/columnar. |
| `relacion_deposit_id_celda.parquet` | Parquet tabular | 141 filas. Campos: `cell_id`, `deposit_id`. | Backend. Anotación de depósito si la celda inspeccionada coincide con una celda mineralizada. | `65c7ef4c80d2d41bb4710b4c712bc5f91e374ae400efcd01c019d630ab15b7fd` |
| `relacion_district_id_celda.parquet` | Parquet tabular | 143 filas. Campos: `cell_id`, `district_id`. | Backend. Asignación inmediata de distrito para la celda inspeccionada. | `d5e4c626abdc1a7f39b5e174a51bc6d8c08ffa69d3a2e4a267052b4044a79c38` |

---

### 2.5. Inventarios Minerales Auditados (Fases B y C)

- **Fuentes**: `data/review/revision_au_fase_b.csv` y `data/review/inventario_distritos_metalogeneticos.csv`

| Artefacto / Archivo | Tipo de Datos | Campos / Registros | Uso en Frontend / Backend | SHA-256 Canónico |
| :--- | :--- | :--- | :--- | :--- |
| `data/review/revision_au_fase_b.csv` | CSV tabular (UTF-8) | 790 registros (190 confirmados, 597 pendientes, 3 rechazados). 46 depósitos, 32 distritos. Coordenadas: `lon`, `lat`, `lon_corregida`, `lat_corregida`. | Backend `/api/deposits`. Capa MapLibre de depósitos confirmados con popup geológico. | `fd8b7826cec0b853b217e988b58a9c321cdfcb63750929c766906bb115f6a4f5` |
| `data/review/inventario_distritos_metalogeneticos.csv` | CSV tabular (UTF-8) | 32 distritos metalogenéticos auditados. Campos: `district_id`, `n_depositos`, `depositos`, `celdas_confirmadas`, `area_recintos_km2`. | Backend `/api/districts`. Información de contexto distrital y delimitación metalogenética. | `942333173f54f6db836c35af5b3343822ec3183cba0b0ee55a548ea52d9896ff` |

---

## 3. Contratos de Datos Derivados para Rendimiento Web

Para garantizar tiempos de respuesta inferiores a 100 ms sin alterar los datos científicos, se autoriza la generación de los siguientes artefactos derivados:

1. `apps/api/data_cache/features_approved_56.parquet`:
   - Subconjunto exclusivo de las 56 columnas aprobadas para las 478.443 celdas elegibles, indexado por `cell_id`.
   - Permite lecturas de atributos locales en $< 5$ ms.
2. `apps/api/data_cache/zonas_prospectividad_4326.geojson`:
   - Polígonos de las 1.529 zonas proyectados a WGS84 (`EPSG:4326`) para carga vectorial directa en MapLibre.
3. `apps/api/data_cache/depositos_confirmados_4326.geojson`:
   - 46 depósitos confirmados agrupados a nivel de `deposit_id` con centroide WGS84, distrito, tipología aurífera y número de indicios asociados.

---

## 4. Reglas Estrictas de Nomenclatura en la API y Frontend

1. El valor numérico de predicción se denomina siempre:
   - `prospectivity_score` o `favorability_score`.
   - **PROHIBIDO**: `probability_of_gold`, `probabilidad_deposito` o cualquier mención de probabilidad absoluta.
2. Todo endpoint que devuelva un score debe incluir el encabezado o campo de guardarraíl científico:
   ```json
   "disclaimer": "Score relativo de favorabilidad geológica. No representa probabilidad calibrada de existencia de un depósito ni estimación económica de recursos."
   ```
3. La relación de proximidad a depósitos históricos mostrada en los targets se etiqueta explícitamente como `post_hoc_annotation: true`.
