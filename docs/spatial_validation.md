# Diseño de validación espacial y experimento incremental

## 1. Principio

El split aleatorio no es la estrategia principal. Puntos próximos comparten geología, campañas, distrito, fuentes bibliográficas y a veces una misma explotación; repartirlos al azar inflaría la generalización. La unidad de separación será un bloque o grupo espacial mayor que el alcance de autocorrelación relevante y nunca menor que la incertidumbre del label.

## 2. Dominio, máscara y resolución

Antes de generar folds:

1. Fijar el territorio de predicción y excluir mar/celdas sin X esencial mediante una máscara versionada.
2. Elegir malla y CRS métrico nacional después de auditar resoluciones y escalas. Mantener CRS84 solo para intercambio de puntos.
3. Colapsar o agrupar para splitting las ocurrencias pertenecientes al mismo depósito/complejo y los duplicados probables. Se pueden conservar como observaciones, pero siempre en el mismo fold.
4. Estimar correlogramas/variogramas o curvas de rendimiento frente a distancia, usando únicamente datos de desarrollo, para proponer tamaños de bloque. Evaluar una parrilla predefinida de escalas plausibles.

## 3. Folds espaciales

Diseño recomendado:

- **Outer CV:** proponer 5 folds de bloques espaciales contiguos y balanceados en positivos, condicionado a que el endpoint tenga soporte. Se congelará una partición primaria antes de modelar. Traslaciones, orientaciones y tamaños adicionales son sensibilidades, no réplicas independientes para inflar `n`. Alternativa cuando la transferencia regional sea la pregunta: leave-one-geological-domain/region-out como prueba de estrés, no sustituto silencioso.
- **Buffer de exclusión:** retirar del entrenamiento puntos/celdas dentro de una distancia predefinida del test para reducir fuga de vecindad. La distancia se decide por autocorrelación y precisión, no por maximizar métricas.
- **Inner CV:** bloques espaciales dentro del entrenamiento outer para imputación, PCA/MNF, selección de variables, tuning, bandwidth de RomanSignal, calibración y umbrales.
- Guardar para cada celda/ocurrencia `fold_id`, bloque, repetición, semilla y grupo depósito/complejo.

Modelos A y B compartirán filas, outer/inner folds, pesos, backgrounds y seeds. Tendrán el mismo espacio y presupuesto de búsqueda, pero podrán elegir hiperparámetros distintos dentro de ese espacio. El outer test no participa en ninguna decisión. Un diagnóstico OOB de RF no sustituye esta separación porque las observaciones OOB pueden seguir siendo vecinas.

Si una commodity rara no permite cinco folds con positivos, reducir complejidad/objetivo, reportar incertidumbre o usar una evaluación regional agregada; no forzar folds vacíos ni rellenar mediante duplicación.

## 4. Background y pseudo-ausencias

El background representa disponibilidad/contraste, no ausencia geológica.

### Regla primaria

- Antes de crear splits, congelar una `eligible_background_mask` que use la versión fijada de Y y buffers de incertidumbre predeclarados alrededor de todos los positivos; no modificarla después de observar resultados.
- Muestrear background de entrenamiento solo dentro de la máscara común y de bloques training. Mantener un background outer de evaluación fijo y pareado para A/B.
- Estratificar por dominios geológicos y, cuando proceda, por esfuerzo/cobertura de observación para evitar que el clasificador aprenda “muestreado frente a no muestreado”.
- Mantener un conjunto background fijo por repetición/semilla para comparar modelos A/B en pares.
- Probar varias razones background:positivo predefinidas; ponderar para que la métrica no dependa arbitrariamente del número muestreado.

### Análisis de sensibilidad

1. Background uniforme dentro de cobertura.
2. Target-group background o background sesgado por esfuerzo de inventario.
3. Background geológicamente emparejado.
4. PU learning con supuestos explícitos de selección; bagging-PU con RF puede ser sensibilidad.
5. Buffers alternativos preespecificados, incluida una sensibilidad sin buffer.

