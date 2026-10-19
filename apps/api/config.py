"""
apps/api/config.py
Configuración de rutas y variables de entorno para GeoAI-Au Explorer Backend.
"""

import os
from pathlib import Path

# Raíz del repositorio
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Rutas Canónicas Inmutables de GeoAI-Au v1.0
RUN_DIR_D = REPO_ROOT / "reports" / "fase_d" / "20260927T135413_959884Z"
RUN_DIR_F = REPO_ROOT / "reports" / "fase_f" / "20260927T135750_819061Z"
RUN_DIR_G = REPO_ROOT / "reports" / "fase_g" / "20260927T141408_460613Z"
RUN_DIR_H = REPO_ROOT / "reports" / "fase_h" / "20260927T142549_961719Z"
DATA_REVIEW_DIR = REPO_ROOT / "data" / "review"

# Rutas de Caché Web Derivado (apps/api/data_cache/)
CACHE_DIR = Path(__file__).resolve().parent / "data_cache"

# Archivos específicos
PATH_GRID_SPEC = RUN_DIR_D / "grid_spec.json"
PATH_ALLOWLIST = RUN_DIR_D / "feature_allowlist.json"
PATH_FEATURE_DICT = RUN_DIR_D / "feature_dictionary.csv"
PATH_REL_DEPOSIT = RUN_DIR_D / "relacion_deposit_id_celda.parquet"
PATH_REL_DISTRICT = RUN_DIR_D / "relacion_district_id_celda.parquet"

PATH_MODEL = RUN_DIR_F / "final_model" / "final_validated_model.joblib"
PATH_MODEL_JSON = RUN_DIR_F / "final_model" / "final_validated_model.json"

PATH_HOLDOUT_OVERALL = RUN_DIR_G / "metrics" / "holdout_overall_metrics.json"
PATH_HOLDOUT_DEPOSITS = RUN_DIR_G / "metrics" / "holdout_by_deposit.csv"
PATH_HOLDOUT_DISTRICTS = RUN_DIR_G / "metrics" / "holdout_by_district.csv"
PATH_COMPARISON_DEV_HOLD = RUN_DIR_G / "metrics" / "development_vs_holdout_comparison.csv"
PATH_BOOTSTRAP = RUN_DIR_G / "metrics" / "bootstrap_deposit_uncertainty.json"

# Extensión Geoquímica IGME y Ensamble Multidisciplinar (64 Predictores)
GEOQ_DIR = REPO_ROOT / "reports" / "geoquimica_20261017"
GEOQ_MAPS_DIR = GEOQ_DIR / "maps"
GEOQ_MODELS_DIR = GEOQ_DIR / "models"

PATH_VARIABLES_INCLUIDAS_CSV = GEOQ_DIR / "variables_incluidas.csv"
PATH_IMPORTANCIA_VARIABLES_CSV = GEOQ_DIR / "importancia_variables.csv"
PATH_COBERTURA_GEOQUIMICA_CSV = GEOQ_DIR / "cobertura_geoquimica.csv"
PATH_IMPORTANCIA_GEOQUIMICA_CSV = GEOQ_DIR / "importancia_geoquimica.csv"
PATH_LEYENDAS_GEOQUIMICAS_CSV = GEOQ_DIR / "leyendas_geoquimicas.csv"
PATH_BENCHMARK_SUMMARY_CSV = GEOQ_DIR / "benchmark_summary.csv"
PATH_FUSION_SUMMARY_JSON = GEOQ_DIR / "fusion_summary.json"
PATH_FUSION_MODEL_JOBLIB = GEOQ_MODELS_DIR / "fusion" / "model.joblib"

PATH_COG_SCORE_RAW = GEOQ_MAPS_DIR / "GeoAI_score.tif"
PATH_COG_SCORE_CALIBRATED = GEOQ_MAPS_DIR / "GeoAI_score_calibrated.tif"
PATH_CALIBRATION_JSON = GEOQ_DIR / "calibracion_score.json"

