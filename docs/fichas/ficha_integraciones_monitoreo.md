# Ficha técnica: Servicio de integraciones y monitoreo (integraciones-monitoreo)

## 1. Identificación

| Campo | Valor |
|---|---|
| Nombre | `integraciones-monitoreo`: servicio de integración con sistemas externos y monitoreo de la plataforma |
| Propósito | Conectar la plataforma con el POS, el ERP, los transportistas y los sistemas financieros, y vigilar que todos los servicios y bases estén funcionando |
| Responsabilidad | **Integraciones:** importar ventas del POS sin duplicarlas, exportar devoluciones para el ERP y finanzas, recibir eventos de transportistas y conciliar identificadores externos e internos. **Monitoreo:** revisar cada minuto la salud y el tiempo de respuesta de los servicios, las bases y la cola de sincronización, abrir y cerrar alertas operativas y reconstruir la traza de una operación |
| Puerto | 8021 |
| Rutas base | `/api/v1/integraciones` y `/api/v1/monitoreo` |

## 2. Justificación

La retroalimentación agrega dos dominios: el 21 (integraciones con POS, ERP, WMS, transportistas y sistemas financieros; contratos JSON/XML con XSD, importación, exportación y conciliación de identificadores) y el 22 (salud de servicios, disponibilidad de bases, colas, tiempos de respuesta, errores, trazabilidad distribuida y alertas). La propuesta de puertos (`docs/PUERTOS.md`) los agrupa en un contenedor porque:

- Los dos miran a la plataforma **desde afuera**: ninguno es dueño de datos del negocio (devoluciones, inspecciones, reembolsos).
- Comparten la necesidad de conocer a todos los servicios y sus identificadores.
- Reducen el número de contenedores en una VM e2-standard-2.

**Requerimientos cubiertos:** dominios 21 y 22 del tercer parcial, RF-05 (catálogos), RF-06 (ventas), RF-13 (estado de la recolección), RF-27 (costos), RF-30 (bitácora), RF-32 (salud del sistema), RN-12 (toda decisión queda registrada), RNF-11 (SQL parametrizado), RNF-22 (disponibilidad), RNF-23 (trazabilidad por correlation id), RNF-28 (pruebas).

## 3. Diseño (Arquitectura interna)

| Capa | Archivo | Responsabilidad |
|---|---|---|
| Entrada y salida | `shared/respuestas.py`, `shared/xsd.py` | JSON o XML según Accept; XSD de la venta del POS, la conciliación y el evento del transportista |
| Seguridad | `shared/seguridad.py` | `@requiere_jwt(roles)` |
| Reglas | `services/integraciones_monitoreo/reglas.py` | Funciones puras: validación de la venta del POS, estado de un servicio, qué alertas dispara un chequeo, disponibilidad y percentil 95 |
| Monitoreo | `services/integraciones_monitoreo/monitor.py` | Chequeo en paralelo de servicios, bases y colas; alertas; hilo de cada minuto |
| Endpoints | `services/integraciones_monitoreo/app.py` | Integraciones y consultas de monitoreo |
| Datos | `shared/infra.py`, `shared/mongo.py`, `shared/paginacion.py` | PostgreSQL, Redis, MongoDB, bitácora y paginación |

**Decisiones de diseño:**

- **Tabla traductora de identificadores:** `integraciones_ids` guarda que "la tienda T-001 del POS es nuestra tienda 3". Su llave (sistema, tipo, id externo) hace idempotente la importación.
- **Nunca adivinar:** un id externo sin equivalencia responde `422 sin_conciliar` y dice exactamente qué falta, en vez de crear datos a ciegas.
- **Candado para envíos simultáneos:** `pg_advisory_xact_lock` sobre el ticket del POS; si dos envíos llegan juntos, el segundo espera y encuentra la venta ya creada.
- **Transportista idempotente por estado:** si la recolección ya está en el estado reportado, responde `cambio: false`.
- **Chequeo en paralelo:** los diez servicios se revisan al mismo tiempo (ThreadPoolExecutor), con 3 s de límite cada uno; un servicio caído no frena a los demás.
- **Un solo vigilante:** gunicorn arranca 2 workers; un candado en Redis (`devoluciones:monitoreo:turno`) hace que solo uno revise en cada minuto.
- **Alertas que se cierran solas:** una sola alerta activa por problema (cuenta las veces); cuando el recurso vuelve a estar bien, pasa a `resuelta`.
- **Monitoreo sin contexto de petición:** `monitor.py` no usa Flask; lo llaman tanto el endpoint como el hilo de fondo.

