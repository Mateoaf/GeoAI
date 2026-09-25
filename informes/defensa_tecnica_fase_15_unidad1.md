# Defensa técnica — Fase 15 · Unidad 1: redes neuronales para prospectividad aurífera

**Audiencia:** comité de ingeniería / revisión técnica  
**Duración recomendada:** 18–22 minutos + preguntas  
**Evidencia congelada:** ejecución `reports/unidad1/20260920T112741_562792Z`  
**Estado del experimento:** completado, diagnóstico; no habilitado para producción.

> Este guion distingue el material didáctico del reto de aguacates de la evidencia del proyecto GeoAI. El reto aporta el marco metodológico —comparar una red con baselines, no filtrar información y reservar el test—. Todos los números que se presentan a continuación proceden del notebook de la fase 15 y de sus artefactos de ejecución, no del reto de aguacates.

## Resumen ejecutivo para abrir la defensa

- La mejor red interna fue la MLP regularizada `[32, 16]`: recuperación media de **43,56 %** de los candidatos P al priorizar el **5 % del área**.
- Random Forest obtuvo **47,17 %** bajo exactamente las mismas tres validaciones espaciales internas: una diferencia de **−3,61 puntos porcentuales** frente a la mejor MLP.
- La MLP regularizada sí aventajó a la regresión logística en **+12,37 pp**, pero eso no justifica sustituir RF.
- El análisis es P/U diagnóstico: P son celdas candidatas y U es fondo no etiquetado. Un score sigmoid **no** es una probabilidad absoluta de descubrir oro.
- El test externo y la reserva territorial permanecieron cerrados; por ello no se afirma mejora demostrada ni aptitud de producción.

---

## Slide 1 — Tesis, alcance y decisión solicitada

**Objetivo técnico**  
Defender qué se ha demostrado en la Unidad 1 y solicitar la aceptación del resultado como ensayo didáctico y diagnóstico, no como modelo operacional de prospectividad.

**Decisiones metodológicas y trade-offs**

- Se adapta exclusivamente U1.1–U1.7 del reto de redes neuronales; TensorFlow avanzado y el cierre comparativo final del reto quedan fuera de alcance.
- Se aplica la regla central del reto: una MLP debe competir con referencias más simples bajo el mismo protocolo; no se asume que una red sea superior por su complejidad.
- Se prioriza integridad experimental (test y reserva cerrados) frente a obtener una conclusión de rendimiento final en esta fase.

**Resultados cuantitativos reales del notebook**

- **21 ajustes:** 7 modelos × 3 folds internos de `outer_00`.
- Mejor MLP: **0,4356** de recuperación al 5 % del área.
- Mejor referencia: RF **0,4717**; decisión automatizada: `promising_in_validation = false` e `improvement_demonstrated_on_test = false`.

**Razonamiento físico/geoespacial/algorítmico**  
Prospectividad no es clasificar píxeles independientes: es ordenar celdas territoriales para concentrar trabajo de exploración. Por ello la pregunta relevante es cuántos candidatos P quedan dentro de un presupuesto espacial fijo, no únicamente qué accuracy alcanza un clasificador sobre una muestra P/U.

**Visual sugerido:** una diapositiva de “semáforo”: verde = ejecución/verificación, ámbar = selección interna exploratoria, rojo = no test/no producción.

---

## Slide 2 — Trazabilidad: de los aguacates a GeoAI, sin trasladar resultados

**Objetivo técnico**  
Demostrar que el reto de aguacates se usó como guía conceptual y metodológica, mientras que datos, variables, etiquetas y métricas del experimento pertenecen a GeoAI.

**Decisiones metodológicas y trade-offs**

- Se conservaron los conceptos U1: perceptrón, XOR, propagación hacia delante, gradiente, activaciones, capacidad, regularización y parada temprana.
- Se sustituyó el dominio comercial de aguacates por datos geológicos, estructurales, geoquímicos, geomorfológicos e hidrográficos de GeoAI.
- No se trasladaron targets, particiones 70/15/15 ni métricas de precio/aguacate: su transferencia habría sido metodológicamente inválida para una priorización espacial P/U.

