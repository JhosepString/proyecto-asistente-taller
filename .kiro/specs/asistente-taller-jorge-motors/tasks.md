# Implementation Plan: Asistente de Gestión de Taller y Repuestos — Jorge Motors

## Overview

Implementación incremental del sistema completo: primero la base de datos y la estructura del proyecto, luego los módulos de dominio uno a uno (OT, Historial, Inventario, Alertas, Comparación, Reportes), los componentes compartidos (McpReadClient, GeminiGateway), el módulo de Asistente IA y finalmente el frontend HTML + JS. Cada módulo se integra con la aplicación principal antes de pasar al siguiente. Las sub-tareas de prueba marcadas con `*` son opcionales para un MVP rápido.

---

## Tasks

- [ ] 1. Configurar estructura del proyecto y base de datos
  - Crear la estructura de carpetas definida en el diseño: `app/`, `app/modules/`, `app/shared/`, `frontend/static/`, `data/`, `tests/`
  - Crear `requirements.txt` con las dependencias fijadas: `fastapi`, `uvicorn[standard]`, `httpx`, `python-dotenv`, `google-generativeai`, `pytest`, `hypothesis`
  - Crear `.env.example` con `GEMINI_API_KEY=your_key_here` (sin valor real)
  - Crear `data/seed.py`: script que genera `data/taller.db` con tablas `clientes`, `vehiculos`, `ordenes_trabajo`, `repuestos`, `stock` y `trazabilidad_ia`, pobladas con datos simulados (sin datos reales de personas — Requisito 8.2)
  - Crear `app/main.py` con la aplicación FastAPI base: arranque, montaje de archivos estáticos y verificación de `GEMINI_API_KEY` al inicio (Requisito 8.3)
  - _Requisitos: 1.2, 1.3, 8.1, 8.2, 8.3_

- [ ] 2. Implementar RepositorioOT y Módulo OT (Registro de OT)
  - [ ] 2.1 Crear modelos Pydantic y RepositorioOT
    - Definir `app/modules/ordenes/schemas.py` con `OTCrear` (campos obligatorios con validaciones de rango: año 1900–año_actual, km 0–999999, DNI 8 dígitos, placa máx. 10 car.) y `OTRespuesta`
    - Implementar `app/modules/ordenes/repositorio.py` con `RepositorioOT.crear_ot(datos) → OT` usando INSERT en SQLite y retornando el id generado con fecha/hora automática
    - _Requisitos: 1.2, 1.3, 1.4_

  - [ ]* 2.2 Escribir prueba de propiedad para unicidad de identificadores de OT
    - **Propiedad 1: Unicidad de identificadores de OT**
    - **Valida: Requisito 1.2**
    - Generar N OT con datos válidos aleatorios; verificar que todos los IDs retornados son distintos
    - `# Feature: asistente-taller-jorge-motors, Propiedad 1: Unicidad de identificadores de OT`

  - [ ]* 2.3 Escribir prueba de propiedad para round-trip de campos obligatorios
    - **Propiedad 2: Round-trip de campos obligatorios de OT**
    - **Valida: Requisito 1.3**
    - Generar datos válidos aleatorios, crear OT, recuperarla y verificar que los campos coinciden exactamente
    - `# Feature: asistente-taller-jorge-motors, Propiedad 2: Round-trip de campos obligatorios de OT`

  - [ ]* 2.4 Escribir prueba de propiedad para rechazo de OT con campos faltantes
    - **Propiedad 3: Rechazo de OT con campos obligatorios faltantes**
    - **Valida: Requisito 1.4**
    - Para cada subconjunto propio de campos obligatorios, verificar que el endpoint retorna 422 y el conteo de OT no aumenta
    - `# Feature: asistente-taller-jorge-motors, Propiedad 3: Rechazo de OT con campos obligatorios faltantes`

  - [ ] 2.5 Crear router del Módulo OT y registrarlo en `main.py`
    - Implementar `app/modules/ordenes/router.py` con `POST /ordenes` que usa `RepositorioOT`
    - Retornar 201 con `{id_ot, mensaje}` en éxito y 422 con campo indicado en error (Requisito 1.4, 1.5)
    - Registrar el router en `app/main.py`
    - _Requisitos: 1.1, 1.4, 1.5, 1.7_

