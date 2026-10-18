"""Validación del sistema de 64 predictores y reescalado Elkan–Noto.

Referencia: https://cseweb.ucsd.edu/~elkan/posonly.pdf (sección 2).
La reserva para estimar c es interna al entrenamiento, nunca el test externo.
El diseño P/U muestreado y ponderado permite una lectura aparente de c;
no identifica la probabilidad real de registro en la población geológica.
"""
from __future__ import annotations

import time
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

from .geochemical_experiment import (
    ExperimentData, cell_hash, label_metrics, make_model, predict,
    select_sample, spatial_splits, write_json,
)

STRATEGY_NAMES = {
    "random": "Random CV",
    "spatial": "Spatial Block CV (0 km)",
    "buffered": "Buffered Spatial CV (15 km)",
}
MODEL_NAMES = {
    "logistic": "Regresión Logística L2",
    "random_forest": "Random Forest",
    "lightgbm": "LightGBM Regularizado",
    "bagging_pu_elkan_noto": "Bagging PU + Elkan–Noto",
    "heterogeneous_fusion": "Fusión heterogénea (pesos internos)",
    "heterogeneous_uniform": "Fusión heterogénea (media uniforme)",
}


def validation_splits(sample, strategy, cfg, seed):
    """Random estratificado o bloques idénticos con buffers de 0/15 km."""
    if strategy == "random":
        splitter = StratifiedKFold(n_splits=cfg["cv_folds"], shuffle=True, random_state=seed)
        return [(train, test, np.array([], dtype=int)) for train, test in splitter.split(sample, sample.label)]
    if strategy not in STRATEGY_NAMES:
        raise ValueError(f"Estrategia desconocida: {strategy}")
    buffer_m = cfg["cv_buffer_m"] if strategy == "buffered" else 0
    return spatial_splits(sample, cfg["cv_folds"], buffer_m, seed)


def calibration_partition(sample, strategy, cfg, seed):
    """Un pliegue interno para c; los restantes ajustan el clasificador."""
    inner = dict(cfg, cv_folds=cfg["en_calibration_folds"])
    return validation_splits(sample, strategy, inner, seed)[0]


def estimate_c(scores, minimum=1e-6):
    scores = np.asarray(scores, dtype=float)
    if scores.ndim != 1 or not len(scores) or not np.isfinite(scores).all():
        raise ValueError("La estimación de c exige positivos de calibración con scores finitos.")
    if (scores < 0).any() or (scores > 1).any():
        raise ValueError("Los scores para estimar c deben pertenecer a [0,1].")
    value = float(scores.mean())
    if not minimum <= value <= 1:
        raise ValueError("c es demasiado pequeño para un reescalado estable; revisar el ajuste.")
    return value


def correct_scores(scores, c):
    """Reescala y recorta; los empates resultantes no amplían el cupo de ranking."""
    if not np.isfinite(c) or not 0 < c <= 1:
        raise ValueError("c debe ser finito y pertenecer a (0,1].")
    return np.clip(np.asarray(scores, dtype=float) / c, 0., 1.)


class ElkanNotoEnsemble:
    """Pipeline PU ajustado sin la reserva de c; corrección por miembro."""
    def __init__(self, pipeline, c_members):
        self.pipeline = pipeline
        self.c_members = np.asarray(c_members, dtype=float)
        self.classes_ = np.array([0, 1])

    @property
    def c_mean(self):
        return float(self.c_members.mean())

    def member_scores(self, X):
        transformed = self.pipeline.named_steps["preprocess"].transform(X)
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="X does not have valid feature names")
            return np.column_stack([member.predict_proba(transformed)[:, 1]
                                    for member in self.pipeline.named_steps["model"].estimators_])

    def predict_proba(self, X):
        raw = self.member_scores(X)
        score = np.mean(np.clip(raw / self.c_members, 0., 1.), axis=1)
        return np.column_stack([1 - score, score])


