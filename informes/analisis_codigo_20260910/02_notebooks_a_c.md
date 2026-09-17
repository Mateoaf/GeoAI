## 4. Notebook 00 — Configuración y fuentes locales

Corresponde a la fase A, pasos 01–06 del plan. Recibe los archivos originales y `config/project.yaml`; entrega un inventario con hashes, un catálogo, diagnósticos de lectura y una especificación todavía candidata. Su centro funcional es [local_sources.py](../../src/geoau/local_sources.py).

### 4.1. Qué hace el módulo que utiliza

`local_path` resuelve rutas dentro de la raíz y rechaza URL o escapes hacia otros directorios. `discover_sources` reúne las extensiones configuradas de la raíz y la carpeta hidrográfica; no incorpora recursivamente los productos de `reports/`. `sha256_file` lee bloques de 8 MiB para identificar el contenido sin cargar todo el archivo en memoria.

`gpkg_info` consulta `gpkg_contents` y `gpkg_geometry_columns` mediante SQLite en lectura. Cuenta filas y registra esquemas; no valida todas las geometrías. `read_table` conserva atributos como texto, incluidos ceros iniciales, vacíos y el literal `NA`. `read_vector` exige autorización explícita para una carga completa y para la conversión preliminar de curvas; cuando recibe `bbox`, transforma sus límites desde el CRS declarado al de la capa.

`inspect_source` distingue inspección de GPKG, TIFF, CSV, Excel, shapefiles, QGIS y ZIP. Captura excepciones por fuente y las registra como `error`, sin convertirlas en una falsa carga válida. Los TIFF se resumen mediante metadatos y una vista reducida: no se realiza aquí una auditoría estadística exhaustiva. El control final repite la verificación de originales para detectar cambios durante la lectura.

@@CELL 00 2 Entorno, raíz e importaciones

Comprueba que los paquetes enumerados puedan localizarse con `find_spec`; si falta alguno, interrumpe antes del inventario. Busca la raíz entre el directorio actual y sus ancestros, con una alternativa histórica llamada `Proyecto Con Luis`. Añade `src` al principio de `sys.path` para importar el paquete local, carga el YAML y muestra versiones. `PROJECT_ROOT_OVERRIDE` permite resolver aperturas desde otra carpeta. La comprobación inicial no incluye todos los paquetes usados después —por ejemplo NumPy— ni acredita compatibilidad binaria; las importaciones y pruebas posteriores completan parcialmente ese control. No instala dependencias.

@@CELL 00 4 Especificación y descubrimiento de archivos

`json_normalize(...).T` transforma las decisiones anidadas de ámbito y diseño en una tabla vertical. `discover_sources` obtiene las rutas y `stat().st_size` suma su volumen; `value_counts` cuenta formatos. Son magnitudes calculadas sobre el contenido descubierto, no cifras pegadas desde el plan. La salida histórica informa 93 archivos. El listado sólo describe disponibilidad local: un archivo existente puede estar vacío, ser únicamente visual o carecer de geometría.

@@CELL 00 6 Inventario completo y hashes

Activa explícitamente `compute_sha256=True`, recorre las fuentes con `inventory` y aplana sus metadatos mediante `catalog_frame`. La tabla separa ruta, papel, estado, filas y bytes; el agrupamiento final muestra cuántos archivos tienen cada estado. Leer hashes tiene coste de disco proporcional al volumen de las fuentes, aunque las previsualizaciones sean pequeñas. El parámetro puede ponerse a falso para explorar, pero B requiere una A satisfactoria con hashes completos; no sería una sustitución equivalente del procedimiento reproducible.

@@CELL 00 8 Fuentes canónicas candidatas e incidencias

Construye `por_ruta` para consultar rápidamente el inventario y `fuentes` para traducir alias como `contactos_geode` a nombres reales. Después comprueba existencia y estado de cada candidata, y muestra archivos vacíos, errores y XML auxiliares sin TIFF. `errores_lectura` se conserva para el cierre. Que `IndiciosII.gpkg` sea la fuente canónica candidata significa que las siguientes fases parten de ella; no declara resueltas sus discrepancias con CSV y Excel.

@@CELL 00 10 Carga de las tres copias de indicios