La estabilidad entre estrategias es un resultado, no una molestia a ocultar. Bajo selección SAR no se presentará calibración absoluta ni prevalencia estimada sin supuestos adicionales.

## 5. Métricas

- **PR-AUC:** métrica primaria para clases raras, junto con la prevalencia/baseline de cada fold.
- **ROC-AUC:** secundaria; puede parecer alta con fuerte desbalance.
- **Recall, precision y F1:** en umbrales elegidos exclusivamente dentro del training/inner CV, por ejemplo máximo F1 o recall mínimo operativo. No ajustar el umbral sobre el test.
- Reportar curvas y métricas por fold/repetición, media, mediana, dispersión e intervalos por bootstrap de bloques/repeticiones.
- Complementos recomendados: calibración/Brier cuando se interpreten scores probabilísticos, precision@área o success-rate curve para uso prospectivo, y métricas por región/commodity/calidad.

El outer test se evaluará sobre todas las celdas elegibles o sobre una muestra probabilística congelada con pesos inversos. Su composición no dependerá de la razón background:positivo usada para entrenar. Cada PR-AUC incluirá la prevalencia de referencia del conjunto de evaluación.

En presencia-background, AUC y PR-AUC miden discriminación frente al background elegido, no sensibilidad/especificidad frente a ausencias verdaderas. Esta limitación debe acompañar cada resultado.

### Interpretabilidad retenida

La interpretación confirmatoria se hará después de congelar predicciones y métricas:

- **Permutation importance:** calcular la caída de PR-AUC al permutar grupos completos —litología/edad, estructuras, geoquímica, magnetometría, gravimetría, radiometría, terreno, teledetección y RomanSignal— exclusivamente en outer-test. Se reasignarán bloques completos dentro de estratos geológicos/cobertura intercambiables para no destruir artificialmente toda la estructura local.
- Reportar distribución y ranking por fold, importancia agrupada para predictores correlacionados y, cuando sea viable, ablación `drop-group` con reentrenamiento. La importancia Gini/MDI queda como diagnóstico de entrenamiento.
- **SHAP posterior:** TreeSHAP solo después de cerrar la evaluación confirmatoria. Cada celda se explica con el modelo outer que no la entrenó; el background del explainer procede de outer-training y se balancea espacialmente. Registrar `model_output`, `feature_perturbation`, agrupación one-hot y estabilidad. Una interacción `RomanSignal x geología` será exploratoria, no causal.
- No seleccionar variables mediante estas explicaciones y conservar después las mismas métricas outer como si fueran independientes.

## 6. Experimento predictivo incremental predefinido

### Hipótesis

`H1`: una señal romana generada sin acceso al test aporta información predictiva incremental para labels modernos después de controlar X geológica.

### Modelos

- **Modelo A:** `X_geología + X_geoquímica + X_geofísica + X_DEM + covariables de cobertura admisibles -> Y_moderna`.
- **Modelo B:** las mismas X y capacidad de modelo + una familia pequeña preespecificada de señal romana fold-aware -> el mismo `Y_moderna`.

### Controles de justicia

- Mismos outer/inner folds, seeds, filas, background, pesos, preprocesamiento permitido, algoritmo, tuning budget y criterio de selección.
- Estimando confirmatorio de transferencia: la señal romana se recalcula en cada fold solo con minas de outer-training y fuera del buffer. Si se aprende `Y_roman ~ X`, el score usado por B debe ser doblemente cross-fitted. El estimando operativo con OxREP completo congelado será solo sensibilidad y exige lineage independiente de Y moderna.
- Comparación pareada `delta_PR-AUC`, `delta_ROC-AUC`, `delta_recall`, `delta_precision`, `delta_F1` y `delta_precision@area`.
- Repetir por endpoint moderno y commodity con tamaño suficiente; controlar multiplicidad o declarar análisis exploratorios.