def fit_elkan_noto(data, sample, strategy, seed):
    fit, calibration, excluded = calibration_partition(sample, strategy, data.config, seed + 10000)
    cal_positive = calibration[sample.iloc[calibration].label.to_numpy() == 1]
    if not len(cal_positive):
        raise ValueError("No hay positivos en la reserva interna para estimar c.")
    model = make_model(data.feature_columns, data.config["geochemical_columns"],
                       "bagging_pu", data.config, seed)
    X = data.features.loc[sample.cell_id, data.feature_columns]
    model.fit(X.iloc[fit], sample.iloc[fit].label,
              model__sample_weight=sample.iloc[fit].peso_confianza)
    wrapper = ElkanNotoEnsemble(model, np.ones(data.config["pu_bags"]))
    positive_scores = wrapper.member_scores(X.iloc[cal_positive])
    wrapper.c_members = np.array([estimate_c(positive_scores[:, i], data.config["en_c_min"])
                                 for i in range(positive_scores.shape[1])])
    memberships = pd.concat([
        pd.DataFrame({"cell_id": sample.iloc[indices].cell_id, "role": role})
        for indices, role in [(fit, "fit"), (calibration, "calibration"), (excluded, "buffer_excluded")]
    ], ignore_index=True)
    positive_predictions = pd.DataFrame({"cell_id": sample.iloc[cal_positive].cell_id.to_numpy(),
        **{f"member_{i:02d}": positive_scores[:, i] for i in range(positive_scores.shape[1])}})
    return wrapper, memberships, positive_predictions


def display_benchmark(summary):
    """La etiqueta PR-AUC conserva AP, como en la tabla solicitada."""
    summary = (summary.assign(_strategy_order=summary.strategy.map({name:i for i,name in enumerate(STRATEGY_NAMES)}),
                              _model_order=summary.model.map({name:i for i,name in enumerate(MODEL_NAMES)}))
               .sort_values(["_strategy_order", "_model_order"]).reset_index(drop=True))
    frame = pd.DataFrame({
        "Estrategia CV": summary.strategy.map(STRATEGY_NAMES),
        "Modelo": [MODEL_NAMES[row.model] + (f" (c={row.c_mean:.3f})" if row.model == "bagging_pu_elkan_noto" else "")
                   for row in summary.itertuples()],
        "ROC-AUC": summary.roc_auc,
        "PR-AUC": summary.average_precision,
        "Brier Loss": summary.brier_loss,
        "Recovery@5%": 100 * summary.positive_cell_recovery_at_05,
        "Recovery@10%": 100 * summary.positive_cell_recovery_at_10,
    })
    return frame.round({"ROC-AUC": 4, "PR-AUC": 4, "Brier Loss": 4,
                        "Recovery@5%": 2, "Recovery@10%": 2})