Carga la geometría completa del GPKG y lee CSV/Excel como texto. Conserva tres objetos separados y calcula filas, códigos únicos y CRS. Esto evita que versiones sucesivas de los mismos indicios se sumen como observaciones independientes. La impresión con `repr` del primer código sirve para comprobar que se mantienen ceros iniciales. Las diferencias de unicidad que aparecen aquí explican por qué una unión o concatenación ingenua multiplicaría la evidencia.

@@CELL 00 12 Vectores completos moderados y muestras de capas grandes

Carga litología y edades completas sólo si el recuento inventariado no supera `max_full_vector_features`. Para cada capa interna de cada GPKG no vacío obtiene cinco registros de atributos con `read_geometry=False`, lo que evita convertir curvas durante ese muestreo. Añade cien geometrías hidrográficas. Se separan así cargas completas de tablas manejables y lecturas parciales de capas millonarias. Las primeras filas de una capa no constituyen una muestra representativa de todos sus tipos o territorios.

@@CELL 00 13 Visualización del diccionario de muestras

Muestra `muestras_vectores`, creado en la celda anterior. No transforma ni persiste información. Es una celda exploratoria que puede producir una salida muy extensa; su utilidad es inspeccionar nombres y atributos. No sustituye una comprobación sistemática de tipos, nulos, dominios y geometrías completas.

@@CELL 00 15 Prueba de transformación y previsualización de curvas

Transforma el punto de longitud −3°, latitud 40° de EPSG:4326 a EPSG:25830 con `always_xy=True`. Comprueba que el meridiano central produce aproximadamente 500.000 m de este y un norte plausible. Después autoriza una muestra de cinco curvas GEODE y comprueba que el lector devuelve datos con CRS. Finalmente lee un recorte de indicios con `bbox_crs` explícito. Son pruebas de funcionamiento del entorno, no selección del piloto ni certificación nacional de la conversión de curvas.

@@CELL 00 16 Segunda muestra de contactos

Lee cien entidades de contactos con geometría y conversión de curvas permitida. Amplía la inspección visual de la celda anterior; no crea una capa armonizada ni calcula distancias. `display(contactos.head())` sólo muestra cinco filas de las cien cargadas. Repetir la celda vuelve a leer la fuente, sin modificarla.

@@CELL 00 18 Tablas de muestra y lectura por bloques

Genera una muestra de cinco filas para cada CSV y Excel legible, respetando la codificación y separador del YAML. Resume columnas y tamaño de muestra. Después abre `ContactosFallasMagna50.csv` como lector por bloques y extrae el primero, de mil filas, dentro de un gestor de contexto que cierra el recurso. Este bloque demuestra lectura escalable; no cuenta aquí toda la tabla ni recupera geometría desde los atributos tabulares.

@@CELL 00 20 Metadatos de bandas y ventanas de ráster

Reúne rutas de TIFF legibles y crea una fila descriptiva por banda: índice, descripción, CRS, resolución, NoData y uso previsto. Genera vistas reducidas de Au y elevación y una ventana nativa de 128×128 píxeles con cuatro bandas de Au. `compressed()` elimina elementos enmascarados para enumerar clases visibles. La vista usa vecino más próximo y sirve para inspección; las clases observadas en ella pueden no incluir todas las clases del ráster original.

@@CELL 00 21 Figura de geoquímica y elevación

Representa las dos vistas reducidas con la extensión espacial de sus metadatos, dos paletas y barras de color. `origin='upper'` refleja el orden de filas de los rásteres. El eje se rotula como EPSG:25830 de forma literal: convendría derivar esa etiqueta del CRS comprobado si se amplía el lector a fuentes distintas. El mapa de Au visualiza códigos de clases, aunque la barra continua de colores pueda sugerir otra lectura; no es un mapa de concentraciones analíticas ni de prospectividad.

@@CELL 00 22 Inspección específica del shapefile hidrográfico

Construye de nuevo un diccionario de muestras de shapefiles y accede al nombre exacto `red-hidrografica2022-27_marzo2023.shp`. Imprime sus geometrías. La celda fallaría con `KeyError` si cambiase el nombre o no existiera esa fuente, aunque el descubrimiento general funcionase. El comentario pide que la geometría no se corte, pero `geometry.head()` no configura por sí mismo una impresión íntegra de WKT; el resultado sigue sujeto al formato de visualización de pandas/GeoPandas.

@@CELL 00 24 Shapefiles y referencias QGIS

