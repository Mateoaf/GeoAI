# Formulación formal de X/Y y plan metodológico

## 1. Pregunta científica y unidad de análisis

La pregunta predictiva incremental futura es si una señal histórica derivada de minería romana mejora la predicción espacial de mineralización moderna por encima de la información geológica y geofísica disponible. No es una estimación causal. Esta fase no entrena ni selecciona un modelo definitivo: fija labels, predictores, riesgos y comparaciones antes de integrar fuentes modernas.

La unidad recomendada para el sistema nacional es una `SpatialCell` de malla común, no cada fila de OxREP. Su resolución debe definirse después de conocer la escala efectiva de la geología, geoquímica, geofísica, precisión de los labels y objetivo operativo. Trabajar a una resolución más fina que la incertidumbre de coordenadas produciría falsa precisión. Las ocurrencias puntuales se asignarán a celdas con tratamiento explícito de incertidumbre y sensibilidad multirresolución.

### Evaluabilidad observada antes de elegir algoritmo

La auditoría real aporta 930 fichas, 923 geocodificadas y 921 pares de coordenadas únicos. La tabla siguiente cuenta positivos confirmados, no muestras independientes ni verdaderos negativos:

| Endpoint histórico | Positivos | Con coordenadas | Coordenadas únicas | Decisión en esta fase |
|---|---:|---:|---:|---|
| `Y_roman` | 930 | 923 | 921 | No entrenable todavía: solo hay clase positiva y falta máscara/background/X. |
| Au | 598 | 591 | 589 | Candidato futuro a RF y modelos regularizados si los outer folds conservan soporte espacial. |
| Ag | 174 | 174 | 174 | Exploratorio; complejidad baja/moderada y comprobación de grupos por fold. |
| Pb | 169 | 169 | 169 | Exploratorio; casi redundante con Ag en OxREP. |
| Cu | 169 | 169 | 169 | Exploratorio; concentración regional fuerte. |
| Fe / Sn / Hg / Zn | 15 / 9 / 5 / 3 | iguales | iguales | No justifican RF nacional independiente con OxREP actual. |

Au está muy concentrado: León reúne el 50,7 % y León+Oviedo el 77,8 % de sus fichas. Ag y Pb se solapan 163 veces (Jaccard 0,906). Hay 13 pares candidatos a duplicado; los registros coincidentes o próximos deben compartir fold. Por ello, el número nominal no decide la viabilidad: antes de aprobar cada endpoint se exigirá que ningún outer fold quede vacío y, como regla operativa predeclarada, al menos 10 positivos de test por fold, preferiblemente 20. Si no se cumple, se reducirán folds o complejidad, se redefinirá el endpoint con fundamento geológico o se mantendrá el análisis descriptivo.

## 2. Formulaciones de Y

### A. `Y_roman`: presencia romana frente a background

- Positivos: celdas asociadas a uno o más registros OxREP del subconjunto curado, después de aplicar una regla reproducible de asignación espacial compatible con `coordinateAccuracy`.
- No etiquetados: el resto de celdas dentro del dominio y de la máscara de cobertura de X.
- Nunca se llamarán “negativos”: ausencia de una mina romana documentada no implica ausencia de mineralización, explotación antigua no conservada, reconocimiento arqueológico o interés romano.
- Uso: modelar dónde aparece/documenta minería romana y construir una señal histórica fuera de muestra. No es por sí mismo un label de mineralización moderna.

Esta formulación es de presencia-background. También admite positive-unlabeled (PU) learning si se explicita la hipótesis de selección de positivos. La hipótesis SCAR —positivos etiquetados completamente al azar— es poco creíble: documentación, visibilidad, región, commodity, técnica y precisión espacial afectan a la probabilidad de inclusión. Conviene evaluar modelos PU sensibles a selección (SAR), ponderación por propensión/cobertura o análisis de sensibilidad, sin presentar probabilidades absolutas como calibradas hasta estimar el proceso de observación.

### B. `Y_Au`, `Y_Ag`, `Y_Cu`, `Y_Pb`, etc.

El dataset deriva booleanos *nullable* por commodity. Para una ficha:

- `True`: OxREP confirma el indicador.
- `False`: OxREP codifica explícitamente ausencia en ese campo.
- `NA`: desconocido (`?`), no informado o valor inválido.

Para presencia-background por commodity, solo `True` define un positivo; `False` en una ficha de otra commodity no demuestra que la celda carezca geológicamente de ese metal. Los recuentos actuales permiten estudiar Au, Ag, Pb y Cu exploratoriamente; Fe, Sn, Hg y Zn son muy escasos y exigen más labels, agrupaciones geológicamente justificadas o un análisis descriptivo, no un clasificador nacional independiente de alta capacidad.

