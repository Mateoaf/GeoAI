# Qué significa cada variable de Grid Master Au y qué puede aportar a la predicción

Informe del 25 de septiembre de 2026. Proyecto GeoAI. Ámbito: componente continental principal de la España peninsular, según la máscara regional candidata del proyecto. Ejecución examinada: `reports/fase_d/20260923T211448_267684Z`.

## 1. Resultado principal y alcance del análisis

**Grid Master Au contiene 245 columnas y 496.855 filas, una por celda terrestre de 1 × 1 km. De esas columnas, 168 son predictoras candidatas, 73 son auxiliares, 3 son etiquetas y 1 es la clave de celda. Actualmente hay 0 predictores aprobados para entrenamiento validado.**

El primer listado proporcionado coincide, en nombre y orden, con `Grid_Master_Au.parquet`. El segundo coincide con `X_features.parquet`: incluye `cell_id` y las 168 candidatas. Por tanto, las 169 columnas del segundo listado no son 169 predictores; `cell_id` solo identifica y enlaza las filas.

La palabra **predictora** tiene aquí dos sentidos que conviene separar. Una variable candidata representa una observación que podría ayudar a anticipar mineralización: por ejemplo, cercanía a estructuras que pudieron conducir fluidos. Una variable con capacidad predictiva demostrada mejora la predicción en territorios independientes, con etiquetas apropiadas y controles de sesgo. Este informe acredita el significado y la construcción de las candidatas; no demuestra esa segunda condición.

La ejecución registra 789 indicios candidatos asignados a 691 celdas y **0 celdas con positivos revisados**. `approved_training_columns` está vacío, `prediction_allowed` es falso y el cierre científico de D es falso. No se han entrenado nuevos modelos ni calculado importancias o correlaciones con candidatos sin revisar: no serían prueba suficiente de utilidad científica. Los datos permiten estudiar prospectividad regional, pero no estimar directamente ley de Au, tonelaje, reservas ni rentabilidad.

Se han leído el Parquet real, los diccionarios, las reglas de construcción y la configuración congelada. Se han recalculado los nulos y valores distintos de cada columna; para las 168 candidatas coinciden con `variables_qc.csv`. El código `features_source.py` guardado en D coincide por SHA-256 con `src/geoau/features.py` en el momento del análisis. Se priorizan estos productos frente a documentación anterior que describe otra estructura del maestro.

{{FAMILIAS}}

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

{{SOPORTE}}

Pasar de `eligible_geo4` a `eligible_geo9` reduce el universo de 472.548 a 288.822 celdas: se pierden 183.726, un 38,88 % del soporte de geo4. Los registros candidatos cubiertos pasan de 755 a 525. Una comparación de rendimiento entre ambos conjuntos confundiría cambio de variables con cambio de territorio si no se realiza además sobre soporte común. Estas banderas no exigen que todas las distancias estructurales o todas las derivadas de relieve estén completas.

**Las distancias tienen nulos con una interpretación específica:** falla cartografiada 18,90 %, falla supuesta 30,21 %, cabalgamiento cartografiado 55,69 %, supuesto 80,06 %, contacto intrusivo cartografiado 69,96 % y supuesto 98,00 %. Cauces: 2,72 %. No encontrar traza dentro de 10 km es parte de la definición del NaN, junto con la limitación de cobertura. La distancia a contacto intrusivo supuesto tiene muy poco soporte observado; requiere especial cautela antes de imputar y atribuir significado.

**Las asociaciones litológicas no añaden mediciones nuevas.** Se verificaron fila a fila las siguientes identidades, incluidos los nulos. Cinco son duplicados exactos de una sola fracción; la de granitoides explícitos es una suma determinista.

{{REDUNDANCIAS}}

{{DUPLICADO_CRUZADO}}

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

{{LEYENDAS}}

## 8. Cómo utilizar el diccionario completo

Las fichas siguientes explican individualmente las 245 columnas. Cada ficha incluye significado, unidades, papel predictivo o razón de exclusión, limitaciones y estadísticas recalculadas sobre las 496.855 filas. Los valores distintos excluyen nulos. Los rangos son observados, no límites teóricos; para categorías se muestran los cuatro valores más frecuentes, que pueden incluir nulos.

Todas las fichas de candidatas describen **posible utilidad**, sin asignar importancia empírica demostrada ni signo obligatorio de efecto. El CSV `diccionario_245_variables.csv` permite filtrar y comparar estas mismas fichas en una hoja de cálculo. El HTML dispone de búsqueda y de impresión a PDF; todos sus contenidos funcionan sin conexión.

{{DICCIONARIO}}

## 9. Fuentes locales y trazabilidad

El directorio [ejecución de Fase D](../../reports/fase_d/20260923T211448_267684Z) contiene los productos examinados. Los principales son [maestro completo](../../reports/fase_d/20260923T211448_267684Z/Grid_Master_Au.parquet), [roles de columnas](../../reports/fase_d/20260923T211448_267684Z/column_roles.csv), [diccionario original de candidatas](../../reports/fase_d/20260923T211448_267684Z/feature_dictionary.csv), [lista de candidatas y aprobadas](../../reports/fase_d/20260923T211448_267684Z/feature_allowlist.json), [control de cierre](../../reports/fase_d/20260923T211448_267684Z/control_cierre.json), [configuración congelada](../../reports/fase_d/20260923T211448_267684Z/config_snapshot.json) y [soporte por conjunto](../../reports/fase_d/20260923T211448_267684Z/soporte_modelos.csv).

Las definiciones detalladas proceden de [código de extracción congelado](../../reports/fase_d/20260923T211448_267684Z/features_source.py), [construcción territorial](../../src/geoau/territory.py), [capas adicionales](../../src/geoau/additional_layers.py) y [selección y codificación para entrenamiento](../../src/geoau/training.py). Las fuentes externas de IGME y USGS están enlazadas junto al fundamento geológico correspondiente; sirven para contexto conceptual, no para validar el resultado del modelo español.

`control_informe.json` registra ejecución, recuentos, comprobaciones y hashes SHA-256 de los archivos usados. `redundancias_verificadas.csv` conserva las seis identidades de asociaciones. `generar_informe.py` y `contenido.md` permiten regenerar el documento con los listados adjuntos y la ejecución local. No se han modificado datos, etiquetas, listas de aprobación, configuración del modelo ni productos sellados de D. La comprobación no constituye una auditoría íntegra de todos los archivos del manifiesto de la ejecución ni una validación geológica de las fuentes.