**Resultados cuantitativos reales del notebook**

- Notebook ejecutado: **23 celdas**, con `TensorFlow 2.21.0`, `Keras 3.15.1`, Python `3.13.15` y semilla **42**.
- El esquema final contiene **93 predictores originales**: 87 numéricos y 6 categóricos.
- El control de ejecución registra `scope: U1.1-U1.7`, `status: completed` y `production_allowed: false`.

**Razonamiento físico/geoespacial/algorítmico**  
Una arquitectura aprende relaciones entre la representación que recibe y la etiqueta disponible. Cambiar de aguacates a geología exige redefinir tanto la física representada por X como el significado de y y el protocolo de validación. Lo transferible es el método de contraste, no una métrica o una conclusión del conjunto de aguacates.

**Visual sugerido:** flecha “Reto Aguacates: conceptos y disciplina” → “GeoAI: datos, P/U, métrica territorial y resultados propios”.

---

## Slide 3 — Formulación del problema: ranking espacial P/U, no probabilidad de oro

**Objetivo técnico**  
Precisar qué aprende el modelo y el significado operativo de su score.

**Decisiones metodológicas y trade-offs**

- En modo `diagnostic`, **P=1** identifica celdas con candidatos; **U=0** es fondo sin etiqueta, no ausencia geológicamente confirmada.
- Se usa una salida sigmoid y BCE para entrenar el contraste P/U; se mantiene el score como ranking, no como probabilidad calibrada de yacimiento o de oro.
- Se fija una relación de muestreo **U/P = 3** y realización 0. Es eficiente para entrenar, pero hace que BCE, AP, AUC, F1 y accuracy dependan del diseño de muestreo.

**Resultados cuantitativos reales del notebook**

- Muestras de entrenamiento por fold: **277 P / 831 U**, **178 P / 534 U** y **219 P / 657 U**.
- Marcos de validación territorial: **97.931**, **91.214** y **97.744** celdas; sus subconjuntos fijos P/U para métricas contienen **10.088**, **10.163** y **10.127** miembros, respectivamente.
- La primera validación 2D tiene prevalencia P/U aproximada de **0,87 %**; por eso su baseline mayoritario alcanza **99,13 %** de accuracy, aunque no recupera señal útil.

**Razonamiento físico/geoespacial/algorítmico**  
Una celda U puede ser mineralizada y simplemente no estar inventariada. Penalizarla como un negativo físico confirmado sería una afirmación geológica injustificada. El score sólo ordena similitud con los P observados frente al fondo U bajo este diseño; convertirlo en probabilidad absoluta requeriría labels y calibración representativos de la presencia/ausencia real.

**Visual sugerido:** diagrama de conjuntos P (candidatos), U (fondo no etiquetado), área priorizada y el texto “score ≠ P(oro)”.

---

## Slide 4 — Representación geocientífica y controles contra fuga

**Objetivo técnico**  
Mostrar que la red recibe evidencia geocientífica permitida y que se evita introducir información de la respuesta o de localización como predictor.

**Decisiones metodológicas y trade-offs**

- Los 93 predictores incluyen litología y edad (fracciones y dominantes), distancia/densidad de fallas, cabalgamientos y contactos intrusivos, unidades litológicas, elevación, pendiente, índices topográficos y geoquímica As/Sb/Bi/Au, además de proximidad/densidad de cauces.
- Las 6 variables categóricas (`litologia_dominante`, `edades_dominante`, y clases modales As/Sb/Bi/Au) se codifican one-hot aprendiendo categorías sólo en train; los valores desconocidos se admiten como tales.
- Imputación mediana y `StandardScaler` se ajustan sólo en train interno. Se excluyen coordenadas, claves, etiquetas, pesos y metadatos de yacimientos de X.
- Trade-off: excluir coordenadas y datos de depósito reduce atajos espaciales y fuga, aunque renuncia a posibles patrones locales aparentes.

**Resultados cuantitativos reales del notebook**

