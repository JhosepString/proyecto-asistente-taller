# Producto · Sistema de Gestión de Inventario Jorge Motors · Redacta todos los documentos en español.

## Propósito
Digitalizar el registro de Órdenes de Trabajo y el control de inventario de repuestos de Jorge Motors, reemplazando el cuaderno y Excel para reducir descuadres de stock y demoras en la atención al cliente.

## Usuarios
- Recepcionista / asesor de servicio (usuario principal; registra y gestiona las OT)
- Técnico mecánico (consulta historial y stock para ejecutar reparaciones)
- Encargado de Compras/Almacén (gestiona alertas de stock mínimo y compara inventario físico)
- Gerente/Administración (genera reportes de desempeño por técnico)

## Lo que hace (DENTRO)
- Registro digital de Orden de Trabajo (OT)
- Consulta de historial de cliente y vehículo
- Consulta de stock de repuestos (solo lectura a través del Servidor MCP)
- Generación de alertas de stock mínimo
- Comparación de conteo físico con el registro del sistema
- Generación de reporte de OT por técnico

> **PENDIENTE (equipo):** La versión original de este documento indicaba "consulta y **actualización** de stock". El resto del sistema (requirements.md, ADR-002) trata el stock como **solo lectura** a través del MCP. Si se requiere actualizar el stock desde esta aplicación, debe abrirse un nuevo requisito funcional y revisarse ADR-002.

## Lo que NO hace (FUERA)
- Facturación electrónica integrada a SUNAT
- Módulo de pagos en línea
- App móvil para clientes
- Compra automática a proveedores

## Reglas no negociables (restricciones)
- Cumplimiento de la Ley N.° 29733 (Protección de Datos Personales): solo se almacenan y procesan datos simulados; ningún dato personal real se almacena ni expone
- Entrega limitada al semestre en curso (restricción de tiempo)
- El Servidor MCP de la semana 4 se usa en modo exclusivo de solo lectura; no se amplía con herramientas de escritura

---

## Historial de cambios

| Fecha | Hallazgo que lo origina | Cambio realizado |
|---|---|---|
| 2026-09-25 | Auditoría Fase 1: "Recepcionista" ausente en lista de usuarios pese a ser el actor principal en requirements.md | Recepcionista añadido con su descripción de rol |
| 2026-09-25 | Auditoría Fase 1: "actualización de stock" en DENTRO contradice el modelo de solo lectura del MCP (requirements.md, ADR-002) | Reemplazado por "Consulta de stock" con nota PENDIENTE para que el equipo decida |