### C. Formulación multi-label

Una explotación puede contener varios metales. El target por celda será un vector nullable:

`[Y_Au, Y_Ag, Y_Pb, Y_Cu, Y_Sn, Y_Fe, Y_Hg, Y_Zn, Y_Other]`.

Opciones futuras: un clasificador binario por etiqueta con el mismo esquema de validación espacial; modelos multi-output que compartan representación; o modelos jerárquicos por sistema mineral/deposit type cuando exista una ontología y masa muestral suficiente. Deben informarse métricas por etiqueta y macro/micro, sin ocultar clases raras en un promedio.

### D. Labels modernos para materias críticas y estratégicas

La prueba central necesita ocurrencias/yacimientos modernos de IGME u otra autoridad, con identificador, commodity normalizada, tipo de ocurrencia, estado, geometría, precisión, fuente y fecha. Se crearán labels separados para REE, Li, W, Sn, Co, Ni, Ta, Nb y las materias que permita el inventario real. No se inferirán de OxREP.

Antes de modelar hay que fijar qué significa “positivo moderno”: indicio, mineralización, recurso, yacimiento o explotación no son equivalentes. Se recomienda mantener niveles ontológicos separados y definir un endpoint por experimento, por ejemplo `modern_occurrence_present` o `modern_deposit_present`, con análisis de sensibilidad.

## 3. Diseño de X

Toda X debe derivarse para cada `SpatialCell` mediante un pipeline espacial versionado, registrar fuente, edición, CRS, resolución/escala, fecha de descarga, transformación, radio/ventana y máscara de cobertura.

### Predictores geológicos prioritarios

| Familia | Variables candidatas | Justificación y cautela |
|---|---|---|
| Litología | unidad litológica, clase de roca, protolito, composición, permeabilidad/fracturabilidad proxy | Controla roca huésped, fuente/reactividad y estilo de depósito; preservar jerarquía y escala cartográfica. |
| Edad | era/período/época, edades mínima/máxima, incertidumbre | Contexto tectono-magmático; no imponer precisión temporal superior al mapa. |
| Estructuras | distancia/densidad/orientación a fallas, cabalgamientos, cizallas, pliegues, intersecciones estructurales | Vías de fluidos y trampas; derivar por tipo y a varias escalas, dentro de cada fold. |
| Contactos | distancia y densidad a contactos; tipos litológicos a ambos lados | Contrastes reológicos/químicos; evitar codificar IDs de unidades como ordinales. |
| Intrusivos/volcanismo | distancia, edad y composición de cuerpos; buffers multiescala | Relevante para sistemas magmático-hidrotermales, W-Sn, pórfidos, skarn, etc. |
| Metalogenia regional | dominios tectónicos/metalogenéticos definidos independientemente del label | Contexto útil, pero una capa construida a partir de los mismos depósitos del target sería leakage. |

### Geoquímica

- Concentraciones elementales, cocientes y asociaciones multielemento en sedimento, suelo, roca o agua, con medio y fracción separados.
- Transformaciones composicionales y robustas, censura bajo límite de detección, unidades, laboratorio/campaña, profundidad y método analítico.
- Estadísticos espaciales dentro de celdas y vecindades, calculados solo con datos temporal y conceptualmente admisibles.
- Máscara de muestreo, distancia/densidad de muestras y campaña como controles del proceso de observación.

No debe imputarse una geoquímica nacional homogénea si la cobertura es parcial. El modelo debe distinguir “no muestreado” de “bajo valor”.

### Geofísica

- Magnetometría: anomalía residual/regional, gradientes, señal analítica, textura multiescala y lineamientos derivados de manera reproducible.
- Gravimetría: anomalía Bouguer/residual, gradientes y rasgos multiescala.
- Radiometría: K, eTh, eU, cocientes y ternario, preservando altura/resolución de campaña.
- Otras campañas públicas justificadas: electromagnetismo o espectrometría, si existe cobertura y licencia.

Los filtros deben fijarse dentro del pipeline y no ajustarse mirando la distribución de positivos en el test.

### DEM y geomorfología

- Elevación, pendiente, orientación transformada a seno/coseno, curvaturas, rugosidad, relieve local, TPI y posición topográfica a varias ventanas.
- Redes y paleogeomorfología cuando sea defendible: distancia a drenajes, acumulación, altura relativa, terrazas y depósitos superficiales.

La topografía puede capturar preservación/visibilidad y técnica romana además de geología. Debe modelarse y discutirse como posible mecanismo de observación, no solo como señal mineral.

### Teledetección y contexto

