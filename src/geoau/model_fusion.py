"""Fusión convexa de modelos con pesos aprendidos mediante CV interna.

Todos los componentes usan las mismas 64 entradas. La validación externa y
los depósitos reservados nunca intervienen en la selección de los pesos.
"""
from __future__ import annotations

import itertools
import json
import math
import time
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from .geochemical_experiment import (
    cell_hash, district_groups, label_metrics, make_model, predict, ranked_cells,
    rotation_pools, select_sample, write_json, write_raster,
)
from .validation_diagnostics import display_benchmark, validation_splits

FUSION = "heterogeneous_fusion"
UNIFORM = "heterogeneous_uniform"


def weight_candidates(n_components, step=.1):
    divisions = int(round(1 / step))
    if n_components < 2 or not np.isclose(divisions * step, 1):
        raise ValueError("La rejilla de pesos debe dividir exactamente la unidad.")
    rows = [np.full(n_components, 1 / n_components)]
    rows += [np.asarray(values, dtype=float) / divisions
             for values in itertools.product(range(divisions + 1), repeat=n_components)
             if sum(values) == divisions]
    return np.unique(np.asarray(rows), axis=0)


def select_fusion_weights(y, component_scores, step=.1):
    """Selecciona AP interna; los empates favorecen pesos próximos a la media."""
    scores, y = np.asarray(component_scores, dtype=float), np.asarray(y)
    if scores.ndim != 2 or scores.shape[0] != len(y) or not np.isfinite(scores).all():
        raise ValueError("Predicciones internas incompletas para seleccionar pesos.")
    if len(np.unique(y)) != 2 or (scores < 0).any() or (scores > 1).any():
        raise ValueError("Se requieren ambas etiquetas y scores en [0,1].")
    candidates = weight_candidates(scores.shape[1], step)
    rows = []
    for weights in candidates:
        ap = float(average_precision_score(y, scores @ weights))
        concentration = float(np.square(weights - 1 / scores.shape[1]).sum())
        rows.append((ap, concentration))
    best = min(range(len(rows)), key=lambda i: (-round(rows[i][0], 12), rows[i][1], tuple(candidates[i])))
    return candidates[best], pd.DataFrame({
        "weights": [json.dumps(weights.tolist()) for weights in candidates],
        "average_precision": [row[0] for row in rows],
        "selected": np.arange(len(rows)) == best,
    })


class HeterogeneousFusion:
    """Media ponderada de scores P/U; los pesos pueden anular un componente."""
    def __init__(self, components, weights, feature_columns):
        self.components = dict(components)
        self.weights = np.asarray(weights, dtype=float)
        self.feature_columns = list(feature_columns)
        if (len(self.components) != len(self.weights) or not np.isfinite(self.weights).all()
                or (self.weights < 0).any() or not np.isclose(self.weights.sum(), 1)):
            raise ValueError("Los pesos deben ser finitos, no negativos y sumar uno.")
        self.classes_ = np.array([0, 1])

    def member_scores(self, X):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="X does not have valid feature names")
            return np.column_stack([model.predict_proba(X[self.feature_columns])[:, 1]
                                    for model in self.components.values()])

    def predict_proba(self, X):
        score = self.member_scores(X) @ self.weights
        return np.column_stack([1 - score, score])


def fit_fusion(data, sample, strategy, seed):
    cfg = data.config
    families = cfg["fusion_components"]
    if cfg["fusion_selection_metric"] != "average_precision":
        raise ValueError("La selección de fusión está fijada a Average Precision interna.")
    inner_cfg = dict(cfg, cv_folds=cfg["fusion_inner_folds"])
    splits = validation_splits(sample, strategy, inner_cfg, seed + 40000)
    X = data.features.loc[sample.cell_id, data.feature_columns]
    scores = np.full((len(sample), len(families)), np.nan)
    roles, fold_of = [], np.full(len(sample), -1, dtype=int)
    for fold, (train, validation, excluded) in enumerate(splits):
        fold_of[validation] = fold
        for role, indices in [("train", train), ("validation", validation), ("buffer_excluded", excluded)]:
            roles.append(pd.DataFrame({"cell_id": sample.iloc[indices].cell_id,
                                       "inner_fold": fold, "role": role}))
        for column, family in enumerate(families):
            model = make_model(data.feature_columns, cfg["geochemical_columns"], family, cfg, seed + 100 + fold)
            model.fit(X.iloc[train], sample.iloc[train].label,
                      model__sample_weight=sample.iloc[train].peso_confianza)
            scores[validation, column] = predict(model, X.iloc[validation], cfg["prediction_batch_size"])
    weights, candidates = select_fusion_weights(sample.label, scores, cfg["fusion_weight_step"])
    fitted = {}
    for family in families:
        model = make_model(data.feature_columns, cfg["geochemical_columns"], family, cfg, seed)
        model.fit(X, sample.label, model__sample_weight=sample.peso_confianza)
        fitted[family] = model
    fusion = HeterogeneousFusion(fitted, weights, data.feature_columns)
    inner_predictions = sample[["cell_id", "label"]].copy()
    inner_predictions["inner_fold"] = fold_of
    for index, family in enumerate(families):
        inner_predictions[family] = scores[:, index]
    inner_predictions["fusion_score"] = scores @ weights
    return fusion, inner_predictions, pd.concat(roles, ignore_index=True), candidates