**Reglas de alerta:**

| Alerta | Severidad | Cuándo |
|---|---|---|
| servicio_caido | alta | El servicio no responde a `/health` |
| servicio_degradado | media | Responde, pero alguna de sus bases falla |
| respuesta_lenta | media | Tarda más de 1500 ms |
| base_no_disponible | alta | PostgreSQL, Redis o MongoDB no responden |
| conflictos_sincronizacion | media | Más de 10 conflictos de sincronización en 24 h |

## 4. Tecnología

| Componente | Tecnología | Versión | Uso en el servicio |
|---|---|---|---|
| Lenguaje | Python | 3.11 | Mismo lenguaje que el sistema web |
| Framework web | Flask | 3.0.3 | Rutas REST de los dos dominios |
| Servidor | Gunicorn | 22.0.0 | 2 workers |
| Acceso a PostgreSQL | psycopg2-binary | 2.9.10 | SQL parametrizado y candados de aplicación |
| Acceso a MongoDB | pymongo | 4.8.0 | Chequeos, alertas y eventos; índice TTL |
| Acceso a Redis | redis-py | 5.0.8 | Sesión JWT y candado del vigilante |
| Tokens | PyJWT | 2.9.0 | Validación de los JWT emitidos por auth |
| Validación XML | lxml | 5.3.0 | Tres contratos XSD |
| Contrato OpenAPI | PyYAML | 6.0.2 | Swagger UI en `/docs` |
| Pruebas | pytest | 8.3.3 | Unitarias e integración |

- Biblioteca estándar: `urllib` (llamadas a `/health`), `concurrent.futures` (chequeo en paralelo), `threading` (vigilante de cada minuto).

## 5. Endpoints

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | `/api/v1/integraciones/ventas` | Administrador | Importa una venta del POS (idempotente por ticket) |
| POST | `/api/v1/integraciones/conciliaciones` | Administrador | Registra que un id externo equivale a un registro interno |
| GET | `/api/v1/integraciones/conciliaciones` | Administrador | Lista paginada; filtros `sistema` y `tipo_entidad` |
| GET | `/api/v1/integraciones/conciliaciones/{sistema}/{tipo}/{id_externo}` | Administrador, Encargado de Reembolsos, Analista | Traduce un id externo al interno |
| GET | `/api/v1/integraciones/exportaciones/devoluciones` | Administrador, Encargado de Reembolsos, Analista | Devoluciones con reembolso y costo para ERP y finanzas |
| POST | `/api/v1/integraciones/transportistas/eventos` | Administrador, Coordinador | Avance de la recolección reportado con la guía del transportista |
| GET | `/api/v1/monitoreo/estado` | Administrador, Supervisor | Chequeo completo en este momento |
| GET | `/api/v1/monitoreo/disponibilidad` | Administrador, Supervisor | Disponibilidad, promedio, p95 y fallas por servicio |
| GET | `/api/v1/monitoreo/alertas` | Administrador, Supervisor | Alertas activas o resueltas |
| GET | `/api/v1/monitoreo/traza/{correlation_id}` | Administrador, Supervisor | Pasos de una operación en todos los servicios |
| GET | `/health`, `/docs`, `/contratos/{nombre}` | — | Salud, Swagger UI y contratos XSD |

