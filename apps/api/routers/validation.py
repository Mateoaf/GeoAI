"""
apps/api/routers/validation.py
Rutas para consulta de métricas de validación ciega en holdout (Fase G).
"""

import pandas as pd
from fastapi import APIRouter

from ..data_loader import get_data_loader
from ..schemas.validation import (
    HoldoutDepositItem,
    HoldoutDistrictItem,
    HoldoutMetricsSummary,
    ValidationDepositsResponse,
    ValidationDistrictsResponse,
    ValidationSummaryResponse,
)

router = APIRouter(tags=["Validation & Holdout"])

@router.get("/api/validation/summary", response_model=ValidationSummaryResponse)
def get_validation_summary():
    loader = get_data_loader()
    val = loader.validation_summary
    boot = loader.validation_bootstrap

    summary = HoldoutMetricsSummary(
        holdout_cells=int(val.get("holdout_cells", 13541)),
        observed_P_cells=int(val.get("observed_P_cells", 19)),
        observed_deposits=int(val.get("observed_deposits", 8)),
        districts_count=int(val.get("districts_count", 5)),
        deposit_recovery_at_01=float(val.get("deposit_recovery_at_01", 0.125)),
        deposit_recovery_at_05=float(val.get("deposit_recovery_at_05", 0.125)),
        deposit_recovery_at_10=float(val.get("deposit_recovery_at_10", 0.250)),
        cell_recovery_at_01=float(val.get("cell_recovery_at_01", 0.1579)),
        cell_recovery_at_05=float(val.get("cell_recovery_at_05", 0.1579)),
        cell_recovery_at_10=float(val.get("cell_recovery_at_10", 0.2105)),
        roc_auc_PU=float(val.get("roc_auc_PU", 0.5807)),
        average_precision_PU=float(val.get("average_precision_PU", 0.0065)),
        bootstrap_uncertainty_ci95=boot
    )
    return ValidationSummaryResponse(summary=summary)


@router.get("/api/validation/deposits", response_model=ValidationDepositsResponse)
def get_validation_deposits():
    loader = get_data_loader()
    df = loader.validation_deposits_df
    if df is None:
        return ValidationDepositsResponse(deposits=[])
    items = [HoldoutDepositItem(**row) for row in df.to_dict(orient="records")]
    return ValidationDepositsResponse(deposits=items)


@router.get("/api/validation/districts", response_model=ValidationDistrictsResponse)
def get_validation_districts():
    loader = get_data_loader()
    df = loader.validation_districts_df
    if df is None:
        return ValidationDistrictsResponse(districts=[])
    items = [HoldoutDistrictItem(**row) for row in df.to_dict(orient="records")]
    return ValidationDistrictsResponse(districts=items)


@router.get("/api/validation/comparison")
def get_validation_comparison():
    loader = get_data_loader()
    df = loader.validation_comparison_df
    if df is None:
        records = []
    else:
        records = df.to_dict(orient="records")
        for r in records:
            for k, v in list(r.items()):
                if pd.isna(v):
                    r[k] = None
    return {
        "comparison": records,
        "transfer_gap_description": (
            "Diferencia observada entre la estimación OOF de desarrollo (Fase F) "
            "y la evaluación ciega territorial (Fase G). Refleja la heterogeneidad regional "
            "y metalogenética entre los 27 distritos de desarrollo y los 5 distritos de reserva."
        )
    }
