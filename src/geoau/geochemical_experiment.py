"""GeoAI: prospectividad regional con 64 predictores y validación espacial.

Las ocho clases geoquímicas se codifican como categorías cartográficas.
El entrenamiento P/U genera puntuaciones relativas, dispersión y novedad.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import time
import warnings

import joblib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.spatial import cKDTree
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score, brier_score_loss, precision_recall_curve, auc
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import yaml
import lightgbm as lgb


GEOCHEMICAL_COLUMNS = [f"{element}_clase_modal" for element in
                       ("as", "sb", "bi", "hg", "cu", "pb", "zn", "w")]
FORBIDDEN_COLUMNS = {"cell_id", "record_id", "deposit_id", "district_id", "row", "col",
                     "x_center", "y_center", "block_id", "land_area_m2", "peso_confianza"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def cell_hash(values) -> str:
    return hashlib.sha256("\n".join(sorted(map(str, values))).encode()).hexdigest()


@dataclass
class ExperimentData:
    root: Path
    config: dict
    output: Path
    report: Path
    grid: pd.DataFrame
    features: pd.DataFrame
    records: pd.DataFrame
    positives: pd.DataFrame
    numeric_columns: list[str]
    feature_columns: list[str]
    grid_spec: dict
    inputs: dict


def consolidate_positives(records: pd.DataFrame, pending_weight: float = 0.5) -> pd.DataFrame:
    """Una celda, una etiqueta; la evidencia confirmada tiene prioridad."""
    accepted = records.loc[records.estado_presencia.isin(["confirmada", "pendiente"])].copy()
    accepted["peso_confianza"] = np.where(accepted.estado_presencia.eq("confirmada"), 1., pending_weight)
    return (accepted.groupby("cell_id", sort=True, as_index=False)
            .agg(peso_confianza=("peso_confianza", "max"), n_records=("record_id", "nunique")))


def load_data(root: Path, config_path: Path | None = None) -> ExperimentData:
    root = Path(root).resolve()
    config_path = config_path or root / "config/geoquimica_20261017.yaml"
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    d, c = root / cfg["phase_d_run"], root / cfg["phase_c_run"]
    audit_path = root / "data/review/auditoria_predictores_fase_d.csv"
    review_path = root / "data/review/revision_au_fase_b.csv"
    audit = pd.read_csv(audit_path)
    numeric = audit.loc[audit.decision.eq("approved") & audit.familia.ne("Geoquímica"), "name"].tolist()
    chemical = list(cfg["geochemical_columns"])
    columns = numeric + chemical
    if len(numeric) != 56 or len(columns) != 64 or len(set(columns)) != 64:
        raise ValueError("El contrato requiere 56 variables numéricas y ocho geoquímicas.")
    if FORBIDDEN_COLUMNS.intersection(columns) or set(chemical) != set(GEOCHEMICAL_COLUMNS):
        raise ValueError("El contrato incluye columnas auxiliares o elementos inesperados.")
    grid_path, x_path = d / "calidad_y_soporte.parquet", d / "X_features.parquet"
    schema = pq.ParquetFile(grid_path).schema.names
    eligibility = next((name for name in ["eligible_approved_features", "eligible_geology_terrain"]
                        if name in schema), None)
    if eligibility is None:
        raise ValueError("Falta una máscara de geología y relieve independiente de geoquímica.")
    grid = pd.read_parquet(grid_path, columns=["cell_id", eligibility, "x_center", "y_center",
                                             "row", "col", "land_area_m2"])
    grid = grid.loc[grid[eligibility]].drop(columns=eligibility).sort_values("cell_id").reset_index(drop=True)
    if not grid.cell_id.is_unique:
        raise ValueError("La malla contiene cell_id repetidos.")
    grid["block_id"] = ((grid.x_center // cfg["block_size_m"]).astype(int).astype(str)
                        + "_" + (grid.y_center // cfg["block_size_m"]).astype(int).astype(str))
    columns = numeric + chemical
    features = pd.read_parquet(x_path, columns=["cell_id"] + columns).set_index("cell_id")
    if not features.index.is_unique or not set(grid.cell_id) <= set(features.index):
        raise ValueError("La matriz y la malla no tienen una correspondencia única y completa.")
    features = features.loc[grid.cell_id].replace([np.inf, -np.inf], np.nan).astype("float32")
    for name in GEOCHEMICAL_COLUMNS:
        values = features[name].dropna().to_numpy()
        if not (np.equal(values, np.floor(values)).all() and ((values >= 0) & (values <= 7)).all()):
            raise ValueError(f"Clases inesperadas en {name}; revisar su leyenda.")
    coverage_path = c / "indicios_celda_cobertura.csv"
    coverage = pd.read_csv(coverage_path, usecols=["record_id", "cell_id"])
    review = pd.read_csv(review_path)
    records = review.merge(coverage, on="record_id", how="left", validate="one_to_one")
    records = records.loc[records.estado_presencia.isin(["confirmada", "pendiente"])
                          & records.cell_id.isin(grid.cell_id)].copy()
    positives = consolidate_positives(records, cfg["pending_weight"])
    output, report = root / cfg["output_directory"], root / cfg["report_directory"]
    for folder in [output, report, output / "partitions", output / "models", output / "maps", report / "figuras"]:
        folder.mkdir(parents=True, exist_ok=True)
    input_paths = [config_path, audit_path, review_path, grid_path, x_path, coverage_path,
                   root / "data/review/seleccion_reserva_distritos.csv",
                   d / "dictionaries/geoquimica_leyendas_locales.csv"]
    groups_path = root / "reports/validacion_rotativa_distritos_20261008/resumen_por_rotacion.csv"
    if groups_path.is_file():
        input_paths.append(groups_path)
    inputs = {path.relative_to(root).as_posix(): sha256(path) for path in input_paths}
    inputs["eligibility_column"] = eligibility
    return ExperimentData(root, cfg, output, report, grid, features, records, positives,
                          numeric, columns, json.loads((d / "grid_spec.json").read_text(encoding="utf-8")), inputs)


def audit_inputs(data: ExperimentData) -> None:
    audit = pd.read_csv(data.root / "data/review/auditoria_predictores_fase_d.csv").set_index("name")
    selection = [{"variable": name, "family": audit.loc[name, "familia"],
                  "representation": "categorical_atlas_class" if name in GEOCHEMICAL_COLUMNS else "numeric",
                  "included_in_model": True, "is_analytical_concentration": False,
                  **{field: audit.loc[name, field] for field in ["significado_geologico", "fuente", "metodo_calculo",
                                                              "unidades", "tratamiento_nodata", "riesgo_leakage_circularidad"]}}
                 for name in data.feature_columns]
    pd.DataFrame(selection).to_csv(data.output / "variables_incluidas.csv", index=False)
    coverage = []
    for name in GEOCHEMICAL_COLUMNS:
        values = data.features[name]
        coverage.append({"variable": name, "n_cells": len(values), "missing_cells": int(values.isna().sum()),
                         "missing_fraction": float(values.isna().mean()),
                         "positive_missing_cells": int(values.loc[data.positives.cell_id].isna().sum()),
                         "classes": ";".join(str(int(value)) for value in sorted(values.dropna().unique()))})
    pd.DataFrame(coverage).to_csv(data.output / "cobertura_geoquimica.csv", index=False)
    legends = pd.read_csv(data.root / data.config["phase_d_run"] / "dictionaries/geoquimica_leyendas_locales.csv")
    legends = legends.loc[legends.element.str.lower().isin([name.split("_")[0] for name in GEOCHEMICAL_COLUMNS])]
    legends.to_csv(data.output / "leyendas_geoquimicas.csv", index=False)
    data.positives.to_csv(data.output / "celdas_positivas.csv", index=False)
    data.records.to_csv(data.output / "registros_elegibles.csv", index=False)
    data.grid.to_parquet(data.output / "dominio_comun.parquet", index=False)
    write_json(data.output / "input_manifest.json", data.inputs)
    write_json(data.output / "config_snapshot.json", data.config)
    write_json(data.output / "dataset_summary.json", {
        "n_cells": len(data.grid), "n_records": len(data.records), "n_positive_cells": len(data.positives),
        "n_deposits": int(data.records.deposit_id.nunique()), "n_districts": int(data.records.district_id.nunique()),
        "n_input_features": len(data.feature_columns), "n_numeric_features": len(data.numeric_columns),
        "n_geochemical_features": len(GEOCHEMICAL_COLUMNS),
        "geochemical_representation": "clases_categoricas_no_ppm",
    })


def make_preprocessor(columns, chemical):
    numeric = [name for name in columns if name not in chemical]
    transformers = [("numeric", Pipeline([
        ("impute", SimpleImputer(strategy="median", keep_empty_features=True, add_indicator=True)),
        ("scale", StandardScaler()),
    ]), numeric)]
    if chemical:
        transformers.append(("geochemical", Pipeline([
            ("impute", SimpleImputer(strategy="constant", fill_value=-1, keep_empty_features=True)),
            ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False, dtype=np.float32)),
        ]), list(chemical)))
    return ColumnTransformer(transformers, remainder="drop", sparse_threshold=0.)


class WeightedPUBaggingClassifier(ClassifierMixin, BaseEstimator):
    """Remuestreo de U con pesos de P; scores P/U sin calibración absoluta."""
    def __init__(self, n_bags=5, u_per_p=2, n_jobs=4, random_state=42):
        self.n_bags = n_bags
        self.u_per_p = u_per_p
        self.n_jobs = n_jobs
        self.random_state = random_state

    def fit(self, X, y, sample_weight=None):
        y = np.asarray(y)
        p, u = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
        if not len(p) or not len(u):
            raise ValueError("El ensamble PU necesita ambas etiquetas P/U.")
        weight = np.ones(len(y)) if sample_weight is None else np.asarray(sample_weight)
        self.estimators_, self.sample_indices_ = [], []
        for member in range(self.n_bags):
            rng = np.random.default_rng(self.random_state + member * 101)
            subset = np.concatenate([p, rng.choice(u, min(len(u), len(p) * self.u_per_p), replace=False)])
            model = lgb.LGBMClassifier(n_estimators=100, max_depth=5, num_leaves=24,
                                      learning_rate=.04, reg_alpha=.4, reg_lambda=1.,
                                      verbosity=-1, n_jobs=self.n_jobs, random_state=self.random_state + member)
            model.fit(X[subset], y[subset], sample_weight=weight[subset])
            self.estimators_.append(model)
            self.sample_indices_.append(subset)
        self.classes_ = np.array([0, 1])
        self.n_features_in_ = X.shape[1]
        return self

    def predict_proba(self, X):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="X does not have valid feature names")
            score = np.mean([model.predict_proba(X)[:, 1] for model in self.estimators_], axis=0)
        return np.column_stack([1 - score, score])


def make_model(columns, chemical, family, cfg, seed):
    if family == "logistic":
        classifier = LogisticRegression(C=.1, max_iter=2000, random_state=seed)
    elif family == "random_forest":
        classifier = RandomForestClassifier(n_estimators=cfg["random_forest_trees"], max_depth=12,
                                            min_samples_leaf=4, n_jobs=cfg["n_jobs"], random_state=seed)
    elif family == "lightgbm":
        classifier = lgb.LGBMClassifier(n_estimators=cfg["lightgbm_trees"], max_depth=5, num_leaves=24,
                                        learning_rate=.04, reg_alpha=.5, reg_lambda=1.,
                                        min_child_samples=10, verbosity=-1, n_jobs=cfg["n_jobs"], random_state=seed)
    elif family == "bagging_pu":
        classifier = WeightedPUBaggingClassifier(cfg["pu_bags"], cfg["pu_u_per_p"], cfg["n_jobs"], seed)
    else:
        raise ValueError(f"Modelo desconocido: {family}")
    return Pipeline([("preprocess", make_preprocessor(columns, chemical)), ("model", classifier)])


def predict(model, X, batch_size=25000):
    scores = []
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="X does not have valid feature names")
        for start in range(0, len(X), batch_size):
            scores.append(model.predict_proba(X.iloc[start:start + batch_size])[:, 1])
    result = np.concatenate(scores)
    if not np.isfinite(result).all():
        raise ValueError("Predicciones no finitas.")
    return result


def select_sample(data: ExperimentData, pool_ids, seed):
    pool_ids = set(pool_ids)
    pos = data.positives.loc[data.positives.cell_id.isin(pool_ids)].sort_values("cell_id")
    background = np.array(sorted(pool_ids - set(pos.cell_id)))
    if pos.empty or not len(background):
        raise ValueError("Pool sin suficientes P/U.")
    rng = np.random.default_rng(seed)
    u = np.sort(rng.choice(background, min(len(background), len(pos) * data.config["u_per_p"]), replace=False))
    sample = pd.concat([pos[["cell_id", "peso_confianza"]].assign(label=1),
                        pd.DataFrame({"cell_id": u, "peso_confianza": 1., "label": 0})], ignore_index=True)
    return sample.merge(data.grid[["cell_id", "block_id", "x_center", "y_center"]],
                        on="cell_id", validate="one_to_one", sort=False)


def spatial_splits(sample, n_splits=5, buffer_m=15000, seed=42):
    blocks = np.array(sorted(sample.block_id.unique()))
    np.random.default_rng(seed).shuffle(blocks)
    if len(blocks) < n_splits:
        raise ValueError("No hay suficientes bloques para los pliegues solicitados.")
    fold_of = {block: i % n_splits for i, block in enumerate(blocks)}
    folds = sample.block_id.map(fold_of).to_numpy()
    coords = sample[["x_center", "y_center"]].to_numpy()
    result = []
    for fold in range(n_splits):
        test = np.flatnonzero(folds == fold)
        candidates = np.flatnonzero(folds != fold)
        distance = cKDTree(coords[test]).query(coords[candidates], k=1)[0]
        train = candidates[distance >= buffer_m]
        excluded = candidates[distance < buffer_m]
        if set(sample.iloc[train].block_id) & set(sample.iloc[test].block_id):
            raise AssertionError("Un bloque aparece en ambos lados.")
        if len(np.unique(sample.iloc[train].label)) < 2 or len(np.unique(sample.iloc[test].label)) < 2:
            raise ValueError(f"El pliegue {fold} no contiene ambas etiquetas.")
        result.append((train, test, excluded))
    return result


def label_metrics(y, scores, ids):
    y, scores = np.asarray(y), np.asarray(scores)
    ordered = np.lexsort((np.asarray(ids, dtype=str), -scores))
    precision, recall, _ = precision_recall_curve(y, scores)
    result = {"roc_auc": float(roc_auc_score(y, scores)),
              "average_precision": float(average_precision_score(y, scores)),
              "pr_auc_trapezoid": float(auc(recall, precision)),
              "brier_loss": float(brier_score_loss(y, scores))}
    for pct in [1, 5, 10]:
        keep = ordered[:max(1, math.ceil(len(y) * pct / 100))]
        result[f"positive_cell_recovery_at_{pct:02d}"] = float(y[keep].sum() / y.sum())
    return result


def run_benchmark(data: ExperimentData):
    cfg = data.config
    reserve = pd.read_csv(data.root / "data/review/seleccion_reserva_distritos.csv")
    reserve_cells = data.records.loc[data.records.district_id.isin(reserve.district_id), "cell_id"]
    reserve_blocks = set(data.grid.loc[data.grid.cell_id.isin(reserve_cells), "block_id"])
    pool = data.grid.loc[~data.grid.block_id.isin(reserve_blocks), "cell_id"]
    sample = select_sample(data, pool, cfg["seed"])
    splits = spatial_splits(sample, cfg["cv_folds"], cfg["cv_buffer_m"], cfg["seed"])
    sample.to_parquet(data.output / "partitions/benchmark_sample.parquet", index=False)
    memberships = []
    for fold, (train, test, excluded) in enumerate(splits):
        for role, indices in [("train", train), ("validation", test), ("buffer_excluded", excluded)]:
            memberships.append(pd.DataFrame({"cell_id": sample.iloc[indices].cell_id, "fold": fold, "role": role}))
    pd.concat(memberships).to_parquet(data.output / "partitions/benchmark_memberships.parquet", index=False)
    write_json(data.output / "partitions/benchmark_design.json", {
        "reserved_blocks_excluded": sorted(reserve_blocks), "sample_hash": cell_hash(sample.cell_id),
        "n_P": int(sample.label.sum()), "n_U": int((sample.label == 0).sum()),
        "cv_buffer_m": cfg["cv_buffer_m"], "block_size_m": cfg["block_size_m"],
    })
    fold_rows, summaries, predictions = [], [], []
    columns = data.feature_columns
    chemical = cfg["geochemical_columns"]
    X = data.features.loc[sample.cell_id, columns]
    for family in cfg["benchmark_models"]:
        scores = np.full(len(sample), np.nan)
        elapsed = 0.
        for fold, (train, test, excluded) in enumerate(splits):
            model = make_model(columns, chemical, family, cfg, cfg["seed"] + fold)
            started = time.perf_counter()
            model.fit(X.iloc[train], sample.iloc[train].label,
                      model__sample_weight=sample.iloc[train].peso_confianza)
            seconds = time.perf_counter() - started
            elapsed += seconds
            fold_score = predict(model, X.iloc[test], cfg["prediction_batch_size"])
            scores[test] = fold_score
            fold_rows.append({"model": family, "fold": fold,
                              "n_input_features": len(columns), "train_cells": len(train),
                              "validation_cells": len(test), "buffer_excluded": len(excluded),
                              "training_ids_sha256": cell_hash(sample.iloc[train].cell_id),
                              "validation_ids_sha256": cell_hash(sample.iloc[test].cell_id),
                              "fit_seconds": seconds, **label_metrics(sample.iloc[test].label, fold_score, sample.iloc[test].cell_id)})
            print(f"CV {family:14s} fold={fold} AUC={fold_rows[-1]['roc_auc']:.4f}", flush=True)
        if not np.isfinite(scores).all():
            raise AssertionError("No se han evaluado todas las muestras fuera de pliegue.")
        summaries.append({"model": family, "n_input_features": len(columns),
                          "sample_hash": cell_hash(sample.cell_id), "fit_seconds": elapsed,
                          **label_metrics(sample.label, scores, sample.cell_id)})
        predictions.append(sample[["cell_id", "label"]].assign(model=family, score=scores))
        pd.DataFrame(fold_rows).to_csv(data.output / "benchmark_folds.csv", index=False)
        pd.DataFrame(summaries).to_csv(data.output / "benchmark_summary.csv", index=False)
    pd.concat(predictions).to_parquet(data.output / "benchmark_oof_predictions.parquet", index=False)
    return pd.DataFrame(summaries)


def district_groups(data: ExperimentData):
    source = data.root / "reports/validacion_rotativa_distritos_20261008/resumen_por_rotacion.csv"
    districts = set(data.records.district_id.dropna())
    if source.is_file():
        mapping = {district: int(row.grupo) for row in pd.read_csv(source).itertuples()
                   for district in row.distritos.split(";")}
        if not districts <= set(mapping):
            raise ValueError("Los grupos de evaluación no cubren todos los distritos.")
    else:
        counts = (data.records.dropna(subset=["district_id"]).groupby("district_id")
                  .deposit_id.nunique().sort_index())
        order = counts.sample(frac=1., random_state=data.config["seed"]).sort_values(ascending=False, kind="stable")
        loads, mapping = np.zeros(7), {}
        for district, count in order.items():
            group = int(loads.argmin())
            mapping[district] = group
            loads[group] += max(1, count)
    result = pd.DataFrame([{"district_id": district, "group": mapping[district]} for district in sorted(districts)])
    result.to_csv(data.output / "partitions/district_groups.csv", index=False)
    return result


def rotation_pools(data: ExperimentData, districts):
    held_cells = data.records.loc[data.records.district_id.isin(districts), "cell_id"]
    blocks = set(data.grid.loc[data.grid.cell_id.isin(held_cells), "block_id"])
    held = data.grid.loc[data.grid.block_id.isin(blocks)].copy()
    train = data.grid.loc[~data.grid.block_id.isin(blocks)].copy()
    if data.config["rotation_buffer_m"]:
        distance = cKDTree(held[["x_center", "y_center"]]).query(train[["x_center", "y_center"]], k=1)[0]
        train = train.loc[distance >= data.config["rotation_buffer_m"]]
    return train, held


def ranked_cells(ids, scores):
    """Orden estable, independiente de las etiquetas; presupuesto en celdas."""
    order = np.lexsort((np.asarray(ids, dtype=str), -np.asarray(scores)))
    rank = np.empty(len(order), dtype=int)
    rank[order] = np.arange(1, len(order) + 1)
    return rank


def run_rotations(data: ExperimentData):
    cfg, groups = data.config, district_groups(data)
    rows, details = [], []
    for group, membership in groups.groupby("group", sort=True):
        districts = set(membership.district_id)
        train, held = rotation_pools(data, districts)
        sample = select_sample(data, train.cell_id, cfg["seed"] + 1000 + int(group))
        if set(sample.cell_id) & set(held.cell_id):
            raise AssertionError("Fuga de celdas reservadas en entrenamiento.")
        relations = (data.records.loc[data.records.district_id.isin(districts)]
                     .dropna(subset=["deposit_id"])[["cell_id", "deposit_id", "district_id"]].drop_duplicates())
        sample.to_parquet(data.output / f"partitions/rotation_{group}_sample.parquet", index=False)
        held[["cell_id", "block_id"]].to_parquet(data.output / f"partitions/rotation_{group}_held.parquet", index=False)
        columns = data.feature_columns
        for family in cfg["rotation_models"]:
            model = make_model(columns, cfg["geochemical_columns"], family, cfg, cfg["seed"] + int(group))
            started = time.perf_counter()
            model.fit(data.features.loc[sample.cell_id, columns], sample.label,
                      model__sample_weight=sample.peso_confianza)
            scores = predict(model, data.features.loc[held.cell_id, columns], cfg["prediction_batch_size"])
            rank = ranked_cells(held.cell_id, scores)
            prediction = pd.DataFrame({"cell_id": held.cell_id, "score": scores, "rank": rank})
            joined = relations.merge(prediction, on="cell_id", validate="many_to_one")
            if joined.empty or joined['rank'].isna().any():
                raise ValueError("Depósitos reservados sin predicción.")
            result = {"model": family, "group": int(group),
                      "n_deposits": int(joined.deposit_id.nunique()), "n_held_cells": len(held),
                      "n_training_P": int(sample.label.sum()), "n_training_U": int((sample.label == 0).sum()),
                      "training_ids_sha256": cell_hash(sample.cell_id), "held_ids_sha256": cell_hash(held.cell_id),
                      "fit_predict_seconds": time.perf_counter() - started}
            for pct in [1, 5, 10]:
                column = f"captured_at_{pct:02d}"
                joined[column] = joined['rank'] <= math.ceil(len(held) * pct / 100)
                count = joined.loc[joined[column], "deposit_id"].nunique()
                result[f"captured_deposits_at_{pct:02d}"] = int(count)
                result[f"deposit_recovery_at_{pct:02d}"] = float(count / result["n_deposits"])
            details.append(joined.assign(model=family, group=int(group)))
            rows.append(result)
            print(f"ROT {group} {family:14s} dep@10={result['captured_deposits_at_10']}/{result['n_deposits']}", flush=True)
            pd.DataFrame(rows).to_csv(data.output / "rotation_metrics.csv", index=False)
    detail = pd.concat(details, ignore_index=True)
    detail.to_csv(data.output / "rotation_deposit_predictions.csv", index=False)
    summaries = []
    for family, frame in detail.groupby("model", sort=False):
        n = frame.deposit_id.nunique()
        result = {"model": family, "n_deposits": int(n)}
        for pct in [1, 5, 10]:
            count = frame.loc[frame[f"captured_at_{pct:02d}"], "deposit_id"].nunique()
            result[f"captured_deposits_at_{pct:02d}"] = int(count)
            result[f"deposit_recovery_at_{pct:02d}"] = float(count / n)
        summaries.append(result)
    summary = pd.DataFrame(summaries)
    summary.to_csv(data.output / "rotation_summary.csv", index=False)
    return summary


def write_raster(data: ExperimentData, name, values, dtype="float32", nodata=-9999):
    import rasterio
    from rasterio.transform import from_origin
    spec = data.grid_spec
    raster = np.full((spec["height"], spec["width"]), nodata, dtype=dtype)
    raster[data.grid.row.to_numpy(), data.grid.col.to_numpy()] = values
    path = data.output / "maps" / f"{name}.tif"
    with rasterio.open(path, "w", driver="GTiff", height=spec["height"], width=spec["width"], count=1,
                       dtype=dtype, crs=spec["crs"], nodata=nodata,
                       transform=from_origin(spec["origin_x"], spec["origin_y"], 1000, 1000),
                       compress="deflate", tiled=True, blockxsize=256, blockysize=256) as dst:
        dst.write(raster, 1)
        dst.update_tags(experiment="geoquimica_20261017", interpretation="relative_PU_score_not_absolute_probability")
    return path


def run_maps(data: ExperimentData):
    cfg, n = data.config, len(data.grid)
    batch = cfg["prediction_batch_size"]
    rows = []
    chemical = cfg["geochemical_columns"]
    columns = data.feature_columns
    folder = data.output / "models" / "GeoAI"
    folder.mkdir(parents=True, exist_ok=True)
    sums, squares = np.zeros(n), np.zeros(n)
    novelty = np.empty(n, dtype=np.float32)
    for member in range(cfg["national_bags"]):
        sample = select_sample(data, data.grid.cell_id, cfg["seed"] + 5000 + member * 101)
        model = make_model(columns, cfg["geochemical_columns"], "lightgbm", cfg, cfg["seed"] + member)
        model.fit(data.features.loc[sample.cell_id, columns], sample.label,
                  model__sample_weight=sample.peso_confianza)
        score = predict(model, data.features[columns], batch)
        sums += score
        squares += score ** 2
        joblib.dump(model, folder / f"member_{member:02d}.joblib", compress=3)
        if member == 0:
            pre = model.named_steps["preprocess"]
            centroid = pre.transform(data.features.loc[data.positives.cell_id, columns]).mean(axis=0)
            for start in range(0, n, batch):
                transformed = pre.transform(data.features[columns].iloc[start:start + batch])
                novelty[start:start + batch] = np.linalg.norm(transformed - centroid, axis=1)
            write_json(folder / "metadata.json", {"input_features": columns,
                "categorical_geochemical_features": cfg["geochemical_columns"],
                "n_input_features": len(columns), "n_encoded_features": len(pre.get_feature_names_out()),
                "n_members": cfg["national_bags"], "pending_weight": cfg["pending_weight"],
                "score_interpretation": "relative_PU_score", "absolute_probability": False,
                "novelty": "Euclidean distance to P centroid; numerical z + categorical one-hot; preprocessing of member 0 fitted on its training sample",
                "training_scope": "full_eligible_domain_after_cross_validation; not_an_independent_test"})
        print(f"MAP GeoAI miembro={member + 1}/{cfg['national_bags']}", flush=True)
    mean = sums / cfg["national_bags"]
    std = np.sqrt(np.maximum(0., squares / cfg["national_bags"] - mean ** 2))
    novelty_high = novelty > np.percentile(novelty, 95)
    high_score, high_std = mean >= np.percentile(mean, 90), std >= np.percentile(std, 75)
    categories = np.select([novelty_high, high_score & ~high_std, high_score & high_std,
                            ~high_score & ~high_std], [1, 2, 3, 4], default=5).astype("uint8")
    result = data.grid.copy()
    result["favorability_mean"] = mean.astype("float32")
    result["ensemble_std"] = std.astype("float32")
    result["novelty_distance"] = novelty
    result["novelty_high"] = novelty_high
    result["category"] = categories
    result["score_percentile"] = pd.Series(mean).rank(method="average", pct=True).to_numpy().astype("float32")
    result["missing_geochemical_features"] = data.features[chemical].isna().sum(axis=1).to_numpy() if chemical else 0
    result.to_parquet(data.output / "maps" / "GeoAI_national.parquet", index=False, compression="zstd")
    for suffix, values in [("score", mean), ("std", std), ("novelty", novelty)]:
        write_raster(data, f"GeoAI_{suffix}", values)
    write_raster(data, "GeoAI_category", categories, "uint8", 0)
    for category, count in pd.Series(categories).value_counts().items():
        rows.append({"category": int(category), "cells": int(count), "fraction": float(count / n)})
    pd.DataFrame(rows).to_csv(data.output / "map_category_counts.csv", index=False)


def frame_markdown(frame, digits=4):
    formatted = frame.copy()
    for column in formatted.select_dtypes(include="number"):
        formatted[column] = formatted[column].map(lambda value: f"{value:.{digits}f}" if isinstance(value, (float, np.floating)) else str(value))
    return "| " + " | ".join(formatted.columns) + " |\n| " + " | ".join(["---"] * len(formatted.columns)) + " |\n" + "\n".join("| " + " | ".join(map(str, row)) + " |" for row in formatted.itertuples(index=False, name=None))


def create_figures(data: ExperimentData):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    benchmark = pd.read_csv(data.output / "benchmark_summary.csv")
    rotations = pd.read_csv(data.output / "rotation_summary.csv")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for axis, frame, column, title in [(axes[0], benchmark, "roc_auc", "CV espacial: ROC-AUC P/U"),
                                      (axes[1], rotations, "deposit_recovery_at_10", "Depósitos recuperados al 10 % de celdas")]:
        axis.bar(frame.model, frame[column], color="#247b91")
        axis.set_title(title)
        axis.set_ylim(0, 1)
        axis.tick_params(axis="x", rotation=15)
        axis.grid(axis="y", alpha=.2)
    fig.suptitle("GeoAI · 64 predictores con geoquímica")
    fig.tight_layout()
    fig.savefig(data.report / "figuras/resultados_modelos.png", dpi=150)
    plt.close(fig)
    frame = pd.read_parquet(data.output / "maps/GeoAI_national.parquet")
    spec = data.grid_spec
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    for axis, column, title in zip(axes, ["favorability_mean", "ensemble_std", "novelty_distance"],
                                   ["Favorabilidad P/U", "Dispersión del ensamble", "Novedad del perfil de variables"]):
        raster = np.full((spec["height"], spec["width"]), np.nan)
        raster[frame.row.to_numpy(), frame.col.to_numpy()] = frame[column]
        im = axis.imshow(raster, cmap="viridis")
        axis.set_title(title)
        axis.set_axis_off()
        fig.colorbar(im, ax=axis, shrink=.65)
    fig.tight_layout()
    fig.savefig(data.report / "figuras/mapa_geoquimica.png", dpi=150)
    plt.close(fig)
    coverage = pd.read_csv(data.output / "cobertura_geoquimica.csv")
    fig, axis = plt.subplots(figsize=(10, 4))
    axis.bar(coverage.variable.str.split("_").str[0].str.upper(), 100 * (1 - coverage.missing_fraction), color="#247b91")
    axis.set(ylim=(0, 105), ylabel="Celdas con dato (%)", title="Cobertura de las ocho variables geoquímicas")
    fig.tight_layout()
    fig.savefig(data.report / "figuras/cobertura_geoquimica.png", dpi=150)
    plt.close(fig)


def summarize_feature_importance(data: ExperimentData):
    """Agrega la ganancia de los árboles por variable de entrada, incluido one-hot."""
    rows = []
    for member in range(data.config["national_bags"]):
        model = joblib.load(data.output / "models/GeoAI" / f"member_{member:02d}.joblib")
        names = model.named_steps["preprocess"].get_feature_names_out()
        gains = model.named_steps["model"].booster_.feature_importance(importance_type="gain")
        totals = dict.fromkeys(data.feature_columns, 0.)
        for encoded, gain in zip(names, gains):
            name = encoded.split("__", 1)[1].removeprefix("missingindicator_")
            original = next((column for column in data.feature_columns
                             if name == column or (column in GEOCHEMICAL_COLUMNS and name.startswith(column + "_"))), None)
            if original is None:
                raise ValueError(f"Columna transformada sin correspondencia: {encoded}")
            totals[original] += float(gain)
        denominator = sum(totals.values())
        rows.extend({"member": member, "variable": column, "gain_fraction": gain / denominator}
                    for column, gain in totals.items())
    summary = (pd.DataFrame(rows).groupby("variable", as_index=False)
               .agg(mean_gain_fraction=("gain_fraction", "mean"), std_gain_fraction=("gain_fraction", "std")))
    summary["geochemical"] = summary.variable.isin(GEOCHEMICAL_COLUMNS)
    summary = summary.sort_values("mean_gain_fraction", ascending=False)
    summary.to_csv(data.output / "importancia_variables.csv", index=False)
    chemistry = summary.loc[summary.geochemical]
    chemistry.to_csv(data.output / "importancia_geoquimica.csv", index=False)
    return chemistry


def generate_report(data: ExperimentData):
    benchmark = pd.read_csv(data.output / "benchmark_summary.csv")
    rotations = pd.read_csv(data.output / "rotation_summary.csv")
    coverage = pd.read_csv(data.output / "cobertura_geoquimica.csv")
    importance = summarize_feature_importance(data)
    ds = json.loads((data.output / "dataset_summary.json").read_text(encoding="utf-8"))
    coverage["coverage_percent"] = (1 - coverage.missing_fraction) * 100
    coverage["missing_percent"] = coverage.missing_fraction * 100
    tables = data.report / "tablas"
    tables.mkdir(parents=True, exist_ok=True)
    for filename in ["benchmark_summary.csv", "benchmark_folds.csv", "rotation_summary.csv", "rotation_metrics.csv",
                     "cobertura_geoquimica.csv", "leyendas_geoquimicas.csv", "variables_incluidas.csv", "map_category_counts.csv",
                     "importancia_variables.csv", "importancia_geoquimica.csv"]:
        (tables / filename).write_bytes((data.output / filename).read_bytes())
    folder = data.output / "models/GeoAI"
    metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    first_member = joblib.load(folder / "member_00.joblib")
    metadata["member_classifier_parameters"] = first_member.named_steps["model"].get_params()
    metadata["u_per_p_each_member"] = data.config["u_per_p"]
    write_json(folder / "metadata.json", metadata)
    create_figures(data)
    bagging = benchmark.loc[benchmark.model.eq("bagging_pu")].iloc[0]
    rotation = rotations.loc[rotations.model.eq("bagging_pu")].iloc[0]
    headline = (f"Bagging PU obtiene ROC-AUC {bagging.roc_auc:.4f} y Average Precision {bagging.average_precision:.4f} "
                f"en predicciones fuera de pliegue. En siete rotaciones territoriales recupera "
                f"{int(rotation.captured_deposits_at_05)} de {int(rotation.n_deposits)} depósitos al 5 % de celdas "
                f"y {int(rotation.captured_deposits_at_10)} al 10 %.")
    text = f"""# GeoAI · Prospectividad aurífera con geoquímica