- En el primer train interno, la mediana de distancia a falla cartografiada fue **946,34 m** y la de pendiente **3,03°**; sus medias tras imputación usadas para escalar fueron **1.626,11 m** y **4,42°**.
- El notebook confirma **93 predictores originales** antes de la expansión one-hot.

**Razonamiento físico/geoespacial/algorítmico**  
Fallas, contactos y litologías pueden controlar circulación de fluidos, permeabilidad, trampas estructurales y contexto metalogenético; topografía y red de drenaje describen exposición, transporte y contexto superficial; la geoquímica aporta proxies de halos o asociaciones. Estas asociaciones son señales para priorización, no pruebas de causalidad ni sustitutos de verificación de campo.

**Visual sugerido:** matriz por familias de variables con una columna “mecanismo geológico plausible” y otra “salvaguarda anti-fuga”.

---

## Slide 5 — Validación espacial: qué se entrena, qué se observa y qué permanece sellado

**Objetivo técnico**  
Defender la separación territorial como condición mínima para evitar una estimación optimista causada por autocorrelación espacial.

**Decisiones metodológicas y trade-offs**

- Se usan los tres folds internos del fold externo prefijado `outer_00`; no se realiza una nueva evaluación anidada completa en U1.
- Cada train interno y su validation pertenecen al train del fold externo; no se solapan y se rechaza explícitamente cualquier celda de test externo o reserva.
- Se reutiliza el marco espacial de F y se calcula la selección por área acumulada. El coste es una estimación más exigente y con menos datos de entrenamiento que un split aleatorio.
- La variación entre folds se comunica como sensibilidad entre particiones dependientes, no como intervalo de confianza.

**Resultados cuantitativos reales del notebook**

- Validaciones espaciales de **91 mil a 98 mil celdas** por fold, no una muestra aleatoria de filas.
- `test_evaluated: false`, `holdout_evaluated: false` y `production_allowed: false` en el artefacto `control.json`.
- La revisión de artefactos se completó sin abrir test ni reserva.

**Razonamiento físico/geoespacial/algorítmico**  
Celdas cercanas tienden a compartir litología, estructuras, relieve y firmas geoquímicas. Si vecindarios casi idénticos se repartieran aleatoriamente entre train y validation, el modelo podría reconocer continuidad espacial en lugar de aprender asociaciones transferibles. Bloquear por territorio estima mejor el comportamiento cuando se priorizan zonas no vistas.

**Visual sugerido:** esquema “outer_00: train externo” que contiene tres pares train/validation internos; fuera de él, test externo y reserva con candado.

---

## Slide 6 — U1.1: perceptrón como baseline geométrico interpretable

**Objetivo técnico**  
Explicar el límite de una frontera lineal con dos variables reales antes de pedir mayor capacidad a una MLP.

**Decisiones metodológicas y trade-offs**

- Se comprueban puertas OR/AND para verificar el mecanismo del perceptrón y después se entrena con distancia a falla cartografiada y pendiente, estandarizadas en train.
- La proyección 2D es deliberadamente pedagógica, no el modelo final de 93 predictores.
- Trade-off: gana interpretabilidad geométrica, pero pierde litología, geoquímica, otras estructuras y relaciones no lineales.

**Resultados cuantitativos reales del notebook**

- OR y AND reprodujeron correctamente sus **4/4** casos lógicos.
- Perceptrón 2D: accuracy de train **0,6570** y accuracy P/U de validation **0,7043**.
- Pesos estandarizados: distancia a falla **0,0195**, pendiente **0,6415**; bias **0,0**.
- La accuracy mayoritaria de esa validation es **0,9913**, prueba de que accuracy es inadecuada como métrica de priorización bajo fuerte desbalance.

**Razonamiento físico/geoespacial/algorítmico**  
El perceptrón sólo puede desplazar y rotar un hiperplano: en 2D, una recta. El peso mayor de pendiente en esta proyección indica cómo esa separación lineal reduce la loss P/U en esa muestra, no que la pendiente sea un controlador causal de la mineralización. La distancia a falla por sí sola tampoco captura tipo, cinemática, conectividad o edad de la estructura.

**Visual sugerido:** reutilizar la frontera 2D de validation generada en el notebook; anotar que se trata de variables estandarizadas y P/U, no de una ley geológica.

