# Informe Científico Final: Cadena Metodológica Integral B → H y Mapa de Prospectividad Aurífera en España Peninsular

## 1. Resumen Ejecutivo y Declaración de Integridad Científica

El presente informe constituye el **cierre científico integral** del proyecto de modelado de favorabilidad y prospección aurífera en España peninsular sobre una malla de soporte regular de 1 km² (EPSG:25830).

**Alcance territorial y delimitación muestral**:
El sistema se encuentra condicionado de forma explícita al **inventario auditado** de 190 ocurrencias minerales confirmadas (correspondientes a 46 depósitos independientes y 32 distritos metalogenéticos de la Base de Datos de Yacimientos y Minerales BDMIN-IGME, de los cuales 45 depósitos y 478.443 celdas resultan modelables bajo la máscara canónica de soporte territorial `eligible_approved_features`). Los resultados generados representan índices cuantitativos relativos de favorabilidad geológica (**prospectivity/favorability scores**) sobre el dominio peninsular modelado y **no deben interpretarse en ningún caso como un inventario exhaustivo de todo el territorio nacional ni como probabilidades de depósito o presencia física de mineralización**.

```mermaid
flowchart TD
    B[Fase B: Auditoría BDMIN<br/>190 confirmados, 597 pendientes, 3 rechazados<br/>46 depósitos, 32 distritos (790 total)] --> C[Fase C: Cartografía Distrital<br/>Malla 1 km EPSG:25830<br/>Mapa territorial determinista]
    C --> D[Fase D: 56 Predictores Aprobados<br/>Soporte: eligible_approved_features<br/>478.443 celdas, 45 depósitos]
    D --> E[Fase E: Pre-registro Espacial<br/>Bloques 50 km + Gap 5 km<br/>Reserva ciega: 5 distritos]
    E --> F[Fase F: Nested Spatial CV<br/>15 splits internos de desarrollo<br/>Selección: logistic_01, C=0.1, ratio 3]
    F --> G[Fase G: Evaluación Ciega Holdout<br/>13.541 celdas, 19 P, 8 depósitos<br/>Recovery@5%=12.5%, ROC-AUC=0.581]
    G --> H[Fase H: Dominio Peninsular y Cierre<br/>478.443 celdas, COG/GPKG/GeoParquet<br/>Interpretabilidad y Limitaciones]
```

### Declaración de Integridad Metodológica
1. **Inmutabilidad Post-Holdout**: Tras la apertura y evaluación de la reserva ciega en Fase G, **no se ha reentrenado, recalibrado ni modificado** ningún hiperparámetro, variable, máscara, umbral, ponderación o preprocesamiento del modelo.
2. **Transparencia en la Procedencia de Fase G**: Se hace constar explícitamente que, tras la congelación definitiva del modelo en Fase F pero con carácter previo a la ejecución canónica sellada de Fase G, existieron accesos exploratorios técnicos durante la depuración del flujo de evaluación; por consiguiente, el informe de Fase G no formula la afirmación de "primera apertura estricta" en términos epistemológicos vírgenes. No obstante, el modelo `logistic_01` permaneció estrictamente congelado y ninguna decisión de modelado fue alterada a raíz de tales accesos.
3. **Mantenimiento Estricto de Métricas**: Todas las métricas de desarrollo (Fase F) y de test ciego (Fase G) se mantienen sin modificaciones y se reportan con total fidelidad empírica.
4. **Denominación Técnica Guardarraíl**: Las agrupaciones de celdas de alta favorabilidad se denominan en toda la cartografía y documentación como **"zonas de prospectividad/priorización"**, evitando categóricamente el término engañoso de "yacimientos predichos". Los valores calculados se denominan invariablemente **prospectivity score** o **favorability score**, nunca probabilidad de depósito.

---

## 2. Síntesis de la Cadena Metodológica (Fases B a G)

