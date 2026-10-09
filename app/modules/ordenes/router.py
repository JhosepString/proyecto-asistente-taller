"""
Router para los endpoints del modulo de Ordenes de Trabajo (OT).
"""

from fastapi import APIRouter, HTTPException, status
from app.modules.ordenes.schemas import OTCrear, OTRespuesta, OTDetalle
from app.modules.ordenes.repositorio import RepositorioOT

router = APIRouter(prefix="/ordenes", tags=["Ordenes de Trabajo"])
repositorio = RepositorioOT()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=OTRespuesta)
def crear_orden_trabajo(datos: OTCrear) -> OTRespuesta:
    """
    Crea una nueva Orden de Trabajo a partir de los datos recibidos.
    Valida campos obligatorios y persiste en SQLite.
    """
    try:
        resultado = repositorio.crear_ot(datos)
        return OTRespuesta(
            id_ot=resultado["id_ot"],
            mensaje="OT creada exitosamente",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al registrar la orden de trabajo: {str(e)}",
        )


@router.get("/{id_ot}", response_model=OTDetalle)
def obtener_orden_trabajo(id_ot: int) -> OTDetalle:
    """Recupera el detalle de una OT por su identificador."""
    ot = repositorio.obtener_ot_por_id(id_ot)
    if not ot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden de trabajo no encontrada",
        )
    return ot
