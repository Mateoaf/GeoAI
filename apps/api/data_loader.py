"""
apps/api/data_loader.py
Carga en memoria y cacheo de alta velocidad de los artefactos científicos de GeoAI-Au v1.0.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import joblib
from pyproj import Transformer

from . import config

logger = logging.getLogger("geoau_api.data_loader")

# Asegurar importación de geoau para unpickling de FeatureGuard
if str(config.REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(config.REPO_ROOT / "src"))


class DataLoader:
    _instance: Optional["DataLoader"] = None

    def __init__(self):
        self.grid_spec: Dict[str, Any] = {}
        self.origin_x: float = -50000.0
        self.origin_y: float = 4860000.0
        self.resolution_m: float = 1000.0
        self.width: int = 1100
        self.height: int = 910

        self.control_cierre: Dict[str, Any] = {}
        self.approved_columns: list = []
        self.feature_dictionary: Dict[str, Any] = {}
        self.coefficients_df: Optional[pd.DataFrame] = None
        self.targets_df: Optional[pd.DataFrame] = None
        self.casos_estudio_df: Optional[pd.DataFrame] = None

        self.validation_summary: Dict[str, Any] = {}
        self.validation_deposits_df: Optional[pd.DataFrame] = None
        self.validation_districts_df: Optional[pd.DataFrame] = None
        self.validation_comparison_df: Optional[pd.DataFrame] = None
        self.validation_bootstrap: Dict[str, Any] = {}

        self.depositos_geojson: Dict[str, Any] = {}
        self.zonas_geojson: Dict[str, Any] = {}

        self.model: Any = None
        self.model_meta: Dict[str, Any] = {}

        # Lookups espaciales ultrarrápidos O(1)
        self.cell_lookup: Dict[str, Dict[str, Any]] = {}
        self.rel_deposit_by_cell: Dict[str, str] = {}
        self.rel_district_by_cell: Dict[str, str] = {}
        self.features_df: Optional[pd.DataFrame] = None

        # Transformadores de coordenadas
        self.proj_to_25830 = Transformer.from_crs("EPSG:4326", "EPSG:25830", always_xy=True)
        self.proj_to_4326 = Transformer.from_crs("EPSG:25830", "EPSG:4326", always_xy=True)

    @classmethod
    def get_instance(cls) -> "DataLoader":
        if cls._instance is None:
            cls._instance = DataLoader()
            cls._instance.load_all()
        return cls._instance

    def load_all(self):
        logger.info("Cargando artefactos científicos canónicos en memoria...")

        # 1. Grid Spec
        with open(config.PATH_GRID_SPEC, "r", encoding="utf-8") as f:
            self.grid_spec = json.load(f)
            self.origin_x = float(self.grid_spec["origin_x"])
            self.origin_y = float(self.grid_spec["origin_y"])
            self.resolution_m = float(self.grid_spec["resolution_m"])
            self.width = int(self.grid_spec["width"])
            self.height = int(self.grid_spec["height"])

        # 2. Control de Cierre Fase H
        with open(config.PATH_CONTROL_CIERRE, "r", encoding="utf-8") as f:
            self.control_cierre = json.load(f)

        # 3. Allowlist de características aprobadas (56)
        with open(config.PATH_ALLOWLIST, "r", encoding="utf-8") as f:
            self.approved_columns = json.load(f)["approved_training_columns"]

        # 4. Diccionario de variables
        df_dict = pd.read_csv(config.PATH_FEATURE_DICT)
        self.feature_dictionary = df_dict.set_index("name").to_dict(orient="index")

        # 5. Coeficientes estandarizados
        self.coefficients_df = pd.read_csv(config.PATH_COEFS_CSV)

        # 6. Targets de priorización (1.529)
        self.targets_df = pd.read_csv(config.PATH_TARGETS_CSV)

        # 7. Casos de estudio
        if config.PATH_CASOS_CSV.exists():
            self.casos_estudio_df = pd.read_csv(config.PATH_CASOS_CSV)

        # 8. Métricas de validación ciega (Fase G)
        with open(config.PATH_HOLDOUT_OVERALL, "r", encoding="utf-8") as f:
            self.validation_summary = json.load(f)

        self.validation_deposits_df = pd.read_csv(config.PATH_HOLDOUT_DEPOSITS)
        self.validation_districts_df = pd.read_csv(config.PATH_HOLDOUT_DISTRICTS)
        self.validation_comparison_df = pd.read_csv(config.PATH_COMPARISON_DEV_HOLD)

        with open(config.PATH_BOOTSTRAP, "r", encoding="utf-8") as f:
            self.validation_bootstrap = json.load(f)

        # 9. GeoJSON de depósitos confirmados y zonas (con auto-generación si falta)
        if not (config.PATH_CACHE_DEPOSITOS_GEOJSON.exists() and config.PATH_CACHE_ZONAS_GEOJSON.exists() and config.PATH_CACHE_FEATURES.exists()):
            logger.info("Caché derivado no encontrado o incompleto. Generando mediante build_all_cache()...")
            from scripts.build_web_cache import build_all_cache
            build_all_cache()

        with open(config.PATH_CACHE_DEPOSITOS_GEOJSON, "r", encoding="utf-8") as f:
            self.depositos_geojson = json.load(f)

        with open(config.PATH_CACHE_ZONAS_GEOJSON, "r", encoding="utf-8") as f:
            self.zonas_geojson = json.load(f)

        # 10. Relaciones de celda a depósito / distrito
        df_rel_dep = pq.read_table(config.PATH_REL_DEPOSIT).to_pandas()
        self.rel_deposit_by_cell = dict(zip(df_rel_dep["cell_id"], df_rel_dep["deposit_id"]))

        df_rel_dist = pq.read_table(config.PATH_REL_DISTRICT).to_pandas()
        self.rel_district_by_cell = dict(zip(df_rel_dist["cell_id"], df_rel_dist["district_id"]))

        # 11. Modelo serializado de Fase F
        self.model = joblib.load(config.PATH_MODEL)
        with open(config.PATH_MODEL_JSON, "r", encoding="utf-8") as f:
            self.model_meta = json.load(f)

        # 12. Cargar celdas de prospectividad para consulta espacial O(1)
        logger.info("Indexando 478.443 celdas de mapa_nacional_prospectividad.geoparquet...")
        df_geo = pq.read_table(
            config.PATH_GEOPARQUET,
            columns=["cell_id", "row", "col", "score", "percentile_favorabilidad", "prioridad_banda", "land_area_m2"]
        ).to_pandas()

        # Construir índice diccionario cell_id -> dict
        for row in df_geo.itertuples(index=False):
            cid = row.cell_id
            x_cent = self.origin_x + row.col * self.resolution_m + (self.resolution_m / 2.0)
            y_cent = self.origin_y - row.row * self.resolution_m - (self.resolution_m / 2.0)
            lon_cent, lat_cent = self.proj_to_4326.transform(x_cent, y_cent)

            self.cell_lookup[cid] = {
                "cell_id": cid,
                "row": int(row.row),
                "col": int(row.col),
                "score": float(row.score),
                "percentile_favorabilidad": float(row.percentile_favorabilidad),
                "prioridad_banda": str(row.prioridad_banda),
                "land_area_m2": float(row.land_area_m2),
                "x_epsg25830": round(x_cent, 1),
                "y_epsg25830": round(y_cent, 1),
                "lon_wgs84": round(lon_cent, 6),
                "lat_wgs84": round(lat_cent, 6),
                "deposit_id": self.rel_deposit_by_cell.get(cid),
                "district_id": self.rel_district_by_cell.get(cid)
            }

        # 13. Cargar características aprobadas (caché derivado de alto rendimiento)
        logger.info("Cargando features_approved_56.parquet...")
        self.features_df = pd.read_parquet(config.PATH_CACHE_FEATURES).set_index("cell_id")

        logger.info("Carga en memoria completada exitosamente.")

    def coordinate_to_cell_id(self, lat: float, lon: float) -> Optional[str]:
        """Proyecta (lat, lon) WGS84 a celda EPSG:25830 en tiempo O(1)."""
        x, y = self.proj_to_25830.transform(lon, lat)
        col = int((x - self.origin_x) // self.resolution_m)
        row = int((self.origin_y - y) // self.resolution_m)

        if 0 <= col < self.width and 0 <= row < self.height:
            cell_id = f"es_pen_utm30_1km_v1_r{row:04d}_c{col:04d}"
            return cell_id
        return None

    def get_cell_info(self, cell_id: str) -> Optional[Dict[str, Any]]:
        return self.cell_lookup.get(cell_id)


def get_data_loader() -> DataLoader:
    return DataLoader.get_instance()
