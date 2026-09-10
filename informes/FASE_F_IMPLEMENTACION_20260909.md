# Implementación de la fase F · 9 de septiembre de 2026

Se revisaron los pasos 31–35 del plan, el cierre y ampliaciones pendientes de D, el diccionario y los conjuntos de predictores, y las particiones/muestras verificadas de E. Se implementó F en `src/geoau/training.py`, con configuración propia, cuadernos 10–14, pruebas, ejecución automatizada y auditoría independiente. La [guía de uso](../notebooks/LEEME_FASE_F.md) desarrolla las decisiones y comandos.

La ejecución `reports/fase_f/20260909T184735_016759Z` completó los cinco cuadernos, con todas sus celdas de código ejecutadas sin errores. Se realizaron 180 ajustes internos y 60 ajustes externos, y se guardaron 60 pipelines y 85 archivos de scores OOF. El cierre mantiene `scientific_training_allowed=false`, `scientific_validation_complete=false` y `production_allowed=false`.

## Punto de partida científico

E terminó técnicamente con 20 diseños y 180 muestras P/U, y su auditoría independiente pasó. Sin embargo, sus etiquetas siguen siendo candidatos: no existen positivos revisados ni depósitos/distritos validados. D conserva vacía la lista de predictores aprobados y mantiene pendientes revisiones semánticas de capas. Por tanto, entrenar ahora solo permite **ensayar el procedimiento con datos candidatos**.

F habilita explícitamente ese ensayo mediante `mode: diagnostic` y `allow_diagnostic_fit: true`. Los modelos se guardan identificados como diagnósticos y sin autorización de producción. E mantiene sus controles científicos. El camino `validated` exige superar los controles E y utilizar columnas aprobadas D.

La configuración fija E `20260909T124128_606717Z`, vinculada a D `20260909T104712_606095Z`. El soporte común contiene 472.548 celdas peninsulares de 1 km y 666 celdas con candidatos. Los test externos cubren 400.487 celdas de desarrollo; las 72.061 celdas elegibles de reserva no se evalúan.

## Correspondencia con el plan

| Paso | Implementación | Límite explícito |
|---|---|---|
| 31 | Lista de X, bloqueo de auxiliares, imputación/escalado por train, categorías ausentes/desconocidas y pipelines completos | La lista candidata no equivale a aprobación geológica |
| 32 | Referencias constante/aleatoria/geológica y regresión logística con regularización y ratio seleccionados internamente | La regla geológica es ilustrativa, no una ley metalogenética |
| 33 | RF de 500 árboles, búsqueda interna, reajuste por fold externo, pipelines y scores OOF | Piloto de tres candidatos; no se declara una búsqueda de 20–30 ya ejecutada |
| 34 | ExtraTrees e HistGradientBoosting con los mismos marcos de evaluación; comparación descriptiva | Modelos adicionales opcionales; igual número de evaluaciones no implica igual coste |
| 35 | Seis conjuntos de variables con control RF fijo, cambio de representación geoquímica y bagging de tres fondos U | 500 m, buffers, revisión de etiquetas, geofísica/cuencas necesitan nuevas entradas y ejecuciones previas |

## Decisiones que evitan comparaciones engañosas

**El soporte permanece fijo entre familias y ablaciones.** Quitar Au o hidrología no amplía automáticamente el territorio de evaluación. De lo contrario una diferencia de cobertura se confundiría con una mejora predictiva.

**Cada muestra interna procede de E.** No se toma simplemente un subconjunto aleatorio de la muestra externa, porque el fondo interno debe respetar su propia separación espacial y sus P de entrenamiento.

**La selección de familia se realiza dentro del anidamiento.** Cada familia elige parámetros y ratio por recuperación al 5 % del área interna. Al cerrar F, la familia seleccionada para cada fold externo también se decide por sus resultados internos. La tabla externa no designa un campeón global.

**La métrica principal usa área terrestre, no número de filas.** Los empates se resuelven por hash ajeno a etiquetas y se respetan presupuestos de área con celdas completas. AP y ROC-AUC se calculan sobre una muestra P/U fija, común a modelos y ratios; no se interpretan como precisión o calibración de descubrimiento real.

**Las categorías geocientíficas no se convierten en magnitudes continuas.** En la matriz base se usan 93 predictores, seis categóricos: litología/edad dominantes y clases modales Au/As/Sb/Bi. Las categorías nuevas reciben un estado reservado aprendido sin consultar test.

**La selección de variables no se aprende con test.** Las ablaciones están prefijadas y usan el mismo RF de 150 árboles, ratio 3 y realización 0. No participan en la elección del procedimiento final. Si sus resultados motivan una nueva selección, esta debe evaluarse de nuevo dentro del anidamiento.

## Conjuntos de variables

