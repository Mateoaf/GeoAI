## 19. Resultados diagnósticos comprobados

Las cifras siguientes se han leído y agregado desde `reports/fase_f/20260909T184735_016759Z/comparison_by_fold.csv`. Los validadores han recomputado las métricas a partir de las predicciones guardadas. Son medias de cinco folds con igual peso; ± indica desviación estándar entre folds, no intervalo de confianza ni incertidumbre física sobre presencia de oro.

| Procedimiento | Recuperación al 5 % del área | AP P/U media | ROC-AUC P/U media |
|---|---:|---:|---:|
| Constante con desempate por hash | 0,0543 ± 0,0214 | 0,0127 | 0,5000 |
| Aleatorio reproducible | 0,0500 ± 0,0129 | 0,0129 | 0,4849 |
| Regla geológica ilustrativa | 0,0632 ± 0,0423 | 0,0178 | 0,6336 |
| Regresión logística | 0,4398 ± 0,1159 | 0,1027 | 0,8719 |
| Random Forest | 0,5220 ± 0,1097 | 0,1654 | 0,8965 |
| ExtraTrees | 0,4617 ± 0,1306 | 0,1355 | 0,8905 |
| HistGradientBoosting | 0,5339 ± 0,0622 | 0,1524 | 0,9032 |

El valor de 0,5339 significa que, en promedio entre folds, se recupera aproximadamente el 53,39 % de las **celdas con candidatos de inventario** al priorizar hasta el 5 % de su área de test. No significa 53,39 % de probabilidad de encontrar oro, ni 53,39 % de depósitos revisados, ni 53,39 % de éxito prospectivo en lugares desconocidos.

RF tiene mayor AP media que boosting, pero boosting mayor recuperación al 5 %. No es contradicción: las métricas valoran aspectos distintos del ranking y del conjunto P/U. Según el plan, la métrica operativa primaria es la recuperación territorial. Aun así, elegir una familia global después de ver esta tabla consumiría información externa de desarrollo y requeriría validación posterior; F conserva la selección de familia por resultados internos de cada fold.

### 19.1. Ablaciones y bagging

| Variante | Recuperación media al 5 % | Condición de comparación |
|---|---:|---|
| Geología + estructuras | 0,4368 | RF fijo, 150 árboles, ratio 3 |
| Añadir relieve | 0,4442 | Mismo diseño y soporte |
| Añadir As/Sb/Bi | 0,4662 | Mismo diseño y soporte |
| Añadir Au | 0,4688 | Mismo diseño y soporte |
| Añadir hidrología | 0,5066 | Referencia completa de la ablación fija |
| Proporciones en lugar de las cuatro modas | 0,5043 | Conserva hidrología; mismo RF fijo |
| Bagging de tres realizaciones U | 0,5093 | RF elegido internamente; comparar con RF 0,5220 |

En este ensayo, el incremento medio al añadir Au después de As/Sb/Bi es pequeño, alrededor de 0,0026. Hidrología muestra un incremento mayor, alrededor de 0,0378 respecto a la variante anterior. Son diferencias exploratorias sobre celdas candidatas y un mismo territorio con geoquímica disponible. No se han calculado aquí intervalos pareados por depósitos/bloques para afirmar significación o transferencia general. La mejora no debe interpretarse como causalidad geológica.

La variante de proporciones no supera claramente a la modal en la media de este contraste, y bagging no mejora recuperación media respecto al RF individual seleccionado. Ambos resultados son útiles porque impiden asumir que más columnas o más miembros siempre mejoran la métrica principal. Tampoco prueban que esas variantes sean inútiles bajo etiquetas o protocolos revisados.

## 20. Correspondencia con los 44 pasos del plan

«Implementado» describe código y artefactos técnicos comprobables. «Parcial» indica funciones disponibles pero requisitos o productos incompletos. «Pendiente» no significa necesariamente un defecto: el plan prevé extensiones condicionadas a datos y revisión.