El sistema integra 64 predictores en una malla de un kilómetro EPSG:25830. El dominio contiene {ds['n_cells']:,} celdas; {ds['n_records']} registros elegibles se consolidan en {ds['n_positive_cells']} celdas P. La evaluación territorial abarca {ds['n_deposits']} depósitos agrupados en {ds['n_districts']} distritos.

{headline}

## Datos y variables predictivas

Los 64 predictores describen 19 fracciones litológicas, 27 fracciones de edades, tres distancias estructurales, seis variables de relieve, una hidrológica y ocho variables geoquímicas. Los identificadores, coordenadas, bloques, depósitos y estados de revisión organizan el trabajo y no son predictores. El inventario contiene 790 registros: 190 confirmados, 597 pendientes y tres rechazados. Tras el cruce con el dominio se utilizan 175 confirmados y 578 pendientes. La unidad de aprendizaje es la celda: se prioriza el peso de la evidencia confirmada cuando coinciden registros.

## Geoquímica: fuentes, variables y significado

Se incorporan As (arsénico), Sb (antimonio), Bi (bismuto), Hg (mercurio), Cu (cobre), Pb (plomo), Zn (zinc) y W (wolframio). Estas capas aportan información sobre la distribución superficial de asociaciones geoquímicas potencialmente relacionadas con los sistemas mineralizantes. La relación depende del contexto geológico: un elemento acompañante no constituye por sí solo una prueba de oro.

