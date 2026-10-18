"""Controles de fuga espacial, pérdidas, ranking y persistencia neuronal."""
from pathlib import Path
import sys
import tempfile
import unittest

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from geoau import neural_tabular as nn
from geoau import neural_u1 as u1
from geoau import neural_explain as nx


class TabularTests(unittest.TestCase):
    def test_log_preprocessing_train_only_unknown_and_empty(self):
        schema = {'columns': ['dist_falla_m', 'tpi_m', 'empty', 'cat'], 'categorical': ['cat']}
        train = pd.DataFrame({'dist_falla_m': [0., 100., np.nan, 1000.],
                              'tpi_m': [-3., 0., 3., 1.], 'empty': [np.nan]*4,
                              'cat': ['a', 'b', None, 'a']})
        pre = nn.make_preprocessor(schema, 'log_standard')
        pre.fit_transform(train)
        steps = pre.named_steps['preprocess'].named_transformers_['numeric'].named_steps
        np.testing.assert_allclose(steps['impute'].statistics_, [100., .5, 0.])
        np.testing.assert_allclose(steps['scale'].mean_[0], np.log1p([0., 100., 100., 1000.]).mean())
        np.testing.assert_allclose(steps['scale'].mean_[1], .25)
        test = pd.DataFrame({'dist_falla_m': [1e8], 'tpi_m': [-10.], 'empty': [np.inf], 'cat': ['new']})
        score = pre.transform(test)
        self.assertTrue(np.isfinite(score).all())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'pre.joblib'
            joblib.dump(pre, path)
            np.testing.assert_array_equal(score, joblib.load(path).transform(test))
        bad = test.copy(); bad['dist_falla_m'] = -1.
        with self.assertRaises(ValueError):
            pre.transform(bad)

    def test_area_budget_is_land_area_and_ties_are_deterministic(self):
        frame = pd.DataFrame({'observed_P': [True, False, True],
                              'land_area_m2': [10., 80., 10.], 'tie_key': [1, 0, 2]})
        self.assertEqual(nn.area_recovery(frame, [3, 2, 1], .1), .5)
        self.assertEqual(nn.area_recovery(frame, [1, 1, 1], .1), 0.)
        with self.assertRaises(ValueError):
            nn.area_recovery(frame, [np.nan, 0, 1])

    def test_rank_blend_is_scale_invariant_and_preserves_ties(self):
        a, b = np.array([.1, .8, .8, .4]), np.array([.4, .1, .9, .2])
        np.testing.assert_allclose(nn.blend_scores(a, b), nn.blend_scores(a*100+20, b*3-4))
        self.assertEqual(nn.percentile_scores(a)[1], nn.percentile_scores(a)[2])
        np.testing.assert_allclose(nn.percentile_scores(a), nn.percentile_against_reference(a, a))
        with self.assertRaises(ValueError):
            nn.blend_scores(a, b[:-1])

    def test_nnpu_clips_negative_risk_and_requires_prior(self):
        risk = nn.nnpu_risk([20., 20.], [-20., -20.], .5)
        self.assertLess(risk['raw_negative_risk'], 0)
        self.assertGreaterEqual(risk['nnpu_risk'], 0)
        self.assertAlmostEqual(risk['nnpu_risk'], risk['positive_risk'])
        with self.assertRaises(ValueError):
            nn.nnpu_risk([0], [0], 0)

    def test_exploration_never_claims_production_or_test(self):
        cfg = {'architectures': [{'name': 'mlp_a'}], 'minimum_relevant_gain': .02}
        rows = [{'split_id': s, 'model': n, 'recovery_at_05': r} for s in ['a', 'b']
                for n, r in [('random_forest', .5), ('logistic', .4), ('mlp_a', .6), ('blend_mlp_a', .65)]]
        decision = nn.summarize_decision(pd.DataFrame(rows), cfg)
        self.assertTrue(decision['promising_in_internal_validation'])
        self.assertFalse(decision['production_allowed'])
        self.assertFalse(decision['improvement_demonstrated_on_test'])

    def test_fixed_epoch_refit_and_all_networks_roundtrip(self):
        cfg = nn.read_config(Path(__file__).resolve().parents[1])
        cfg = {**cfg, 'epochs': 2, 'minimum_epochs': 1, 'batch_size': 16}
        rng = np.random.default_rng(42)
        X = rng.normal(size=(32, 4)).astype(np.float32)
        y = (X[:, 0] > 0).astype(np.float32)
        tf = u1.tensorflow()
        for kind in ('plain', 'wide_deep', 'residual'):
            architecture = {**cfg['architectures'][0], 'hidden': [4, 4], 'kind': kind, 'rank_weight': .2}
            model, history, epoch = nn.fit_network(X, y, architecture, cfg, 42, fixed_epochs=2)
            self.assertEqual(epoch, 2)
            self.assertNotIn('tuning_bce', history)
            self.assertTrue(np.isfinite(history.to_numpy()).all())
            expected = nn.predict_logits(model, X)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/'model.keras'
                model.save(path)
                restored = tf.keras.models.load_model(path, compile=False)
                np.testing.assert_allclose(nn.predict_logits(restored, X), expected, atol=1e-6)

    def test_integrated_gradients_completeness_for_linear_model(self):
        tf = u1.tensorflow()
        model = tf.keras.Sequential([tf.keras.layers.Input(shape=(2,)), tf.keras.layers.Dense(1)])
        model.set_weights([np.array([[2.], [-3.]], dtype=np.float32), np.array([.5], dtype=np.float32)])
        X = np.array([[1., 2.], [2., -1.]], dtype=np.float32)
        attribution, residual = nx.integrated_gradients(model, X, [0., 0.], steps=8)
        np.testing.assert_allclose(attribution, X*[2, -3], atol=1e-6)
        np.testing.assert_allclose(residual, 0., atol=1e-6)


if __name__ == '__main__':
    unittest.main()
