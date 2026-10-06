# Changelog: GeoAI-Au

Todas las modificaciones y evoluciones notables de este proyecto están documentadas en este archivo siguiendo los principios de [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/) y versionado semántico.

---

## [GeoAI-Au v1.0] - 2026-09-27

### 🌟 Hito Científico: Release Oficial GeoAI-Au v1.0
Cierre metodológico integral de la cadena de valor científico Fases B $\rightarrow$ H. Publicación del mapa de prospectividad aurífera en España peninsular, modelos congelados, suites cartográficas en formatos geoespaciales modernos (COG, GeoParquet, GeoPackage) y documentación técnica formal de gobernanza de IA.

### ✨ Añadido (Added)
- **Suite de Productos Cartográficos en Dominio Peninsular Modelado (Fase H)**:
  - `mapa_nacional_favorabilidad_score.tif`: Ráster Cloud Optimized GeoTIFF (COG, Float32, EPSG:25830) con el favorability score continuo (0.0003 a 0.9899) sobre las 478.443 celdas elegibles.
  - `mapa_nacional_favorabilidad_percentil.tif`: Ráster COG (Float32, EPSG:25830) con el percentil acumulado sobre el dominio peninsular modelado (0% a 100%).
  - `mapa_nacional_bandas_prioritarias.tif`: Ráster COG categórico (Byte, EPSG:25830) con las bandas de priorización: Top 1% (score $\ge 0,8333$), Top 1-5% (score $\ge 0,6526$), Top 5-10% (score $\ge 0,5179$) y Fondo (0).
  - `mapa_nacional_prospectividad.geoparquet`: Dataset vectorial en GeoParquet con las 478.443 celdas terrestres elegibles (geometrías Point EPSG:25830).
  - `mapa_nacional_prospectividad.gpkg`: GeoPackage multi-capa conteniendo `celdas_priorizadas_top10` (47.845 puntos) y `zonas_prospectividad` (1.529 polígonos de zonas prioritarias contiguas).
- **Delineación y Ranking de Zonas de Prospectividad/Priorización**:
  - `zonas_prospectividad_ranking.csv`: Ranking de 1.529 zonas contiguas delineadas mediante vecindad 8-conectada en las bandas Top 1% y Top 5%, con métricas de superficie (km²), número de celdas, scores máximos/medios y categoría de prioridad.
- **Interpretabilidad y Casos de Estudio**:
  - `coeficientes_estandarizados.csv`: Desglose analítico de los 56 coeficientes estandarizados lineales (escala logit) y Odds Ratios del modelo `logistic_01`, especificando que $\exp(\beta)$ representa el cambio en los odds por incremento de 1 desviación estándar ($+1\sigma$) de la covariable tras preprocesamiento.
  - `contribuciones_locales_casos_estudio.csv`: Descomposición de log-odds ($\beta_j \tilde{x}_j$) en los cuatro depósitos de estudio: Rodalquilar, La Jara, Corcoesto y Santa Comba.
- **Análisis de Incertidumbre y Sensibilidad**:
  - `sensibilidad_leave_one_district_out.csv`: Análisis de impacto Leave-One-District-Out (LODO) sobre las predicciones selladas de Fase G.
  - `curva_sensibilidad_umbrales_holdout.csv`: Curva de sensibilidad de recuperación continua para fracciones de área $f \in [0,005; 0,20]$.
  - `dispersion_scores_por_distrito.csv`: Estadísticas descriptivas de distribución de scores por distrito de test.
- **Documentación Técnica Formal y Gobernanza**:
  - `MODEL_CARD.md`: Ficha técnica del modelo `logistic_01` conforme a estándares de Mitchell et al. (2019).
  - `DATA_CARD.md`: Ficha técnica de datos conforme a estándares de Gebru et al. (2021).
  - `LIMITATIONS.md`: Declaración exhaustiva de limitaciones estadísticas, geológicas y epistemológicas.
  - `PROVENANCE_B_H.md`: Diagrama de procedencia integral y tabla de trazabilidad criptográfica de hashes SHA-256.
  - `informes/informe_final_prospectividad_aurifera_b_h.md`: Informe científico maestro Fases B $\rightarrow$ H.
