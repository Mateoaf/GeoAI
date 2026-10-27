"""Paired ablations and genuinely fitted NB29 models, sharing NB27 sampling."""
from __future__ import annotations

import json
import time
import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from .controlled_system_features import FoldPathfinders
from .controlled_system_models import BackgroundCDF, blend, choose_weights
from .geochemical_experiment import cell_hash, make_preprocessor, predict
from .prospective_features import ALLUVIAL, SPECTRAL, NEW_FEATURES

COMPONENTS29 = ("mono96_aluvial", "mono96_espectral", "mono97", "primario97", "aluvial97", "epitermal97")
FAMILY29 = ["mono97", "primario97", "aluvial97", "epitermal97"]
NEW_METHODS29 = ["mono96_aluvial", "mono96_espectral", "mono97", "max3_97", "fusion3_97"]
REFERENCES29 = {"mono95_ref": "mono95", "max3_95_ref": "max_3", "fusion3_95_ref": "fusion_3", "regla_geologica_ref": "regla_geologica"}
METHODS29 = list(REFERENCES29)+NEW_METHODS29
SPECIALIST_FLAGS = {"primario97": "primario_otro", "aluvial97": "aluvial", "epitermal97": "epitermal"}


def component_columns(columns, component):
    exclude = [SPECTRAL] if component == "mono96_aluvial" else [ALLUVIAL] if component == "mono96_espectral" else []
    return [c for c in columns if c not in exclude]


def fit29(data, X, systems, pool, expected_p, ids, cfg, seed, folder, scope, partition, level, log):
    p = data.positives.loc[data.positives.cell_id.isin(pool.cell_id)].copy()
    if set(p.cell_id) != set(expected_p):
        raise AssertionError("Las P no coinciden con el control pareado.")
    if scope != "national" and set(ids) & set(pool.cell_id):
        raise AssertionError("El entrenamiento invade la evaluación externa.")
    all_p = set(data.positives.cell_id)
    background = pool.loc[~pool.cell_id.isin(all_p), "cell_id"].to_numpy()
    flags = systems.set_index("cell_id")
    targets = {c: p if c not in SPECIALIST_FLAGS else p.loc[flags.loc[p.cell_id, SPECIALIST_FLAGS[c]].to_numpy()]
               for c in COMPONENTS29}
    estimators = {c: [] for c in COMPONENTS29}
    scores = {c: [] for c in COMPONENTS29}
    rows, runs = [], []
    started = time.perf_counter()
    for member in range(cfg["bags"]):
        sample_seed = seed+5000+member*101
        rng = np.random.default_rng(sample_seed)
        draw = background[rng.choice(len(background), 3*len(p), replace=False)]
        for c in COMPONENTS29:
            target = targets[c]
            if len(target) < cfg["minimum_specialist_P"]:
                continue
            sample = pd.concat([target[["cell_id", "peso_confianza"]].assign(label=1),
                pd.DataFrame({"cell_id": draw[:3*len(target)], "peso_confianza": 1., "label": 0})], ignore_index=True)
            params = dict(cfg["classifier"])
            if c == "epitermal97":
                params.update(cfg["epithermal_classifier"])
            params["random_state"] = seed+member
            columns = component_columns(X.columns, c)
            model = Pipeline([("derived_training_statistics", FoldPathfinders()),
                ("preprocess", make_preprocessor(columns, data.config["geochemical_columns"])),
                ("model", lgb.LGBMClassifier(**params))])
            model.fit(X.loc[sample.cell_id, columns], sample.label, model__sample_weight=sample.peso_confianza)
            score = predict(model, X.loc[ids, columns], cfg["prediction_batch_size"])
            estimators[c].append(model)
            scores[c].append(score)
            rows.append(sample.assign(component=c, member=member, level=level))
            runs.append({"scope": scope, "partition": partition, "level": level, "component": c,
                "member": member, "n_P": len(target), "n_U": 3*len(target), "sample_seed": sample_seed,
                "classifier_seed": seed+member, "n_features": len(columns), "sample_hash": cell_hash(sample.cell_id)})
        if scope == "national" and level == "outer":
            log(f"Nacional: miembro {member+1}/{cfg['bags']} entrenado y puntuado en {len(ids)} celdas")
    raw = pd.DataFrame({"cell_id": ids})
    for c in COMPONENTS29:
        raw[c] = np.column_stack(scores[c]).mean(axis=1) if scores[c] else np.nan
    pd.concat(rows, ignore_index=True).to_parquet(folder / f"training_{level}.parquet", index=False)
    pd.DataFrame(runs).to_csv(folder / f"fits_{level}.csv", index=False)
    raw.to_parquet(folder / f"raw_{level}.parquet", index=False)
    log(f"{scope}/{partition}/{level}: P={len(p)}, {len(runs)} ajustes nuevos, {time.perf_counter()-started:.1f}s")
    return estimators, raw


