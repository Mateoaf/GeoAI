## 11. Notebook 07 — Particiones espaciales y reserva

Implementa pasos 27–28 mediante [evaluation.py](../../src/geoau/evaluation.py). Carga la D fijada por `evaluation.yaml`, con objetivo `general`, soporte `eligible_geo4`, bloques de 50 km, cinco folds externos, tres internos y separación de 5 km. El modo actual es diagnóstico.

### 11.1. Disponibilidad científica

`source_data` verifica productos D y selecciona columnas de identidad/soporte sin cargar X para crear particiones. `choose_labels` selecciona registros del objetivo que estén dentro de soporte; en diagnóstico usa candidatos y en validado sólo revisados. Valida booleanos explícitamente para evitar el error de convertir la cadena `"False"` a verdadero.

`readiness` exige positivos revisados, IDs de depósito y distrito, predictores aprobados, un mapa territorial de distritos coherente con los registros, distritos elegidos para reserva y protocolo revisado. Para aluvial exige además cuencas. Los datos actuales no superan esas condiciones; cambiar `mode` no evita el bloqueo. La función es un control programático de requisitos, no la revisión experta de su contenido.

### 11.2. Construcción de unidades, folds y separaciones

`connected_units` asigna bloques de 50 km desde fila/columna, y une transitivamente bloques ligados por el mismo depósito o distrito. En diagnóstico añade grupos de proximidad de 500 m. Si hay cartografía territorial de distritos/cuencas, agrupa también sus celdas. Esas unidades completas son lo que se reparte entre folds: no se trocean por balancear el número de registros.

`seed_for` deriva enteros de SHA-256 a partir de semilla y etiquetas del procedimiento. La reserva diagnóstica toma aproximadamente el 15 % del **número de unidades**, ordenadas por hash; no busca el 15 % exacto de área ni de positivos. En los productos actuales contiene 72.061 celdas elegibles y 23 candidatas. El resto contiene 643 celdas candidatas.

La separación usa una transformada de distancia entre centros y la cota conservadora `d_inferior = max(0, d_centros − √2·resolución)`. Restar dos semidiagonales de celda evita tratar como suficiente una distancia que sólo existe entre centros. La cota no es la distancia exacta entre polígonos recortados por costa. Se excluye del entrenamiento lo que no alcanza los 5 km frente a región de test y reserva, incluyendo referencias espaciales sin soporte; esto puede ser más conservador que separar únicamente muestras.

Los folds se asignan por hash de unidad, sin scores. Se prueban menos folds si no hay suficientes unidades con P en train/test; este ajuste de factibilidad usa distribución de positivos, no rendimiento de modelos. Dentro de cada entrenamiento externo se crean sus propios folds internos con nuevas separaciones. Las membresías distinguen `train`, `test`, `spatial_gap`, `holdout`, `outside_support` y `outside_parent`.

@@CELL 07 1 Preparación de E y lectura de requisitos

Localiza la raíz, recarga `evaluation` y llama a `ensure_run`. Si hay ejecución compatible la recupera; en caso contrario crea una nueva tras verificar D y configuración. Muestra `readiness.json`, que explicita siete carencias principales en el estado actual. Crear E en diagnóstico autoriza construir diseños de evaluación, pero no transforma los candidatos en P revisados ni cambia la lista de predictores aprobados de D.

@@CELL 07 3 Construcción de particiones y diagnóstico de tamaños

`build_splits` calcula o recupera las membresías selladas. Guarda relaciones de unidades, positivos seleccionados, planes, resúmenes y sensibilidad de tamaños 25/50/100 km. Esa sensibilidad cuenta bloques y unidades disponibles; no estima autocorrelación ni compara rendimiento. El producto real contiene cinco diseños externos y quince internos, veinte en total. Las comprobaciones de disponibilidad mínima operan sobre unidades espaciales con candidatos, no sobre un número acreditado de depósitos geológicos independientes.

@@CELL 07 5 Mapa de folds y reserva

