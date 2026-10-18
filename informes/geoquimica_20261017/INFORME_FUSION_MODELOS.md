# GeoAI · Fusión heterogénea de modelos

Se combinan logística L2, Random Forest, LightGBM y Bagging PU sobre las mismas 64 entradas, incluidas las ocho clases geoquímicas. Se evalúan la media uniforme, con peso fijo 0,25 para cada componente, y una fusión que aprende pesos en CV interna. Bagging PU agrega miembros de una familia; estas fusiones reúnen algoritmos con estructuras diferentes. La correlación entre sus scores fuera de pliegue permite inspeccionar su complementariedad. Ese diagnóstico es descriptivo y no elige pesos sobre el test.

## Aprendizaje de pesos sin utilizar el test externo

El score es **S(x)=Σ w_j s_j(x)**, con pesos no negativos que suman uno. La media uniforme fija w_j=0,25 sin usar etiquetas para ajustarlos. En la fusión con pesos aprendidos, cada entrenamiento externo genera predicciones fuera de pliegue de los cuatro componentes mediante tres pliegues internos. La separación interna reproduce la estrategia aleatoria, por bloques o con buffer de 15 km. Imputación, escalado y one-hot se ajustan dentro de cada entrenamiento interno.

Se evalúa una rejilla simplex de paso 0.1 y la media de pesos iguales. Se selecciona Average Precision interna; los empates favorecen pesos menos concentrados. La rejilla permite peso cero y seleccionar un único componente cuando la mezcla no añade señal interna. Los cuatro pipelines se reajustan después con todo el entrenamiento externo y los pesos quedan fijados antes de predecir el test. El procedimiento completo, incluida esta selección, se evalúa en los cinco pliegues externos.

Se combinan scores P/U sin corrección Elkan–Noto. La optimización de ranking absorbe diferencias de escala dentro del entrenamiento, sin convertir las salidas en probabilidades físicas calibradas. El c del diagnóstico pertenece a su modelo específico.

## Resultados en CV espacial con buffer

| model | roc_auc | average_precision | positive_cell_recovery_at_05 | positive_cell_recovery_at_10 |
| --- | --- | --- | --- | --- |
| logistic | 0.8680 | 0.6648 | 0.1653 | 0.3084 |
| random_forest | 0.8497 | 0.6803 | 0.1749 | 0.3307 |
| lightgbm | 0.8734 | 0.6963 | 0.1685 | 0.3307 |
| bagging_pu | 0.8866 | 0.7119 | 0.1733 | 0.3307 |
| heterogeneous_fusion | 0.8701 | 0.6915 | 0.1717 | 0.3211 |
| heterogeneous_uniform | 0.8827 | 0.7141 | 0.1701 | 0.3323 |

La **media uniforme** obtiene **AP 0.714075** y **ROC-AUC 0.882745**. La mayor AP entre los componentes es 0.711931 (bagging_pu); la mayor AUC es 0.886605 (bagging_pu). La diferencia de AP es +0.002144 y la de AUC frente a la mayor referencia es -0.003860. Estas diferencias describen esta evaluación interna; no prueban significación estadística ni mejora universal. La tabla conserva también los resultados de pesos aprendidos para no confundir selección interna con mejora garantizada.

El benchmark de tres estrategias incorpora la fusión y conserva ROC-AUC, PR-AUC/AP, Brier y recuperación exacta al 5 % y 10 %. Las predicciones y particiones externas e internas se exportan para comprobar el procedimiento.

## Recuperación de depósitos por territorios reservados

