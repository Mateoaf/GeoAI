"""Fase F: ajuste anidado reproducible; diagnósticos separados de validación."""
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import shutil
import time

import joblib
import numpy as np
import pandas as pd
import psutil
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from threadpoolctl import threadpool_limits
import yaml

from . import evaluation as ev
from .local_sources import write_json


class FeatureGuard(TransformerMixin, BaseEstimator):
    """Exige exactamente X autorizada; normalización sin estadísticas globales."""
    def __init__(self, columns, categorical):
        self.columns = columns
        self.categorical = categorical

    def fit(self, X, y=None):
        self.transform(X)
        self.feature_names_in_ = np.asarray(self.columns, dtype=object)
        return self

    def transform(self, X):
        if not isinstance(X, pd.DataFrame) or list(X.columns) != list(self.columns):
            raise ValueError('X debe contener exclusivamente los predictores, en el orden congelado.')
        result = X.copy()
        for col in self.columns:
            if col in self.categorical:
                result[col] = result[col].map(lambda x: '__MISSING__' if pd.isna(x) else 'v:' + str(x))
            else:
                result[col] = pd.to_numeric(result[col], errors='raise').replace([np.inf, -np.inf], np.nan).astype(float)
        return result


class SafeOneHot(TransformerMixin, BaseEstimator):
    """Aprende categorías solo en train y reserva códigos para desconocido/ausente."""
    def fit(self, X, y=None):
        values = np.asarray(X, dtype=object)
        self.categories_ = [sorted(set(values[:, j]) | {'__UNKNOWN__', '__MISSING__'})
                            for j in range(values.shape[1])]
        self.encoder_ = OneHotEncoder(categories=self.categories_, handle_unknown='error',
                                      sparse_output=False, dtype=np.float32)
        self.encoder_.fit(values)
        return self

    def transform(self, X):
        values = np.asarray(X, dtype=object).copy()
        for j, categories in enumerate(self.categories_):
            values[~np.isin(values[:, j], categories), j] = '__UNKNOWN__'
        return self.encoder_.transform(values)

    def get_feature_names_out(self, input_features=None):
        return self.encoder_.get_feature_names_out(input_features)


def feature_sets(d):
    sets = ev.read_json(d/'feature_sets.json')
    base = sets['base_geologia_relieve_estructuras']
    terrain = [c for c in base if c.startswith(('elevacion_', 'pendiente_', 'tpi_', 'desv_elevacion_'))]
    hydro = [c for c in base if c == 'dist_cauce_m' or c.startswith('dens_aprox_cauce_')]
    geology = [c for c in base if c not in terrain + hydro]
    pathfinders = ['as_clase_modal', 'sb_clase_modal', 'bi_clase_modal']
    return {'geology': geology, 'geology_terrain': geology + terrain,
            'geology_terrain_pathfinders': geology + terrain + pathfinders,
            'geology_terrain_geo4': geology + terrain + pathfinders + ['au_clase_modal'],
            'geology_terrain_geo4_hydro': geology + terrain + pathfinders + ['au_clase_modal'] + hydro,
            'geo4_proportions': geology + terrain + hydro + [c for c in sets['proporciones_alternativas']
                                                            if c.startswith(('au_', 'as_', 'sb_', 'bi_'))]}


def authorize_columns(columns, dictionary, allowlist, mode):
    allowed = allowlist['approved_training_columns' if mode == 'validated' else 'candidate_columns']
    if not columns or len(set(columns)) != len(columns) or not set(columns) <= set(allowed):
        raise ValueError('Predictores fuera de la lista permitida por D.')
    if not set(columns) <= set(dictionary.name):
        raise ValueError('Falta diccionario de predictores.')
    forbidden = ('cell_id', 'row', 'col', 'x_center', 'y_center', 'deposit_id', 'district_id',
                 'sample_class', 'sample_role', 'unit_id', 'block_id', 'land_area_m2')
    if set(columns) & set(forbidden):
        raise ValueError('Columna auxiliar/etiqueta prohibida en X.')
    return [c for c in columns if dictionary.set_index('name').loc[c, 'representation'] == 'categorical'
            or c.endswith('_clase_modal')]


