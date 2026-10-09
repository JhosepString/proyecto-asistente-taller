---
inclusion: auto
name: structure
description: Estructura de carpetas canónica del proyecto asistente_taller. Activar cuando se discuta dónde crear, mover o nombrar archivos y directorios.
---

# Estructura de carpetas · Asistente de Gestión de Taller y Repuestos · Jorge Motors

> Fuente de verdad para la ubicación de todos los archivos del proyecto.
> Toda referencia en design.md, tasks.md o cualquier ADR debe coincidir con este documento.

```
asistente_taller/          ← raíz del repositorio
  app/
    main.py                ← entrada FastAPI: arranque, lifespan, montaje de routers y estáticos
    modules/
      ordenes/             ← Módulo OT (H1): schemas.py, router.py, repositorio.py
      historial/           ← Módulo Historial (H2): schemas.py, router.py
      inventario/          ← Módulo Inventario (H3): schemas.py, router.py
      alertas/             ← Módulo Alertas (H4): schemas.py, router.py
      comparacion/         ← Módulo Comparación (H5): schemas.py, router.py, repositorio.py
      reportes/            ← Módulo Reportes (H6): schemas.py, router.py
      asistente/           ← Módulo Asistente IA (Unidad 3): schemas.py, router.py
    shared/
      mcp_client.py        ← McpReadClient: único punto de acceso al Servidor MCP (solo lectura)
      gemini_gateway.py    ← GeminiGateway: único punto de acceso a Gemini API
  frontend/
    index.html             ← SPA principal servida como archivo estático por FastAPI
    static/
      app.js               ← lógica JS: llamadas a la API REST, spinner, timeout 30 s
      styles.css           ← estilos base
  data/
    taller.db              ← base de datos SQLite (generada por seed.py; nunca se versiona con datos)
    seed.py                ← script de generación de datos simulados (sin datos personales reales)
  tests/
    test_ordenes.py        ← pruebas unitarias y PBT del Módulo OT
    test_historial.py
    test_inventario.py
    test_alertas.py
    test_comparacion.py
    test_reportes.py
    test_asistente.py
    test_mcp_client.py
    test_gemini_gateway.py
  docs/
    ADR-001.md             ← FastAPI vs Flask vs Django
    ADR-002.md             ← Acceso a datos: lecturas MCP, escrituras repositorio propio
    ADR-003.md             ← Integración Gemini con degradación controlada
  .env.example             ← plantilla de variables de entorno (GEMINI_API_KEY=your_key_here)
  .gitignore               ← debe incluir .env, data/taller.db, __pycache__
  requirements.txt         ← dependencias fijadas (fastapi, uvicorn[standard], httpx,
                             python-dotenv, google-generativeai, pytest, hypothesis)
  README.md
```

## Reglas de nomenclatura

- Módulos de dominio: `app/modules/<nombre_en_minúscula_sin_tildes>/`
- Archivos dentro de cada módulo: siempre `schemas.py`, `router.py` y, si hay escrituras, `repositorio.py`
- Archivos compartidos: solo en `app/shared/`; no crear subcarpetas en shared/
- Tests: un archivo por módulo, con prefijo `test_`
- La base de datos `data/taller.db` nunca se incluye en el repositorio si contiene datos; solo se versiona `seed.py`

## Puertos por proceso (PENDIENTE de confirmar con el equipo contra la configuración real del Servidor MCP de la semana 4)

| Proceso | Puerto por defecto |
|---|---|
| FastAPI App (`uvicorn`) | 8000 |
| Servidor MCP | 8001 — **PENDIENTE verificación** |

---

## Historial de cambios

| Fecha | Hallazgo que lo origina | Cambio realizado |
|---|---|---|
| 2026-09-25 | Auditoría Fase 1: estructura de carpetas documentada solo en design.md y tasks.md, sin archivo de steering canónico | Archivo creado como steering con inclusion: auto |
