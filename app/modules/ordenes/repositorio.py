"""
Repositorio para operaciones de base de datos relacionadas con Ordenes de Trabajo.
Maneja transacciones directas en SQLite cumpliendo con ADR-002.
"""

import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.modules.ordenes.schemas import OTCrear, OTDetalle

RUTA_DB_DEFAULT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "taller.db")


class RepositorioOT:
    """Acceso a datos de escritura y lectura directa para Ordenes de Trabajo."""

    def __init__(self, ruta_db: Optional[str] = None):
        self.ruta_db = ruta_db or RUTA_DB_DEFAULT

    def _obtener_conexion(self) -> sqlite3.Connection:
        conexion = sqlite3.connect(self.ruta_db)
        conexion.execute("PRAGMA foreign_keys = ON;")
        conexion.row_factory = sqlite3.Row
        return conexion

    def crear_ot(self, datos: OTCrear) -> Dict[str, Any]:
        """
        Registra una nueva Orden de Trabajo en SQLite.
        Inserta o actualiza cliente y vehiculo, e inserta la orden con fecha/hora automatica.
        Retorna un diccionario con id_ot y fecha_hora generados.
        """
        fecha_hora = datetime.now(timezone.utc).isoformat()
        estado_inicial = "abierta"

        with self._obtener_conexion() as conexion:
            cursor = conexion.cursor()

            # 1. Obtener o crear cliente
            cursor.execute("SELECT id FROM clientes WHERE dni = ?;", (datos.dni,))
            fila_cliente = cursor.fetchone()
            if fila_cliente:
                id_cliente = fila_cliente["id"]
                cursor.execute(
                    "UPDATE clientes SET nombre = ? WHERE id = ?;",
                    (datos.nombre, id_cliente),
                )
            else:
                cursor.execute(
                    "INSERT INTO clientes (nombre, dni) VALUES (?, ?);",
                    (datos.nombre, datos.dni),
                )
                id_cliente = cursor.lastrowid

            # 2. Obtener o crear vehiculo
            cursor.execute("SELECT id FROM vehiculos WHERE placa = ?;", (datos.placa,))
            fila_vehiculo = cursor.fetchone()
            if fila_vehiculo:
                id_vehiculo = fila_vehiculo["id"]
                cursor.execute(
                    """
                    UPDATE vehiculos
                    SET marca = ?, modelo = ?, anio = ?, id_cliente = ?
                    WHERE id = ?;
                    """,
                    (datos.marca, datos.modelo, datos.anio, id_cliente, id_vehiculo),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO vehiculos (placa, marca, modelo, anio, id_cliente)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (datos.placa, datos.marca, datos.modelo, datos.anio, id_cliente),
                )
                id_vehiculo = cursor.lastrowid

            # 3. Insertar orden de trabajo
            cursor.execute(
                """
                INSERT INTO ordenes_trabajo (
                    id_vehiculo, id_cliente, kilometraje, motivo, tecnico, estado, observaciones, fecha_hora
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    id_vehiculo,
                    id_cliente,
                    datos.kilometraje,
                    datos.motivo,
                    datos.tecnico,
                    estado_inicial,
                    datos.observaciones,
                    fecha_hora,
                ),
            )
            id_ot = cursor.lastrowid
            conexion.commit()

        return {
            "id_ot": id_ot,
            "fecha_hora": fecha_hora,
        }

    def obtener_ot_por_id(self, id_ot: int) -> Optional[OTDetalle]:
        """Recupera el detalle completo de una OT por su identificador."""
        with self._obtener_conexion() as conexion:
            cursor = conexion.cursor()
            cursor.execute(
                """
                SELECT
                    ot.id,
                    c.nombre,
                    c.dni,
                    v.placa,
                    v.marca,
                    v.modelo,
                    v.anio,
                    ot.kilometraje,
                    ot.motivo,
                    ot.tecnico,
                    ot.estado,
                    ot.observaciones,
                    ot.fecha_hora
                FROM ordenes_trabajo ot
                JOIN clientes c ON ot.id_cliente = c.id
                JOIN vehiculos v ON ot.id_vehiculo = v.id
                WHERE ot.id = ?;
                """,
                (id_ot,),
            )
            fila = cursor.fetchone()
            if not fila:
                return None

            return OTDetalle(
                id=fila["id"],
                nombre=fila["nombre"],
                dni=fila["dni"],
                placa=fila["placa"],
                marca=fila["marca"],
                modelo=fila["modelo"],
                anio=fila["anio"],
                kilometraje=fila["kilometraje"],
                motivo=fila["motivo"],
                tecnico=fila["tecnico"],
                estado=fila["estado"],
                observaciones=fila["observaciones"],
                fecha_hora=fila["fecha_hora"],
            )