def make_pipeline(columns, categorical, family, params, seed, n_jobs):
    numeric = [c for c in columns if c not in categorical]
    num_steps = [('impute', SimpleImputer(strategy='median', keep_empty_features=True))]
    if family == 'logistic': num_steps.append(('scale', StandardScaler()))
    transformers = [('numeric', Pipeline(num_steps), numeric)]
    if categorical: transformers.append(('categorical', SafeOneHot(), categorical))
    pre = ColumnTransformer(transformers, remainder='drop', sparse_threshold=0)
    if family == 'logistic':
        estimator = LogisticRegression(max_iter=3000, solver='lbfgs', random_state=seed, **params)
    elif family == 'random_forest':
        estimator = RandomForestClassifier(random_state=seed, n_jobs=n_jobs, oob_score=False, **params)
    elif family == 'extra_trees':
        estimator = ExtraTreesClassifier(random_state=seed, n_jobs=n_jobs, **params)
    elif family == 'hist_boosting':
        estimator = HistGradientBoostingClassifier(random_state=seed, early_stopping=False,
                                                   categorical_features=None, **params)
    else: raise ValueError(f'Familia no implementada: {family}')
    return Pipeline([('guard', FeatureGuard(columns, categorical)), ('preprocess', pre), ('model', estimator)])


def candidates(cfg, family):
    rng = np.random.default_rng(ev.seed_for(cfg['seed'], 'search', family))
    result = []
    for i in range(cfg['search_trials']):
        ratio = cfg['ratios_u_to_p'][i % len(cfg['ratios_u_to_p'])]
        if family == 'logistic':
            params = {'C': float([1., .1, 10.][i]) if i < 3 else float(10 ** rng.uniform(-3, 2))}
        elif family in ('random_forest', 'extra_trees'):
            params = {'n_estimators': cfg['forest_trees'], 'min_samples_leaf': 5 if i == 0 else int(rng.choice([2, 5, 10, 20])),
                      'max_features': 'sqrt' if i == 0 or rng.random() < .5 else .5,
                      'max_depth': None if i == 0 else [8, 16, None][int(rng.integers(3))]}
        elif family == 'hist_boosting':
            params = {'max_iter': 100, 'learning_rate': [.1, .05, .15][i % 3],
                      'max_leaf_nodes': int([15, 31, 7][i % 3]), 'min_samples_leaf': int(rng.choice([10, 20, 30]))}
        else: raise ValueError(family)
        result.append({'candidate_id': f'{family}_{i:02d}', 'family': family, 'ratio': ratio, 'params': params})
    return result


def check_inputs(root, cfg):
    e = root/cfg['phase_e_run']
    ecfg, grid, relations, spec, _ = ev.context(root, e)
    ev.verify(e, ev.read_json(e/'outputs_manifest.json'))
    control = ev.read_json(e/'control_cierre.json')
    if control['estado_ejecucion'] != 'completada': raise ValueError('E no está completa.')
    if cfg['mode'] not in ('diagnostic', 'validated'): raise ValueError('Modo inválido.')
    if cfg['mode'] == 'validated': ev.assert_ready_for_training(root, e)
    elif not cfg.get('allow_diagnostic_fit') or ecfg['mode'] != 'diagnostic':
        raise ValueError('El ensayo con candidatos requiere E diagnóstica y autorización explícita en configuración F.')
    if cfg['mode'] != ecfg['mode']: raise ValueError('Modos E/F incompatibles.')
    if not set(cfg['ratios_u_to_p']) <= set(ecfg['ratios_u_to_p']): raise ValueError('Ratios ausentes de E.')
    if not cfg['pu_realizations'] or cfg['pu_realizations'] != list(range(len(cfg['pu_realizations']))) or len(cfg['pu_realizations']) > ecfg['realizations']:
        raise ValueError('Realizaciones PU incompatibles con E.')
    if 3 not in cfg['ratios_u_to_p']: raise ValueError('Las ablaciones predefinidas requieren ratio 3 disponible.')
    for key in ('search_trials', 'forest_trees', 'ablation_trees', 'n_jobs', 'prediction_batch_size', 'evaluation_background_size'):
        if not isinstance(cfg[key], int) or cfg[key] < 1: raise ValueError(key)
    if cfg['fit_weighting'] not in ('none', 'normalized_design_u'): raise ValueError('Ponderación no implementada.')
    if cfg['primary_metric'] != 'recovery_at_05': raise ValueError('Métrica no implementada.')
    if cfg['families'] != ['logistic', 'random_forest', 'extra_trees', 'hist_boosting']:
        raise ValueError('Esta entrega exige las cuatro familias predefinidas.')
    return e, root/ecfg['phase_d_run'], ecfg, grid, relations