Las fuentes son capas cartográficas del atlas geoquímico, integradas mediante su clasificación de colores y agregadas como clase modal de cada celda. El catálogo de cada clase, color RGB e intervalo local está en leyendas_geoquimicas.csv. Esos intervalos conservan la transcripción de las leyendas locales; su medio de muestreo, extracción y unidades requieren contraste con la ficha oficial de cada capa. El modelo utiliza códigos categóricos, sin convertirlos en concentraciones analíticas verificadas ni asumir que la distancia entre códigos es una distancia química.

{frame_markdown(coverage[['variable', 'coverage_percent', 'missing_percent', 'positive_missing_cells', 'classes']])}

La clase cero es válida. Los ausentes se imputan como categoría -1 y se codifican mediante one-hot; las categorías se aprenden exclusivamente dentro del entrenamiento de cada partición. Una categoría no observada se gestiona con handle_unknown=ignore. Las variables numéricas se imputan con la mediana del entrenamiento, añaden indicadores de ausencia cuando procede y se estandarizan. El número de columnas transformadas depende de las categorías presentes en entrenamiento; 64 es el número de variables de entrada.

Zn y W presentan la menor cobertura. Se conserva su ausencia de forma explícita y se exporta un contador de elementos ausentes por celda. El dominio se define por el soporte geológico y de relieve; no se descartan celdas por carecer de algún elemento. La falta de cobertura puede aportar señal del muestreo y exige interpretación contextual. Au queda fuera de los predictores para reducir el riesgo de circularidad con el inventario que define la señal objetivo.