| Paso | Entrega prevista | Estado y ubicación efectiva |
|---:|---|---|
| 01 | Especificación de experimento y piloto | Parcial: `project.yaml`; piloto y objetivos científicos por cerrar |
| 02 | Entorno reproducible y pruebas GIS | Implementación técnica A y dependencias por fase; falta un cierre único de dependencias de F |
| 03 | Inventario/manifiesto de fuentes | Implementado en 00 con hashes y estados |
| 04 | Lectores y acceso a datos | Implementado en `local_sources.py`; geometría avanzada se resuelve en C |
| 05 | Catálogo y clasificación de fuentes | Implementado técnicamente en A; procedencia/licencias/semántica no todas verificadas |
| 06 | Resolver o recuperar entradas necesarias | Parcial: pendientes A y ocho capas adicionales integradas en C; no descarga desde 00 |
| 07 | Conciliación de indicios | Implementada en 01; discrepancias no resueltas individualmente |
| 08 | Normalizar conservando originales | Implementado; celda 11 de 01 elimina el indicador propagado de conflicto |
| 09 | Verificación territorial y administrativa | Parcial: QC básico y cuarentena; máscara/admin de B sin configurar |
| 10 | Códigos, posiciones y depósitos | Parcial: posiciones/grupos de proximidad; sin depósitos/distritos revisados |
| 11 | Contexto aurífero revisado | Plantilla y validadores implementados; cero positivos revisados |
| 12 | Representatividad y sesgo | EDA de registros; análisis por depósitos/distritos y esfuerzo pendiente |
| 13 | Máscara y rejilla | Implementado en 02; máscara regional candidata, sólo componente principal |
| 14 | Soporte uniforme por variable | Diccionario C y definición efectiva D implementados |
| 15 | Reproyección y saneamiento | Implementado con QC y caché; linealización contrastada en muestra |
| 16 | Alineación de rásteres | Implementada para mallas exactamente anidadas 500 m→1 km |
| 17 | Cobertura por ámbito/familia | Implementada; la cobertura de levantamientos estructurales sigue desconocida |
| 18 | Litología, edad y unidades | Parcial: cartografía regional y asociaciones explícitas; recintos detallados y jerarquía geológica pendientes |
| 19 | Variables estructurales | Base GEODE implementada; densidades aproximadas y semántica pendiente |
| 20 | Estructuras avanzadas | Pendiente: intersecciones, orientación, pliegues y buzamientos como predictores |
| 21 | Geoquímica clasificada | Implementada con QC RGB; leyenda, unidades, medio y extracción aún por validar |
| 22 | Geoquímica analítica cuantitativa | Pendiente/opcional; no se han creado análisis a partir de colores |
| 23 | Relieve reconstruido | Implementado con máscara, fórmulas y radios explícitos |
| 24 | Hidrología/aluvial | Distancia/densidad regional implementadas; terrazas, cuencas y altura relativa pendientes |
| 25 | Geofísica cuantitativa | Pendiente; C incorpora diagnóstico de fuentes, no bloques predictivos aprobados |
| 26 | `Grid_Master_Au` y roles | Implementado en 06; 168 candidatos, sin predictores aprobados |
| 27 | Particiones espaciales y separación | Implementado diagnóstico en 07; faltan grupos y justificación científica |
| 28 | Reserva y anidamiento | Implementado técnico; reserva de unidades geográficas, no distritos acreditados |
| 29 | Muestras U por entrenamiento | Implementado en 08: 180 diseños; alternativa por esfuerzo pendiente |
| 30 | P/U y bagging | Contrato en 09, clasificadores en F, bagging en 14; sin estimar prevalencia |
| 31 | Pipelines sin aprendizaje global | Implementado en 10, guard y pruebas de transformaciones por train |
| 32 | Referencias mínimas | Implementadas constante/aleatoria/regla/logística en 11 |
| 33 | Random Forest anidado | Ejecutado diagnóstico; tres candidatos, no búsqueda de 20–30 |
| 34 | Comparación gradual | Cuatro familias implementadas; alternativas avanzadas opcionales pendientes |
| 35 | Ablaciones y sensibilidad | Seis conjuntos y tres fondos; 500 m, etiquetas, buffers y geofísica pendientes |
| 36 | Métricas territoriales y espaciales | Núcleo ya implementado en F; falta cierre G por depósitos/distritos e intervalos por grupos |
| 37 | Explicación sobre retenidos | Pendiente: permutación por familias, SHAP y revisión sistemática de casos/artefactos |
| 38 | Estabilidad y aplicabilidad | Parcial: dispersión del bagging; no hay área de aplicabilidad ni diagnóstico completo de extrapolación |
| 39 | Criterios de aceptación | Pendiente; no hay aprobación científica ni operativa |
| 40 | Reentrenamiento e inferencia final | Pendiente; scores OOF no son reentrenamiento final de entrega |
| 41 | Objetivos geológicos | Pendiente; no hay delimitación final roca/aluvial aprobada |
| 42 | Revisión de objetivos/campañas | Pendiente; requiere evidencia y revisión geológica |
| 43 | Entrega, QGIS e inferencia puntual | Pendiente; la API y rutas del README histórico no existen como producto actual |
| 44 | Mantenimiento y revalidación | Parcial: fundamentos de hashes/versionado; sin ciclo de sustitución de modelo validado |