def start_run(root):
    root = Path(root).resolve()
    cfg_path = root/'config/training.yaml'
    cfg = yaml.safe_load(cfg_path.read_text(encoding='utf-8'))
    e, d, ecfg, grid, relations = check_inputs(root, cfg)
    sets = feature_sets(d)
    dictionary = pd.read_csv(d/'feature_dictionary.csv')
    allow = ev.read_json(d/'feature_allowlist.json')
    schema = {}
    for name, columns in sets.items():
        cats = authorize_columns(columns, dictionary, allow, cfg['mode'])
        schema[name] = {'columns': columns, 'categorical': cats}
    if cfg['feature_set'] not in schema: raise ValueError('Conjunto X desconocido.')
    out = root/cfg['output_directory']/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    out.mkdir(parents=True)
    for sub in ('models', 'predictions', 'search', 'evaluation', 'experiments'): (out/sub).mkdir()
    frozen = [cfg_path, Path(__file__).resolve(), root/'src/geoau/evaluation.py',
              root/'src/geoau/local_sources.py', e/'outputs_manifest.json', d/'outputs_manifest.json']
    write_json(out/'inputs.json', {'frozen': ev.records(root, frozen), 'phase_e_run': cfg['phase_e_run'],
                                  'phase_d_run': d.relative_to(root).as_posix()})
    write_json(out/'config_snapshot.json', cfg)
    write_json(out/'feature_schema.json', schema)
    write_json(out/'environment.json', {n: importlib.metadata.version(n) for n in
               ('scikit-learn', 'numpy', 'pandas', 'scipy', 'joblib', 'pyarrow', 'threadpoolctl', 'psutil')})
    shutil.copy2(Path(__file__), out/'training_source.py')
    search = {family: candidates(cfg, family) for family in cfg['families']}
    write_json(out/'candidates.json', search)
    selected, _ = ev.choose_labels(grid, relations, ecfg)
    positive_ids = set(selected.cell_id)
    # Congela marcos de evaluación antes de ajustar modelos; nunca usa scores.
    paths = []
    for item in ev.read_json(e/'split_plan.json')['splits']:
        split_id = item['split_id']
        membership = pd.read_parquet(e/f'memberships/{split_id}.parquet')
        ids = membership.loc[membership.role.eq('test'), 'cell_id']
        frame = grid.set_index('cell_id').loc[ids, ['land_area_m2']].reset_index()
        frame['observed_P'] = frame.cell_id.isin(positive_ids)
        background = frame.loc[~frame.observed_P, 'cell_id']
        n = min(cfg['evaluation_background_size'], len(background))
        rng = np.random.default_rng(ev.seed_for(cfg['seed'], 'fixed_evaluation', split_id))
        u = set(rng.choice(background.to_numpy(), n, replace=False))
        frame['pu_metric_member'] = frame.observed_P | frame.cell_id.isin(u)
        frame['tie_key'] = [ev.seed_for(cfg['seed'], 'ties', c) for c in frame.cell_id]
        frame['unit_for_reporting'] = pd.read_parquet(e/'design/spatial_units.parquet').set_index('cell_id').loc[frame.cell_id, 'unit_id'].to_numpy()
        p = out/f'evaluation/{split_id}.parquet'; ev.atomic_parquet(frame, p); paths.append(p)
    ev.atomic_parquet(selected, out/'evaluation/positive_records.parquet'); paths.append(out/'evaluation/positive_records.parquet')
    write_json(out/'control_cierre.json', {'estado_ejecucion': 'en_curso', 'mode': cfg['mode'],
                                         'scientific_training_allowed': cfg['mode'] == 'validated', 'prediction_allowed': False})
    ev.seal_stage(out, 'preparation', paths + [out/'feature_schema.json', out/'candidates.json'])
    write_json(out.parent/'current_run.json', {'run': out.relative_to(root).as_posix()})
    print('Fase F:', out, flush=True)
    return out