**Criterio de métodos HTTP:** POST para lo que crea o cambia (venta, conciliación, evento); GET para consultas y exportaciones. No hay PUT ni DELETE: una conciliación equivocada se corrige con el administrador de la base para no romper exportaciones ya enviadas.

## 6. Entrada

**Cuerpo de POST /integraciones/ventas** (contrato `venta_pos.xsd`):

| Campo | Tipo | Obligatorio | Validación |
|---|---|---|---|
| `id_externo` | texto | Sí | Ticket del POS: 1 a 64 letras, números o `_ . : / -` |
| `tienda_externa` | texto | Sí | Código de tienda del POS; debe estar conciliado |
| `cliente_email` | texto | Sí | Cliente activo existente |
| `fecha_venta` | fecha | Sí | AAAA-MM-DD, no en el futuro |
| `lineas` | lista | Sí | 1 a 100 líneas con `sku`, `numero_lote`, `cantidad` (≥ 1) y `precio_unitario` (≥ 0) |

```
{ "id_externo": "TK-88123", "tienda_externa": "T-001", "cliente_email": "cliente@demo.mx",
  "fecha_venta": "2026-11-20",
  "lineas": [ { "sku": "LEC-001", "numero_lote": "L-2026-11", "cantidad": 2, "precio_unitario": 32.50 } ] }
```

**Cuerpo de POST /integraciones/conciliaciones** (`conciliacion.xsd`): `sistema` (pos, erp, wms, transportista, financiero), `tipo_entidad` (tienda, venta, producto, devolucion, recoleccion), `id_externo` e `id_interno`.

**Cuerpo de POST /integraciones/transportistas/eventos** (`evento_transportista.xsd`): `guia`, `estado` (en_transito, completada, fallida) y `fecha` opcional.

**Parámetros:**

| Endpoint | Parámetros |
|---|---|
| exportaciones/devoluciones | `desde`, `hasta` (AAAA-MM-DD, máximo 366 días; por defecto los últimos 30), `pagina`, `por_pagina` |
| monitoreo/disponibilidad | `horas` (1 a 168; por defecto 24) |
| monitoreo/alertas | `estado` (activa o resuelta), `pagina`, `por_pagina` |
| monitoreo/traza | `correlation_id` en la ruta (letras, números, `_` y `-`) |

## 7. Salida

**POST /integraciones/ventas:** 201 la primera vez; 200 con `repetida: true` si el ticket ya se había importado.

```
{ "venta_id": 512, "folio_venta": "POS-TK-88123", "id_externo": "TK-88123",
  "lineas": 1, "repetida": false }
```

**GET /monitoreo/estado (extracto):**

```
{ "fecha": "2026-11-20T18:44:59Z",
  "servicios": [ { "servicio": "auth", "estado": "ok", "codigo": 200, "ms": 122,
                   "dependencias": { "postgresql": true, "redis": true } }, ... ],
  "bases": { "postgresql": { "ok": true, "ms": 8 }, "redis": { "ok": true, "ms": 2 },
             "mongodb": { "ok": true, "ms": 5 } },
  "colas": { "operaciones_offline": { "aceptada_24h": 14, "conflicto_24h": 1,
                                      "rechazada_24h": 2, "reintentos_24h": 3 } },
  "resumen": { "estado": "ok", "servicios_ok": 10, "servicios_total": 10, "alertas": 0 },
  "alertas": [] }
```

| Endpoint | Respuesta exitosa |
|---|---|
| exportaciones/devoluciones | 200: folio, estado, producto, lote, reembolso, costo total, `venta_id_pos`, `devolucion_id_erp`, paginación y periodo |
| transportistas/eventos | 200: estado anterior, estado nuevo y `cambio` (true o false) |
| monitoreo/disponibilidad | 200: por servicio, chequeos, ok, degradado, caído, `disponibilidad_pct`, `ms_promedio` y `ms_p95` |
| monitoreo/alertas | 200: tipo, recurso, severidad, mensaje, veces, primera y última vez, estado |
| monitoreo/traza | 200: pasos en orden (bitácora y eventos) y servicios involucrados |

