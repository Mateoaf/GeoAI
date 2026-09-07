# Plan de ejecución del proyecto de prospectividad aurífera en España

Fecha: 5 de septiembre de 2026. Base: auditoría local `auditoria_2026-09-05`, documentos aportados y revisión de los scripts existentes.

No se ha encontrado una carpeta `auditoria_2026-09-09`. Se interpreta esa referencia como la auditoría del 5 de septiembre que está abierta en el IDE. Este documento constituye un plan propuesto; no acredita que los procesos descritos estén implementados ni que exista un modelo validado.

**Decisión principal:** construir primero una base territorial reproducible y fiable, y después comparar modelos. La primera versión será un índice de favorabilidad regional a 1 km, con validación espacial y productos separados para oro en roca y oro aluvial cuando las etiquetas permitan sostenerlos. El ámbito español completo será una ampliación explícita: la extensión de los rásteres actuales no basta para acreditarlo.

## 1. Qué demuestra la auditoría y qué sigue pendiente

Se inspeccionaron los esquemas y recuentos de los 36 GeoPackage, las bandas y valores de los 20 TIFF, los 16 CSV, el Excel de indicios y las 33 referencias del proyecto QGIS. También se revisaron los dos PDF aportados, el DOCX de reunión, el notebook del vino y los scripts de generación de capas. El informe técnico adicional y el README se utilizaron como contexto, contrastando sus afirmaciones con los archivos.

La auditoría comprueba contenido, no certifica todavía la validez de todas las geometrías, la cobertura territorial completa, la exactitud geológica ni la ausencia de duplicados espaciales entre fuentes. Esas verificaciones forman parte del trabajo pendiente.

| Hallazgo comprobado | Consecuencia para el proyecto |
|---|---|
| `IndiciosII.gpkg`: 11.732 registros y códigos únicos; 790 registros incluyen oro | Fuente de partida para las etiquetas, todavía pendiente de revisión espacial y geológica |
| Los 790 registros auríferos ocupan 787 posiciones distintas | Ni registros ni posiciones equivalen directamente a depósitos independientes |
| `IndiciosII.csv`: 11.732 filas, 10.989 códigos únicos, 844 filas con oro y 783 códigos auríferos | No es una copia equivalente del GPKG; reconciliar por identificador y contenido |
| `Indicios.xlsx`: 11.732 filas, 10.141 códigos únicos; 889 filas con oro y 771 códigos auríferos | No concatenar Excel y GPKG ni tomar 889 como número de positivos nuevos |
| En el GPKG, 595 filas tienen X/Y tabulares fuera de los límites de longitud/latitud | Utilizar la geometría espacial como candidata preferente y comprobarla; no asignar automáticamente un CRS a X/Y |
| Hay geometrías del inventario general con latitudes próximas a 4°, incompatibles con sus provincias españolas | Incluso la geometría del GPKG necesita validación; los ejemplos detectados no eran registros auríferos |
| Morfología aurífera: 299 aluvionares, 294 filonianos, 77 desconocidos y 120 de otras morfologías | Separar mecanismos geológicos y revisar las categorías; filoniano no significa automáticamente orogénico |
| León reúne 352 registros Au y Asturias 123: aproximadamente el 60 % entre ambas | El tamaño muestral efectivo y la transferencia a otras regiones serán limitaciones centrales |
| Nueve GPKG no contienen tablas de capas | Su existencia en disco no significa disponibilidad de datos |
| La geoquímica procede de mapas renderizados clasificados por colores | Las bandas denominadas concentración son valores representativos de intervalos, no mediciones continuas |
| Au y W tienen siete clases; As, Sb, Bi, Hg, Cu, Pb y Zn, ocho | Evitar falsa precisión, interpolación de clases y redundancia entre bandas |
| Los nueve rásteres geoquímicos dejan cinco registros Au sin valor en el muestreo efectuado | Revisar esos puntos y sus máscaras; no rellenarlos con cero ni eliminarlos sin registrar el motivo |
| El MDT contiene elevación y tres derivados, a 500 m | Los derivados necesitan reconstrucción/verificación de NoData, ventanas y definiciones |
| Los GPKG estructurales contienen contactos, fallas y también bordes de hoja, agua y elementos antrópicos | Clasificar las entidades antes de calcular distancias y densidades |
| Varias geometrías estructurales son `MULTICURVE`, algunas con Z/M | Preparar una conversión geoespacial controlada; un lector tabular no basta |
| `mdt25.tif` no aparece; `contactos.gpkg` se corresponde nominalmente con el archivo existente `contactos-002.gpkg` | Corregir el catálogo y programar la recuperación del MDT detallado cuando proceda |
| `models/` está vacío y faltan los módulos, tests y resultados anunciados por el README | No utilizar sus métricas, su cifra de 906 positivos ni sus declaraciones de producción como resultados verificados |

Los recuentos de identificadores únicos en las grandes capas coinciden con sus filas. Esto descarta duplicación de esos identificadores dentro de cada copia, pero no descarta trazas repetidas, solapes entre hojas ni duplicación GEODE–MAGNA.

**Lectura crítica de los documentos.** El documento de reunión es el más prudente al describir el estado: preparación de datos realizada parcialmente, entrenamiento pendiente. `CAPAS.pdf` sirve como inventario nominal, pero llama analíticos a productos derivados de simbología y enumera capas vacías o ausentes. `analisis proyecto.pdf` acierta al priorizar rejilla, etiquetas, aprendizaje presencia–fondo, validación espacial e incertidumbre; este plan concreta cómo ejecutar esos conceptos sobre los archivos reales.

Del notebook del vino se reutilizará su estructura explicativa y el uso de `Pipeline`/`ColumnTransformer`. La celda 9, contando desde cero, imputa medianas antes de las particiones; esa operación se eliminará en la adaptación. La celda 182 usa un reparto aleatorio y la 582 un stacking con `cv=3`; ambos requieren sustitución espacial. La importancia por permutación del Random Forest se calcula en entrenamiento, aunque otra sección del árbol sí la calcula en test: no conviene generalizar esa crítica a todo el notebook.

## 2. Producto que se construirá y alcance por versiones

**V0 — Base geocientífica verificable.** Catálogo de fuentes, inventario de indicios depurado, clasificación geológica, máscara territorial, rejilla, predictores y particiones espaciales. Este es el siguiente entregable real, antes de Random Forest.

**V1 — Piloto regional a 1 km.** Elegir una zona del noroeste/macizo varisco como candidata inicial por la disponibilidad de registros, sin declararla elegida por sus futuros resultados. El límite definitivo dependerá de depósitos independientes, cobertura y capacidad para reservar distritos completos. Comparar un modelo sencillo y Random Forest. El piloto comprueba toda la cadena, no demuestra validez nacional.