def current_run(root):
    root = Path(root).resolve()
    cfg = yaml.safe_load((root/'config/training.yaml').read_text(encoding='utf-8'))
    out = root/ev.read_json(root/cfg['output_directory']/'current_run.json')['run']
    if cfg != ev.read_json(out/'config_snapshot.json'): raise ValueError('Configuración F modificada; iniciar nueva ejecución en 10.')
    ev.verify(root, ev.read_json(out/'inputs.json')['frozen'])
    return out


def ensure_run(root):
    try: return current_run(root)
    except (FileNotFoundError, ValueError): return start_run(root)


def load_context(root, out):
    root, out = Path(root).resolve(), Path(out).resolve()
    ev.verify(root, ev.read_json(out/'inputs.json')['frozen'])
    cfg = ev.read_json(out/'config_snapshot.json')
    e, d, ecfg, grid, relations = check_inputs(root, cfg)
    ev.stage_exists(out, 'preparation')
    schema = ev.read_json(out/'feature_schema.json')
    columns = list(dict.fromkeys(c for group in schema.values() for c in group['columns']))
    X = pd.read_parquet(d/'X_features.parquet', columns=['cell_id'] + columns).set_index('cell_id')
    if not X.index.is_unique or set(X.index) != set(grid.cell_id): raise ValueError('Claves X incompatibles.')
    return cfg, e, X, schema


def fixed_frame(out, split_id):
    return pd.read_parquet(out/f'evaluation/{split_id}.parquet')


def metrics(frame, scores, positive_records=None, mode='diagnostic'):
    scores = np.asarray(scores, dtype=float)
    if len(scores) != len(frame) or not np.isfinite(scores).all(): raise ValueError('Scores inválidos.')
    order = np.lexsort((frame.tie_key.to_numpy(), -scores))
    ranked = frame.iloc[order]
    cumulative = ranked.land_area_m2.cumsum().to_numpy()
    total_area = float(cumulative[-1])
    y = frame.observed_P.to_numpy(dtype=int)
    if not y.any(): raise ValueError('Evaluación sin P.')
    output = {'cells': len(frame), 'observed_P_cells': int(y.sum()),
              'positive_unit': 'candidate_cell' if mode == 'diagnostic' else 'reviewed_deposit'}
    if mode == 'validated':
        links = positive_records[positive_records.cell_id.isin(frame.cell_id)]
        if links.deposit_id.isna().any(): raise ValueError('Depósitos ausentes en evaluación validada.')
        n_targets = links.deposit_id.nunique()
    else: n_targets = int(y.sum())
    for fraction, suffix in ((.01, '01'), (.05, '05'), (.10, '10')):
        selected = ranked.loc[cumulative <= fraction * total_area]
        hits = int(selected.observed_P.sum()) if mode == 'diagnostic' else links.loc[links.cell_id.isin(selected.cell_id), 'deposit_id'].nunique()
        output[f'recovery_at_{suffix}'] = hits / n_targets
        output[f'area_fraction_{suffix}'] = float(selected.land_area_m2.sum() / total_area)
    mask = frame.pu_metric_member.to_numpy()
    output['average_precision_PU'] = float(average_precision_score(y[mask], scores[mask]))
    output['roc_auc_PU'] = float(roc_auc_score(y[mask], scores[mask])) if len(np.unique(y[mask])) == 2 else None
    return output