![Cobertura geoquímica](figuras/cobertura_geoquimica.png)

## Uso de los elementos dentro del ensamble

La tabla agrega por variable original la ganancia de las divisiones de los árboles, reuniendo sus categorías one-hot. En cada miembro se normaliza por la ganancia total y después se calcula la media y la desviación entre los ocho miembros. Describe el uso de las variables durante el ajuste; no mide causalidad, contribución individual a cada celda ni una mejora predictiva atribuible al elemento. La correlación, la cantidad de categorías y el patrón de ausencias pueden influir en estos valores.

{frame_markdown(importance[['variable', 'mean_gain_fraction', 'std_gain_fraction']])}

Las 64 variables se documentan en importancia_variables.csv. Esta inspección global se completa con la consulta de las clases y las capas de cada localización.

## Aprendizaje con presencias y territorio no etiquetado

Las celdas con indicios son P y el resto es U: no se asume que el territorio no inventariado carezca de mineralización. La confianza se incorpora como peso: confirmada=1, pendiente={data.config['pending_weight']}, U=1. Si coinciden varios registros se toma el peso máximo. Se muestrean hasta tres U por P, con semillas fijadas y particiones exportadas.

Se evalúan logística L2, Random Forest, LightGBM y Bagging PU. Este último conserva P y remuestrea U para cada miembro. La evaluación espacial de este apartado utiliza scores relativos del ensamble. El benchmark de tres estrategias desarrollado más adelante incorpora Bagging PU + Elkan–Noto con una reserva interna para c; el reescalado no acredita por sí solo probabilidades físicas de depósito.

