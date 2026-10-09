"""
Router para la consulta de historial de clientes y vehiculos (Modulo Historial).
"""

import re
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.modules.historial.schemas import HistorialRespuesta, OTHistorialItem
from app.shared.mcp_client import McpReadClient, McpNoDisponibleError

router = APIRouter(prefix="/historial", tags=["Historial"])
mcp_client = McpReadClient()


def validar_criterio_busqueda(q: str) -> str:
    """
    Valida si el parametro cumple con formato de DNI (8 digitos)
    o formato de placa (maximo 8 caracteres alfanumericos con guion opcional).
    Retorna 'dni' o 'placa'. Eleva HTTPException(422) si no cumple.
    """
    if not q or not q.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El parametro de busqueda no puede estar vacio",
        )

    q_limpio = q.strip()

    # Validar formato DNI: exactamente 8 digitos numericos
    if re.fullmatch(r"^\d{8}$", q_limpio):
        return "dni"

    # Validar formato Placa: maximo 8 caracteres alfanumericos (guion opcional)
    # Ejemplo: ABC-123 o ABC123
    patron_placa = r"^[A-Za-z0-9]{1,4}-?[A-Za-z0-9]{1,4}$"
    if re.fullmatch(patron_placa, q_limpio) and len(q_limpio) <= 8:
        return "placa"

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Formato invalido: ingrese un DNI (8 digitos) o una placa valida (max. 8 caracteres alfanumericos)",
    )


@router.get("", response_model=HistorialRespuesta)
def buscar_historial(q: str = Query(..., description="Placa o DNI a buscar")) -> HistorialRespuesta:
    """
    Busca las hasta 100 OT mas recientes asociadas a una placa o DNI.
    Valida el formato previo a la llamada del MCP.
    """
    tipo = validar_criterio_busqueda(q)
    criterio = q.strip()

    try:
        filas = mcp_client.buscar_historial(criterio, tipo=tipo)
    except McpNoDisponibleError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de historial no esta disponible en este momento",
        )

    if not filas:
        return HistorialRespuesta(
            ordenes=[],
            mensaje="No se encontraron registros para ese criterio de busqueda",
        )

    items = [OTHistorialItem(**fila) for fila in filas]
    return HistorialRespuesta(ordenes=items)


@router.get("/{id_ot}", response_model=OTHistorialItem)
def obtener_detalle_ot(id_ot: int) -> OTHistorialItem:
    """
    Recupera el detalle de una OT por identificador con los 6 campos requeridos.
    """
    try:
        # En el stub de solo lectura, consultamos todas y filtramos por id_ot
        with mcp_client._obtener_conexion_sqlite_ro() as conexion:
            cursor = conexion.cursor()
            cursor.execute(
                """
                SELECT id, fecha_hora AS fecha, motivo, tecnico, estado, observaciones
                FROM ordenes_trabajo
                WHERE id = ?;
                """,
                (id_ot,),
            )
            fila = cursor.fetchone()
            if not fila:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Orden de trabajo no encontrada",
                )
            return OTHistorialItem(
                id=fila["id"],
                fecha=fila["fecha"],
                motivo=fila["motivo"],
                tecnico=fila["tecnico"],
                estado=fila["estado"],
                observaciones=fila["observaciones"] or "",
            )
    except McpNoDisponibleError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de historial no esta disponible en este momento",
        )
