"""Separa calibración de test y verifica presupuesto, métricas y corrección PU."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from geoau.geochemical_experiment import label_metrics
from geoau.validation_diagnostics import (
    ElkanNotoEnsemble, calibration_partition, correct_scores, estimate_c,
    fit_elkan_noto, validation_splits,
)


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.cfg = {"cv_folds": 5, "en_calibration_folds": 5, "cv_buffer_m": 15000}
        self.sample = pd.DataFrame({"cell_id": [f"c{i:03d}" for i in range(100)],
            "block_id": [f"b{i//2:03d}" for i in range(100)], "label": [0, 1] * 50,
            "x_center": [i//2*50000 + i%2*100 for i in range(100)], "y_center": 0.})

    def test_spatial_strategies_share_validation_blocks(self):
        spatial = validation_splits(self.sample, "spatial", self.cfg, 42)
        buffered = validation_splits(self.sample, "buffered", self.cfg, 42)
        for (_, va, _), (tr_buffer, va_buffer, _) in zip(spatial, buffered):
            np.testing.assert_array_equal(va, va_buffer)
            self.assertFalse(set(self.sample.iloc[tr_buffer].block_id) & set(self.sample.iloc[va_buffer].block_id))

    def test_random_split_covers_each_sample_once_and_is_reproducible(self):
        first = validation_splits(self.sample, "random", self.cfg, 42)
        second = validation_splits(self.sample, "random", self.cfg, 42)
        self.assertEqual(sorted(np.concatenate([va for _, va, _ in first]).tolist()), list(range(100)))
        for (tr, va, _), (_, again, _) in zip(first, second):
            np.testing.assert_array_equal(va, again)
            self.assertFalse(set(tr) & set(va))

    def test_internal_calibration_cannot_include_outer_validation(self):
        for strategy in ["random", "spatial", "buffered"]:
            for train, test, _ in validation_splits(self.sample, strategy, self.cfg, 42):
                inner = self.sample.iloc[train].reset_index(drop=True)
                fit, cal, excluded = calibration_partition(inner, strategy, self.cfg, 17)
                self.assertFalse(set(fit) & set(cal))
                self.assertFalse(set(inner.iloc[cal].cell_id) & set(self.sample.iloc[test].cell_id))
                self.assertFalse(set(inner.iloc[fit].cell_id) & set(self.sample.iloc[test].cell_id))
                self.assertEqual(set(np.concatenate([fit, cal, excluded])), set(range(len(inner))))

    def test_c_uses_only_held_out_positive_predictions(self):
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        data = SimpleNamespace(config=dict(self.cfg, pu_bags=1, en_c_min=1e-6,
                                          geochemical_columns=[]), feature_columns=["x"],
            features=pd.DataFrame({"x": np.arange(100.)}, index=self.sample.cell_id))
        sample = self.sample.assign(peso_confianza=1.)
        # A small estimator with the interface of the PU ensemble exercises the full fit path.
        class MiniPU:
            def fit(self, X, y, sample_weight=None):
                self.estimators_ = [LogisticRegression().fit(X, y, sample_weight=sample_weight)]
                return self
        pipeline = Pipeline([("preprocess", StandardScaler()), ("model", MiniPU())])
        with patch("geoau.validation_diagnostics.make_model", return_value=pipeline):
            model, membership, predictions = fit_elkan_noto(data, sample, "random", 42)
        fit_ids = set(membership.loc[membership.role.eq("fit"), "cell_id"])
        self.assertFalse(fit_ids & set(predictions.cell_id))
        self.assertTrue(sample.set_index("cell_id").loc[predictions.cell_id, "label"].eq(1).all())
        self.assertAlmostEqual(model.c_mean, predictions.member_00.mean())
        self.assertTrue(np.isfinite(model.predict_proba(data.features)).all())

    def test_invalid_c_estimates_fail_instead_of_silent_fallback(self):
        self.assertAlmostEqual(estimate_c([.2, .4]), .3)
        for values in [[], [0, 0], [np.nan], [1.1]]:
            with self.assertRaises(ValueError):
                estimate_c(values)
        with self.assertRaises(ValueError):
            correct_scores([.3], 0)

    def test_member_wise_rescaling_clips_before_averaging(self):
        model = ElkanNotoEnsemble(None, [.25, .5])
        with patch.object(model, "member_scores", return_value=np.array([[.5, .2], [.1, .1]])):
            np.testing.assert_allclose(model.predict_proba(None)[:, 1], [.7, .3])
        self.assertFalse(np.isclose(.7, np.mean([.5, .2]) / np.mean([.25, .5])))

    def test_ties_at_one_do_not_inflate_recovery_budget(self):
        y = np.array([1] * 20 + [0] * 80)
        metrics = label_metrics(y, np.ones(100), [f"c{i:03d}" for i in range(100)])
        self.assertEqual(metrics["positive_cell_recovery_at_05"], 5 / 20)
        self.assertEqual(metrics["positive_cell_recovery_at_10"], 10 / 20)
        self.assertAlmostEqual(metrics["brier_loss"], .8)
        self.assertIn("pr_auc_trapezoid", metrics)


if __name__ == "__main__":
    unittest.main()
