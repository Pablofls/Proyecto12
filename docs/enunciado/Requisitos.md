Requisitos de seguridad obligatorios: Todos los proyectos deberán incorporar:
Contraseñas con hash seguro.
JWT de acceso de corta duración.
Token de renovación.
Revocación mediante Redis.
Control de acceso basado en roles.
Autorización por recurso.
Separación de tenants cuando corresponda.
Protección contra inyección SQL.
Validación de JSON y XML.
Protección contra XML External Entity.
Limitación de peticiones.
Registro de intentos fallidos.
Bloqueo temporal.
Cifrado de comunicaciones.
Secretos fuera del código.
URLs firmadas para objetos privados.
Bitácoras de auditoría.
Ocultamiento de datos sensibles.
Políticas de retención.
Eliminación lógica cuando corresponda.

Pruebas obligatorias: Cada equipo deberá entregar evidencia de:
Pruebas unitarias.
Pruebas de integración.
Pruebas de contratos JSON.
Pruebas de esquemas XML.
Pruebas de autenticación.
Pruebas de autorización.
Pruebas de expiración de tokens.
Pruebas de revocación.
Pruebas de recuperación ante fallos.
Pruebas de caída de PostgreSQL.
Pruebas de caída de MongoDB.
Pruebas de caída de Redis.
Pruebas de microservicios no disponibles.
Pruebas de carga con Locust.
Pruebas de concurrencia.
Pruebas de archivos grandes.
Pruebas de grandes volúmenes de datos.
Pruebas básicas de seguridad.
La prueba de Locust deberá simular diferentes perfiles y no solamente peticiones repetidas a un único endpoint.
Documentación requerida: Cada proyecto deberá entregar:
Documento de visión.
Descripción del problema.
Requerimientos funcionales.
Requerimientos no funcionales.
Historias de usuario.
Casos de uso.
Diagrama de contexto.
Diagrama de componentes.
Diagrama de despliegue.
Diagrama de secuencia.
Modelo relacional.
Diseño de colecciones MongoDB.
Diseño de claves Redis.
Catálogo de microservicios.
Contratos JSON.
Esquemas XML.
Documentación Swagger.
Matriz de roles y permisos.
Estrategia de seguridad.
Plan de pruebas.
Resultados de Locust.
Manual de despliegue.
Manual de usuario.
Manual técnico.
Registro de riesgos.
Evidencia de operación en GCP.

Criterio central de integración: No se considerará completo un proyecto compuesto únicamente por cuatro aplicaciones separadas. El equipo deberá demostrar que:
El sistema web funciona de manera independiente.
La aplicación móvil consume exclusivamente JSON.
La aplicación de escritorio consume exclusivamente XML.
Los microservicios son independientes y desplegables por separado.
JWT y Redis se utilizan en todas las peticiones protegidas.
Los datos están distribuidos justificadamente entre PostgreSQL, MongoDB y Redis.
Los archivos se almacenan en buckets.
Los servicios cuentan con health checks.
Swagger documenta las APIs.
Locust demuestra el comportamiento bajo carga.
Los algoritmos resuelven un problema real.
La plataforma funciona en Google Cloud Platform.
La arquitectura puede crecer sin reconstruir completamente el sistema.
Una falla parcial no provoca necesariamente la caída total de la solución.
