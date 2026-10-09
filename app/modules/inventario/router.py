"""
Router para la consulta de inventario y stock de repuestos (Modulo Inventario).
"""

from fastapi import APIRouter, HTTPException, Query, status
from app.modules.inventario.schemas import InventarioRespuesta, RepuestoStockItem
from app.shared.mcp_client import McpReadClient, McpNoDisponibleError

router = APIRouter(prefix="/inventario", tags=["Inventario"])
mcp_client = McpReadClient()


@router.get("", response_model=InventarioRespuesta)
def consultar_inventario(
    q: str = Query(..., description="Codigo o nombre del repuesto a consultar")
) -> InventarioRespuesta:
    """
    Consulta stock de un repuesto por codigo exacto o coincidencia por nombre.
    Rechaza cadenas vacias o con solo espacios con 422 (Requisito 3.7).
    """
    if not q or not q.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El parametro de busqueda no puede estar vacio ni contener solo espacios",
        )

    termino = q.strip()
    try:
        filas = mcp_client.consultar_stock(termino)
    except McpNoDisponibleError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de inventario no esta disponible en este momento",
        )

    if not filas:
        return InventarioRespuesta(
            resultados=[],
            mensaje="El repuesto no fue encontrado",
        )

    resultados = [RepuestoStockItem(**fila) for fila in filas]
    return InventarioRespuesta(resultados=resultados)