def predict_batches(model, X, columns, batch_size):
    return np.concatenate([model.predict_proba(X.iloc[i:i+batch_size][columns])[:, 1]
                           for i in range(0, len(X), batch_size)])


def fit_one(cfg, e, X, schema, candidate, split_id, repetition=0, feature_set=None):
    sample_path = e/f"samples/{split_id}_ratio{candidate['ratio']}_rep{repetition:02d}.parquet"
    sample = pd.read_parquet(sample_path)
    membership = pd.read_parquet(e/f'memberships/{split_id}.parquet')
    if not sample.cell_id.is_unique or not set(sample.cell_id) <= set(membership.loc[membership.role.eq('train'), 'cell_id']):
        raise ValueError('Muestra fuera del entrenamiento o duplicada.')
    if cfg['mode'] == 'validated' and (not sample.training_allowed.all() or set(sample.sample_role) != {'P_reviewed', 'U_unlabelled'}):
        raise ValueError('Muestra no autorizada como validada.')
    cols = schema[feature_set or cfg['feature_set']]
    seed = ev.seed_for(cfg['seed'], 'model', candidate['family'], split_id, repetition) % (2**32)
    model = make_pipeline(cols['columns'], cols['categorical'], candidate['family'], candidate['params'], seed, cfg['n_jobs'])
    kwargs = {}
    if cfg['fit_weighting'] == 'normalized_design_u':
        weights = np.ones(len(sample)); is_u = sample.sample_class.eq(0).to_numpy()
        raw = sample.loc[is_u, 'area_weight_m2'].to_numpy()
        weights[is_u] = raw/raw.mean()
        kwargs['model__sample_weight'] = weights
    began = time.perf_counter()
    with threadpool_limits(limits=cfg['n_jobs']):
        model.fit(X.loc[sample.cell_id, cols['columns']], sample.sample_class.to_numpy(), **kwargs)
    return model, {'fit_seconds': time.perf_counter()-began, 'train_P': int(sample.sample_class.sum()),
                   'train_U': int(sample.sample_class.eq(0).sum()),
                   'rss_after_fit_mb': psutil.Process().memory_info().rss / 2**20,
                   'sample_path': sample_path.as_posix(), 'sample_sha256': ev.sha256_file(sample_path)}


def evaluate_model(cfg, out, X, model, columns, split_id, records):
    frame = fixed_frame(out, split_id)
    began = time.perf_counter()
    with threadpool_limits(limits=cfg['n_jobs']):
        scores = predict_batches(model, X.loc[frame.cell_id], columns, cfg['prediction_batch_size'])
    result = metrics(frame, scores, records, cfg['mode'])
    result['predict_seconds'] = time.perf_counter()-began
    return frame, scores, result


def save_model(out, tag, model, metadata):
    p = out/f'models/{tag}.joblib'
    temporary = p.with_name('.'+p.name+'.tmp')
    joblib.dump(model, temporary, compress=3); temporary.replace(p)
    q = out/f'models/{tag}.json'; write_json(q, metadata)
    return [p, q]


def save_scores(out, tag, frame, scores, mode, spread=None):
    result = frame[['cell_id']].copy()
    result['score'] = scores; result['mode'] = mode
    result['is_absolute_gold_probability'] = False
    if spread is not None: result['background_score_std'] = spread
    p = out/f'predictions/{tag}.parquet'; ev.atomic_parquet(result, p)
    return p


