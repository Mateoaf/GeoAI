# Qué significa cada variable de Grid Master Au y qué puede aportar a la predicción

Informe del 25 de septiembre de 2026. Proyecto GeoAI. Ámbito: componente continental principal de la España peninsular, según la máscara regional candidata del proyecto. Ejecución examinada: `reports/fase_d/20260923T211448_267684Z`.

## 1. Resultado principal y alcance del análisis

**Grid Master Au contiene 245 columnas y 496.855 filas, una por celda terrestre de 1 × 1 km. De esas columnas, 168 son predictoras candidatas, 73 son auxiliares, 3 son etiquetas y 1 es la clave de celda. Actualmente hay 0 predictores aprobados para entrenamiento validado.**

El primer listado proporcionado coincide, en nombre y orden, con `Grid_Master_Au.parquet`. El segundo coincide con `X_features.parquet`: incluye `cell_id` y las 168 candidatas. Por tanto, las 169 columnas del segundo listado no son 169 predictores; `cell_id` solo identifica y enlaza las filas.

La palabra **predictora** tiene aquí dos sentidos que conviene separar. Una variable candidata representa una observación que podría ayudar a anticipar mineralización: por ejemplo, cercanía a estructuras que pudieron conducir fluidos. Una variable con capacidad predictiva demostrada mejora la predicción en territorios independientes, con etiquetas apropiadas y controles de sesgo. Este informe acredita el significado y la construcción de las candidatas; no demuestra esa segunda condición.

La ejecución registra 789 indicios candidatos asignados a 691 celdas y **0 celdas con positivos revisados**. `approved_training_columns` está vacío, `prediction_allowed` es falso y el cierre científico de D es falso. No se han entrenado nuevos modelos ni calculado importancias o correlaciones con candidatos sin revisar: no serían prueba suficiente de utilidad científica. Los datos permiten estudiar prospectividad regional, pero no estimar directamente ley de Au, tonelaje, reservas ni rentabilidad.

Se han leído el Parquet real, los diccionarios, las reglas de construcción y la configuración congelada. Se han recalculado los nulos y valores distintos de cada columna; para las 168 candidatas coinciden con `variables_qc.csv`. El código `features_source.py` guardado en D coincide por SHA-256 con `src/geoau/features.py` en el momento del análisis. Se priorizan estos productos frente a documentación anterior que describe otra estructura del maestro.

| Familia | Rol | Columnas |
|---|---|---|
| Identificación y soporte territorial | auxiliar_no_predictor | 9 |
| Identificación y soporte territorial | clave | 1 |
| Calidad geológica | auxiliar_no_predictor | 6 |
| Calidad de trazas | auxiliar_no_predictor | 7 |
| Soporte de vecindario | auxiliar_no_predictor | 6 |
| Calidad de levantamiento | auxiliar_no_predictor | 2 |
| Calidad geoquímica | auxiliar_no_predictor | 9 |
| Calidad de relieve | auxiliar_no_predictor | 6 |
| Cobertura heredada de C | auxiliar_no_predictor | 15 |
| Estado de validación | auxiliar_no_predictor | 2 |
| Capas adicionales: presencia | auxiliar_no_predictor | 6 |
| Capas adicionales: huella | auxiliar_no_predictor | 2 |
| Elegibilidad técnica | auxiliar_no_predictor | 3 |
| Litología | predictor_candidato | 20 |
| Edades | predictor_candidato | 29 |
| Estructuras | predictor_candidato | 24 |
| Geoquímica | predictor_candidato | 79 |
| Relieve | predictor_candidato | 6 |
| Hidrografía | predictor_candidato | 4 |
| Asociaciones litológicas | predictor_candidato | 6 |
| Etiquetas | etiqueta | 3 |

## 2. Cómo leer los números correctamente

Las coordenadas están en **ETRS89 / UTM zona 30N, EPSG:25830**, en metros; no son longitud y latitud. La fila aumenta hacia el sur y la columna hacia el este. Aunque la celda sea un cuadrado de un kilómetro, su superficie terrestre puede ser menor junto a la costa o los límites de la máscara.

Hay tres denominadores diferentes. En litología y edades, la fracción es área de una unidad dividida por área terrestre total de la celda. En geoquímica, la proporción de una clase usa solo el área válida del elemento. En indicadores de calidad, la fracción compara área válida o cubierta con el soporte correspondiente. No deben intercambiarse.

Ejemplo ilustrativo: una celda con 800.000 m² terrestres y 400.000 m² de una unidad litológica tiene fracción 0,50 de esa unidad. Si dispone de 780.000 m² geoquímicos válidos, su soporte geoquímico es 0,975. Si 195.000 m² válidos pertenecen a una clase, su proporción de clase es 0,25. Esa proporción no significa 25 % de metal, ni 25 % de probabilidad de encontrarlo.

**Cero y NaN no significan lo mismo.** Cero en una fracción geológica válida indica que esa unidad no aparece en la celda. Cero como código de clase geoquímica es una categoría real. Cero en densidad indica ausencia de longitud registrada por el procedimiento. NaN señala falta de valor utilizable: en distancias, también aparece cuando no hay traza registrada dentro de 10 km. No se sustituye automáticamente por cero ni por 10.000 m.

Los códigos `u000`, `u001`, etc. se asignan a descripciones ordenadas alfabéticamente en cada diccionario. No ordenan antigüedad, dureza, contenido metálico ni favorabilidad. `litologia_u017` y `edades_u024` corresponden a `SIN_ATRIBUTO` y por eso no aparecen como fracciones predictoras: no son omisiones accidentales. La grafía «cuarictas» de `litologia_u016` se conserva porque así figura en la leyenda local.

## 3. Fundamento de las familias predictoras

Las interpretaciones siguientes son **hipótesis geológicas para contrastar en este proyecto**, no conclusiones ya verificadas para cada celda ni un ranking de variables. Un predictor puede ayudar a delimitar un contexto desfavorable o distinguir dominios, aunque no aumente la prospectividad cuando aumenta su valor.

### Litología y edades: encajante e historia geológica

Las 20 variables litológicas incluyen una unidad dominante y 19 fracciones; las 29 de edades incluyen una dominante y 28 fracciones. El tipo de roca puede aproximar propiedades del encajante que condicionan circulación de fluidos, fracturación, reactividad y preservación. Las edades delimitan dominios e historia geológica. Su utilidad esperable es principalmente **contextual y en interacción** con estructuras y geoquímica.

Una fracción de una unidad mixta no descompone sus componentes. Por ejemplo, 0,60 de «Migmatitas, mármoles y granitoides indiferenciados» no significa 60 % de granito. Tampoco la edad cartografiada de una roca equivale a la edad de la mineralización. No hay una regla general «más antiguo = más oro» o «más granito = más oro».

Las intersecciones se calculan exactamente, disolviendo geometrías por categoría. D exige cobertura atribuida de al menos 95 % y un solape entre categorías inferior o igual al máximo de 1 m² y una millonésima del área terrestre. Si falla la condición, conserva los indicadores de calidad y deja las variables geológicas como NaN. La dominante retiene solo la categoría de mayor área; las fracciones preservan mezclas. Son representaciones relacionadas que conviene comparar.

### Estructuras: posibles conductos y contactos

Hay 24 candidatas: distancia y tres densidades para cada una de seis clases. Estas separan fallas/cizallas, cabalgamientos y contactos intrusivos, distinguiendo trazas cartografiadas de supuestas. La clasificación procede de reglas sobre `DESC_LINE` de `contactos_geode`; no integra por defecto todas las estructuras de todas las fuentes.

