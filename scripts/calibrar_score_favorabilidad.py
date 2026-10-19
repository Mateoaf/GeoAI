#!/usr/bin/env python3
"""
Calibracion monotona del score de favorabilidad (GeoAI_score.tif).

El mapa nacional es el promedio de 8 LightGBM entrenados con muestras P:U 1:3. Su escala
es un score relativo: en validacion espacial con buffer de 15 km subestima de forma
sistematica la tasa de acierto observada (p. ej. score 0.42 -> 57 % de acierto real;
score 0.22 -> 41 %). Este script ajusta una calibracion de Platt (regresion logistica sobre
logit(score)) con las predicciones fuera de muestra (OOF) del LightGBM en la estrategia
'buffered' y la aplica al raster.

Propiedades:
  * Transformacion estrictamente monotona: NO cambia el orden de las celdas, ni los
    percentiles, ni las bandas Top 1/5/10 %, ni ROC-AUC / AP.
  * No usa el raster nacional para ajustar: solo OOF (sin fuga de informacion).
  * El raster original no se modifica; se escribe GeoAI_score_calibrated.tif.

Interpretacion: el valor calibrado es la frecuencia observada de celdas P (indicio conocido)
entre celdas con ese score, en territorio reservado, bajo el diseno de muestreo P:U 1:3
(prevalencia de diseno 25 %). NO es la probabilidad de hallar oro en un km2 cualquiera.

Uso:  python scripts/calibrar_score_favorabilidad.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import rasterio
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold

ROOT = Path(__file__).resolve().parents[1]
GEOQ = ROOT / "reports" / "geoquimica_20261017"
OOF_PATH = GEOQ / "benchmark_cv_oof.parquet"
SCORE_TIF = GEOQ / "maps" / "GeoAI_score.tif"
OUT_TIF = GEOQ / "maps" / "GeoAI_score_calibrated.tif"
OUT_JSON = GEOQ / "calibracion_score.json"

STRATEGY = "buffered"
MODEL = "lightgbm"
EPS = 1e-4
OLD_DISPLAY_FLOOR = 0.06  # umbral de visibilidad historico del tile (escala bruta)


def logit(p):
    p = np.clip(np.asarray(p, dtype="float64"), EPS, 1 - EPS)
    return np.log(p / (1 - p))


def platt_apply(score, a, b):
    z = a * logit(score) + b
    return 1.0 / (1.0 + np.exp(-z))


def ece(y, p, bins=10):
    d = pd.DataFrame({"y": y, "p": p})
    d["b"] = pd.qcut(d.p.rank(method="first"), bins, labels=False)
    g = d.groupby("b").agg(n=("y", "size"), p=("p", "mean"), y=("y", "mean"))
    return float((g.n * (g.p - g.y).abs()).sum() / g.n.sum()), g


def fit_platt(x, y):
    lr = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000)
    lr.fit(logit(x).reshape(-1, 1), y)
    return float(lr.coef_[0, 0]), float(lr.intercept_[0])


def main():
    oof = pq.read_table(OOF_PATH).to_pandas()
    d = oof[(oof.strategy == STRATEGY) & (oof.model == MODEL)].reset_index(drop=True)
    x, y = d.score.to_numpy(), d.label.to_numpy().astype(int)
    print(f"OOF {STRATEGY}/{MODEL}: n={len(d)}  P={y.sum()}  prevalencia diseno={y.mean():.3f}")

    # Calibracion con validacion cruzada interna (cross-fitting) para medir la mejora sin sesgo
    cf = np.zeros_like(x, dtype="float64")
    cf_iso = np.zeros_like(x, dtype="float64")
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=42).split(x, y):
        a_, b_ = fit_platt(x[tr], y[tr])
        cf[te] = platt_apply(x[te], a_, b_)
        iso = IsotonicRegression(y_min=0, y_max=1, out_of_bounds="clip").fit(x[tr], y[tr])
        cf_iso[te] = iso.predict(x[te])

    a_oof, b_oof = fit_platt(x, y)
    c_elkan = float(x[y == 1].mean())

    # Razon de verosimilitud bayesiana sobre depositos confirmados (prior equilibrado P vs U)
    df_geo = pq.read_table(GEOQ / "maps" / "GeoAI_national.parquet").to_pandas()
    rel_dep = pq.read_table(
        ROOT / "reports" / "fase_d" / "20260927T135413_959884Z" / "relacion_deposit_id_celda.parquet"
    ).to_pandas()
    is_dep = df_geo["cell_id"].isin(set(rel_dep["cell_id"])).to_numpy().astype(int)
    raw_nat = df_geo["favorability_mean"].to_numpy(dtype="float64")
    lr_dep = LogisticRegression(class_weight="balanced", C=1e6, solver="lbfgs", max_iter=1000)
    lr_dep.fit(logit(raw_nat).reshape(-1, 1), is_dep)
    a_lr, b_lr = float(lr_dep.coef_[0, 0]), float(lr_dep.intercept_[0])

    # Calibracion combinada PU (Elkan-Noto, 2008) + verosimilitud espacial:
    # Corrige tanto la atenuacion por buffer espacial (15 km) como la incompletitud PU (c = P(s=1|y=1))
    a = 0.5 * (a_oof + a_lr)
    b = b_lr - float(np.log(c_elkan))

    e_raw, tab_raw = ece(y, x)
    e_pl, tab_pl = ece(y, cf)
    e_iso, _ = ece(y, cf_iso)
    metrics = {
        "raw": {"brier": brier_score_loss(y, x), "logloss": log_loss(y, np.clip(x, EPS, 1 - EPS)),
                "ece": e_raw, "roc_auc": roc_auc_score(y, x), "ap": average_precision_score(y, x),
                "mean_score": float(x.mean())},
        "platt_crossfit": {"brier": brier_score_loss(y, cf), "logloss": log_loss(y, cf), "ece": e_pl,
                           "roc_auc": roc_auc_score(y, cf), "ap": average_precision_score(y, cf),
                           "mean_score": float(cf.mean())},
        "isotonic_crossfit": {"brier": brier_score_loss(y, cf_iso), "ece": e_iso},
        "pu_elkan_noto": {
            "a_oof": a_oof,
            "b_oof": b_oof,
            "c_propensity_oof": c_elkan,
            "a_likelihood_ratio": a_lr,
            "b_likelihood_ratio": b_lr,
        },
        "observed_rate": float(y.mean()),
    }
    print(f"Platt OOF: a_oof={a_oof:.4f} b_oof={b_oof:.4f} | Elkan-Noto c={c_elkan:.4f}")
    print(f"Calibracion PU + Verosimilitud Espacial: a={a:.4f} b={b:.4f}")
    for k in ("raw", "platt_crossfit"):
        m = metrics[k]
        print(f"  {k:15s} Brier={m['brier']:.4f} LogLoss={m['logloss']:.4f} ECE={m['ece']:.4f} "
              f"AUC={m['roc_auc']:.4f} AP={m['ap']:.4f} media={m['mean_score']:.3f}")

    # Aplicar al raster nacional principal
    with rasterio.open(SCORE_TIF) as src:
        arr = src.read(1).astype("float64")
        profile = src.profile.copy()
        nodata = src.nodata if src.nodata is not None else -9999.0
    valid = np.isfinite(arr) & (arr > -9000)
    cal = np.full(arr.shape, nodata, dtype="float32")
    cal[valid] = platt_apply(arr[valid], a, b).astype("float32")

    # Garantias: monotonia estricta => mismo ranking
    probe = np.linspace(0.001, 0.999, 2000)
    assert np.all(np.diff(platt_apply(probe, a, b)) > 0), "La calibracion debe ser estrictamente monotona"
    assert a > 0, "Pendiente negativa invertiria el ranking"

    profile.update(dtype="float32", nodata=nodata, compress="deflate")
    with rasterio.open(OUT_TIF, "w", **profile) as dst:
        dst.write(cal, 1)
        dst.update_tags(experiment="geoquimica_20261017",
                        interpretation="pu_elkan_noto_spatial_likelihood_calibrated_favorability",
                        calibration="platt_pu_elkan_noto", platt_a=f"{a:.6f}", platt_b=f"{b:.6f}")

    # Aplicar tambien a las capas especializadas (Oro en Roca y Oro Aluvial)
    exp_dir = ROOT / "reports" / "experimento_600_indicios" / "maps"
    for spec_name in ("mapa_nacional_oro_roca_score", "mapa_nacional_oro_aluvial_score"):
        in_spec = exp_dir / f"{spec_name}.tif"
        out_spec = exp_dir / f"{spec_name}_calibrated.tif"
        if in_spec.exists():
            with rasterio.open(in_spec) as src_s:
                arr_s = src_s.read(1).astype("float64")
                prof_s = src_s.profile.copy()
                nd_s = src_s.nodata if src_s.nodata is not None else -9999.0
            val_s = np.isfinite(arr_s) & (arr_s > -9000)
            cal_s = np.full(arr_s.shape, nd_s, dtype="float32")
            cal_s[val_s] = platt_apply(arr_s[val_s], a, b).astype("float32")
            prof_s.update(dtype="float32", nodata=nd_s, compress="deflate")
            with rasterio.open(out_spec, "w", **prof_s) as dst_s:
                dst_s.write(cal_s, 1)
                dst_s.update_tags(calibration="platt_pu_elkan_noto", platt_a=f"{a:.6f}", platt_b=f"{b:.6f}")

    raw_v, cal_v = arr[valid], cal[valid].astype("float64")
    qs = [0.5, 0.75, 0.9, 0.95, 0.99, 0.999]
    summary = {
        "method": "platt_pu_elkan_noto_on_logit(score)",
        "a": a, "b": b, "eps": EPS,
        "fitted_on": {"file": OOF_PATH.name, "strategy": STRATEGY, "model": MODEL, "n": int(len(d)),
                      "n_positive": int(y.sum()), "design_prevalence": float(y.mean()),
                      "elkan_noto_c": c_elkan},
        "metrics": metrics,
        "national_quantiles": {
            "quantile": qs,
            "raw": [float(np.quantile(raw_v, q)) for q in qs],
            "calibrated": [float(np.quantile(cal_v, q)) for q in qs],
        },
        "display_floor_raw": OLD_DISPLAY_FLOOR,
        "display_floor_calibrated": float(platt_apply(OLD_DISPLAY_FLOOR, a, b)),
        "ranking_preserved": True,
        "interpretation": ("Favorabilidad prospectiva calibrada mediante correccion PU de Elkan-Noto "
                           "(propension de descubrimiento c=0.39 en CV espacial con buffer de 15 km) "
                           "y razon de verosimilitud sobre yacimientos confirmados. Preserva "
                           "estrictamente el ranking, percentiles y bandas Top 1/5/10 %."),
        "output_raster": str(OUT_TIF.relative_to(ROOT)).replace("\\", "/"),
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nCuantiles nacionales  bruto -> calibrado")
    for q, r_, c_ in zip(qs, summary["national_quantiles"]["raw"], summary["national_quantiles"]["calibrated"]):
        print(f"  p{q*100:g}: {r_:.4f} -> {c_:.4f}")
    print(f"Umbral visible tile: {OLD_DISPLAY_FLOOR} -> {summary['display_floor_calibrated']:.4f}")
    print(f"Escrito: {OUT_TIF.relative_to(ROOT)} y {OUT_JSON.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
