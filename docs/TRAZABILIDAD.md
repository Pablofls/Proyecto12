# Matriz de trazabilidad

## Entrega final — Roberto

| Requisito | Implementación | Prueba/evidencia |
|---|---|---|
| Inspección por categoría | `services/inspecciones/reglas.py` y contrato ampliado | `test_casos_finales.py` |
| Cinco escenarios solicitados | Daño, empaque, frío, evidencia insuficiente y recuperable | 5 pruebas unitarias |
| Disposición solo autorizada | Servicio 8014 + permiso crítico de un uso | `services/disposicion_inventario/tests` |
| Cuarentena obligatoria | Migración 030, trigger y endpoints separados | Estado inicial y reincorporación |
| Costos completos | Recolección, transporte, inspección, almacenamiento, reparación, reacondicionamiento, destrucción y reembolso | `/costos/{id}` |
| Valor recuperado y costo neto | `recuperaciones_valor` y vista de impacto | `/recuperaciones` y `/comparacion-destinos/{id}` |
| Reembolso único concurrente | Redis + restricción única PostgreSQL | prueba real con dos hilos |
| Escritorio PySide6 XML/XSD | `apps/escritorio`, sin acceso directo a datos | `test_cliente_xml.py` |

## Ampliacion del segundo parcial

| Requerimiento | Implementacion distribuida | Evidencia automatizada |
|---|---|---|
| RF-12 a RF-15 | `services/logistica/app.py`: programacion, asignacion, estados y recepcion | `services/logistica/tests/test_api.py` |
| Dominio 20: sincronizacion offline (RF-09, RF-12 a RF-15) | `services/sincronizacion/app.py`: cola de operaciones con `id_operacion` (idempotencia), conflicto por `estado_esperado`, fotos con SHA-256, operaciones criticas solo en linea; tabla `operaciones_offline` (migracion 017) | `services/sincronizacion/tests/test_integracion.py` (reintento y doble envio sin duplicados, conflicto, integridad de la foto) y `test_reglas.py`; guia para las apps en `docs/GUIA_SINCRONIZACION.md` |
| Dominios 21 y 22: integraciones y monitoreo (RF-05, RF-06, RF-32, RNF-22, RNF-23) | `services/integraciones_monitoreo/`: importacion idempotente de ventas del POS, exportacion para ERP/finanzas, eventos de transportista, conciliacion de ids (tabla `integraciones_ids`, migracion 018); monitoreo de servicios, bases y colas con alertas que se resuelven solas y traza por `X-Correlation-ID`. Guia: `docs/GUIA_INTEGRACIONES_MONITOREO.md` | `services/integraciones_monitoreo/tests/test_integracion.py` (ticket repetido y simultaneo sin duplicar, XML, exportacion, alerta abierta y resuelta, traza) y `test_reglas.py` |
| Consistencia monolito / distribuido (correccion del segundo parcial) | Mismas reglas en `apps/web/app/blueprints/devoluciones.py` y `services/devoluciones`; politica en tabla compartida. Ver `docs/MONOLITICO_VS_DISTRIBUIDO.md` | `apps/web/app/tests/test_paridad.py` (8 casos por 3 caminos) y `scripts/prueba_recuperacion.py` (servicios caidos sin duplicados) |
| Seguridad del tercer parcial (RN-13, RNF-08, RNF-09, RNF-11, RNF-16) | Roles de campo, sucursal y operaciones criticas en `shared/seguridad.py` y `services/auth` | `tests/e2e/test_04_seguridad_tercer_parcial.py` (corrida del 2026-11-22, ver `docs/pruebas/REPORTE_FINAL.md`) |
| RF-16, RF-17; RN-05 a RN-07 | `services/inspecciones/app.py`: documento MongoDB, referencia PostgreSQL y calculo de aptitud | `services/inspecciones/tests/test_reglas.py` |
| RF-18, RF-19 | `services/disposicion_inventario/app.py`: decisión autorizada, cuarentena y reincorporación | Swagger y prueba integrada en VM |
| RF-20, RF-21; RN-03, RN-04 | `services/reembolsos_costos/app.py`: reembolso unico con lock Redis | `services/reembolsos_costos/tests/test_api.py` |
| RF-27 | `services/reembolsos_costos/app.py`: costo y desglose por etapa | Swagger y prueba integrada en VM |
| RNF-08, RNF-09 | `shared/seguridad.py` (`requiere_jwt`, `comprobar_en_redis`) usado por los ocho servicios | casos 401 y 403 de cada suite |
| RNF-13 | `shared/infra.py:limitar` (ventana fija en Redis) usado en `services/auth` (login 10/min por IP, refresh 30/min) y `services/devoluciones` (alta 20/min por usuario) | `services/auth/tests/test_auth.py::test_rate_limit_de_login`, `services/devoluciones/tests/test_api.py::test_rate_limit_de_registro` |
| RNF-16, RNF-23 | errores uniformes y `X-Correlation-ID` de `shared/respuestas.py` | pruebas de error JSON/XML |
| RNF-27 | Dockerfile independiente y entradas nuevas de `docker-compose.yml` | `docker compose config` y despliegue VM |
| RF-05, RF-06 | `services/ventas_catalogos`: ventas y siete catalogos con listas blancas | `services/ventas_catalogos/tests/test_reglas.py` |
| RF-09 | `services/evidencias`: comentario JSON/XML y archivos privados con metadatos MongoDB; `apps/web/.../devoluciones.py` `ver_evidencia` reenvia la foto con el JWT de la sesion y el detalle la muestra en linea | `services/evidencias/tests/test_seguridad_archivos.py` |
| RF-22, RF-30; RN-09, RN-11, RN-12 | Tercer parcial, dominio 10: `services/clasificacion_motivos` (8010). Categorias (producto, empaque, transporte, error comercial, mal uso) y submotivos con versiones inmutables (`db/migrations/041_clasificacion_motivos.sql`); la sugerencia por palabras clave queda pendiente hasta que una persona la confirme, corrija o descarte, y nunca modifica la devolucion | `services/clasificacion_motivos/tests/` (reglas, XSD y seguridad en cualquier maquina; `test_integracion.py` en la VM) |
| RF-05, RF-23, RF-24; RN-09, RN-10 | Tercer parcial, dominio 9 (lotes-trazabilidad, dentro de `ventas-catalogos` 8006): numeros de serie por lote (`db/migrations/040_series_trazabilidad.sql`), trazabilidad de lote y de serie hasta tienda, venta y recorrido de cada devolucion, y tasas de devolucion por proveedor, tienda, producto, lote y ruta. Datos de la demo: lote `L-2026-PROB-01` en `scripts/seed_demo.py` | `services/ventas_catalogos/trazabilidad.py`, `reglas.py`; pruebas `tests/test_trazabilidad.py` y `tests/test_integracion_trazabilidad.py` (VM) |
| RF-24, RF-26, RF-27; RN-09, RN-12 | Tercer parcial, dominio 13: `services/proveedores` (8013). Proveedores con lo que surten e indicadores de calidad (tasa de devolucion, inspecciones no aptas, costo, tiempo de respuesta, semaforo con muestra minima); reclamaciones con folio, estados controlados, linea de tiempo inmutable y cierre con resolucion y monto recuperado (`db/migrations/042_reclamaciones_proveedor.sql`) | `services/proveedores/tests/` (reglas, XSD y seguridad en cualquier maquina; `test_integracion.py` en la VM) |
| RF-23, RF-26, RF-30 | `services/analisis_auditoria`: snapshot, Pareto MongoDB, cache Redis y consulta de bitacora | `services/analisis_auditoria/tests/test_pareto.py` |
| RF-23, RF-24, RF-26; RN-09, RN-11, RN-12, RN-13 | Tercer parcial, dominios 11 y 12: `services/causa_raiz` (8011). Flujo de 9 pasos del profe: deteccion de patrones y alertas que proponen investigar, investigacion con evidencia inmutable, hipotesis (cadena de 5 porques e Ishikawa), verificacion, causa confirmada o inconclusa (confirmar exige evidencia y una hipotesis verificada), acciones CAPA con responsable y fecha, medicion de eficacia por cohortes de venta (antes contra despues, sin contar lo que aun puede devolverse) y cierre por un supervisor distinto del analista con reconfirmacion de contrasena (`db/migrations/043_investigaciones_causa_raiz.sql`, `044_acciones_capa.sql`). Guia: `docs/GUIA_CAUSA_RAIZ.md` | `services/causa_raiz/tests/` (reglas, XSD y seguridad en cualquier maquina; `test_integracion.py` recorre los 9 pasos en la VM) |
| RF-30; RN-12, RN-13, RNF-16 | Tercer parcial, dominio 8: la auditoria se separa del analisis en `services/analisis_auditoria`. `auditoria.py` (bitacora y eventos, solo lectura, no importa el analisis) y `retirado.py` (el analisis se retiro: sus rutas responden 410 con los sucesores); la bitacora solo admite agregar (`db/migrations/045_bitacora_solo_agregar.sql`: UPDATE, DELETE y TRUNCATE fallan salvo la anonimizacion por `ON DELETE SET NULL`). Etapas y pendientes: `docs/MIGRACION_ANALISIS_8008.md` | `services/analisis_auditoria/tests/test_separacion.py` (independencia, solo lectura, rutas retiradas y filtros, sin base) y `test_integracion.py` (el trigger real, en la VM) |
| RF-32 | `apps/web/app/microservicios.py` y `/integracion/servicios` consultan los ocho health checks | `apps/web/app/tests/test_microservicios.py` |
| Integracion web/API | `apps/web/app/api_client.py` y blueprints web: JWT/refresh y flujo funcional por HTTP | `apps/web/app/tests/test_api_client.py` y prueba E2E en VM |
| RNF-28; RF-29, RF-31; RN-03, RN-06, RN-11, RN-13 | Suite E2E de 11 pasos mas notificaciones por rol y campanita (paso 6b), seguridad y errores, JSON/XML y 429 (`tests/e2e/`) y `test_integracion.py` en los 8 servicios; casos en `docs/PRUEBAS.md` | `tests/e2e/`, `services/*/tests/test_integracion.py`; resultado de la VM pendiente (`docs/pruebas/`) |
| RF-28, UC-24 | Exportacion CSV (UTF-8 con BOM, streaming, escape de formulas): `apps/web/app/exportacion.py` y `apps/web/app/blueprints/reportes.py` (devoluciones, costos, Pareto de causas, bitacora, reembolsos) | `apps/web/app/tests/test_exportacion.py` y descarga en VM |
| RF-29, UC-25, RN-13 | Campanita y bandeja por rol: `apps/web/app/notificaciones.py` (matriz de destinatarios), `apps/web/app/blueprints/notificaciones.py`, `templates/_campanita.html`, `db/migrations/013_notificaciones_enlace.sql`; `services/devoluciones/app.py` agrega enlace y aviso al Coordinador | `apps/web/app/tests/test_notificaciones.py` y recorrido por rol en VM |