| Código | Tipo | Cuándo ocurre |
|---|---|---|
| 400 | validacion, xml_no_cumple_xsd | Datos con forma inválida, rango de fechas inválido |
| 401 / 403 | no_autenticado / sin_permiso | Token inválido o rol no permitido |
| 404 | no_encontrado | Registro interno inexistente, traza sin registros |
| 409 | conciliacion_distinta, folio_ocupado, transicion_invalida | El id ya apunta a otro registro, folio usado o avance imposible |
| 422 | sin_conciliar, cliente_desconocido, lote_desconocido | Falta una equivalencia o un dato del catálogo |

## 8. Seguridad

| Operación | Administrador | Supervisor | Coordinador | Encargado de Reembolsos / Analista |
|---|---|---|---|---|
| Importar ventas y conciliar | Sí | No | No | No |
| Traducir un id externo | Sí | No | No | Sí |
| Exportar devoluciones | Sí | No | No | Sí |
| Eventos del transportista | Sí | No | Sí | No |
| Monitoreo | Sí | Sí | No | No |

- **Inyección SQL:** parámetros ligados; el nombre de la tabla a conciliar sale de un diccionario fijo del código, nunca de la petición (RNF-11).
- **Identificadores externos acotados:** solo letras, números y `_ . : / -`, hasta 64 caracteres.
- **Errores sin datos internos:** `/health` y el monitoreo nunca muestran contraseñas, hosts ni trazas; el detalle va al log (RNF-16).
- **XML seguro:** XSD y lector sin entidades externas (XXE).
- **Bitácora:** cada importación, conciliación, exportación y evento de transportista queda registrado.

## 9. Persistencia

**PostgreSQL. Tabla nueva `integraciones_ids` (migración 018):** `sistema`, `tipo_entidad`, `id_externo`, `id_interno`, `creado_por`, `creado_en`. Llave primaria (sistema, tipo_entidad, id_externo) e índice único (sistema, tipo_entidad, id_interno): un registro tiene un solo id por sistema.

| Tabla | Operación | Uso |
|---|---|---|
| ventas, venta_detalle | Inserción | Venta importada del POS (folio `POS-<ticket>`) |
| tiendas, usuarios, lotes, productos | Consulta | Validar tienda, cliente y lote |
| devoluciones, reembolsos, costos | Consulta | Exportación para ERP y finanzas |
| recolecciones | Actualización | Eventos del transportista |
| operaciones_offline | Consulta | Cola de sincronización (monitoreo) |
| bitacora | Inserción y consulta | Auditoría y traza distribuida |

**MongoDB:**

| Colección | Uso |
|---|---|
| `monitoreo_chequeos` | Un documento por chequeo; índice TTL que lo borra a los 7 días |
| `alertas_operativas` | Una alerta activa por (tipo, recurso); veces, primera y última vez, resuelta_en |
| `eventos` | `venta_importada` y lectura de eventos de todos los servicios para la traza |

**Redis:** sesión JWT y `devoluciones:monitoreo:turno` (candado del vigilante, expira cada minuto).

## 10. Integración

```
POS / ERP / transportista --JWT--> integraciones-monitoreo (8021) --> PostgreSQL (integraciones_ids, ventas, ...)
                                        |   \--> MongoDB (chequeos, alertas, eventos)
                                        |
                       cada 60 s  GET /health --> web, auth, ventas-catalogos, devoluciones, evidencias,
                                                  logistica, inspecciones, reembolsos-costos,
                                                  analisis-auditoria, sincronizacion
```