- Sentinel-2: índices/minerales de alteración solo donde la vegetación, suelo, atmósfera y resolución lo permitan; composiciones multitemporales reproducibles.
- Sentinel-1: textura/estructura superficial complementaria.
- Uso/cobertura del suelo, accesibilidad y densidad de observación como covariables de sesgo o estratos de background, no necesariamente como predictores del potencial geológico final.

## 4. Matriz espacial reproducible y productos cartográficos

Se adopta de Rodríguez-Galiano et al. (2015) el patrón conceptual `stack de evidencias -> SpatialCell -> matriz ML -> score continuo`, no su resolución ni su definición de clase estéril. Para cada endpoint habrá una fila por `SpatialCell`; varias fichas del mismo depósito/complejo no crearán réplicas independientes.

La matriz se separará en tablas enlazadas por `cell_id`:

- geometría, CRS, identificadores, `deposit_group_id` y provenance;
- máscaras de cobertura, observabilidad y QA;
- `X_base`, con las mismas filas y significado para todos los modelos;
- grupo `RomanSignal`, añadido únicamente al Modelo B;
- `Y`, estado positivo/no etiquetado y `sample_weight`;
- asignaciones `outer_fold`, `inner_fold`, bloque, buffer, repetición y seed en un artefacto independiente.

Las categorías litológicas no recibirán un orden numérico artificial. `NoData` no será cero. Imputación, PCA/MNF, selección de variables, escalado y cualquier transformación que aprenda parámetros se ajustarán dentro del inner fold; una transformación determinista de una fuente externa congelada puede precomputarse si se documenta su carácter inductivo/transductivo y no consulta Y.

Los productos futuros serán: mosaico de predicciones outer out-of-fold; mapas pareados A y B; `delta_score = score_B - score_A`; cobertura e incertidumbre entre particiones; y, solo después de cerrar la evaluación, un mapa final reajustado con todo el desarrollo y rotulado como no validado independientemente. Se conservará el score continuo. Un umbral operativo se elegirá en inner CV y nunca se optimizará con el mapa/test final.

## 5. Baseline RF inspirado en Rodríguez-Galiano et al. (2015)

El antecedente de Rodalquilar integra litología, fracturas, geoquímica multielemental, magnetometría, gravimetría e información hiperespectral. Añade procedimientos útiles: QA espectral; PCA geoquímico; reducción señal-ruido MNF; abundancias espectrales; interpolación versionada; análisis de sensibilidad al tamaño muestral; mapa continuo; y curva de ocurrencias capturadas frente al área priorizada. La extracción verificable, páginas y límites de transferencia están en [la ficha metodológica del artículo](rodriguez_galiano_2015_methodological_reference.md).

RF será el baseline no lineal principal cuando el endpoint tenga soporte por bloque, comparado al menos con regresión logística/MaxEnt regularizada u otro baseline transparente adecuado a presencia-background. No se fijarán 50 árboles, 15 variables por split ni ningún hiperparámetro porque funcionaran en Rodalquilar. Un número de árboles suficientemente grande se elegirá mediante estabilización; `max_features`, profundidad, hojas mínimas, bootstrap/submuestreo, pesos y demás complejidad se ajustarán solo en inner spatial CV. OOB sirve como diagnóstico de convergencia, no como sustituto del outer spatial test.

En presencia-background o PU, el score de RF no se presentará como probabilidad absoluta de depósito salvo que se justifiquen muestreo y calibración. `sample_weight` y `class_weight` no corregirán dos veces el mismo diseño. Los Modelos A y B tendrán el mismo espacio y presupuesto de tuning, aunque cada uno pueda seleccionar hiperparámetros distintos dentro de él.

Interpretabilidad predefinida:

1. permutation importance agrupada por familia, calculada exclusivamente en observaciones outer-test y mediante permutaciones espacialmente coherentes;
2. estabilidad entre folds, dominios y diseños de background, más ablación `drop-group` cuando haya fuerte correlación;
3. importancia Gini/MDI solo como diagnóstico interno, nunca como evidencia confirmatoria;
4. TreeSHAP posteriormente, con cada celda explicada por un modelo que no la entrenó, background del explainer tomado de outer-training y variables one-hot/correlacionadas agrupadas;
5. ninguna importancia o SHAP se interpretará causalmente ni se reutilizará para seleccionar variables y volver a reportar el mismo outer test.

## 6. Señal romana derivada

La señal romana candidata no debe construirse después de mirar `Y_moderna`. Se predefinen dos estimandos distintos:

1. **Transferencia, confirmatorio:** para una celda outer-test, `RomanSignal` utiliza solo minas romanas de outer-training y excluye el buffer. Pregunta si la evidencia histórica generaliza a dominios donde no se permite consultar observaciones romanas locales.
2. **Operativo, sensibilidad:** usa todo OxREP congelado antes de abrir `Y_moderna`, como covariable disponible en despliegue. Solo es interpretable si un análisis de lineage descarta que OxREP haya heredado sus posiciones del mismo inventario moderno usado como Y.