## Validación espacial

Se utilizan cinco pliegues por bloques de 50 km, excluyendo del pool los bloques de los distritos de reserva. Se retiran del entrenamiento las muestras a menos de 15 km de las muestras de validación. Imputación, escalado y codificación se ajustan solo con entrenamiento. Las métricas se calculan sin ponderar, sobre las predicciones fuera de pliegue de la muestra P/U.

{frame_markdown(benchmark[['model', 'n_input_features', 'roc_auc', 'average_precision', 'positive_cell_recovery_at_05', 'positive_cell_recovery_at_10']])}

La recuperación de esta tabla mide celdas P dentro de la muestra de evaluación, no depósitos ni superficie nacional. ROC-AUC mide ordenación de etiquetas P/U; Average Precision depende también de la composición de la muestra.

## Evaluación territorial por distritos

Se reentrena en siete rotaciones, reservando grupos de distritos completos, sus bloques y un buffer de 15 km respecto a las celdas de esos bloques. También quedan excluidos los indicios sin distrito que se sitúan en ese territorio. Se puntúan todas las celdas reservadas; un depósito se recupera si alguna celda asociada entra en el 1 %, 5 % o 10 % mejor puntuado del grupo. Los empates se resuelven por cell_id, sin utilizar la etiqueta.

{frame_markdown(rotations[['model', 'n_deposits', 'captured_deposits_at_01', 'captured_deposits_at_05', 'captured_deposits_at_10', 'deposit_recovery_at_10']])}