Une `territory.parquet` y las unidades 1:1, dibuja desarrollo coloreado por fold y reserva en negro. La figura incluye el diseño territorial y no aplica todas las máscaras específicas de cada membresía; por ello no permite leer directamente qué centros quedan finalmente en train después del buffer. El título y el texto remiten correctamente a las máscaras. La asignación de colores no representa score, geología ni calidad del modelo.

### 11.3. Interpretación y límites

Un fold externo contiene varias unidades geográficas y no necesariamente una única región contigua. La capacidad medida es transferencia a esas zonas retenidas bajo el diseño de bloques, no validación leave-one-district-out acreditada. Faltan depósitos/distritos y justificación empírica de 50 km/5 km. La cota mínima de separación entre train y test/reserva en los productos es 5.293,99 m. Pasar ese control prueba separación geométrica conservadora, no independencia geológica absoluta.

## 12. Notebook 08 — Muestreo presencia–fondo

Implementa el paso 29 y prepara el 30. Las funciones principales son `background_pool`, `stratified_u` y `build_samples` de [evaluation.py](../../src/geoau/evaluation.py), líneas 329–432.

### 12.1. Construcción del universo U

Para cada membresía se toman sólo celdas `train`; se separan las P seleccionadas de ese entrenamiento y se aplica un buffer de 250 m calculado conservadoramente entre huellas de celdas de 1 km. Las posiciones de P externas o de reserva no se usan para vaciar el pool U. Así no se facilita artificialmente la tarea evitando fondo cerca de los positivos retenidos.

El buffer de 250 m no equivale a excluir todo un distrito de 5 km. Ambos radios tienen fines distintos: incertidumbre/proximidad alrededor de P de entrenamiento frente a separación entre desarrollo y evaluación. La discretización impone saltos: entre centros a 2 km, la cota inferior es unos 586 m, mientras entre vecinos diagonales de 1 km por eje es cero. No se debe interpretar este procedimiento como un buffer circular exacto de 250 m alrededor del punto del indicio.

### 12.2. Diseño estratificado e inclusión

Se solicitan ratios U:P de 1, 3 y 10, con tres realizaciones. Si n≥H, donde H es el número de bloques con pool, se asigna inicialmente una U por bloque y se reparte el resto según área y capacidad. Dentro de cada bloque se muestrea sin reemplazo. Para n<H se eligen n bloques al azar y una celda por bloque seleccionado.

En el primer caso la probabilidad de inclusión de una celda del bloque h es `π_h = n_h/N_h`. En el segundo, `π_h = (n/H)·(1/N_h)`. Los pesos guardados son `1/π_h` y `área_celda/π_h`. La probabilidad 1 que se asigna a P significa que todas las P observadas de ese entrenamiento se incluyen en la muestra, no que su probabilidad de descubrimiento o registro en la población sea uno.

`sample_class=1` corresponde a `P_candidate_proxy` en diagnóstico o a `P_reviewed` en validado; `sample_class=0` siempre acompaña `U_unlabelled`. Las muestras se generan desde cada train interno completo de forma independiente del subconjunto externo, respetando sus propios buffers.

@@CELL 08 1 Generación de muestras P/U

Recupera E e invoca `build_samples`. La función exige las particiones de 07, selecciona P/pool por membresía y crea nueve diseños por split: tres ratios por tres realizaciones. Guarda un Parquet de muestra y otro de asignación por estrato, con semilla derivada e inclusión. El resultado actual suma **20×3×3 = 180 muestras**. Si el pool es menor que lo solicitado, conserva lo disponible y registra `pool_capped`, ratio realizado y tamaño solicitado; no duplica U para aparentar el ratio.

@@CELL 08 3 Resumen y ejemplo de diseño

Agrupa el resumen por nivel externo/interno y ratio, mostrando número de diseños, mínimos/máximos de P y U y casos limitados por el pool. Lee la primera muestra y su tabla de asignación. Es una inspección explicativa de artefactos ya construidos; no selecciona un ratio ganador. Ésa será una decisión del bucle interno de F, mientras el territorio de evaluación queda constante.

### 12.3. Aspectos todavía no resueltos

