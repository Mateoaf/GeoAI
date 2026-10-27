"""Factorial global/desacoplado x 64/95, with the original national recipe."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.stats import hypergeom

from .base_decoupling_models import COMPONENTS, METHODS, fit_nested_paired, ordered_hash
from .controlled_system_experiment import ControlledExperiment, DEFAULT_CONFIG, markdown_table
from .controlled_system_features import audit_systems
from .controlled_system_models import BackgroundCDF
from .geochemical_experiment import (load_data, sha256, cell_hash, write_json, label_metrics,
    rotation_pools, write_raster, select_sample, make_model, predict)
from .national_evaluation import cv_training_pool, deposit_metrics


DEFAULT_OUTPUT = "reports/control_desacoplamiento_base64_nb26_20261022"
NOTEBOOK = "notebooks/26_desacoplamiento_sistemas_minerales_y_reentrenamiento.ipynb"
CONTRASTS = {
    "desacoplamiento_con_64": ("max3_64", "global64"),
    "desacoplamiento_con_95": ("max3_95", "global95"),
    "variables_en_global": ("global95", "global64"),
    "variables_en_desacoplado": ("max3_95", "max3_64"),
}


def prefix_hash(cells):
    """Hash complete parsed historical cells, including their existing outputs."""
    return hashlib.sha256(json.dumps(cells, sort_keys=True, ensure_ascii=False,
        separators=(",", ":")).encode("utf-8")).hexdigest()


class BaseDecouplingControl(ControlledExperiment):
    # Reuse only the existing spatial inner-split and log implementations.
    def __init__(self, root, output=DEFAULT_OUTPUT):
        self.root = Path(root).resolve()
        self.output = self.root / output
        self.report_dir = self.root / "informes" / self.output.name
        self.output.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.data = load_data(self.root)
        self.grid = self.data.grid.set_index("cell_id")
        self.base = self.root / "reports/nb27_comparacion_controlada_20261022"
        self.sample = pd.read_parquet(self.data.output / "partitions/benchmark_sample.parquet")
        self.membership = pd.read_parquet(self.data.output / "partitions/benchmark_memberships.parquet")
        self.old_design = json.loads((self.data.output / "partitions/benchmark_design.json").read_text(encoding="utf-8"))
        self.groups = pd.read_csv(self.data.output / "partitions/district_groups.csv")
        self.cfg = json.loads(json.dumps(DEFAULT_CONFIG))
        self.cfg["classifier"]["colsample_bytree"] = 1.0
        self.cfg.update(default_national_method="max3_64", bootstrap_repeats=10000,
            primary_endpoint="deposit_recovery_at_05", primary_contrast="max3_64 minus global64",
            selection_metric="none; four methods fixed; maximum has no learned fusion weights",
            notes="original national global recipe, identical paired samples and seeds for 64/95; audited systems; training-only CDF")
        _, self.systems, summary = audit_systems(self.data.records, self.data.positives)
        self.systems.to_csv(self.output / "sistemas_por_celda.csv", index=False)
        summary.to_csv(self.output / "resumen_tipologias.csv", index=False)
        self.history = json.loads((self.output / "historical_notebook.json").read_text(encoding="utf-8"))
        self.protected = self._protected_control()
        code_names = ["base_decoupling_control.py", "base_decoupling_models.py", "controlled_system_features.py",
            "controlled_system_models.py", "controlled_system_experiment.py", "geochemical_experiment.py", "national_evaluation.py"]
        self.code = {f"src/geoau/{n}": sha256(self.root / "src/geoau" / n) for n in code_names}
        self.code["scripts/append_control_64_nb26.py"] = sha256(self.root / "scripts/append_control_64_nb26.py")
        design = {"config": self.cfg, "code_hashes": self.code, "source_hashes": self.protected,
            "historical_prefix": self.history, "methods": list(METHODS), "contrasts": CONTRASTS,
            "fixed_before_control_results": True, "external_test": False, "previously_explored_territories": True,
            "feature_control": "original 64 unchanged; corrected NB27 95 = same 64 + 31",
            "seed_rule": "42+fold for CV, 42+group for rotation, 42 nationally; inner +1000*(fold+1)",
            "sampling_rule": "global exactly select_sample; paired rows/order/weights for 64 and 95 in every component",
            "normalization": "empirical CDF from three spatial inner OOF U predictions in training only",
            "score_meaning": "relative prospectivity; no absolute discovery probability",
            "date_local": "2026-10-22"}
        path = self.output / "design.json"
        if path.exists() and json.loads(path.read_text(encoding="utf-8")) != json.loads(json.dumps(design)):
            raise ValueError("Entradas, código o diseño diferentes: usar otra carpeta de salida.")
        write_json(path, design)
        write_json(self.output / "environment.json", {"python": sys.version, "executable": sys.executable,
            "packages": {n: importlib.metadata.version(n) for n in
                ["numpy", "pandas", "scikit-learn", "lightgbm", "scipy", "rasterio", "pyarrow", "nbclient", "joblib"]}})
        self.log("Control NB26 fijado: cuatro opciones, 5 CV, 7 rotaciones y reentrenamiento nacional")

    def _protected_control(self):
        paths = {self.root / n for n in self.data.inputs if n != "eligibility_column"}
        paths.update(p for p in (self.data.output / "partitions").glob("*") if p.is_file())
        for folder in [self.data.output / "models/GeoAI", self.data.output / "maps",
                       self.root / "reports/reentrenamiento_desacoplamiento_sistemas_20261022"]:
            paths.update(p for p in folder.rglob("*") if p.is_file())
        paths.update(self.base / n for n in ["X_nb27.parquet", "feature_inputs.json", "design.json", "outputs_manifest.json"])
        reference = self.root / "reports/evaluacion_configuracion_nacional_20261021"
        paths.update(reference / n for n in ["cv_predictions.parquet", "rotation_cell_predictions.parquet", "cv_metrics.csv"])
        # NB26 itself is explicitly being extended; its original byte copy is frozen instead.
        paths.add(self.output / "notebook26_original.ipynb")
        return {p.relative_to(self.root).as_posix(): sha256(p) for p in sorted(paths) if p.is_file()}

    def prepare_features(self):
        extended = pd.read_parquet(self.base / "X_nb27.parquet")
        original = self.data.features
        if len(extended.columns) != 95 or len(original.columns) != 64 or not extended.index.equals(original.index):
            raise AssertionError("Contratos 64/95 incorrectos.")
        pd.testing.assert_frame_equal(extended.loc[:, original.columns], original)
        self.matrices = {64: original, 95: extended}
        rows = []
        for n, X in self.matrices.items():
            for name in X:
                rows.append({"matrix": n, "feature": name, "original64": name in original,
                    "missing_fraction": float(X[name].isna().mean())})
        table = pd.DataFrame(rows)
        table.to_csv(self.output / "contrato_variables_64_95.csv", index=False)
        self.log(f"478443 celdas: base de 64 exacta y control extendido de 95; {len(self.data.positives)} P")
        return table.groupby("matrix").agg(variables=("feature", "size"), originales=("original64", "sum"))

    def run_partition(self, scope, partition, pool, expected_p, evaluation_ids):
        folder = self.output / "partitions" / f"{scope}_{partition}"
        folder.mkdir(parents=True, exist_ok=True)
        marker = folder / "complete.json"
        contract = {"evaluation_hash": ordered_hash(evaluation_ids), "positive_hash": cell_hash(expected_p),
                    "pool_hash": cell_hash(pool.cell_id), "design_sha256": sha256(self.output / "design.json")}
        if marker.exists():
            saved = json.loads(marker.read_text(encoding="utf-8"))
            if any(saved[k] != v for k, v in contract.items()):
                raise ValueError("Partición guardada con otra muestra o diseño.")
            for name, digest in saved["files"].items():
                if sha256(folder / name) != digest:
                    raise ValueError(f"Artefacto de partición modificado: {name}")
            self.log(f"Reutilizando control completado: {scope}/{partition}")
            return pd.read_parquet(folder / "predictions.parquet")
        self.log(f"Iniciando {scope}/{partition}: {len(expected_p)} P; {len(evaluation_ids)} celdas evaluadas")
        seed = self.cfg["seed"] + (partition if scope != "national" else 0)
        predictions = fit_nested_paired(self, pool, expected_p, evaluation_ids, seed, folder, scope, partition)
        contract["files"] = {p.name: sha256(p) for p in sorted(folder.iterdir()) if p.is_file() and p != marker}
        write_json(marker, contract)
        return predictions

    def evaluate_cv(self):
        frames, metrics = [], []
        for fold in range(5):
            roles = self.membership.loc[self.membership.fold.eq(fold)]
            test = self.sample.set_index("cell_id").loc[roles.loc[roles.role.eq("validation"), "cell_id"]].reset_index()
            train = self.sample.loc[self.sample.cell_id.isin(roles.loc[roles.role.eq("train"), "cell_id"])]
            pool = cv_training_pool(self.data, self.sample, self.membership, fold, self.old_design["reserved_blocks_excluded"])
            frame = self.run_partition("cv", fold, pool, train.loc[train.label.eq(1), "cell_id"], test.cell_id)
            frame = frame.merge(test[["cell_id", "label"]], validate="one_to_one").assign(fold=fold)
            frames.append(frame)
            for m in METHODS:
                metrics.append({"method": m, "fold": fold, **label_metrics(frame.label, frame[m], frame.cell_id)})
            pd.DataFrame(metrics).to_csv(self.output / "cv_fold_metrics.csv", index=False)
            self.log(f"CV {fold+1}/5 terminada")
        joined = pd.concat(frames, ignore_index=True)
        joined.to_parquet(self.output / "cv_oof_predictions.parquet", index=False)
        summary = pd.DataFrame([{"method": m, **label_metrics(joined.label, joined[m], joined.cell_id)} for m in METHODS])
        summary.to_csv(self.output / "cv_summary.csv", index=False)
        # This diagnostic distinguishes pooled-CV normalization effects from model fits.
        pd.DataFrame([{"method": f"cdf_global{n}", **label_metrics(joined.label, joined[f"cdf_global{n}"], joined.cell_id)}
                      for n in [64, 95]]).to_csv(self.output / "cv_cdf_diagnostic.csv", index=False)
        return summary

    def evaluate_rotations(self):
        details, metrics, random = [], [], []
        for group, districts in self.groups.groupby("group"):
            group = int(group)
            pool, held = rotation_pools(self.data, set(districts.district_id))
            frozen = pd.read_parquet(self.data.output / f"partitions/rotation_{group}_held.parquet")
            train = pd.read_parquet(self.data.output / f"partitions/rotation_{group}_sample.parquet")
            if set(held.cell_id) != set(frozen.cell_id):
                raise AssertionError("Territorio de rotación modificado.")
            frame = self.run_partition("rotation", group, pool, train.loc[train.label.eq(1), "cell_id"], frozen.cell_id)
            relations = self.data.records.loc[self.data.records.district_id.isin(districts.district_id)].dropna(subset=["deposit_id"])
            relations = relations[["cell_id", "deposit_id", "district_id"]].drop_duplicates()
            for method in METHODS:
                values, detail, _ = deposit_metrics(relations, frame[["cell_id", method]].rename(columns={method: "score"}))
                details.append(detail.assign(method=method, group=group))
                metrics.append({"method": method, "group": group, **values})
            for pct in self.cfg["percentages"]:
                footprints = relations.groupby("deposit_id").cell_id.nunique().to_numpy()
                expected = hypergeom.sf(0, len(held), footprints, math.ceil(len(held)*pct/100)).sum()
                random.append({"group": group, "budget_percent": pct, "expected_deposits": float(expected)})
            pd.DataFrame(metrics).to_csv(self.output / "rotation_metrics.csv", index=False)
            self.log(f"Rotación {group+1}/7 terminada")
        detail = pd.concat(details, ignore_index=True)
        detail.to_csv(self.output / "rotation_deposit_predictions.csv", index=False)
        summary = []
        for method in METHODS:
            sub = detail.loc[detail.method.eq(method)]
            row = {"method": method, "n_deposits": sub.deposit_id.nunique()}
            for pct in self.cfg["percentages"]:
                captured = sub.loc[sub[f"captured_at_{pct:02d}"], "deposit_id"].nunique()
                row[f"captured_{pct:02d}"] = captured
                row[f"recovery_{pct:02d}"] = captured / row["n_deposits"]
            summary.append(row)
        table = pd.DataFrame(summary)
        table.to_csv(self.output / "rotation_summary.csv", index=False)
        pd.DataFrame(random).to_csv(self.output / "random_by_group.csv", index=False)
        pd.DataFrame(random).groupby("budget_percent", as_index=False).expected_deposits.sum().to_csv(
            self.output / "random_summary.csv", index=False)
        self.compare_factorial()
        return table

    def compare_factorial(self):
        cv = pd.read_csv(self.output / "cv_summary.csv").set_index("method")
        rotation = pd.read_csv(self.output / "rotation_metrics.csv")
        summary = pd.read_csv(self.output / "rotation_summary.csv").set_index("method")
        # Whole rotation groups, keeping the four methods paired in every draw.
        groups = sorted(rotation.group.unique())
        draws = np.random.default_rng(42).integers(0, len(groups), (self.cfg["bootstrap_repeats"], len(groups)))
        denominators = rotation.loc[rotation.method.eq(METHODS[0])].set_index("group").loc[groups, "n_deposits"].to_numpy()
        rows = []
        for contrast, (a, b) in CONTRASTS.items():
            for pct in self.cfg["percentages"]:
                counts = rotation.pivot(index="group", columns="method", values=f"captured_deposits_at_{pct:02d}").loc[groups]
                delta = counts[a].to_numpy() - counts[b].to_numpy()
                bootstrap = 100 * delta[draws].sum(axis=1) / denominators[draws].sum(axis=1)
                rows.append({"contrast": contrast, "method_A": a, "method_B": b, "budget_percent": pct,
                    "captured_A": int(summary.loc[a, f"captured_{pct:02d}"]),
                    "captured_B": int(summary.loc[b, f"captured_{pct:02d}"]),
                    "delta_captured": int(delta.sum()), "delta_recovery_pp": float(100*delta.sum()/denominators.sum()),
                    "ci025_pp": float(np.quantile(bootstrap, .025)), "ci975_pp": float(np.quantile(bootstrap, .975)),
                    "delta_cv_auc": float(cv.loc[a, "roc_auc"]-cv.loc[b, "roc_auc"]),
                    "delta_cv_ap": float(cv.loc[a, "average_precision"]-cv.loc[b, "average_precision"])})
        table = pd.DataFrame(rows)
        table.to_csv(self.output / "factorial_contrasts.csv", index=False)
        return table

    def fit_national(self):
        frame = self.run_partition("national", 0, self.data.grid, self.data.positives.cell_id, self.data.grid.cell_id)
        frame.to_parquet(self.output / "favorabilidad_nacional_control_64_95.parquet", index=False)
        (self.output / "maps").mkdir(exist_ok=True)
        view = replace(self.data, output=self.output)
        for method in METHODS:
            write_raster(view, f"NB26_control_{method}_score", frame[method].to_numpy())
        relations = self.data.records.dropna(subset=["deposit_id"])[["cell_id", "deposit_id"]].drop_duplicates()
        metrics = []
        for method in METHODS:
            values, _, _ = deposit_metrics(relations, frame[["cell_id", method]].rename(columns={method: "score"}))
            metrics.append({"method": method, **values})
        summary = pd.DataFrame(metrics)
        summary.to_csv(self.output / "national_in_sample_metrics.csv", index=False)
        bundle = joblib.load(self.output / "partitions/national_0/model.joblib")
        gains = []
        for key, models in bundle.estimators.items():
            for member, model in enumerate(models):
                names = model.named_steps["preprocess"].get_feature_names_out()
                for name, gain in zip(names, model.named_steps["model"].booster_.feature_importance(importance_type="gain")):
                    gains.append({"component": key, "member": member, "feature": name, "gain": float(gain)})
        pd.DataFrame(gains).to_csv(self.output / "national_feature_gain.csv", index=False)
        self.log("Reentrenamiento nacional terminado: cuatro mapas, ocho componentes y modelos persistidos")
        return summary

    def validate(self):
        checks, fits = [], []
        def check(condition, message):
            if not bool(condition):
                raise AssertionError(message)
            checks.append(message)
        for name, digest in {**self.protected, **self.code}.items():
            check(sha256(self.root / name) == digest, f"Entrada/código intacto: {name}")
        import nbformat
        book = nbformat.read(self.root / NOTEBOOK, as_version=4)
        check(prefix_hash(book.cells[:self.history["historical_cell_count"]]) == self.history["prefix_sha256"],
              "Se conservan exactamente las celdas históricas y sus salidas")
        cv = pd.read_parquet(self.output / "cv_oof_predictions.parquet")
        check(cv.cell_id.is_unique and set(cv.cell_id) == set(self.sample.cell_id), "CV externo OOF completo y único")
        reference_dir = self.root / "reports/evaluacion_configuracion_nacional_20261021"
        reference_cv = pd.read_parquet(reference_dir / "cv_predictions.parquet")
        if "method" in reference_cv:
            reference_cv = reference_cv.loc[reference_cv.method.eq("national_recipe_8x150")]
        reference_score = reference_cv.set_index("cell_id")["score"]
        check(np.allclose(cv.global64, reference_score.loc[cv.cell_id], rtol=0, atol=1e-12),
              "global64 reproduce exactamente las predicciones CV de la receta nacional evaluada")
        summary = pd.read_csv(self.output / "cv_summary.csv").set_index("method")
        for method in METHODS:
            calculated = label_metrics(cv.label, cv[method], cv.cell_id)
            check(all(abs(value-summary.loc[method, name]) < 1e-12 for name, value in calculated.items()),
                  f"Métricas CV recalculadas: {method}")
        known = set(self.data.positives.cell_id)
        weights = self.data.positives.set_index("cell_id").peso_confianza
        reference_rotations = pd.read_parquet(reference_dir / "rotation_cell_predictions.parquet")
        for scope, count in [("cv", 5), ("rotation", 7), ("national", 1)]:
            for partition in range(count):
                folder = self.output / "partitions" / f"{scope}_{partition}"
                pred = pd.read_parquet(folder / "predictions.parquet")
                bundle = joblib.load(folder / "model.joblib")
                inner = pd.read_parquet(folder / "inner_predictions.parquet")
                roles = pd.read_parquet(folder / "inner_memberships.parquet")
                if scope == "cv":
                    outer_role = self.membership.loc[self.membership.fold.eq(partition)]
                    held = outer_role.loc[outer_role.role.eq("validation"), "cell_id"]
                    allowed = cv_training_pool(self.data, self.sample, self.membership, partition, self.old_design["reserved_blocks_excluded"])
                    train = self.sample.loc[self.sample.cell_id.isin(outer_role.loc[outer_role.role.eq("train"), "cell_id"])]
                elif scope == "rotation":
                    districts = set(self.groups.loc[self.groups.group.eq(partition), "district_id"])
                    allowed, territory = rotation_pools(self.data, districts)
                    held = territory.cell_id
                    train = pd.read_parquet(self.data.output / f"partitions/rotation_{partition}_sample.parquet")
                    reference = reference_rotations.loc[reference_rotations.partition.eq(partition)]
                    if "method" in reference:
                        reference = reference.loc[reference.method.eq("national_recipe_8x150")]
                    check(np.allclose(pred.global64, reference.set_index("cell_id").loc[pred.cell_id, "score"], rtol=0, atol=1e-12),
                          f"Receta original reproducida en rotación {partition}")
                else:
                    allowed, held, train = self.data.grid, pd.Series(dtype=str), self.data.positives.assign(label=1)
                expected_p = set(train.loc[train.label.eq(1), "cell_id"])
                check(set(inner.cell_id) <= set(allowed.cell_id), f"OOF interno contenido en entrenamiento {scope}/{partition}")
                if scope != "national":
                    check(not (set(inner.cell_id) & set(held)), f"Referencias CDF ajenas al test {scope}/{partition}")
                for key in bundle.normalizers:
                    rebuilt = BackgroundCDF().fit(inner.loc[inner.label.eq(0), key])
                    normalizer = bundle.normalizers[key]
                    check(rebuilt.available_ == normalizer.available_, f"Disponibilidad CDF: {scope}/{partition}/{key}")
                    if rebuilt.available_:
                        check(np.array_equal(rebuilt.x_, normalizer.x_) and np.array_equal(rebuilt.p_, normalizer.p_),
                              f"CDF solo con U internas: {scope}/{partition}/{key}")
                for path in sorted(folder.glob("training_*.parquet")):
                    level = path.stem.removeprefix("training_")
                    training = pd.read_parquet(path)
                    runs = pd.read_csv(folder / f"fits_{level}.csv")
                    fits.append(runs)
                    check(runs.groupby(["component", "member"]).features.apply(lambda x: sorted(x) == [64, 95]).all(),
                          f"Dos ajustes pareados 64/95 por muestra: {scope}/{partition}/{level}")
                    check(runs.groupby(["component", "member"]).ordered_sample_hash.nunique().eq(1).all(),
                          f"Mismo orden de filas 64/95: {scope}/{partition}/{level}")
                    excluded = set(held)
                    allowed_level = set(allowed.cell_id)
                    if level != "outer":
                        fold = int(level.removeprefix("inner_"))
                        test_ids = roles.loc[roles.fold.eq(fold) & roles.role.eq("validation"), "cell_id"]
                        excluded |= set(test_ids)
                        role_train = roles.loc[roles.fold.eq(fold) & roles.role.eq("train"), "cell_id"]
                        validation_roles = roles.loc[roles.role.eq("validation"), ["cell_id", "fold"]]
                        assigned = self.grid.loc[validation_roles.loc[validation_roles.fold.ne(fold), "cell_id"], "block_id"].unique()
                        allowed_level &= set(self.data.grid.loc[self.data.grid.block_id.isin(assigned), "cell_id"])
                        expected_level_p = set(role_train) & known
                        test_xy = self.grid.loc[test_ids, ["x_center", "y_center"]]
                    else:
                        expected_level_p = expected_p
                        test_xy = self.grid.loc[held, ["x_center", "y_center"]] if len(held) else None
                    for (component, member), sample in training.groupby(["component", "member"]):
                        p = sample.loc[sample.label.eq(1)]
                        u = sample.loc[sample.label.eq(0)]
                        check(sample.cell_id.is_unique, f"Muestra única {scope}/{partition}/{level}/{component}/{member}")
                        check(not (set(sample.cell_id) & excluded), "Ausencia de celdas de test en entrenamiento")
                        check(set(sample.cell_id) <= allowed_level, "Entrenamiento en los bloques autorizados")
                        check(len(u) == 3*len(p) and not (set(u.cell_id) & known), "U:P=3:1; ninguna P se usa como U")
                        target = expected_level_p
                        if component != "global":
                            flag = self.systems.set_index("cell_id")[component]
                            target = {v for v in target if flag.loc[v]}
                        check(set(p.cell_id) == target, "Todas las P autorizadas del componente están presentes")
                        check(np.array_equal(p.peso_confianza.to_numpy(), weights.loc[p.cell_id].to_numpy()), "Pesos P preservados")
                        if test_xy is not None:
                            distance = cKDTree(test_xy).query(self.grid.loc[sample.cell_id, ["x_center", "y_center"]])[0]
                            check((distance >= 15000).all(), "Buffer de 15 km verificado en las muestras reales")
                for n in [64, 95]:
                    for component in COMPONENTS:
                        for model in bundle.estimators[f"{component}{n}"]:
                            check(list(model.named_steps["preprocess"].feature_names_in_) == list(self.matrices[n]),
                                  f"Contrato real de {n} columnas, {component}")
                            check(("pathfinders_training_only" in model.named_steps) == (n == 95),
                                  "La base64 no utiliza variables extendidas ni pathfinders")
                ids = pred.cell_id.iloc[:17].tolist() + pred.cell_id.iloc[-17:].tolist()
                ids = list(dict.fromkeys(ids))
                matrices = {n: X.loc[ids] for n, X in self.matrices.items()}
                replay = bundle.combine(bundle.raw_predictions(matrices))
                for m in METHODS:
                    check(np.allclose(replay[m], pred.set_index("cell_id").loc[ids, m], rtol=0, atol=1e-12),
                          f"Modelo guardado reproduce {m} en {scope}/{partition}")
                single = bundle.predict({n: X.iloc[:1] for n, X in matrices.items()})
                check(np.allclose(single, replay.max3_64.iloc[:1], rtol=0, atol=1e-12), "Score independiente del lote de inferencia")
        all_fits = pd.concat(fits, ignore_index=True)
        all_fits.to_csv(self.output / "all_fits.csv", index=False)
        rotation = pd.read_csv(self.output / "rotation_summary.csv").set_index("method")
        details = pd.read_csv(self.output / "rotation_deposit_predictions.csv")
        for method in METHODS:
            sub = details.loc[details.method.eq(method)]
            check(sub.deposit_id.nunique() == 45, "45 depósitos únicos en las rotaciones")
            for pct in self.cfg["percentages"]:
                check(sub.loc[sub[f"captured_at_{pct:02d}"], "deposit_id"].nunique() == rotation.loc[method, f"captured_{pct:02d}"],
                      "Recuperación territorial recalculada")
        result = {"passed": True, "n_checks": len(checks), "n_actual_fits": len(all_fits),
            "n_national_fits": int((all_fits.scope.eq("national") & all_fits.level.eq("outer")).sum()),
            "original_global64_reproduced": True, "historical_cells_preserved": True, "checks": checks}
        write_json(self.output / "validation.json", result)
        self.log(f"Control validado: {len(checks)} comprobaciones; {len(all_fits)} ajustes reales")
        return {k: v for k, v in result.items() if k != "checks"}

    def make_figures(self):
        import matplotlib.pyplot as plt
        folder = self.output / "figuras"
        folder.mkdir(exist_ok=True)
        cv = pd.read_csv(self.output / "cv_summary.csv").set_index("method").loc[list(METHODS)]
        rotation = pd.read_csv(self.output / "rotation_summary.csv").set_index("method")
        random = pd.read_csv(self.output / "random_summary.csv")
        fig, axes = plt.subplots(1, 3, figsize=(16, 5))
        cv.roc_auc.plot.bar(ax=axes[0], ylim=(.5, 1), title="ROC-AUC · CV espacial")
        cv.average_precision.plot.bar(ax=axes[1], ylim=(.3, .9), title="Average Precision · CV espacial")
        for method in METHODS:
            axes[2].plot([1, 5, 10, 20], [rotation.loc[method, f"captured_{p:02d}"] for p in [1, 5, 10, 20]], marker="o", label=method)
        axes[2].plot(random.budget_percent, random.expected_deposits, "k--", label="Azar: esperanza exacta")
        axes[2].set(xlabel="Celdas priorizadas (%)", ylabel="Depósitos recuperados de 45", title="Rotaciones territoriales")
        axes[2].legend(fontsize=8)
        for ax in axes[:2]:
            ax.tick_params(axis="x", rotation=35)
        fig.tight_layout()
        path = folder / "control_factorial_64_95.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        return path

    def write_report(self):
        cv = pd.read_csv(self.output / "cv_summary.csv")
        rotation = pd.read_csv(self.output / "rotation_summary.csv")
        contrasts = pd.read_csv(self.output / "factorial_contrasts.csv")
        national = pd.read_csv(self.output / "national_in_sample_metrics.csv")
        validation = json.loads((self.output / "validation.json").read_text(encoding="utf-8"))
        principal = contrasts.loc[contrasts.contrast.eq("desacoplamiento_con_64") & contrasts.budget_percent.eq(5)].iloc[0]
        selected = ["method", "n_deposits", "captured_01", "captured_05", "captured_10", "captured_20"]
        text = f"""# Control factorial de NB26: base original64 y ampliada95

