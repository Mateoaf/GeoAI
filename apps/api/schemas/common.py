"""
apps/api/schemas/common.py
Esquemas y guardarraíles comunes para GeoAI-Au Explorer.
"""

from pydantic import BaseModel, Field

SCIENTIFIC_DISCLAIMER = (
    "Score relativo de prospectividad y favorabilidad geológica. "
    "No representa probabilidad calibrada de existencia de un depósito ni cubicación de recursos o reservas."
)

class BaseResponse(BaseModel):
    disclaimer: str = Field(default=SCIENTIFIC_DISCLAIMER, description="Guardarraíl metodológico y delimitación científica.")
