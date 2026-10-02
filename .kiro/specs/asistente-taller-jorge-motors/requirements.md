# Requirements Document

## Introduction

El **Asistente de Gestión de Taller y Repuestos para Jorge Motors** digitaliza el registro de Órdenes de Trabajo (OT) y el control de inventario de repuestos, reemplazando el cuaderno y el Excel actuales. El sistema elimina el doble registro en recepción, reduce los descuadres entre el inventario físico y el digital, y acelera el diagnóstico técnico al centralizar el historial de clientes y vehículos.

El sistema está compuesto por un backend FastAPI (Python 3.11+), un frontend HTML + JavaScript simple, una base de datos SQLite con datos simulados y la Gemini API para funcionalidades de asistencia. Consume un servidor MCP propio de solo lectura (conectado en la semana 4) para todas las consultas de inventario y de historial. Todos los datos son simulados; ningún dato personal real es almacenado ni expuesto (Ley N.° 29733).

**Fuera de alcance:** facturación electrónica e integración con SUNAT, módulo de pagos en línea, compras automáticas a proveedores y aplicación móvil para clientes.

---

## Glossary

- **Sistema**: La aplicación web Asistente de Gestión de Taller y Repuestos de Jorge Motors.
- **OT / Orden de Trabajo**: Registro digital que documenta el ingreso de un vehículo al taller, el motivo de atención, el técnico asignado y el estado del servicio.
- **Recepcionista**: Asesor de servicio responsable de registrar y gestionar las OT.
- **Técnico**: Mecánico automotriz asignado a una OT (Luis Pachas, Luis Luna, Miguel Torres).
- **Encargado_Compras**: Encargado de Compras/Abastecimiento (Génesis Hernández) responsable del inventario de repuestos.
- **Gerente**: Gerente de Jorge Motors, responsable de la supervisión operativa y el desempeño del taller.
- **Servidor_MCP**: Servidor MCP de solo lectura propio del proyecto, disponible desde la semana 4, que expone los datos de inventario e historial almacenados en SQLite.
- **Stock_Mínimo**: Cantidad umbral configurada por repuesto; cuando el stock real cae por debajo de ese umbral se activa una alerta.
- **Conteo_Físico**: Recuento manual de unidades de repuestos realizado por el Encargado_Compras e ingresado al Sistema para comparación.
- **Gemini_API**: Servicio de IA de Google utilizado para asistencia contextual; su clave se gestiona exclusivamente mediante variable de entorno.

---

## Requirements

### Requisito 1: Registro de Orden de Trabajo Digital

**Historia de usuario:** Como recepcionista, quiero registrar la orden de trabajo de forma digital al recibir un vehículo, para eliminar el doble registro en cuaderno y Excel y reducir el tiempo de atención en recepción.

#### Criterios de aceptación

1. WHEN el Recepcionista completa todos los campos obligatorios definidos en el criterio 3 y envía el formulario, THE Sistema SHALL crear la OT digital y dejarla disponible para el Técnico asignado en un plazo máximo de 2 minutos desde el envío del formulario.
2. THE Sistema SHALL asignar automáticamente un identificador único e irrepetible a cada OT en el momento de su creación.
3. THE Sistema SHALL registrar en cada OT los siguientes campos obligatorios: nombre del cliente (máximo 100 caracteres), DNI del cliente (exactamente 8 dígitos numéricos), placa del vehículo (máximo 10 caracteres), marca (máximo 50 caracteres), modelo (máximo 50 caracteres), año del vehículo (entre 1900 y el año en curso inclusive), kilometraje (entre 0 y 999,999 km inclusive), motivo de ingreso (máximo 500 caracteres), Técnico asignado y fecha/hora de creación generada automáticamente por el Sistema.
4. IF el Recepcionista omite algún campo obligatorio de la OT, THEN THE Sistema SHALL mostrar un mensaje de error indicando el campo faltante y no crear la OT hasta que todos los campos obligatorios estén completos.
5. WHEN la OT es creada exitosamente, THE Sistema SHALL mostrar al Recepcionista la confirmación con el identificador de la OT generada.
6. THE Sistema SHALL permitir registrar únicamente datos de prueba que no correspondan a personas naturales identificables; ningún valor ingresado en los campos de nombre o DNI podrá coincidir con datos reales de personas, en cumplimiento de la Ley N.° 29733.
7. IF el Sistema no puede crear la OT dentro del plazo de 2 minutos desde el envío del formulario, THEN THE Sistema SHALL mostrar al Recepcionista un mensaje de error indicando que la operación no pudo completarse y conservar los datos ingresados en el formulario para permitir un nuevo intento.