**V2 — Modelo de la España peninsular.** Ampliar las capas verificadas, revisar los otros dominios geológicos, hacer validación anidada y por distritos, comparar boosting y publicar favorabilidad, estabilidad y aplicabilidad. Donde falten datos o representatividad, publicar un estado explícito de no evaluable/extrapolación.

**V3 — Cobertura española completa.** Auditar y obtener las fuentes necesarias para Baleares, Canarias, Ceuta y Melilla; estudiar su representatividad geológica y sus sistemas de referencia. La falta de ejemplos o de soporte geocientífico puede impedir una predicción supervisada defendible. En ese caso, entregar cobertura y diagnóstico de carencias, o una evaluación experta diferenciada, sin presentar una extrapolación peninsular como validación local.

**V4 — Refinamiento de objetivos.** MDT de mayor detalle, cartografía y muestreo local, hidrología detallada, geofísica cuantitativa y, si aporta valor, teledetección. La resolución local se decidirá por la información disponible; un remuestreo de 1 km a 25 m no crea información geológica.

La salida será un **índice de favorabilidad**, no una estimación de ley, tonelaje, profundidad, rentabilidad ni probabilidad absoluta de descubrimiento. Los resultados operativos o de acceso al terreno se mantendrán en una capa de decisión posterior, separada de la favorabilidad geológica.

## 3. Decisiones metodológicas que se fijarán antes de entrenar

