"""
Pruebas para el Modulo Alertas (H4).
Incluye pruebas de propiedad PBT segun design.md y tasks.md.
"""

import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from data.seed import inicializar_base_datos
from app.shared.mcp_client import McpReadClient
from app.main import app
import app.modules.alertas.router as modulo_alertas


@pytest.fixture
def cliente_api():
    """Cliente de prueba para la API FastAPI."""
    os.environ["MODO_TEST"] = "1"
    os.environ["GEMINI_API_KEY"] = "clave_prueba"
    return TestClient(app)


# Feature: asistente-taller-jorge-motors, Propiedad 11: Corrección del filtrado de alertas de stock mínimo
# Valida: Requisitos 4.1, 4.2
def test_propiedad_11_filtrado_alertas():
    """
    Para inventario con N repuestos de cantidades conocidas, verificar que la lista
    de alertas contiene exactamente los repuestos con cantidad <= stock_minimo.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        ruta_db = tmp.name

    inicializar_base_datos(ruta_db)

    # Insertar repuestos y stock de prueba
    repuestos_prueba = [
        (10, "REP-T1", "Repuesto Bajo", "unidad", 10),
        (20, "REP-T2", "Repuesto Exacto", "unidad", 5),
        (30, "REP-T3", "Repuesto Sobrante", "unidad", 5),
    ]
    stock_prueba = [
        (10, 3),   # 3 <= 10 -> En alerta
        (20, 5),   # 5 <= 5  -> En alerta
        (30, 20),  # 20 > 5  -> NO alerta
    ]

    import sqlite3
    with sqlite3.connect(ruta_db) as conn:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO repuestos (id, codigo, nombre, unidad, stock_minimo) VALUES (?, ?, ?, ?, ?);",
            repuestos_prueba,
        )
        cursor.executemany(
            "INSERT INTO stock (id_repuesto, cantidad) VALUES (?, ?);",
            stock_prueba,
        )
        conn.commit()

    cliente_mcp = McpReadClient(usar_stub=True, ruta_db=ruta_db)
    alertas = cliente_mcp.listar_alertas()
    codigos_alertas = {a["codigo"] for a in alertas}
    assert codigos_alertas == {"REP-T1", "REP-T2"}

    # Cada alerta debe incluir los 4 campos minimos
    for a in alertas:
        assert a["cantidad"] <= a["stock_minimo"]
        assert "nombre" in a
        assert "codigo" in a
        assert "cantidad" in a
        assert "stock_minimo" in a

    if os.path.exists(ruta_db):
        try:
            os.remove(ruta_db)
        except OSError:
            pass


def test_alertas_panel_endpoint(cliente_api):
    """Verifica respuesta del endpoint GET /alertas en la base actual."""
    respuesta = cliente_api.get("/alertas")
    assert respuesta.status_code == 200
    alertas = respuesta.json()["alertas"]
    assert len(alertas) >= 1
    for item in alertas:
        assert item["cantidad"] <= item["stock_minimo"]


def test_alertas_sin_alertas_activas(cliente_api, monkeypatch):
    """Verifica respuesta cuando no hay alertas activas."""
    class StubSinAlertas:
        def listar_alertas(self):
            return []

    monkeypatch.setattr(modulo_alertas, "mcp_client", StubSinAlertas())
    respuesta = cliente_api.get("/alertas")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["alertas"] == []
    assert "No hay alertas de stock activas" in cuerpo["mensaje"]


def test_alertas_mcp_caido(cliente_api, monkeypatch):
    """Verifica que si el MCP no responde, se retorna HTTP 503."""
    cliente_caido = McpReadClient(simular_error_conexion=True)
    monkeypatch.setattr(modulo_alertas, "mcp_client", cliente_caido)

    respuesta = cliente_api.get("/alertas")
    assert respuesta.status_code == 503
    assert "servicio de inventario no esta disponible" in respuesta.json()["detail"]