### 20.1. Cambios relevantes respecto al documento de septiembre 5

La afirmación histórica de que faltan módulos, pruebas y modelos ya no describe todo el repositorio: existen `src/geoau`, 62 pruebas y modelos dentro de F. En cambio, la advertencia de no usar los benchmarks antiguos del README continúa siendo pertinente. Los archivos vacíos de la primera auditoría han cambiado de estado tras recuperación; el inventario A más reciente sólo informa un archivo sin datos.

El diseño llegó hasta una ejecución diagnóstica peninsular antes de cerrar el piloto y los positivos revisados. Puede ser útil para comprobar ingeniería y detectar problemas, pero no constituye el hito V1 validado del plan. El siguiente avance científico prioritario no es agregar más algoritmos: es completar y propagar revisión de etiquetas, depósitos, cartografía y protocolo.

## 21. Hallazgos priorizados y acciones concretas

Se distingue entre hechos reproducidos, riesgos inferidos del código y tareas científicas pendientes. La prioridad indica el impacto sobre la interpretación o reproducibilidad; no implica que todos los puntos sean errores que hayan afectado a los resultados actuales.

### H01 — Falta la evidencia necesaria para presentar un modelo validado

**Prioridad alta; hecho comprobado.** B/D/E contienen cero positivos revisados; D no aprueba columnas de entrenamiento; no hay depósitos/distritos y cartografía territorial revisada ni criterios de aceptación cerrados. Los controles científicos y producción están correctamente bloqueados. Evidencia: `control_cierre.json` de B–F, `feature_allowlist.json` D y `readiness.json` E.

**Acción:** completar revisión documentada por indicio y depósito, justificar ámbito y particiones y generar nuevas ejecuciones dependientes. Hace falta además una vía versionada para aprobar predictores: `assemble` escribe actualmente una lista aprobada vacía de forma incondicional. La fase de revisión debe aportar un artefacto auditable de aprobación; editar manualmente un JSON sellado rompe la cadena y no es un procedimiento de aceptación.

### H02 — El notebook 01 pierde `conflicto_au` en ejecución secuencial

**Prioridad alta para incorporar revisiones; reproducido.** La celda 10 propaga conflictos por código y la 11 reconstruye `normalizados` sin esa columna. La conciliación independiente sigue conservando conflictos, pero el inventario que alimenta revisiones y QC pierde ese indicador. Los tests del módulo no ejecutan esta secuencia completa de celdas.

**Acción:** una única normalización y propagación posterior de conflictos; comprobar al final de la secuencia que el indicador existe y coincide con la conciliación. No es necesario rehacer el algoritmo de normalización para resolver un error de orquestación del notebook.

### H03 — Una celda de visualización modifica candidatos usados posteriormente

