# Arquitectura del Sistema: GeoAI-Au Explorer
### Mineral Prospectivity Intelligence — España Peninsular

## 1. Visión General y Filosofía de Diseño

**GeoAI-Au Explorer** es una plataforma web geoespacial interactiva de nivel profesional, diseñada bajo el paradigma de *GeoAI Command Center*. La aplicación proporciona una interfaz de usuario fluida, analíticamente densa y visualmente atractiva para explorar los resultados del modelo de inteligencia artificial de prospectividad aurífera **GeoAI-Au v1.0**.

El sistema se estructura en dos capas principales desacopladas:
1. **Backend de Servicios Geoespaciales y Analíticos (FastAPI + Python)**: Procesa rásteres COG, sirve teselas cartográficas dinámicas en Web Mercator, resuelve consultas territoriales espaciales en $O(1)$, calcula descomposiciones aditivas exactas de explicabilidad ($\beta \cdot z$) y sirve metadatos de validación científica.
2. **Frontend Interactivo de Comando GeoAI (Next.js + TypeScript + MapLibre GL + TailwindCSS)**: Interfaz de usuario con mapa a pantalla completa, panel izquierdo de control de capas y mapa base, panel inferior de inspección territorial y panel derecho con pestañas de Explicabilidad, Targets priorizados, Validación ciega y Copiloto asistido.

```mermaid
flowchart TB
    subgraph DataSources["Artefactos Científicos Sellados (Read-Only)"]
        FaseH["Fase H: COG Rasters, GeoParquet, GeoPackage, Targets CSV"]
        FaseG["Fase G: Holdout Metrics, Bootstrap JSON, Comparison CSV"]
        FaseF["Fase F: final_validated_model.joblib"]
        FaseD["Fase D: Grid Spec, Feature Dictionary, X_features"]
        FaseB["Fase B: Inventario Depósitos Auditados BDMIN"]
    end

    subgraph Backend["FastAPI Backend (apps/api)"]
        TileEngine["Motor de Teselas Ráster COG (WarpedVRT + PIL)"]
        SpatialIndex["Resolutor Determinista de Celdas O(1)"]
        ExplainEngine["Motor de Explicabilidad Aditiva Exacta (β · z)"]
        CopilotEngine["GeoAI Copilot Determinista"]
        DataCache["Caché de Derivados (apps/api/data_cache/)"]
    end

    subgraph Frontend["Next.js Frontend (apps/web)"]
        MapLibre["MapLibre GL Canvas (Vector + Raster Tiles)"]
        LayerControl["Panel de Capas y Opacidad"]
        Inspector["Inspector Territorial de Celda"]
        Tabs["Panel Derecho: Explicabilidad | Targets | Validación | Copiloto"]
        Guardrails["Guardarraíles Científicos y Modal de Metodología"]
    end

    DataSources --> Backend
    TileEngine -->|/api/tiles/{layer}/{z}/{x}/{y}.png| MapLibre
    SpatialIndex -->|/api/cell/by-coordinate| Inspector
    ExplainEngine -->|/api/cell/{cell_id}/explain| Tabs
    Backend -->|JSON APIs| Tabs
    MapLibre -->|Click Event (lat, lon)| Inspector
```

---

## 2. Flujo de Datos y Operaciones Clave

### 2.1. Consulta e Inspección Territorial en $O(1)$
1. El usuario hace clic en cualquier punto del mapa en el frontend.
2. MapLibre emite un evento `click` con coordenadas geográficas WGS84 `(lng, lat)`.
3. El frontend invoca `GET /api/cell/by-coordinate?lat={lat}&lon={lon}`.
4. El backend proyecta `(lng, lat)` a `(x, y)` en `EPSG:25830` mediante `pyproj`.
5. Utilizando los parámetros exactos de `grid_spec.json` (`origin_x = -50000`, `origin_y = 4860000`, `resolution = 1000`):
   $$\text{col} = \lfloor (x - \text{origin\_x}) / 1000 \rfloor$$
   $$\text{row} = \lfloor (\text{origin\_y} - y) / 1000 \rfloor$$
   $$\text{cell\_id} = \text{f"es\_pen\_utm30\_1km\_v1\_r\{row:04d\}\_c\{col:04d\}"}$$