def run_diagnostics(data: ExperimentData):
    cfg, out = data.config, data.output
    sample = pd.read_parquet(out / "partitions/benchmark_sample.parquet")
    X = data.features.loc[sample.cell_id, data.feature_columns]
    families = ["logistic", "random_forest", "lightgbm", "bagging_pu_elkan_noto"]
    rows, fold_rows, predictions, memberships, inner_memberships, calibration_predictions = [], [], [], [], [], []
    for strategy in cfg["diagnostic_cv_strategies"]:
        splits = validation_splits(sample, strategy, cfg, cfg["seed"])
        for fold, (train, test, excluded) in enumerate(splits):
            for role, indices in [("train", train), ("validation", test), ("buffer_excluded", excluded)]:
                memberships.append(pd.DataFrame({"cell_id": sample.iloc[indices].cell_id,
                                                 "strategy": strategy, "fold": fold, "role": role}))
        for family in families:
            scores, raw_scores = np.full(len(sample), np.nan), np.full(len(sample), np.nan)
            factors = []
            for fold, (train, test, excluded) in enumerate(splits):
                started = time.perf_counter()
                c_members = []
                if family == "bagging_pu_elkan_noto":
                    training = sample.iloc[train].reset_index(drop=True)
                    model, inner, cal_predictions = fit_elkan_noto(data, training, strategy, cfg["seed"] + fold)
                    inner_memberships.append(inner.assign(strategy=strategy, fold=fold))
                    calibration_predictions.append(cal_predictions.assign(strategy=strategy, fold=fold))
                    c_members = model.c_members.tolist()
                    factors.extend(c_members)
                    matrix = model.member_scores(X.iloc[test])
                    raw_scores[test] = matrix.mean(axis=1)
                    scores[test] = np.clip(matrix / model.c_members, 0., 1.).mean(axis=1)
                else:
                    model = make_model(data.feature_columns, cfg["geochemical_columns"], family, cfg, cfg["seed"] + fold)
                    model.fit(X.iloc[train], sample.iloc[train].label,
                              model__sample_weight=sample.iloc[train].peso_confianza)
                    scores[test] = predict(model, X.iloc[test], cfg["prediction_batch_size"])
                    raw_scores[test] = scores[test]
                fold_rows.append({"strategy": strategy, "model": family, "fold": fold,
                    "train_cells": len(train), "validation_cells": len(test), "buffer_excluded": len(excluded),
                    "training_ids_sha256": cell_hash(sample.iloc[train].cell_id),
                    "validation_ids_sha256": cell_hash(sample.iloc[test].cell_id),
                    "c_mean": float(np.mean(c_members)) if c_members else np.nan,
                    "c_members": ";".join(map(str, c_members)),
                    "fit_predict_seconds": time.perf_counter() - started,
                    **label_metrics(sample.iloc[test].label, scores[test], sample.iloc[test].cell_id)})
            if not np.isfinite(scores).all():
                raise AssertionError("Predicciones incompletas fuera de pliegue.")
            rows.append({"strategy": strategy, "model": family, "n_input_features": len(data.feature_columns),
                "n_P": int(sample.label.sum()), "n_U": int(sample.label.eq(0).sum()),
                "sample_hash": cell_hash(sample.cell_id),
                "c_mean": float(np.mean(factors)) if factors else np.nan,
                "c_std": float(np.std(factors)) if factors else np.nan,
                "fraction_score_one": float(np.mean(scores >= 1)),
                **label_metrics(sample.label, scores, sample.cell_id)})
            predictions.append(sample[["cell_id", "label"]].assign(strategy=strategy, model=family,
                                                                      score=scores, raw_score=raw_scores))
            print(f"DIAGNOSTICS {strategy:8s} {family:24s} AUC={rows[-1]['roc_auc']:.4f}", flush=True)
    summary = pd.DataFrame(rows)
    summary.to_csv(out / "benchmark_cv_summary.csv", index=False)
    display_benchmark(summary).to_csv(out / "benchmark_cv_tabla.csv", index=False)
    pd.DataFrame(fold_rows).to_csv(out / "benchmark_cv_folds.csv", index=False)
    pd.concat(predictions, ignore_index=True).to_parquet(out / "benchmark_cv_oof.parquet", index=False)
    pd.concat(memberships, ignore_index=True).to_parquet(out / "partitions/benchmark_cv_memberships.parquet", index=False)
    pd.concat(inner_memberships, ignore_index=True).to_parquet(out / "partitions/benchmark_en_calibration_memberships.parquet", index=False)
    pd.concat(calibration_predictions, ignore_index=True).to_parquet(out / "benchmark_en_calibration_predictions.parquet", index=False)

    # A catalogue-wide diagnostic uses its own spatial reserve for c.
    catalog = select_sample(data, data.grid.cell_id, cfg["seed"] + 20000)
    model, roles, cal_predictions = fit_elkan_noto(data, catalog, "buffered", cfg["seed"] + 30000)
    joblib.dump(model, out / "models/catalog_elkan_noto.joblib", compress=3)
    catalog.to_parquet(out / "partitions/propensity_catalog_sample.parquet", index=False)
    roles.to_parquet(out / "partitions/propensity_catalog_memberships.parquet", index=False)
    cal_predictions.to_csv(out / "propensity_catalog_positive_predictions.csv", index=False)
    cal_ids = roles.loc[roles.role.eq("calibration"), "cell_id"]
    matrix = model.member_scores(data.features.loc[cal_ids, data.feature_columns])
    pd.DataFrame({"cell_id": cal_ids.to_numpy(), "raw_score": matrix.mean(axis=1),
                  "en_score": np.clip(matrix / model.c_members, 0., 1.).mean(axis=1)}).to_csv(
                      out / "propensity_catalog_score_examples.csv", index=False)
    result = {
        "method": "Elkan-Noto mean score on held-out positive cells; member-wise correction",
        "n_input_features": 64, "catalog_positive_cells": len(data.positives),
        "sample_P": int(catalog.label.sum()), "sample_U": int(catalog.label.eq(0).sum()),
        "fit_cells": int(roles.role.eq("fit").sum()), "calibration_cells": len(cal_ids),
        "calibration_positive_cells": len(cal_predictions),
        "c_members": model.c_members.tolist(), "c_mean": model.c_mean,
        "inverse_c_mean": 1 / model.c_mean, "mean_inverse_c": float(np.mean(1 / model.c_members)),
        "c_role": "apparent_rescaling_factor_under_PU_sampling_and_confidence_weights",
        "population_registration_probability_identified": False,
        "SCAR_verified": False, "calibration_excluded_from_fit": True,
        "applied_to_national_map": False,
        "scope": "catalogue diagnostic ensemble; national map retains its own raw relative-score pipelines",
        "reference": "https://cseweb.ucsd.edu/~elkan/posonly.pdf",
    }
    write_json(out / "propensity_catalog_summary.json", result)
    write_json(out / "benchmark_cv_design.json", {
        "n_input_features": 64, "strategies": STRATEGY_NAMES, "folds": cfg["cv_folds"],
        "sample_hash": cell_hash(sample.cell_id), "n_P": int(sample.label.sum()), "n_U": int(sample.label.eq(0).sum()),
        "PR_AUC_display_definition": "average_precision_score; trapezoidal area exported separately as pr_auc_trapezoid",
        "Brier_definition": "mean squared error against observed P/U labels, not latent geological labels",
        "Recovery_definition": "exact ceil(percent * n) cells; descending score then cell_id",
        "EN_calibration": "first internal fold; same random/block/buffer strategy; no outer test labels",
        "EN_prediction": "mean over members of clip(raw_member_score / c_member, 0, 1)",
        "national_map": "relative raw scores; the catalogue diagnostic factor is not transferred to different fitted models",
    })
    print(f"CATALOG c={model.c_mean:.6f}; 1/c={1/model.c_mean:.6f}", flush=True)
    return summary