Fecha: 22/10/2026. Sección añadida al final de NB26 por petición expresa. Resultados realmente ejecutados.

## Resultado principal

Con 64 variables, desacoplar cambia la captura al 5% en **{int(principal.delta_captured):+d} depósitos de 45** frente al global original: {int(principal.captured_A)} frente a {int(principal.captured_B)}. Diferencia: {principal.delta_recovery_pp:+.2f} puntos porcentuales; intervalo exploratorio por grupos [{principal.ci025_pp:.2f}, {principal.ci975_pp:.2f}].

La comparación utiliza cuatro entrenamientos nuevos y emparejados. `global64` reproduce las predicciones de la receta nacional evaluada, no una aproximación con otros hiperparámetros. La complejidad de una matriz menor no garantiza por sí misma mejores resultados; se decide a partir de estos contrastes.

## Qué se compara

- `global64`: ocho miembros LightGBM con las 64 variables originales (56 numéricas y ocho clases geoquímicas).
- `max3_64`: el mismo global más especialistas primario no epitermal, aluvial y epitermal, todos con esas 64 variables; máximo de sus percentiles CDF aprendidos dentro del entrenamiento.
- `global95` y `max3_95`: los mismos procedimientos y muestras con la matriz corregida de 95 variables de NB27 (64 idénticas +31).
- El global conserva las 664 P, incluidas las 98 de sistema no resuelto. No se usan otras P como fondo U. Las etiquetas mixtas pueden participar en ambos especialistas documentados.

