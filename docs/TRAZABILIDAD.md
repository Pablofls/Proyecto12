# Matriz de trazabilidad

Relaciona los identificadores del documento con el lugar del repositorio donde
quedan implementados. **Actualiza esta tabla en el mismo commit en el que
implementas un requerimiento.**

Estado: `implementado` en el monolito del primer parcial, `parcial` si queda una
parte pendiente, `pendiente` si corresponde a un parcial posterior.

## Requerimientos funcionales

| ID | Requerimiento | Implementacion | Estado |
|---|---|---|---|
| RF-01 | Inicio y cierre de sesion | `app/blueprints/auth.py` | implementado |
| RF-02 | Recuperacion de contrasena | — | pendiente |
| RF-03 | Administrar usuarios | `app/blueprints/usuarios.py` | implementado |
| RF-04 | Roles y permisos | `app/security.py`, `db/migrations/008_roles_base.sql` | implementado |
| RF-05 | Administrar catalogos | `app/blueprints/catalogos.py` | implementado |
| RF-06 | Devolucion ligada a venta y producto | `db/migrations/002_venta_detalle.sql`, `app/blueprints/devoluciones.py` | implementado |
| RF-07 | Registrar solicitud con motivo | `devoluciones.nueva` | implementado |
| RF-08 | Folio unico de devolucion | `db/migrations/007_folio_devolucion.sql` | implementado |
| RF-09 | Evidencias (fotos, documentos, comentarios) | `db/migrations/003_evidencias.sql`, `devoluciones.agregar_evidencia` | parcial (falta la carga a GCS) |
| RF-10 | Autorizar, rechazar o pedir informacion | `devoluciones.resolver` | implementado |
| RF-11 | Consulta del estado por el cliente | `devoluciones.detalle`, `panel/cliente.html` | implementado |
| RF-12 | Programar fecha y lugar de recoleccion | `logistica.programar` | implementado |
| RF-13 | Asignar ruta, transportista y estado | `logistica.actualizar_estado` | implementado |
| RF-14 | Escaneo de codigos QR o de barras | — | pendiente (aplicacion movil) |
| RF-15 | Confirmar recepcion en el centro | `logistica.registrar_recepcion` | implementado |
| RF-16 | Registrar estado fisico, empaque y caducidad | `inspecciones.registrar` | implementado |
| RF-17 | Datos de refrigeracion y cadena de frio | `inspecciones.registrar` | implementado |
| RF-18 | Determinar el destino del producto | `inspecciones.disposicion` | implementado |
| RF-19 | Etiquetas e inventario recuperable | `inspecciones.inventario`, `inspecciones.etiquetar` | parcial (falta impresion) |
| RF-20 | Aprobar o rechazar el reembolso | `app/blueprints/reembolsos.py` | implementado |
| RF-21 | Un solo reembolso valido por devolucion | `UNIQUE devolucion_id` + validacion en `reembolsos.registrar` | implementado |
| RF-22 | Sugerencia automatica del motivo | — | pendiente (microservicio de clasificacion) |
| RF-23 | Agrupar devoluciones por caracteristicas | `panel.causas` (agrupacion basica) | parcial |
| RF-24 | Ranking de causas probables | — | pendiente (microservicio de causa raiz) |
| RF-25 | Senalar posible fraude | `db/migrations/006_validaciones_reembolso.sql` (monto excesivo) | parcial |
| RF-26 | Panel de causas y Pareto | `panel.causas` | parcial (falta Pareto) |
| RF-27 | Consulta de costos | `panel.costos` | implementado |
| RF-28 | Generar y exportar reportes | — | pendiente |
| RF-29 | Notificaciones automaticas | tabla `notificaciones` creada, sin uso | pendiente |
| RF-30 | Bitacora de operaciones | `app/security.py:registrar_bitacora`, `panel.bitacora` | implementado |
| RF-31 | JSON para movil y XML para escritorio | — | pendiente (microservicios) |
| RF-32 | Monitoreo del estado de los servicios | `/health` | parcial |

## Requerimientos no funcionales

