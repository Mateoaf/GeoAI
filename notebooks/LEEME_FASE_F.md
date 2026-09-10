# Fase F · Entrenar y comparar modelos

Implementa los pasos 31–35 del [plan](../informes/PLAN_PROSPECTIVIDAD_AURIFERA_ESPANA.md), con `src/geoau/training.py`, `config/training.yaml` y los cuadernos 10–14. Consume la ejecución E `20260909T124128_606717Z`, ligada a D `20260909T104712_606095Z`. Los datos, etiquetas, soporte y particiones anteriores se mantienen versionados.

## Qué permite el estado actual

E contiene cero positivos revisados y D no tiene predictores científicamente aprobados. Por eso F usa `mode: diagnostic` y exige `allow_diagnostic_fit: true`. Esto permite **ajustes exploratorios con candidatos** para ejecutar y comprobar el flujo de aprendizaje. No cambia los controles `training_allowed` de E ni transforma los candidatos en positivos confirmados. Los pipelines y scores F llevan su modo y `production_allowed: false`.

El modo `validated` exige que E supere `assert_ready_for_training` y que todas las columnas usadas estén aprobadas por D. Cambiar una bandera de F no elimina las revisiones pendientes de B/D/E. Incluso con entrenamiento autorizado, la evaluación científica G y la decisión de publicación siguen pendientes.

Los scores son respuestas de modelos P/U bajo un diseño de muestreo, no porcentajes absolutos de encontrar oro. Las métricas actuales miden recuperación de **celdas con candidatos**. No se presentan como recuperación de depósitos revisados ni como rendimiento de descubrimiento.

## Entorno y ejecución

Se utiliza `.venv-fase-a`, el mismo entorno de las fases previas. Se añaden scikit-learn y sus dependencias mediante:

```powershell
.\.venv-fase-a\Scripts\python.exe -m pip install -r requirements-fase-f.txt
.\.venv-fase-a\Scripts\python.exe scripts/ejecutar_notebooks_fase_f.py
```

Los cuadernos también se ejecutan manualmente en orden con ese intérprete. El runner guarda las salidas y permite continuar por etapa, por ejemplo `--desde 12 --hasta 14`. Una etapa completamente sellada se verifica y reutiliza. Si se interrumpe dentro de una familia, al repetir se recalcula esa familia; no se mezclan modelos parcialmente ejecutados. No ejecutar dos instancias sobre la misma ejecución.

```powershell
.\.venv-fase-a\Scripts\python.exe -m unittest discover -s tests -p test_training.py -v
.\.venv-fase-a\Scripts\python.exe scripts/validar_fase_f.py
```

`scripts/crear_notebooks_fase_f.py` solo crea cuadernos ausentes. Una nueva configuración o cambio de código exige iniciar una nueva ejecución desde 10. F verifica manifiestos SHA-256 de E/D y congela su código, configuración, versiones del entorno y candidatos de búsqueda. La ejecución queda en `reports/fase_f/<fecha_UTC>/`.

## 10 · Contrato y pipelines

La matriz se lee de `X_features.parquet`, con claves verificadas frente a la malla E. Solo se seleccionan columnas presentes en la lista de candidatos D para diagnóstico o en la lista aprobada para modo validado. El pipeline exige exactamente los nombres y orden congelados. Coordenadas, claves, etiquetas, grupos, área y pesos no entran en X.

Las variables numéricas se imputan con mediana aprendida en el train correspondiente. Una variable completamente ausente en ese train se conserva con relleno cero. Logística añade escalado aprendido en train. Los árboles no necesitan escalado. Los infinitos se consideran ausentes mediante una conversión sin estadísticas aprendidas.

Las unidades geológicas dominantes y las clases modales geoquímicas se tratan como categorías, no como números continuos. Se aprenden categorías solo en train; se reservan estados explícitos `__MISSING__` y `__UNKNOWN__`. La representación base utiliza clases modales de Au/As/Sb/Bi; la alternativa de proporciones sustituye esas clases. No se incluyen simultáneamente ambas representaciones.