6. El backend consulta el registro en la memoria indexada (`mapa_nacional_prospectividad.geoparquet`) en $< 0,1$ ms:
   - Si la celda no es elegible o cae en mar, devuelve `eligible: false` y coordenadas.
   - Si la celda es elegible, devuelve: `score`, `percentile_favorabilidad`, `prioridad_banda`, `land_area_m2`, `distrito_id` y `deposito_id` (si coincide).

### 2.2. Explicabilidad Local Aditiva Exacta ($\beta \cdot z$)
Para cualquier celda elegible seleccionada, el backend computa la descomposición exacta del clasificador lineal congelado:
1. Recupera el vector $x \in \mathbb{R}^{56}$ con los valores brutos de las 56 variables aprobadas.
2. Aplica la imputación por mediana y el escalador estándar `StandardScaler` del pipeline congelado `final_validated_model.joblib`:
   $$z_i = \frac{x_i - \mu_i}{\sigma_i}$$
3. Multiplica por el coeficiente estandarizado del modelo logístico:
   $$c_i = \beta_i \cdot z_i$$
4. Verifica en tiempo de ejecución la igualdad matemática estricta:
   $$| \text{intercept} + \sum_{i=1}^{56} c_i - \text{model.decision\_function}(x) | < 10^{-7}$$
   $$\sigma(\text{logit}) = \frac{1}{1 + e^{-\text{logit}}} \approx \text{score}$$
5. Clasifica las contribuciones en **Factores que aumentan la favorabilidad** ($c_i > 0$) y **Factores que reducen la favorabilidad** ($c_i < 0$), enriqueciéndolas con el significado geológico del diccionario de variables.

### 2.3. Sistema de Teselas Ráster Dinámicas
- Los mapas continuos de *Prospectivity Score*, *Percentil Territorial* y *Bandas Prioritarias* se sirven mediante el endpoint `/api/tiles/{layer}/{z}/{x}/{y}.png`.
- Utiliza `rasterio.vrt.WarpedVRT` para reproyectar en memoria desde `EPSG:25830` a Web Mercator (`EPSG:3857`) por demanda de cuadrante.
- Aplica una rampa de color perceptual (Viridis para score, Plasma para percentil, paleta discreta normalizada para bandas).
- Tiempos de renderizado por tesela: $\approx 10\text{--}15$ ms gracias a la estructura Cloud Optimized GeoTIFF (tiling interno $512 \times 512$ y pirámides de resolución `[2, 4]`).

---

## 3. Especificación de Endpoints del Backend (FastAPI)