---

### Requisito 2: Consulta de Historial de Cliente y Vehículo

**Historia de usuario:** Como técnico mecánico, quiero consultar el historial del cliente y del vehículo, para diagnosticar más rápido sin depender del cuaderno físico.

#### Criterios de aceptación

1. WHEN el Técnico ingresa una placa (máximo 8 caracteres alfanuméricos) o un DNI (exactamente 8 dígitos numéricos) y ejecuta la búsqueda, THE Sistema SHALL devolver las hasta 100 OT más recientes asociadas a ese criterio en un plazo máximo de 5 segundos.
2. WHEN el Técnico selecciona una OT del historial, THE Sistema SHALL mostrar exactamente los siguientes campos: identificador de OT, fecha, motivo de ingreso, Técnico asignado, estado y observaciones técnicas.
3. IF no existen OT previas para la placa o el DNI ingresados, THEN THE Sistema SHALL mostrar un mensaje indicando que no se encontraron registros para ese criterio de búsqueda.
4. IF el Servidor_MCP no está disponible al momento de la consulta, THEN THE Sistema SHALL mostrar un mensaje de error indicando que el servicio de historial no está disponible en este momento.
5. IF el Técnico envía el formulario de búsqueda con el campo vacío o con un formato que no corresponda a placa (máximo 8 caracteres alfanuméricos) ni a DNI (exactamente 8 dígitos numéricos), THEN THE Sistema SHALL mostrar un mensaje de error indicando el formato requerido y no ejecutar la búsqueda.

---

### Requisito 3: Consulta de Stock de Repuestos

**Historia de usuario:** Como técnico mecánico, quiero consultar el stock de un repuesto antes de iniciar la reparación, para no detener el trabajo por falta de información sobre el inventario disponible.

#### Criterios de aceptación

1. WHEN el Técnico o el Encargado_Compras ingresa el nombre (máximo 100 caracteres) o el código (máximo 20 caracteres) de un repuesto y ejecuta la consulta, THE Sistema SHALL mostrar la cantidad actual en stock en un plazo máximo de 5 segundos.
2. WHEN el Sistema devuelve el resultado de la consulta de stock, THE Sistema SHALL mostrar exactamente: nombre del repuesto, código, cantidad disponible y unidad de medida, y la consulta no modificará ningún dato del inventario.
3. IF el código ingresado coincide exactamente con un repuesto del inventario, THE Sistema SHALL mostrar únicamente ese repuesto.
4. IF la búsqueda por nombre devuelve más de un repuesto coincidente, THEN THE Sistema SHALL mostrar la lista de todos los repuestos coincidentes para que el usuario seleccione el deseado.
5. IF el código o nombre del repuesto ingresado no existe en el inventario, THEN THE Sistema SHALL mostrar un mensaje indicando que el repuesto no fue encontrado.
6. IF el Servidor_MCP no está disponible al momento de la consulta, THEN THE Sistema SHALL mostrar un mensaje de error indicando que el servicio de inventario no está disponible en este momento.
7. IF el usuario envía el formulario de búsqueda con el campo vacío o que contenga solo espacios en blanco, THEN THE Sistema SHALL mostrar un mensaje de error solicitando ingresar un nombre o código válido y no ejecutar la consulta.

---

### Requisito 4: Alertas de Stock Mínimo

**Historia de usuario:** Como encargada de compras y abastecimiento, quiero recibir una alerta cuando un repuesto llegue a su stock mínimo, para generar el pedido al proveedor antes de que se agote el inventario.

#### Criterios de aceptación

