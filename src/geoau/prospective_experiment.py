"""Executed NB29: paired feature ablations, national refits and prospective design."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import importlib.metadata
import json
import math
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
from scipy.spatial import cKDTree
from scipy.stats import hypergeom

from .controlled_system_experiment import ControlledExperiment, DEFAULT_CONFIG, markdown_table
from .controlled_system_models import BackgroundCDF, choose_weights
from .geochemical_experiment import load_data, sha256, cell_hash, write_json, label_metrics, rotation_pools
from .national_evaluation import cv_training_pool, deposit_metrics
from .prospective_features import NEW_FEATURES, FEATURE_PARAMETERS, add_descriptors, audit_sources, match_pilot
from .prospective_models import (COMPONENTS29, FAMILY29, NEW_METHODS29, REFERENCES29, METHODS29,
    SPECIALIST_FLAGS, component_columns, nested29)


def random_capture_counts(relations, population, budget, size, seed):
    """Exact random-cell null via multivariate hypergeometric signature counts.

    A signature encodes all deposits occupying a cell, preserving overlapping
    deposit footprints and the dependence induced by sampling without replacement.
    """
    rel = relations[["cell_id", "deposit_id"]].drop_duplicates()
    deposits = sorted(rel.deposit_id.unique())
    code = {v: i for i, v in enumerate(deposits)}
    signatures = Counter(tuple(sorted(code[v] for v in g.deposit_id)) for _, g in rel.groupby("cell_id"))
    patterns = list(signatures)
    covered = sum(signatures.values())
    if covered > population:
        raise ValueError("Las huellas superan el territorio.")
    colors = [population-covered]+[signatures[p] for p in patterns]
    incidence = np.zeros((len(colors), len(deposits)), dtype=np.int16)
    for i, pattern in enumerate(patterns, start=1):
        incidence[i, list(pattern)] = 1
    draws = np.random.default_rng(seed).multivariate_hypergeometric(colors, budget, size=size, method="marginals")
    return (((draws > 0).astype(np.int16) @ incidence) > 0).sum(axis=1).astype(np.int16)


class ProspectiveExperiment(ControlledExperiment):
    """Reuse the historical split implementation, never its fitted NB29 outputs."""
    def __init__(self, root, output="reports/reentrenamiento_nb29_descriptores_y_piloto_20261022"):
        self.root = Path(root).resolve()
        self.output = self.root / output
        self.report_dir = self.root / "informes" / self.output.name
        self.output.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.base = self.root / "reports/nb27_comparacion_controlada_20261022"
        self.data = load_data(self.root)
        self.grid = self.data.grid.set_index("cell_id")
        self.sample = pd.read_parquet(self.data.output / "partitions/benchmark_sample.parquet")
        self.membership = pd.read_parquet(self.data.output / "partitions/benchmark_memberships.parquet")
        self.old_design = json.loads((self.data.output / "partitions/benchmark_design.json").read_text(encoding="utf-8"))
        self.groups = pd.read_csv(self.data.output / "partitions/district_groups.csv")
        self.cfg = json.loads(json.dumps(DEFAULT_CONFIG))
        self.cfg.update(default_national_method="max3_97", null_simulations=20000, bootstrap_repeats=10000,
            pilot_triplets=12, pilot_known_buffer_m=15000., pilot_separation_m=10000., pilot_matching_radius_m=75000.,
            primary_endpoint="deposit_recovery_at_05", primary_contrast="max3_97 minus max3_95_ref")
        original = json.loads((self.base / "design.json").read_text(encoding="utf-8"))
        for name, digest in original["code_hashes"].items():
            if sha256(self.root / name) != digest:
                raise ValueError(f"Código del control NB27 modificado: {name}")
        old_environment = json.loads((self.base / "environment.json").read_text(encoding="utf-8"))
        packages = {p: importlib.metadata.version(p) for p in old_environment["packages"]}
        if packages != old_environment["packages"]:
            raise ValueError("El entorno difiere del control; reentrenar también el control antes de comparar.")
        manifest = json.loads((self.base / "outputs_manifest.json").read_text(encoding="utf-8"))
        for name, digest in manifest.items():
            if sha256(self.base / name) != digest:
                raise ValueError(f"Artefacto NB27 modificado: {name}")
        self.protected = self._protected29()
        sources = ["prospective_features.py", "prospective_models.py", "prospective_experiment.py",
                   "controlled_system_features.py", "controlled_system_models.py", "controlled_system_experiment.py",
                   "geochemical_experiment.py", "national_evaluation.py"]
        self.code = {f"src/geoau/{n}": sha256(self.root / "src/geoau" / n) for n in sources}
        self.code["scripts/build_notebook_29.py"] = sha256(self.root / "scripts/build_notebook_29.py")
        design = {"config": self.cfg, "feature_parameters": FEATURE_PARAMETERS, "code_hashes": self.code,
            "input_hashes": self.protected, "fixed_before_nb29_results": True, "external_test": False,
            "territories_previously_explored": True, "national_method_predeclared": "max3_97",
            "control": "NB27 frozen model outputs and exact member samples; identical environment and shared code",
            "ablations": {"mono96_aluvial": "95 + aluvial", "mono96_espectral": "95 + spectral", "mono97": "95 + both"},
            "uncertainty": "paired bootstrap of seven rotation groups; exploratory, not confirmatory",
            "new_independent_observations": False, "field_results_available": False, "date_local": "2026-10-22"}
        path = self.output / "design.json"
        if path.exists() and json.loads(path.read_text(encoding="utf-8")) != design:
            raise ValueError("Diseño/entradas/código cambiados: utilizar --output con otra carpeta.")
        write_json(path, design)
        write_json(self.output / "environment.json", {"python": sys.version, "packages": packages})
        self.log("NB29: diseño fijado; ablaciones reales, 5 CV, 7 rotaciones y ajuste nacional")

    def _protected29(self):
        paths = {self.root / n for n in self.data.inputs if n != "eligibility_column"}
        for folder in [self.base, self.root / "reports/reentrenamiento_nb28_sistemas_integrados_20261022",
                       self.data.output / "partitions"]:
            paths.update(p for p in folder.rglob("*") if p.is_file() and p.name != "progress.log")
        paths.update(self.root / "notebooks" / n for n in ["27_auditoria_sistemas_y_comparacion_controlada.ipynb",
            "28_sistemas_minerales_auditados_y_piloto_prospeccion.ipynb"])
        paths.update(self.root / self.data.config["phase_d_run"] / "dictionaries" / n for n in ["litologia.csv", "edades.csv"])
        paths.add(self.root / "cuaternariorecintos.gpkg")
        return {p.relative_to(self.root).as_posix(): sha256(p) for p in sorted(paths)}

    def prepare_features(self):
        baseline = pd.read_parquet(self.base / "X_nb27.parquet")
        if not baseline.index.equals(pd.Index(self.data.grid.cell_id, name="cell_id")):
            raise AssertionError("Índice de covariables distinto del territorio.")
        audit = audit_sources(self.data, baseline, self.output)
        self.X = add_descriptors(baseline)
        if self.X.shape != (len(self.grid), 97):
            raise AssertionError("Se requieren 95 columnas inalteradas + 2 descriptores.")
        pd.testing.assert_frame_equal(self.X.drop(columns=NEW_FEATURES), baseline)
        self.X.to_parquet(self.output / "X_nb29.parquet")
        self.X[NEW_FEATURES].describe().to_csv(self.output / "estadisticas_descriptores.csv")
        self.log(f"Matriz NB29: {len(self.X)} celdas y {len(self.X.columns)} variables; 95 originales idénticas")
        return audit

    def reference_predictions(self, scope, partition, ids):
        original = pd.read_parquet(self.base / "partitions" / f"{scope}_{partition}" / "predictions.parquet",
            columns=["cell_id"]+list(REFERENCES29.values())).set_index("cell_id")
        if set(original.index) != set(ids):
            raise AssertionError("El control no corresponde al territorio actual.")
        return original.loc[ids].rename(columns={v: k for k, v in REFERENCES29.items()})

    def run_partition(self, scope, partition, pool, expected_p, evaluation_ids):
        folder = self.output / "partitions" / f"{scope}_{partition}"
        folder.mkdir(parents=True, exist_ok=True)
        marker = folder / "complete.json"
        identity = {"evaluation_hash": cell_hash(evaluation_ids), "positive_hash": cell_hash(expected_p),
                    "pool_hash": cell_hash(pool.cell_id)}
        if marker.exists():
            saved = json.loads(marker.read_text(encoding="utf-8"))
            if any(saved[k] != v for k, v in identity.items()):
                raise ValueError("Partición guardada con otras muestras.")
            for name in ["predictions.parquet", "model.joblib"]:
                if sha256(folder / name) != saved[name]:
                    raise ValueError(f"Partición NB29 alterada: {folder.name}/{name}")
            self.log(f"Reutilizando NB29 completado: {scope}/{partition}")
            return pd.read_parquet(folder / "predictions.parquet")
        seed = self.cfg["seed"]+{"cv": 0, "rotation": 1000000, "national": 2000000}[scope]+10000*partition
        self.log(f"Iniciando {scope}/{partition}: {len(expected_p)} P; {len(evaluation_ids)} celdas de evaluación")
        frame = nested29(self, pool, expected_p, evaluation_ids, seed, folder, scope, partition)
        reference = self.reference_predictions(scope, partition, frame.cell_id)
        for c in REFERENCES29:
            frame[c] = reference[c].to_numpy()
        frame.to_parquet(folder / "predictions.parquet", index=False)
        write_json(marker, identity | {n: sha256(folder / n) for n in ["predictions.parquet", "model.joblib"]})
        return frame

    def evaluate_cv(self):
        frames, rows = [], []
        for fold in range(5):
            roles = self.membership.loc[self.membership.fold.eq(fold)]
            test = self.sample.set_index("cell_id").loc[roles.loc[roles.role.eq("validation"), "cell_id"]].reset_index()
            train = self.sample.loc[self.sample.cell_id.isin(roles.loc[roles.role.eq("train"), "cell_id"])]
            pool = cv_training_pool(self.data, self.sample, self.membership, fold, self.old_design["reserved_blocks_excluded"])
            frame = self.run_partition("cv", fold, pool, train.loc[train.label.eq(1), "cell_id"], test.cell_id)
            frame = frame.merge(test[["cell_id", "label"]], validate="one_to_one").assign(fold=fold)
            frames.append(frame)
            rows.extend({"method": m, "fold": fold, **label_metrics(frame.label, frame[m], frame.cell_id)} for m in METHODS29)
            pd.DataFrame(rows).to_csv(self.output / "cv_fold_metrics.csv", index=False)
            self.log(f"CV espacial {fold+1}/5 terminada")
        oof = pd.concat(frames, ignore_index=True)
        oof.to_parquet(self.output / "cv_oof_predictions.parquet", index=False)
        summary = pd.DataFrame([{"method": m, **label_metrics(oof.label, oof[m], oof.cell_id)} for m in METHODS29])
        summary.to_csv(self.output / "cv_summary.csv", index=False)
        return summary

    def evaluate_rotations(self):
        details, metrics, random_expectations = [], [], []
        simulations = {p: np.zeros(self.cfg["null_simulations"], dtype=np.int16) for p in self.cfg["percentages"]}
        for group, districts in self.groups.groupby("group"):
            group = int(group)
            pool, held = rotation_pools(self.data, set(districts.district_id))
            frozen = pd.read_parquet(self.data.output / f"partitions/rotation_{group}_held.parquet")
            train = pd.read_parquet(self.data.output / f"partitions/rotation_{group}_sample.parquet")
            if set(held.cell_id) != set(frozen.cell_id):
                raise AssertionError("Territorio reservado alterado.")
            frame = self.run_partition("rotation", group, pool, train.loc[train.label.eq(1), "cell_id"], frozen.cell_id)
            rel = self.data.records.loc[self.data.records.district_id.isin(districts.district_id)].dropna(subset=["deposit_id"])
            rel = rel[["cell_id", "deposit_id", "district_id"]].drop_duplicates()
            for method in METHODS29:
                values, detail, _ = deposit_metrics(rel, frame[["cell_id", method]].rename(columns={method: "score"}))
                metrics.append({"method": method, "group": group, **values})
                details.append(detail.assign(method=method, group=group))
            footprints = rel.groupby("deposit_id").cell_id.nunique().to_numpy()
            for p in self.cfg["percentages"]:
                k = math.ceil(len(held)*p/100)
                expected = float(hypergeom.sf(0, len(held), footprints, k).sum())
                random_expectations.append({"group": group, "budget_percent": p, "expected_deposits": expected})
                simulations[p] += random_capture_counts(rel, len(held), k, self.cfg["null_simulations"], 42000+100*p+group)
            pd.DataFrame(metrics).to_csv(self.output / "rotation_metrics.csv", index=False)
            self.log(f"Rotación territorial {group+1}/7 terminada; referencia aleatoria simulada")
        detail = pd.concat(details, ignore_index=True)
        detail.to_csv(self.output / "rotation_deposit_predictions.csv", index=False)
        rows = []
        for m, sub in detail.groupby("method", sort=False):
            row = {"method": m, "n_deposits": sub.deposit_id.nunique()}
            for p in self.cfg["percentages"]:
                n = sub.loc[sub[f"captured_at_{p:02d}"], "deposit_id"].nunique()
                row[f"captured_{p:02d}"] = n
                row[f"recovery_{p:02d}"] = n/row["n_deposits"]
            rows.append(row)
        summary = pd.DataFrame(rows)
        summary.to_csv(self.output / "rotation_summary.csv", index=False)
        expectations = pd.DataFrame(random_expectations)
        expectations.to_csv(self.output / "random_by_group.csv", index=False)
        exact = expectations.groupby("budget_percent").expected_deposits.sum()
        random_rows, tails = [], []
        for p, values in simulations.items():
            random_rows.append({"budget_percent": p, "expected_deposits": exact.loc[p], "simulation_mean": values.mean(),
                "null_q025": np.quantile(values, .025), "null_q975": np.quantile(values, .975),
                "simulation_standard_error": values.std(ddof=1)/np.sqrt(len(values))})
            for row in rows:
                observed = row[f"captured_{p:02d}"]
                tails.append({"method": row["method"], "budget_percent": p, "observed": observed,
                    "random_tail_mc": (1+int((values >= observed).sum()))/(len(values)+1),
                    "exploratory_unadjusted": True})
        pd.DataFrame({f"budget_{p:02d}": v for p, v in simulations.items()}).to_parquet(self.output / "random_null_simulations.parquet", index=False)
        pd.DataFrame(random_rows).to_csv(self.output / "random_summary.csv", index=False)
        pd.DataFrame(tails).to_csv(self.output / "random_tail_diagnostics.csv", index=False)
        self.paired_comparison(pd.DataFrame(metrics))
        return summary

    def paired_comparison(self, metrics):
        groups = sorted(metrics.group.unique())
        counts = metrics.loc[metrics.method.eq("mono95_ref")].set_index("group").loc[groups, "n_deposits"].to_numpy()
        draws = np.random.default_rng(29042).multinomial(len(groups), np.ones(len(groups))/len(groups), size=self.cfg["bootstrap_repeats"])
        contrasts = {"aluvial_vs_95": {"mono96_aluvial": 1, "mono95_ref": -1},
            "espectral_vs_95": {"mono96_espectral": 1, "mono95_ref": -1},
            "ambos_vs_95": {"mono97": 1, "mono95_ref": -1},
            "interaccion_descriptores": {"mono97": 1, "mono96_aluvial": -1, "mono96_espectral": -1, "mono95_ref": 1},
            "max97_vs_max95": {"max3_97": 1, "max3_95_ref": -1},
            "fusion97_vs_fusion95": {"fusion3_97": 1, "fusion3_95_ref": -1},
            "max97_vs_mono97": {"max3_97": 1, "mono97": -1}}
        rows = []
        for p in self.cfg["percentages"]:
            table = metrics.pivot(index="group", columns="method", values=f"captured_deposits_at_{p:02d}").loc[groups]
            for name, weights in contrasts.items():
                delta = sum(table[m].to_numpy()*w for m, w in weights.items())
                distribution = 100*(draws @ delta)/(draws @ counts)
                rows.append({"contrast": name, "budget_percent": p, "delta_captured": int(delta.sum()),
                    "delta_recovery_pp": 100*delta.sum()/counts.sum(), "ci025_pp": np.quantile(distribution, .025),
                    "ci975_pp": np.quantile(distribution, .975), "bootstrap_unit": "rotation_group", "n_clusters": len(groups)})
        pd.DataFrame(rows).to_csv(self.output / "paired_ablation_comparison.csv", index=False)

    def fit_national(self):
        frame = self.run_partition("national", 0, self.data.grid, self.data.positives.cell_id, self.data.grid.cell_id)
        frame.to_parquet(self.output / "favorabilidad_nacional_nb29.parquet", index=False)
        maps = self.output / "maps"
        maps.mkdir(exist_ok=True)
        spec = self.data.grid_spec
        for method in NEW_METHODS29:
            field = np.full((spec["height"], spec["width"]), -9999., dtype="float32")
            field[self.data.grid.row, self.data.grid.col] = frame.set_index("cell_id").loc[self.data.grid.cell_id, method]
            with rasterio.open(maps / f"NB29_{method}_score.tif", "w", driver="GTiff", height=spec["height"], width=spec["width"],
                count=1, dtype="float32", crs=spec["crs"], nodata=-9999., compress="deflate",
                transform=from_origin(spec["origin_x"], spec["origin_y"], 1000, 1000)) as raster:
                raster.write(field, 1)
                raster.update_tags(EXPERIMENT="NB29", METHOD=method, ABSOLUTE_PROBABILITY="false", IN_SAMPLE_MAP="true")
        relations = self.data.records.dropna(subset=["deposit_id"])[["cell_id", "deposit_id"]].drop_duplicates()
        summary = pd.DataFrame([{"method": m, **deposit_metrics(relations, frame[["cell_id", m]].rename(columns={m: "score"}))[0]} for m in METHODS29])
        summary.to_csv(self.output / "national_in_sample_metrics.csv", index=False)
        bundle = joblib.load(self.output / "partitions/national_0/model.joblib")
        importance = []
        for c, models in bundle.estimators.items():
            for member, model in enumerate(models):
                names = model.named_steps["preprocess"].get_feature_names_out()
                gain = model.named_steps["model"].booster_.feature_importance(importance_type="gain")
                importance.extend({"component": c, "member": member, "feature": n, "gain": float(g)} for n, g in zip(names, gain))
        pd.DataFrame(importance).to_csv(self.output / "national_feature_gain.csv", index=False)
        self.log("Reentrenamiento nacional real terminado; guardados modelos, cinco GeoTIFF y scores")
        return summary

    def prepare_pilot(self):
        national = pd.read_parquet(self.output / "favorabilidad_nacional_nb29.parquet", columns=["cell_id", "max3_97"]).set_index("cell_id")
        grid = self.data.grid.copy()
        grid["score"] = national.loc[grid.cell_id, "max3_97"].to_numpy()
        grid["percentile"] = grid.score.rank(method="average", pct=True)
        lithology = [n for n in self.X if n.startswith("litologia_u")]
        grid["substrate"] = self.X.loc[grid.cell_id, lithology].idxmax(axis=1).to_numpy()
        coverage = pd.read_csv(self.root / self.data.config["phase_c_run"] / "indicios_celda_cobertura.csv")
        all_grid = pd.read_parquet(self.root / self.data.config["phase_d_run"] / "calidad_y_soporte.parquet",
            columns=["cell_id", "x_center", "y_center"])
        known = all_grid.loc[all_grid.cell_id.isin(coverage.cell_id)].drop_duplicates("cell_id")
        grid["distance_known_cell_m"] = cKDTree(known[["x_center", "y_center"]]).query(grid[["x_center", "y_center"]])[0]
        candidates = grid.loc[~grid.cell_id.isin(coverage.cell_id) & grid.distance_known_cell_m.ge(self.cfg["pilot_known_buffer_m"])].copy()
        candidates.loc[candidates.percentile.ge(.995)].to_parquet(self.output / "pilot_high_candidate_pool.parquet", index=False)
        selected, rejections = match_pilot(candidates, target_pairs=self.cfg["pilot_triplets"],
            separation_m=self.cfg["pilot_separation_m"], radius_m=self.cfg["pilot_matching_radius_m"])
        if selected.empty:
            selected = pd.DataFrame(columns=list(candidates.columns)+["region", "stratum", "triplet_id"])
        selected["crs"] = "EPSG:25830"
        selected["field_outcome"] = "pendiente_de_campana"
        selected.to_csv(self.output / "pilot_matched_triplets.csv", index=False)
        rejections.to_csv(self.output / "pilot_rejections.csv", index=False)
        protocol = {"status": "local_design_only_no_field_results", "score_method": "max3_97", "requested_triplets": self.cfg["pilot_triplets"],
            "selected_triplets": int(selected.triplet_id.nunique()), "candidate_high_cells": int(candidates.percentile.ge(.995).sum()),
            "all_catalogue_records": len(coverage), "mapped_known_cells": len(known),
            "known_exclusion_m": self.cfg["pilot_known_buffer_m"], "minimum_intersite_m": self.cfg["pilot_separation_m"],
            "matching": "same dominant lithology and 100 km grid region; controls within 75 km of target",
            "strata": {"alta": [.995, 1.], "media": [.80, .85], "baja": [.20, .25]},
            "restrictions_relaxed": False, "unknown_is_not_unexplored": True,
            "distance_reference": "centers of all inventory cells, not exact occurrence coordinates",
            "outcome_predeclared": "presence of Au confirmed by independent blinded field/laboratory protocol, recorded before unblinding strata",
            "field_protocol": "same sampling effort per matched triplet; method and detection limit adapted to documented system and fixed before sampling; laboratory blanks, duplicates and controls; no low-score site assumed sterile",
            "catalogue_sha256": sha256(self.output / "pilot_matched_triplets.csv"), "created_utc": datetime.now(timezone.utc).isoformat()}
        write_json(self.output / "prospective_protocol.json", protocol)
        self.log(f"Piloto local preparado: {protocol['selected_triplets']} tripletes completos; sin relajar distancias")
        return protocol

    def validate(self):
        checks, all_runs = [], []
        def check(value, description):
            if not value:
                raise AssertionError(description)
            checks.append(description)
        check(self._protected29() == self.protected, "NB27, NB28 y todas las entradas previas intactas")
        baseline = pd.read_parquet(self.base / "X_nb27.parquet")
        check(self.X.drop(columns=NEW_FEATURES).equals(baseline), "95 columnas originales exactamente conservadas")
        check(add_descriptors(baseline)[NEW_FEATURES].equals(self.X[NEW_FEATURES]), "Descriptores recalculados sin etiquetas")
        cv = pd.read_parquet(self.output / "cv_oof_predictions.parquet")
        check(cv.cell_id.is_unique and set(cv.cell_id) == set(self.sample.cell_id), "OOF externo completo y único")
        summary = pd.read_csv(self.output / "cv_summary.csv").set_index("method")
        for m in METHODS29:
            expected = label_metrics(cv.label, cv[m], cv.cell_id)
            check(all(np.isclose(v, summary.loc[m, k], rtol=0, atol=1e-12) for k, v in expected.items()), f"Métricas CV recalculadas: {m}")
        flags = self.systems.set_index("cell_id")
        pweights = self.data.positives.set_index("cell_id").peso_confianza
        all_p = set(pweights.index)
        for scope, count in [("cv", 5), ("rotation", 7), ("national", 1)]:
            for partition in range(count):
                folder = self.output / "partitions" / f"{scope}_{partition}"
                old = self.base / "partitions" / f"{scope}_{partition}"
                pred = pd.read_parquet(folder / "predictions.parquet").set_index("cell_id")
                reference = self.reference_predictions(scope, partition, pred.index)
                check(pred[list(REFERENCES29)].equals(reference), f"Control NB27 sin alteraciones: {scope}/{partition}")
                bundle = joblib.load(folder / "model.joblib")
                inner = pd.read_parquet(folder / "inner_predictions.parquet")
                old_inner = pd.read_parquet(old / "inner_predictions.parquet")
                check(inner.cell_id.tolist() == old_inner.cell_id.tolist() and inner.inner_fold.tolist() == old_inner.inner_fold.tolist(),
                    f"Pliegues internos idénticos al control: {scope}/{partition}")
                check(inner.cell_id.is_unique and (scope == "national" or not set(inner.cell_id) & set(pred.index)),
                    f"OOF interno sin test externo: {scope}/{partition}")
                normalized = pd.read_parquet(folder / "inner_normalized_predictions.parquet")
                w, _ = choose_weights(inner.label, normalized[FAMILY29].to_numpy(), self.cfg["weight_step"])
                check(np.array_equal(w, bundle.weights) and w[0] >= .1 and abs(w.sum()-1) < 1e-12,
                    f"Pesos de fusión solo de entrenamiento interno: {scope}/{partition}")
                for c in COMPONENTS29:
                    expected_cdf = BackgroundCDF().fit(inner.loc[inner.label.eq(0), c])
                    actual = bundle.normalizers[c]
                    check(expected_cdf.available_ == actual.available_ and (not actual.available_ or
                        (np.array_equal(expected_cdf.x_, actual.x_) and np.array_equal(expected_cdf.p_, actual.p_))),
                        f"Normalizador solo de U OOF internas: {scope}/{partition}/{c}")
                for path in sorted(folder.glob("training_*.parquet")):
                    level = path.stem.removeprefix("training_")
                    train = pd.read_parquet(path)
                    old_train = pd.read_parquet(old / path.name)
                    runs = pd.read_csv(folder / f"fits_{level}.csv")
                    all_runs.append(runs)
                    if level.startswith("inner_"):
                        fold = int(level.split("_")[1])
                        evaluation = inner.loc[inner.inner_fold.eq(fold), "cell_id"]
                    else:
                        evaluation = pred.index
                    if scope != "national" or level != "outer":
                        unique = train.cell_id.drop_duplicates()
                        check(not set(unique) & set(evaluation), f"Sin evaluación en entrenamiento: {scope}/{partition}/{level}")
                        check(not set(self.grid.loc[unique].block_id) & set(self.grid.loc[evaluation].block_id), f"Bloques separados: {scope}/{partition}/{level}")
                        distance = cKDTree(self.grid.loc[evaluation, ["x_center", "y_center"]]).query(self.grid.loc[unique, ["x_center", "y_center"]])[0]
                        check((distance >= 15000).all(), f"Buffer espacial 15 km: {scope}/{partition}/{level}")
                    if scope != "national" and level.startswith("inner_"):
                        distance = cKDTree(self.grid.loc[pred.index, ["x_center", "y_center"]]).query(self.grid.loc[train.cell_id.drop_duplicates(), ["x_center", "y_center"]])[0]
                        check((distance >= 15000).all(), f"Test externo aislado también de ajustes internos: {scope}/{partition}/{level}")
                    for (c, member), rows in train.groupby(["component", "member"]):
                        ps, us = rows.loc[rows.label.eq(1)], rows.loc[rows.label.eq(0)]
                        check(rows.cell_id.is_unique and len(us) == 3*len(ps) and not set(us.cell_id) & all_p,
                            f"U:P=3:1 sin reemplazo y U sin P: {scope}/{partition}/{level}/{c}/{member}")
                        check(np.array_equal(ps.peso_confianza, pweights.loc[ps.cell_id]), f"Pesos documentales: {scope}/{partition}/{level}/{c}/{member}")
                        old_c = SPECIALIST_FLAGS.get(c, "mono95")
                        old_rows = old_train.loc[old_train.component.eq(old_c) & old_train.member.eq(member)]
                        check(rows.cell_id.tolist() == old_rows.cell_id.tolist() and rows.label.tolist() == old_rows.label.tolist(),
                            f"Muestras pareadas exactas con NB27: {scope}/{partition}/{level}/{c}/{member}")
                        if c in SPECIALIST_FLAGS:
                            check(flags.loc[ps.cell_id, SPECIALIST_FLAGS[c]].all(), f"P especialista documentadas: {scope}/{partition}/{level}/{c}/{member}")
                        recorded = runs.loc[runs.component.eq(c) & runs.member.eq(member)].iloc[0]
                        check(cell_hash(rows.cell_id) == recorded.sample_hash, f"Hash de entrenamiento: {scope}/{partition}/{level}/{c}/{member}")
                        if level == "outer":
                            model = bundle.estimators[c][int(member)]
                            columns = component_columns(self.X.columns, c)
                            check(recorded.n_features == len(columns) and list(model.named_steps["preprocess"].feature_names_in_) == columns,
                                f"96/97 variables realmente entrenadas: {scope}/{partition}/{c}/{member}")
                            derived = model.named_steps["derived_training_statistics"]
                            fx = self.X.loc[rows.cell_id, derived.columns_]
                            mu = fx.mean().fillna(0.)
                            sd = fx.std(ddof=0).replace(0., 1.).fillna(1.)
                            check(np.allclose(derived.mean_, mu, atol=1e-7) and np.allclose(derived.std_, sd, atol=1e-7),
                                f"Estadísticas aprendidas solo de su muestra: {scope}/{partition}/{c}/{member}")
                probe = pred.index[np.linspace(0, len(pred)-1, min(32, len(pred)), dtype=int)]
                raw, _ = bundle.predict_components(self.X.loc[probe])
                replay, _ = bundle.combine(raw)
                check(all(np.allclose(replay[m], pred.loc[probe, m], rtol=0, atol=1e-12) for m in NEW_METHODS29),
                    f"Predicciones reproducidas desde modelo guardado: {scope}/{partition}")
                singleton = bundle.predict(self.X.loc[probe[:1]])[0]
                check(abs(singleton-replay.max3_97.iloc[0]) < 1e-12, f"Inferencia invariante al lote: {scope}/{partition}")
        all_runs = pd.concat(all_runs, ignore_index=True)
        all_runs.to_csv(self.output / "all_fit_runs.csv", index=False)
        details = pd.read_csv(self.output / "rotation_deposit_predictions.csv")
        rotation = pd.read_csv(self.output / "rotation_summary.csv").set_index("method")
        for method in METHODS29:
            detail = details.loc[details.method.eq(method)]
            check(detail.deposit_id.nunique() == 45 and detail.groupby("deposit_id").group.nunique().eq(1).all(), f"45 depósitos únicos: {method}")
            for p in self.cfg["percentages"]:
                check(detail.loc[detail[f"captured_at_{p:02d}"], "deposit_id"].nunique() == rotation.loc[method, f"captured_{p:02d}"],
                    f"Recuperación territorial recalculada: {method}/{p}%")
        random = pd.read_csv(self.output / "random_summary.csv")
        check(((random.simulation_mean-random.expected_deposits).abs() <= 6*random.simulation_standard_error+1e-8).all(),
            "Simulación aleatoria compatible con esperanza hipergeométrica exacta")
        pilot = pd.read_csv(self.output / "pilot_matched_triplets.csv")
        if len(pilot):
            check(pilot.cell_id.is_unique and pilot.groupby("triplet_id").size().eq(3).all(), "Tripletes completos y sitios únicos")
            check(pilot.distance_known_cell_m.ge(self.cfg["pilot_known_buffer_m"]).all(), "Piloto alejado de todas las celdas inventariadas")
            coords = pilot[["x_center", "y_center"]].to_numpy()
            check(cKDTree(coords).query(coords, k=2)[0][:, 1].min() >= self.cfg["pilot_separation_m"], "Piloto con separación entre todos los sitios")
            check(pilot.groupby("triplet_id").substrate.nunique().eq(1).all() and pilot.groupby("triplet_id").region.nunique().eq(1).all(),
                "Controles emparejados por región y litología")
            for label, low, high in [("alta", .995, 1.), ("media", .8, .85), ("baja", .2, .25)]:
                check(pilot.loc[pilot.stratum.eq(label), "percentile"].between(low, high).all(), f"Estrato correcto: {label}")
        check(self._protected29() == self.protected, "Entradas y resultados previos intactos al finalizar")
        result = {"passed": True, "n_checks": len(checks), "actual_fits": len(all_runs), "bundles_replayed": 13,
            "field_validation_performed": False, "checks": checks}
        write_json(self.output / "validation.json", result)
        self.log(f"Validación NB29 superada: {len(checks)} comprobaciones; {len(all_runs)} ajustes nuevos")
        return {k: v for k, v in result.items() if k != "checks"}

    def make_figures(self):
        import matplotlib.pyplot as plt
        folder = self.output / "figuras"
        folder.mkdir(exist_ok=True)
        rotation = pd.read_csv(self.output / "rotation_summary.csv").set_index("method")
        random = pd.read_csv(self.output / "random_summary.csv")
        cv = pd.read_csv(self.output / "cv_summary.csv").set_index("method")
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        cv.average_precision.plot.bar(ax=axes[0], ylim=(0, 1), title="AP · CV espacial P/U")
        rotation.captured_05.plot.bar(ax=axes[1], title="Depósitos recuperados · Top 5%")
        axes[1].axhline(random.loc[random.budget_percent.eq(5), "expected_deposits"].iloc[0], color="black", linestyle="--")
        for method in ["mono95_ref", "mono97", "max3_95_ref", "max3_97", "fusion3_97", "regla_geologica_ref"]:
            axes[2].plot(self.cfg["percentages"], [rotation.loc[method, f"captured_{p:02d}"] for p in self.cfg["percentages"]], marker="o", label=method)
        axes[2].fill_between(random.budget_percent, random.null_q025, random.null_q975, color="grey", alpha=.2, label="Azar: intervalo nulo 95%")
        axes[2].plot(random.budget_percent, random.expected_deposits, "k--", label="Azar: esperanza exacta")
        axes[2].set(xlabel="Presupuesto de celdas (%)", ylabel="Depósitos de 45", title="Transferencia territorial exploratoria")
        axes[2].legend(fontsize=7)
        for ax in axes[:2]:
            ax.tick_params(axis="x", rotation=65)
        fig.tight_layout()
        fig.savefig(folder / "comparacion_nb29.png", dpi=150)
        plt.close(fig)
        national = pd.read_parquet(self.output / "favorabilidad_nacional_nb29.parquet").set_index("cell_id")
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        for ax, method in zip(axes.flat[:3], ["max3_95_ref", "max3_97", "mono97"]):
            field = np.full((self.data.grid_spec["height"], self.data.grid_spec["width"]), np.nan)
            field[self.data.grid.row, self.data.grid.col] = national.loc[self.data.grid.cell_id, method].rank(pct=True)
            im = ax.imshow(field, vmin=0, vmax=1, cmap="magma")
            ax.set_title(method+" · percentil nacional")
            fig.colorbar(im, ax=ax, shrink=.7)
        delta = national.max3_97.rank(pct=True)-national.max3_95_ref.rank(pct=True)
        field = np.full((self.data.grid_spec["height"], self.data.grid_spec["width"]), np.nan)
        field[self.data.grid.row, self.data.grid.col] = delta.loc[self.data.grid.cell_id]
        im = axes.flat[3].imshow(field, vmin=-.5, vmax=.5, cmap="RdBu_r")
        axes.flat[3].set_title("Cambio de percentil · max97 menos max95")
        fig.colorbar(im, ax=axes.flat[3], shrink=.7)
        for ax in axes.flat:
            ax.set_axis_off()
        fig.suptitle("Scores relativos; no probabilidades de encontrar oro")
        fig.tight_layout()
        fig.savefig(folder / "mapas_nb29.png", dpi=150)
        plt.close(fig)
        pilot = pd.read_csv(self.output / "pilot_matched_triplets.csv")
        fig, ax = plt.subplots(figsize=(9, 8))
        ax.scatter(self.data.grid.x_center/1000, self.data.grid.y_center/1000, s=.2, c="lightgrey", rasterized=True)
        if len(pilot):
            for label, color in [("alta", "red"), ("media", "orange"), ("baja", "blue")]:
                sub = pilot.loc[pilot.stratum.eq(label)]
                ax.scatter(sub.x_center/1000, sub.y_center/1000, label=label, c=color, s=22)
            ax.legend()
        ax.set(xlabel="UTM X (km)", ylabel="UTM Y (km)", title="Diseño de piloto emparejado; sin resultados de campo")
        ax.set_aspect("equal")
        fig.tight_layout()
        fig.savefig(folder / "piloto_nb29.png", dpi=150)
        plt.close(fig)
        return [folder / n for n in ["comparacion_nb29.png", "mapas_nb29.png", "piloto_nb29.png"]]

    def write_report(self):
        cv = pd.read_csv(self.output / "cv_summary.csv")
        rotation = pd.read_csv(self.output / "rotation_summary.csv")
        random = pd.read_csv(self.output / "random_summary.csv")
        paired = pd.read_csv(self.output / "paired_ablation_comparison.csv")
        primary = paired.loc[paired.contrast.eq("max97_vs_max95") & paired.budget_percent.eq(5)].iloc[0]
        protocol = json.loads((self.output / "prospective_protocol.json").read_text(encoding="utf-8"))
        validation = json.loads((self.output / "validation.json").read_text(encoding="utf-8"))
        weights = json.loads((self.output / "partitions/national_0/weights.json").read_text(encoding="utf-8"))
        conclusion = "El intervalo exploratorio incluye cero; no se demuestra una mejora consistente entre territorios." if primary.ci025_pp <= 0 <= primary.ci975_pp else "El intervalo exploratorio excluye cero; requiere confirmación en territorios o campaña nuevos por la reutilización del benchmark."
        text = f"""# NB29 · Descriptores corregidos, ablación y reentrenamiento real

