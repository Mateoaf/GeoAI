"""Evaluate the national mapping recipe against frozen spatial holdouts.

The original experiment and its maps are read-only. Every national member gets
its own P/U sample and preprocessing, exactly as in run_maps. Positive training
cells and evaluation cells are paired with the historical Bagging PU experiment;
U samples are drawn from the admissible training territory, not from its small
historical U sample. This compares procedures, not a single hyperparameter.
"""

from __future__ import annotations

from datetime import datetime, timezone
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import sys
import time

import joblib
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from .geochemical_experiment import (
    cell_hash, label_metrics, load_data, make_model, predict, ranked_cells,
    rotation_pools, select_sample, sha256, spatial_splits, write_json,
)


REFERENCE = "bagging_pu_reference"
NATIONAL = "national_recipe_8x150"
PERCENTAGES = (1, 5, 10, 20)


def directory_hashes(directory):
    return {p.relative_to(directory).as_posix(): sha256(p)
            for p in sorted(directory.rglob("*")) if p.is_file()}


def cv_training_pool(data, sample, membership, fold, reserved_blocks):
    """Extend the frozen fold's training region to its unsampled U cells.

Blocks without a sampled cell have no historical fold assignment. They are
excluded from CV, rather than assigned to training by an arbitrary new rule.
The CV buffer is measured against validation samples, as in the reference.
"""
    validation_roles = membership.loc[membership.role.eq("validation"), ["cell_id", "fold"]]
    assigned = sample[["cell_id", "block_id"]].merge(validation_roles, validate="one_to_one")
    if assigned.groupby("block_id").fold.nunique().gt(1).any():
        raise ValueError("Un bloque tiene más de un pliegue de validación.")
    mapping = assigned.drop_duplicates("block_id").set_index("block_id").fold
    grid_folds = data.grid.block_id.map(mapping)
    pool = data.grid.loc[grid_folds.notna() & grid_folds.ne(fold)
                         & ~data.grid.block_id.isin(reserved_blocks)].copy()
    test_ids = membership.loc[membership.fold.eq(fold) & membership.role.eq("validation"), "cell_id"]
    test = sample.set_index("cell_id").loc[test_ids]
    distance = cKDTree(test[["x_center", "y_center"]]).query(pool[["x_center", "y_center"]])[0]
    return pool.loc[distance >= data.config["cv_buffer_m"]].copy()


def deposit_metrics(relations, predictions):
    """An exact cell budget and one count per deposit, without label-based ties."""
    if not predictions.cell_id.is_unique:
        raise ValueError("Celdas territoriales repetidas.")
    ranked = predictions.copy()
    ranked["rank"] = ranked_cells(ranked.cell_id, ranked.score)
    detail = relations.merge(ranked[["cell_id", "score", "rank"]], on="cell_id", how="left",
                             validate="many_to_one")
    if detail.empty or detail["rank"].isna().any():
        raise ValueError("Depósitos reservados sin predicción.")
    result = {"n_deposits": int(detail.deposit_id.nunique()), "n_held_cells": len(ranked)}
    for pct in PERCENTAGES:
        name = f"captured_at_{pct:02d}"
        detail[name] = detail["rank"] <= math.ceil(len(ranked) * pct / 100)
        count = int(detail.loc[detail[name], "deposit_id"].nunique())
        result[f"captured_deposits_at_{pct:02d}"] = count
        result[f"deposit_recovery_at_{pct:02d}"] = count / result["n_deposits"]
        result[f"recovery_at_{pct:02d}"] = count / result["n_deposits"]
    return result, detail, ranked


