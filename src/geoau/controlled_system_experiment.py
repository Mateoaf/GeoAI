"""Audited, reproducible experiment behind Notebook 27 (review items 1--4)."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import importlib.metadata
import json
import math
from pathlib import Path
import sys
import time

import joblib
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.stats import hypergeom

from .controlled_system_features import audit_systems, build_features, DIAGNOSTIC, GEOCHEMICAL
from .controlled_system_models import COMPONENTS, FAMILIES, METHODS, fit_nested, BackgroundCDF
from .geochemical_experiment import (load_data, sha256, write_json, label_metrics,
    cell_hash, rotation_pools, spatial_splits, write_raster)
from .national_evaluation import cv_training_pool, deposit_metrics


DEFAULT_CONFIG = {
    "seed": 42, "bags": 8, "inner_folds": 3, "buffer_m": 15000,
    "weight_step": .1, "minimum_specialist_P": 2, "prediction_batch_size": 25000,
    "default_national_method": "fusion_3", "selection_metric": "inner_oof_average_precision",
    "classifier": {"n_estimators": 150, "max_depth": 5, "num_leaves": 24,
        "learning_rate": .04, "reg_alpha": .5, "reg_lambda": 1.,
        "min_child_samples": 10, "colsample_bytree": .7, "verbosity": -1, "n_jobs": 4},
    "epithermal_classifier": {"n_estimators": 80, "max_depth": 3, "num_leaves": 8, "min_child_samples": 2},
    "percentages": [1, 5, 10, 20],
    "notes": "8 bags everywhere; no sampling replacement; training-only normalization; >=0.1 global fusion weight; exploratory reused outer territories",
}


def markdown_table(frame):
    columns = list(frame.columns)
    rows = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"]*len(columns)) + " |"]
    for values in frame.itertuples(index=False, name=None):
        rows.append("| " + " | ".join(f"{v:.5f}" if isinstance(v, float) else str(v) for v in values) + " |")
    return "\n".join(rows)


class ControlledExperiment:
    def __init__(self, root, output=None):
        self.root = Path(root).resolve()
        self.output = self.root / (output or "reports/nb27_comparacion_controlada_20261022")
        self.report_dir = self.root / "informes" / self.output.name
        self.output.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.cfg = json.loads(json.dumps(DEFAULT_CONFIG))
        self.data = load_data(self.root)
        self.grid = self.data.grid.set_index("cell_id")
        self.sample = pd.read_parquet(self.data.output / "partitions/benchmark_sample.parquet")
        self.membership = pd.read_parquet(self.data.output / "partitions/benchmark_memberships.parquet")
        self.old_design = json.loads((self.data.output / "partitions/benchmark_design.json").read_text(encoding="utf-8"))
        self.groups = pd.read_csv(self.data.output / "partitions/district_groups.csv")
        self.protected = self._protected_inputs()
        self.code = {str(p.relative_to(self.root)).replace("\\", "/"): sha256(p) for p in [
            self.root / "src/geoau/controlled_system_features.py",
            self.root / "src/geoau/controlled_system_models.py",
            self.root / "src/geoau/controlled_system_experiment.py",
            self.root / "scripts/build_notebook_27.py"]}
        design = {"config": self.cfg, "source_hashes": self.protected, "code_hashes": self.code,
            "fixed_before_evaluation": True, "outer_territories_previously_explored": True,
            "external_test": False, "absolute_probability": False,
            "scope": "review items 1-4 only; existing cached sources; no new imagery or field campaign",
            "feature_corrections": "interval representatives, missingness retained, training-only pathfinder statistics; fixed label-free spatial context",
            "control": "mono93/mono95 identical rows, seeds, hyperparameters; shared global and alluvial models in 2/3 expert variants",
            "epithermal_rule": "documented Rodalquilar deposits only; no province rule; unresolved P remain in global backbone",
            "date_local": "2026-10-22"}
        design_path = self.output / "design.json"
        if design_path.exists():
            if json.loads(design_path.read_text(encoding="utf-8")) != design:
                raise ValueError("La carpeta contiene otra configuración, entradas o código. Utiliza una carpeta nueva.")
        else:
            write_json(design_path, design)
        write_json(self.output / "environment.json", {"python": sys.version,
            "packages": {p: importlib.metadata.version(p) for p in ["numpy", "pandas", "scipy", "scikit-learn", "lightgbm", "rasterio", "pyarrow", "nbclient", "joblib"]}})
        self.log("Experimento NB27 iniciado: 5 CV + 7 rotaciones + ajuste nacional; configuración fijada")

    def _protected_inputs(self):
        paths = [self.root / k for k in self.data.inputs if k != "eligibility_column"]
        paths += list((self.data.output / "partitions").glob("*"))
        paths += [self.data.output / n for n in ["benchmark_summary.csv", "benchmark_oof_predictions.parquet", "rotation_metrics.csv", "rotation_summary.csv"]]
        for folder in [self.data.output / "models/GeoAI", self.data.output / "maps",
                       self.root / "reports/reentrenamiento_desacoplamiento_sistemas_20261022"]:
            paths += [p for p in folder.rglob("*") if p.is_file()]
        paths += [self.root / "notebooks/26_desacoplamiento_sistemas_minerales_y_reentrenamiento.ipynb"]
        return {p.relative_to(self.root).as_posix(): sha256(p) for p in sorted(set(paths)) if p.is_file()}

    def log(self, message):
        text = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {message}"
        print(text, flush=True)
        with (self.output / "progress.log").open("a", encoding="utf-8") as stream:
            stream.write(text+"\n")

    def audit_labels(self):
        records, self.systems, summary = audit_systems(self.data.records, self.data.positives)
        records.to_csv(self.output / "auditoria_sistemas_por_registro.csv", index=False)
        self.systems.to_csv(self.output / "sistemas_por_celda.csv", index=False)
        summary.to_csv(self.output / "resumen_tipologias.csv", index=False)
        records.loc[records.sin_tipo_documentado].to_csv(self.output / "registros_sin_sistema_resuelto.csv", index=False)
        self.log("Auditoría de tipologías: "+summary.to_json(orient="records"))
        return summary

    def prepare_features(self):
        path = self.output / "X_nb27.parquet"
        marker = self.output / "feature_inputs.json"
        if path.exists() and marker.exists():
            for name, expected in json.loads(marker.read_text(encoding="utf-8")).items():
                if sha256(self.root / name) != expected:
                    raise ValueError(f"Fuente de covariables modificada: {name}")
            self.X = pd.read_parquet(path)
        else:
            self.log("Auditando los ocho rásteres y reconstruyendo covariables MODIS desde la caché")
            self.X, inputs = build_features(self.data, self.output)
            write_json(marker, {p.relative_to(self.root).as_posix(): sha256(p) for p in inputs})
        if len(self.X.columns) != 95 or not self.X.index.equals(pd.Index(self.data.grid.cell_id, name="cell_id")):
            raise AssertionError("Contrato de 95 covariables o correspondencia de celdas incorrectos.")
        self.log(f"Matriz corregida disponible: {self.X.shape[0]} celdas x {self.X.shape[1]} variables")
        return pd.read_csv(self.output / "auditoria_geoquimica.csv")

    def inner_splits(self, pool, seed):
        p = self.data.positives.loc[self.data.positives.cell_id.isin(pool.cell_id)]
        background = pool.loc[~pool.cell_id.isin(self.data.positives.cell_id), "cell_id"].to_numpy()
        rng = np.random.default_rng(seed+90000)
        u = background[rng.choice(len(background), 3*len(p), replace=False)]
        master = pd.concat([p[["cell_id", "peso_confianza"]].assign(label=1),
            pd.DataFrame({"cell_id": u, "peso_confianza": 1., "label": 0})], ignore_index=True)
        master = master.merge(pool[["cell_id", "block_id", "x_center", "y_center"]], validate="one_to_one")
        split = spatial_splits(master, self.cfg["inner_folds"], self.cfg["buffer_m"], seed)
        memberships = []
        for fold, (train, test, excluded) in enumerate(split):
            for role, indices in [("train", train), ("validation", test), ("buffer_excluded", excluded)]:
                memberships.append(pd.DataFrame({"cell_id": master.iloc[indices].cell_id,
                                                 "fold": fold, "role": role}))
        combined = pd.concat(memberships, ignore_index=True)
        view = replace(self.data, grid=pool)
        parts = []
        for fold, (train, test, _) in enumerate(split):
            admissible = cv_training_pool(view, master, combined, fold, [])
            expected = set(master.iloc[train].loc[master.iloc[train].label.eq(1), "cell_id"])
            actual = set(self.data.positives.loc[self.data.positives.cell_id.isin(admissible.cell_id), "cell_id"])
            if actual != expected:
                raise AssertionError("Las P de la región interna no coinciden con las de su pliegue.")
            parts.append((fold, admissible, master.iloc[test]))
        return master, memberships, parts

    def run_partition(self, scope, partition, pool, expected_p, evaluation_ids):
        folder = self.output / "partitions" / f"{scope}_{partition}"
        folder.mkdir(parents=True, exist_ok=True)
        complete = folder / "complete.json"
        if complete.exists():
            saved = json.loads(complete.read_text(encoding="utf-8"))
            if saved["evaluation_hash"] != cell_hash(evaluation_ids) or saved["positive_hash"] != cell_hash(expected_p):
                raise ValueError("Una partición guardada no corresponde al experimento actual.")
            self.log(f"Reutilizando partición NB27 ya completada: {scope}/{partition}")
            return pd.read_parquet(folder / "predictions.parquet")
        self.log(f"Comenzando {scope}/{partition}: {len(expected_p)} P, {len(evaluation_ids)} celdas a puntuar")
        seed = self.cfg["seed"] + {"cv": 0, "rotation": 1000000, "national": 2000000}[scope]+10000*partition
        _, predictions = fit_nested(self.data, self.X, self.systems, pool, expected_p, evaluation_ids,
            self.cfg, seed, folder, scope, partition, self.inner_splits, self.log)
        write_json(complete, {"evaluation_hash": cell_hash(evaluation_ids),
            "positive_hash": cell_hash(expected_p), "predictions_sha256": sha256(folder / "predictions.parquet"),
            "model_sha256": sha256(folder / "model.joblib")})
        return predictions

    def evaluate_cv(self):
        predictions, rows = [], []
        for fold in range(5):
            roles = self.membership.loc[self.membership.fold.eq(fold)]
            test = self.sample.set_index("cell_id").loc[roles.loc[roles.role.eq("validation"), "cell_id"]].reset_index()
            reference_train = self.sample.loc[self.sample.cell_id.isin(roles.loc[roles.role.eq("train"), "cell_id"])]
            expected = reference_train.loc[reference_train.label.eq(1), "cell_id"]
            pool = cv_training_pool(self.data, self.sample, self.membership, fold, self.old_design["reserved_blocks_excluded"])
            frame = self.run_partition("cv", fold, pool, expected, test.cell_id)
            frame = frame.merge(test[["cell_id", "label"]], validate="one_to_one").assign(fold=fold)
            predictions.append(frame)
            for method in METHODS:
                rows.append({"method": method, "fold": fold, "n_train_P": len(expected),
                             **label_metrics(frame.label, frame[method], frame.cell_id)})
            pd.DataFrame(rows).to_csv(self.output / "cv_fold_metrics.csv", index=False)
            self.log(f"CV {fold+1}/5 terminada; AUC mono95={rows[-6]['roc_auc']:.4f}")
        joined = pd.concat(predictions, ignore_index=True)
        joined.to_parquet(self.output / "cv_oof_predictions.parquet", index=False)
        summary = pd.DataFrame([{"method": m, **label_metrics(joined.label, joined[m], joined.cell_id)} for m in METHODS])
        summary.to_csv(self.output / "cv_summary.csv", index=False)
        return summary

    def evaluate_rotations(self):
        details, metrics, expected_random = [], [], []
        for group, districts in self.groups.groupby("group"):
            group = int(group)
            pool, held = rotation_pools(self.data, set(districts.district_id))
            frozen = pd.read_parquet(self.data.output / f"partitions/rotation_{group}_held.parquet")
            train = pd.read_parquet(self.data.output / f"partitions/rotation_{group}_sample.parquet")
            if set(held.cell_id) != set(frozen.cell_id):
                raise AssertionError("Se ha alterado un territorio de evaluación.")
            expected_p = train.loc[train.label.eq(1), "cell_id"]
            frame = self.run_partition("rotation", group, pool, expected_p, frozen.cell_id)
            rel = self.data.records.loc[self.data.records.district_id.isin(districts.district_id)].dropna(subset=["deposit_id"])
            rel = rel[["cell_id", "deposit_id", "district_id"]].drop_duplicates()
            for method in METHODS:
                values, detail, _ = deposit_metrics(rel, frame[["cell_id", method]].rename(columns={method: "score"}))
                details.append(detail.assign(group=group, method=method))
                metrics.append({"method": method, "group": group, **values})
            for pct in self.cfg["percentages"]:
                footprints = rel.groupby("deposit_id").cell_id.nunique().to_numpy()
                expected = float(hypergeom.sf(0, len(held), footprints, math.ceil(len(held)*pct/100)).sum())
                expected_random.append({"group": group, "budget_percent": pct,
                                       "n_deposits": len(footprints), "expected_deposits": expected})
            pd.DataFrame(metrics).to_csv(self.output / "rotation_metrics.csv", index=False)
            self.log(f"Rotación {group+1}/7 terminada")
        detail = pd.concat(details, ignore_index=True)
        detail.to_csv(self.output / "rotation_deposit_predictions.csv", index=False)
        rows = []
        for method, frame in detail.groupby("method", sort=False):
            n = frame.deposit_id.nunique()
            row = {"method": method, "n_deposits": n}
            for pct in self.cfg["percentages"]:
                count = frame.loc[frame[f"captured_at_{pct:02d}"], "deposit_id"].nunique()
                row[f"captured_{pct:02d}"] = count
                row[f"recovery_{pct:02d}"] = count/n
            rows.append(row)
        summary = pd.DataFrame(rows)
        summary.to_csv(self.output / "rotation_summary.csv", index=False)
        random = pd.DataFrame(expected_random)
        random.to_csv(self.output / "random_by_group.csv", index=False)
        random.groupby("budget_percent", as_index=False).expected_deposits.sum().to_csv(self.output / "random_summary.csv", index=False)
        return summary

    def fit_national(self):
        frame = self.run_partition("national", 0, self.data.grid, self.data.positives.cell_id, self.data.grid.cell_id)
        frame.to_parquet(self.output / "favorabilidad_nacional_controlada.parquet", index=False)
        default = self.cfg["default_national_method"]
        (self.output / "maps").mkdir(exist_ok=True)
        write_raster(replace(self.data, output=self.output), "NB27_fusion3_score", frame[default].to_numpy())
        rel = self.data.records.dropna(subset=["deposit_id"])[["cell_id", "deposit_id"]].drop_duplicates()
        rows = []
        for method in METHODS:
            values, _, _ = deposit_metrics(rel, frame[["cell_id", method]].rename(columns={method: "score"}))
            rows.append({"method": method, **values})
        summary = pd.DataFrame(rows)
        summary.to_csv(self.output / "national_in_sample_metrics.csv", index=False)
        self.log("Ajuste nacional terminado; sus recuperaciones son descriptivas, no un test independiente")
        return summary

    def validate(self):
        checks = []
        def check(condition, message):
            if not condition:
                raise AssertionError(message)
            checks.append(message)
        check(self._protected_inputs() == self.protected, "Entradas, NB26, mapas y métricas anteriores intactos")
        for name, expected in json.loads((self.output / "feature_inputs.json").read_text(encoding="utf-8")).items():
            check(sha256(self.root / name) == expected, f"Fuente de covariables intacta: {name}")
        audit = pd.read_csv(self.output / "auditoria_sistemas_por_registro.csv")
        check(audit.loc[audit.epitermal, "deposit_id"].isin(["dep_rodalquilar_cinto", "dep_rodalquilar_santa_josefa"]).all(),
              "Epitermal sin regla provincial ni placeres del Darro")
        check(not (self.systems.no_resuelto & self.systems.primario).any(), "Los no resueltos no se fuerzan a primario")
        cv = pd.read_parquet(self.output / "cv_oof_predictions.parquet")
        check(cv.cell_id.is_unique and set(cv.cell_id) == set(self.sample.cell_id), "OOF externo completo y único")
        summary = pd.read_csv(self.output / "cv_summary.csv").set_index("method")
        for method in METHODS:
            calculated = label_metrics(cv.label, cv[method], cv.cell_id)
            check(all(abs(v-summary.loc[method, k]) < 1e-12 for k, v in calculated.items()), f"Métricas CV recalculadas: {method}")
        runs = []
        positive_ids = set(self.data.positives.cell_id)
        positive_weights = self.data.positives.set_index("cell_id").peso_confianza
        for scope, count in [("cv", 5), ("rotation", 7), ("national", 1)]:
            for partition in range(count):
                folder = self.output / "partitions" / f"{scope}_{partition}"
                pred = pd.read_parquet(folder / "predictions.parquet")
                bundle = joblib.load(folder / "model.joblib")
                inner = pd.read_parquet(folder / "inner_predictions.parquet")
                member_roles = pd.read_parquet(folder / "inner_memberships.parquet")
                if scope == "cv":
                    role = self.membership.loc[self.membership.fold.eq(partition)]
                    held = role.loc[role.role.eq("validation"), "cell_id"]
                    reference = self.sample.loc[self.sample.cell_id.isin(role.loc[role.role.eq("train"), "cell_id"])]
                    expected_p = set(reference.loc[reference.label.eq(1), "cell_id"])
                elif scope == "rotation":
                    held = pd.read_parquet(self.data.output / f"partitions/rotation_{partition}_held.parquet").cell_id
                    reference = pd.read_parquet(self.data.output / f"partitions/rotation_{partition}_sample.parquet")
                    expected_p = set(reference.loc[reference.label.eq(1), "cell_id"])
                else:
                    held = self.data.grid.cell_id
                    expected_p = positive_ids
                check(inner.cell_id.is_unique and (scope == "national" or not set(inner.cell_id) & set(held)),
                      f"OOF interno completo sin territorio externo: {scope}/{partition}")
                for component in COMPONENTS:
                    fitted = bundle.normalizers[component]
                    recalculated = BackgroundCDF().fit(inner.loc[inner.label.eq(0), component])
                    check(fitted.available_ == recalculated.available_ and (not fitted.available_ or
                          (np.array_equal(fitted.x_, recalculated.x_) and np.array_equal(fitted.p_, recalculated.p_))),
                          f"Normalización ajustada solo con U OOF internas: {scope}/{partition}/{component}")
                for path in sorted(folder.glob("training_*.parquet")):
                    level = path.stem.removeprefix("training_")
                    train = pd.read_parquet(path)
                    fit_rows = pd.read_csv(folder / f"fits_{level}.csv")
                    runs.append(fit_rows)
                    if level.startswith("inner_"):
                        fold = int(level.split("_")[1])
                        eval_ids = inner.loc[inner.inner_fold.eq(fold), "cell_id"]
                        forbidden_blocks = set(self.grid.loc[eval_ids].block_id)
                        allowed_inner = set(member_roles.loc[member_roles.fold.eq(fold) & member_roles.role.eq("train"), "cell_id"])
                        check(set(train.loc[train.label.eq(1), "cell_id"]) <= allowed_inner,
                              f"P internas autorizadas: {scope}/{partition}/{level}")
                        check(scope == "national" or not set(train.cell_id) & set(held),
                              f"Todos los ajustes internos excluyen el test externo: {scope}/{partition}/{level}")
                        if scope != "national":
                            unique_inner = train.cell_id.drop_duplicates()
                            outer_distance = cKDTree(self.grid.loc[held, ["x_center", "y_center"]]).query(
                                self.grid.loc[unique_inner, ["x_center", "y_center"]])[0]
                            check((outer_distance >= 15000).all(),
                                  f"Buffer externo respetado también en el ajuste interno: {scope}/{partition}/{level}")
                    else:
                        eval_ids = held
                        forbidden_blocks = set(self.grid.loc[eval_ids].block_id)
                    if scope != "national" or level != "outer":
                        unique = train.cell_id.drop_duplicates()
                        check(not set(unique) & set(eval_ids), f"Sin celdas de evaluación entrenadas: {scope}/{partition}/{level}")
                        check(not set(self.grid.loc[unique].block_id) & forbidden_blocks,
                              f"Bloques separados: {scope}/{partition}/{level}")
                        distances = cKDTree(self.grid.loc[eval_ids, ["x_center", "y_center"]]).query(
                            self.grid.loc[unique, ["x_center", "y_center"]])[0]
                        check((distances >= 15000).all(), f"Buffer interno/externo: {scope}/{partition}/{level}")
                    for (component, member), rows in train.groupby(["component", "member"]):
                        p, u = rows.loc[rows.label.eq(1)], rows.loc[rows.label.eq(0)]
                        check(rows.cell_id.is_unique and len(u) == 3*len(p) and not set(u.cell_id) & positive_ids,
                              f"U:P=3:1 sin reemplazo ni P en U: {scope}/{partition}/{level}/{component}/{member}")
                        check(np.array_equal(p.peso_confianza, positive_weights.loc[p.cell_id]),
                              f"Pesos documentales conservados: {scope}/{partition}/{level}/{component}/{member}")
                        if component not in ["mono93", "mono95"]:
                            flags = self.systems.set_index("cell_id")
                            check(flags.loc[p.cell_id, component].all(),
                                  f"Especialista usa solo P tipificadas: {scope}/{partition}/{level}/{component}/{member}")
                        if component in ["mono93", "mono95"] and level == "outer":
                            check(set(p.cell_id) == expected_p, f"Todas las P originales: {scope}/{partition}/{component}/{member}")
                        recorded = fit_rows.loc[fit_rows.component.eq(component) & fit_rows.member.eq(member)].iloc[0]
                        check(cell_hash(rows.cell_id) == recorded.sample_hash,
                              f"Hash de muestra por miembro: {scope}/{partition}/{level}/{component}/{member}")
                        if level == "outer":
                            model = bundle.estimators[component][int(member)]
                            columns = [n for n in self.X if component != "mono93" or n not in DIAGNOSTIC]
                            fit_x = self.X.loc[rows.cell_id, columns]
                            derived = model.named_steps["derived_training_statistics"]
                            expected_mean = fit_x[derived.columns_].mean().fillna(0.)
                            check(np.allclose(derived.mean_, expected_mean, atol=1e-7),
                                  f"Estadísticas pathfinder solo de su entrenamiento: {scope}/{partition}/{component}/{member}")
                    # The two global models differ only in their two diagnostic columns.
                    for member in range(8):
                        a = train.loc[train.component.eq("mono93") & train.member.eq(member), "cell_id"]
                        b = train.loc[train.component.eq("mono95") & train.member.eq(member), "cell_id"]
                        check(a.tolist() == b.tolist(), f"Ablación 93/95 pareada: {scope}/{partition}/{level}/{member}")
                probe = pred.cell_id.iloc[np.linspace(0, len(pred)-1, min(64, len(pred)), dtype=int)]
                raw, _ = bundle.predict_raw(self.X.loc[probe])
                actual, _ = bundle.combine(raw, self.X.loc[probe])
                expected = pred.set_index("cell_id").loc[probe]
                check(all(np.allclose(actual[m], expected[m], rtol=0, atol=1e-12) for m in METHODS),
                      f"Predicciones reproducidas del modelo guardado: {scope}/{partition}")
        all_runs = pd.concat(runs, ignore_index=True)
        all_runs.to_csv(self.output / "all_fit_runs.csv", index=False)
        details = pd.read_csv(self.output / "rotation_deposit_predictions.csv")
        rotation_summary = pd.read_csv(self.output / "rotation_summary.csv").set_index("method")
        for method in METHODS:
            frame = details.loc[details.method.eq(method)]
            check(frame.deposit_id.nunique() == 45 and frame.groupby("deposit_id").group.nunique().eq(1).all(),
                  f"45 depósitos únicos: {method}")
            for pct in self.cfg["percentages"]:
                check(frame.loc[frame[f"captured_at_{pct:02d}"], "deposit_id"].nunique() == rotation_summary.loc[method, f"captured_{pct:02d}"],
                      f"Recuperación territorial recalculada: {method}/{pct}%")
        check(self._protected_inputs() == self.protected, "Artefactos anteriores intactos al terminar")
        result = {"passed": True, "n_checks": len(checks), "recorded_component_fits": len(all_runs),
                  "actual_component_fits": int((~all_runs.reused_identical_fit).sum()), "bundles_replayed": 13, "checks": checks}
        write_json(self.output / "validation.json", result)
        self.log(f"Validación final: {len(checks)} comprobaciones, 13 modelos de experimento reproducidos")
        return {k: v for k, v in result.items() if k != "checks"}

    def make_figures(self):
        import matplotlib.pyplot as plt
        folder = self.output / "figuras"
        folder.mkdir(exist_ok=True)
        cv = pd.read_csv(self.output / "cv_summary.csv").set_index("method")
        rotation = pd.read_csv(self.output / "rotation_summary.csv").set_index("method")
        random = pd.read_csv(self.output / "random_summary.csv")
        fig, axes = plt.subplots(1, 3, figsize=(17, 5))
        cv.roc_auc.plot.bar(ax=axes[0], ylim=(.4, 1), title="ROC-AUC · CV espacial")
        cv.average_precision.plot.bar(ax=axes[1], ylim=(0, 1), title="Average Precision · CV espacial")
        for method in METHODS:
            axes[2].plot(self.cfg["percentages"], [rotation.loc[method, f"captured_{p:02d}"] for p in self.cfg["percentages"]], marker="o", label=method)
        axes[2].plot(random.budget_percent, random.expected_deposits, "k--", label="Azar: esperanza exacta")
        axes[2].set(xlabel="Presupuesto de celdas (%)", ylabel="Depósitos de 45", title="Rotaciones territoriales")
        axes[2].legend(fontsize=7)
        for ax in axes[:2]:
            ax.tick_params(axis="x", rotation=55)
        fig.tight_layout()
        fig.savefig(folder / "comparacion_metricas_nb27.png", dpi=150)
        plt.close(fig)
        national = pd.read_parquet(self.output / "favorabilidad_nacional_controlada.parquet").set_index("cell_id")
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        shape = (self.data.grid_spec["height"], self.data.grid_spec["width"])
        for ax, method in zip(axes.flat, ["mono93", "mono95", "fusion_2", "fusion_3"]):
            field = np.full(shape, np.nan)
            field[self.data.grid.row, self.data.grid.col] = national.loc[self.data.grid.cell_id, method].rank(pct=True)
            image = ax.imshow(field, cmap="magma", vmin=0, vmax=1)
            ax.set_title(method+" · percentil nacional")
            ax.set_axis_off()
        fig.colorbar(image, ax=axes.ravel().tolist(), shrink=.7, label="Percentil relativo; no probabilidad")
        fig.savefig(folder / "mapas_comparacion_nb27.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        return [folder / "comparacion_metricas_nb27.png", folder / "mapas_comparacion_nb27.png"]

    def write_report(self):
        cv = pd.read_csv(self.output / "cv_summary.csv")
        rot = pd.read_csv(self.output / "rotation_summary.csv")
        random = pd.read_csv(self.output / "random_summary.csv")
        systems = pd.read_csv(self.output / "resumen_tipologias.csv")
        validation = json.loads((self.output / "validation.json").read_text(encoding="utf-8"))
        text = f"""# NB27 · Auditoría y comparación controlada de sistemas minerales

