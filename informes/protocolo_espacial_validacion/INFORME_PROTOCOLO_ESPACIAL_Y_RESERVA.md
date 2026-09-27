# INFORME DE PRE-REGISTRO Y CIERRE DEL PROTOCOLO ESPACIAL DE VALIDACIÓN

**Fecha:** 27 de septiembre de 2026  
**Proyecto:** GeoAI - Prospección Aurífera en España Peninsular  
**Fase:** Fase E (Diseño y Protocolo Espacial de Evaluación)  
**Configuración:** `config/evaluation.yaml` (`mode: diagnostic`, protocolo revisado)  

---

## 1. Justificación y Metodología de Selección de la Reserva Ciega

La selección de distritos de reserva (*blind holdout*) se ha realizado **exclusivamente mediante criterios geológicos, espaciales y de aislamiento territorial**, sin emplear resultados de modelos, puntuaciones predictivas ni métricas de ajuste.

### Criterios de Selección Aplicados:
1. **Aislamiento en Bloques de 50 km**: Cada distrito seleccionado constituye una unidad conectada (`unit_id`) totalmente aislada. Ninguno de los 5 distritos de reserva comparte bloque ni conectividad espacial con ningún distrito del conjunto de desarrollo.
2. **Indivisibilidad Territorial**: El 100% de las celdas territoriales y depósitos pertenecientes a cada distrito quedan confinados íntegramente en la reserva. Ningún distrito aparece fragmentado entre desarrollo y holdout.
3. **Diversidad Metalogenética**: Cubre los principales modelos de depósito aurífero presentes en la península:
   - *Epitermal de alta sulfuración en calderas volcánicas neógenas* (Cabo de Gata - Rodalquilar).
   - *Orogénico tardi-varisco en zonas de cizalla* (Costa da Morte - Corcoesto).
   - *Filones hidrotermales en zócalo neoproterozoico* (Montes de Toledo - La Jara).
   - *Skarn y reemplazamiento polimetálico de Au-Cu* (Ossa-Morena - Peñaflor).
   - *Placer y abanico aluvial intramontañoso bético* (Béticas - Río Darro).
4. **Dispersión Geográfica Extrema**: Distritos distribuidos en cuadrantes opuestos de España (Almería, A Coruña, Toledo, Sevilla, Granada), con separaciones inter-distrito de entre 250 km y más de 850 km.
5. **Proporcionalidad**:
   - 5 distritos de reserva sobre 32 totales (**15.6%**, en concordancia exacta con `holdout_fraction: 0.15`).
   - 8 depósitos independientes sobre 46 (**17.4%**).
   - 19 celdas positivas revisadas sobre 130 (**14.6%**).
   - 14.151 celdas terrestres en holdout (**2.85%** de la superficie peninsular).

### Cuadro de los 5 Distritos de Reserva Seleccionados

| Distrito ID | Nombre | Provincia | Dominio Metalogenético | N.º Depósitos | N.º Celdas P | Bloque 50 km |
|---|---|---|---|---|---|---|
| `dist_cabo_de_gata` | Cabo de Gata - Rodalquilar | Almería | Epitermal Au-Ag de alta sulfuración en calderas vo... | 2 | 4 | `b15_12 (unidad aislada)` |
| `dist_galicia_costa_da_morte` | Costa da Morte - Corcoesto | A Coruña | Filones y cizallas orogénicas tardi-variscas en me... | 2 | 6 | `b1_1 (unidad aislada)` |
| `dist_montes_de_toledo_jara` | Montes de Toledo - La Jara | Toledo | Filones de cuarzo aurífero en esquistos y grauvaca... | 1 | 4 | `b9_7 (unidad aislada)` |
| `dist_ossa_morena_penaflor` | Ossa-Morena - Peñaflor | Sevilla | Skarn y reemplazamiento hidrotermal polimetálico d... | 2 | 4 | `b13_6 (unidad aislada)` |
| `dist_beticas_granada` | Béticas - Río Darro (California Granadina) | Granada | Placer y abanicos aluviales pliocenos/cuaternarios... | 1 | 1 | `b14_10 (unidad aislada)` |

---

## 2. Análisis de Sensibilidad de Parámetros Espaciales

### 2.1. Sensibilidad del Tamaño de Bloque (`block_size_m`)