def _replace_rows(path, added, key="model", model_code=FUSION):
    old = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    result = pd.concat([old.loc[old[key].ne(model_code)], added], ignore_index=True)
    if path.suffix == ".parquet":
        result.to_parquet(path, index=False)
    else:
        result.to_csv(path, index=False)
    return result


def run_fusion(data):
    cfg, out = data.config, data.output
    sample = pd.read_parquet(out / "partitions/benchmark_sample.parquet")
    X = data.features.loc[sample.cell_id, data.feature_columns]
    families = cfg["fusion_components"]
    rows, folds, predictions, components = [], [], [], []
    inner_frames, memberships, searches, weights_rows = [], [], [], []

    def remember(model, inner, roles, candidates, scope, strategy, fold):
        context = {"scope": scope, "strategy": strategy, "outer_fold": int(fold)}
        inner_frames.append(inner.assign(**context))
        memberships.append(roles.assign(**context))
        searches.append(candidates.assign(**context))
        weights_rows.extend({**context, "component": family, "weight": float(weight),
                             "training_ids_sha256": cell_hash(inner.cell_id)}
                            for family, weight in zip(families, model.weights))

    for strategy in cfg["diagnostic_cv_strategies"]:
        scores = np.full(len(sample), np.nan)
        for fold, (train, test, excluded) in enumerate(validation_splits(sample, strategy, cfg, cfg["seed"])):
            started = time.perf_counter()
            training = sample.iloc[train].reset_index(drop=True)
            model, inner, roles, candidates = fit_fusion(data, training, strategy, cfg["seed"] + fold)
            remember(model, inner, roles, candidates, "cv", strategy, fold)
            matrix = model.member_scores(X.iloc[test])
            scores[test] = matrix @ model.weights
            component_frame = sample.iloc[test][["cell_id", "label"]].copy()
            for j, family in enumerate(families):
                component_frame[family] = matrix[:, j]
            components.append(component_frame.assign(strategy=strategy, fold=fold, fusion_score=scores[test]))
            folds.append({"strategy": strategy, "model": FUSION, "fold": fold,
                "n_input_features": 64, "train_cells": len(train), "validation_cells": len(test),
                "buffer_excluded": len(excluded), "training_ids_sha256": cell_hash(training.cell_id),
                "validation_ids_sha256": cell_hash(sample.iloc[test].cell_id),
                "c_mean": np.nan, "c_members": "", "fit_predict_seconds": time.perf_counter() - started,
                **label_metrics(sample.iloc[test].label, scores[test], sample.iloc[test].cell_id)})
            print(f"FUSION CV {strategy:8s} fold={fold} weights={model.weights.round(3)}", flush=True)
        metrics = label_metrics(sample.label, scores, sample.cell_id)
        rows.append({"strategy": strategy, "model": FUSION, "n_input_features": 64,
            "n_P": int(sample.label.sum()), "n_U": int(sample.label.eq(0).sum()),
            "sample_hash": cell_hash(sample.cell_id), "c_mean": np.nan, "c_std": np.nan,
            "fraction_score_one": float(np.mean(scores >= 1)), **metrics})
        predictions.append(sample[["cell_id", "label"]].assign(strategy=strategy, model=FUSION,
                                                                score=scores, raw_score=scores))
        print(f"FUSION {strategy}: AUC={metrics['roc_auc']:.4f}; AP={metrics['average_precision']:.4f}", flush=True)
    fusion_summary = pd.DataFrame(rows)
    combined = _replace_rows(out / "benchmark_cv_summary.csv", fusion_summary)
    display_benchmark(combined).to_csv(out / "benchmark_cv_tabla.csv", index=False)
    fold_df = pd.DataFrame(folds)
    _replace_rows(out / "benchmark_cv_folds.csv", fold_df)
    oof = pd.concat(predictions, ignore_index=True)
    _replace_rows(out / "benchmark_cv_oof.parquet", oof)
    buffered = fusion_summary.loc[fusion_summary.strategy.eq("buffered")].drop(columns="strategy")
    buffered["fit_seconds"] = fold_df.loc[fold_df.strategy.eq("buffered"), "fit_predict_seconds"].sum()
    _replace_rows(out / "benchmark_summary.csv", buffered)
    _replace_rows(out / "benchmark_folds.csv", fold_df.loc[fold_df.strategy.eq("buffered")].drop(columns="strategy"))
    _replace_rows(out / "benchmark_oof_predictions.parquet", oof.loc[oof.strategy.eq("buffered")].drop(columns=["strategy", "raw_score"]))
    pd.concat(components, ignore_index=True).to_parquet(out / "fusion_cv_component_predictions.parquet", index=False)

    groups = district_groups(data)
    rotation_rows, details, territory_predictions = [], [], []
    for group, group_frame in groups.groupby("group", sort=True):
        districts = set(group_frame.district_id)
        train, held = rotation_pools(data, districts)
        training = pd.read_parquet(out / f"partitions/rotation_{group}_sample.parquet")
        if not set(training.cell_id) <= set(train.cell_id):
            raise ValueError("La muestra de rotación no respeta el pool territorial.")
        started = time.perf_counter()
        model, inner, roles, candidates = fit_fusion(data, training, "buffered", cfg["seed"] + int(group))
        remember(model, inner, roles, candidates, "rotation", "buffered", int(group))
        held_X = data.features.loc[held.cell_id, data.feature_columns]
        matrix = np.concatenate([model.member_scores(held_X.iloc[start:start + cfg["prediction_batch_size"]])
                                 for start in range(0, len(held_X), cfg["prediction_batch_size"])])
        scores = matrix @ model.weights
        rank = ranked_cells(held.cell_id, scores)
        pred = pd.DataFrame({"cell_id": held.cell_id.to_numpy(), "score": scores, "rank": rank})
        relations = (data.records.loc[data.records.district_id.isin(districts)].dropna(subset=["deposit_id"])
                      [["cell_id", "deposit_id", "district_id"]].drop_duplicates())
        joined = relations.merge(pred, on="cell_id", validate="many_to_one")
        result = {"model": FUSION, "group": int(group), "n_deposits": int(joined.deposit_id.nunique()),
            "n_held_cells": len(held), "n_training_P": int(training.label.sum()),
            "n_training_U": int(training.label.eq(0).sum()), "training_ids_sha256": cell_hash(training.cell_id),
            "held_ids_sha256": cell_hash(held.cell_id), "fit_predict_seconds": time.perf_counter() - started}
        for pct in [1, 5, 10]:
            joined[f"captured_at_{pct:02d}"] = joined['rank'] <= math.ceil(len(held) * pct / 100)
            count = joined.loc[joined[f"captured_at_{pct:02d}"], "deposit_id"].nunique()
            result[f"captured_deposits_at_{pct:02d}"] = int(count)
            result[f"deposit_recovery_at_{pct:02d}"] = float(count / result["n_deposits"])
        details.append(joined.assign(model=FUSION, group=int(group)))
        rotation_rows.append(result)
        for j, family in enumerate(families):
            pred[family] = matrix[:, j]
        territory_predictions.append(pred.assign(group=int(group)))
        print(f"FUSION ROT {group}: dep@10={result['captured_deposits_at_10']}/{result['n_deposits']}", flush=True)
    details_df = pd.concat(details, ignore_index=True)
    _replace_rows(out / "rotation_metrics.csv", pd.DataFrame(rotation_rows))
    _replace_rows(out / "rotation_deposit_predictions.csv", details_df)
    n = int(details_df.deposit_id.nunique())
    rotation_summary = {"model": FUSION, "n_deposits": n}
    for pct in [1, 5, 10]:
        count = int(details_df.loc[details_df[f"captured_at_{pct:02d}"], "deposit_id"].nunique())
        rotation_summary.update({f"captured_deposits_at_{pct:02d}": count,
                                 f"deposit_recovery_at_{pct:02d}": count / n})
    _replace_rows(out / "rotation_summary.csv", pd.DataFrame([rotation_summary]))
    pd.concat(territory_predictions, ignore_index=True).to_parquet(out / "fusion_rotation_component_predictions.parquet", index=False)

    # Weights for deployment are selected anew using only the national fitting sample.
    national_sample = select_sample(data, data.grid.cell_id, cfg["seed"] + 5000)
    model, inner, roles, candidates = fit_fusion(data, national_sample, "buffered", cfg["seed"])
    remember(model, inner, roles, candidates, "national", "buffered", -1)
    folder = out / "models/fusion"
    folder.mkdir(exist_ok=True)
    joblib.dump(model, folder / "model.joblib", compress=3)
    national_sample.to_parquet(out / "partitions/fusion_national_sample.parquet", index=False)
    _write_fusion_map(data, model)
    metadata = {"n_input_features": 64, "components": families,
        "weights": dict(zip(families, map(float, model.weights))), "weight_selection": "three inner buffered folds; maximize pooled OOF Average Precision",
        "weight_step": cfg["fusion_weight_step"], "fit_P": int(national_sample.label.sum()),
        "fit_U": int(national_sample.label.eq(0).sum()), "absolute_probability": False,
        "training_scope": "full eligible inventory after evaluation; not an independent test",
        "disagreement": "weighted standard deviation across model families, not a confidence interval"}
    write_json(folder / "metadata.json", metadata)
    pd.DataFrame(weights_rows).to_csv(out / "fusion_weights.csv", index=False)
    pd.concat(inner_frames, ignore_index=True).to_parquet(out / "fusion_inner_predictions.parquet", index=False)
    pd.concat(memberships, ignore_index=True).to_parquet(out / "partitions/fusion_inner_memberships.parquet", index=False)
    pd.concat(searches, ignore_index=True).to_csv(out / "fusion_candidate_metrics.csv", index=False)
    base_oof = pd.read_parquet(out / "benchmark_oof_predictions.parquet")
    wide = base_oof.loc[base_oof.model.isin(families)].pivot(index="cell_id", columns="model", values="score")
    wide.corr(method="spearman").to_csv(out / "fusion_component_correlations.csv")
    write_json(out / "fusion_summary.json", {"n_input_features": 64, "selection_metric": "average_precision",
        "weight_selection_uses_outer_test": False, "inner_folds": cfg["fusion_inner_folds"],
        "components": families, "buffered_metrics": json.loads(buffered.drop(columns=["c_mean", "c_std"]).to_json(orient="records", double_precision=15))[0],
        "rotations": rotation_summary, "national_weights": metadata["weights"],
        "validation_scope": "internal nested evaluation on known catalogue; no prospective campaign"})
    add_uniform_fusion(data)
    return fusion_summary