Se mantienen ocho miembros, U:P=3:1 sin reemplazo, pesos de confianza, semilla por partición y orden de filas iguales entre 64/95. El clasificador general reproduce la receta original: 150 árboles, profundidad5, 24 hojas, learning_rate0.04, colsample_bytree1.0. El pequeño especialista epitermal conserva la receta auditada de 80 árboles/profundidad3/8 hojas; solo hay cuatro P epitermales de Rodalquilar y puede estar ausente en un pliegue.

La matriz64 no calcula ni recibe pathfinders, magnetometría, gravimetría, MODIS o variables estructurales nuevas. Sus ocho clases del atlas siguen siendo categorías, presentes ya en la base original. En95, las estadísticas de pathfinders y toda imputación se ajustan en cada entrenamiento.

Este control no repite las etiquetas provinciales ni el min–max del territorio de prueba del NB26 histórico. Esos resultados previos permanecen como historial; las cifras nuevas deben compararse dentro del diseño pareado actual. También se elimina el cambio accidental de colsample_bytree y semillas entre algunos experimentos anteriores. No se atribuye una diferencia frente al NB26 antiguo solo al número de variables.

## CV espacial externa: cinco pliegues

{markdown_table(cv)}

OOF sobre la muestra P/U congelada de 2516 celdas (629P y1887U), bloques de50km y buffer de15km. Cada P evaluada se predice sin entrenar con ella. Las métricas P/U dependen del inventario y el muestreo de U; U no significa ausencia comprobada. El Brier de los percentiles max3 describe discriminación P/U, no calibración de una probabilidad de oro. `cv_cdf_diagnostic.csv` muestra por separado el efecto de normalizar el global en la métrica CV agrupada.