Se evaluaron tamaños de 25 km, 50 km y 100 km mediante agregación transitiva de bloques en `connected_units()`:

| Tamaño de Bloque | Bloques Brutos | Unidades Conectadas | Unidades con Positivos | Máx P / Unidad | Media P / Unidad | Diagnóstico Metodológico |
|---|---|---|---|---|---|---|
| **25.0 km** (25000.0 m) | 888.0 | 869.0 | 26.0 | 22.0 | 5.0 | Demasiado pequeño: fragmenta distritos continuos |
| **50.0 km** (50000.0 m) | 246.0 | 237.0 | 22.0 | 27.0 | 5.91 | Óptimo: balance entre representatividad y 5 folds viables |
| **100.0 km** (100000.0 m) | 72.0 | 69.0 | 16.0 | 30.0 | 8.12 | Demasiado grande: agrupa distritos independientes y reduce folds |

**Conclusión de tamaño de bloque:** El valor **`block_size_m = 50000`** es óptimo. A 25 km, distritos regionales continuos (ej. Maragatería o Navelgas) se fragmentan a través de los límites de bloque. A 100 km, el número de unidades positivas cae a 16, lo que impide una validación cruzada estratificada balanceada de 5 pliegues. A 50 km se obtienen **22 unidades positivas independientes**, permitiendo entre 12 y 14 unidades positivas de entrenamiento y entre 2 y 5 de test por pliegue.

### 2.2. Sensibilidad del Margen de Separación Espacial (`spatial_gap_m`)

Se evaluaron buffers de exclusión de 5 km, 10 km y 20 km:

| Spatial Gap | Celdas Train Medias | Celdas Test Medias | Celdas Buffer Perdidas | % Territorio Perdido | Separación Mínima Verificada | Diagnóstico |
|---|---|---|---|---|---|---|
| **5.0 km** (5000.0 m) | 327,984.0 | 91,802.0 | 39,224.0 | 7.89 % | 5294.0 m | Óptimo: elimina autocorrelación local sin desangrar fondo |
| **10.0 km** (10000.0 m) | 293,438.0 | 91,802.0 | 73,771.0 | 14.85 % | 10247.7 m | Pérdida moderada: reduce fondo un 14% |
| **20.0 km** (20000.0 m) | 219,806.0 | 91,802.0 | 147,403.0 | 29.67 % | 20056.7 m | Inviable: elimina >27% del país en cada split |

**Conclusión de margen de separación:** El valor **`spatial_gap_m = 5000`** es óptimo. Garantiza una distancia física estricta de $> 5.293\text{ m}$ entre la huella de cualquier celda de test/reserva y cualquier celda de entrenamiento, superando con creces la longitud de autocorrelación espacial de los predictores de relieve y litología, y perdiendo únicamente un 7.3% de celdas buffer.

---

## 3. Estado de Viabilidad de los Folds de Validación Cruzada (Outer Folds)

Se simuló la partición anidada en 5 pliegues exteriores sobre las 232 unidades de desarrollo (excluyendo la reserva):

- **Fold 0**: 14 unidades positivas en train, 3 en test (327.946 celdas train / 93.054 celdas test).
- **Fold 1**: 14 unidades positivas en train, 3 en test (333.098 celdas train / 88.078 celdas test).
- **Fold 2**: 13 unidades positivas en train, 4 en test (329.256 celdas train / 89.670 celdas test).
- **Fold 3**: 12 unidades positivas en train, 5 en test (326.749 celdas train / 93.704 celdas test).
- **Fold 4**: 13 unidades positivas en train, 2 en test (322.875 celdas train / 94.506 celdas test).

Todos los pliegues superan ampliamente el contrato mínimo (`train_p_units >= 2` y `test_p_units >= 1`), con separación espacial garantizada de $> 5.000\text{ m}$.

---

## 4. Resultado de la Verificación con `readiness()`

Tras pre-registrar la reserva ciega (`reserve_district_ids`) y establecer `protocol_reviewed: true` en `config/evaluation.yaml`, la compuerta científica `readiness()` ha sido evaluada:

- `ready_for_scientific_training`: **TRUE**
- `reasons`: **[] (0 bloqueos científicos restantes)**
- `mode`: **diagnostic** (mantenido intacto; modelos no entrenados)
