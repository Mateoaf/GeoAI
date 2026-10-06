"""
apps/api/schemas/summary.py
Modelos Pydantic para el resumen global del proyecto y metadatos de release.
"""

from pydantic import BaseModel, Field

from .common import BaseResponse


class ThresholdsSummary(BaseModel):
    top_01: float = Field(..., description="Umbral de corte de score para banda Top 1% (área acumulada)")
    top_05: float = Field(..., description="Umbral de corte de score para banda Top 5% (área acumulada)")
    top_10: float = Field(..., description="Umbral de corte de score para banda Top 10% (área acumulada)")

class ProjectSummary(BaseModel):
    project_name: str = Field(default="GeoAI-Au", description="Nombre del sistema")
    tagline: str = Field(default="Mineral Prospectivity Intelligence — España Peninsular", description="Subtítulo oficial")
    release_version: str = Field(default="v1.0", description="Versión científica sellada")
    is_scientific_release: bool = Field(default=True, description="Indica versión inmutable sellada")
    model_name: str = Field(..., description="Identificador del modelo congelado (logistic_01)")
    model_family: str = Field(..., description="Familia de algoritmo: Logistic Regression (L2, C=0.1)")
    resolution: str = Field(default="1 km x 1 km (100 hectáreas)", description="Resolución territorial de celda")
    crs: str = Field(default="EPSG:25830 (ETRS89 / UTM 30N)", description="Sistema de referencia oficial")
    region: str = Field(default="España peninsular", description="Dominio geográfico modelado")
    eligible_cells_count: int = Field(..., description="Total de celdas en la máscara canónica (478.443)")
    features_count: int = Field(default=56, description="Número de predictores auditados y aprobados")
    prioritized_zones_count: int = Field(..., description="Total de zonas de prospectividad delimitadas (1.529)")
    thresholds: ThresholdsSummary = Field(..., description="Umbrales canónicos de corte de favorabilidad")
    run_ids: dict[str, str] = Field(..., description="Identificadores canónicos de ejecución de Fases D a H")

class ProjectSummaryResponse(BaseResponse):
    summary: ProjectSummary