**Prioridad alta para datos futuros; riesgo confirmado en el código, sin pérdida efectiva demostrada en los Au actuales.** La celda 24 de 01 convierte coordenadas y reasigna `candidatos = candidatos.dropna(...)`. Un registro sin coordenadas quedaría fuera de la rama de etiquetas/exportación por haber dibujado un mapa. Su persistencia en `qc` no evita una discrepancia entre el inventario y las tablas específicas Au.

**Acción:** crear `candidatos_mapa = candidatos.copy()` y filtrar sólo esa vista. Registrar candidatos excluidos del cálculo espacial por motivo, conservándolos en las tablas de revisión. Añadir una comprobación de invariancia del conjunto de IDs antes/después de figuras.

### H04 — Reproducción de F ligada a una carpeta externa antigua

**Prioridad alta de portabilidad; hecho comprobado.** Los 60 metadatos de modelos incluyen `sample_path` absoluto bajo `.../Proyecto Con Luis/...`, fuera de la raíz actual `.../GeoAI/GeoAI`. `scripts/validar_fase_f.py` abre directamente esa ruta. En este equipo la carpeta antigua todavía existe, los hashes concuerdan y la validación pasa; eso no demuestra reproducción autónoma de una copia trasladada a otro equipo.

**Acción:** guardar ruta relativa al proyecto o a la ejecución E junto a su hash. En la validación resolverla desde la raíz actual y comprobar pertenencia a la E declarada. Conservar la ruta de origen como metadato informativo si interesa. La comprobación definitiva debe realizarse desde una copia aislada que no pueda leer la carpeta histórica.

### H05 — El ejecutor raíz y buena parte del README son incompatibles con la estructura actual

**Prioridad alta de uso; ausencia de destinos comprobada.** `run_pipeline.py` invoca `src/build_ml_dataset_v2.py`, `src/run_spatial_experiments_v2.py`, `src/build_interactive_map_v2.py` y `tests/test_geoai_hardened_suite.py`, ninguno presente. El README anuncia otro paquete, otros notebooks, 906 positivos, métricas y una API por coordenadas que no corresponden a esta cadena.

**Acción:** reescribir el punto de entrada alrededor de los ejecutores reales, o marcar claramente el CLI como histórico hasta reemplazarlo. Consolidar README con el estado A–F, rutas correctas y los límites actuales. Los avisos al principio del README ayudan, pero no eliminan las instrucciones contradictorias posteriores.

### H06 — Pérdida de media longitud en un caso de borde terrestre

**Prioridad media; reproducción sintética, impacto nacional no cuantificado.** `lines` pasa a `line_lengths` el borde del rectángulo total del ráster. `line_lengths` considera compartido un segmento sobre borde de celda que no esté en ese borde exterior. Si sólo una celda con tierra participa y su borde coincide con la costa sobre una línea de rejilla, reparte la mitad como si existiera una segunda celda contabilizada. En el caso mínimo revisado, una traza de 10 m produce 5 m.

**Acción:** repartir por multiplicidad real de celdas procesadas o reconocer los bordes del dominio terrestre efectivo, manteniendo el reparto correcto entre teselas. Incluir ejemplos de costa/huecos sobre rejilla y comprobar conservación de longitud. No se afirma que todas las densidades actuales estén divididas por dos: el caso requiere una coincidencia geométrica específica.

### H07 — Ausencia de traza y distancia superior al límite comparten `NaN`

**Prioridad científica alta; diseño explícito con consecuencias.** Las distancias quedan ausentes cuando no hay traza a 10 km, y las densidades pueden valer cero sin huella de levantamiento acreditada. F imputa medianas; una columna totalmente ausente recibe cero dentro del pipeline. Esto puede hacer que una celda muy alejada o no cartografiada reciba una distancia típica, o cero en un train sin observaciones de esa variable.

**Acción:** separar censura por radio de falta de cobertura cuando las fuentes lo permitan. Estudiar distancia truncada acompañada de indicador, exclusión de variables casi vacías o dominios de aplicabilidad. Las alternativas deben contrastarse dentro de la validación interna y sin introducir máscaras de campaña como predictores de forma inadvertida. El hecho de que la imputación no use test evita una fuga estadística, pero no resuelve la semántica del dato ausente.