No hay selección estadística global de variables. Los conjuntos se definen de antemano a partir de familias D. Cualquier futura selección aprendida debe situarse dentro del pipeline y ajustarse en train interno. El boosting usa one-hot y `early_stopping=False`, evitando una validación aleatoria implícita.

## Evaluación común y selección

Se conservan los cinco folds externos, tres internos por externo y la reserva de E. Cada ajuste lee la muestra P/U específica de su train, con comprobación de pertenencia. **No se remuestrea un train interno a partir de la muestra externa:** se utiliza su muestra propia de E, que respeta sus buffers.

Antes del primer ajuste se congelan los marcos de evaluación de cada split:

- Evaluación territorial: todas las celdas elegibles `role=test` del split, sin variar con familia, parámetros, ratio ni realización.
- Métricas P/U auxiliares: todos los P seleccionados de test y hasta 10.000 U elegidas por una semilla fija, sin buffer alrededor de P de test. `Average Precision` y `ROC-AUC` se etiquetan como métricas P/U; no se informa Brier como calibración física.
- Empates de score: orden por hash de celda independiente de etiquetas. Se seleccionan celdas completas mientras el área acumulada no exceda 1/5/10 % del área terrestre elegible. Por tanto el porcentaje realizado puede quedar ligeramente por debajo del presupuesto.

La métrica de selección es `recovery_at_05`, promediada entre folds internos con igual peso por fold. En diagnóstico cuenta celdas candidatas una sola vez; en modo validado cuenta una vez cada `deposit_id` si alguna celda suya entra en el área priorizada. Se conserva el tipo de unidad en cada tabla.

La proporción P/U de evaluación puede variar entre folds porque cambia el número de P retenidos. AP depende de esa proporción: las comparaciones pareadas entre modelos dentro del mismo fold comparten diseño, pero una media de AP entre folds no constituye una precisión poblacional. F tampoco informa estabilidad por distritos reales porque aún faltan sus identificadores revisados; conserva unidades territoriales para la auditoría posterior.

Cada familia selecciona candidato y ratio por resultados internos, con desempate por ID predefinido. Solo después se reajusta en train externo y se obtiene su predicción OOF. Al cerrar F se selecciona también la familia **por resultados internos de cada fold externo**. Esa selección nunca usa el rendimiento externo; produce `nested_procedure_metrics.csv` y `nested_selected_*.parquet`.

La tabla externa de familias es descriptiva. No se proclama un ganador global por su mayor media externa. Las desviaciones entre cinco folds describen dispersión y no son intervalos de confianza de observaciones independientes. La reserva no recibe predicciones, métricas ni ajustes.

## 11–13 · Referencias y familias

| Cuaderno | Implementación |
|---|---|
| 11 | Score constante, ranking aleatorio por hash, regla geológica ilustrativa y regresión logística regularizada |
| 12 | Random Forest: búsqueda interna, reajustes externos, pipelines y predicciones OOF |
| 13 | ExtraTrees y HistGradientBoosting, con la misma evaluación y comparación descriptiva |

La regla geológica fija es `0.5*exp(-dist_falla_cartografiada_m/5000) + 0.5*unidades_granitoides_explicitos_fraccion`. Los componentes ausentes aportan cero. Es una referencia interpretable pendiente de revisión, no una afirmación metalogenética válida para cualquier depósito ni un modelo aluvial específico. La referencia constante produce un ranking por desempate aleatorio reproducible; no se interpreta como información geológica.

El piloto usa **tres candidatos por familia**, cada uno con un ratio 3/1/10. Esto cubre alternativas conjuntas acotadas; no permite aislar por sí solo el efecto de ratio frente al del parámetro. Puede ampliarse con `search_trials` en una nueva ejecución; 20–30 es una propuesta posterior del plan, no una búsqueda ya realizada.

Con cinco folds externos y tres internos, el presupuesto configurado es de 180 ajustes internos, 20 reajustes externos de familias, 30 ajustes de ablaciones y 10 miembros adicionales de bagging: 240 ajustes en total. Los 60 pipelines externos se conservan; los modelos internos se reconstruyen a partir de configuración, muestras y semillas. Ampliar la búsqueda aumenta sobre todo los ajustes y predicciones internos.