Relaciona los identificadores del documento con el lugar del repositorio donde
quedan implementados. **Actualiza esta tabla en el mismo commit en el que
implementas un requerimiento.**

Estado: `implementado` en el monolito del primer parcial, `parcial` si queda una
parte pendiente, `pendiente` si corresponde a un parcial posterior.

## Requerimientos funcionales

| ID | Requerimiento | Implementacion | Estado |
|---|---|---|---|
| RF-01 | Inicio y cierre de sesion | `apps/web/app/blueprints/auth.py`; API: `services/auth` (`POST /api/v1/auth/login`, `/logout`) | implementado |
| RF-02 | Recuperacion de contrasena | — | pendiente |
| RF-03 | Administrar usuarios | `apps/web/app/blueprints/usuarios.py` | implementado |
| RF-04 | Roles y permisos | `apps/web/app/security.py`, `db/migrations/008_roles_base.sql`; roles de la app Android (Recolector, Operador de Almacen, Supervisor) en `db/migrations/014_roles_operacion_campo.sql` y `shared/seguridad.py`; control por sucursal (`db/migrations/015_sucursal_usuario.sql`, `condicion_tienda`/`exigir_tienda`) y operaciones criticas con reconfirmacion (`POST /api/v1/auth/autorizar-operacion`, `exigir_autorizacion_operacion`); ver `docs/GUIA_SEGURIDAD.md` | implementado |
| RF-05 | Administrar catalogos | `apps/web/app/blueprints/catalogos.py` | implementado |
| RF-06 | Devolucion ligada a venta y producto | `db/migrations/002_venta_detalle.sql`, `apps/web/app/blueprints/devoluciones.py` | implementado |
| RF-07 | Registrar solicitud con motivo | `devoluciones.nueva`; API: `POST /api/v1/devoluciones` (`services/devoluciones`) | implementado |
| RF-08 | Folio unico de devolucion | `db/migrations/007_folio_devolucion.sql` | implementado |
| RF-09 | Evidencias (fotos, documentos, comentarios) | `services/evidencias`: volumen privado, referencia PostgreSQL y metadatos MongoDB | implementado para esta entrega |
| RF-10 | Autorizar, rechazar o pedir informacion | `devoluciones.resolver`; API: `PATCH /api/v1/devoluciones/{id}/resolucion`, correccion con `PUT /api/v1/devoluciones/{id}` | implementado |
| RF-11 | Consulta del estado por el cliente | `devoluciones.detalle`, `panel/cliente.html`; API: `GET /api/v1/devoluciones` y `/{id}` | implementado |
| RF-12 | Programar fecha y lugar de recoleccion | `logistica.programar` | implementado |
| RF-13 | Asignar ruta, transportista y estado | `logistica.actualizar_estado` | implementado |
| RF-14 | Escaneo de codigos QR o de barras | — | pendiente (aplicacion movil) |
| RF-15 | Confirmar recepcion en el centro | `logistica.registrar_recepcion` | implementado |
| RF-16 | Registrar estado fisico, empaque y caducidad | `inspecciones.registrar` | implementado |
| RF-17 | Datos de refrigeracion y cadena de frio | `inspecciones.registrar` | implementado |
| RF-18 | Determinar el destino del producto | `inspecciones.disposicion`, destinos ampliados en `db/migrations/011_destino_donacion.sql` | implementado |
| RF-19 | Etiquetas e inventario recuperable | `inspecciones.inventario`, `inspecciones.etiquetar` | parcial (falta impresion) |
| RF-20 | Aprobar o rechazar el reembolso | `apps/web/app/blueprints/reembolsos.py` | implementado |
| RF-21 | Un solo reembolso valido por devolucion | `UNIQUE devolucion_id` + validacion en `reembolsos.registrar` | implementado |
| RF-22 | Sugerencia automatica del motivo | `POST /api/v1/analisis/clasificar-motivo`; ranking explicable y confirmacion humana | implementado |
| RF-23 | Agrupar devoluciones por caracteristicas y tasas de devolucion | `panel.causas`: agrupacion por motivo/producto/lote/proveedor/tienda/ruta, tasas contra unidades vendidas, lotes y tiendas atipicos | implementado |
| RF-24 | Ranking de causas probables | `panel.causas`: cruce producto-lote-proveedor-ruta-tienda con `% del lote`, rutas relacionadas con dano | implementado (se adelanto al monolito por la retroalimentacion del profesor; ver `docs/BITACORA.md`) |
| RF-25 | Senalar posible fraude | `GET /api/v1/analisis/alertas-fraude`; frecuencia, rechazos y monto con revision humana | implementado |
| RF-26 | Panel de causas, Pareto y KPIs ejecutivos | `panel.causas`: Pareto de motivos, costo por causa via `vista_costo_devolucion`, tendencia mensual y KPIs (devoluciones, tasa, monto reembolsado, costo logistico, tiempo promedio de resolucion via `devoluciones.fecha_cierre` en `db/migrations/012_fecha_cierre_devolucion.sql`, % recuperado) | implementado |
| RF-27 | Consulta de costos y costo total por devolucion | `panel.costos`, captura de costo en `logistica.py`, `inspecciones.py`, `devoluciones.agregar_costo`; `db/migrations/009_ampliar_tipos_costo.sql`, `010_vista_costo_devolucion.sql` | implementado |
| RF-28 | Generar y exportar reportes | `reportes.devoluciones/costos/causas/bitacora/reembolsos` (`/reportes/*.csv`) con el control de rol y los filtros de su pantalla; bitacora `exportar_reporte` | implementado |
| RF-23, RF-24, RF-25, RF-26, RF-28; RN-09, RN-15, RN-16 | Tercer parcial, dominios 18 y 19: `services/reportes_analitica` (8018). Reportes (devoluciones, costos, tasas, Pareto y tendencia) en JSON, XML, CSV, Excel y PDF sin librerias externas; datos para Highcharts; tendencias por regresion con prueba de significancia, pronosticos con intervalo del 95 %, anomalias con puntaje z robusto, analisis de varios factores (`/analitica/factores`: cruce de dos dimensiones con intervalo de Wilson del 95 % y lectura de donde se concentra el exceso), y las alertas de fraude. Las tasas por cohorte de venta usan solo meses que ya cumplieron el plazo de devolucion. Guia: `docs/GUIA_REPORTES_ANALITICA.md` | `services/reportes_analitica/tests/` (estadistica, formatos, endpoints con la base simulada y seguridad en cualquier maquina; `test_integracion.py` contrasta las cifras contra la base en la VM) |
| RF-29 | Notificaciones automaticas | `apps/web/app/notificaciones.py:notificar_evento` en cada paso del flujo; bandeja y campanita en `blueprints/notificaciones.py`; `services/devoluciones` notifica al resolver (con enlace) | implementado |
| RF-30 | Bitacora de operaciones | `apps/web/app/security.py:registrar_bitacora`, `panel.bitacora` | implementado |
| RF-31 | JSON para movil y XML para escritorio | `shared/respuestas.py`, contratos XSD y OpenAPI de los ocho servicios | implementado |
| RF-32 | Monitoreo del estado de los servicios | `/health` en cada contenedor y `/integracion/servicios` en el web | implementado |