Estas rotaciones permiten examinar transferencia regional dentro del inventario conocido. Los ajustes comparten datos entre rotaciones; una campaña nueva permitiría evaluar la utilidad prospectiva externa.

![Resultados de los modelos](figuras/resultados_modelos.png)

## Cartografía, estabilidad e interpretación

La cartografía nacional se obtiene con ocho miembros LightGBM ajustados después de evaluar, utilizando las {ds['n_positive_cells']} celdas P y diferentes muestras U. Cada miembro tiene {data.config['lightgbm_trees']} árboles y una muestra de hasta {data.config['u_per_p']} U por P. La evaluación de Bagging PU utiliza {data.config['pu_bags']} miembros de 100 árboles y hasta {data.config['pu_u_per_p']} U por P dentro de su muestra de entrenamiento; sus métricas corresponden a ese protocolo y no son un test independiente de los ocho objetos nacionales.

Se exportan media de favorabilidad, desviación del ensamble, novedad, percentil de score, categoría y número de variables geoquímicas ausentes. La novedad es la distancia euclídea al centroide P en el espacio numérico estandarizado y categórico one-hot del primer miembro. La dispersión mide sensibilidad entre miembros, no toda la incertidumbre geológica. La inspección de variables permite relacionar la prioridad con sus evidencias; no se calculan SHAP ni EBM en esta cadena.

