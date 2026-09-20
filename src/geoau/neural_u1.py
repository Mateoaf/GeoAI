"""Unidad 1: fundamentos y MLP diagnóstica en validación espacial de E/F.

No evalúa test externo ni reserva. TensorFlow es una dependencia opcional,
importada solo al construir redes; las fases anteriores conservan su entorno.
"""
from datetime import datetime, timezone
import importlib.metadata
from pathlib import Path
import sys
import time

import joblib
import numpy as np
import pandas as pd
from scipy.special import expit, softmax
from sklearn.linear_model import Perceptron
from sklearn.metrics import accuracy_score, f1_score
from threadpoolctl import threadpool_limits
import yaml

from . import evaluation as ev
from . import training as tr


def tensorflow():
    try:
        import tensorflow as tf
    except ImportError as exc:
        raise RuntimeError('Unidad 1 requiere el entorno .venv-unidad1 (Python 3.13) '
                           'con requirements-unidad1.txt.') from exc
    return tf


def step01(z):
    return (np.asarray(z) >= 0).astype(int)


def perceptron_predict(X, w, b):
    return step01(np.asarray(X) @ np.asarray(w) + b)


def xor_manual(X):
    """OR y AND como representación oculta; salida OR - AND."""
    X = np.asarray(X)
    hidden = np.column_stack((perceptron_predict(X, [1, 1], -.5),
                              perceptron_predict(X, [1, 1], -1.5)))
    return perceptron_predict(hidden, [1, -1], -.5)


def activations(z):
    z = np.asarray(z, dtype=float)
    return {'step': step01(z), 'sigmoid': expit(z), 'tanh': np.tanh(z),
            'ReLU': np.maximum(z, 0), 'LeakyReLU': np.where(z >= 0, z, .1*z),
            'linear': z}


def forward_manual(x):
    x = np.asarray(x, dtype=float)
    W1 = np.array([[.8, -.4, .5], [-.3, .9, .2]])
    z1 = x @ W1 + np.array([.1, -.2, .05])
    h1 = np.maximum(z1, 0)
    z2 = h1 @ np.array([.7, -.5, .4]) + .02
    return {'x': x, 'z1': z1, 'h1': h1, 'z2': z2, 'score_PU': expit(z2)}


def logistic_loss_gradient(theta, X, y):
    """BCE estable desde logits y derivada manual para P/U (no calibra oro)."""
    X, y = np.asarray(X, float), np.asarray(y, float)
    logits = X @ theta[:-1] + theta[-1]
    loss = np.mean(np.logaddexp(0, logits) - y * logits)
    error = expit(logits) - y
    gradient = np.r_[X.T @ error / len(y), error.mean()]
    return float(loss), gradient


def gradient_check(theta, X, y, epsilon=1e-6):
    _, analytic = logistic_loss_gradient(theta, X, y)
    numeric = np.empty_like(analytic)
    for j in range(len(theta)):
        delta = np.zeros_like(analytic); delta[j] = epsilon
        numeric[j] = (logistic_loss_gradient(theta+delta, X, y)[0] -
                      logistic_loss_gradient(theta-delta, X, y)[0]) / (2*epsilon)
    return pd.DataFrame({'analytic': analytic, 'finite_difference': numeric,
                         'absolute_error': np.abs(analytic-numeric)})


def gradient_descent(X, y, epochs=200, learning_rate=.05):
    theta = np.zeros(np.asarray(X).shape[1]+1)
    history = []
    for _ in range(epochs):
        loss, gradient = logistic_loss_gradient(theta, X, y)
        history.append(loss)
        theta -= learning_rate * gradient
    return theta, np.asarray(history)


def make_preprocessor(columns, categorical):
    # Reutiliza guardia, imputación y codificación de F; descarta su estimador.
    return tr.make_pipeline(columns, categorical, 'logistic', {}, 42, 1)[:-1]


