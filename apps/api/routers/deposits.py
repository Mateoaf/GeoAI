"""
apps/api/routers/deposits.py
Ruta para servir la capa vectorial de depósitos históricos auditados (Fase B).
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ..data_loader import get_data_loader

router = APIRouter(tags=["Mineral Deposits"])

@router.get("/api/deposits")
def get_deposits_geojson():
    loader = get_data_loader()
    return JSONResponse(content=loader.depositos_geojson)
