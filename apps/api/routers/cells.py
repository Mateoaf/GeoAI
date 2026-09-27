"""
apps/api/routers/cells.py
Rutas de inspección territorial y explicabilidad de celdas de 1 km².
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ..data_loader import get_data_loader
from ..services.explain_service import get_explain_service
from ..schemas.cell import CellResponse, CellInfo
from ..schemas.explain import CellExplainResponse

router = APIRouter(tags=["Cell Inspection"])

@router.get("/api/cell/by-coordinate", response_model=CellResponse)
def get_cell_by_coordinate(
    lat: float = Query(..., description="Latitud en WGS84", ge=34.0, le=45.0),
    lon: float = Query(..., description="Longitud en WGS84", ge=-10.0, le=5.0)
):
    loader = get_data_loader()
    cell_id = loader.coordinate_to_cell_id(lat=lat, lon=lon)

    query_coords = {"lat": lat, "lon": lon}

    if not cell_id:
        return CellResponse(
            eligible=False,
            cell=None,
            query_coordinates=query_coords
        )

    cell_data = loader.get_cell_info(cell_id)
    if not cell_data:
        # La celda existe en la cuadrícula teórica pero es NoData (mar o excluida por falta de 56 variables)
        return CellResponse(
            eligible=False,
            cell=None,
            query_coordinates=query_coords
        )

    cell_info = CellInfo(**cell_data)
    return CellResponse(
        eligible=True,
        cell=cell_info,
        query_coordinates=query_coords
    )


@router.get("/api/cell/{cell_id}", response_model=CellResponse)
def get_cell_by_id(cell_id: str):
    loader = get_data_loader()
    cell_data = loader.get_cell_info(cell_id)

    if not cell_data:
        raise HTTPException(
            status_code=404,
            detail=f"Celda '{cell_id}' no encontrada o no pertenece a la máscara canónica eligible_approved_features."
        )

    return CellResponse(
        eligible=True,
        cell=CellInfo(**cell_data),
        query_coordinates=None
    )


@router.get("/api/cell/{cell_id}/explain", response_model=CellExplainResponse)
def explain_cell(cell_id: str):
    explain_service = get_explain_service()
    explanation = explain_service.explain_cell(cell_id)

    if not explanation:
        raise HTTPException(
            status_code=404,
            detail=f"No se pudieron calcular las contribuciones para la celda '{cell_id}'."
        )

    return CellExplainResponse(explanation=explanation)
