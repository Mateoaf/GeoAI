"""Paso 10 — Fase G: Evaluación final ciega, única e irreversible del modelo congelado.

Abre por primera vez los 5 distritos pre-registrados del holdout y evalúa
exclusivamente el pipeline congelado logistic_01 de Phase F.
Bajo ninguna circunstancia reentrena, recalibra, altera hiperparámetros ni
repite la evaluación con otro modelo.
"""
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import shutil
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score
import yaml

from geoau import evaluation as ev
from geoau.local_sources import sha256_file, write_json
from geoau.training import FeatureGuard, SafeOneHot  # Requeridos para unpickle del pipeline


def ejecutar_fase_g():
    print("=" * 80)
    print("PASO 10 — FASE G: EVALUACIÓN FINAL CIEGA DEL MODELO CONGELADO")
    print("=" * 80)
    t_start = time.time()

    root = Path(__file__).resolve().parents[1]
    
    # 1. Configuración de entrada congelada
    f_run = "reports/fase_f/20260927T135750_819061Z"
    meta_path = root / f_run / "final_model/final_validated_model.json"
    model_path = root / f_run / "final_model/final_validated_model.joblib"
    
    if not meta_path.exists() or not model_path.exists():
        raise FileNotFoundError(f"No se encuentra el modelo congelado en {f_run}")
        
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    d_run = meta["phase_d_run"]
    e_run = meta["phase_e_run"]
    cols = meta["columns"]
    seed = 42

    print(f"Modelo congelado: {meta['candidate_id']} ({meta['family']}, ratio={meta['ratio']}, C={meta['params'].get('C')})")
    print(f"Procedencia: D={d_run}, E={e_run}, F={f_run}")
    print(f"Predictores congelados: {len(cols)}")

    # 2. Verificar integridad criptográfica de entradas
    ev.verify(root / d_run, ev.read_json(root / d_run / "outputs_manifest.json"))
    ev.verify(root / e_run, ev.read_json(root / e_run / "outputs_manifest.json"))
    ev.verify(root / f_run, ev.read_json(root / f_run / "outputs_manifest.json"))
    print("Integridad SHA-256 de Fases D, E y F verificada al 100%.")

    # 3. Crear directorio de ejecución sellado para Fase G
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    out = root / "reports/fase_g" / stamp
    out.mkdir(parents=True, exist_ok=False)
    (out / "predictions").mkdir()
    (out / "metrics").mkdir()
    print(f"Directorio Fase G: {out}")

    # 4. Cargar datos del Holdout Ciego
    print("\n--- Apertura Ciega de los 5 Distritos de Holdout ---")
    spatial = pd.read_parquet(root / e_run / "design/spatial_units.parquet")
    supp = pd.read_parquet(root / d_run / "calidad_y_soporte.parquet")
    rel = pd.read_parquet(root / d_run / "relacion_indicios_celda.parquet")
    groups = pd.read_csv(root / "data/review/territorial_groups.csv")

    # Selección rigurosa de celdas holdout elegibles
    h_mask = spatial.holdout & spatial.cell_id.isin(supp.loc[supp.eligible_approved_features, "cell_id"])
    holdout_cells = spatial.loc[h_mask, ["cell_id", "unit_id"]].copy().reset_index(drop=True)
    
    n_holdout = len(holdout_cells)
    if n_holdout != 13541:
        raise ValueError(f"Se esperaban exactamente 13.541 celdas elegibles en holdout, se encontraron {n_holdout}")
    print(f"Celdas elegibles de holdout identificadas: {n_holdout}")

    # Añadir área terrestre
    holdout_cells = holdout_cells.merge(supp[["cell_id", "land_area_m2"]], on="cell_id", how="left")
    total_area_m2 = float(holdout_cells["land_area_m2"].sum())
    print(f"Área terrestre total del holdout: {total_area_m2 / 1e6:.2f} km²")

    # Identificar positivos revisados en holdout
    p_rev = rel[rel.elegible_general_revisada.eq(True)]
    p_holdout = p_rev[p_rev.cell_id.isin(holdout_cells.cell_id)].copy()
    
    p_cells_unique = p_holdout.cell_id.nunique()
    deposits_unique = p_holdout.deposit_id.nunique()
    if p_cells_unique != 19 or deposits_unique != 8:
        raise ValueError(f"Se esperaban 19 celdas P y 8 depósitos, encontrados {p_cells_unique} celdas P y {deposits_unique} depósitos")
    print(f"Positivos revisados en holdout: {len(p_holdout)} registros, {p_cells_unique} celdas P únicas, {deposits_unique} depósitos independientes.")

    # Mapeo de unidades a distritos
    unit_to_district = {
        "b1_1": "dist_galicia_costa_da_morte",
        "b9_7": "dist_montes_de_toledo_jara",
        "b13_6": "dist_ossa_morena_penaflor",
        "b14_10": "dist_beticas_granada",
        "b15_12": "dist_cabo_de_gata"
    }
    holdout_cells["district_id"] = holdout_cells["unit_id"].map(unit_to_district)

    # 5. Cargar pipeline congelado y predecir sin modificaciones
    print("\n--- Ejecución de Predicción con Pipeline Congelado ---")
    pipeline = joblib.load(model_path)
    X = pd.read_parquet(root / d_run / "X_features.parquet", columns=["cell_id"] + cols).set_index("cell_id")
    X_holdout = X.loc[holdout_cells.cell_id, cols]

    t_pred = time.time()
    scores = pipeline.predict_proba(X_holdout)[:, 1]
    dt_pred = time.time() - t_pred
    print(f"Predicciones generadas en {dt_pred:.4f}s.")
    print(f"Rango de scores: min={scores.min():.4f}, media={scores.mean():.4f}, mediana={np.median(scores):.4f}, max={scores.max():.4f}")

    # 6. Ordenamiento y métricas territoriales deterministas
    holdout_cells["score"] = scores
    holdout_cells["tie_key"] = [ev.seed_for(seed, "ties", cid) for cid in holdout_cells.cell_id]
    
    # Desempate determinista
    order = np.lexsort((holdout_cells["tie_key"].to_numpy(), -scores))
    ranked = holdout_cells.iloc[order].copy().reset_index(drop=True)
    ranked["rank"] = np.arange(1, len(ranked) + 1)
    ranked["cumulative_area_m2"] = ranked["land_area_m2"].cumsum()
    ranked["cumulative_area_fraction"] = ranked["cumulative_area_m2"] / total_area_m2
    ranked["percentile_favorability"] = 100.0 * (1.0 - (ranked["rank"] - 0.5) / len(ranked))

    # Identificar celdas P en el ranking
    p_cell_set = set(p_holdout.cell_id)
    ranked["is_P"] = ranked.cell_id.isin(p_cell_set)
    
    # Mapear deposit_id a cada celda P
    cell_to_deposit = p_holdout.groupby("cell_id")["deposit_id"].first().to_dict()
    ranked["deposit_id"] = ranked.cell_id.map(cell_to_deposit)

    # Cálculo de recuperaciones al 1%, 5%, 10%
    metrics_summary = {
        "holdout_cells": n_holdout,
        "total_area_km2": float(total_area_m2 / 1e6),
        "observed_P_cells": p_cells_unique,
        "observed_deposits": deposits_unique,
        "districts_count": 5
    }

    # Mapa de depósito -> celdas
    dep_to_cells = p_holdout.groupby("deposit_id")["cell_id"].unique().to_dict()

    for frac, suffix in [(0.01, "01"), (0.05, "05"), (0.10, "10")]:
        sel = ranked[ranked["cumulative_area_fraction"] <= frac]
        sel_cells = set(sel.cell_id)
        
        # Recuperación de celdas
        c_hits = int(sel.is_P.sum())
        c_rec = float(c_hits / p_cells_unique)
        metrics_summary[f"cell_recovery_at_{suffix}"] = c_rec
        metrics_summary[f"cell_hits_at_{suffix}"] = c_hits
        
        # Recuperación de depósitos (contando cada depósito una sola vez)
        d_hits = 0
        for dep, c_list in dep_to_cells.items():
            if any(c in sel_cells for c in c_list):
                d_hits += 1
        d_rec = float(d_hits / deposits_unique)
        metrics_summary[f"deposit_recovery_at_{suffix}"] = d_rec
        metrics_summary[f"deposit_hits_at_{suffix}"] = d_hits
        metrics_summary[f"realized_area_fraction_{suffix}"] = float(sel["cumulative_area_m2"].iloc[-1] / total_area_m2) if len(sel) > 0 else 0.0

    # Métricas auxiliares P/U
    y_true = ranked.is_P.astype(int).to_numpy()
    metrics_summary["average_precision_PU"] = float(average_precision_score(y_true, ranked.score))
    metrics_summary["roc_auc_PU"] = float(roc_auc_score(y_true, ranked.score))

    print("\n--- Resultados Globales en Holdout Ciego ---")
    print(f"Deposit Recovery @ 1%:  {metrics_summary['deposit_recovery_at_01']:.4f} ({metrics_summary['deposit_hits_at_01']}/{deposits_unique})")
    print(f"Deposit Recovery @ 5%:  {metrics_summary['deposit_recovery_at_05']:.4f} ({metrics_summary['deposit_hits_at_05']}/{deposits_unique})")
    print(f"Deposit Recovery @ 10%: {metrics_summary['deposit_recovery_at_10']:.4f} ({metrics_summary['deposit_hits_at_10']}/{deposits_unique})")
    print(f"Cell Recovery @ 1%:     {metrics_summary['cell_recovery_at_01']:.4f} ({metrics_summary['cell_hits_at_01']}/{p_cells_unique})")
    print(f"Cell Recovery @ 5%:     {metrics_summary['cell_recovery_at_05']:.4f} ({metrics_summary['cell_hits_at_05']}/{p_cells_unique})")
    print(f"Cell Recovery @ 10%:    {metrics_summary['cell_recovery_at_10']:.4f} ({metrics_summary['cell_hits_at_10']}/{p_cells_unique})")
    print(f"ROC-AUC P/U:            {metrics_summary['roc_auc_PU']:.4f}")
    print(f"PR-AUC P/U:             {metrics_summary['average_precision_PU']:.4f}")

    # 7. Desglose detallado por depósito
    deposit_rows = []
    for dep, c_list in sorted(dep_to_cells.items()):
        dep_p = ranked[ranked.cell_id.isin(c_list)]
        best_rank = int(dep_p["rank"].min())
        best_area_frac = float(dep_p["cumulative_area_fraction"].min())
        max_score = float(dep_p["score"].max())
        mean_score = float(dep_p["score"].mean())
        dist = dep_p["district_id"].iloc[0]
        
        deposit_rows.append({
            "deposit_id": dep,
            "district_id": dist,
            "p_cells_count": len(c_list),
            "max_score": max_score,
            "mean_score": mean_score,
            "best_rank_in_holdout": best_rank,
            "best_area_fraction": best_area_frac,
            "best_percentile_favorability": float(100.0 * (1.0 - best_area_frac)),
            "recovered_at_01": best_area_frac <= 0.01,
            "recovered_at_05": best_area_frac <= 0.05,
            "recovered_at_10": best_area_frac <= 0.10
        })
    df_deposits = pd.DataFrame(deposit_rows)
    print("\n--- Desglose por Depósito ---")
    print(df_deposits[["deposit_id", "district_id", "p_cells_count", "best_rank_in_holdout", "best_area_fraction", "recovered_at_05"]])

    # 8. Desglose detallado por distrito
    district_rows = []
    for dist_id in sorted(holdout_cells["district_id"].unique()):
        dist_ranked = ranked[ranked["district_id"] == dist_id]
        dist_total_cells = len(dist_ranked)
        dist_p_cells = int(dist_ranked["is_P"].sum())
        
        # Depósitos presentes en este distrito
        dist_deps = [d for d, r in df_deposits.iterrows() if r["district_id"] == dist_id]
        dist_deps_df = df_deposits[df_deposits["district_id"] == dist_id]
        n_dist_deps = len(dist_deps_df)
        
        # Recuperación de depósitos al 1%, 5%, 10%
        rec_dep_01 = int(dist_deps_df["recovered_at_01"].sum())
        rec_dep_05 = int(dist_deps_df["recovered_at_05"].sum())
        rec_dep_10 = int(dist_deps_df["recovered_at_10"].sum())
        
        # Celdas recuperadas dentro de los percentiles globales
        sel_01 = ranked[ranked["cumulative_area_fraction"] <= 0.01]
        sel_05 = ranked[ranked["cumulative_area_fraction"] <= 0.05]
        sel_10 = ranked[ranked["cumulative_area_fraction"] <= 0.10]
        
        c_rec_01 = int(dist_ranked.cell_id.isin(sel_01.cell_id[sel_01.is_P]).sum())
        c_rec_05 = int(dist_ranked.cell_id.isin(sel_05.cell_id[sel_05.is_P]).sum())
        c_rec_10 = int(dist_ranked.cell_id.isin(sel_10.cell_id[sel_10.is_P]).sum())
        
        district_rows.append({
            "district_id": dist_id,
            "unit_id": dist_ranked["unit_id"].iloc[0],
            "total_cells": dist_total_cells,
            "p_cells": dist_p_cells,
            "n_deposits": n_dist_deps,
            "deposits_list": "; ".join(dist_deps_df["deposit_id"].tolist()),
            "score_mean": float(dist_ranked["score"].mean()),
            "score_median": float(dist_ranked["score"].median()),
            "score_max": float(dist_ranked["score"].max()),
            "deposits_recovered_at_01": rec_dep_01,
            "deposit_recovery_rate_at_01": float(rec_dep_01 / n_dist_deps) if n_dist_deps > 0 else 0.0,
            "deposits_recovered_at_05": rec_dep_05,
            "deposit_recovery_rate_at_05": float(rec_dep_05 / n_dist_deps) if n_dist_deps > 0 else 0.0,
            "deposits_recovered_at_10": rec_dep_10,
            "deposit_recovery_rate_at_10": float(rec_dep_10 / n_dist_deps) if n_dist_deps > 0 else 0.0,
            "cells_recovered_at_01": c_rec_01,
            "cells_recovered_at_05": c_rec_05,
            "cells_recovered_at_10": c_rec_10
        })
    df_districts = pd.DataFrame(district_rows)
    print("\n--- Desglose por Distrito ---")
    print(df_districts[["district_id", "total_cells", "p_cells", "n_deposits", "deposit_recovery_rate_at_05", "score_mean"]])

    # 9. Intervalos de Incertidumbre Bootstrap a Nivel de Depósito
    print("\n--- Estimación Bootstrap de Incertidumbre (N=8 depósitos) ---")
    B = 2000
    rng = np.random.default_rng(seed)
    n_deps = len(df_deposits)
    
    rec_01_arr = df_deposits["recovered_at_01"].astype(int).to_numpy()
    rec_05_arr = df_deposits["recovered_at_05"].astype(int).to_numpy()
    rec_10_arr = df_deposits["recovered_at_10"].astype(int).to_numpy()
    
    boot_01, boot_05, boot_10 = [], [], []
    for _ in range(B):
        idx = rng.choice(n_deps, size=n_deps, replace=True)
        boot_01.append(rec_01_arr[idx].mean())
        boot_05.append(rec_05_arr[idx].mean())
        boot_10.append(rec_10_arr[idx].mean())
        
    boot_01 = np.array(boot_01)
    boot_05 = np.array(boot_05)
    boot_10 = np.array(boot_10)
    
    bootstrap_results = {
        "bootstrap_replications": B,
        "seed": seed,
        "sample_size_deposits": n_deps,
        "discrete_granularity": float(1.0 / n_deps),
        "notes": "Solo existen 8 depósitos en el conjunto de test ciego, por lo que la distribución empírica es discreta con saltos de 12.5%.",
        "recovery_at_01": {
            "point_estimate": float(metrics_summary["deposit_recovery_at_01"]),
            "bootstrap_mean": float(boot_01.mean()),
            "bootstrap_std": float(boot_01.std()),
            "ci_95_percentile_low": float(np.percentile(boot_01, 2.5)),
            "ci_95_percentile_high": float(np.percentile(boot_01, 97.5))
        },
        "recovery_at_05": {
            "point_estimate": float(metrics_summary["deposit_recovery_at_05"]),
            "bootstrap_mean": float(boot_05.mean()),
            "bootstrap_std": float(boot_05.std()),
            "ci_95_percentile_low": float(np.percentile(boot_05, 2.5)),
            "ci_95_percentile_high": float(np.percentile(boot_05, 97.5))
        },
        "recovery_at_10": {
            "point_estimate": float(metrics_summary["deposit_recovery_at_10"]),
            "bootstrap_mean": float(boot_10.mean()),
            "bootstrap_std": float(boot_10.std()),
            "ci_95_percentile_low": float(np.percentile(boot_10, 2.5)),
            "ci_95_percentile_high": float(np.percentile(boot_10, 97.5))
        }
    }
    
    print(f"Bootstrap @ 1%:  {bootstrap_results['recovery_at_01']['point_estimate']:.4f} (IC 95%: [{bootstrap_results['recovery_at_01']['ci_95_percentile_low']:.4f}, {bootstrap_results['recovery_at_01']['ci_95_percentile_high']:.4f}], SE={bootstrap_results['recovery_at_01']['bootstrap_std']:.4f})")
    print(f"Bootstrap @ 5%:  {bootstrap_results['recovery_at_05']['point_estimate']:.4f} (IC 95%: [{bootstrap_results['recovery_at_05']['ci_95_percentile_low']:.4f}, {bootstrap_results['recovery_at_05']['ci_95_percentile_high']:.4f}], SE={bootstrap_results['recovery_at_05']['bootstrap_std']:.4f})")
    print(f"Bootstrap @ 10%: {bootstrap_results['recovery_at_10']['point_estimate']:.4f} (IC 95%: [{bootstrap_results['recovery_at_10']['ci_95_percentile_low']:.4f}, {bootstrap_results['recovery_at_10']['ci_95_percentile_high']:.4f}], SE={bootstrap_results['recovery_at_10']['bootstrap_std']:.4f})")

    # 10. Comparación descriptiva Desarrollo vs Holdout
    nested_summary = pd.read_csv(root / f_run / "nested_procedure_summary.csv", index_col=0)
    dev_cv_ranking = pd.read_csv(root / f_run / "development_cv_candidate_ranking.csv").set_index("candidate_id")
    winner_row = dev_cv_ranking.loc[meta["candidate_id"]]

    comparison_rows = [
        {
            "metric": "deposit_recovery_at_01",
            "nested_spatial_cv_oof_mean": float(nested_summary.loc["deposit_recovery_at_01", "mean"]),
            "nested_spatial_cv_oof_std": float(nested_summary.loc["deposit_recovery_at_01", "std"]),
            "development_cv_internal_mean": float(winner_row["deposit_recovery_at_01"]),
            "holdout_blind_evaluation": float(metrics_summary["deposit_recovery_at_01"]),
            "delta_vs_nested_oof": float(metrics_summary["deposit_recovery_at_01"] - nested_summary.loc["deposit_recovery_at_01", "mean"]),
            "delta_vs_dev_cv": float(metrics_summary["deposit_recovery_at_01"] - winner_row["deposit_recovery_at_01"])
        },
        {
            "metric": "deposit_recovery_at_05",
            "nested_spatial_cv_oof_mean": float(nested_summary.loc["deposit_recovery_at_05", "mean"]),
            "nested_spatial_cv_oof_std": float(nested_summary.loc["deposit_recovery_at_05", "std"]),
            "development_cv_internal_mean": float(winner_row["deposit_recovery_at_05"]),
            "holdout_blind_evaluation": float(metrics_summary["deposit_recovery_at_05"]),
            "delta_vs_nested_oof": float(metrics_summary["deposit_recovery_at_05"] - nested_summary.loc["deposit_recovery_at_05", "mean"]),
            "delta_vs_dev_cv": float(metrics_summary["deposit_recovery_at_05"] - winner_row["deposit_recovery_at_05"])
        },
        {
            "metric": "deposit_recovery_at_10",
            "nested_spatial_cv_oof_mean": float(nested_summary.loc["deposit_recovery_at_10", "mean"]),
            "nested_spatial_cv_oof_std": float(nested_summary.loc["deposit_recovery_at_10", "std"]),
            "development_cv_internal_mean": float(winner_row["deposit_recovery_at_10"]),
            "holdout_blind_evaluation": float(metrics_summary["deposit_recovery_at_10"]),
            "delta_vs_nested_oof": float(metrics_summary["deposit_recovery_at_10"] - nested_summary.loc["deposit_recovery_at_10", "mean"]),
            "delta_vs_dev_cv": float(metrics_summary["deposit_recovery_at_10"] - winner_row["deposit_recovery_at_10"])
        },
        {
            "metric": "cell_recovery_at_05",
            "nested_spatial_cv_oof_mean": float(nested_summary.loc["cell_recovery_at_05", "mean"]),
            "nested_spatial_cv_oof_std": float(nested_summary.loc["cell_recovery_at_05", "std"]),
            "development_cv_internal_mean": float(winner_row["cell_recovery_at_05"]),
            "holdout_blind_evaluation": float(metrics_summary["cell_recovery_at_05"]),
            "delta_vs_nested_oof": float(metrics_summary["cell_recovery_at_05"] - nested_summary.loc["cell_recovery_at_05", "mean"]),
            "delta_vs_dev_cv": float(metrics_summary["cell_recovery_at_05"] - winner_row["cell_recovery_at_05"])
        },
        {
            "metric": "roc_auc_PU",
            "nested_spatial_cv_oof_mean": float(nested_summary.loc["roc_auc_PU", "mean"]),
            "nested_spatial_cv_oof_std": float(nested_summary.loc["roc_auc_PU", "std"]),
            "development_cv_internal_mean": float(winner_row["roc_auc_PU"]),
            "holdout_blind_evaluation": float(metrics_summary["roc_auc_PU"]),
            "delta_vs_nested_oof": float(metrics_summary["roc_auc_PU"] - nested_summary.loc["roc_auc_PU", "mean"]),
            "delta_vs_dev_cv": float(metrics_summary["roc_auc_PU"] - winner_row["roc_auc_PU"])
        },
        {
            "metric": "average_precision_PU",
            "nested_spatial_cv_oof_mean": float(nested_summary.loc["average_precision_PU", "mean"]),
            "nested_spatial_cv_oof_std": float(nested_summary.loc["average_precision_PU", "std"]),
            "development_cv_internal_mean": float(winner_row["splits_evaluated"] * 0 + np.nan),  # No fue reportada en ranking
            "holdout_blind_evaluation": float(metrics_summary["average_precision_PU"]),
            "delta_vs_nested_oof": float(metrics_summary["average_precision_PU"] - nested_summary.loc["average_precision_PU", "mean"]),
            "delta_vs_dev_cv": np.nan
        }
    ]
    df_comparison = pd.DataFrame(comparison_rows)
    print("\n--- Comparación Descriptiva Desarrollo vs Holdout ---")
    print(df_comparison[["metric", "nested_spatial_cv_oof_mean", "development_cv_internal_mean", "holdout_blind_evaluation", "delta_vs_nested_oof"]])

    # 11. Persistencia y sellado de productos
    print("\n--- Guardando Productos de Fase G ---")
    # Predicciones completas
    pred_path = out / "predictions/holdout_predictions.parquet"
    ev.atomic_parquet(ranked, pred_path)
    
    # Exportar top 100 celdas a CSV para inspección inmediata
    ranked.head(100).to_csv(out / "predictions/holdout_top100_cells.csv", index=False)
    
    # Métricas
    write_json(out / "metrics/holdout_overall_metrics.json", metrics_summary)
    pd.DataFrame([metrics_summary]).to_csv(out / "metrics/holdout_overall_metrics.csv", index=False)
    df_deposits.to_csv(out / "metrics/holdout_by_deposit.csv", index=False)
    df_districts.to_csv(out / "metrics/holdout_by_district.csv", index=False)
    write_json(out / "metrics/bootstrap_deposit_uncertainty.json", bootstrap_results)
    pd.DataFrame([
        {"fraction": "01", **bootstrap_results["recovery_at_01"]},
        {"fraction": "05", **bootstrap_results["recovery_at_05"]},
        {"fraction": "10", **bootstrap_results["recovery_at_10"]}
    ]).to_csv(out / "metrics/bootstrap_deposit_uncertainty.csv", index=False)
    df_comparison.to_csv(out / "metrics/development_vs_holdout_comparison.csv", index=False)

    # Config snapshot e inputs
    config_snapshot = {
        "phase": "fase_g",
        "mode": "validated",
        "evaluation_type": "blind_holdout_irreversible",
        "phase_f_run": f_run,
        "phase_e_run": e_run,
        "phase_d_run": d_run,
        "candidate_id": meta["candidate_id"],
        "family": meta["family"],
        "ratio": meta["ratio"],
        "params": meta["params"],
        "n_features": len(cols),
        "seed": seed,
        "reserve_district_ids": list(unit_to_district.values()),
        "bootstrap_replications": B,
        "timestamp_utc": stamp
    }
    write_json(out / "config_snapshot.json", config_snapshot)

    frozen_inputs = [
        model_path, meta_path,
        root / d_run / "calidad_y_soporte.parquet",
        root / d_run / "X_features.parquet",
        root / d_run / "relacion_indicios_celda.parquet",
        root / e_run / "design/spatial_units.parquet",
        root / "data/review/territorial_groups.csv"
    ]
    write_json(out / "inputs.json", {"frozen_inputs": ev.records(root, frozen_inputs)})

    write_json(out / "environment.json", {
        n: importlib.metadata.version(n) for n in ("scikit-learn", "numpy", "pandas", "scipy", "joblib", "pyarrow")
    })

    # Control de cierre con opened_once: true
    control_cierre = {
        "estado_ejecucion": "completada",
        "phase": "fase_g",
        "mode": "validated",
        "opened_once": True,
        "quarantine_lifted_for_blind_evaluation": True,
        "holdout_cells_evaluated": n_holdout,
        "holdout_districts_evaluated": 5,
        "holdout_deposits_evaluated": deposits_unique,
        "holdout_p_cells_evaluated": p_cells_unique,
        "frozen_model_path": f"{f_run}/final_model/final_validated_model.joblib",
        "deposit_recovery_at_05": metrics_summary["deposit_recovery_at_05"],
        "deposit_recovery_at_01": metrics_summary["deposit_recovery_at_01"],
        "deposit_recovery_at_10": metrics_summary["deposit_recovery_at_10"],
        "roc_auc_PU": metrics_summary["roc_auc_PU"],
        "average_precision_PU": metrics_summary["average_precision_PU"],
        "execution_duration_seconds": float(time.time() - t_start),
        "reproducible": True,
        "no_further_evaluation_permitted": "La reserva ha sido abierta y consumida. El protocolo prohíbe reevaluaciones o ajuste de otros modelos tras observar estos resultados."
    }
    write_json(out / "control_cierre.json", control_cierre)

    # 12. Sellar Manifiesto de Salidas con SHA-256
    files = sorted(p for p in out.rglob("*") if p.is_file() and p.name != "outputs_manifest.json" and not p.name.startswith("."))
    manifest = ev.records(out, files)
    write_json(out / "outputs_manifest.json", manifest)
    ev.verify(out, manifest)
    print(f"\nFase G sellada con éxito: {len(manifest)} ficheros verificados con SHA-256.")

    # Guardar puntero a la ejecución actual
    write_json(root / "reports/fase_g/current_run.json", {"run": out.relative_to(root).as_posix()})

    total_time = time.time() - t_start
    print(f"Evaluación ciega de Fase G completada en {total_time:.2f}s.")
    return out.relative_to(root).as_posix()


if __name__ == "__main__":
    ejecutar_fase_g()