- [ ] 3. Punto de control — Verificar Módulo OT
  - Asegurar que todas las pruebas del módulo OT pasen. Consultar al usuario si surge alguna duda.

- [ ] 4. Implementar McpReadClient
  - [ ] 4.1 Crear McpReadClient con manejo de disponibilidad
    - Implementar `app/shared/mcp_client.py` con la clase `McpReadClient`
    - Exponer métodos: `buscar_historial(criterio, tipo)`, `consultar_stock(termino)`, `listar_alertas()`, `comparar_conteo(items)`, `generar_reporte(fecha_inicio, fecha_fin)`
    - Si el servidor MCP no responde, elevar `McpNoDisponibleError` (capturado en cada módulo para retornar 503)
    - Incluir stub configurable para pruebas (sin conectar al MCP real hasta la semana 4)
    - _Requisitos: 2.4, 3.6, 4.6, 5.5, 6.6_

  - [ ]* 4.2 Escribir pruebas unitarias para McpReadClient con mock
    - Verificar comportamiento cuando el MCP responde correctamente
    - Verificar que `McpNoDisponibleError` se eleva cuando el servidor no está disponible
    - _Requisitos: 2.4, 3.6, 4.6, 5.5, 6.6_

- [ ] 5. Implementar Módulo Historial
  - [ ] 5.1 Crear router del Módulo Historial
    - Implementar `app/modules/historial/router.py` con `GET /historial?q=<placa_o_dni>`
    - Validar el formato de entrada antes de llamar al MCP: placa (máx. 8 car. alfanuméricos) o DNI (exactamente 8 dígitos); retornar 422 si no cumple (Requisito 2.5)
    - Invocar `McpReadClient.buscar_historial()` y retornar las hasta 100 OT más recientes
    - Manejar `McpNoDisponibleError` → 503 con mensaje al usuario (Requisito 2.4)
    - Registrar el router en `app/main.py`
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 5.2 Escribir prueba de propiedad para límite y orden del historial
    - **Propiedad 4: Límite y orden del historial de OT**
    - **Valida: Requisito 2.1**
    - Generar N OT con fechas aleatorias; verificar máximo 100 resultados y orden descendente por fecha
    - `# Feature: asistente-taller-jorge-motors, Propiedad 4: Límite y orden del historial de OT`

  - [ ]* 5.3 Escribir prueba de propiedad para completitud de campos de OT en historial
    - **Propiedad 5: Completitud de campos al consultar una OT del historial**
    - **Valida: Requisito 2.2**
    - Para cualquier OT almacenada, verificar que la respuesta contiene exactamente los 6 campos requeridos
    - `# Feature: asistente-taller-jorge-motors, Propiedad 5: Completitud de campos al consultar una OT del historial`

  - [ ]* 5.4 Escribir prueba de propiedad para rechazo de búsqueda con formato inválido
    - **Propiedad 6: Rechazo de búsqueda con formato inválido**
    - **Valida: Requisito 2.5**
    - Para cadenas que no cumplen el formato de placa ni DNI, verificar que el endpoint retorna 422 sin consultar el MCP
    - `# Feature: asistente-taller-jorge-motors, Propiedad 6: Rechazo de búsqueda con formato inválido`

