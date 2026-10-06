"""
apps/api/schemas/cell.py
Modelos Pydantic para inspección territorial de celdas de 1 km².
"""


from pydantic import BaseModel, Field

from .common import BaseResponse


class CellInfo(BaseModel):
    cell_id: str = Field(..., description="Identificador único determinista de la celda de 1 km²")
    row: int = Field(..., description="Fila en la rejilla nacional (0 a 909)")
    col: int = Field(..., description="Columna en la rejilla nacional (0 a 1099)")
    score: float = Field(..., description="Prospectivity/Favorability score en (0, 1)")
    percentile_favorabilidad: float = Field(..., description="Percentil territorial nacional [0, 100]")
    prioridad_banda: str = Field(..., description="Banda de prioridad de exploración: top_01, top_05, top_10, resto")
    land_area_m2: float = Field(..., description="Superficie terrestre válida de la celda en m²")
    x_epsg25830: float = Field(..., description="Coordenada X este en EPSG:25830")
    y_epsg25830: float = Field(..., description="Coordenada Y norte en EPSG:25830")
    lon_wgs84: float = Field(..., description="Longitud geográfica en WGS84")
    lat_wgs84: float = Field(..., description="Latitud geográfica en WGS84")
    deposit_id: str | None = Field(None, description="Depósito mineral confirmado si existe presencia en la celda")
    district_id: str | None = Field(None, description="Distrito metalogenético asignado a la celda")
    favorabilidad_pu_media: float | None = Field(None, description="Score calibrado de favorabilidad PU Learning v3.0 [0, 1]")
    incertidumbre_std: float | None = Field(None, description="Incertidumbre epistémica std (desviación del ensamble bagging) v3.0")
    categoria_fiabilidad: str | None = Field(None, description="Categoría de la matriz de fiabilidad territorial 2D (ej. 'Alta Favorabilidad + Alta Certeza (Prioridad A)')")
    es_extrapolacion: bool | None = Field(None, description="Indica si la celda cae en extrapolación fuera de distribución (> 3 sigma)")
    distancia_dominio_z: float | None = Field(None, description="Distancia multivariante normalizada Z al centroide de mineralizaciones conocidas")

class CellResponse(BaseResponse):
    eligible: bool = Field(..., description="Indica si la celda pertenece a la máscara canónica eligible_approved_features")
    cell: CellInfo | None = Field(None, description="Datos detallados de la celda si es elegible")
    query_coordinates: dict | None = Field(None, description="Coordenadas originales de la consulta")
