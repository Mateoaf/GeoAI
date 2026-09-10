from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from geoau import training as tr
from geoau import evaluation as ev


class TrainingTests(unittest.TestCase):
    def test_guard_rejects_auxiliary(self):
        guard = tr.FeatureGuard(['x'], [])
        with self.assertRaises(ValueError): guard.fit(pd.DataFrame({'x': [1], 'sample_class': [1]}))
        dictionary = pd.DataFrame({'name': ['x', 'cell_id'], 'representation': ['numeric', 'numeric']})
        with self.assertRaises(ValueError):
            tr.authorize_columns(['cell_id'], dictionary, {'candidate_columns': ['cell_id']}, 'diagnostic')

    def test_no_approved_predictors_means_no_validated_X(self):
        with self.assertRaises(ValueError):
            tr.authorize_columns(['x'], pd.DataFrame({'name': ['x']}), {'approved_training_columns': []}, 'validated')

    def test_pipeline_train_only_imputation_and_unknown(self):
        X = pd.DataFrame({'x': [1., 3., np.nan, 5.], 'cat': ['a', 'a', 'b', None]})
        model = tr.make_pipeline(['x', 'cat'], ['cat'], 'logistic', {'C': 1.}, 42, 1)
        model.fit(X, [0, 1, 0, 1])
        imputer = model.named_steps['preprocess'].named_transformers_['numeric'].named_steps['impute']
        self.assertEqual(imputer.statistics_[0], 3.)
        test = pd.DataFrame({'x': [100000., np.nan], 'cat': ['unseen', None]})
        scores = model.predict_proba(test)
        self.assertTrue(np.isfinite(scores).all())
        self.assertEqual(imputer.statistics_[0], 3.)
        encoder = model.named_steps['preprocess'].named_transformers_['categorical']
        self.assertNotIn('v:unseen', encoder.categories_[0])
        self.assertIn('__UNKNOWN__', encoder.categories_[0])

    def test_empty_numeric_train_column_survives(self):
        X = pd.DataFrame({'x': [np.nan]*4, 'z': [0., 1., 2., 3.]})
        model = tr.make_pipeline(['x', 'z'], [], 'random_forest', {'n_estimators': 5}, 42, 1)
        model.fit(X, [0, 0, 1, 1])
        self.assertEqual(model.predict_proba(pd.DataFrame({'x': [4.], 'z': [2.]})).shape, (1, 2))

    def test_geochemical_codes_categorical(self):
        dictionary = pd.DataFrame({'name': ['au_clase_modal'], 'representation': ['numeric']})
        self.assertEqual(tr.authorize_columns(['au_clase_modal'], dictionary,
                         {'candidate_columns': ['au_clase_modal']}, 'diagnostic'), ['au_clase_modal'])

    def test_boosting_no_hidden_random_validation(self):
        model = tr.make_pipeline(['x'], [], 'hist_boosting', {'max_iter': 5}, 42, 1)
        self.assertFalse(model.named_steps['model'].early_stopping)

    def test_area_ranking_and_ties_independent_of_label(self):
        frame = pd.DataFrame({'cell_id': ['a', 'b', 'c', 'd'], 'land_area_m2': [1., 1., 9., 9.],
                              'observed_P': [True, False, False, False], 'tie_key': [1, 2, 3, 4],
                              'pu_metric_member': True})
        result = tr.metrics(frame, [.5]*4)
        self.assertEqual(result['area_fraction_05'], .05)
        self.assertEqual(result['recovery_at_05'], 1.)
        changed = frame.copy(); changed['observed_P'] = [False, True, False, False]
        self.assertEqual(tr.metrics(changed, [.5]*4)['recovery_at_05'], 0.)
        self.assertEqual(tr.metrics(changed, [.5]*4)['area_fraction_05'], .05)

    def test_reviewed_deposits_count_once(self):
        frame = pd.DataFrame({'cell_id': [f'c{i}' for i in range(100)], 'land_area_m2': 1.,
                              'observed_P': [True]*2+[False]*97+[True], 'tie_key': range(100), 'pu_metric_member': True})
        records = pd.DataFrame({'cell_id': ['c0', 'c1', 'c99'], 'deposit_id': ['d1', 'd1', 'd2']})
        self.assertEqual(tr.metrics(frame, np.arange(100)[::-1], records, 'validated')['recovery_at_05'], .5)

    def test_serialized_pipeline_identical_predictions(self):
        model = tr.make_pipeline(['x'], [], 'extra_trees', {'n_estimators': 5}, 42, 1)
        X = pd.DataFrame({'x': [0., 1., 2., 3.]}); model.fit(X, [0, 0, 1, 1])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'model.joblib'; joblib.dump(model, path)
            np.testing.assert_array_equal(model.predict_proba(X), joblib.load(path).predict_proba(X))

    def test_nested_training_uses_frozen_memberships(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); e = root/'e'; out = root/'f'
            for base, names in [(e, ['memberships', 'samples']), (out, ['models', 'predictions', 'search', 'evaluation'])]:
                for name in names: (base/name).mkdir(parents=True)
            X = pd.DataFrame({'x': np.arange(80, dtype=float)}, index=[f'c{i}' for i in range(80)])
            cfg = {'mode': 'diagnostic', 'feature_set': 'all', 'seed': 42, 'n_jobs': 1,
                   'prediction_batch_size': 20, 'fit_weighting': 'none', 'primary_metric': 'recovery_at_05'}
            schema = {'all': {'columns': ['x'], 'categorical': []}}
            plans = []; observed = set(X.index[::4])
            for outer in range(2):
                outer_train = np.arange(40) + outer*40
                outer_test = np.arange(40) + (1-outer)*40
                entries = [(f'outer_{outer:02d}', outer_train, outer_test, 'outer')]
                for inner in range(2):
                    entries.append((f'outer_{outer:02d}_inner_{inner:02d}', outer_train[inner*20:(inner+1)*20],
                                    outer_train[(1-inner)*20:(2-inner)*20], 'inner'))
                for split_id, train, test, level in entries:
                    plans.append({'split_id': split_id, 'level': level, 'outer_fold': outer})
                    membership = pd.DataFrame({'cell_id': X.index, 'role': 'outside_parent'})
                    membership.loc[train, 'role'] = 'train'; membership.loc[test, 'role'] = 'test'
                    ev.atomic_parquet(membership, e/f'memberships/{split_id}.parquet')
                    sample = pd.DataFrame({'cell_id': X.index[train]})
                    sample['sample_class'] = sample.cell_id.isin(observed).astype(int)
                    ev.atomic_parquet(sample, e/f'samples/{split_id}_ratio3_rep00.parquet')
                    frame = pd.DataFrame({'cell_id': X.index[test], 'land_area_m2': 1., 'tie_key': test,
                                          'pu_metric_member': True, 'observed_P': X.index[test].isin(observed)})
                    ev.atomic_parquet(frame, out/f'evaluation/{split_id}.parquet')
            ev.write_json(e/'split_plan.json', {'splits': plans})
            ev.atomic_parquet(pd.DataFrame({'cell_id': sorted(observed)}), out/'evaluation/positive_records.parquet')
            ev.write_json(out/'candidates.json', {'logistic': [
                dict(candidate_id='logistic_00', family='logistic', ratio=3, params={'C': 1.}),
                dict(candidate_id='logistic_01', family='logistic', ratio=3, params={'C': 100.})]})
            original_evaluate = tr.evaluate_model
            def controlled_evaluation(cfg, out, X, model, columns, split_id, records):
                frame, scores, values = original_evaluate(cfg, out, X, model, columns, split_id, records)
                # El candidato 00 gana dentro y pierde fuera: debe elegirse 00.
                preferred = model.named_steps['model'].C == 1.
                values['recovery_at_05'] = float(preferred if '_inner_' in split_id else not preferred)
                return frame, scores, values
            with patch.object(tr, 'load_context', return_value=(cfg, e, X, schema)), \
                 patch.object(tr, 'evaluate_model', side_effect=controlled_evaluation):
                results = tr.fit_family(root, out, 'logistic')
            self.assertEqual(len(results), 2)
            self.assertTrue(results.candidate_id.eq('logistic_00').all())
            for split_id in ('outer_00', 'outer_01'):
                pred = pd.read_parquet(out/f'predictions/logistic_{split_id}.parquet')
                self.assertEqual(len(pred), 40)
                self.assertFalse(pred.is_absolute_gold_probability.any())
            ev.verify(out, ev.read_json(out/'logistic_manifest.json'))


if __name__ == '__main__': unittest.main()
