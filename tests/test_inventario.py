"""
Pruebas para el Modulo Inventario (H3).
Incluye pruebas de propiedad PBT segun design.md y tasks.md.
"""

import os
import pytest
from fastapi.testclient import TestClient
from hypothesis import given, strategies as st, settings, HealthCheck

from app.shared.mcp_client import McpReadClient
from app.main import app
import app.modules.inventario.router as modulo_inventario


@pytest.fixture
def cliente_api():
    """Cliente de prueba para la API FastAPI."""
    os.environ["MODO_TEST"] = "1"
    os.environ["GEMINI_API_KEY"] = "clave_prueba"
    return TestClient(app)


# Feature: asistente-taller-jorge-motors, Propiedad 7: Completitud e inmutabilidad de la consulta de stock
# Valida: Requisito 3.2
def test_propiedad_7_completitud_e_inmutabilidad(cliente_api):
    """
    Para cualquier repuesto existente, consultar su stock debe:
    (a) retornar un objeto con exactamente los 4 campos definidos (nombre, codigo, cantidad, unidad).
    (b) no modificar la cantidad registrada en el inventario tras la consulta.
    """
    # Consulta 1
    resp1 = cliente_api.get("/inventario?q=REP-001")
    assert resp1.status_code == 200
    resultados1 = resp1.json()["resultados"]
    assert len(resultados1) == 1
    repuesto1 = resultados1[0]

    campos_esperados = {"nombre", "codigo", "cantidad", "unidad"}
    assert set(repuesto1.keys()) == campos_esperados
    cantidad_inicial = repuesto1["cantidad"]

    # Consulta 2 repetida para validar inmutabilidad
    resp2 = cliente_api.get("/inventario?q=REP-001")
    assert resp2.status_code == 200
    cantidad_posterior = resp2.json()["resultados"][0]["cantidad"]

    assert cantidad_inicial == cantidad_posterior


# Feature: asistente-taller-jorge-motors, Propiedad 8: Exactitud de búsqueda por código de repuesto
# Valida: Requisito 3.3
@pytest.mark.parametrize("codigo", ["REP-001", "REP-002", "REP-003", "REP-004", "REP-005"])
def test_propiedad_8_exactitud_busqueda_por_codigo(cliente_api, codigo):
    """
    Para cualquier codigo existente, la busqueda debe retornar exactamente un resultado
    cuyo campo codigo coincida de forma exacta con el codigo buscado.
    """
    respuesta = cliente_api.get(f"/inventario?q={codigo}")
    assert respuesta.status_code == 200
    resultados = respuesta.json()["resultados"]
    assert len(resultados) == 1
    assert resultados[0]["codigo"] == codigo


# Feature: asistente-taller-jorge-motors, Propiedad 9: Completitud de resultados en búsqueda por nombre de repuesto
# Valida: Requisito 3.4
def test_propiedad_9_completitud_resultados_por_nombre(cliente_api):
    """
    Para cualquier termino de busqueda por nombre que coincida con K repuestos,
    el resultado debe contener exactamente esos K repuestos.
    """
    # 'aceite' coincide con REP-002 (Filtro de aceite) y REP-003 (Aceite de motor)
    respuesta = cliente_api.get("/inventario?q=aceite")
    assert respuesta.status_code == 200
    resultados = respuesta.json()["resultados"]
    assert len(resultados) == 2
    codigos = {r["codigo"] for r in resultados}
    assert codigos == {"REP-002", "REP-003"}


# Feature: asistente-taller-jorge-motors, Propiedad 10: Rechazo de consulta de stock con entrada vacía o de solo espacios
# Valida: Requisito 3.7
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
@given(espacios=st.text(alphabet=" ", min_size=0, max_size=10))
def test_propiedad_10_rechazo_entrada_vacia_o_espacios(cliente_api, espacios):
    """
    Para cadenas vacias o de solo espacios, el endpoint retorna 422 sin consultar el MCP.
    """
    respuesta = cliente_api.get("/inventario", params={"q": espacios})
    assert respuesta.status_code == 422


def test_repuesto_no_encontrado(cliente_api):
    """Verifica respuesta 200 cuando el repuesto no existe."""
    respuesta = cliente_api.get("/inventario?q=NO_EXISTE_999")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["resultados"] == []
    assert "no fue encontrado" in cuerpo["mensaje"]


def test_inventario_mcp_caido(cliente_api, monkeypatch):
    """Verifica que si el MCP no responde, se retorna HTTP 503."""
    cliente_caido = McpReadClient(simular_error_conexion=True)
    monkeypatch.setattr(modulo_inventario, "mcp_client", cliente_caido)

    respuesta = cliente_api.get("/inventario?q=REP-001")
    assert respuesta.status_code == 503
    assert "servicio de inventario no esta disponible" in respuesta.json()["detail"]