Las categorías son: 1 novedad elevada (distancia superior al percentil 95); 2 favorabilidad alta y dispersión baja; 3 favorabilidad alta y dispersión alta; 4 favorabilidad menor y dispersión baja; 5 favorabilidad menor y dispersión elevada. Favorabilidad alta usa el percentil 90 y dispersión alta el percentil 75. Son umbrales relativos al dominio.

{frame_markdown(pd.read_csv(data.output / 'map_category_counts.csv').sort_values('category'))}

![Cartografía GeoAI](figuras/mapa_geoquimica.png)

## Reproducción y productos

Ejecutar .venv-fase-a/Scripts/python.exe scripts/ejecutar_geoquimica.py desde la raíz. La configuración está en config/geoquimica_20261017.yaml. El notebook 18 reúne el recorrido completo; el 04 detalla geoquímica y el 17 presenta mapas y consulta de celdas. Los notebooks de preparación y modelado leen la misma configuración y los mismos resultados.

reports/geoquimica_20261017 contiene variables, cobertura, leyendas, registros, particiones, métricas, ocho modelos joblib y cartografía Parquet/GeoTIFF EPSG:25830. Los manifiestos SHA-256 registran entradas, código y salidas; environment.json conserva el entorno. El sistema apoya priorización regional y revisión geológica. No estima leyes, reservas ni rentabilidad; su aplicación se completa con contraste geológico y trabajo de campo.
"""
    if (data.output / "benchmark_cv_summary.csv").is_file():
        from .validation_diagnostics import generate_diagnostic_report
        diagnostic_text = generate_diagnostic_report(data)
        text += "\n\n" + diagnostic_text.replace("# GeoAI · Validación cruzada y factor de propensión aparente", "# Validación de tres estrategias y propensión", 1)
    if (data.output / "fusion_summary.json").is_file():
        from .model_fusion import generate_fusion_report
        text += "\n\n" + generate_fusion_report(data)
    (data.report / "INFORME_RESULTADOS_GEOQUIMICA.md").write_text(text, encoding="utf-8")
    card = f"""# GeoAI · Model card