### H08 — Geoquímica validada contra paletas locales, todavía no contra significado analítico

**Prioridad científica alta; limitación reconocida.** La coherencia RGB descarta clasificaciones dudosas, pero no certifica medio, extracción, umbral, unidad ni procedencia del dato cartográfico. La pérdida de soporte Zn/W muestra además que exigir todos los elementos cambia mucho el ámbito.

**Acción:** revisar leyendas oficiales y metadatos de cada capa; conservar mapas de aceptación/rechazo y estudiar independencia de minería/contaminación y soporte sedimentario. Si se recuperan valores analíticos, crear una versión distinta, sin presentar puntos medios de intervalos como medidas continuas.

### H09 — Geología regional, redundancia y estructuras incompletas

**Prioridad científica media/alta.** D usa litología/edades regionales, aunque C tenga recintos detallados. Retiene dominantes, fracciones y asociaciones superpuestas; el conjunto completo F supera el presupuesto inicial de variables del plan. Pliegues, orientaciones, geofísica y aluvial detallado aún no están implementados como bloques.

**Acción:** revisar jerarquía geológica y elegir representaciones según evidencia, con control de cardinalidad y redundancia. La selección estadística aprendida debe entrar dentro del pipeline interno. Validar el valor de datos detallados antes de expandir la matriz por disponibilidad de archivos.

### H10 — La búsqueda mezcla efecto del ratio y del hiperparámetro

**Prioridad media; limitación experimental explícita.** Con tres candidatos, cada ratio corresponde a parámetros diferentes. Las medias por candidato sirven para seleccionar una alternativa conjunta, pero no identifican cuánto de la diferencia se debe al ratio o a la complejidad del modelo. El mismo número de candidatos entre familias tampoco iguala coste computacional.

**Acción:** una vez revisado el protocolo, predefinir una búsqueda mayor y un contraste pequeño que mantenga parámetros al cambiar ratio. No explorar todas las combinaciones sobre el test externo ni elegir una configuración después de ver la reserva.

### H11 — La reserva y los grupos aún no responden a la unidad geológica del plan

**Prioridad científica alta.** La reserva de aproximadamente 15 % de unidades contiene sólo 23 de las 666 celdas candidatas elegibles, alrededor de 3,45 %. Los bloques del diagnóstico evitan una partición puntual aleatoria, pero falta explicar su relación con distritos, independencia efectiva y objetivo de transferencia.

**Acción:** revisar depósitos y territorio antes de una evaluación científica, estudiar dependencia espacial y diseñar reserva geológica con capacidad informativa. La lectura de estos recuentos no autoriza escoger una reserva nueva por una métrica favorable. No se ha abierto aquí la reserva para calcular scores.

### H12 — Reejecución y generadores de notebooks tienen comportamientos diferentes

**Prioridad media de mantenimiento.** Los generadores 00/01/02 escriben sus destinos sin protección de existencia; los generadores D/E/F conservan notebooks existentes. Por tanto, ejecutar un creador antiguo puede borrar anotaciones/salidas manuales, mientras ejecutar uno posterior no actualiza cambios en la plantilla. A sí registra un hash del tipo/fuente del cuaderno 00, pero no hay un contrato uniforme que vincule las salidas antiguas de toda la serie al texto actual de cada celda. Un contador de ejecución o un output sin error no demuestra esa correspondencia.

**Acción:** separar creación, actualización y ejecución, con respaldo o propuesta de diferencias para actualizaciones. Sellar también el contenido fuente de notebooks consumidos cuando se publican resultados y usar ejecuciones completas desde kernel limpio para comprobar su orquestación. Esta revisión no ha ejecutado generadores ni sobrescrito cuadernos.

### H13 — Dependencias y versiones no tienen una única fuente de verdad