class ProspectiveBundle:
    def __init__(self, estimators, normalizers, weights, columns):
        self.estimators, self.normalizers, self.weights = estimators, normalizers, np.asarray(weights)
        self.feature_columns = list(columns)
        self.default_method = "max3_97"

    def predict_components(self, X):
        raw, spread = {}, {}
        for c in COMPONENTS29:
            cols = component_columns(self.feature_columns, c)
            models = self.estimators[c]
            values = np.column_stack([predict(m, X[cols], 25000) for m in models]) if models else None
            raw[c] = values.mean(axis=1) if models else np.full(len(X), np.nan)
            spread[c] = values.std(axis=1) if models else np.full(len(X), np.nan)
        return pd.DataFrame(raw, index=X.index), pd.DataFrame(spread, index=X.index)

    def combine(self, raw):
        norm = pd.DataFrame({c: self.normalizers[c].transform(raw[c]) for c in COMPONENTS29}, index=raw.index)
        result = raw[list(COMPONENTS29[:3])].copy()
        result["max3_97"] = norm[FAMILY29].max(axis=1)
        result["fusion3_97"] = blend(norm[FAMILY29].to_numpy(), self.weights)
        return result, norm

    def predict(self, X):
        raw, _ = self.predict_components(X)
        return self.combine(raw)[0][self.default_method].to_numpy()


def nested29(exp, pool, expected_p, ids, seed, folder, scope, partition):
    sample, memberships, parts = exp.inner_splits(pool, seed)
    inner_frames = []
    for fold, allowed, test in parts:
        ps = exp.data.positives.loc[exp.data.positives.cell_id.isin(allowed.cell_id), "cell_id"]
        _, raw = fit29(exp.data, exp.X, exp.systems, allowed, ps, test.cell_id, exp.cfg,
            seed+1000*(fold+1), folder, scope, partition, f"inner_{fold}", exp.log)
        inner_frames.append(raw.merge(test[["cell_id", "label"]], validate="one_to_one").assign(inner_fold=fold))
    inner = pd.concat(inner_frames, ignore_index=True)
    if not inner.cell_id.is_unique or set(inner.cell_id) != set(sample.cell_id):
        raise AssertionError("OOF interno incompleto o duplicado.")
    inner.to_parquet(folder / "inner_predictions.parquet", index=False)
    pd.concat(memberships, ignore_index=True).to_parquet(folder / "inner_memberships.parquet", index=False)
    normalized = pd.DataFrame(index=inner.index, columns=COMPONENTS29, dtype=float)
    for fold in sorted(inner.inner_fold.unique()):
        target = inner.inner_fold.eq(fold)
        ref = inner.inner_fold.ne(fold) & inner.label.eq(0)
        for c in COMPONENTS29:
            normalized.loc[target, c] = BackgroundCDF().fit(inner.loc[ref, c]).transform(inner.loc[target, c])
    normalized.to_parquet(folder / "inner_normalized_predictions.parquet", index=False)
    normalizers = {c: BackgroundCDF().fit(inner.loc[inner.label.eq(0), c]) for c in COMPONENTS29}
    weights, search = choose_weights(inner.label, normalized[FAMILY29].to_numpy(), exp.cfg["weight_step"])
    search.to_csv(folder / "weight_search.csv", index=False)
    estimators, raw = fit29(exp.data, exp.X, exp.systems, pool, expected_p, ids, exp.cfg, seed,
        folder, scope, partition, "outer", exp.log)
    bundle = ProspectiveBundle(estimators, normalizers, weights, exp.X.columns)
    scores, norm = bundle.combine(raw.set_index("cell_id"))
    for c in COMPONENTS29:
        scores[f"raw_{c}"] = raw.set_index("cell_id")[c]
        scores[f"normalized_{c}"] = norm[c]
    scores.index.name = "cell_id"
    scores.reset_index().to_parquet(folder / "predictions.parquet", index=False)
    joblib.dump(bundle, folder / "model.joblib", compress=3)
    (folder / "weights.json").write_text(json.dumps(dict(zip(FAMILY29, map(float, weights))), indent=2), encoding="utf-8")
    return scores.reset_index()