---

## Slide 7 — U1.2–U1.3: por qué una capa oculta puede representar relaciones geológicas más ricas

**Objetivo técnico**  
Conectar XOR y la propagación hacia delante con la capacidad de modelar interacciones entre señales geocientíficas.

**Decisiones metodológicas y trade-offs**

- XOR se usa sólo como prueba lógica de no separabilidad lineal; no simula geología.
- La demostración Keras usa una capa `tanh(4)` y salida sigmoid; la MLP de proyecto usa ReLU en capas ocultas y sigmoid para P/U.
- Se muestra un forward manual con pesos didácticos sobre una celda real; no se presenta como score validado.

**Resultados cuantitativos reales del notebook**

- XOR Keras clasificó los cuatro patrones correctamente: scores **0,000173**, **0,996447**, **0,998423** y **0,003406** para objetivos 0, 1, 1, 0.
- Forward manual de una celda: `x = [-0,5258, 0,4459]`, activación ReLU no nula `0,4117`, logit `−0,1858` y score P/U didáctico **0,4537**.

**Razonamiento físico/geoespacial/algorítmico**  
Una capa oculta aprende representaciones intermedias, por ejemplo combinaciones de proximidad a estructuras, litología y anomalías, que pueden activar regiones no separables mediante una sola regla lineal. Esto es capacidad representacional, no evidencia automática de que tales interacciones existan, sean estables o generalicen fuera de los folds.

**Visual sugerido:** cuatro puntos XOR → capa oculta → regiones separables; junto a la ecuación `h=ReLU(XW₁+b₁)`, `s=sigmoid(hW₂+b₂)`.

---

## Slide 8 — U1.4–U1.5: optimización verificable y significado de las activaciones

**Objetivo técnico**  
Evidenciar que el entrenamiento no es una caja negra: se verifican gradientes, se reduce la BCE y se alinea activación–loss–objetivo.

**Decisiones metodológicas y trade-offs**

- Para P/U se utiliza BCE y salida sigmoid; ReLU aporta no linealidad en ocultas. Step queda restringida al perceptrón didáctico porque no es apropiada para backpropagation estándar.
- Se contrasta gradiente analítico con diferencias finitas en una neurona sigmoid; el chequeo valida la implementación local, no la validez geológica del target.
- Se ilustra Softmax sin crear artificialmente clases BAJO/MEDIO/ALTO de oro; esas clases no existen en los datos de esta fase.

**Resultados cuantitativos reales del notebook**

- Error absoluto máximo del gradient check: **6,42 × 10⁻¹¹**, menor que el umbral de **10⁻⁶**.
- Descenso manual: BCE inicial **0,693147** y BCE tras las actualizaciones **0,545447**.
- Parámetros finales de esa neurona didáctica: `[-0,1520, 0,3116, −0,9765]`.
- La softmax ilustrativa `[1, 2, 3]` produjo `[0,0900, 0,2447, 0,6652]`, suma **1,0**.

**Razonamiento físico/geoespacial/algorítmico**  
Backpropagation calcula cómo cambiar pesos para disminuir un contraste estadístico P/U. Sigmoid convierte un logit en score 0–1, pero el intervalo numérico no crea calibración física. ReLU evita la saturación positiva típica de sigmoid en capas ocultas, aunque puede inactivar neuronas para entradas negativas.

**Visual sugerido:** cadena “forward → BCE → gradientes → Adam → pesos actualizados”, con el gradient-check como control unitario.

---

## Slide 9 — Diseño comparativo: arquitecturas, baselines y criterio de éxito

**Objetivo técnico**  
Justificar que la selección no favorece arbitrariamente a Deep Learning y que el criterio responde al presupuesto territorial.

**Decisiones metodológicas y trade-offs**