def _write_fusion_map(data, model, prefix="GeoAI_fusion", category_filename="fusion_map_category_counts.csv"):
    cfg, n = data.config, len(data.grid)
    matrix = np.concatenate([model.member_scores(data.features[data.feature_columns].iloc[start:start + cfg["prediction_batch_size"]])
                             for start in range(0, n, cfg["prediction_batch_size"])])
    mean = matrix @ model.weights
    disagreement = np.sqrt(np.square(matrix - mean[:, None]) @ model.weights)
    pre = next(iter(model.components.values())).named_steps["preprocess"]
    centroid = pre.transform(data.features.loc[data.positives.cell_id, data.feature_columns]).mean(axis=0)
    novelty = np.empty(n)
    for start in range(0, n, cfg["prediction_batch_size"]):
        novelty[start:start + cfg["prediction_batch_size"]] = np.linalg.norm(
            pre.transform(data.features[data.feature_columns].iloc[start:start + cfg["prediction_batch_size"]]) - centroid, axis=1)
    high_novelty = novelty > np.percentile(novelty, 95)
    high_score, high_disagreement = mean >= np.percentile(mean, 90), disagreement >= np.percentile(disagreement, 75)
    category = np.select([high_novelty, high_score & ~high_disagreement, high_score & high_disagreement,
                          ~high_score & ~high_disagreement], [1, 2, 3, 4], default=5).astype('uint8')
    result = data.grid.copy()
    result["favorability_mean"] = mean.astype('float32')
    result["component_disagreement_std"] = disagreement.astype('float32')
    result["novelty_distance"] = novelty.astype('float32')
    result["category"] = category
    result["missing_geochemical_features"] = data.features[cfg["geochemical_columns"]].isna().sum(axis=1).to_numpy()
    for j, family in enumerate(cfg["fusion_components"]):
        result[f"score_{family}"] = matrix[:, j].astype('float32')
    result.to_parquet(data.output / "maps" / f"{prefix}_national.parquet", index=False, compression='zstd')
    for suffix, values in [("score", mean), ("disagreement", disagreement), ("novelty", novelty)]:
        write_raster(data, f"{prefix}_{suffix}", values)
    write_raster(data, f"{prefix}_category", category, 'uint8', 0)
    pd.Series(category).value_counts().rename_axis('category').reset_index(name='cells').to_csv(
        data.output / category_filename, index=False)