Fecha local: 22 de octubre de 2026. Se ajustan modelos nuevos con 96/97 variables y se reutiliza únicamente el control NB27 verificado, con entorno, código común, particiones y muestras idénticos. Las salidas NB27/NB28 permanecen intactas. La versión nacional principal se fija como `max3_97` antes de obtener resultados; no se elige un ganador mirando el test.

## Qué se ha corregido

u000 no identifica terrazas: su leyenda es una unidad mixta de areniscas, conglomerados, arcillas, calizas y evaporitas. Se utiliza u012, gravas/conglomerados/arenas/limos, como contexto amplio. La fracción cuaternaria u004 es una copia exacta y no se duplica. El GPKG auxiliar tiene un único descriptor genérico y código geomorfológico 0; no permite acreditar terrazas y no se incorpora. Las fórmulas y constantes se fijan antes de entrenar en `contrato_descriptores_nb29.csv`. Son interacciones de covariables existentes, no nuevas mediciones.

El descriptor aluvial combina distancia a cauce, pendiente, u012 y TPI local. No se presenta como energía hidráulica ni como terraza observada. El espectral combina excesos de ratios MODIS con atenuación vegetal cuadrática; no se afirma adquisición Sentinel-2, QA nueva ni diagnóstico mineral. Los ausentes se conservan hasta la imputación de cada miembro. Pathfinder, medianas, escalas y categorías se ajustan con entrenamiento exclusivamente.

