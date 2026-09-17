## 7. Notebook 03 — Geología y estructuras

Corresponde al núcleo de D, pasos 18–20. Utiliza [features.py](../../src/geoau/features.py), especialmente `geology` (líneas 311–357), `lines` (400–453) y las funciones de caché. Produce 49 variables geológicas y 24 estructurales, con calidad separada. Las seis asociaciones litológicas adicionales se incorporan en 06.

### 7.1. Ejecuciones, reutilización y coste

`ensure_run` intenta continuar una D compatible; si cambia configuración o código, inicia una nueva y busca bloques reutilizables. `context` comprueba fuentes externas, manifiesto C y sus productos cada vez que se invoca un bloque. `cached` acepta un bloque sólo si los archivos sellados conservan sus hashes. Este diseño es deliberadamente estricto y permite reproducibilidad, aunque reverificar repetidamente grandes productos produce coste de lectura considerable.

La equivalencia para reutilizar bloques se basa en una lista manual de funciones de cálculo convertidas a AST, parámetros relevantes y constantes. Ignora diferencias cosméticas como números de línea; no ignora cambios de algoritmos incluidos en la lista. Si una refactorización añade una dependencia nueva, debe actualizarse esa lista: no es un análisis automático completo del grafo de dependencias. Los ficheros importados que ya se congelan por hash se verifican adicionalmente.

### 7.2. Geología: área cartografiada, no composición mineral

La extracción efectiva emplea `Litologia` de la capa regional y `SISTEMA` de edades. Aunque C armoniza `recintos`, D no utiliza todavía sus unidades detalladas para el banco principal. `geology` enumera descripciones originales, asigna IDs ordenados y escribe diccionarios. En teselas de 100×100 celdas intersecta cada celda con la máscara y disuelve polígonos por categoría antes de medir superficies; así evita doble conteo de polígonos de la misma clase.

Para una celda terrestre de área A y categoría k calcula `f_k = área(unión de polígonos k ∩ celda ∩ máscara) / A`. La cobertura es el área de la unión de categorías dividida por A. El solape entre categorías se mide como la suma de sus áreas menos el área de la unión. Sólo admite celdas con al menos 95 % de área de atributo conocido y solape no mayor de `max(1 m², A·10⁻⁶)`.

Las fracciones se expresan sobre área terrestre total, por lo que pueden sumar entre aproximadamente 0,95 y 1 cuando se tolera una pequeña parte sin cartografía. No deben forzarse a sumar exactamente uno como las proporciones geoquímicas, cuyo denominador es el área válida. La clase dominante corresponde a mayor área, con desempate por descripción ordenada. Una unidad mixta conserva su descripción: no se inventa su porcentaje interno de granito, mármol u otra litología.

### 7.3. Estructuras: distancias y densidades

`structural_class` normaliza texto y excluye agua, bordes, límites, escombreras, cortas y símbolos. Separa falla/cizalla, cabalgamiento y contacto intrusivo, y divide cada grupo entre cartografiado y supuesto/oculto/inferido. El resultado son seis grupos. No utiliza todos los contactos, pliegues o medidas estructurales como predictores por el simple hecho de que existan archivos.

La distancia se calcula con `STRtree.query_nearest` desde el centro fijo de la celda a una traza, hasta 10 km. Un resultado sin traza en ese radio es `NaN`, acompañado por una bandera de calidad. Puede significar distancia superior al límite o falta de cartografía: el valor no permite distinguirlos. La distancia tampoco es la distancia mínima entre toda la superficie de la celda y la traza.

Para densidades, `line_lengths` disuelve trazas geométricamente coincidentes, mide longitud intersectada por celda y reparte líneas sobre bordes compartidos. Después `fftconvolve` aplica un círculo aproximado mediante pesos de intersección círculo–celda a radios de 1, 5 y 10 km. La fórmula es `densidad = 1.000 · Σ(w_j L_j) / Σ(w_j A_j)`, con L en metros y A en m², resultando km/km². Se utiliza área terrestre, no área de levantamiento acreditada. El reparto de longitud dentro de cada celda se considera uniforme: a 1 km de radio esta aproximación subcelda puede ser especialmente relevante.

@@CELL 03 1 Inicio o continuación de D

