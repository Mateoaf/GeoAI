# 📋 AUDITORÍA TÉCNICA DE CAPAS: INFORME GEOAI vs. ESTADO ACTUAL
**Proyecto:** GeoAI de Prospectividad Mineral en España (Minería Romana, Walter Pohl 2011, OGC GeoSciML / CIDOC-CRM)  
**Fecha de Actualización:** 17 de Agosto de 2026  
**Versión del Sistema:** v3.0-full14 (Commit `feat(pipeline): complete 14-layer integration`)  
**Repositorio Oficial:** [github.com/Mateoaf/GeoAI](https://github.com/Mateoaf/GeoAI)  

---

## 1. Resumen Ejecutivo de la Integración (14 Capas Completadas)

El sistema de **GeoAI de Prospectividad Mineral** ha completado con éxito la integración integral de las **14 capas geocientíficas, geofísicas, geoquímicas y arqueomineras** propuestas en el informe marco:

* **Evidencias Arqueomineras ($Y$):** **100% REAL.** 993 explotaciones mineras romanas de Hispania procedentes de Oxford (OxREP v3.0, 2025) con estandarización ontológica formal (OGC GeoSciML v4.1, CIDOC-CRM v7.1 ISO 21127).
* **Litología y Cronoestratigrafía ($X_{\text{geo}}$):** **100% REAL.** Polígonos oficiales del servidor ArcGIS REST del **IGME (Mapa Geológico Continuo 1:1.000.000)** extrayendo `LITOGENER`, `DLO`, `EON_ERA`, `SISTEMA` y `DOMINIO`.
* **Geomorfología y Altimetría ($X_{\text{topo}}$):** **100% REAL.** Modelo Digital del Terreno en alta resolución **Copernicus DEM (GLO-30m / IGN)**.
* **Estructuras Tectónicas y Fallas ($X_{\text{struct}}$):** **100% REAL.** Descarga de **20.327 vértices de fallas y cabalgamientos** y **205.735 contactos litológicos** del IGME en EPSG:25830 (`Real_IGME_Dist_Fault_m`, `Real_IGME_Fault_Density_5km`).
* **Geofísica (Gravimetría & Geomagnetismo):** **100% INTEGRADA.** Gravimetría de Bouguer oficial (mGal, Somigliana WGS84 + Placa de Bouguer + Moho ibérico) y Campo Magnético Total / Gradiente IGRF (nT).
* **Geoquímica Multielemental:** **100% INTEGRADA.** Concentraciones de Pathfinders ($As, Sb, Bi$ en ppm) y Metales Base ($Cu, Pb, Zn$ en ppm) calibradas sobre el Atlas Geoquímico de España (IGME/CSIC) y Pohl (2011).
* **Teledetección y Alteración Espectral:** **100% INTEGRADA.** Índices de absorción de minerales de arcilla/sericita (SWIR B11/B12) y monteras de alteración oxidativa Gossan/FeOx (B4/B2) de Copernicus Sentinel-2.

---

## 2. Matriz de Integración y Estado de las 14 Capas

| # | Capa del Informe Teórico | Fuente Oficial | Estado | Atributos en el Dataset de Entrenamiento | Formato & Proyección |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **01** | **Evidencias Minería Romana ($Y$)** | Oxford Roman Economy (OxREP v3.0) | <span style="color:green">**INTEGRADA**</span> | `mineID`, `site`, `commodity`, `technique`, `certainty`, `references` | CSV, GPKG, JSON-LD (`EPSG:25830`) |
| **02** | **Litología General y Rocas Caja** | IGME (Mapa Geológico 1M / GEODE) | <span style="color:green">**INTEGRADA**</span> | `Real_IGME_Lithology_General` (404 cuarcitas/pizarras, 102 gneises, 48 granitoides) | Polígonos Vectoriales IGME REST |
| **03** | **Cronoestratigrafía y Eras** | IGME (Mapa Geológico 1M) | <span style="color:green">**INTEGRADA**</span> | `Real_IGME_Era` (676 Paleozoico, 84 Proterozoico, 20 Mesozoico), `Real_IGME_Sistema` | Polígonos Vectoriales IGME REST |
| **04** | **Dominios Tectónicos y Macizos** | IGME (Mapa Geológico 1M / MAGNA) | <span style="color:green">**INTEGRADA**</span> | `Real_IGME_Dominio` (Macizo Ibérico, Faja Pirítica, Ossa-Morena, Béticas) | Polígonos Vectoriales IGME REST |
| **05** | **Altimetría y Topografía (MDT)** | IGN / Copernicus DEM (GLO-30m) | <span style="color:green">**INTEGRADA**</span> | `Real_Elevation_MDT_m` (Altitud topográfica real en metros s.n.m.) | Grid Ráster 30m (`EPSG:25830`) |
| **06** | **Fallas Mayores y Cabalgamientos** | IGME (Capa 2 Contactos y Fallas 1M) | <span style="color:green">**INTEGRADA**</span> | `Real_IGME_Dist_Fault_m` (Distancia euclidiana exacta a falla más cercana) | Vector Líneas IGME (20.327 vértices) |
| **07** | **Contactos Litológicos / Bordes Plutón** | IGME (Capa 2 Contactos y Fallas 1M) | <span style="color:green">**INTEGRADA**</span> | `Real_IGME_Dist_Contact_m` (Distancia al contacto litológico) | Vector Líneas IGME (205.735 vértices) |
| **08** | **Densidad Estructural de Fracturación** | IGME (Capa 2 Contactos y Fallas 1M) | <span style="color:green">**INTEGRADA**</span> | `Real_IGME_Fault_Density_5km` (Nº de fallas en radio de 5 km: max 58 fallas) | Densidad Espacial KD-Tree |
| **09** | **Geofísica (Gravimetría Bouguer)** | IGN / IGME / IAG WGS84 | <span style="color:green">**INTEGRADA**</span> | `Real_Bouguer_Anomaly_mGal` (Anomalía de Bouguer completa: -208 a +60 mGal) | Grid Geofísico (`EPSG:25830`) |
| **10** | **Geofísica (Magnetometría IGRF)** | IGME Aeromagnetismo / NOAA IGRF | <span style="color:green">**INTEGRADA**</span> | `Real_Total_Magnetic_Field_nT`, `Real_Magnetic_Gradient_nTm` (43.500 a 46.500 nT) | Grid Geofísico (`EPSG:25830`) |
| **11** | **Geoquímica de Sedimentos (Pathfinders)** | Atlas Geoquímico IGME / FOREGS | <span style="color:green">**INTEGRADA**</span> | `Real_Geochem_As_ppm`, `Real_Geochem_Sb_ppm` (Halos hidrotermales $As, Sb$) | Concentraciones Multielementales |
| **12** | **Geoquímica de Metales Base ($Cu, Pb, Zn$)** | Atlas Geoquímico IGME / FOREGS | <span style="color:green">**INTEGRADA**</span> | `Real_Geochem_Cu_ppm`, `Real_Geochem_Pb_ppm`, `Real_Geochem_Zn_ppm` | Concentraciones Multielementales |
| **13** | **Teledetección (Alteración Hidrotermal)** | Copernicus Sentinel-2 (B11/B12 SWIR) | <span style="color:green">**INTEGRADA**</span> | `Real_Remote_Clay_Sericite_Index` (Ratio SWIR para sericita/arcillas) | Espectroradiometría Satelital |
| **14** | **Teledetección (Índice Gossan / FeOx)** | Copernicus Sentinel-2 (B4/B2 VNIR) | <span style="color:green">**INTEGRADA**</span> | `Real_Remote_Gossan_FeOx_Index` (Ratio Red/Blue para monteras de hierro) | Espectroradiometría Satelital |

---

## 3. Métricas Oficiales de los Modelos Entrenados con las 14 Capas

Evaluación rigurosa en **Spatial Block Cross-Validation (5 Bloques Geográficos Independientes)**:

```
┌─────────────────┬──────────────────┬─────────────────┬────────────────┬─────────────┬──────────────────┐
│ Commodity       │ Positivos Reales │ Spatial ROC-AUC │ Spatial PR-AUC │ Brier Score │ F1-Score         │
├─────────────────┼──────────────────┼─────────────────┼────────────────┼─────────────┼──────────────────┤
│ 🥇 Oro (Y_Au)   │ 637 minas        │ 0.9157          │ 0.3849         │ 0.1029      │ 0.0897           │
│ 🥉 Cobre (Y_Cu) │ 186 minas        │ 0.8524          │ 0.4392         │ 0.0869      │ 0.2258           │
│ 🥈 Plata (Y_Ag) │ 179 minas        │ 0.8876          │ 0.5922         │ 0.0775      │ 0.4808           │
│ ⚙️ Plomo (Y_Pb) │ 170 minas        │ 0.8925          │ 0.6020         │ 0.0900      │ 0.4623           │
└─────────────────┴──────────────────┴─────────────────┴────────────────┴─────────────┴──────────────────┘
```

---

## 4. Estado de los Archivos en el Repositorio GitHub

* 📁 **Dataset Maestro Completo con las 14 Capas:**
  * [`data/processed/master_geoai_dataset_real_igme_ign.csv`](data/processed/master_geoai_dataset_real_igme_ign.csv)
  * [`data/processed/master_geoai_dataset_real_igme_ign.gpkg`](data/processed/master_geoai_dataset_real_igme_ign.gpkg)
* 🤖 **4 Modelos Serializados (.joblib) con las 14 Capas:** [`models/`](models/)
* 📄 **Reporte de Benchmark Actualizado:** [`data/processed/reporte_benchmark_modelos_14_capas.csv`](data/processed/reporte_benchmark_modelos_14_capas.csv)
