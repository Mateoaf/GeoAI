"""Controles científicos de soporte: casos pequeños con respuesta conocida."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio.transform import Affine
from shapely.geometry import box, Point, Polygon
import yaml
from geoau.territory import aggregate_values, aggregate_sum, land_areas, grid_spec, assign_points, clean_geometries, save_raster, _harmonize_vectors_uncached as harmonize_vectors, align_rasters


class TerritoryTests(unittest.TestCase):
    def test_zero_class_and_nodata(self):
        values = np.array([[0., 1.], [0., -9999.]])
        value, fraction, proportions = aggregate_values(values, values != -9999, np.ones((2,2)), 2)
        self.assertEqual(value[0,0], 0)
        self.assertEqual(fraction[0,0], .75)
        np.testing.assert_allclose(proportions[:,0,0], [2/3, 1/3])

    def test_tie_lowest_and_all_missing(self):
        v = np.array([[1.,0.],[1.,0.]])
        self.assertEqual(aggregate_values(v,np.ones((2,2),bool),np.ones((2,2)),2)[0][0,0],0)
        result, frac, prop = aggregate_values(v,np.zeros((2,2),bool),np.ones((2,2)),2)
        self.assertEqual(result[0,0],-9999)
        self.assertEqual(frac[0,0],0)
        self.assertTrue((prop == -9999).all())

    def test_fractional_classes_rejected(self):
        with self.assertRaises(ValueError):
            aggregate_values(np.full((2,2),.5),np.ones((2,2),bool),np.ones((2,2)),2)

    def test_land_weighting_not_ocean(self):
        v = np.array([[0.,1.],[1.,1.]])
        land = np.array([[1.,.1],[0.,0.]])
        mode, fraction, prop = aggregate_values(v,np.ones((2,2),bool),land,2)
        self.assertEqual(mode[0,0],0)
        self.assertEqual(fraction[0,0],1)
        np.testing.assert_allclose(prop[:,0,0],[1/1.1,.1/1.1])
        mean = aggregate_values(np.array([[10.,1000.],[99.,99.]]),np.array([[True,False],[True,True]]),land)[0]
        self.assertEqual(mean[0,0],10)

    def test_exact_coast_hole_and_tiny_island(self):
        main = box(.25,.25,2.75,2.75).difference(box(1,1,2,2))
        mask = main.union(box(3.1,3.1,3.2,3.2))
        area = land_areas(mask,(4,4),Affine(1,0,0,0,-1,4))
        self.assertAlmostEqual(area.sum(),mask.area)
        self.assertAlmostEqual(area[0,3],.01)
        self.assertEqual(area[2,1],0)
        self.assertAlmostEqual(aggregate_sum(area).sum(),mask.area)

    def test_mask_outside_extent_fails(self):
        with self.assertRaises(ValueError):
            land_areas(box(-1,0,2,2),(2,2),Affine(1,0,0,0,-1,2))

    def test_boundary_assignment_unique_and_quarantine(self):
        spec={'crs':'EPSG:25830','origin_x':0,'origin_y':2000,'resolution_m':1000}
        grid=pd.DataFrame({'row':[0,0,1,1],'col':[0,1,0,1],'cell_id':['a','b','c','d']})
        pts=gpd.GeoDataFrame({'record_id':['p1','p2','p3','p4'],'Codigo_indicio':['01','02','03','04'],
             'geo_cuarentena':[False,False,False,True],'elegible_general_revisada':[False]*4,'Provincia':['x']*4},
             geometry=[Point(1000,1000),Point(2000,1000),Point(-1,1),Point(100,100)],crs=25830)
        result=assign_points(pts,box(0,0,2000,2000),grid,spec)
        self.assertEqual(result.cell_id.iloc[0],'d')
        self.assertEqual(result.estado_territorial.iloc[1],'fuera_rejilla')
        self.assertEqual(result.estado_territorial.iloc[2],'fuera_mascara_candidata')
        self.assertEqual(result.estado_territorial.iloc[3],'geometria_no_utilizable')

    def test_repair_keeps_ids_and_audits(self):
        bad=Polygon([(0,0),(2,2),(2,0),(0,2),(0,0)])
        frame=gpd.GeoDataFrame({'code':['001']},geometry=[bad],crs=25830,index=[42])
        clean, metrics=clean_geometries(frame,25830)
        self.assertTrue(clean.geometry.is_valid.all())
        self.assertEqual(clean.code.iloc[0],'001')
        self.assertEqual(clean.source_fid.iloc[0],42)
        self.assertTrue(metrics.invalid_before.iloc[0])

    def test_raster_exact_transform_roundtrip(self):
        config=yaml.safe_load((Path(__file__).resolve().parents[1]/'config/grid.yaml').read_text(encoding='utf-8'))
        config.update(width=2,height=2)
        spec=grid_spec(config)
        with tempfile.TemporaryDirectory() as d:
            save_raster(Path(d)/'x.tif',np.array([[0.,1.],[-9999.,2.]]),['class'],spec)
            import rasterio
            with rasterio.open(Path(d)/'x.tif') as src:
                self.assertEqual(src.transform,spec['transform'])
                self.assertFalse(src.read(1,masked=True).mask[0,0])
                self.assertTrue(src.read(1,masked=True).mask[1,0])

    def test_half_pixel_shift_rejected(self):
        import rasterio
        config=yaml.safe_load((Path(__file__).resolve().parents[1]/'config/grid.yaml').read_text(encoding='utf-8'))
        config.update(width=2,height=2)
        spec=grid_spec(config)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with rasterio.open(root/'shift.tif','w',driver='GTiff',height=4,width=4,count=1,
                    dtype='float32',crs=25830,transform=spec['native_transform']*Affine.translation(.5,0)) as dst:
                dst.write(np.ones((4,4),dtype='float32'),1)
            with self.assertRaisesRegex(ValueError,'no anidada'):
                align_rasters(root,{'relieve':'shift.tif'},np.ones((4,4)),spec,root)

    def test_vector_pagination_and_margin(self):
        import pyogrio
        config=yaml.safe_load((Path(__file__).resolve().parents[1]/'config/grid.yaml').read_text(encoding='utf-8'))
        config.update(width=2,height=2,origin_x=0,origin_y=2000,vector_batch_size=2,vector_families=['litologia'])
        spec=grid_spec(config)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'vectors').mkdir();(root/'rasters').mkdir()
            geometries=[box(0,0,1000,1000),box(1000,0,2000,1000),box(0,1000,1000,2000),
                        box(1000,1000,2000,2000),box(3000,0,4000,1000),box(100000,0,101000,1000)]
            frame=gpd.GeoDataFrame({'code':['01','02','03','04','05','06']},geometry=geometries,crs=25830)
            frame.to_file(root/'input.gpkg',layer='rocks')
            frac,summary=harmonize_vectors(root,{'litologia':'input.gpkg'},box(0,0,2000,2000),
                                           np.full((4,4),250000.),spec,root)
            self.assertEqual(summary.read_bbox.iloc[0],5)
            self.assertEqual(summary.kept_with_margin.iloc[0],5)
            result=pyogrio.read_dataframe(root/'vectors/litologia.gpkg')
            self.assertEqual(set(result.code),{'01','02','03','04','05'})
            self.assertTrue(result.source_fid.is_unique)
            np.testing.assert_allclose(frac['litologia'],1)


if __name__ == '__main__':
    unittest.main()