- [ ] 6. Implementar Módulo Inventario
  - [ ] 6.1 Crear router del Módulo Inventario
    - Implementar `app/modules/inventario/router.py` con `GET /inventario?q=<nombre_o_codigo>`
    - Validar que el campo no esté vacío ni sea solo espacios; retornar 422 si lo está (Requisito 3.7)
    - Invocar `McpReadClient.consultar_stock()` y retornar nombre, código, cantidad disponible, unidad de medida
    - Manejar repuesto no encontrado → 200 con `{resultados: [], mensaje}` (Requisito 3.5)
    - Manejar `McpNoDisponibleError` → 503 (Requisito 3.6)
    - Registrar el router en `app/main.py`
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [ ]* 6.2 Escribir prueba de propiedad para completitud e inmutabilidad de consulta de stock
    - **Propiedad 7: Completitud e inmutabilidad de la consulta de stock**
    - **Valida: Requisito 3.2**
    - Para cualquier repuesto existente, verificar que la respuesta tiene exactamente 4 campos y que el stock no se modifica tras la consulta
    - `# Feature: asistente-taller-jorge-motors, Propiedad 7: Completitud e inmutabilidad de la consulta de stock`

  - [ ]* 6.3 Escribir prueba de propiedad para exactitud de búsqueda por código
    - **Propiedad 8: Exactitud de búsqueda por código de repuesto**
    - **Valida: Requisito 3.3**
    - Para cualquier código existente, verificar que el resultado contiene exactamente ese código
    - `# Feature: asistente-taller-jorge-motors, Propiedad 8: Exactitud de búsqueda por código de repuesto`

  - [ ]* 6.4 Escribir prueba de propiedad para completitud de resultados por nombre
    - **Propiedad 9: Completitud de resultados en búsqueda por nombre de repuesto**
    - **Valida: Requisito 3.4**
    - Para cualquier término que coincida con K repuestos, verificar que el resultado contiene exactamente esos K repuestos
    - `# Feature: asistente-taller-jorge-motors, Propiedad 9: Completitud de resultados en búsqueda por nombre de repuesto`

  - [ ]* 6.5 Escribir prueba de propiedad para rechazo de entrada vacía en stock
    - **Propiedad 10: Rechazo de consulta de stock con entrada vacía o de solo espacios**
    - **Valida: Requisito 3.7**
    - Para cadenas vacías o de solo espacios, verificar que el endpoint retorna 422 sin consultar el MCP
    - `# Feature: asistente-taller-jorge-motors, Propiedad 10: Rechazo de consulta de stock con entrada vacía o de solo espacios`

- [ ] 7. Implementar Módulo Alertas
  - [ ] 7.1 Crear router del Módulo Alertas
    - Implementar `app/modules/alertas/router.py` con `GET /alertas`
    - Invocar `McpReadClient.listar_alertas()` y retornar la lista de repuestos con cantidad ≤ stock_mínimo
    - Incluir en cada alerta: nombre, código, cantidad actual, stock_mínimo (Requisito 4.2)
    - Si lista vacía → 200 con mensaje indicando que no hay alertas activas (Requisito 4.3)
    - Manejar `McpNoDisponibleError` → 503 (Requisito 4.6)
    - Registrar el router en `app/main.py`
    - _Requisitos: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ]* 7.2 Escribir prueba de propiedad para corrección del filtrado de alertas
    - **Propiedad 11: Corrección del filtrado de alertas de stock mínimo**
    - **Valida: Requisitos 4.1, 4.2**
    - Para inventario con N repuestos de cantidades aleatorias, verificar que la lista contiene exactamente los repuestos con cantidad ≤ stock_mínimo
    - `# Feature: asistente-taller-jorge-motors, Propiedad 11: Corrección del filtrado de alertas de stock mínimo`

