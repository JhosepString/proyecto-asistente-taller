"""
Repositorio para persistir registros de comparacion de inventario fisico en SQLite.
Cumple con ADR-002: escrituras a traves de repositorios propios de cada modulo.
"""

import os
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional
from app.modules.comparacion.schemas import ResultadoComparacionItem

RUTA_DB_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "data",
    "taller.db",
)


class RepositorioComparacion:
    """Manejo de persistencia de las comparaciones de inventario."""

    def __init__(self, ruta_db: Optional[str] = None):
        self.ruta_db = ruta_db or RUTA_DB_DEFAULT
        self._inicializar_tabla()

    def _obtener_conexion(self) -> sqlite3.Connection:
        conexion = sqlite3.connect(self.ruta_db)
        conexion.execute("PRAGMA foreign_keys = ON;")
        return conexion

    def _inicializar_tabla(self) -> None:
        """Crea la tabla comparaciones_inventario si no existe."""
        with self._obtener_conexion() as conexion:
            cursor = conexion.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS comparaciones_inventario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT NOT NULL,
                    nombre TEXT NOT NULL,
                    cantidad_sistema INTEGER NOT NULL,
                    conteo_fisico INTEGER NOT NULL,
                    diferencia INTEGER NOT NULL,
                    descuadre INTEGER NOT NULL,
                    fecha_hora TEXT NOT NULL
                );
                """
            )
            conexion.commit()

    def guardar_comparacion(self, resultados: List[ResultadoComparacionItem]) -> None:
        """Guarda los resultados de una comparacion de inventario."""
        if not resultados:
            return

        fecha_hora = datetime.now(timezone.utc).isoformat()
        filas = [
            (
                r.codigo,
                r.nombre,
                r.sistema,
                r.conteo,
                r.diferencia,
                1 if r.descuadre else 0,
                fecha_hora,
            )
            for r in resultados
        ]

        with self._obtener_conexion() as conexion:
            cursor = conexion.cursor()
            cursor.executemany(
                """
                INSERT INTO comparaciones_inventario (
                    codigo, nombre, cantidad_sistema, conteo_fisico, diferencia, descuadre, fecha_hora
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                filas,
            )
            conexion.commit()
