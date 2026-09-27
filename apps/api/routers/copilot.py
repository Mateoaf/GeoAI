"""
apps/api/routers/copilot.py
Ruta para el copiloto determinista de GeoAI-Au.
"""

from fastapi import APIRouter
from ..schemas.copilot import CopilotQuery, CopilotResponse
from ..services.copilot_service import get_copilot_service

router = APIRouter(tags=["GeoAI Copilot"])

@router.post("/api/copilot/query", response_model=CopilotResponse)
def query_copilot(query: CopilotQuery):
    copilot = get_copilot_service()
    return copilot.answer(query)
