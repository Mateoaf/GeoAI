import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from geoau import evaluation as ev


def fixture():
    row, col = np.indices((40, 40))
    grid = pd.DataFrame({'cell_id': [f'c{i}' for i in range(row.size)],
                         'row': row.ravel(), 'col': col.ravel()})
    grid['x_center'] = grid.col * 1000 + 500
    grid['y_center'] = grid.row * 1000 + 500
    grid['land_area_m2'] = 1e6
    grid['eligible'] = True
    p = grid[(grid.row % 4 == 1) & (grid.col % 4 == 1)]
    relations = p[['cell_id']].copy().reset_index(drop=True)
    relations['record_id'] = relations.cell_id
    relations['deposit_id'] = None
    relations['district_id'] = None
    relations['proximity_group_500m'] = relations.cell_id
    relations['elegible_general_revisada'] = False
    cfg = dict(mode='diagnostic', target='general', block_size_m=4000,
               sensitivity_block_sizes_m=[4000, 8000], outer_folds=3,
               inner_folds=2, minimum_positive_units_test=1,
               minimum_positive_units_train=2, seed=42, reserve_district_ids=[],
               holdout_fraction=.1, spatial_gap_m=1000, background_buffer_m=250,
               diagnostic_group_column='proximity_group_500m', ratios_u_to_p=[1, 3],
               realizations=2)
    return cfg, grid, relations, dict(height=40, width=40, resolution_m=1000), None


class EvaluationTests(unittest.TestCase):
    def test_fold_reproducibility(self):
        self.assertEqual(ev.assign_fold(['a', 'b', 'c'], 2, 3),
                         ev.assign_fold(['c', 'b', 'a', 'a'], 2, 3))

    def test_transitive_groups(self):
        _, grid, _, _, _ = fixture()
        rel = pd.DataFrame({'cell_id': ['c0', 'c4', 'c4', 'c8'],
                            'deposit_id': ['a', 'a', 'b', 'b']})
        units, _ = ev.connected_units(grid, rel, 4000, 1000, ['deposit_id'])
        self.assertEqual(units.set_index('cell_id').loc[['c0', 'c4', 'c8'], 'unit_id'].nunique(), 1)

    def test_distance_is_conservative(self):
        _, grid, _, spec, _ = fixture()
        lower = ev.distance_lower_bound(grid, grid.cell_id.eq('c0').to_numpy(), spec)
        self.assertAlmostEqual(lower[4], 4000 - np.sqrt(2) * 1000)
        self.assertLessEqual(lower[4], 3000)  # Actual distance between square edges.

    def test_test_labels_do_not_change_background(self):
        _, grid, _, _, _ = fixture()
        membership = grid[['cell_id']].assign(role=np.where(grid.col < 20, 'train', 'test'))
        p1, u1 = ev.background_pool(grid, membership, {'c41'}, 250, 1000)
        p2, u2 = ev.background_pool(grid, membership, {'c41', 'c39'}, 250, 1000)
        pd.testing.assert_frame_equal(u1, u2)
        pd.testing.assert_frame_equal(p1, p2)

    def test_two_stage_inclusion(self):
        pool = pd.DataFrame({'cell_id': list('abcdef'), 'block_id': ['a']*2+['b']*2+['c']*2,
                             'land_area_m2': [1.]*6})
        sample, allocation = ev.stratified_u(pool, 1, 42)
        self.assertEqual(len(sample), 1)
        np.testing.assert_allclose(allocation.cell_inclusion_probability, 1/6)
        self.assertEqual(sample.inverse_inclusion_weight.iloc[0], 6)

    def test_sample_cap_and_reproducibility(self):
        pool = pd.DataFrame({'cell_id': list('abcdef'), 'block_id': ['a']*2+['b']*4,
                             'land_area_m2': [1.]*6})
        a, _ = ev.stratified_u(pool, 4, 42)
        b, _ = ev.stratified_u(pool.sample(frac=1), 4, 42)
        pd.testing.assert_frame_equal(a, b)
        all_rows, _ = ev.stratified_u(pool, 100, 42)
        self.assertEqual(len(all_rows), 6)
        self.assertTrue(all_rows.inclusion_probability.eq(1).all())

    def test_candidate_is_not_reviewed(self):
        cfg, grid, rel, _, _ = fixture()
        selected, reviewed = ev.choose_labels(grid, rel, cfg)
        self.assertGreater(len(selected), 0)
        self.assertTrue(reviewed.empty)
        cfg['mode'] = 'validated'
        self.assertTrue(ev.choose_labels(grid, rel, cfg)[0].empty)

    def test_reject_string_boolean(self):
        cfg, grid, rel, _, _ = fixture()
        rel['elegible_general_revisada'] = 'False'
        with self.assertRaises(ValueError): ev.choose_labels(grid, rel, cfg)

    def test_readiness_requires_scientific_inputs(self):
        cfg, grid, rel, _, _ = fixture()
        cfg.update(phase_d_run='d', protocol_reviewed=False)
        with patch.object(ev, 'read_json', return_value={'approved_training_columns': []}):
            gate = ev.readiness(Path('.'), cfg, grid, rel, None)
        self.assertFalse(gate['ready_for_scientific_training'])
        self.assertEqual(gate['reviewed_positive_cells'], 0)
        self.assertGreaterEqual(len(gate['reasons']), 6)

    def test_validated_mode_cannot_bypass_readiness(self):
        cfg, grid, rel, spec, groupmap = fixture()
        cfg['mode'] = 'validated'
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'config').mkdir()
            import yaml
            (root/'config/evaluation.yaml').write_text(yaml.safe_dump(cfg), encoding='utf-8')
            with patch.object(ev, 'source_data', return_value=(root, grid, rel, spec, groupmap)), \
                 patch.object(ev, 'readiness', return_value={'ready_for_scientific_training': False,
                                                             'reasons': ['No reviewed positives']}):
                with self.assertRaisesRegex(ValueError, 'Modo validado'):
                    ev.start_run(root)

    def test_manifest_tampering(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder); p = base/'x.txt'; p.write_text('original')
            entries = ev.records(base, [p]); ev.verify(base, entries)
            p.write_text('modified')
            with self.assertRaises(ValueError): ev.verify(base, entries)

    def test_nested_pipeline(self):
        data = fixture()
        with tempfile.TemporaryDirectory() as folder, patch.object(ev, 'context', return_value=data):
            out = Path(folder); (out/'design').mkdir()
            summary = ev.build_splits(out, out)
            samples = ev.build_samples(out, out)
            self.assertEqual(len(summary), 9)
            self.assertEqual(len(samples), 36)
            ev.verify(out, ev.read_json(out/'splits_manifest.json'))
            ev.verify(out, ev.read_json(out/'samples_manifest.json'))
            for item in ev.read_json(out/'split_plan.json')['splits']:
                membership = pd.read_parquet(out/f"memberships/{item['split_id']}.parquet")
                if item['level'] == 'inner':
                    outer = pd.read_parquet(out/f"memberships/outer_{item['outer_fold']:02d}.parquet")
                    self.assertTrue(set(membership.loc[membership.role.isin(['train', 'test']), 'cell_id']) <=
                                    set(outer.loc[outer.role.eq('train'), 'cell_id']))
            for sample_id in samples.sample_id:
                sample = pd.read_parquet(out/f'samples/{sample_id}.parquet')
                self.assertTrue(sample.cell_id.is_unique)
                self.assertFalse(sample.training_allowed.any())
                self.assertEqual(set(sample.sample_role), {'P_candidate_proxy', 'U_unlabelled'})


if __name__ == '__main__': unittest.main()
