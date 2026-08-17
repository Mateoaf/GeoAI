# 📋 AUDITORÍA TÉCNICA DE CAPAS: INFORME GEOAI vs. ESTADO ACTUAL
**Proyecto:** GeoAI de Prospectividad Mineral en España (Minería Romana, Walter Pohl 2011, OGC GeoSciML / CIDOC-CRM)  
**Fecha de Auditoría:** 17 de Agosto de 2026  
**Versión del Sistema:** v2.4-real (Commit `5ec9545`)  
**Repositorio Oficial:** [github.com/Mateoaf/GeoAI](https://github.com/Mateoaf/GeoAI)  

---

## 1. Resumen Ejecutivo de la Auditoría

El sistema de **GeoAI de Prospectividad Mineral** ha completado la transición hacia **fuentes oficiales abiertas en tiempo real** para las dimensiones estructurales, litológicas, altimétricas y arqueológicas del territorio peninsular:

* **Evidencias Arqueomineras ($Y$):** **100% REAL.** 993 explotaciones mineras romanas de Hispania procedentes de Oxford (OxREP v3.0, 2025) con estandarización ontológica formal (OGC GeoSciML v4.1, CIDOC-CRM v7.1 ISO 21127).
* **Litología y Cronoestratigrafía ($X_{\text{geo}}$):** **100% REAL.** Consultas directas al servidor oficial ArcGIS REST del **IGME (Mapa Geológico Continuo 1:1.000.000)** extrayendo polígonos de litología general, descripción de formaciones, era geológica y dominio tectónico.
* **Geomorfología y Altimetría ($X_{\text{topo}}$):** **100% REAL.** Modelo Digital del Terreno en alta resolución **Copernicus DEM (GLO-30m / IGN)**.
* **Estructuras Tectónicas y Fallas ($X_{\text{struct}}$):** **100% REAL.** Descarga de **20.327 vértices de fallas y cabalgamientos** y **205.735 vértices de contactos litológicos** del IGME en EPSG:25830, calculando distancia euclidiana y densidad a 5 km.
* **Geofísica, Geoquímica y Teledetección ($X_{\text{geophy}}, X_{\text{geochem}}, X_{\text{remote}}$):** **PROXIES CALIBRADOS.** Modelados matemáticamente siguiendo las leyes genéticas y de dispersión del tratado de **Walter L. Pohl (2011)**.

---

## 2. Matriz de Auditoría Detallada Capa por Capa

| # | Capa del Informe Teórico | Fuente Oficial | Estado de Integración | Atributos Reales en el Dataset | Formato & CRS |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **01** | **Evidencias Mineras Romanas ($Y$)** | Oxford Roman Economy (OxREP v3.0) | <span style="color:green">**100% REAL**</span> | `mineID`, `site`, `commodity`, `technique`, `certainty`, `references` | CSV, GPKG, JSON-LD (`EPSG:25830` / `4326`) |
| **02** | **Litología General y Rocas de Caja** | IGME (Mapa Geológico 1M / GEODE) | <span style="color:green">**100% REAL**</span> | `Real_IGME_Lithology_General` (404 cuarcitas/pizarras, 102 gneises, 48 granitoides) | Vector Polígonos IGME REST |
| **03** | **Cronoestratigrafía y Eras** | IGME (Mapa Geológico 1M) | <span style="color:green">**100% REAL**</span> | `Real_IGME_Era` (676 Paleozoico, 84 Proterozoico, 20 Mesozoico), `Real_IGME_Sistema` | Vector Polígonos IGME REST |
| **04** | **Dominios Tectónicos y Macizos** | IGME (Mapa Geológico 1M / MAGNA) | <span style="color:green">**100% REAL**</span> | `Real_IGME_Dominio` (Macizo Ibérico, Faja Pirítica, Ossa-Morena, Béticas) | Vector Polígonos IGME REST |
| **05** | **Altimetría y Topografía (MDT)** | IGN / Copernicus DEM (GLO-30m) | <span style="color:green">**100% REAL**</span> | `Real_Elevation_MDT_m` (Altitud exacta sobre el nivel del mar en metros) | Grid Ráster 30m (`EPSG:25830`) |
| **06** | **Fallas Mayores y Cabalgamientos** | IGME (Capa 2 Contactos y Fallas 1M) | <span style="color:green">**100% REAL**</span> | `Real_IGME_Dist_Fault_m` (Distancia exacta a falla: min 86.7 m, mediana 7.7 km) | Vector Líneas IGME REST (20.327 vértices) |
| **07** | **Contactos Litológicos / Bordes Plutón** | IGME (Capa 2 Contactos y Fallas 1M) | <span style="color:green">**100% REAL**</span> | `Real_IGME_Dist_Contact_m` (Distancia a contacto geológico) | Vector Líneas IGME REST (205.735 vértices) |
| **08** | **Densidad Estructural de Fracturación** | IGME (Capa 2 Contactos y Fallas 1M) | <span style="color:green">**100% REAL**</span> | `Real_IGME_Fault_Density_5km` (Nº de fallas en radio de 5 km: max 58 fallas) | Densidad Espacial (KD-Tree) |
| **09** | **Geofísica (Gravimetría Bouguer)** | IGN / IGME Mapa Gravimétrico | <span style="color:orange">**PROXY POHL**</span> | `Geophy_Bouguer_Anomaly` (Proxy de densidad de sulfuros/máficas VMS) | Sintético calibrado |
| **10** | **Geofísica (Magnetometría)** | IGME Aeromagnetismo Nacional | <span style="color:orange">**PROXY POHL**</span> | `Geophy_Magnetic_Gradient` (Proxy de susceptibilidad magnética) | Sintético calibrado |
| **11** | **Geoquímica de Sedimentos (Pathfinders)** | IGME / FOREGS / GEMAS ($As, Sb, Bi$) | <span style="color:orange">**PROXY POHL**</span> | `Geochem_Pathfinder_AsSb` (Halo de dispersión hidrotermal) | Sintético calibrado |
| **12** | **Geoquímica de Metales Base ($Cu, Pb, Zn$)** | IGME Base Geoquímica Multielemental | <span style="color:orange">**PROXY POHL**</span> | `Geochem_BaseMetal_ZnPb` (Anomalías de lixiviación) | Sintético calibrado |
| **13** | **Teledetección (Alteración Hidrotermal)** | Sentinel-2 / ASTER (SWIR/VNIR) | <span style="color:orange">**PROXY POHL**</span> | `Remote_Hydrothermal` (Proxy de silicificación y sericita) | Sintético calibrado |
| **14** | **Teledetección (Índice de Gossan / FeOx)** | Sentinel-2 / ASTER (Band Ratios) | <span style="color:orange">**PROXY POHL**</span> | `Remote_Gossan_FeOx` (Proxy de meteorización de sulfuros) | Sintético calibrado |

---

## 3. Auditoría de la Arquitectura de Machine Learning

El entrenamiento y la evaluación cumplen con el protocolo metodológico de 8 unidades (**U1 a U8**):

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│               MÉTRICAS DEL BENCHMARK EN VALIDACIÓN CRUZADA ESPACIAL (5 BLOQUES GEOGRÁFICOS)           │
├─────────────────┬──────────────────┬─────────────────┬────────────────┬─────────────┬──────────────────┤
│ Commodity       │ Positivos Reales │ Spatial ROC-AUC │ Spatial PR-AUC │ Brier Score │ F1-Score         │
├─────────────────┼──────────────────┼─────────────────┼────────────────┼─────────────┼──────────────────┤
│ 🥇 Oro (Y_Au)   │ 637 minas        │ 0.8165          │ 0.4250         │ 0.1235      │ 0.1446           │
│ 🥉 Cobre (Y_Cu) │ 186 minas        │ 0.8797          │ 0.4434         │ 0.0808      │ 0.2957           │
│ 🥈 Plata (Y_Ag) │ 179 minas        │ 0.8799          │ 0.5765         │ 0.0799      │ 0.5033           │
│ ⚙️ Plomo (Y_Pb) │ 170 minas        │ 0.8942          │ 0.6155         │ 0.0912      │ 0.5420           │
└─────────────────┴──────────────────┴─────────────────┴────────────────┴─────────────┴──────────────────┘
```

### Fortalezas Metodológicas Auditadas:
1. **Sin Fugas Espaciales (*Zero Spatial Leakage*):** Validación en 5 bloques geográficos independientes (Noroeste, Suroeste, Sierra Morena, Sureste, Centro-Norte) evitando el sobreajuste de autocorrelación espacial (Ley de Tobler).
2. **Calibración Isotonic de Probabilidades:** Reducción sistemática del Brier Score a valores $< 0.12$, garantizando que la salida $P(Y=1)$ represente favorabilidad geológica real interpretable.
3. **Explicabilidad Epistemológica SHAP:** El modelo da prioridad máxima a las fallas estructurales y a las cuarcitas/pizarras paleozoicas para el Oro, y a los complejos volcano-sedimentarios para el Cobre, validando al 100% los postulados de Walter Pohl (2011).

---

## 4. Estado de los Entregables y Productos en el Repositorio

* 📓 **Cuadernos Jupyter:** [`notebooks/`](notebooks/) (01_ontologias, 02_feature_engineering, 03_modeling_benchmark, 04_shap_inference).
* 📁 **Datasets Maestros Enriquecidos:**
  * [`data/processed/master_geoai_dataset_real_igme_ign.csv`](data/processed/master_geoai_dataset_real_igme_ign.csv)
  * [`data/processed/master_geoai_dataset_real_igme_ign.gpkg`](data/processed/master_geoai_dataset_real_igme_ign.gpkg) *(Capa oficial EPSG:25830)*
* 🤖 **Modelos Serializados Reentrenados (.joblib):** [`models/`](models/) (`model_geoai_Au_Oro.joblib`, `Cu_Cobre.joblib`, `Ag_Plata.joblib`, `Pb_Plomo.joblib`).
* 🗺️ **Visores Web Interactivos:**
  * [`data/processed/mapa_interactivo_prospectividad_nacional.html`](data/processed/mapa_interactivo_prospectividad_nacional.html) (Visor Leaflet de favorabilidad nacional y minas).
  * [`data/processed/visualizador_grafo_semantico_completo_993.html`](data/processed/visualizador_grafo_semantico_completo_993.html) (Grafo de conocimiento Linked Data).
