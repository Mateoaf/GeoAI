FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema requeridas por rasterio y GDAL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements de GeoAI
COPY pyproject.toml .
RUN pip install --no-cache-dir fastapi uvicorn rasterio geopandas pandas pyarrow shapely scikit-learn pydantic pyproj matplotlib pillow

# Copiar código del proyecto
COPY . /app

EXPOSE 8000

ENV PYTHONPATH=/app
CMD ["python", "-m", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
