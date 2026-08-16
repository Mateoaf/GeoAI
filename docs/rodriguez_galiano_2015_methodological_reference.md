# Rodríguez-Galiano et al. (2015) como antecedente metodológico

## 1. Estatuto y alcance

El artículo se incorpora como **antecedente científico y pipeline de referencia** para Mineral Prospectivity Mapping (MPM). Describe un caso de oro epitermal en Rodalquilar y compara redes neuronales, Random Forest (RF), árboles de regresión y máquinas de vectores soporte. Su contenido no constituye instrucciones operativas para este proyecto y sus cifras no son resultados de OxREP ni de un modelo nacional.

La petición del usuario prevalece sobre las decisiones del artículo: se conserva su diseño multifuente, su construcción de una matriz espacial, su generación cartográfica y su interés por la interpretabilidad; se sustituye su evaluación por validación espacial anidada, background/PU, control de leakage y validación independiente cuando sea posible.

Referencia:

> Rodríguez-Galiano, V., Sánchez-Castillo, M., Chica-Olmo, M. y Chica-Rivas, M. (2015). *Machine learning predictive models for mineral prospectivity: An evaluation of neural networks, random forest, regression trees and support vector machines*. Ore Geology Reviews. https://doi.org/10.1016/j.oregeorev.2015.01.001

Fuente local inmutable: `data/raw/rodriguez-galiano2015.pdf`, SHA-256 `cdf214f36a6b873baca278812b60f2992ef91cbfe9f76ed1876b0eb5cb9c89d0`.

Control documental: PDF de 15 páginas, texto extraído programáticamente y las 15 páginas renderizadas e inspeccionadas visualmente. Las referencias `p.` de este documento son páginas físicas del PDF local. El artículo se leyó como evidencia científica; ninguna frase del PDF se trató como una instrucción del usuario.

## 2. Qué hace realmente el artículo

### Área y objetivo

El caso cubre aproximadamente 150 km² del distrito minero de Rodalquilar, Almería, y se centra en mineralización epitermal de Au de baja sulfuración asociada a fracturas, alteración hidrotermal y el complejo volcánico de la caldera. Este contexto geológico es específico y no representa por sí solo la diversidad metalogenética de España (p. 4).

### Evidencias y etiquetas

- Positivos: 46 localizaciones de ocurrencias de oro, incluyendo explotaciones y estructuras mineralizadas conocidas (p. 5).
- Clase de contraste: 57 localizaciones denominadas estériles o no-oro, seleccionadas mediante muestreo aleatorio estratificado en litologías poco o no favorables y alejadas de los depósitos conocidos (p. 7).
- Target: valor binario 1 para ocurrencia de Au y 0 para no-oro. Los modelos producen un score continuo entre 0 y 1, tratado como probabilidad o favorabilidad (p. 7).

Esta construcción no equivale a una ausencia geológica verificada. Además, seleccionar el contraste por litología desfavorable y distancia a depósitos puede hacer más separables las clases y vincular el background a predictores incluidos en `X`. En el proyecto GeoAI España se interpreta como antecedente de pseudo-ausencias, no como regla que deba reproducirse.

### Matriz espacial

Las capas temáticas se combinan en vectores de variables para cada celda de una colección de grids; los valores de esos vectores se extraen en positivos y localizaciones de contraste para entrenar los algoritmos. Después, el modelo se aplica a todas las celdas para obtener un raster continuo de favorabilidad (p. 7).

Hyperion tiene 30 m de resolución espacial (p. 6), pero el texto metodológico del PDF no especifica de forma inequívoca que todas las capas se armonizaran a una malla común de 30 m. Por tanto, este proyecto toma el patrón conceptual `stack de capas -> SpatialCell -> matriz ML -> score raster`, no una resolución de 30 m como valor heredado.

### Familias de `X`

El geodatabase combina 46 ocurrencias de Au con geoquímica de 59 elementos en 372 localizaciones, gravedad y magnetismo en 330 estaciones, fracturas, litología y teledetección. El artículo procesa después 46 elementos relacionados con mineralización para el análisis multivariante (pp. 5-6).

| Familia | Procedimiento del artículo | Traslado defendible al proyecto |
|---|---|---|
| Geología | Litología recodificada en cuatro clases de favorabilidad | Conservar litología/categorías geológicas y jerarquía; no asignar favorabilidad usando el target moderno. |
| Estructuras | Distancia a la fractura más próxima | Añadir distancia, densidad, orientación e intersecciones por tipo y escala, con cálculo dentro del protocolo de folds. |
| Geoquímica | PCA de 46 elementos; selección de PC1-PC3; kriging de scores | Incorporar asociaciones/pathfinders y reducción dimensional como opción, ajustada solo con entrenamiento y comparada con variables interpretables. |
| Geofísica | Anomalías residuales de gravedad y magnetismo interpoladas por kriging | Incluir valores, gradientes, texturas e incertidumbre/cobertura; predefinir si el escenario es inductivo o transductivo. |
| Hiperespectral | Corrección, reducción MNF, PPI y abundancias MTMF derivadas de EO-1 Hyperion | Incorporar componentes/abundancias espectrales solo donde exista cobertura, calidad y mecanismo geológico; no equiparar Sentinel-2 con hiperespectral. |