### 2.1. Fase B: Auditoría Geológica y Conciliación de Indicios
- **Punto de Partida**: Base de Datos de Yacimientos y Minerales (BDMIN, IGME) con 790 registros brutos con presencia de oro en España peninsular.
- **Protocolo de Auditoría**: Aplicación de criterios geológicos estrictos (paragénesis aurífera comprobada, tipología filoniana/orogénica/aluvial documentada, coordenadas contrastadas y fuentes bibliográficas trazables).
- **Inventario Auditado Consolidado**:
  - **190 registros positivos confirmados** (`confirmada`) pertenecientes a **46 depósitos independientes** y **32 distritos metalogenéticos**.
  - **597 registros pendientes** (`pendiente`) mantenidos en estricta cuarentena bibliográfica por evidencia insuficiente en fuentes accesibles.
  - **3 registros rechazados** (`rechazada`) descartados formalmente tras revisión geológica específica.
  - **Total**: **790 registros BDMIN** clasificados canónicamente (190 confirmados + 597 pendientes + 3 rechazados = 790).
- **Registro Canónico**: [`data/review/revision_au_fase_b.csv`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/data/review/revision_au_fase_b.csv).

### 2.2. Fase C: Cartografía Territorial de Distritos
- **Cartografía Oficial**: Delimitación explícita cell_id $\rightarrow$ district_id para los 32 distritos auríferos de España peninsular ([`data/review/territorial_groups.csv`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/data/review/territorial_groups.csv)), basada en estructuras metalogenéticas documentadas y sin polígonos arbitrarios alrededor de los indicios.
- **Armonización**: Rejilla de 1 km² en EPSG:25830 (1.100 columnas $\times$ 910 filas), garantizando concordancia uno a uno entre positivos y unidades distritales indivisibles.

### 2.3. Fase D: Auditoría Semántica de Predictores y Máscara de Soporte
- **Auditoría Semántica**: De 168 variables candidatas en `feature_allowlist.json`, se auditaron y rechazaron 112 capas (proxies de mineralización, geoquímica de sedimentos con simbología cualitativa no homogénea o falta de cobertura analítica, y variables con riesgo de fuga de información).
- **56 Predictores Aprobados**:
  - 19 fracciones litológicas continuas (unidades del mapa geológico nacional 1:200.000).
  - 27 fracciones cronoestratigráficas continuas (del Proterozoico al Cuaternario).
  - 3 distancias euclídeas continuas a estructuras geológicas (fallas/cizallas, cabalgamientos y contactos intrusivos).
  - 6 variables de relieve del MDT (elevación media, pendiente media, TPI a 1.000 m y 5.000 m, rugosidad/desviación de elevación).
  - 1 variable hidrológica regional (distancia a cauce de la red hidrográfica).
- **Máscara de Soporte Canónica**: `eligible_approved_features` (incorporada nativamente en [`src/geoau/features.py`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/src/geoau/features.py)). Exige cobertura completa de las 56 variables aprobadas sin depender de capas geoquímicas excluidas.
  - Universo elegible en el dominio peninsular modelado: **478.443 celdas** (96,29% del territorio de España peninsular).
  - Depósitos modelables: **45 depósitos independientes** (recuperación del depósito clave de **`dep_salave`** en Asturias; exclusión técnica legítima de `dep_la_preciosa_penaflor` por cobertura litológica incompleta $70,46\% < 80\%$).
  - Distritos cubiertos: **32 de 32 distritos metalogenéticos** (100%).
- **Ejecución Canónica Sellada**: [`reports/fase_d/20260927T135413_959884Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_d/20260927T135413_959884Z).

### 2.4. Fase E: Pre-registro del Protocolo Espacial y Cuarentena de Holdout
- **Protocolo de Validación**: Bloques espaciales de 50.000 m $\times$ 50.000 m con banda de exclusión (*spatial gap*) de 5.000 m para mitigar autocorrelación espacial.
- **Reserva Ciega (Holdout)**: Pre-registro inmutable de 5 distritos completos:
  1. `dist_cabo_de_gata` (Almería)
  2. `dist_galicia_costa_da_morte` (A Coruña)
  3. `dist_montes_de_toledo_jara` (Toledo/Ciudad Real)
  4. `dist_ossa_morena_penaflor` (Sevilla/Córdoba)
  5. `dist_beticas_granada` (Granada)
- **Partición Territorial**:
  - Desarrollo: 464.902 celdas elegibles, 112 celdas positivas ($P$), 37 depósitos, 27 distritos.
  - Holdout ciego: 13.541 celdas elegibles, 19 celdas positivas ($P$), 8 depósitos, 5 distritos.
- **Muestras P/U**: Generación de 180 muestras de entrenamiento estratificado en desarrollo bajo ratios $P/U \in \{1, 3, 10\}$ y 3 realizaciones independientes de pseudo-ausencias.
- **Ejecución Canónica Sellada**: [`reports/fase_e/20260927T135620_576911Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_e/20260927T135620_576911Z).