Repite las muestras de shapefile, muestra sus CRS y primeras filas y reúne referencias extraídas del QGZ. `inspect_qgis` abre el ZIP y el XML local, sin consultar servicios. El filtro `local_exists.eq(False)` identifica rutas locales rotas; los servicios remotos se registran con existencia local no aplicable. Es un diagnóstico de referencias: la visibilidad de una capa remota en QGIS no significa que sus datos cuantitativos estén descargados.

@@CELL 00 26 Escritura de informes de A

`write_reports` crea una carpeta de ejecución bajo el directorio configurado y escribe manifiesto, catálogo, configuración, entorno y pendientes. También congela todas las distribuciones instaladas en `environment.freeze.txt` y registra un hash de los tipos/fuentes de las celdas de 00, excluyendo outputs y metadatos de ejecución. Esta celda añade resumen de indicios, bandas, fuentes canónicas y la figura previamente creada. `RUN_DIR` identifica el producto que podrán consumir las fases siguientes. Los pendientes proceden de la configuración y pueden necesitar actualización cuando se recuperan nuevas fuentes: no son una comprobación automática de todas las necesidades científicas.

@@CELL 00 28 Integridad y cierre de carga

Reverifica tamaño, fechas y hashes conforme a `verify_unchanged`, construye `control_cierre.json` y exige que no haya originales modificados ni errores de lectura. `hashes_completos` informa si todas las fuentes están identificadas por contenido. Mantiene expresamente sin realizar la limpieza geológica y sin descargas remotas. La salida habilita la carga de B, pero no significa que se hayan resuelto licencias, revisión de leyendas, geometría completa o ámbito del piloto.

### 4.2. Relación con el plan

La fase A implementa bien el inventario local, la trazabilidad y los lectores. La especificación geológica y el piloto continúan pendientes. El paso 06 se ha concretado principalmente como registro de carencias y catálogo de entradas; el notebook no ejecuta un proceso de recuperación remota. Los archivos añadidos posteriormente se reconocen mediante nuevos inventarios, por lo que los nueve GPKG vacíos de la auditoría de septiembre 5 no describen el estado de septiembre 8.

## 5. Notebook 01 — Indicios, limpieza y etiquetas

Corresponde a B, pasos 07–12. Parte de una A satisfactoria y de `config/labels.yaml`. Produce conciliación, inventario normalizado, cuarentena, candidatos, relaciones de proximidad y plantilla de revisión. El módulo [labels.py](../../src/geoau/labels.py) conserva evidencia original y evita declarar negativos geológicos.

### 5.1. Lógica de etiquetas y dependencia

`normalize` aplica Unicode NFKC, reduce espacios y trata una lista explícita de tokens nulos. `key` elimina acentos y diferencias de mayúsculas para comparar. `substance_tokens` separa coma, punto y coma y barra vertical; no separa `/` porque puede formar parte de una descripción mineral. Au se reconoce por igualdad exacta con `oro`/`au`, evitando coincidencias parciales.

`normalize_indicios` conserva atributos con sufijo `_raw`, WKT y CRS original. Reproyecta a 4326 y asigna `record_id = gpkg:<hash de fuente>:<fila>`. Es estable para esa copia y orden de lectura, no un identificador geológico universal. La morfología `Filoniana` sugiere roca y `Aluvionar` sugiere aluvial; otras morfologías quedan desconocidas y ninguna se declara automáticamente orogénica.

`geometry_qc` comprueba punto válido, coordenadas finitas, rangos y ventanas de plausibilidad. Puede contrastar una máscara y límites administrativos si se aportan. En la configuración actual faltan esos dos apoyos y el archivo de revisión. Una geometría puede superar plausibilidad y seguir sin estar contrastada provincialmente. X/Y tabulares se comparan geodésicamente sólo si podrían ser longitud/latitud; no se infiere su CRS ni se desplaza el punto a ciegas.

`group_candidates` calcula distancias geodésicas entre pares y componentes conexas a 250, 500 y 1.000 m. Para 790 candidatos su coste cuadrático es manejable; no escalaría igual a millones de puntos. Sus IDs derivan de los miembros y cambian cuando éstos cambian. `define_labels` exige confirmación de presencia, validación geométrica y código no duplicado para P revisado. Los IDs de depósito y distrito proceden exclusivamente de revisión documental.

@@CELL 01 1 Configuración de la fase B

