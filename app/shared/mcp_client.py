"""
Cliente de solo lectura para el Servidor MCP (McpReadClient).
Encapsula todas las operaciones de lectura de historial e inventario (ADR-002).
Incluye stub configurable para pruebas y desarrollo antes de conectar al MCP real (Semana 4).
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional

RUTA_DB_DEFAULT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "taller.db")


class McpNoDisponibleError(Exception):
    """Excepcion elevada cuando el Servidor MCP no se encuentra disponible."""

    def __init__(self, mensaje: str = "El servicio MCP no esta disponible en este momento"):
        super().__init__(mensaje)
        self.mensaje = mensaje


class McpReadClient:
    """
    Cliente para interactuar de forma exclusiva en solo lectura con el Servidor MCP.
    Soporta modo stub para operar contra SQLite local o simular caidas de servicio.
    """

    def __init__(
        self,
        base_url: Optional[str] = "http://localhost:8001",
        usar_stub: bool = True,
        ruta_db: Optional[str] = None,
        simular_error_conexion: bool = False,
    ):
        self.base_url = base_url
        self.usar_stub = usar_stub
        self.ruta_db = ruta_db or RUTA_DB_DEFAULT
        self.simular_error_conexion = simular_error_conexion

    def _verificar_disponibilidad(self) -> None:
        """Eleva McpNoDisponibleError si se encuentra configurado para simular caida."""
        if self.simular_error_conexion:
            raise McpNoDisponibleError("Error de conexion: no se pudo contactar al servidor MCP")

    def _obtener_conexion_sqlite_ro(self) -> sqlite3.Connection:
        """Abre conexion a SQLite en modo solo lectura."""
        self._verificar_disponibilidad()
        if not os.path.exists(self.ruta_db):
            raise McpNoDisponibleError(f"Base de datos no encontrada para el stub MCP: {self.ruta_db}")

        try:
            conexion = sqlite3.connect(f"file:{self.ruta_db}?mode=ro", uri=True)
            conexion.row_factory = sqlite3.Row
            return conexion
        except sqlite3.Error as e:
            raise McpNoDisponibleError(f"Fallo al abrir SQLite en modo solo lectura: {str(e)}")

    def buscar_historial(self, criterio: str, tipo: str = "placa") -> List[Dict[str, Any]]:
        """
        Consulta las hasta 100 OT mas recientes por placa o por DNI.
        Retorna: [{id, fecha, motivo, tecnico, estado, observaciones}]
        """
        self._verificar_disponibilidad()
        if not self.usar_stub:
            raise McpNoDisponibleError("Conexion al servidor MCP real no configurada aun")

        criterio_limpio = criterio.strip()
        with self._obtener_conexion_sqlite_ro() as conexion:
            cursor = conexion.cursor()
            if tipo == "dni":
                query = """
                    SELECT
                        ot.id,
                        ot.fecha_hora AS fecha,
                        ot.motivo,
                        ot.tecnico,
                        ot.estado,
                        ot.observaciones
                    FROM ordenes_trabajo ot
                    JOIN clientes c ON ot.id_cliente = c.id
                    WHERE c.dni = ?
                    ORDER BY ot.fecha_hora DESC
                    LIMIT 100;
                """
                cursor.execute(query, (criterio_limpio,))
            else:
                query = """
                    SELECT
                        ot.id,
                        ot.fecha_hora AS fecha,
                        ot.motivo,
                        ot.tecnico,
                        ot.estado,
                        ot.observaciones
                    FROM ordenes_trabajo ot
                    JOIN vehiculos v ON ot.id_vehiculo = v.id
                    WHERE v.placa = ?
                    ORDER BY ot.fecha_hora DESC
                    LIMIT 100;
                """
                cursor.execute(query, (criterio_limpio,))

            filas = cursor.fetchall()
            return [
                {
                    "id": fila["id"],
                    "fecha": fila["fecha"],
                    "motivo": fila["motivo"],
                    "tecnico": fila["tecnico"],
                    "estado": fila["estado"],
                    "observaciones": fila["observaciones"] or "",
                }
                for fila in filas
            ]

    def consultar_stock(self, termino: str) -> List[Dict[str, Any]]:
        """
        Consulta repuestos por coincidencia exacta de codigo o coincidencia parcial de nombre.
        Retorna: [{nombre, codigo, cantidad, unidad}]
        """
        self._verificar_disponibilidad()
        if not self.usar_stub:
            raise McpNoDisponibleError("Conexion al servidor MCP real no configurada aun")

        termino_limpio = termino.strip()
        with self._obtener_conexion_sqlite_ro() as conexion:
            cursor = conexion.cursor()
            # 1. Intentar coincidencia exacta por codigo (Requisito 3.3)
            cursor.execute(
                """
                SELECT r.nombre, r.codigo, COALESCE(s.cantidad, 0) AS cantidad, r.unidad
                FROM repuestos r
                LEFT JOIN stock s ON r.id = s.id_repuesto
                WHERE UPPER(r.codigo) = UPPER(?);
                """,
                (termino_limpio,),
            )
            filas_codigo = cursor.fetchall()
            if filas_codigo:
                return [
                    {
                        "nombre": f["nombre"],
                        "codigo": f["codigo"],
                        "cantidad": f["cantidad"],
                        "unidad": f["unidad"],
                    }
                    for f in filas_codigo
                ]

            # 2. Busqueda por nombre (Requisito 3.4)
            cursor.execute(
                """
                SELECT r.nombre, r.codigo, COALESCE(s.cantidad, 0) AS cantidad, r.unidad
                FROM repuestos r
                LEFT JOIN stock s ON r.id = s.id_repuesto
                WHERE LOWER(r.nombre) LIKE LOWER(?);
                """,
                (f"%{termino_limpio}%",),
            )
            filas_nombre = cursor.fetchall()
            return [
                {
                    "nombre": f["nombre"],
                    "codigo": f["codigo"],
                    "cantidad": f["cantidad"],
                    "unidad": f["unidad"],
                }
                for f in filas_nombre
            ]

    def listar_alertas(self) -> List[Dict[str, Any]]:
        """
        Lista repuestos con cantidad disponible menor o igual al stock minimo.
        Retorna: [{nombre, codigo, cantidad, stock_minimo}]
        """
        self._verificar_disponibilidad()
        if not self.usar_stub:
            raise McpNoDisponibleError("Conexion al servidor MCP real no configurada aun")

        with self._obtener_conexion_sqlite_ro() as conexion:
            cursor = conexion.cursor()
            cursor.execute(
                """
                SELECT r.nombre, r.codigo, COALESCE(s.cantidad, 0) AS cantidad, r.stock_minimo
                FROM repuestos r
                LEFT JOIN stock s ON r.id = s.id_repuesto
                WHERE COALESCE(s.cantidad, 0) <= r.stock_minimo
                ORDER BY r.nombre ASC;
                """
            )
            filas = cursor.fetchall()
            return [
                {
                    "nombre": f["nombre"],
                    "codigo": f["codigo"],
                    "cantidad": f["cantidad"],
                    "stock_minimo": f["stock_minimo"],
                }
                for f in filas
            ]

    def comparar_conteo(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compara conteo fisico ingresado contra el stock registrado en el sistema.
        items: [{"codigo": "REP-001", "conteo_fisico": 5}, ...]
        Retorna: [{nombre, codigo, sistema, conteo, diferencia, descuadre}]
        Omite repuestos no encontrados segun Requisito 5.6.
        """
        self._verificar_disponibilidad()
        if not self.usar_stub:
            raise McpNoDisponibleError("Conexion al servidor MCP real no configurada aun")

        resultados = []
        with self._obtener_conexion_sqlite_ro() as conexion:
            cursor = conexion.cursor()
            for item in items:
                codigo = item.get("codigo", "").strip()
                conteo = int(item.get("conteo_fisico", 0))

                cursor.execute(
                    """
                    SELECT r.nombre, r.codigo, COALESCE(s.cantidad, 0) AS sistema
                    FROM repuestos r
                    LEFT JOIN stock s ON r.id = s.id_repuesto
                    WHERE UPPER(r.codigo) = UPPER(?);
                    """,
                    (codigo,),
                )
                fila = cursor.fetchone()
                if fila:
                    sistema = fila["sistema"]
                    diferencia = conteo - sistema
                    resultados.append(
                        {
                            "nombre": fila["nombre"],
                            "codigo": fila["codigo"],
                            "sistema": sistema,
                            "conteo": conteo,
                            "diferencia": diferencia,
                            "descuadre": (diferencia != 0),
                        }
                    )
        return resultados

    def generar_reporte(self, fecha_inicio: str, fecha_fin: str) -> List[Dict[str, Any]]:
        """
        Genera reporte de ordenes de trabajo agrupado por tecnico entre fecha_inicio y fecha_fin.
        fechas en formato YYYY-MM-DD.
        Retorna: [{tecnico, total, abierta, en_proceso, cerrada}]
        """
        self._verificar_disponibilidad()
        if not self.usar_stub:
            raise McpNoDisponibleError("Conexion al servidor MCP real no configurada aun")

        # Rango de fechas inclusivo
        inicio_iso = f"{fecha_inicio}T00:00:00"
        fin_iso = f"{fecha_fin}T23:59:59"

        with self._obtener_conexion_sqlite_ro() as conexion:
            cursor = conexion.cursor()
            cursor.execute(
                """
                SELECT
                    tecnico,
                    COUNT(*) AS total,
                    SUM(CASE WHEN estado = 'abierta' THEN 1 ELSE 0 END) AS abierta,
                    SUM(CASE WHEN estado = 'en proceso' THEN 1 ELSE 0 END) AS en_proceso,
                    SUM(CASE WHEN estado = 'cerrada' THEN 1 ELSE 0 END) AS cerrada
                FROM ordenes_trabajo
                WHERE fecha_hora >= ? AND fecha_hora <= ?
                GROUP BY tecnico
                ORDER BY tecnico ASC;
                """,
                (inicio_iso, fin_iso),
            )
            filas = cursor.fetchall()
            return [
                {
                    "tecnico": f["tecnico"],
                    "total": f["total"],
                    "abierta": f["abierta"],
                    "en_proceso": f["en_proceso"],
                    "cerrada": f["cerrada"],
                }
                for f in filas
            ]