# El mapa de favorabilidad usa el score calibrado (monotono: mismo ranking) salvo GEOAI_SCORE_MODE=raw
_USE_CALIBRATED = (
    os.getenv("GEOAI_SCORE_MODE", "calibrated").lower() != "raw"
    and PATH_COG_SCORE_CALIBRATED.exists()
    and PATH_CALIBRATION_JSON.exists()
)
PATH_COG_SCORE = PATH_COG_SCORE_CALIBRATED if _USE_CALIBRATED else PATH_COG_SCORE_RAW
PATH_COG_PERCENTILE = RUN_DIR_H / "maps" / "mapa_nacional_favorabilidad_percentil.tif"
PATH_COG_PRIORITY = RUN_DIR_H / "maps" / "mapa_nacional_bandas_prioritarias.tif"
PATH_COG_STD = GEOQ_MAPS_DIR / "GeoAI_std.tif"
PATH_COG_NOVELTY = GEOQ_MAPS_DIR / "GeoAI_novelty.tif"
PATH_COG_CATEGORY = GEOQ_MAPS_DIR / "GeoAI_category.tif"
PATH_GEOPARQUET = GEOQ_MAPS_DIR / "GeoAI_national.parquet"
PATH_GPKG = RUN_DIR_H / "maps" / "mapa_nacional_prospectividad.gpkg"
PATH_TARGETS_CSV = RUN_DIR_H / "targets" / "zonas_prospectividad_ranking.csv"
PATH_COEFS_CSV = RUN_DIR_H / "interpretability" / "coeficientes_estandarizados.csv"

# Modelos y Rásteres Especializados v2 (Experimento 787 Indicios - LightGBM)
PATH_COG_EXP_DIR = REPO_ROOT / "reports" / "experimento_600_indicios" / "maps"
PATH_COG_GLOBAL_V2 = PATH_COG_EXP_DIR / "mapa_nacional_oro_global_score.tif"
PATH_COG_ROCA = PATH_COG_EXP_DIR / "mapa_nacional_oro_roca_score.tif"
PATH_COG_ALUVIAL = PATH_COG_EXP_DIR / "mapa_nacional_oro_aluvial_score.tif"

# Modelos y Rásteres de Producción Oficial (Score PU, Incertidumbre y Fiabilidad Territorial con Geoquímica)
PATH_V3_DIR = REPO_ROOT / "reports" / "experimento_v3_riguroso"
PATH_V3_MAPS_DIR = GEOQ_MAPS_DIR
PATH_V3_PARQUET = GEOQ_MAPS_DIR / "GeoAI_national.parquet"
PATH_V3_PU_SCORE = PATH_COG_SCORE
PATH_V3_INCERTIDUMBRE_TIF = GEOQ_MAPS_DIR / "GeoAI_std.tif"
PATH_V3_BENCHMARK_CSV = GEOQ_DIR / "benchmark_summary.csv"
PATH_V3_RESUMEN_JSON = GEOQ_DIR / "fusion_summary.json"

PATH_CASOS_CSV = RUN_DIR_H / "interpretability" / "contribuciones_locales_casos_estudio.csv"
PATH_CONTROL_CIERRE = RUN_DIR_H / "control_cierre.json"

PATH_FASE_B_CSV = DATA_REVIEW_DIR / "revision_au_fase_b.csv"
PATH_DISTRITOS_CSV = DATA_REVIEW_DIR / "inventario_distritos_metalogeneticos.csv"

# Caché derivado
PATH_CACHE_FEATURES = CACHE_DIR / "features_approved_64.parquet"
PATH_CACHE_ZONAS_GEOJSON = CACHE_DIR / "zonas_prospectividad_4326.geojson"
PATH_CACHE_DEPOSITOS_GEOJSON = CACHE_DIR / "depositos_confirmados_4326.geojson"
PATH_CACHE_INDICIOS_GEOJSON = CACHE_DIR / "indicios_787_4326.geojson"
PATH_CACHE_DISTRITOS_GEOJSON = CACHE_DIR / "distritos_33_4326.geojson"

# Servidor
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "127.0.0.1")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,*").split(",")
