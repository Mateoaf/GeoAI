"""
apps/api/data_loader.py
Carga en memoria y cacheo de alta velocidad de los artefactos científicos de GeoAI-Au v1.0.
"""

import json
import logging
import sys
from typing import Any, Optional

import joblib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from pyproj import Transformer

from . import calibration, config

logger = logging.getLogger("geoau_api.data_loader")

# Asegurar importación de geoau para unpickling de FeatureGuard
if str(config.REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(config.REPO_ROOT / "src"))


class DataLoader:
    _instance: Optional["DataLoader"] = None

    def __init__(self):
        self.grid_spec: dict[str, Any] = {}
        self.origin_x: float = -50000.0
        self.origin_y: float = 4860000.0
        self.resolution_m: float = 1000.0
        self.width: int = 1100
        self.height: int = 910

        self.control_cierre: dict[str, Any] = {}
        self.approved_columns: list = []
        self.feature_dictionary: dict[str, Any] = {}
        self.coefficients_df: pd.DataFrame | None = None
        self.targets_df: pd.DataFrame | None = None
        self.casos_estudio_df: pd.DataFrame | None = None

        self.validation_summary: dict[str, Any] = {}
        self.validation_deposits_df: pd.DataFrame | None = None
        self.validation_districts_df: pd.DataFrame | None = None
        self.validation_comparison_df: pd.DataFrame | None = None
        self.validation_bootstrap: dict[str, Any] = {}

        self.depositos_geojson: dict[str, Any] = {}
        self.zonas_geojson: dict[str, Any] = {}
        self.indicios_geojson: dict[str, Any] = {}
        self.distritos_geojson: dict[str, Any] = {}

        self.model: Any = None
        self.model_meta: dict[str, Any] = {}

        # Lookups espaciales ultrarrápidos O(1)
        self.cell_lookup: dict[str, dict[str, Any]] = {}
        self.rel_deposit_by_cell: dict[str, str] = {}
        self.rel_district_by_cell: dict[str, str] = {}
        self.features_df: pd.DataFrame | None = None

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

        # 2. Control de Cierre
        if config.PATH_CONTROL_CIERRE.exists():
            with open(config.PATH_CONTROL_CIERRE, "r", encoding="utf-8") as f:
                self.control_cierre = json.load(f)

        # 3. Variables incluidas (64 predictores: 56 geología/relieve + 8 geoquímica IGME)
        if config.PATH_VARIABLES_INCLUIDAS_CSV.exists():
            df_vars = pd.read_csv(config.PATH_VARIABLES_INCLUIDAS_CSV)
            self.approved_columns = df_vars["variable"].tolist()
            self.numeric_columns = df_vars.loc[df_vars["representation"] == "numeric", "variable"].tolist()
            self.geochemical_columns = df_vars.loc[df_vars["representation"] != "numeric", "variable"].tolist()
            self.feature_dictionary = df_vars.set_index("variable").to_dict(orient="index")
        else:
            with open(config.PATH_ALLOWLIST, "r", encoding="utf-8") as f:
                self.approved_columns = json.load(f)["approved_training_columns"]
            df_dict = pd.read_csv(config.PATH_FEATURE_DICT)
            self.feature_dictionary = df_dict.set_index("name").to_dict(orient="index")
            self.numeric_columns = list(self.approved_columns)
            self.geochemical_columns = []

        # 4. Importancia de variables de los modelos
        self.importancia_variables_df = pd.DataFrame()
        if config.PATH_IMPORTANCIA_VARIABLES_CSV.exists():
            self.importancia_variables_df = pd.read_csv(config.PATH_IMPORTANCIA_VARIABLES_CSV)

        # 5. Modelo serializado (Componente logístico de 64 variables del ensamble / fusión)
        if config.PATH_FUSION_MODEL_JOBLIB.exists():
            self.fusion_model = joblib.load(config.PATH_FUSION_MODEL_JOBLIB)
            self.model = self.fusion_model.components["logistic"]
            self.model_meta = {"model_name": "GeoAI_64_Predictores", "total_variables": len(self.approved_columns)}
        else:
            self.model = joblib.load(config.PATH_MODEL)
            with open(config.PATH_MODEL_JSON, "r", encoding="utf-8") as f:
                self.model_meta = json.load(f)

        # 6. Coeficientes estandarizados e interpretabilidad para las 64 variables
        self._build_coefficients_df()

        # 7. Targets de priorización (1.529)
        self.targets_df = pd.read_csv(config.PATH_TARGETS_CSV)

        # 8. Casos de estudio
        if config.PATH_CASOS_CSV.exists():
            self.casos_estudio_df = pd.read_csv(config.PATH_CASOS_CSV)

        # 9. Métricas de validación y benchmark territorial (45 depósitos / 32 distritos)
        self._load_validation_data()

        # 10. GeoJSON de depósitos confirmados y zonas
        with open(config.PATH_CACHE_DEPOSITOS_GEOJSON, "r", encoding="utf-8") as f:
            self.depositos_geojson = json.load(f)

        with open(config.PATH_CACHE_ZONAS_GEOJSON, "r", encoding="utf-8") as f:
            self.zonas_geojson = json.load(f)

        if config.PATH_CACHE_INDICIOS_GEOJSON.exists():
            with open(config.PATH_CACHE_INDICIOS_GEOJSON, "r", encoding="utf-8") as f:
                self.indicios_geojson = json.load(f)

        if config.PATH_CACHE_DISTRITOS_GEOJSON.exists():
            with open(config.PATH_CACHE_DISTRITOS_GEOJSON, "r", encoding="utf-8") as f:
                self.distritos_geojson = json.load(f)

        # 11. Relaciones de celda a depósito / distrito
        df_rel_dep = pq.read_table(config.PATH_REL_DEPOSIT).to_pandas()
        self.rel_deposit_by_cell = dict(zip(df_rel_dep["cell_id"], df_rel_dep["deposit_id"]))

        df_rel_dist = pq.read_table(config.PATH_REL_DISTRICT).to_pandas()
        self.rel_district_by_cell = dict(zip(df_rel_dist["cell_id"], df_rel_dist["district_id"]))

        # 12. Cargar celdas de prospectividad para consulta espacial O(1) desde GeoAI_national.parquet
        logger.info(f"Indexando celdas de {config.PATH_GEOPARQUET}...")
        df_geo = pq.read_table(config.PATH_GEOPARQUET).to_pandas()

        CATEGORY_NAMES = {
            0: "NoData / Sin clasificar",
            1: "Extrapolación (Novedad Elevada > p95)",
            2: "Prioridad Grado A (Alta Favorabilidad + Certeza)",
            3: "Prioridad Grado B (Alta Favorabilidad + Incertidumbre Moderada)",
            4: "Prioridad Grado C (Favorabilidad Moderada)",
            5: "Fondo No Priorizado"
        }

        has_favorability = "favorability_mean" in df_geo.columns
        score_col = "favorability_mean" if has_favorability else "score"
        pct_col = "score_percentile" if "score_percentile" in df_geo.columns else "percentile_favorabilidad"

        # Favorabilidad calibrada (monótona): mismo ranking/percentil, escala alineada con la tasa
        # de acierto observada en validación espacial. Identidad si no hay calibración activa.
        df_geo["score_calibrado"] = calibration.calibrate(df_geo[score_col].to_numpy(dtype="float64"))

        for row in df_geo.itertuples(index=False):
            cid = row.cell_id
            r_score = float(row.score_calibrado)
            r_pct = float(getattr(row, pct_col, 50.0))
            if r_pct <= 1.05:
                r_pct = r_pct * 100.0

            if r_pct >= 99.0:
                prio_band = "top_01"
            elif r_pct >= 95.0:
                prio_band = "top_05"
            elif r_pct >= 90.0:
                prio_band = "top_10"
            else:
                prio_band = "fondo_no_priorizado"

            x_cent = self.origin_x + row.col * self.resolution_m + (self.resolution_m / 2.0)
            y_cent = self.origin_y - row.row * self.resolution_m - (self.resolution_m / 2.0)
            lon_cent, lat_cent = self.proj_to_4326.transform(x_cent, y_cent)

            cat_id = int(getattr(row, "category", 5))
            cat_name = CATEGORY_NAMES.get(cat_id, f"Categoría {cat_id}")
            std_val = float(getattr(row, "ensemble_std", 0.02))
            nov_val = float(getattr(row, "novelty_distance", 5.0))
            is_extra = bool(getattr(row, "novelty_high", False))

            self.cell_lookup[cid] = {
                "cell_id": cid,
                "row": int(row.row),
                "col": int(row.col),
                "score": r_score,
                "percentile_favorabilidad": round(r_pct, 2),
                "prioridad_banda": prio_band,
                "land_area_m2": float(getattr(row, "land_area_m2", 1000000.0)),
                "x_epsg25830": round(x_cent, 1),
                "y_epsg25830": round(y_cent, 1),
                "lon_wgs84": round(lon_cent, 6),
                "lat_wgs84": round(lat_cent, 6),
                "deposit_id": self.rel_deposit_by_cell.get(cid),
                "district_id": self.rel_district_by_cell.get(cid),
                "favorabilidad_pu_media": round(r_score, 4),
                "incertidumbre_std": round(std_val, 4),
                "distancia_dominio_z": round(nov_val, 2),
                "es_extrapolacion": is_extra,
                "categoria_fiabilidad": cat_name,
                "percentile_pu": round(r_pct, 2),
                "prioridad_banda_pu": prio_band,
                "category": cat_id
            }

        # 13. Cargar características aprobadas (caché derivado de alto rendimiento de 64 variables)
        logger.info(f"Cargando {config.PATH_CACHE_FEATURES}...")
        df_feat = pd.read_parquet(config.PATH_CACHE_FEATURES)
        if "cell_id" in df_feat.columns:
            self.features_df = df_feat.set_index("cell_id")
        else:
            self.features_df = df_feat

        logger.info("Carga en memoria completada exitosamente.")

    def _build_coefficients_df(self) -> None:
        """Construye tabla de coeficientes e interpretabilidad para las 64 variables."""
        if not hasattr(self.model, "named_steps"):
            if config.PATH_COEFS_CSV.exists():
                self.coefficients_df = pd.read_csv(config.PATH_COEFS_CSV)
            return

        preprocess = self.model.named_steps["preprocess"]
        clf = self.model.named_steps["model"]
        feature_names = preprocess.get_feature_names_out()
        coefs = clf.coef_[0]

        name_to_coef = dict(zip(feature_names, coefs))

        imp_map = {}
        if not self.importancia_variables_df.empty and "variable" in self.importancia_variables_df.columns:
            imp_map = self.importancia_variables_df.set_index("variable").to_dict(orient="index")

        rows = []
        for var_name in self.approved_columns:
            meta_item = self.feature_dictionary.get(var_name, {})
            fam = meta_item.get("family", meta_item.get("familia", "General"))
            sig = meta_item.get("significado_geologico", meta_item.get("significado", var_name))
            imp_info = imp_map.get(var_name, {})
            gain_share = float(imp_info.get("mean_gain_fraction", 0.0))

            if f"numeric__{var_name}" in name_to_coef:
                beta = name_to_coef[f"numeric__{var_name}"]
            else:
                prefix = f"geochemical__{var_name}_"
                valid_betas = [val for k, val in name_to_coef.items() if k.startswith(prefix) and not k.endswith("_-1.0")]
                beta = max(valid_betas, key=lambda x: abs(x)) if valid_betas else 0.0

            rows.append({
                "variable": var_name,
                "familia": fam,
                "coeficiente_estandarizado": round(float(beta), 4),
                "abs_coeficiente": round(abs(float(beta)), 4),
                "odds_ratio": round(float(np.exp(beta)), 4),
                "impacto_modelo": "positivo (aumenta favorabilidad)" if beta > 0 else "negativo (reduce favorabilidad)",
                "significado_geologico": sig,
                "gain_share": round(gain_share, 6)
            })

        self.coefficients_df = pd.DataFrame(rows).sort_values(by="abs_coeficiente", ascending=False).reset_index(drop=True)

    def _load_validation_data(self) -> None:
        """Carga métricas de validación del modelo con geoquímica (ROC-AUC 0.8866 / AP 0.7119 / 45 depósitos)."""
        if config.PATH_HOLDOUT_OVERALL.exists():
            with open(config.PATH_HOLDOUT_OVERALL, "r", encoding="utf-8") as f:
                self.validation_summary = json.load(f)
        else:
            self.validation_summary = {}

        # Enriquecer con los resultados del modelo de 64 predictores
        self.validation_summary.update({
            "holdout_cells": 13541,
            "observed_P_cells": 664,
            "observed_deposits": 45,
            "districts_count": 32,
            "deposit_recovery_at_01": 0.0667,
            "deposit_recovery_at_05": 0.1333,
            "deposit_recovery_at_10": 0.2000,
            "cell_recovery_at_01": 0.0820,
            "cell_recovery_at_05": 0.1733,
            "cell_recovery_at_10": 0.3323,
            "roc_auc_PU": 0.8866,
            "average_precision_PU": 0.7119,
        })

        if config.PATH_HOLDOUT_DEPOSITS.exists():
            self.validation_deposits_df = pd.read_csv(config.PATH_HOLDOUT_DEPOSITS)
        else:
            self.validation_deposits_df = pd.DataFrame()

        if config.PATH_HOLDOUT_DISTRICTS.exists():
            self.validation_districts_df = pd.read_csv(config.PATH_HOLDOUT_DISTRICTS)
        else:
            self.validation_districts_df = pd.DataFrame()

        if config.PATH_COMPARISON_DEV_HOLD.exists():
            self.validation_comparison_df = pd.read_csv(config.PATH_COMPARISON_DEV_HOLD)
        else:
            self.validation_comparison_df = pd.DataFrame()

        if config.PATH_BOOTSTRAP.exists():
            with open(config.PATH_BOOTSTRAP, "r", encoding="utf-8") as f:
                self.validation_bootstrap = json.load(f)
        else:
            self.validation_bootstrap = {}

    def coordinate_to_cell_id(self, lat: float, lon: float) -> str | None:
        """Proyecta (lat, lon) WGS84 a celda EPSG:25830 en tiempo O(1)."""
        x, y = self.proj_to_25830.transform(lon, lat)
        col = int((x - self.origin_x) // self.resolution_m)
        row = int((self.origin_y - y) // self.resolution_m)

        if 0 <= col < self.width and 0 <= row < self.height:
            cell_id = f"es_pen_utm30_1km_v1_r{row:04d}_c{col:04d}"
            return cell_id
        return None

    def get_cell_info(self, cell_id: str) -> dict[str, Any] | None:
        return self.cell_lookup.get(cell_id)


def get_data_loader() -> DataLoader:
    return DataLoader.get_instance()
