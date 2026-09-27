"""
apps/api/routers/tiles.py
Rutas para servir teselas ráster Web Mercator (EPSG:3857) a MapLibre.
"""

from fastapi import APIRouter, HTTPException, Response

from ..services.tile_service import get_tile_service

router = APIRouter(tags=["Map Tiles"])

@router.get(
    "/api/tiles/{layer}/{z}/{x}/{y}.png",
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "Retorna imagen PNG de 256x256 con transparencia"
        }
    }
)
def get_tile(layer: str, z: int, x: int, y: int):
    valid_layers = ("score", "percentile", "priority", "global_v2_score", "rock_score", "alluvial_score")
    if layer not in valid_layers:
        raise HTTPException(
            status_code=400,
            detail=f"Capa '{layer}' no válida. Opciones: {', '.join(valid_layers)}."
        )

    tile_service = get_tile_service()
    png_bytes = tile_service.render_tile(layer=layer, z=z, x=x, y=y)

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=86400, immutable"
        }
    )