### 2.5. Fase F: Aprendizaje Espacial Anidado y Selección de Modelo
- **Arquitectura de Evaluación**: Validación cruzada espacial anidada (*nested spatial CV*, 5 folds externos $\times$ 3 folds internos = 15 particiones de ajuste interno).
- **Familias Comparadas**: Logistic Regression, Random Forest, ExtraTrees, HistGradientBoosting (3 candidatos por familia $\times$ 3 ratios).
- **Procedimiento Predefinido de Selección**: Promedio de rendimiento en las 15 particiones internas de desarrollo, priorizando la recuperación de depósitos independientes al 5% del área (`deposit_recovery@5%`).
- **Modelo Ganador**: `logistic_01` (Regresión Logística L2, $C=0.1$, ratio $P/U=3$).
  - Rendimiento CV interna desarrollo: `deposit_recovery@5% = 0.3206`, `ROC-AUC = 0.7357`.
  - Rendimiento OOF desarrollo (folds externos): `deposit_recovery@5% = 0.4389 \pm 0.1804`, `ROC-AUC = 0.7402 \pm 0.2054`.
- **Ajuste Final de Desarrollo**: Entrenado sobre la muestra global de desarrollo (112 celdas $P$ + 336 celdas $U$ = 448 observaciones), congelado y serializado en [`final_validated_model.joblib`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_f/20260927T135750_819061Z/final_model/final_validated_model.joblib).
- **Ejecución Canónica Sellada**: [`reports/fase_f/20260927T135750_819061Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_f/20260927T135750_819061Z).

### 2.6. Fase G: Evaluación Ciega Final en Holdout
- **Universo de Test**: 13.541 celdas elegibles (13.539,26 km²), 19 celdas $P$, 8 depósitos independientes.
- **Resultados Globales Observados**:
  - `deposit_recovery@1% = 0.1250` (1 / 8 depósitos: Rodalquilar Cinto)
  - `deposit_recovery@5% = 0.1250` (1 / 8 depósitos: Rodalquilar Cinto)
  - `deposit_recovery@10% = 0.2500` (2 / 8 depósitos: Rodalquilar Cinto y La Oriental)
  - `cell_recovery@5% = 0.1579` (3 / 19 celdas $P$)
  - `cell_recovery@10% = 0.2105` (4 / 19 celdas $P$)
  - `ROC-AUC P/U = 0.5807`
  - `Average Precision P/U = 0.0065` (prevalencia base = 0,0014)
- **Ejecución Canónica Sellada**: [`reports/fase_g/20260927T141408_460613Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_g/20260927T141408_460613Z).

---

## 3. Productos Cartográficos y Entregables GIS de Fase H

