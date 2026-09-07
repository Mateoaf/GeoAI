from pathlib import Path
import sys
import unittest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from geoau.labels import (normalize_indicios, substance_tokens, reconcile, apply_reviews,
    geometry_qc, group_candidates, define_labels, REVIEW_FIELDS)


class LabelTests(unittest.TestCase):
    def setUp(self):
        self.cfg = yaml.safe_load((ROOT/'config/labels.yaml').read_text(encoding='utf8'))
        self.cfg['source_sha256'] = 'fixture_hash'

    def data(self, substances=('Oro','Fluorita'), coords=((-3,40),(-2,40))):
        return gpd.GeoDataFrame({
            'Codigo_indicio': [f'{i:07}' for i in range(len(substances))],
            'Sustancia': list(substances), 'Morfologia': ['Filoniana']*len(substances),
            'Nombre_mina': ['Prueba']*len(substances), 'Provincia': ['Madrid']*len(substances),
            'Municipio': ['Madrid']*len(substances), 'X': [p[0] for p in coords], 'Y': [p[1] for p in coords],
        },geometry=[Point(*p) for p in coords],crs=4326)

    def prepared(self, data=None):
        clean = normalize_indicios(self.data() if data is None else data, self.cfg)
        clean['conflicto_au'] = False
        reviewed, _ = apply_reviews(clean)
        return geometry_qc(reviewed, self.cfg)

    def test_exact_tokens_raw_and_no_negative(self):
        data = self.data((' Oro ; Au | Arsénico ', 'Bauxita, Fluorita'), ((-3,40),(-2,40)))
        out = normalize_indicios(data,self.cfg)
        self.assertEqual(out.label_observada.tolist(),['P','U'])
        self.assertEqual(out.Codigo_indicio.iloc[0],'0000000')
        self.assertEqual(out.Sustancia_raw.iloc[0],data.Sustancia.iloc[0])
        self.assertEqual(substance_tokens('Tierras raras / Monacita, ORO'), ['oro','tierras raras / monacita'])
        self.assertTrue(out.sistema_mineral.eq('no_determinado').all())

    def test_reconciliation_does_not_multiply_duplicates(self):
        data = self.data().drop(columns='geometry')
        copy = pd.concat([data.iloc[[0]],data.iloc[[0]],data.iloc[[1]]],ignore_index=True)
        copy.loc[0,'Sustancia']='Cobre'
        rec, dups = reconcile({'gpkg':data,'csv':copy,'excel':data})
        self.assertEqual(len(rec),2)
        self.assertEqual(rec.iloc[0].n_csv,2)
        self.assertEqual(len(dups),2)
        self.assertTrue(rec.iloc[0].conflicto_au)
        self.assertTrue(rec.iloc[0].au_mixto_csv)
        copy.loc[1,'Sustancia']='Cobre'
        rec, _ = reconcile({'gpkg':data,'csv':copy,'excel':data})
        self.assertTrue(rec.iloc[0].conflicto_au)

    def test_bad_xy_does_not_relocate_geometry(self):
        data=self.data();data.loc[0,'X']=500000;data.loc[0,'Y']=4400000
        out=self.prepared(data)
        self.assertEqual(out.xy_estado.iloc[0],'crs_tabular_desconocido')
        self.assertEqual(out.geometry.iloc[0],Point(-3,40))
        self.assertFalse(out.geo_cuarentena.iloc[0])
        self.assertEqual(out.territorio_estado.iloc[0],'pendiente_mascara')

    def test_mask_and_bad_latitude_quarantine(self):
        out=self.prepared(self.data(coords=((-3,4),(-2,40))))
        self.assertTrue(out.geo_cuarentena.iloc[0])
        mask=gpd.GeoDataFrame(geometry=[Polygon([(-3,39),(-1,39),(-1,41),(-3,41)])],crs=4326)
        out=geometry_qc(out,self.cfg,mask=mask)
        self.assertEqual(out.territorio_estado.tolist(),['fuera_mascara','dentro_mascara'])

    def test_transitive_proximity_is_not_deposit_and_is_order_stable(self):
        out=self.prepared(self.data(('Oro',)*3,((-3,40),(-2.9975,40),(-2.995,40))))
        grouped,pairs,counts=group_candidates(out,(250,500,1000))
        self.assertEqual(grouped.proximity_group_250m.nunique(),1)
        self.assertEqual(grouped.position_id.nunique(),3)
        self.assertTrue(grouped.deposit_id.eq('').all())
        shuffled,_,_=group_candidates(out.iloc[::-1],(250,500,1000))
        a=grouped.set_index('record_id').proximity_group_250m.sort_index()
        b=shuffled.set_index('record_id').proximity_group_250m.sort_index()
        pd.testing.assert_series_equal(a,b)
        self.assertFalse(define_labels(grouped).elegible_general_revisada.any())

    def test_review_requires_evidence_and_versions_and_preserves_raw(self):
        clean=normalize_indicios(self.data(),self.cfg)
        row={f:'' for f in REVIEW_FIELDS}
        row.update(record_id=clean.record_id.iloc[0],estado_presencia='confirmada',estado_geometria='validada',
                   tipo_au_revisado='roca',lon_corregida='-3.1',lat_corregida='40.1')
        with self.assertRaises(ValueError):apply_reviews(clean,pd.DataFrame([row]))
        row.update(revisor='test',fecha_revision='2026-09-06',evidencia='documento de prueba',motivo='prueba')
        out,log=apply_reviews(clean,pd.DataFrame([row]))
        self.assertEqual(out.geometry.iloc[0],Point(-3.1,40.1))
        self.assertEqual(out.geometry_wkt_raw.iloc[0],Point(-3,40).wkt)
        self.assertTrue(log.campo.eq('geometry').any())
        qc=geometry_qc(out,self.cfg)
        labels=define_labels(qc)
        self.assertTrue(labels.elegible_roca_revisada.iloc[0])
        row['record_id']='gpkg:otra_version:0'
        with self.assertRaises(ValueError):apply_reviews(clean,pd.DataFrame([row]))


if __name__=='__main__':unittest.main()