**Prioridad media de instalación.** `pyproject.toml`, `requirements.txt` y archivos por fase no enumeran exactamente el mismo entorno. Por ejemplo, el paquete base no declara todos los componentes usados por notebooks y fases actuales; los locks A/D no constituyen un lock completo F. El entorno local tiene scikit-learn 1.9.0 y pasa unittest; `pytest` no estaba instalado, aunque se mencione en dependencias generales.

**Acción:** consolidar dependencias base y extras por fase, fijar un entorno completo probado y documentar la orden real de pruebas. No deducir incompatibilidad de Python 3.14 sólo por el aviso antiguo del plan: el entorno concreto de esta revisión ejecutó satisfactoriamente las pruebas. Tampoco deducir que cualquier instalación mínima declarada reproduzca ese entorno.

### H14 — Condiciones de calidad no equivalen todavía a una máscara de aplicabilidad

**Prioridad alta para publicación.** Los conjuntos elegibles y el estado de categorías desconocidas protegen aspectos de soporte, pero no miden novedad multivariante, cambio de dominio geológico ni representatividad respecto a train. El bagging guarda dispersión de tres ajustes y no satisface todo el paso 38.

**Acción:** implementar G con explicaciones sobre datos retenidos, diagnóstico de extrapolación y reglas de no evaluable. Después cerrar criterios de aceptación y H. Un mapa suave de scores o varias métricas altas no sustituyen esa decisión.

## 22. Código auxiliar e histórico

### 22.1. Scripts de adquisición geoquímica

Los scripts de Au/As/Sb/Bi y el batch de Hg/Cu/Pb/Zn/W siguen una secuencia similar: fijar rutas y paleta; solicitar imagen renderizada del servicio; clasificar colores por distancia mínima; crear TIFF de clase y valores representativos/límites; vectorizar clases; y, cuando corresponde, muestrear sobre el mismo inventario de indicios. El número de filas enriquecidas no es número de muestras nuevas.

En `generar_mapa_geoquimica_oro.py`, `clasificar_pixeles` acepta los píxeles con alfa no nulo y elige `argmin` sin umbral de rechazo. `generar_geotiff` guarda cuatro bandas derivadas de esa clasificación y `generar_vector_geopackage` produce polígonos de clases. Las etiquetas de funciones que hablan de valores continuos o atributos analíticos son más fuertes que lo que realmente crean. El control de 04 mejora esta debilidad al exigir coherencia RGB, sin inventar análisis químicos.

Estos scripts contienen rutas históricas y pueden descargar/escribir datos. La fase D sólo lee sus constantes mediante AST; no los ejecuta ni necesita importar sus efectos secundarios. Para regenerar fuentes habría que crear una ejecución de adquisición versionada con parámetros y metadatos adecuados.

### 22.2. Dos implementaciones históricas de relieve que no deben confundirse

`descargar_mdt_cnig.py` solicita elevación, la reproyecta/remuestrea y calcula gradientes y estadísticas locales tras sustituir huecos por cero para ciertas operaciones. Su banda denominada TRI es una desviación local basada en momentos; su comentario de ventana 3×3 como radio 1,5 km no representa correctamente ese soporte.

`generar_topografia_mdt_cnig.py` utiliza otra implementación: copia una respuesta WCS con offsets redondeados, calcula derivadas tipo Sobel, TPI respecto a ocho vecinos y una raíz de media de diferencias cuadráticas usando `np.roll`. El redondeo de offsets puede desalinear datos si el origen recibido no cae en la rejilla; `np.roll` conecta bordes opuestos en sus desplazamientos. Tampoco debe generalizarse a este script la fórmula exacta de TRI del anterior: son derivados distintos.

El notebook 05 corrige la dependencia de esas bandas reconstruyendo relieve desde la banda de elevación con definiciones explícitas. Queda pendiente acreditar la procedencia y precisión de la elevación fuente: recalcular derivadas no corrige retroactivamente un posible error de georreferenciación en un MDT ya producido.

### 22.3. Ejecutores y validadores