- [ ] 8. Implementar Módulo Comparación y RepositorioComparacion
  - [ ] 8.1 Crear modelos Pydantic y RepositorioComparacion
    - Definir `app/modules/comparacion/schemas.py` con `ItemConteo`, `SolicitudComparacion` y `ResultadoComparacion`
    - Implementar `app/modules/comparacion/repositorio.py` con `RepositorioComparacion.guardar_comparacion(resultados)` usando INSERT en SQLite
    - _Requisitos: 5.1, 5.2_

  - [ ] 8.2 Crear router del Módulo Comparación
    - Implementar `app/modules/comparacion/router.py` con `POST /comparacion`
    - Validar que se ingrese al menos un ítem de conteo; retornar 422 si no (Requisito 5.4)
    - Invocar `McpReadClient.comparar_conteo()` para obtener cantidades del sistema
    - Calcular diferencia = conteo_físico − cantidad_sistema para cada repuesto
    - Marcar con indicador de descuadre si diferencia ≠ 0 (Requisito 5.3)
    - Manejar repuesto no encontrado → excluir fila con mensaje (Requisito 5.6)
    - Manejar `McpNoDisponibleError` → 503 (Requisito 5.5)
    - Persistir resultados con `RepositorioComparacion`
    - Registrar el router en `app/main.py`
    - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ]* 8.3 Escribir prueba de propiedad para corrección del cálculo de diferencias
    - **Propiedad 12: Corrección del cálculo de diferencias en comparación de conteo físico**
    - **Valida: Requisitos 5.1, 5.2**
    - Para cualquier par (conteo_físico, cantidad_sistema), verificar que diferencia = conteo_físico − cantidad_sistema con signo correcto y los 5 campos presentes
    - `# Feature: asistente-taller-jorge-motors, Propiedad 12: Corrección del cálculo de diferencias en comparación de conteo físico`

  - [ ]* 8.4 Escribir prueba de propiedad para clasificación del indicador de descuadre
    - **Propiedad 13: Clasificación correcta del indicador de descuadre**
    - **Valida: Requisito 5.3**
    - Para cualquier diferencia ≠ 0, verificar indicador de descuadre presente; para diferencia = 0, verificar que no está
    - `# Feature: asistente-taller-jorge-motors, Propiedad 13: Clasificación correcta del indicador de descuadre`

- [ ] 9. Punto de control — Verificar módulos de dominio (OT, Historial, Inventario, Alertas, Comparación)
  - Asegurar que todas las pruebas de los módulos anteriores pasen. Consultar al usuario si surge alguna duda.

- [ ] 10. Implementar Módulo Reportes
  - [ ] 10.1 Crear router del Módulo Reportes con exportación CSV
    - Implementar `app/modules/reportes/router.py` con `GET /reportes?fecha_inicio=&fecha_fin=`
    - Validar que fecha_inicio ≤ fecha_fin; retornar 422 si no (Requisito 6.4)
    - Invocar `McpReadClient.generar_reporte()` para obtener OT en el rango (extremos inclusivos)
    - Agrupar por técnico: total de OT, cantidad por estado (abierta, en proceso, cerrada)
    - Si no hay OT en el rango → 200 con mensaje (Requisito 6.3)
    - Exponer `GET /reportes/csv` que retorna `StreamingResponse` con `Content-Type: text/csv` y las 5 columnas definidas (nombre técnico, total OT, abiertas, en proceso, cerradas) en UTF-8 (Requisito 6.5)
    - Manejar `McpNoDisponibleError` → 503 (Requisito 6.6)
    - Registrar el router en `app/main.py`
    - _Requisitos: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [ ]* 10.2 Escribir prueba de propiedad para filtrado de OT por rango de fechas
    - **Propiedad 14: Filtrado correcto de OT por rango de fechas en el reporte**
    - **Valida: Requisitos 6.1, 6.2**
    - Para cualquier rango válido, verificar que todas las OT incluidas están dentro del rango y ninguna fuera
    - `# Feature: asistente-taller-jorge-motors, Propiedad 14: Filtrado correcto de OT por rango de fechas en el reporte`

  - [ ]* 10.3 Escribir prueba de propiedad para rechazo de rango de fechas inválido
    - **Propiedad 15: Rechazo de rango de fechas inválido en el reporte**
    - **Valida: Requisito 6.4**
    - Para cualquier par donde fecha_inicio > fecha_fin, verificar que el endpoint retorna 422 sin consultar el MCP
    - `# Feature: asistente-taller-jorge-motors, Propiedad 15: Rechazo de rango de fechas inválido en el reporte`

  - [ ]* 10.4 Escribir prueba de propiedad para completitud y consistencia del CSV
    - **Propiedad 16: Completitud y consistencia del CSV exportado**
    - **Valida: Requisito 6.5**
    - Para cualquier reporte generado, verificar que el CSV tiene exactamente 5 columnas y que abierta + en_proceso + cerrada = total para cada fila
    - `# Feature: asistente-taller-jorge-motors, Propiedad 16: Completitud y consistencia del CSV exportado`

