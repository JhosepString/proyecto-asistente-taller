"""
Esquemas Pydantic para el modulo de Alertas de Stock Minimo.
"""

from typing import List, Optional
from pydantic import BaseModel


class AlertaItem(BaseModel):
    """Representa una alerta de repuesto bajo o igual al stock minimo (Requisito 4.2)."""

    nombre: str
    codigo: str
    cantidad: int
    stock_minimo: int


class AlertasRespuesta(BaseModel):
    """Respuesta del endpoint de alertas."""

    alertas: List[AlertaItem]
    mensaje: Optional[str] = None
