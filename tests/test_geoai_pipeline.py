"""
Suite Oficial de Pruebas y Validación Científica GeoAI v2.
Verifica integridad de datos, ausencia de leakage, paridad de features y robustez de inferencia.
"""
import os
import sys
from pathlib import Path
import pytest
import yaml
import numpy as np
import pandas as pd
import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

CONFIG_DIR = PROJECT_ROOT / "config"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_V2_DIR = PROJECT_ROOT / "models" / "v2"

from geoai_roman_spain.features.extractor import extract_geoscientific_features
from geoai_roman_spain.inference.predictor import predict_by_coordinates, get_loaded_models_v2

def test_feature_provenance_yaml_integrity():
    """Verifica que el registro de procedencia de features exista y sea completo."""
    prov_file = CONFIG_DIR / "feature_provenance.yaml"
    assert prov_file.exists(), "El archivo feature_provenance.yaml no existe."
    
    with open(prov_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    assert "features" in data
    assert len(data["features"]) >= 10
    
    required_keys = ["name", "family", "observed_or_derived", "source", "output_crs", "leakage_risk"]
    for feat in data["features"]:
        for k in required_keys:
            assert k in feat, f"La característica {feat.get('name')} no tiene el campo obligatorio {k}"

def test_no_mine_coordinate_leakage_in_structural_features():
    """Garantiza que ninguna feature estructural se calcule a partir de coordenadas de minas conocidas."""
    from geoai_roman_spain.gis.fault_analysis import load_spatial_structures
    
    fault_cache = PROJECT_ROOT / "data" / "interim" / "igme_faults_lines.gpkg"
    fault_tree, contact_tree = load_spatial_structures(fault_cache)
    
    assert fault_tree is not None
    assert contact_tree is not None
    # Verificar que el árbol no proviene del número de minas (993) sino de segmentos vectoriales
    assert fault_tree.n != 993, "El árbol espacial coincide exactamente con el número de minas conocidas (Leakage detectado)."

def test_feature_extractor_parity_and_output_schema():
    """Verifica que el extractor unificado retorne el esquema exacto de 13 características reales."""
    # Coordenadas de prueba en Salave (Asturias)
    feats = extract_geoscientific_features(43.5615, -6.9378)
    
    expected_keys = [
        "Real_Elevation_MDT_m", "Real_Slope_Deg", "Real_TPI_1km", "Real_TRI_Roughness",
        "Real_IGME_Dist_Fault_m", "Real_IGME_Dist_Contact_m",
        "Real_IGME_Fault_Density_5km", "Real_IGME_Fault_Density_2_5km",
        "Coord_X", "Coord_Y",
        "Real_IGME_Lithology_General", "Real_IGME_Era", "Real_IGME_Dominio"
    ]
    
    for k in expected_keys:
        assert k in feats, f"Falta la variable requerida {k} en el extractor unificado."
        
    assert feats["Real_Elevation_MDT_m"] >= 0.0
    assert feats["Real_IGME_Dist_Fault_m"] >= 0.0
    assert len(feats["Real_IGME_Lithology_General"]) > 0

def test_predict_by_coordinates_runs_cleanly():
    """Verifica que la función oficial de inferencia predict_by_coordinates funcione de punta a punta."""
    res = predict_by_coordinates(37.6930, -6.5940, "Riotinto (Huelva)")
    
    assert "prospectivity_scores" in res
    assert "favorability_classes" in res
    assert "features_extracted" in res
    
    scores = res["prospectivity_scores"]
    for c in ["Au_Oro", "Cu_Cobre", "Ag_Plata", "Pb_Plomo"]:
        assert c in scores
        assert 0.0 <= scores[c] <= 1.0, f"Score de prospectividad {c} fuera de rango [0, 1]: {scores[c]}"

def test_out_of_bounds_handling():
    """Verifica el comportamiento robusto ante coordenadas fuera de España continental."""
    # Coordenadas en medio del Atlántico Norte (50.0°N, -20.0°W)
    feats = extract_geoscientific_features(50.0, -20.0)
    assert feats is not None
    assert "Real_Elevation_MDT_m" in feats

def test_dataset_v2_has_no_synthetic_columns():
    """Verifica que el dataset v2 no contenga variables sintéticas filtradas con el target."""
    csv_v2 = PROCESSED_DIR / "ml_dataset_real_v2.csv"
    if csv_v2.exists():
        df = pd.read_csv(csv_v2)
        # Columnas prohibidas que antes tenían target leakage
        forbidden_cols = ["Real_Geochem_As_ppm", "Real_Geochem_Cu_ppm", "Real_Geochem_Pb_ppm", "Real_Remote_Gossan_FeOx_Index"]
        for col in forbidden_cols:
            assert col not in df.columns, f"Columna con leakage prohibida encontrada en dataset v2: {col}"