- MLPs definidas antes de examinar resultados: superficial `[32]`, U1 `[32,16]`, profunda `[64,32,16]` y regularizada `[32,16]` con Dropout 0,2 y L2 0,001.
- Adam con learning rate **0,001**, máximo **100** épocas, batch **32**, BCE, ReLU/sigmoid; `EarlyStopping` restaura el menor `val_loss` con paciencia **10**.
- Referencias reajustadas bajo las mismas filas y splits: perceptrón, logística `C=1` y RF de **500** árboles con hoja mínima **5**.
- Métrica primaria: recuperación al 5 % del área; AP y ROC-AUC P/U son auxiliares. F1/accuracy a umbral 0,5 no eligen arquitectura.
- Margen exploratorio prefijado: mejora pareada de al menos **0,02** frente a cada baseline. Trade-off: exige relevancia práctica mínima, pero aún no equivale a validación final independiente.

**Resultados cuantitativos reales del notebook**

- Parámetros por fold: MLP superficial **5.537–5.601**, U1 y regularizada **6.049–6.113**, profunda **13.633–13.761**.
- Mejor época restaurada: superficial **12/12/12**, U1 **8/7/2**, profunda **3/3/2**, regularizada **10/14/9** en los tres folds.

**Razonamiento físico/geoespacial/algorítmico**  
La recuperación al 5 % pregunta: “si sólo se puede investigar el 5 % del territorio evaluado, ¿qué fracción de candidatos conocidos cae dentro de esa envolvente de prioridad?”. Así enlaza el modelo con coste de campaña y superficie inspeccionable. RF representa una referencia tabular no lineal fuerte; la logística mide el valor de una frontera global lineal.

**Visual sugerido:** tabla compacta de las cuatro MLP y tres baselines; resaltar en color la métrica primaria, no F1/accuracy.

---

## Slide 10 — Resultados principales: ranking territorial y métricas auxiliares

**Objetivo técnico**  
Presentar la comparación honesta de los siete modelos con medias de los tres folds internos.

**Decisiones metodológicas y trade-offs**

- Se da el mismo peso a cada fold y se informa la desviación estándar descriptiva; no se convierte esa dispersión en un intervalo de confianza porque los entrenamientos internos se solapan.
- Se ordena por recuperación media al 5 % de área, no por una métrica auxiliar favorable a una familia concreta.

**Resultados cuantitativos reales del notebook**

| Modelo | Recuperación @ 5 % (media ± DE) | AP P/U | ROC-AUC P/U | F1 P/U @ 0,5 |
|---|---:|---:|---:|---:|
| Random Forest | **0,4717 ± 0,0364** | **0,1912** | **0,8917** | **0,2446** |
| MLP regularizada `[32,16]` | 0,4356 ± 0,1156 | 0,0941 | 0,8670 | 0,1344 |
| MLP profunda `[64,32,16]` | 0,3956 ± 0,0604 | 0,0810 | 0,8451 | 0,1416 |
| MLP superficial `[32]` | 0,3863 ± 0,1068 | 0,0817 | 0,8573 | 0,1196 |
| MLP U1 `[32,16]` | 0,3831 ± 0,1440 | 0,0704 | 0,8366 | 0,1326 |
| Regresión logística | 0,3119 ± 0,0945 | 0,0590 | 0,8220 | 0,1093 |
| Perceptrón | 0,2643 ± 0,0397 | 0,0512 | 0,8102 | 0,0962 |

**Razonamiento físico/geoespacial/algorítmico**  
RF domina tanto la métrica territorial como AP, AUC y F1 de este ensayo, señal de que sus particiones pueden acomodar no linealidades e interacciones tabulares sin el coste de ajuste de una MLP. La regularización sí mejora a las otras redes, pero no elimina la brecha con RF ni convierte el score en validación de descubrimientos.

**Visual sugerido:** barras de recuperación @5 % con puntos de los tres folds superpuestos; no utilizar sólo la media.

---

## Slide 11 — Sensibilidad entre folds: el mejor caso no es la conclusión

**Objetivo técnico**  
Evitar elegir una arquitectura por su fold más favorable y exponer la estabilidad real observada.

**Decisiones metodológicas y trade-offs**

- Se comparan resultados pareados por fold, porque cada modelo evalúa exactamente el mismo territorio de cada partición.
- No se ocultan los casos favorables a MLP ni los contrarios; la selección usa la media de recuperación de los tres folds.
- Trade-off: con sólo tres folds internos no se reclama significación estadística ni independencia entre mediciones.

