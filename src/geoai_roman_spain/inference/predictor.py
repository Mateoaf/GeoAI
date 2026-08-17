"""
Motor de Inferencia de Producción GeoAI v2.
Extrae características en tiempo real mediante el extractor oficial unificado
y evalúa los modelos serializados calibrados v2.
"""
from pathlib import Path
import joblib
import pandas as pd
import numpy as np

from ..features.extractor import extract_geoscientific_features

MODELS_V2_DIR = Path(__file__).resolve().parent.parent.parent.parent / "models" / "v2"
_LOADED_MODELS_V2 = None

def get_loaded_models_v2():
    """Carga en memoria los 4 modelos calibrados v2 de prospectividad mineral."""
    global _LOADED_MODELS_V2
    if _LOADED_MODELS_V2 is None:
        _LOADED_MODELS_V2 = {}
        commodities = ['Au_Oro', 'Cu_Cobre', 'Ag_Plata', 'Pb_Plomo']
        for c in commodities:
            p = MODELS_V2_DIR / f"model_geoai_v2_{c}.joblib"
            if p.exists():
                _LOADED_MODELS_V2[c] = joblib.load(p)
            else:
                # Fallback al directorio models raíz si aún no está en v2
                fallback_p = MODELS_V2_DIR.parent / f"model_geoai_{c}.joblib"
                if fallback_p.exists():
                    _LOADED_MODELS_V2[c] = joblib.load(fallback_p)
    return _LOADED_MODELS_V2

def predict_by_coordinates(lat: float, lng: float, location_name: str = None) -> dict:
    """
    Ejecuta el pipeline oficial de inferencia para una coordenada geográfica (WGS84):
    1. Extrae las características geocientíficas observadas y derivadas reales (IGME + DEM).
    2. Evalúa los modelos de Machine Learning v2.
    3. Retorna un informe de favorabilidad mineral cuantitativo e interpretable.
    """
    models = get_loaded_models_v2()
    
    # 1. Extracción de variables observadas y derivadas mediante el extractor unificado
    features = extract_geoscientific_features(lat, lng)
    df_features = pd.DataFrame([features])
    
    scores = {}
    classes = {}
    
    for ckey, bundle in models.items():
        model = bundle['model']
        model_feats = bundle['features']
        
        # Validar y seleccionar las columnas exactas esperadas por el modelo
        X_sub = df_features[model_feats]
        
        score = float(model.predict_proba(X_sub)[0, 1])
        scores[ckey] = round(score, 4)
        
        if score >= 0.50:
            classes[ckey] = "Alta Favorabilidad"
        elif score >= 0.25:
            classes[ckey] = "Favorabilidad Media"
        else:
            classes[ckey] = "Baja Favorabilidad"
            
    loc_title = location_name if location_name else f"Punto ({lat:.4f}°, {lng:.4f}°)"
    
    return {
        "location": loc_title,
        "latitude": lat,
        "longitude": lng,
        "utm_x": features["Coord_X"],
        "utm_y": features["Coord_Y"],
        "features_extracted": features,
        "prospectivity_scores": {
            "Au_Oro": scores.get("Au_Oro", 0.0),
            "Cu_Cobre": scores.get("Cu_Cobre", 0.0),
            "Ag_Plata": scores.get("Ag_Plata", 0.0),
            "Pb_Plomo": scores.get("Pb_Plomo", 0.0)
        },
        "favorability_classes": classes,
        "interpretation": (
            f"Evaluación geológica en {features['Real_IGME_Lithology_General']} "
            f"({features['Real_IGME_Era']}, {features['Real_IGME_Dominio']}) "
            f"con distancia a falla IGME de {features['Real_IGME_Dist_Fault_m']:.0f} m "
            f"y elevación de {features['Real_Elevation_MDT_m']:.0f} m s.n.m."
        )
    }
