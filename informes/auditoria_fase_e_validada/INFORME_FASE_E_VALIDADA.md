# Informe de Auditoría y Cierre Técnico: Fase E Validada (Paso 8)

**Fecha de ejecución:** 2026-09-27  
**Identificador de ejecución E:** [`reports/fase_e/20260927T115302_113892Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_e/20260927T115302_113892Z)  
**Ejecución D congelada de origen:** [`reports/fase_d/20260927T112256_510493Z`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_d/20260927T112256_510493Z)  
**Configuración activa:** [`config/evaluation.yaml`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/config/evaluation.yaml)  
**Estado:** `completada` | `mode: validated` | `fase_e_cientifica_cerrada: true` | `training_allowed: true`

---

## 1. Resumen Ejecutivo y Declaración de Transición a Modo Validado

En cumplimiento del **Paso 8**, se ha activado formalmente el protocolo científico validado (`mode: validated`) y se ha regenerado la Fase E desde cero.

Esta ejecución supera todos los bloqueos metodológicos y diagnósticos de las fases anteriores:
1. **Rol estricto de Positivos Revisados:** El protocolo selecciona exclusivamente registros con evidencia geológica confirmada (`selected_role == 'P_reviewed'`). **Cero candidatos proxy (`P_candidate_proxy`) participan como positivos.**
2. **Espacio de Características Autorizado:** Se restringe rigurosamente a las **56 variables aprobadas** en la auditoría semántica de Fase D ([`feature_allowlist.json`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_d/20260927T112256_510493Z/feature_allowlist.json)), excluyendo las 94 variables rechazadas y las 18 pendientes.
3. **Reserva Ciega Pre-Registrada:** Se han aislado los **5 distritos metalogenéticos congelados** en el Paso 7 como holdout ciego territorial.
4. **Protocolo Espacial Congelado:** Bloques transitivos de 50.000 m (50 km) con un buffer de separación espacial de 5.000 m (5 km), garantizando una cota inferior real de separación $> 5.293,9\text{ m}$.
5. **Cuarentena Absoluta de la Reserva:** La reserva ciega no participa en entrenamiento, selección de hiperparámetros, imputación, escalado, selección de variables ni elección de modelo. **No se ha evaluado ningún modelo sobre la reserva ciega.**
6. **Estructura Anidada Completa:** 5 folds externos (`outer`), 15 particiones internas (`inner`) y 180 muestras de presencia/fondo ($P/U$) estratificadas y ponderadas.

---

## 2. Auditoría del Universo de Positivos Revisados (`P_reviewed`)

En Fase E validada, la selección de etiquetas utiliza exclusivamente el campo `elegible_general_revisada == True`, descartando por diseño cualquier indicio no auditado.

| Métrica de Positivos | Valor Auditado | Observaciones Metodológicas |
| :--- | :---: | :--- |
| **Registros positivos revisados con soporte (`eligible_geo4`)** | **174** | De los 190 confirmados en Fase B; 16 registros caen fuera de la máscara de soporte geoquímico/territorial de 1 km. |
| **Celdas únicas positivas (1 km)** | **130** | Huella rasterizada territorial efectiva sin multiplicidad por labores mineras. |
| **Yacimientos/depósitos independientes** | **44** | Unidades genéticas auditadas con evidencia documental trazable. |
| **Distritos metalogenéticos representados** | **31** | Distritos geológicos delimitados según cartografía territorial. |
| **Rol en protocolo (`protocol_role`)** | **`P_reviewed` (100%)** | 174/174 registros. **Cero `P_candidate_proxy`.** |
| **Verificación de duplicidad / dispersión** | **Aprobada** | Múltiples labores del mismo yacimiento agrupadas bajo un único `deposit_id`. |

Artefacto sellado: [`design/selected_positive_records.parquet`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_e/20260927T115302_113892Z/design/selected_positive_records.parquet).

---

## 3. Desglose Territorial: Desarrollo (CV) vs. Holdout (Reserva Ciega)

La partición entre el universo de desarrollo (destinado al bucle anidado de entrenamiento, validación y evaluación externa) y la reserva ciega (holdout final intocable) se realiza a nivel de unidades transitivas completas de 50 km asociadas a los distritos pre-registrados.

### 3.1 Balance Cuantitativo General

| Dimensión Territorial | Desarrollo (CV) | Holdout (Reserva Ciega) | Total Nacional Elegible | % Holdout |
| :--- | :---: | :---: | :---: | :---: |
| **Celdas de 1 km con soporte** | 459.012 | 13.536 | 472.548 | 2,86 % |
| **Celdas positivas revisadas ($P$)** | 111 | 19 | 130 | 14,62 % |
| **Yacimientos independientes** | 36 | 8 | 44 | 18,18 % |
| **Distritos metalogenéticos** | 26 | 5 | 31 | 16,13 % |
| **Unidades conectadas (50 km)** | 224 | 5 | 229 | 2,18 % |
| **Solapamiento transitivo** | — | — | **0 unidades** | **0,00 %** |

### 3.2 Inventario Detallado de la Reserva Ciega Holdout

Los 5 distritos de reserva conforman 5 unidades espaciales de 50 km completamente disjuntas del universo de desarrollo:

| Distrito Holdout | Código Unidad (50 km) | Yacimientos / Depósitos Independientes | Celdas $P$ | Registros $P$ | Tipología Geológica Principal |
| :--- | :---: | :--- | :---: | :---: | :--- |
| **`dist_cabo_de_gata`** | `b15_12` | `dep_rodalquilar_cinto`, `dep_rodalquilar_santa_josefa` | 4 | 7 | Epitermal de alta sulfuración volcánico Neógeno |
| **`dist_galicia_costa_da_morte`** | `b1_1` | `dep_corcoesto`, `dep_santa_comba_zas` | 6 | 6 | Filones de cuarzo y cizallas orogénicas hercínicas |
| **`dist_montes_de_toledo_jara`** | `b9_7` | `dep_la_oriental_la_jara` | 4 | 4 | Cizallas e intrusiones tardi-hercínicas en metasedimentos |
| **`dist_ossa_morena_penaflor`** | `b13_6` | `dep_la_almenara_penaflor`, `dep_navalmedio_penaflor` | 4 | 13 | Skarn y filones hidrotermales en zócalo paleozoico |
| **`dist_beticas_granada`** | `b14_10` | `dep_california_granadina_darro` | 1 | 1 | Placeres y mineralizaciones aluviales/complejo bético |
| **Total Reserva Holdout** | **5 unidades** | **8 depósitos independientes** | **19 celdas** | **31 registros** | **Representación multigenética equilibrada** |

Artefacto sellado: [`design/spatial_units.parquet`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_e/20260927T115302_113892Z/design/spatial_units.parquet).

---

## 4. Cuarentena y Blindaje de la Reserva Ciega

Se ha verificado matemáticamente y por software la estricta cuarentena de la reserva:

1. **Cuarentena en Membresías (`memberships/*.parquet`):**
   - En las 20 particiones (5 outer, 15 inner), las 13.536 celdas de holdout tienen asignado obligatoriamente el rol `role == 'holdout'`.
   - **Intersección de celdas holdout con train:** $\emptyset$ (0 celdas en todos los splits).
   - **Intersección de celdas holdout con test:** $\emptyset$ (0 celdas en todos los splits).
   - **Intersección de celdas holdout con spatial_gap:** $\emptyset$ (0 celdas).
2. **Cuarentena en Muestras de Fondo ($P/U$):**
   - El generador [`background_pool()`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/src/geoau/evaluation.py#L329-L342) filtra exclusivamente `membership.role == 'train'`.
   - Dado que ninguna celda de holdout tiene rol `train`, **cero celdas de holdout entran en el pool de no-etiquetados ($U$)**.
   - Se ha auditado cada uno de los 180 ficheros de muestras en [`samples/`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_e/20260927T115302_113892Z/samples/): **0 celdas de holdout en todas las muestras.**
3. **Contrato de Aprendizaje (`learning_contract.json`):**
   - Cláusula de Holdout: *"no se generan muestras para entrenar/ajustar sobre la reserva"*.
   - Cláusula de Preprocesamiento: *"imputación, codificación, selección y escalado se ajustan en cada train interno"*.
   - Cláusula de Ajuste: *"corresponde a fase F; aquí solo contratos y diseños"*.
   - **Ningún modelo de Machine Learning ha sido evaluado ni ajustado sobre la reserva.**

---

## 5. Auditoría de las 20 Particiones Espaciales Anidadas

### 5.1 Folds Externos (Outer CV, $k=5$)

El universo de desarrollo (224 unidades de 50 km) se particiona en 5 folds externos balanceados por bloques y depósitos:

| Split ID | Celdas Train | Celdas Test | Celdas $P$ Train | Celdas $P$ Test | Unidades $P$ Train | Unidades $P$ Test | Cota Inferior Gap Espacial ($m$) | Solapamiento Unidades |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`outer_00`** | 327.946 | 93.054 | 91 | 19 | 14 | 3 | $5.294,0\text{ m}$ | 0 |
| **`outer_01`** | 333.098 | 88.078 | 99 | 9 | 14 | 3 | $5.294,0\text{ m}$ | 0 |
| **`outer_02`** | 329.256 | 89.670 | 91 | 20 | 13 | 4 | $5.294,0\text{ m}$ | 0 |
| **`outer_03`** | 326.749 | 93.704 | 72 | 35 | 12 | 5 | $5.294,0\text{ m}$ | 0 |
| **`outer_04`** | 322.875 | 94.506 | 71 | 28 | 13 | 2 | $5.294,0\text{ m}$ | 0 |

- **Separación espacial garantizada:** En todos los folds externos, la cota inferior de distancia entre cualquier huella de celda de train y cualquier huella de celda de test o holdout es $\ge 5.294,0\text{ m}$, superando el requisito de 5.000 m.
- **Factibilidad demostrada:** Todos los folds superan ampliamente el umbral mínimo fijado (`minimum_positive_units_test >= 1` y `minimum_positive_units_train >= 2`).

### 5.2 Folds Internos (Inner CV, 15 particiones)

Dentro de cada fold externo, su conjunto `train` se particiona en 3 folds internos ($5 \times 3 = 15$ splits) para la selección de hiperparámetros, ratio $P/U$ y calibración:

| Split ID | Celdas Train | Celdas Test | Celdas $P$ Train | Celdas $P$ Test | Unidades $P$ Train | Unidades $P$ Test | Gap Espacial ($m$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `outer_00_inner_00` | 190.140 | 108.540 | 70 | 10 | 9 | 4 | $5.294,0\text{ m}$ |
| `outer_00_inner_01` | 188.228 | 114.597 | 39 | 48 | 8 | 6 | $5.294,0\text{ m}$ |
| `outer_00_inner_02` | 196.658 | 104.809 | 58 | 33 | 10 | 4 | $5.294,0\text{ m}$ |
| `outer_01_inner_00` | 198.410 | 107.472 | 91 | 3 | 12 | 1 | $5.294,0\text{ m}$ |
| `outer_01_inner_01` | 205.256 | 103.256 | 67 | 32 | 9 | 5 | $5.294,0\text{ m}$ |
| `outer_01_inner_02` | 183.840 | 122.370 | 32 | 64 | 5 | 8 | $5.294,0\text{ m}$ |
| `outer_02_inner_00` | 177.532 | 125.786 | 22 | 65 | 6 | 6 | $5.294,0\text{ m}$ |
| `outer_02_inner_01` | 202.022 | 101.711 | 67 | 18 | 8 | 5 | $5.294,0\text{ m}$ |
| `outer_02_inner_02` | 199.894 | 101.759 | 83 | 8 | 11 | 2 | $5.294,0\text{ m}$ |
| `outer_03_inner_00` | 194.927 | 106.575 | 47 | 25 | 6 | 6 | $5.294,0\text{ m}$ |
| `outer_03_inner_01` | 194.257 | 105.235 | 67 | 1 | 10 | 1 | $5.294,0\text{ m}$ |
| `outer_03_inner_02` | 184.624 | 114.939 | 26 | 46 | 7 | 5 | $5.294,0\text{ m}$ |
| `outer_04_inner_00` | 193.788 | 101.448 | 36 | 35 | 8 | 5 | $5.294,0\text{ m}$ |
| `outer_04_inner_01` | 185.757 | 108.632 | 45 | 26 | 8 | 5 | $5.294,0\text{ m}$ |
| `outer_04_inner_02` | 182.135 | 112.795 | 57 | 10 | 10 | 3 | $5.294,0\text{ m}$ |

- **Anidamiento estricto:** Se ha comprobado que $\text{train}_{\text{inner}} \cup \text{test}_{\text{inner}} \subseteq \text{train}_{\text{outer}}$. Ningún dato de prueba externa es visible en el bucle interno.

Artefactos sellados: [`split_summary.csv`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_e/20260927T115302_113892Z/split_summary.csv), [`split_plan.json`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_e/20260927T115302_113892Z/split_plan.json).

---

## 6. Auditoría del Muestreo de Presencia / Fondo ($P/U$)

Se han generado 180 conjuntos de muestras ($20\text{ particiones} \times 3\text{ ratios } [1, 3, 10] \times 3\text{ realizaciones } [0, 1, 2]$):

| Nivel | Ratio Solicitado ($U:P$) | Total Muestras | Rango $n_P$ | Rango $n_U$ | $U$ Disponibles en Pool | Tasa de Saturación (`pool_capped`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Outer** | 1 | 15 | 71 – 99 | 71 – 99 | 288.756 – 299.117 | **0 / 15** |
| **Outer** | 3 | 15 | 71 – 99 | 213 – 297 | 288.756 – 299.117 | **0 / 15** |
| **Outer** | 10 | 15 | 71 – 99 | 710 – 990 | 288.756 – 299.117 | **0 / 15** |
| **Inner** | 1 | 45 | 22 – 91 | 22 – 91 | 156.402 – 186.208 | **0 / 45** |
| **Inner** | 3 | 45 | 22 – 91 | 66 – 273 | 156.402 – 186.208 | **0 / 45** |
| **Inner** | 10 | 45 | 22 – 91 | 220 – 910 | 156.402 – 186.208 | **0 / 45** |
| **Total** | — | **180** | **22 – 99** | **22 – 990** | **156.402 – 299.117** | **0 / 180 (0,0%)** |

### 6.1 Propiedades Estadísticas Verificadas
1. **Representatividad Territorial:** Muestreo aleatorio estratificado en dos etapas por bloque territorial. Todos los estratos poseen probabilidad de inclusión positiva ($> 0$).
2. **Buffer de Protección Conservador:** Se aplica un buffer de exclusión de 250 m respecto a los $P$ de entrenamiento para evitar incluir zonas inmediatas de yacimientos como fondo no etiquetado.
3. **Ponderaciones Rigurosas:** Cada muestra incluye `inclusion_probability`, `inverse_inclusion_weight` y `area_weight_m2`. No se utilizan pesos arbitrarios ni asunciones no demostradas de prevalencia.
4. **Bandera de Entrenamiento:** `sample['training_allowed'] == True` y `sample['mode'] == 'validated'` en las 180 muestras.

Artefactos sellados: [`sample_summary.csv`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_e/20260927T115302_113892Z/sample_summary.csv), [`samples/*.parquet`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_e/20260927T115302_113892Z/samples/).

---

## 7. Espacio de Características Congelado (56 Variables Aprobadas)

De acuerdo con la auditoría semántica de predictores de Fase D (Paso 6), el ajuste de modelos en Fase F consumirá estrictamente las 56 variables aprobadas contenidas en [`feature_allowlist.json`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_d/20260927T112256_510493Z/feature_allowlist.json):

1. **Litología y Geoquímica de Roca (3 variables):** `litologia_frecuente`, `edad_min_frecuente`, `edad_max_frecuente`.
2. **Estructuras Tectónicas y Fallas (6 variables):** `dist_contacto_m`, `dist_falla_m`, `dens_contactos_km_km2`, `dens_fallas_km_km2`, `dens_ejes_km_km2`, `tipo_contacto_frecuente`.
3. **Morfometría y Relieve MDT 25m (8 variables):** `elevacion_media_m`, `pendiente_media_grad`, `curvatura_media`, `rugosidad_media_m`, `tpi_300m_media_m`, `tpi_1000m_media_m`, `tpi_2000m_media_m`, `desv_elevacion_m`.
4. **Geofísica Regional IGME (8 variables):** `bouguer_media_mgal`, `gradiente_bouguer_mgal_km`, `anomalia_magnetica_media_nt`, `gradiente_magnetico_nt_km`, `radiometria_k_media_pct`, `radiometria_th_media_ppm`, `radiometria_u_media_ppm`, `ratio_u_th_media`.
5. **Hidrografía y Red de Drenaje (4 variables):** `dist_cauce_m`, `dens_aprox_cauce_1km_km2`, `dens_aprox_cauce_3km_km2`, `dens_aprox_cauce_5km_km2`.
6. **Geoquímica Multielemental de Sedimentos de Corriente (27 variables):**
   - Au: `au_ppm_media`, `au_clase_modal`, `au_enriquecimiento_regional`.
   - As (Pathfinder): `as_ppm_media`, `as_clase_modal`, `as_enriquecimiento_regional`.
   - Sb (Pathfinder): `sb_ppm_media`, `sb_clase_modal`, `sb_enriquecimiento_regional`.
   - Bi (Pathfinder): `bi_ppm_media`, `bi_clase_modal`, `bi_enriquecimiento_regional`.
   - Cu, Pb, Zn, W, Hg (Base metals / elementos indicadores): media, clase modal y enriquecimiento regional para cada elemento.

*Variables rechazadas (94) y pendientes (18)* permanecen deshabilitadas en el diccionario y manifiesto de Fase D.

---

## 8. Cierre Técnico y Cadena de Custodia Criptográfica

La ejecución validada ha sido cerrada y verificada mediante:
- **`control_cierre.json`:**
  ```json
  {
    "estado_ejecucion": "completada",
    "mode": "validated",
    "fase_e_cientifica_cerrada": true,
    "training_allowed": true,
    "prediction_allowed": false,
    "eligible_cells": 472548,
    "reviewed_positive_cells": 130,
    "selected_protocol_positive_cells": 130,
    "outer_folds": 5,
    "split_designs": 20,
    "sample_designs": 180,
    "minimum_gap_lower_bound_m": 5293.990370126274,
    "reasons_not_ready": []
  }
  ```
- **Sellado Criptográfico:** Manifiesto [`outputs_manifest.json`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_e/20260927T115302_113892Z/outputs_manifest.json) con **398 archivos** sellados con sus respectivos hashes SHA256.
- **Validación Independiente:** [`scripts/validar_fase_e.py`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/scripts/validar_fase_e.py) ejecutado con éxito comprobando el 100% de muestras y particiones.
- **Suite de Pruebas:** 75 tests unitarios superados en [`tests/`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/tests/), incluyendo el nuevo test formal `test_validated_phase_e_contract`.
- **Configuración de Entrenamiento:** [`config/training.yaml`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/config/training.yaml) actualizado para apuntar a `reports/fase_e/20260927T115302_113892Z`.
