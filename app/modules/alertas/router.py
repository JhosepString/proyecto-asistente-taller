"""
Router para la consulta de alertas de stock minimo (Modulo Alertas).
"""

from fastapi import APIRouter, HTTPException, status
from app.modules.alertas.schemas import AlertasRespuesta, AlertaItem
from app.shared.mcp_client import McpReadClient, McpNoDisponibleError

router = APIRouter(prefix="/alertas", tags=["Alertas"])
mcp_client = McpReadClient()


@router.get("", response_model=AlertasRespuesta)
def obtener_alertas() -> AlertasRespuesta:
    """
    Obtiene la lista consolidada de repuestos con cantidad menor o igual al stock minimo.
    """
    try:
        filas = mcp_client.listar_alertas()
    except McpNoDisponibleError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de inventario no esta disponible en este momento",
        )

    if not filas:
        return AlertasRespuesta(
            alertas=[],
            mensaje="No hay alertas de stock activas",
        )

    alertas = [AlertaItem(**fila) for fila in filas]
    return AlertasRespuesta(alertas=alertas)