def fit_national_members(data, pool, evaluation_ids, expected_positive_ids, seed, scope,
                         partition, output, classifier_parameters):
    """Use the national per-member sampling, seeds, Pipeline and classifier."""
    evaluation_ids = pd.Index(evaluation_ids)
    expected_positive_ids = set(expected_positive_ids)
    pool_positive_ids = set(data.positives.loc[data.positives.cell_id.isin(pool.cell_id), "cell_id"])
    if pool_positive_ids != expected_positive_ids:
        raise AssertionError("Las P de entrenamiento difieren de la partición de referencia.")
    if set(pool.cell_id) & set(evaluation_ids):
        raise AssertionError("El territorio de entrenamiento incluye celdas de evaluación.")
    predictions = pd.DataFrame({"cell_id": evaluation_ids})
    training_frames, runs = [], []
    folder = output / "models" / f"{scope}_{partition}"
    folder.mkdir(parents=True, exist_ok=True)
    evaluation_features = data.features.loc[evaluation_ids, data.feature_columns]
    started = time.perf_counter()
    for member in range(data.config["national_bags"]):
        sample_seed = seed + 5000 + member * 101
        classifier_seed = seed + member
        sample = select_sample(data, pool.cell_id, sample_seed)
        if set(sample.loc[sample.label.eq(1), "cell_id"]) != expected_positive_ids:
            raise AssertionError("Un miembro no conserva las P autorizadas.")
        n_p, n_u = int(sample.label.sum()), int(sample.label.eq(0).sum())
        if n_u != data.config["u_per_p"] * n_p:
            raise AssertionError("No hay suficientes U para reproducir la receta nacional 1:3.")
        model = make_model(data.feature_columns, data.config["geochemical_columns"],
                           "lightgbm", data.config, classifier_seed)
        expected_parameters = dict(classifier_parameters, random_state=classifier_seed)
        if model.named_steps["model"].get_params() != expected_parameters:
            raise AssertionError("El clasificador no coincide con los modelos nacionales guardados.")
        model.fit(data.features.loc[sample.cell_id, data.feature_columns], sample.label,
                  model__sample_weight=sample.peso_confianza)
        predictions[f"member_{member:02d}"] = predict(model, evaluation_features,
                                                     data.config["prediction_batch_size"])
        joblib.dump(model, folder / f"member_{member:02d}.joblib", compress=3)
        training_frames.append(sample.assign(scope=scope, partition=partition, member=member))
        runs.append({"scope": scope, "partition": partition, "member": member,
                     "sample_seed": sample_seed, "classifier_seed": classifier_seed,
                     "n_P": n_p, "n_U": n_u, "training_ids_sha256": cell_hash(sample.cell_id),
                     "positive_ids_sha256": cell_hash(expected_positive_ids),
                     "pool_ids_sha256": cell_hash(pool.cell_id)})
    values = predictions.filter(regex="^member_").to_numpy()
    predictions["score"] = values.mean(axis=1)
    predictions["ensemble_std"] = values.std(axis=1)
    predictions["scope"], predictions["partition"] = scope, partition
    return predictions, pd.concat(training_frames, ignore_index=True), runs, time.perf_counter() - started


def verify_reference(data):
    base = data.output
    snapshot = json.loads((base / "config_snapshot.json").read_text(encoding="utf-8"))
    original = json.loads((base / "input_manifest.json").read_text(encoding="utf-8"))
    if data.config != snapshot:
        raise ValueError("La configuración actual difiere semánticamente de la evaluación original.")
    config_name = "config/geoquimica_20261017.yaml"
    differences = {name for name in set(original) | set(data.inputs)
                   if original.get(name) != data.inputs.get(name)}
    if differences - {config_name}:
        raise ValueError(f"Entradas originales modificadas: {sorted(differences)}")
    positives = pd.read_csv(base / "celdas_positivas.csv")
    pd.testing.assert_frame_equal(data.positives.reset_index(drop=True), positives,
                                  check_dtype=False)
    metadata = json.loads((base / "models/GeoAI/metadata.json").read_text(encoding="utf-8"))
    if (metadata["input_features"] != data.feature_columns
            or metadata["n_members"] != data.config["national_bags"]
            or metadata["u_per_p_each_member"] != data.config["u_per_p"]):
        raise ValueError("La receta actual no coincide con los metadatos nacionales.")
    parameters = None
    for member in range(metadata["n_members"]):
        saved = joblib.load(base / "models/GeoAI" / f"member_{member:02d}.joblib")
        actual = saved.named_steps["model"].get_params()
        expected = make_model(data.feature_columns, data.config["geochemical_columns"],
                              "lightgbm", data.config, data.config["seed"] + member)
        if actual != expected.named_steps["model"].get_params():
            raise ValueError(f"Parámetros nacionales discordantes: miembro {member}.")
        if member == 0:
            parameters = actual
    return parameters, {"config_semantics_match": True,
                        "config_bytes_match_historical_hash": config_name not in differences,
                        "scientific_input_hashes_match": True}


