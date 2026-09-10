# Revisión e integración de fase D · 9 de septiembre de 2026

Se revisaron el DOCX del plan (pasos 18–26), `features.py`, configuración, los
cuadernos 03–06 y la ejecución `20260909T085704_618911Z`. Esta última no tenía
`geology_manifest.json` ni los productos de geología; su cierre seguía `en_curso`.
El 06 conservaba salidas de `20260908T131414_539995Z`, que no acreditaban la
integración de la ejecución abierta por el usuario.

La ejecución final de esta revisión es:

`reports/fase_d/20260909T104712_606095Z`

## Correcciones

- Un único inicio en 03 mediante `ensure_run`; se restauró la caché de geología.
- Recuperación auditada de bloques compatibles: comparación de funciones AST,
  constantes de extracción, parámetros y fuentes; comprobación SHA-256 de sus
  archivos. Cada bloque recuperado identifica ejecución, código y manifiesto origen.
- Se conservaron las exploraciones del usuario y se corrigió el filtro `>0` del
  04 para mantener la clase cero. Los cuadernos previos están archivados en
  `reports/revision_fase_d_20260909/antes/`.
- Control RGB con tolerancia máxima 2 y margen mínimo 10 frente a la segunda
  clase. Las desviaciones de 8 de Zn/W no se aceptan automáticamente.
- Reparto correcto de longitud en bordes exteriores frente a compartidos;
  supresión de ruido FFT inferior a `1e-7` metros. Se recalcularon estructuras
  e hidrografía. La densidad circular sigue siendo una aproximación sobre celdas.
- Asociaciones litológicas explícitas sin inventar composición interna de unidades.
- Integración de cobertura C, calidad D y atributos de B con claves verificadas.
- Maestro completo, X independiente, roles de columnas y particiones de
  almacenamiento; estas últimas no se presentan como folds de evaluación.
- Escritura determinista de particiones y reemplazo atómico de archivos para que
  reintentar una escritura no acumule filas duplicadas.

## Productos

| Producto | Contenido |
|---|---|
| `Grid_Master_Au.parquet` | 496.855 celdas, 245 columnas: predictores, soporte, cobertura y etiquetas |
| `Grid_Master_Au/` | Mismos registros en particiones espaciales de almacenamiento |
| `X_features.parquet` | `cell_id` y 168 predictores candidatos |
| `calidad_y_soporte.parquet` | Rejilla, calidad de extracción y elegibilidad |
| `etiquetas_por_celda.parquet` | Recuentos y estados; U permanece desconocido |
| `relacion_indicios_celda.parquet` | 790 indicios con trazabilidad B/C, tipo, depósito/distrito y grupos |
| `column_roles.csv` | Diferencia predictores de claves, auxiliares y etiquetas |
| `feature_dictionary.csv` | Fuente, unidad, método y condición de cada predictor |
| `feature_sets.json` | Familias y representaciones alternativas para futuras comparaciones |
| `soporte_modelos.csv` | Cobertura y candidatos conservados según conjunto de variables |
| `outputs_manifest.json` | Hashes de productos completos |

789 indicios tienen celda y ocupan 691 celdas; el registro fuera de máscara se
conserva sin asignación. No hay depósitos/distritos revisados identificados en B;
sus relaciones se exportan vacías, sin crear identificadores ficticios. Los grupos
de proximidad conservan su identidad como agrupaciones geométricas.

## Soporte observado

| Criterio | Celdas | Indicios candidatos | Celdas con positivo revisado |
|---|---:|---:|---:|
| Geología y elevación/pendiente, costa admitida | 478.443 | 756 | 0 |
| Anterior + Au/As/Sb/Bi | 472.548 | 755 | 0 |
| Anterior + los nueve elementos | 288.822 | 525 | 0 |

Exigir los nueve elementos reduce sustancialmente el territorio frente a usar
los cuatro principales. Esto es un diagnóstico de soporte, no una comparación
de rendimiento. En E/F, las comparaciones de modelos deben usar el mismo ámbito
de evaluación para no confundir una diferencia de cobertura con una mejora.

No hay predictores completamente ausentes. `zn_proporcion_clase_3` y
`w_proporcion_clase_2` son constantes entre sus valores presentes: corresponden a
las clases cuyo color presenta discrepancia mayor. Se señalan para revisión;
no se presentan como pruebas de ausencia química en el territorio.

## Correspondencia con el plan

- **18:** unidades/edad, fracciones, dominantes y asociaciones explícitas implementadas.
  Las equivalencias metalogenéticas y las mezclas internas requieren revisión.
- **19:** diccionario GEODE, distancias, densidades aproximadas multiescala y
  controles de cobertura implementados; no se suma MAGNA duplicado.
- **20:** intersecciones/orientaciones continúan como ampliación condicionada a
  saneamiento topológico y leyendas. No se usan símbolos como trazas físicas.
- **21:** control de clases/RGB, moda y proporciones con máscaras implementados.
  Unidades, medio, extracción y leyendas oficiales no se declaran validados.
- **22:** geoquímica analítica cuantitativa sigue como ampliación opcional; los
  mapas clasificados no se convierten en análisis químicos puntuales.
- **23:** elevación y derivadas de terreno implementadas con soporte explícito.
- **24:** red hidrográfica regional implementada; terrazas, cuencas y detalle
  aluvial requieren datos e interpretación adicionales.
- **25:** geofísica permanece como extensión condicionada. No se interpolan
  localizaciones documentales como si fueran propiedades físicas.
- **26:** maestro completo y particionado, X separada, relaciones auxiliares,
  roles, conjuntos candidatos y controles implementados.

El cierre **técnico** de la base regional se completa; el cierre **científico**
permanece pendiente. `approved_training_columns` sigue vacío y
`prediction_allowed=false`, coherente con la ausencia de positivos revisados y
con las revisiones semánticas pendientes. No se entrenó Random Forest ni se
generaron negativos, imputaciones o particiones de evaluación.

## Validación y uso

Los cuatro notebooks se ejecutan sobre la misma ejecución. Las pruebas incluyen
casos geométricos conocidos, bordes exteriores, tolerancia/ambigüedad RGB, clase
cero, proporciones, firmas de cálculo, conservación de claves y reintentos de
escritura. El validador comprueba también los productos nacionales y sus hashes.

Guía vigente: [`LEEME_FASE_D_REVISION_20260909.md`](../notebooks/LEEME_FASE_D_REVISION_20260909.md).
Para trabajar con predictores, leer `X_features.parquet`; no entregar todas las
columnas de `Grid_Master_Au` a un algoritmo de aprendizaje.
