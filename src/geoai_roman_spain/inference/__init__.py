"""
Inference Subpackage for GeoAI
"""
from .predictor import predict_by_coordinates, get_loaded_models_v2

__all__ = ["predict_by_coordinates", "get_loaded_models_v2"]
