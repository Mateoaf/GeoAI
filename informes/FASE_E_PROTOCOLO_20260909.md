# Revisión e implementación de fase E · 9 de septiembre de 2026

Se ha implementado el diseño de evaluación espacial anidada y el muestreo presencia–fondo de los pasos 27–30 de `PLAN_PROSPECTIVIDAD_AURIFERA_ESPANA.md`. La guía operativa está en [LEEME_FASE_E.md](../notebooks/LEEME_FASE_E.md).

## Datos efectivamente utilizados

- Origen D: `reports/fase_d/20260909T104712_606095Z`, comprobado mediante manifiesto SHA-256.
- Ejecución E: `reports/fase_e/20260909T124128_606717Z`.
- Malla heredada: 496.855 celdas, componente peninsular principal, resolución 1 km, EPSG:25830.
- Soporte `eligible_geo4`: 472.548 celdas; 666 celdas contienen candidatos disponibles para el ensayo.
- Positivos revisados: **0**. Los candidatos se conservan con el rol `P_candidate_proxy`.

El soporte procede de D y se fija antes del muestreo. Los productos de las fases anteriores se consumen sin recalcular ni editar sus ejecuciones selladas. Las columnas predictoras no intervienen en la asignación de folds.

## Productos ejecutados

Los tres cuadernos se han ejecutado y guardado con sus salidas:

1. [07_particiones_espaciales.ipynb](../notebooks/07_particiones_espaciales.ipynb): unidades territoriales, reserva, mapa y particiones externas/internas.
2. [08_muestreo_presencia_fondo.ipynb](../notebooks/08_muestreo_presencia_fondo.ipynb): muestras U estratificadas, probabilidades de inclusión y pesos.
3. [09_protocolo_PU_y_control.ipynb](../notebooks/09_protocolo_PU_y_control.ipynb): contrato de aprendizaje, trazabilidad y cierre técnico.

El módulo está en `src/geoau/evaluation.py`; la configuración en `config/evaluation.yaml`. Se incorporan runner, generador de cuadernos que conserva archivos existentes, auditoría independiente y pruebas específicas.

## Resultados del diseño diagnóstico

Los bloques de 50 km generan 246 unidades territoriales. La reserva fija comprende 37 unidades y 72.061 celdas elegibles. Se mantienen cinco folds externos y tres internos por externo: **20 diseños**. La cota inferior mínima de separación entre huellas de entrenamiento y prueba/reserva es **5.293,99 m**, por encima de los 5.000 m configurados.

| Fold externo | Celdas train | Celdas test | Celdas candidatas train | Celdas candidatas test | Unidades con candidatos test |
|---|---:|---:|---:|---:|---:|
| 0 | 286.889 | 67.947 | 378 | 189 | 10 |
| 1 | 265.282 | 85.001 | 498 | 108 | 8 |
| 2 | 256.071 | 93.064 | 468 | 123 | 10 |
| 3 | 280.684 | 72.474 | 533 | 65 | 11 |
| 4 | 270.291 | 82.001 | 395 | 158 | 13 |

No se equilibraron los folds para maximizar rendimiento ni se ajustó ningún modelo. La diferencia de candidatos entre folds forma parte del diagnóstico geográfico. Las unidades con candidatos son bloques/grupos geométricos; no equivalen a depósitos independientes revisados.

Con ratios U:P de 1/3/10 y tres realizaciones por diseño se generan **180 conjuntos P/U**, más sus 180 tablas de asignación por estrato. No fue necesario limitar ningún ratio por agotamiento de U. Según el split, hay 170–533 celdas P de entrenamiento y 170–5.330 U por conjunto. El test territorial permanece fijo al cambiar ratio o realización.

La comparación de 25/50/100 km arroja 109/61/30 unidades con candidatos. Describe factibilidad de agrupación; queda pendiente medir dependencia espacial y justificar científicamente el tamaño seleccionado.

## Interpretación y condiciones pendientes

El cierre es **técnico y diagnóstico**, no científico. `training_allowed` y `prediction_allowed` permanecen en `false`. Hace falta revisar positivos y tipologías, identificar depósitos/distritos, aportar cartografía territorial de distritos y aprobar los predictores en D. También deben revisarse bloques, separaciones, buffer P y reserva; para aluvial se necesitan cuencas.

El buffer de fondo de 250 m es una separación conservadora entre huellas de celdas de 1 km; no se presenta como precisión de los indicios. Se aplica solo respecto a P de entrenamiento. El buffer espacial de 5 km tiene otra función: separar entrenamiento de zonas retenidas.

No se ha fabricado una variable de esfuerzo de observación. Esa alternativa del plan requiere evidencia adicional. El protocolo de referencia P/U y bagging queda preparado para el ajuste en fase F; las tres realizaciones no constituyen por sí mismas un modelo PU entrenado. Ningún producto de E estima un porcentaje absoluto de presencia de oro.

## Reproducción y controles

Las 12 pruebas de `tests/test_evaluation.py` pasan. Cubren agrupación transitiva, reproducibilidad, cota espacial, independencia del fondo respecto a etiquetas retenidas, inclusión de U, límites de capacidad, hashes, etiquetas booleanas, bloqueo del modo validado y ejecución anidada integrada.

Los cuadernos 07–09 tienen todas sus celdas de código ejecutadas sin salidas de error. Para comprobar los productos nacionales se dispone de `scripts/validar_fase_e.py`, que contrasta hashes, claves, pertenencia a entrenamiento, anidamiento, exclusión de reserva, pesos y distancias mediante un árbol espacial independiente del cálculo raster empleado en el diseño.

La auditoría independiente finalizó correctamente sobre los 20 diseños y las 180 muestras nacionales, sin solapamientos indebidos ni incumplimientos de distancia.