def validate_evaluation(data, output, replay=True):
    """Recalculate metrics and independently audit saved member memberships."""
    checks = []

    def check(condition, message):
        if not condition:
            raise AssertionError(message)
        checks.append(message)

    base = data.output
    design = json.loads((output / "evaluation_design.json").read_text(encoding="utf-8"))
    check(directory_hashes(base) == design["original_artifact_hashes"],
          "Todos los artefactos originales permanecen intactos")
    sample = pd.read_parquet(base / "partitions/benchmark_sample.parquet")
    membership = pd.read_parquet(base / "partitions/benchmark_memberships.parquet")
    training = pd.read_parquet(output / "member_training_cells.parquet")
    runs = pd.read_csv(output / "member_runs.csv")
    cv = pd.read_parquet(output / "cv_predictions.parquet")
    reference = pd.read_parquet(output / "reference_cv_predictions.parquet")
    territorial = pd.read_parquet(output / "rotation_cell_predictions.parquet")
    details = pd.read_csv(output / "rotation_deposit_predictions.csv")
    cv_summary = pd.read_csv(output / "cv_metrics.csv").set_index("model")
    rotation_summary = pd.read_csv(output / "rotation_summary.csv").set_index("model")
    grid = data.grid.set_index("cell_id")
    positive_weights = data.positives.set_index("cell_id").peso_confianza
    for code, frame in [(REFERENCE, reference), (NATIONAL, cv)]:
        check(frame.cell_id.is_unique and set(frame.cell_id) == set(sample.cell_id),
              f"OOF completo y único: {code}")
        check(np.array_equal(frame.set_index("cell_id").loc[sample.cell_id, "label"], sample.label),
              f"Etiquetas OOF originales: {code}")
        calculated = label_metrics(frame.label, frame.score, frame.cell_id)
        check(all(abs(value - cv_summary.loc[code, name]) < 1e-12
                  for name, value in calculated.items() if name in cv_summary.columns), f"Métricas OOF recalculadas: {code}")
        detail = details.loc[details.model.eq(code)]
        check(detail.deposit_id.nunique() == 45 and detail.groupby("deposit_id").group.nunique().eq(1).all(),
              f"45 depósitos, sin duplicación entre grupos: {code}")
        for pct in PERCENTAGES:
            col = f"captured_deposits_at_{pct:02d}"
            if col in rotation_summary.columns:
                count = detail.loc[detail[f"captured_at_{pct:02d}"], "deposit_id"].nunique()
                check(count == rotation_summary.loc[code, col],
                      f"Recuperación agregada recalculada: {code}/{pct}%")
    replayed = 0
    for (scope, partition), train_part in training.groupby(["scope", "partition"]):
        partition = int(partition)
        if scope == "cv":
            roles = membership.loc[membership.fold.eq(partition)]
            held_ids = roles.loc[roles.role.eq("validation"), "cell_id"]
            reference_train = sample.loc[sample.cell_id.isin(roles.loc[roles.role.eq("train"), "cell_id"])]
            predictions = cv.loc[cv.partition.eq(partition)].set_index("cell_id").loc[held_ids]
            buffer_m = data.config["cv_buffer_m"]
        else:
            held_ids = pd.read_parquet(base / f"partitions/rotation_{partition}_held.parquet").cell_id
            reference_train = pd.read_parquet(base / f"partitions/rotation_{partition}_sample.parquet")
            predictions = territorial.loc[territorial.partition.eq(partition)].set_index("cell_id").loc[held_ids]
            buffer_m = data.config["rotation_buffer_m"]
            relations = data.records.loc[data.records.district_id.isin(
                design["district_groups"][str(partition)])].dropna(subset=["deposit_id"])
            relations = relations[["cell_id", "deposit_id", "district_id"]].drop_duplicates()
            calculated, recalculated, _ = deposit_metrics(relations, predictions.reset_index())
            stored = details.loc[details.model.eq(NATIONAL) & details.group.eq(partition)]
            for pct in PERCENTAGES:
                cap_col = f"captured_at_{pct:02d}"
                if cap_col in stored.columns:
                    columns = ["cell_id", "deposit_id", cap_col]
                    pd.testing.assert_frame_equal(recalculated[columns].sort_values(columns[:2]).reset_index(drop=True),
                                                  stored[columns].sort_values(columns[:2]).reset_index(drop=True))
            checks.append(f"Ranking territorial y presupuestos exactos: grupo {partition}")
        expected_p = set(reference_train.loc[reference_train.label.eq(1), "cell_id"])
        check(set(train_part.member) == set(range(data.config["national_bags"])),
              f"Ocho miembros completos: {scope}/{partition}")
        check(np.allclose(predictions.filter(regex="^member_").mean(axis=1), predictions.score,
                          rtol=0, atol=1e-15), f"Media de ocho scores: {scope}/{partition}")
        tree = cKDTree(grid.loc[held_ids, ["x_center", "y_center"]])
        for member, member_train in train_part.groupby("member"):
            member = int(member)
            p = member_train.loc[member_train.label.eq(1)]
            u = member_train.loc[member_train.label.eq(0)]
            label = f"{scope}/{partition}/{member}"
            check(member_train.cell_id.is_unique and not set(member_train.cell_id) & set(held_ids),
                  f"Ninguna celda evaluada se entrena: {label}")
            check(set(p.cell_id) == expected_p and len(u) == 3 * len(p), f"P pareadas y U:P=3:1: {label}")
            check(not set(u.cell_id) & set(positive_weights.index), f"U sin presencias inventariadas: {label}")
            check(np.array_equal(p.peso_confianza, positive_weights.loc[p.cell_id])
                  and u.peso_confianza.eq(1).all(), f"Pesos originales: {label}")
            check(not set(grid.loc[member_train.cell_id].block_id) & set(grid.loc[held_ids].block_id),
                  f"Bloques separados: {label}")
            distances = tree.query(grid.loc[member_train.cell_id, ["x_center", "y_center"]])[0]
            check((distances >= buffer_m).all(), f"Buffer de 15 km: {label}")
            row = runs.loc[runs.scope.eq(scope) & runs.partition.eq(partition) & runs.member.eq(member)].iloc[0]
            check(cell_hash(member_train.cell_id) == row.training_ids_sha256, f"Hash de muestra: {label}")
            if replay:
                model = joblib.load(output / "models" / f"{scope}_{partition}" / f"member_{member:02d}.joblib")
                expected_parameters = dict(design["classifier_parameters"], random_state=int(row.classifier_seed))
                check(model.named_steps["model"].get_params() == expected_parameters,
                      f"Parámetros nacionales exactos: {label}")
                probe_ids = held_ids.iloc[np.linspace(0, len(held_ids)-1, min(64, len(held_ids)), dtype=int)]
                actual = predict(model, data.features.loc[probe_ids, data.feature_columns])
                check(np.allclose(actual, predictions.loc[probe_ids, f"member_{member:02d}"], rtol=0, atol=1e-12),
                      f"Predicciones reproducidas desde el modelo guardado: {label}")
                replayed += 1
    check(len(runs) == 96 and len(cv) == 2516, "96 ajustes y 2.516 predicciones OOF")
    check(directory_hashes(base) == design["original_artifact_hashes"], "Originales intactos tras validar")
    return {"passed": True, "n_checks": len(checks), "models_replayed": replayed, "checks": checks}


