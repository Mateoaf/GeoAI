"""Paired 64/95 feature control appended to NB26; no outer-test normalization."""
from __future__ import annotations

import time
import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from .controlled_system_features import FoldPathfinders
from .controlled_system_models import BackgroundCDF
from .geochemical_experiment import cell_hash, make_preprocessor, predict, select_sample


COMPONENTS = ("global", "primario_otro", "aluvial", "epitermal")
METHODS = ("global64", "max3_64", "global95", "max3_95")


def pipeline_for(columns, chemical, parameters, extended):
    # The original matrix must not acquire the 95-variable pathfinder index.
    steps = [("pathfinders_training_only", FoldPathfinders())] if extended else []
    steps += [("preprocess", make_preprocessor(list(columns), chemical)),
              ("model", lgb.LGBMClassifier(**parameters))]
    return Pipeline(steps)


def paired_samples(data, systems, pool, cfg, seed):
    """Draw once per member, before choosing a feature matrix.

    Global samples exactly reproduce select_sample / the national mapping recipe.
    Specialists retain every eligible typed P; their U is a shared nested subset
    of the global draw. All known P, including other systems, are excluded from U.
    """
    flags = systems.set_index("cell_id")
    for member in range(cfg["bags"]):
        sample_seed = seed + 5000 + 101 * member
        full = select_sample(data, pool.cell_id, sample_seed)
        positive = full.loc[full.label.eq(1), ["cell_id", "peso_confianza", "label"]]
        background = full.loc[full.label.eq(0), ["cell_id", "peso_confianza", "label"]]
        # An independent permutation keeps every specialist subset uniform over U.
        order = np.random.default_rng(sample_seed + 700000).permutation(len(background))
        for component in COMPONENTS:
            target = positive if component == "global" else positive.loc[
                flags.loc[positive.cell_id, component].to_numpy()]
            if len(target) < cfg["minimum_specialist_P"]:
                continue
            n_u = 3 * len(target)
            if len(background) < n_u:
                raise ValueError("Fondo insuficiente para U:P=3:1 sin reemplazo.")
            if component == "global":
                sample = full[["cell_id", "peso_confianza", "label"]].copy()
            else:
                chosen = background.iloc[order[:n_u]].sort_values("cell_id")
                sample = pd.concat([target, chosen], ignore_index=True)
            if sample.cell_id.duplicated().any():
                raise AssertionError("Muestreo P/U duplicado.")
            yield component, member, sample_seed, seed + member, sample


def fit_paired(data, matrices, systems, pool, expected_p, evaluation_ids, cfg,
               seed, folder, scope, partition, level, log):
    actual = set(data.positives.loc[data.positives.cell_id.isin(pool.cell_id), "cell_id"])
    if actual != set(expected_p):
        raise AssertionError("Las P no coinciden con la partición congelada.")
    if scope != "national" and set(pool.cell_id) & set(evaluation_ids):
        raise AssertionError("Celdas evaluadas presentes en el entrenamiento.")
    estimators = {f"{c}{n}": [] for n in matrices for c in COMPONENTS}
    values = {k: np.full((len(evaluation_ids), cfg["bags"]), np.nan) for k in estimators}
    rows, runs = [], []
    started = time.perf_counter()
    for component, member, sample_seed, classifier_seed, sample in paired_samples(data, systems, pool, cfg, seed):
        rows.append(sample.assign(component=component, member=member, level=level))
        parameters = dict(cfg["classifier"], random_state=classifier_seed)
        if component == "epitermal":
            parameters.update(cfg["epithermal_classifier"])
        for n, X in matrices.items():
            key = f"{component}{n}"
            pipeline = pipeline_for(X.columns, data.config["geochemical_columns"], parameters, n == 95)
            pipeline.fit(X.loc[sample.cell_id], sample.label, model__sample_weight=sample.peso_confianza)
            values[key][:, member] = predict(pipeline, X.loc[evaluation_ids], cfg["prediction_batch_size"])
            estimators[key].append(pipeline)
            runs.append({"scope": scope, "partition": partition, "level": level, "component": component,
                "features": n, "member": member, "sample_seed": sample_seed, "classifier_seed": classifier_seed,
                "n_P": int(sample.label.sum()), "n_U": int(sample.label.eq(0).sum()),
                "sample_hash": cell_hash(sample.cell_id), "ordered_sample_hash": ordered_hash(sample.cell_id),
                "positive_hash": cell_hash(sample.loc[sample.label.eq(1), "cell_id"])})
        if scope == "national" and level == "outer" and component == COMPONENTS[-1]:
            log(f"Nacional: miembro {member + 1}/{cfg['bags']} ajustado y puntuado con 64 y 95 variables")
    raw = pd.DataFrame({"cell_id": list(evaluation_ids)})
    for key in estimators:
        raw[key] = values[key].mean(axis=1)
        raw[f"std_{key}"] = values[key].std(axis=1)
    folder.mkdir(parents=True, exist_ok=True)
    pd.concat(rows, ignore_index=True).to_parquet(folder / f"training_{level}.parquet", index=False)
    pd.DataFrame(runs).to_csv(folder / f"fits_{level}.csv", index=False)
    raw.to_parquet(folder / f"raw_{level}.parquet", index=False)
    log(f"{scope}/{partition}/{level}: {len(actual)} P, {len(runs)} ajustes reales, {time.perf_counter()-started:.1f}s")
    return estimators, raw