## Diseño y atribución

Muestra externa, cinco pliegues espaciales, siete reservas distritales y presupuestos 1/5/10/20% idénticos al control. Cada ajuste tiene ocho miembros y U:P=3:1 sin reemplazo. Las ablaciones `mono96_aluvial`, `mono96_espectral`, `mono97` comparten exactamente P/U, pesos e hiperparámetros con `mono95_ref`. Las ramas de 97 variables se comparan con los controles del mismo sistema y semillas. Los casos desconocidos permanecen en el global; epitermal se limita a cuatro celdas de dos depósitos documentados.

`max3_97` y `fusion3_97` agregan los mismos global97, primario_otro97, aluvial97 y epitermal97. Se conservan tres pliegues internos espaciales con buffer de 15 km para la CDF y selección de pesos por AP P/U. AP interna es un proxy de discriminación P/U, no optimización directa de recuperación por área. No se usan mínimos/máximos del test ni el factor 0,7.

### CV espacial P/U

{markdown_table(cv[['method','roc_auc','average_precision','positive_cell_recovery_at_05','positive_cell_recovery_at_10']])}

La muestra P/U no representa prevalencia nacional. Brier no acredita calibración física de los scores normalizados.

### Recuperación territorial

{markdown_table(rotation[['method','n_deposits','captured_01','captured_05','captured_10','captured_20']])}