Localiza la raíz, importa el módulo y carga `labels.yaml`. Las aserciones comprueban versión de esquema, que el radio propuesto esté entre los radios evaluados y que las tolerancias tengan signo válido. Muestra la configuración, donde `review_file`, máscara y límites administrativos son actualmente nulos. NumPy y GeoPandas se importan antes de la comprobación de raíz; una dependencia ausente provocaría el error de importación correspondiente. Esta celda prepara el entorno, sin crear etiquetas por sí misma.

@@CELL 01 2 Carga de la A enlazada y huella de la fuente

`load_phase_a` busca la última ejecución satisfactoria si no se fija una ruta. Revalida las fuentes inventariadas y exige los campos necesarios de GPKG/CSV/Excel. Añade a `CONFIG` el hash de la base canónica que se usará en `record_id`. La tabla muestra cuántas filas y columnas tiene cada fuente. Seleccionar una A diferente puede cambiar IDs y volver incompatibles las revisiones anteriores: es una protección de versión, no una pérdida accidental de ceros de código.

@@CELL 01 3 Exploración de la base completa

Muestra `originales['gpkg']` sin modificarlo. La representación de Jupyter normalmente limita filas/columnas, aunque el objeto contiene toda la base. Esta vista ayuda a reconocer atributos, pero no sustituye un análisis completo de nulos, coordenadas o sustancias. No aporta nuevas observaciones al conjunto.

@@CELL 01 4 Celda vacía

No contiene instrucciones, no tiene efecto en el estado y no acredita una etapa implementada. Se registra para mantener correspondencia exacta entre el informe y las posiciones reales del notebook.

@@CELL 01 6 Primera conciliación y visualización completa

`reconcile` agrupa cada fuente por código normalizado y compara conjuntos de valores. Produce una fila por código, conteos por fuente y banderas de discrepancia, además de una tabla independiente de códigos repetidos. La celda muestra el resultado completo. No concatena registros de las tres copias. El cálculo se repite inmediatamente en la celda 7; esta primera llamada es redundante desde el punto de vista del flujo reproducible.

@@CELL 01 7 Conciliación, resumen de duplicados y Au fuera de la base

Vuelve a calcular los dos objetos anteriores. Resume códigos presentes y repetidos por fuente; muestra conflictos de Au y localiza códigos auríferos presentes en CSV/Excel pero ausentes del GPKG. `au_solo_copias` queda disponible para exportación. El uso de `fillna(False)` aquí sólo responde a si una copia contiene evidencia textual para ese código; no convierte territorio U en ausencia geológica. Los casos extra se entregan para conciliación y no se añaden automáticamente como positivos.

@@CELL 01 9 Conteo inicial de valores nulos

`isna().sum()` cuenta nulos reconocidos por pandas en la base vectorial. Es una inspección previa a la normalización. No incluye necesariamente cadenas vacías, espacios o expresiones como `s/d`, que se tratarán después. La salida no es suficiente para concluir que un atributo esté completo desde el punto de vista semántico.

@@CELL 01 10 Normalización y propagación de conflictos

Crea el inventario normalizado y agrega `conflicto_au` mediante una correspondencia por `Codigo_indicio`. Las aserciones conservan número de registros e IDs únicos. La selección mostrada relaciona texto original, tokens, etiqueta observada y tipología propuesta. Esta celda intenta mantener los conflictos visibles junto a cada registro; sin embargo, la siguiente vuelve a crear `normalizados` y pierde esa columna. El comportamiento se ha reproducido sobre la base local sin exportar cambios.

@@CELL 01 11 Segunda normalización que sobrescribe la anterior

Repite `normalize_indicios` y asigna su resultado al mismo nombre `normalizados`. Conserva atributos originales y vuelve a comprobar filas/IDs, pero **elimina `conflicto_au` añadido en la celda 10**, ya que la función no lo crea. La tabla de conciliación independiente continúa existiendo y los conflictos no desaparecen de todos los informes; lo que se pierde es su propagación al inventario que se usa después. Conviene dejar una sola normalización y un único bloque posterior de enriquecimiento de conflictos.

@@CELL 01 12 Vista de los registros con Au observado

Filtra `au_observado` para obtener `au_observados`, muestra el subconjunto y cuenta sus nulos. Es diagnóstico, no selección de P revisados. Más adelante `candidatos` también puede incluir registros confirmados documentalmente que no contengan Au en el texto original, por lo que ambos subconjuntos no tienen por qué coincidir si se incorporan revisiones.

@@CELL 01 14 Entradas opcionales y revisión documentada

