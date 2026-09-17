# Análisis técnico y metodológico del código de prospectividad aurífera

Fecha de revisión: **10 de septiembre de 2026**. Proyecto inspeccionado: `GeoAI/GeoAI`. Informe basado en el código y productos locales presentes durante esta revisión.

## 1. Alcance, lectura y conclusión principal

El proyecto dispone de una cadena técnica sustancial desde el inventario de fuentes hasta el entrenamiento espacial anidado. Su resultado actual es un **experimento diagnóstico de favorabilidad relativa con candidatos del inventario**, todavía sin cierre científico de etiquetas, predictores, protocolo ni validación final. La existencia de modelos serializados y métricas reproducibles demuestra que hay una implementación ejecutada; no demuestra todavía capacidad contrastada de descubrimiento de depósitos nuevos.

La referencia a «14 notebooks» se ha interpretado como la serie que termina en el número 14. En disco existen **15 cuadernos, del 00 al 14**, que contienen **95 celdas de tipo código**, 91 con instrucciones ejecutables y cuatro vacías o compuestas exclusivamente por comentarios. Su fuente suma 786 líneas según `splitlines()`. Se explican todas las celdas, incluidas las exploratorias y las redundantes. Los números de celda utilizados son **índices del JSON desde cero**; se muestra también su posición desde uno. El contador `In[n]` guardado no identifica la posición de la celda y puede pertenecer a sesiones anteriores.

Se han leído los siete módulos funcionales de `src/geoau`, sus configuraciones, los ejecutores y validadores, las pruebas, los scripts históricos que explican la procedencia de los rásteres, el plan y documentación asociada. El cuaderno del vino en `informes/` es una referencia metodológica ajena a la serie de prospectividad y no se incluye en el análisis exhaustivo de celdas. Los cuadernos 15 y 16 aparecen previstos en el plan y no existen en la serie implementada.

El plan adjunto se trata como **documentación a contrastar**. Sus propuestas de descargas, entrenamiento, revisión experta o publicación no se han interpretado como órdenes nuevas del usuario. Este encargo consiste en analizar y redactar un informe: se han conservado los notebooks y el código operativo, incluido el cambio previo que Git ya registraba en el notebook 03.

La revisión combina cuatro niveles de evidencia: lectura estática de instrucciones y funciones; inspección de resultados persistidos; ejecución de la suite existente y de validadores de productos; y reproducciones pequeñas de comportamientos concretos. No se han vuelto a ejecutar los 15 notebooks ni se ha repetido el geoprocesamiento nacional o la búsqueda de modelos. Las salidas antiguas guardadas en una celda se describen como tales, sin afirmar que fueron producidas por el texto actual de esa misma celda.

### 1.1. Cómo utilizar el informe

Cada capítulo indica el propósito del notebook, sus entradas y salidas, la lógica delegada a Python y su relación con el plan. A continuación aparece una ficha por celda con el código original y una explicación de lo que consume, transforma, muestra o escribe. Al final se reúnen las diferencias con los 44 pasos del plan, los hallazgos priorizados y los límites de las comprobaciones.

Los enlaces a código remiten a los archivos del repositorio. Los intervalos de líneas se dan en el texto, porque corresponden a la copia analizada; el anexo `fuentes_analizadas_sha256.json` permite identificarla exactamente. La explicación de las funciones es necesaria: desde el notebook 03 una llamada de una sola línea puede desencadenar miles de operaciones espaciales, verificaciones de archivos y escritura de productos.

### 1.2. Inventario de la serie

{{INVENTARIO}}

### 1.3. Arquitectura efectiva

