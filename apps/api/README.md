# GeoAI-Au Explorer — Backend API

Backend de servicios geoespaciales, analíticos y de explicabilidad para **GeoAI-Au Explorer**, desarrollado con **FastAPI**, **Rasterio**, **PyArrow** y **Scikit-learn**.

## 1. Misión y Principios
- Opera estrictamente en modo **READ-ONLY** sobre los artefactos científicos sellados de GeoAI-Au v1.0.
- Sirve teselas ráster Web Mercator dinámicas directamente desde los Cloud Optimized GeoTIFFs (COGs).
- Resuelve búsquedas e inspección espacial de celdas en tiempo determinista $O(1)$ sin escanear el conjunto de datos.
- Proporciona explicabilidad local aditiva exacta ($\beta \cdot z$) verificada contra `decision_function` del modelo lineal.
- Cumple rigurosamente los guardarraíles metodológicos: prohíbe el uso del término "probabilidad de depósito" o "probabilidad de oro".

## 2. Endpoints Principales

### Resumen del Sistema y Capas
- `GET /api/health`: Estado de salud, verificación de integridad y número de celdas indexadas.
- `GET /api/project/summary`: Metadatos globales (modelo, resolución 1 km, 478.443 celdas, 56 predictores, umbrales de corte).
- `GET /api/layers`: Catálogo de capas para MapLibre con configuración de leyendas y estilos.

### Inspección Espacial y Explicabilidad
- `GET /api/cell/by-coordinate?lat={lat}&lon={lon}`: Inspección territorial por coordenadas WGS84 en $O(1)$.
- `GET /api/cell/{cell_id}`: Datos detallados de la celda de 1 km².
- `GET /api/cell/{cell_id}/explain`: Descomposición aditiva exacta $\text{logit} = \text{intercept} + \sum \beta_i \cdot z_i$ con factores positivos y negativos.

### Zonas de Prospectividad (Targets)
- `GET /api/targets`: Lista filtrable y paginada de las 1.529 zonas de priorización (Top 1% y Top 5%).
- `GET /api/targets/{zona_id}`: Ficha técnica y estadísticas de una zona específica.
- `GET /api/targets/geojson`: GeoJSON WGS84 de los polígonos de las 1.529 zonas.

### Validación Ciega (Fase G)
- `GET /api/validation/summary`: Métricas globales del holdout (Recovery@1/5/10%, ROC-AUC, PR-AUC, intervalos bootstrap al 95%).
- `GET /api/validation/deposits`: Desglose individual de los 8 depósitos del test ciego.
- `GET /api/validation/districts`: Desglose de los 5 distritos en cuarentena.
- `GET /api/validation/comparison`: Comparativa entre validación cruzada en desarrollo y evaluación territorial en holdout.

### Cartografía y Teselas Ráster COG
- `GET /api/tiles/score/{z}/{x}/{y}.png`: Teselas del score continuo de prospectividad (coloreado Viridis).
- `GET /api/tiles/percentile/{z}/{x}/{y}.png`: Teselas del percentil territorial nacional (coloreado Plasma).
- `GET /api/tiles/priority/{z}/{x}/{y}.png`: Teselas de bandas operativas de exploración (Top 1%, Top 1-5%, Top 5-10%).
- `GET /api/deposits`: GeoJSON WGS84 de los 46 depósitos minerales confirmados (Fase B).

### Copiloto Asistido
- `POST /api/copilot/query`: Asistente determinista que responde consultas geocientíficas basándose exclusivamente en los datos del proyecto.

## 3. Puesta en Marcha Local

```bash
# 1. Instalar dependencias (si no se tienen)
pip install fastapi uvicorn pydantic rasterio shapely pyproj pyarrow geopandas scikit-learn

# 2. Generar artefactos de caché web de alto rendimiento (si es primera vez)
python scripts/build_web_cache.py

# 3. Arrancar servidor de desarrollo
cd apps/api
uvicorn main:app --reload --port 8000
```

Documentación interactiva disponible en: `http://localhost:8000/api/docs`.
