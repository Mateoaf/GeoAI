"""
Ejecutor de Pruebas Unitarias GeoAI v2 con unittest.
"""
import unittest
import sys
from pathlib import Path
import yaml
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

CONFIG_DIR = PROJECT_ROOT / "config"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_V2_DIR = PROJECT_ROOT / "models" / "v2"

from geoai_roman_spain.features.extractor import extract_geoscientific_features
from geoai_roman_spain.inference.predictor import predict_by_coordinates, get_loaded_models_v2

class TestGeoAIPipeline(unittest.TestCase):
    
    def test_feature_provenance_yaml_integrity(self):
        """Verifica que el archivo config/feature_provenance.yaml sea válido y completo."""
        prov_file = CONFIG_DIR / "feature_provenance.yaml"
        self.assertTrue(prov_file.exists(), "El archivo feature_provenance.yaml no existe.")
        
        with open(prov_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        self.assertIn("features", data)
        self.assertGreaterEqual(len(data["features"]), 10)
        
        required_keys = ["name", "family", "observed_or_derived", "source", "output_crs", "leakage_risk"]
        for feat in data["features"]:
            for k in required_keys:
                self.assertIn(k, feat, f"Falta {k} en {feat.get('name')}")

    def test_no_mine_coordinate_leakage_in_structural_features(self):
        """Verifica que el árbol estructural no se construya sobre las 993 minas."""
        from geoai_roman_spain.gis.fault_analysis import load_spatial_structures
        fault_cache = PROJECT_ROOT / "data" / "interim" / "igme_faults_lines.gpkg"
        fault_tree, contact_tree = load_spatial_structures(fault_cache)
        self.assertIsNotNone(fault_tree)
        self.assertNotEqual(fault_tree.n, 993, "Leakage detectado: el KDTree estructural usa el número de minas.")

    def test_feature_extractor_parity_and_output_schema(self):
        """Verifica que el extractor unificado devuelva las 13 variables observadas/derivadas reales."""
        feats = extract_geoscientific_features(43.5615, -6.9378)
        expected_keys = [
            "Real_Elevation_MDT_m", "Real_Slope_Deg", "Real_TPI_1km", "Real_TRI_Roughness",
            "Real_IGME_Dist_Fault_m", "Real_IGME_Dist_Contact_m",
            "Real_IGME_Fault_Density_5km", "Real_IGME_Fault_Density_2_5km",
            "Coord_X", "Coord_Y",
            "Real_IGME_Lithology_General", "Real_IGME_Era", "Real_IGME_Dominio"
        ]
        for k in expected_keys:
            self.assertIn(k, feats, f"Falta la variable {k} en el extractor unificado.")
        self.assertGreaterEqual(feats["Real_Elevation_MDT_m"], 0.0)

    def test_predict_by_coordinates_runs_cleanly(self):
        """Verifica la inferencia oficial en un yacimiento emblemático."""
        res = predict_by_coordinates(37.6930, -6.5940, "Minas de Riotinto (Huelva)")
        self.assertIn("prospectivity_scores", res)
        self.assertIn("favorability_classes", res)
        scores = res["prospectivity_scores"]
        for c in ["Au_Oro", "Cu_Cobre", "Ag_Plata", "Pb_Plomo"]:
            self.assertIn(c, scores)
            self.assertGreaterEqual(scores[c], 0.0)
            self.assertLessEqual(scores[c], 1.0)

    def test_dataset_v2_has_no_synthetic_columns(self):
        """Verifica que el dataset v2 no contenga variables sintéticas filtradas con el target."""
        csv_v2 = PROCESSED_DIR / "ml_dataset_real_v2.csv"
        self.assertTrue(csv_v2.exists())
        df = pd.read_csv(csv_v2)
        forbidden_cols = ["Real_Geochem_As_ppm", "Real_Geochem_Cu_ppm", "Real_Geochem_Pb_ppm", "Real_Remote_Gossan_FeOx_Index"]
        for col in forbidden_cols:
            self.assertNotIn(col, df.columns, f"Columna prohibida con leakage encontrada: {col}")

if __name__ == '__main__':
    unittest.main(verbosity=2)