Experimento ejecutado el 22 de octubre de 2026. Alcance: puntos 1 a 4 de la revisión del NB26. Fuentes existentes; no se adquieren nuevas campañas ni imágenes.

## 1. Tipologías

{markdown_table(systems)}

Primario incluye los contextos de roca documentados; no equivale a orogénico. Epitermal se limita a los dos depósitos documentados de Rodalquilar. No se utiliza provincia, cercanía ni predicciones para asignar tipos. Los no resueltos permanecen en todos los modelos globales y en el backbone de las fusiones, sin enviarse por defecto a roca. Las celdas mixtas conservan sus etiquetas múltiples. Son reglas operativas auditables a partir del inventario; no sustituyen una nueva revisión geológica experta.

## 2. Geoquímica y covariables

La banda 2 se audita por clase y se denomina representante de intervalo, no medición analítica continua. Promediar píxeles o aplicar log1p no crea información analítica nueva. Se conservan los ausentes, se aprende la imputación dentro de cada miembro y se reconstruye la covariable MODIS de la caché sin el relleno por mediana nacional anterior. Los coeficientes del índice pathfinder se fijan antes de evaluar; sus medias y desviaciones se aprenden solo con las filas de entrenamiento. Los residuos espaciales de ventana fija son covariables de cartografía disponible, calculadas sin etiquetas. Los proxies litológicos no se presentan como mediciones de metamorfismo. Las versiones de 93 y 95 variables comparten todas estas correcciones; la única diferencia entre ellas son los dos descriptores diagnósticos del NB26.