Modelo de prospectividad regional con 64 entradas: 56 variables numéricas y ocho clases geoquímicas (As, Sb, Bi, Hg, Cu, Pb, Zn y W). One-hot distingue clases y ausencias; las entradas no son concentraciones analíticas verificadas. Au y los identificadores quedan fuera de los predictores.

{headline}

Se utilizan {ds['n_records']} registros elegibles consolidados en {ds['n_positive_cells']} celdas P. Confirmadas tienen peso 1 y pendientes 0,5. Se evalúa mediante cinco pliegues espaciales y siete rotaciones territoriales con bloques de 50 km y buffer de 15 km. Las métricas se refieren a etiquetas P/U conocidas y a esos protocolos.

La cartografía contiene {data.config['national_bags']} miembros LightGBM de {data.config['lightgbm_trees']} árboles ajustados sobre todo el dominio elegible. Modelos y parámetros: reports/geoquimica_20261017/models/GeoAI/. La evaluación de Bagging PU emplea cinco miembros de 100 árboles; la cartografía posterior al ajuste no constituye un conjunto de evaluación independiente.

Salidas: score relativo P/U, dispersión, novedad y categorías. No se estima probabilidad física de mineralización. La cobertura desigual, especialmente Zn y W, la revisión pendiente de leyendas y el sesgo del inventario condicionan su interpretación. Uso previsto: priorización regional con revisión experta y contraste de campo. Detalles y tablas: informes/geoquimica_20261017/INFORME_RESULTADOS_GEOQUIMICA.md.
"""
    (data.report / "MODEL_CARD_GEOQUIMICA.md").write_text(card, encoding="utf-8")
    write_json(data.output / "environment.json", {"python": platform.python_version(),
        "packages": {name: importlib.metadata.version(name) for name in
                     ["numpy", "pandas", "scipy", "scikit-learn", "lightgbm", "pyarrow", "nbformat", "rasterio"]}})
    write_json(data.output / "control_ejecucion.json", {"status": "complete", "models_retrained": True,
        "n_cv_results": len(benchmark), "n_rotation_results": len(rotations),
        "n_cells": ds["n_cells"], "n_input_features": 64, "geoquimica_incluida": True, "absolute_probability": False,
        "n_cv_diagnostic_results": len(pd.read_csv(data.output / "benchmark_cv_summary.csv")) if (data.output / "benchmark_cv_summary.csv").is_file() else 0})
    code_paths = [Path(__file__), data.root / "scripts/ejecutar_geoquimica.py",
                  data.root / "scripts/actualizar_notebooks_geoquimica.py", data.root / "scripts/generar_notebook_18.py",
                  data.root / "scripts/validar_geoquimica.py", data.root / "tests/test_geochemical_experiment.py",
                  data.root / "src/geoau/validation_diagnostics.py", data.root / "tests/test_validation_diagnostics.py"]
    code_paths += [data.root / "src/geoau/model_fusion.py", data.root / "tests/test_model_fusion.py"]
    write_json(data.output / "code_manifest.json", {path.relative_to(data.root).as_posix(): sha256(path) for path in code_paths})
    paths = sorted(path for path in data.output.rglob("*") if path.is_file() and path.name != "outputs_manifest.json")
    write_json(data.output / "outputs_manifest.json", [
        {"path": path.relative_to(data.output).as_posix(), "sha256": sha256(path), "bytes": path.stat().st_size} for path in paths])
    return text


def run_experiment(root: Path, config_path: Path | None = None, stage="all"):
    data = load_data(root, config_path)
    if stage in ["all", "audit"]:
        audit_inputs(data)
    else:
        old = json.loads((data.output / "input_manifest.json").read_text(encoding="utf-8"))
        if old != data.inputs:
            raise ValueError("Han cambiado las entradas. Ejecutar primero la auditoría y regenerar resultados.")
    if stage in ["all", "audit", "benchmark", "diagnostics", "rotations", "maps", "fusion"]:
        write_json(data.output / "control_ejecucion.json", {"status": "running", "stage": stage})
    if stage in ["all", "benchmark"]:
        run_benchmark(data)
    if stage in ["all", "benchmark", "diagnostics"]:
        from .validation_diagnostics import run_diagnostics
        run_diagnostics(data)
    if stage in ["all", "rotations"]:
        run_rotations(data)
    if stage in ["all", "maps"]:
        run_maps(data)
    if stage in ["all", "fusion"]:
        from .model_fusion import run_fusion
        run_fusion(data)
    if stage in ["all", "report"]:
        generate_report(data)
    return data