1. WHEN el Encargado_Compras accede al panel del Sistema, THE Sistema SHALL consultar los niveles de stock a través del Servidor_MCP y generar las alertas correspondientes en un plazo máximo de 5 segundos, mostrando la lista consolidada de todos los repuestos cuya cantidad sea menor o igual al Stock_Mínimo configurado.
2. WHEN el Sistema muestra una alerta de stock mínimo, THE Sistema SHALL incluir en cada alerta al menos: nombre del repuesto, código, cantidad actual y Stock_Mínimo configurado.
3. IF ningún repuesto ha alcanzado su Stock_Mínimo al momento de la consulta, THEN THE Sistema SHALL mostrar un estado que indique que no hay alertas de stock activas.
4. WHEN el Encargado_Compras accede al panel del Sistema, THE Sistema SHALL mostrar la lista consolidada de todos los repuestos cuya cantidad sea menor o igual al Stock_Mínimo configurado.
5. IF la búsqueda de alertas detecta que la cantidad de un repuesto es menor o igual al Stock_Mínimo configurado, THEN THE Sistema SHALL incluir ese repuesto en la lista de alertas visible para el Encargado_Compras.
6. IF el Servidor_MCP no está disponible cuando el Encargado_Compras accede al panel, THEN THE Sistema SHALL mostrar un mensaje de error indicando que el servicio de inventario no está disponible y no mostrará alertas hasta que el servicio se restaure.

---

### Requisito 5: Comparación de Conteo Físico con Registro del Sistema

**Historia de usuario:** Como encargada de compras y abastecimiento, quiero comparar el conteo físico de repuestos con el registro del sistema, para detectar y documentar los descuadres entre el inventario real y el digital.

#### Criterios de aceptación

1. WHEN el Encargado_Compras ingresa las cantidades del Conteo_Físico para uno o más repuestos y solicita la comparación, THE Sistema SHALL consultar las cantidades registradas en el Servidor_MCP y calcular la diferencia (Conteo_Físico − cantidad registrada en el sistema) para cada repuesto ingresado en un plazo máximo de 5 segundos.
2. WHEN el Sistema presenta los resultados de la comparación, THE Sistema SHALL mostrar, por cada repuesto comparado: nombre, código, cantidad registrada en el sistema, cantidad del Conteo_Físico y diferencia exacta expresada como valor entero con signo (positivo si hay excedente físico, negativo si hay faltante físico, cero si coinciden).
3. IF la diferencia entre el Conteo_Físico y el registro del sistema es distinta de cero para algún repuesto, THEN THE Sistema SHALL marcar ese repuesto con un indicador de descuadre claramente distinguible del resto de filas en los resultados.
4. IF el Encargado_Compras no ingresa ninguna cantidad de Conteo_Físico antes de solicitar la comparación, THEN THE Sistema SHALL mostrar un mensaje de error indicando que se debe ingresar al menos un repuesto con su conteo físico.
5. IF el Servidor_MCP no está disponible cuando el Encargado_Compras solicita la comparación, THEN THE Sistema SHALL mostrar un mensaje de error indicando que el servicio de inventario no está disponible y no ejecutará la comparación.
6. IF el código o nombre de un repuesto ingresado en el Conteo_Físico no existe en el inventario del sistema, THEN THE Sistema SHALL mostrar un mensaje indicando que ese repuesto no fue encontrado y no incluirá esa fila en los resultados de la comparación.

---

### Requisito 6: Reporte de Órdenes de Trabajo por Técnico

**Historia de usuario:** Como gerente de Jorge Motors, quiero generar un reporte de órdenes de trabajo agrupado por técnico, para evaluar la carga de trabajo y el desempeño de cada mecánico en un período determinado.

#### Criterios de aceptación

