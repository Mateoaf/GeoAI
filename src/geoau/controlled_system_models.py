"""Shared estimators and nested, training-only fusion used by Notebook 27."""
from __future__ import annotations

import itertools
import json
from pathlib import Path
import time

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline

from .controlled_system_features import DIAGNOSTIC, FoldPathfinders, geological_rule
from .geochemical_experiment import cell_hash, make_preprocessor, predict


COMPONENTS = ("mono93", "mono95", "primario", "aluvial", "primario_otro", "epitermal")
METHODS = ("mono93", "mono95", "max_2", "fusion_2", "max_3", "fusion_3", "regla_geologica")
FAMILIES = {"fusion_2": ["mono95", "primario", "aluvial"],
            "fusion_3": ["mono95", "primario_otro", "aluvial", "epitermal"]}


class BackgroundCDF(TransformerMixin, BaseEstimator):
    """Interpolate background midranks with fixed 0/1 endpoints.

    References are U predictions made out of fold inside training. Values are
    relative background percentiles, not calibrated mineralization probabilities.
    Applying to another batch cannot change a cell's normalized score.
    """
    def fit(self, X, y=None):
        values = np.asarray(X, dtype=float).ravel()
        values = values[np.isfinite(values)]
        self.available_ = len(values) > 0
        if self.available_:
            unique, counts = np.unique(values, return_counts=True)
            midranks = (np.cumsum(counts)-.5*counts)/len(values)
            inside = (unique > 0) & (unique < 1)
            self.x_ = np.r_[0., unique[inside], 1.]
            self.p_ = np.r_[0., midranks[inside], 1.]
        return self

    def transform(self, X):
        values = np.asarray(X, dtype=float)
        if not self.available_:
            return np.full(values.shape, np.nan)
        return np.interp(values, self.x_, self.p_, left=0., right=1.)


def blend(matrix, weights):
    matrix, weights = np.asarray(matrix, float), np.asarray(weights, float)
    valid = np.isfinite(matrix)
    denominator = valid @ weights
    result = np.divide(np.nan_to_num(matrix) @ weights, denominator,
                       out=np.zeros(len(matrix)), where=denominator > 0)
    return np.where(denominator > 0, result, matrix[:, 0])


def choose_weights(y, matrix, step=.1):
    """Pooled inner AP; a >=0.1 global backbone retains unresolved presences."""
    n = matrix.shape[1]
    divisions = int(round(1/step))
    available = np.isfinite(matrix).any(axis=0)
    if not available[0]:
        raise ValueError("No hay predicciones internas del componente global.")
    candidates = [available.astype(float)/available.sum()]
    candidates += [np.asarray(v, float)/divisions for v in itertools.product(range(divisions+1), repeat=n)
                   if sum(v) == divisions and v[0] >= 1
                   and not np.any(np.asarray(v)[~available])]
    candidates = np.unique(candidates, axis=0)
    rows = []
    for w in candidates:
        rows.append({"weights": json.dumps(w.tolist()),
                     "average_precision": float(average_precision_score(y, blend(matrix, w))),
                     "distance_uniform": float(np.square(w-1/n).sum())})
    best = min(range(len(rows)), key=lambda i: (-round(rows[i]["average_precision"], 12),
                                               rows[i]["distance_uniform"], rows[i]["weights"]))
    table = pd.DataFrame(rows)
    table["selected"] = np.arange(len(table)) == best
    return candidates[best], table


