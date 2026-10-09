"""
Esquemas Pydantic para el modulo de Comparacion de Conteo Fisico.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ItemConteo(BaseModel):
    """Representa un item ingresado en el conteo fisico manual."""

    codigo: str = Field(..., min_length=1, max_length=20, description="Codigo del repuesto")
    conteo_fisico: int = Field(..., ge=0, description="Cantidad fisica contada")


class SolicitudComparacion(BaseModel):
    """Cuerpo de solicitud para realizar la comparacion."""

    items: List[ItemConteo] = Field(..., min_length=1, description="Lista de repuestos a comparar (minimo 1)")


class ResultadoComparacionItem(BaseModel):
    """Resultado individual de comparacion con calculo de diferencia y descuadre."""

    nombre: str
    codigo: str
    sistema: int
    conteo: int
    diferencia: int
    descuadre: bool


class ComparacionRespuesta(BaseModel):
    """Respuesta con los resultados de la comparacion."""

    resultados: List[ResultadoComparacionItem]
    mensaje: Optional[str] = None
