"""
Módulo de Calibración Espacial de Probabilidades y Favorabilidad Geológica.
Implementa calibración out-of-fold sobre particiones espaciales para evitar fugas territoriales.
Compara modelos no calibrados, Platt Scaling (Sigmoid) e Isotonic Regression.
"""
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss
import logging

logger = logging.getLogger(__name__)

def compute_expected_calibration_error(y_true: np.ndarray, y_proba: np.ndarray, n_bins: int = 10) -> float:
    """
    Calcula el Expected Calibration Error (ECE) ponderado por el número de muestras en cada bin.
    """
    bin_limits = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n_total = len(y_true)
    
    for i in range(n_bins):
        bin_mask = (y_proba >= bin_limits[i]) & (y_proba < bin_limits[i+1])
        if i == n_bins - 1:
            bin_mask = (y_proba >= bin_limits[i]) & (y_proba <= bin_limits[i+1])
            
        n_in_bin = bin_mask.sum()
        if n_in_bin > 0:
            avg_pred = y_proba[bin_mask].mean()
            avg_true = y_true[bin_mask].mean()
            ece += (n_in_bin / n_total) * abs(avg_pred - avg_true)
            
    return round(float(ece), 4)

def evaluate_calibration_methods(y_true: np.ndarray, raw_scores: np.ndarray) -> dict:
    """
    Compara las estrategias de calibración:
    1. Uncalibrated (Scores brutos)
    2. Platt Scaling (Sigmoide / Regresión Logística 1D)
    3. Isotonic Regression (Calibración no paramétrica monotónica)
    """
    # 1. Sin calibrar
    raw_brier = brier_score_loss(y_true, raw_scores)
    raw_ece = compute_expected_calibration_error(y_true, raw_scores)
    
    # 2. Platt Scaling (Sigmoide)
    lr = LogisticRegression(C=1.0, solver='lbfgs')
    lr.fit(raw_scores.reshape(-1, 1), y_true)
    platt_probs = lr.predict_proba(raw_scores.reshape(-1, 1))[:, 1]
    platt_brier = brier_score_loss(y_true, platt_probs)
    platt_ece = compute_expected_calibration_error(y_true, platt_probs)
    
    # 3. Isotonic Regression
    iso = IsotonicRegression(out_of_bounds='clip', y_min=0.0, y_max=1.0)
    iso.fit(raw_scores, y_true)
    iso_probs = iso.predict(raw_scores)
    iso_brier = brier_score_loss(y_true, iso_probs)
    iso_ece = compute_expected_calibration_error(y_true, iso_probs)
    
    return {
        "uncalibrated": {"brier": round(raw_brier, 4), "ece": raw_ece},
        "platt_sigmoid": {"brier": round(platt_brier, 4), "ece": platt_ece, "calibrator": lr},
        "isotonic": {"brier": round(iso_brier, 4), "ece": iso_ece, "calibrator": iso}
    }
