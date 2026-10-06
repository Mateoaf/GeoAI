"""
apps/api/main.py
Punto de entrada principal de FastAPI para GeoAI-Au Explorer Backend.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .data_loader import get_data_loader
from .routers import (
    cells,
    copilot,
    deposits,
    health,
    model,
    summary,
    targets,
    tiles,
    validation,
)
from .services.explain_service import get_explain_service
from .services.tile_service import get_tile_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("geoau_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando servicios de GeoAI-Au Explorer Backend...")
    # Precargar datos y modelos
    loader = get_data_loader()
    _ = get_tile_service()
    _ = get_explain_service()
    logger.info(f"Servicios listos. {len(loader.cell_lookup):,} celdas indexadas.")
    yield
    logger.info("Cerrando servicios de GeoAI-Au Explorer Backend.")


app = FastAPI(
    title="GeoAI-Au Explorer API",
    description=(
        "API geoespacial y de inteligencia mineral para España peninsular basada en GeoAI-Au v1.0.\n\n"
        "**Guardarraíl Metodológico**: Las puntuaciones representan índices relativos de favorabilidad geológica. "
        "No constituyen estimaciones de recursos, reservas ni probabilidades físicas calibradas de existencia de oro."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de Routers
app.include_router(health.router)
app.include_router(summary.router)
app.include_router(cells.router)
app.include_router(targets.router)
app.include_router(validation.router)
app.include_router(model.router)
app.include_router(tiles.router)
app.include_router(deposits.router)
app.include_router(copilot.router)


@app.get("/")
def root():
    return {
        "system": "GeoAI-Au Explorer API",
        "version": "v1.0",
        "documentation": "/api/docs",
        "status": "operational"
    }
