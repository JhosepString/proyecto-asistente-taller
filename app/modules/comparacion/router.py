"""
Router para el modulo de Comparacion de Conteo Fisico.
"""

from fastapi import APIRouter, HTTPException, status
from app.modules.comparacion.schemas import (
    SolicitudComparacion,
    ComparacionRespuesta,
    ResultadoComparacionItem,
)
from app.modules.comparacion.repositorio import RepositorioComparacion
from app.shared.mcp_client import McpReadClient, McpNoDisponibleError

router = APIRouter(prefix="/comparacion", tags=["Comparacion"])
mcp_client = McpReadClient()
repositorio = RepositorioComparacion()


@router.post("", response_model=ComparacionRespuesta)
def comparar_inventario(solicitud: SolicitudComparacion) -> ComparacionRespuesta:
    """
    Compara las cantidades ingresadas en el conteo fisico con el stock en sistema.
    Calcula la diferencia exacta con signo y marca descuadres (Requisito 5.1-5.3).
    Rechaza solicitudes sin items con 422 (Requisito 5.4).
    Excluye repuestos inexistentes (Requisito 5.6).
    """
    if not solicitud.items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debe ingresar al menos un repuesto con su conteo fisico",
        )

    # Convertir items a diccionarios para el cliente MCP
    items_dict = [
        {"codigo": item.codigo, "conteo_fisico": item.conteo_fisico}
        for item in solicitud.items
    ]

    try:
        filas = mcp_client.comparar_conteo(items_dict)
    except McpNoDisponibleError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de inventario no esta disponible en este momento",
        )

    resultados = [ResultadoComparacionItem(**f) for f in filas]

    # Guardar en repositorio SQLite propio (ADR-002)
    if resultados:
        repositorio.guardar_comparacion(resultados)

    mensaje = None
    if len(resultados) < len(solicitud.items):
        mensaje = "Algunos repuestos no fueron encontrados en el inventario y se omitieron"

    return ComparacionRespuesta(resultados=resultados, mensaje=mensaje)
