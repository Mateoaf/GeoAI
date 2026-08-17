"""
GeoAI Hispania Mineral Prospectivity Mapping Package (Audited v2.0)
"""
from .inference.predictor import predict_by_coordinates, get_loaded_models_v2
from .features.extractor import extract_geoscientific_features, extract_features_to_dataframe

__version__ = "2.0.0"
__all__ = [
    "predict_by_coordinates",
    "get_loaded_models_v2",
    "extract_geoscientific_features",
    "extract_features_to_dataframe"
]