## Requerimientos no funcionales

| ID | Requerimiento | Implementacion | Estado |
|---|---|---|---|
| RNF-01 | El sistema web funciona de forma independiente | El monolito no depende de otros componentes | implementado |
| RNF-02 | Cada servicio en su contenedor | ocho Dockerfile y `docker-compose.yml` | implementado |
| RNF-03 | Los clientes no acceden directo a las bases | Postgres, Redis y MongoDB publicados solo en `127.0.0.1` (`docker-compose.yml`) | implementado |
| RNF-04 | Movil consume JSON, escritorio XML | negociacion `Accept`, cuerpos JSON/XML y 22 XSD (21 por servicio y `shared/contratos/error.xsd`) | implementado |
| RNF-05 | Versionamiento y Swagger | `/api/v1`, `/docs` y `openapi.yaml` en los ocho servicios | implementado |
| RNF-06 | Distribucion entre Postgres, Mongo, Redis y almacenamiento | Compose integra las tres bases; inspecciones, evidencias y analisis usan Mongo; evidencias usa volumen privado | implementado |
| RNF-07 | Hash seguro de contrasenas | `werkzeug.security` en `auth.py` y `usuarios.py` | implementado |
| RNF-08 | JWT corto y token de renovacion | `services/auth` emite access/refresh y todos verifican sesion/revocacion Redis | implementado |
| RNF-09 | Verificar rol y permisos antes de cada operacion | `roles_required`, `exigir_devolucion_visible` | implementado |
| RNF-10 | Validar los datos antes de almacenarlos | Validacion en navegador y servidor en cada blueprint | implementado |
| RNF-11 | Proteccion contra inyeccion SQL y XXE | Parametros ligados en `apps/web/app/db.py` y `shared/infra.py`; listas blancas en `catalogos.py` y `services/ventas_catalogos`; parser `lxml` sin entidades ni red en `shared/xsd.py`; XXE probado en la VM por E2E FMT-07 (400 `xml_invalido`, entidad no resuelta) | implementado |
| RNF-12 | Registro de intentos fallidos y bloqueo | `apps/web/app/cache.py`, `db/migrations/004_control_accesos.sql` | implementado |
| RNF-13 | Limitacion de peticiones | `shared/infra.py:limitar` aplica reglas de negocio; Nginx agrega límite general y uno específico para login | implementado |
| RNF-14 | Cifrado y secretos fuera del codigo | `.env` fuera de git; `docker-compose.tls.yml` termina TLS 1.2/1.3 en Nginx con certificados externos al repositorio | implementado al desplegar la variante TLS |
| RNF-15 | Enlaces firmados para evidencias privadas | `services/evidencias`: enlace HMAC-SHA256 de 15 min (`GET /{id}/enlace`) sobre archivos en volumen privado; el bucket es logico, sin GCS todavia | parcial (falta GCS) |
| RNF-16 | Ocultar informacion sensible | Mensaje de login generico; bitacora sin datos sensibles | implementado |
| RNF-17 | Separacion por organizacion | No aplica en el alcance actual | pendiente |
| RNF-18 | Respuesta maxima de tres segundos | Indices en todas las llaves foraneas | implementado |
| RNF-19 | Consistencia con usuarios concurrentes | Transaccion por peticion; folio por secuencia | implementado |
| RNF-20 | Escalar agregando instancias | — | pendiente |
| RNF-21 | Una falla parcial no tumba todo | `/health` degradado; bloqueo persistido en Postgres | parcial |
| RNF-22 | Health checks | `/health` responde 200 en los nueve endpoints (VM, `docs/evidencias/bases/docker.txt`); `healthcheck` de Compose en ocho contenedores, faltan `app`, `logistica`, `inspecciones` y `reembolsos-costos` | parcial |
| RNF-23 | Identificador de correlacion | `apps/web/app/security.py:correlation_id`; `shared/respuestas.py` (header `X-Correlation-ID`, bitacora y coleccion `eventos`) | implementado |
| RNF-24 | Respaldo y recuperacion | — | pendiente |
| RNF-25 | Mensajes claros al usuario | Mensajes flash en todas las operaciones | implementado |
| RNF-26 | Adaptarse a distintos tamanos de pantalla | `apps/web/app/static/css/estilos.css` | implementado |
| RNF-27 | Docker y Google Compute Engine | `docker-compose.yml`, VM del equipo | implementado |
| RNF-28 | Pruebas | 119 unitarias y de API con dobles en `services/*/tests` y `apps/web/app/tests`; suite E2E `tests/e2e/` y `test_integracion.py` en los ocho servicios (`INTEGRACION=1`, solo en la VM); casos en `docs/PRUEBAS.md`. VM (21 de octubre): E2E 100 passed y integracion 8 de 8 (`docs/pruebas/salida_2026-10-21.txt`); 119 unitarias passed en local. Faltan caidas de dependencias, concurrencia real, 413 y carga | parcial |
| RNF-29 | Locust con distintos perfiles | `tests/carga/locustfile.py` (5 perfiles), `scripts/correr_carga.sh` (3 escenarios), resultados en `docs/pruebas/CARGA.md` | implementado |
| RNF-30 | Retencion y eliminacion logica | `db/migrations/005_eliminacion_logica.sql`; `DELETE /api/v1/devoluciones/{id}` marca `eliminado_en` | implementado |