Define `optional_input`, que resuelve una ruta configurada, exige su existencia y guarda su SHA-256. Si es shapefile, añade componentes auxiliares existentes. Lee el CSV de revisión si se especifica y ejecuta `apply_reviews`. Cada decisión sustantiva requiere ID de esta versión, valores permitidos, revisor, fecha, evidencia y motivo. Una corrección de coordenadas exige longitud y latitud juntas y geometría marcada como validada. Con la configuración actual no se incorpora ninguna decisión; los campos de revisión quedan vacíos.

@@CELL 01 16 Control geométrico

Carga máscara y límites sólo si están configurados, y llama a `geometry_qc`. Muestra cuarentenas, estados de X/Y e identificadores de registros problemáticos. Las ventanas geográficas amplias descartan incoherencias graves pero contienen también territorio extranjero y mar; no reemplazan fronteras. El resultado local de B contiene tres registros generales en cuarentena y ninguno de los 790 Au. Esto acredita el control básico ejecutado, no validación provincial ni revisión experta de sus posiciones.

@@CELL 01 17 Inspección de coordenadas tabulares de CRS desconocido

Muestra diez filas cuyo X/Y no puede compararse razonablemente como longitud/latitud y sus geometrías. No convierte esas columnas ni corrige el GPKG. Los comentarios inferiores son fragmentos exploratorios inactivos. Es importante que una geometría usable y unos X/Y de CRS desconocido pueden coexistir: el proyecto conserva esa discrepancia para investigar la procedencia de ambas representaciones.

@@CELL 01 19 Estados de confirmación

Cuenta `estado_presencia`, incluyendo nulos. Permite distinguir decisiones documentadas de campos vacíos. No realiza confirmaciones ni asigna tipología. En ausencia del archivo de revisión, el predominio de valores vacíos es esperado y explica por qué la fase B no produce positivos revisados.

@@CELL 01 20 Candidatos, posiciones y grupos de proximidad

Selecciona registros con Au observado o presencia confirmada y calcula posiciones exactas, pares cercanos y sensibilidad de componentes. Muestra posiciones compartidas y obtiene un representante por posición ordenando `record_id`. Este representante es una elección técnica determinista, no el indicio de mayor confianza ni un depósito único. `group_candidates` conserva filas pero no agrupa como válidas aquellas en cuarentena o rechazadas; los grupos resultantes no sustituyen a `deposit_id`.

@@CELL 01 22 Inspección de un grupo concreto

Filtra un ID de proximidad literal a 500 m. La salida depende de esa versión de fuentes y de la composición del grupo. Si cambian datos o IDs puede quedar vacía sin lanzar error; por eso no es una prueba ni una regla reutilizable de selección. No modifica `candidatos`.

@@CELL 01 23 Segunda celda vacía

No ejecuta código. Se conserva en el inventario para explicar por qué los índices no son consecutivos al contar únicamente operaciones sustantivas.

@@CELL 01 24 Mapa de grupos con modificación del objeto de trabajo

Convierte `lon`/`lat` a números, sustituye `candidatos` por su subconjunto sin nulos y factoriza IDs para asignar colores cíclicos de `tab20`. El mapa usa puntos grandes, transparencia, límites con margen y ejes de longitud/latitud. **El filtrado actúa sobre el mismo objeto que después alimenta `define_labels` y la exportación**: futuros candidatos sin coordenadas desaparecerían de esa rama, aunque permanezcan en el inventario general `qc`. Debe hacerse sobre una copia de visualización. En los 790 Au actuales no hay cuarentenas y no se ha demostrado una pérdida efectiva de filas por esta celda.

`set_aspect('equal')` iguala grados dibujados en ambos ejes; no convierte el gráfico en una proyección métrica ni corrige la diferencia de longitud física de un grado de longitud y de latitud. `factorize` da códigos según el orden de aparición: los colores son reproducibles para ese orden, no una identidad estable de grupo frente a reordenaciones.

@@CELL 01 26 Etiquetas finales y elegibilidad revisada

`define_labels` conserva tipología propuesta cuando no hay revisión y separa la confianza de presencia. La elegibilidad general exige presencia confirmada y geometría validada; roca/aluvial exigen además tipología revisada específica. Los rechazados se rotulan como excluidos sin equivalencia con ausencia. Las aserciones impiden una etiqueta textual `0` y positivos revisados en cuarentena. El resultado actual es cero en las tres elegibilidades: el cuaderno prepara revisión, no la suplanta.