- [ ] 11. Implementar GeminiGateway y Módulo Asistente IA
  - [ ] 11.1 Crear GeminiGateway con degradación controlada
    - Implementar `app/shared/gemini_gateway.py` con la clase `GeminiGateway`
    - Leer `GEMINI_API_KEY` exclusivamente desde variable de entorno (nunca del código — Requisito 8.1)
    - Aplicar timeout < 30 s; retornar resultado tipado: `GeminiExito(respuesta: str)` o `GeminiError(mensaje: str)`
    - En caso de error o timeout, retornar `GeminiError` sin propagar excepción al llamador (degradación controlada — ADR-003)
    - _Requisitos: 8.1, 8.3, 9.3_

  - [ ]* 11.2 Escribir pruebas unitarias para GeminiGateway
    - Verificar comportamiento en éxito (mock de respuesta Gemini)
    - Verificar que timeout retorna `GeminiError` sin propagar excepción
    - Verificar que error de API retorna `GeminiError`
    - _Requisitos: 8.1, 8.3_

  - [ ] 11.3 Crear router del Módulo Asistente IA
    - Implementar `app/modules/asistente/router.py` con `POST /asistente`
    - Recibir `{pregunta, rol}` donde rol ∈ {Recepcionista, Técnico, Encargado_Compras, Gerente}
    - Invocar `McpReadClient` para obtener contexto de inventario/historial relevante
    - Pasar contexto + pregunta a `GeminiGateway.generar_respuesta()`
    - Registrar en `trazabilidad_ia`: id único, timestamp ISO 8601, rol, pregunta, contexto MCP, respuesta (Requisito 9.1, 9.2)
    - Si `GeminiGateway` retorna `GeminiError`, responder 200 con `{asistencia: null, mensaje: "Asistencia de IA no disponible en este momento"}` y registrar el error en el log (Requisito 9.3)
    - Registrar el router en `app/main.py`
    - _Requisitos: 9.1, 9.2, 9.3_

  - [ ]* 11.4 Escribir prueba de propiedad para completitud y unicidad del log de trazabilidad IA
    - **Propiedad 17: Completitud y unicidad del log de trazabilidad de IA**
    - **Valida: Requisitos 9.1, 9.2**
    - Para N consultas procesadas, verificar que cada entrada tiene los 6 campos requeridos y los N identificadores son distintos
    - `# Feature: asistente-taller-jorge-motors, Propiedad 17: Completitud y unicidad del log de trazabilidad de IA`

- [ ] 12. Implementar indicador de carga y manejo de timeouts en el frontend
  - [ ] 12.1 Implementar indicador de carga y manejo de timeouts en el frontend
    - En `frontend/static/app.js`, añadir lógica que muestra el spinner/barra de progreso cuando una petición supera 2 segundos (Requisito 7.2)
    - Añadir lógica que oculta el spinner y muestra mensaje de error con opción de reintento cuando la petición supera 30 segundos (Requisito 7.3)
    - _Requisitos: 7.2, 7.3_