**Resultados cuantitativos reales del notebook**

| Fold interno | RF @5 % | MLP regularizada @5 % | Diferencia MLP − RF |
|---|---:|---:|---:|
| `outer_00_inner_00` | 0,4318 | 0,3409 | −0,0909 |
| `outer_00_inner_01` | 0,5031 | **0,5644** | +0,0613 |
| `outer_00_inner_02` | 0,4803 | 0,4016 | −0,0787 |
| **Media pareada** | **0,4717** | **0,4356** | **−0,0361** |

- Frente a logística, la ganancia media pareada de la MLP regularizada fue **+0,1237**; frente a RF fue **−0,0361**.

**Razonamiento físico/geoespacial/algorítmico**  
La victoria de la MLP en el segundo bloque muestra que puede capturar una estructura útil en algunas particiones, pero su incapacidad para repetirla en las otras dos señala sensibilidad a la distribución espacial de P/U. En exploración, una mejora local no es evidencia suficiente para sustituir un método que rinde mejor de forma más consistente.

**Visual sugerido:** gráfico de líneas por fold ya generado en el notebook, con RF y MLP regularizada enfatizados.

---

## Slide 12 — Capacidad y regularización: evidencia de sobreajuste y efecto de los controles

**Objetivo técnico**  
Relacionar curvas de entrenamiento con la decisión de usar regularización y parada temprana, sin atribuir causalidad excesiva a una sola técnica.

**Decisiones metodológicas y trade-offs**

- L2 penaliza magnitudes de peso; Dropout 0,2 desactiva unidades durante train; EarlyStopping detiene/restaura pesos según `val_loss`. Son mecanismos distintos.
- En modelos L2, la loss incluye penalización y Dropout actúa sólo en train; por tanto los valores absolutos de loss entre arquitecturas no se comparan como si fuesen idénticos.
- Trade-off: la regularización limita capacidad de memorizar train y puede mejorar transferencia, pero también puede infraajustar si se aplica en exceso.

**Resultados cuantitativos reales del notebook**

- MLP profunda, fold 00: mejor `val_loss` **0,1657** en época **3**; al final de la época 13, train loss bajó a **0,0411** mientras validation loss subió a **0,3229**.
- MLP regularizada, fold 00: mejor `val_loss` **0,2071** en época **10**; terminó en época 20 con train **0,1881** y validation **0,2506**.
- La red profunda tiene más del doble de parámetros que `[32,16]` (≈**13,6–13,8 mil** frente a ≈**6,0–6,1 mil**) y no supera a la regularizada en recuperación media.

**Razonamiento físico/geoespacial/algorítmico**  
La caída sostenida de loss de train junto con deterioro de validation es el patrón de memorización relativa a las muestras P/U internas. En un dominio espacial con pocos P y variables correlacionadas, más capacidad puede aprender peculiaridades locales de la partición. EarlyStopping conserva el punto de mejor transferencia observada, pero se eligió con esos mismos folds y no reemplaza un test final.

**Visual sugerido:** cuatro curvas train/validation del fold 00, con la época restaurada marcada; aclarar la diferencia de escala/penalización de loss.

---

## Slide 13 — Interpretación de la decisión: qué se puede afirmar y qué no

**Objetivo técnico**  
Cerrar el MUST Gate con una conclusión técnicamente defendible y límites explícitos.

**Decisiones metodológicas y trade-offs**

- La arquitectura seleccionada exploratoriamente es `mlp_regularizada`, por mayor media de recuperación entre las redes.
- El umbral de relevancia predefinido es 0,02 frente a **cada** baseline. La MLP cumple frente a logística (+0,1237) pero falla frente a RF (−0,0361).
- Se elige no abrir el test para “buscar” una conclusión favorable: ese sacrificio de inmediatez preserva la evaluación final.

**Resultados cuantitativos reales del notebook**

```json
{
  "selected_by_validation": "mlp_regularizada",
  "minimum_relevant_gain": 0.02,
  "mean_paired_gain": {"random_forest": -0.03610, "logistic": 0.12371},
  "promising_in_validation": false,
  "improvement_demonstrated_on_test": false
}
```

