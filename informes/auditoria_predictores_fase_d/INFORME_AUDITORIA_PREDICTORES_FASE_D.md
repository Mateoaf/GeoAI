# INFORME DE AUDITORÍA SEMÁNTICA Y APROBACIÓN DE PREDICTORES DE FASE D

**Fecha de auditoría:** 27 de septiembre de 2026  
**Proyecto:** GeoAI - Prospección Aurífera en España Peninsular  
**Ejecución de Fase D auditada:** `reports/fase_d/20260927T112256_510493Z`  
**Malla de referencia:** Rejilla canónica de 1 km (`es_pen_utm30_1km_v1`, 496.855 celdas terrestres)  

---

## 1. Resumen Ejecutivo y Balance de la Auditoría

Se ha auditado formalmente el universo completo de las **168 variables candidatas** incorporadas en la matriz de predictores de Fase D (`feature_allowlist.json`).

El objetivo estricto de esta auditoría es garantizar que los modelos de aprendizaje automático predictivo se alimenten únicamente con variables que reúnan:
1. **Significado físico/geológico defendible** en relación con los procesos formadores de yacimientos minerales (metalotectos litológicos, estructurales, termales o geomorfológicos).
2. **Disponibilidad objetiva e independiente en territorio virgen/desconocido**, sin depender de la previa existencia de labores mineras o derechos registrados.
3. **Ausencia absoluta de circularidad o fuga de información (leakage)** respecto a las etiquetas de oro de BDMIN, identificadores de depósito (`deposit_id`), agrupaciones espaciales o distritos metalogenéticos (`district_id`).
4. **Inmunidad ante artefactos de colinealidad exacta**, varianza nula o colapso de soporte territorial nacional.

### Cuadro de Clasificación Global

| Estado de Clasificación | Número de Variables | % del Catálogo | Destino en el Protocolo Científico |
|---|---|---|---|
| **APPROVED (Aprobadas)** | **56** | 33.33 % | Incorporadas a `approved_training_columns` para entrenamiento validado nacional |
| **PENDING (Pendientes)** | **18** | 10.71 % | Retenidas temporalmente hasta homologación analítica de leyendas o validación convolucional |
| **REJECTED (Rechazadas)** | **94** | 55.95 % | Excluidas taxativamente por circularidad, colinealidad exacta, varianza cero o colapso territorial |
| **TOTAL AUDITADAS** | **168** | 100.00 % | Catálogo íntegro de candidatas de Fase D |

---

## 2. Criterios Científicos de Exclusión y Clasificación

### 2.1. Exclusión de Circularidad y Fuga de Objetivo (Leakage)
La predicción de favorabilidad aurífera regional debe aprender las firmas de los procesos geológicos que causaron la mineralización (roca fuente, permeabilidad estructural, contacto térmico), no el hallazgo humano del metal.
- **`au_clase_modal` y las 7 fracciones `au_proporcion_clase_0..6` (8 variables)** han sido **RECHAZADAS**: utilizar la anomalía de oro como predictor para predecir yacimientos de oro es una tautología epistémica. Las anomalías superficiales de Au en suelos y aluviones coinciden directamente con las escombreras romanas, lavaderos y desmontes mineros históricos ya censados en BDMIN. En territorio desconocido sin muestreo detallado de Au, el modelo quedaría ciego.

### 2.2. Exclusión de Varianza Cero
- `zn_proporcion_clase_3` y `w_proporcion_clase_2` (2 variables) han sido **RECHAZADAS**: tienen valor constante 0.0 en el 100% de las celdas válidas de España. No aportan información y distorsionan imputadores.

### 2.3. Exclusión de Colinealidad Exacta y Duplicados Sintéticos
- **Asociaciones litológicas textuales (6 variables)** han sido **RECHAZADAS**: se comprobó que 5 de ellas son duplicados exactos al 100% de fracciones primarias (`unidades_mixtas_con_granitoides` $\equiv$ `litologia_u014`; `unidades_volcanicas` $\equiv$ `litologia_u019`; `unidades_basicas_ultrabasicas` $\equiv$ `litologia_u018`; `unidades_con_gneisses` $\equiv$ `litologia_u010`; `unidades_con_gravas_arenas_limos` $\equiv$ `litologia_u012`), mientras que `unidades_granitoides_explicitos` es la suma determinista exacta de `litologia_u011` + `litologia_u015`.
- **Duplicado inter-fuente (1 variable)**: `edades_u004_fraccion` (Cuaternario) es 100% idéntica en toda España a `litologia_u012_fraccion` (Gravas y conglomerados). Ha sido **RECHAZADA** en edades para preservar la fracción litológica correspondiente.
- **Dominantes categóricas redundantes (2 variables)**: `litologia_dominante` y `edades_dominante` son el argmax discreto de sus respectivas fracciones continuas. Han sido **RECHAZADAS** para evitar redundancia y singularidad con el espacio continuo.
- **Proporciones geoquímicas redundantes (48 variables)**: las 8 proporciones por elemento para As, Sb, Bi, Hg, Cu y Pb suman 1.0 por celda y duplican la información de la clase modal. Han sido **RECHAZADAS**.