```text
Fuentes locales + config/project.yaml
  └─ 00 / local_sources.py → A: catálogo, hashes, lectura
       └─ 01 / labels.py → B: conciliación, geometría, candidatos y revisión
            └─ 02 / territory.py + additional_layers.py
                 → C: máscara, rejilla, armonización, cobertura
                 └─ 03 geología/estructuras ┐
                    04 geoquímica         ├─ features.py → D
                    05 relieve/hidrología ┘
                    06 matriz y roles → Grid_Master_Au + X + calidad + etiquetas
                         └─ 07 particiones ┐
                            08 muestras    ├─ evaluation.py → E
                            09 contrato    ┘
                                 └─ 10 pipelines ┐
                                    11 referencias/logística
                                    12 Random Forest
                                    13 alternativas/comparación
                                    14 ablaciones/PU/cierre
                                      → training.py → F: modelos y predicciones OOF

G: aceptación, explicación y aplicabilidad → pendiente
H: mapas finales, objetivos e inferencia de entrega → pendiente
```

Los ficheros YAML enlazan ejecuciones concretas. B permite escoger la última A satisfactoria, pero C fija una B, D fija una C, E fija una D y F fija una E. Los JSON `current_run.json` de D/E/F facilitan continuar la ejecución correspondiente. Un directorio reciente no equivale automáticamente a una ejecución completa.

La implementación efectiva utiliza módulos planos en `src/geoau`, no la jerarquía de subpaquetes propuesta en el plan ni el paquete `geoai_gold_spain` anunciado en el README histórico. El diseño modular permite reutilizar algoritmos sin copiar grandes bloques en Jupyter; su debilidad práctica es que el usuario debe conocer los contratos entre ejecuciones, configuraciones y manifiestos.

## 2. Estado real y significado de las cifras

| Concepto | Evidencia local | Interpretación |
|---|---:|---|
| Fuentes del último inventario A | 93; cero errores de lectura; un archivo sin datos | Estado posterior a la auditoría original del plan |
| Registros de la base canónica | 11.732 | Filas del inventario general |
| Registros con Au observado | 790 | Au reconocido en `Sustancia`; aún candidatos |
| Posiciones Au distintas | 787 | Coincidencia geométrica, no depósitos independientes |
| Candidatos asociados a rejilla C/D | 789 | Uno queda fuera de la máscara candidata |
| Celdas ocupadas por candidatos en D | 691 | Varios indicios pueden compartir celda |
| Celdas terrestres de D | 496.855 | Todas las intersecciones de área positiva con la máscara |
| Área de la máscara en EPSG:25830 | 493.639,6117 km² | Superficie proyectada del ámbito candidato, no certificación catastral |
| Predictores candidatos en D | 168 | Banco de representaciones; F usa subconjuntos |
| Predictores de la referencia F | 93 | 87 numéricos y seis categóricos antes de codificación |
| Territorio elegible E, `eligible_geo4` | 472.548 celdas | Geología, relieve y Au/As/Sb/Bi con soporte requerido |
| Celdas candidatas elegibles E | 666 | Sustitutos diagnósticos de P |
| Reserva elegible | 72.061 celdas; 23 candidatas | 15,25 % del área elegible aproximadamente |
| Evaluación externa de desarrollo | 400.487 celdas; 643 candidatas | Cobertura conjunta de los cinco tests externos |
| Celdas positivas revisadas | **0** | Bloqueo científico principal |
| Modelos externos guardados en F | 60 | Familias, ablaciones y miembros adicionales de bagging |
| Archivos de predicciones F | 85 | Incluyen referencias, variantes y selección anidada |

La secuencia **790 → 787 → 789 → 691 → 666 → 643 + 23** mezcla unidades diferentes y debe leerse con cuidado: registros, posiciones, registros asignados, celdas ocupadas, celdas elegibles y reparto desarrollo/reserva. No es una serie de eliminaciones sucesivas de depósitos.

D ofrece 478.443 celdas en `eligible_geology_terrain`, 472.548 en `eligible_geo4` y 288.822 en `eligible_geo9`. Exigir los nueve elementos reduce mucho el soporte, en particular tras el control RGB de Zn/W. Las comparaciones F mantienen `eligible_geo4` incluso cuando una ablación prescinde de geoquímica; así se compara la información de las variables sobre el mismo territorio. Esa decisión limita también el alcance de las conclusiones: no evalúa las zonas adicionales que podría cubrir un modelo sin geoquímica.

