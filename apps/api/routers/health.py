"""
apps/api/routers/health.py
Ruta de healthcheck y verificación de estado.
"""

from fastapi import APIRouter
from ..data_loader import get_data_loader

router = APIRouter(tags=["Health"])

@router.get("/api/health")
def healthcheck():
    loader = get_data_loader()
    return {
        "status": "healthy",
        "service": "GeoAI-Au Explorer Backend",
        "version": "v1.0",
        "scientific_release": "GeoAI-Au v1.0 (España peninsular)",
        "cells_indexed": len(loader.cell_lookup),
        "zones_count": len(loader.targets_df) if loader.targets_df is not None else 0,
        "features_loaded": len(loader.approved_columns)
    }