### Referencia aleatoria e incertidumbre

{markdown_table(random)}

Se simulan 20.000 selecciones uniformes por presupuesto, conservando huellas multicelda y posibles celdas compartidas por depósitos mediante una hipergeométrica multivariante. Los intervalos nulos no son intervalos de confianza de la tasa de descubrimiento. Las colas Monte Carlo, guardadas por diagnóstico, son exploratorias y no se corrigen por búsqueda entre variantes.

Contraste principal predeclarado, max97 frente a max95 al 5%: **{int(primary.delta_captured):+d} depósitos**, diferencia de recuperación **{primary.delta_recovery_pp:+.2f} puntos porcentuales**, intervalo bootstrap pareado de siete grupos **[{primary.ci025_pp:.2f}, {primary.ci975_pp:.2f}]**. {conclusion}

{markdown_table(paired.loc[paired.budget_percent.eq(5)])}

Los grupos ya se observaron durante NB19–28. Esta evaluación es exploratoria; un buen resultado no convierte la reserva en una prueba externa nueva. Siete grupos aportan una incertidumbre estimada con limitaciones. El término interacción en la tabla es un contraste de resultados de algoritmos; no demuestra causalidad geológica.

## Ajuste nacional

Todos los modelos nuevos se reajustan con las {len(self.data.positives)} P elegibles. Se guardan miembros reales, pipelines, CDF, pesos y cinco GeoTIFF EPSG:25830, además de todos los controles. Modelo principal: `partitions/national_0/model.joblib`, método `max3_97`. Mapa principal: `maps/NB29_max3_97_score.tif`. La fusión aprendida nacional tiene estos pesos internos: {json.dumps(weights, ensure_ascii=False)}. Las recuperaciones nacionales en `national_in_sample_metrics.csv` son descriptivas y no validan descubrimientos.