@@CELL 01 28 Cobertura puntual de candidatos

Selecciona los nueve rásteres geoquímicos y el MDT del catálogo A, comprueba que estén disponibles y muestrea su banda 1 en la geometría de cada candidato usable. `coverage_at_points` distingue valor válido, NoData, fuera de extensión y geometría no muestreada. La cobertura se calcula en el punto real; posteriormente la cobertura por celda puede ser diferente porque agrega superficie. Las tablas no imputan ni eliminan indicios sin valor.

@@CELL 01 29 Repetición de la tabla de cobertura

Vuelve a mostrar la tabla cruzada fuente/estado creada en la celda anterior. No repite el muestreo ni modifica `cobertura`. Es redundancia visual y puede retirarse en una limpieza editorial sin alterar el resultado del cálculo.

@@CELL 01 31 Representatividad territorial y tipológica

Dibuja candidatos localizables por tipología propuesta y un gráfico de registros por provincia declarada. Cuenta también registros por `Zona_Geode` declarada. Los ejes y títulos reconocen que los conteos son de registros; no se han depurado depósitos independientes ni se ha transformado `Zona_Geode` en distrito metalogenético. La concentración en unas provincias puede reflejar tanto geología como historia de observación y no permite separar ambas causas con estas figuras.

@@CELL 01 33 Exportación y cierre B

`export_phase_b` conserva tablas de conciliación, decisiones, proximidad, cobertura, plantilla, candidatos y cuarentena; escribe GPKG y CSV e inventaría código y entradas. Sólo escribiría el GPKG de revisados si hubiera filas. La celda añade Au ausentes de la base, representantes de posición y la figura, y reverifica todas las fuentes de A y entradas adicionales. El cierre técnico no cierra científicamente B. B no publica un manifiesto final exhaustivo de hashes de sus salidas; C congela los productos B que consume al empezar, dejando constancia explícita de esa limitación temporal.

### 5.2. Valoración respecto al plan

La conciliación y preservación de originales están implementadas. La deduplicación llega a códigos y posiciones, y propone agrupaciones geométricas; la identificación geológica de depósitos/distritos y la tipología revisada siguen abiertas. El contraste administrativo opcional tampoco está activo. Las celdas 11 y 24 merecen corregirse antes de incorporar revisión real, porque introducen efectos de estado fuera del módulo probado.

## 6. Notebook 02 — Rejilla, armonización y cobertura

Corresponde a C, pasos 13–17. Recibe B, las fuentes inventariadas, una máscara local y `grid.yaml`. Genera la estructura territorial uniforme que permite pasar de registros puntuales a una matriz completa P/U. Utiliza [territory.py](../../src/geoau/territory.py) y [additional_layers.py](../../src/geoau/additional_layers.py).

### 6.1. Rejilla y agregación

La malla fuente tiene 2.200×1.820 píxeles de 500 m; la de destino, 1.100×910 celdas de 1 km. El origen es (−50.000, 4.860.000) m en EPSG:25830 y las filas avanzan hacia el sur. `grid_spec` impone estos dos tamaños de píxel y el ámbito peninsular implementado. Cambiar sólo `resolution_m` a 500 no activa una sensibilidad a 500 m: la función lo rechaza porque requiere otro contrato de extracción.

`land_areas` rasteriza el interior y calcula intersecciones exactas con la máscara en píxeles de borde. Comprueba que su suma conserve el área de la máscara. `aggregate_sum` reorganiza bloques 2×2 y suma. Para una celda, la fracción válida es `Σ área terrestre de píxeles válidos / Σ área terrestre de sus cuatro píxeles`. La media continua se pondera por esa área válida. Para categorías se suman áreas por clase, se normalizan sobre área válida y gana la moda de mayor área; los empates favorecen la clase menor.

`make_grid` conserva toda celda con tierra, calcula centros, fila/columna, área y elegibilidad costera desde 50 % de tierra. Los IDs codifican versión, fila y columna. No genera millones de polígonos para persistir la malla: la geometría es reconstruible desde la especificación. Las medidas de distorsión se calculan como diagnóstico muestreado en la proyección y no como certificado de equivalencia de áreas.

### 6.2. Armonización vectorial

