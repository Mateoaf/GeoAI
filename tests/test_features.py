"""Casos geocientíficos pequeños con respuestas conocidas, sin fuentes nacionales."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import shapely
import pandas as pd
from geoau import features as fd
from geoau.features import (structural_class, categorical_areas, nearest_distances,
    line_lengths, terrain_arrays, color_quality, records, verify_records, disk_kernel)

class FeatureTests(unittest.TestCase):
    def test_fast_clip_preserves_coast_holes_and_boundary(self):
        mask=shapely.box(0,0,10,10).difference(shapely.box(4,4,6,6))
        geoms=np.array([shapely.box(1,1,3,3),shapely.box(3,3,7,7),shapely.box(-1,-1,1,1),
                         shapely.LineString([(0,0),(0,10)])])
        result=fd.clip_to_mask(geoms,mask)
        self.assertTrue(shapely.equals(result,shapely.intersection(geoms,mask)).all())
    def test_false_structures_and_uncertainty(self):
        for s in ['Masas de agua','Borde de hoja','Contacto concordante',None,'símbolo']:
            self.assertEqual(structural_class(s),'excluido')
        self.assertEqual(structural_class('Falla supuesta (oculta)'),'falla_supuesta')
        self.assertEqual(structural_class('Cabalgamiento'),'cabalgamiento_cartografiada')
        self.assertEqual(structural_class('Contacto intrusivo'),'contacto_intrusivo_cartografiada')

    def test_exact_polygon_area_and_overlap(self):
        cell=np.array([shapely.box(0,0,10,10)],dtype=object)
        polys=np.array([shapely.box(0,0,7,10),shapely.box(5,0,10,10)],dtype=object)
        cats,mass,area,overlap=categorical_areas(polys,['a','b'],cell)
        np.testing.assert_allclose(mass,[[70,50]])
        np.testing.assert_allclose(area,[100]);np.testing.assert_allclose(overlap,[20])
        _,mass,area,overlap=categorical_areas(polys,['a','a'],cell)
        np.testing.assert_allclose(mass,[[100]]);np.testing.assert_allclose(overlap,[0])

    def test_distance_no_trace_is_not_zero(self):
        points=shapely.points([0,30],[0,0]);lines=np.array([shapely.LineString([(3,-1),(3,1)])])
        d=nearest_distances(points,lines,10)
        self.assertEqual(d[0],3);self.assertTrue(np.isnan(d[1]))

    def test_length_duplicate_and_cell_boundary(self):
        cells=np.array([shapely.box(0,0,10,10),shapely.box(10,0,20,10)])
        line=shapely.LineString([(10,0),(10,10)])
        np.testing.assert_allclose(line_lengths(np.array([line,line]),cells),[5,5])
        line=shapely.LineString([(0,5),(20,5)])
        np.testing.assert_allclose(line_lengths(np.array([line,line]),cells),[10,10])

    def test_plane_slope_and_hole(self):
        z=np.tile(np.arange(21)*500.,(21,1));valid=np.ones(z.shape,bool)
        d=terrain_arrays(z,valid,500,[1000],1)
        self.assertAlmostEqual(d['pendiente_grados'][10,10],45)
        self.assertAlmostEqual(d['tpi_1000m_m'][10,10],0)
        valid[10,11]=False
        d=terrain_arrays(z,valid,500,[1000],1)
        self.assertTrue(np.isnan(d['pendiente_grados'][10,10]))
        self.assertTrue(np.isnan(d['tpi_1000m_m'][10,10]))

    def test_zero_class_rgb_mismatch_and_mask(self):
        rgb=np.array([[[1,9],[1,1]],[[2,9],[2,2]],[[3,9],[3,3]]])
        classes=np.array([[0.,0.],[0.,-9999.]])
        good,d=color_quality(rgb,classes,np.array([[True,True],[False,True]]),[(0,[1,2,3])])
        np.testing.assert_array_equal(good,[[True,False],[False,False]])

    def test_disk_area_and_tamper(self):
        self.assertAlmostEqual(disk_kernel(1000,1000,True).sum(),np.pi,places=3)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'input.txt';p.write_text('original')
            rec=records(root,[p]);verify_records(root,rec)
            p.write_text('cambiado')
            with self.assertRaises(ValueError): verify_records(root,rec)

    def test_master_many_indications_unknown_and_no_label_leak(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);out=root/'d';out.mkdir();(out/'blocks').mkdir()
            c=root/'c';c.mkdir()
            grid=pd.DataFrame({'cell_id':['a','b','c'],'row':[0,100,200],
                               'land_area_m2':[1e6]*3,'coastal_eligible':[True]*3})
            grid.to_csv(c/'coverage_by_cell.csv.gz',index=False)
            for block in fd.BLOCKS:
                x=grid[['cell_id']].assign(**{block+'_value':[1.,2.,np.nan]})
                if block=='geology':
                    x['litologia_dominante']=['u1','u2',None];x['edades_dominante']=['e1','e2',None]
                if block=='terrain':
                    x['pendiente_grados']=[10.,20.,np.nan];x['elevacion_media_m']=[100.,200.,np.nan]
                if block=='geochemistry':
                    for element in ('au','as','sb','bi','hg','cu','pb','zn','w'):x[element+'_clase_modal']=[0.,1.,np.nan]
                fd.finish_block(out,block,x,grid[['cell_id']].copy(),[fd.meta(n,block,'m','fixture') for n in x if n!='cell_id'])
            labels=pd.DataFrame({'record_id':['p1','p2','p3','p4'],'Codigo_indicio':['001','002','003','004'],
                'cell_id':['a','a','b',None],'positivo_revisado':[False,False,True,False],
                'deposit_id':[None]*4,'district_id':[None]*4,'proximity_group_500m':['g','g','h',None]})
            spec={'scope':'fixture','grid_version':'fixture_v1'}
            fd.write_json(c/'grid_spec.json',spec)
            with patch.object(fd,'context',return_value=({},c,spec,grid,None)), \
                 patch.object(fd,'label_relations',return_value=labels), \
                 patch.object(fd,'geological_associations',side_effect=lambda x,out:(x,[])):
                x,q,y=fd.assemble(root,out)
            self.assertEqual(len(x),3)
            self.assertEqual(y.n_candidatos.tolist(),[2,1,0])
            self.assertEqual(y.estado_etiqueta.tolist(),['candidato_no_revisado','P_revisado','U'])
            self.assertNotIn('n_candidatos',x)
            self.assertEqual(fd.read_json(out/'feature_allowlist.json')['approved_training_columns'],[])
            full=pd.read_parquet(out/'Grid_Master_Au.parquet')
            self.assertIn('n_candidatos',full)
            self.assertEqual(len(pd.read_parquet(out/'Grid_Master_Au')),3)
            fd.verify_records(out,fd.read_json(out/'outputs_manifest.json'))

    def test_outer_edge_not_halved(self):
        cell=np.array([shapely.box(0,0,10,10)])
        line=np.array([shapely.LineString([(0,0),(0,10)])])
        np.testing.assert_allclose(line_lengths(line,cell),[10])

    def test_rgb_tolerance_and_ambiguity(self):
        rgb=np.array([[[106]],[[176]],[[158]]])
        palette=[(0,[105,176,159]),(1,[255,0,0])]
        good,_=color_quality(rgb,np.zeros((1,1)),np.ones((1,1),bool),palette,2,10)
        self.assertTrue(good[0,0])
        ambiguous=[(0,[105,176,159]),(1,[106,176,157])]
        good,_=color_quality(rgb,np.zeros((1,1)),np.ones((1,1),bool),ambiguous,2,10)
        self.assertFalse(good[0,0])

    def test_signature_rejects_changed_numeric_function(self):
        before='def geology():\n return 1\n'
        after='def geology():\n return 2\n'
        self.assertNotEqual(fd.compute_signature(before,'geology'),fd.compute_signature(after,'geology'))

    def test_matrix_rejects_bad_fraction(self):
        x=pd.DataFrame({'cell_id':['a'],'bad_fraccion':[1.1]})
        with self.assertRaises(ValueError):fd.validate_matrix(x,[fd.meta('bad_fraccion','x','fraccion','test')])

    def test_partition_retry_does_not_append(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)
            data=pd.DataFrame({'cell_id':['a','b','c'],'partition_id':[0,0,1],'value':[1.,2.,3.]})
            fd.write_master(data,out)
            data.loc[0,'value']=5.
            fd.write_master(data,out)
            result=pd.read_parquet(out/'Grid_Master_Au').sort_values('cell_id')
            self.assertEqual(len(result),3)
            self.assertEqual(result.value.tolist(),[5.,2.,3.])

if __name__=='__main__': unittest.main()