## 3. Combinación de expertos

Ocho miembros por componente y ajuste. Las escalas se hacen comparables mediante percentiles aproximados del fondo U predicho fuera de pliegue dentro del entrenamiento, con interpolación monótona y anclas fijas 0/1. No se utiliza el mínimo o máximo del territorio evaluado, ni el factor 0,7. Estos percentiles no son probabilidades de mineralización.

`max_2` y `fusion_2` utilizan exactamente el mismo global95 y los mismos especialistas primario/aluvial. `max_3` y `fusion_3` utilizan exactamente el mismo global95 y los especialistas primario_otro/aluvial/epitermal. Solo cambia el operador de agregación. Las fusiones eligen pesos no negativos en rejilla 0,1 mediante AP interna; conservan un peso global mínimo 0,1 para las presencias no resueltas. Un especialista con menos de dos P no se entrena y se registra como no disponible: no se inventan etiquetas ni se sustituye por una regla después de observar el test. El especialista epitermal, muy escaso, usa la regularización y capacidad reducida declaradas en design.json.

## 4. Comparación controlada

Se conservan las cinco particiones espaciales de la muestra original y las siete rotaciones distritales, bloques de 50 km y buffer de 15 km. Cada entrenamiento externo realiza tres pliegues espaciales internos con buffer para construir las referencias de fondo y seleccionar los pesos. Muestreo U sin reemplazo sobre el territorio permitido tanto en CV como en rotaciones y en el ajuste nacional; siempre tres U por P y miembro. Global93 y global95 comparten exactamente filas, semillas e hiperparámetros. Se reutilizan los componentes comunes entre métodos, sin reentrenarlos con otras semillas para favorecer una opción.

