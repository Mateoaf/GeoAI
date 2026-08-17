# 📊 Benchmark Científico Oficial de Modelos GeoAI v2

## 1. Resumen Metodológico
* **Estrategia de Validación:** Spatial Block Cross-Validation (5 folds espaciales basados en coordenadas métricas EPSG:25830).
* **Calibración Probabilística:** Out-of-fold Isotonic Regression para mapeo de Prospectivity / Favorability Score (0.0 a 1.0).
* **Datos de Entrada:** 100% observables y derivados de cartografía oficial (IGME 1M + Copernicus DEM).
* **Exclusión de Coordenadas:** Coord_X y Coord_Y han sido estrictamente excluidas del vector predictor oficial.

## 2. Rendimiento Global por Commodity Mineral

| Commodity | Positivos | Spatial ROC-AUC | Spatial PR-AUC | Brier Score | F1 Score | Precision@Top10% | Capture Rate (Top 10%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Explotación Minera General (General_Mining)** | 993 | 0.7131 | 0.6912 | 0.2006 | 0.7695 | 0.7374 | 13.3% |
| **Oro (Au_Oro)** | 637 | 0.5035 | 0.3569 | 0.2286 | 0.0000 | 0.0615 | 1.7% |
| **Cobre (Cu_Cobre)** | 186 | 0.5179 | 0.1148 | 0.0922 | 0.0212 | 0.1564 | 15.0% |
| **Plata (Ag_Plata)** | 179 | 0.5037 | 0.1008 | 0.0898 | 0.0000 | 0.0279 | 2.8% |
| **Plomo (Pb_Plomo)** | 170 | 0.5550 | 0.1060 | 0.0854 | 0.0000 | 0.1006 | 10.6% |

## 3. Estudio de Ablación de Coordenadas

| Modelo | Predictors | Spatial ROC-AUC | Spatial PR-AUC | Brier Score | Interpretación |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Modelo A (Oficial)** | 7 Numéricos + 3 Categóricos IGME | **0.6872** | **0.6649** | 0.2394 | Modelo generalizable sin memorización espacial |
| **Modelo B (Ablation)** | Numéricos + Categóricos + Coord_X/Y | 0.7387 | 0.7390 | 0.3118 | Memorización espacial de latitud/longitud |

## 4. Resultados Leave-One-District-Out (LODO)

| Distrito / Provincia Metalogénica | Estado Muestral | N Train Pos | N Test Pos | N Test Fondo | ROC-AUC | PR-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Noroeste Galaico-Leonés (Au orogénico / Las Médulas, Salave, Teleno)** | `ROBUST` | 380 | 613 | 77 | 0.5553 | 0.8864 |
| **Faja Pirítica Ibérica (Cu-VMS / Riotinto, Tharsis, Aznalcóllar)** | `ROBUST` | 922 | 71 | 31 | 0.6742 | 0.7620 |
| **Sierra Morena / Linares-La Carolina (Pb-Ag filoniano / Los Pedroches)** | `ROBUST` | 860 | 133 | 26 | 0.4232 | 0.8231 |
| **Sureste Bético / Mazarrón-Rodalquilar (Au-Ag-Pb epitermal neógeno)** | `ROBUST` | 976 | 17 | 32 | 0.6535 | 0.5868 |
| **Zona Centroibérica / Sistema Central (Filones de Cuarzo-Sulfuros)** | `EXPLORATORY_LOW_N` | 979 | 14 | 110 | 0.5987 | 0.2035 |