| Método | Ruta | Descripción | Parámetros | Respuesta Principal |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Estado del servicio y verificación de integridad | Ninguno | `{"status": "healthy", "version": "v1.0", "sources_verified": true}` |
| `GET` | `/api/project/summary` | Metadatos globales del experimento | Ninguno | Modelo, celdas elegibles (478.443), umbrales canónicos, distritos, fecha. |
| `GET` | `/api/layers` | Catálogo de capas disponibles y configuración de leyendas | Ninguno | Identificadores, nombres, tipos (raster/vector), rangos, paletas de color. |
| `GET` | `/api/cell/by-coordinate` | Inspección territorial por latitud y longitud | `lat` (float), `lon` (float) | Atributos de celda, elegibilidad, score, percentil, banda, distrito. |
| `GET` | `/api/cell/{cell_id}` | Inspección territorial por identificador de celda | `cell_id` (str) | Atributos detallados de la celda de 1 km². |
| `GET` | `/api/cell/{cell_id}/explain` | Descomposición aditiva local $\beta \cdot z$ | `cell_id` (str) | Contribuciones positivas, negativas, logit, intercepto, test de consistencia. |
| `GET` | `/api/targets` | Lista filtrable de las 1.529 zonas priorizadas | `categoria`, `min_score`, `distrito`, `sin_deposito_cercano` | GeoJSON o lista tabular de zonas ordenadas por ranking nacional. |
| `GET` | `/api/targets/{zona_id}` | Ficha monográfica de una zona de prospectividad | `zona_id` (str) | Estadísticos de zona, ranking, celdas, polígono y depósito histórico próximo. |
| `GET` | `/api/validation/summary` | Resumen de la evaluación ciega en holdout | Ninguno | Recovery@1/5/10%, ROC-AUC, PR-AUC, N=8 depósitos, N=5 distritos. |
| `GET` | `/api/validation/deposits` | Rendimiento desglosado por depósito de test | Ninguno | Tabla de los 8 depósitos del holdout y su detección por percentil. |
| `GET` | `/api/validation/districts` | Rendimiento desglosado por distrito reservado | Ninguno | Tabla de los 5 distritos del holdout. |
| `GET` | `/api/model/coefficients` | Coeficientes estandarizados globales del modelo | Ninguno | Las 56 variables, familia, $\beta$, odds ratio, impacto y descripción. |
| `GET` | `/api/deposits` | GeoJSON de los 46 depósitos minerales auditados | Ninguno | FeatureCollection con puntos WGS84, `deposit_id`, `district_id`, `tipo_au`. |
| `GET` | `/api/tiles/{layer}/{z}/{x}/{y}.png` | Teselas ráster dinámicas en Web Mercator | `layer` (`score`, `percentile`, `priority`), `z`, `x`, `y` | Imagen PNG $256 \times 256$ con canal alfa (transparente en NoData). |
| `POST` | `/api/copilot/query` | Consultas predefinidas del copiloto determinista | `{"query": str, "context": dict}` | Respuesta basada en datos científicos reales y enlaces de acción en UI. |

---

## 4. Guardarraíles Científicos y Principios de Integridad en la UI

1. **Aviso Permanente en el Header / Footer**:
   > *"GeoAI-Au es un sistema regional de priorización territorial. Las puntuaciones representan índices relativos de favorabilidad geológica y no constituyen estimaciones de recursos, reservas ni probabilidades físicas de existencia de oro."*
2. **Nomenclatura Controlada**:
   - `Prospectivity Score` / `Favorability Score` / `Score de Favorabilidad`.
   - **Terminantemente prohibido**: usar "probabilidad de depósito", "probabilidad de encontrar oro" o formatos porcentuales de probabilidad (e.g. "95% de probabilidad").
3. **Anotación Post-Hoc de Depósitos**:
   - Las distancias a depósitos históricos mostradas en la tabla de targets se marcan visiblemente como `Anotación geográfica post-hoc: no intervino en el entrenamiento del modelo`.
4. **Modal de Metodología y Limitaciones**:
   - Acceso permanente en la barra superior a la documentación formal consumiendo [`MODEL_CARD.md`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/MODEL_CARD.md), [`DATA_CARD.md`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/DATA_CARD.md) y [`LIMITATIONS.md`](file:///c:/Users/mdmat/Desktop/programacion/GeoAI/LIMITATIONS.md).

---

## 5. Instrucciones de Ejecución Local

### 5.1. Variables de Entorno

Crear un fichero `.env` en la raíz del proyecto (o en `apps/api/.env` y `apps/web/.env.local`):

```bash
# Backend (apps/api)
PORT=8000
HOST=127.0.0.1
CORS_ORIGINS=http://localhost:3000

# Frontend (apps/web)
NEXT_PUBLIC_API_URL=http://localhost:8000
# Opcional: clave para mapas satélite/callejero privados (si no se proporciona, se activa fallback libre CartoDB Dark/OSM)
NEXT_PUBLIC_MAPTILER_KEY=
```

### 5.2. Puesta en Marcha

1. **Verificación Previa de Fuentes Científicas**:
   ```bash
   python scripts/verify_dashboard_sources.py
   ```
2. **Arranque del Backend FastAPI**:
   ```bash
   cd apps/api
   uvicorn main:app --reload --port 8000
   ```
3. **Arranque del Frontend Next.js**:
   ```bash
   cd apps/web
   npm install
   npm run dev
   ```
4. Abrir en el navegador: `http://localhost:3000`.