Para el estimando confirmatorio, la señal se calcula **dentro de cada fold**. Alternativas preespecificadas:

1. Distancia a la mina romana de entrenamiento más próxima, truncada y transformada.
2. Densidad/kernel de minas romanas de entrenamiento a varios anchos, definidos antes de evaluar.
3. Distancias/densidades por commodity romana, con regularización de clases escasas.
4. Probabilidad/score `Y_roman ~ X` generado con predicción *out-of-fold* y transferido al experimento moderno.
5. Resumen probabilístico que integre `coordinateAccuracy`, en lugar de tratar todos los puntos como exactos.

Si se aprende `Y_roman ~ X`, se requiere doble cross-fitting: score out-of-fold dentro del outer-training mediante inner folds y predicción del outer-test con el modelo romano ajustado fuera de ese bloque. Como ese score es parcialmente una transformación de X, distancia/KDE fold-aware desde el patrón romano será la señal confirmatoria primaria. No se usarán simultáneamente decenas de variantes sin corrección/preespecificación: convertiría el experimento A/B en búsqueda oportunista.

## 7. Target leakage y variables inadmisibles

### Leakage directo

- Distancia o densidad a la misma ocurrencia moderna usada como target.
- Un mapa de favorabilidad, metalogenia prospectiva o “potencial” construido usando esos labels.
- Campos de OxREP como `mineID`, nombre del sitio, referencias, `description`, `notes`, IDs bibliográficos, región/distrito nominal o commodity romana cuando el objetivo sea probar una señal espacial romana controlada; estos son provenance/labels, no geología.
- Inventarios de labores modernas que duplican las ocurrencias target.
- La capa de indicios mineros `MPMIN`, símbolos de mina de MAGNA/GEODE o capas metalogenéticas construidas a partir del inventario que define `Y_moderna`.

### Leakage espacial o de folds

- Calcular interpolaciones, normalización, imputación, selección de variables, kernel romano, densidad de positivos o tuning con todo el territorio antes de separar folds.
- Colocar puntos del mismo complejo/distrito o duplicados probables en train y test.
- Seleccionar background junto al positivo de test usando información del test.
- Usar todos los puntos romanos en el estimando de transferencia o seleccionar variables con permutation importance/SHAP del mismo outer-test que se reportará como evaluación.

### Confusión que debe medirse

- OxREP puede haber heredado localizaciones de cartografía minera moderna; la aparente señal romana podría reflejar historia de investigación.
- La proximidad a vías, agua, relieve y afloramiento controla explotación/preservación/detección romana.
- La cobertura de IGME y de campañas geofísicas/geoquímicas no es uniforme.
- Una campaña seleccionada alrededor de depósitos conocidos puede codificar esfuerzo de búsqueda; su huella y densidad deben acompañar a los valores.

## 8. Estrategia de modelado por fases

1. Integrar y auditar X; construir máscara común de cobertura.
2. Integrar labels modernos y resolver duplicados/familias espaciales sin borrar trazabilidad.
3. Verificar evaluabilidad por grupos positivos en cada outer fold antes de escoger algoritmo; RF no se fuerza en endpoints escasos.
4. Baseline transparente y RF como baseline no lineal principal cuando proceda; comparar métodos adicionales con el mismo protocolo, no por reputación.
5. Calibrar transformaciones e hiperparámetros solo en inner spatial CV; mantener el outer test cerrado.
6. Generar señal romana estrictamente fold-aware para el estimando confirmatorio.
7. Ejecutar comparación pareada A/B con exactamente las mismas filas, folds, background y tuning budget.
8. Calcular interpretabilidad únicamente después de congelar predicciones/métricas confirmatorias.
9. Analizar estabilidad por región, commodity, tipo de depósito, calidad del label y resolución; reservar una fuente/dominio independiente si existe.

## 9. Afirmaciones permitidas en esta fase

El Excel respalda que existe una base positiva amplia y multimetálica de minería romana, pero no demuestra que esa señal prediga mineralización moderna. Tampoco permite identificar nuevas áreas favorables sin X oficial, labels modernos y evaluación espacial. La contribución incremental romana solo podrá afirmarse si el Modelo B mejora de forma estable y fuera de muestra al Modelo A bajo el experimento predefinido.

El AUC 0,999, Kappa 0,92 y OA 0,96 publicados para RF pertenecen a 46 ocurrencias de Au epitermal y 57 localizaciones de contraste de Rodalquilar. No son una expectativa de rendimiento nacional. Los propios autores advierten que la superioridad del algoritmo no se generaliza automáticamente a otros datasets.