No se ha incorporado una superficie de esfuerzo de observación verificable. Muestrear U de forma territorial no elimina el sesgo de localización de P. En futuros objetivos específicos, otros tipos de indicios pueden formar parte del territorio no etiquetado del objetivo; deben seguir identificados como desconocidos y estudiarse en sensibilidad, sin presentarlos como negativos geológicos. La selección diagnóstica tampoco debería reintroducir registros explícitamente rechazados si se añaden revisiones en B: actualmente no hay decisiones de ese tipo en la cadena examinada.

## 13. Notebook 09 — Contrato P/U y cierre de E

Fija el contrato del paso 30 y verifica la terminación técnica de E. Aquí no se entrenan clasificadores ni se estima prevalencia. El bagging previsto se ejecutará en 14.

@@CELL 09 1 Cierre técnico y contrato de aprendizaje

Recupera E y llama a `finish_run`, que verifica etapas de particiones y muestras, reevalúa requisitos científicos, escribe control y sella productos. Muestra además `learning_contract.json`: referencia P/U, elección interna del ratio, evaluación territorial completa, reserva sin ajuste, pesos y agregación de scores. La ejecución actual queda técnicamente completa con `training_allowed=False`; el contrato no confunde ese bloqueo con prohibición de cualquier ensayo diagnóstico posterior explícitamente separado.

@@CELL 09 3 Verificación de manifiesto y comprobación de autorización

Verifica los archivos sellados e intenta `assert_ready_for_training`. En diagnóstico captura el `ValueError` esperado y muestra por qué no está aprobado. Si el control indicara autorización pero el guard fallara, vuelve a lanzar el error, evitando ocultar una inconsistencia. La captura no concede aprobación: permite que el notebook termine informando correctamente del bloqueo. F tiene una vía de diagnóstico explícita distinta del modo validado.

### 13.1. Qué entrega y qué falta

E proporciona un protocolo técnico comprobable y congelado: territorio, unidades, particiones, muestras y decisiones. No cierra científicamente tamaño de bloques, representatividad, depósitos, distritos ni cuencas. La transición a un experimento validado necesita nuevos productos de B/D/E con revisión trazable; cambiar únicamente una bandera en F no satisface esos requisitos.

## 14. Notebook 10 — Pipelines y contrato de entrenamiento

Implementa el paso 31 con [training.py](../../src/geoau/training.py). Verifica E y D, congela familias/candidatos/conjuntos X y prepara marcos de evaluación antes de ajustar modelos.

### 14.1. Construcción real de X

`feature_sets` separa familias por nombres del diccionario D. El conjunto denominado `geology` incluye **geología, asociaciones y estructuras**, no sólo litología. Las variantes son 79 predictores base; 85 con relieve; 88 al añadir As/Sb/Bi; 89 al añadir Au; 93 al añadir hidrología; y 120 al sustituir las cuatro modas por 31 proporciones geoquímicas, conservando hidrología.

`authorize_columns` exige pertenencia a la lista candidata o aprobada, existencia de diccionario y ausencia de una lista de auxiliares/etiquetas prohibidas. No selecciona columnas mirando correlación con todo y. Las litologías/edades dominantes y modas geoquímicas se codifican como categorías. Las clases geoquímicas tienen orden conceptual, pero la implementación one-hot actual no impone una relación ordinal o monótona al modelo.

### 14.2. Pipeline, paso por paso

`FeatureGuard` exige un DataFrame con nombres **y orden** exactamente congelados. Convierte numéricos sin coerción silenciosa de texto inválido y trata infinitos como ausentes. En categorías antepone `v:` a valores presentes y usa `__MISSING__` para nulos. No aprende estadísticas en esta conversión.

`ColumnTransformer` divide numéricas y categóricas y descarta cualquier resto. Numéricas: `SimpleImputer(strategy='median', keep_empty_features=True)`; sólo logística añade `StandardScaler`. Categóricas: `SafeOneHot` aprende valores del train y reserva `__UNKNOWN__` y `__MISSING__`; categorías nuevas se asignan al primero. Se utiliza matriz densa float32 en la codificación y `sparse_threshold=0`, aspecto relevante si crece mucho la cardinalidad.

