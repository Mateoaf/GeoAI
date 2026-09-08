from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import yaml
from shapely.geometry import Point, box
from geoau.additional_layers import harmonize_additional, attribute_checks
from geoau.territory import grid_spec, feature_dictionary, base_vector_config


class AdditionalTests(unittest.TestCase):
    def test_points_preserved_z_and_no_fake_coverage(self):
        config = yaml.safe_load((Path(__file__).resolve().parents[1]/'config/grid.yaml').read_text(encoding='utf-8'))
        config.update(width=2,height=2,origin_x=0,origin_y=2000,vector_batch_size=2,
                      additional_vectors={'buzamientos':'points.gpkg'})
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'vectors').mkdir();(root/'rasters').mkdir()
            frame=gpd.GeoDataFrame({'ROTATION':[15.,20.,30.],'STRING':['40','999','50']},
                geometry=[Point(100,100,12),Point(200,200,14),Point(100000,100000,30)],crs=25830)
            frame.to_file(root/'points.gpkg')
            feature_dictionary(root)
            summary=harmonize_additional(root,config['additional_vectors'],box(0,0,2000,2000),
                np.full((4,4),250000.),grid_spec(config),root)
            self.assertEqual(summary.kept_with_margin.iloc[0],2)
            self.assertEqual(summary.quarantine_count.iloc[0],0)
            self.assertEqual(summary.outside_scope_margin.iloc[0],1)
            result=gpd.read_file(root/'vectors/buzamientos.gpkg')
            self.assertEqual(set(result.z_original),{12,14})
            self.assertFalse(result.geometry.has_z.any())
            self.assertEqual(set(result.STRING),{'40','999'})
            with rasterio.open(root/'rasters/buzamientos_support_1km.tif') as src:
                self.assertIn('NO_cobertura',src.descriptions[0])
                self.assertEqual(src.read(1).sum(),1)

    def test_angular_qc_does_not_rewrite_source(self):
        frame=pd.DataFrame({'DIRECCION':[30,450,None],'BUZAMIENTO':[50,-1,999]})
        saved=frame.copy(deep=True)
        checks=attribute_checks(frame,'medidasestructurales')
        self.assertEqual(checks[0]['fuera_rango_angular_candidato'],1)
        self.assertEqual(checks[1]['fuera_rango_angular_candidato'],2)
        pd.testing.assert_frame_equal(frame,saved)

    def test_cache_ignores_only_unrelated_inputs(self):
        a={'phase_b_run':'old','vector_cache_run':'x','additional_vectors':{},'vector_margin_m':20000}
        b={**a,'phase_b_run':'new','additional_vectors':{'new':'file'}}
        self.assertEqual(base_vector_config(a),base_vector_config(b))
        self.assertNotEqual(base_vector_config(a),base_vector_config({**b,'vector_margin_m':10000}))
