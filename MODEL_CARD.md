# Model Card: GeoAI-Au v1.0 (`logistic_01`)

## 1. Resumen y Detalles del Modelo

- **Nombre del Modelo**: GeoAI-Au v1.0 (`logistic_01`)
- **Versión**: 1.0 (Release Científico)
- **Tipo de Algoritmo**: Regresión Logística Binaria con regularización de norma L2 (Ridge).
- **Entorno de Ejecución**: Python 3.10+, `scikit-learn>=1.3.0`, `joblib>=1.3.0`.
- **Artefacto Serializado**: [`reports/fase_f/20260927T135750_819061Z/final_model/final_validated_model.joblib`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/reports/fase_f/20260927T135750_819061Z/final_model/final_validated_model.joblib)
- **Hash SHA-256 del Modelo**: `63013b0aef1c7bb5e905ef96472f1092e077a942daffc05fc085600b841d7c35`
- **Fecha de Congelación**: 27 de septiembre de 2026.
- **Licencia**: MIT.

### Hiperparámetros y Preprocesamiento
- **Pipeline**:
  1. `StandardScaler(with_mean=True, with_std=True)`: Estandarización de medias y varianzas empíricas ajustadas exclusivamente sobre el conjunto global de desarrollo.
  2. `LogisticRegression(C=0.1, penalty='l2', solver='lbfgs', max_iter=1000, random_state=42)`: Clasificador lineal regularizado.
- **Estrategia P/U**: Muestreo estratificado de Presencias ($P$) y Fondo no etiquetado ($U$) con ratio $P/U = 3$ (por cada celda positiva, 3 celdas de fondo).

---

## 2. Uso Previsto y Alcance Científico

### Usos Previstos
- **Priorización Espacial en Exploración Mineral**: Asignación de rangos relativos de favorabilidad geológica (**prospectivity/favorability scores**) sobre las 478.443 celdas de 1 km² que conforman el universo de soporte `eligible_approved_features` en el dominio peninsular modelado de España peninsular.
- **Delineación de Zonas de Prospectividad**: Identificación de clusters espaciales contiguos de alta favorabilidad (Top 1%, Top 5% del dominio peninsular modelado) para planificar campañas de reconocimiento de campo, prospección geoquímica y geofísica.
- **Análisis de Evidencia Geológica Multivariante**: Estudio de las contribuciones locales (log-odds) de litologías, cronoestratigrafía y relieve que diferencian distritos fértiles de terrenos estériles.

### Usos No Autorizados / Fuera de Alcance
- **Decisiones Directas de Sondeo**: El modelo opera a escala regional (1 km²); no sustituye el trabajo de geología de detalle ni la cartografía estructural a escala 1:5.000 o 1:1.000.
- **Cubicación o Estimación Económica de Recursos**: Las puntuaciones **no representan leyes de corte, tonelaje, recursos inferidos ni reservas minerales**.
- **Interpretación como "Probabilidad de Depósito"**: Los valores predichos son índices continuos en $(0, 1)$ derivados de un clasificador lineal entrenado sobre una muestra sintéticamente balanceada ($P/U=3$). **No están calibrados como probabilidades físicas o estadísticas absolutas**.
- **Extrapolación Territorial**: No debe aplicarse en territorio insular (Baleares, Canarias) ni fuera de la máscara canónica de soporte `eligible_approved_features`.

---

## 3. Datos de Entrada y Vector de Características

El modelo consume exactamente **56 predictores continuos aprobados** procedentes de fuentes cartográficas oficiales del IGME-CSIC y Copernicus DEM:

1. **Fracciones Litológicas (19 variables continuas)**: Fracción de área terrestre (0 a 1) ocupada por unidades del mapa geológico continuo 1:200.000 (granitoides de dos micas, otros granitoides, vulcanitas, pizarras y cuarcitas, rocas carbonatadas, evaporitas, etc.).
2. **Fracciones Cronoestratigráficas (27 variables continuas)**: Fracción de área (0 a 1) por época geológica (Proterozoico, Vendiense, Cámbrico, Ordovícico, Silúrico, Devónico, Carbonífero, Mesozoico, Cenozoico).
3. **Estructuras Geológicas (3 variables continuas)**: Distancias euclídeas en metros (truncadas a 10.000 m) a trazas de fallas cartografiadas, cabalgamientos y contactos intrusivos del mapa 1:1.000.000.
4. **Relieve y Morfometría (6 variables continuas)**: Elevación media ponderada (m), pendiente media (grados), Topographic Position Index a 1.000 m y 5.000 m (TPI), y desviación estándar de elevación a 1.000 m y 5.000 m (rugosidad regional).
5. **Hidrología (1 variable continua)**: Distancia euclídea al cauce más próximo de la red hidrográfica regional (m).

> [!CAUTION]
> **Anti-Leakage**: El vector de características $X$ excluyó de forma estricta cualquier proximidad a indicios minerales conocidos, nombres de mina, sustancias o asociaciones metalíferas.

---

## 4. Datos de Entrenamiento y Protocolo de Validación

### Muestra de Desarrollo (Fases B → F)
- **Territorio de Desarrollo**: 27 distritos metalogenéticos independientes, 464.902 celdas elegibles.
- **Positivos ($P$)**: 112 celdas de 1 km² correspondientes a 37 depósitos auríferos independientes del inventario auditado.
- **Fondo ($U$)**: 336 celdas terrestres muestreadas fuera del buffer de exclusión estricto de 5.000 m alrededor de los indicios conocidos.
- **Total Muestra de Ajuste**: 448 observaciones.