Para una variable numérica totalmente ausente en train, `keep_empty_features=True` mantiene la columna con relleno cero, conforme al comportamiento documentado de [SimpleImputer](https://scikit-learn.org/stable/modules/generated/sklearn.impute.SimpleImputer.html). Es un relleno interno del modelo; no reescribe la capa geocientífica. Aun así, si la variable es una distancia, cero tiene un significado físico fuerte y esta política necesita una evaluación específica de sensibilidad y aplicabilidad.

Los árboles no llevan escalado. Random Forest desactiva OOB como evaluación; HistGradientBoosting desactiva `early_stopping` y usa one-hot en lugar de categorías nativas. Logística emplea `lbfgs`, hasta 3.000 iteraciones y regularización controlada por C; no se ha implementado aquí la ElasticNet que anuncia el README histórico.

### 14.3. Marco de evaluación fijo

Para cada split se guardan **todas** las celdas `role=test` con su área. Antes del ajuste se marcan sus P y una muestra auxiliar reproducible de hasta 10.000 U para AP/ROC-AUC. Los modelos comparten estas mismas celdas; cambiar ratio de entrenamiento no cambia la prueba. El desempate de scores usa hash de celda independiente de etiquetas. No se construyen predicciones ni métricas de reserva.

@@CELL 10 1 Preparación de F

Localiza y recarga `training`, recupera o crea F con `ensure_run` y muestra control y configuración. `check_inputs` exige compatibilidad E/F, ratios y realizaciones disponibles y permiso explícito `allow_diagnostic_fit` para diagnóstico. En validado ejecutaría además el guard científico de E. Congela código, configuración, versiones, listas y marcos de evaluación. La salida de `scientific_training_allowed=False` coexistiendo con diagnóstico activo es coherente: se permite probar el código sin atribuir validez científica a los candidatos.

@@CELL 10 3 Inspección del esquema y los candidatos

Muestra tamaños de los seis conjuntos, número de categóricas y candidatos por familia. `candidates` predefine tres configuraciones para cada familia con ratios 3/1/10. El primer RF tiene 500 árboles, hoja mínima 5, `sqrt` y profundidad ilimitada; los demás exploran parámetros por semilla. El ratio cambia conjuntamente con hiperparámetros: estas tres alternativas no permiten aislar el efecto exclusivo del ratio. El número de candidatos es igual entre familias, pero no el coste ni la amplitud efectiva de búsqueda.

### 14.4. Cómo se calcula la métrica central

`metrics` ordena scores descendentes y resuelve empates con `tie_key`. Acumula `land_area_m2` y selecciona el prefijo de celdas completas cuya suma no excede 1 %, 5 % o 10 % del área. El presupuesto realizado puede quedar ligeramente por debajo; se guarda en `area_fraction_*`.

En diagnóstico, `recovery_at_05 = celdas candidatas dentro del prefijo / celdas candidatas del test`. En validado, el numerador y denominador son depósitos distintos y un depósito se recupera si alguna de sus celdas entra. Si un test tiene 100 celdas candidatas y recupera 40 dentro del presupuesto, la recuperación es 0,40; no significa que el 40 % de las celdas priorizadas contengan oro.

`average_precision_PU` utiliza AP de scikit-learn en la muestra P/U fija, una suma de precisiones ponderadas por incrementos de recall, distinta del área trapezoidal de una curva PR. Esta distinción sigue la [definición oficial de average_precision_score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html). Su valor depende del diseño de P/U; una precisión frente a U no estima directamente la tasa de descubrimiento en campo. `roc_auc_PU` también utiliza ese marco etiquetado de observación.

## 15. Notebook 11 — Referencias y regresión logística

Implementa el paso 32. Ofrece controles mínimos para que una métrica alta se compare con referencias informativas sobre el mismo territorio. El ajuste de logística comparte el mecanismo anidado que usarán las demás familias.

### 15.1. Referencias efectivas

La referencia constante asigna 0,5 a toda celda; el ranking territorial se produce por desempate de hash, mientras su ROC-AUC es 0,5. La aleatoria genera un valor reproducible por hash distinto. Ambas deben interpretarse como referencias de orden sin evidencia geológica.

La regla ilustrativa es `s = 0,5·exp(−d_falla/5.000) + 0,5·f_granitoides`. Una distancia ausente se convierte en infinito y aporta cero; la fracción granitoide ausente aporta cero. Es una hipótesis regional sencilla y explícita, no una regla metalogenética universal ni un modelo aluvial. El tratamiento de ausentes aquí difiere del de los clasificadores, lo que también condiciona su rendimiento como referencia.

### 15.2. Flujo compartido de `fit_family`

Para cada externo, se recorre cada candidato y cada interno. `fit_one` lee la muestra E correspondiente y verifica que sus IDs pertenezcan al train; crea un pipeline nuevo y ajusta todas sus transformaciones sólo allí. `evaluate_model` predice todas las celdas del test interno por lotes de 20.000 y calcula métricas. Se promedia recuperación al 5 % con igual peso por fold y se desempata por ID predefinido.

La decisión se guarda antes de evaluar el externo. Se reajusta el candidato elegido sobre su train externo, se predice su test y se guardan pipeline completo, parámetros, variables, semilla reproducible, tiempos, tamaños P/U, hash de muestra y scores OOF. Los modelos internos se descartan de memoria; sus configuraciones y muestras permiten reconstrucción. La política `fit_weighting=none` usa el diseño muestreado sin pesos adicionales; `normalized_design_u` normalizaría pesos de área/inclusión de U para conservar su masa total.

@@CELL 11 1 Evaluación de referencias

Recupera F y ejecuta `fit_references`. Aunque la función se llama `fit`, las tres referencias no aprenden un estimador: calculan scores predefinidos sobre los cinco tests externos y los evalúan. Guarda quince archivos de predicción, métricas y fórmula de la regla geológica. No utiliza los resultados para elegir una regla diferente ni abre reserva.

@@CELL 11 3 Entrenamiento anidado de logística

Ejecuta `fit_family(..., 'logistic')`. Cada candidato combina C y ratio; los valores iniciales de C son 1, 0,1 y 10. Un C menor implica mayor regularización. El escalado de numéricas y la codificación categórica se reaprenden en cada entrenamiento. Con cinco externos, tres internos y tres candidatos se realizan 45 ajustes internos y cinco reajustes externos para la familia. La tabla devuelta contiene las métricas externas del candidato que ganó internamente en cada fold.

### 15.3. Lectura de resultados

La logística diagnóstica recupera en promedio el 43,98 % de las celdas candidatas al priorizar el 5 % del área, frente a aproximadamente 5 % de la referencia aleatoria. Este contraste es evidencia de señal predictiva respecto a los candidatos bajo el diseño actual. No permite separar por sí solo señal geológica y sesgo de inventario ni demuestra recuperación de depósitos independientes.

## 16. Notebook 12 — Random Forest espacial

Implementa el paso 33. Random Forest promedia numerosos árboles entrenados con aleatoriedad de muestras y subconjuntos de variables. Esa capacidad para relaciones no lineales no suprime la necesidad de particiones espaciales y revisión de las fuentes.

@@CELL 12 1 Ajuste y evaluación anidada de Random Forest

Recupera F y ejecuta la misma función `fit_family` con `random_forest`. Usa los marcos E/F ya congelados, 500 árboles por candidato, cinco externos y tres internos. `min_samples_leaf` controla cuánto pueden adaptarse las hojas a pocos ejemplos; profundidad y `max_features` limitan complejidad y diversidad. OOB queda desactivado y no se usa como prueba de transferencia espacial. Los scores externos sólo se calculan después de guardar la elección interna.

@@CELL 12 3 Parámetros seleccionados por fold

Lee `random_forest_selections.json` y muestra candidato, ratio, parámetros y recuperación interna media. La selección puede variar entre folds porque cambia el territorio de aprendizaje. En la ejecución examinada gana el candidato 02 con ratio 10 en cuatro folds y el candidato 00 con ratio 3 en uno. Esto no demuestra que 10:1 sea universalmente mejor: el ratio está asociado a otros parámetros y los datos de entrenamiento difieren.

### 16.1. Interpretación y reproducibilidad

La media externa RF de recuperación al 5 % es 52,20 %, y AP P/U media 0,1654. La dispersión entre folds es considerable y no es un intervalo de confianza basado en depósitos independientes. Los metadatos registran RSS del proceso después del ajuste: no es pico de memoria ni consumo exclusivo del modelo. Los pipelines guardados contienen guard, transformaciones y estimador; conservar sólo el bosque sin codificadores haría incompatible una inferencia posterior.

## 17. Notebook 13 — Alternativas y comparación

Implementa el paso 34 con ExtraTrees e HistGradientBoosting. No ejecuta XGBoost, LightGBM, CatBoost, KNN, SVM ni Naïve Bayes, aunque aparezcan mencionados como ampliaciones o en documentación histórica.

### 17.1. Diferencias de algoritmos

ExtraTrees construye árboles con mayor aleatoriedad en umbrales y agrega sus respuestas. Comparte en el código la familia de parámetros de RF, pero sus mecanismos internos y defaults no son idénticos. HistGradientBoosting añade iterativamente árboles que corrigen errores de la función objetivo y discretiza numéricos para el cálculo. Aquí usa 100 iteraciones predefinidas, tasa de aprendizaje y complejidad de hojas, sin parada temprana basada en una partición aleatoria oculta.

@@CELL 13 1 ExtraTrees anidado

Recupera F y llama a `fit_family(..., 'extra_trees')`. Igual que RF, utiliza tres candidatos de 500 árboles y selecciona dentro de cada externo, con sus propias realizaciones deterministas del estimador. Comparte muestras para un mismo ratio/split, predictores de referencia y test fijo. El resultado actual tiene recuperación media al 5 % de 46,17 %. No es una ablación de aleatoriedad controlando cada diferencia de algoritmo, sino comparación de procedimientos de ajuste predefinidos.

@@CELL 13 2 HistGradientBoosting anidado

Ejecuta la cuarta familia. El constructor impone `early_stopping=False` y `categorical_features=None` porque las categorías ya están codificadas. Explora tasas 0,1/0,05/0,15, tamaños de hojas y ratios asociados. La recuperación media externa al 5 % es 53,39 %. Es mayor que la media RF en esta tabla descriptiva, pero por sí sola no autoriza proclamar un ganador final tras inspeccionar los tests externos.

@@CELL 13 4 Comparación agregada por familia

Lee los CSV externos de las cuatro familias, los concatena y calcula media y desviación estándar de recuperación, AP y ROC-AUC. Cada fold tiene el mismo peso, aunque área y número de candidatos varíen. La desviación estándar de pandas utiliza corrección muestral; no debe confundirse con incertidumbre por celda del bagging. La tabla no incluye todavía las referencias en esta vista —el cierre 14 sí genera una comparación conjunta— ni calcula intervalos pareados por unidades.

### 17.2. Cómo interpretar la comparación

Las familias comparten el marco de prueba y el número de candidatos, lo que permite comparaciones pareadas dentro de fold. AP cambia también con la proporción P/U del fold, porque se mantienen todas las P y hasta 10.000 U. La media de AP de cinco folds no es una precisión poblacional. El procedimiento final de F elegirá también la **familia** por sus medias internas, no por escoger la fila con mayor media externa de esta pantalla.

## 18. Notebook 14 — Ablaciones, bagging de U y cierre

Implementa el paso 35 y la agregación del paso 30. Utiliza `run_sensitivity` y `finish_run` de [training.py](../../src/geoau/training.py), líneas 401–490. Produce contrastes de familias de variables y variación del fondo, y documenta la selección anidada completa.

### 18.1. Ablaciones y control experimental

Para cada externo se ajustan los seis conjuntos X con un RF fijo de 150 árboles, hoja mínima 5, `sqrt`, profundidad ilimitada, ratio 3 y realización 0. Se conserva soporte `eligible_geo4`, train, test y semilla del estimador para el mismo fold. Así la diferencia principal entre estas variantes es el conjunto de variables. No se deben comparar sus resultados como si se hubiera usado el RF optimizado de 500 árboles de 12: la referencia interna apropiada es el conjunto completo de **esa misma ablación fija**.

Las seis variantes son base geológica/estructural; añadir relieve; añadir As/Sb/Bi; añadir Au; añadir hidrología; y sustituir las modas de Au/As/Sb/Bi por proporciones conservando hidrología. No se evalúan aquí cambios de resolución, buffers, confianza de etiquetas o geofísica. Esos cambios requieren nuevas ejecuciones anteriores que mantengan la cadena de evidencia.

### 18.2. Bagging de U

Para cada fold se reutiliza el RF seleccionado internamente con realización 0 y se ajustan dos modelos adicionales con realizaciones U 1 y 2. Mantiene P, parámetros y territorio test. El score final es `media(s_0, s_1, s_2)`; la dispersión es `sqrt(media((s_r − media_s)²))`, desviación poblacional de tres miembros.

También cambia la semilla del estimador con la realización. Por tanto, la dispersión combina cambio de U y aleatoriedad del RF; no aísla exclusivamente el efecto del fondo, no es un intervalo de confianza de presencia y no estima prevalencia. Los tres miembros son pocos para caracterizar estabilidad fina. La mejora mediante bagging es una hipótesis a evaluar, no una propiedad garantizada: en esta ejecución su recuperación media al 5 % es ligeramente inferior a RF individual.

@@CELL 14 1 Ejecución de sensibilidad

Recupera F y exige que las cuatro familias estén terminadas. `run_sensitivity` ajusta seis ablaciones por cada uno de los cinco externos y dos RF adicionales de bagging por externo; guarda modelos, predicciones individuales, media/dispersión y métricas. Son 30 ajustes de ablación y diez miembros nuevos de PU. Si existe un sello completo de sensibilidad se verifica y reutiliza; un procesamiento parcial no recibe aprobación por tener algunos archivos presentes.

@@CELL 14 3 Cierre de F y procedimiento seleccionado

`finish_run` verifica referencias, cuatro familias y sensibilidad. Genera comparación conjunta y, en cada externo, elige familia/candidato exclusivamente por `mean_inner_recovery_at_05`, con desempates predefinidos. Copia sus predicciones a `nested_selected_*`, calcula métricas del procedimiento de selección y guarda contrato, pendientes y manifiesto final. Mantiene `scientific_validation_complete`, `prediction_allowed` y `production_allowed` en falso. La reserva sigue sin predicciones ni métricas.

@@CELL 14 4 Gráfico comparativo y verificación final

Lee `comparison_by_fold.csv`, dibuja recuperación al 5 % por fold para referencias y familias y comprueba el manifiesto F. El gráfico usa como unidad celdas candidatas, coherente con diagnóstico. El rótulo tendría que adaptarse al modo validado si se incorporan depósitos revisados. La figura no decide el ganador del procedimiento ni cambia umbrales; la selección ya se hizo con datos internos.

### 18.3. Presupuesto real y alcance de cierre

La configuración corresponde a 180 ajustes internos —4 familias×5 externos×3 internos×3 candidatos—, 20 reajustes externos, 30 ablaciones y diez modelos nuevos de bagging: **240 ajustes** del diseño completo. Se guardan 60 pipelines externos; los 180 internos no se serializan. Las referencias no requieren ajuste. La presencia de 60 archivos en F y de una carpeta raíz `models/` vacía son compatibles: se guardan dentro del directorio de ejecución, no en el directorio histórico anunciado por el README.

El cierre permite inspeccionar una cadena técnica reproducible. Falta la fase G de revisión, explicación, estabilidad por grupos y aplicabilidad; también H de reentrenamiento autorizado, mapas de entrega, objetivos e inferencia por coordenadas. No existe todavía un mapa final validado ni un servicio de predicción operativo acreditado por estos notebooks.
