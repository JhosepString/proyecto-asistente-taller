"""
Esquemas Pydantic para el modulo de Historial de Cliente y Vehiculo.
"""

from typing import List, Optional
from pydantic import BaseModel


class OTHistorialItem(BaseModel):
    """Representa una Orden de Trabajo en la lista de historial."""

    id: int
    fecha: str
    motivo: str
    tecnico: str
    estado: str
    observaciones: Optional[str] = ""


class HistorialRespuesta(BaseModel):
    """Respuesta del endpoint de busqueda de historial."""

    ordenes: List[OTHistorialItem]
    mensaje: Optional[str] = None
