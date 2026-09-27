"""
apps/api/schemas/explain.py
Modelos Pydantic para explicabilidad local aditiva exacta (beta * z).
"""

from typing import List
from pydantic import BaseModel, Field
from .common import BaseResponse

class FeatureContribution(BaseModel):
    variable: str = Field(..., description="Nombre técnico de la variable")
    familia: str = Field(..., description="Familia geológica (Litología, Edades, Estructuras, Relieve, Hidrología)")
    raw_value: float = Field(..., description="Valor original de la variable en la celda")
    standardized_z: float = Field(..., description="Valor estandarizado con StandardScaler (z-score)")
    coefficient: float = Field(..., description="Coeficiente estandarizado beta_i del modelo logístico")
    contribution: float = Field(..., description="Contribución local aditiva: beta_i * z_i")
    odds_ratio: float = Field(..., description="Odds ratio por incremento de 1 desviación estándar")
    significado_geologico: str = Field(..., description="Interpretación geocientífica de la variable")

class CellExplanation(BaseModel):
    cell_id: str = Field(..., description="Identificador de la celda explicada")
    prospectivity_score: float = Field(..., description="Score continuo predicho por el modelo en (0, 1)")
    intercept: float = Field(..., description="Intercepto beta_0 del modelo logístico")
    logit_calculated: float = Field(..., description="Logit calculado: intercept + sum(beta_i * z_i)")
    logit_decision_function: float = Field(..., description="Logit devuelto por model.decision_function")
    consistency_error: float = Field(..., description="Diferencia absoluta entre logit calculado y decision_function")
    consistency_test_passed: bool = Field(..., description="True si abs(logit_calc - decision_function) < 1e-6")
    sigmoid_score: float = Field(..., description="Score calculado mediante función sigmoide: 1 / (1 + exp(-logit))")
    top_positive_contributions: List[FeatureContribution] = Field(..., description="Factores que más aumentan la favorabilidad")
    top_negative_contributions: List[FeatureContribution] = Field(..., description="Factores que más reducen la favorabilidad")
    all_contributions: List[FeatureContribution] = Field(..., description="Descomposición aditiva completa de las 56 variables")

class CellExplainResponse(BaseResponse):
    explanation: CellExplanation