`scripts/ejecutar_notebook_00.py`, 01 y 02 usan un kernel temporal configurado con `sys.executable`, ejecutan desde `notebooks/` y guardan la salida cuando termina correctamente. Los ejecutores D/E/F permiten `--desde`/`--hasta`, transmiten progreso y guardan un `.failed.ipynb` en caso de error. Esto ayuda a inspeccionar fallos sin reemplazar el cuaderno original con una ejecución incompleta.

Los validadores D/E/F revisan productos sin recalcular la cadena nacional. D comprueba matrices y roles; E recorre muestras, reservas, buffers y pesos; F reconstituye selecciones internas, recomputa métricas, comprueba imputación/categorías aprendidas y reproduce predicciones de control. Su resultado depende también de que los metadatos apunten a las muestras correctas, incluida la limitación de rutas absolutas de H04.

## 23. Comprobaciones realizadas y sus límites

### 23.1. Suite de pruebas existente

Se ejecutó desde la raíz actual:

```powershell
.\.venv-fase-a\Scripts\python.exe -m unittest discover -s tests -v
```

Resultado: **62 pruebas, todas satisfactorias**, en 9,552 segundos según unittest. Se observaron avisos de futura deprecación de operaciones de `Affine`, no fallos. El código operativo no se modificó para conseguir este resultado.

| Archivo | Pruebas | Qué comprueba principalmente |
|---|---:|---|
| `test_local_sources.py` | 6 | Ceros de ID, CSV, rutas, curvas, máscaras, ventanas y hashes |
| `test_labels.py` | 6 | Tokens, originales, conciliación, geometría, revisión y proximidad |
| `test_territory.py` | 11 | Área terrestre, costa/huecos, clases, alineación, geometría y paginación |
| `test_additional_layers.py` | 3 | Conservación de puntos/Z, QC angular y restricciones de caché |
| `test_features.py` | 14 | Intersecciones, distancias, longitudes, relieve, RGB, matriz y escritura |
| `test_evaluation.py` | 12 | Grupos, separación, muestras, autorización, hashes y anidamiento |
| `test_training.py` | 10 | Guard, imputación por train, categorías, métricas, serialización y selección interna |

Son pruebas sustantivas con ejemplos conocidos y algunos flujos sintéticos integrados. No constituyen una ejecución completa de los 15 notebooks ni cubren todas las decisiones geológicas. En particular, no detectaban la sobrescritura entre celdas 10/11 de 01 ni el caso costero concreto de H06.

### 23.2. Validadores sobre productos reales

| Comprobación | Resultado de esta revisión | Alcance |
|---|---|---|
| `scripts/validar_fase_d.py` | Correcto, código 0 | Matriz, particiones, roles, etiquetas, rangos y hashes |
| `scripts/validar_fase_e.py` | Correcto, código 0 | 180 muestras; hashes, anidamiento, reserva, distancias, etiquetas y pesos |
| `scripts/validar_fase_f.py` | Correcto, código 0 | 60 pipelines y 85 archivos OOF; selección, imputación, categorías, métricas y bagging |

F reproduce **15 predicciones de control por pipeline**, seleccionadas a lo largo del archivo de cada modelo; no se volvió a predecir todo el territorio con cada modelo. Las métricas de comparación sí se recomputaron desde los scores completos ya guardados. Las medianas, escalas y categorías se contrastaron con las muestras que indica cada metadato. Los logs se conservan en `validacion_fase_d.txt`, `validacion_fase_e.txt`, `validacion_fase_f.txt` y el resumen en `resultado_validadores.json`.

### 23.3. Reproducciones y revisión estática complementarias

Se validó mediante AST la sintaxis de las 95 celdas y se construyó un inventario de índices, contadores, líneas, instrucciones ejecutables y hashes de fuente. No había outputs de tipo `error` guardados en las celdas inspeccionadas; los contadores guardados no prueban que el texto actual se ejecutase de principio a fin.