1. **Unidad estadística:** una celda territorial. El identificador será estable y dependerá de versión de rejilla, fila y columna. Todos los positivos y puntos de fondo utilizarán el mismo procedimiento de extracción.
2. **Rejilla inicial:** 1 km; contraste a 500 m en experimentos predefinidos. El Atlas declara superficies interpoladas sobre una malla de 1.000 m mediante inverso de la distancia al cuadrado. Esa malla tampoco equivale a una muestra de laboratorio por km². [Descripción oficial del Atlas y servicios IGME](https://mapas.igme.es/Servicios/default.aspx).
3. **CRS:** rejilla peninsular candidata en ETRS89/UTM 30N, coherente con los TIFF. Cuantificar distorsiones en extremos; para geometría fina o extensiones insulares, usar la proyección regional apropiada. No medir distancias y superficies directamente en EPSG:3857 ni en grados.
4. **Etiquetas persistidas:** `P` para presencia revisada; `U` para territorio sin etiqueta. Si un clasificador necesita 0/1, el cero será una codificación de entrenamiento de U, con su significado conservado.
5. **Objetivos:** Au en roca, Au aluvial y, como referencia, Au general. Los 77 casos desconocidos no se asignarán automáticamente a roca. Tampoco se etiquetará oro aluvial como ausencia de oro en roca.
6. **Particiones:** fijar depósitos, distritos, bloques y reserva final antes de seleccionar modelos, variables o umbrales.
7. **Métrica operativa principal:** recuperación de depósitos reservados dentro del 5 % del área evaluable mejor ordenada; acompañar de 1 % y 10 %. La fracción podrá cambiar por necesidades del proyecto, pero debe quedar fijada antes de ver el test.
8. **Comparación justa:** mismos territorios, positivos, pesos y muestra de evaluación para todos los candidatos. Cambiar el ratio de fondo de entrenamiento no autoriza a cambiar el conjunto de prueba.
9. **Variables prohibidas en X:** nombre de mina, sustancia, asociación mineral del indicio, tamaño, código, ESRI_OID, provincia, municipio, coordenadas e identificadores espaciales como predictores directos, y distancias/densidades derivadas de los propios indicios auríferos.
10. **Transformaciones aprendidas:** imputación, escalado, selección, agrupación estadística de categorías raras y calibración se ajustan solo dentro del entrenamiento de cada partición. Una cartografía externa fija puede armonizarse previamente; una interpolación o transformación ajustada para el experimento exige revisar qué información usa. [Buenas prácticas oficiales de scikit-learn](https://scikit-learn.org/stable/common_pitfalls.html).

## 4. Destino de cada familia de archivos

| Archivos reales | Uso y tratamiento previsto |
|---|---|
| `IndiciosII.gpkg` | Base canónica candidata para etiquetas; conservar geometría e identificadores originales, revisar posiciones y agrupar depósitos |
| `IndiciosII.csv`, `Indicios.xlsx` | Reconciliación y recuperación documental de diferencias; nunca concatenación automática ni unión por número de fila |
| `recintos.gpkg`, `RecintosGeologicos.csv` | 612.170 recintos. Usar el GPKG; normalizar `DESC_UNIT`, edades y códigos. Interpretar `CODE_UNIO` dentro de su zona/leyenda, no como código nacional universal |
| `litologias.gpkg`, `Litologias_España.csv` | 16.007 polígonos de litología regional. Fuente de referencia y respaldo; usar geometría del GPKG |
| `edades.gpkg`, `Edades_España.csv` | 16.007 polígonos. Familias de edad y atributos cronoestratigráficos; verificar correspondencia espacial con litología |
| `zonasgeode.gpkg` | Sin tablas. Recuperar geometría de dominios o producir agrupaciones documentadas desde recintos; `ZONA` no se asumirá equivalente a dominio metalogenético |
| `cuaternariorecintos.gpkg`, `Cuaternario – Recintos.csv` | GPKG vacío; CSV con 44.464 registros sin geometría. Recuperar polígonos del servicio; no se puede rasterizar directamente este CSV |
| `contactos-002.gpkg`, `ContactosGeode.csv` | 2.126.026 entidades. Separar contactos intrusivos, otros contactos, fallas, cizallas y elementos no geológicos; fuente preferente candidata en zonas con cobertura adecuada |
| `contactosyfallas.gpkg`, `ContactosFallasMagna50.csv` | 2.229.505 entidades. Alternativa/complemento MAGNA; quitar bordes de hoja y solapes antes de combinar con GEODE |
| `ejes.gpkg`, `Ejes.csv` | 27.556 entidades. Pliegues GEODE por tipo y confianza; distancias/densidades tras revisar geometrías |
| `estructuras de plegamiento.gpkg`, `EstrucPlegMagna.csv` | 31.801 entidades. Complemento MAGNA; controlar duplicación con ejes |
| `buzamientos.gpkg`, `medidasestructurales.gpkg` | Vacíos. Recuperación opcional; requieren medidas y convenciones angulares, no solo símbolos de mapa |
| `MDT_Espana_CNIG_500m.tif` | Cuatro bandas; auditar elevación y reconstruir pendiente, posición topográfica y rugosidad con máscaras correctas |
| `MDT_Espana_CNIG_Sombreado_RGB.tif` | Visualización; no se utilizará como predictor |
| `MDT_CNIG_Topografia_2012.tif.aux.xml`, `MDT_CNIG_Elevacion_Hillshade_RGB.tif.aux.xml` | Metadatos auxiliares cuyos TIFF base no aparecen; no contienen un MDT utilizable por sí mismos |
| `redhidrografica.gpkg` | 13.396 tramos en EPSG:4258. Distancia a cauce y control de cobertura; comprobar si representa una red de masas de agua y qué cabeceras omite |
| `red-hidrografica2022_27/*.shp/.dbf/.shx/.prj/.cpg`, ZIP original | Respaldo de la red. El DBF también tiene 13.396 filas; verificar equivalencia espacial y atributos, conservar juntos los componentes |
| `gravimetria.gpkg`, `magnetometriaradiometria.gpkg`, `magnetotelurico.gpkg`, `petrofisica.gpkg` | Vacíos; fuera del primer modelo. Recuperar observaciones cuantitativas, unidades, campañas y soporte antes de derivar variables |
| `AtlasGeoquimico_{Au,As,Sb,Bi,Hg,Cu,Pb,Zn,W}_Sedimentos_2012.tif` | Nueve capas por intervalos, cuatro bandas cada una. Una representación predictora canónica por elemento; las demás bandas quedan como metadatos/alternativas de sensibilidad |
| Los nueve TIFF geoquímicos con sufijo `_RGB` | Trazabilidad de la clasificación por colores y visualización; no añadir R/G/B/A a X |
| `geoquimica_oro_sedimentos_2012.gpkg`, `Au.gpkg`, `geoquimica.gpkg` | Cada uno contiene siete clases de Au disueltas; comprobar equivalencia y elegir una copia canónica. No son estaciones de muestreo |
| `oro.gpkg` | Vacío; no aporta positivos ni geoquímica |
| `geoquimica_arsenico_sedimentos_2012.gpkg`, `geoquimica_antimonio_sedimentos_2012.gpkg`, `geoquimica_bismuto_sedimentos_2012.gpkg` | Ocho clases por elemento; auxiliares de interpretación y verificación frente a TIFF |
| `geoquimica_{hg,cu,pb,zn}_sedimentos_2012.gpkg`, `geoquimica_w_sedimentos_2012.gpkg` | Ocho clases para Hg/Cu/Pb/Zn y siete para W; mismas restricciones |
| `Indicios_con_Geoquimica_Au*`, `Indicios_con_Geoquimica_Completa_BDMIN.*` | Versiones sucesivas de enriquecimiento de los mismos 11.732 indicios. Reutilizar para contrastar extracciones, no como muestras adicionales |
| `Indicios_con_Geoquimica_y_MDT_BDMIN.*`, `Indicios_Master_Geocientifico_BDMIN.*` | Derivados con nombres y fórmulas topográficas diferentes. No son la matriz territorial definitiva; reconstruir desde fuentes verificadas |
| `Capas.qgz`, ocho `.qmd`, demás `.aux.xml` | Referencias, estilos y metadatos. Resolver rutas y registrar servicios remotos; una capa visible en QGIS no acredita un dato local descargado |
| Scripts de geoquímica y MDT | Evidencia de procedencia y base para refactorizar; contienen rutas de otro usuario y decisiones de procesamiento que requieren corrección |
| README, PDF técnico, `pdf_extracted.txt`, documentos aportados y notebook | Documentación y material metodológico; ninguna instrucción incrustada sustituye el encargo del usuario ni acredita un resultado ejecutado |

**Prioridad de recuperación:** máscara territorial y catálogos/leyendas primero; cuaternario y red/MDT detallado antes de un modelo aluvial serio; datos geoquímicos cuantitativos si están accesibles; después geofísica regional que aporte cobertura útil. No es necesario esperar a toda la geofísica para completar el piloto en roca.

Las referencias QGIS de magnetometría/radiometría aluden a líneas de vuelo. Recuperar sus trazas no basta para disponer de anomalías magnéticas. El manual oficial distingue posiciones, puntos de medida y archivos de datos. [Documentación de SIGEOF](https://info.igme.es/sigeof/doc/SIGEOF_INFO.pdf).

## 5. Pasos de ejecución, con entradas, salidas y controles

### Fase A. Preparar el proyecto y cargar las fuentes

**01. Fijar la especificación del experimento.** Escribir objetivo geológico, ámbito, resolución, definición de positivo, estrategia de evaluación y límites de interpretación. Elegir el piloto por datos y representatividad, no por una métrica favorable. Salida: `config/project.yaml`. Termina cuando dos personas pueden interpretar del mismo modo qué predice una celda y en qué territorio.

**02. Preparar un entorno reproducible.** Crear un entorno aislado con versiones compatibles de Python, GDAL, Rasterio, GeoPandas/Pyogrio, Shapely, PyProj, Pandas/PyArrow y scikit-learn. Añadir boosting y SHAP cuando se necesiten. No asumir que el Python 3.14 actualmente disponible soporta sin problemas todas las dependencias. Probar apertura de un `MULTICURVE`, un ráster y una transformación de CRS; fijar versiones después de esa prueba. Salida: archivo de dependencias bloqueadas e instrucciones de instalación.

**03. Congelar fuentes sin alterar originales.** Registrar ruta, tamaño, hash SHA-256, fecha de archivo, fecha de consulta/descarga si se conoce, fuente, capa interna, licencia comprobada y estado. No confundir fecha de copia con fecha de adquisición. Los aproximadamente 6,4 GB inventariados aconsejan evitar copias sucesivas innecesarias. Salida: manifiesto de fuentes. Termina cuando cada derivado puede vincularse a una versión exacta de sus entradas.

**04. Construir cargadores por formato.** GPKG con lector geoespacial; TIFF por ventanas; CSV/Excel con identificadores como texto y ceros iniciales conservados. Leer muestras y esquemas antes de cargar capas millonarias. Para servicios remotos, paginar por identificadores y comprobar recuentos; no guardar un resultado truncado como cobertura completa. Salida: módulo de lectura más informes de filas, CRS, columnas, geometrías y errores.

**05. Resolver inventario y rutas.** Mantener una sola referencia canónica por fuente. Corregir la referencia a `contactos.gpkg`, registrar los nueve GPKG vacíos y las rutas QGIS rotas, incluida la referencia a `data/processed/bdmin_au_clean.gpkg`. El código nuevo resolverá rutas desde la raíz/configuración, sin `C:\Users\mdmat\...`. Salida: catálogo de capas con estados `utilizable`, `requiere_limpieza`, `recuperar`, `visual`, `derivado`.

**06. Recuperar datos mínimos ausentes.** Obtener límite terrestre oficial y leyendas geológicas. Para el aluvial, recuperar polígonos cuaternarios y cartografía fluvial/relieve con detalle suficiente. Verificar acceso a datos del Atlas anteriores al renderizado y a fuentes cuantitativas de SIGEOF. Guardar URL, respuesta, identificadores y límites de cobertura. La disponibilidad de un servicio deberá confirmarse al ejecutar la descarga. Salida: fuentes nuevas y registro de lo que continúa sin acceso.

### Fase B. Limpiar indicios y definir las etiquetas

**07. Conciliar las tres bases de indicios.** Comparar GPKG, CSV y Excel por `Codigo_indicio` y contenido; tratar `ESRI_OID` como identificador de una copia, no necesariamente estable entre versiones. Producir listas de solo-en-una-fuente, duplicados, sustancias discrepantes y posiciones discrepantes. No rellenar por coincidencia de fila. Salida: `reconciliacion_indicios.csv` y elección justificada de la fuente vigente.

**08. Limpiar atributos sin perder el original.** Mantener campos `*_raw`; normalizar blancos, nulos, mayúsculas, codificación y separadores. Tokenizar `Sustancia` y reconocer exactamente Oro/Au según diccionario; no usar coincidencias parciales arbitrarias. Conservar Au principal/acompañante como metadato de etiqueta cuando sea verificable. Salida: inventario tabular normalizado y reglas versionadas.

**09. Verificar las coordenadas.** Comprobar geometría no nula, tipo punto, CRS, relación con máscara española y provincia/municipio de referencia. Comparar geometría con X/Y, registrar precisión conocida y origen del ajuste. Poner anomalías en cuarentena; no cambiar de signo, mover al municipio o inferir husos a ciegas. Salida: `indicios_geometry_qc.gpkg` y `correcciones_coordenadas.csv`. Los registros sin localización defendible quedan fuera del entrenamiento, con motivo.

**10. Deduplicar en tres niveles.** Primero código repetido; después posición coincidente; finalmente depósito/sistema geológico compartido. Revisar las dos agrupaciones de coordenadas auríferas repetidas detectadas. Utilizar nombres, cartografía y distancia como ayuda, sin asumir que cualquier pareja cercana es el mismo depósito. Comparar agrupaciones espaciales con radios tentativos de 250/500/1.000 m, condicionados por precisión y geología. Salida: `deposit_id`, `district_id` y correspondencia entre registros y depósitos. No fijar el total final en 787: esa cifra es solo de posiciones.

**11. Clasificar el contexto aurífero.** Geólogo: asignar `roca`, `aluvial`, `mixto`, `desconocido` y, cuando haya evidencia, sistema mineral específico. Revisar los 120 casos no aluvionares/no filonianos/no desconocidos antes de asignarlos a roca. Definir confianza y justificación. El modelo general puede usar positivos inciertos respecto a tipología si la presencia y posición de Au son fiables; los modelos específicos requieren tipología defendible. Salida: `etiquetas_au_revisadas.gpkg`.

**12. Medir representatividad y sesgo.** EDA de depósitos por distrito, tipología, dominio, cobertura de capas y calidad. Informar registros, posiciones, depósitos y celdas positivas por separado. Estudiar concentración espacial y zonas de exploración histórica. La abundancia de registros puede reflejar geología y esfuerzo de observación: no atribuirla exclusivamente a uno. Salida: informe de etiquetas y propuesta de reservas espaciales.

### Fase C. Construir la rejilla y armonizar las capas

**13. Crear la máscara y rejilla territorial.** Definir una geometría española terrestre, ámbitos de modelización y estados de cobertura. La caja de los TIFF es de 1.100 × 910 km: a 500 m contiene 4.004.000 celdas y a 1 km, 1.001.000, incluyendo mar y territorio ajeno. Recortar con máscara independiente; el NoData geoquímico no representa la frontera nacional. Añadir área terrestre efectiva por celda y política para celdas costeras. Salida: `grid_1km` y su especificación de origen, transformada, extensión y CRS.

**14. Fijar el soporte de extracción.** Para cada predictor decidir valor en centroide, proporción de superficie, distancia mínima de la celda o estadístico de ventana. Recomendación inicial: geología por fracciones y clase dominante; distancia desde centroide; densidades en ventanas; geoquímica por clase/proporciones; relieve por estadísticas agregadas. El soporte será idéntico para celdas positivas, U e inferencia. Salida: `feature_dictionary.csv`.

**15. Reproyectar y sanear vectores.** Transformar coordenadas, convertir curvas a geometrías lineales con tolerancia documentada, tratar Z/M cuando no se usan y reparar geometrías inválidas con control de cambios. Conservar códigos de origen. Usar índice espacial y particiones; trabajar con margen alrededor del ámbito para no cortar el vecindario de una distancia o densidad. Salida: capas limpias por familia y métricas de cambios geométricos.

**16. Alinear rásteres y máscaras.** Verificar igualdad exacta de CRS, origen, paso, forma, extensión y NoData. Clases: vecino más próximo o proporciones/moda al agregar; nunca bilinear sobre códigos. Elevación continua: remuestreo/agrupación apropiado según cambio de escala. Mantener máscara de cobertura y fracción válida; no confundir clase cero geoquímica con ausencia. Salida: rásteres alineados y controles de coincidencia de píxel.

**17. Dibujar el mapa de cobertura real.** Cuantificar por ámbito y familia: área válida, huecos, solapes, discontinuidades y positivos cubiertos. Revisar los cinco puntos Au sin geoquímica. Un porcentaje nacional de cobertura puede ocultar un distrito entero sin datos. Definir dónde funciona el conjunto básico y dónde se necesita una versión reducida o no se emite predicción. Salida: `coverage.gpkg` y tabla de decisiones de cobertura.

### Fase D. Crear variables geocientíficas

**18. Derivar litología, edad y unidades.** Crear diccionario geológico jerárquico desde `DESC_UNIT`, `Litologia`, `SISTEMA` y leyendas. Unificar variantes textuales; agrupar por conocimiento geológico sin usar y. Calcular litología dominante, fracciones de grupos principales, edad, presencia/proporción de granitoides, metasedimentos, materiales volcánicos y cuaternarios cuando sean cartografiables. Añadir proximidad a contactos intrusivos seleccionados. No convertir todo Paleozoico en una regla fija de favorabilidad. Salida: tabla/rásteres de geología con procedencia por celda.

**19. Derivar estructuras.** Construir una tabla explícita para `TIPO` y `DESC_LINE`: falla/cizalla, cabalgamiento, contacto intrusivo, otro contacto, pliegue y excluido. Excluir agua, límites políticos, bordes de hoja, escombreras, cortas y simbología. Separar observado/supuesto. Elegir una fuente preferente por zona y evitar sumar GEODE y MAGNA duplicados. Calcular distancias en metros y longitud/área en km/km² a 1, 5 y 10 km; no contar segmentos como densidad de fallas. Salida: `features_structural`.

**20. Añadir estructuras avanzadas solo con control.** Intersecciones reales frente a cruces artificiales, orientación axial mediante seno/coseno de doble ángulo, distancias a ejes de pliegue y, si se recuperan, estadísticas de buzamiento. Las intersecciones requieren tolerancia y saneamiento topológico; un cruce de trazas en un mapa no acredita una conexión mineralizante. Probar estas variables después de una base estable. Salida: bloque experimental separado.

**21. Reconstruir la geoquímica por clases.** Revisar paleta, umbrales y leyenda de cada elemento. El algoritmo existente asigna todo píxel opaco al color más cercano sin un umbral de rechazo: comprobar colores exactos, antialiasing y bordes. Guardar máscara de calidad de clasificación. Au/Hg están rotulados en ppb; As/Sb/Bi/Cu/Pb/Zn/W en ppm o mg/kg. Verificar esas unidades contra fuente. Seleccionar clase ordinal como primera representación; para modelos lineales comparar one-hot. Mantener mínimo, máximo y valor representativo como metadatos, no como cuatro evidencias independientes.

Al agregar 500 m a 1 km, conservar proporciones de las cuatro celdas válidas o moda con regla de desempate. Los ratios químicos y logaritmos de valores representativos de intervalos no equivalen a ratios/logaritmos de análisis reales. No asumir distribuciones uniformes dentro del intervalo ni usar sus extremos como intervalo de confianza. Salida: `features_geochemistry_classes` y verificación contra RGB/leyenda.

**22. Preparar una mejora geoquímica cuantitativa, si es viable.** Obtener puntos analíticos o ráster original con metadatos de muestreo, extracción, unidades, censura y límites de detección. Separar sedimento, suelo y roca. Una anomalía de sedimento integra transporte aguas arriba; no demuestra oro en roca bajo ese píxel. Si se construye interpolación propia, validarla espacialmente, documentar densidad y soporte, y distinguir datos externos disponibles a la fecha del estudio de información posterior. Salida: versión cuantitativa opcional, comparada con la base clasificada.

**23. Reconstruir relieve.** Auditar la banda de elevación y aplicar máscara terrestre independiente. Recalcular pendiente sin rellenar huecos con cero; usar vecindarios válidos y margen de cálculo. En el script actual, el TPI 3×3 a 500 m tiene un lado de 1,5 km, no radio de 1,5 km ni una definición inequívoca de TPI a 1 km. La banda denominada TRI se calcula como desviación típica local: renombrarla o implementar el índice de rugosidad elegido. Guardar fórmula, radio, unidades y tratamiento de bordes. Salida: elevación, pendiente, TPI con radios explícitos y rugosidad definida.

**24. Crear hidrología y predictores aluviales.** Para la base, distancia a cauce y densidad de red con limitación de cobertura conocida. Para aluvial: cartografiar terrazas y depósitos, incorporar MDT más fino, acondicionar drenaje, definir dirección/acumulación, cuencas, altura relativa al cauce y contexto aguas arriba. Distinguir terrazas antiguas de cauce actual; no restringir automáticamente los positivos a una franja arbitraria del río. Reservar cuencas/distritos para evitar que tramos conectados aparezcan a ambos lados del test. Salida: bloque aluvial y dominio de evaluación documentado. [Descargas oficiales de modelos de elevaciones del CNIG](https://centrodedescargas.cnig.es/CentroDescargas/modelos-digitales-elevaciones).

**25. Incorporar geofísica cuando sea cuantitativa.** Gravimetría: unidades y correcciones, anomalía de Bouguer u otra magnitud identificada; magnetometría: campo/anomalía, referencia y nivelado entre campañas; radiometría: canales y soporte real; magnetotelúrica: profundidad y naturaleza del modelo; petrofísica: ubicación, litología y representatividad. No interpolar una propiedad puntual sobre España sin soporte suficiente. Separar cobertura de campañas de valores físicos. Probar la mejora frente al conjunto básico en exactamente el mismo territorio de evaluación. Salida: modelos con geofísica como extensión, no requisito para V1.

**26. Construir `Grid_Master_Au`.** Unir por `cell_id` bloques de predictores, calidad, cobertura y etiquetas. Agregar múltiples indicios a una única celda y conservar tablas auxiliares de relación depósito–celda. No multiplicar filas por uniones muchos-a-muchos. Mantener las U como desconocidas. Guardar matriz en Parquet por particiones y geometrías aparte; no generar millones de polígonos pesados si fila/columna permiten reconstruirlos. Salida: matriz territorial versionada y manifiesto de variables permitidas.

### Fase E. Diseñar la evaluación y el aprendizaje presencia–fondo

**27. Congelar particiones externas y reserva final.** Construir bloques geográficos y asignar depósitos completos. Elegir tamaño a partir del objetivo de transferencia, dependencia espacial de covariables y distancias entre depósitos; contrastar, por ejemplo, 25/50/100 km como hipótesis, no valores universales. Introducir separación espacial entre entrenamiento y prueba y comprobar las distancias reales. Para aluvial considerar además conexión de cuencas. Buscar cinco particiones externas solo si los grupos lo permiten; reducirlas o replantear el ámbito si quedan particiones sin positivos. Salida: `spatial_splits` y mapa de grupos. La validación espacial requiere diseño explícito, no solo pasar números de grupo a `GroupKFold`. [Estudio sobre validación espacial](https://arxiv.org/abs/2005.14263).

**28. Separar prueba final y decisiones de desarrollo.** Reservar distritos completos si el número de depósitos independientes lo permite. Usar validación anidada en desarrollo: bucle externo para evaluar el procedimiento y bucle interno para elegir variables, algoritmo e hiperparámetros. Si se escoge un ganador después de comparar sus resultados externos, informar la posible selección optimista y usar la reserva para comprobarlo. Si no hay datos suficientes para reserva adicional, declarar esa limitación y evaluar el procedimiento completo de selección dentro del anidamiento. Salida: protocolo de evaluación cerrado.

**29. Generar U de entrenamiento dentro de cada partición.** Muestrear únicamente en la región de entrenamiento, con cobertura y área elegible definidas sin mirar los positivos de prueba. Ensayar un fondo estratificado territorialmente y una alternativa ligada a esfuerzo de observación verificable. Los indicios de otros minerales pueden servir como contraste de sesgo, pero no son ausencias de Au. Probar ratios U:P de 1:1, 3:1 y 10:1 de forma escalonada; registrar probabilidades de inclusión y pesos cuando correspondan.

Separar el buffer de incertidumbre alrededor de positivos de entrenamiento del buffer entre train/test. No vaciar el fondo de todo un distrito favorable con un radio universal de 5 km. Comparar radios motivados por precisión y agrupación, y no usar las posiciones de los depósitos reservados para facilitar el muestreo de entrenamiento. Los positivos de prueba solo se utilizan para evaluar. Salida: realizaciones de fondo con semilla, región, criterio y ponderación.

**30. Implementar referencia presencia–fondo y alternativa PU.** Primera referencia: clasificar P frente a U seleccionadas, documentando que U contiene posibles positivos no registrados. Después comparar bagging de distintos subconjuntos U, manteniendo exactamente la evaluación espacial. Empezar con 3–5 realizaciones en el piloto y ampliar a unas 20 en la variante final si la estabilidad lo justifica. PU no elimina automáticamente el sesgo: estimar probabilidad absoluta requiere hipótesis adicionales sobre prevalencia y mecanismo de registro. No asumir que los positivos conocidos son una muestra aleatoria de toda mineralización. [Trabajo original sobre PU con selección dependiente de características](https://proceedings.mlr.press/v94/bekker18a.html).

### Fase F. Entrenar y comparar modelos

**31. Crear pipelines sin fuga de información.** Separar numéricas/categóricas y columnas auxiliares. Regresión logística/KNN/SVM: imputación en entrenamiento y escalado; árboles: sin escalado obligatorio. Categóricas: desconocido explícito y codificación compatible con categorías nuevas. Códigos geológicos no se tratan como magnitudes continuas. Ajustar cualquier selección de variables dentro de la partición interna. Comprobar también que el early stopping, la calibración interna de SVM y otros mecanismos no introducen particiones aleatorias inadvertidas. Salida: constructores de pipelines y pruebas contra filtración de columnas.

**32. Entrenar referencias mínimas.** Incluir ranking aleatorio/constante para comparación territorial, una regla geológica sencilla predefinida y regresión logística regularizada. Un árbol pequeño puede servir como explicación didáctica. Medir con el mismo protocolo que RF. No usar accuracy del modelo mayoritario como criterio principal. Salida: primeras predicciones espaciales fuera de entrenamiento y resultados de referencia.

**33. Entrenar Random Forest.** Usar la matriz limpia P/U y los grupos congelados. Referencia inicial sugerida: 500 árboles, `min_samples_leaf` 5, `max_features='sqrt'`, semilla fija y profundidad sin limitar como un candidato, no como ganador. Ajustar en búsqueda interna una selección acotada de profundidad, tamaño mínimo de hoja, fracción de variables y pesos de clase. Por ejemplo, profundidades 8/16/sin límite, hojas 2/5/10/20 y `max_features` sqrt/0,5, usando búsqueda aleatoria de unas 20–30 configuraciones antes de ampliar.

No compensar simultáneamente ratio de fondo y `class_weight` sin estudiar su efecto. No utilizar OOB como resultado de generalización espacial. Guardar el pipeline completo, parámetros, variables, datos/versiones y predicciones por grupo. Salida: RF reproducible y evaluación OOF —predicciones realizadas sin entrenar en la zona evaluada—.

**34. Comparar alternativas de forma gradual.** Primero ExtraTrees y un boosting; después XGBoost/LightGBM y CatBoost si la cardinalidad geológica lo justifica. Naïve Bayes, KNN y SVM pueden completar el cuaderno comparativo del estilo del vino, pero no son dependencias del MVP. Mantener un presupuesto comparable de búsqueda, preprocesamiento adecuado y el mismo fondo de prueba. SVM/KNN pueden ser costosos al predecir todo el territorio. Salida: tabla de métricas, estabilidad por distrito, tiempo y memoria; ningún algoritmo gana por nombre.

**35. Ejecutar ablaciones y sensibilidad.** Comparar geología+estructuras; añadir relieve; añadir geoquímica sin Au; añadir Au; añadir hidrología; añadir geofísica donde exista. Contrastar clases frente a representación alternativa y 1 km frente a 500 m. Evaluar cambios en etiquetas de baja confianza, fondo y buffers. El contraste sin Au geoquímico muestra la dependencia de esa evidencia, pero Au externo no es fuga por sí mismo: se debe revisar su procedencia y posible influencia de minería/contaminación histórica. No explorar todo el producto cartesiano de modelos, radios, resoluciones y semillas. Salida: evidencia de qué bloques aportan mejora transferible.

### Fase G. Validar, explicar y decidir si el modelo se acepta

**36. Calcular métricas espaciales y territoriales.** Predecir todas las celdas evaluables del bloque retenido, no solo el fondo muestreado. Ordenar el territorio por score y medir depósitos independientes recuperados al priorizar 1/5/10 % del área terrestre elegible. En depósitos con varias celdas, definir antes cuándo se considera recuperado y contarlo una sola vez. Tratar empates de score con una regla reproducible que no use etiquetas. Informar por distrito, tipología, cobertura y tamaño de bloque.

La referencia aleatoria tiene recuperación esperada próxima a la fracción de área bajo su supuesto uniforme; acompañarla de referencias geológicas y análisis de sesgo. Informar Average Precision con su nombre exacto —no confundirla con integración trapezoidal de PR— y ROC-AUC en una muestra P/U de prueba fija. La precisión y el Brier frente a U no miden descubrimiento real de oro, porque U no es ausencia confirmada. Los intervalos se estimarán re-muestreando depósitos/bloques, no millones de píxeles como si fueran independientes.

**37. Explicar el modelo sobre datos retenidos.** Importancia por permutación por familia y por variable, SHAP en muestras espaciales y fichas de casos acertados/fallidos. Revisar artefactos de hojas, costa, cobertura, rutas de campañas y unidades raras. Variables correlacionadas reparten o enmascaran importancias; no interpretar un único gráfico como causalidad. Si las explicaciones motivan cambios, estos vuelven al circuito de desarrollo; el test final deja de ser final si se usa repetidamente para rediseñar.

**38. Estimar estabilidad y aplicabilidad.** Guardar dispersión entre semillas/fondos, particiones y modelos, indicando qué cambia en cada comparación. Reportar percentiles o desviación como estabilidad del procedimiento, no como intervalo de confianza físico de presencia de Au. Construir distancia/disimilitud en espacio de predictores y umbrales estimados desde entrenamiento/validación; marcar categorías geológicas nuevas y patrones de falta de datos. No inventar un umbral universal. Salida: score, estabilidad y máscara/índice de aplicabilidad. [Método de área de aplicabilidad de Meyer y Pebesma](https://arxiv.org/abs/2005.07939).

**39. Revisar criterios de aceptación.** Propuesta técnica: trazabilidad y pruebas críticas superadas; mejora territorial estable sobre referencias; desempeño reportado por distrito; ausencia de artefactos dominantes; cobertura/aplicabilidad explícitas; capacidad de reproducir inferencia. Como criterio estadístico deseable, la mejora pareada de recuperación al 5 % del área debe sostenerse al re-muestrear grupos. El umbral operativo de utilidad se fijará antes de evaluar, según el área que el equipo pueda investigar. No prometer AUC >0,9 ni que 790 registros garanticen un buen modelo. Si falla, volver a etiquetas/capas/muestreo y no publicar una versión como validada.

### Fase H. Generar mapas, objetivos y una entrega mantenible

**40. Reentrenar y predecir.** Una vez cerrado el diseño y obtenida la evaluación final, entrenar el modelo seleccionado con los datos autorizados para la entrega. Si se incorporan las antiguas zonas de test al ajuste final, conservar el resultado de evaluación anterior y distinguirlo de predicciones ajustadas. Inferir por bloques de celdas con el mismo pipeline, orden de columnas y máscaras. Salida: GeoTIFF/COG por modelo geológico, con NoData fuera de su dominio.

**41. Crear objetivos geológicos.** Delimitar áreas contiguas de alta favorabilidad con umbral de área fijado; documentar tamaño mínimo y cualquier suavizado. Mantener separados objetivos de roca y aluviales. Añadir área, score, estabilidad, aplicabilidad, coberturas, principales evidencias y cercanía a indicios conocidos solo como información posterior. No sumar los scores de modelos específicos ni usar `1-(1-p_roca)(1-p_aluvial)` como si fueran probabilidades independientes. Una vista general puede presentar ambos paneles o un ranking combinado claramente definido.

**42. Validar objetivos y preparar campañas.** Revisión experta de fichas y cartografía; seleccionar zonas de favorabilidad alta estable, alta incierta y algunos controles de menor score. Planificar observaciones/muestreo con protocolos y registro de negativos verificados cuando existan, sin confundir una visita sin hallazgo con ausencia demostrada. Registrar el diseño de campaña para evaluar el sistema prospectivamente. La selección de accesos y restricciones operativas se hará sobre la capa geológica, conservando ambos resultados separados.

**43. Entregar y versionar.** Proyecto QGIS con rutas relativas, mapas, objetivos, matriz, modelos completos, catálogo, diccionario y reporte. Añadir inferencia por coordenada que devuelva celda, versión, score, estado de cobertura y aplicabilidad; rechazar de forma informativa puntos fuera de dominio. Ejecutar desde un entorno limpio una reproducción del piloto y un control de igualdad de inferencia por lote/punto.

**44. Mantener el proyecto.** Actualización de fuentes con hashes, comparación de etiquetas/cobertura, incorporación controlada de campañas y revalidación antes de sustituir el modelo. Conservar versiones anteriores y fechas de información disponibles. El producto se amplía cuando mejora la evidencia, no solo al añadir más algoritmos.

## 6. Esquema mínimo de datos que debe quedar cerrado

| Grupo | Columnas propuestas | ¿Entra en X? |
|---|---|---|
| Identidad espacial | `cell_id`, `grid_version`, fila, columna, geometría/centroide, área terrestre | No; unión, cartografía y ponderación |
| Etiqueta | `label_state`, tipología revisada, confianza, número de indicios | No |
| Dependencia | `deposit_id` en tabla relacionada, `district_id`, bloque, partición | No; agrupación y validación |
| Geología | litología dominante, fracciones por grupo, edad, proporción de cuaternario | Sí, si se deriva de cartografía externa |
| Estructuras básicas | distancia a falla/cizalla, contacto intrusivo y cabalgamiento; densidad a 1/5/10 km | Sí, con procedencia y unidades |
| Geoquímica | clase Au/As/Sb/Bi/Hg/Cu/Pb/Zn/W o representación alternativa predefinida | Sí; una representación por elemento en la referencia |
| Relieve | elevación, pendiente, TPI con radio explícito, rugosidad definida | Sí, tras reconstrucción |
| Hidrología | distancia a cauce; para aluvial: terraza, altura relativa, cuenca y rasgos aguas arriba | Sí, según disponibilidad y soporte |
| Geofísica | magnitudes cuantitativas y derivados de escala justificada | Solo en extensión verificada |
| Calidad | máscara por fuente, fracción válida, origen/escala, aplicabilidad | Principalmente QA; su uso predictivo exige experimento de sesgo |
| Muestreo | realización U, semilla, probabilidad de inclusión, peso | No como predictor |

El número de columnas inicial será deliberadamente moderado, aproximadamente 25–50 antes de one-hot, como presupuesto de diseño y no límite rígido. Se aumentará con evidencia de mejora. Con unos cientos de depósitos efectivos, cientos de variables redundantes elevan el riesgo de memorizar peculiaridades regionales.

## 7. Organización del código y del cuaderno explicativo

Los siguientes directorios son **propuestos**, no existentes certificados:

```text
config/                  # objetivo, fuentes, rejilla, variables, experimentos
data/raw/                # fuentes congeladas o referencias inmutables a originales
data/interim/            # capas limpias y armonizadas
data/processed/          # rejilla, features, etiquetas y particiones
data/outputs/            # rasters finales y objetivos
src/geoau/io/            # lectura y descargas
src/geoau/clean/         # indicios, geometrías, catálogos
src/geoau/features/      # geología, estructuras, geoquímica, relieve, hidrología
src/geoau/sampling/      # particiones espaciales y fondo
src/geoau/models/        # pipelines, búsqueda, evaluación
src/geoau/inference/     # lotes, coordenadas, máscaras
notebooks/               # explicación, mapas y comparación
reports/                 # calidad, métricas y fichas
models/                  # pipelines seleccionados y manifiestos
tests/                   # controles que detectan fallos sustantivos
```

Los notebooks mostrarán explicación, código invocable, tablas, gráficos y decisiones, siguiendo el estilo del reto del vino. El procesamiento reutilizable residirá en `src`, evitando ejecutar manualmente cientos de celdas para regenerar un mapa.

| Notebook propuesto | Contenido |
|---|---|
| `00_configuracion_y_fuentes` | Pasos 01–06 |
| `01_indicios_limpieza_etiquetas` | Pasos 07–12 |
| `02_rejilla_armonizacion_cobertura` | Pasos 13–17 |
| `03_variables_geologia_estructuras` | Pasos 18–20 |
| `04_variables_geoquimica` | Pasos 21–22 |
| `05_variables_relieve_hidrologia_geofisica` | Pasos 23–25 |
| `06_matriz_territorial_y_particiones` | Pasos 26–28 |
| `07_fondo_y_pipelines` | Pasos 29–31 |
| `08_referencias_y_random_forest` | Pasos 32–33 |
| `09_comparacion_modelos_ablacion` | Pasos 34–35 |
| `10_validacion_explicacion_aplicabilidad` | Pasos 36–39 |
| `11_mapas_objetivos_y_entrega` | Pasos 40–44 |

## 8. Pruebas necesarias antes de aceptar resultados

| Control | Fallo que debe detectar |
|---|---|
| Identificadores y uniones | Ceros iniciales perdidos, fuentes concatenadas como si fueran observaciones nuevas, duplicación de celdas |
| Geometría y CRS | Coordenadas tabulares proyectadas interpretadas como grados, puntos fuera del ámbito, geometrías inválidas |
| Rejilla | Desfase de medio píxel, extensiones incompatibles o extracción distinta entre positivos y fondo |
| Clases y NoData | Clase 0 convertida en ausencia, códigos fraccionarios por bilinear, huecos rellenados con cero |
| Estructuras | Borde de hoja contado como falla, densidad por número de segmentos, duplicación GEODE/MAGNA |
| Topografía | Pendientes artificiales junto a NoData y ventanas con radio mal rotulado |
| Particiones | Depósito/celda compartido entre train/test, distancia menor al buffer, cuencas conectadas mal separadas |
| Preprocesamiento | Imputación/selección ajustada con test, columnas de etiqueta incorporadas a X |
| Evaluación territorial | Top 5 % calculado sobre muestras P/U en vez de sobre área real; depósitos contados varias veces |
| Inferencia | Cambio en orden/tipos de variables, modelo sin codificadores, predicción silenciosa fuera de cobertura |

Estas son pruebas de integridad científica y geoespacial. No basta con que el entrenamiento termine sin excepciones.

## 9. Hitos, dependencias y estimación de esfuerzo

Estimación orientativa para una persona técnica con revisión geológica disponible; se recalculará al medir geometrías, tiempos de procesamiento y recuperación de fuentes. Son días de trabajo, no fechas comprometidas. El trabajo aluvial detallado, geofísica y extensión insular puede añadir plazos externos de descarga o revisión.

| Hito | Pasos | Esfuerzo orientativo | Entregable y condición de salida |
|---|---|---|---|
| H0. Preparación | 01–06 | 2–4 días | Entorno, fuentes y alcance reproducibles |
| H1. Etiquetas | 07–12 | 4–8 días | Positivos revisados, depósitos agrupados y discrepancias justificadas |
| H2. Territorio | 13–17 | 3–6 días | Rejilla, máscara, capas armonizadas y cobertura |
| H3. Predictores básicos | 18–26, priorizando roca | 6–12 días | `Grid_Master_Au` con extracción uniforme |
| H4. Protocolo ML | 27–32 | 3–5 días | Grupos/fondo congelados, pipelines y referencias |
| H5. RF y comparación | 33–35 | 4–8 días | Resultados espaciales y ablaciones de candidatos |
| H6. Revisión | 36–39 | 3–6 días | Informe de validez, limitaciones y decisión de aceptación |
| H7. Producto | 40–44 | 3–5 días | Mapas, objetivos, inferencia y reproducción |

Total de referencia: **28–54 días de trabajo técnico**, aproximadamente 6–11 semanas a dedicación completa, condicionado a datos y disponibilidad geológica. No incluye una campaña de campo ni garantiza completar toda España o toda la geofísica en ese plazo. Un primer RF piloto puede aparecer antes de acabar el proyecto, pero solo después de disponer de etiquetas, features y particiones válidas.

Responsabilidades propuestas: perfil GIS/datos para carga y armonización; geólogo para etiquetas, dominios, clasificación de unidades/estructuras y objetivos; perfil ML para muestreo, modelos y validación. Una persona puede asumir varias funciones, dejando explícita la revisión geológica pendiente. No se asignan compromisos personales a Luis ni a otro integrante sin que el equipo los acuerde.

La ruta de dependencias es: **fuentes → etiquetas y rejilla → predictores territoriales → particiones y fondo → referencias/RF → validación → mapas**. La geofísica y el refinamiento local son ramas posteriores; la corrección de etiquetas y la separación espacial no se pueden posponer hasta después del entrenamiento.

## 10. Primer bloque de trabajo que recomiendo ejecutar

1. Crear configuración, entorno y manifiesto sin mover los originales.
2. Conciliar GPKG/CSV/Excel y producir el inventario Au revisable.
3. Resolver coordenadas problemáticas, agrupar depósitos y revisar tipologías.
4. Elegir piloto y reserva geográfica con el inventario ya depurado.
5. Crear máscara y rejilla de 1 km.
6. Limpiar una fuente estructural y unificar litología/edad.
7. Verificar clases geoquímicas y reconstruir relieve.
8. Construir matriz de todas las celdas del piloto y comprobar cobertura.
9. Congelar bloques, buffers y muestreo U; dejar el test aislado.
10. Ejecutar regresión logística y Random Forest con predicciones espaciales retenidas.

La primera demostración útil será una tabla que explique qué fuentes y depósitos se usaron, qué territorio quedó reservado y cuánto área prioriza el modelo para recuperar esos depósitos. Después se construirá el mapa de entrega con su incertidumbre y sus límites de aplicación.

**Archivos de apoyo a este plan:** `auditoria_2026-09-05/geopackages.json`, `rasters.json`, `tablas_comprobaciones.json`, `indicios_validacion.json`, `qgis_layers.json` y los textos extraídos. Los recuentos adicionales de `IndiciosII.csv` se verificaron conservando los códigos como texto al elaborar este plan. Las estimaciones de esfuerzo, prioridades, radios y configuraciones de modelos son propuestas de diseño, no resultados observados.
