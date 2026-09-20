from pathlib import Path
import importlib.util
import sys
import tempfile
import unittest

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from geoau import neural_u1 as u1


class FundamentalsTests(unittest.TestCase):
    def test_logic_and_stable_activations(self):
        X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
        np.testing.assert_array_equal(u1.perceptron_predict(X, [1, 1], -.5), [0, 1, 1, 1])
        np.testing.assert_array_equal(u1.perceptron_predict(X, [1, 1], -1.5), [0, 0, 0, 1])
        np.testing.assert_array_equal(u1.xor_manual(X), [0, 1, 1, 0])
        values = u1.activations([-1000., 0., 1000.])
        self.assertTrue(all(np.isfinite(a).all() for a in values.values()))

    def test_gradients_and_loss_descent(self):
        X = np.array([[-1., 2.], [0., -1.], [1., 0.], [2., 1.]])
        y = np.array([0., 0., 1., 1.])
        check = u1.gradient_check(np.array([.2, -.4, .1]), X, y)
        self.assertLess(check.absolute_error.max(), 1e-8)
        theta, history = u1.gradient_descent(X, y)
        self.assertLess(u1.logistic_loss_gradient(theta, X, y)[0], history[0])
        loss, gradient = u1.logistic_loss_gradient(np.array([1000., 0., 0.]), X, y)
        self.assertTrue(np.isfinite(loss) and np.isfinite(gradient).all())

    def test_preprocessing_is_train_only_and_roundtrips(self):
        X = pd.DataFrame({'x': [1., 3., np.nan, 5.], 'empty': [np.nan]*4,
                          'cat': ['a', 'b', 'a', None]})
        pre = u1.make_preprocessor(list(X.columns), ['cat'])
        transformed = pre.fit_transform(X)
        test = pd.DataFrame({'x': [1e8, np.nan], 'empty': [50., np.inf], 'cat': ['new', None]})
        prediction = pre.transform(test)
        num = pre.named_steps['preprocess'].named_transformers_['numeric'].named_steps
        np.testing.assert_allclose(num['impute'].statistics_, [3., 0.])
        np.testing.assert_allclose(num['scale'].mean_, [3., 0.])
        self.assertTrue(np.isfinite(prediction).all())
        self.assertEqual(transformed.shape[1], prediction.shape[1])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'pre.joblib'; joblib.dump(pre, path)
            np.testing.assert_array_equal(joblib.load(path).transform(test), prediction)

    def test_partition_rejects_test_holdout_and_duplicates(self):
        sample = pd.DataFrame({'cell_id': ['a', 'b'], 'sample_class': [0, 1]})
        frame = pd.DataFrame({'cell_id': ['c', 'd'], 'observed_P': [True, False], 'pu_metric_member': True})
        member = pd.DataFrame({'cell_id': list('abcde'), 'role': ['train', 'train', 'test', 'test', 'outside_parent']})
        parent = pd.DataFrame({'cell_id': list('abcde'), 'role': ['train']*4+['test']})
        u1.check_partition(sample, member, frame, parent, {'h'})
        with self.assertRaises(ValueError): u1.check_partition(sample, member, frame, parent, {'a'})
        with self.assertRaises(ValueError): u1.check_partition(sample, member, frame, parent, {'c'})
        with self.assertRaises(ValueError): u1.check_partition(pd.concat([sample, sample]), member, frame, parent, set())
        bad = parent.copy(); bad.loc[bad.cell_id.eq('d'), 'role'] = 'test'
        with self.assertRaises(ValueError): u1.check_partition(sample, member, frame, bad, set())
        bad_sample = sample.copy(); bad_sample.loc[0, 'cell_id'] = 'e'
        with self.assertRaises(ValueError): u1.check_partition(bad_sample, member, frame, parent, set())

    def test_selection_paired_and_never_claims_test_improvement(self):
        rows = [{'split_id': split, 'model': model, 'recovery_at_05': value}
                for split in ('a', 'b') for model, value in
                [('random_forest', .5), ('logistic', .4), ('mlp_a', .6), ('mlp_b', .55)]]
        decision = u1.validation_decision(pd.DataFrame(rows), .02)
        self.assertEqual(decision['selected_by_validation'], 'mlp_a')
        self.assertTrue(decision['promising_in_validation'])
        self.assertFalse(decision['improvement_demonstrated_on_test'])
        with self.assertRaises(ValueError): u1.validation_decision(pd.DataFrame(rows[:-1]), .02)


@unittest.skipUnless(importlib.util.find_spec('tensorflow'), 'TensorFlow se prueba en .venv-unidad1')
class TensorFlowTests(unittest.TestCase):
    def test_manual_forward_matches_keras(self):
        tf = u1.tensorflow()
        model = tf.keras.Sequential([tf.keras.layers.Input(shape=(2,)),
            tf.keras.layers.Dense(3, activation='relu'), tf.keras.layers.Dense(1, activation='sigmoid')])
        model.set_weights([np.array([[.8, -.4, .5], [-.3, .9, .2]]), np.array([.1, -.2, .05]),
                           np.array([[.7], [-.5], [.4]]), np.array([.02])])
        X = np.array([[1., 2.], [-.5, 1.]], dtype=np.float32)
        np.testing.assert_allclose(model(X).numpy().ravel(), u1.forward_manual(X)['score_PU'], rtol=1e-6)

    def test_fit_uses_explicit_validation_and_saved_model_reproduces_scores(self):
        rng = np.random.default_rng(42)
        X = rng.normal(size=(48, 2)).astype(np.float32)
        y = (X[:, 0] > 0).astype(np.float32)
        arch = {'hidden': [4, 2], 'dropout': .2, 'l2': .001}
        cfg = {'learning_rate': .01, 'seed': 42, 'patience': 1, 'epochs': 3, 'batch_size': 8}
        model, history = u1.fit_mlp(X[:32], y[:32], X[32:], y[32:], arch, cfg)
        self.assertIn('val_loss', history)
        self.assertTrue(np.isfinite(history.to_numpy()).all())
        scores = model(X[32:], training=False).numpy()
        self.assertTrue(((scores >= 0) & (scores <= 1)).all())
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'model.keras'; model.save(path)
            restored = u1.tensorflow().keras.models.load_model(path)
            np.testing.assert_allclose(scores, restored(X[32:], training=False).numpy(), rtol=1e-6)


if __name__ == '__main__': unittest.main()