## Reglas de negocio

| ID | Regla | Donde se hace cumplir |
|---|---|---|
| RN-01 | Toda devolucion vinculada a una venta y un producto | `devoluciones.venta_detalle_id NOT NULL`; el formulario solo se abre desde la linea de venta; la API bloquea la linea y responde 409 `cantidad_excedida` |
| RN-02 | Folio unico e irrepetible | `seq_folio_devolucion` + `UNIQUE` (migracion 007) |
| RN-03 | Un solo reembolso valido por devolucion | `UNIQUE (devolucion_id)` en `reembolsos` |
| RN-04 | El reembolso requiere devolucion autorizada | `fn_validar_reembolso` (migracion 006) + `reembolsos.registrar` |
| RN-05 | Clasificacion determina los datos obligatorios | `inspecciones.registrar` exige temperatura y tiempo si es refrigerado |
| RN-06 | Refrigerado fuera de tiempo no vuelve a inventario | `evaluar_aptitud` + `fn_validar_destino_inventario` |
| RN-07 | Danos, caducidad o cadena rota impiden inventario | `evaluar_aptitud` + `trg_validar_destino_inventario` (migracion 001) y `trg_validar_inspeccion_vs_disposicion` (migracion 006) |
| RN-08 | Recoleccion completada requiere datos completos | `logistica.actualizar_estado` |
| RN-09 | El analisis es apoyo, no determinacion automatica | El panel de causas solo agrupa; no asigna responsabilidad |
| RN-10 | Agrupacion por atributos definidos por el negocio | `panel.causas` agrupa y filtra por motivo, producto, lote, proveedor, tienda, ruta y estado |
| RN-11 | La clasificacion automatica es sugerencia | `clasificar-motivo` devuelve `requiere_confirmacion=true`; no modifica la devolucion |
| RN-12 | Toda decision queda registrada con usuario y fecha | `registrar_bitacora` en cada operacion |
| RN-13 | Cada usuario solo ejecuta lo de su rol | `roles_required` en todas las vistas; en los servicios, `requiere_jwt()` sin roles solo acepta los 7 roles base, la sucursal limita los registros y las operaciones criticas exigen reconfirmar la contrasena |
| RN-14 | Evidencias privadas por enlaces temporales | Parcial: enlaces temporales HMAC de 15 min en `services/evidencias`; falta almacenar en GCS |
| RN-15 | No exponer informacion sensible sin autorizacion | Bitacora y errores sin datos sensibles |
| RN-16 | Plazo de devolucion: 30 dias no refrigerado, 7 refrigerado, desde la venta; una sola solicitud abierta por linea y motivo | Tabla `politicas_devolucion` (migracion 016); `services/devoluciones/app.py` (`_exigir_plazo`, `_exigir_no_duplicada`, `GET /api/v1/devoluciones/elegibilidad`) y la misma regla en `apps/web/app/blueprints/devoluciones.py` (modo monolitico) |