def fit_family(root, out, family):
    cfg, e, X, schema = load_context(root, out)
    if ev.stage_exists(out, family): return pd.read_csv(out/f'{family}_outer_metrics.csv')
    candidates_list = ev.read_json(out/'candidates.json')[family]
    plans = ev.read_json(e/'split_plan.json')['splits']
    records = pd.read_parquet(out/'evaluation/positive_records.parquet')
    rows, selections, paths = [], [], []
    for outer in [p for p in plans if p['level'] == 'outer']:
        split_id = outer['split_id']; search_rows = []
        inner = [p for p in plans if p['level'] == 'inner' and p['outer_fold'] == outer['outer_fold']]
        for candidate in candidates_list:
            for item in inner:
                model, timing = fit_one(cfg, e, X, schema, candidate, item['split_id'])
                _, _, values = evaluate_model(cfg, out, X, model, schema[cfg['feature_set']]['columns'], item['split_id'], records)
                search_rows.append({'candidate_id': candidate['candidate_id'], 'split_id': item['split_id'], **timing, **values})
                del model
            print(f"{family} {split_id}: candidato {candidate['candidate_id']} evaluado internamente", flush=True)
        search = pd.DataFrame(search_rows)
        # Empate por ID predefinido, nunca por resultados externos.
        ranking = search.groupby('candidate_id')[cfg['primary_metric']].mean().reset_index().sort_values(
            [cfg['primary_metric'], 'candidate_id'], ascending=[False, True])
        winner_id = ranking.candidate_id.iloc[0]
        winner = next(c for c in candidates_list if c['candidate_id'] == winner_id)
        selection = {'outer_split': split_id, **winner, 'mean_inner_recovery_at_05': float(ranking.iloc[0][cfg['primary_metric']])}
        selections.append(selection)
        p = out/f'search/{family}_{split_id}.csv'; search.to_csv(p, index=False); paths.append(p)
        # Guarda la decisión antes de leer scores de test externo.
        p = out/f'search/{family}_{split_id}_selection.json'; write_json(p, selection); paths.append(p)
        model, timing = fit_one(cfg, e, X, schema, winner, split_id)
        frame, scores, values = evaluate_model(cfg, out, X, model, schema[cfg['feature_set']]['columns'], split_id, records)
        tag = f'{family}_{split_id}'
        paths += save_model(out, tag, model, {'selection': selection, 'feature_set': cfg['feature_set'],
                    'columns': schema[cfg['feature_set']]['columns'], 'mode': cfg['mode'], 'production_allowed': False, **timing})
        paths.append(save_scores(out, tag, frame, scores, cfg['mode']))
        rows.append({'family': family, 'split_id': split_id, 'candidate_id': winner_id, 'ratio': winner['ratio'], **timing, **values})
        print(f'{family} {split_id}: modelo y predicciones OOF guardados', flush=True)
    p = out/f'{family}_outer_metrics.csv'; pd.DataFrame(rows).to_csv(p, index=False); paths.append(p)
    p = out/f'{family}_selections.json'; write_json(p, selections); paths.append(p)
    ev.seal_stage(out, family, paths)
    return pd.DataFrame(rows)


def fit_references(root, out):
    cfg, e, X, schema = load_context(root, out)
    if ev.stage_exists(out, 'references'): return pd.read_csv(out/'reference_metrics.csv')
    rows, paths = [], []
    records = pd.read_parquet(out/'evaluation/positive_records.parquet')
    for item in ev.read_json(e/'split_plan.json')['splits']:
        if item['level'] != 'outer': continue
        split_id = item['split_id']; frame = fixed_frame(out, split_id)
        x = X.loc[frame.cell_id]
        # Regla ilustrativa fijada antes de resultados; escala regional de 5 km.
        fault = np.exp(-pd.to_numeric(x.dist_falla_cartografiada_m).fillna(np.inf).to_numpy()/5000.)
        granitoid = pd.to_numeric(x.unidades_granitoides_explicitos_fraccion).fillna(0).clip(0, 1).to_numpy()
        scores = {'constant': np.full(len(frame), .5),
                  'random': np.array([ev.seed_for(cfg['seed'], 'random_reference', c)/2**64 for c in frame.cell_id]),
                  'geological_rule': .5*fault + .5*granitoid}
        for family, values in scores.items():
            rows.append({'family': family, 'split_id': split_id, **metrics(frame, values, records, cfg['mode'])})
            paths.append(save_scores(out, f'{family}_{split_id}', frame, values, cfg['mode']))
    p = out/'reference_metrics.csv'; pd.DataFrame(rows).to_csv(p, index=False); paths.append(p)
    write_json(out/'geological_rule.json', {'formula': '0.5*exp(-dist_falla_cartografiada_m/5000)+0.5*unidades_granitoides_explicitos_fraccion',
                                          'missing': 'componente ausente aporta cero', 'status': 'referencia ilustrativa predefinida, no criterio metalogenético validado'})
    paths.append(out/'geological_rule.json'); ev.seal_stage(out, 'references', paths)
    return pd.DataFrame(rows)


