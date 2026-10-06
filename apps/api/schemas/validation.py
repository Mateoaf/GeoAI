"""
apps/api/schemas/validation.py
Modelos Pydantic para métricas de evaluación ciega en holdout (Fase G).
Basado estrictamente en los esquemas reales de Fase G.
"""

from typing import Any

from pydantic import BaseModel, Field

from .common import BaseResponse


class HoldoutMetricsSummary(BaseModel):
    holdout_cells: int = Field(..., description="Total de celdas de la reserva ciega (13.541)")
    observed_P_cells: int = Field(..., description="Celdas positivas observadas en el holdout (19)")
    observed_deposits: int = Field(..., description="Depósitos independientes de test en el holdout (8)")
    districts_count: int = Field(..., description="Distritos reservados en cuarentena (5)")
    deposit_recovery_at_01: float = Field(..., description="Tasa de recuperación de depósitos en Top 1%")
    deposit_recovery_at_05: float = Field(..., description="Tasa de recuperación de depósitos en Top 5%")
    deposit_recovery_at_10: float = Field(..., description="Tasa de recuperación de depósitos en Top 10%")
    cell_recovery_at_01: float = Field(..., description="Tasa de recuperación de celdas positivas en Top 1%")
    cell_recovery_at_05: float = Field(..., description="Tasa de recuperación de celdas positivas en Top 5%")
    cell_recovery_at_10: float = Field(..., description="Tasa de recuperación de celdas positivas en Top 10%")
    roc_auc_PU: float = Field(..., description="Área bajo la curva ROC en evaluación ciega P/U")
    average_precision_PU: float = Field(..., description="Área bajo la curva Precision-Recall (Average Precision)")
    transfer_gap_note: str = Field(
        default="Brecha de transferencia observada: rendimiento en holdout independiente limitado a N=8 depósitos; alta incertidumbre estadística.",
        description="Declaración metodológica de honestidad intelectual."
    )
    bootstrap_uncertainty_ci95: dict[str, Any] = Field(..., description="Intervalos de confianza bootstrap al 95% para N=8 depósitos")

class ValidationSummaryResponse(BaseResponse):
    summary: HoldoutMetricsSummary

class HoldoutDepositItem(BaseModel):
    deposit_id: str
    district_id: str
    p_cells_count: int
    max_score: float
    mean_score: float
    best_rank_in_holdout: int
    best_area_fraction: float
    best_percentile_favorability: float
    recovered_at_01: bool
    recovered_at_05: bool
    recovered_at_10: bool

class ValidationDepositsResponse(BaseResponse):
    deposits: list[HoldoutDepositItem]

class HoldoutDistrictItem(BaseModel):
    district_id: str
    unit_id: str
    total_cells: int
    p_cells: int
    n_deposits: int
    deposits_list: str
    score_mean: float
    score_median: float
    score_max: float
    deposits_recovered_at_01: int
    deposit_recovery_rate_at_01: float
    deposits_recovered_at_05: int
    deposit_recovery_rate_at_05: float
    deposits_recovered_at_10: int
    deposit_recovery_rate_at_10: float
    cells_recovered_at_01: int
    cells_recovered_at_05: int
    cells_recovered_at_10: int

class ValidationDistrictsResponse(BaseResponse):
    districts: list[HoldoutDistrictItem]
