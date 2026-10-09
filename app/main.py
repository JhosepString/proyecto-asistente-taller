"""
Punto de entrada principal de la aplicacion FastAPI para Jorge Motors.
Configura el ciclo de vida, verifica credenciales segun Requisito 8.3,
monta archivos estaticos del frontend y registra los routers de los modulos.
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from app.modules.ordenes.router import router as router_ordenes
from app.modules.historial.router import router as router_historial
from app.modules.inventario.router import router as router_inventario
from app.modules.alertas.router import router as router_alertas
from app.modules.comparacion.router import router as router_comparacion

# Cargar variables de entorno desde archivo .env si existe
load_dotenv()

# Configuracion de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("asistente_taller")


def verificar_clave_gemini() -> None:
    """
    Verifica la presencia de la clave GEMINI_API_KEY segun Requisito 8.3.
    Termina el proceso con codigo distinto de cero si no esta definida,
    a menos que se indique MODO_TEST=1 para entornos de pruebas aislados.
    """
    clave = os.getenv("GEMINI_API_KEY")
    modo_test = os.getenv("MODO_TEST", "0") == "1"

    if not clave and not modo_test:
        logger.error("Error de configuracion: clave de API de asistencia no configurada.")
        sys.exit(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicacion FastAPI."""
    verificar_clave_gemini()
    logger.info("Aplicacion iniciada exitosamente.")
    yield
    logger.info("Aplicacion detenida.")


app = FastAPI(
    title="Jorge Motors - Asistente de Gestion de Taller y Repuestos",
    description="Sistema digital para ordenes de trabajo, inventario y asistencia de taller",
    version="1.0.0",
    lifespan=lifespan,
)

# Montar archivos estaticos si la carpeta existe
ruta_frontend = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
ruta_estaticos = os.path.join(ruta_frontend, "static")

if os.path.exists(ruta_estaticos):
    app.mount("/static", StaticFiles(directory=ruta_estaticos), name="static")


@app.get("/", include_in_schema=False)
def servir_inicio():
    """Sirve la pagina principal index.html."""
    ruta_index = os.path.join(ruta_frontend, "index.html")
    if os.path.exists(ruta_index):
        return FileResponse(ruta_index)
    return {"mensaje": "Jorge Motors API operativa"}


# Registrar routers
app.include_router(router_ordenes)
app.include_router(router_historial)
app.include_router(router_inventario)
app.include_router(router_alertas)
app.include_router(router_comparacion)
