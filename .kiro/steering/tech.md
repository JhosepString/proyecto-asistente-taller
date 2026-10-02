# Tecnología · Sistema de Gestión de Inventario Jorge Motors

Redacta en español.

## Backend
- Python 3.11+
- FastAPI

## Frontend
- HTML + JS simple (sin frameworks pesados)

## IA
- Gemini API para funcionalidades de asistencia (ej. explicar disponibilidad de un repuesto al cliente)
- La clave de la API se guarda en variable de entorno, nunca en el código

## Base de datos
- SQLite con datos simulados (clientes, vehículos, repuestos, stock)

## Integración de datos
- Servidor MCP propio, de solo lectura, conectado en la semana 4, usado por las funcionalidades marcadas con * (consultar stock, actualizar inventario, generar reporte de bajo stock)

## Control de versiones
- Git/GitHub

## Principio de diseño
- Sin sobreingeniería: priorizar la solución más simple que cumpla el alcance DENTRO definido, evitando patrones o capas innecesarias para un proyecto de un semestre.