La justificación general es que ciertas estructuras pueden facilitar el movimiento de fluidos y crear lugares de depósito. La asociación de Au orogénico con sistemas de fallas no implica que todas las fallas sean favorables: importan jerarquía, geometría, condiciones del encajante y cronología. [USGS: sistemas minerales de oro orogénico](https://pubs.usgs.gov/publication/dr1198/full).

La distancia aproxima cercanía a una traza desde el centro de la celda, con búsqueda limitada a 10 km. Las densidades expresan longitud por superficie terrestre en radios de 1, 5 y 10 km; aportan contexto local, intermedio y regional. Son escalas elegidas por el proyecto, no radios universales de influencia metalogenética. Se usan longitudes exactas por celda, pero una distribución uniforme dentro de cada celda para aproximar ventanas circulares. No se miden intersecciones, conectividad, orientación ni actividad durante la mineralización.

Una distancia corta puede ser compatible con una hipótesis favorable, pero su signo y su efecto deben aprenderse y verificarse. Un cero de densidad no acredita ausencia de estructuras: la cobertura de levantamiento no está validada. Las trazas supuestas añaden incertidumbre interpretativa.

### Geoquímica: señal del elemento y elementos guía

Hay 79 candidatas: 9 clases modales y 70 proporciones. Au y W tienen siete clases locales; As, Sb, Bi, Hg, Cu, Pb y Zn tienen ocho. La moda resume la clase que ocupa más área válida. Las proporciones conservan la mezcla y pueden revelar una clase minoritaria que la moda oculta, aunque siguen limitadas por el mapa fuente y la resolución nativa de 500 m.

Au aporta una señal del propio elemento; As y Sb permiten probar asociaciones hidrotermales; Bi y W pueden contextualizar ciertos sistemas vinculados a intrusiones. Estas asociaciones dependen del modelo de depósito. Su presencia conjunta no garantiza mineralización y no exige correlación directa entre concentraciones. [USGS: prospectividad de Au en roca y asociaciones geoquímicas](https://pubs.usgs.gov/of/2021/1041/ofr20211041_v1.1.pdf).

Hg, Cu, Pb y Zn pueden añadir contexto de algunos sistemas epitermales o polimetálicos, pero no son marcadores universales de oro. Se deben interpretar con litología, estructuras y posibles aportes ajenos al proceso mineralizante. [USGS: modelos descriptivos de depósitos epitermales Au-Ag](https://www.usgs.gov/publications/descriptive-models-epithermal-gold-silver-deposits).

**Estas columnas contienen clases recuperadas de imágenes cartográficas, no ensayos analíticos individuales.** D contrasta los colores con una paleta local: distancia RGB máxima de 2 y margen mínimo de 10 frente a la segunda clase más próxima. Exige al menos 95 % de área terrestre aceptada para conservar el agregado. Esto controla correspondencia de colores; no valida la leyenda ni convierte clases en concentraciones.

El servicio oficial de Au diferencia sedimentos y suelos, y extracción total y parcial. Por tanto, medio y procedimiento analítico forman parte de la interpretación, además de las unidades. En D sigue pendiente acreditar la correspondencia de los archivos locales con la leyenda oficial. [IGME: servicio del Atlas Geoquímico de Au](https://mapas.igme.es/gis/rest/services/AtlasGeoquimico/IGME_MapaIsovalores2012_Au/MapServer).

Una clase mayor corresponde a un intervalo mayor en la leyenda local, pero los códigos no tienen distancias físicas iguales. No se debe promediar códigos como si fueran concentraciones ni afirmar que la clase 6 contiene el doble que la 3. El entrenamiento actual trata las clases modales como categóricas mediante codificación de categorías. Las proporciones suman uno entre clases cuando hay datos válidos: en modelos lineales con intercepto hay que resolver la dependencia mediante una representación adecuada o regularización.

Usar `au_clase_modal` no es automáticamente fuga de información: puede ser evidencia independiente disponible en el territorio. Sí lo sería derivarla del objetivo que se intenta predecir o usar información posterior al escenario de predicción. También conviene controlar señal asociada a explotación previa y comparar modelos con y sin Au. No deben confundirse las etiquetas de indicios con las clases geoquímicas de Au.

### Relieve e hidrografía: transporte, erosión y posición del terreno

Las seis variables de relieve describen elevación, pendiente, posición topográfica relativa y variabilidad del relieve. El TPI es elevación menos la media del entorno: negativo indica posición baja relativa; positivo, alta. La desviación estándar de elevación mide contraste topográfico, no incertidumbre del MDT. Los radios son de 1 y 5 km. Las derivadas se calculan a 500 m y se promedian a 1 km; esto no resuelve pequeñas terrazas, filones o trampas fluviales.

Las cuatro variables hidrográficas miden distancia a cauce y densidades en radios de 1, 5 y 10 km. Para Au aluvial su interés es contextualizar liberación, transporte y concentración del oro. Un placer requiere una fuente y mecanismos de concentración; estar cerca de cualquier río es insuficiente. [USGS: oro en depósitos de placer](https://www.usgs.gov/publications/gold-placer-deposits).

Como hipótesis de trabajo, la combinación de sedimentos detríticos, posición de valle y conexión con una fuente favorable puede aportar más que la distancia al cauce aislada. La tabla actual no representa explícitamente cuencas aportantes, posición aguas arriba, caudal, terrazas específicas ni trampas sedimentarias. Para Au en roca, relieve y cauces pueden captar exposición y sesgo de observación tanto como mineralización; hay que comprobar su contribución por separado.

## 4. Columnas que deben quedar fuera de X

**Identificadores y coordenadas:** se usan para enlaces, mapas y particiones espaciales. Pueden ayudar a memorizar distritos conocidos, pero el diseño actual no los autoriza como evidencia geológica transferible.

**Calidad, soporte y elegibilidad:** describen dónde y con qué soporte existe información. Permiten decidir qué celdas comparar y explicar por qué faltan datos. Su capacidad aparente para separar candidatos puede proceder del patrón de campañas y cartografía. Se mantienen fuera de X según `column_roles.csv` y la lista explícita de candidatas.

**Presencia de entidades y huellas de capas adicionales:** que exista una entidad de gravimetría en una celda no equivale a una anomalía gravimétrica; lo mismo vale para magnetometría, radiometría, magnetotelúrica, buzamientos y petrofísica. Los indicadores solo acreditan presencia local de registros o símbolos. Las huellas de Cuaternario y zonas GEODE tampoco codifican sus propiedades geológicas específicas.

**Etiquetas y recuentos de indicios:** `n_candidatos`, `n_positivos_revisados` y `estado_etiqueta` describen la respuesta o su proceso de revisión. Introducirlos como predictores produciría fuga de información. `U` significa no etiquetado: no acredita ausencia de oro. Varios registros en una celda no son necesariamente varios depósitos independientes.

**Particiones:** `partition_id = row // 100` organiza archivos; no es un conjunto de entrenamiento o prueba. `diagnostic_block` agrupa diagnóstico en bloques de 50 km; tampoco garantiza por sí solo independencia de la evaluación.

## 5. Hallazgos concretos en los valores actuales

**Dos candidatas no aportan variación de valor:** `zn_proporcion_clase_3` y `w_proporcion_clase_2` son cero en todas sus celdas válidas. Siguen presentes en la lista candidata, pero no pueden discriminar por valor. Sus NaN podrían transportar información de cobertura en algoritmos que la aprovechen; eso no es evidencia metalogenética. La causa concreta exige revisar la paleta y el rechazo RGB, no declarar ausencia del elemento. En las modas se observan siete clases de Zn y seis de W, respectivamente.

**La geoquímica ampliada reduce mucho el soporte:** Zn tiene 28,89 % de nulos y W 17,15 %, frente a 1,76 % en Au, As, Bi, Hg y Cu, 2,01 % en Pb y 2,09 % en Sb. La litología y las edades tienen 3,10 % de nulos. Las cifras de nulos por variable no equivalen a la intersección de celdas completas para un modelo.

| Criterio | Celdas | % del maestro | Registros candidatos |
|---|---|---|---|
| eligible_geology_terrain | 478,443 | 96.29 % | 756 |
| eligible_geo4 | 472,548 | 95.11 % | 755 |
| eligible_geo9 | 288,822 | 58.13 % | 525 |

Pasar de `eligible_geo4` a `eligible_geo9` reduce el universo de 472.548 a 288.822 celdas: se pierden 183.726, un 38,88 % del soporte de geo4. Los registros candidatos cubiertos pasan de 755 a 525. Una comparación de rendimiento entre ambos conjuntos confundiría cambio de variables con cambio de territorio si no se realiza además sobre soporte común. Estas banderas no exigen que todas las distancias estructurales o todas las derivadas de relieve estén completas.

**Las distancias tienen nulos con una interpretación específica:** falla cartografiada 18,90 %, falla supuesta 30,21 %, cabalgamiento cartografiado 55,69 %, supuesto 80,06 %, contacto intrusivo cartografiado 69,96 % y supuesto 98,00 %. Cauces: 2,72 %. No encontrar traza dentro de 10 km es parte de la definición del NaN, junto con la limitación de cobertura. La distancia a contacto intrusivo supuesto tiene muy poco soporte observado; requiere especial cautela antes de imputar y atribuir significado.

**Las asociaciones litológicas no añaden mediciones nuevas.** Se verificaron fila a fila las siguientes identidades, incluidos los nulos. Cinco son duplicados exactos de una sola fracción; la de granitoides explícitos es una suma determinista.

| Variable derivada | Identidad comprobada |
|---|---|
| unidades_granitoides_explicitos_fraccion | litologia_u011_fraccion + litologia_u015_fraccion |
| unidades_mixtas_con_granitoides_fraccion | litologia_u014_fraccion |
| unidades_volcanicas_fraccion | litologia_u019_fraccion |
| unidades_basicas_ultrabasicas_fraccion | litologia_u018_fraccion |
| unidades_con_gneisses_fraccion | litologia_u010_fraccion |
| unidades_con_gravas_arenas_limos_fraccion | litologia_u012_fraccion |

También se ha comprobado igualdad exacta, incluidos los nulos, entre `edades_u004_fraccion` (CUATERNARIO) y `litologia_u012_fraccion` (Gravas, conglomerados, arenas y limos).

Esto puede repartir artificialmente la importancia entre variables equivalentes o dar más oportunidades de selección a una misma señal. No se deben interpretar como fuentes independientes de evidencia. Dominantes, fracciones, sumas y radios vecinos también pueden estar relacionados, aunque no sean idénticos.

## 6. Cómo demostrar cuáles ayudan a predecir

1. Definir el objetivo: presencia de mineralización en roca, depósitos aluviales o un objetivo general bien delimitado. La utilidad y la interpretación de las mismas columnas cambian entre estos casos.
2. Revisar etiquetas y agrupar registros del mismo depósito/distrito. Plantear explícitamente positivos frente a no etiquetados cuando no existan negativos fiables; no convertir U en ausencia confirmada.
3. Validar semántica y soporte: leyendas geoquímicas, medio/unidades, categorías estructurales, representatividad de la máscara y disponibilidad real para el territorio donde se aplicará el modelo.
4. Seleccionar X mediante la lista de candidatas y resolver duplicados/constantes. Comparar dominante frente a fracciones y moda geoquímica frente a proporciones; no introducir todo automáticamente. Separar variables admitidas en exploración de variables aprobadas para entrenamiento validado.
5. Evaluar con bloques y grupos espaciales que eviten repartir el mismo depósito o vecinos muy dependientes entre ajuste y prueba. Diseñar separaciones compatibles con autocorrelación y ventanas de hasta 10 km; las franjas de almacenamiento no cumplen esta función automáticamente.
6. Ajustar imputación, codificación, escalado y selección únicamente dentro de cada entrenamiento. El tratamiento de una distancia censurada por búsqueda merece un análisis específico; imputarla por la mediana sin más mezcla falta de observación con proximidad.
7. Comparar familias sobre celdas comunes: geología; añadir estructuras; añadir relieve; añadir As/Sb/Bi; añadir Au; añadir hidrografía; y contrastar los nueve elementos. Estas son comparaciones propuestas, no resultados calculados ni cambios efectuados en el proyecto.
8. Medir recuperación de positivos independientes al prospectar una fracción fija del territorio y, cuando las etiquetas lo permitan, métricas de precisión/recobrado. Con positivos y no etiquetados, precisión, falsos positivos y calibración requieren supuestos adicionales; no deben presentarse como probabilidades verificadas de yacimiento.
9. Examinar ablación por familia y permutación agrupada en datos espaciales de prueba. La correlación entre columnas puede repartir u ocultar importancia. Exigir estabilidad entre regiones y semillas, y estimar incertidumbre por bloques. SHAP o una importancia de bosque explican un modelo, no prueban causalidad.

Una variable será defendible cuando su significado sea correcto, esté disponible en el escenario de uso y aporte una mejora repetible fuera de las áreas con las que se ajustó el modelo. No basta con que tenga un mecanismo plausible, correlacione con indicios o aparezca en `X_features`.

## 7. Leyendas geoquímicas locales, clase por clase

La tabla siguiente reproduce las etiquetas de `geoquimica_leyendas_locales.csv`. **Los rangos conservan su texto local y no se les asignan ppm, ppb u otra unidad no validada.** Las categorías se reconstruyen por colores; esta tabla no autoriza reclasificar mediciones con sus límites, algunos redondeados o coincidentes. En las fichas individuales se especifica qué clase representa cada proporción.

| Elemento | Clase | Etiqueta local (unidades no validadas) |
|---|---|---|
| Au | 0 | 0,08 - 1,34 |
| Au | 1 | 1,35 - 2 |
| Au | 2 | 2,01 - 3,5 |
| Au | 3 | 3,51 - 6,1 |
| Au | 4 | 6,11 - 12,05 |
| Au | 5 | 12,06 - 43 |
| Au | 6 | 43,01 - 1.964 |
| As | 0 | 0,08 - 4,55 |
| As | 1 | 4,56 - 6 |
| As | 2 | 6,01 - 8,78 |
| As | 3 | 8,79 - 12,67 |
| As | 4 | 12,68 - 16,16 |
| As | 5 | 16,17 - 19,9 |
| As | 6 | 19,91 - 45 |
| As | 7 | 45,01 - 1.949,5 |
| Sb | 0 | 0,043 - 0,228 |
| Sb | 1 | 0,228 - 0,61 |
| Sb | 2 | 0,61 - 0,78 |
| Sb | 3 | 0,78 - 1,19 |
| Sb | 4 | 1,19 - 1,96 |
| Sb | 5 | 1,96 - 3,16 |
| Sb | 6 | 3,16 - 6,3 |
| Sb | 7 | 6,3 - 343,14 |
| Bi | 0 | 0,08 - 0,09 |
| Bi | 1 | 0,1 - 0,14 |
| Bi | 2 | 0,15 - 0,18 |
| Bi | 3 | 0,19 - 0,25 |
| Bi | 4 | 0,26 - 0,32 |
| Bi | 5 | 0,33 - 0,42 |
| Bi | 6 | 0,43 - 0,68 |
| Bi | 7 | 0,69 - 63,86 |
| Hg | 0 | 0,28 - 6 |
| Hg | 1 | 6,01 - 11,38 |
| Hg | 2 | 11,39 - 15,67 |
| Hg | 3 | 15,68 - 23,95 |
| Hg | 4 | 23,96 - 37,23 |
| Hg | 5 | 37,24 - 47 |
| Hg | 6 | 47,01 - 150 |
| Hg | 7 | 150,01 - 76.203 |
| Cu | 0 | 0,42 - 6,28 |
| Cu | 1 | 6,29 - 10,35 |
| Cu | 2 | 10,36 - 12,73 |
| Cu | 3 | 12,74 - 16,43 |
| Cu | 4 | 16,44 - 22,51 |
| Cu | 5 | 22,52 - 28,25 |
| Cu | 6 | 28,26 - 50 |
| Cu | 7 | 50,01 - 2.038,62 |
| Pb | 0 | 0,28 - 10,43 |
| Pb | 1 | 10,44 - 14,25 |
| Pb | 2 | 14,26 - 17,16 |
| Pb | 3 | 17,17 - 22,51 |
| Pb | 4 | 22,52 - 29,75 |
| Pb | 5 | 29,76 - 35,12 |
| Pb | 6 | 35,13 - 65 |
| Pb | 7 | 65,01 - 4.979,11 |
| Zn | 0 | 0,53 - 21,12 |
| Zn | 1 | 21,13 - 31,74 |
| Zn | 2 | 31,75 - 41,08 |
| Zn | 3 | 41,09 - 56,62 |
| Zn | 4 | 56,63 - 73,79 |
| Zn | 5 | 73,8 - 90,5 |
| Zn | 6 | 90,51 - 157 |
| Zn | 7 | 157,01 - 21.638,97 |
| W | 0 | 0,5 - 0,53 |
| W | 1 | 0,54 - 0,68 |
| W | 2 | 0,69 - 0,84 |
| W | 3 | 0,85 - 1,32 |
| W | 4 | 1,33 - 2,27 |
| W | 5 | 2,28 - 6,5 |
| W | 6 | 6,51 - 473,61 |

## 8. Cómo utilizar el diccionario completo

Las fichas siguientes explican individualmente las 245 columnas. Cada ficha incluye significado, unidades, papel predictivo o razón de exclusión, limitaciones y estadísticas recalculadas sobre las 496.855 filas. Los valores distintos excluyen nulos. Los rangos son observados, no límites teóricos; para categorías se muestran los cuatro valores más frecuentes, que pueden incluir nulos.

Todas las fichas de candidatas describen **posible utilidad**, sin asignar importancia empírica demostrada ni signo obligatorio de efecto. El CSV `diccionario_245_variables.csv` permite filtrar y comparar estas mismas fichas en una hoja de cálculo. El HTML dispone de búsqueda y de impresión a PDF; todos sus contenidos funcionan sin conexión.

## Identificación y soporte territorial — diccionario completo

### `row`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Índice de fila desde 0; aumenta hacia el sur.

**Unidades:** índice.

**Por qué puede predecir o por qué se excluye:** No se propone como predictor geológico.

**Límites:** Permite reconstruir la rejilla; puede memorizar localización.

**Datos observados:** 0.00 % nulos; 872 valores distintos no nulos. Rango o valores más frecuentes: 0 … 871.

**Procedencia:** Fases C/D; código y configuración.

### `col`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Índice de columna desde 0; aumenta hacia el este.

**Unidades:** índice.

**Por qué puede predecir o por qué se excluye:** No se propone como predictor geológico.

**Límites:** Localiza la celda en la matriz; no representa un proceso geológico.

**Datos observados:** 0.00 % nulos; 1,035 valores distintos no nulos. Rango o valores más frecuentes: 36 … 1070.

**Procedencia:** Fases C/D; código y configuración.

### `cell_id`

**Rol y uso:** clave; Excluir de X.

**Qué significa:** Identificador único formado por versión de rejilla, fila y columna.

**Unidades:** texto.

**Por qué puede predecir o por qué se excluye:** No se propone como predictor geológico.

**Límites:** Clave de unión y trazabilidad; nunca una magnitud geológica.

**Datos observados:** 0.00 % nulos; 496,855 valores distintos no nulos. Rango o valores más frecuentes: es_pen_utm30_1km_v1_r0000_c0172: 1; es_pen_utm30_1km_v1_r0000_c0173: 1; es_pen_utm30_1km_v1_r0001_c0172: 1; es_pen_utm30_1km_v1_r0001_c0173: 1.

**Procedencia:** Fases C/D; código y configuración.

### `x_center`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Coordenada este del centro: -50000 + (col + 0,5) × 1000.

**Unidades:** m; EPSG:25830.

**Por qué puede predecir o por qué se excluye:** No se propone como predictor geológico.

**Límites:** Localización espacial; usar para mapas y evaluación espacial, no como predictor autorizado.

**Datos observados:** 0.00 % nulos; 1,035 valores distintos no nulos. Rango o valores más frecuentes: -13500.0 … 1020500.0.

**Procedencia:** Fases C/D; código y configuración.

### `y_center`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Coordenada norte del centro: 4860000 - (row + 0,5) × 1000.

**Unidades:** m; EPSG:25830.

**Por qué puede predecir o por qué se excluye:** No se propone como predictor geológico.

**Límites:** Localización espacial; no es latitud y puede codificar provincias de exploración.

**Datos observados:** 0.00 % nulos; 872 valores distintos no nulos. Rango o valores más frecuentes: 3988500.0 … 4859500.0.

**Procedencia:** Fases C/D; código y configuración.

### `land_area_m2`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Superficie terrestre de la celda según la máscara candidata.

**Unidades:** m².

**Por qué puede predecir o por qué se excluye:** No se propone como predictor geológico.

**Límites:** Denominador para agregaciones; mide soporte territorial.

**Datos observados:** 0.00 % nulos; 6,374 valores distintos no nulos. Rango o valores más frecuentes: 0.6185531052243661 … 1000000.0.

**Procedencia:** Fases C/D; código y configuración.

### `land_fraction`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** land_area_m2 / 1000000; fracción terrestre del cuadrado de 1 km.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** No se propone como predictor geológico.

**Límites:** Describe costa y bordes de la máscara, no fertilidad.

**Datos observados:** 0.00 % nulos; 6,374 valores distintos no nulos. Rango o valores más frecuentes: 6.185531052243661e-07 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `coastal_eligible`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Verdadero cuando land_fraction ≥ 0,5.

**Unidades:** booleano.

**Por qué puede predecir o por qué se excluye:** No se propone como predictor geológico.

**Límites:** Filtro de soporte mínimo costero; no una probabilidad de oro.

**Datos observados:** 0.00 % nulos; 2 valores distintos no nulos. Rango o valores más frecuentes: False … True.

**Procedencia:** Fases C/D; código y configuración.

### `diagnostic_block`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Bloque de diagnóstico de 50 × 50 km, construido con fila y columna.

**Unidades:** categoría espacial.

**Por qué puede predecir o por qué se excluye:** No se propone como predictor geológico.

**Límites:** Agrupa diagnósticos de cobertura; no es automáticamente un fold de validación.

**Datos observados:** 0.00 % nulos; 246 valores distintos no nulos. Rango o valores más frecuentes: b1_2: 2,500; b1_3: 2,500; b1_4: 2,500; b1_5: 2,500.

**Procedencia:** Fases C/D; código y configuración.

### `partition_id`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** División entera row // 100; organiza franjas de 100 filas en el Parquet particionado.

**Unidades:** entero.

**Por qué puede predecir o por qué se excluye:** No se propone como predictor geológico.

**Límites:** Partición de almacenamiento, sin significado metalogenético ni función de validación por sí misma.

**Datos observados:** 0.00 % nulos; 9 valores distintos no nulos. Rango o valores más frecuentes: 0 … 8.

**Procedencia:** Fases C/D; código y configuración.

## Calidad geológica — diccionario completo

### `litologia_cobertura`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Área de unión de polígonos de la familia / área terrestre de la celda.

**Unidades:** m²/m² terrestre.

**Por qué puede predecir o por qué se excluye:** Controla si la extracción es utilizable.

**Límites:** No interpreta litología ni edad; filtrar/auditar fuera de X. El exceso de solape no tiene garantizado el límite 1 en cualquier conjunto de datos.

**Datos observados:** 0.00 % nulos; 4,900 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0000000000000004.

**Procedencia:** Fases C/D; código y configuración.

### `litologia_solape_fraccion`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Exceso de suma de áreas de categorías sobre área de unión, dividido por área terrestre; detecta conflicto entre categorías.

**Unidades:** m²/m² terrestre.

**Por qué puede predecir o por qué se excluye:** Controla si la extracción es utilizable.

**Límites:** No interpreta litología ni edad; filtrar/auditar fuera de X. El exceso de solape no tiene garantizado el límite 1 en cualquier conjunto de datos.

**Datos observados:** 0.00 % nulos; 433 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 9.740918998714609e-12.

**Procedencia:** Fases C/D; código y configuración.

### `litologia_sin_atributo_fraccion`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Área de polígonos SIN_ATRIBUTO / área terrestre.

**Unidades:** m²/m² terrestre.

**Por qué puede predecir o por qué se excluye:** Controla si la extracción es utilizable.

**Límites:** No interpreta litología ni edad; filtrar/auditar fuera de X. El exceso de solape no tiene garantizado el límite 1 en cualquier conjunto de datos.

**Datos observados:** 0.00 % nulos; 12,726 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0000000000000002.

**Procedencia:** Fases C/D; código y configuración.

### `edades_cobertura`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Área de unión de polígonos de la familia / área terrestre de la celda.

**Unidades:** m²/m² terrestre.

**Por qué puede predecir o por qué se excluye:** Controla si la extracción es utilizable.

**Límites:** No interpreta litología ni edad; filtrar/auditar fuera de X. El exceso de solape no tiene garantizado el límite 1 en cualquier conjunto de datos.

**Datos observados:** 0.00 % nulos; 4,900 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0000000000000004.

**Procedencia:** Fases C/D; código y configuración.

### `edades_solape_fraccion`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Exceso de suma de áreas de categorías sobre área de unión, dividido por área terrestre; detecta conflicto entre categorías.

**Unidades:** m²/m² terrestre.

**Por qué puede predecir o por qué se excluye:** Controla si la extracción es utilizable.

**Límites:** No interpreta litología ni edad; filtrar/auditar fuera de X. El exceso de solape no tiene garantizado el límite 1 en cualquier conjunto de datos.

**Datos observados:** 0.00 % nulos; 435 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 9.740918998714609e-12.

**Procedencia:** Fases C/D; código y configuración.

### `edades_sin_atributo_fraccion`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Área de polígonos SIN_ATRIBUTO / área terrestre.

**Unidades:** m²/m² terrestre.

**Por qué puede predecir o por qué se excluye:** Controla si la extracción es utilizable.

**Límites:** No interpreta litología ni edad; filtrar/auditar fuera de X. El exceso de solape no tiene garantizado el límite 1 en cualquier conjunto de datos.

**Datos observados:** 0.00 % nulos; 12,726 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0000000000000002.

**Procedencia:** Fases C/D; código y configuración.

## Calidad de trazas — diccionario completo

### `falla_cartografiada_sin_traza_en_10000m`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Verdadero cuando no hay distancia finita a falla_cartografiada dentro de 10000 m.

**Unidades:** booleano.

**Por qué puede predecir o por qué se excluye:** Indicador de búsqueda sin resultado; ayuda a interpretar el NaN de distancia.

**Límites:** No demuestra ausencia de estructura/cauce ni que la zona haya sido levantada. Excluido de la lista de predictores.

**Datos observados:** 0.00 % nulos; 2 valores distintos no nulos. Rango o valores más frecuentes: False … True.

**Procedencia:** Fases C/D; código y configuración.

### `falla_supuesta_sin_traza_en_10000m`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Verdadero cuando no hay distancia finita a falla_supuesta dentro de 10000 m.

**Unidades:** booleano.

**Por qué puede predecir o por qué se excluye:** Indicador de búsqueda sin resultado; ayuda a interpretar el NaN de distancia.

**Límites:** No demuestra ausencia de estructura/cauce ni que la zona haya sido levantada. Excluido de la lista de predictores.

**Datos observados:** 0.00 % nulos; 2 valores distintos no nulos. Rango o valores más frecuentes: False … True.

**Procedencia:** Fases C/D; código y configuración.

### `cabalgamiento_cartografiada_sin_traza_en_10000m`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Verdadero cuando no hay distancia finita a cabalgamiento_cartografiada dentro de 10000 m.

**Unidades:** booleano.

**Por qué puede predecir o por qué se excluye:** Indicador de búsqueda sin resultado; ayuda a interpretar el NaN de distancia.

**Límites:** No demuestra ausencia de estructura/cauce ni que la zona haya sido levantada. Excluido de la lista de predictores.

**Datos observados:** 0.00 % nulos; 2 valores distintos no nulos. Rango o valores más frecuentes: False … True.

**Procedencia:** Fases C/D; código y configuración.

### `cabalgamiento_supuesta_sin_traza_en_10000m`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Verdadero cuando no hay distancia finita a cabalgamiento_supuesta dentro de 10000 m.

**Unidades:** booleano.

**Por qué puede predecir o por qué se excluye:** Indicador de búsqueda sin resultado; ayuda a interpretar el NaN de distancia.

**Límites:** No demuestra ausencia de estructura/cauce ni que la zona haya sido levantada. Excluido de la lista de predictores.

**Datos observados:** 0.00 % nulos; 2 valores distintos no nulos. Rango o valores más frecuentes: False … True.

**Procedencia:** Fases C/D; código y configuración.

### `contacto_intrusivo_cartografiada_sin_traza_en_10000m`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Verdadero cuando no hay distancia finita a contacto_intrusivo_cartografiada dentro de 10000 m.

**Unidades:** booleano.

**Por qué puede predecir o por qué se excluye:** Indicador de búsqueda sin resultado; ayuda a interpretar el NaN de distancia.

**Límites:** No demuestra ausencia de estructura/cauce ni que la zona haya sido levantada. Excluido de la lista de predictores.

**Datos observados:** 0.00 % nulos; 2 valores distintos no nulos. Rango o valores más frecuentes: False … True.

**Procedencia:** Fases C/D; código y configuración.

### `contacto_intrusivo_supuesta_sin_traza_en_10000m`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Verdadero cuando no hay distancia finita a contacto_intrusivo_supuesta dentro de 10000 m.

**Unidades:** booleano.

**Por qué puede predecir o por qué se excluye:** Indicador de búsqueda sin resultado; ayuda a interpretar el NaN de distancia.

**Límites:** No demuestra ausencia de estructura/cauce ni que la zona haya sido levantada. Excluido de la lista de predictores.

**Datos observados:** 0.00 % nulos; 2 valores distintos no nulos. Rango o valores más frecuentes: False … True.

**Procedencia:** Fases C/D; código y configuración.

### `cauce_sin_traza_en_10000m`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Verdadero cuando no hay distancia finita a cauce dentro de 10000 m.

**Unidades:** booleano.

**Por qué puede predecir o por qué se excluye:** Indicador de búsqueda sin resultado; ayuda a interpretar el NaN de distancia.

**Límites:** No demuestra ausencia de estructura/cauce ni que la zona haya sido levantada. Excluido de la lista de predictores.

**Datos observados:** 0.00 % nulos; 2 valores distintos no nulos. Rango o valores más frecuentes: False … True.

**Procedencia:** Fases C/D; código y configuración.

## Soporte de vecindario — diccionario completo

### `structural_soporte_terrestre_1000m`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Área terrestre ponderada de la ventana de radio 1000 m dividida por el área de la ventana discretizada usada en densidades.

**Unidades:** fracción ≈0–1.

**Por qué puede predecir o por qué se excluye:** Controla el denominador efectivo junto a costas y límites.

**Límites:** No mide porcentaje de estructuras/cauces observados ni cobertura de campaña; pequeñas desviaciones numéricas pueden deberse a la convolución.

**Datos observados:** 0.00 % nulos; 12,226 valores distintos no nulos. Rango o valores más frecuentes: 0.03639710891793203 … 1.000000000000001.

**Procedencia:** Fases C/D; código y configuración.

### `structural_soporte_terrestre_5000m`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Área terrestre ponderada de la ventana de radio 5000 m dividida por el área de la ventana discretizada usada en densidades.

**Unidades:** fracción ≈0–1.

**Por qué puede predecir o por qué se excluye:** Controla el denominador efectivo junto a costas y límites.

**Límites:** No mide porcentaje de estructuras/cauces observados ni cobertura de campaña; pequeñas desviaciones numéricas pueden deberse a la convolución.

**Datos observados:** 0.00 % nulos; 29,607 valores distintos no nulos. Rango o valores más frecuentes: 0.028286446680885126 … 1.000000000000001.

**Procedencia:** Fases C/D; código y configuración.

### `structural_soporte_terrestre_10000m`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Área terrestre ponderada de la ventana de radio 10000 m dividida por el área de la ventana discretizada usada en densidades.

**Unidades:** fracción ≈0–1.

**Por qué puede predecir o por qué se excluye:** Controla el denominador efectivo junto a costas y límites.

**Límites:** No mide porcentaje de estructuras/cauces observados ni cobertura de campaña; pequeñas desviaciones numéricas pueden deberse a la convolución.

**Datos observados:** 0.00 % nulos; 48,907 valores distintos no nulos. Rango o valores más frecuentes: 0.120610047196506 … 1.0000000000000009.

**Procedencia:** Fases C/D; código y configuración.

### `hydrology_soporte_terrestre_1000m`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Área terrestre ponderada de la ventana de radio 1000 m dividida por el área de la ventana discretizada usada en densidades.

**Unidades:** fracción ≈0–1.

**Por qué puede predecir o por qué se excluye:** Controla el denominador efectivo junto a costas y límites.

**Límites:** No mide porcentaje de estructuras/cauces observados ni cobertura de campaña; pequeñas desviaciones numéricas pueden deberse a la convolución.

**Datos observados:** 0.00 % nulos; 12,226 valores distintos no nulos. Rango o valores más frecuentes: 0.03639710891793203 … 1.000000000000001.

**Procedencia:** Fases C/D; código y configuración.

### `hydrology_soporte_terrestre_5000m`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Área terrestre ponderada de la ventana de radio 5000 m dividida por el área de la ventana discretizada usada en densidades.

**Unidades:** fracción ≈0–1.

**Por qué puede predecir o por qué se excluye:** Controla el denominador efectivo junto a costas y límites.

**Límites:** No mide porcentaje de estructuras/cauces observados ni cobertura de campaña; pequeñas desviaciones numéricas pueden deberse a la convolución.

**Datos observados:** 0.00 % nulos; 29,607 valores distintos no nulos. Rango o valores más frecuentes: 0.028286446680885126 … 1.000000000000001.

**Procedencia:** Fases C/D; código y configuración.

### `hydrology_soporte_terrestre_10000m`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Área terrestre ponderada de la ventana de radio 10000 m dividida por el área de la ventana discretizada usada en densidades.

**Unidades:** fracción ≈0–1.

**Por qué puede predecir o por qué se excluye:** Controla el denominador efectivo junto a costas y límites.

**Límites:** No mide porcentaje de estructuras/cauces observados ni cobertura de campaña; pequeñas desviaciones numéricas pueden deberse a la convolución.

**Datos observados:** 0.00 % nulos; 48,907 valores distintos no nulos. Rango o valores más frecuentes: 0.120610047196506 … 1.0000000000000009.

**Procedencia:** Fases C/D; código y configuración.

## Calidad de levantamiento — diccionario completo

### `structural_cobertura_levantamiento_acreditada`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Bandera de acreditación de cobertura del levantamiento estructural o hidrográfico; el código la fija en falso.

**Unidades:** booleano.

**Por qué puede predecir o por qué se excluye:** Control científico de disponibilidad, sin señal geológica.

**Límites:** Falso no significa territorio sin fallas/cauces. Es constante en esta ejecución.

**Datos observados:** 0.00 % nulos; 1 valores distintos no nulos. Rango o valores más frecuentes: False … False.

**Procedencia:** Fases C/D; código y configuración.

### `hydrology_cobertura_levantamiento_acreditada`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Bandera de acreditación de cobertura del levantamiento estructural o hidrográfico; el código la fija en falso.

**Unidades:** booleano.

**Por qué puede predecir o por qué se excluye:** Control científico de disponibilidad, sin señal geológica.

**Límites:** Falso no significa territorio sin fallas/cauces. Es constante en esta ejecución.

**Datos observados:** 0.00 % nulos; 1 valores distintos no nulos. Rango o valores más frecuentes: False … False.

**Procedencia:** Fases C/D; código y configuración.

## Calidad geoquímica — diccionario completo

### `geoquimica_au_valid_rgb`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción del área terrestre con clase y RGB aceptados para oro.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Determina si puede conservarse la variable geoquímica.

**Límites:** RGB compatible no prueba leyenda correcta. Tolerancia euclídea 2 y margen mínimo 10 frente al segundo color; umbral de área 0,95.

**Datos observados:** 0.00 % nulos; 1,847 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `geoquimica_as_valid_rgb`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción del área terrestre con clase y RGB aceptados para arsénico.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Determina si puede conservarse la variable geoquímica.

**Límites:** RGB compatible no prueba leyenda correcta. Tolerancia euclídea 2 y margen mínimo 10 frente al segundo color; umbral de área 0,95.

**Datos observados:** 0.00 % nulos; 1,847 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `geoquimica_sb_valid_rgb`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción del área terrestre con clase y RGB aceptados para antimonio.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Determina si puede conservarse la variable geoquímica.

**Límites:** RGB compatible no prueba leyenda correcta. Tolerancia euclídea 2 y margen mínimo 10 frente al segundo color; umbral de área 0,95.

**Datos observados:** 0.00 % nulos; 1,819 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `geoquimica_bi_valid_rgb`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción del área terrestre con clase y RGB aceptados para bismuto.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Determina si puede conservarse la variable geoquímica.

**Límites:** RGB compatible no prueba leyenda correcta. Tolerancia euclídea 2 y margen mínimo 10 frente al segundo color; umbral de área 0,95.

**Datos observados:** 0.00 % nulos; 1,847 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `geoquimica_hg_valid_rgb`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción del área terrestre con clase y RGB aceptados para mercurio.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Determina si puede conservarse la variable geoquímica.

**Límites:** RGB compatible no prueba leyenda correcta. Tolerancia euclídea 2 y margen mínimo 10 frente al segundo color; umbral de área 0,95.

**Datos observados:** 0.00 % nulos; 1,847 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `geoquimica_cu_valid_rgb`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción del área terrestre con clase y RGB aceptados para cobre.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Determina si puede conservarse la variable geoquímica.

**Límites:** RGB compatible no prueba leyenda correcta. Tolerancia euclídea 2 y margen mínimo 10 frente al segundo color; umbral de área 0,95.

**Datos observados:** 0.00 % nulos; 1,847 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `geoquimica_pb_valid_rgb`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción del área terrestre con clase y RGB aceptados para plomo.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Determina si puede conservarse la variable geoquímica.

**Límites:** RGB compatible no prueba leyenda correcta. Tolerancia euclídea 2 y margen mínimo 10 frente al segundo color; umbral de área 0,95.

**Datos observados:** 0.00 % nulos; 2,245 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `geoquimica_zn_valid_rgb`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción del área terrestre con clase y RGB aceptados para zinc.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Determina si puede conservarse la variable geoquímica.

**Límites:** RGB compatible no prueba leyenda correcta. Tolerancia euclídea 2 y margen mínimo 10 frente al segundo color; umbral de área 0,95.

**Datos observados:** 0.00 % nulos; 1,639 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `geoquimica_w_valid_rgb`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción del área terrestre con clase y RGB aceptados para wolframio.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Determina si puede conservarse la variable geoquímica.

**Límites:** RGB compatible no prueba leyenda correcta. Tolerancia euclídea 2 y margen mínimo 10 frente al segundo color; umbral de área 0,95.

**Datos observados:** 0.00 % nulos; 1,804 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

## Calidad de relieve — diccionario completo

### `elevacion_media_m_valid_fraction`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Área terrestre con valor finito de elevacion_media_m / área terrestre total de la celda.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Controla la aceptación del agregado de relieve.

**Límites:** No es relieve, pendiente ni rugosidad; exige ≥0,95 para conservar el predictor.

**Datos observados:** 0.00 % nulos; 1 valores distintos no nulos. Rango o valores más frecuentes: 1.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `pendiente_grados_valid_fraction`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Área terrestre con valor finito de pendiente_grados / área terrestre total de la celda.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Controla la aceptación del agregado de relieve.

**Límites:** No es relieve, pendiente ni rugosidad; exige ≥0,95 para conservar el predictor.

**Datos observados:** 0.00 % nulos; 3,118 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `tpi_1000m_m_valid_fraction`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Área terrestre con valor finito de tpi_1000m_m / área terrestre total de la celda.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Controla la aceptación del agregado de relieve.

**Límites:** No es relieve, pendiente ni rugosidad; exige ≥0,95 para conservar el predictor.

**Datos observados:** 0.00 % nulos; 1,952 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `desv_elevacion_1000m_m_valid_fraction`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Área terrestre con valor finito de desv_elevacion_1000m_m / área terrestre total de la celda.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Controla la aceptación del agregado de relieve.

**Límites:** No es relieve, pendiente ni rugosidad; exige ≥0,95 para conservar el predictor.

**Datos observados:** 0.00 % nulos; 1,952 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `tpi_5000m_m_valid_fraction`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Área terrestre con valor finito de tpi_5000m_m / área terrestre total de la celda.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Controla la aceptación del agregado de relieve.

**Límites:** No es relieve, pendiente ni rugosidad; exige ≥0,95 para conservar el predictor.

**Datos observados:** 0.00 % nulos; 12 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `desv_elevacion_5000m_m_valid_fraction`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Área terrestre con valor finito de desv_elevacion_5000m_m / área terrestre total de la celda.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Controla la aceptación del agregado de relieve.

**Límites:** No es relieve, pendiente ni rugosidad; exige ≥0,95 para conservar el predictor.

**Datos observados:** 0.00 % nulos; 12 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

## Cobertura heredada de C — diccionario completo

### `fase_c_valid_relieve`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción de soporte de relieve heredada de C: área terrestre con píxeles considerados válidos en la armonización de C.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Diagnóstico de cobertura previo a la extracción de predictores en D.

**Límites:** No es booleano pese a valid_. No incorpora todos los controles posteriores de D; en geoquímica no sustituye valid_rgb; en geología no sustituye intersecciones exactas y conflictos.

**Datos observados:** 0.00 % nulos; 1 valores distintos no nulos. Rango o valores más frecuentes: 1.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `fase_c_valid_geoquimica_au`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción de soporte de geoquimica_au heredada de C: área terrestre con píxeles considerados válidos en la armonización de C.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Diagnóstico de cobertura previo a la extracción de predictores en D.

**Límites:** No es booleano pese a valid_. No incorpora todos los controles posteriores de D; en geoquímica no sustituye valid_rgb; en geología no sustituye intersecciones exactas y conflictos.

**Datos observados:** 0.00 % nulos; 1,847 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `fase_c_valid_geoquimica_as`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción de soporte de geoquimica_as heredada de C: área terrestre con píxeles considerados válidos en la armonización de C.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Diagnóstico de cobertura previo a la extracción de predictores en D.

**Límites:** No es booleano pese a valid_. No incorpora todos los controles posteriores de D; en geoquímica no sustituye valid_rgb; en geología no sustituye intersecciones exactas y conflictos.

**Datos observados:** 0.00 % nulos; 1,847 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `fase_c_valid_geoquimica_sb`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción de soporte de geoquimica_sb heredada de C: área terrestre con píxeles considerados válidos en la armonización de C.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Diagnóstico de cobertura previo a la extracción de predictores en D.

**Límites:** No es booleano pese a valid_. No incorpora todos los controles posteriores de D; en geoquímica no sustituye valid_rgb; en geología no sustituye intersecciones exactas y conflictos.

**Datos observados:** 0.00 % nulos; 1,819 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `fase_c_valid_geoquimica_bi`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción de soporte de geoquimica_bi heredada de C: área terrestre con píxeles considerados válidos en la armonización de C.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Diagnóstico de cobertura previo a la extracción de predictores en D.

**Límites:** No es booleano pese a valid_. No incorpora todos los controles posteriores de D; en geoquímica no sustituye valid_rgb; en geología no sustituye intersecciones exactas y conflictos.

**Datos observados:** 0.00 % nulos; 1,847 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `fase_c_valid_geoquimica_hg`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción de soporte de geoquimica_hg heredada de C: área terrestre con píxeles considerados válidos en la armonización de C.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Diagnóstico de cobertura previo a la extracción de predictores en D.

**Límites:** No es booleano pese a valid_. No incorpora todos los controles posteriores de D; en geoquímica no sustituye valid_rgb; en geología no sustituye intersecciones exactas y conflictos.

**Datos observados:** 0.00 % nulos; 1,847 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `fase_c_valid_geoquimica_cu`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción de soporte de geoquimica_cu heredada de C: área terrestre con píxeles considerados válidos en la armonización de C.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Diagnóstico de cobertura previo a la extracción de predictores en D.

**Límites:** No es booleano pese a valid_. No incorpora todos los controles posteriores de D; en geoquímica no sustituye valid_rgb; en geología no sustituye intersecciones exactas y conflictos.

**Datos observados:** 0.00 % nulos; 1,847 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `fase_c_valid_geoquimica_pb`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción de soporte de geoquimica_pb heredada de C: área terrestre con píxeles considerados válidos en la armonización de C.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Diagnóstico de cobertura previo a la extracción de predictores en D.

**Límites:** No es booleano pese a valid_. No incorpora todos los controles posteriores de D; en geoquímica no sustituye valid_rgb; en geología no sustituye intersecciones exactas y conflictos.

**Datos observados:** 0.00 % nulos; 2,245 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `fase_c_valid_geoquimica_zn`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción de soporte de geoquimica_zn heredada de C: área terrestre con píxeles considerados válidos en la armonización de C.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Diagnóstico de cobertura previo a la extracción de predictores en D.

**Límites:** No es booleano pese a valid_. No incorpora todos los controles posteriores de D; en geoquímica no sustituye valid_rgb; en geología no sustituye intersecciones exactas y conflictos.

**Datos observados:** 0.00 % nulos; 1,847 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `fase_c_valid_geoquimica_w`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción de soporte de geoquimica_w heredada de C: área terrestre con píxeles considerados válidos en la armonización de C.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Diagnóstico de cobertura previo a la extracción de predictores en D.

**Límites:** No es booleano pese a valid_. No incorpora todos los controles posteriores de D; en geoquímica no sustituye valid_rgb; en geología no sustituye intersecciones exactas y conflictos.

**Datos observados:** 0.00 % nulos; 1,847 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `fase_c_valid_litologia`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción de soporte de litologia heredada de C: ocupación por polígonos estimada a 500 m y ponderada por tierra.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Diagnóstico de cobertura previo a la extracción de predictores en D.

**Límites:** No es booleano pese a valid_. No incorpora todos los controles posteriores de D; en geoquímica no sustituye valid_rgb; en geología no sustituye intersecciones exactas y conflictos.

**Datos observados:** 0.00 % nulos; 1,458 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `fase_c_valid_edades`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción de soporte de edades heredada de C: ocupación por polígonos estimada a 500 m y ponderada por tierra.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Diagnóstico de cobertura previo a la extracción de predictores en D.

**Límites:** No es booleano pese a valid_. No incorpora todos los controles posteriores de D; en geoquímica no sustituye valid_rgb; en geología no sustituye intersecciones exactas y conflictos.

**Datos observados:** 0.00 % nulos; 1,458 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `fase_c_valid_recintos`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción de soporte de recintos heredada de C: ocupación por polígonos estimada a 500 m y ponderada por tierra.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Diagnóstico de cobertura previo a la extracción de predictores en D.

**Límites:** No es booleano pese a valid_. No incorpora todos los controles posteriores de D; en geoquímica no sustituye valid_rgb; en geología no sustituye intersecciones exactas y conflictos.

**Datos observados:** 0.00 % nulos; 2,453 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `fase_c_coverage_code`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Código: 1 costera con tierra <50 %; 2 geología, relieve y los nueve elementos con soporte ≥95 %; 3 geología y relieve suficientes sin los nueve elementos completos; 4 soporte insuficiente.

**Unidades:** código 1–4.

**Por qué puede predecir o por qué se excluye:** Resume reglas de soporte para diagnóstico.

**Límites:** Categoría administrativa de cobertura, no orden de probabilidad de oro. La regla costera tiene prioridad; recintos no interviene en este código.

**Datos observados:** 0.00 % nulos; 4 valores distintos no nulos. Rango o valores más frecuentes: 1 … 4.

**Procedencia:** Fases C/D; código y configuración.

### `fase_c_coverage_decision`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Texto equivalente al código C: costera_baja_fraccion, soporte_basico_candidato, candidato_reducido_sin_geoquimica_completa o soporte_insuficiente.

**Unidades:** categoría.

**Por qué puede predecir o por qué se excluye:** Facilita interpretar decisiones de soporte.

**Límites:** Redundante con fase_c_coverage_code; excluir de X.

**Datos observados:** 0.00 % nulos; 4 valores distintos no nulos. Rango o valores más frecuentes: soporte_basico_candidato: 482,830; candidato_reducido_sin_geoquimica_completa: 8,053; costera_baja_fraccion: 3,221; soporte_insuficiente: 2,751.

**Procedencia:** Fases C/D; código y configuración.

## Estado de validación — diccionario completo

### `fase_c_prediction_allowed`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Bandera de permiso científico de predicción; heredada de C.

**Unidades:** booleano.

**Por qué puede predecir o por qué se excluye:** Expresa el estado del proceso de revisión.

**Límites:** No es probabilidad ni resultado del modelo. En la ejecución examinada todas las celdas tienen falso.

**Datos observados:** 0.00 % nulos; 1 valores distintos no nulos. Rango o valores más frecuentes: False … False.

**Procedencia:** Fases C/D; código y configuración.

### `prediction_allowed`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Bandera final de permiso científico de predicción de D, fijada en falso.

**Unidades:** booleano.

**Por qué puede predecir o por qué se excluye:** Expresa el estado del proceso de revisión.

**Límites:** No es probabilidad ni resultado del modelo. En la ejecución examinada todas las celdas tienen falso.

**Datos observados:** 0.00 % nulos; 1 valores distintos no nulos. Rango o valores más frecuentes: False … False.

**Procedencia:** Fases C/D; código y configuración.

## Capas adicionales: presencia — diccionario completo

### `fase_c_entity_present_magnetometriaradiometria`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Indica si hay alguna entidad de magnetometriaradiometria en la celda rasterizada; valores 0/1.

**Unidades:** indicador 0/1.

**Por qué puede predecir o por qué se excluye:** Inventario de disponibilidad, no propiedad física.

**Límites:** No mide campo magnético, radiactividad, resistividad, densidad, buzamiento ni petrofísica; no acredita cobertura total. Puede reproducir sesgo de campañas.

**Datos observados:** 0.00 % nulos; 2 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `fase_c_entity_present_magnetotelurico`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Indica si hay alguna entidad de magnetotelurico en la celda rasterizada; valores 0/1.

**Unidades:** indicador 0/1.

**Por qué puede predecir o por qué se excluye:** Inventario de disponibilidad, no propiedad física.

**Límites:** No mide campo magnético, radiactividad, resistividad, densidad, buzamiento ni petrofísica; no acredita cobertura total. Puede reproducir sesgo de campañas.

**Datos observados:** 0.00 % nulos; 2 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `fase_c_entity_present_medidasestructurales`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Indica si hay alguna entidad de medidasestructurales en la celda rasterizada; valores 0/1.

**Unidades:** indicador 0/1.

**Por qué puede predecir o por qué se excluye:** Inventario de disponibilidad, no propiedad física.

**Límites:** No mide campo magnético, radiactividad, resistividad, densidad, buzamiento ni petrofísica; no acredita cobertura total. Puede reproducir sesgo de campañas.

**Datos observados:** 0.00 % nulos; 2 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `fase_c_entity_present_petrofisica`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Indica si hay alguna entidad de petrofisica en la celda rasterizada; valores 0/1.

**Unidades:** indicador 0/1.

**Por qué puede predecir o por qué se excluye:** Inventario de disponibilidad, no propiedad física.

**Límites:** No mide campo magnético, radiactividad, resistividad, densidad, buzamiento ni petrofísica; no acredita cobertura total. Puede reproducir sesgo de campañas.

**Datos observados:** 0.00 % nulos; 2 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `fase_c_entity_present_buzamientos`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Indica si hay alguna entidad de buzamientos en la celda rasterizada; valores 0/1.

**Unidades:** indicador 0/1.

**Por qué puede predecir o por qué se excluye:** Inventario de disponibilidad, no propiedad física.

**Límites:** No mide campo magnético, radiactividad, resistividad, densidad, buzamiento ni petrofísica; no acredita cobertura total. Puede reproducir sesgo de campañas.

**Datos observados:** 0.00 % nulos; 2 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `fase_c_entity_present_gravimetria`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Indica si hay alguna entidad de gravimetria en la celda rasterizada; valores 0/1.

**Unidades:** indicador 0/1.

**Por qué puede predecir o por qué se excluye:** Inventario de disponibilidad, no propiedad física.

**Límites:** No mide campo magnético, radiactividad, resistividad, densidad, buzamiento ni petrofísica; no acredita cobertura total. Puede reproducir sesgo de campañas.

**Datos observados:** 0.00 % nulos; 2 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

## Capas adicionales: huella — diccionario completo

### `fase_c_footprint_cuaternariorecintos`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción estimada de área terrestre cubierta por polígonos de cuaternariorecintos, rasterizados a 500 m.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Diagnóstico espacial de huella de una capa.

**Límites:** No codifica la edad/tipología específica de depósitos cuaternarios ni la identidad de zona GEODE; no es cobertura acreditada de investigación.

**Datos observados:** 0.00 % nulos; 19 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

### `fase_c_footprint_zonasgeode`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** Fracción estimada de área terrestre cubierta por polígonos de zonasgeode, rasterizados a 500 m.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Diagnóstico espacial de huella de una capa.

**Límites:** No codifica la edad/tipología específica de depósitos cuaternarios ni la identidad de zona GEODE; no es cobertura acreditada de investigación.

**Datos observados:** 0.00 % nulos; 9 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** Fases C/D; código y configuración.

## Elegibilidad técnica — diccionario completo

### `eligible_geology_terrain`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** coastal_eligible y valores no nulos de litologia_dominante, edades_dominante, elevacion_media_m y pendiente_grados.

**Unidades:** booleano.

**Por qué puede predecir o por qué se excluye:** Selecciona celdas con soporte para un conjunto concreto.

**Límites:** No significa favorable para Au ni valida entrenamiento. No garantiza disponibilidad de TPI, desviaciones ni distancias estructurales.

**Datos observados:** 0.00 % nulos; 2 valores distintos no nulos. Rango o valores más frecuentes: False … True.

**Procedencia:** Fases C/D; código y configuración.

### `eligible_geo4`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** coastal_eligible y valores no nulos de litologia_dominante, edades_dominante, elevacion_media_m y pendiente_grados. Además, clases modales no nulas de Au, As, Sb y Bi.

**Unidades:** booleano.

**Por qué puede predecir o por qué se excluye:** Selecciona celdas con soporte para un conjunto concreto.

**Límites:** No significa favorable para Au ni valida entrenamiento. No garantiza disponibilidad de TPI, desviaciones ni distancias estructurales.

**Datos observados:** 0.00 % nulos; 2 valores distintos no nulos. Rango o valores más frecuentes: False … True.

**Procedencia:** Fases C/D; código y configuración.

### `eligible_geo9`

**Rol y uso:** auxiliar_no_predictor; Excluir de X.

**Qué significa:** coastal_eligible y valores no nulos de litologia_dominante, edades_dominante, elevacion_media_m y pendiente_grados. Además, clases modales no nulas de Au, As, Sb, Bi, Hg, Cu, Pb, Zn y W.

**Unidades:** booleano.

**Por qué puede predecir o por qué se excluye:** Selecciona celdas con soporte para un conjunto concreto.

**Límites:** No significa favorable para Au ni valida entrenamiento. No garantiza disponibilidad de TPI, desviaciones ni distancias estructurales.

**Datos observados:** 0.00 % nulos; 2 valores distintos no nulos. Rango o valores más frecuentes: False … True.

**Procedencia:** Fases C/D; código y configuración.

## Litología — diccionario completo

### `litologia_dominante`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Código de la unidad con mayor área terrestre; empate resuelto por orden textual de categoría.

**Unidades:** categoría nominal.

**Por qué puede predecir o por qué se excluye:** Resume el encajante y dominio geológico.

**Límites:** Los códigos uNNN no son rangos de favorabilidad ni edades numéricas. Pierde mezclas minoritarias; la edad de la roca no fecha la mineralización.

**Datos observados:** 3.10 % nulos; 19 valores distintos no nulos. Rango o valores más frecuentes: litologia_u000: 126,737; litologia_u012: 66,036; litologia_u008: 48,309; litologia_u009: 41,783.

**Procedencia:** litologia. Método registrado: mayor área terrestre; empate por texto ordenado.

### `litologia_u000_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «Areniscas, conglomerados, arcillas; calizas y evaporitas».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Describe una mezcla sedimentaria: permeabilidad y reactividad pueden condicionar circulación y precipitación; su amplitud impide asignarle favorabilidad fija.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 83,398 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `litologia_u001_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «Areniscas, pizarras y calizas».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Combina encajantes siliciclásticos y carbonatados; sus contrastes mecánicos y químicos pueden localizar mineralización si hay fluidos y estructuras apropiadas.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 14,614 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `litologia_u002_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «Calizas detríticas, calcarenitas, margas, arcillas y calizas».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Contexto sedimentario carbonatado y detrítico. Puede distinguir cuencas, cobertura y encajantes reactivos; señal principalmente contextual.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 10,245 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `litologia_u003_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «Calizas, dolomías y margas. Areniscas y conglomerados».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Carbonatos potencialmente reactivos junto con materiales detríticos; hipótesis de control del encajante, sin evidencia de alteración en esta variable.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 27,945 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `litologia_u004_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «Conglomerados, areniscas y lutitas».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Contexto detrítico con conglomerados. Puede señalar ambientes de transporte o encajantes, pero no identifica paleoplaceres auríferos por sí solo.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 697 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `litologia_u005_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «Conglomerados, areniscas, arcillas y calizas. Evaporitas».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Mezcla sedimentaria y evaporítica; diferencia dominios y cobertura. No hay una relación positiva universal con Au.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 20,316 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `litologia_u006_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «Conglomerados, areniscas, calizas, yesos y arcillas versicolores».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Unidad sedimentaria heterogénea con yesos; aporta contexto de cuenca y posibles contrastes de permeabilidad, no una señal aurífera directa.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 17,501 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `litologia_u007_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «Conglomerados, areniscas, pizarras y calizas. Carbón».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Encajantes detríticos y pizarrosos, carbonatos y carbón. Sugiere contrastes mecánicos y químicos, sin medir materia reductora ni sulfuros efectivamente presentes.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 7,947 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `litologia_u008_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «Cuarcitas, pizarras, areniscas y calizas».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Contrastes entre cuarcitas, pizarras y carbonatos pueden condicionar fracturación, circulación y reacción con fluidos; requiere estructuras favorables.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 29,400 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `litologia_u009_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «Dolomías, calizas y margas. Areniscas».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Carbonatos y materiales detríticos: contexto de encajante reactivo y permeabilidad; no basta para inferir un sistema mineralizado.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 35,918 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `litologia_u010_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «Gneisses».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Representa basamento metamórfico; puede contextualizar zonas de cizalla y vetas, pero gneiss no equivale a roca aurífera.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 3,650 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `litologia_u011_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «Granitoides de dos micas».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Contexto granítico para evaluar sistemas relacionados con intrusiones; necesita edad, fertilidad y geoquímica compatibles.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 10,510 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `litologia_u012_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «Gravas, conglomerados, arenas y limos».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Hipótesis de transporte y acumulación detrítica de Au; la unidad incluye depósitos no auríferos y no distingue terrazas de otros sedimentos.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 68,905 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `litologia_u013_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «Micaesquistos, filitas, areniscas, mármoles, calizas, dolomías y margas».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Encajantes metamórficos y carbonatados con contrastes mecánicos y químicos; posible contexto de vetas y reacción roca-fluido.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 5,730 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `litologia_u014_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «Migmatitas, mármoles y granitoides indiferenciados».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Unidad mixta de basamento y granitoides; puede aportar contexto térmico e intrusivo, pero no cuantifica cuánto granito contiene.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 1,840 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `litologia_u015_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «Otros granitoides».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Contexto intrusivo genérico; útil para contrastar hipótesis relacionadas con magmatismo, sin asumir que cualquier granitoide es fértil.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 12,907 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `litologia_u016_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «Pizarras, grauwackas, cuarictas y conglomerados».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Encajantes siliciclásticos/metasedimentarios: posible contexto de vetas y cizallas; necesita estructura, cronología y señal geoquímica.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 12,150 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `litologia_u018_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «Serpentinitas y peridotitas. Rocas básicas y ultrabásicas».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Contexto máfico y ultramáfico; permite probar controles del encajante y contrastes litológicos sin asumir asociación universal con Au.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 3,938 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `litologia_u019_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «Vulcanitas y rocas volcanoclásticas».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Contexto volcánico/volcanoclástico donde se pueden probar hipótesis hidrotermales; no informa sobre alteración ni fertilidad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 5,324 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

## Edades — diccionario completo

### `edades_dominante`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Código de la unidad con mayor área terrestre; empate resuelto por orden textual de categoría.

**Unidades:** categoría nominal.

**Por qué puede predecir o por qué se excluye:** Resume el dominio cronoestratigráfico cartografiado; permite contrastar asociaciones con historia geológica.

**Límites:** Los códigos uNNN no son rangos de favorabilidad ni edades numéricas. Pierde mezclas minoritarias; la edad de la roca no fecha la mineralización.

**Datos observados:** 3.10 % nulos; 28 valores distintos no nulos. Rango o valores más frecuentes: edades_u011: 108,220; edades_u004: 66,065; edades_u002: 39,219; edades_u008: 36,720.

**Procedencia:** edades. Método registrado: mayor área terrestre; empate por texto ordenado.

### `edades_u000_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «CARBONÍFERO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 13,017 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u001_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «CARBONÍFERO-PÉRMICO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 697 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u002_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «CRETÁCICO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 32,114 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u003_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «CRETÁCICO-PALEÓGENO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 6,937 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u004_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «CUATERNARIO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Contexto cuaternario útil para plantear transporte, depósito y cobertura superficial; no identifica por sí solo un placer aurífero.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 68,905 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u005_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «CÁMBRICO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 5,302 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u006_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «CÁMBRICO-ORDOVÍCICO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 11,985 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u007_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «DEVÓNICO-CARBONÍFERO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 7,747 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u008_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «DEVÓNICO-CARBONÍFERO-PÉRMICO (Plut. Hercínico)».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** La leyenda vincula la unidad al plutonismo hercínico; permite probar contexto intrusivo, sin fechar el oro ni acreditar fertilidad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 16,973 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u009_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «JURÁSICO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 14,427 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u010_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «JURÁSICO-CRETÁCICO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 21,963 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u011_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «NEÓGENO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 75,422 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u012_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «NEÓGENO-CUATERNARIO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 15,834 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u013_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «ORDOVÍCICO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 17,306 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u014_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «ORDOVÍCICO-SILÚRICO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 383 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u015_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «PALEÓGENO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 9,616 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u016_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «PALEÓGENO-NEÓGENO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 17,242 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u017_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «PROTEROZOICO SUPERIOR-VENDIENSE».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 9,206 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u018_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «PÉRMICO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 18 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 0.9996915459632874.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u019_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «PÉRMICO-TRIÁSICO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 1,256 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u020_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «RIFEENSE».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 2,154 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u021_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «RIFEENSE-VENDIENSE-CÁMBRICO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 1,638 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u022_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «SILÚRICO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 3,998 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u023_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «SILÚRICO-DEVÓNICO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 7,539 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u025_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «TRIÁSICO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 20,800 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u026_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «TRIÁSICO-JURÁSICO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 1,286 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u027_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «VENDIENSE».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 2,209 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

### `edades_u028_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción de área terrestre ocupada por la unidad «VENDIENSE-CÁMBRICO».

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.

**Límites:** Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.

**Datos observados:** 3.10 % nulos; 7,663 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** edades. Método registrado: intersección exacta; fracción de unidad mixta, no de mineral.

## Estructuras — diccionario completo

### `dist_falla_cartografiada_m`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Distancia euclídea del centro de celda a la traza más próxima de falla/cizalla cartografiada sin marcador textual de supuesta, buscada hasta 10000 m.

**Unidades:** m.

**Por qué puede predecir o por qué se excluye:** Las fracturas y cizallas pueden conducir fluidos y localizar trampas estructurales para mineralización hidrotermal.

**Límites:** NaN si no se encuentra traza en 10 km; no es distancia cero ni ausencia geológica. No se calcula desde el borde de la celda; la cobertura del levantamiento no está acreditada.

**Datos observados:** 18.90 % nulos; 401,517 valores distintos no nulos. Rango o valores más frecuentes: 4.5324184611672536e-05 … 9999.8740234375.

**Procedencia:** contactos_geode. Método registrado: centro a traza cartografiada; NaN sin traza dentro de 10000 m; cobertura no acreditada.

### `dens_aprox_falla_cartografiada_1000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de falla/cizalla cartografiada sin marcador textual de supuesta por superficie terrestre en una ventana de radio 1000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Las fracturas y cizallas pueden conducir fluidos y localizar trampas estructurales para mineralización hidrotermal. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 251,917 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 8.816088676452637.

**Procedencia:** contactos_geode. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

### `dens_aprox_falla_cartografiada_5000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de falla/cizalla cartografiada sin marcador textual de supuesta por superficie terrestre en una ventana de radio 5000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Las fracturas y cizallas pueden conducir fluidos y localizar trampas estructurales para mineralización hidrotermal. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 356,677 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 3.9366743564605713.

**Procedencia:** contactos_geode. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

### `dens_aprox_falla_cartografiada_10000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de falla/cizalla cartografiada sin marcador textual de supuesta por superficie terrestre en una ventana de radio 10000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Las fracturas y cizallas pueden conducir fluidos y localizar trampas estructurales para mineralización hidrotermal. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 395,772 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 2.763320207595825.

**Procedencia:** contactos_geode. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

### `dist_falla_supuesta_m`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Distancia euclídea del centro de celda a la traza más próxima de falla/cizalla supuesta/oculta, buscada hasta 10000 m.

**Unidades:** m.

**Por qué puede predecir o por qué se excluye:** Las fracturas y cizallas pueden conducir fluidos y localizar trampas estructurales para mineralización hidrotermal.

**Límites:** NaN si no se encuentra traza en 10 km; no es distancia cero ni ausencia geológica. No se calcula desde el borde de la celda; la cobertura del levantamiento no está acreditada.

**Datos observados:** 30.21 % nulos; 344,989 valores distintos no nulos. Rango o valores más frecuentes: 0.039505358785390854 … 9999.9765625.

**Procedencia:** contactos_geode. Método registrado: centro a traza cartografiada; NaN sin traza dentro de 10000 m; cobertura no acreditada.

### `dens_aprox_falla_supuesta_1000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de falla/cizalla supuesta/oculta por superficie terrestre en una ventana de radio 1000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Las fracturas y cizallas pueden conducir fluidos y localizar trampas estructurales para mineralización hidrotermal. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 92,973 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 3.4959490299224854.

**Procedencia:** contactos_geode. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

### `dens_aprox_falla_supuesta_5000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de falla/cizalla supuesta/oculta por superficie terrestre en una ventana de radio 5000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Las fracturas y cizallas pueden conducir fluidos y localizar trampas estructurales para mineralización hidrotermal. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 233,163 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.4204356670379639.

**Procedencia:** contactos_geode. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

### `dens_aprox_falla_supuesta_10000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de falla/cizalla supuesta/oculta por superficie terrestre en una ventana de radio 10000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Las fracturas y cizallas pueden conducir fluidos y localizar trampas estructurales para mineralización hidrotermal. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 314,586 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 0.8389087319374084.

**Procedencia:** contactos_geode. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

### `dist_cabalgamiento_cartografiada_m`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Distancia euclídea del centro de celda a la traza más próxima de cabalgamiento cartografiada sin marcador textual de supuesta, buscada hasta 10000 m.

**Unidades:** m.

**Por qué puede predecir o por qué se excluye:** Puede representar zonas de deformación y contactos que canalizan fluidos; la cronología respecto al oro es decisiva.

**Límites:** NaN si no se encuentra traza en 10 km; no es distancia cero ni ausencia geológica. No se calcula desde el borde de la celda; la cobertura del levantamiento no está acreditada.

**Datos observados:** 55.69 % nulos; 219,459 valores distintos no nulos. Rango o valores más frecuentes: 0.0027950857765972614 … 9999.80078125.

**Procedencia:** contactos_geode. Método registrado: centro a traza cartografiada; NaN sin traza dentro de 10000 m; cobertura no acreditada.

### `dens_aprox_cabalgamiento_cartografiada_1000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de cabalgamiento cartografiada sin marcador textual de supuesta por superficie terrestre en una ventana de radio 1000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Puede representar zonas de deformación y contactos que canalizan fluidos; la cronología respecto al oro es decisiva. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 65,016 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 5.458712100982666.

**Procedencia:** contactos_geode. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

### `dens_aprox_cabalgamiento_cartografiada_5000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de cabalgamiento cartografiada sin marcador textual de supuesta por superficie terrestre en una ventana de radio 5000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Puede representar zonas de deformación y contactos que canalizan fluidos; la cronología respecto al oro es decisiva. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 147,164 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 2.758855104446411.

**Procedencia:** contactos_geode. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

### `dens_aprox_cabalgamiento_cartografiada_10000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de cabalgamiento cartografiada sin marcador textual de supuesta por superficie terrestre en una ventana de radio 10000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Puede representar zonas de deformación y contactos que canalizan fluidos; la cronología respecto al oro es decisiva. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 209,695 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.725170612335205.

**Procedencia:** contactos_geode. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

### `dist_cabalgamiento_supuesta_m`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Distancia euclídea del centro de celda a la traza más próxima de cabalgamiento supuesta/oculta, buscada hasta 10000 m.

**Unidades:** m.

**Por qué puede predecir o por qué se excluye:** Puede representar zonas de deformación y contactos que canalizan fluidos; la cronología respecto al oro es decisiva.

**Límites:** NaN si no se encuentra traza en 10 km; no es distancia cero ni ausencia geológica. No se calcula desde el borde de la celda; la cobertura del levantamiento no está acreditada.

**Datos observados:** 80.06 % nulos; 98,876 valores distintos no nulos. Rango o valores más frecuentes: 0.024025872349739075 … 9999.9814453125.

**Procedencia:** contactos_geode. Método registrado: centro a traza cartografiada; NaN sin traza dentro de 10000 m; cobertura no acreditada.

### `dens_aprox_cabalgamiento_supuesta_1000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de cabalgamiento supuesta/oculta por superficie terrestre en una ventana de radio 1000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Puede representar zonas de deformación y contactos que canalizan fluidos; la cronología respecto al oro es decisiva. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 16,407 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 2.43988037109375.

**Procedencia:** contactos_geode. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

### `dens_aprox_cabalgamiento_supuesta_5000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de cabalgamiento supuesta/oculta por superficie terrestre en una ventana de radio 5000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Puede representar zonas de deformación y contactos que canalizan fluidos; la cronología respecto al oro es decisiva. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 47,990 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 0.730979859828949.

**Procedencia:** contactos_geode. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

### `dens_aprox_cabalgamiento_supuesta_10000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de cabalgamiento supuesta/oculta por superficie terrestre en una ventana de radio 10000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Puede representar zonas de deformación y contactos que canalizan fluidos; la cronología respecto al oro es decisiva. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 79,349 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 0.38278114795684814.

**Procedencia:** contactos_geode. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

### `dist_contacto_intrusivo_cartografiada_m`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Distancia euclídea del centro de celda a la traza más próxima de contacto intrusivo cartografiada sin marcador textual de supuesta, buscada hasta 10000 m.

**Unidades:** m.

**Por qué puede predecir o por qué se excluye:** Puede aproximar interfaces entre intrusión y encajante asociadas a circulación hidrotermal y reacción roca-fluido.

**Límites:** NaN si no se encuentra traza en 10 km; no es distancia cero ni ausencia geológica. No se calcula desde el borde de la celda; la cobertura del levantamiento no está acreditada.

**Datos observados:** 69.96 % nulos; 148,991 valores distintos no nulos. Rango o valores más frecuentes: 0.004934257362037897 … 9999.9375.

**Procedencia:** contactos_geode. Método registrado: centro a traza cartografiada; NaN sin traza dentro de 10000 m; cobertura no acreditada.

### `dens_aprox_contacto_intrusivo_cartografiada_1000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de contacto intrusivo cartografiada sin marcador textual de supuesta por superficie terrestre en una ventana de radio 1000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Puede aproximar interfaces entre intrusión y encajante asociadas a circulación hidrotermal y reacción roca-fluido. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 67,262 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 18.93927001953125.

**Procedencia:** contactos_geode. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

### `dens_aprox_contacto_intrusivo_cartografiada_5000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de contacto intrusivo cartografiada sin marcador textual de supuesta por superficie terrestre en una ventana de radio 5000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Puede aproximar interfaces entre intrusión y encajante asociadas a circulación hidrotermal y reacción roca-fluido. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 112,224 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 10.35904598236084.

**Procedencia:** contactos_geode. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

### `dens_aprox_contacto_intrusivo_cartografiada_10000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de contacto intrusivo cartografiada sin marcador textual de supuesta por superficie terrestre en una ventana de radio 10000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Puede aproximar interfaces entre intrusión y encajante asociadas a circulación hidrotermal y reacción roca-fluido. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 144,147 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 6.646313667297363.

**Procedencia:** contactos_geode. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

### `dist_contacto_intrusivo_supuesta_m`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Distancia euclídea del centro de celda a la traza más próxima de contacto intrusivo supuesta/oculta, buscada hasta 10000 m.

**Unidades:** m.

**Por qué puede predecir o por qué se excluye:** Puede aproximar interfaces entre intrusión y encajante asociadas a circulación hidrotermal y reacción roca-fluido.

**Límites:** NaN si no se encuentra traza en 10 km; no es distancia cero ni ausencia geológica. No se calcula desde el borde de la celda; la cobertura del levantamiento no está acreditada.

**Datos observados:** 98.00 % nulos; 9,940 valores distintos no nulos. Rango o valores más frecuentes: 0.25351035594940186 … 9998.984375.

**Procedencia:** contactos_geode. Método registrado: centro a traza cartografiada; NaN sin traza dentro de 10000 m; cobertura no acreditada.

### `dens_aprox_contacto_intrusivo_supuesta_1000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de contacto intrusivo supuesta/oculta por superficie terrestre en una ventana de radio 1000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Puede aproximar interfaces entre intrusión y encajante asociadas a circulación hidrotermal y reacción roca-fluido. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 1,020 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 3.238482713699341.

**Procedencia:** contactos_geode. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

### `dens_aprox_contacto_intrusivo_supuesta_5000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de contacto intrusivo supuesta/oculta por superficie terrestre en una ventana de radio 5000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Puede aproximar interfaces entre intrusión y encajante asociadas a circulación hidrotermal y reacción roca-fluido. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 3,840 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 0.6592413187026978.

**Procedencia:** contactos_geode. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

### `dens_aprox_contacto_intrusivo_supuesta_10000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de contacto intrusivo supuesta/oculta por superficie terrestre en una ventana de radio 10000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Puede aproximar interfaces entre intrusión y encajante asociadas a circulación hidrotermal y reacción roca-fluido. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 7,974 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 0.2605421245098114.

**Procedencia:** contactos_geode. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

## Geoquímica — diccionario completo

### `au_clase_modal`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Clase de oro con mayor área válida en la celda; empate a la clase menor. Códigos según la leyenda local reproducida en este informe.

**Unidades:** índice de clase.

**Por qué puede predecir o por qué se excluye:** Señal del propio elemento objetivo en sedimentos; puede reflejar una fuente aurífera en la cuenca aportante. No localiza necesariamente el yacimiento en la celda y puede reflejar actividad minera previa.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 7 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 6.0.

**Procedencia:** geoquimica_au. Método registrado: moda ponderada; empate clase menor; RGB coincidente; leyenda local pendiente.

### `au_proporcion_clase_0`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 0 de oro; etiqueta local «0,08 - 1,34». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Señal del propio elemento objetivo en sedimentos; puede reflejar una fuente aurífera en la cuenca aportante. No localiza necesariamente el yacimiento en la celda y puede reflejar actividad minera previa.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 92 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_au. Método registrado: proporciones alternativas a moda; no concentraciones.

### `au_proporcion_clase_1`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 1 de oro; etiqueta local «1,35 - 2». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Señal del propio elemento objetivo en sedimentos; puede reflejar una fuente aurífera en la cuenca aportante. No localiza necesariamente el yacimiento en la celda y puede reflejar actividad minera previa.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 169 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_au. Método registrado: proporciones alternativas a moda; no concentraciones.

### `au_proporcion_clase_2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 2 de oro; etiqueta local «2,01 - 3,5». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Señal del propio elemento objetivo en sedimentos; puede reflejar una fuente aurífera en la cuenca aportante. No localiza necesariamente el yacimiento en la celda y puede reflejar actividad minera previa.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 197 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_au. Método registrado: proporciones alternativas a moda; no concentraciones.

### `au_proporcion_clase_3`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 3 de oro; etiqueta local «3,51 - 6,1». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Señal del propio elemento objetivo en sedimentos; puede reflejar una fuente aurífera en la cuenca aportante. No localiza necesariamente el yacimiento en la celda y puede reflejar actividad minera previa.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 180 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_au. Método registrado: proporciones alternativas a moda; no concentraciones.

### `au_proporcion_clase_4`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 4 de oro; etiqueta local «6,11 - 12,05». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Señal del propio elemento objetivo en sedimentos; puede reflejar una fuente aurífera en la cuenca aportante. No localiza necesariamente el yacimiento en la celda y puede reflejar actividad minera previa.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 131 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_au. Método registrado: proporciones alternativas a moda; no concentraciones.

### `au_proporcion_clase_5`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 5 de oro; etiqueta local «12,06 - 43». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Señal del propio elemento objetivo en sedimentos; puede reflejar una fuente aurífera en la cuenca aportante. No localiza necesariamente el yacimiento en la celda y puede reflejar actividad minera previa.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 70 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_au. Método registrado: proporciones alternativas a moda; no concentraciones.

### `au_proporcion_clase_6`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 6 de oro; etiqueta local «43,01 - 1.964». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Señal del propio elemento objetivo en sedimentos; puede reflejar una fuente aurífera en la cuenca aportante. No localiza necesariamente el yacimiento en la celda y puede reflejar actividad minera previa.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 19 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_au. Método registrado: proporciones alternativas a moda; no concentraciones.

### `as_clase_modal`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Clase de arsénico con mayor área válida en la celda; empate a la clase menor. Códigos según la leyenda local reproducida en este informe.

**Unidades:** índice de clase.

**Por qué puede predecir o por qué se excluye:** Elemento guía de ciertos sistemas auríferos hidrotermales; una asociación As-Au coherente con el contexto puede aportar evidencia indirecta. También existen anomalías de As sin Au.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 8 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 7.0.

**Procedencia:** geoquimica_as. Método registrado: moda ponderada; empate clase menor; RGB coincidente; leyenda local pendiente.

### `as_proporcion_clase_0`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 0 de arsénico; etiqueta local «0,08 - 4,55». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Elemento guía de ciertos sistemas auríferos hidrotermales; una asociación As-Au coherente con el contexto puede aportar evidencia indirecta. También existen anomalías de As sin Au.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 18 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_as. Método registrado: proporciones alternativas a moda; no concentraciones.

### `as_proporcion_clase_1`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 1 de arsénico; etiqueta local «4,56 - 6». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Elemento guía de ciertos sistemas auríferos hidrotermales; una asociación As-Au coherente con el contexto puede aportar evidencia indirecta. También existen anomalías de As sin Au.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 33 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_as. Método registrado: proporciones alternativas a moda; no concentraciones.

### `as_proporcion_clase_2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 2 de arsénico; etiqueta local «6,01 - 8,78». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Elemento guía de ciertos sistemas auríferos hidrotermales; una asociación As-Au coherente con el contexto puede aportar evidencia indirecta. También existen anomalías de As sin Au.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 58 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_as. Método registrado: proporciones alternativas a moda; no concentraciones.

### `as_proporcion_clase_3`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 3 de arsénico; etiqueta local «8,79 - 12,67». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Elemento guía de ciertos sistemas auríferos hidrotermales; una asociación As-Au coherente con el contexto puede aportar evidencia indirecta. También existen anomalías de As sin Au.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 94 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_as. Método registrado: proporciones alternativas a moda; no concentraciones.

### `as_proporcion_clase_4`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 4 de arsénico; etiqueta local «12,68 - 16,16». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Elemento guía de ciertos sistemas auríferos hidrotermales; una asociación As-Au coherente con el contexto puede aportar evidencia indirecta. También existen anomalías de As sin Au.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 111 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_as. Método registrado: proporciones alternativas a moda; no concentraciones.

### `as_proporcion_clase_5`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 5 de arsénico; etiqueta local «16,17 - 19,9». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Elemento guía de ciertos sistemas auríferos hidrotermales; una asociación As-Au coherente con el contexto puede aportar evidencia indirecta. También existen anomalías de As sin Au.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 119 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_as. Método registrado: proporciones alternativas a moda; no concentraciones.

### `as_proporcion_clase_6`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 6 de arsénico; etiqueta local «19,91 - 45». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Elemento guía de ciertos sistemas auríferos hidrotermales; una asociación As-Au coherente con el contexto puede aportar evidencia indirecta. También existen anomalías de As sin Au.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 97 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_as. Método registrado: proporciones alternativas a moda; no concentraciones.

### `as_proporcion_clase_7`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 7 de arsénico; etiqueta local «45,01 - 1.949,5». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Elemento guía de ciertos sistemas auríferos hidrotermales; una asociación As-Au coherente con el contexto puede aportar evidencia indirecta. También existen anomalías de As sin Au.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 33 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_as. Método registrado: proporciones alternativas a moda; no concentraciones.

### `sb_clase_modal`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Clase de antimonio con mayor área válida en la celda; empate a la clase menor. Códigos según la leyenda local reproducida en este informe.

**Unidades:** índice de clase.

**Por qué puede predecir o por qué se excluye:** Elemento guía en determinadas asociaciones hidrotermales con Au; su combinación con As y estructuras es una hipótesis más específica que Sb aislado.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 2.09 % nulos; 8 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 7.0.

**Procedencia:** geoquimica_sb. Método registrado: moda ponderada; empate clase menor; RGB coincidente; leyenda local pendiente.

### `sb_proporcion_clase_0`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 0 de antimonio; etiqueta local «0,043 - 0,228». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Elemento guía en determinadas asociaciones hidrotermales con Au; su combinación con As y estructuras es una hipótesis más específica que Sb aislado.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 2.09 % nulos; 14 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_sb. Método registrado: proporciones alternativas a moda; no concentraciones.

### `sb_proporcion_clase_1`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 1 de antimonio; etiqueta local «0,228 - 0,61». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Elemento guía en determinadas asociaciones hidrotermales con Au; su combinación con As y estructuras es una hipótesis más específica que Sb aislado.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 2.09 % nulos; 52 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_sb. Método registrado: proporciones alternativas a moda; no concentraciones.

### `sb_proporcion_clase_2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 2 de antimonio; etiqueta local «0,61 - 0,78». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Elemento guía en determinadas asociaciones hidrotermales con Au; su combinación con As y estructuras es una hipótesis más específica que Sb aislado.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 2.09 % nulos; 64 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_sb. Método registrado: proporciones alternativas a moda; no concentraciones.

### `sb_proporcion_clase_3`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 3 de antimonio; etiqueta local «0,78 - 1,19». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Elemento guía en determinadas asociaciones hidrotermales con Au; su combinación con As y estructuras es una hipótesis más específica que Sb aislado.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 2.09 % nulos; 72 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_sb. Método registrado: proporciones alternativas a moda; no concentraciones.

### `sb_proporcion_clase_4`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 4 de antimonio; etiqueta local «1,19 - 1,96». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Elemento guía en determinadas asociaciones hidrotermales con Au; su combinación con As y estructuras es una hipótesis más específica que Sb aislado.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 2.09 % nulos; 96 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_sb. Método registrado: proporciones alternativas a moda; no concentraciones.

### `sb_proporcion_clase_5`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 5 de antimonio; etiqueta local «1,96 - 3,16». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Elemento guía en determinadas asociaciones hidrotermales con Au; su combinación con As y estructuras es una hipótesis más específica que Sb aislado.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 2.09 % nulos; 91 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_sb. Método registrado: proporciones alternativas a moda; no concentraciones.

### `sb_proporcion_clase_6`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 6 de antimonio; etiqueta local «3,16 - 6,3». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Elemento guía en determinadas asociaciones hidrotermales con Au; su combinación con As y estructuras es una hipótesis más específica que Sb aislado.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 2.09 % nulos; 59 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_sb. Método registrado: proporciones alternativas a moda; no concentraciones.

### `sb_proporcion_clase_7`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 7 de antimonio; etiqueta local «6,3 - 343,14». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Elemento guía en determinadas asociaciones hidrotermales con Au; su combinación con As y estructuras es una hipótesis más específica que Sb aislado.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 2.09 % nulos; 23 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_sb. Método registrado: proporciones alternativas a moda; no concentraciones.

### `bi_clase_modal`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Clase de bismuto con mayor área válida en la celda; empate a la clase menor. Códigos según la leyenda local reproducida en este informe.

**Unidades:** índice de clase.

**Por qué puede predecir o por qué se excluye:** Puede ayudar a reconocer asociaciones de Au vinculadas a intrusiones; su utilidad depende del tipo de sistema y del contexto geológico.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 8 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 7.0.

**Procedencia:** geoquimica_bi. Método registrado: moda ponderada; empate clase menor; RGB coincidente; leyenda local pendiente.

### `bi_proporcion_clase_0`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 0 de bismuto; etiqueta local «0,08 - 0,09». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede ayudar a reconocer asociaciones de Au vinculadas a intrusiones; su utilidad depende del tipo de sistema y del contexto geológico.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 24 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_bi. Método registrado: proporciones alternativas a moda; no concentraciones.

### `bi_proporcion_clase_1`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 1 de bismuto; etiqueta local «0,1 - 0,14». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede ayudar a reconocer asociaciones de Au vinculadas a intrusiones; su utilidad depende del tipo de sistema y del contexto geológico.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 61 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_bi. Método registrado: proporciones alternativas a moda; no concentraciones.

### `bi_proporcion_clase_2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 2 de bismuto; etiqueta local «0,15 - 0,18». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede ayudar a reconocer asociaciones de Au vinculadas a intrusiones; su utilidad depende del tipo de sistema y del contexto geológico.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 68 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_bi. Método registrado: proporciones alternativas a moda; no concentraciones.

### `bi_proporcion_clase_3`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 3 de bismuto; etiqueta local «0,19 - 0,25». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede ayudar a reconocer asociaciones de Au vinculadas a intrusiones; su utilidad depende del tipo de sistema y del contexto geológico.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 95 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_bi. Método registrado: proporciones alternativas a moda; no concentraciones.

### `bi_proporcion_clase_4`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 4 de bismuto; etiqueta local «0,26 - 0,32». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede ayudar a reconocer asociaciones de Au vinculadas a intrusiones; su utilidad depende del tipo de sistema y del contexto geológico.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 108 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_bi. Método registrado: proporciones alternativas a moda; no concentraciones.

### `bi_proporcion_clase_5`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 5 de bismuto; etiqueta local «0,33 - 0,42». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede ayudar a reconocer asociaciones de Au vinculadas a intrusiones; su utilidad depende del tipo de sistema y del contexto geológico.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 98 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_bi. Método registrado: proporciones alternativas a moda; no concentraciones.

### `bi_proporcion_clase_6`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 6 de bismuto; etiqueta local «0,43 - 0,68». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede ayudar a reconocer asociaciones de Au vinculadas a intrusiones; su utilidad depende del tipo de sistema y del contexto geológico.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 83 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_bi. Método registrado: proporciones alternativas a moda; no concentraciones.

### `bi_proporcion_clase_7`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 7 de bismuto; etiqueta local «0,69 - 63,86». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede ayudar a reconocer asociaciones de Au vinculadas a intrusiones; su utilidad depende del tipo de sistema y del contexto geológico.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 39 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_bi. Método registrado: proporciones alternativas a moda; no concentraciones.

### `hg_clase_modal`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Clase de mercurio con mayor área válida en la celda; empate a la clase menor. Códigos según la leyenda local reproducida en este informe.

**Unidades:** índice de clase.

**Por qué puede predecir o por qué se excluye:** Puede aportar evidencia de determinados sistemas epitermales; deben distinguirse anomalías naturales de aportes mineros o ambientales.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 8 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 7.0.

**Procedencia:** geoquimica_hg. Método registrado: moda ponderada; empate clase menor; RGB coincidente; leyenda local pendiente.

### `hg_proporcion_clase_0`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 0 de mercurio; etiqueta local «0,28 - 6». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede aportar evidencia de determinados sistemas epitermales; deben distinguirse anomalías naturales de aportes mineros o ambientales.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 40 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_hg. Método registrado: proporciones alternativas a moda; no concentraciones.

### `hg_proporcion_clase_1`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 1 de mercurio; etiqueta local «6,01 - 11,38». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede aportar evidencia de determinados sistemas epitermales; deben distinguirse anomalías naturales de aportes mineros o ambientales.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 116 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_hg. Método registrado: proporciones alternativas a moda; no concentraciones.

### `hg_proporcion_clase_2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 2 de mercurio; etiqueta local «11,39 - 15,67». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede aportar evidencia de determinados sistemas epitermales; deben distinguirse anomalías naturales de aportes mineros o ambientales.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 132 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_hg. Método registrado: proporciones alternativas a moda; no concentraciones.

### `hg_proporcion_clase_3`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 3 de mercurio; etiqueta local «15,68 - 23,95». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede aportar evidencia de determinados sistemas epitermales; deben distinguirse anomalías naturales de aportes mineros o ambientales.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 178 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_hg. Método registrado: proporciones alternativas a moda; no concentraciones.

### `hg_proporcion_clase_4`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 4 de mercurio; etiqueta local «23,96 - 37,23». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede aportar evidencia de determinados sistemas epitermales; deben distinguirse anomalías naturales de aportes mineros o ambientales.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 165 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_hg. Método registrado: proporciones alternativas a moda; no concentraciones.

### `hg_proporcion_clase_5`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 5 de mercurio; etiqueta local «37,24 - 47». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede aportar evidencia de determinados sistemas epitermales; deben distinguirse anomalías naturales de aportes mineros o ambientales.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 119 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_hg. Método registrado: proporciones alternativas a moda; no concentraciones.

### `hg_proporcion_clase_6`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 6 de mercurio; etiqueta local «47,01 - 150». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede aportar evidencia de determinados sistemas epitermales; deben distinguirse anomalías naturales de aportes mineros o ambientales.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 92 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_hg. Método registrado: proporciones alternativas a moda; no concentraciones.

### `hg_proporcion_clase_7`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 7 de mercurio; etiqueta local «150,01 - 76.203». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede aportar evidencia de determinados sistemas epitermales; deben distinguirse anomalías naturales de aportes mineros o ambientales.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 21 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_hg. Método registrado: proporciones alternativas a moda; no concentraciones.

### `cu_clase_modal`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Clase de cobre con mayor área válida en la celda; empate a la clase menor. Códigos según la leyenda local reproducida en este informe.

**Unidades:** índice de clase.

**Por qué puede predecir o por qué se excluye:** Permite probar asociaciones hidrotermales Cu-Au; muchas anomalías de Cu responden a otros procesos y no implican oro.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 8 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 7.0.

**Procedencia:** geoquimica_cu. Método registrado: moda ponderada; empate clase menor; RGB coincidente; leyenda local pendiente.

### `cu_proporcion_clase_0`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 0 de cobre; etiqueta local «0,42 - 6,28». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Permite probar asociaciones hidrotermales Cu-Au; muchas anomalías de Cu responden a otros procesos y no implican oro.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 21 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_cu. Método registrado: proporciones alternativas a moda; no concentraciones.

### `cu_proporcion_clase_1`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 1 de cobre; etiqueta local «6,29 - 10,35». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Permite probar asociaciones hidrotermales Cu-Au; muchas anomalías de Cu responden a otros procesos y no implican oro.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 63 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_cu. Método registrado: proporciones alternativas a moda; no concentraciones.

### `cu_proporcion_clase_2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 2 de cobre; etiqueta local «10,36 - 12,73». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Permite probar asociaciones hidrotermales Cu-Au; muchas anomalías de Cu responden a otros procesos y no implican oro.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 87 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_cu. Método registrado: proporciones alternativas a moda; no concentraciones.

### `cu_proporcion_clase_3`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 3 de cobre; etiqueta local «12,74 - 16,43». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Permite probar asociaciones hidrotermales Cu-Au; muchas anomalías de Cu responden a otros procesos y no implican oro.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 112 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_cu. Método registrado: proporciones alternativas a moda; no concentraciones.

### `cu_proporcion_clase_4`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 4 de cobre; etiqueta local «16,44 - 22,51». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Permite probar asociaciones hidrotermales Cu-Au; muchas anomalías de Cu responden a otros procesos y no implican oro.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 138 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_cu. Método registrado: proporciones alternativas a moda; no concentraciones.

### `cu_proporcion_clase_5`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 5 de cobre; etiqueta local «22,52 - 28,25». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Permite probar asociaciones hidrotermales Cu-Au; muchas anomalías de Cu responden a otros procesos y no implican oro.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 135 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_cu. Método registrado: proporciones alternativas a moda; no concentraciones.

### `cu_proporcion_clase_6`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 6 de cobre; etiqueta local «28,26 - 50». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Permite probar asociaciones hidrotermales Cu-Au; muchas anomalías de Cu responden a otros procesos y no implican oro.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 83 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_cu. Método registrado: proporciones alternativas a moda; no concentraciones.

### `cu_proporcion_clase_7`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 7 de cobre; etiqueta local «50,01 - 2.038,62». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Permite probar asociaciones hidrotermales Cu-Au; muchas anomalías de Cu responden a otros procesos y no implican oro.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 1.76 % nulos; 24 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_cu. Método registrado: proporciones alternativas a moda; no concentraciones.

### `pb_clase_modal`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Clase de plomo con mayor área válida en la celda; empate a la clase menor. Códigos según la leyenda local reproducida en este informe.

**Unidades:** índice de clase.

**Por qué puede predecir o por qué se excluye:** Contexto de asociaciones polimetálicas que en ciertos sistemas acompañan Au; señal menos específica, sensible al fondo litológico y a actividad humana.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 2.01 % nulos; 8 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 7.0.

**Procedencia:** geoquimica_pb. Método registrado: moda ponderada; empate clase menor; RGB coincidente; leyenda local pendiente.

### `pb_proporcion_clase_0`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 0 de plomo; etiqueta local «0,28 - 10,43». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Contexto de asociaciones polimetálicas que en ciertos sistemas acompañan Au; señal menos específica, sensible al fondo litológico y a actividad humana.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 2.01 % nulos; 13 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_pb. Método registrado: proporciones alternativas a moda; no concentraciones.

### `pb_proporcion_clase_1`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 1 de plomo; etiqueta local «10,44 - 14,25». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Contexto de asociaciones polimetálicas que en ciertos sistemas acompañan Au; señal menos específica, sensible al fondo litológico y a actividad humana.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 2.01 % nulos; 22 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_pb. Método registrado: proporciones alternativas a moda; no concentraciones.

### `pb_proporcion_clase_2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 2 de plomo; etiqueta local «14,26 - 17,16». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Contexto de asociaciones polimetálicas que en ciertos sistemas acompañan Au; señal menos específica, sensible al fondo litológico y a actividad humana.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 2.01 % nulos; 35 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_pb. Método registrado: proporciones alternativas a moda; no concentraciones.

### `pb_proporcion_clase_3`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 3 de plomo; etiqueta local «17,17 - 22,51». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Contexto de asociaciones polimetálicas que en ciertos sistemas acompañan Au; señal menos específica, sensible al fondo litológico y a actividad humana.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 2.01 % nulos; 66 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_pb. Método registrado: proporciones alternativas a moda; no concentraciones.

### `pb_proporcion_clase_4`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 4 de plomo; etiqueta local «22,52 - 29,75». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Contexto de asociaciones polimetálicas que en ciertos sistemas acompañan Au; señal menos específica, sensible al fondo litológico y a actividad humana.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 2.01 % nulos; 105 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_pb. Método registrado: proporciones alternativas a moda; no concentraciones.

### `pb_proporcion_clase_5`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 5 de plomo; etiqueta local «29,76 - 35,12». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Contexto de asociaciones polimetálicas que en ciertos sistemas acompañan Au; señal menos específica, sensible al fondo litológico y a actividad humana.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 2.01 % nulos; 108 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_pb. Método registrado: proporciones alternativas a moda; no concentraciones.

### `pb_proporcion_clase_6`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 6 de plomo; etiqueta local «35,13 - 65». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Contexto de asociaciones polimetálicas que en ciertos sistemas acompañan Au; señal menos específica, sensible al fondo litológico y a actividad humana.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 2.01 % nulos; 96 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_pb. Método registrado: proporciones alternativas a moda; no concentraciones.

### `pb_proporcion_clase_7`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 7 de plomo; etiqueta local «65,01 - 4.979,11». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Contexto de asociaciones polimetálicas que en ciertos sistemas acompañan Au; señal menos específica, sensible al fondo litológico y a actividad humana.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 2.01 % nulos; 39 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_pb. Método registrado: proporciones alternativas a moda; no concentraciones.

### `zn_clase_modal`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Clase de zinc con mayor área válida en la celda; empate a la clase menor. Códigos según la leyenda local reproducida en este informe.

**Unidades:** índice de clase.

**Por qué puede predecir o por qué se excluye:** Contexto de asociaciones polimetálicas; puede añadir información conjunta, aunque Zn elevado por sí solo no acredita Au.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 28.89 % nulos; 7 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 7.0.

**Procedencia:** geoquimica_zn. Método registrado: moda ponderada; empate clase menor; RGB coincidente; leyenda local pendiente.

### `zn_proporcion_clase_0`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 0 de zinc; etiqueta local «0,53 - 21,12». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Contexto de asociaciones polimetálicas; puede añadir información conjunta, aunque Zn elevado por sí solo no acredita Au.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 28.89 % nulos; 7 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_zn. Método registrado: proporciones alternativas a moda; no concentraciones.

### `zn_proporcion_clase_1`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 1 de zinc; etiqueta local «21,13 - 31,74». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Contexto de asociaciones polimetálicas; puede añadir información conjunta, aunque Zn elevado por sí solo no acredita Au.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 28.89 % nulos; 25 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_zn. Método registrado: proporciones alternativas a moda; no concentraciones.

### `zn_proporcion_clase_2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 2 de zinc; etiqueta local «31,75 - 41,08». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Contexto de asociaciones polimetálicas; puede añadir información conjunta, aunque Zn elevado por sí solo no acredita Au.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 28.89 % nulos; 24 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_zn. Método registrado: proporciones alternativas a moda; no concentraciones.

### `zn_proporcion_clase_3`

**Rol y uso:** predictor_candidato; Candidata en lista; descartar como señal de valor constante.

**Qué significa:** Fracción del área válida asignada a clase 3 de zinc; etiqueta local «41,09 - 56,62». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Contexto de asociaciones polimetálicas; puede añadir información conjunta, aunque Zn elevado por sí solo no acredita Au.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida. En esta ejecución es 0 en todas las celdas no nulas: no discrimina valores; revisar paleta/rechazo RGB.

**Datos observados:** 28.89 % nulos; 1 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 0.0.

**Procedencia:** geoquimica_zn. Método registrado: proporciones alternativas a moda; no concentraciones.

### `zn_proporcion_clase_4`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 4 de zinc; etiqueta local «56,63 - 73,79». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Contexto de asociaciones polimetálicas; puede añadir información conjunta, aunque Zn elevado por sí solo no acredita Au.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 28.89 % nulos; 61 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_zn. Método registrado: proporciones alternativas a moda; no concentraciones.

### `zn_proporcion_clase_5`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 5 de zinc; etiqueta local «73,8 - 90,5». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Contexto de asociaciones polimetálicas; puede añadir información conjunta, aunque Zn elevado por sí solo no acredita Au.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 28.89 % nulos; 120 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_zn. Método registrado: proporciones alternativas a moda; no concentraciones.

### `zn_proporcion_clase_6`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 6 de zinc; etiqueta local «90,51 - 157». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Contexto de asociaciones polimetálicas; puede añadir información conjunta, aunque Zn elevado por sí solo no acredita Au.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 28.89 % nulos; 107 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_zn. Método registrado: proporciones alternativas a moda; no concentraciones.

### `zn_proporcion_clase_7`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 7 de zinc; etiqueta local «157,01 - 21.638,97». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Contexto de asociaciones polimetálicas; puede añadir información conjunta, aunque Zn elevado por sí solo no acredita Au.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 28.89 % nulos; 43 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_zn. Método registrado: proporciones alternativas a moda; no concentraciones.

### `w_clase_modal`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Clase de wolframio con mayor área válida en la celda; empate a la clase menor. Códigos según la leyenda local reproducida en este informe.

**Unidades:** índice de clase.

**Por qué puede predecir o por qué se excluye:** Puede acompañar sistemas hidrotermales relacionados con intrusiones; su asociación espacial con Au no exige correlación de concentraciones.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 17.15 % nulos; 6 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 6.0.

**Procedencia:** geoquimica_w. Método registrado: moda ponderada; empate clase menor; RGB coincidente; leyenda local pendiente.

### `w_proporcion_clase_0`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 0 de wolframio; etiqueta local «0,5 - 0,53». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede acompañar sistemas hidrotermales relacionados con intrusiones; su asociación espacial con Au no exige correlación de concentraciones.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 17.15 % nulos; 56 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_w. Método registrado: proporciones alternativas a moda; no concentraciones.

### `w_proporcion_clase_1`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 1 de wolframio; etiqueta local «0,54 - 0,68». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede acompañar sistemas hidrotermales relacionados con intrusiones; su asociación espacial con Au no exige correlación de concentraciones.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 17.15 % nulos; 75 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_w. Método registrado: proporciones alternativas a moda; no concentraciones.

### `w_proporcion_clase_2`

**Rol y uso:** predictor_candidato; Candidata en lista; descartar como señal de valor constante.

**Qué significa:** Fracción del área válida asignada a clase 2 de wolframio; etiqueta local «0,69 - 0,84». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede acompañar sistemas hidrotermales relacionados con intrusiones; su asociación espacial con Au no exige correlación de concentraciones.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida. En esta ejecución es 0 en todas las celdas no nulas: no discrimina valores; revisar paleta/rechazo RGB.

**Datos observados:** 17.15 % nulos; 1 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 0.0.

**Procedencia:** geoquimica_w. Método registrado: proporciones alternativas a moda; no concentraciones.

### `w_proporcion_clase_3`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 3 de wolframio; etiqueta local «0,85 - 1,32». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede acompañar sistemas hidrotermales relacionados con intrusiones; su asociación espacial con Au no exige correlación de concentraciones.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 17.15 % nulos; 90 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_w. Método registrado: proporciones alternativas a moda; no concentraciones.

### `w_proporcion_clase_4`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 4 de wolframio; etiqueta local «1,33 - 2,27». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede acompañar sistemas hidrotermales relacionados con intrusiones; su asociación espacial con Au no exige correlación de concentraciones.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 17.15 % nulos; 129 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_w. Método registrado: proporciones alternativas a moda; no concentraciones.

### `w_proporcion_clase_5`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 5 de wolframio; etiqueta local «2,28 - 6,5». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede acompañar sistemas hidrotermales relacionados con intrusiones; su asociación espacial con Au no exige correlación de concentraciones.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 17.15 % nulos; 96 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_w. Método registrado: proporciones alternativas a moda; no concentraciones.

### `w_proporcion_clase_6`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Fracción del área válida asignada a clase 6 de wolframio; etiqueta local «6,51 - 473,61». No son unidades de concentración verificadas.

**Unidades:** fracción 0–1 del área válida.

**Por qué puede predecir o por qué se excluye:** Puede acompañar sistemas hidrotermales relacionados con intrusiones; su asociación espacial con Au no exige correlación de concentraciones.

**Límites:** Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.

**Datos observados:** 17.15 % nulos; 36 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** geoquimica_w. Método registrado: proporciones alternativas a moda; no concentraciones.

## Relieve — diccionario completo

### `elevacion_media_m`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Media de elevación del MDT nativo de 500 m, ponderada por área terrestre válida dentro de la celda de 1 km.

**Unidades:** m.

**Por qué puede predecir o por qué se excluye:** Contextualiza posición geomorfológica, exposición y nivel erosivo; puede también capturar diferencias regionales ajenas a mineralización.

**Límites:** Soporte regional: derivados nativos de 500 m promediados a 1 km. TPI/desviación requieren ≥95 % de vecinos válidos; sin relación universal creciente con Au.

**Datos observados:** 0.00 % nulos; 488,938 valores distintos no nulos. Rango o valores más frecuentes: -2.0 … 3317.0390625.

**Procedencia:** MDT banda 1. Método registrado: derivación nativa 500m; TPI z-media circular incluyendo centro; desviación poblacional; media terrestre a 1km.

### `pendiente_grados`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Media terrestre de pendientes calculadas a 500 m con diferencias centrales: atan(raíz(dx²+dy²)), convertida a grados.

**Unidades:** grados.

**Por qué puede predecir o por qué se excluye:** Aproxima inclinación y procesos de erosión/transporte; puede ayudar en modelos aluviales junto con otras variables. No mide pendiente de cauce.

**Límites:** Soporte regional: derivados nativos de 500 m promediados a 1 km. TPI/desviación requieren ≥95 % de vecinos válidos; sin relación universal creciente con Au.

**Datos observados:** 1.03 % nulos; 488,460 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 38.870479583740234.

**Procedencia:** MDT banda 1. Método registrado: derivación nativa 500m; TPI z-media circular incluyendo centro; desviación poblacional; media terrestre a 1km.

### `tpi_1000m_m`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Elevación menos media de vecinos en radio 1000 m, incluyendo el centro; luego media terrestre a 1 km. Positivo: alto relativo; negativo: bajo relativo.

**Unidades:** m.

**Por qué puede predecir o por qué se excluye:** Describe posición relativa en laderas, valles y divisorias; posible contexto de transporte y acumulación.

**Límites:** Soporte regional: derivados nativos de 500 m promediados a 1 km. TPI/desviación requieren ≥95 % de vecinos válidos; sin relación universal creciente con Au.

**Datos observados:** 1.51 % nulos; 486,734 valores distintos no nulos. Rango o valores más frecuentes: -232.2666778564453 … 236.5657196044922.

**Procedencia:** MDT banda 1. Método registrado: derivación nativa 500m; TPI z-media circular incluyendo centro; desviación poblacional; media terrestre a 1km.

### `desv_elevacion_1000m_m`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Desviación estándar poblacional de elevaciones en radio 1000 m; luego media terrestre a 1 km. Mide variabilidad del relieve; no es error del MDT ni TRI.

**Unidades:** m.

**Por qué puede predecir o por qué se excluye:** Resume contraste topográfico a esta escala; puede contextualizar erosión y relieve de cuenca sin identificar directamente Au.

**Límites:** Soporte regional: derivados nativos de 500 m promediados a 1 km. TPI/desviación requieren ≥95 % de vecinos válidos; sin relación universal creciente con Au.

**Datos observados:** 1.51 % nulos; 486,477 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 381.6034240722656.

**Procedencia:** MDT banda 1. Método registrado: derivación nativa 500m; TPI z-media circular incluyendo centro; desviación poblacional; media terrestre a 1km.

### `tpi_5000m_m`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Elevación menos media de vecinos en radio 5000 m, incluyendo el centro; luego media terrestre a 1 km. Positivo: alto relativo; negativo: bajo relativo.

**Unidades:** m.

**Por qué puede predecir o por qué se excluye:** Describe posición relativa en laderas, valles y divisorias; posible contexto de transporte y acumulación.

**Límites:** Soporte regional: derivados nativos de 500 m promediados a 1 km. TPI/desviación requieren ≥95 % de vecinos válidos; sin relación universal creciente con Au.

**Datos observados:** 4.08 % nulos; 475,496 valores distintos no nulos. Rango o valores más frecuentes: -865.5039672851562 … 846.810302734375.

**Procedencia:** MDT banda 1. Método registrado: derivación nativa 500m; TPI z-media circular incluyendo centro; desviación poblacional; media terrestre a 1km.

### `desv_elevacion_5000m_m`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Desviación estándar poblacional de elevaciones en radio 5000 m; luego media terrestre a 1 km. Mide variabilidad del relieve; no es error del MDT ni TRI.

**Unidades:** m.

**Por qué puede predecir o por qué se excluye:** Resume contraste topográfico a esta escala; puede contextualizar erosión y relieve de cuenca sin identificar directamente Au.

**Límites:** Soporte regional: derivados nativos de 500 m promediados a 1 km. TPI/desviación requieren ≥95 % de vecinos válidos; sin relación universal creciente con Au.

**Datos observados:** 4.08 % nulos; 473,529 valores distintos no nulos. Rango o valores más frecuentes: 0.15063178539276123 … 609.320068359375.

**Procedencia:** MDT banda 1. Método registrado: derivación nativa 500m; TPI z-media circular incluyendo centro; desviación poblacional; media terrestre a 1km.

## Hidrografía — diccionario completo

### `dist_cauce_m`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Distancia euclídea del centro de celda a la traza más próxima de cauce, buscada hasta 10000 m.

**Unidades:** m.

**Por qué puede predecir o por qué se excluye:** Contextualiza transporte y acumulación detrítica; para Au aluvial importan además fuente aguas arriba, conectividad y trampas sedimentarias.

**Límites:** NaN si no se encuentra traza en 10 km; no es distancia cero ni ausencia geológica. No se calcula desde el borde de la celda; la cobertura del levantamiento no está acreditada.

**Datos observados:** 2.72 % nulos; 480,443 valores distintos no nulos. Rango o valores más frecuentes: 0.0027415300719439983 … 9999.9609375.

**Procedencia:** hidrografia. Método registrado: centro a traza cartografiada; NaN sin traza dentro de 10000 m; cobertura no acreditada.

### `dens_aprox_cauce_1000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de cauce por superficie terrestre en una ventana de radio 1000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Contextualiza transporte y acumulación detrítica; para Au aluvial importan además fuente aguas arriba, conectividad y trampas sedimentarias. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 231,533 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 3.6718742847442627.

**Procedencia:** hidrografia. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

### `dens_aprox_cauce_5000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de cauce por superficie terrestre en una ventana de radio 5000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Contextualiza transporte y acumulación detrítica; para Au aluvial importan además fuente aguas arriba, conectividad y trampas sedimentarias. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 441,948 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.1030036211013794.

**Procedencia:** hidrografia. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

### `dens_aprox_cauce_10000m_km_km2`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Longitud aproximada de cauce por superficie terrestre en una ventana de radio 10000 m.

**Unidades:** km/km².

**Por qué puede predecir o por qué se excluye:** Contextualiza transporte y acumulación detrítica; para Au aluvial importan además fuente aguas arriba, conectividad y trampas sedimentarias. La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.

**Límites:** Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.

**Datos observados:** 0.00 % nulos; 478,660 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 0.7008928060531616.

**Procedencia:** hidrografia. Método registrado: longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia.

## Asociaciones litológicas — diccionario completo

### `unidades_granitoides_explicitos_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Suma de fracciones de unidades: Granitoides de dos micas; Otros granitoides. Fórmula: litologia_u011_fraccion + litologia_u015_fraccion.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Contexto granítico para evaluar sistemas relacionados con intrusiones; necesita edad, fertilidad y geoquímica compatibles.

**Límites:** Combinación determinista de fracciones existentes; no añade una medición independiente. No estima el porcentaje interno de cada roca.

**Datos observados:** 3.10 % nulos; 18,661 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: suma de unidades explícitas; no proporción interna de roca.

### `unidades_mixtas_con_granitoides_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Suma de fracciones de unidades: Migmatitas, mármoles y granitoides indiferenciados. Fórmula: litologia_u014_fraccion.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Unidad mixta de basamento y granitoides; puede aportar contexto térmico e intrusivo, pero no cuantifica cuánto granito contiene.

**Límites:** Duplicado exacto de una fracción original; elegir una representación. No estima el porcentaje interno de cada roca.

**Datos observados:** 3.10 % nulos; 1,840 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: suma de unidades explícitas; no proporción interna de roca.

### `unidades_volcanicas_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Suma de fracciones de unidades: Vulcanitas y rocas volcanoclásticas. Fórmula: litologia_u019_fraccion.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Contexto volcánico/volcanoclástico donde se pueden probar hipótesis hidrotermales; no informa sobre alteración ni fertilidad.

**Límites:** Duplicado exacto de una fracción original; elegir una representación. No estima el porcentaje interno de cada roca.

**Datos observados:** 3.10 % nulos; 5,324 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: suma de unidades explícitas; no proporción interna de roca.

### `unidades_basicas_ultrabasicas_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Suma de fracciones de unidades: Serpentinitas y peridotitas. Rocas básicas y ultrabásicas. Fórmula: litologia_u018_fraccion.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Contexto máfico y ultramáfico; permite probar controles del encajante y contrastes litológicos sin asumir asociación universal con Au.

**Límites:** Duplicado exacto de una fracción original; elegir una representación. No estima el porcentaje interno de cada roca.

**Datos observados:** 3.10 % nulos; 3,938 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: suma de unidades explícitas; no proporción interna de roca.

### `unidades_con_gneisses_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Suma de fracciones de unidades: Gneisses. Fórmula: litologia_u010_fraccion.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Representa basamento metamórfico; puede contextualizar zonas de cizalla y vetas, pero gneiss no equivale a roca aurífera.

**Límites:** Duplicado exacto de una fracción original; elegir una representación. No estima el porcentaje interno de cada roca.

**Datos observados:** 3.10 % nulos; 3,650 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: suma de unidades explícitas; no proporción interna de roca.

### `unidades_con_gravas_arenas_limos_fraccion`

**Rol y uso:** predictor_candidato; Candidata; no aprobada.

**Qué significa:** Suma de fracciones de unidades: Gravas, conglomerados, arenas y limos. Fórmula: litologia_u012_fraccion.

**Unidades:** fracción 0–1.

**Por qué puede predecir o por qué se excluye:** Hipótesis de transporte y acumulación detrítica de Au; la unidad incluye depósitos no auríferos y no distingue terrazas de otros sedimentos.

**Límites:** Duplicado exacto de una fracción original; elegir una representación. No estima el porcentaje interno de cada roca.

**Datos observados:** 3.10 % nulos; 68,905 valores distintos no nulos. Rango o valores más frecuentes: 0.0 … 1.0.

**Procedencia:** litologia. Método registrado: suma de unidades explícitas; no proporción interna de roca.

## Etiquetas — diccionario completo

### `n_candidatos`

**Rol y uso:** etiqueta; Excluir de X.

**Qué significa:** Número de registros de indicios candidatos asignados a la celda; puede haber varios del mismo depósito.

**Unidades:** conteo.

**Por qué puede predecir o por qué se excluye:** Sirve para construir y auditar la respuesta objetivo, no para explicarla.

**Límites:** Incluirla en X filtra información de la etiqueta. U significa no etiquetado, no ausencia de oro.

**Datos observados:** 0.00 % nulos; 7 valores distintos no nulos. Rango o valores más frecuentes: 0 … 9.

**Procedencia:** Fases C/D; código y configuración.

### `n_positivos_revisados`

**Rol y uso:** etiqueta; Excluir de X.

**Qué significa:** Número de registros con positivo_revisado verdadero asignados a la celda.

**Unidades:** conteo.

**Por qué puede predecir o por qué se excluye:** Sirve para construir y auditar la respuesta objetivo, no para explicarla.

**Límites:** Incluirla en X filtra información de la etiqueta. U significa no etiquetado, no ausencia de oro.

**Datos observados:** 0.00 % nulos; 1 valores distintos no nulos. Rango o valores más frecuentes: 0 … 0.

**Procedencia:** Fases C/D; código y configuración.

### `estado_etiqueta`

**Rol y uso:** etiqueta; Excluir de X.

**Qué significa:** P_revisado si n_positivos_revisados > 0; candidato_no_revisado si solo hay candidatos; U si no hay registros candidatos.

**Unidades:** categoría.

**Por qué puede predecir o por qué se excluye:** Sirve para construir y auditar la respuesta objetivo, no para explicarla.

**Límites:** Incluirla en X filtra información de la etiqueta. U significa no etiquetado, no ausencia de oro.

**Datos observados:** 0.00 % nulos; 2 valores distintos no nulos. Rango o valores más frecuentes: U: 496,164; candidato_no_revisado: 691.

**Procedencia:** Fases C/D; código y configuración.


## 9. Fuentes locales y trazabilidad

El directorio [ejecución de Fase D](../../reports/fase_d/20260923T211448_267684Z) contiene los productos examinados. Los principales son [maestro completo](../../reports/fase_d/20260923T211448_267684Z/Grid_Master_Au.parquet), [roles de columnas](../../reports/fase_d/20260923T211448_267684Z/column_roles.csv), [diccionario original de candidatas](../../reports/fase_d/20260923T211448_267684Z/feature_dictionary.csv), [lista de candidatas y aprobadas](../../reports/fase_d/20260923T211448_267684Z/feature_allowlist.json), [control de cierre](../../reports/fase_d/20260923T211448_267684Z/control_cierre.json), [configuración congelada](../../reports/fase_d/20260923T211448_267684Z/config_snapshot.json) y [soporte por conjunto](../../reports/fase_d/20260923T211448_267684Z/soporte_modelos.csv).

Las definiciones detalladas proceden de [código de extracción congelado](../../reports/fase_d/20260923T211448_267684Z/features_source.py), [construcción territorial](../../src/geoau/territory.py), [capas adicionales](../../src/geoau/additional_layers.py) y [selección y codificación para entrenamiento](../../src/geoau/training.py). Las fuentes externas de IGME y USGS están enlazadas junto al fundamento geológico correspondiente; sirven para contexto conceptual, no para validar el resultado del modelo español.

`control_informe.json` registra ejecución, recuentos, comprobaciones y hashes SHA-256 de los archivos usados. `redundancias_verificadas.csv` conserva las seis identidades de asociaciones. `generar_informe.py` y `contenido.md` permiten regenerar el documento con los listados adjuntos y la ejecución local. No se han modificado datos, etiquetas, listas de aprobación, configuración del modelo ni productos sellados de D. La comprobación no constituye una auditoría íntegra de todos los archivos del manifiesto de la ejecución ni una validación geológica de las fuentes.