def add_uniform_fusion(data):
    """Media de pesos constantes, reconstruida de las mismas predicciones externas."""
    out, cfg = data.output, data.config
    families = cfg['fusion_components']
    components = pd.read_parquet(out / 'fusion_cv_component_predictions.parquet')
    cv_rows, fold_rows, predictions = [], [], []
    source_folds = pd.read_csv(out / 'benchmark_cv_folds.csv')
    for strategy, frame in components.groupby('strategy',sort=False):
        score = frame[families].mean(axis=1).to_numpy()
        cv_rows.append({'strategy':strategy,'model':UNIFORM,'n_input_features':64,
            'n_P':int(frame.label.sum()),'n_U':int(frame.label.eq(0).sum()),'sample_hash':cell_hash(frame.cell_id),
            'c_mean':np.nan,'c_std':np.nan,'fraction_score_one':float(np.mean(score>=1)),
            **label_metrics(frame.label,score,frame.cell_id)})
        predictions.append(frame[['cell_id','label']].assign(strategy=strategy,model=UNIFORM,score=score,raw_score=score))
        for fold, subset in frame.groupby('fold'):
            source = source_folds.loc[source_folds.strategy.eq(strategy)&source_folds.fold.eq(fold)&source_folds.model.eq(FUSION)].iloc[0].to_dict()
            source.update(model=UNIFORM, **label_metrics(subset.label,subset[families].mean(axis=1),subset.cell_id))
            fold_rows.append(source)
    cv = pd.DataFrame(cv_rows)
    combined = _replace_rows(out/'benchmark_cv_summary.csv',cv,model_code=UNIFORM)
    display_benchmark(combined).to_csv(out/'benchmark_cv_tabla.csv',index=False)
    fold_df = pd.DataFrame(fold_rows)
    _replace_rows(out/'benchmark_cv_folds.csv',fold_df,model_code=UNIFORM)
    oof = pd.concat(predictions,ignore_index=True)
    _replace_rows(out/'benchmark_cv_oof.parquet',oof,model_code=UNIFORM)
    _replace_rows(out/'benchmark_summary.csv',cv.loc[cv.strategy.eq('buffered')].drop(columns='strategy'),model_code=UNIFORM)
    _replace_rows(out/'benchmark_folds.csv',fold_df.loc[fold_df.strategy.eq('buffered')].drop(columns='strategy'),model_code=UNIFORM)
    _replace_rows(out/'benchmark_oof_predictions.parquet',oof.loc[oof.strategy.eq('buffered')].drop(columns=['strategy','raw_score']),model_code=UNIFORM)
    territories = pd.read_parquet(out/'fusion_rotation_component_predictions.parquet')
    groups = pd.read_csv(out/'partitions/district_groups.csv')
    rotation_rows, details = [], []
    source_rotations = pd.read_csv(out/'rotation_metrics.csv')
    for group, frame in territories.groupby('group',sort=True):
        score = frame[families].mean(axis=1).to_numpy()
        prediction = frame[['cell_id']].assign(score=score,rank=ranked_cells(frame.cell_id,score))
        districts = set(groups.loc[groups.group.eq(group),'district_id'])
        relations = (data.records.loc[data.records.district_id.isin(districts)].dropna(subset=['deposit_id'])
                      [['cell_id','deposit_id','district_id']].drop_duplicates())
        joined = relations.merge(prediction,on='cell_id',validate='many_to_one')
        result = source_rotations.loc[source_rotations.group.eq(group)&source_rotations.model.eq(FUSION)].iloc[0].to_dict()
        result['model'] = UNIFORM
        for pct in [1,5,10]:
            joined[f'captured_at_{pct:02d}'] = joined['rank']<=math.ceil(len(frame)*pct/100)
            count = int(joined.loc[joined[f'captured_at_{pct:02d}'],'deposit_id'].nunique())
            result[f'captured_deposits_at_{pct:02d}'] = count
            result[f'deposit_recovery_at_{pct:02d}'] = count/result['n_deposits']
        rotation_rows.append(result)
        details.append(joined.assign(model=UNIFORM,group=int(group)))
    _replace_rows(out/'rotation_metrics.csv',pd.DataFrame(rotation_rows),model_code=UNIFORM)
    joined = pd.concat(details,ignore_index=True)
    _replace_rows(out/'rotation_deposit_predictions.csv',joined,model_code=UNIFORM)
    n = int(joined.deposit_id.nunique())
    result = {'model':UNIFORM,'n_deposits':n}
    for pct in [1,5,10]:
        count = int(joined.loc[joined[f'captured_at_{pct:02d}'],'deposit_id'].nunique())
        result[f'captured_deposits_at_{pct:02d}'] = count
        result[f'deposit_recovery_at_{pct:02d}'] = count/n
    _replace_rows(out/'rotation_summary.csv',pd.DataFrame([result]),model_code=UNIFORM)
    learned = joblib.load(out/'models/fusion/model.joblib')
    model = HeterogeneousFusion(learned.components,np.full(len(families),1/len(families)),data.feature_columns)
    folder = out/'models/fusion_uniform'
    folder.mkdir(exist_ok=True)
    joblib.dump(model,folder/'model.joblib',compress=3)
    _write_fusion_map(data,model,'GeoAI_fusion_uniform','fusion_uniform_map_category_counts.csv')
    summary = {'n_input_features':64,'components':families,'weights':dict(zip(families,map(float,model.weights))),
        'weight_selection':'fixed equal weights; no label-dependent tuning', 'rotations':result,
        'buffered_metrics':json.loads(cv.loc[cv.strategy.eq('buffered')].drop(columns=['c_mean','c_std']).to_json(orient='records',double_precision=15))[0],
        'absolute_probability':False,'validation_scope':'internal evaluation on known catalogue'}
    write_json(folder/'metadata.json',summary)
    write_json(out/'fusion_uniform_summary.json',summary)
    print(f"FUSION UNIFORME: AP={summary['buffered_metrics']['average_precision']:.6f}; dep@10={result['captured_deposits_at_10']}/{n}",flush=True)