## Rotaciones de distritos: siete grupos, 45 depósitos

{markdown_table(rotation[selected])}

Se reservan los mismos grupos de distritos metalogenéticos operativos, sus bloques completos y15km adicionales. El modelo se ajusta fuera de esa reserva y puntúa todas sus celdas. Los presupuestos son ceil(N×porcentaje), con desempate por cell_id y un recuento por depósito. La referencia aleatoria contempla huellas multicelda y no presupone que un depósito equivalga a una celda:

{markdown_table(pd.read_csv(self.output / 'random_summary.csv'))}

## Contrastes que permiten atribuir los cambios

{markdown_table(contrasts)}

`desacoplamiento_con_64` aísla la estrategia en la base original; `desacoplamiento_con_95` la aísla en la ampliada. `variables_en_global` mide añadir31 variables al global y `variables_en_desacoplado` lo mide manteniendo el desacoplamiento. Son contrastes del procedimiento completo; no identifican cuál de las31 variables causa una diferencia.

El presupuesto principal predeclarado es5%; se muestran también1/10/20%. Los intervalos proceden de10000 remuestreos pareados de los siete grupos de rotación. Con pocos grupos y territorios reutilizados son exploratorios: no sustituyen una validación externa nueva ni demuestran descubrimientos.

## Reentrenamiento nacional

