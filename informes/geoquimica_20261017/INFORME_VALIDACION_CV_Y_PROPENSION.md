# GeoAI · Validación cruzada y factor de propensión aparente

El experimento emplea **64 predictores**, incluidas las clases geoquímicas As, Sb, Bi, Hg, Cu, Pb, Zn y W. Las tres estrategias comparten 629 P y 1887 U, excluyendo los bloques de los distritos de reserva. Se ajustan cinco pliegues por estrategia.

## Factor c estimado sobre el catálogo

**c = 0.431122; escala de referencia 1/c = 2.3195×.**

El diagnóstico parte de las 664 celdas P del catálogo elegible y 1992 U. Reserva espacialmente 530 celdas, de las que 154 son P, para estimar c. Ajusta con 1778 celdas, excluyendo la reserva y un buffer de 15 km. Las transformaciones se aprenden exclusivamente con el ajuste.

En cada miembro, **c_b = media de g_b(x) sobre positivos de la reserva interna**. Se calcula **q_b(x) = clip(g_b(x)/c_b, 0, 1)** y el ensamble promedia q_b. La c informada es la media de los cinco c_b. Su inversa resume una escala de referencia: con factores distintos y recorte no equivale a dividir la media del ensamble por una única constante.

El 43.11 % expresa el score medio aparente de los positivos reservados bajo este diseño P/U. Identificarlo con probabilidad de registro exige selección aleatoria de positivos (SCAR), un clasificador probabilístico adecuado y un muestreo compatible. Aquí U se muestrea y los positivos tienen pesos de confianza: el valor no acredita qué porcentaje del oro o de los depósitos reales está inventariado.

El factor del catálogo pertenece al ensamble diagnóstico guardado en models/catalog_elkan_noto.joblib. La cartografía conserva sus ocho pipelines de scores relativos; no se les aplica automáticamente el factor de otro ajuste. Los factores del benchmark se estiman dentro del entrenamiento de cada pliegue, sin consultar su test externo.

## Modelos y tres estrategias de validación

| Estrategia CV | Modelo | ROC-AUC | PR-AUC | Brier Loss | Recovery@5% | Recovery@10% |
| --- | --- | --- | --- | --- | --- | --- |
| Random CV | Regresión Logística L2 | 0.9299 | 0.8044 | 0.0927 | 18.4400 | 35.2900 |
| Random CV | Random Forest | 0.9352 | 0.8250 | 0.0977 | 18.6000 | 37.3600 |
| Random CV | LightGBM Regularizado | 0.9409 | 0.8356 | 0.0846 | 18.2800 | 36.7200 |
| Random CV | Bagging PU + Elkan–Noto (c=0.601) | 0.9312 | 0.8040 | 0.1030 | 17.3300 | 36.0900 |
| Random CV | Fusión heterogénea (pesos internos) | 0.9443 | 0.8420 | 0.0855 | 18.7600 | 37.2000 |
| Random CV | Fusión heterogénea (media uniforme) | 0.9434 | 0.8360 | 0.0859 | 18.6000 | 37.3600 |
| Spatial Block CV (0 km) | Regresión Logística L2 | 0.8905 | 0.7111 | 0.1186 | 17.0100 | 33.2300 |
| Spatial Block CV (0 km) | Random Forest | 0.8795 | 0.7207 | 0.1262 | 17.3300 | 33.7000 |
| Spatial Block CV (0 km) | LightGBM Regularizado | 0.8985 | 0.7341 | 0.1181 | 17.3300 | 33.7000 |
| Spatial Block CV (0 km) | Bagging PU + Elkan–Noto (c=0.529) | 0.8841 | 0.6859 | 0.1329 | 16.3800 | 32.2700 |
| Spatial Block CV (0 km) | Fusión heterogénea (pesos internos) | 0.8912 | 0.7275 | 0.1189 | 17.4900 | 32.9100 |
| Spatial Block CV (0 km) | Fusión heterogénea (media uniforme) | 0.9040 | 0.7517 | 0.1128 | 17.6500 | 34.3400 |
| Buffered Spatial CV (15 km) | Regresión Logística L2 | 0.8680 | 0.6648 | 0.1332 | 16.5300 | 30.8400 |
| Buffered Spatial CV (15 km) | Random Forest | 0.8497 | 0.6803 | 0.1382 | 17.4900 | 33.0700 |
| Buffered Spatial CV (15 km) | LightGBM Regularizado | 0.8734 | 0.6963 | 0.1322 | 16.8500 | 33.0700 |
| Buffered Spatial CV (15 km) | Bagging PU + Elkan–Noto (c=0.465) | 0.8663 | 0.6565 | 0.1541 | 15.9000 | 33.7000 |
| Buffered Spatial CV (15 km) | Fusión heterogénea (pesos internos) | 0.8701 | 0.6915 | 0.1309 | 17.1700 | 32.1100 |
| Buffered Spatial CV (15 km) | Fusión heterogénea (media uniforme) | 0.8827 | 0.7141 | 0.1254 | 17.0100 | 33.2300 |