Los territorios ya se han examinado en cuadernos anteriores: es una comparación interna exploratoria, no una nueva prueba ciega externa. No se selecciona un ganador nacional utilizando los resultados externos. `fusion_3` se declara antes como cartografía principal experimental y se conservan todos los demás mapas. Cada presupuesto selecciona exactamente ceil(porcentaje × celdas), con desempate por cell_id y un único recuento por depósito.

### CV espacial: misma muestra P/U

{markdown_table(cv[['method','roc_auc','average_precision','brier_loss','positive_cell_recovery_at_05','positive_cell_recovery_at_10']])}

AP y AUC se refieren a etiquetas P/U. Brier sobre los percentiles de las fusiones es solo un diagnóstico numérico frente a P/U: no acredita calibración física ni es un criterio para elegir entre scores con escalas diferentes.

### Recuperación de depósitos en las siete rotaciones

{markdown_table(rot[['method','n_deposits','captured_01','captured_05','captured_10','captured_20']])}

Referencia aleatoria exacta, teniendo en cuenta las varias celdas de cada depósito:

{markdown_table(random)}

La regla geológica es una referencia simple predefinida de drenaje/pendiente, encajante/fallas y vulcanismo/ratios; no se ha optimizado con los territorios de evaluación. Las diferencias observadas no aíslan causalidad geológica ni garantizan significación. La comparación 93/95 aísla la incorporación de dos covariables bajo este procedimiento; 2/3 expertos compara las arquitecturas documentadas y el operador máximo/fusión sobre componentes compartidos.