def create_report(data, output, report, cv_summary, rotation_summary, folds, rotation_rows):
    def markdown(frame):
        columns = list(frame.columns)
        lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
        for row in frame.itertuples(index=False, name=None):
            lines.append("| " + " | ".join(f"{v:.6f}" if isinstance(v, float) else str(v) for v in row) + " |")
        return "\n".join(lines)

    cv = cv_summary.set_index("model")
    rot = rotation_summary.set_index("model")
    delta_auc = cv.loc[NATIONAL, "roc_auc"] - cv.loc[REFERENCE, "roc_auc"]
    delta_ap = cv.loc[NATIONAL, "average_precision"] - cv.loc[REFERENCE, "average_precision"]
    report.parent.mkdir(parents=True, exist_ok=True)
    design = json.loads((output / "evaluation_design.json").read_text(encoding="utf-8"))
    text = f"""# Evaluación espacial de la configuración nacional GeoAI

Fecha: {design['date_local']}. Resultados calculados mediante nuevos entrenamientos; no son estimaciones.

## Resultado principal

Frente al Bagging PU de referencia, la receta nacional cambia ROC-AUC en {delta_auc:+.6f} y Average Precision en {delta_ap:+.6f}. Los resultados se refieren a etiquetas P/U y a la muestra espacial fija, no a probabilidades físicas de mineralización. No se ha realizado una prueba de significación estadística ni selección posterior de hiperparámetros.

## Procedimientos comparados

| Aspecto | Referencia | Receta nacional evaluada |
| --- | --- | --- |
| Miembros LightGBM | 5 | 8 |
| Árboles por miembro | 100 | 150 |
| U por P y miembro | Hasta 2, dentro de una muestra U común | 3, con muestra propia de cada miembro |
| Preprocesamiento | Compartido antes del remuestreo de miembros | Pipeline propio de cada miembro |
| reg_alpha | 0,4 | 0,5 |
| min_child_samples | 20 (valor del clasificador de referencia) | 10 |
| Celdas P de entrenamiento y pesos | Los de cada partición original | Exactamente las mismas P y pesos |

Se conserva la receta de `run_maps`: cada miembro utiliza `select_sample` sobre el territorio de entrenamiento permitido, crea un Pipeline LightGBM nuevo y ajusta su propio preprocesamiento. Se verifican los parámetros contra los ocho modelos nacionales ya guardados. La semilla base es 42 + número de pliegue/grupo; la muestra de cada miembro usa base + 5000 + 101 × miembro, y el clasificador base + miembro.

La comparación incluye el cambio de muestreo U del procedimiento nacional. No es una ablación que permita atribuir las diferencias solo al número de árboles o miembros. La referencia conserva sus predicciones originales; no se recalcula usando un fondo diferente.

## Cinco pliegues espaciales con buffer

Se reutilizan las mismas 629 P y 1.887 U de evaluación, los mismos pliegues y las reservas históricas, bloques de 50 km y buffer de 15 km respecto a las muestras de validación. Cada celda tiene una única predicción OOF. Las métricas globales se recalculan sobre esas predicciones reunidas, sin ponderar; no son una media simple de las métricas por pliegue.

Para los U de entrenamiento se utiliza el territorio admisible de los bloques de entrenamiento y se aplica el mismo buffer. Los {design['cv_unassigned_blocks']} bloques sin ninguna muestra en el benchmark original carecen de pliegue asignado y se excluyen de esta CV ({design['cv_unassigned_cells']} celdas, ninguna P). Así no se introduce una asignación territorial nueva. Todas las P de entrenamiento coinciden exactamente con las originales.

{markdown(cv_summary[['model', 'roc_auc', 'average_precision', 'brier_loss', 'positive_cell_recovery_at_05', 'positive_cell_recovery_at_10']])}

Brier se calcula contra las etiquetas P/U observadas; no mide calibración de presencia real de oro. Recovery en esta tabla se expresa como fracción de celdas P de la muestra, no como recuperación de depósitos. PR-AUC/AP es Average Precision; el área trapezoidal se exporta aparte.

{markdown(folds[['model', 'fold', 'n_training_P', 'validation_cells', 'roc_auc', 'average_precision']])}

## Siete rotaciones territoriales

Se reutilizan los siete grupos de distritos, los bloques reservados completos y el buffer de 15 km respecto a todas las celdas reservadas. Cada miembro se entrena con las P admisibles de la rotación y una muestra U propia del resto del territorio. Se puntúan todas las celdas de cada reserva. Se seleccionan exactamente ceil(porcentaje × número de celdas), con desempate por cell_id, y cada depósito se cuenta una vez.

{markdown(rotation_summary[[c for c in ['model', 'n_deposits', 'captured_deposits_at_01', 'captured_deposits_at_05', 'captured_deposits_at_10', 'captured_deposits_at_20', 'recovery_at_01', 'deposit_recovery_at_10', 'recovery_at_20'] if c in rotation_summary.columns]])}

{markdown(rotation_rows[[c for c in ['model', 'group', 'n_deposits', 'n_held_cells', 'captured_deposits_at_05', 'captured_deposits_at_10', 'captured_deposits_at_20', 'recovery_at_20'] if c in rotation_rows.columns]])}

Estas rotaciones comparten entrenamiento entre sí y usan inventario conocido. Evalúan transferencia territorial interna. Una campaña independiente seguiría siendo necesaria para comprobar utilidad prospectiva externa. La evaluación se ha definido después de conocer los resultados de referencia; esta comparación no constituye un test externo nuevo ni acredita una mejora universal.

## Integridad, salidas y reproducción

Los mapas, modelos y métricas originales permanecen intactos. La carpeta de esta evaluación conserva los 96 pipelines ajustados, las muestras de entrenamiento por miembro, las predicciones OOF, todas las predicciones territoriales, las métricas de ambos procedimientos, los hashes, el entorno y un informe de validación independiente con reproducción de predicciones desde los modelos guardados. No se genera ni sustituye un mapa nacional.

La configuración YAML actual es semánticamente idéntica a `config_snapshot.json`; su hash de bytes histórico {'coincide' if design['reference_integrity']['config_bytes_match_historical_hash'] else 'difiere (se acepta únicamente porque el contenido YAML coincide exactamente con la instantánea JSON)'}. Los hashes de las entradas científicas sí coinciden.

Resultados: `{output.relative_to(data.root).as_posix()}`.

Reproducir en una carpeta nueva:

```powershell
& .venv-fase-a/Scripts/python.exe scripts/evaluar_configuracion_nacional.py --output reports/evaluacion_nacional_repeticion --report informes/evaluacion_nacional_repeticion/INFORME.md
```

Validar nuevamente esta ejecución:

```powershell
& .venv-fase-a/Scripts/python.exe scripts/evaluar_configuracion_nacional.py --validate-only
```
"""
    report.write_text(text, encoding="utf-8")