## Casos de uso cubiertos

Implementados: UC-01, UC-03, UC-04, UC-05, UC-06, UC-07, UC-08, UC-09, UC-10,
UC-11, UC-13, UC-14, UC-15, UC-16, UC-17, UC-22, UC-23, UC-24, UC-25, UC-26.
Desde el segundo parcial tambien UC-18 a UC-21 (RF-22 a RF-25:
`services/analisis_auditoria` y `panel.causas`) y UC-27 (RF-32:
`/integracion/servicios`).

Pendientes: UC-02 (recuperar contrasena) y UC-12 (escaneo).

## Evidencias request/response (sesion de Postman)

| Identificadores | Que cubre | Archivos |
|---|---|---|
| RF-31, RNF-05 | Coleccion Postman por servicio (exito en JSON y XML, 400, 401, 403, 404 y 409) y environment de la VM | `docs/postman/*.postman_collection.json`, `docs/postman/vm.postman_environment.json`, generados por `docs/postman/generar_colecciones.py` desde `docs/postman/especificaciones.py` |
| RNF-05, RNF-22, RNF-23 | Plantilla del apartado 5 por endpoint de `openapi.yaml`, con marcadores de captura pendiente | `docs/EVIDENCIAS.md` |
| RNF-06, RNF-08, RNF-12, RNF-13, RN-12 | Guia de captura en la VM: `psql`, `mongosh`, `redis-cli`, Docker y volumen privado | `docs/evidencias/README.md`, `docs/evidencias/CHECKLIST_CAPTURAS.md` |
| RF-31, RNF-05, RNF-11, RNF-13, RNF-28; RN-03 | Ejecucion real en la VM (22 de octubre): 238 casos de Newman con peticion y respuesta (JSON, XML, 400, 401, 403, 404, 409, 415), 767 verificaciones sin fallos; XXE, 429 y lock 409 | `docs/evidencias/ejecuciones/*.md`, `docs/pruebas/salida_2026-10-21.txt`, `docs/evidencias/bases/redis.txt` |
| RNF-06, RNF-22, RNF-27 | Efecto en PostgreSQL, MongoDB (incluye `getIndexes()`), Redis, Docker (12 contenedores, nueve `/health` en 200) y volumen privado | `docs/evidencias/bases/*.txt` |
| RF-31, RNF-05, RNF-06, RNF-28 | Documento tecnico con la evidencia real resumida y enlazada (apartados 10, 13, 15, 16 y 17) y la tabla de evidencia pendiente (apartado 19.3) | `docs/DOCUMENTO_TECNICO.md` |