Busca la raíz por la existencia de `features.py`, importa pandas, gráficos y el módulo, lo recarga y llama a `ensure_run`. `reload` permite que el kernel vea cambios de código, mientras los hashes determinan si puede continuar el mismo producto. El resultado guardado informa reutilización de cinco bloques compatibles. Recargar un módulo no equivale por sí mismo a validar los datos; la comprobación de entradas ocurre en `context` al ejecutar las funciones de bloque.

@@CELL 03 3 Variables geológicas

`fd.geology` carga un bloque sellado o ejecuta las intersecciones y los criterios anteriores. Devuelve `geology` con `cell_id` y predictores y `geology_quality` con cobertura, solapes y ausencia de atributos. `head()` puede mostrar filas sin valores al comienzo geográfico de la rejilla; eso no significa que toda la geología esté vacía. `describe()` de calidad permite evaluar distribución de soporte pero no valida las equivalencias de las unidades.

@@CELL 03 4 Ejemplo comentado de lectura de calidad geológica

Todas las líneas están comentadas: no se importa PyArrow ni se lee el archivo de la ruta antigua. El fragmento muestra un intento de inspeccionar un Parquet y filtrar sumas numéricas positivas. Esa suma no sería un criterio geológico general, porque mezcla cantidades distintas. La ruta absoluta pertenece a una ejecución histórica; al quedar inactiva no condiciona la ejecución actual, pero convendría sustituirla por una ruta basada en `RUN` si se reutiliza.

@@CELL 03 5 Ejemplo comentado de calidad estructural

También es una celda sin instrucciones ejecutables. Contiene una ruta absoluta de un producto estructural antiguo y un ejemplo de lectura/conversión a pandas. Se contabiliza como celda de código del notebook, pero no produce variables ni diagnósticos en una ejecución completa.

@@CELL 03 7 Variables estructurales

`fd.lines(ROOT, RUN)` usa por defecto la única fuente estructural admitida, GEODE, con seis grupos y cuatro variables por grupo: una distancia y tres densidades. Esta decisión evita sumar directamente copias GEODE/MAGNA, aunque no resuelve desplazamientos o duplicación imperfecta dentro de una misma fuente. La tabla descriptiva muestra distribución y faltantes; por ejemplo, las distancias pueden tener menos observaciones que las densidades porque la búsqueda se limita a 10 km y la densidad cartografiada permite cero.

@@CELL 03 8 Diccionario estructural y continuidad

Muestra `dictionaries/estructuras.csv`, que relaciona descripción original, número de entidades y grupo asignado. Éste es el punto de revisión semántica de reglas textuales: encontrar `Falla` no acredita por sí mismo certeza geométrica ni cobertura suficiente. El mensaje final indica la ejecución que debe continuar 04. No realiza nuevos cálculos ni aprueba las reglas.

### 7.4. Limitaciones específicas

Los pasos de estructuras avanzadas —orientaciones axiales, intersecciones topológicas, distancias a pliegues y estadísticas de buzamiento— permanecen pendientes. La fuente geológica regional puede limitar capacidad de detectar controles más finos. Las asociaciones y fracciones originales redundantes elevan el número de columnas respecto al presupuesto inicial de 25–50 del plan. La revisión ha reproducido un caso sintético de borde costero donde `line_lengths`, al recibir el borde del rectángulo global, reparte la mitad de una traza sobre el borde de la única celda terrestre; se detalla en hallazgos, sin extrapolar su magnitud a todo el territorio.

## 8. Notebook 04 — Geoquímica por clases y control RGB

Desarrolla el paso 21; el 22, mejora con datos analíticos cuantitativos, sigue pendiente. [features.py](../../src/geoau/features.py), líneas 456–546, lee paletas, comprueba color, agrega clases y registra calidad. Genera 79 variables: nueve modas y 70 proporciones de clases. F selecciona una representación por elemento dentro de cada conjunto de variables.

### 8.1. Procedencia y control de clasificación

Los scripts históricos descargaron mapas renderizados y asignaron a cada píxel visible el color de paleta más cercano. Las bandas de valores representativos, límites y clases provienen de esa misma asignación; no son cuatro mediciones independientes. `local_palettes` extrae las constantes mediante `ast.literal_eval` sin importar ni ejecutar los scripts de descarga. Esto evita efectos secundarios y preserva la paleta utilizada, pero una paleta local coherente todavía requiere contraste con la leyenda oficial.