La versión sin caché pagina por FID creciente y usa el índice RTree del GPKG para un recorte rectangular con margen de 20 km. Compara el recuento leído con una consulta independiente para detectar truncación. Reproyecta, elimina Z/M del cálculo 2D, repara geometrías inválidas y audita cambios. Los tipos incompatibles se ponen en cuarentena: el comentario sobre `GeometryCollection` es más amplio que el filtro real, que admite tipos lineales o poligonales simples/múltiples, no colecciones arbitrarias.

Para GEODE contrasta una muestra de linealización de curvas con pasos angulares de 1° y 0,5°, exigiendo una diferencia Hausdorff de hasta 1 m. No es una prueba sobre todas las curvas. La caché compara funciones mediante AST, parámetros, máscara, fuentes y hashes de los productos antes de copiar. Para polígonos estima huella mediante centros de píxeles de 500 m; para líneas registra presencia de trazas y no la interpreta como cobertura del levantamiento.

@@CELL 02 2 Inicialización y especificación espacial

Detecta raíz, importa módulos y lee `grid.yaml`. `grid_spec` añade transformadas afines y formas a la configuración y valida el contrato implementado. Muestra el intérprete y los parámetros. A diferencia de 00/01, `next(...)` no usa un valor por defecto: abrir fuera del árbol esperado produce `StopIteration`, menos informativo que un error que solicite raíz. No realiza todavía geometría ni escritura de productos.

@@CELL 02 4 Inicio de C con entradas verificadas

`start_run` comprueba el cierre B, localiza su A enlazada, valida fuentes y entradas, verifica procedencia de la máscara y congela archivos de entrada. Crea la carpeta de ejecución y sus subdirectorios. Lee los candidatos B y muestra sus códigos y elegibilidad revisada. Esta función no toma una A más reciente ajena a B: conserva la cadena. Los resultados candidatos B se sellan al inicio de C porque B no los había sellado exhaustivamente al finalizar.

@@CELL 02 6 Máscara y ámbitos de España

Carga el archivo territorial, exige país ES, CRS y geometrías válidas, descompone componentes y calcula sus áreas en EPSG:3035 para escoger la mayor. Exporta todas las componentes y una máscara de la principal reproyectada a 25830. La tabla identifica lo incluido y lo fuera de alcance. El área impresa se mide ya en UTM30, por lo que difiere conceptualmente del área equivalente usada para escoger la componente.

@@CELL 02 7 Visualización de la geometría de máscara

Devuelve el objeto Shapely `mascara` para su representación automática. No modifica el ámbito ni calcula cobertura. Su dibujo permite una comprobación visual general, pero no resolver precisión de costa, pequeños islotes, fronteras o componentes omitidas por el criterio de mayor área.

@@CELL 02 9 Área terrestre y creación de malla

Calcula áreas de píxel nativo y las agrega en `make_grid`; exporta malla, especificación, fracción terrestre y diagnóstico de distorsión. La consulta `land_fraction == 0` debe quedar vacía porque sólo se conservan áreas positivas. La salida de 496.855 celdas describe la máscara candidata actual. El denominador rectangular de 1.001.000 celdas incluye mar y territorio ajeno, por lo que no puede usarse directamente como área española evaluable.

@@CELL 02 11 Exploración de las celdas terrestres

Muestra las filas con fracción terrestre mayor que cero. Por construcción son todas las filas de `grid`, por lo que no introduce una selección adicional. Es útil como inspección de estructura e IDs; no aplica todavía el umbral costero ni los requisitos de datos de cada modelo.

@@CELL 02 13 Diccionario de soporte

`feature_dictionary` escribe y muestra los nombres conceptuales, fuentes, unidades, soporte y política de ausentes. Algunas variables sólo quedan previstas para D. La columna `same_for_P_U_inference=True` expresa el contrato de extracción uniforme. Este diccionario inicial no contiene todavía las 168 variables efectivamente calculadas ni sus decisiones semánticas finales; D construye su diccionario más detallado.

@@CELL 02 15 Alineación de geoquímica y elevación

`align_rasters` abre los nueve elementos y el MDT y exige igualdad exacta de CRS, forma y transformada nativa. No corrige de forma silenciosa un desfase: falla si la fuente no está anidada. Lee la banda 1 por bloques y aplica media ponderada para elevación o moda/proporciones para clases, con NoData separado del cero. Produce TIFF a 1 km y fracciones válidas. El control RGB se ejecutará después en 04 y puede reducir la cobertura inicialmente calculada aquí.

