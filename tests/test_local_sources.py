"""Controles sobre fallos reales de ingestión, sin modificar los datos del proyecto."""
from pathlib import Path
from contextlib import closing
import sqlite3
import sys
import tempfile
import unittest

import numpy as np
import geopandas as gpd
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import Point

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from geoau.local_sources import (read_table, iter_csv, gpkg_info, read_vector,
    read_raster_window, read_raster_preview, local_path, sha256_file, verify_unchanged)


class LocalSourcesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_ids_and_csv_logical_rows(self):
        path = self.root / 'indicios.csv'
        path.write_text('Codigo_indicio,Nombre\n0001001,"texto\nen dos líneas"\n0001002,NA\n', encoding='utf-8-sig')
        data = read_table(path, nrows=None)
        self.assertEqual(data.Codigo_indicio.tolist(), ['0001001', '0001002'])
        self.assertEqual(data.Nombre.iloc[1], 'NA')
        with iter_csv(path, chunksize=1) as blocks:
            self.assertEqual(sum(len(b) for b in blocks), 2)

    def test_empty_geopackage_not_created_or_loaded(self):
        path = self.root / 'empty.gpkg'
        with closing(sqlite3.connect(path)) as con:
            con.execute('create table gpkg_contents (table_name text)')
            con.execute('create table gpkg_geometry_columns (table_name text)')
        before = sha256_file(path)
        self.assertEqual(gpkg_info(path), [])
        with self.assertRaisesRegex(ValueError, 'no contiene capas'):
            read_vector(path)
        self.assertEqual(before, sha256_file(path))
        missing = self.root / 'missing.gpkg'
        with self.assertRaises(sqlite3.OperationalError):
            gpkg_info(missing)
        self.assertFalse(missing.exists())

    def test_window_mask_zero_and_transform(self):
        path = self.root / 'classes.tif'
        values = np.array([[0, -9999, 2], [3, 4, 5]], dtype='int16')
        with rasterio.open(path, 'w', driver='GTiff', width=3, height=2, count=1,
                           dtype='int16', crs='EPSG:25830', transform=from_origin(0, 20, 10, 10), nodata=-9999) as dst:
            dst.write(values, 1)
        data, info = read_raster_window(path, col_off=0, row_off=0, width=2, height=2)
        self.assertFalse(data.mask[0, 0, 0])
        self.assertTrue(data.mask[0, 0, 1])
        self.assertEqual(data[0, 0, 0], 0)
        cropped, info = read_raster_window(path, col_off=1, row_off=1, width=2, height=1)
        self.assertEqual(info['transform'][2], 10)
        self.assertEqual(info['transform'][5], 10)
        preview, _ = read_raster_preview(path, side=2)
        self.assertTrue(set(preview.compressed()).issubset(set(values.ravel())))
        with self.assertRaises(ValueError):
            read_raster_window(path, col_off=2, row_off=0, width=2, height=2)

    def test_bbox_transforms_and_full_load_guard(self):
        path = self.root / 'points.gpkg'
        data = gpd.GeoDataFrame({'code': ['0001', '0002']}, geometry=[Point(-3, 40), Point(0, 45)], crs=4326).to_crs(3857)
        data.to_file(path, layer='points', driver='GPKG', engine='pyogrio')
        selected = read_vector(path, bbox=(-3.1, 39.9, -2.9, 40.1), bbox_crs=4326)
        self.assertEqual(selected.code.tolist(), ['0001'])
        self.assertEqual(selected.crs.to_epsg(), 3857)
        with self.assertRaises(ValueError):
            read_vector(path, bbox=(-4, 39, -2, 41))
        with self.assertRaises(ValueError):
            read_vector(path, max_features=None)

    def test_curved_geometry_requires_explicit_preview(self):
        path = self.root / 'curve.gpkg'
        gpd.GeoDataFrame({'a': [1]}, geometry=[Point(0, 0)], crs=4326).to_file(path, layer='curve', driver='GPKG')
        with closing(sqlite3.connect(path)) as con:
            # Solo metadata para comprobar la protección antes de que intervenga GDAL.
            con.execute("update gpkg_geometry_columns set geometry_type_name='MULTICURVE'")
            con.commit()
        with self.assertRaisesRegex(ValueError, 'Geometría curva'):
            read_vector(path)

    def test_reject_network_escape_and_detect_same_size_change(self):
        with self.assertRaises(ValueError):
            local_path(self.root, 'https://example.com/datos.csv')
        with self.assertRaises(ValueError):
            local_path(self.root, '../escape.csv')
        p = self.root / 'data.csv'
        p.write_bytes(b'123')
        s = p.stat()
        row = {'path': p.name, 'bytes': s.st_size, 'mtime_ns': s.st_mtime_ns, 'sha256': sha256_file(p)}
        p.write_bytes(b'456')
        import os
        os.utime(p, ns=(s.st_atime_ns, s.st_mtime_ns))
        self.assertEqual(verify_unchanged(self.root, [row], rehash=True)[0]['reason'], 'SHA-256 diferente')


if __name__ == '__main__':
    unittest.main()