def ordered_hash(values):
    import hashlib
    return hashlib.sha256("\n".join(map(str, values)).encode()).hexdigest()


class BaseDecouplingBundle:
    """Two feature contracts, eight-member components and fixed training CDFs."""
    def __init__(self, estimators, normalizers, columns):
        self.estimators = estimators
        self.normalizers = normalizers
        self.columns = {n: list(v) for n, v in columns.items()}

    def raw_predictions(self, matrices, batch_size=25000):
        index = matrices[64].index
        raw = pd.DataFrame(index=index)
        for n in self.columns:
            X = matrices[n].loc[index, self.columns[n]]
            for component in COMPONENTS:
                key = f"{component}{n}"
                models = self.estimators[key]
                raw[key] = (np.column_stack([predict(m, X, batch_size) for m in models]).mean(axis=1)
                            if models else np.nan)
        return raw

    def combine(self, raw):
        result = raw.copy()
        for n in self.columns:
            keys = [f"{c}{n}" for c in COMPONENTS]
            for key in keys:
                result[f"cdf_{key}"] = self.normalizers[key].transform(raw[key])
            matrix = result[[f"cdf_{k}" for k in keys]].to_numpy()
            maximum = np.where(np.isfinite(matrix), matrix, -np.inf).max(axis=1)
            if not np.isfinite(maximum).all():
                raise AssertionError("Falta un componente global disponible.")
            result[f"max3_{n}"] = maximum
        if not np.isfinite(result[list(METHODS)].to_numpy()).all():
            raise AssertionError("Predicciones finales no finitas.")
        return result

    def predict(self, matrices, method="max3_64"):
        return self.combine(self.raw_predictions(matrices))[method].to_numpy()


def fit_nested_paired(experiment, pool, expected_p, evaluation_ids, seed, folder, scope, partition):
    master, roles, parts = experiment.inner_splits(pool, seed)
    pd.concat(roles, ignore_index=True).to_parquet(folder / "inner_memberships.parquet", index=False)
    inner = []
    for fold, allowed, test in parts:
        p = experiment.data.positives.loc[experiment.data.positives.cell_id.isin(allowed.cell_id), "cell_id"]
        _, frame = fit_paired(experiment.data, experiment.matrices, experiment.systems, allowed, p,
            test.cell_id, experiment.cfg, seed + 1000 * (fold + 1), folder, scope, partition,
            f"inner_{fold}", experiment.log)
        inner.append(frame.merge(test[["cell_id", "label"]], validate="one_to_one").assign(inner_fold=fold))
    reference = pd.concat(inner, ignore_index=True)
    if not reference.cell_id.is_unique or set(reference.cell_id) != set(master.cell_id):
        raise AssertionError("Predicciones internas OOF incompletas.")
    reference.to_parquet(folder / "inner_predictions.parquet", index=False)
    keys = [f"{c}{n}" for n in experiment.matrices for c in COMPONENTS]
    normalizers = {k: BackgroundCDF().fit(reference.loc[reference.label.eq(0), k]) for k in keys}
    estimators, raw = fit_paired(experiment.data, experiment.matrices, experiment.systems, pool,
        expected_p, evaluation_ids, experiment.cfg, seed, folder, scope, partition, "outer", experiment.log)
    bundle = BaseDecouplingBundle(estimators, normalizers, {n: X.columns for n, X in experiment.matrices.items()})
    predictions = bundle.combine(raw.set_index("cell_id")).reset_index()
    predictions.to_parquet(folder / "predictions.parquet", index=False)
    joblib.dump(bundle, folder / "model.joblib", compress=3)
    return predictions