def run_sensitivity(root, out):
    cfg, e, X, schema = load_context(root, out)
    if ev.stage_exists(out, 'sensitivity'): return pd.read_csv(out/'sensitivity_metrics.csv')
    for family in cfg['families']:
        if not ev.stage_exists(out, family): raise ValueError(f'Falta {family}.')
    records = pd.read_parquet(out/'evaluation/positive_records.parquet')
    selections = ev.read_json(out/'random_forest_selections.json')
    rows, paths = [], []
    for selection in selections:
        split_id = selection['outer_split']
        frame = fixed_frame(out, split_id)
        # Ablaciones con parámetros/ratio fijos; no se escoge una por test externo.
        fixed = {'family': 'random_forest', 'ratio': 3, 'params': {'n_estimators': cfg['ablation_trees'],
                  'max_features': 'sqrt', 'min_samples_leaf': 5, 'max_depth': None}}
        for name in schema:
            model, timing = fit_one(cfg, e, X, schema, fixed, split_id, feature_set=name)
            _, scores, values = evaluate_model(cfg, out, X, model, schema[name]['columns'], split_id, records)
            tag = f'ablation_{name}_{split_id}'
            paths += save_model(out, tag, model, {'feature_set': name, 'columns': schema[name]['columns'], 'candidate': fixed,
                        'mode': cfg['mode'], 'production_allowed': False, **timing})
            paths.append(save_scores(out, tag, frame, scores, cfg['mode']))
            rows.append({'experiment': name, 'kind': 'fixed_ablation', 'split_id': split_id, **timing, **values})
        # Bagging de U: mismos parámetros elegidos internamente y mismo test territorial.
        baseline = pd.read_parquet(out/f'predictions/random_forest_{split_id}.parquet')
        if not baseline.cell_id.equals(frame.cell_id): raise ValueError('Evaluación PU desalineada.')
        predictions = [baseline.score.to_numpy()]
        for repetition in cfg['pu_realizations'][1:]:
            model, timing = fit_one(cfg, e, X, schema, selection, split_id, repetition)
            _, scores, _ = evaluate_model(cfg, out, X, model, schema[cfg['feature_set']]['columns'], split_id, records)
            tag = f'pu_rep{repetition:02d}_{split_id}'
            paths += save_model(out, tag, model, {'selection': selection, 'repetition': repetition,
                        'columns': schema[cfg['feature_set']]['columns'], 'mode': cfg['mode'], 'production_allowed': False, **timing})
            paths.append(save_scores(out, tag, frame, scores, cfg['mode']))
            predictions.append(scores)
        mean = np.mean(predictions, axis=0); spread = np.std(predictions, axis=0)
        paths.append(save_scores(out, f'pu_bagging_{split_id}', frame, mean, cfg['mode'], spread))
        rows.append({'experiment': 'pu_bagging', 'kind': 'background_sensitivity', 'split_id': split_id,
                     **metrics(frame, mean, records, cfg['mode'])})
        print('Ablaciones y PU:', split_id, flush=True)
    p = out/'sensitivity_metrics.csv'; pd.DataFrame(rows).to_csv(p, index=False); paths.append(p)
    p = out/'pending_experiments.json'; write_json(p, {
        '500m_and_buffers': 'Requiere nuevas ejecuciones C/D/E; no interpolar ni alterar folds sellados.',
        'geophysics_and_alluvial': 'No hay bloques cuantitativos/cuencas aprobados en D.',
        'label_confidence': 'Requiere revisión B y propagación hasta E.',
        'observation_effort': 'Fuente verificable ausente; no se simula.',
        'extended_models': 'XGBoost/LightGBM/CatBoost y KNN/SVM son ampliaciones opcionales.',
        'larger_search': 'Piloto de 3 candidatos por familia; 20–30 mediante search_trials tras revisar protocolo.',
        'pu_interpretation': 'Variación de fondo y semilla del estimador; no intervalo de confianza de mineralización.'}); paths.append(p)
    ev.seal_stage(out, 'sensitivity', paths)
    return pd.DataFrame(rows)