La Fase H ha generado la suite completa de entregables geoespaciales raster y vectoriales en el directorio sellado [`reports/fase_h/20260927T142549_961719Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_h/20260927T142549_961719Z):

| Formato | Nombre del Archivo | Descripción Técnica |
| :--- | :--- | :--- |
| **COG Raster** | [`mapa_nacional_favorabilidad_score.tif`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_h/20260927T142549_961719Z/maps/mapa_nacional_favorabilidad_score.tif) | Cloud Optimized GeoTIFF (Float32, EPSG:25830, 1 km). Favorability score continuo del modelo (0.0003 a 0.9899) en el dominio peninsular modelado. |
| **COG Raster** | [`mapa_nacional_favorabilidad_percentil.tif`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_h/20260927T142549_961719Z/maps/mapa_nacional_favorabilidad_percentil.tif) | Cloud Optimized GeoTIFF (Float32, EPSG:25830, 1 km). Percentil acumulado sobre el dominio peninsular modelado (0% a 100%). |
| **COG Raster** | [`mapa_nacional_bandas_prioritarias.tif`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_h/20260927T142549_961719Z/maps/mapa_nacional_bandas_prioritarias.tif) | Cloud Optimized GeoTIFF categórico (Byte, EPSG:25830). Código 1: Top 1%, Código 2: Top 1-5%, Código 3: Top 5-10%, Código 0: Fondo. |
| **GeoParquet** | [`mapa_nacional_prospectividad.geoparquet`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_h/20260927T142549_961719Z/maps/mapa_nacional_prospectividad.geoparquet) | GeoParquet con las 478.443 celdas elegibles, centroides (Point EPSG:25830), score, percentil, fila, columna y banda de prioridad. |
| **GeoPackage** | [`mapa_nacional_prospectividad.gpkg`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_h/20260927T142549_961719Z/maps/mapa_nacional_prospectividad.gpkg) | Capa `celdas_priorizadas_top10`: 47.845 centroides en el 10% superior. Capa `zonas_prospectividad`: 1.529 polígonos de zonas prioritarias. |

### Umbrales de Priorización Territorial sobre el Dominio Peninsular Modelado
Derivados de la distribución del área terrestre acumulada sobre las 478.443 celdas elegibles del inventario:
- **Banda Top 1% de Área**: Favorability score $\ge \mathbf{0,8333}$ (Superficie: 4.783,7 km²).
- **Banda Top 5% de Área**: Favorability score $\ge \mathbf{0,6526}$ (Superficie acumulada: 23.918,3 km²).
- **Banda Top 10% de Área**: Favorability score $\ge \mathbf{0,5179}$ (Superficie acumulada: 47.837,0 km²).

---

## 4. Delineación y Ranking de Zonas de Prospectividad/Priorización

A partir de la conectividad espacial de las celdas clasificadas en el Top 1% y Top 5% de favorabilidad en el dominio peninsular modelado, se delinearon mediante análisis de vecindad 8-conectada un total de **1.529 zonas contiguas de prospectividad/priorización**, vectorizadas en polígonos cerrados en [`targets/zonas_prospectividad_ranking.csv`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_h/20260927T142549_961719Z/targets/zonas_prospectividad_ranking.csv):

| Ranking | Identificador | Categoría de Prioridad | Superficie (km²) | Score Máx. | Score Medio | Depósito Histórico Próximo | Distrito Asociado | Distancia al Depósito (km) |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :---: |
| **1** | `zona_priorizacion_1425` | Muy Alta (Top 1%) | 28,0 | **0,9899** | 0,9325 | `dep_mina_pepin_espiel` | Valle del Guadiato | 22,4 km |
| **2** | `zona_priorizacion_1381` | Muy Alta (Top 1%) | 84,0 | **0,9898** | 0,9618 | `dep_aguablanca` | Ossa Morena (Monesterio) | 40,0 km |
| **3** | `zona_priorizacion_1128` | Muy Alta (Top 1%) | 7,0 | **0,9892** | 0,8911 | `dep_la_oriental_la_jara` | Montes de Toledo / La Jara | 127,3 km |
| **4** | `zona_priorizacion_1360` | Muy Alta (Top 1%) | 43,0 | **0,9889** | 0,9268 | `dep_california_extremena_monesterio` | Ossa Morena (Monesterio) | 26,0 km |
| **5** | `zona_priorizacion_1428` | Muy Alta (Top 1%) | 79,0 | **0,9887** | 0,8787 | `dep_aguablanca` | Ossa Morena (Monesterio) | 5,6 km |
| **6** | `zona_priorizacion_1323` | Muy Alta (Top 1%) | 2,0 | **0,9886** | 0,9593 | `dep_aguablanca` | Ossa Morena (Monesterio) | 44,1 km |
| **7** | `zona_priorizacion_1245` | Muy Alta (Top 1%) | 32,0 | **0,9885** | 0,8880 | `dep_mina_pepin_espiel` | Valle del Guadiato | 108,6 km |
| **8** | `zona_priorizacion_1152` | Muy Alta (Top 1%) | 15,0 | **0,9881** | 0,9223 | `dep_la_oriental_la_jara` | Montes de Toledo / La Jara | 125,0 km |
| **9** | `zona_priorizacion_1433` | Muy Alta (Top 1%) | 77,0 | **0,9881** | 0,9178 | `dep_navalmedio_penaflor` | Ossa Morena (Peñaflor) | 29,7 km |
| **10** | `zona_priorizacion_1234` | Muy Alta (Top 1%) | 18,0 | **0,9875** | 0,9142 | `dep_el_chocolatero_segura` | Ossa Morena (Bodonal) | 64,1 km |

> [!IMPORTANT]
> **Anotación Geográfica Post-Hoc Exclusiva**: Las columnas relativas a depósitos y distritos históricos (`Depósito Histórico Próximo`, `Distrito Asociado`, `Distancia al Depósito (km)`) fueron computadas **exclusivamente como anotación descriptiva post-hoc** una vez delineados y clasificados los polígonos de las zonas vectoriales, con el único fin de proveer contexto geográfico a equipos de exploración. **Ningún identificador, etiqueta, distancia ni metadato de yacimientos conocidos formó parte del vector de variables predictoras $X$ ni intervino en la inferencia del modelo.**

> [!CAUTION]
> **Aviso de Responsabilidad Geológica**: Estas zonas representan agrupaciones estadísticas de alta similitud multivariante respecto a las firmas geológicas del conjunto de entrenamiento de desarrollo. **No constituyen cubicaciones mineras, recursos inferidos ni yacimientos demostrados**. Deben utilizarse exclusivamente como guía para campañas de campo de reconocimiento geoquímico y geofísico.

---

## 5. Interpretabilidad del Modelo: Coeficientes y Casos de Estudio

### 5.1. Coeficientes Estandarizados Globales
El modelo `logistic_01` asigna pesos lineales (escala logit) sobre las variables estandarizadas ([`interpretability/coeficientes_estandarizados.csv`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_h/20260927T142549_961719Z/interpretability/coeficientes_estandarizados.csv)). En la formulación de la regresión logística con variables estandarizadas, $\exp(\beta)$ representa el **Odds Ratio**, es decir, el cambio proporcional en los odds relativos de favorabilidad por cada incremento de **1 desviación estándar ($+1\sigma$) de la variable continua después del preprocesamiento con `StandardScaler`**:

- **Variables con Mayor Impacto Positivo (Aumentan Favorabilidad)**:
  1. `edades_u023_fraccion` ($\beta = +0,5962$, Odds Ratio = 1,815 por $+1\sigma$): Fracción de rocas del **Silúrico-Devónico**.
  2. `litologia_u019_fraccion` ($\beta = +0,4391$, Odds Ratio = 1,551 por $+1\sigma$): **Vulcanitas y rocas volcanoclásticas**.
  3. `elevacion_media_m` ($\beta = +0,3943$, Odds Ratio = 1,483 por $+1\sigma$): Elevación topográfica media (afloramientos montañosos de zócalo primario vs. cuencas sedimentarias).
  4. `litologia_u008_fraccion` ($\beta = +0,3817$, Odds Ratio = 1,465 por $+1\sigma$): **Cuarcitas, pizarras, areniscas y calizas** (facies paleozoicas tipo Serie de Los Cabos / Cuarcita Armoricana).
  5. `litologia_u011_fraccion` ($\beta = +0,3518$, Odds Ratio = 1,422 por $+1\sigma$): **Granitoides de dos micas** (plutonismo hercínico tardío).
  6. `litologia_u016_fraccion` ($\beta = +0,3008$, Odds Ratio = 1,351 por $+1\sigma$): Pizarras, grauwackas y cuarcitas.
  7. `edades_u006_fraccion` ($\beta = +0,2861$, Odds Ratio = 1,331 por $+1\sigma$): Cámbrico-Ordovícico.
  8. `edades_u013_fraccion` ($\beta = +0,2738$, Odds Ratio = 1,315 por $+1\sigma$): Ordovícico.
  9. `edades_u017_fraccion` ($\beta = +0,2625$, Odds Ratio = 1,300 por $+1\sigma$): Proterozoico Superior - Vendiense.
  10. `dist_falla_cartografiada_m` ($\beta = +0,2122$, Odds Ratio = 1,236 por $+1\sigma$): Distancia euclídea a trazas de fallas cartografiadas.

- **Variables con Mayor Impacto Negativo (Disminuyen Favorabilidad)**:
  1. `dist_cauce_m` ($\beta = -0,4482$, Odds Ratio = 0,639 por $+1\sigma$): Distancia a cauce.
  2. `litologia_u015_fraccion` ($\beta = -0,3192$, Odds Ratio = 0,727 por $+1\sigma$): "Otros granitoides" indiferenciados.
  3. `litologia_u005_fraccion` ($\beta = -0,2729$, Odds Ratio = 0,761 por $+1\sigma$): Conglomerados, arcillas y evaporitas terciarias/mesozoicas.
  4. `litologia_u009_fraccion` ($\beta = -0,2702$, Odds Ratio = 0,763 por $+1\sigma$): Dolomías, calizas y margas mesozoicas.
  5. `tpi_5000m_m` ($\beta = -0,2692$, Odds Ratio = 0,764 por $+1\sigma$): Índice de Posición Topográfica regional a 5 km.
  6. `edades_u002_fraccion` ($\beta = -0,2494$, Odds Ratio = 0,779 por $+1\sigma$): Cretácico.
  7. `edades_u025_fraccion` ($\beta = -0,2273$, Odds Ratio = 0,797 por $+1\sigma$): Triásico.
  8. `edades_u016_fraccion` ($\beta = -0,2181$, Odds Ratio = 0,804 por $+1\sigma$): Paleógeno-Neógeno (cuencas sedimentarias estériles).

### 5.2. Análisis Riguroso del Signo en Variables Estructurales y de Distancia

El análisis multivariante exige diferenciar nítidamente la evidencia matemática del modelo frente a la interpretación geológica, formulando explicaciones como hipótesis estadísticas y no como leyes causales demostradas:

| Variable de Distancia | Coeficiente Estandarizado ($\beta$) | Odds Ratio ($e^\beta$, cambio por $+1\sigma$) | Comportamiento Matemático del Modelo | Hipótesis Geológica y Análisis de Datos |
| :--- | :---: | :---: | :--- | :--- |
| `dist_cauce_m` | **-0,4482** | **0,639** | **Negativo**: a menor distancia al cauce, mayor favorability score. | Fuerte asociación espacial con valles encajados a lo largo de zonas de fractura y presencia de depósitos aluviales/placer en el inventario de desarrollo. |
| `dist_contacto_intrusivo_cartografiada_m` | **-0,1335** | **0,875** | **Negativo**: a menor distancia al contacto ígneo, mayor favorability score. | Coherente con halos metamórficos térmicos, skarns y mineralizaciones peribatolíticas hercínicas. |
| `dist_cabalgamiento_cartografiada_m` | **-0,0769** | **0,926** | **Negativo**: a menor distancia a cabalgamientos, mayor favorability score. | Coherente con trampas estructurales compresivas y cizallas dúctiles hercínicas. |
| `dist_falla_cartografiada_m` | **+0,2122** | **1,236** | **Positivo**: condicionado al resto de covariables, a mayor distancia a fallas cartografiadas, mayor favorability score. | **Hipótesis estadística y cartográfica (no mecanismo demostrado)**: Se formula como hipótesis que el signo positivo deriva de la colinealidad multivariante en la regresión regularizada L2 cuando conviven otras variables estructurales (cabalgamientos y contactos intrusivos con coeficientes negativos), combinado con posibles artefactos de escala cartográfica (1:1.000.000) y la concentración del muestreo de fondo $U$ en zonas montañosas con densa fracturación cartografiada regional. |

> [!WARNING]
> **No Causalidad en el Signo de `dist_falla_cartografiada_m`**: El coeficiente positivo de `dist_falla_cartografiada_m` no significa que el oro prefiera alejarse de las fallas ni constituye un mecanismo físico demostrado de formación de yacimientos. Es una propiedad matemática del ajuste lineal regularizado L2 sobre el espacio conjunto de las 56 variables aprobadas en los 27 distritos de desarrollo. En modelos multivariantes con variables correlacionadas (cabalgamientos, litología y fallas), los signos univariantes pueden invertirse legítimamente sin implicar causalidad geológica.

### 5.3. Análisis de Contribuciones Locales en Casos de Estudio: Diagnósticos e Hipótesis

El desglose de log-odds ($\beta_j \tilde{x}_j$) registrado en [`interpretability/contribuciones_locales_casos_estudio.csv`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_h/20260927T142549_961719Z/interpretability/contribuciones_locales_casos_estudio.csv) documenta la descomposición matemática en los cuatro distritos clave:

1. **`dep_rodalquilar_cinto` (Score: 0,8739 – 0,8801 | Rango Holdout: 47 / 13.541 | Percentil: 99,65%)**:
   - *Evidencia del Modelo*: La variable `litologia_u019_fraccion` aporta $+4,476$ log-odds debido a la presencia dominante de vulcanitas calcoalcalinas neógenas. Aunque la baja elevación costera resta $-0,498$, el término volcánico sitúa la celda en el Top 0,35% del holdout ciego.
   - *Hipótesis Geológica*: El clasificador lineal reconoce con éxito la singularidad litológica del complejo volcánico de Cabo de Gata frente a la corteza sedimentaria o metamórfica circundante.

2. **`dep_la_oriental_la_jara` (Score máx: 0,6333 | Rango Holdout: 940 / 13.541 | Percentil: 93,07%)**:
   - *Evidencia del Modelo*: Contribuciones positivas sustanciales de `litologia_u008_fraccion` ($+0,645$), `litologia_u016_fraccion` ($+0,249$) y `edades_u017_fraccion` ($+0,246$). El depósito queda clasificado en el Top 6,93% del holdout (Top 10%).
   - *Hipótesis Geológica*: La combinación de metasedimentos del Proterozoico Superior / Paleozoico Inferior con relieve moderado proporciona una firma afín a los depósitos orogénicos del zócalo centroibérico presentes en el entrenamiento.

3. **`dep_corcoesto` (Score: 0,0582 | Rango Holdout: 8.524 / 13.541 | Percentil: 37,05%)**:
   - *Evidencia del Modelo*: A pesar del aporte positivo de `edades_u006_fraccion` ($+1,233$), la celda se clasifica en `litologia_u015_fraccion` ("Otros granitoides"), que impone una fuerte penalización de $-1,773$ log-odds, combinada con la baja cota costera ($-0,538$). El score resultante cae a la mitad inferior de la distribución.
   - *Hipótesis Geológica Explicativa (No Demostrada Causalmente)*: Se postula como hipótesis que, al carecer el modelo de geoquímica analítica aprobada de elementos guía (As, Sb, Bi) y de densidad de vetas de cuarzo a escala de detalle, el clasificador regional no dispone de información para distinguir un granitoide atravesado por una zona de cizalla fértil de un macizo plutónico estéril regional, asimilándolo al fondo litológico granítico.

4. **`dep_santa_comba_zas` (Score medio: 0,0476 | Rango Holdout: 8.152 / 13.541 | Percentil: 39,80%)**:
   - *Evidencia del Modelo*: Mismo patrón matemático de Corcoesto. Penalizaciones concurrentes de `litologia_u015_fraccion` ($-0,667$), `litologia_u018_fraccion` ($-0,434$) y `edades_u000_fraccion` ($-0,367$) neutralizan los términos estructurales e hidrológicos.
   - *Hipótesis Geológica Explicativa (No Demostrada Causalmente)*: Se formula la hipótesis de que las mineralizaciones de Au-W asociadas a leucogranitos hercínicos en Galicia requieren información composicional y mineralógica fina que no está resuelta a la escala cartográfica regional de 1:200.000 / 1 km².

---

## 6. Sensibilidad de Incertidumbre sobre Predicciones de Fase G

El análisis de sensibilidad por distritos sobre las predicciones selladas en Fase G ([`uncertainty/sensibilidad_leave_one_district_out.csv`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_h/20260927T142549_961719Z/uncertainty/sensibilidad_leave_one_district_out.csv)) demuestra el tremendo impacto que tiene la heterogeneidad regional en muestras pequeñas:

| Distrito Omitido | Distritos Evaluados | Depósitos Evaluados | Recovery @ 5% | Recovery @ 10% | ROC-AUC P/U | Variación ROC-AUC vs. Holdout Completo (0,5807) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| *(Holdout Completo)* | *5* | *8* | *0,1250* | *0,2500* | *0,5807* | *Referencia* |
| `dist_galicia_costa_da_morte` | 4 | 6 | 0,1667 | **0,3333** | **0,6988** | **+0,1181** |
| `dist_ossa_morena_penaflor` | 4 | 6 | 0,1667 | **0,3333** | **0,6239** | **+0,0432** |
| `dist_montes_de_toledo_jara` | 4 | 7 | 0,1429 | 0,2857 | **0,6023** | **+0,0216** |
| `dist_beticas_granada` | 4 | 7 | 0,1429 | 0,1429 | **0,5052** | **-0,0755** |
| `dist_cabo_de_gata` | 4 | 6 | **0,0000** | 0,1667 | **0,4761** | **-0,1046** |

### Conclusiones de la Sensibilidad:
1. **La presencia de Cabo de Gata es el motor de la señal epitermal**: Si se omite Cabo de Gata, la recuperación al 5% cae a cero y el ROC-AUC se reduce a 0,4761.
2. **La presencia de Costa da Morte impacta la métrica global**: Si se omite Costa da Morte, el ROC-AUC del modelo asciende a 0,6988 (+0,118) y la recuperación al 10% alcanza un tercio de los depósitos.
3. Esto prueba rigurosamente que el rendimiento del modelo en holdout depende fuertemente de la afinidad metalogenética del distrito con las variables geológicas dominantes.

---

## 7. Limitaciones Científicas Explícitas del Proyecto

Para garantizar una honestidad intelectual sin concesiones, se documentan las limitaciones estructurales del estudio:

1. **Tamaño Muestral de Depósitos Modelables en el Inventario Auditado ($N=45$)**:
   El inventario auditado de España peninsular cuenta únicamente con 45 depósitos independientes de oro con presencia confirmada y cobertura completa de predictores. En aprendizaje automático, entrenar con 37 depósitos y testear con 8 es una muestra muy reducida que impone alta varianza estimativa.
2. **Potencia Estadística en el Test Ciego ($N=8$)**:
   Con solo 8 depósitos en holdout, cada acierto o fallo representa un salto discreto del 12,5% en la tasa de recuperación. Los intervalos de confianza bootstrap del 95% calculados en Fase G abarcan desde 0% hasta 37,5% (al 5% de área) y hasta 50% (al 10% de área).
3. **Heterogeneidad Metalogenética Ineludible**:
   El oro en España se presenta en estilos geológicos radicalmente dispares:
   - Depósitos filonianos orogénicos en zonas de cizalla dúctil-frágil (Galicia, Asturias, León).
   - Intrusiones graníticas y skarns de Au-Bi-As-W (Salave, Carles, Extremadura).
   - Epitermales volcánicos de alta sulfuración vinculados al magmatismo calcoalcalino neógeno (Rodalquilar).
   - Placeres aluviales cenozoicos (cuencas fluviales del Miño, Sil, Duero).
   Un único clasificador lineal no puede capturar con igual eficacia tipologías con firmas genéticas tan diferentes.
4. **Ausencia de Capas Geoquímicas Aprobadas**:
   El Atlas Geoquímico de Sedimentos de Corriente disponible presentaba limitaciones insalvables (datos derivados de clasificación por intervalos de color, discontinuidades espaciales en costas y fronteras, y falta de ensayos analíticos cuantitativos continuos). Su exclusión en Fase D protegió al modelo del sobreajuste y del sesgo de muestreo, pero privó al clasificador de los vectores de dispersión química secundaria (As, Sb, Bi, Au) fundamentales para localizar yacimientos en zonas como la Costa da Morte.
5. **Brecha de Transferencia Observada ($N=8$)**:
   La diferencia entre la estimación OOF de desarrollo en Fase F (ROC-AUC 0,7402; recovery@5% 43,89%) y el rendimiento ciego en Fase G (ROC-AUC 0,5807; recovery@5% 12,50%) se denomina técnicamente **brecha de transferencia observada ($N=8$)**. Refleja que la capacidad de generalización espacial decae cuando el clasificador se enfrenta a distritos geográficamente distantes con estilos geológicos no balanceados en el conjunto de entrenamiento.

---

## 8. Dictamen Final y Conclusión del Proyecto

1. **Cierre Formal**: La cadena metodológica $B \rightarrow C \rightarrow D \rightarrow E \rightarrow F \rightarrow G \rightarrow H$ queda formalmente **completada, sellada y cerrada** en [`reports/fase_h/20260927T142549_961719Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_h/20260927T142549_961719Z).
2. **Productos Disponibles**: Los mapas COG raster y vectoriales GeoPackage/GeoParquet se encuentran listos para su integración en sistemas GIS (QGIS, ArcGIS) por parte de equipos geológicos de exploración bajo la versión **GeoAI-Au v1.0**.
3. **Reproducibilidad Garantizada**: Todos los algoritmos, datos procesados, manifiestos SHA-256 y suites de pruebas unitarias (77 tests) quedan preservados de forma determinista para su verificación y auditoría externa.