| Componente | Integración |
|---|---|
| Los diez servicios | Les pregunta su `/health` cada minuto; se configuran en `MONITOREO_SERVICIOS` |
| sincronizacion | Lee la cola `operaciones_offline` para contar conflictos y reintentos |
| Todos los servicios | La traza junta su bitácora y sus eventos por `X-Correlation-ID` |
| POS, ERP, transportistas | Guía en `docs/GUIA_INTEGRACIONES_MONITOREO.md` |

## 11. Despliegue

| Elemento | Valor |
|---|---|
| Servicio / contenedor | `integraciones-monitoreo` / `devoluciones_integraciones_monitoreo` |
| Puerto | 8021 (host) → 8000 (contenedor) |
| Dependencias | postgres, redis y mongo en estado healthy |
| Healthcheck | GET /health cada 15 s, 3 reintentos |
| Variables | Desde `.env`: JWT_SECRET, POSTGRES_*, REDIS_*, MONGO_*; `MONITOREO_INTERVALO_SEG` (60) y `MONITOREO_SERVICIOS` (opcional) |
| Migración | `018_integraciones_ids.sql` |

```
docker compose up -d --build integraciones-monitoreo
docker compose exec app python scripts/migrate.py
curl "http://localhost:$(grep ^PROXY_HTTP_PORT .env | cut -d= -f2)/servicios/integraciones-monitoreo/health"
docker compose logs -f integraciones-monitoreo
```

## 12. Evidencias

Capturas por tomar con Postman o Swagger contra la VM (tokens ocultos). Nombre: `NN_integraciones_<endpoint>_<metodo>_<codigo>_<caso>.png` o `NN_monitoreo_...`.

| Endpoint | Caso | Código |
|---|---|---|
| GET /health | Servicio y sus tres bases en línea | 200 |
| POST /integraciones/ventas | Tienda sin conciliar | 422 |
| POST /integraciones/conciliaciones | Conciliar la tienda del POS | 201 |
| POST /integraciones/ventas | Venta importada | 201 |
| POST /integraciones/ventas | **El mismo ticket otra vez: `repetida: true`** | 200 |
| POST /integraciones/ventas | Venta en XML | 201 |
| GET /integraciones/exportaciones/devoluciones | Exportación en XML para el ERP | 200 |
| POST /integraciones/transportistas/eventos | Evento aplicado y reenviado (`cambio: false`) | 200 |
| GET /monitoreo/estado | Los diez servicios en `ok` con su tiempo | 200 |
| GET /monitoreo/alertas | Alerta `base_no_disponible` (durante la prueba de recuperación) | 200 |
| GET /monitoreo/disponibilidad | Disponibilidad y p95 de las últimas 24 h | 200 |
| GET /monitoreo/traza/{id} | Pasos de una operación | 200 |
| GET /monitoreo/estado | Cliente intenta ver el monitoreo | 403 |

## 13. Pruebas

| Tipo | Archivo | Resultado |
|---|---|---|
| Unitarias de reglas | `tests/test_reglas.py` | 12 passed |
| Unitarias de endpoints | `tests/test_api.py` | 7 passed |
| Integración (VM) | `tests/test_integracion.py` | 8 passed |
| Recuperación (VM) | `scripts/prueba_recuperacion.py`, escenario 3 | OK: alerta abierta y resuelta sola |

**Casos de integración:**

| Prueba | Qué comprueba |
|---|---|
| test_1 | Venta con tienda sin conciliar (422); después se importa una sola vez y el reenvío responde `repetida` |
| test_2 | Dos envíos simultáneos del mismo ticket: una sola venta |
| test_3 | Venta en XML y exportación para el ERP con el ticket del POS; Cliente recibe 403 |
| test_4 | Evento del transportista: sin conciliar, aplicado, reenviado sin cambio y transición inválida |
| test_5 | Conciliación hacia otro registro: 409 |
| test_6 | Estado de toda la plataforma: servicios, bases y cola |
| test_7 | Un servicio caído abre la alerta; al volver, se resuelve sola; aparece en la disponibilidad |
| test_8 | Traza por correlation id; uno inexistente responde 404 |