def generate_diagnostic_report(data: ExperimentData):
    """Tabla de validación y estimación de propensión del catálogo."""
    import json
    from .geochemical_experiment import frame_markdown
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out, report = data.output, data.report
    summary = pd.read_csv(out / "benchmark_cv_summary.csv")
    catalog = json.loads((out / "propensity_catalog_summary.json").read_text(encoding="utf-8"))
    table = display_benchmark(summary)
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    for axis, column, title in zip(axes.flat,
            ["roc_auc", "average_precision", "brier_loss", "positive_cell_recovery_at_10"],
            ["ROC-AUC P/U", "PR-AUC (Average Precision)", "Brier frente a etiquetas P/U", "Recuperación P al 10 % de la muestra"]):
        pivot = summary.pivot(index="strategy", columns="model", values=column).reindex(list(STRATEGY_NAMES))
        pivot.rename(index=STRATEGY_NAMES, columns=MODEL_NAMES).plot.bar(ax=axis, rot=10, legend=False)
        axis.set(title=title, xlabel="", ylim=(0, 1))
        axis.tick_params(axis="x", labelsize=8)
        axis.grid(axis="y", alpha=.2)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3)
    fig.suptitle("GeoAI · 64 predictores con geoquímica · tres estrategias CV")
    fig.tight_layout(rect=(0, .09, 1, .96))
    fig.savefig(report / "figuras/validacion_tres_estrategias.png", dpi=150)
    plt.close(fig)
    c_table = summary.loc[summary.model.eq("bagging_pu_elkan_noto"), ["strategy", "c_mean", "c_std", "fraction_score_one"]].copy()
    c_table["strategy"] = c_table.strategy.map(STRATEGY_NAMES)
    text = f"""# GeoAI · Validación cruzada y factor de propensión aparente

El experimento emplea **64 predictores**, incluidas las clases geoquímicas As, Sb, Bi, Hg, Cu, Pb, Zn y W. Las tres estrategias comparten {int(summary.iloc[0].n_P)} P y {int(summary.iloc[0].n_U)} U, excluyendo los bloques de los distritos de reserva. Se ajustan cinco pliegues por estrategia.

## Factor c estimado sobre el catálogo

**c = {catalog['c_mean']:.6f}; escala de referencia 1/c = {catalog['inverse_c_mean']:.4f}×.**

El diagnóstico parte de las {catalog['catalog_positive_cells']} celdas P del catálogo elegible y {catalog['sample_U']} U. Reserva espacialmente {catalog['calibration_cells']} celdas, de las que {catalog['calibration_positive_cells']} son P, para estimar c. Ajusta con {catalog['fit_cells']} celdas, excluyendo la reserva y un buffer de 15 km. Las transformaciones se aprenden exclusivamente con el ajuste.

En cada miembro, **c_b = media de g_b(x) sobre positivos de la reserva interna**. Se calcula **q_b(x) = clip(g_b(x)/c_b, 0, 1)** y el ensamble promedia q_b. La c informada es la media de los cinco c_b. Su inversa resume una escala de referencia: con factores distintos y recorte no equivale a dividir la media del ensamble por una única constante.

El {100*catalog['c_mean']:.2f} % expresa el score medio aparente de los positivos reservados bajo este diseño P/U. Identificarlo con probabilidad de registro exige selección aleatoria de positivos (SCAR), un clasificador probabilístico adecuado y un muestreo compatible. Aquí U se muestrea y los positivos tienen pesos de confianza: el valor no acredita qué porcentaje del oro o de los depósitos reales está inventariado.

El factor del catálogo pertenece al ensamble diagnóstico guardado en models/catalog_elkan_noto.joblib. La cartografía conserva sus ocho pipelines de scores relativos; no se les aplica automáticamente el factor de otro ajuste. Los factores del benchmark se estiman dentro del entrenamiento de cada pliegue, sin consultar su test externo.

## Modelos y tres estrategias de validación

{frame_markdown(table)}

Random CV utiliza cinco pliegues estratificados. Spatial Block CV separa bloques de 50 km sin buffer. Buffered Spatial CV utiliza los mismos pliegues espaciales y retira muestras de entrenamiento a menos de 15 km de validación. Las tres estrategias emplean las mismas 64 variables.

Logística L2, Random Forest y LightGBM ajustan su Pipeline con todo el entrenamiento externo. Bagging PU + Elkan–Noto combina cinco LightGBM y reserva un pliegue interno para c con el mismo tipo de separación aleatoria o espacial de la estrategia. El test externo no participa en el ajuste ni en c; la reserva interna reduce la muestra efectiva del procedimiento PU.

## Interpretación de las métricas

- **ROC-AUC:** ordenación de etiquetas P/U sobre predicciones fuera de pliegue.
- **PR-AUC:** conserva la definición de la tabla solicitada, Average Precision calculada con average_precision_score. El área trapezoidal se exporta separadamente como pr_auc_trapezoid; son cálculos diferentes.
- **Brier Loss:** error cuadrático medio frente a etiquetas P/U. No evalúa calibración de mineralización real: U no es ausencia confirmada y la muestra tiene un ratio P/U definido por el experimento.
- **Recovery@5% y @10%:** porcentaje de celdas P recuperadas en un cupo exacto de ceil(porcentaje × celdas de la muestra). Los empates se resuelven por cell_id sin utilizar etiquetas. No mide depósitos ni superficie nacional.

El recorte en uno puede crear empates. Se exportan scores brutos y corregidos para inspeccionar el cálculo, manteniendo el presupuesto de selección.

## Factores c por estrategia

{frame_markdown(c_table)}

c_mean y c_std resumen los 25 factores de cinco miembros en cinco pliegues. fraction_score_one es la fracción de scores finales OOF iguales a uno. Ningún c utiliza los positivos del test externo.

![Resultados de validación](figuras/validacion_tres_estrategias.png)

## Reproducción

benchmark_cv_tabla.csv es la tabla de presentación; benchmark_cv_summary.csv conserva precisión completa y el área PR trapezoidal. benchmark_cv_folds.csv y benchmark_cv_oof.parquet permiten recalcular métricas. Se exportan las pertenencias externas e internas y las predicciones de los positivos usados para c. propensity_catalog_summary.json registra factores, tamaños y alcance; propensity_catalog_score_examples.csv muestra el reescalado. Ejecutar scripts/ejecutar_geoquimica.py --stage diagnostics y después --stage report.

Referencia: [Elkan y Noto (2008), sección 2](https://cseweb.ucsd.edu/~elkan/posonly.pdf).
"""
    (report / "INFORME_VALIDACION_CV_Y_PROPENSION.md").write_text(text, encoding="utf-8")
    for filename in ["benchmark_cv_tabla.csv", "benchmark_cv_summary.csv", "benchmark_cv_folds.csv",
                     "propensity_catalog_summary.json", "benchmark_cv_design.json"]:
        (report / "tablas" / filename).write_bytes((out / filename).read_bytes())
    return text
