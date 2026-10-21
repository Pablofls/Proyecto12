# Integracion funcional web -> microservicios

Rama: `roberto/integracion-web-microservicios`.

Esta version conserva las pantallas del primer parcial, pero las operaciones
criticas ya no escriben directamente en PostgreSQL. `app/api_client.py` envia
HTTP JSON a las API `/api/v1`, propaga `X-Correlation-ID` y adjunta el JWT del
usuario.

Los access y refresh tokens se almacenan exclusivamente en la sesion Flask del
servidor respaldada por Redis. Si el access token vence, el cliente llama una
vez a `/api/v1/auth/refresh` y repite la operacion. Si la renovacion falla,
elimina la sesion local.

## Operaciones conectadas

| Pantalla/accion web | Microservicio y endpoint |
|---|---|
| Login | `POST auth /api/v1/auth/login` |
| Logout | `POST auth /api/v1/auth/logout` |
| Listar/detallar ventas | `GET ventas-catalogos /api/v1/ventas[...]` |
| Listar/registrar devolucion | `GET/POST devoluciones /api/v1/devoluciones` |
| Resolver devolucion | `PATCH devoluciones /api/v1/devoluciones/{id}/resolucion` |
| Agregar comentario | `POST evidencias /api/v1/evidencias` |
| Programar/asignar/avanzar recoleccion | `logistica /api/v1/logistica/recolecciones[...]` |
| Confirmar recepcion | `POST logistica /api/v1/logistica/recepciones` |
| Registrar inspeccion | `POST inspecciones /api/v1/inspecciones` |
| Decidir disposicion | `POST inspecciones /api/v1/inspecciones/{id}/disposicion` |
| Generar etiqueta | `POST inspecciones /api/v1/inspecciones/inventario/{id}/etiqueta` |
| Registrar costos | `POST reembolsos-costos /api/v1/reembolsos-costos/costos` |
| Resolver reembolso | `POST reembolsos-costos /api/v1/reembolsos-costos/reembolsos` |
| Consultar resumen y Pareto | `GET analisis-auditoria /api/v1/analisis/resumen` y `/pareto` |
| Sincronizar datos para causas | `POST analisis-auditoria /api/v1/analisis/sincronizar` |

Las consultas compuestas del expediente y los paneles conservan lectura
relacional directa por ahora: agregan informacion de varios dominios para una
sola plantilla. Las mutaciones del proceso distribuido pasan por el servicio
responsable y quedan identificadas como `(API)` en la bitacora.

## Modo de contingencia

`USE_MICROSERVICES=true` activa la arquitectura distribuida y muestra la
insignia **API distribuida**. Para una contingencia controlada se puede arrancar
el mismo artefacto con `USE_MICROSERVICES=false`; las rutas conservan la logica
original del monolito. La rama estable `roberto/tres-microservicios` permanece
sin cambios como respaldo adicional.

No existe fallback silencioso: si una API falla en modo distribuido, la web
muestra el error y no repite la escritura directamente en la base, evitando
duplicados y ocultamiento de fallas durante la demostracion.

## Verificacion E2E en la VM

El 21 de octubre de 2026 se ejecuto desde formularios web el caso
`DEV-2026-0033`:

1. login de cliente por `auth`;
2. alta y autorizacion por `devoluciones`;
3. programacion, asignacion, transito, entrega y recepcion por `logistica`;
4. inspeccion refrigerada por `inspecciones`, con `mongo_doc_id` real;
5. disposicion a inventario y etiqueta `REC-2026-0033`;
6. reembolso de 32.24 por `reembolsos-costos`;
7. cierre automatico de la devolucion y liberacion del lock Redis (`TTL=-2`);
8. sincronizacion del panel de causas hacia MongoDB y consulta Pareto con cache
   Redis mediante `analisis-auditoria`.

Todos los formularios respondieron con redireccion HTTP 302, cada API registro
su request 200/201 con usuario y correlation id, y PostgreSQL termino con la
devolucion en estado `cerrada`.