### Prueba estadística predefinida de valor incremental

1. Elegir antes del tuning un endpoint confirmatorio, `delta_PR-AUC = PR-AUC_B - PR-AUC_A` como contraste primario y un umbral mínimo de relevancia práctica. Commodities adicionales serán secundarios y usarán corrección de multiplicidad o etiqueta exploratoria.
2. Concatenar las predicciones outer out-of-fold de la partición espacial primaria y calcular la diferencia sobre exactamente las mismas celdas. Las rotaciones de bloques se usan para sensibilidad, no como observaciones independientes.
3. Obtener IC95 mediante bootstrap de bloques espaciales, recomputando ambas métricas sobre cada remuestreo pareado. Reportar efecto, intervalo y distribución por bloque, no solo un valor p.
4. Construir un nulo espacial permutando o desplazando RomanSignal por bloques dentro de estratos intercambiables y reentrenando B con el mismo pipeline. Valor p empírico: `(1 + nulos >= observado) / (M + 1)`, con `M` y seeds predeclarados.
5. Si la intercambiabilidad espacial no es defendible, presentar placebos como falsificación descriptiva, no como p exacto. No usar t-test, Wilcoxon o DeLong sobre celdas autocorreladas ni folds solapados.
6. Exigir también una mejora práctica en la curva de captura-área o `precision@top-area`, adaptando el success-rate map del antecedente sin copiar su umbral 0,5.

### Ablaciones y falsificación

1. B con señal romana real.
2. Señal romana permutada **por bloques** preservando autocorrelación aproximada.
3. Señal de sitios romanos/mineros desplazada espacialmente a distancias predefinidas como placebo, si es científicamente defendible.
4. B sin covariables de accesibilidad/preservación frente a B con ellas, para evaluar confusión.
5. Excluir registros OxREP de peor precisión/incertidumbre y repetir.
6. Leave-region/domain-out para comprobar si el incremento solo memoriza distritos conocidos.

## 7. Criterio de éxito

La señal romana aporta valor solo si el incremento de B sobre A:

- es positivo y estable en outer folds/repeticiones, especialmente en PR-AUC;
- conserva utilidad bajo backgrounds y tamaños de bloque alternativos;
- no desaparece en ablaciones de registros dudosos;
- supera placebos y no depende únicamente de una región dominante;
- tiene magnitud práctica en el área priorizada, no solo significación numérica.

Un resultado nulo o heterogéneo también es informativo: puede indicar que X ya contiene la señal, que la minería romana responde a accesibilidad/tecnología más que a presencia mineral, que el label moderno no es comparable o que la calidad/cobertura no permite detectar el incremento.

## 8. Evaluación final e independencia

El nested outer spatial CV es validación interna. Antes de cualquier selección se reservará, si los datos lo permiten, un dominio geológico completo, una cohorte temporal futura de BDMIN, un levantamiento de campo ciego u otro inventario con observaciones *upstream* realmente distintas. La evaluación independiente se abrirá una sola vez tras congelar endpoint, features, algoritmo y umbral.

Dos portales que redistribuyen la misma ocurrencia no constituyen validación independiente. Cada label registrará `upstream_dataset_id`, organismo/campaña original, fechas de observación e ingestión, relaciones de derivación e `independent_of_target`. MIN4EU o un mapa metalogenético derivado de BDMIN será QA, no test externo. Si el conjunto aún no existe, se declarará **validación independiente pendiente**; leave-domain-out es una prueba de estrés, no su sustituto.

## 9. Registro reproducible mínimo

Para cada ejecución futura guardar: hashes/versiones de X e Y; reglas de inclusión; malla/CRS; fold GeoPackage/GeoJSON; buffers; seeds; background; transformaciones; hiperparámetros; predicciones out-of-fold; métricas por fold; curvas; entorno; y manifest de artefactos. Las decisiones se fijan antes de consultar los scores del test.