`color_quality` calcula distancia euclídea RGB entre el píxel y el color de su clase declarada. El píxel se acepta si es visible, tiene clase entera válida, distancia ≤2 y una separación de al menos 10 respecto a la segunda clase más cercana; además la clase declarada debe ser la más cercana. El control examina colores únicos para limitar memoria. Con cuatro bandas exige alfa 255. Clase cero sigue siendo válida.

Las clases aceptadas se agregan de 500 m a 1 km ponderando por tierra. Se publican predictores sólo si la fracción RGB válida alcanza 95 %. Las proporciones suman uno sobre el área válida; no describen incertidumbre de concentración dentro de los intervalos. La comparación de tolerancias 0, 2 y 8 es un diagnóstico: la configuración no acepta automáticamente las discrepancias de ocho niveles detectadas en Zn/W.

@@CELL 04 1 Recuperación de ejecución y versiones adicionales

Carga el módulo D y recupera `current_run`, que exige coincidencia del YAML con el snapshot. Escribe `environment_fase_d.json` con versiones de NumPy, SciPy y PyArrow. Esa escritura aporta trazabilidad, pero después del cierre D el archivo puede estar incluido en el manifiesto: reejecutar esta celda con versiones distintas puede modificar un archivo sellado y hacer fallar controles posteriores. La respuesta correcta sería iniciar una ejecución nueva, no cambiar el sello para ocultar la diferencia.

@@CELL 04 2 Extracción y auditoría RGB

Ejecuta o recupera `geochemistry` y muestra `geoquimica_rgb_qc.csv`. El informe registra píxeles válidos originales, aceptados/rechazados, diferencias de moda respecto a C, celdas con soporte suficiente y que la leyenda oficial aún no está validada. Se escriben TIFF de clases/proporciones controladas y tablas de predictores/calidad. El cambio de cobertura respecto a 02 es deliberado: C comprobaba máscaras y códigos, mientras D exige además consistencia del color.

@@CELL 04 3 Inspección de predictores y calidad

Muestra primeras filas del banco geoquímico y estadísticas de la tabla de calidad. Una celda puede tener valores de algunos elementos y `NaN` en otros. Las columnas de proporciones no deben incorporarse junto a la moda del mismo elemento por defecto: representan la misma evidencia con distinta agregación. La selección efectiva se determina después en `training.feature_sets`.

@@CELL 04 4 Filtrado visual correcto de presencia de datos

Identifica columnas cuyo nombre termina en `_modal` y construye `df_limpio` con filas que tienen al menos una moda no nula. Usa `notna()` y no `>0`, de modo que conserva la clase cero. Es una vista alternativa y no sustituye el objeto `geochemistry` que se integra en 06. Tener al menos un elemento presente tampoco equivale a cumplir el soporte `eligible_geo4`, que exige los cuatro elementos seleccionados.

@@CELL 04 5 Histogramas de clases

Dibuja un histograma de cada moda con ocho bins y ajusta la figura. Permite reconocer distribución y clases dominantes en las celdas con valor. Para códigos discretos serían más explícitas barras por clase con límites alineados; ocho bins comunes no coinciden necesariamente con los siete niveles de Au/W. El gráfico cuenta celdas, no estaciones analíticas ni depósitos. No evalúa normalidad de concentraciones químicas reales.

### 8.2. Lectura geológica

Una anomalía cartográfica de sedimentos puede estar relacionada con transporte y fuentes aguas arriba. Este bloque no modela cuencas, procedencia de sedimento ni contaminación histórica. Utilizar Au externo no demuestra por sí solo fuga de etiquetas; exige estudiar la procedencia de la capa y sus relaciones con los indicios. La ablación con/sin Au ayuda a medir dependencia predictiva, pero no sustituye esa revisión.

## 9. Notebook 05 — Relieve e hidrología

Desarrolla el paso 23 y la base del 24; la geofísica del paso 25 y la hidrología aluvial detallada quedan pendientes. Calcula seis variables de relieve y cuatro hidrográficas en [features.py](../../src/geoau/features.py).

### 9.1. Fórmulas reales del relieve

La pendiente se deriva en la malla nativa de 500 m. Para píxel p, `dz/dx = (z_este − z_oeste)/(2p)` y análogamente en y. La pendiente en grados es `atan(sqrt((dz/dx)² + (dz/dy)²)) · 180/π`. Se exige centro y los cuatro vecinos finitos, por propagación de NaN y máscara. El signo norte/sur del gradiente no afecta a la magnitud de pendiente.