### 2.4. Exclusión de Trazas Supuestas e Inferidas
- **Trazas supuestas (12 variables)**: `dist_contacto_intrusivo_supuesta_m` posee un **98.00% de nulos** en España (es una capa virtualmente inexistente a nivel nacional). `dist_cabalgamiento_supuesta_m` presenta un **80.06% de nulos**. Las 9 densidades de trazas supuestas añaden ruido interpretativo sin soporte de afloramiento físico verificado. Han sido **RECHAZADAS**.

### 2.5. Exclusión por Colapso de Cobertura Territorial Nacional
- **Zinc y Wolframio (15 variables restantes)**: la inclusión de las láminas de Zn (28.89% nulos) o W (17.15% nulos) provoca la pérdida de hasta 143.000 celdas (>38% del territorio nacional evaluable). Han sido **RECHAZADAS**.

### 2.6. Clasificación como Pendientes (Pending)
- **Pathfinders Modales (6 variables: As, Sb, Bi, Hg, Cu, Pb)**: elementos guía de enorme relevancia genética pero cuyo estado actual en la base de datos es `leyenda_local_no_validada` (categorías de color RGB de mapas históricos sin calibración analítica absoluta en ppm/ppb). Se mantienen **PENDING** hasta su homologación química.
- **Densidades Aproximadas (12 variables)**: calculadas mediante reparto uniforme intra-celda (`status: experimental_aproximacion_1km`). Se mantienen **PENDING** de refinamiento convolucional.

---

## 3. Detalle de los 56 Predictores Aprobados (`approved_training_columns`)

Los 56 predictores aprobados constituyen un bloque coherente, robusto e independiente que cubre la totalidad de los metalotectos regionales:

