"""Invariantes de la fusión: pesos, predicción y selección interna."""
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from geoau.model_fusion import HeterogeneousFusion, fit_fusion, select_fusion_weights, weight_candidates
from geoau.geochemical_experiment import make_preprocessor
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


class FusionTests(unittest.TestCase):
    def test_candidates_are_convex_and_include_equal_and_individual_models(self):
        weights = weight_candidates(4)
        self.assertTrue((weights >= 0).all())
        np.testing.assert_allclose(weights.sum(axis=1), 1)
        for expected in [np.ones(4)/4, *np.eye(4)]:
            self.assertTrue(np.isclose(weights, expected).all(axis=1).any())

    def test_identical_models_prefer_equal_weights(self):
        y = np.array([0,1,0,1])
        scores = np.tile([.2,.8,.4,.6], (4,1)).T
        weights, candidates = select_fusion_weights(y, scores)
        np.testing.assert_allclose(weights, .25)
        self.assertEqual(candidates.selected.sum(), 1)

    def test_selection_can_discard_an_inverted_model(self):
        y = np.array([0,1,0,1])
        scores = np.column_stack([[.1,.8,.3,.9],[.9,.2,.7,.1]])
        weights, _ = select_fusion_weights(y, scores)
        self.assertGreater(weights[0], weights[1])

    def test_invalid_or_incomplete_predictions_fail(self):
        with self.assertRaises(ValueError):
            select_fusion_weights([0,1], [[.1,np.nan],[.8,.9]])
        with self.assertRaises(ValueError):
            HeterogeneousFusion({'a':None,'b':None}, [-.1,1.1], ['x'])

    def test_predictions_are_a_convex_average(self):
        a = SimpleNamespace(predict_proba=lambda X: np.array([[.8,.2],[.2,.8]]))
        b = SimpleNamespace(predict_proba=lambda X: np.array([[.2,.8],[.8,.2]]))
        model = HeterogeneousFusion({'a':a,'b':b}, [.75,.25], ['x'])
        result = model.predict_proba(pd.DataFrame({'x':[0,1]}))
        np.testing.assert_allclose(result[:,1], [.35,.65])
        np.testing.assert_allclose(result.sum(axis=1), 1)

    def test_inner_predictions_exclude_their_own_fit_rows(self):
        sample = pd.DataFrame({'cell_id':[f'c{i:03d}' for i in range(60)],
            'label':[0,1]*30, 'peso_confianza':1., 'block_id':[f'b{i//2}' for i in range(60)],
            'x_center':[i//2*50000 for i in range(60)], 'y_center':0.})
        features = pd.DataFrame({'x':np.arange(60.)}, index=sample.cell_id)
        cfg = {'fusion_components':['a','b'], 'fusion_inner_folds':3, 'fusion_weight_step':.1,
            'fusion_selection_metric':'average_precision', 'geochemical_columns':[],
            'prediction_batch_size':100, 'cv_buffer_m':15000, 'cv_folds':5}
        data = SimpleNamespace(config=cfg,features=features,feature_columns=['x'])
        fits = []
        def factory(columns, chemical, family, config, seed):
            class RecordedLogistic(LogisticRegression):
                def fit(self, X, y, **kwargs):
                    fits.append((len(X), tuple(y)))
                    return super().fit(X,y,**kwargs)
            return Pipeline([('preprocess',make_preprocessor(columns,chemical)),('model',RecordedLogistic())])
        with patch('geoau.model_fusion.make_model', side_effect=factory):
            model, predictions, membership, candidates = fit_fusion(data,sample,'buffered',42)
        self.assertEqual(len(predictions),len(sample))
        self.assertTrue(np.isfinite(predictions[['a','b','fusion_score']]).all().all())
        for fold, roles in membership.groupby('inner_fold'):
            fit_ids = set(roles.loc[roles.role.eq('train'),'cell_id'])
            test_ids = set(roles.loc[roles.role.eq('validation'),'cell_id'])
            self.assertFalse(fit_ids & test_ids)
            self.assertEqual(test_ids,set(predictions.loc[predictions.inner_fold.eq(fold),'cell_id']))
        self.assertEqual([count for count,_ in fits[-2:]], [60,60])
        selected = candidates.loc[candidates.selected,'average_precision'].iloc[0]
        self.assertAlmostEqual(selected,candidates.average_precision.max())


if __name__ == '__main__':
    unittest.main()