## Piloto prospectivo local

Se han seleccionado **{protocol['selected_triplets']} tripletes completos** de un objetivo máximo de {protocol['requested_triplets']}. Cada triplete contiene alta prioridad (percentil >=99,5), control medio (80–85) y bajo (20–25), con la misma litología dominante y región de 100 km. Se exige >=15 km de todas las celdas del inventario de {protocol['all_catalogue_records']} registros y >=10 km entre todos los sitios; controles a <=75 km de su diana. No se relajan condiciones para completar la muestra. Pool de alta prioridad elegible: {protocol['candidate_high_cells']} celdas. Las coordenadas y distancias se refieren a centros de celda de 1 km.

El catálogo y protocolo se sellan localmente con SHA-256 antes del campo. No se presentan como registro público ni como campaña ejecutada. La ausencia en el inventario no prueba que una zona esté inexplorada; los controles bajos no se consideran estériles. Antes de muestrear deben fijarse el procedimiento y límite de detección apropiados a cada sistema, el mismo esfuerzo por triplete y la lectura independiente de resultados. No hay resultados nuevos de campo ni nuevas tasas de descubrimiento.

## Verificación

{validation['n_checks']} comprobaciones superadas; {validation['actual_fits']} ajustes nuevos registrados, 13 bundles reproducidos. Se revisan muestras pareadas con NB27, bloques, buffers internos y externos, tipologías, índices aprendidos, número real de columnas, pesos, CDF, métricas, lote de inferencia y distancias del piloto. Los artefactos originales permanecen intactos.