def build_binary_mlp(n_features, hidden=(32, 16), dropout=0., l2=0., lr=.001, seed=42):
    if n_features < 1 or not hidden or any(int(n) != n or n < 1 for n in hidden):
        raise ValueError('Dimensiones de la red inválidas.')
    if not 0 <= dropout < 1 or l2 < 0 or lr <= 0:
        raise ValueError('Regularización o tasa de aprendizaje inválida.')
    tf = tensorflow()
    tf.keras.utils.set_random_seed(seed)
    reg = tf.keras.regularizers.l2(l2) if l2 else None
    layers = [tf.keras.layers.Input(shape=(n_features,))]
    for units in hidden:
        layers.append(tf.keras.layers.Dense(units, activation='relu', kernel_regularizer=reg))
        if dropout: layers.append(tf.keras.layers.Dropout(dropout))
    layers.append(tf.keras.layers.Dense(1, activation='sigmoid'))
    model = tf.keras.Sequential(layers)
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=lr),
                  loss='binary_crossentropy',
                  metrics=['accuracy', tf.keras.metrics.AUC(name='auc')])
    return model


def fit_mlp(X_train, y_train, X_validation, y_validation, architecture, cfg):
    tf = tensorflow()
    tf.keras.backend.clear_session()
    model = build_binary_mlp(X_train.shape[1], hidden=architecture['hidden'],
                            dropout=architecture['dropout'], l2=architecture['l2'],
                            lr=cfg['learning_rate'], seed=cfg['seed'])
    callback = tf.keras.callbacks.EarlyStopping(monitor='val_loss', mode='min',
                                                patience=cfg['patience'], restore_best_weights=True)
    history = model.fit(X_train, y_train, validation_data=(X_validation, y_validation),
                        epochs=cfg['epochs'], batch_size=cfg['batch_size'],
                        callbacks=[callback, tf.keras.callbacks.TerminateOnNaN()], verbose=0)
    history = pd.DataFrame(history.history)
    if not np.isfinite(history.to_numpy()).all():
        raise ValueError('Entrenamiento no finito; no se aceptan resultados parciales.')
    history.insert(0, 'epoch', np.arange(1, len(history)+1))
    return model, history


def check_partition(sample, membership, frame, parent, holdout):
    """Solo train interno y validation dentro de train externo; nunca reserva."""
    if not sample.cell_id.is_unique or not membership.cell_id.is_unique or not frame.cell_id.is_unique:
        raise ValueError('Claves duplicadas.')
    train, validation = set(sample.cell_id), set(frame.cell_id)
    allowed_train = set(membership.loc[membership.role.eq('train'), 'cell_id'])
    allowed_val = set(membership.loc[membership.role.eq('test'), 'cell_id'])
    parent_train = set(parent.loc[parent.role.eq('train'), 'cell_id'])
    if not train or not validation or not train <= allowed_train or validation != allowed_val:
        raise ValueError('Muestra o marco fuera de su partición interna.')
    if train & validation or (train | validation) & set(holdout) or not (train | validation) <= parent_train:
        raise ValueError('Fuga a validación, test externo o reserva.')
    if set(sample.sample_class) != {0, 1}:
        raise ValueError('El entrenamiento necesita ambas clases P/U.')
    if set(frame.loc[frame.pu_metric_member, 'observed_P'].astype(int)) != {0, 1}:
        raise ValueError('La validación necesita ambas clases P/U.')


def load_context(root, cfg):
    root = Path(root).resolve()
    source = root/cfg['phase_f_run']
    fcfg, e, X, schemas = tr.load_context(root, source)
    if fcfg['fit_weighting'] != 'none':
        raise ValueError('U1 implementa el diseño sin pesos adicionales de F.')
    if cfg['ratio_u_to_p'] not in fcfg['ratios_u_to_p'] or cfg['repetition'] not in fcfg['pu_realizations']:
        raise ValueError('Muestra P/U no incluida en F.')
    plan = ev.read_json(e/'split_plan.json')['splits']
    outer = next((p for p in plan if p['level'] == 'outer' and p['split_id'] == cfg['outer_split']), None)
    if outer is None: raise ValueError('Fold externo desconocido.')
    inner = [p['split_id'] for p in plan if p['level'] == 'inner' and p['outer_fold'] == outer['outer_fold']]
    if len(inner) < 2: raise ValueError('Se necesitan varios folds internos.')
    units = pd.read_parquet(e/'design/spatial_units.parquet')
    parent = pd.read_parquet(e/f"memberships/{cfg['outer_split']}.parquet")
    holdout = set(units.loc[units.holdout, 'cell_id'])
    partitions = {}
    for split in inner:
        sample_path = e/f"samples/{split}_ratio{cfg['ratio_u_to_p']}_rep{cfg['repetition']:02d}.parquet"
        sample = pd.read_parquet(sample_path)
        frame = tr.fixed_frame(source, split)
        check_partition(sample, pd.read_parquet(e/f'memberships/{split}.parquet'), frame, parent, holdout)
        if fcfg['mode'] == 'validated' and (not sample.training_allowed.all() or
                set(sample.sample_role) != {'P_reviewed', 'U_unlabelled'}):
            raise ValueError('Muestra no autorizada para modo validado.')
        partitions[split] = (sample, frame, sample_path)
    return fcfg, source, X, schemas[fcfg['feature_set']], partitions


