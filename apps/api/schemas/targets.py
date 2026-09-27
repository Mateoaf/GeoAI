"""
apps/api/schemas/targets.py
Modelos Pydantic para zonas de prospectividad y priorización territorial.
"""

from pydantic import BaseModel, Field

from .common import BaseResponse


class TargetZone(BaseModel):
    zona_id: str = Field(..., description="Identificador único de la zona de priorización")
    denominacion: str = Field(..., description="Nombre formal de la zona de priorización")
    categoria_prioridad: str = Field(..., description="Categoría de prospección: prioridad_muy_alta_top01 o prioridad_alta_top05")
    ranking_nacional: int = Field(..., description="Posición en el ranking nacional de prospectividad (1 a 1529)")
    score_maximo: float = Field(..., description="Score continuo máximo alcanzado dentro del clúster")
    score_medio: float = Field(..., description="Score continuo promedio de las celdas del clúster")
    area_km2: float = Field(..., description="Extensión territorial de la zona en kilómetros cuadrados")
    celdas_count: int = Field(..., description="Número de celdas de 1 km² que componen la zona")
    centroide_x: float = Field(..., description="Coordenada X del centroide en EPSG:25830")
    centroide_y: float = Field(..., description="Coordenada Y del centroide en EPSG:25830")
    deposito_conocido_proximo: str = Field(..., description="Depósito aurífero del inventario auditado más cercano")
    distrito_conocido_proximo: str = Field(..., description="Distrito metalogenético más próximo")
    distancia_deposito_proximo_km: float = Field(..., description="Distancia euclídea al depósito histórico más cercano en km")
    anotacion_post_hoc: str = Field(
        default="Anotación descriptiva post-hoc: la distancia a depósitos históricos no intervino en el cálculo del score.",
        description="Aclaración metodológica obligatoria sobre la independencia de la predicción."
    )

class TargetsResponse(BaseResponse):
    total_count: int = Field(..., description="Número total de zonas tras filtros")
    zones: list[TargetZone] = Field(..., description="Lista de zonas de prospectividad")
