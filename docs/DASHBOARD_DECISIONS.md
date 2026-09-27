# Registro de Decisiones Técnicas y de Diseño: GeoAI-Au Explorer

Este documento registra las decisiones arquitectónicas, de ingeniería geoespacial y de producto adoptadas durante la concepción y desarrollo de **GeoAI-Au Explorer**.

---

## DEC-001: Inmutabilidad Estricta de la Cadena Científica B → H
- **Contexto**: El proyecto GeoAI-Au v1.0 cuenta con una cadena científica auditada y sellada criptográficamente (Fases B, C, D, E, F, G y H).
- **Decisión**: Los directorios `reports/` y `data/review/` se declaran estrictamente de solo lectura (**READ-ONLY**). Ningún proceso del dashboard web puede escribir, modificar o reentrenar modelos.
- **Consecuencia**: Toda optimización necesaria para la aplicación web se generará exclusivamente en directorios derivados claramente catalogados (`apps/api/data_cache/`). Se implementa un script de verificación previo [`scripts/verify_dashboard_sources.py`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/scripts/verify_dashboard_sources.py) que aborta la compilación o arranque si se detecta cualquier alteración en los hashes SHA-256 de los artefactos sellados.

---

## DEC-002: Resolución Espacial Determinista $O(1)$ de Celdas
- **Contexto**: El universo de modelado abarca 478.443 celdas de 1 km² en la proyección oficial `EPSG:25830`. Realizar un escaneo tabular o una búsqueda en árbol espacial (RTree) para cada clic del usuario introduciría latencias innecesarias de decenas o cientos de milisegundos.
- **Decisión**: Aprovechar la regularidad matemática de la malla territorial definida en `grid_spec.json` (`origin_x = -50000`, `origin_y = 4860000`, `resolution = 1000`).
- **Implementación**:
  $$\text{col} = \lfloor (x - (-50000)) / 1000 \rfloor$$
  $$\text{row} = \lfloor (4860000 - y) / 1000 \rfloor$$
  $$\text{cell\_id} = \text{f"es\_pen\_utm30\_1km\_v1\_r\{row:04d\}\_c\{col:04d\}"}$$
- **Consecuencia**: La identificación de la celda inspeccionada se realiza en tiempo $O(1)$ ($< 0,05$ milisegundos), permitiendo una interacción ultrafluida en el mapa.

---

## DEC-003: Explicabilidad Aditiva Local Exacta ($\beta \cdot z$) sin SHAP
- **Contexto**: El modelo de producción congelado (`logistic_01`) es una Regresión Logística regularizada ($L2$, $C=0,1$). El usuario requiere entender los factores geológicos específicos que explican la favorabilidad asignada a cada celda.
- **Decisión**: Emplear la formulación aditiva exacta en el espacio logit:
  $$\text{logit}(x) = \text{intercept} + \sum_{i=1}^{56} \beta_i \cdot z_i$$
  donde $z_i$ representa la covariable estandarizada con `StandardScaler`.
- **Justificación**: En modelos lineales, la descomposición $\beta_i \cdot z_i$ es matemáticamente exacta, determinista y equivale analíticamente a los valores SHAP sin necesidad de muestreos costosos ni aproximaciones estocásticas. Además, se añade un test de aserción en runtime que verifica que la suma reproduce exactamente `decision_function(x)` y que $\sigma(\text{logit}) \approx \text{score}$ con error numérico $< 10^{-7}$.

---

## DEC-004: Servicio Dinámico de Teselas Ráster COG en Backend
- **Contexto**: Enviar 478.443 polígonos o puntos en formato GeoJSON al navegador colapsaría el hilo principal de JavaScript y consumiría más de 100 MB de transferencia por carga.
- **Decisión**: Los mapas continuos de favorabilidad, percentil y bandas prioritarias se sirven como teselas ráster PNG de $256 \times 256$ píxeles mediante un endpoint ligero en FastAPI (`/api/tiles/{layer}/{z}/{x}/{y}.png`).
- **Implementación**: Se utiliza `rasterio.vrt.WarpedVRT` para la reproyección al vuelo a Web Mercator (`EPSG:3857`) aprovechando la estructura interna piramidal de los Cloud Optimized GeoTIFF (COG). Los píxeles NoData (`-9999.0`) se mapean con canal alfa 0 (completamente transparentes).
- **Rendimiento**: Latencia media por cuadrante $< 15$ ms.

---

## DEC-005: Caché de Derivados para Rendimiento Web
- **Contexto**: `X_features.parquet` tiene 496.855 filas y 169 columnas (65 MB). Cargar todas las columnas para una sola celda resulta ineficiente.
- **Decisión**: Crear en `apps/api/data_cache/`:
  1. `features_approved_56.parquet`: Sólo las 56 columnas aprobadas indexadas por `cell_id`.
  2. `zonas_prospectividad_4326.geojson`: Polígonos de las 1.529 zonas en WGS84 para visualización vectorial en MapLibre.
  3. `depositos_confirmados_4326.geojson`: 46 depósitos confirmados de Fase B con coordenadas WGS84 y tipología.
- **Garantía**: Estos ficheros se documentan formalmente como artefactos derivados de rendimiento y su generación es 100% reproducible a partir de las fuentes canónicas selladas.

---

## DEC-006: Guardarraíles Científicos contra la "Probabilidad de Oro"
- **Contexto**: En el marco de Positive-Unlabeled (PU) Learning con ratio de muestreo sintético $P/U=3$, las probabilidades predichas por la función sigmoide reflejan favorabilidad relativa, no la prevalencia física real de mineralización aurífera en la corteza terrestre (que es inferior al 0,05%).
- **Decisión**: La interfaz y los esquemas Pydantic de la API prohíben taxativamente términos como "probabilidad de depósito" o "probabilidad de encontrar oro". La métrica se denomina siempre `Prospectivity Score`, `Favorability Score` o `Score de favorabilidad`. Se incorpora un descargo científico explícito en la UI y en las respuestas de la API.

---

## DEC-007: Arquitectura de Copiloto Determinista Desacoplada (`CopilotProvider`)
- **Contexto**: Se requiere una interfaz de copiloto inteligente en el panel derecho sin riesgo de alucinaciones geológicas ni dependencia inicial de servicios de LLM externos.
- **Decisión**: Implementar un `CopilotProvider` basado en una máquina de estados y consultas estructuradas predefinidas que resuelven preguntas geocientíficas directas ("¿Por qué esta celda tiene score alto?", "¿Cuáles son los targets Top 1%?", "¿Qué ocurrió en el holdout?") consultando estrictamente los datos verificados del modelo. La arquitectura queda desacoplada mediante una interfaz que permitirá conectar futuros modelos RAG sin modificar el frontend.
