# Data Card: Inventario Mineral Auditado y Capas Predictoras GeoAI-Au v1.0

## 1. Motivación y Resumen del Conjunto de Datos

- **Propósito**: Proporcionar una base de datos geocientífica estandarizada, saneada y libre de fuga de información (*anti-leakage*) para el modelado cuantitativo de prospectividad mineral (MPM) de oro (Au) en España peninsular.
- **Creadores e Integradores**: Proyecto GeoAI, integrando fuentes cartográficas y bases de datos oficiales del **IGME-CSIC**, **IGN** y **Copernicus Land Monitoring Service (ESA)**.
- **Fecha de Congelación Canónica**: 27 de septiembre de 2026.
- **Licencia de Datos**: Fuentes abiertas con atribución (CC-BY 4.0 IGME; Copernicus Open Access; MIT para código de procesamiento).

---

## 2. Composición y Estructura del Inventario

### 2.1. Ocurrencias Auríferas (Etiquetas Positivas)
- **Fuente Primaria**: Base de Datos de Yacimientos y Minerales de España (**BDMIN - IGME**).
- **Inventario Inicial Bruto**: 790 registros minerales con indicación de mineralizaciones auríferas en España peninsular.
- **Auditoría Geológica Exhaustiva (Fase B)**:
  - **190 ocurrencias positivas confirmadas (`confirmada` / `P_reviewed`)**: Registros con paragénesis aurífera comprobada en bibliografía técnica o informes mineros históricos, coordenadas contrastadas y tipología genética documentada (orogénico, placer, skarn, epitermal).
  - **597 ocurrencias pendientes (`pendiente`)**: Registros en estricta cuarentena bibliográfica por evidencia insuficiente en fuentes accesibles; excluidos de todo entrenamiento y evaluación.
  - **3 ocurrencias rechazadas (`rechazada`)**: Registros formalmente descartados tras revisión geológica específica.
  - **Total**: **790 registros BDMIN** clasificados canónicamente (190 confirmados + 597 pendientes + 3 rechazados = 790).
- **Agrupación Jerárquica**:
  - Los 190 indicios confirmados corresponden a **46 depósitos independientes** y **32 distritos metalogenéticos**.
  - **Registro Maestro**: [`data/review/revision_au_fase_b.csv`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/data/review/revision_au_fase_b.csv)

### 2.2. Soporte Espacial y Rejilla Territorial
- **Sistema de Coordenadas de Referencia**: `EPSG:25830` (ETRS89 / UTM huso 30N).
- **Malla Regular de Soporte**:
  - Resolución: 1.000 m $\times$ 1.000 m (1 km² por celda).
  - Extensión de la Rejilla: 1.100 columnas $\times$ 910 filas (1.001.000 celdas teóricas).
  - Celdas terrestres de España peninsular: 496.862 celdas.