def read_config(root):
    cfg = yaml.safe_load((Path(root)/'config/unidad1.yaml').read_text(encoding='utf-8'))
    for key in ('epochs', 'batch_size', 'patience'):
        if type(cfg[key]) is not int or cfg[key] < 1: raise ValueError(key)
    names = [a['name'] for a in cfg['architectures']]
    if not names or len(names) != len(set(names)) or any(not n.startswith('mlp_') or not n.replace('_', '').isalnum() for n in names):
        raise ValueError('Nombres de arquitectura inválidos o repetidos.')
    if not 0 <= cfg['minimum_relevant_gain'] <= 1: raise ValueError('Margen inválido.')
    return cfg


def validation_decision(table, margin):
    """Selección exploratoria interna; comparación pareada contra RF y logística."""
    pivot = table.pivot(index='split_id', columns='model', values='recovery_at_05')
    names = sorted(n for n in pivot if n.startswith('mlp_'))
    if pivot.isna().any().any(): raise ValueError('Comparación incompleta.')
    winner = sorted(names, key=lambda n: (-pivot[n].mean(), n))[0]
    deltas = {baseline: float((pivot[winner]-pivot[baseline]).mean())
              for baseline in ('random_forest', 'logistic')}
    return {'selected_by_validation': winner, 'minimum_relevant_gain': margin,
            'mean_paired_gain': deltas,
            'promising_in_validation': all(v >= margin for v in deltas.values()),
            'improvement_demonstrated_on_test': False,
            'interpretation': 'Selección exploratoria sobre folds internos dependientes; '
                              'requiere evaluación final independiente para demostrar mejora.'}


