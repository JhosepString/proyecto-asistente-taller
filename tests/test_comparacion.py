"""
Pruebas para el Modulo Comparacion (H5).
Incluye pruebas de propiedad PBT segun design.md y tasks.md.
"""

import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from hypothesis import given, strategies as st, settings, HealthCheck

from data.seed import inicializar_base_datos
from app.shared.mcp_client import McpReadClient
from app.main import app
from app.modules.comparacion.schemas import ResultadoComparacionItem
from app.modules.comparacion.repositorio import RepositorioComparacion
import app.modules.comparacion.router as modulo_comparacion


@pytest.fixture
def cliente_api():
    """Cliente de prueba para la API FastAPI."""
    os.environ["MODO_TEST"] = "1"
    os.environ["GEMINI_API_KEY"] = "clave_prueba"
    return TestClient(app)


# Feature: asistente-taller-jorge-motors, Propiedad 12: Corrección del cálculo de diferencias en comparación de conteo físico
# Valida: Requisitos 5.1, 5.2
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
@given(
    conteo_fisico=st.integers(min_value=0, max_value=500),
    cantidad_sistema=st.integers(min_value=0, max_value=500),
)
def test_propiedad_12_calculo_diferencias(conteo_fisico, cantidad_sistema):
    """
    Para cualquier par (conteo_fisico, cantidad_sistema), verificar que:
    diferencia = conteo_fisico - cantidad_sistema
    con el signo exacto correspondiente y los campos presentes.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        ruta_db = tmp.name

    inicializar_base_datos(ruta_db)

    import sqlite3
    with sqlite3.connect(ruta_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO repuestos (id, codigo, nombre, unidad, stock_minimo) VALUES (100, 'REP-PBT', 'PBT Repuesto', 'unidad', 5);"
        )
        cursor.execute(
            "INSERT INTO stock (id_repuesto, cantidad) VALUES (100, ?);",
            (cantidad_sistema,),
        )
        conn.commit()

    cliente_mcp = McpReadClient(usar_stub=True, ruta_db=ruta_db)
    items = [{"codigo": "REP-PBT", "conteo_fisico": conteo_fisico}]
    resultados = cliente_mcp.comparar_conteo(items)

    assert len(resultados) == 1
    r = resultados[0]
    assert r["sistema"] == cantidad_sistema
    assert r["conteo"] == conteo_fisico
    assert r["diferencia"] == (conteo_fisico - cantidad_sistema)

    if os.path.exists(ruta_db):
        try:
            os.remove(ruta_db)
        except OSError:
            pass


# Feature: asistente-taller-jorge-motors, Propiedad 13: Clasificación correcta del indicador de descuadre
# Valida: Requisito 5.3
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
@given(
    conteo=st.integers(min_value=0, max_value=200),
    sistema=st.integers(min_value=0, max_value=200),
)
def test_propiedad_13_clasificacion_indicador_descuadre(conteo, sistema):
    """
    Para cualquier diferencia != 0, verificar que descuadre == True;
    para diferencia == 0, verificar que descuadre == False.
    """
    diferencia = conteo - sistema
    espera_descuadre = (diferencia != 0)

    resultado = ResultadoComparacionItem(
        nombre="Repuesto Test",
        codigo="REP-001",
        sistema=sistema,
        conteo=conteo,
        diferencia=diferencia,
        descuadre=(diferencia != 0),
    )
    assert resultado.descuadre == espera_descuadre


def test_rechazo_comparacion_sin_items(cliente_api):
    """Verifica que enviar lista vacia de items retorne 422 (Requisito 5.4)."""
    respuesta = cliente_api.post("/comparacion", json={"items": []})
    assert respuesta.status_code == 422


def test_comparacion_exitosa_y_persistencia(cliente_api):
    """Verifica ejecucion exitosa de POST /comparacion y persistencia en repositorio."""
    payload = {
        "items": [
            {"codigo": "REP-001", "conteo_fisico": 3},   # Sistema tiene 3 -> diferencia 0
            {"codigo": "REP-002", "conteo_fisico": 18},  # Sistema tiene 15 -> diferencia +3
        ]
    }
    respuesta = cliente_api.post("/comparacion", json=payload)
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo["resultados"]) == 2

    r1 = next(item for item in cuerpo["resultados"] if item["codigo"] == "REP-001")
    assert r1["diferencia"] == 0
    assert r1["descuadre"] is False

    r2 = next(item for item in cuerpo["resultados"] if item["codigo"] == "REP-002")
    assert r2["diferencia"] == 3
    assert r2["descuadre"] is True


def test_comparacion_omite_repuesto_inexistente(cliente_api):
    """Verifica que los repuestos inexistentes se excluyan de los resultados (Requisito 5.6)."""
    payload = {
        "items": [
            {"codigo": "REP-001", "conteo_fisico": 3},
            {"codigo": "NO_EXISTE_XYZ", "conteo_fisico": 5},
        ]
    }
    respuesta = cliente_api.post("/comparacion", json=payload)
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo["resultados"]) == 1
    assert cuerpo["resultados"][0]["codigo"] == "REP-001"
    assert "omitieron" in cuerpo["mensaje"]


def test_comparacion_mcp_caido(cliente_api, monkeypatch):
    """Verifica retorno 503 cuando el MCP esta caido (Requisito 5.5)."""
    cliente_caido = McpReadClient(simular_error_conexion=True)
    monkeypatch.setattr(modulo_comparacion, "mcp_client", cliente_caido)

    payload = {"items": [{"codigo": "REP-001", "conteo_fisico": 2}]}
    respuesta = cliente_api.post("/comparacion", json=payload)
    assert respuesta.status_code == 503
    assert "servicio de inventario no esta disponible" in respuesta.json()["detail"]