### 2.3. Máscara Canónica de Soporte: `eligible_approved_features`
Incorporada nativamente en Fase D ([`reports/fase_d/20260927T135413_959884Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_d/20260927T135413_959884Z)), define el universo territorial elegible para modelado con base exclusiva en la disponibilidad de los 56 predictores aprobados:
- **Criterios de Elegibilidad**:
  1. Fracción terrestre válida $\ge 10\%$.
  2. Cobertura litológica continua $\ge 80\%$.
  3. Cobertura cronoestratigráfica continua $\ge 80\%$.
  4. Elevación válida en MDT.
  5. Distancias a estructuras calculadas $\le 10.000$ m.
- **Universo Elegible Resultante**: **478.443 celdas** (96,29% del territorio de España peninsular).
- **Depósitos Modelables Cubiertos**: **45 de los 46 depósitos independientes** (97,8%).
  - *Depósito Clave Recuperado*: **`dep_salave`** (Asturias, 4 celdas positivas modelables).
  - *Depósito Legítimamente Excluido*: **`dep_la_preciosa_penaflor`** (Sevilla), excluido por cobertura litológica del 70,46% (< 80%).
- **Distritos Cubiertos**: **32 de 32 distritos** (100% de representatividad territorial).

---

## 3. Predictores Geocientíficos Aprobados (56 Variables)

De 168 variables candidatas en `feature_allowlist.json`, se auditaron y aprobaron **56 variables continuas**, rechazando 112 capas (proxies de mineralización, geoquímica discontinua o variables con riesgo de fuga de información):

| Familia | N° Variables | Fuente Oficial | Método de Cálculo | Unidades | Tratamiento NoData |
| :--- | :---: | :--- | :--- | :---: | :---: |
| **Litología** | 19 | IGME GEODE 1:200.000 | Fracción de área ocupada por unidad litológica dentro de la celda de 1 km² | [0, 1] | 0.0 si ausente; NoData si cobertura < 80% |
| **Cronoestratigrafía** | 27 | IGME GEODE 1:200.000 | Fracción de área ocupada por edad geológica dentro de la celda de 1 km² | [0, 1] | 0.0 si ausente; NoData si cobertura < 80% |
| **Estructuras Geológicas** | 3 | Mapa Geológico 1:1.000.000 IGME | Distancia euclídea exacta (STRtree) a trazas de fallas, cabalgamientos y contactos ígneos | Metros | Truncado a 10.000 m |
| **Relieve y Morfometría** | 6 | Copernicus DEM (GLO-30m) / MDT25 IGN | Elevación media, pendiente media, TPI (1km y 5km), rugosidad/desviación estándar (1km y 5km) | Metros / Grados | Ponderado por área terrestre válida |
| **Hidrología Regional** | 1 | Red Hidrográfica IGN/IGME | Distancia euclídea continua al cauce fluvial más próximo | Metros | Truncado a 10.000 m |

> [!NOTE]
> **Ausencia de Geoquímica Aprobada**: El Atlas Geoquímico de Sedimentos de Corriente disponible fue formalmente excluido tras la auditoría de Fase D debido a falta de cobertura analítica continua, discontinuidades de muestreo en costas/fronteras y codificación cualitativa por intervalos de color.

---

## 4. Particiones Territoriales y Muestreo P/U

### 4.1. Cuarentena de Distritos y Reserva Ciega (*Holdout*)
Pre-registrada formalmente en Fase E ([`reports/fase_e/20260927T135620_576911Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_e/20260927T135620_576911Z)) para evitar cualquier fuga espacial:
- **Distritos de Reserva Ciega (Holdout)**:
  1. `dist_cabo_de_gata` (Almería, tipología epitermal).
  2. `dist_galicia_costa_da_morte` (A Coruña, cizallas graníticas y leucogranitos).
  3. `dist_montes_de_toledo_jara` (Toledo/Ciudad Real, orogénico en metasedimentos).
  4. `dist_ossa_morena_penaflor` (Sevilla/Córdoba, skarns y cizallas).
  5. `dist_beticas_granada` (Granada, filones y aluviales béticos).
- **Dimensiones de la Partición**:
  - **Desarrollo**: 27 distritos, 37 depósitos modelables, 112 celdas positivas ($P$), 464.902 celdas elegibles.
  - **Holdout Ciego**: 5 distritos, 8 depósitos modelables, 19 celdas positivas ($P$), 13.541 celdas elegibles.

### 4.2. Muestreo de Fondo (PU Learning)
- **Buffer de Exclusión Estricto**: 5.000 m alrededor de todos los positivos conocidos para evitar contaminación de falsas ausencias.
- **Muestreo Estratificado**: Selección de celdas no etiquetadas ($U$) bajo ratios $P/U \in \{1, 3, 10\}$ con 3 realizaciones aleatorias reproducibles.

---

## 5. Integridad, Procedencia y Trazabilidad Criptográfica

Cada transformación y producto de datos se encuentra sellado mediante un manifiesto JSON con firmas SHA-256:
- Fase B: [`data/review/revision_au_fase_b.csv`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/data/review/revision_au_fase_b.csv)
- Fase C: [`data/review/territorial_groups.csv`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/data/review/territorial_groups.csv)
- Fase D: [`reports/fase_d/20260927T135413_959884Z/outputs_manifest.json`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_d/20260927T135413_959884Z/outputs_manifest.json)
- Fase E: [`reports/fase_e/20260927T135620_576911Z/outputs_manifest.json`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_e/20260927T135620_576911Z/outputs_manifest.json)
- Fase F: [`reports/fase_f/20260927T135750_819061Z/outputs_manifest.json`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_f/20260927T135750_819061Z/outputs_manifest.json)
- Fase G: [`reports/fase_g/20260927T141408_460613Z/outputs_manifest.json`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_g/20260927T141408_460613Z/outputs_manifest.json)
- Fase H: [`reports/fase_h/20260927T142549_961719Z/outputs_manifest.json`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_h/20260927T142549_961719Z/outputs_manifest.json)
