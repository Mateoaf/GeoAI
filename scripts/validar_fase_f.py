"""Comprueba productos F, selección interna y reproducción de modelos propios."""
from pathlib import Path
import sys
import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from geoau import training as tr
from geoau import evaluation as ev


def main():
    out = tr.current_run(ROOT)
    cfg, e, X, schema = tr.load_context(ROOT, out)
    ev.verify(out, ev.read_json(out/'outputs_manifest.json'))
    units = pd.read_parquet(e/'design/spatial_units.parquet')
    holdout = set(units.loc[units.holdout, 'cell_id'])
    plans = ev.read_json(e/'split_plan.json')['splits']
    positives = pd.read_parquet(out/'evaluation/positive_records.parquet')
    selected = set(positives.cell_id)
    for item in plans:
        frame = tr.fixed_frame(out, item['split_id'])
        membership = pd.read_parquet(e/f"memberships/{item['split_id']}.parquet")
        expected = set(membership.loc[membership.role.eq('test'), 'cell_id'])
        assert frame.cell_id.is_unique and set(frame.cell_id) == expected
        assert not set(frame.cell_id) & holdout
        assert set(frame.loc[frame.observed_P, 'cell_id']) == expected & selected
        assert frame.loc[frame.observed_P, 'pu_metric_member'].all()
    # Reproduce decisiones usando únicamente tablas internas.
    all_selections = []
    for family in cfg['families']:
        selections = ev.read_json(out/f'{family}_selections.json')
        for selection in selections:
            split_id = selection['outer_split']
            inner = pd.read_csv(out/f'search/{family}_{split_id}.csv')
            assert inner.split_id.str.startswith(split_id+'_inner_').all()
            rank = inner.groupby('candidate_id')[cfg['primary_metric']].mean().reset_index().sort_values(
                [cfg['primary_metric'], 'candidate_id'], ascending=[False, True])
            assert selection['candidate_id'] == rank.candidate_id.iloc[0]
            assert np.isclose(selection['mean_inner_recovery_at_05'], rank.iloc[0][cfg['primary_metric']])
        all_selections += selections
    nested = pd.read_csv(out/'nested_procedure_metrics.csv')
    for row in nested.itertuples(index=False):
        winner = sorted([s for s in all_selections if s['outer_split'] == row.outer_split],
                        key=lambda s: (-s['mean_inner_recovery_at_05'], s['family'], s['candidate_id']))[0]
        assert winner['family'] == row.family and winner['candidate_id'] == row.candidate_id
        original = pd.read_parquet(out/f'predictions/{row.family}_{row.outer_split}.parquet')
        chosen = pd.read_parquet(out/f'predictions/nested_selected_{row.outer_split}.parquet')
        pd.testing.assert_frame_equal(original, chosen)
    # Todos los productos de predicción cubren test externo completo, nunca reserva.
    prediction_files = list((out/'predictions').glob('*.parquet'))
    for path in prediction_files:
        split_id = 'outer_'+path.stem.rsplit('_', 1)[-1]
        frame = tr.fixed_frame(out, split_id)
        prediction = pd.read_parquet(path)
        assert prediction.cell_id.equals(frame.cell_id)
        assert prediction.score.between(0, 1).all()
        assert prediction['mode'].eq(cfg['mode']).all()
        assert not prediction.is_absolute_gold_probability.any()
    for row in pd.read_csv(out/'comparison_by_fold.csv').itertuples(index=False):
        frame = tr.fixed_frame(out, row.split_id)
        prediction = pd.read_parquet(out/f'predictions/{row.family}_{row.split_id}.parquet')
        recomputed = tr.metrics(frame, prediction.score, positives, cfg['mode'])
        for key in ('recovery_at_01', 'recovery_at_05', 'recovery_at_10', 'average_precision_PU', 'roc_auc_PU'):
            np.testing.assert_allclose(getattr(row, key), recomputed[key], rtol=1e-10, atol=1e-12)
    # Carga únicamente modelos de esta ejecución cuyos hashes ya se verificaron.
    models = list((out/'models').glob('*.joblib'))
    for path in models:
        meta = ev.read_json(path.with_suffix('.json'))
        assert not meta['production_allowed']
        sample_path = Path(meta['sample_path'])
        assert ev.sha256_file(sample_path) == meta['sample_sha256']
        split_id = 'outer_'+path.stem.rsplit('_', 1)[-1]
        membership = pd.read_parquet(e/f'memberships/{split_id}.parquet')
        sample = pd.read_parquet(sample_path)
        assert set(sample.cell_id) <= set(membership.loc[membership.role.eq('train'), 'cell_id'])
        assert not set(sample.cell_id) & holdout
        model = joblib.load(path)
        assert model.named_steps['guard'].columns == meta['columns']
        assert model.named_steps['model'].get_params().get('early_stopping', False) is False
        assert model.named_steps['model'].get_params().get('oob_score', False) is False
        numerical = [c for c in meta['columns'] if c not in model.named_steps['guard'].categorical]
        raw = X.loc[sample.cell_id, numerical].replace([np.inf, -np.inf], np.nan)
        expected = raw.median().fillna(0).to_numpy()
        actual = model.named_steps['preprocess'].named_transformers_['numeric'].named_steps['impute'].statistics_
        np.testing.assert_allclose(actual, expected)
        numeric_pipeline = model.named_steps['preprocess'].named_transformers_['numeric']
        if 'scale' in numeric_pipeline.named_steps:
            imputed = numeric_pipeline.named_steps['impute'].transform(raw.astype(float))
            np.testing.assert_allclose(numeric_pipeline.named_steps['scale'].mean_, imputed.mean(axis=0))
        cats = model.named_steps['guard'].categorical
        if cats:
            normalized = model.named_steps['guard'].transform(X.loc[sample.cell_id, meta['columns']])
            learned = model.named_steps['preprocess'].named_transformers_['categorical'].categories_
            for col, categories in zip(cats, learned):
                assert set(categories) == set(normalized[col]) | {'__MISSING__', '__UNKNOWN__'}
        prediction = pd.read_parquet(out/f'predictions/{path.stem}.parquet')
        check = prediction.iloc[np.linspace(0, len(prediction)-1, 15, dtype=int)]
        with threadpool_limits(limits=cfg['n_jobs']):
            actual_scores = model.predict_proba(X.loc[check.cell_id, meta['columns']])[:, 1]
        np.testing.assert_allclose(actual_scores, check.score, rtol=1e-10, atol=1e-12)
        print('Modelo reproducido:', path.stem, flush=True)
    for row in ev.read_json(out/'random_forest_selections.json'):
        split_id = row['outer_split']
        values = [pd.read_parquet(out/f'predictions/random_forest_{split_id}.parquet').score.to_numpy()]
        for rep in cfg['pu_realizations'][1:]:
            values.append(pd.read_parquet(out/f'predictions/pu_rep{rep:02d}_{split_id}.parquet').score.to_numpy())
        bag = pd.read_parquet(out/f'predictions/pu_bagging_{split_id}.parquet')
        np.testing.assert_allclose(bag.score, np.mean(values, axis=0))
        np.testing.assert_allclose(bag.background_score_std, np.std(values, axis=0))
    control = ev.read_json(out/'control_cierre.json')
    assert not control['prediction_allowed'] and not control['production_allowed']
    print(f'OK: {len(models)} pipelines reproducidos y {len(prediction_files)} archivos OOF; selección, imputación, reserva y PU verificados.')


if __name__ == '__main__': main()
