"""
Pruebas para el Modulo de Ordenes de Trabajo (OT).
Incluye pruebas de propiedad PBT con Hypothesis segun tasks.md y design.md.
"""

import os
import tempfile
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from hypothesis import given, strategies as st, settings, HealthCheck

from data.seed import inicializar_base_datos
from app.modules.ordenes.repositorio import RepositorioOT
from app.modules.ordenes.schemas import OTCrear
from app.main import app


@pytest.fixture
def repo_temporal():
    """Crea una base de datos temporal para pruebas de repositorio aisladas."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        ruta_db = tmp.name

    inicializar_base_datos(ruta_db)
    repo = RepositorioOT(ruta_db=ruta_db)
    yield repo

    if os.path.exists(ruta_db):
        try:
            os.remove(ruta_db)
        except OSError:
            pass


@pytest.fixture
def cliente_api():
    """Cliente de pruebas para FastAPI."""
    os.environ["MODO_TEST"] = "1"
    os.environ["GEMINI_API_KEY"] = "clave_prueba"
    return TestClient(app)


# Estrategia de generacion de datos validos para OTCrear
estrategia_dni = st.integers(min_value=10000000, max_value=99999999).map(str)
estrategia_placa = st.from_regex(r"[A-Z]{3}-[0-9]{3}", fullmatch=True)
estrategia_texto_corto = st.text(
    alphabet=st.characters(categories=["L", "N", "Zs"]), min_size=1, max_size=40
).map(lambda s: s.strip() or "Valido")
estrategia_motivo = st.text(
    alphabet=st.characters(categories=["L", "N", "Zs"]), min_size=5, max_size=200
).map(lambda s: s.strip() or "Mantenimiento general")
estrategia_tecnico = st.sampled_from(["Luis Pachas", "Luis Luna", "Miguel Torres"])
anio_actual = datetime.now().year


# Feature: asistente-taller-jorge-motors, Propiedad 1: Unicidad de identificadores de OT
# Valida: Requisito 1.2
def test_propiedad_1_unicidad_de_identificadores(repo_temporal):
    """
    Para cualquier conjunto de N Ordenes de Trabajo creadas en el sistema,
    todos sus identificadores deben ser distintos entre si.
    """
    total_ot = 15
    ids_generados = set()

    for i in range(total_ot):
        datos = OTCrear(
            nombre=f"Cliente Prueba {i}",
            dni=f"{10000000 + i:08d}",
            placa=f"PLK-{i:03d}",
            marca="Toyota",
            modelo="Yaris",
            anio=2020,
            kilometraje=15000 + (i * 100),
            motivo=f"Revision periodica {i}",
            tecnico="Luis Pachas",
            observaciones="Sin observaciones",
        )
        resultado = repo_temporal.crear_ot(datos)
        id_ot = resultado["id_ot"]
        assert id_ot not in ids_generados, f"Colision detectada en ID: {id_ot}"
        ids_generados.add(id_ot)

    assert len(ids_generados) == total_ot


# Feature: asistente-taller-jorge-motors, Propiedad 2: Round-trip de campos obligatorios de OT
# Valida: Requisito 1.3
@settings(max_examples=25, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
@given(
    nombre=estrategia_texto_corto,
    dni=estrategia_dni,
    placa=estrategia_placa,
    marca=estrategia_texto_corto,
    modelo=estrategia_texto_corto,
    anio=st.integers(min_value=1900, max_value=anio_actual),
    km=st.integers(min_value=0, max_value=999999),
    motivo=estrategia_motivo,
    tecnico=estrategia_tecnico,
)
def test_propiedad_2_round_trip_campos_obligatorios(
    repo_temporal, nombre, dni, placa, marca, modelo, anio, km, motivo, tecnico
):
    """
    Para cualquier OT creada con datos validos generados aleatoriamente,
    recuperar esa OT del sistema debe retornar exactamente los mismos valores enviados.
    """
    datos = OTCrear(
        nombre=nombre,
        dni=dni,
        placa=placa,
        marca=marca,
        modelo=modelo,
        anio=anio,
        kilometraje=km,
        motivo=motivo,
        tecnico=tecnico,
    )
    res = repo_temporal.crear_ot(datos)
    id_creado = res["id_ot"]

    recuperada = repo_temporal.obtener_ot_por_id(id_creado)
    assert recuperada is not None
    assert recuperada.id == id_creado
    assert recuperada.nombre == nombre
    assert recuperada.dni == dni
    assert recuperada.placa == placa
    assert recuperada.marca == marca
    assert recuperada.modelo == modelo
    assert recuperada.anio == anio
    assert recuperada.kilometraje == km
    assert recuperada.motivo == motivo
    assert recuperada.tecnico == tecnico
    assert recuperada.estado == "abierta"
    assert recuperada.fecha_hora is not None


# Feature: asistente-taller-jorge-motors, Propiedad 3: Rechazo de OT con campos obligatorios faltantes
# Valida: Requisito 1.4
def test_propiedad_3_rechazo_campos_faltantes(cliente_api):
    """
    Para cada subconjunto propio de los campos obligatorios de una OT,
    el endpoint debe retornar 422 y no crear la OT.
    """
    campos_base = {
        "nombre": "Juan Valido",
        "dni": "87654321",
        "placa": "ABC-123",
        "marca": "Toyota",
        "modelo": "Corolla",
        "anio": 2021,
        "kilometraje": 25000,
        "motivo": "Fallo electrico",
        "tecnico": "Luis Luna",
    }

    # Verificar que omitir cualquiera de los campos obligatorios retorna 422
    for campo in campos_base.keys():
        datos_incompletos = dict(campos_base)
        del datos_incompletos[campo]

        respuesta = cliente_api.post("/ordenes", json=datos_incompletos)
        assert respuesta.status_code == 422, f"Se esperaba 422 al omitir campo {campo}, recibido {respuesta.status_code}"


def test_creacion_ot_exitosa_via_endpoint(cliente_api):
    """Verifica que POST /ordenes retorna 201 con id_ot y mensaje."""
    payload = {
        "nombre": "Carlos Mendoza",
        "dni": "44332211",
        "placa": "ABC-999",
        "marca": "Kia",
        "modelo": "Rio",
        "anio": 2022,
        "kilometraje": 12000,
        "motivo": "Cambio de pastillas",
        "tecnico": "Miguel Torres",
        "observaciones": "Cliente solicita revision rapida",
    }
    respuesta = cliente_api.post("/ordenes", json=payload)
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert "id_ot" in cuerpo
    assert cuerpo["id_ot"] > 0
    assert cuerpo["mensaje"] == "OT creada exitosamente"
