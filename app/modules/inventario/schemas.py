"""
Esquemas Pydantic para el modulo de Inventario y Consulta de Stock.
"""

from typing import List, Optional
from pydantic import BaseModel


class RepuestoStockItem(BaseModel):
    """Representa el stock de un repuesto con exactamente los 4 campos requeridos (Requisito 3.2)."""

    nombre: str
    codigo: str
    cantidad: int
    unidad: str


class InventarioRespuesta(BaseModel):
    """Respuesta para busquedas de inventario."""

    resultados: List[RepuestoStockItem]
    mensaje: Optional[str] = None
