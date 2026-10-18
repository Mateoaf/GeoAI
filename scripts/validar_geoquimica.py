"""Comprueba particiones, métricas, notebooks y modelos de la rama geoquímica."""
from pathlib import Path
import json
import math
import sys

import joblib
import nbformat
import numpy as np
import pandas as pd
import rasterio
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from geoau.geochemical_experiment import load_data, sha256, label_metrics, predict
from geoau.validation_diagnostics import correct_scores
from geoau.model_fusion import FUSION, UNIFORM


def validate():
    data = load_data(ROOT)
    out = data.output
    checks = []

    def check(condition, message):
        if not condition:
            raise AssertionError(message)
        checks.append(message)

    control = json.loads((out / "control_ejecucion.json").read_text(encoding="utf-8"))
    check(control["status"] == "complete" and control["models_retrained"], "Ejecución completa con modelos reentrenados")
    original_inputs = json.loads((out / "input_manifest.json").read_text(encoding="utf-8"))
    check(data.inputs == original_inputs, "Entradas y configuración coinciden con los hashes registrados")
    manifest = json.loads((out / "outputs_manifest.json").read_text(encoding="utf-8"))
    for item in manifest:
        path = out / item["path"]
        check(path.is_file() and sha256(path) == item["sha256"], f"Integridad de {item['path']}")
    code_manifest = json.loads((out / "code_manifest.json").read_text(encoding="utf-8"))
    for path, digest in code_manifest.items():
        check(sha256(ROOT / path) == digest, f"Código registrado: {path}")
    summary = pd.read_csv(out / "benchmark_summary.csv")
    folds = pd.read_csv(out / "benchmark_folds.csv")
    check(len(summary) == 6 and len(folds) == 30, "Seis procedimientos por cinco pliegues, con 64 predictores")
    check(summary.sample_hash.nunique() == 1, "Muestra común de benchmark")
    check(folds.groupby("fold").training_ids_sha256.nunique().eq(1).all(), "Entrenamientos pareados en cada pliegue")
    check(folds.groupby("fold").validation_ids_sha256.nunique().eq(1).all(), "Validaciones pareadas en cada pliegue")
    sample = pd.read_parquet(out / "partitions/benchmark_sample.parquet")
    membership = pd.read_parquet(out / "partitions/benchmark_memberships.parquet")
    tested = membership.loc[membership.role.eq("validation")]
    check(tested.cell_id.is_unique and set(tested.cell_id) == set(sample.cell_id), "Cada muestra se predice fuera de pliegue exactamente una vez")
    grid = data.grid.set_index("cell_id")
    design = json.loads((out / "partitions/benchmark_design.json").read_text(encoding="utf-8"))
    check(not set(sample.block_id) & set(design["reserved_blocks_excluded"]), "Reserva histórica excluida del benchmark")
    for fold, frame in membership.groupby("fold"):
        tr = grid.loc[frame.loc[frame.role.eq("train"), "cell_id"]]
        va = grid.loc[frame.loc[frame.role.eq("validation"), "cell_id"]]
        check(not set(tr.block_id) & set(va.block_id), f"CV {fold}: bloques separados")
        distance = cKDTree(va[["x_center", "y_center"]]).query(tr[["x_center", "y_center"]])[0]
        check((distance >= data.config["cv_buffer_m"]).all(), f"CV {fold}: buffer de 15 km verificado")
    oof = pd.read_parquet(out / "benchmark_oof_predictions.parquet")
    for row in summary.itertuples():
        subset = oof.loc[oof.model.eq(row.model)]
        check(subset.cell_id.is_unique and len(subset) == len(sample), f"OOF completo {row.model}")
        metrics = label_metrics(subset.label, subset.score, subset.cell_id)
        check(abs(metrics["roc_auc"] - row.roc_auc) < 1e-12
              and abs(metrics["average_precision"] - row.average_precision) < 1e-12,
              f"Métricas recalculadas {row.model}")
    full_cv = pd.read_csv(out / "benchmark_cv_summary.csv")
    full_folds = pd.read_csv(out / "benchmark_cv_folds.csv")
    full_oof = pd.read_parquet(out / "benchmark_cv_oof.parquet")
    memberships = pd.read_parquet(out / "partitions/benchmark_cv_memberships.parquet")
    internal = pd.read_parquet(out / "partitions/benchmark_en_calibration_memberships.parquet")
    cal_predictions = pd.read_parquet(out / "benchmark_en_calibration_predictions.parquet")
    check(len(full_cv) == 18 and len(full_folds) == 90, "Tres estrategias por seis procedimientos por cinco pliegues")
    check(full_cv.n_input_features.eq(64).all() and full_cv.sample_hash.nunique() == 1,
          "Tres estrategias con las mismas 64 variables y muestra P/U")
    for row in full_cv.itertuples():
        subset = full_oof.loc[full_oof.strategy.eq(row.strategy) & full_oof.model.eq(row.model)]
        check(subset.cell_id.is_unique and set(subset.cell_id) == set(sample.cell_id),
              f"OOF completo {row.strategy}/{row.model}")
        calculated = label_metrics(subset.label, subset.score, subset.cell_id)
        check(all(abs(value - getattr(row, key)) < 1e-12 for key, value in calculated.items()),
              f"ROC, AP, área PR, Brier y recovery recalculados {row.strategy}/{row.model}")
        for pct in [5, 10]:
            maximum = min(1., math.ceil(len(sample) * pct / 100) / sample.label.sum())
            check(getattr(row, f"positive_cell_recovery_at_{pct:02d}") <= maximum + 1e-12,
                  f"Recovery respeta el presupuesto {row.strategy}/{row.model}/{pct}%")
    for (strategy, fold), roles in memberships.groupby(["strategy", "fold"]):
        fit = roles.loc[roles.role.eq("train"), "cell_id"]
        test = roles.loc[roles.role.eq("validation"), "cell_id"]
        check(not set(fit) & set(test), f"Test externo separado {strategy}/{fold}")
        if strategy != "random":
            check(not set(grid.loc[fit].block_id) & set(grid.loc[test].block_id),
                  f"Bloques externos separados {strategy}/{fold}")
        if strategy == "buffered":
            distances = cKDTree(grid.loc[test, ["x_center", "y_center"]]).query(grid.loc[fit, ["x_center", "y_center"]])[0]
            check((distances >= data.config["cv_buffer_m"]).all(), f"Buffer externo adicional verificado {strategy}/{fold}")
        inner = internal.loc[internal.strategy.eq(strategy) & internal.fold.eq(fold)]
        fit_inner = inner.loc[inner.role.eq("fit"), "cell_id"]
        cal_inner = inner.loc[inner.role.eq("calibration"), "cell_id"]
        check(set(inner.cell_id) == set(fit) and not set(fit_inner) & set(cal_inner),
              f"Calibración interna contenida en train y separada de ajuste {strategy}/{fold}")
        check(not set(cal_inner) & set(test), f"c no consulta el test externo {strategy}/{fold}")
        if strategy == "buffered":
            distances = cKDTree(grid.loc[cal_inner, ["x_center", "y_center"]]).query(grid.loc[fit_inner, ["x_center", "y_center"]])[0]
            check((distances >= data.config["cv_buffer_m"]).all(), f"Buffer interno de calibración {strategy}/{fold}")
        cal = cal_predictions.loc[cal_predictions.strategy.eq(strategy) & cal_predictions.fold.eq(fold)]
        check(set(cal.cell_id) <= set(cal_inner) and sample.set_index("cell_id").loc[cal.cell_id].label.eq(1).all(),
              f"c usa exclusivamente positivos reservados {strategy}/{fold}")
        recorded = full_folds.loc[full_folds.strategy.eq(strategy) & full_folds.fold.eq(fold)
                                 & full_folds.model.eq("bagging_pu_elkan_noto")].iloc[0]
        expected = cal.filter(regex="^member_").mean().to_numpy()
        actual = np.array(list(map(float, recorded.c_members.split(";"))))
        check(np.allclose(actual, expected, atol=1e-12), f"Factores c recalculados {strategy}/{fold}")
    propensity = json.loads((out / "propensity_catalog_summary.json").read_text(encoding="utf-8"))
    catalog_model = joblib.load(out / "models/catalog_elkan_noto.joblib")
    catalog_roles = pd.read_parquet(out / "partitions/propensity_catalog_memberships.parquet")
    catalog_positive_predictions = pd.read_csv(out / "propensity_catalog_positive_predictions.csv")
    fit_ids = set(catalog_roles.loc[catalog_roles.role.eq("fit"), "cell_id"])
    cal_ids = set(catalog_roles.loc[catalog_roles.role.eq("calibration"), "cell_id"])
    check(not fit_ids & cal_ids and not fit_ids & set(catalog_positive_predictions.cell_id),
          "Propensión del catálogo estimada fuera del ajuste")
    check(np.allclose(catalog_positive_predictions.filter(regex="^member_").mean(), catalog_model.c_members),
          "c del catálogo coincide con predicciones de positivos reservados")
    check(abs(propensity["c_mean"] - catalog_model.c_mean) < 1e-12
          and abs(propensity["inverse_c_mean"] - 1/catalog_model.c_mean) < 1e-12,
          "c y escala 1/c del catálogo verificados")
    examples = pd.read_csv(out / "propensity_catalog_score_examples.csv").head(64)
    member_scores = catalog_model.member_scores(data.features.loc[examples.cell_id, data.feature_columns])
    corrected = np.mean([correct_scores(member_scores[:, i], c) for i,c in enumerate(catalog_model.c_members)], axis=0)
    check(np.allclose(corrected, examples.en_score), "Corrección por miembro reproduce los ejemplos exportados")
    rotations = pd.read_csv(out / "rotation_metrics.csv")
    check(len(rotations) == 35, "Siete rotaciones de cinco procedimientos")
    check(rotations.groupby("group").training_ids_sha256.nunique().eq(1).all(), "Muestras de entrenamiento pareadas por rotación")
    check(rotations.groupby("group").held_ids_sha256.nunique().eq(1).all(), "Territorios reservados pareados por rotación")
    for group in range(7):
        train = pd.read_parquet(out / f"partitions/rotation_{group}_sample.parquet")
        held = pd.read_parquet(out / f"partitions/rotation_{group}_held.parquet")
        check(not set(train.cell_id) & set(held.cell_id), f"Rotación {group}: ninguna celda reservada se entrena")
        distance = cKDTree(grid.loc[held.cell_id, ["x_center", "y_center"]]).query(grid.loc[train.cell_id, ["x_center", "y_center"]])[0]
        check((distance >= data.config["rotation_buffer_m"]).all(), f"Rotación {group}: buffer territorial verificado")
    details = pd.read_csv(out / "rotation_deposit_predictions.csv")
    aggregated = pd.read_csv(out / "rotation_summary.csv")
    for row in aggregated.itertuples():
        frame = details.loc[details.model.eq(row.model)]
        check(frame.deposit_id.nunique() == row.n_deposits == 45, f"45 depósitos evaluados en {row.model}")
        check(frame.groupby("deposit_id").group.nunique().eq(1).all(), f"Un único grupo por depósito en {row.model}")
        for pct in [1, 5, 10]:
            captured = frame.loc[frame[f"captured_at_{pct:02d}"], "deposit_id"].nunique()
            check(captured == getattr(row, f"captured_deposits_at_{pct:02d}"),
                  f"Capturas agregadas {row.model}/{pct}%")
    rng = np.random.default_rng(123)
    indices = np.sort(rng.choice(len(data.grid), 128, replace=False))
    fusion_weights = pd.read_csv(out / 'fusion_weights.csv')
    fusion_inner = pd.read_parquet(out / 'fusion_inner_predictions.parquet')
    fusion_roles = pd.read_parquet(out / 'partitions/fusion_inner_memberships.parquet')
    searches = pd.read_csv(out / 'fusion_candidate_metrics.csv')
    component_predictions = pd.read_parquet(out / 'fusion_cv_component_predictions.parquet')
    families = data.config['fusion_components']
    for (scope,strategy,outer_fold), weight_frame in fusion_weights.groupby(['scope','strategy','outer_fold']):
        weights = weight_frame.set_index('component').loc[families,'weight'].to_numpy()
        check((weights>=0).all() and abs(weights.sum()-1)<1e-12, f'Pesos convexos {scope}/{strategy}/{outer_fold}')
        inner = fusion_inner.loc[fusion_inner.scope.eq(scope)&fusion_inner.strategy.eq(strategy)&fusion_inner.outer_fold.eq(outer_fold)]
        roles = fusion_roles.loc[fusion_roles.scope.eq(scope)&fusion_roles.strategy.eq(strategy)&fusion_roles.outer_fold.eq(outer_fold)]
        candidates = searches.loc[searches.scope.eq(scope)&searches.strategy.eq(strategy)&searches.outer_fold.eq(outer_fold)]
        inner_metrics = label_metrics(inner.label,inner[families].to_numpy()@weights,inner.cell_id)
        check(abs(inner_metrics['average_precision']-candidates.average_precision.max())<1e-12,
              f'Pesos elegidos por AP interna {scope}/{strategy}/{outer_fold}')
        if scope == 'cv':
            outer = memberships.loc[memberships.strategy.eq(strategy)&memberships.fold.eq(outer_fold)]
            outer_train = set(outer.loc[outer.role.eq('train'),'cell_id'])
            outer_test = set(outer.loc[outer.role.eq('validation'),'cell_id'])
        elif scope == 'rotation':
            outer_train = set(pd.read_parquet(out/f'partitions/rotation_{outer_fold}_sample.parquet').cell_id)
            outer_test = set(pd.read_parquet(out/f'partitions/rotation_{outer_fold}_held.parquet').cell_id)
        else:
            outer_train = set(pd.read_parquet(out/'partitions/fusion_national_sample.parquet').cell_id)
            outer_test = set()
        check(inner.cell_id.is_unique and set(inner.cell_id)==outer_train and not set(inner.cell_id)&outer_test,
              f'Selección sin celdas del test {scope}/{strategy}/{outer_fold}')
        for inner_fold, subroles in roles.groupby('inner_fold'):
            tr_ids = subroles.loc[subroles.role.eq('train'),'cell_id']
            va_ids = subroles.loc[subroles.role.eq('validation'),'cell_id']
            check(not set(tr_ids)&set(va_ids) and set(va_ids)==set(inner.loc[inner.inner_fold.eq(inner_fold),'cell_id']),
                  f'OOF interna sin ajuste sobre validación {scope}/{strategy}/{outer_fold}/{inner_fold}')
            if strategy == 'buffered':
                distances = cKDTree(grid.loc[va_ids,['x_center','y_center']]).query(grid.loc[tr_ids,['x_center','y_center']])[0]
                check((distances>=data.config['cv_buffer_m']).all(),f'Buffer interno fusión {scope}/{outer_fold}/{inner_fold}')
        if scope == 'cv':
            frame = component_predictions.loc[component_predictions.strategy.eq(strategy)&component_predictions.fold.eq(outer_fold)]
            for code, expected in [(FUSION,frame[families].to_numpy()@weights),(UNIFORM,frame[families].mean(axis=1).to_numpy())]:
                stored = full_oof.loc[full_oof.strategy.eq(strategy)&full_oof.model.eq(code)].set_index('cell_id').loc[frame.cell_id,'score']
                check(np.allclose(stored,expected,atol=1e-12),f'Fusión OOF reconstruida {code}/{strategy}/{outer_fold}')
    for folder,prefix in [('fusion','GeoAI_fusion'),('fusion_uniform','GeoAI_fusion_uniform')]:
        model = joblib.load(out/f'models/{folder}/model.joblib')
        frame = pd.read_parquet(out/f'maps/{prefix}_national.parquet')
        check(frame.cell_id.tolist()==data.grid.cell_id.tolist(),f'Dominio nacional de {folder}')
        predicted = predict(model,data.features[data.feature_columns].iloc[indices])
        check(np.allclose(predicted,frame.iloc[indices].favorability_mean,atol=1e-6),f'Modelo guardado reproduce mapa {folder}')
        matrix = model.member_scores(data.features[data.feature_columns].iloc[indices])
        disagreement = np.sqrt(np.square(matrix-predicted[:,None])@model.weights)
        check(np.allclose(disagreement,frame.iloc[indices].component_disagreement_std,atol=1e-6),f'Desacuerdo reproducible {folder}')
        with rasterio.open(out/f'maps/{prefix}_score.tif') as raster:
            values = raster.read(1,masked=True)
            check(raster.crs.to_epsg()==25830 and values.count()==len(frame)
                  and np.allclose(values[frame.row.to_numpy(),frame.col.to_numpy()],frame.favorability_mean),f'GeoTIFF de fusión coherente {folder}')
    for model_name in ["GeoAI"]:
        frame = pd.read_parquet(out / "maps" / f"{model_name}_national.parquet")
        check(frame.cell_id.tolist() == data.grid.cell_id.tolist() and len(frame) == 478443,
              f"Mismo dominio cartografiado: {model_name}")
        check(np.isfinite(frame[["favorability_mean", "ensemble_std", "novelty_distance"]].to_numpy()).all(),
              f"Salidas finitas en {model_name}")
        check(frame.favorability_mean.between(0, 1).all() and (frame.ensemble_std >= 0).all(), f"Escala de score y dispersión {model_name}")
        members = []
        X = data.features[data.feature_columns].iloc[indices]
        for member in range(data.config["national_bags"]):
            model = joblib.load(out / "models" / model_name / f"member_{member:02d}.joblib")
            members.append(predict(model, X))
        expected_mean = np.mean(members, axis=0)
        expected_std = np.std(members, axis=0)
        check(np.allclose(frame.iloc[indices].favorability_mean, expected_mean, atol=1e-6), f"Modelos guardados reproducen score {model_name}")
        check(np.allclose(frame.iloc[indices].ensemble_std, expected_std, atol=1e-6), f"Modelos guardados reproducen dispersión {model_name}")
        with rasterio.open(out / "maps" / f"{model_name}_score.tif") as raster:
            check(raster.crs.to_epsg() == 25830, f"CRS del GeoTIFF {model_name}")
            values = raster.read(1, masked=True)
            check(values.count() == len(frame), f"Máscara del GeoTIFF {model_name}")
            check(np.allclose(values[frame.row.to_numpy(), frame.col.to_numpy()], frame.favorability_mean),
                  f"GeoTIFF coincide con Parquet {model_name}")
    from actualizar_notebooks_geoquimica import NAMES, TAG
    for number, name in NAMES.items():
        nb = nbformat.read(ROOT / "notebooks" / name, as_version=4)
        nbformat.validate(nb)
        cells = [cell for cell in nb.cells if TAG in cell.metadata.get("tags", [])]
        check(bool(cells), f"Configuración integrada presente en notebook {number}")
        for cell in cells:
            if cell.cell_type == "code":
                check(cell.execution_count is not None and not any(output.output_type == "error" for output in cell.outputs),
                      f"Celda ejecutada sin errores en notebook {number}")
    check(summary.n_input_features.eq(64).all(), "Todos los algoritmos emplean las 64 variables")
    check(len(pd.read_csv(out / "cobertura_geoquimica.csv")) == 8, "Cobertura de los ocho elementos documentada")
    importance = pd.read_csv(out / "importancia_variables.csv")
    check(len(importance) == 64 and importance.variable.is_unique and abs(importance.mean_gain_fraction.sum() - 1) < 1e-10,
          "Importancias agregadas para las 64 variables y normalizadas por miembro")
    check(len(pd.read_csv(out / "importancia_geoquimica.csv")) == 8, "Importancia de los ocho elementos registrada")
    check(set(pd.read_csv(out / "leyendas_geoquimicas.csv").element.str.lower()) == {"as","sb","bi","hg","cu","pb","zn","w"}, "Leyendas de los ocho elementos")
    forbidden = ["base56", "geo59", "geo65_au", "delta_vs_base", "sin geoquímica", "Contenido de la etapa anterior"]
    for name in NAMES.values():
        raw = (ROOT / "notebooks" / name).read_text(encoding="utf-8")
        check(not any(value in raw for value in forbidden), f"Presentación única en {name}")
    for name in ["README.md", "MODEL_CARD.md", "DATA_CARD.md",
                 "informes/defensa_geoai_15_minutos_20261015/GEOAI_Guion_Defensa_15_Minutos.md",
                 "informes/defensa_geoai_15_minutos_20261015/GEOAI_Guion_Defensa_15_Minutos_Version_Breve.md",
                 "informes/geoquimica_20261017/INFORME_RESULTADOS_GEOQUIMICA.md"]:
        raw = (ROOT / name).read_text(encoding="utf-8")
        check(not any(value in raw for value in forbidden), f"Documentación unificada: {name}")
    for name in ["benchmark_summary.csv", "rotation_summary.csv", "variables_incluidas.csv", "maps/GeoAI_national.parquet"]:
        columns = pd.read_parquet(out / name).columns if name.endswith("parquet") else pd.read_csv(out / name, nrows=1).columns
        check("variant" not in columns and not any("delta" in column for column in columns), f"Esquema único sin diferencias entre variantes: {name}")
    result = {"status": "passed", "checks": len(checks), "unit_test_file": "tests/test_geochemical_experiment.py",
              "validation_checks": checks}
    (data.report / "VALIDACION_RESULTADOS.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": len(checks), "notebooks": len(NAMES)}, ensure_ascii=False))


if __name__ == "__main__":
    validate()
