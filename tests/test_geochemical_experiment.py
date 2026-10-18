"""Invariantes del experimento geoquímico, sin entrenamientos nacionales."""
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from geoau.geochemical_experiment import (
    ExperimentData, WeightedPUBaggingClassifier, consolidate_positives,
    make_preprocessor, ranked_cells, rotation_pools, spatial_splits,
)


class GeochemicalExperimentTests(unittest.TestCase):
    def test_confirmed_cell_weight_has_priority_independent_of_order(self):
        records = pd.DataFrame({"cell_id": ["a", "a", "b", "c"], "record_id": ["r1", "r2", "r3", "r4"],
                                "estado_presencia": ["pendiente", "confirmada", "pendiente", "rechazada"]})
        expected = consolidate_positives(records)
        pd.testing.assert_frame_equal(expected, consolidate_positives(records.iloc[::-1]))
        self.assertEqual(expected.cell_id.tolist(), ["a", "b"])
        self.assertEqual(expected.peso_confianza.tolist(), [1., .5])
        self.assertEqual(expected.n_records.tolist(), [2, 1])

    def test_zero_geochemical_class_is_not_missing(self):
        X = pd.DataFrame({"numeric": [1., 2., 3., 4.], "as_clase_modal": [0., np.nan, 1., 0.]})
        pre = make_preprocessor(X.columns.tolist(), ["as_clase_modal"])
        transformed = pre.fit_transform(X)
        self.assertFalse(np.array_equal(transformed[0, 1:], transformed[1, 1:]))
        categories = pre.named_transformers_["geochemical"].named_steps["encode"].categories_[0]
        self.assertIn(-1, categories)
        self.assertIn(0, categories)

    def test_imputation_and_scaling_are_fitted_only_on_training(self):
        X = pd.DataFrame({"numeric": [1., 3., np.nan], "as_clase_modal": [0., 1., np.nan]})
        pre = make_preprocessor(X.columns.tolist(), ["as_clase_modal"])
        pre.fit(X)
        imputer = pre.named_transformers_["numeric"].named_steps["impute"]
        self.assertEqual(imputer.statistics_[0], 2.)
        test = pd.DataFrame({"numeric": [1e9, np.nan], "as_clase_modal": [7., np.nan]})
        self.assertTrue(np.isfinite(pre.transform(test)).all())
        self.assertEqual(imputer.statistics_[0], 2.)
        self.assertNotIn(7, pre.named_transformers_["geochemical"].named_steps["encode"].categories_[0])

    def test_spatial_folds_exclude_blocks_and_buffer(self):
        positions = [0, 10000, 100000, 150000, 200000, 250000]
        sample = pd.DataFrame({"cell_id": [f"c{i}" for i in range(12)],
            "block_id": [f"b{i}" for i in range(6) for _ in range(2)],
            "x_center": [x + delta for x in positions for delta in (0, 100)],
            "y_center": 0., "label": [0, 1] * 6})
        splits = spatial_splits(sample, n_splits=2, buffer_m=15000)
        tested = []
        for train, test, excluded in splits:
            self.assertFalse(set(sample.iloc[train].block_id) & set(sample.iloc[test].block_id))
            distance = cKDTree(sample.iloc[test][["x_center", "y_center"]]).query(sample.iloc[train][["x_center", "y_center"]])[0]
            self.assertTrue((distance >= 15000).all())
            self.assertFalse(set(train) & set(excluded))
            tested.extend(test)
        self.assertEqual(sorted(tested), list(range(len(sample))))

    def test_rotation_excludes_entire_blocks_and_nearby_unassigned_cells(self):
        grid = pd.DataFrame({"cell_id": ["held", "same_block", "near", "far"],
                             "block_id": ["b0", "b0", "b1", "b2"],
                             "x_center": [0., 1000., 10000., 50000.], "y_center": 0.})
        records = pd.DataFrame({"cell_id": ["held", "same_block", "near", "far"],
                                "district_id": ["reserved", None, None, "other"]})
        data = ExperimentData(Path("."), {"rotation_buffer_m": 15000}, Path("."), Path("."),
                              grid, pd.DataFrame(), records, pd.DataFrame(), [], {}, {}, {})
        train, held = rotation_pools(data, {"reserved"})
        self.assertEqual(train.cell_id.tolist(), ["far"])
        self.assertEqual(held.cell_id.tolist(), ["held", "same_block"])

    def test_ties_are_resolved_by_cell_id_without_using_labels(self):
        ids = np.array(["c", "a", "b"])
        rank = ranked_cells(ids, [.5, .5, .5])
        self.assertEqual(dict(zip(ids, rank)), {"a": 1, "b": 2, "c": 3})
        order = np.array([2, 0, 1])
        self.assertEqual(dict(zip(ids[order], ranked_cells(ids[order], [.5] * 3))), dict(zip(ids, rank)))

    def test_bagging_keeps_positives_and_resamples_only_background(self):
        X = np.arange(60, dtype=float).reshape(20, 3)
        y = np.array([1] * 4 + [0] * 16)
        weight = np.array([1., .5, 1., .5] + [1.] * 16)
        model = WeightedPUBaggingClassifier(n_bags=2, u_per_p=2, n_jobs=1, random_state=7)
        model.fit(X, y, sample_weight=weight)
        for indices in model.sample_indices_:
            self.assertEqual(set(indices[:4]), {0, 1, 2, 3})
            self.assertEqual(len(indices), 12)
            self.assertEqual(len(set(indices)), 12)
        self.assertFalse(np.array_equal(model.sample_indices_[0], model.sample_indices_[1]))
        probabilities = model.predict_proba(X)
        self.assertTrue(np.isfinite(probabilities).all())
        np.testing.assert_allclose(probabilities.sum(axis=1), 1.)


if __name__ == "__main__":
    unittest.main()