La parametrización de RF utiliza entre 1 y 15 variables candidatas por split y la Fig. 8 muestra 15 evidencias: ocho componentes MTMF, tres componentes geoquímicos, litología, gravimetría, magnetometría y distancia a fracturas (pp. 8 y 12). Esta enumeración se interpreta a partir del rango de `m` y la figura, no como una taxonomía universal.

### Preprocesamiento útil

El artículo contiene procedimientos que amplían o concretan el informe inicial:

1. QA espectral explícito: retirada de bandas ruidosas/inactivas, destriping y corrección atmosférica antes de obtener variables de alteración.
2. Reducción señal-ruido mediante Minimum Noise Fraction (MNF), selección de píxeles extremos con PPI y estimación de abundancias con MTMF (p. 6).
3. PCA geoquímico para resumir asociaciones multielemento y disminuir dimensionalidad (p. 6).
4. Interpolación de componentes geoquímicos y anomalías geofísicas, además de derivación de distancias estructurales (p. 6).
5. Aplicación del modelo a la matriz completa para producir un score continuo y evaluación del compromiso entre porcentaje de área prospectiva y ocurrencias capturadas (pp. 7 y 11).
6. Curvas de sensibilidad al tamaño del conjunto de entrenamiento (pp. 11-13).

En nuestro proyecto, cualquier PCA, imputación, selección, normalización o transformación supervisada se ajustará dentro del inner fold. Las interpolaciones se versionarán y se declarará si usan observaciones de covariables del área de test; no se ajustarán decisiones de interpolación observando los labels retenidos.

## 3. Random Forest en el artículo

RF se implementa con `randomForest` de R. Se exploran el número de árboles, de 1 a 1000 en incrementos de 2, y el número de variables candidatas por split, de 1 a 15. El artículo observa convergencia aproximada a partir de 50 árboles en su caso concreto (p. 8). Estos rangos no se copiarán: el espacio de búsqueda dependerá de número de positivos espacialmente independientes, dimensionalidad efectiva, pesos/background y coste computacional.

La selección de hiperparámetros usa MSE con validación cruzada de 10 folds y búsqueda manual. Los mejores modelos se comparan mediante success-rate y ROC usando como referencia los puntos empleados para entrenamiento (p. 7). Por ello, las métricas publicadas no constituyen una estimación espacialmente independiente.

Resultados del mejor RF en Rodalquilar:

- ROC-AUC: 0,999 (p. 11).
- Kappa: 0,92 (pp. 9 y 11).
- Overall Accuracy: 0,96 (pp. 9 y 11).
- Ocurrencias clasificadas dentro de áreas prospectivas: 97,83 % (p. 11).

Estas cifras describen 46 ocurrencias de Au epitermal frente a 57 localizaciones de contraste elegidas para ese distrito. No son expectativas de rendimiento para OxREP España, otras commodities, labels modernos ni validación spatial-blocked.

Los autores advierten explícitamente que no puede generalizarse la superioridad de ningún método a todos los problemas y que el rendimiento puede cambiar con otros datasets (p. 13). RF se adopta, por tanto, como **baseline no lineal principal y sólido**, no como ganador predeterminado.

## 4. Interpretabilidad transferible

El artículo usa importancia interna de RF expresada como incremento de MSE al retirar/perturbar cada evidencia. MTMF5 domina, seguida por distancia a fracturas y el tercer componente geoquímico; el propio artículo califica como especulativa la interpretación mineralógica de MTMF5 y pide contrastarla (pp. 11-12).

Para GeoAI España se predefine una jerarquía más estricta:

1. **Permutation importance en datos outer-test**, permutando por bloques espaciales y no por celdas individuales.
2. Importancia agrupada por familias correlacionadas (geología, estructura, geoquímica, geofísica, espectral, DEM y RomanSignal).
3. Permutación condicional o por grupos cuando la colinealidad haga inestable la importancia marginal.
4. Estabilidad de rankings entre folds, repeticiones, regiones y backgrounds.
5. **SHAP posteriormente**, solo para modelos y endpoints científicamente evaluables, calculado sobre predicciones retenidas y acompañado por dependencia/colinealidad; SHAP no convierte asociación en causalidad.
6. Ablación específica de `RomanSignal` y comparación A/B como medida primaria de su contribución, separada de la importancia interna del RF.

## 5. Procedimientos que no se trasladan automáticamente