| model | n_deposits | captured_deposits_at_01 | deposit_recovery_at_01 | captured_deposits_at_05 | deposit_recovery_at_05 | captured_deposits_at_10 | deposit_recovery_at_10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| logistic | 45 | 2 | 0.0444 | 4 | 0.0889 | 8 | 0.1778 |
| lightgbm | 45 | 3 | 0.0667 | 5 | 0.1111 | 9 | 0.2000 |
| bagging_pu | 45 | 1 | 0.0222 | 5 | 0.1111 | 9 | 0.2000 |
| heterogeneous_fusion | 45 | 2 | 0.0444 | 4 | 0.0889 | 7 | 0.1556 |
| heterogeneous_uniform | 45 | 2 | 0.0444 | 6 | 0.1333 | 6 | 0.1333 |

La **media uniforme** recupera **6 de 45 depósitos al 5 %** de celdas y **6 al 10 %**. Sus pesos permanecen constantes en todos los grupos. En la fusión aprendida se eligen únicamente con los datos de entrenamiento, mediante CV interna con buffer. Las muestras de entrenamiento y los territorios son los mismos que en los demás procedimientos; se excluyen los bloques reservados y un buffer de 15 km. Se cuenta una vez cada depósito capturado.

![Resultados de la fusión](figuras/fusion_resultados.png)

## Pesos y complementariedad

| strategy | component | mean_weight | std_weight |
| --- | --- | --- | --- |
| buffered | bagging_pu | 0.3200 | 0.2864 |
| buffered | lightgbm | 0.1600 | 0.2302 |
| buffered | logistic | 0.3000 | 0.1414 |
| buffered | random_forest | 0.2200 | 0.3347 |
| random | bagging_pu | 0.0000 | 0.0000 |
| random | lightgbm | 0.6200 | 0.1483 |
| random | logistic | 0.1800 | 0.0837 |
| random | random_forest | 0.2000 | 0.1414 |
| spatial | bagging_pu | 0.3600 | 0.3507 |
| spatial | lightgbm | 0.0800 | 0.1789 |
| spatial | logistic | 0.3400 | 0.1517 |
| spatial | random_forest | 0.2200 | 0.2775 |

Los pesos aprendidos cambian por entrenamiento y no son importancias de las variables geológicas. Para su modelo nacional se seleccionan de nuevo usando únicamente la muestra de ajuste y tres pliegues internos espaciales. Sus valores son:

| logistic | random_forest | lightgbm | bagging_pu |
| --- | --- | --- | --- |
| 0.2000 | 0.1000 | 0.7000 | 0.0000 |

![Complementariedad](figuras/fusion_complementariedad.png)

## Modelo y cartografía de la fusión

models/fusion_uniform/model.joblib contiene los cuatro pipelines y pesos iguales; models/fusion/model.joblib conserva los pesos aprendidos. La muestra nacional utiliza 664 P y 1992 U; el ajuste posterior a la evaluación no constituye un test independiente. maps/GeoAI_fusion_uniform_national.parquet y los GeoTIFF asociados exportan la media uniforme, scores individuales, desacuerdo, novedad y categorías. También se conservan los productos de la fusión aprendida.

El desacuerdo es **raíz de Σ w_j(s_j−S)²** entre familias. Tiene un significado diferente de la variación por remuestreo U del ensamble de ocho LightGBM: ambos son diagnósticos de variación, sin representar toda la incertidumbre ni un intervalo de confianza. Las categorías de la fusión usan percentiles relativos de score, desacuerdo y novedad.

![Cartografía de la fusión](figuras/fusion_mapa.png)

## Reproducción y alcance

Ejecutar scripts/ejecutar_geoquimica.py --stage fusion y después --stage report. La ejecución all incluye la fusión. fusion_weights.csv, fusion_candidate_metrics.csv, fusion_inner_predictions.parquet y partitions/fusion_inner_memberships.parquet registran la selección. fusion_cv_component_predictions.parquet y fusion_rotation_component_predictions.parquet permiten reconstruir la media ponderada y la recuperación. Los resultados proceden del inventario conocido; una campaña externa permitiría contrastar su utilidad prospectiva.

Referencia técnica: [agregación de clasificadores por media ponderada, scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.VotingClassifier.html).