| Conjunto | Predictores | Categóricos |
|---|---:|---:|
| Geología + estructuras | 79 | 2 |
| Añadir relieve | 85 | 2 |
| Añadir As/Sb/Bi | 88 | 5 |
| Añadir Au | 89 | 6 |
| Añadir hidrología — referencia completa | 93 | 6 |
| Completo con proporciones geoquímicas sustituyendo clases | 120 | 2 |

El contraste con/sin Au estudia dependencia de esa evidencia. No demuestra automáticamente fuga o ausencia de fuga: siguen pendientes las revisiones de procedencia, medio y efectos de minería/contaminación señaladas en D.

## Entregables y comprobaciones

Los cuadernos son [10](../notebooks/10_pipelines_y_contrato_entrenamiento.ipynb), [11](../notebooks/11_referencias_y_regresion_logistica.ipynb), [12](../notebooks/12_random_forest_espacial.ipynb), [13](../notebooks/13_comparacion_modelos.ipynb) y [14](../notebooks/14_ablaciones_PU_y_cierre.ipynb). Se añaden `requirements-fase-f.txt` y los scripts de creación, ejecución y validación.

Las diez pruebas específicas pasan. Incluyen imputación aprendida solo con train, categorías nuevas, columnas totalmente ausentes, rechazo de auxiliares/predictores no aprobados, conteo único de depósitos, empates independientes de etiquetas, serialización reproducible y entrenamiento integrado. Un caso controlado fuerza resultados internos y externos opuestos para comprobar que la selección conserva el ganador interno.

`scripts/validar_fase_f.py` verifica manifiestos, correspondencia de test con E, reserva excluida, decisiones internas, cobertura de todos los scores OOF, medianas de imputación reconstruidas desde cada muestra de entrenamiento, predicciones de pipelines serializados y media/dispersión de bagging.

**La auditoría final pasó:** se reprodujeron predicciones de los 60 pipelines guardados, se comprobaron sus estadísticas de imputación/escalado y categorías contra los entrenamientos originales, los 85 archivos OOF, las decisiones internas, las métricas de comparación, la reserva excluida y la agregación PU. `pip check` también terminó sin dependencias incompatibles.

El código registra RSS después del ajuste, no pico de memoria, y tiempo por ajuste/predicción. Los experimentos no disponibles se describen en `pending_experiments.json`. La guía detalla cómo continuar hacia una ejecución científicamente aprobada y la evaluación G.

## Resultados observados del ensayo

La siguiente tabla resume medias entre los cinco folds externos. La recuperación se refiere a **celdas candidatas conocidas dentro del 5 % del área priorizada**, no a probabilidad de encontrar oro ni a depósitos científicamente revisados.

| Familia/referencia | Recuperación al 5 % del área | Average Precision P/U | ROC-AUC P/U |
|---|---:|---:|---:|
| Constante con desempate por hash | 5,43 % | 0,0127 | 0,5000 |
| Aleatoria | 5,00 % | 0,0129 | 0,4849 |
| Regla geológica ilustrativa | 6,32 % | 0,0178 | 0,6336 |
| Regresión logística | 43,98 % | 0,1027 | 0,8719 |
| Random Forest | 52,20 % | 0,1654 | 0,8965 |
| ExtraTrees | 46,17 % | 0,1355 | 0,8905 |
| HistGradientBoosting | 53,39 % | 0,1524 | 0,9032 |

Esta tabla no selecciona un ganador global. El procedimiento anidado eligió RF para los folds 0–3 y ExtraTrees para el 4, exclusivamente por resultados internos. Su recuperación externa media al 5 % del área fue aproximadamente 50,43 %. La media mayor de boosting en la tabla externa no se utilizó para reemplazar esas decisiones.

Con el RF fijo de ablación, las recuperaciones medias al 5 % del área fueron: geología/estructuras 43,68 %; añadir relieve 44,42 %; añadir As/Sb/Bi 46,62 %; añadir Au 46,88 %; añadir hidrología 50,66 %. La representación de proporciones con el conjunto completo alcanzó 50,43 %. Estas diferencias son descriptivas: no se calculó significación, no acreditan causalidad y no justifican seleccionar variables por test externo.

El bagging de tres fondos con los parámetros RF seleccionados internamente obtuvo una media de 50,93 %, frente al 52,20 % de la realización de referencia. **No mejoró automáticamente el promedio de esta métrica en este piloto.** No se ha utilizado ese resultado para ajustar las semillas ni para abrir la reserva. Las tablas por fold conservan la variación que esas medias ocultan.

También se actualizó el índice de notebooks del plan para reflejar la implementación 00–14 y situar G/H como continuación prevista, evitando que sus antiguos números 10/11 se confundan con los cuadernos F actuales.