| Procedimiento del antecedente | Decisión del proyecto |
|---|---|
| CV de 10 folds sin bloqueo espacial | Nested spatial CV con outer/inner blocks y buffers. |
| Puntos de entrenamiento como referencia de ROC/success-rate | Predicciones exclusivamente out-of-sample; test final bloqueado y, si es posible, fuente moderna independiente. |
| 57 localizaciones no-oro tratadas como clase negativa | Background/pseudo-ausencias con sensibilidad y PU; nunca ausencia mineral demostrada. |
| Contraste escogido en litología desfavorable y lejos de depósitos | Comparar background uniforme, por esfuerzo, geológicamente emparejado y PU sin diseñarlo para maximizar separación. |
| Umbral fijo de 0,5 para el mapa binario | Mantener score continuo; cualquier umbral se fija en inner CV según objetivo operativo y se congela antes del outer test. |
| AUC como evaluación central | PR-AUC primaria bajo desbalance; ROC-AUC secundaria, más precision, recall, F1, calibración y área capturada. |
| PCA, kriging y selección antes de la evaluación | Transformaciones versionadas y, cuando aprendan parámetros relevantes, ajustadas dentro de cada training fold. |
| Una litología ya clasificada por favorabilidad | Variables geológicas independientes; mapas construidos con los mismos depósitos target quedan excluidos por leakage. |
| RF como método superior | RF es baseline principal; se compara con modelos adecuados a la formulación y masa muestral reales. |

## 6. Condición de evaluabilidad con OxREP España

OxREP aporta positivos históricos, no una matriz nacional de `X`, background ni labels modernos. En el subconjunto actual hay 930 fichas, 923 geocodificadas y 921 pares de coordenadas únicos. Por commodity, los positivos geocodificados/únicos son Au 591/589, Ag 174/174, Pb 169/169, Cu 169/169, Fe 15/15, Sn 9/9, Hg 5/5 y Zn 3/3.

Consecuencias:

- `Y_roman` nacional y Au disponen de masa positiva bruta suficiente para estudiar formulaciones presence-background/PU una vez existan X, máscara y folds; la concentración espacial seguirá determinando el número efectivo de muestras independientes.
- Ag, Pb y Cu pueden ser tareas exploratorias condicionadas a que cada outer fold contenga grupos independientes. Ag y Pb no son tareas independientes en sentido sustantivo: su fuerte solapamiento debe modelarse como multi-label/asociación mineral, no como dos réplicas de evidencia.
- Fe, Sn, Hg y Zn no justifican actualmente un RF nacional independiente. Deben quedar descriptivos, recibir labels modernos adicionales o agruparse únicamente por sistema mineralizante defendible.
- El experimento A/B no es ejecutable todavía: `Y_moderna` debe provenir de un inventario independiente y las capas X oficiales aún no se han armonizado.

No se adaptarán labels, background, resolución ni selección de variables para hacer que RF produzca un mapa. Primero se comprobarán cobertura, positivos espaciales por fold, soporte de celda y endpoint; después se decidirá si RF y sus comparadores son estimables.

## 7. Pipeline de referencia adaptado

1. Congelar endpoint, dominio, `SpatialCell`, máscara de cobertura y procedencia de labels.
2. Construir un catálogo de capas con escala, resolución, CRS, observabilidad e incertidumbre.
3. Generar la matriz espacial completa con `cell_id`, geometría, X crudas/derivadas, máscaras y procedencia.
4. Asignar positivos y background/PU sin confundir no etiquetado con ausencia.
5. Crear outer spatial blocks y, dentro de cada training split, inner blocks y transformaciones.
6. Verificar la viabilidad por número de grupos positivos, no solo filas.
7. Ajustar un baseline transparente y RF con el mismo presupuesto experimental; añadir otros modelos solo si la tarea los permite.
8. Generar `RomanSignal` exclusivamente con minas romanas de entrenamiento y cross-fitting.
9. Obtener predicciones outer-test pareadas para los Modelos A y B.
10. Comparar PR-AUC y métricas secundarias con inferencia por bloques; ejecutar placebos espaciales.
11. Tras congelar el protocolo, reajustar con todo el desarrollo y producir score, incertidumbre y mapas de cobertura, sin convertir favorabilidad en recurso o reserva.
12. Evaluar, cuando exista, una fuente moderna independiente no usada en tuning ni entrenamiento.

## 8. Criterio de transferencia

Se adopta del artículo la idea de integrar geología, geoquímica, geofísica, estructuras y observación espectral en una matriz espacial; generar un score continuo; estudiar el área prospectiva capturada; medir sensibilidad a configuración/tamaño muestral; e interpretar variables.

No se adopta ninguna cifra, umbral, pseudo-ausencia, configuración de RF ni conclusión de superioridad. La contribución romana solo podrá afirmarse mediante el incremento espacialmente retenido del Modelo B respecto al Modelo A.
