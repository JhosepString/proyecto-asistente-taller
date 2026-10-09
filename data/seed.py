"""
Script para inicializar y poblar la base de datos SQLite data/taller.db
con datos simulados de clientes, vehiculos, repuestos, stock y ordenes de trabajo.
Cumple con la Ley N.° 29733 (datos no reales).
"""

import os
import sqlite3
from datetime import datetime, timezone

RUTA_BASE_DATOS_POR_DEFECTO = os.path.join(os.path.dirname(__file__), "taller.db")


def inicializar_base_datos(ruta_db: str = RUTA_BASE_DATOS_POR_DEFECTO) -> None:
    """Crea las tablas de la base de datos si no existen."""
    directorio = os.path.dirname(ruta_db)
    if directorio and not os.path.exists(directorio):
        os.makedirs(directorio, exist_ok=True)

    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()

    # Habilitar claves foraneas y modo WAL
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA journal_mode = WAL;")

    # Tabla clientes
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            dni TEXT NOT NULL UNIQUE
        );
        """
    )

    # Tabla vehiculos
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS vehiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT NOT NULL UNIQUE,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            anio INTEGER NOT NULL,
            id_cliente INTEGER NOT NULL,
            FOREIGN KEY (id_cliente) REFERENCES clientes (id)
        );
        """
    )

    # Tabla ordenes_trabajo
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ordenes_trabajo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_vehiculo INTEGER NOT NULL,
            id_cliente INTEGER NOT NULL,
            kilometraje INTEGER NOT NULL,
            motivo TEXT NOT NULL,
            tecnico TEXT NOT NULL,
            estado TEXT NOT NULL,
            observaciones TEXT,
            fecha_hora TEXT NOT NULL,
            FOREIGN KEY (id_vehiculo) REFERENCES vehiculos (id),
            FOREIGN KEY (id_cliente) REFERENCES clientes (id)
        );
        """
    )

    # Tabla repuestos
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS repuestos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            unidad TEXT NOT NULL,
            stock_minimo INTEGER NOT NULL
        );
        """
    )

    # Tabla stock
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS stock (
            id_repuesto INTEGER PRIMARY KEY,
            cantidad INTEGER NOT NULL,
            FOREIGN KEY (id_repuesto) REFERENCES repuestos (id)
        );
        """
    )

    # Tabla trazabilidad_ia
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS trazabilidad_ia (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            rol TEXT NOT NULL,
            pregunta TEXT NOT NULL,
            contexto_mcp TEXT NOT NULL,
            respuesta TEXT,
            error TEXT
        );
        """
    )

    conexion.commit()
    conexion.close()


def poblar_datos_simulados(ruta_db: str = RUTA_BASE_DATOS_POR_DEFECTO) -> None:
    """Inserta registros ficticios de prueba si no existen."""
    conexion = sqlite3.connect(ruta_db)
    cursor = conexion.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Clientes simulados (Ley N.° 29733)
    clientes_simulados = [
        (1, "Cliente Simulado Uno", "10000001"),
        (2, "Cliente Simulado Dos", "10000002"),
        (3, "Cliente Simulado Tres", "10000003"),
    ]
    cursor.executemany(
        """
        INSERT OR IGNORE INTO clientes (id, nombre, dni)
        VALUES (?, ?, ?);
        """,
        clientes_simulados,
    )

    # Vehiculos simulados
    vehiculos_simulados = [
        (1, "ABC-123", "Toyota", "Corolla", 2018, 1),
        (2, "XYZ-789", "Nissan", "Sentra", 2020, 2),
        (3, "MNO-456", "Hyundai", "Elantra", 2019, 3),
    ]
    cursor.executemany(
        """
        INSERT OR IGNORE INTO vehiculos (id, placa, marca, modelo, anio, id_cliente)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        vehiculos_simulados,
    )

    # Repuestos simulados
    repuestos_simulados = [
        (1, "REP-001", "Pastillas de freno delanteras", "juego", 5),
        (2, "REP-002", "Filtro de aceite sintetico", "unidad", 10),
        (3, "REP-003", "Aceite de motor 5W-30", "litro", 20),
        (4, "REP-004", "Bujia de iridio", "unidad", 8),
        (5, "REP-005", "Amortiguador delantero", "unidad", 4),
    ]
    cursor.executemany(
        """
        INSERT OR IGNORE INTO repuestos (id, codigo, nombre, unidad, stock_minimo)
        VALUES (?, ?, ?, ?, ?);
        """,
        repuestos_simulados,
    )

    # Stock simulado (algunos por debajo del stock minimo para probar alertas)
    stock_simulado = [
        (1, 3),   # Menor que stock_minimo (5) -> Alerta
        (2, 15),  # Normal
        (3, 8),   # Menor que stock_minimo (20) -> Alerta
        (4, 12),  # Normal
        (5, 4),   # Igual a stock_minimo (4) -> Alerta
    ]
    cursor.executemany(
        """
        INSERT OR IGNORE INTO stock (id_repuesto, cantidad)
        VALUES (?, ?);
        """,
        stock_simulado,
    )

    # Ordenes de trabajo simuladas
    ahora_iso = datetime.now(timezone.utc).isoformat()
    ordenes_simuladas = [
        (1, 1, 1, 45000, "Mantenimiento preventivo 45k", "Luis Pachas", "cerrada", "Cambio de aceite y filtros", ahora_iso),
        (2, 2, 2, 60000, "Ruido al frenar", "Luis Luna", "en proceso", "Revision de pastillas y discos", ahora_iso),
        (3, 3, 3, 32000, "Fallo en encendido", "Miguel Torres", "abierta", "Pendiente diagnostico electrico", ahora_iso),
    ]
    cursor.executemany(
        """
        INSERT OR IGNORE INTO ordenes_trabajo (
            id, id_vehiculo, id_cliente, kilometraje, motivo, tecnico, estado, observaciones, fecha_hora
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        ordenes_simuladas,
    )

    conexion.commit()
    conexion.close()


def ejecutar_semilla(ruta_db: str = RUTA_BASE_DATOS_POR_DEFECTO) -> None:
    """Inicializa la estructura y puebla los datos."""
    inicializar_base_datos(ruta_db)
    poblar_datos_simulados(ruta_db)
    print(f"Base de datos inicializada exitosamente en: {ruta_db}")


if __name__ == "__main__":
    ejecutar_semilla()