**Razonamiento físico/geoespacial/algorítmico**  
La elección de la mejor MLP responde a una pregunta didáctica de arquitectura; no es una recomendación de modelo de producción. La decisión de ingeniería actual es mantener RF como referencia ganadora en validación interna y tratar la MLP regularizada como hipótesis a contrastar, nunca como un mapa de probabilidad absoluta de oro o un sustituto de trabajo geológico.

**Visual sugerido:** tabla “Afirmación permitida / No permitida”.

| Permitido | No permitido |
|---|---|
| La MLP regularizada supera a logística en estas validaciones internas. | La red supera a RF. |
| RF es la mejor referencia en recuperación media interna. | La red/RF ha demostrado rendimiento en test o producción. |
| Los scores ordenan evidencia P/U diagnóstica. | Un score alto es probabilidad absoluta de encontrar oro. |

---

## Slide 14 — Reproducibilidad, auditoría y controles de ingeniería

**Objetivo técnico**  
Evidenciar que las conclusiones pueden ser reproducidas, inspeccionadas y rechazadas si se rompe una salvaguarda.

**Decisiones metodológicas y trade-offs**

- Semilla fija 42 y operaciones deterministas cuando TensorFlow lo permite; se reconoce que hardware/implementaciones pueden introducir diferencias fuera del entorno registrado.
- Se guardan configuración, versiones, hashes SHA-256 de entradas, esquema, preprocesadores, modelos, historiales, predicciones por celda, métricas, decisión y manifiesto de salidas.
- Validadores prueban gradientes, equivalencia forward–Keras, ausencia de estadística de validation en train, categorías nuevas, rechazo de test/reserva y recarga de modelos.
- Trade-off: el nivel de trazabilidad incrementa almacenamiento y disciplina operativa, pero permite auditoría de los resultados y de la ausencia de fuga.

**Resultados cuantitativos reales del notebook**

- El manifiesto contiene **21** modelos de ajuste: 12 MLP `.keras` y 9 baselines `.joblib`, además de preprocesadores, predicciones, historiales y métricas.
- `outputs_manifest.json` fue verificado por el notebook y `scripts/validar_unidad1.py` finalizó correctamente sobre esta ejecución.
- Entorno registrado: TensorFlow **2.21.0**, Keras **3.15.1**, scikit-learn **1.9.1**, NumPy **2.5.3** y pandas **3.0.6**.

**Razonamiento físico/geoespacial/algorítmico**  
En una priorización territorial, una diferencia de versión, una categoría codificada de otro modo o una contaminación de validation puede cambiar el orden de miles de celdas. Trazar tanto transformación como predicción permite reconstruir qué evidencia llegó al modelo y con qué reglas, condición necesaria antes de convertir un ranking en una decisión de exploración.

**Visual sugerido:** cadena de trazabilidad: configuración/inputs con hash → preprocesador → modelo → scores por celda → métricas/decisión → manifiesto verificado.

---

## Slide 15 — Cierre ante el comité y próximo gate técnico

**Objetivo técnico**  
Convertir los hallazgos en una recomendación de ingeniería proporcionada a la evidencia disponible.

**Decisiones metodológicas y trade-offs**

- Aceptar la fase como evidencia de dominio conceptual, implementación reproducible y comparación interna honesta.
- No promover ninguna MLP a producción ni afirmar descubrimiento/validación de oro antes de una evaluación final independiente autorizada.
- Si se autoriza la continuidad, fijar arquitectura y protocolo antes de abrir test externo; no retocar hiperparámetros tras ver ese resultado.

**Resultados cuantitativos reales del notebook**

- La mejor red recupera **43,56 %** de P candidatos en el 5 % de área; RF recupera **47,17 %**.
- La brecha es **3,61 pp** a favor de RF; la red no alcanza el margen mínimo de **2 pp** contra todos los baselines.
- Test externo evaluado: **no**. Reserva evaluada: **no**. Producción permitida: **no**.