La máscara es la componente de mayor área del archivo GISCO 2024 generalizado a 1:1.000.000. Las otras componentes se inventarían aparte. Por tanto, el producto no representa toda España, ni todos sus componentes terrestres, ni una máscara peninsular de precisión local. El piloto sigue sin delimitarse y justificarse geológicamente; el ensayo técnico ya abarca el territorio peninsular elegible.

### 2.1. Ejecuciones que forman la cadena examinada

| Fase | Directorio bajo `reports/` |
|---|---|
| A | `fase_a/20260908T085134_494059Z` |
| B | `fase_b/20260908T085820_294458Z` |
| C | `fase_c/20260908T122215_992338Z` |
| D | `fase_d/20260909T104712_606095Z` |
| E | `fase_e/20260909T124128_606717Z` |
| F | `fase_f/20260909T184735_016759Z` |

El paso vectorial C utiliza además una caché anterior fijada en `grid.yaml`. D recuperó bloques compatibles de una ejecución previa, dejando constancia en `reuse_audit.json`. Esta reutilización forma parte del diseño y necesita verificarse por hashes y equivalencia del cálculo, no por coincidencia de nombres de archivo.

## 3. Conceptos que conectan las fases

**Presencia observada y presencia revisada.** Encontrar el token `oro` o `au` identifica un registro candidato. La confirmación final exige presencia y geometría revisadas, y tipología revisada en los objetivos específicos. Una ausencia del token o una revisión que rechace un registro no equivale a ausencia demostrada de mineralización.

**Unidad estadística.** El aprendizaje usa una fila por celda. La tabla de relaciones conserva varios indicios y depósitos por celda sin multiplicar las filas de X. Los grupos de proximidad sirven para explorar dependencia; una cadena de puntos a menos de 500 m puede tener extremos mucho más alejados y no se convierte automáticamente en un depósito.

**Cobertura y valor.** Un cero puede ser una clase geoquímica válida, una fracción litológica nula o una longitud cartografiada nula. `NaN` indica falta de valor utilizable según su contrato. La ausencia de trazas de fallas o de puntos de campaña no demuestra que el territorio esté suficientemente estudiado.

**Soporte espacial.** La celda de salida mide 1 km de lado, pero el contenido puede proceder de una cartografía regional, cuatro píxeles de 500 m, un centro fijo o un vecindario circular. La resolución del archivo no crea detalle geológico que la fuente no contiene. Todos los positivos y U reciben las mismas variables territoriales calculadas en D.

**Aprendizaje P/U.** El cero de `sample_class` codifica territorio no etiquetado. La salida de `predict_proba` es la respuesta del clasificador bajo ese diseño y sus hipótesis. El sesgo en el registro de positivos puede depender de las características del territorio; el bagging de U no lo corrige automáticamente. Esta limitación se corresponde con la formulación de PU con selección dependiente de características de [Bekker y Davis, 2018](https://proceedings.mlr.press/v94/bekker18a.html).

**Separación y anidamiento.** Los folds internos deciden parámetros y ratios; los externos evalúan ese procedimiento. Una reserva adicional permanece sin predicciones. Aprender medianas, escalas o categorías con todo el conjunto antes de dividirlo introduciría información de evaluación: el proyecto evita ese patrón mediante pipelines ajustados por entrenamiento, de acuerdo con las [prácticas de scikit-learn sobre fuga de información](https://scikit-learn.org/stable/common_pitfalls.html).

**Cierre técnico y cierre científico.** Un manifiesto correcto demuestra identidad de archivos. Una prueba sintética demuestra un comportamiento bajo sus entradas. Ninguno acredita por sí solo la leyenda de una capa, la independencia de depósitos ni la validez de una predicción prospectiva. Las banderas de bloqueo del proyecto reflejan esa distinción.