Random CV utiliza cinco pliegues estratificados. Spatial Block CV separa bloques de 50 km sin buffer. Buffered Spatial CV utiliza los mismos pliegues espaciales y retira muestras de entrenamiento a menos de 15 km de validación. Las tres estrategias emplean las mismas 64 variables.

Logística L2, Random Forest y LightGBM ajustan su Pipeline con todo el entrenamiento externo. Bagging PU + Elkan–Noto combina cinco LightGBM y reserva un pliegue interno para c con el mismo tipo de separación aleatoria o espacial de la estrategia. El test externo no participa en el ajuste ni en c; la reserva interna reduce la muestra efectiva del procedimiento PU.

## Interpretación de las métricas

- **ROC-AUC:** ordenación de etiquetas P/U sobre predicciones fuera de pliegue.
- **PR-AUC:** conserva la definición de la tabla solicitada, Average Precision calculada con average_precision_score. El área trapezoidal se exporta separadamente como pr_auc_trapezoid; son cálculos diferentes.
- **Brier Loss:** error cuadrático medio frente a etiquetas P/U. No evalúa calibración de mineralización real: U no es ausencia confirmada y la muestra tiene un ratio P/U definido por el experimento.
- **Recovery@5% y @10%:** porcentaje de celdas P recuperadas en un cupo exacto de ceil(porcentaje × celdas de la muestra). Los empates se resuelven por cell_id sin utilizar etiquetas. No mide depósitos ni superficie nacional.

El recorte en uno puede crear empates. Se exportan scores brutos y corregidos para inspeccionar el cálculo, manteniendo el presupuesto de selección.

## Factores c por estrategia

| strategy | c_mean | c_std | fraction_score_one |
| --- | --- | --- | --- |
| Random CV | 0.6009 | 0.0106 | 0.1399 |
| Spatial Block CV (0 km) | 0.5294 | 0.0493 | 0.1037 |
| Buffered Spatial CV (15 km) | 0.4653 | 0.0729 | 0.1411 |

c_mean y c_std resumen los 25 factores de cinco miembros en cinco pliegues. fraction_score_one es la fracción de scores finales OOF iguales a uno. Ningún c utiliza los positivos del test externo.

![Resultados de validación](figuras/validacion_tres_estrategias.png)

## Reproducción

benchmark_cv_tabla.csv es la tabla de presentación; benchmark_cv_summary.csv conserva precisión completa y el área PR trapezoidal. benchmark_cv_folds.csv y benchmark_cv_oof.parquet permiten recalcular métricas. Se exportan las pertenencias externas e internas y las predicciones de los positivos usados para c. propensity_catalog_summary.json registra factores, tamaños y alcance; propensity_catalog_score_examples.csv muestra el reescalado. Ejecutar scripts/ejecutar_geoquimica.py --stage diagnostics y después --stage report.

Referencia: [Elkan y Noto (2008), sección 2](https://cseweb.ucsd.edu/~elkan/posonly.pdf).