def run_evaluation(root, output, report):
    root, output, report = Path(root).resolve(), Path(output).resolve(), Path(report).resolve()
    data = load_data(root)
    if output == data.output or output.is_relative_to(data.output):
        raise ValueError("La evaluación debe guardarse fuera de los resultados originales.")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("La carpeta de resultados no está vacía; utiliza una carpeta nueva.")
    parameters, integrity = verify_reference(data)
    original_hashes = directory_hashes(data.output)
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "control_ejecucion.json", {"status": "running"})
    base = data.output
    sample = pd.read_parquet(base / "partitions/benchmark_sample.parquet")
    membership = pd.read_parquet(base / "partitions/benchmark_memberships.parquet")
    historical_design = json.loads((base / "partitions/benchmark_design.json").read_text(encoding="utf-8"))
    # Verify that frozen memberships still reproduce the original splitter.
    for fold, parts in enumerate(spatial_splits(sample, data.config["cv_folds"], data.config["cv_buffer_m"], data.config["seed"])):
        for role, indices in zip(["train", "validation", "buffer_excluded"], parts):
            saved = membership.loc[membership.fold.eq(fold) & membership.role.eq(role), "cell_id"]
            if set(saved) != set(sample.iloc[indices].cell_id):
                raise AssertionError("Las pertenencias congeladas no reproducen el splitter original.")
    groups = pd.read_csv(base / "partitions/district_groups.csv")
    missing_blocks = set(data.grid.block_id) - set(sample.block_id) - set(historical_design["reserved_blocks_excluded"])
    design = {"date_local": "2026-10-21", "model_code": NATIONAL, "reference_code": REFERENCE,
              "n_members": data.config["national_bags"], "classifier_parameters": parameters,
              "config": data.config, "reference_integrity": integrity,
              "original_artifact_hashes": original_hashes,
              "cv_unassigned_blocks": len(missing_blocks),
              "cv_unassigned_cells": int(data.grid.block_id.isin(missing_blocks).sum()),
              "district_groups": {str(int(g)): frame.district_id.tolist() for g, frame in groups.groupby("group")},
              "comparison": "same training P and weights; same evaluation cells; national per-member U sampling from allowed territory",
              "absolute_probability": False, "uses_national_fitted_weights": False,
              "created_at_utc": datetime.now(timezone.utc).isoformat()}
    write_json(output / "evaluation_design.json", design)
    write_json(output / "environment.json", {"python": sys.version, "platform": platform.platform(),
        "packages": {p: importlib.metadata.version(p) for p in ["numpy", "pandas", "scipy", "scikit-learn", "lightgbm", "pyarrow", "joblib"]}})
    write_json(output / "input_manifest.json", data.inputs)
    code_paths = [root / "src/geoau/national_evaluation.py", root / "src/geoau/geochemical_experiment.py",
                  root / "scripts/evaluar_configuracion_nacional.py"]
    write_json(output / "code_manifest.json", {p.relative_to(root).as_posix(): sha256(p) for p in code_paths})
    source_oof = pd.read_parquet(base / "benchmark_oof_predictions.parquet")
    reference = source_oof.loc[source_oof.model.eq("bagging_pu")].copy()
    reference["model"] = REFERENCE
    reference.to_parquet(output / "reference_cv_predictions.parquet", index=False)
    baseline_cv = label_metrics(reference.label, reference.score, reference.cell_id)
    stored_cv = pd.read_csv(base / "benchmark_summary.csv").set_index("model").loc["bagging_pu"]
    if any(abs(baseline_cv[k] - stored_cv[k]) > 1e-12 for k in ["roc_auc", "average_precision"]):
        raise AssertionError("Las métricas de referencia no reproducen sus predicciones.")
    all_training, all_runs, cv_predictions, fold_rows = [], [], [], []
    for fold in range(data.config["cv_folds"]):
        roles = membership.loc[membership.fold.eq(fold)]
        test = sample.set_index("cell_id").loc[roles.loc[roles.role.eq("validation"), "cell_id"]].reset_index()
        reference_train = sample.loc[sample.cell_id.isin(roles.loc[roles.role.eq("train"), "cell_id"])]
        pool = cv_training_pool(data, sample, membership, fold, historical_design["reserved_blocks_excluded"])
        if not set(reference_train.cell_id) <= set(pool.cell_id):
            raise AssertionError("La región nacional no contiene el entrenamiento original.")
        p_ids = reference_train.loc[reference_train.label.eq(1), "cell_id"]
        predictions, training, runs, seconds = fit_national_members(data, pool, test.cell_id, p_ids,
            data.config["seed"] + fold, "cv", fold, output, parameters)
        predictions = predictions.merge(test[["cell_id", "label"]], validate="one_to_one")
        cv_predictions.append(predictions)
        all_training.append(training)
        all_runs.extend(runs)
        baseline = reference.set_index("cell_id").loc[test.cell_id]
        for code, scores in [(REFERENCE, baseline.score), (NATIONAL, predictions.score)]:
            fold_rows.append({"model": code, "fold": fold, "n_training_P": len(p_ids),
                "validation_cells": len(test), "training_positive_ids_sha256": cell_hash(p_ids),
                "validation_ids_sha256": cell_hash(test.cell_id),
                **label_metrics(test.label, scores, test.cell_id)})
        metric = label_metrics(predictions.label, predictions.score, predictions.cell_id)
        print(f"CV {fold+1}/5: P={len(p_ids)} AUC={metric['roc_auc']:.6f} AP={metric['average_precision']:.6f} ({seconds:.1f}s)", flush=True)
    cv = pd.concat(cv_predictions, ignore_index=True)
    cv["model"] = NATIONAL
    cv.to_parquet(output / "cv_predictions.parquet", index=False)
    cv_summary = pd.DataFrame([{"model": REFERENCE, **baseline_cv},
                               {"model": NATIONAL, **label_metrics(cv.label, cv.score, cv.cell_id)}])
    cv_summary.to_csv(output / "cv_metrics.csv", index=False)
    folds = pd.DataFrame(fold_rows)
    folds.to_csv(output / "cv_fold_metrics.csv", index=False)
    reference_rot = pd.read_csv(base / "rotation_metrics.csv")
    reference_rot = reference_rot.loc[reference_rot.model.eq("bagging_pu")].copy()
    reference_rot["model"] = REFERENCE
    reference_details = pd.read_csv(base / "rotation_deposit_predictions.csv")
    reference_details = reference_details.loc[reference_details.model.eq("bagging_pu")].copy()
    reference_details["model"] = REFERENCE
    if "captured_at_20" not in reference_details.columns:
        for g, group_df in reference_details.groupby("group"):
            n_held = reference_rot.loc[reference_rot.group.eq(g), "n_held_cells"].iloc[0]
            k20 = math.ceil(n_held * 20 / 100)
            reference_details.loc[reference_details.group.eq(g), "captured_at_20"] = reference_details.loc[reference_details.group.eq(g), "rank"] <= k20
            count20 = int(reference_details.loc[reference_details.group.eq(g) & reference_details.captured_at_20, "deposit_id"].nunique())
            n_deps = int(reference_rot.loc[reference_rot.group.eq(g), "n_deposits"].iloc[0])
            reference_rot.loc[reference_rot.group.eq(g), "captured_deposits_at_20"] = count20
            reference_rot.loc[reference_rot.group.eq(g), "deposit_recovery_at_20"] = count20 / n_deps
            reference_rot.loc[reference_rot.group.eq(g), "recovery_at_20"] = count20 / n_deps
        if "recovery_at_01" not in reference_rot.columns and "deposit_recovery_at_01" in reference_rot.columns:
            reference_rot["recovery_at_01"] = reference_rot["deposit_recovery_at_01"]
        if "recovery_at_10" not in reference_rot.columns and "deposit_recovery_at_10" in reference_rot.columns:
            reference_rot["recovery_at_10"] = reference_rot["deposit_recovery_at_10"]
    rotation_rows = reference_rot.to_dict("records")
    details, territorial_predictions = [reference_details], []
    for group, group_frame in groups.groupby("group", sort=True):
        group = int(group)
        pool, held = rotation_pools(data, set(group_frame.district_id))
        saved_held = pd.read_parquet(base / f"partitions/rotation_{group}_held.parquet")
        reference_train = pd.read_parquet(base / f"partitions/rotation_{group}_sample.parquet")
        reference_row = reference_rot.loc[reference_rot.group.eq(group)].iloc[0]
        if (set(held.cell_id) != set(saved_held.cell_id)
                or cell_hash(held.cell_id) != reference_row.held_ids_sha256
                or cell_hash(reference_train.cell_id) != reference_row.training_ids_sha256
                or not set(reference_train.cell_id) <= set(pool.cell_id)):
            raise AssertionError("La rotación no coincide con el territorio o muestra originales.")
        held = held.set_index("cell_id").loc[saved_held.cell_id].reset_index()
        p_ids = reference_train.loc[reference_train.label.eq(1), "cell_id"]
        predictions, training, runs, seconds = fit_national_members(data, pool, held.cell_id, p_ids,
            data.config["seed"] + group, "rotation", group, output, parameters)
        relations = data.records.loc[data.records.district_id.isin(group_frame.district_id)].dropna(subset=["deposit_id"])
        relations = relations[["cell_id", "deposit_id", "district_id"]].drop_duplicates()
        metrics, detail, ranked = deposit_metrics(relations, predictions)
        details.append(detail.assign(model=NATIONAL, group=group))
        territorial_predictions.append(ranked)
        rotation_rows.append({"model": NATIONAL, "group": group, "n_training_P": len(p_ids),
            "n_training_U_per_member": 3*len(p_ids), "held_ids_sha256": cell_hash(held.cell_id),
            "training_positive_ids_sha256": cell_hash(p_ids), "fit_predict_seconds": seconds, **metrics})
        all_training.append(training)
        all_runs.extend(runs)
        print(f"ROT {group+1}/7: P={len(p_ids)} dep@5={metrics['captured_deposits_at_05']}/{metrics['n_deposits']} dep@10={metrics['captured_deposits_at_10']}/{metrics['n_deposits']} ({seconds:.1f}s)", flush=True)
    detail = pd.concat(details, ignore_index=True)
    detail.to_csv(output / "rotation_deposit_predictions.csv", index=False)
    pd.concat(territorial_predictions, ignore_index=True).to_parquet(output / "rotation_cell_predictions.parquet", index=False)
    pd.concat(all_training, ignore_index=True).to_parquet(output / "member_training_cells.parquet", index=False)
    pd.DataFrame(all_runs).to_csv(output / "member_runs.csv", index=False)
    rotation_rows = pd.DataFrame(rotation_rows)
    rotation_rows.to_csv(output / "rotation_metrics.csv", index=False)
    summaries = []
    for code, frame in detail.groupby("model", sort=False):
        row = {"model": code, "n_deposits": int(frame.deposit_id.nunique())}
        for pct in PERCENTAGES:
            count = int(frame.loc[frame[f"captured_at_{pct:02d}"], "deposit_id"].nunique())
            row[f"captured_deposits_at_{pct:02d}"] = count
            row[f"deposit_recovery_at_{pct:02d}"] = count / row["n_deposits"]
            row[f"recovery_at_{pct:02d}"] = count / row["n_deposits"]
        summaries.append(row)
    rotation_summary = pd.DataFrame(summaries)
    rotation_summary.to_csv(output / "rotation_summary.csv", index=False)
    create_report(data, output, report, cv_summary, rotation_summary, folds, rotation_rows)
    validation = validate_evaluation(data, output)
    write_json(output / "validation.json", validation)
    write_json(output / "control_ejecucion.json", {"status": "complete", "models_fitted": len(all_runs),
        "validation_passed": True, "n_cv_predictions": len(cv), "n_rotations": 7,
        "report": report.relative_to(root).as_posix(), "report_sha256": sha256(report),
        "completed_at_utc": datetime.now(timezone.utc).isoformat()})
    write_json(output / "outputs_manifest.json", directory_hashes(output))
    print(cv_summary.to_string(index=False), flush=True)
    print(rotation_summary.to_string(index=False), flush=True)
    print(f"Validación: {validation['n_checks']} comprobaciones, {validation['models_replayed']} modelos reproducidos", flush=True)
    return output