@@CELL 02 16 Vista de fracciones de Au

Convierte la matriz de fracciones de soporte de Au en un DataFrame y muestra sus primeras filas. Los valores representan proporción válida, no clase modal ni contenido de oro. Es una inspección de la matriz rectangular; no está limitada a las filas terrestres del DataFrame `grid`.

@@CELL 02 18 Armonización o recuperación de vectores

Llama a `harmonize_vectors` con el margen, máscara y configuración espacial. La ejecución actual utiliza el checkpoint fijado por `vector_cache_run` y verifica su compatibilidad antes de copiarlo. La tabla de control resume paginación, entidades, geometrías, cobertura y cambios, aunque la visualización elimina columnas largas de advertencias y semántica. Ocultarlas en pantalla no equivale a resolverlas: permanecen en el CSV del producto.

@@CELL 02 20 Capas adicionales recuperadas

Armoniza ocho familias adicionales: vuelos magnéticos/radiométricos, magnetotelúrica, medidas estructurales, petrofísica, buzamientos, cuaternario, gravimetría y zonas GEODE. El módulo conserva atributos y Z original en puntos cuando procede, inspecciona rangos angulares y reconoce el papel de cada fuente. Una línea de vuelo no se transforma en anomalía magnética ni una localización EDI en resistividad. El control es de ocupación/huella y atributos; la lista de campos cuantitativos útiles sigue dependiendo de metadatos verificados.

@@CELL 02 22 Productos territoriales de cobertura

Une fracciones a la malla, define estados de costa y soporte, asigna candidatos a celdas y calcula resúmenes por ámbito y bloques diagnósticos. La asignación comprueba que el punto esté cubierto por la máscara y usa intervalos semiabiertos: un punto exactamente en borde este/sur pasa a la celda adyacente. Conserva una fila por indicio y agrega sus conteos después. `prediction_allowed=False` en toda la malla evita confundir cobertura de datos con autorización de predicción.

@@CELL 02 24 Consulta de soporte adicional y relaciones exactas

Lee resúmenes de las ocho capas y relaciones punto–polígono con zonas/cuaternario. En líneas/puntos la presencia en una celda no se convierte en área válida de levantamiento. La relación puntual exacta puede mostrar ausencia de intersección aunque haya una huella en otra parte de la misma celda. El texto `sin_interseccion_NO_ausencia` mantiene esa diferencia; no prueba que no existan materiales o depósitos aluviales.

@@CELL 02 26 Casos sin geoquímica y comparación B–C

Lee todos los candidatos con alguna falta de geoquímica puntual y cuenta `record_id` distintos, no filas elemento–indicio. El resultado guardado es siete registros con al menos una carencia; el recuento de cinco del plan pertenece a una auditoría anterior y otro detalle de muestreo. La comparación externa B/C se realiza por `record_id` y fuente con unión 1:1, comprobando coherencia entre ambas fases. No impone el recuento antiguo ni rellena huecos con cero.

@@CELL 02 28 Mapa de cobertura

Representa la matriz de estados con colores discretos y oculta el fondo rectangular de código cero. Añade los candidatos fuera de cuarentena reproyectados al CRS de la malla y una leyenda de soporte. Guarda la figura y muestra bloques con peor cobertura de Au. La extensión usa el literal 1.000 m, coherente con el contrato actual pero no genérico. Este mapa explica disponibilidad de información; sus zonas verdes no son zonas favorables a oro.

@@CELL 02 30 Aserciones finales, integridad y sellado C

Exige paginación completa de vectores base y adicionales, IDs de celda únicos, conservación de la relación indicio–celda y ausencia de autorización de predicción. `finish_run` repite hashes de originales y entradas congeladas, escribe pendientes y sella productos. El control local informa 789 candidatos asignados y uno fuera de máscara, todos sin revisión positiva. Las pruebas cubren integridad y geometría operativa; la máscara generalizada, huellas de levantamiento y revisión geológica continúan pendientes.

### 6.3. Diferencia entre las coberturas C y D

C utiliza huellas poligonales estimadas en centros de 500 m para diagnóstico de disponibilidad. D recalcula intersecciones exactas por categoría y rechaza ciertos solapes y atributos ausentes. Además, 04 filtra colores de geoquímica. Por ello una cobertura favorable en C no obliga a que la misma celda sea elegible en D: la fase de variables añade requisitos de calidad más estrictos.