def run_experiment(root):
    root = Path(root).resolve(); cfg = read_config(root)
    tf = tensorflow()
    tf.config.experimental.enable_op_determinism()
    fcfg, source, X, schema, partitions = load_context(root, cfg)
    out = root/cfg['output_directory']/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    out.mkdir(parents=True)
    for folder in ('models', 'histories', 'predictions'): (out/folder).mkdir()
    frozen = [root/'config/unidad1.yaml', Path(__file__).resolve(),
              root/'src/geoau/training.py', source/'inputs.json', source/'preparation_manifest.json']
    ev.write_json(out/'inputs.json', ev.records(root, frozen))
    ev.write_json(out/'config_snapshot.json', cfg)
    ev.write_json(out/'feature_schema.json', schema)
    ev.write_json(out/'environment.json', {'python': sys.version, **{n: importlib.metadata.version(n)
        for n in ('tensorflow', 'keras', 'scikit-learn', 'numpy', 'pandas', 'joblib')}})
    ev.write_json(out/'control.json', {'status': 'running', 'production_allowed': False})
    records = pd.read_parquet(source/'evaluation/positive_records.parquet')
    rows = []
    for split, (sample, frame, sample_path) in partitions.items():
        raw_train = X.loc[sample.cell_id, schema['columns']]
        raw_val = X.loc[frame.cell_id, schema['columns']]
        y = sample.sample_class.to_numpy(dtype=np.float32)
        mask = frame.pu_metric_member.to_numpy(dtype=bool)
        yval = frame.loc[mask, 'observed_P'].to_numpy(dtype=np.float32)
        pre = make_preprocessor(**schema)
        train = pre.fit_transform(raw_train).astype(np.float32)
        val = pre.transform(raw_val).astype(np.float32)
        if not np.isfinite(train).all() or not np.isfinite(val).all(): raise ValueError('X no finita.')
        joblib.dump(pre, out/f'models/preprocessor_{split}.joblib', compress=3)
        ev.write_json(out/f'models/sample_{split}.json', {'path': sample_path.relative_to(root).as_posix(),
                      'sha256': ev.sha256_file(sample_path), 'train_P': int(y.sum()),
                      'train_U': int((y == 0).sum()), 'validation_cells': len(frame),
                      'transformed_features': train.shape[1], 'mode': fcfg['mode'], 'production_allowed': False})
        def record(name, scores, seconds, parameters=None, best_epoch=None):
            values = tr.metrics(frame, scores, records, fcfg['mode'])
            rows.append({'model': name, 'split_id': split, 'role': 'validation',
                         'mode': fcfg['mode'], 'fit_seconds': seconds, 'parameters': parameters,
                         'best_epoch': best_epoch, 'accuracy_PU_at_05': accuracy_score(yval, scores[mask] >= .5),
                         'f1_PU_at_05': f1_score(yval, scores[mask] >= .5, zero_division=0), **values})
            tr.save_scores(out, f'{name}_{split}', frame, scores, fcfg['mode'])
            pd.DataFrame(rows).to_csv(out/'validation_metrics.csv', index=False)
            print(f"{split} {name}: recovery@5%={values['recovery_at_05']:.4f}", flush=True)
        # RF y logística se reajustan con exactamente las mismas filas que las MLP.
        for family, params in [('logistic', {'C': 1.}), ('random_forest', {
                'n_estimators': fcfg['forest_trees'], 'min_samples_leaf': 5, 'max_features': 'sqrt'})]:
            model = tr.make_pipeline(**schema, family=family, params=params, seed=cfg['seed'], n_jobs=fcfg['n_jobs'])
            started = time.perf_counter()
            with threadpool_limits(limits=fcfg['n_jobs']): model.fit(raw_train, y)
            seconds = time.perf_counter()-started
            scores = tr.predict_batches(model, raw_val, schema['columns'], fcfg['prediction_batch_size'])
            joblib.dump(model, out/f'models/{family}_{split}.joblib', compress=3)
            record(family, scores, seconds)
        model = Perceptron(random_state=cfg['seed'], max_iter=2000, tol=1e-4)
        started = time.perf_counter(); model.fit(train, y)
        seconds = time.perf_counter()-started
        # Sigmoid monótona para ranking; este perceptrón no está calibrado.
        record('perceptron', expit(model.decision_function(val)), seconds)
        joblib.dump(model, out/f'models/perceptron_{split}.joblib', compress=3)
        for architecture in cfg['architectures']:
            name = architecture['name']; started = time.perf_counter()
            model, history = fit_mlp(train, y, val[mask], yval, architecture, cfg)
            seconds = time.perf_counter()-started
            scores = model.predict(val, batch_size=fcfg['prediction_batch_size'], verbose=0).ravel()
            model.save(out/f'models/{name}_{split}.keras')
            history.to_csv(out/f'histories/{name}_{split}.csv', index=False)
            record(name, scores, seconds, model.count_params(), int(history.loc[history.val_loss.idxmin(), 'epoch']))
    table = pd.DataFrame(rows)
    decision = validation_decision(table, cfg['minimum_relevant_gain'])
    ev.write_json(out/'decision.json', decision)
    table.groupby('model')[['recovery_at_05', 'average_precision_PU', 'roc_auc_PU', 'f1_PU_at_05']].agg(
        ['mean', 'std']).to_csv(out/'validation_summary.csv')
    ev.verify(root, ev.read_json(out/'inputs.json'))
    ev.write_json(out/'control.json', {'status': 'completed', 'scope': 'U1.1-U1.7', 'mode': fcfg['mode'],
        'test_evaluated': False, 'holdout_evaluated': False, 'production_allowed': False,
        'is_absolute_gold_probability': False})
    paths = [p for p in out.rglob('*') if p.is_file()]
    ev.write_json(out/'outputs_manifest.json', ev.records(out, paths))
    ev.write_json(out.parent/'current_run.json', {'run': out.relative_to(root).as_posix()})
    return out


def completed_run(root):
    root = Path(root).resolve(); cfg = read_config(root)
    out = root/ev.read_json(root/cfg['output_directory']/'current_run.json')['run']
    if ev.read_json(out/'config_snapshot.json') != cfg: raise ValueError('Configuración U1 modificada.')
    ev.verify(root, ev.read_json(out/'inputs.json'))
    ev.verify(out, ev.read_json(out/'outputs_manifest.json'))
    source = root/cfg['phase_f_run']
    ev.verify(root, ev.read_json(source/'inputs.json')['frozen'])
    return out