**Razonamiento físico/geoespacial/algorítmico**  
La mejor decisión no es la arquitectura más compleja sino la que ofrece valor reproducible para el presupuesto espacial y la incertidumbre geológica del problema. Hoy la evidencia favorece conservar RF como referencia de validación y usar la MLP regularizada como aprendizaje/hipótesis. Un test territorial independiente decidirá si cualquiera de las dos generaliza fuera de la selección interna.

**Solicitud al comité**  
Validar el cierre de U1 como fase diagnóstica y, si procede continuar, aprobar un protocolo sellado de evaluación externa que incluya: modelo/hiperparámetros congelados, métrica primaria de recuperación por área, reglas de comparación, interpretación P/U y criterio de promoción explícito.

---

## Anexo A — Respuestas breves a objeciones previsibles

### “¿Por qué no usar accuracy si llega a ser alta?”

Porque P es extremadamente minoritario en el marco P/U. En la demostración 2D, predecir siempre la clase mayoritaria da 99,13 % de accuracy, aunque no priorice candidatos. Recuperación al 5 % responde al presupuesto de área; AP y AUC evalúan ranking en la muestra P/U fija.

### “¿La sigmoid dice que hay un 80 % de probabilidad de oro?”

No. En modo diagnóstico, la sigmoid es un score para separar candidatos P de fondo U según la muestra y el preprocesado. U no es ausencia confirmada; no se ha hecho calibración de probabilidad absoluta ni validación geológica independiente.

### “La MLP ganó un fold: ¿por qué no elegirla?”

Porque perdió frente a RF en los otros dos folds y su media pareada es −3,61 pp. Elegir el mejor caso sería selección oportunista de una partición, no evidencia de generalización estable.

### “¿Por qué no abrir el test ahora para resolverlo?”

Porque la arquitectura MLP ya se seleccionó usando estas validaciones. El test debe recibir un procedimiento congelado una sola vez; reabrirlo para iterar convertiría el test en otra validation y sesgaría su estimación.

### “¿Qué aporta la Unidad 1 si RF sigue ganando?”

Demuestra de forma reproducible los mecanismos de una red, implementa controles contra fuga, compara capacidad/regularización y concluye sin sesgo de familia. Que RF gane es un resultado útil: evita desplegar complejidad no justificada.

## Anexo B — Artefactos de respaldo

- [Notebook de la fase](../notebooks/15_unidad1_redes_neuronales.ipynb)
- [Guía local de Unidad 1](../notebooks/LEEME_UNIDAD1.md)
- [Configuración congelada](../config/unidad1.yaml)
- [Resumen de validación](../reports/unidad1/20260920T112741_562792Z/validation_summary.csv)
- [Métricas por fold](../reports/unidad1/20260920T112741_562792Z/validation_metrics.csv)
- [Decisión automatizada](../reports/unidad1/20260920T112741_562792Z/decision.json)
- [Control de alcance](../reports/unidad1/20260920T112741_562792Z/control.json)
- [Esquema de variables](../reports/unidad1/20260920T112741_562792Z/feature_schema.json)

## Anexo C — Matriz de correspondencia con el reto de aguacates

| Unidad del reto | Adaptación GeoAI en fase 15 | Límite de interpretación |
|---|---|---|
| 1.1 Perceptrón | OR/AND y frontera con distancia a falla + pendiente | Proyección 2D didáctica; pesos no causales |
| 1.2 MLP/XOR | XOR y MLP Keras | XOR no representa datos geológicos |
| 1.3 Forward | Cálculo manual sobre una celda real | Pesos didácticos; score no validado |
| 1.4 Gradiente | BCE P/U, diferencias finitas y descenso manual | Validar el gradiente no valida el target |
| 1.5 Activaciones | ReLU/sigmoid y comparación de activaciones | Sigmoid no está calibrada como probabilidad de oro |
| 1.6 Profundidad | Cuatro MLP frente a logística, perceptrón y RF | Sólo selección interna, no test |
| 1.7 Regularización | L2, Dropout, EarlyStopping y curvas espaciales | Las curvas no prueban por sí solas causalidad ni generalización externa |
