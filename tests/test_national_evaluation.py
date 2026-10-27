"""Protect spatial holdouts and the territorial recovery unit in national evaluation."""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from geoau.national_evaluation import cv_training_pool, deposit_metrics


class NationalEvaluationTests(unittest.TestCase):
    def test_unsampled_background_respects_whole_blocks_buffer_and_unassigned_blocks(self):
        sample = pd.DataFrame({"cell_id": ["test", "train", "reserved"],
            "block_id": ["A", "B", "R"], "x_center": [0., 60000., 120000.], "y_center": 0.})
        extra = pd.DataFrame({"cell_id": ["same_block_far", "too_close", "allowed_u", "unassigned"],
            "block_id": ["A", "B", "B", "X"],
            "x_center": [40000., 14000., 50000., 100000.], "y_center": 0.})
        grid = pd.concat([sample, extra], ignore_index=True)
        roles = pd.DataFrame({"cell_id": ["test", "train", "reserved"],
                              "fold": [0, 1, 1], "role": "validation"})
        data = SimpleNamespace(grid=grid, config={"cv_buffer_m": 15000})
        pool = cv_training_pool(data, sample, roles, 0, ["R"])
        self.assertEqual(set(pool.cell_id), {"train", "allowed_u"})

    def test_recovery_counts_deposits_once_and_has_an_exact_label_independent_budget(self):
        predictions = pd.DataFrame({"cell_id": [f"c{i:03d}" for i in range(100)], "score": np.ones(100)})
        relations = pd.DataFrame({"cell_id": ["c000", "c001", "c004", "c005", "c099"],
                                   "deposit_id": ["a", "a", "b", "c", "d"]})
        metrics, detail, ranked = deposit_metrics(relations, predictions.sample(frac=1, random_state=17))
        self.assertEqual(metrics["captured_deposits_at_01"], 1)
        self.assertEqual(metrics["captured_deposits_at_05"], 2)
        self.assertEqual(metrics["captured_deposits_at_10"], 3)
        self.assertEqual(metrics["captured_deposits_at_20"], 3)
        self.assertAlmostEqual(metrics["recovery_at_01"], 0.25)
        self.assertAlmostEqual(metrics["recovery_at_20"], 0.75)
        self.assertEqual(int((ranked["rank"] <= 5).sum()), 5)
        self.assertEqual(metrics["n_deposits"], 4)

    def test_missing_deposit_cell_is_an_error_not_an_uncaptured_deposit(self):
        with self.assertRaises(ValueError):
            deposit_metrics(pd.DataFrame({"cell_id": ["missing"], "deposit_id": ["a"]}),
                            pd.DataFrame({"cell_id": ["c0"], "score": [.5]}))


if __name__ == "__main__":
    unittest.main()