Para radios de 1 y 5 km se construye un disco de **centros** de píxeles, incluido el centro. Se calcula número de píxeles válidos, suma de alturas y suma de cuadrados mediante convolución. `TPI = z_centro − media_vecindario`; `desv_elevacion = sqrt(max(0, media(z²) − media(z)²))`. La segunda magnitud es desviación típica poblacional de elevaciones, no el índice TRI de otro algoritmo. Se exige al menos 95 % de los centros nominales del disco válidos y centro válido.

El cero que aparece en la suma de la convolución sólo sirve para anular términos inválidos; el denominador cuenta datos válidos. Por tanto, no se interpreta como elevación cero en océano o huecos. Después las derivadas de 500 m se agregan con media ponderada por área terrestre válida a 1 km y se exige nuevamente soporte ≥95 %. Cerca de costa y frontera, enmascarar a tierra española antes del cálculo reduce el soporte de vecindarios aunque el MDT tuviera alturas al otro lado de la frontera.

@@CELL 05 1 Contexto de D

Importa el módulo y recupera la ejecución actual según el YAML. Debe ser la misma iniciada por 03. Esta celda no abre el MDT ni recalcula relieve. Los bloques invocados después harán la verificación profunda de entradas y podrán reutilizar productos ya sellados.

@@CELL 05 2 Cálculo de relieve

`fd.terrain` lee exclusivamente la banda de elevación del MDT original, verifica rejilla y máscaras y reconstruye las seis variables mediante las fórmulas anteriores. No reutiliza las bandas derivadas históricas de pendiente/TPI/TRI. Devuelve predictores y fracciones válidas y guarda TIFF por variable. La tabla descriptiva resume media, dispersión y límites; que la elevación media tenga dato en toda la malla no implica que TPI de 5 km lo tenga, por sus requisitos de vecindario.

@@CELL 05 3 Cálculo hidrográfico

`fd.lines(..., hydro=True)` activa el mismo motor espacial de distancias y longitud/área para el grupo único `cauce`. Produce distancia al cauce hasta 10 km y densidades aproximadas a 1, 5 y 10 km. La red es la capa hidrográfica disponible, con sus posibles omisiones de cabeceras y tramos; el resultado no equivale a distancia al drenaje real completo. No calcula dirección de flujo, acumulación, cuencas, terrazas ni altura relativa al cauce.

@@CELL 05 4 Calidad de relieve y continuidad

Muestra estadísticas de las fracciones válidas de cada variable y señala que la integración corresponde a 06. La calidad se mantiene fuera de X y permite localizar dónde faltan vecinos o datos. No imprime `hydrology_quality` aquí, aunque el objeto existe y se incorpora posteriormente; los indicadores hidrográficos de falta de traza y cobertura de levantamiento continúan siendo relevantes.

### 9.2. Alcance del modelo aluvial

Relieve regional y proximidad al cauce pueden formar parte de una referencia general, pero no realizan el modelo aluvial descrito en el plan. Faltan diferenciación de terrazas, MDT de detalle, acondicionamiento hidrológico y agrupación por cuencas. La configuración F usa el objetivo general. Las categorías roca/aluvial propuestas en B no acreditan dos modelos específicos ejecutados.

## 10. Notebook 06 — Matriz, roles y cierre técnico

Implementa el paso 26 y cierre técnico D. Su función central es `assemble`, líneas 677–772 de [features.py](../../src/geoau/features.py). Une cinco bloques, añade seis asociaciones litológicas y separa predictores, calidad y etiquetas.

### 10.1. Contrato de integración

El banco queda compuesto por 49 variables geológicas, 24 estructurales, 79 geoquímicas, seis de relieve, cuatro de hidrología y seis asociaciones: **168**. Las asociaciones agrupan descripciones explícitas de granitoides, unidades mixtas con granitoides, volcanitas, rocas básicas/ultrabásicas, gneises y gravas/arenas/limos. Son fracciones de unidades cartográficas, no estimaciones de mineralogía interna. Algunas duplican o suman fracciones ya presentes, lo que debe considerarse en regularización e interpretación de importancias.