Se reprodujo la desaparición de `conflicto_au` al repetir normalización, y el reparto de media longitud en el caso geométrico descrito. Se verificó que todos los metadatos de modelos utilizan rutas absolutas de muestras fuera de la raíz actual. Una prueba ilustrativa del pool confirma que territorio con candidato no revisado puede entrar en U cuando sólo se seleccionan los P revisados: eso es compatible con PU si se conserva su significado desconocido, pero requiere una política explícita al tratar candidatos rechazados u objetivos diferentes.

No se han auditado de nuevo todas las geometrías originales entidad por entidad, verificado todas las licencias y leyendas, descargado fuentes, revisado depósitos como geólogo ni evaluado la reserva. Los checks y cifras se refieren al estado local y a la cadena de ejecuciones identificada en este informe.

## 24. Secuencia propuesta para completar el proyecto

1. **Coherencia del código de trabajo.** Corregir sobrescrituras de 01, evitar mutaciones desde figuras, eliminar dependencia de rutas externas en modelos, resolver el caso de borde de longitudes y consolidar CLI/documentación. Verificar desde una copia aislada y un kernel limpio que el flujo utiliza los archivos previstos.
2. **Etiquetas y unidades geológicas.** Incorporar revisión documentada de candidatos y coordenadas, identificar depósitos/distritos y delimitar el piloto por información disponible. Registrar descartes y tipologías sin convertir desconocidos en ausencias.
3. **Aprobación de variables.** Validar diccionarios y semántica de estructuras/geoquímica, revisar faltantes y cobertura, definir predictores aprobados mediante un artefacto versionado. Mantener separadas extensiones cuantitativas todavía sin soporte.
4. **Nuevo protocolo E.** Justificar bloques/buffers, reserva y grupos; para aluvial incorporar cuencas. Congelar decisiones y comparar procedimientos dentro del anidamiento con un conjunto de prueba común.
5. **Entrenamiento F revisado y fase G.** Ejecutar búsqueda acotada, analizar mejoras pareadas por grupos, explicaciones retenidas, artefactos y aplicabilidad. Acordar aceptación antes de utilizar la reserva final como contraste decisivo.
6. **Entrega H.** Sólo tras aceptación, reentrenar según la política fijada, producir mapas con cobertura/aplicabilidad, delimitar objetivos geológicos, preparar inferencia por coordenada y comprobar equivalencia entre lote y punto. Conservar evaluación anterior separada del ajuste final.

El valor actual del repositorio es una base técnica verificable para recorrer esa secuencia. Su mayor necesidad de mejora científica es convertir candidatos y cartografía disponible en evidencia revisada y un dominio de aplicación defendible; el número de algoritmos ya implementados es suficiente para iniciar esa validación cuando los datos estén listos.

## 25. Evidencias y referencias

Los enlaces técnicos principales remiten a fuentes locales primarias: [plan de prospectividad](../PLAN_PROSPECTIVIDAD_AURIFERA_ESPANA.md), [configuraciones](../../config), [módulos geoau](../../src/geoau), [pruebas](../../tests) y [ejecuciones guardadas](../../reports). Los documentos de fase se han contrastado con el código y los productos, sin tomar sus instrucciones como nuevas autorizaciones de trabajo.

Los anexos de esta revisión son [inventario de celdas](inventario_celdas.csv), [hashes de fuentes](fuentes_analizadas_sha256.json), [evidencias calculadas](evidencias.json), [métricas diagnósticas](metricas_diagnosticas.csv), [ablaciones](ablaciones_diagnosticas.csv), [resultados de validadores](resultado_validadores.json) y el [script de comprobación](comprobar_evidencias.py). Las explicaciones autorales se conservan en los cinco archivos Markdown de composición y el generador del informe verifica cobertura íntegra de celdas.

Se consultaron el 10 de septiembre de 2026 las fuentes técnicas primarias enlazadas en los apartados correspondientes: prevención de fuga, SimpleImputer y Average Precision de scikit-learn, y Bekker/Davis sobre PU. Esas referencias respaldan las definiciones metodológicas citadas; los recuentos, métricas y hallazgos del repositorio proceden de los archivos locales y de las comprobaciones descritas.