- **Pipeline de Cierre**: Script determinista [`scripts/ejecutar_fase_h_cierre.py`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/scripts/ejecutar_fase_h_cierre.py) para la exportación y análisis reproducible de Fase H.

### 🔄 Modificado y Auditado (Changed & Hotfix)
- **Corrección Canónica de Inventario de Fase B**:
  - Corregida en toda la documentación la clasificación canónica de los 790 registros brutos de BDMIN: **190 confirmados**, **597 pendientes** y **3 rechazados** (eliminadas todas las erratas con cifras incompatibles).
- **Especificación Estadística de Odds Ratio**:
  - Aclarado explícitamente en todas las tablas y textos que $\exp(\beta)$ cuantifica la variación multiplicativa de odds ante un incremento de **1 desviación estándar ($+1\sigma$)** de la variable tras el preprocesamiento con `StandardScaler`.
- **Formulación Rigurosa como Hipótesis para `dist_falla_cartografiada_m`**:
  - Reformulada la explicación del coeficiente positivo ($\beta = +0,2122$) estrictamente como **hipótesis estadística y cartográfica** (colinealidad multivariante con cabalgamientos/contactos y muestreo de fondo en cordilleras fracturadas) y **nunca como un mecanismo físico o metalogenético demostrado**.
- **Delimitación Territorial Precisa**:
  - Sustituida la expresión genérica de "mapa nacional / España" por **"España peninsular / dominio peninsular modelado"** para reflejar con exactitud la cobertura de la máscara canónica `eligible_approved_features`.
- **Auditoría Documental del Informe Final y README**:
  - Estandarizada la denominación de los outputs como **prospectivity / favorability score** y percentiles territoriales, suprimiendo cualquier mención de "probabilidad de depósito" o "probabilidad de oro".
  - Reformuladas las explicaciones de Corcoesto y Santa Comba estrictamente como **hipótesis geológicas no demostradas causalmente** (ausencia de geoquímica secundaria aprobada y de alteración hidrotermal a escala fina frente a penalización por la unidad regional "Otros granitoides").
  - Denominada la discrepancia de rendimiento entre desarrollo y holdout como **"brecha de transferencia observada ($N=8$)"**.
  - Aclarado de forma explícita que la proximidad a depósitos históricos incluida en el ranking de zonas es una **anotación geográfica post-hoc** que **no intervino en el vector de predictores ni en la inferencia del modelo**.
- **Auditoría de Transparencia en Fase G**:
  - Modificado el informe de Fase G ([`informes/evaluacion_ciega_fase_g/informe_fase_g_evaluacion_ciega.md`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/informes/evaluacion_ciega_fase_g/informe_fase_g_evaluacion_ciega.md)) para declarar que existieron accesos exploratorios técnicos tras congelar el modelo pero antes de la ejecución canónica sellada, descartando afirmaciones de "primera apertura estricta", manteniendo rigurosamente intactas todas las métricas empíricas.
- **Inmutabilidad de Artefactos de Modelado**:
  - Las ejecuciones previas de Fase D ([`reports/fase_d/20260927T135413_959884Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_d/20260927T135413_959884Z)), Fase E ([`reports/fase_e/20260927T135620_576911Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_e/20260927T135620_576911Z)), Fase F ([`reports/fase_f/20260927T135750_819061Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_f/20260927T135750_819061Z)), Fase G ([`reports/fase_g/20260927T141408_460613Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_g/20260927T141408_460613Z)) y Fase H ([`reports/fase_h/20260927T142549_961719Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_h/20260927T142549_961719Z)) se mantienen estrictamente inmutables con sus manifiestos criptográficos íntegros.

### 🛡️ Pruebas y Verificación (Fixed & Verified)
- Ejecutada la suite completa de 77 pruebas unitarias e integradas con resultado 100% satisfactorio (75 tests passed, 2 skipped opcionales de TensorFlow).