RF y ExtraTrees usan 500 árboles. El primer candidato tiene hoja mínima 5, `max_features='sqrt'` y profundidad sin límite. Los demás exploran hojas 2/5/10/20, profundidades 8/16/sin límite y `max_features` sqrt/0,5 por semilla fija. RF mantiene `oob_score=False`. Logística explora C y boosting tasa de aprendizaje, hojas y tamaño mínimo de hoja, con 100 iteraciones fijas. Las familias tienen el mismo número de candidatos y folds; sus costes computacionales son diferentes.

Se registran tiempo de ajuste y predicción, tamaño P/U, hash de la muestra y **RSS del proceso después del ajuste**. RSS no es un pico de memoria ni memoria atribuible exclusivamente al modelo. Los pipelines finales de cada fold se serializan junto a variables, parámetros y modo.

La ponderación inicial es `fit_weighting: none`, sin `class_weight` adicional: el clasificador aprende bajo el diseño de muestreo P/U. La opción `normalized_design_u` usa los pesos de área/inclusión de U normalizados para conservar su peso total. No proporciona pesos de observación de P ni estima prevalencia. Compararla exige una ejecución distinta predefinida; no cambiarla tras observar la reserva.

XGBoost, LightGBM, CatBoost, KNN y SVM permanecen como ampliaciones opcionales, no dependencias obligatorias del MVP.

## 14 · Ablaciones y bagging

Se ejecutan seis conjuntos con **el mismo RF fijo**, ratio 3, realización 0, 150 árboles y el mismo soporte/muestras/folds:

1. Geología y estructuras.
2. Añadir relieve.
3. Añadir As/Sb/Bi.
4. Añadir Au.
5. Añadir hidrología regional.
6. Sustituir las clases modales de los cuatro elementos por sus proporciones, conservando geología, estructuras, relieve e hidrología.

Los modelos de ablación no se comparan como si fueran el RF ajustado de la búsqueda: su control es el conjunto completo con esos mismos parámetros fijos. Son contrastes exploratorios y no entran en la selección del procedimiento final. Si motivan cambios de variables, esos cambios deben volver al bucle interno de una nueva evaluación. Usar Au geoquímico no demuestra fuga por sí mismo; la procedencia y contaminación histórica siguen pendientes de revisión D.

El bagging aplica el candidato RF elegido internamente en cada fold a las tres realizaciones U de E. Reutiliza la realización 0 y ajusta las otras dos. Conserva P y el territorio evaluado; guarda scores por miembro, media y desviación. Las semillas del estimador también cambian, por lo que esa dispersión combina variación de fondo y del ajuste. No se presenta como intervalo físico de presencia de Au. Esta variante predefinida no se elige por la reserva ni incorpora una suposición automática SCAR.

500 m, sensibilidad a buffers y etiquetas, geofísica y cuencas requieren nuevas entradas y ejecuciones C/D/E. Se documentan en `pending_experiments.json`; no se inventan capas ni se cambia el soporte entre ablaciones para favorecer un resultado.

## Productos y continuación

`models/` contiene pipelines y metadatos por fold; `predictions/` contiene scores OOF completos; `search/` documenta todas las evaluaciones internas y decisiones; `evaluation/` conserva test territorial y muestra P/U fija. También se escriben tablas de comparación, sensibilidad, selección anidada, contrato y manifiesto final.

Para continuar científicamente hacen falta las revisiones de etiquetas y predictores descritas en E, identificación/cartografía de depósitos y distritos, justificación de la independencia espacial y nuevo protocolo aprobado. G deberá evaluar estabilidad, sesgo, aplicabilidad y criterios de aceptación. No se ha generado un mapa de producción ni un servicio de probabilidad por coordenada.

Referencias técnicas: [prevención de fuga con pipelines](https://scikit-learn.org/stable/common_pitfalls.html), [codificación categórica OneHotEncoder](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html), [validación anidada](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html) y [PU con registro dependiente de características](https://proceedings.mlr.press/v94/bekker18a.html).