### Cartografía y ajuste final

Los modelos se reajustan con todas las 664 P elegibles y sus muestras U. Sus recuperaciones nacionales son descriptivas in-sample, no una validación. `favorabilidad_nacional_controlada.parquet` conserva todos los scores y componentes; `maps/NB27_fusion3_score.tif` exporta el score principal experimental. Los percentiles, el score máximo y los pesos no constituyen probabilidades de encontrar oro.

![Comparación](../../{self.output.relative_to(self.root).as_posix()}/figuras/comparacion_metricas_nb27.png)

![Mapas](../../{self.output.relative_to(self.root).as_posix()}/figuras/mapas_comparacion_nb27.png)

## Validación y reproducibilidad

{validation['n_checks']} comprobaciones superadas; {validation['actual_component_fits']} ajustes efectivos y {validation['recorded_component_fits']} ajustes declarados contando componentes idénticos compartidos. Se reproducen predicciones desde los trece bundles guardados. Se comprueban miembros, muestras, ratios, pesos, buffer, bloques, normalizadores internos, estadísticas aprendidas y métricas. Las salidas previas y el NB26 permanecen intactos.

Notebook ejecutado: `notebooks/27_auditoria_sistemas_y_comparacion_controlada.ipynb`.

Reproducir: `.venv-fase-a/Scripts/python.exe scripts/build_notebook_27.py`. Los entrenamientos NB27 completos se reutilizan solo si diseño, código y entradas coinciden. Para una ejecución independiente usar `--output reports/nb27_repeticion`.
"""
        path = self.report_dir / "INFORME_NB27_COMPARACION_CONTROLADA.md"
        path.write_text(text, encoding="utf-8")
        return path

    def seal(self, report):
        write_json(self.output / "control_ejecucion.json", {"status": "complete", "validation_passed": True,
            "outer_cv_folds": 5, "district_rotations": 7, "inner_folds": 3, "bags": 8,
            "n_features": 95, "n_positive_cells": len(self.data.positives),
            "report": report.relative_to(self.root).as_posix(), "report_sha256": sha256(report),
            "completed_utc": datetime.now(timezone.utc).isoformat()})
        manifest = {p.relative_to(self.output).as_posix(): sha256(p) for p in self.output.rglob("*")
                    if p.is_file() and p.name not in ["outputs_manifest.json", "progress.log"]}
        write_json(self.output / "outputs_manifest.json", manifest)
        self.log("NB27 completado y sellado; sin sustituir los resultados anteriores")
