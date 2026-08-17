# 📊 Benchmark Oficial GeoAI v2: Validación Espacial y Evaluación Científica

Validación espacial estricta sin target leakage, sin variables sintéticas y evaluada out-of-fold.

## 1. Resumen de Métricas (Spatial Block Cross-Validation - 5 Folds)

| Commodity | Positivos | Spatial ROC-AUC | Spatial PR-AUC | Brier Score (OOF) | F1-Score | Archivo Serializado |
|---|---|---|---|---|---|---|
| **Oro (Au)** | 637 | 0.7936 ± 0.1681 | 0.4253 ± 0.3309 | 0.2465 ± 0.2953 | 0.1947 | `models/v2/model_geoai_v2_Au_Oro.joblib` |
| **Cobre (Cu)** | 186 | 0.6602 ± 0.1315 | 0.1747 ± 0.1890 | 0.1114 ± 0.1368 | 0.0250 | `models/v2/model_geoai_v2_Cu_Cobre.joblib` |
| **Plata (Ag)** | 179 | 0.5526 ± 0.2217 | 0.1620 ± 0.1688 | 0.1055 ± 0.1240 | 0.0414 | `models/v2/model_geoai_v2_Ag_Plata.joblib` |
| **Plomo (Pb)** | 170 | 0.6064 ± 0.2051 | 0.2025 ± 0.1663 | 0.1002 ± 0.1099 | 0.0400 | `models/v2/model_geoai_v2_Pb_Plomo.joblib` |


## 2. Evaluación Leave-One-District-Out (LODO)

Capacidad de generalización en distritos mineros completamente ciegos:

| Commodity | Distrito Excluido | Positivos Val | ROC-AUC | PR-AUC | Brier Score |
|---|---|---|---|---|---|
| Oro (Au) | Faja_Piritica_Iberica | 4 | 0.5269 | 0.0449 | 0.2232 |
| Oro (Au) | Centro_Iberico_Meseta | 40 | 0.6933 | 0.1464 | 0.1269 |
| Oro (Au) | Noroeste_Aurifero | 590 | 0.5482 | 0.9114 | 0.7727 |
| Oro (Au) | Sierra_Morena_Linares | 1 | 0.9492 | 0.0769 | 0.1797 |
| Oro (Au) | Sureste_Betico | 2 | 0.9802 | 0.6429 | 0.0294 |
| Cobre (Cu) | Faja_Piritica_Iberica | 68 | 0.9162 | 0.9399 | 0.4946 |
| Cobre (Cu) | Centro_Iberico_Meseta | 18 | 0.5921 | 0.0696 | 0.0513 |
| Cobre (Cu) | Noroeste_Aurifero | 6 | 0.3442 | 0.0076 | 0.08 |
| Cobre (Cu) | Sierra_Morena_Linares | 88 | 0.7196 | 0.559 | 0.3011 |
| Cobre (Cu) | Sureste_Betico | 6 | 0.9221 | 0.2575 | 0.0418 |
| Plata (Ag) | Faja_Piritica_Iberica | 12 | 0.6115 | 0.1638 | 0.0977 |
| Plata (Ag) | Centro_Iberico_Meseta | 26 | 0.6924 | 0.2062 | 0.0476 |
| Plata (Ag) | Noroeste_Aurifero | 5 | 0.2682 | 0.0061 | 0.0517 |
| Plata (Ag) | Sierra_Morena_Linares | 125 | 0.7205 | 0.7391 | 0.4787 |
| Plata (Ag) | Sureste_Betico | 11 | 0.784 | 0.2756 | 0.0787 |
| Plomo (Pb) | Faja_Piritica_Iberica | 5 | 0.5858 | 0.0861 | 0.0559 |
| Plomo (Pb) | Centro_Iberico_Meseta | 28 | 0.6907 | 0.1844 | 0.0536 |
| Plomo (Pb) | Noroeste_Aurifero | 5 | 0.3991 | 0.0089 | 0.0485 |
| Plomo (Pb) | Sierra_Morena_Linares | 122 | 0.7406 | 0.7571 | 0.458 |
| Plomo (Pb) | Sureste_Betico | 10 | 0.8758 | 0.436 | 0.0687 |


## 3. Coordinate Ablation Study (Con vs. Sin Coordenadas XY)

| Commodity | Configuración | Features | Spatial ROC-AUC | Spatial PR-AUC | Brier Score |
|---|---|---|---|---|---|
| Oro (Au) | Modelo A (Con Coordenadas XY) | 13 | 0.6981 ± 0.1632 | 0.2521 ± 0.3712 | 0.1666 ± 0.2824 |
| Oro (Au) | Modelo B (Sin Coordenadas - Geología Pura) | 11 | 0.7936 ± 0.1681 | 0.4253 ± 0.3309 | 0.2465 ± 0.2953 |
| Cobre (Cu) | Modelo A (Con Coordenadas XY) | 13 | 0.6863 ± 0.1566 | 0.1777 ± 0.1872 | 0.0921 ± 0.1462 |
| Cobre (Cu) | Modelo B (Sin Coordenadas - Geología Pura) | 11 | 0.6602 ± 0.1315 | 0.1747 ± 0.1890 | 0.1114 ± 0.1368 |
| Plata (Ag) | Modelo A (Con Coordenadas XY) | 13 | 0.6582 ± 0.1504 | 0.1546 ± 0.1931 | 0.0723 ± 0.0931 |
| Plata (Ag) | Modelo B (Sin Coordenadas - Geología Pura) | 11 | 0.5526 ± 0.2217 | 0.1620 ± 0.1688 | 0.1055 ± 0.1240 |
| Plomo (Pb) | Modelo A (Con Coordenadas XY) | 13 | 0.7143 ± 0.0881 | 0.1820 ± 0.2010 | 0.0734 ± 0.0882 |
| Plomo (Pb) | Modelo B (Sin Coordenadas - Geología Pura) | 11 | 0.6064 ± 0.2051 | 0.2025 ± 0.1663 | 0.1002 ± 0.1099 |


---
*Generado automáticamente por el Pipeline Científico GeoAI v2.*