def finish_run(root, out):
    cfg, e, X, schema = load_context(root, out)
    if (out/'outputs_manifest.json').exists():
        ev.verify(out, ev.read_json(out/'outputs_manifest.json')); return ev.read_json(out/'control_cierre.json')
    for name in ['references', *cfg['families'], 'sensitivity']:
        if not ev.stage_exists(out, name): raise ValueError(f'Falta etapa {name}.')
    comparison = pd.concat([pd.read_csv(out/'reference_metrics.csv')] +
                           [pd.read_csv(out/f'{family}_outer_metrics.csv') for family in cfg['families']], ignore_index=True)
    comparison.to_csv(out/'comparison_by_fold.csv', index=False)
    comparison.groupby('family')[['recovery_at_01', 'recovery_at_05', 'recovery_at_10', 'average_precision_PU', 'roc_auc_PU']].agg(
        ['mean', 'std']).to_csv(out/'comparison_summary.csv')
    selections = [s for family in cfg['families'] for s in ev.read_json(out/f'{family}_selections.json')]
    chosen = []
    records = pd.read_parquet(out/'evaluation/positive_records.parquet')
    for split_id in sorted({s['outer_split'] for s in selections}):
        winner = sorted([s for s in selections if s['outer_split'] == split_id],
                        key=lambda s: (-s['mean_inner_recovery_at_05'], s['family'], s['candidate_id']))[0]
        frame = fixed_frame(out, split_id)
        prediction = pd.read_parquet(out/f"predictions/{winner['family']}_{split_id}.parquet")
        if not prediction.cell_id.equals(frame.cell_id): raise ValueError('OOF desalineada.')
        save_scores(out, f'nested_selected_{split_id}', frame, prediction.score.to_numpy(), cfg['mode'])
        chosen.append({**winner, **metrics(frame, prediction.score, records, cfg['mode'])})
    pd.DataFrame(chosen).to_csv(out/'nested_procedure_metrics.csv', index=False)
    write_json(out/'selection_contract.json', {'primary': cfg['primary_metric'], 'aggregation': 'media de folds internos',
        'selection': 'familia y candidato por resultado interno, desempate determinista',
        'external_comparison': 'descriptiva; no se elige ganador global por resultados externos',
        'ablation': 'parámetros fijos; exploratoria, no incorporada a selección del ganador',
        'holdout': 'sin predicciones ni métricas; no abierto', 'absolute_gold_probability': False})
    control = {'estado_ejecucion': 'completada', 'mode': cfg['mode'],
        'scientific_training_allowed': cfg['mode'] == 'validated', 'scientific_validation_complete': False,
        'prediction_allowed': False, 'production_allowed': False, 'outer_folds': len(chosen),
        'search_trials_per_family': cfg['search_trials'], 'families': cfg['families'],
        'fitted_model_files': len(list((out/'models').glob('*.joblib'))),
        'reason': 'Ensayo con candidatos y predictores no aprobados; revisar B/D/E antes de validación científica.' if cfg['mode'] == 'diagnostic' else 'Pendiente evaluación científica G; reserva no abierta.'}
    write_json(out/'control_cierre.json', control)
    files = sorted(p for p in out.rglob('*') if p.is_file() and p.name != 'outputs_manifest.json' and not p.name.startswith('.'))
    write_json(out/'outputs_manifest.json', ev.records(out, files))
    return control