### Protocolo de Selección de Modelo (Fase F)
- **Nested Spatial Block CV**: 5 bloques espaciales externos (50 km $\times$ 50 km) con banda de exclusión de 5 km $\times$ 3 folds internos (15 particiones de ajuste interno).
- **Criterio de Elección**: Rendimiento medio en folds internos priorizando `deposit_recovery@5%` (recuperación de depósitos contando cada `deposit_id` una sola vez).

---

## 5. Rendimiento Cuantitativo y Evaluación Ciega

### 1. Estimación en Desarrollo (Nested Spatial CV, Fase F)
- **Selección Interna de Desarrollo**:
  - `deposit_recovery@5%`: $0,3206 \pm 0,1651$
  - `ROC-AUC`: $0,7357 \pm 0,0812$
- **Generalización OOF Folds Externos**:
  - `deposit_recovery@5%`: $0,4389 \pm 0,1804$
  - `ROC-AUC`: $0,7402 \pm 0,2054$
  - `deposit_recovery@10%`: $0,5500 \pm 0,2236$

### 2. Evaluación Ciega en Holdout (Fase G, Pre-registrado en Fase E)
- **Reserva Ciega**: 5 distritos completos aislados durante todo el modelado (13.541 celdas, 19 celdas $P$, 8 depósitos independientes).
- **Métricas Observadas**:
  - `deposit_recovery@1%`: **0,1250** (1 / 8 depósitos: Rodalquilar Cinto)
  - `deposit_recovery@5%`: **0,1250** (1 / 8 depósitos: Rodalquilar Cinto)
  - `deposit_recovery@10%`: **0,2500** (2 / 8 depósitos: Rodalquilar Cinto y La Oriental)
  - `cell_recovery@5%`: **0,1579** (3 / 19 celdas)
  - `cell_recovery@10%`: **0,2105** (4 / 19 celdas)
  - `ROC-AUC P/U`: **0,5807**
  - `PR-AUC (Average Precision)`: **0,0065** (prevalencia de test = 0,0014)

### 3. Brecha de Transferencia Observada ($N=8$)
La diferencia entre el rendimiento de validación cruzada en desarrollo (ROC-AUC 0,7402) y la evaluación ciega en holdout (ROC-AUC 0,5807) se define como la **brecha de transferencia observada ($N=8$)**. Se debe a la heterogeneidad metalogenética entre los distritos de desarrollo (mayoritariamente orogénicos y placer) y los distritos de holdout (donde confluyen epitermales en Cabo de Gata y leucogranitos hercínicos en Costa da Morte).

---

## 6. Interpretabilidad y Significado de Signos

### Especificación Estadística de Odds Ratio
En la formulación de la regresión logística sobre covariables estandarizadas ($z = (x - \mu)/\sigma$), **$\exp(\beta)$ representa el cambio en los odds por incremento de 1 desviación estándar ($+1\sigma$) de la covariable continua después del preprocesamiento con `StandardScaler`**.

### Coeficientes Lineales Clave
- **Mayores Pesos Positivos**: `edades_u023_fraccion` (+0,5962, OR=1,815), `litologia_u019_fraccion` (+0,4391, OR=1,551), `elevacion_media_m` (+0,3943, OR=1,483), `litologia_u008_fraccion` (+0,3817, OR=1,465), `litologia_u011_fraccion` (+0,3518, OR=1,422).
- **Mayores Pesos Negativos**: `dist_cauce_m` (-0,4482, OR=0,639), `litologia_u015_fraccion` (-0,3192, OR=0,727), `litologia_u005_fraccion` (-0,2729, OR=0,761), `tpi_5000m_m` (-0,2692, OR=0,764).

### Variables de Distancia y Advertencia de No Causalidad
- `dist_cauce_m` ($\beta = -0,4482$, OR=0,639 por $+1\sigma$): Negativo $\rightarrow$ mayor cercanía al cauce aumenta el score.
- `dist_contacto_intrusivo_cartografiada_m` ($\beta = -0,1335$, OR=0,875 por $+1\sigma$): Negativo $\rightarrow$ mayor cercanía a intrusiones aumenta el score.
- `dist_cabalgamiento_cartografiada_m` ($\beta = -0,0769$, OR=0,926 por $+1\sigma$): Negativo $\rightarrow$ mayor cercanía a cabalgamientos aumenta el score.
- `dist_falla_cartografiada_m` ($\beta = +0,2122$, OR=1,236 por $+1\sigma$): **Positivo** $\rightarrow$ mayor distancia euclídea a fallas cartografiadas aumenta matemáticamente el score en el ajuste multivariante condicionado.
  - **Hipótesis estadística y cartográfica (no mecanismo demostrado)**: Se formula como hipótesis que el signo positivo deriva de la colinealidad multivariante en la regresión regularizada L2 cuando conviven otras variables estructurales (cabalgamientos y contactos intrusivos con coeficientes negativos), combinado con posibles artefactos de escala cartográfica (1:1.000.000) y la concentración del muestreo de fondo $U$ en zonas montañosas con densa fracturación cartografiada regional. **Bajo ningún concepto debe interpretarse como un mecanismo físico o metalogenético demostrado** que indique que la mineralización aurífera eluda las fallas.

---

## 7. Limitaciones y Consideraciones Éticas

- **Tamaño Muestral ($N=45$ depósitos modelables)**: La base empírica de depósitos confirmados en el inventario auditado de España peninsular es reducida.
- **Poder Estadístico en Test ($N=8$ depósitos)**: Intervalos de confianza bootstrap del 95% para `deposit_recovery@5%`: $[0,00\%, 37,50\%]$.
- **Ausencia de Geoquímica**: El modelo no incluye capas geoquímicas aprobadas (As, Sb, Bi) por falta de cobertura analítica homogénea continua.
- **Anotación Post-Hoc**: La cercanía a minas históricas en el ranking de zonas es una anotación descriptiva posterior y nunca intervino en la inferencia del modelo.