def fit_components(data, X, systems, pool, expected_p, evaluation_ids, cfg, seed, folder,
                   scope, partition, level, log):
    """A single sampling/fitting implementation for inner, outer and national fits."""
    expected_p = set(expected_p)
    pool_ids = pd.Index(pool.cell_id)
    all_p = data.positives.set_index("cell_id")
    actual_p = set(pool_ids.intersection(all_p.index))
    if actual_p != expected_p:
        raise AssertionError("Las P admisibles no coinciden con la partición declarada.")
    if set(evaluation_ids) & set(pool_ids) and scope != "national":
        raise AssertionError("El entrenamiento contiene celdas evaluadas.")
    p = data.positives.loc[data.positives.cell_id.isin(pool_ids)].copy()
    background = pool.loc[~pool.cell_id.isin(all_p.index), "cell_id"].to_numpy()
    flags = systems.set_index("cell_id")
    targets = {"mono93": p, "mono95": p}
    for component in COMPONENTS[2:]:
        targets[component] = p.loc[flags.loc[p.cell_id, component].to_numpy()]
    columns = {c: [n for n in X.columns if c != "mono93" or n not in DIAGNOSTIC] for c in COMPONENTS}
    estimators = {c: [] for c in COMPONENTS}
    # Keep every member's predictions to replay the stored outer/national models.
    scores = {c: np.full((len(evaluation_ids), cfg["bags"]), np.nan) for c in COMPONENTS}
    training, runs = [], []
    test_X = X.loc[evaluation_ids]
    started = time.perf_counter()
    for member in range(cfg["bags"]):
        sample_seed = seed+5000+member*101
        rng = np.random.default_rng(sample_seed)
        draw = background[rng.choice(len(background), min(len(background), 3*len(p)), replace=False)]
        cache = {}
        for component in COMPONENTS:
            target = targets[component]
            if len(target) < cfg["minimum_specialist_P"]:
                continue
            n_u = 3*len(target)
            if len(draw) < n_u:
                raise ValueError("Fondo insuficiente para U:P=3:1 sin reemplazo.")
            sample = pd.concat([target[["cell_id", "peso_confianza"]].assign(label=1),
                pd.DataFrame({"cell_id": draw[:n_u], "peso_confianza": 1., "label": 0})], ignore_index=True)
            if sample.cell_id.duplicated().any():
                raise AssertionError("Muestreo con reemplazo no autorizado.")
            params = dict(cfg["classifier"])
            if component == "epitermal":
                params.update(cfg["epithermal_classifier"])
            params["random_state"] = seed+member
            key = (tuple(target.cell_id), tuple(columns[component]), tuple(sorted(params.items())))
            reused = key in cache
            if reused:
                pipeline, score = cache[key]
            else:
                pipeline = Pipeline([
                    ("derived_training_statistics", FoldPathfinders()),
                    ("preprocess", make_preprocessor(columns[component], data.config["geochemical_columns"])),
                    ("model", lgb.LGBMClassifier(**params)),
                ])
                pipeline.fit(X.loc[sample.cell_id, columns[component]], sample.label,
                             model__sample_weight=sample.peso_confianza)
                score = predict(pipeline, test_X[columns[component]], cfg["prediction_batch_size"])
                cache[key] = pipeline, score
            estimators[component].append(pipeline)
            scores[component][:, member] = score
            training.append(sample.assign(component=component, member=member, level=level))
            runs.append({"scope": scope, "partition": partition, "level": level, "component": component,
                "member": member, "sample_seed": sample_seed, "classifier_seed": seed+member,
                "n_P": len(target), "n_U": n_u, "sample_hash": cell_hash(sample.cell_id),
                "positive_hash": cell_hash(target.cell_id), "reused_identical_fit": reused})
    means = pd.DataFrame({"cell_id": evaluation_ids})
    for component in COMPONENTS:
        means[component] = scores[component].mean(axis=1)
    folder.mkdir(parents=True, exist_ok=True)
    if training:
        pd.concat(training, ignore_index=True).to_parquet(folder / f"training_{level}.parquet", index=False)
    pd.DataFrame(runs).to_csv(folder / f"fits_{level}.csv", index=False)
    means.to_parquet(folder / f"raw_{level}.parquet", index=False)
    log(f"{scope} {partition} {level}: P={len(p)}, especialistas="
        +str({c: len(targets[c]) for c in COMPONENTS[2:]})+f", {len(runs)} ajustes declarados, {time.perf_counter()-started:.1f}s")
    return estimators, means, scores, runs


