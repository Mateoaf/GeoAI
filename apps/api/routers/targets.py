"""
apps/api/routers/targets.py
Rutas para consulta, filtrado y descarga de zonas de prospectividad y priorización.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from ..data_loader import get_data_loader
from ..schemas.targets import TargetsResponse, TargetZone

router = APIRouter(tags=["Targets & Prioritization"])

@router.get("/api/targets", response_model=TargetsResponse)
def get_targets(
    categoria: str | None = Query(None, description="Filtrar por 'prioridad_muy_alta_top01' o 'prioridad_alta_top05'"),
    distrito: str | None = Query(None, description="Filtrar por texto en distrito próximo"),
    min_score: float | None = Query(None, description="Score mínimo requerido"),
    sin_deposito_cercano: bool | None = Query(False, description="Si True, muestra targets alejados (>15 km) de depósitos conocidos (targets potencialmente novedosos)"),
    limit: int = Query(500, ge=1, le=1529),
    offset: int = Query(0, ge=0)
):
    loader = get_data_loader()
    df = loader.targets_df.copy()

    if categoria:
        df = df[df["categoria_prioridad"] == categoria]

    if distrito:
        df = df[df["distrito_conocido_proximo"].str.contains(distrito, case=False, na=False)]

    if min_score is not None:
        df = df[df["score_maximo"] >= min_score]

    if sin_deposito_cercano:
        # Distancia mayor a 15 km
        df = df[df["distancia_deposito_proximo_km"] >= 15.0]

    total_count = len(df)
    df_slice = df.iloc[offset : offset + limit]

    zones_list = [TargetZone(**row) for row in df_slice.to_dict(orient="records")]
    return TargetsResponse(total_count=total_count, zones=zones_list)


@router.get("/api/targets/geojson")
def get_targets_geojson():
    loader = get_data_loader()
    return JSONResponse(content=loader.zonas_geojson)


@router.get("/api/targets/{zona_id}", response_model=TargetZone)
def get_target_by_id(zona_id: str):
    loader = get_data_loader()
    df = loader.targets_df
    matches = df[df["zona_id"] == zona_id]

    if matches.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Zona de priorización '{zona_id}' no encontrada en el inventario de Fase H."
        )

    return TargetZone(**matches.iloc[0].to_dict())