- [ ] 13. Construir el frontend HTML + JS
  - [ ] 13.1 Implementar `frontend/index.html` con navegación por rol y pantallas de cada módulo
    - Crear `frontend/index.html` con selector de rol (Recepcionista, Técnico, Encargado_Compras, Gerente) visible sin autenticación (deuda técnica aceptada — ADR-002)
    - Implementar pantalla de Registro de OT: formulario con los 9 campos obligatorios y manejo de errores de validación con el campo indicado (Requisito 1.4, 1.5)
    - Implementar pantalla de Historial: campo de búsqueda por placa o DNI, lista de resultados, detalle de OT seleccionada con los 6 campos (Requisito 2.1, 2.2, 2.3)
    - Implementar pantalla de Inventario: campo de búsqueda, lista de resultados con 4 campos por repuesto (Requisito 3.1, 3.2)
    - Implementar pantalla de Alertas: lista automática al cargar con nombre, código, cantidad actual y stock_mínimo (Requisito 4.1, 4.2)
    - Implementar pantalla de Comparación: formulario de conteo físico y tabla de resultados con indicador de descuadre (Requisito 5.1, 5.2, 5.3)
    - Implementar pantalla de Reportes: selector de fechas, tabla por técnico y botón de exportar CSV (Requisito 6.1, 6.5)
    - Implementar pantalla de Asistente IA: campo de pregunta y área de respuesta con degradación visible (Requisito 9.1, 9.3)
    - Servir `frontend/` como archivos estáticos desde `app/main.py`
    - _Requisitos: 1.4, 1.5, 2.1, 2.2, 3.1, 3.2, 4.1, 4.2, 5.1, 5.2, 5.3, 6.1, 6.5, 9.1, 9.3_

- [ ] 14. Punto de control final — Verificar sistema integrado
  - Asegurar que todas las pruebas del sistema pasen (unitarias, PBT y de humo). Consultar al usuario si surge alguna duda.
  - [ ] 14.1 Smoke test de rendimiento para R7.1 (p95 ≤ 5 s)
    - Ejecutar 100 peticiones consecutivas contra `/historial` y `/inventario` con el Servidor MCP disponible y un usuario concurrente
    - Medir el p95; documentar el resultado en `docs/resultados_rendimiento.md`
    - Si el p95 supera 5 s, abrir una incidencia en el repositorio antes de cerrar la tarea
    - _Requisito: R7.1_

---

## Notes

- Las sub-tareas marcadas con `*` son opcionales y se pueden omitir para un MVP rápido.
- Cada tarea referencia los requisitos específicos del documento `requirements.md` para trazabilidad.
- Las pruebas de propiedades (Hypothesis) deben ejecutarse con mínimo 100 iteraciones; las que involucran MCP o Gemini usan mocks para mantener las pruebas rápidas y deterministas.
- El servidor MCP real se conecta en la semana 4; hasta entonces `McpReadClient` usa un stub configurable.
- Los checkpoints en las tareas 3, 9 y 14 garantizan validación incremental antes de avanzar al siguiente módulo.
- El rol de usuario se selecciona en la UI sin autenticación (deuda técnica aceptada, documentada en ADR-002).

---

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2.1", "4.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4", "4.2"] },
    { "id": 3, "tasks": ["2.5"] },
    { "id": 4, "tasks": ["3"] },
    { "id": 5, "tasks": ["5.1", "6.1", "7.1", "8.1"] },
    { "id": 6, "tasks": ["5.2", "5.3", "5.4", "6.2", "6.3", "6.4", "6.5", "7.2", "8.2"] },
    { "id": 7, "tasks": ["8.3", "8.4", "10.1"] },
    { "id": 8, "tasks": ["10.2", "10.3", "10.4", "11.1"] },
    { "id": 9, "tasks": ["9"] },
    { "id": 10, "tasks": ["11.2", "11.3"] },
    { "id": 11, "tasks": ["11.4", "12.1"] },
    { "id": 12, "tasks": ["13.1"] },
    { "id": 13, "tasks": ["14"] }
  ]
}
```


---

## Historial de cambios

| Fecha | Hallazgo que lo origina | Cambio realizado |
|---|---|---|
| 2026-09-25 | Auditor?a Fase 1 ? Verificaci?n 6: checkpoints 3, 9 y 14 ausentes en el Task Dependency Graph | Grafo actualizado con olas 4, 9 y 13 para dichos checkpoints |
| 2026-09-25 | Auditor?a Fase 1 ? Verificaci?n 1: R7.1 (p95 ? 5 s) sin tarea observable | Sub-tarea 14.1 a?adida: smoke test 100 peticiones, medici?n p95, documentaci?n resultado |