def generate_fusion_report(data):
    """Presenta mejoras y límites observados, sin seleccionar con los tests."""
    from .geochemical_experiment import frame_markdown
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out, report = data.output, data.report
    benchmark = pd.read_csv(out / 'benchmark_summary.csv')
    rotations = pd.read_csv(out / 'rotation_summary.csv')
    weights = pd.read_csv(out / 'fusion_weights.csv')
    metadata = json.loads((out / 'models/fusion/metadata.json').read_text(encoding='utf-8'))
    fusion = benchmark.loc[benchmark.model.eq(UNIFORM)].iloc[0]
    reference = benchmark.loc[~benchmark.model.isin([FUSION, UNIFORM])]
    best_ap = reference.loc[reference.average_precision.idxmax()]
    best_auc = reference.loc[reference.roc_auc.idxmax()]
    recovery = rotations.loc[rotations.model.eq(UNIFORM)].iloc[0]
    weight_table = (weights.loc[weights.scope.eq('cv')].groupby(['strategy','component'],as_index=False)
                    .agg(mean_weight=('weight','mean'),std_weight=('weight','std')))
    correlations = pd.read_csv(out / 'fusion_component_correlations.csv',index_col=0)
    fig, axes = plt.subplots(1,3,figsize=(17,5))
    plot_names = {'logistic':'Logística','random_forest':'Random Forest','lightgbm':'LightGBM',
                  'bagging_pu':'Bagging PU',FUSION:'Fusión pesos',UNIFORM:'Fusión media'}
    for axis,frame,column,title in [(axes[0],benchmark,'average_precision','Average Precision · CV con buffer'),
                                    (axes[1],benchmark,'roc_auc','ROC-AUC · CV con buffer'),
                                    (axes[2],rotations,'deposit_recovery_at_10','Depósitos recuperados al 10 %')]:
        colors = ['#d27a2b' if name in [FUSION, UNIFORM] else '#247b91' for name in frame.model]
        axis.bar(frame.model.map(plot_names),frame[column],color=colors)
        axis.set(ylim=(0,1),title=title)
        axis.tick_params(axis='x',rotation=28,labelsize=7)
        axis.grid(axis='y',alpha=.2)
    fig.tight_layout()
    fig.savefig(report/'figuras/fusion_resultados.png',dpi=150)
    plt.close(fig)
    fig,axis=plt.subplots(figsize=(6,5))
    im=axis.imshow(correlations,vmin=0,vmax=1,cmap='viridis')
    axis.set_xticks(range(len(correlations)),correlations.columns,rotation=25,ha='right')
    axis.set_yticks(range(len(correlations)),correlations.index)
    for i in range(len(correlations)):
        for j in range(len(correlations)):
            axis.text(j,i,f'{correlations.iloc[i,j]:.3f}',ha='center',va='center',color='black')
    axis.set_title('Correlación Spearman de scores OOF')
    fig.colorbar(im,ax=axis)
    fig.tight_layout()
    fig.savefig(report/'figuras/fusion_complementariedad.png',dpi=150)
    plt.close(fig)
    frame=pd.read_parquet(out/'maps/GeoAI_fusion_uniform_national.parquet')
    fig,axes=plt.subplots(1,3,figsize=(16,6))
    for axis,column,title in zip(axes,['favorability_mean','component_disagreement_std','novelty_distance'],
                                 ['Favorabilidad fusionada','Desacuerdo entre familias','Novedad del perfil']):
        raster=np.full((data.grid_spec['height'],data.grid_spec['width']),np.nan)
        raster[frame.row.to_numpy(),frame.col.to_numpy()]=frame[column]
        im=axis.imshow(raster,cmap='viridis')
        axis.set_title(title)
        axis.set_axis_off()
        fig.colorbar(im,ax=axis,shrink=.65)
    fig.tight_layout()
    fig.savefig(report/'figuras/fusion_mapa.png',dpi=150)
    plt.close(fig)
    text=f'''# GeoAI · Fusión heterogénea de modelos

Se combinan logística L2, Random Forest, LightGBM y Bagging PU sobre las mismas 64 entradas, incluidas las ocho clases geoquímicas. Se evalúan la media uniforme, con peso fijo 0,25 para cada componente, y una fusión que aprende pesos en CV interna. Bagging PU agrega miembros de una familia; estas fusiones reúnen algoritmos con estructuras diferentes. La correlación entre sus scores fuera de pliegue permite inspeccionar su complementariedad. Ese diagnóstico es descriptivo y no elige pesos sobre el test.

## Aprendizaje de pesos sin utilizar el test externo

El score es **S(x)=Σ w_j s_j(x)**, con pesos no negativos que suman uno. La media uniforme fija w_j=0,25 sin usar etiquetas para ajustarlos. En la fusión con pesos aprendidos, cada entrenamiento externo genera predicciones fuera de pliegue de los cuatro componentes mediante tres pliegues internos. La separación interna reproduce la estrategia aleatoria, por bloques o con buffer de 15 km. Imputación, escalado y one-hot se ajustan dentro de cada entrenamiento interno.

Se evalúa una rejilla simplex de paso {data.config['fusion_weight_step']} y la media de pesos iguales. Se selecciona Average Precision interna; los empates favorecen pesos menos concentrados. La rejilla permite peso cero y seleccionar un único componente cuando la mezcla no añade señal interna. Los cuatro pipelines se reajustan después con todo el entrenamiento externo y los pesos quedan fijados antes de predecir el test. El procedimiento completo, incluida esta selección, se evalúa en los cinco pliegues externos.

Se combinan scores P/U sin corrección Elkan–Noto. La optimización de ranking absorbe diferencias de escala dentro del entrenamiento, sin convertir las salidas en probabilidades físicas calibradas. El c del diagnóstico pertenece a su modelo específico.

## Resultados en CV espacial con buffer

{frame_markdown(benchmark[['model','roc_auc','average_precision','positive_cell_recovery_at_05','positive_cell_recovery_at_10']])}

La **media uniforme** obtiene **AP {fusion.average_precision:.6f}** y **ROC-AUC {fusion.roc_auc:.6f}**. La mayor AP entre los componentes es {best_ap.average_precision:.6f} ({best_ap.model}); la mayor AUC es {best_auc.roc_auc:.6f} ({best_auc.model}). La diferencia de AP es {fusion.average_precision-best_ap.average_precision:+.6f} y la de AUC frente a la mayor referencia es {fusion.roc_auc-best_auc.roc_auc:+.6f}. Estas diferencias describen esta evaluación interna; no prueban significación estadística ni mejora universal. La tabla conserva también los resultados de pesos aprendidos para no confundir selección interna con mejora garantizada.

El benchmark de tres estrategias incorpora la fusión y conserva ROC-AUC, PR-AUC/AP, Brier y recuperación exacta al 5 % y 10 %. Las predicciones y particiones externas e internas se exportan para comprobar el procedimiento.

## Recuperación de depósitos por territorios reservados

{frame_markdown(rotations)}

La **media uniforme** recupera **{int(recovery.captured_deposits_at_05)} de {int(recovery.n_deposits)} depósitos al 5 %** de celdas y **{int(recovery.captured_deposits_at_10)} al 10 %**. Sus pesos permanecen constantes en todos los grupos. En la fusión aprendida se eligen únicamente con los datos de entrenamiento, mediante CV interna con buffer. Las muestras de entrenamiento y los territorios son los mismos que en los demás procedimientos; se excluyen los bloques reservados y un buffer de 15 km. Se cuenta una vez cada depósito capturado.

![Resultados de la fusión](figuras/fusion_resultados.png)

## Pesos y complementariedad

{frame_markdown(weight_table)}

Los pesos aprendidos cambian por entrenamiento y no son importancias de las variables geológicas. Para su modelo nacional se seleccionan de nuevo usando únicamente la muestra de ajuste y tres pliegues internos espaciales. Sus valores son:

{frame_markdown(pd.DataFrame([metadata['weights']]))}

![Complementariedad](figuras/fusion_complementariedad.png)

## Modelo y cartografía de la fusión

models/fusion_uniform/model.joblib contiene los cuatro pipelines y pesos iguales; models/fusion/model.joblib conserva los pesos aprendidos. La muestra nacional utiliza {metadata['fit_P']} P y {metadata['fit_U']} U; el ajuste posterior a la evaluación no constituye un test independiente. maps/GeoAI_fusion_uniform_national.parquet y los GeoTIFF asociados exportan la media uniforme, scores individuales, desacuerdo, novedad y categorías. También se conservan los productos de la fusión aprendida.

El desacuerdo es **raíz de Σ w_j(s_j−S)²** entre familias. Tiene un significado diferente de la variación por remuestreo U del ensamble de ocho LightGBM: ambos son diagnósticos de variación, sin representar toda la incertidumbre ni un intervalo de confianza. Las categorías de la fusión usan percentiles relativos de score, desacuerdo y novedad.

![Cartografía de la fusión](figuras/fusion_mapa.png)

## Reproducción y alcance

Ejecutar scripts/ejecutar_geoquimica.py --stage fusion y después --stage report. La ejecución all incluye la fusión. fusion_weights.csv, fusion_candidate_metrics.csv, fusion_inner_predictions.parquet y partitions/fusion_inner_memberships.parquet registran la selección. fusion_cv_component_predictions.parquet y fusion_rotation_component_predictions.parquet permiten reconstruir la media ponderada y la recuperación. Los resultados proceden del inventario conocido; una campaña externa permitiría contrastar su utilidad prospectiva.

Referencia técnica: [agregación de clasificadores por media ponderada, scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.VotingClassifier.html).
'''
    (report/'INFORME_FUSION_MODELOS.md').write_text(text,encoding='utf-8')
    for filename in ['fusion_weights.csv','fusion_candidate_metrics.csv','fusion_component_correlations.csv',
                     'fusion_summary.json','fusion_map_category_counts.csv','fusion_uniform_summary.json','fusion_uniform_map_category_counts.csv']:
        (report/'tablas'/filename).write_bytes((out/filename).read_bytes())
    return text
