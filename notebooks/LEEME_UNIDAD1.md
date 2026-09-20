# Unidad 1 · Redes neuronales en GeoAI

El cuaderno [15_unidad1_redes_neuronales.ipynb](15_unidad1_redes_neuronales.ipynb) adapta los apartados **1.1–1.7** del reto de aguacates al proyecto aurífero. El límite se interpreta como no entrar en la **Unidad 2**. El archivo `implementar Unidad 1.txt` aporta la arquitectura MLP de dos capas `[32,16]`, escalado, Adam y BCE. Las instrucciones de los documentos se han utilizado como contexto para la adaptación solicitada.

## Contenido y adaptación

| Apartado | Implementación |
|---|---|
| 1.1 | OR/AND y perceptrón con distancia a falla y pendiente reales; frontera en validación |
| 1.2 | XOR resuelto con capa oculta manual y MLP Keras |
| 1.3 | Forward manual de una celda de entrenamiento, ReLU y sigmoid |
| 1.4 | BCE, gradientes analíticos comprobados con diferencias finitas y descenso manual P/U |
| 1.5 | Step, sigmoid, tanh, ReLU, LeakyReLU, linear y ejemplo softmax |
| 1.6 | Comparación de redes `[32]`, `[32,16]`, `[64,32,16]` y variante regularizada |
| 1.7 | Saturación, gradientes pequeños, curvas, L2, Dropout y EarlyStopping |

El código reutilizable está en `src/geoau/neural_u1.py` y la configuración en `config/unidad1.yaml`. No se modifica el módulo F, su configuración ni sus resultados sellados. Los cuadernos previos se conservan.

## Diseño experimental

Se consume F `20260909T184735_016759Z`, ligada a las ejecuciones E/D existentes. La configuración actual es diagnóstica: **P son candidatos y U es terreno no etiquetado**. Los scores no expresan probabilidad absoluta de oro.

Se utilizan los tres folds internos del primer fold externo `outer_00`, prefijado por configuración; ratio U/P=3 y realización 0. Es un ensayo didáctico acotado de U1, no la evaluación anidada completa de una nueva familia de producción. No se generan predicciones ni métricas de test externo o reserva. La comparación definitiva del reto pertenece a U3 y queda fuera de esta entrega.

Cada preprocesador aprende imputación, categorías y escalado exclusivamente en su train interno. Se conservan las guardias de columnas y muestras de F. No se incluyen coordenadas, IDs, etiquetas ni metadatos de yacimientos en X. Categorías nuevas se representan como desconocidas; columnas numéricas totalmente vacías en train se conservan con relleno cero.

MLP, logística y RF comparten filas y evaluación. RF y logística se reajustan como referencias fijas: 500 árboles/hoja mínima 5 y `C=1`, respectivamente. No se comparan métricas nuevas de validación con los scores históricos de test. La MLP usa ReLU, salida sigmoid, Adam 0.001, BCE, lotes de 32 y hasta 100 épocas. EarlyStopping restaura la mejor `val_loss`, con paciencia 10, sobre validación espacial explícita.

La selección usa media de recuperación al 5 % del área. AP y ROC-AUC se computan sobre el marco fijo P/U de F; F1 y accuracy usan umbral 0.5. Son métricas del diseño de muestreo. Las diferencias con RF/logística se calculan dentro de cada fold y después se promedian. El margen exploratorio predefinido es 0.02. No se presenta la dispersión entre folds como un intervalo de confianza ni se afirma mejora demostrada en test.

## Entorno y ejecución

Se ha preparado un entorno independiente `.venv-unidad1` con Python 3.13 y TensorFlow 2.21.0. `.venv-fase-a` se conserva. Compatibilidad consultada en la [documentación de TensorFlow](https://www.tensorflow.org/install/pip); semántica de restauración en [EarlyStopping](https://keras.io/api/callbacks/early_stopping/) y validación explícita en la [API de entrenamiento Keras](https://keras.io/api/models/model_training_apis/).

Para recrearlo en Windows:

```powershell
py -3.13 -m venv .venv-unidad1
.\.venv-unidad1\Scripts\python.exe -m pip install -r requirements-unidad1.txt
.\.venv-unidad1\Scripts\python.exe -m ipykernel install --user --name geoau-unidad1 --display-name "GeoAu Unidad 1 (Python 3.13)"
.\.venv-unidad1\Scripts\python.exe scripts/ejecutar_unidad1.py
```

El runner guarda el cuaderno con sus salidas. Reutiliza una ejecución completa si configuración y hashes coinciden. Para volver a entrenar: `scripts/ejecutar_unidad1.py --nuevo`. El creador `scripts/crear_notebook_unidad1.py` solo crea un cuaderno ausente. Un fallo guarda una copia `.failed.ipynb` y mantiene el cuaderno anterior. No ejecutar dos runners sobre el mismo cuaderno a la vez.

`requirements-unidad1.lock.txt` recoge las versiones exactas del entorno comprobado. Para reproducirlas, usa ese archivo en lugar de `requirements-unidad1.txt` al instalar. El cuaderno se abre con el kernel **GeoAu Unidad 1 (Python 3.13)**.

## Artefactos y verificación

Las ejecuciones quedan en `reports/unidad1/<fecha_UTC>/` (directorio de informes ignorado por Git): configuración, esquema de variables, versiones, entradas SHA-256, métricas y resumen de validación, decisión, preprocesadores, baselines `.joblib`, redes `.keras`, historiales por época y scores por celda de validación. `current_run.json` apunta únicamente a una ejecución completada. `outputs_manifest.json` permite detectar cambios en los productos.

```powershell
.\.venv-unidad1\Scripts\python.exe -m unittest discover -s tests -p test_neural_u1.py -v
.\.venv-unidad1\Scripts\python.exe scripts/validar_unidad1.py
```

Las pruebas comprueban gradientes, equivalencia del forward con Keras, ausencia de aprendizaje de estadísticas de validación, categorías desconocidas, rechazo de test/reserva y reproducción de scores tras guardar/cargar. El validador verifica cada ajuste real, sus métricas, preprocesamiento, membresías y modelos.

## Resultado de la ejecución local del 20 de septiembre de 2026

Ejecución `20260920T112741_562792Z`: cuaderno completo con salidas y 21 ajustes (7 modelos × 3 folds internos). La media asigna el mismo peso a cada fold.

| Modelo | Recuperación al 5 % del área | AP P/U | ROC-AUC P/U |
|---|---:|---:|---:|
| Random Forest | 0.4717 | 0.1912 | 0.8917 |
| MLP regularizada `[32,16]` | 0.4356 | 0.0941 | 0.8670 |
| MLP profunda `[64,32,16]` | 0.3956 | 0.0810 | 0.8451 |
| MLP superficial `[32]` | 0.3863 | 0.0817 | 0.8573 |
| MLP del TXT `[32,16]` | 0.3831 | 0.0704 | 0.8366 |
| Regresión logística | 0.3119 | 0.0590 | 0.8220 |
| Perceptrón | 0.2643 | 0.0512 | 0.8102 |

La MLP regularizada es la mejor red de este ensayo: mejora 12.37 puntos porcentuales frente a logística en recuperación, pero queda 3.61 puntos por debajo de RF. Algunas redes superan a RF en el segundo fold; ese comportamiento no se mantiene en los otros dos. **No hay evidencia aquí para sustituir RF por una red.** Las curvas del primer fold muestran descenso de loss train mientras empeora validation, especialmente en la red profunda; EarlyStopping conserva una época anterior. Estas observaciones son diagnósticas y no evalúan descubrimiento de oro ni rendimiento en test.
