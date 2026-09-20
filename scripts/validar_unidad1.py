"""Verifica particiones, métricas y reproducción de cada modelo guardado de U1."""
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.metrics import accuracy_score, f1_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from geoau import neural_u1 as u1
from geoau import training as tr
from geoau import evaluation as ev


def main():
    out = u1.completed_run(ROOT)
    cfg = u1.read_config(ROOT)
    fcfg, source, X, schema, partitions = u1.load_context(ROOT, cfg)
    table = pd.read_csv(out/'validation_metrics.csv')
    records = pd.read_parquet(source/'evaluation/positive_records.parquet')
    expected_models = {'logistic', 'random_forest', 'perceptron'} | {a['name'] for a in cfg['architectures']}
    assert set(table.split_id) == set(partitions)
    assert table.role.eq('validation').all()
    for split, (sample, frame, path) in partitions.items():
        rows = table[table.split_id.eq(split)]
        assert set(rows.model) == expected_models and len(rows) == len(expected_models)
        meta = ev.read_json(out/f'models/sample_{split}.json')
        assert meta['sha256'] == ev.sha256_file(path)
        pre = joblib.load(out/f'models/preprocessor_{split}.joblib')
        raw = X.loc[sample.cell_id, schema['columns']]
        normalized = pre.named_steps['guard'].transform(raw)
        numeric = [c for c in schema['columns'] if c not in schema['categorical']]
        steps = pre.named_steps['preprocess'].named_transformers_['numeric'].named_steps
        np.testing.assert_allclose(steps['impute'].statistics_, normalized[numeric].median().fillna(0))
        imputed = steps['impute'].transform(normalized[numeric])
        np.testing.assert_allclose(steps['scale'].mean_, imputed.mean(axis=0))
        chosen = np.linspace(0, len(frame)-1, 17, dtype=int)
        raw_check = X.loc[frame.iloc[chosen].cell_id, schema['columns']]
        for row in rows.itertuples(index=False):
            prediction = pd.read_parquet(out/f'predictions/{row.model}_{split}.parquet')
            assert prediction.cell_id.equals(frame.cell_id)
            assert prediction.score.between(0, 1).all()
            assert not prediction.is_absolute_gold_probability.any()
            metric = tr.metrics(frame, prediction.score, records, fcfg['mode'])
            for key in ('recovery_at_01', 'recovery_at_05', 'recovery_at_10', 'average_precision_PU', 'roc_auc_PU'):
                np.testing.assert_allclose(getattr(row, key), metric[key], rtol=1e-9)
            mask = frame.pu_metric_member.to_numpy(dtype=bool)
            yval = frame.loc[mask, 'observed_P'].to_numpy(dtype=np.float32)
            labels = prediction.loc[mask, 'score'].to_numpy() >= .5
            np.testing.assert_allclose(row.accuracy_PU_at_05, accuracy_score(yval, labels))
            np.testing.assert_allclose(row.f1_PU_at_05, f1_score(yval, labels, zero_division=0))
            if row.model.startswith('mlp_'):
                model = u1.tensorflow().keras.models.load_model(out/f'models/{row.model}_{split}.keras')
                actual = model(pre.transform(raw_check).astype(np.float32), training=False).numpy().ravel()
                history = pd.read_csv(out/f'histories/{row.model}_{split}.csv')
                assert row.best_epoch == int(history.loc[history.val_loss.idxmin(), 'epoch'])
                assert row.parameters == model.count_params()
                validation = pre.transform(X.loc[frame.loc[mask, 'cell_id'], schema['columns']]).astype(np.float32)
                values = model.evaluate(validation, yval, batch_size=1024, verbose=0, return_dict=True)
                np.testing.assert_allclose(values['loss'], history.val_loss.min(), rtol=2e-5, atol=2e-6)
            elif row.model == 'perceptron':
                model = joblib.load(out/f'models/{row.model}_{split}.joblib')
                actual = expit(model.decision_function(pre.transform(raw_check).astype(np.float32)))
            else:
                model = joblib.load(out/f'models/{row.model}_{split}.joblib')
                actual = model.predict_proba(raw_check)[:, 1]
            np.testing.assert_allclose(actual, prediction.iloc[chosen].score, atol=2e-6, rtol=1e-5)
        print('Verificado:', split, flush=True)
    decision = u1.validation_decision(table, cfg['minimum_relevant_gain'])
    saved = ev.read_json(out/'decision.json')
    assert decision['selected_by_validation'] == saved['selected_by_validation']
    assert decision['promising_in_validation'] == saved['promising_in_validation']
    for name, gain in decision['mean_paired_gain'].items():
        np.testing.assert_allclose(gain, saved['mean_paired_gain'][name])
    control = ev.read_json(out/'control.json')
    assert control['status'] == 'completed'
    assert not any(control[k] for k in ('test_evaluated', 'holdout_evaluated', 'production_allowed'))
    print(f'OK: {len(table)} ajustes; métricas, modelos y exclusión de test/reserva verificados.')


if __name__ == '__main__': main()
