"""
Motor de Inferencia de Producción GeoAI v2.
Extrae características en tiempo real mediante el extractor oficial unificado
y evalúa los modelos serializados calibrados v2.
"""
from pathlib import Path
import logging
import joblib
import pandas as pd
import numpy as np

from ..features.extractor import extract_geoscientific_features, is_point_in_iberian_domain

logger = logging.getLogger(__name__)

MODELS_V2_DIR = Path(__file__).resolve().parent.parent.parent.parent / "models" / "v2"
_LOADED_MODELS_V2 = None

def get_loaded_models_v2():
    """Carga en memoria los modelos calibrados v2 de prospectividad mineral."""
    global _LOADED_MODELS_V2
    if _LOADED_MODELS_V2 is None:
        _LOADED_MODELS_V2 = {}
        model_names = ['General_Mining', 'Au_Oro', 'Cu_Cobre', 'Ag_Plata', 'Pb_Plomo']
        for c in model_names:
            p = MODELS_V2_DIR / f"model_geoai_v2_{c}.joblib"
            if p.exists():
                try:
                    _LOADED_MODELS_V2[c] = joblib.load(p)
                except Exception as e:
                    logger.warning(f"Error al cargar {p}: {e}")
    return _LOADED_MODELS_V2

def predict_by_coordinates(lat: float, lng: float, location_name: str = None) -> dict:
    """
    Ejecuta el pipeline oficial de inferencia para una coordenada geográfica (WGS84):
    1. Verifica si la coordenada está en el dominio continental peninsular.
    2. Extrae las características geocientíficas observadas y derivadas reales (IGME + DEM).
    3. Evalúa los modelos de Machine Learning v2.
    4. Retorna un informe de favorabilidad mineral cuantitativo e interpretable.
    """
    if not is_point_in_iberian_domain(lat, lng):
        return {
            "error": "OUT_OF_DOMAIN",
            "message": "La coordenada se encuentra fuera del dominio continental de la Península Ibérica o en aguas marítimas.",
            "latitude": lat,
            "longitude": lng,
            "prospectivity_scores": {}
        }
        
    models = get_loaded_models_v2()
    
    # 1. Extracción de variables observadas y derivadas mediante el extractor unificado
    features = extract_geoscientific_features(lat, lng)
    df_features = pd.DataFrame([features])
    
    scores = {}
    classes = {}
    
    for ckey, bundle in models.items():
        model = bundle['model']
        model_feats = bundle['features']
        calibrator = bundle.get('calibrator')
        
        # Validar y seleccionar las columnas exactas esperadas por el modelo
        X_sub = df_features[model_feats]
        
        raw_score = float(model.predict_proba(X_sub)[0, 1])
        if calibrator is not None:
            calib_score = float(calibrator.predict(np.array([raw_score]))[0])
            score = max(0.0, min(1.0, calib_score))
        else:
            score = raw_score
            
        scores[ckey] = round(score, 4)
        
        if score >= 0.50:
            classes[ckey] = "Alta Favorabilidad"
        elif score >= 0.25:
            classes[ckey] = "Favorabilidad Media"
        else:
            classes[ckey] = "Baja Favorabilidad"
            
    loc_title = location_name if location_name else f"Punto ({lat:.4f}°, {lng:.4f}°)"
    
    elev_str = f"{features['Real_Elevation_MDT_m']:.0f} m" if pd.notna(features.get('Real_Elevation_MDT_m')) else "N/D"
    fault_dist_str = f"{features['Real_IGME_Dist_Fault_m']:.0f} m" if pd.notna(features.get('Real_IGME_Dist_Fault_m')) else "N/D"
    
    return {
        "location": loc_title,
        "latitude": lat,
        "longitude": lng,
        "utm_x": features["Coord_X"],
        "utm_y": features["Coord_Y"],
        "features_extracted": features,
        "prospectivity_scores": scores,
        "favorability_classes": classes,
        "interpretation": (
            f"Evaluación geológica en {features['Real_IGME_Lithology_General']} "
            f"({features['Real_IGME_Era']}, {features['Real_IGME_Dominio']}) "
            f"con distancia a falla IGME de {fault_dist_str} "
            f"y elevación de {elev_str} s.n.m."
        )
    }