Las uniones se validan como 1:1 por `cell_id`. Se exige que todos los bloques cubran la misma rejilla y que sus nombres no colisionen. `validate_matrix` rechaza IDs inválidos, infinitos, fracciones fuera de rango, distancias/densidades negativas, pendientes imposibles y proporciones geoquímicas incompletas o no normalizadas. Las tablas de indicios se conservan aparte y sus conteos se agregan por celda.

`X_features.parquet` incluye predictores candidatos y `cell_id`; **la clave debe retirarse antes de entrenar**, como hace F. `calidad_y_soporte.parquet` reúne auxiliares y máscaras; `etiquetas_por_celda.parquet` distingue `P_revisado`, `candidato_no_revisado` y `U`. El maestro completo combina estos papeles, por lo que no puede pasarse entero a un clasificador.

`partition_id = row // 100` crea bandas de almacenamiento. El fichero monolítico y cada partición se escriben con temporal y reemplazo atómico. Esa partición no está diseñada como fold espacial de evaluación. El diccionario de roles lo marca como auxiliar.

@@CELL 06 1 Recuperación de ejecución

Importa el módulo D y recupera el mismo `RUN` de 03–05. No reconstruye por sí solo bloques faltantes. La secuencia debe haber generado o recuperado geología, estructuras, geoquímica, relieve e hidrología antes de llamar a integración.

@@CELL 06 2 Ensamblado y control de cierre

`assemble` verifica entradas y, si D ya está sellada, comprueba el manifiesto y devuelve los tres Parquet existentes. Si no está cerrada, integra bloques, asociaciones, etiquetas, roles, soporte, diccionarios y manifiesto. La salida observada son 496.855 celdas y 168 variables candidatas. `approved_training_columns` se escribe vacío y las banderas científicas permanecen falsas: la terminación técnica acredita la matriz y su estructura, no aprueba el entrenamiento científico.

@@CELL 06 3 Faltantes, estados de etiqueta y ampliaciones

Ordena `variables_qc.csv` por fracción faltante, muestra los estados de etiqueta y lee `pending_extensions.json`. Las distancias a contactos intrusivos supuestos presentan un faltante especialmente alto. Es importante distinguir no encontrar una traza en 10 km de no tener la fuente; la imputación posterior no resolverá esa ambigüedad semántica. El JSON de ampliaciones documenta geofísica, estructuras avanzadas, aluvial, leyendas y cobertura pendientes.

@@CELL 06 4 Soporte de modelos, roles y particiones Parquet

Muestra cuántas celdas y candidatos cumplen cada combinación de soporte, cuenta roles del maestro y lee sólo la partición 0 de `Grid_Master_Au`. El filtro Parquet reduce lectura sin cambiar la definición de los datos. En la salida hay 168 predictores, 73 auxiliares, tres columnas de etiqueta y una clave. El nombre `partition_id` identifica almacenamiento; reutilizarlo como CV sería una decisión nueva ajena al diseño E.

@@CELL 06 6 Mapa de pendiente como revisión espacial

Une coordenadas auxiliares y pendiente mediante `validate='one_to_one'`, representa todos los centros con color y mantiene escala métrica igual. Las coordenadas sólo sirven para dibujo y no se agregan a X. El mapa permite detectar huecos y discontinuidades, pero una figura continua y plausible no confirma los procesos geológicos ni la exactitud del MDT. El título evita interpretarlo como prospectividad.

@@CELL 06 7 Verificación final de productos

Recalcula los hashes de todos los productos listados en `outputs_manifest.json`. Si un archivo ha cambiado o desaparecido, `verify_records` lanza un error. Es un control de integridad de la ejecución D, independiente de las estadísticas o del mapa anteriores. El mensaje de productos verificados no es una autorización de producción: esa decisión continúa bloqueada en los propios archivos de control.

### 10.2. Selección de soporte y posible sesgo

`eligible_geology_terrain` exige elegibilidad costera y datos de litología dominante, edad dominante, elevación y pendiente. No exige que todas las variables de TPI o distancias estén presentes. `eligible_geo4` añade Au/As/Sb/Bi; `eligible_geo9` añade los nueve elementos. Los faltantes restantes podrán imputarse dentro del entrenamiento. Escoger este territorio condiciona el problema que se evalúa: los resultados no deben aplicarse silenciosamente a celdas que fueron descartadas por cobertura.
