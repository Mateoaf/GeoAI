"""
apps/api/calibration.py
Calibracion monotona (Platt sobre logit) del score de favorabilidad.

Los parametros se generan con scripts/calibrar_score_favorabilidad.py a partir de las
predicciones fuera de muestra (CV espacial con buffer de 15 km) y se guardan en
reports/geoquimica_20261017/calibracion_score.json.

La transformacion es estrictamente monotona: preserva el ranking, los percentiles y las
bandas Top 1/5/10 %. Si el JSON no existe o GEOAI_SCORE_MODE=raw, actua como identidad.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any

import numpy as np

from . import config

_EPS = 1e-4


@lru_cache(maxsize=1)
def _params() -> dict[str, Any] | None:
    if os.getenv("GEOAI_SCORE_MODE", "calibrated").lower() == "raw":
        return None
    if not config.PATH_CALIBRATION_JSON.exists():
        return None
    with open(config.PATH_CALIBRATION_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not {"a", "b"} <= data.keys() or float(data["a"]) <= 0:
        return None
    return data


def is_active() -> bool:
    return _params() is not None


def calibrate(score: Any) -> Any:
    """Convierte el score bruto en favorabilidad calibrada. Admite escalares y arrays."""
    p = _params()
    if p is None:
        return score
    s = np.clip(np.asarray(score, dtype="float64"), _EPS, 1.0 - _EPS)
    z = float(p["a"]) * np.log(s / (1.0 - s)) + float(p["b"])
    out = 1.0 / (1.0 + np.exp(-z))
    return float(out) if np.ndim(out) == 0 else out


def display_floor(default_raw: float = 0.06) -> float:
    """Umbral de visibilidad del tile equivalente al historico (0.06) en la escala activa."""
    return float(calibrate(default_raw))