1. WHEN el Gerente selecciona un rango de fechas (ambos extremos inclusivos) y solicita el reporte, THE Sistema SHALL consultar el Servidor_MCP y presentar, por cada Técnico, el número total de OT registradas en el período y la cantidad de OT por estado (abierta, en proceso, cerrada).
2. THE Sistema SHALL incluir en el reporte únicamente las OT cuya fecha de creación sea igual o posterior a la fecha de inicio e igual o anterior a la fecha de fin del rango seleccionado por el Gerente.
3. IF no existen OT en el rango de fechas seleccionado, THEN THE Sistema SHALL mostrar un mensaje indicando que no se encontraron órdenes de trabajo en el período indicado.
4. IF la fecha de inicio del rango es posterior a la fecha de fin, THEN THE Sistema SHALL mostrar un mensaje de error indicando que el rango de fechas es inválido y no generará el reporte hasta que el rango sea corregido.
5. WHEN el reporte es generado exitosamente, THE Sistema SHALL permitir al Gerente exportar los resultados en formato CSV con las siguientes columnas mínimas: nombre del Técnico, total de OT en el período, cantidad de OT con estado "abierta", cantidad de OT con estado "en proceso" y cantidad de OT con estado "cerrada".
6. IF el Servidor_MCP no está disponible cuando el Gerente solicita el reporte, THEN THE Sistema SHALL mostrar un mensaje de error indicando que el servicio de datos no está disponible y no generará el reporte.

---

### Requisito 7: Rendimiento y Disponibilidad del Sistema

**Historia de usuario:** Como usuario del sistema (Recepcionista, Técnico, Encargado_Compras o Gerente), quiero que el sistema responda de forma oportuna, para no interrumpir el flujo de trabajo del taller.

#### Criterios de aceptación

1. THE Sistema SHALL responder al menos el 95 % de las consultas de historial y de stock en un tiempo igual o menor a 5 segundos, medido en una sesión con un único usuario concurrente y con el Servidor_MCP disponible.
2. IF una operación tarda más de 2 segundos en devolver respuesta, THEN THE Sistema SHALL mostrar al usuario un indicador de carga visible (spinner o barra de progreso) mientras procesa la solicitud.
3. IF una operación supera los 30 segundos sin devolver respuesta, THEN THE Sistema SHALL ocultar el indicador de carga, mostrar un mensaje de error indicando que la operación no pudo completarse y ofrecer al usuario la opción de volver a intentar la operación.

---

### Requisito 8: Seguridad de Credenciales y Privacidad de Datos

**Historia de usuario:** Como administrador del proyecto, quiero que las credenciales de la API y los datos sensibles estén protegidos, para cumplir con la Ley N.° 29733 y con las buenas prácticas de seguridad del equipo.

#### Criterios de aceptación

1. THE Sistema SHALL almacenar la clave de la Gemini_API exclusivamente en una variable de entorno y nunca incluirla en el código fuente, en archivos de configuración ni en archivos .env versionados en Git.
2. THE Sistema SHALL utilizar únicamente datos simulados durante el desarrollo y las pruebas; los datos simulados no deberán contener DNIs, nombres, direcciones ni números de teléfono reales de personas naturales identificables, en cumplimiento de la Ley N.° 29733.
3. IF la variable de entorno que contiene la clave de la Gemini_API no está definida al iniciar el Sistema, THEN THE Sistema SHALL terminar el proceso con código de salida distinto de cero, registrar un error de configuración en el log y mostrar en la interfaz de usuario un mensaje genérico de servicio no disponible, sin mencionar la ausencia de la clave de API.

---

### Requisito 9: Trazabilidad de Consultas con Asistencia IA

**Historia de usuario:** Como administrador del proyecto, quiero que cada consulta asistida por la Gemini API quede registrada, para garantizar la trazabilidad de las respuestas generadas por IA en el sistema.

#### Criterios de aceptación

1. WHEN el Sistema procesa una consulta asistida por la Gemini_API, THE Sistema SHALL registrar en el log una entrada con identificador único, marca de tiempo en formato ISO 8601, el rol del usuario que realizó la consulta (Recepcionista, Técnico, Encargado_Compras o Gerente), la pregunta recibida, los datos recuperados del Servidor_MCP utilizados como contexto y la respuesta generada.
2. THE Sistema SHALL registrar cada entrada de log de trazabilidad con un identificador único de entrada que permita recuperar la interacción completa.
3. IF la Gemini_API devuelve un error en una consulta asistida, THEN THE Sistema SHALL registrar en el log la pregunta original, el error devuelto por la Gemini_API y la marca de tiempo en formato ISO 8601, e informar al usuario que la asistencia de IA no está disponible en ese momento, sin interrumpir las funcionalidades no dependientes de IA.