![Comparación](../../{self.output.relative_to(self.root).as_posix()}/figuras/comparacion_nb29.png)

![Mapas](../../{self.output.relative_to(self.root).as_posix()}/figuras/mapas_nb29.png)

![Piloto](../../{self.output.relative_to(self.root).as_posix()}/figuras/piloto_nb29.png)

Reproducir: `.venv-fase-a/Scripts/python.exe scripts/build_notebook_29.py`. Para otra ejecución completa usar `--output reports/nb29_repeticion`. Los checkpoints NB29 se reutilizan solo con diseño, código, entradas y hashes de modelo/predicciones coincidentes.
"""
        path = self.report_dir / "INFORME_NB29_DESCRIPTORES_Y_REENTRENAMIENTO.md"
        path.write_text(text, encoding="utf-8")
        return path

    def seal(self, report):
        write_json(self.output / "control_ejecucion.json", {"status": "complete", "validation_passed": True,
            "n_positive_cells": len(self.data.positives), "n_features": len(self.X.columns), "outer_cv_folds": 5,
            "rotations": 7, "bags": 8, "national_method": "max3_97", "external_validation": False,
            "report": report.relative_to(self.root).as_posix(), "report_sha256": sha256(report),
            "model_sha256": sha256(self.output / "partitions/national_0/model.joblib"), "completed_utc": datetime.now(timezone.utc).isoformat()})
        manifest = {p.relative_to(self.output).as_posix(): sha256(p) for p in self.output.rglob("*")
                    if p.is_file() and p.name not in ["outputs_manifest.json", "progress.log", "notebook_execution.json"]}
        write_json(self.output / "outputs_manifest.json", manifest)
        self.log("NB29 ejecutado, validado y sellado")