| ID | Requerimiento | Implementacion | Estado |
|---|---|---|---|
| RNF-01 | El sistema web funciona de forma independiente | El monolito no depende de otros componentes | implementado |
| RNF-02 | Cada servicio en su contenedor | `docker-compose.yml` | parcial |
| RNF-03 | Los clientes no acceden directo a las bases | Postgres y Redis publicados solo en `127.0.0.1` | implementado |
| RNF-04 | Movil consume JSON, escritorio XML | — | pendiente |
| RNF-05 | Versionamiento y Swagger | — | pendiente |
| RNF-06 | Distribucion entre Postgres, Mongo, Redis y bucket | Postgres y Redis en uso; Mongo y GCS declarados | parcial |
| RNF-07 | Hash seguro de contrasenas | `werkzeug.security` en `auth.py` y `usuarios.py` | implementado |
| RNF-08 | JWT corto y token de renovacion | Sesion en Redis; JWT queda para el segundo parcial | parcial |
| RNF-09 | Verificar rol y permisos antes de cada operacion | `roles_required`, `exigir_devolucion_visible` | implementado |
| RNF-10 | Validar los datos antes de almacenarlos | Validacion en navegador y servidor en cada blueprint | implementado |
| RNF-11 | Proteccion contra inyeccion SQL y XXE | Parametros ligados en `app/db.py`; lista blanca en `catalogos.py` | implementado (XXE no aplica aun) |
| RNF-12 | Registro de intentos fallidos y bloqueo | `app/cache.py`, `db/migrations/004_control_accesos.sql` | implementado |
| RNF-13 | Limitacion de peticiones | — | pendiente |
| RNF-14 | Cifrado y secretos fuera del codigo | `.env` fuera de git, `app/config.py` | parcial (falta HTTPS) |
| RNF-15 | Enlaces firmados para evidencias privadas | Estructura lista en `evidencias`; sin GCS todavia | pendiente |
| RNF-16 | Ocultar informacion sensible | Mensaje de login generico; bitacora sin datos sensibles | implementado |
| RNF-17 | Separacion por organizacion | No aplica en el alcance actual | pendiente |
| RNF-18 | Respuesta maxima de tres segundos | Indices en todas las llaves foraneas | implementado |
| RNF-19 | Consistencia con usuarios concurrentes | Transaccion por peticion; folio por secuencia | implementado |
| RNF-20 | Escalar agregando instancias | — | pendiente |
| RNF-21 | Una falla parcial no tumba todo | `/health` degradado; bloqueo persistido en Postgres | parcial |
| RNF-22 | Health checks | `/health` y `healthcheck` en el compose | implementado |
| RNF-23 | Identificador de correlacion | `app/security.py:correlation_id` | implementado |
| RNF-24 | Respaldo y recuperacion | — | pendiente |
| RNF-25 | Mensajes claros al usuario | Mensajes flash en todas las operaciones | implementado |
| RNF-26 | Adaptarse a distintos tamanos de pantalla | `app/static/css/estilos.css` | implementado |
| RNF-27 | Docker y Google Compute Engine | `docker-compose.yml`, VM del equipo | implementado |
| RNF-28 | Pruebas | — | pendiente |
| RNF-29 | Locust con distintos perfiles | — | pendiente |
| RNF-30 | Retencion y eliminacion logica | `db/migrations/005_eliminacion_logica.sql` | implementado |

## Reglas de negocio

| ID | Regla | Donde se hace cumplir |
|---|---|---|
| RN-01 | Toda devolucion vinculada a una venta y un producto | `devoluciones.venta_detalle_id NOT NULL`; el formulario solo se abre desde la linea de venta |
| RN-02 | Folio unico e irrepetible | `seq_folio_devolucion` + `UNIQUE` (migracion 007) |
| RN-03 | Un solo reembolso valido por devolucion | `UNIQUE (devolucion_id)` en `reembolsos` |
| RN-04 | El reembolso requiere devolucion autorizada | `fn_validar_reembolso` (migracion 006) + `reembolsos.registrar` |
| RN-05 | Clasificacion determina los datos obligatorios | `inspecciones.registrar` exige temperatura y tiempo si es refrigerado |
| RN-06 | Refrigerado fuera de tiempo no vuelve a inventario | `evaluar_aptitud` + `fn_validar_destino_inventario` |
| RN-07 | Danos, caducidad o cadena rota impiden inventario | `evaluar_aptitud` + los dos triggers de la migracion 006 |
| RN-08 | Recoleccion completada requiere datos completos | `logistica.actualizar_estado` |
| RN-09 | El analisis es apoyo, no determinacion automatica | El panel de causas solo agrupa; no asigna responsabilidad |
| RN-10 | Agrupacion por atributos definidos por el negocio | `panel.causas` agrupa por motivo, producto, lote y proveedor |
| RN-11 | La clasificacion automatica es sugerencia | Sin clasificacion automatica todavia; el motivo lo elige el usuario |
| RN-12 | Toda decision queda registrada con usuario y fecha | `registrar_bitacora` en cada operacion |
| RN-13 | Cada usuario solo ejecuta lo de su rol | `roles_required` en todas las vistas |
| RN-14 | Evidencias privadas por enlaces temporales | Pendiente: requiere GCS |
| RN-15 | No exponer informacion sensible sin autorizacion | Bitacora y errores sin datos sensibles |

## Casos de uso cubiertos por el monolito

Implementados: UC-01, UC-03, UC-04, UC-05, UC-06, UC-07, UC-08, UC-09, UC-10,
UC-11, UC-13, UC-14, UC-15, UC-16, UC-17, UC-22 (basico), UC-23, UC-26.

Pendientes: UC-02 (recuperar contrasena), UC-12 (escaneo), UC-18 a UC-21
(algoritmos), UC-24 (exportar reportes), UC-25 (notificaciones), UC-27
(monitoreo de microservicios).