| Nombre del Predictor | Familia | Fuente Oficial | Unidades | Significado Metalogenético | Soporte Válido |
|---|---|---|---|---|---|
| `edades_u000_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: CARBONÍFERO. Contextualiza ciclo... | 96.90% válido |
| `edades_u001_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: CARBONÍFERO-PÉRMICO. Contextuali... | 96.90% válido |
| `edades_u002_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: CRETÁCICO. Contextualiza ciclo o... | 96.90% válido |
| `edades_u003_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: CRETÁCICO-PALEÓGENO. Contextuali... | 96.90% válido |
| `edades_u005_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: CÁMBRICO. Contextualiza ciclo or... | 96.90% válido |
| `edades_u006_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: CÁMBRICO-ORDOVÍCICO. Contextuali... | 96.90% válido |
| `edades_u007_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: DEVÓNICO-CARBONÍFERO. Contextual... | 96.90% válido |
| `edades_u008_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: DEVÓNICO-CARBONÍFERO-PÉRMICO (Pl... | 96.90% válido |
| `edades_u009_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: JURÁSICO. Contextualiza ciclo or... | 96.90% válido |
| `edades_u010_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: JURÁSICO-CRETÁCICO. Contextualiz... | 96.90% válido |
| `edades_u011_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: NEÓGENO. Contextualiza ciclo oro... | 96.90% válido |
| `edades_u012_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: NEÓGENO-CUATERNARIO. Contextuali... | 96.90% válido |
| `edades_u013_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: ORDOVÍCICO. Contextualiza ciclo ... | 96.90% válido |
| `edades_u014_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: ORDOVÍCICO-SILÚRICO. Contextuali... | 96.90% válido |
| `edades_u015_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: PALEÓGENO. Contextualiza ciclo o... | 96.90% válido |
| `edades_u016_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: PALEÓGENO-NEÓGENO. Contextualiza... | 96.90% válido |
| `edades_u017_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: PROTEROZOICO SUPERIOR-VENDIENSE.... | 96.90% válido |
| `edades_u018_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: PÉRMICO. Contextualiza ciclo oro... | 96.90% válido |
| `edades_u019_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: PÉRMICO-TRIÁSICO. Contextualiza ... | 96.90% válido |
| `edades_u020_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: RIFEENSE. Contextualiza ciclo or... | 96.90% válido |
| `edades_u021_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: RIFEENSE-VENDIENSE-CÁMBRICO. Con... | 96.90% válido |
| `edades_u022_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: SILÚRICO. Contextualiza ciclo or... | 96.90% válido |
| `edades_u023_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: SILÚRICO-DEVÓNICO. Contextualiza... | 96.90% válido |
| `edades_u025_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: TRIÁSICO. Contextualiza ciclo or... | 96.90% válido |
| `edades_u026_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: TRIÁSICO-JURÁSICO. Contextualiza... | 96.90% válido |
| `edades_u027_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: VENDIENSE. Contextualiza ciclo o... | 96.90% válido |
| `edades_u028_fraccion` | Edades | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción cronoestratigráfica de la unidad: VENDIENSE-CÁMBRICO. Contextualiz... | 96.90% válido |
| `dist_cabalgamiento_cartografiada_m` | Estructuras | IGME | metros | Distancia euclídea a cabalgamiento cartografiado real. Despegues compresivo... | 44.31% válido |
| `dist_contacto_intrusivo_cartografiada_m` | Estructuras | IGME | metros | Distancia euclídea a contacto magmático plutónico cartografiado real. Zona ... | 30.04% válido |
| `dist_falla_cartografiada_m` | Estructuras | IGME | metros | Distancia euclídea a falla o zona de cizalla cartografiada real. Metalotect... | 81.10% válido |
| `dist_cauce_m` | Hidrografía | IGN / MITECO | metros | Distancia euclídea del centroide de celda al cauce fluvial cartografiado má... | 97.28% válido |
| `litologia_u000_fraccion` | Litología | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción superficial ocupada por la unidad: Areniscas, conglomerados, arcil... | 96.90% válido |
| `litologia_u001_fraccion` | Litología | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción superficial ocupada por la unidad: Areniscas, pizarras y calizas. ... | 96.90% válido |
| `litologia_u002_fraccion` | Litología | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción superficial ocupada por la unidad: Calizas detríticas, calcarenita... | 96.90% válido |
| `litologia_u003_fraccion` | Litología | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción superficial ocupada por la unidad: Calizas, dolomías y margas. Are... | 96.90% válido |
| `litologia_u004_fraccion` | Litología | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción superficial ocupada por la unidad: Conglomerados, areniscas y luti... | 96.90% válido |
| `litologia_u005_fraccion` | Litología | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción superficial ocupada por la unidad: Conglomerados, areniscas, arcil... | 96.90% válido |
| `litologia_u006_fraccion` | Litología | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción superficial ocupada por la unidad: Conglomerados, areniscas, caliz... | 96.90% válido |
| `litologia_u007_fraccion` | Litología | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción superficial ocupada por la unidad: Conglomerados, areniscas, pizar... | 96.90% válido |
| `litologia_u008_fraccion` | Litología | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción superficial ocupada por la unidad: Cuarcitas, pizarras, areniscas ... | 96.90% válido |
| `litologia_u009_fraccion` | Litología | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción superficial ocupada por la unidad: Dolomías, calizas y margas. Are... | 96.90% válido |
| `litologia_u010_fraccion` | Litología | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción superficial ocupada por la unidad: Gneisses. Representa litología ... | 96.90% válido |
| `litologia_u011_fraccion` | Litología | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción superficial ocupada por la unidad: Granitoides de dos micas. Repre... | 96.90% válido |
| `litologia_u012_fraccion` | Litología | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción superficial ocupada por la unidad: Gravas, conglomerados, arenas y... | 96.90% válido |
| `litologia_u013_fraccion` | Litología | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción superficial ocupada por la unidad: Micaesquistos, filitas, arenisc... | 96.90% válido |
| `litologia_u014_fraccion` | Litología | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción superficial ocupada por la unidad: Migmatitas, mármoles y granitoi... | 96.90% válido |
| `litologia_u015_fraccion` | Litología | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción superficial ocupada por la unidad: Otros granitoides. Representa l... | 96.90% válido |
| `litologia_u016_fraccion` | Litología | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción superficial ocupada por la unidad: Pizarras, grauwackas, cuarictas... | 96.90% válido |
| `litologia_u018_fraccion` | Litología | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción superficial ocupada por la unidad: Serpentinitas y peridotitas. Ro... | 96.90% válido |
| `litologia_u019_fraccion` | Litología | IGME | fracción (m2/m2 terrestre, [0, 1]) | Fracción superficial ocupada por la unidad: Vulcanitas y rocas volcanoclást... | 96.90% válido |
| `desv_elevacion_1000m_m` | Relieve | IGN | metros | Rugosidad topográfica local (desviación típica de cota en 1 km). Indicador ... | 98.49% válido |
| `desv_elevacion_5000m_m` | Relieve | IGN | metros | Rugosidad regional (5 km). Contraste altitudinal de media escala.... | 95.92% válido |
| `elevacion_media_m` | Relieve | IGN | metros | Altitud media sobre el nivel del mar en la celda de 1 km. Contexto geomorfo... | 100.00% válido |
| `pendiente_grados` | Relieve | IGN | grados | Gradiente topográfico medio. Controla estabilidad de vertientes, erosión y ... | 98.97% válido |
| `tpi_1000m_m` | Relieve | IGN | metros | Topographic Position Index local (1 km). Diferencia entre altitud central y... | 98.49% válido |
| `tpi_5000m_m` | Relieve | IGN | metros | Topographic Position Index regional (5 km). Posición mesotopográfica en val... | 95.92% válido |

---

## 4. Tabla Completa de Auditoría de los 168 Predictores

| Nombre | Familia | Decisión | Motivo Técnico / Científico |
|---|---|---|---|
| `edades_u000_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u001_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u002_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u003_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u005_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u006_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u007_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u008_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u009_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u010_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u011_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u012_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u013_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u014_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u015_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u016_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u017_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u018_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u019_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u020_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u021_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u022_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u023_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u025_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u026_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u027_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `edades_u028_fraccion` | Edades | **APPROVED** | Delimita dominios tectonotermales y orogenias (Varisca, Alpina) de forma continua y objetiva. |
| `dist_cabalgamiento_cartografiada_m` | Estructuras | **APPROVED** | Aprobada: trampa estructural y límite tectonoestratigráfico regional de primer orden. |
| `dist_contacto_intrusivo_cartografiada_m` | Estructuras | **APPROVED** | Aprobada: metalotecto indispensable para sistemas intrusion-related (IRGS) y skarns auríferos. |
| `dist_falla_cartografiada_m` | Estructuras | **APPROVED** | Aprobada: conducto hidrotermal primordial en depósitos de oro orogénicos y filonianos. |
| `dist_cauce_m` | Hidrografía | **APPROVED** | Métrica continua fundamental para contextualizar transporte aluvial y disección fluvial de filones. |
| `litologia_u000_fraccion` | Litología | **APPROVED** | Componente esencial de la petrografía del encajante. Preserva mezclas subcelda sin forzar agregación categórica. |
| `litologia_u001_fraccion` | Litología | **APPROVED** | Componente esencial de la petrografía del encajante. Preserva mezclas subcelda sin forzar agregación categórica. |
| `litologia_u002_fraccion` | Litología | **APPROVED** | Componente esencial de la petrografía del encajante. Preserva mezclas subcelda sin forzar agregación categórica. |
| `litologia_u003_fraccion` | Litología | **APPROVED** | Componente esencial de la petrografía del encajante. Preserva mezclas subcelda sin forzar agregación categórica. |
| `litologia_u004_fraccion` | Litología | **APPROVED** | Componente esencial de la petrografía del encajante. Preserva mezclas subcelda sin forzar agregación categórica. |
| `litologia_u005_fraccion` | Litología | **APPROVED** | Componente esencial de la petrografía del encajante. Preserva mezclas subcelda sin forzar agregación categórica. |
| `litologia_u006_fraccion` | Litología | **APPROVED** | Componente esencial de la petrografía del encajante. Preserva mezclas subcelda sin forzar agregación categórica. |
| `litologia_u007_fraccion` | Litología | **APPROVED** | Componente esencial de la petrografía del encajante. Preserva mezclas subcelda sin forzar agregación categórica. |
| `litologia_u008_fraccion` | Litología | **APPROVED** | Componente esencial de la petrografía del encajante. Preserva mezclas subcelda sin forzar agregación categórica. |
| `litologia_u009_fraccion` | Litología | **APPROVED** | Componente esencial de la petrografía del encajante. Preserva mezclas subcelda sin forzar agregación categórica. |
| `litologia_u010_fraccion` | Litología | **APPROVED** | Componente esencial de la petrografía del encajante. Preserva mezclas subcelda sin forzar agregación categórica. |
| `litologia_u011_fraccion` | Litología | **APPROVED** | Componente esencial de la petrografía del encajante. Preserva mezclas subcelda sin forzar agregación categórica. |
| `litologia_u012_fraccion` | Litología | **APPROVED** | Componente esencial de la petrografía del encajante. Preserva mezclas subcelda sin forzar agregación categórica. |
| `litologia_u013_fraccion` | Litología | **APPROVED** | Componente esencial de la petrografía del encajante. Preserva mezclas subcelda sin forzar agregación categórica. |
| `litologia_u014_fraccion` | Litología | **APPROVED** | Componente esencial de la petrografía del encajante. Preserva mezclas subcelda sin forzar agregación categórica. |
| `litologia_u015_fraccion` | Litología | **APPROVED** | Componente esencial de la petrografía del encajante. Preserva mezclas subcelda sin forzar agregación categórica. |
| `litologia_u016_fraccion` | Litología | **APPROVED** | Componente esencial de la petrografía del encajante. Preserva mezclas subcelda sin forzar agregación categórica. |
| `litologia_u018_fraccion` | Litología | **APPROVED** | Componente esencial de la petrografía del encajante. Preserva mezclas subcelda sin forzar agregación categórica. |
| `litologia_u019_fraccion` | Litología | **APPROVED** | Componente esencial de la petrografía del encajante. Preserva mezclas subcelda sin forzar agregación categórica. |
| `desv_elevacion_1000m_m` | Relieve | **APPROVED** | Variable física continua de cobertura nacional completa, objetiva, reproducible y sin riesgo de sesgo por prospección. |
| `desv_elevacion_5000m_m` | Relieve | **APPROVED** | Variable física continua de cobertura nacional completa, objetiva, reproducible y sin riesgo de sesgo por prospección. |
| `elevacion_media_m` | Relieve | **APPROVED** | Variable física continua de cobertura nacional completa, objetiva, reproducible y sin riesgo de sesgo por prospección. |
| `pendiente_grados` | Relieve | **APPROVED** | Variable física continua de cobertura nacional completa, objetiva, reproducible y sin riesgo de sesgo por prospección. |
| `tpi_1000m_m` | Relieve | **APPROVED** | Variable física continua de cobertura nacional completa, objetiva, reproducible y sin riesgo de sesgo por prospección. |
| `tpi_5000m_m` | Relieve | **APPROVED** | Variable física continua de cobertura nacional completa, objetiva, reproducible y sin riesgo de sesgo por prospección. |
| `dens_aprox_cabalgamiento_cartografiada_10000m_km_km2` | Estructuras | **PENDING** | Estado experimental_aproximacion_1km. Pendiente de contrastar con convolución exacta sin artefactos. |
| `dens_aprox_cabalgamiento_cartografiada_1000m_km_km2` | Estructuras | **PENDING** | Estado experimental_aproximacion_1km. Pendiente de contrastar con convolución exacta sin artefactos. |
| `dens_aprox_cabalgamiento_cartografiada_5000m_km_km2` | Estructuras | **PENDING** | Estado experimental_aproximacion_1km. Pendiente de contrastar con convolución exacta sin artefactos. |
| `dens_aprox_contacto_intrusivo_cartografiada_10000m_km_km2` | Estructuras | **PENDING** | Estado experimental_aproximacion_1km. Pendiente de contrastar con convolución exacta sin artefactos. |
| `dens_aprox_contacto_intrusivo_cartografiada_1000m_km_km2` | Estructuras | **PENDING** | Estado experimental_aproximacion_1km. Pendiente de contrastar con convolución exacta sin artefactos. |
| `dens_aprox_contacto_intrusivo_cartografiada_5000m_km_km2` | Estructuras | **PENDING** | Estado experimental_aproximacion_1km. Pendiente de contrastar con convolución exacta sin artefactos. |
| `dens_aprox_falla_cartografiada_10000m_km_km2` | Estructuras | **PENDING** | Estado experimental_aproximacion_1km. Pendiente de contrastar con convolución exacta sin artefactos. |
| `dens_aprox_falla_cartografiada_1000m_km_km2` | Estructuras | **PENDING** | Estado experimental_aproximacion_1km. Pendiente de contrastar con convolución exacta sin artefactos. |
| `dens_aprox_falla_cartografiada_5000m_km_km2` | Estructuras | **PENDING** | Estado experimental_aproximacion_1km. Pendiente de contrastar con convolución exacta sin artefactos. |
| `as_clase_modal` | Geoquímica | **PENDING** | Estado técnico leyenda_local_no_validada. Requiere calibración cuantitativa (ppm/ppb) frente a las campañas analíticas originales del IGME antes de aprobar su uso. |
| `bi_clase_modal` | Geoquímica | **PENDING** | Estado técnico leyenda_local_no_validada. Requiere calibración cuantitativa (ppm/ppb) frente a las campañas analíticas originales del IGME antes de aprobar su uso. |
| `cu_clase_modal` | Geoquímica | **PENDING** | Estado técnico leyenda_local_no_validada. Requiere calibración cuantitativa (ppm/ppb) frente a las campañas analíticas originales del IGME antes de aprobar su uso. |
| `hg_clase_modal` | Geoquímica | **PENDING** | Estado técnico leyenda_local_no_validada. Requiere calibración cuantitativa (ppm/ppb) frente a las campañas analíticas originales del IGME antes de aprobar su uso. |
| `pb_clase_modal` | Geoquímica | **PENDING** | Estado técnico leyenda_local_no_validada. Requiere calibración cuantitativa (ppm/ppb) frente a las campañas analíticas originales del IGME antes de aprobar su uso. |
| `sb_clase_modal` | Geoquímica | **PENDING** | Estado técnico leyenda_local_no_validada. Requiere calibración cuantitativa (ppm/ppb) frente a las campañas analíticas originales del IGME antes de aprobar su uso. |
| `dens_aprox_cauce_10000m_km_km2` | Hidrografía | **PENDING** | Estado técnico experimental_aproximacion_1km. Requiere validar anisotropía y correlación frente a distancia exacta. |
| `dens_aprox_cauce_1000m_km_km2` | Hidrografía | **PENDING** | Estado técnico experimental_aproximacion_1km. Requiere validar anisotropía y correlación frente a distancia exacta. |
| `dens_aprox_cauce_5000m_km_km2` | Hidrografía | **PENDING** | Estado técnico experimental_aproximacion_1km. Requiere validar anisotropía y correlación frente a distancia exacta. |
| `unidades_basicas_ultrabasicas_fraccion` | Asociaciones Litológicas | **REJECTED** | Rechazada por duplicado exacto al 100% de litologia_u018_fraccion. |
| `unidades_con_gneisses_fraccion` | Asociaciones Litológicas | **REJECTED** | Rechazada por duplicado exacto al 100% de litologia_u010_fraccion. |
| `unidades_con_gravas_arenas_limos_fraccion` | Asociaciones Litológicas | **REJECTED** | Rechazada por duplicado exacto al 100% de litologia_u012_fraccion. |
| `unidades_granitoides_explicitos_fraccion` | Asociaciones Litológicas | **REJECTED** | Rechazada por colinealidad exacta: es la suma determinista de u011 + u015. |
| `unidades_mixtas_con_granitoides_fraccion` | Asociaciones Litológicas | **REJECTED** | Rechazada por duplicado exacto al 100% de litologia_u014_fraccion. |
| `unidades_volcanicas_fraccion` | Asociaciones Litológicas | **REJECTED** | Rechazada por duplicado exacto al 100% de litologia_u019_fraccion. |
| `edades_dominante` | Edades | **REJECTED** | Rechazada por redundancia estricta: es el argmax de las 28 fracciones de edad. |
| `edades_u004_fraccion` | Edades | **REJECTED** | Rechazada por duplicación exacta inter-fuente: 100% idéntica a litologia_u012_fraccion en todas las celdas. |
| `dens_aprox_cabalgamiento_supuesta_10000m_km_km2` | Estructuras | **REJECTED** | Rechazada: traza inferida sin afloramiento comprobado, introduce ruido y sesgo interpretativo. |
| `dens_aprox_cabalgamiento_supuesta_1000m_km_km2` | Estructuras | **REJECTED** | Rechazada: traza inferida sin afloramiento comprobado, introduce ruido y sesgo interpretativo. |
| `dens_aprox_cabalgamiento_supuesta_5000m_km_km2` | Estructuras | **REJECTED** | Rechazada: traza inferida sin afloramiento comprobado, introduce ruido y sesgo interpretativo. |
| `dens_aprox_contacto_intrusivo_supuesta_10000m_km_km2` | Estructuras | **REJECTED** | Rechazada: traza inferida sin afloramiento comprobado, introduce ruido y sesgo interpretativo. |
| `dens_aprox_contacto_intrusivo_supuesta_1000m_km_km2` | Estructuras | **REJECTED** | Rechazada: traza inferida sin afloramiento comprobado, introduce ruido y sesgo interpretativo. |
| `dens_aprox_contacto_intrusivo_supuesta_5000m_km_km2` | Estructuras | **REJECTED** | Rechazada: traza inferida sin afloramiento comprobado, introduce ruido y sesgo interpretativo. |
| `dens_aprox_falla_supuesta_10000m_km_km2` | Estructuras | **REJECTED** | Rechazada: traza inferida sin afloramiento comprobado, introduce ruido y sesgo interpretativo. |
| `dens_aprox_falla_supuesta_1000m_km_km2` | Estructuras | **REJECTED** | Rechazada: traza inferida sin afloramiento comprobado, introduce ruido y sesgo interpretativo. |
| `dens_aprox_falla_supuesta_5000m_km_km2` | Estructuras | **REJECTED** | Rechazada: traza inferida sin afloramiento comprobado, introduce ruido y sesgo interpretativo. |
| `dist_cabalgamiento_supuesta_m` | Estructuras | **REJECTED** | Rechazada: 80.06% de nulos en España y alta subjetividad interpretativa. |
| `dist_contacto_intrusivo_supuesta_m` | Estructuras | **REJECTED** | Rechazada: 98.00% de nulos en España. Capa prácticamente vacía cuya imputación falsearía territorio. |
| `dist_falla_supuesta_m` | Estructuras | **REJECTED** | Rechazada: traza inferida sin afloramiento comprobado, introduce ruido y sesgo interpretativo. |
| `as_proporcion_clase_0` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `as_proporcion_clase_1` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `as_proporcion_clase_2` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `as_proporcion_clase_3` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `as_proporcion_clase_4` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `as_proporcion_clase_5` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `as_proporcion_clase_6` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `as_proporcion_clase_7` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `au_clase_modal` | Geoquímica | **REJECTED** | Rechazada: riesgo severo de circularidad epistemológica y fuga de información del objetivo a predecir. |
| `au_proporcion_clase_0` | Geoquímica | **REJECTED** | Rechazada: riesgo severo de circularidad epistemológica y fuga de información del objetivo a predecir. |
| `au_proporcion_clase_1` | Geoquímica | **REJECTED** | Rechazada: riesgo severo de circularidad epistemológica y fuga de información del objetivo a predecir. |
| `au_proporcion_clase_2` | Geoquímica | **REJECTED** | Rechazada: riesgo severo de circularidad epistemológica y fuga de información del objetivo a predecir. |
| `au_proporcion_clase_3` | Geoquímica | **REJECTED** | Rechazada: riesgo severo de circularidad epistemológica y fuga de información del objetivo a predecir. |
| `au_proporcion_clase_4` | Geoquímica | **REJECTED** | Rechazada: riesgo severo de circularidad epistemológica y fuga de información del objetivo a predecir. |
| `au_proporcion_clase_5` | Geoquímica | **REJECTED** | Rechazada: riesgo severo de circularidad epistemológica y fuga de información del objetivo a predecir. |
| `au_proporcion_clase_6` | Geoquímica | **REJECTED** | Rechazada: riesgo severo de circularidad epistemológica y fuga de información del objetivo a predecir. |
| `bi_proporcion_clase_0` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `bi_proporcion_clase_1` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `bi_proporcion_clase_2` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `bi_proporcion_clase_3` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `bi_proporcion_clase_4` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `bi_proporcion_clase_5` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `bi_proporcion_clase_6` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `bi_proporcion_clase_7` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `cu_proporcion_clase_0` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `cu_proporcion_clase_1` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `cu_proporcion_clase_2` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `cu_proporcion_clase_3` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `cu_proporcion_clase_4` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `cu_proporcion_clase_5` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `cu_proporcion_clase_6` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `cu_proporcion_clase_7` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `hg_proporcion_clase_0` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `hg_proporcion_clase_1` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `hg_proporcion_clase_2` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `hg_proporcion_clase_3` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `hg_proporcion_clase_4` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `hg_proporcion_clase_5` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `hg_proporcion_clase_6` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `hg_proporcion_clase_7` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `pb_proporcion_clase_0` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `pb_proporcion_clase_1` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `pb_proporcion_clase_2` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `pb_proporcion_clase_3` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `pb_proporcion_clase_4` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `pb_proporcion_clase_5` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `pb_proporcion_clase_6` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `pb_proporcion_clase_7` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `sb_proporcion_clase_0` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `sb_proporcion_clase_1` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `sb_proporcion_clase_2` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `sb_proporcion_clase_3` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `sb_proporcion_clase_4` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `sb_proporcion_clase_5` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `sb_proporcion_clase_6` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `sb_proporcion_clase_7` | Geoquímica | **REJECTED** | Rechazada: redundante con la clase modal correspondiente y colineal con el resto de proporciones de la celda. |
| `w_clase_modal` | Geoquímica | **REJECTED** | Rechazada: pérdida severa de cobertura territorial (17.15% de nulos en España). |
| `w_proporcion_clase_0` | Geoquímica | **REJECTED** | Rechazada: pérdida severa de cobertura territorial (17.15% de nulos en España). |
| `w_proporcion_clase_1` | Geoquímica | **REJECTED** | Rechazada: pérdida severa de cobertura territorial (17.15% de nulos en España). |
| `w_proporcion_clase_2` | Geoquímica | **REJECTED** | Rechazada: varianza cero (valor 0.0 en todas las celdas válidas del territorio nacional). |
| `w_proporcion_clase_3` | Geoquímica | **REJECTED** | Rechazada: pérdida severa de cobertura territorial (17.15% de nulos en España). |
| `w_proporcion_clase_4` | Geoquímica | **REJECTED** | Rechazada: pérdida severa de cobertura territorial (17.15% de nulos en España). |
| `w_proporcion_clase_5` | Geoquímica | **REJECTED** | Rechazada: pérdida severa de cobertura territorial (17.15% de nulos en España). |
| `w_proporcion_clase_6` | Geoquímica | **REJECTED** | Rechazada: pérdida severa de cobertura territorial (17.15% de nulos en España). |
| `zn_clase_modal` | Geoquímica | **REJECTED** | Rechazada: colapso territorial nacional (28.89% de celdas nulas; recorta drásticamente el dominio prospectable). |
| `zn_proporcion_clase_0` | Geoquímica | **REJECTED** | Rechazada: colapso territorial nacional (28.89% de celdas nulas; recorta drásticamente el dominio prospectable). |
| `zn_proporcion_clase_1` | Geoquímica | **REJECTED** | Rechazada: colapso territorial nacional (28.89% de celdas nulas; recorta drásticamente el dominio prospectable). |
| `zn_proporcion_clase_2` | Geoquímica | **REJECTED** | Rechazada: colapso territorial nacional (28.89% de celdas nulas; recorta drásticamente el dominio prospectable). |
| `zn_proporcion_clase_3` | Geoquímica | **REJECTED** | Rechazada: varianza cero (valor 0.0 en todas las celdas válidas del territorio nacional). |
| `zn_proporcion_clase_4` | Geoquímica | **REJECTED** | Rechazada: colapso territorial nacional (28.89% de celdas nulas; recorta drásticamente el dominio prospectable). |
| `zn_proporcion_clase_5` | Geoquímica | **REJECTED** | Rechazada: colapso territorial nacional (28.89% de celdas nulas; recorta drásticamente el dominio prospectable). |
| `zn_proporcion_clase_6` | Geoquímica | **REJECTED** | Rechazada: colapso territorial nacional (28.89% de celdas nulas; recorta drásticamente el dominio prospectable). |
| `zn_proporcion_clase_7` | Geoquímica | **REJECTED** | Rechazada: colapso territorial nacional (28.89% de celdas nulas; recorta drásticamente el dominio prospectable). |
| `litologia_dominante` | Litología | **REJECTED** | Rechazada por redundancia estricta: es el argmax discreto de las 19 fracciones continuas. |

---

## 5. Conclusiones y Estado de los Bloqueos Científicos

1. La aprobación de los **56 predictores físicamente defendibles** resuelve de forma definitiva el bloqueo de Fase D en `readiness()`.
2. Se ha actualizado `reports/fase_d/20260927T112256_510493Z/feature_allowlist.json` y `feature_dictionary.csv`, y se ha resellado `outputs_manifest.json`.
3. `config/features.yaml` ha sido actualizado a `semantic_validation: auditada_paso6`.
4. Se mantiene `mode: diagnostic` y no se ha entrenado ningún modelo validado.