Se vuelven a ajustar todos los componentes con las664 P elegibles y U nacionales: **{validation['n_national_fits']} modelos finales**. Se guardan cuatro mapas y un bundle que permite inferencia y reproduce las predicciones. `max3_64` es el mapa experimental predeclarado para estudiar la base simplificada, sin promoción automática a la aplicación. El mapa servido por la app conserva sus artefactos originales.

Archivo nacional: `{self.output.relative_to(self.root).as_posix()}/favorabilidad_nacional_control_64_95.parquet`.
Modelo: `partitions/national_0/model.joblib`. Mapas: `maps/NB26_control_{{global64,max3_64,global95,max3_95}}_score.tif`.

Las siguientes recuperaciones nacionales son **in-sample**, porque incluyen depósitos usados para ajustar. No se presentan como validación:

{markdown_table(national)}

## Reproducibilidad

{validation['n_actual_fits']} ajustes reales en total; {validation['n_checks']} comprobaciones aprobadas. Se verifican muestras, pesos, buffers, etiquetas, CDF internas, contratos64/95, predicciones de modelos serializados y reproducción del global original en CV y las siete rotaciones. Los modelos guardados permiten cambiar el lote de inferencia sin cambiar el score.

Se mantienen las {self.history['historical_cell_count']} celdas originales de NB26, incluidas sus salidas. La copia byte a byte anterior a la ampliación está en `notebook26_original.ipynb`. El hash completo del notebook ampliado cambia de forma autorizada; los manifiestos de NB27/NB29 anteriores no se reescriben. Si un verificador histórico exige aquel hash completo, la copia preservada permite comprobarlo.

Para reproducir esta sección sin volver a ejecutar ni sobrescribir las salidas históricas: `.venv-fase-a/Scripts/python.exe scripts/append_control_64_nb26.py`. Las particiones ya completadas solo se reutilizan cuando sus hashes y diseño coinciden.

## Siguiente decisión

Evaluar la ganancia a un presupuesto de prospección útil junto con su estabilidad por territorio. Elegir una base de trabajo no equivale a declarar un ganador para descubrir nuevos indicios. La confirmación requiere observaciones prospectivas nuevas o un territorio externo que no haya intervenido en estas iteraciones.
"""
        path = self.report_dir / "INFORME_CONTROL_64_95.md"
        path.write_text(text, encoding="utf-8")
        return path

    def seal(self, report):
        write_json(self.output / "outputs_manifest.json", {p.relative_to(self.output).as_posix(): sha256(p)
            for p in sorted(self.output.rglob("*")) if p.is_file()
            and not p.is_relative_to(self.output / "runtime")
            and p.name not in {"outputs_manifest.json", "progress.log", "notebook_execution.json"}})
        self.log(f"Control NB26 ejecutado, reentrenado y sellado. Informe: {report}")
