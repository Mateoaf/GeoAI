"""
Suite Integral de Tests de Robustez Científica y Reproducibilidad GeoAI v2.
Contiene 20 asertos obligatorios para verificar la integridad del pipeline geocientífico.
"""
import os
import sys
import unittest
import numpy as np
import pandas as pd
import joblib
import yaml
from pathlib import Path
from shapely.geometry import Point

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from geoai_roman_spain.data_sources.dem_client import (
    query_elevation_at_point,
    derive_terrain_morphometry
)
from geoai_roman_spain.data_sources.igme_client import query_igme_lithology_at_point
from geoai_roman_spain.gis.fault_analysis import (
    load_spatial_structures,
    compute_structural_features
)
from geoai_roman_spain.features.extractor import (
    extract_geoscientific_features,
    is_point_in_iberian_domain,
    to_utm30n
)
from geoai_roman_spain.ml.spatial_cv import create_spatial_folds, evaluate_fold_metrics
from geoai_roman_spain.ml.lodo import DISTRICT_DEFINITIONS

class TestGeoAIHardenedSuite(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.dataset_path = PROJECT_ROOT / "data" / "processed" / "ml_dataset_real_v2.csv"
        cls.models_dir = PROJECT_ROOT / "models" / "v2"
        cls.reports_dir = PROJECT_ROOT / "reports"
        cls.config_path = PROJECT_ROOT / "config" / "feature_provenance.yaml"
        cls.cache_faults = PROJECT_ROOT / "data" / "interim" / "igme_fault_lines.gpkg"
        
        if cls.dataset_path.exists():
            cls.df = pd.read_csv(cls.dataset_path)
        else:
            cls.df = None

    # Test 1: No synthetic elevation fallback
    def test_01_no_synthetic_elevation_fallback(self):
        """Verifica que el cliente DEM devuelva np.nan o un valor observado real, nunca 550.0 arbitrario."""
        res = query_elevation_at_point(999.0, 999.0)  # Coordenada fuera del planeta
        self.assertTrue(np.isnan(res), "Fallo: Coordenada inválida no devolvió np.nan")

    # Test 2: No synthetic morphometry fallbacks
    def test_02_no_synthetic_morphometry_fallbacks(self):
        """Verifica que slope/TPI/TRI devuelvan np.nan con estado QA controlado en caso de error."""
        res = derive_terrain_morphometry(999.0, 999.0)
        self.assertTrue(np.isnan(res['slope_deg']), "Pendiente no es np.nan ante coordenadas inválidas")
        self.assertTrue(res['dem_qa_status'] in ['NODATA_ERROR', 'NODATA_API_LIMIT', 'OBSERVED_POINT_ONLY'])

    # Test 3: IGME client returns real data or controlled nodata
    def test_03_igme_client_no_mock_geometries(self):
        """Verifica que el cliente IGME devuelva np.nan / UNMAPPED_OR_NODATA para puntos marinos sin inventar litologías."""
        res = query_igme_lithology_at_point(36.0, -15.0)  # Océano Atlántico abierto
        self.assertTrue(pd.isna(res['lithology']) or res['lithology'] == "UNMAPPED_OR_NODATA")
        self.assertTrue(res['igme_qa_status'] in ["UNMAPPED_OR_NODATA", "NODATA_ERROR", "OBSERVED_IGME_1M"])

    # Test 4: STRtree fault distance calculation
    def test_04_strtree_fault_distance_metric(self):
        """Verifica que las distancias a fallas se calculen en metros mediante STRtree y sean no negativas."""
        x_utm, y_utm = to_utm30n(42.45, -6.70)  # Las Médulas
        res = compute_structural_features(x_utm, y_utm, self.cache_faults)
        self.assertGreaterEqual(res['dist_fault_m'], 0.0)
        self.assertGreaterEqual(res['dist_contact_m'], 0.0)
        self.assertLess(res['dist_fault_m'], 200000.0)

    # Test 5: Fault length density units
    def test_05_fault_length_density_units(self):
        """Verifica que la densidad de fallas esté en km/km² y dentro de rangos geológicos razonables."""
        x_utm, y_utm = to_utm30n(37.70, -6.55)  # Riotinto
        res = compute_structural_features(x_utm, y_utm, self.cache_faults)
        self.assertGreaterEqual(res['fault_length_density_5km'], 0.0)
        self.assertLessEqual(res['fault_length_density_5km'], 5.0)

    # Test 6: Iberian domain rejects oceanic points
    def test_06_iberian_domain_filter_rejects_sea(self):
        """Verifica que las coordenadas marinas sean rechazadas por la máscara peninsular."""
        self.assertFalse(is_point_in_iberian_domain(39.0, 5.0))   # Mar Balear profundo
        self.assertFalse(is_point_in_iberian_domain(44.5, -4.0))  # Golfo de Vizcaya profundo

    # Test 7: Iberian domain accepts land points
    def test_07_iberian_domain_filter_accepts_land(self):
        """Verifica que los puntos continentales de Hispania sean aceptados."""
        self.assertTrue(is_point_in_iberian_domain(40.4168, -3.7038)) # Madrid
        self.assertTrue(is_point_in_iberian_domain(42.4597, -6.7645)) # Las Médulas
        self.assertTrue(is_point_in_iberian_domain(37.6969, -6.5936)) # Riotinto

    # Test 8: Background points buffer exclusion
    def test_08_background_buffer_exclusion(self):
        """Verifica que en el dataset maestro los fondos respeten buffer >= 5 km respecto a minas."""
        if self.df is not None:
            bg_df = self.df[self.df['target_class'] == 0]
            pos_df = self.df[self.df['target_class'] == 1]
            from scipy.spatial import cKDTree
            tree = cKDTree(pos_df[['Coord_X', 'Coord_Y']].values)
            dists, _ = tree.query(bg_df[['Coord_X', 'Coord_Y']].values)
            min_dist = dists.min()
            self.assertGreaterEqual(min_dist, 4900.0, f"Violación de buffer: distancia mínima de {min_dist} m")

    # Test 9: Feature extractor schema and parity
    def test_09_feature_extractor_parity(self):
        """Verifica la paridad total del extractor de inferencia puntual."""
        feat = extract_geoscientific_features(42.45, -6.70)
        expected_keys = [
            'Real_IGME_Dist_Fault_m', 'Real_IGME_Dist_Contact_m',
            'Real_IGME_Fault_Length_Density_5km', 'Real_IGME_Lithology_General',
            'Real_IGME_Era', 'Real_IGME_Dominio', 'in_domain'
        ]
        for k in expected_keys:
            self.assertIn(k, feat, f"Falta clave {k} en extractor unificado")

    # Test 10: Exclusion of Coord_X / Coord_Y from official model features
    def test_10_no_coordinate_leakage_in_features(self):
        """Verifica que las coordenadas X/Y no formen parte del vector predictor oficial."""
        model_path = self.models_dir / "model_geoai_v2_General_Mining.joblib"
        if model_path.exists():
            bundle = joblib.load(model_path)
            self.assertNotIn("Coord_X", bundle["features"])
            self.assertNotIn("Coord_Y", bundle["features"])

    # Test 11: Production model bundle integrity
    def test_11_model_bundle_structure(self):
        """Verifica que los modelos serializados contengan pipeline, calibrador y métricas espaciales."""
        model_path = self.models_dir / "model_geoai_v2_General_Mining.joblib"
        if model_path.exists():
            bundle = joblib.load(model_path)
            self.assertIn("model", bundle)
            self.assertIn("calibrator", bundle)
            self.assertIn("overall_metrics", bundle)
            self.assertIn("fold_metrics", bundle)

    # Test 12: Monotonicity and bounds of Isotonic Calibrator
    def test_12_calibrator_monotonicity(self):
        """Verifica que el calibrador isotónico devuelva valores monótonos acotados en [0.0, 1.0]."""
        model_path = self.models_dir / "model_geoai_v2_General_Mining.joblib"
        if model_path.exists():
            bundle = joblib.load(model_path)
            cal = bundle["calibrator"]
            test_inputs = np.linspace(0.0, 1.0, 50)
            calib_outputs = cal.predict(test_inputs)
            self.assertTrue(np.all(calib_outputs >= 0.0))
            self.assertTrue(np.all(calib_outputs <= 1.0))
            self.assertTrue(np.all(np.diff(calib_outputs) >= -1e-7))

    # Test 13: Spatial Block CV non-degeneracy
    def test_13_spatial_folds_balance(self):
        """Verifica que los 5 folds espaciales contengan muestras de ambas clases."""
        if self.df is not None:
            folds = create_spatial_folds(self.df, n_splits=5, seed=42)
            self.assertEqual(len(np.unique(folds)), 5)
            for f in range(5):
                mask = (folds == f)
                n_pos = self.df.loc[mask, 'target_class'].sum()
                n_neg = (self.df.loc[mask, 'target_class'] == 0).sum()
                self.assertGreater(n_pos, 0, f"Fold {f+1} carece de muestras positivas")
                self.assertGreater(n_neg, 0, f"Fold {f+1} carece de muestras de fondo")

    # Test 14: Metallogenic districts defined
    def test_14_lodo_districts_defined(self):
        """Verifica que las 5 provincias metalogénicas principales estén formalmente definidas."""
        expected_districts = [
            "Noroeste_Galaico_Leones", "Faja_Piritica_Iberica",
            "Sierra_Morena_Linares", "Sureste_Betico", "Zona_Centroiberica"
        ]
        for d in expected_districts:
            self.assertIn(d, DISTRICT_DEFINITIONS)

    # Test 15: YAML Feature Provenance valid schema
    def test_15_feature_provenance_yaml_valid(self):
        """Verifica que el catálogo de procedencia YAML sea válido y cumpla la taxonomía."""
        self.assertTrue(self.config_path.exists())
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.assertIn("features", data)
        valid_taxonomies = {"OBSERVED", "DERIVED_FROM_OBSERVED", "PROXY", "SYNTHETIC", "METADATA", "SPATIAL_INDEX_ONLY"}
        for feat in data["features"]:
            self.assertIn(feat["observed_or_derived"], valid_taxonomies)

    # Test 16: QA metadata columns in dataset
    def test_16_qa_metadata_present_in_dataset(self):
        """Verifica que las columnas de diagnóstico QA existan en el dataset maestro."""
        if self.df is not None:
            self.assertIn("dem_qa_status", self.df.columns)
            self.assertIn("igme_qa_status", self.df.columns)

    # Test 17: Interactive map anti-offshore check
    def test_17_interactive_map_anti_offshore(self):
        """Verifica que el mapa interactivo rechace solicitudes fuera de tierra firme."""
        from geoai_roman_spain.features.extractor import is_point_in_iberian_domain
        self.assertFalse(is_point_in_iberian_domain(35.5, -4.5)) # Mar de Alborán

    # Test 18: Target semantics separation
    def test_18_target_semantics_documented(self):
        """Verifica que el dataset contenga flags para commodities individuales (Au, Cu, Ag, Pb)."""
        if self.df is not None:
            for flag in ["flag_Au", "flag_Cu", "flag_Ag", "flag_Pb"]:
                self.assertIn(flag, self.df.columns)

    # Test 19: SHAP plot exists
    def test_19_shap_summary_plot_exists(self):
        """Verifica que el gráfico SHAP resumen haya sido generado."""
        shap_png = self.reports_dir / "shap_summary_v2_gold.png"
        self.assertTrue(shap_png.exists())

    # Test 20: Benchmark report exists
    def test_20_benchmark_report_exists(self):
        """Verifica que el informe de benchmark markdown oficial esté generado."""
        bench_md = self.reports_dir / "geoai_v2_model_benchmark.md"
        self.assertTrue(bench_md.exists())

if __name__ == "__main__":
    unittest.main()