class ControlledSystemBundle:
    """Final fitted members plus training-derived normalization and fusion."""
    def __init__(self, estimators, normalizers, weights, feature_columns, default="fusion_3"):
        self.estimators = estimators
        self.normalizers = normalizers
        self.weights = weights
        self.feature_columns = list(feature_columns)
        self.default = default

    def predict_raw(self, X, batch_size=25000):
        scores, std = {}, {}
        for c in COMPONENTS:
            if self.estimators[c]:
                columns = [n for n in self.feature_columns if c != "mono93" or n not in DIAGNOSTIC]
                values = np.column_stack([predict(m, X[columns], batch_size) for m in self.estimators[c]])
                scores[c], std[c] = values.mean(axis=1), values.std(axis=1)
            else:
                scores[c], std[c] = np.full(len(X), np.nan), np.full(len(X), np.nan)
        return pd.DataFrame(scores, index=X.index), pd.DataFrame(std, index=X.index)

    def combine(self, raw, X):
        norm = pd.DataFrame({c: self.normalizers[c].transform(raw[c]) for c in COMPONENTS}, index=raw.index)
        scores = pd.DataFrame({"mono93": raw.mono93, "mono95": raw.mono95}, index=raw.index)
        for count in [2, 3]:
            family = FAMILIES[f"fusion_{count}"]
            # Same components for maximum and learned fusion: only aggregation changes.
            experts = norm[family].to_numpy()
            valid = np.isfinite(experts).any(axis=1)
            maximum = np.where(np.isfinite(experts), experts, -np.inf).max(axis=1)
            scores[f"max_{count}"] = np.where(valid, maximum, norm.mono95)
            scores[f"fusion_{count}"] = blend(norm[family].to_numpy(), self.weights[f"fusion_{count}"])
        scores["regla_geologica"] = geological_rule(X)
        if not np.isfinite(scores.to_numpy()).all():
            raise ValueError("Predicciones finales no finitas.")
        return scores[list(METHODS)], norm

    def predict(self, X):
        raw, _ = self.predict_raw(X)
        return self.combine(raw, X)[0][self.default].to_numpy()


def fit_nested(data, X, systems, pool, expected_p, evaluation_ids, cfg, seed, folder,
               scope, partition, make_inner_splits, log):
    """Outer evaluation data is never supplied to normalization/weight fitting."""
    inner_sample, memberships, inner_parts = make_inner_splits(pool, seed)
    inner_predictions = []
    for inner_fold, inner_pool, test in inner_parts:
        p_ids = data.positives.loc[data.positives.cell_id.isin(inner_pool.cell_id), "cell_id"]
        _, raw, _, _ = fit_components(data, X, systems, inner_pool, p_ids, test.cell_id,
            cfg, seed+1000*(inner_fold+1), folder, scope, partition, f"inner_{inner_fold}", log)
        inner_predictions.append(raw.merge(test[["cell_id", "label"]], validate="one_to_one").assign(inner_fold=inner_fold))
    inner = pd.concat(inner_predictions, ignore_index=True)
    if inner.cell_id.duplicated().any() or set(inner.cell_id) != set(inner_sample.cell_id):
        raise AssertionError("Las predicciones internas no son OOF completas.")
    membership = pd.concat(memberships, ignore_index=True)
    membership.to_parquet(folder / "inner_memberships.parquet", index=False)
    inner.to_parquet(folder / "inner_predictions.parquet", index=False)
    normalized = pd.DataFrame(index=inner.index, columns=COMPONENTS, dtype=float)
    # Cross-fitted background references for choosing the weights.
    for fold in sorted(inner.inner_fold.unique()):
        target = inner.inner_fold.eq(fold)
        reference_u = inner.inner_fold.ne(fold) & inner.label.eq(0)
        for component in COMPONENTS:
            normalizer = BackgroundCDF().fit(inner.loc[reference_u, component])
            normalized.loc[target, component] = normalizer.transform(inner.loc[target, component])
    normalized.to_parquet(folder / "inner_normalized_predictions.parquet", index=False)
    normalizers = {c: BackgroundCDF().fit(inner.loc[inner.label.eq(0), c]) for c in COMPONENTS}
    weights, searches = {}, []
    for method, family in FAMILIES.items():
        w, search = choose_weights(inner.label, normalized[family].to_numpy(), cfg["weight_step"])
        weights[method] = w
        searches.append(search.assign(method=method))
    pd.concat(searches, ignore_index=True).to_csv(folder / "weight_search.csv", index=False)
    estimators, raw, member_scores, runs = fit_components(data, X, systems, pool, expected_p,
        evaluation_ids, cfg, seed, folder, scope, partition, "outer", log)
    bundle = ControlledSystemBundle(estimators, normalizers, weights, X.columns)
    scores, norm = bundle.combine(raw.set_index("cell_id"), X.loc[evaluation_ids])
    combined = scores.copy()
    for c in COMPONENTS:
        combined[f"raw_{c}"] = raw.set_index("cell_id")[c]
        combined[f"normalized_{c}"] = norm[c]
    combined.index.name = "cell_id"
    combined.reset_index().to_parquet(folder / "predictions.parquet", index=False)
    joblib.dump(bundle, folder / "model.joblib", compress=3)
    (folder / "weights.json").write_text(json.dumps({m: dict(zip(FAMILIES[m], map(float, w)))
        for m, w in weights.items()}, indent=2), encoding="utf-8")
    return bundle, combined.reset_index()
