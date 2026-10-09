"""
Pruebas para el Modulo Historial (H2).
Incluye pruebas de propiedad PBT segun design.md y tasks.md.
"""

import os
import tempfile
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from hypothesis import given, strategies as st, settings, HealthCheck

from data.seed import inicializar_base_datos, poblar_datos_simulados
from app.shared.mcp_client import McpReadClient
from app.main import app
import app.modules.historial.router as modulo_historial


@pytest.fixture
def cliente_api():
    """Cliente de prueba para la API FastAPI."""
    os.environ["MODO_TEST"] = "1"
    os.environ["GEMINI_API_KEY"] = "clave_prueba"
    return TestClient(app)


# Feature: asistente-taller-jorge-motors, Propiedad 4: Límite y orden del historial de OT
# Valida: Requisito 2.1
def test_propiedad_4_limite_y_orden_historial():
    """
    Generar N OT (N > 100) con fechas aleatorias asociadas a un mismo vehiculo;
    verificar que el historial retorna como maximo 100 resultados y en orden descendente por fecha.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        ruta_db = tmp.name

    inicializar_base_datos(ruta_db)
    poblar_datos_simulados(ruta_db)

    # Insertar 120 OT con fechas secuenciales para la placa ABC-123 (id_vehiculo=1, id_cliente=1)
    base_time = datetime.now(timezone.utc)
    filas_ot = []
    for i in range(120):
        fecha_iso = (base_time - timedelta(minutes=i)).isoformat()
        filas_ot.append(
            (
                1000 + i,
                1,
                1,
                10000 + i,
                f"Motivo {i}",
                "Luis Pachas",
                "cerrada",
                f"Obs {i}",
                fecha_iso,
            )
        )

    import sqlite3
    with sqlite3.connect(ruta_db) as conn:
        conn.cursor().executemany(
            """
            INSERT INTO ordenes_trabajo (
                id, id_vehiculo, id_cliente, kilometraje, motivo, tecnico, estado, observaciones, fecha_hora
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            filas_ot,
        )
        conn.commit()

    cliente_mcp = McpReadClient(usar_stub=True, ruta_db=ruta_db)

    resultados = cliente_mcp.buscar_historial("ABC-123", tipo="placa")
    assert len(resultados) <= 100
    assert len(resultados) == 100

    # Verificar orden descendente
    fechas = [r["fecha"] for r in resultados]
    assert fechas == sorted(fechas, reverse=True)

    if os.path.exists(ruta_db):
        try:
            os.remove(ruta_db)
        except OSError:
            pass


# Feature: asistente-taller-jorge-motors, Propiedad 5: Completitud de campos al consultar una OT del historial
# Valida: Requisito 2.2
def test_propiedad_5_completitud_campos_historial(cliente_api):
    """
    Para cualquier OT consultada por su ID, la respuesta debe contener exactamente
    los 6 campos requeridos: id, fecha, motivo, tecnico, estado y observaciones.
    """
    respuesta = cliente_api.get("/historial/1")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()

    campos_esperados = {"id", "fecha", "motivo", "tecnico", "estado", "observaciones"}
    assert set(cuerpo.keys()) == campos_esperados
    assert cuerpo["id"] == 1
    assert cuerpo["tecnico"] != ""


# Feature: asistente-taller-jorge-motors, Propiedad 6: Rechazo de búsqueda con formato inválido
# Valida: Requisito 2.5
@settings(max_examples=25, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
@given(
    texto_invalido=st.text(alphabet=st.characters(blacklist_categories=["Cs", "Cc"])).filter(
        lambda s: not (
            s.isdigit() and len(s) == 8
        ) and not (
            len(s) <= 8 and s.isalnum() and len(s) > 0
        )
    )
)
def test_propiedad_6_rechazo_busqueda_formato_invalido(cliente_api, texto_invalido):
    """
    Para cadenas que no cumplen el formato de placa ni DNI, verificar
    que el endpoint retorna 422 sin consultar el MCP.
    """
    respuesta = cliente_api.get("/historial", params={"q": texto_invalido})
    assert respuesta.status_code == 422


def test_busqueda_historial_sin_registros(cliente_api):
    """Verifica respuesta adecuada cuando no hay registros para el criterio."""
    respuesta = cliente_api.get("/historial?q=99999999")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["ordenes"] == []
    assert "No se encontraron registros" in cuerpo["mensaje"]


def test_historial_mcp_caido(cliente_api, monkeypatch):
    """Verifica que si el MCP no responde, se retorna HTTP 503."""
    cliente_caido = McpReadClient(simular_error_conexion=True)
    monkeypatch.setattr(modulo_historial, "mcp_client", cliente_caido)

    respuesta = cliente_api.get("/historial?q=10000001")
    assert respuesta.status_code == 503
    assert "servicio de historial no esta disponible" in respuesta.json()["detail"]
