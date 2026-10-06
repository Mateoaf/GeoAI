"""
apps/api/schemas/copilot.py
Modelos Pydantic para el copiloto determinista de GeoAI-Au.
"""

from typing import Any

from pydantic import BaseModel, Field

from .common import BaseResponse


class CopilotQuery(BaseModel):
    query: str = Field(..., description="Texto de la consulta o intención seleccionada")
    context: dict[str, Any] | None = Field(default_factory=dict, description="Contexto actual (celda seleccionada, zona activa, etc.)")

class CopilotAction(BaseModel):
    action_type: str = Field(..., description="Tipo de acción: zoom_to_cell, zoom_to_zone, select_tab, highlight_feature")
    payload: dict[str, Any] = Field(default_factory=dict, description="Datos de la acción")

class CopilotResponse(BaseResponse):
    query: str
    answer_markdown: str = Field(..., description="Respuesta geocientífica estructurada en Markdown")
    sources: list[str] = Field(default_factory=list, description="Artefactos y fuentes científicas consultadas")
    suggested_queries: list[str] = Field(default_factory=list, description="Consultas de seguimiento sugeridas")
    action: CopilotAction | None = Field(None, description="Acción interactiva disparada en el frontend")
