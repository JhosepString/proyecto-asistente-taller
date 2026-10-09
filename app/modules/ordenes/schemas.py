"""
Esquemas Pydantic para el modulo de Ordenes de Trabajo (OT).
Define las validaciones requeridas segun Requisito 1.3 y Requisito 1.4.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class OTCrear(BaseModel):
    """Modelo para la creacion de una nueva Orden de Trabajo."""

    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre del cliente")
    dni: str = Field(..., min_length=8, max_length=8, description="DNI del cliente (8 digitos numericos)")
    placa: str = Field(..., min_length=1, max_length=10, description="Placa del vehiculo")
    marca: str = Field(..., min_length=1, max_length=50, description="Marca del vehiculo")
    modelo: str = Field(..., min_length=1, max_length=50, description="Modelo del vehiculo")
    anio: int = Field(..., description="Anio del vehiculo (entre 1900 y anio en curso inclusive)")
    kilometraje: int = Field(..., ge=0, le=999999, description="Kilometraje entre 0 y 999999")
    motivo: str = Field(..., min_length=1, max_length=500, description="Motivo de ingreso")
    tecnico: str = Field(..., min_length=1, max_length=100, description="Nombre del tecnico asignado")
    observaciones: Optional[str] = Field(default=None, max_length=1000, description="Observaciones opcionales")

    @field_validator("dni")
    @classmethod
    def validar_dni(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit() or len(v) != 8:
            raise ValueError("El DNI debe contener exactamente 8 digitos numericos")
        return v

    @field_validator("placa")
    @classmethod
    def validar_placa(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("La placa no puede estar vacia")
        return v

    @field_validator("anio")
    @classmethod
    def validar_anio(cls, v: int) -> int:
        anio_actual = datetime.now().year
        if v < 1900 or v > anio_actual:
            raise ValueError(f"El anio debe estar entre 1900 y {anio_actual} inclusive")
        return v


class OTRespuesta(BaseModel):
    """Modelo de confirmacion al crear una OT exitosamente."""

    id_ot: int
    mensaje: str = "OT creada exitosamente"


class OTDetalle(BaseModel):
    """Modelo con el detalle completo de una Orden de Trabajo."""

    id: int
    nombre: str
    dni: str
    placa: str
    marca: str
    modelo: str
    anio: int
    kilometraje: int
    motivo: str
    tecnico: str
    estado: str
    observaciones: Optional[str] = None
    fecha_hora: str
