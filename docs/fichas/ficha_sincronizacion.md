# Ficha técnica: Servicio de sincronización offline (sincronizacion)

## 1. Identificación

| Campo | Valor |
|---|---|
| Nombre | `sincronizacion`: servicio de sincronización de operaciones capturadas sin conexión |
| Propósito | Recibir las operaciones que las apps Android y de escritorio guardaron mientras no tenían red, y aplicarlas una sola vez |
| Responsabilidad | Recibe la cola de operaciones pendientes de un dispositivo, decide por cada una si se acepta, si choca con un cambio hecho en el servidor (conflicto) o si se rechaza, y garantiza que una operación reenviada nunca se aplique dos veces |
| Puerto | 8020 |
| Ruta base | `/api/v1/sincronizacion` |

## 2. Justificación

El trabajo de campo (recolectores y almacén) ocurre en lugares sin buena señal. La retroalimentación pide que la app pueda capturar sin conexión, pero que una recolección o recepción **no aparezca como confirmada hasta que el servidor la acepte**, y que las operaciones financieras, autorizaciones y disposiciones **siempre** comprueben permisos y estado en el servidor. Separarlo en un microservicio propio permite que:

- La lógica de reintentos, duplicados y conflictos viva en un solo lugar y no se repita en logística, evidencias y cada app.
- Las apps tengan un único punto de entrada para vaciar su cola, sin importar cuántos tipos de operación haya.
- El servidor decida qué se puede hacer sin conexión y qué no.

**Resultados posibles de cada operación:** `aceptada` (aplicada y confirmada), `conflicto` (el servidor cambió mientras el dispositivo no tenía red), `rechazada` (datos inválidos, sin permiso u operación que solo se hace en línea) y `reintentar` (falla temporal del servidor).

**Requerimientos cubiertos:** dominio 20 del tercer parcial, RF-09 (evidencias), RF-12 a RF-15 (recolección y recepción), RN-12 (toda decisión queda registrada), RN-13 (cada usuario solo ejecuta lo de su rol), RNF-09 (autorización por rol), RNF-11 (SQL parametrizado), RNF-16 (errores sin datos internos), RNF-23 (trazabilidad por correlation id), RNF-28 (pruebas). Prueba de la retroalimentación: *"se captura un evento permitido offline y se sincroniza sin duplicaciones"*.

## 3. Diseño (Arquitectura interna)

El microservicio usa las mismas capas que auth y devoluciones y reutiliza la carpeta `shared/`.

| Capa | Archivo | Responsabilidad |
|---|---|---|
| Entrada y salida | `shared/respuestas.py`, `shared/xsd.py` | JSON o XML según Accept, validación del XML contra `lote.xsd`, errores con formato estándar |
| Seguridad | `shared/seguridad.py` | `@requiere_jwt(roles)`, control por sucursal (`exigir_tienda`) |
| Reglas | `services/sincronizacion/reglas.py` | Funciones puras: tipos permitidos offline, huella SHA-256, fecha de captura, transiciones, GPS |
| Lógica de negocio | `services/sincronizacion/app.py` | Idempotencia, conflictos y efecto de cada tipo de operación |
| Datos | `shared/infra.py`, `shared/mongo.py`, `shared/paginacion.py` | PostgreSQL (incluye `confirmar()`), Redis, MongoDB, bitácora y paginación |

**Qué pasa con cada operación del envío:**

| Paso | Qué hace | Para qué |
|---|---|---|
| 1 | Valida que `id_operacion` sea un UUID | Es la llave de idempotencia |
| 2 | Calcula la huella SHA-256 del contenido | Detectar un id reutilizado con otros datos |
| 3 | `INSERT ... ON CONFLICT DO NOTHING` en `operaciones_offline` | Apartar el id. Si otro envío trae el mismo id al mismo tiempo, PostgreSQL lo hace esperar |
| 4a | Si el id ya existía: devuelve el resultado guardado con `repetida: true` | El reintento recibe la misma respuesta y no se aplica otra vez |
| 4b | Si es nuevo: aplica el efecto dentro de un SAVEPOINT | Si falla, se deshace solo esa operación |
| 5 | Guarda el resultado (aceptada, conflicto o rechazada) | Un reintento de un conflicto recibe el mismo conflicto |
| 6 | Al final del envío: `confirmar()` (commit) **antes** de responder | La app nunca recibe "aceptada" de algo que no quedó guardado |

**Decisiones de diseño:**

- **El dispositivo genera el id:** se crea una sola vez al capturar y se reutiliza en cada reintento. Así el servidor reconoce la misma operación aunque llegue horas después.
- **Fila y efecto en la misma transacción:** o quedan las dos cosas o ninguna. No puede haber una recepción sin su registro de idempotencia, ni al revés.
- **Conflicto por estado esperado:** el dispositivo manda el estado que vio (`estado_esperado`). Si el servidor tiene otro, no se aplica y se devuelve `estado_servidor` para que el usuario decida.
- **409 = conflicto, otro error = rechazo:** se reutilizan los mismos códigos que logística; un 409 de negocio significa que el mundo cambió, no que los datos estén mal.
- **Fecha real de la captura:** la recepción guarda como fecha la de la captura (cuando el producto llegó) y no la de la sincronización.
- **Evidencias íntegras:** la foto viaja en base64 con su SHA-256; si no coincide se rechaza (`archivo_corrupto`).

## 4. Tecnología

| Componente | Tecnología | Versión | Uso en el servicio |
|---|---|---|---|
| Lenguaje | Python | 3.11 | Mismo lenguaje que el sistema web |
| Framework web | Flask | 3.0.3 | Rutas REST y manejo de errores |
| Servidor | Gunicorn | 22.0.0 | 2 workers |
| Acceso a PostgreSQL | psycopg2-binary | 2.9.10 | SQL parametrizado, SAVEPOINT por operación |
| Acceso a MongoDB | pymongo | 4.8.0 | Metadatos de evidencias y eventos |
| Acceso a Redis | redis-py | 5.0.8 | Sesión JWT y rate limiting |
| Tokens | PyJWT | 2.9.0 | Validación de los JWT emitidos por auth |
| Validación XML | lxml | 5.3.0 | Validación del envío contra `lote.xsd` |
| Contrato OpenAPI | PyYAML | 6.0.2 | Swagger UI en `/docs` |
| Pruebas | pytest | 8.3.3 | Unitarias e integración |

- Biblioteca estándar: `hashlib` (SHA-256), `base64` (fotos), `uuid` (validación del id), `werkzeug.utils.secure_filename` (nombre del archivo).
- Dependencias fijadas en `services/sincronizacion/requirements.txt`.

## 5. Endpoints

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | `/api/v1/sincronizacion/operaciones` | Recolector, Operador de Almacén, Encargado del Centro, Coordinador | Recibe la cola de operaciones del dispositivo (máximo 50) y responde un resultado por operación |
| GET | `/api/v1/sincronizacion/operaciones` | Los anteriores, Supervisor y Administrador | Historial paginado; filtros `estado`, `dispositivo_id` y `devolucion_id` |
| GET | `/api/v1/sincronizacion/operaciones/{id_operacion}` | Los anteriores, Supervisor y Administrador | Estado de una operación cuya respuesta no le llegó a la app |
| GET | `/api/v1/sincronizacion/tipos` | Los anteriores, Supervisor y Administrador | Qué se puede capturar sin conexión, si tu rol puede y los límites |
| GET | `/health` | — | Estado del servicio, PostgreSQL, Redis y MongoDB |
| GET | `/docs` | — | Swagger UI |
| GET | `/contratos/{nombre}` | — | Contrato XSD publicado (`lote.xsd`) |

**Criterio de métodos HTTP:** POST porque el envío crea registros nuevos y no es seguro repetirlo a ciegas (la idempotencia la da el `id_operacion`, no el método); GET para consultar. No hay PUT, PATCH ni DELETE: una operación sincronizada no se edita ni se borra; si el usuario quiere otra cosa, captura una operación nueva.

## 6. Entrada

**Headers:** `Authorization: Bearer <token>`, `Content-Type: application/json` o `application/xml`, `Accept` y `X-Correlation-ID` opcional.

**Cuerpo de POST /operaciones** (contrato `lote.xsd`):

| Campo | Tipo | Obligatorio | Validación |
|---|---|---|---|
| `dispositivo_id` | texto | Sí | 1 a 64 letras, números o `_ . : -` |
| `operaciones` | lista | Sí | De 1 a 50 operaciones |
| `operaciones[].id_operacion` | UUID | Sí | Generado por el dispositivo |
| `operaciones[].tipo` | texto | Sí | `estado_recoleccion`, `recepcion` o `evidencia` |
| `operaciones[].capturado_en` | fecha y hora | Sí | ISO 8601 con zona horaria; no más de 7 días atrás ni en el futuro |
| `operaciones[].datos` | objeto | Sí | Depende del tipo (tabla siguiente) |

| Tipo | Datos |
|---|---|
| `estado_recoleccion` | `recoleccion_id`, `estado_esperado`, `estado` (`en_transito`, `completada` o `fallida`), `ubicacion` opcional `{latitud, longitud}` |
| `recepcion` | `devolucion_id`, `coincide_expediente` (opcional, true por defecto) |
| `evidencia` | `devolucion_id`, `comentario` (máximo 2000) y/o `archivo {nombre, contenido_base64, sha256}` (JPG, PNG o PDF de hasta 5 MB) |

```
{ "dispositivo_id": "android-luis-01",
  "operaciones": [
    { "id_operacion": "6f1c2a3b-8d4e-4f5a-9b6c-7d8e9f0a1b2c", "tipo": "estado_recoleccion",
      "capturado_en": "2026-11-20T09:15:00-06:00",
      "datos": { "recoleccion_id": 12, "estado_esperado": "asignada", "estado": "en_transito",
                 "ubicacion": { "latitud": 25.6866, "longitud": -100.3161 } } } ] }

<sincronizacion>
  <dispositivo_id>escritorio-1</dispositivo_id>
  <operaciones><item>
    <id_operacion>6f1c2a3b-8d4e-4f5a-9b6c-7d8e9f0a1b2c</id_operacion>
    <tipo>recepcion</tipo>
    <capturado_en>2026-11-20T09:15:00-06:00</capturado_en>
    <datos><devolucion_id>40</devolucion_id><coincide_expediente>true</coincide_expediente></datos>
  </item></operaciones>
</sincronizacion>
```

**Parámetros de GET /operaciones:** `estado` (aceptada, conflicto o rechazada), `dispositivo_id`, `devolucion_id`, `pagina` y `por_pagina` (1 a 100).

- **Validación en dos niveles:** primero la forma del envío (XSD o JSON); después cada operación por separado. Una operación mala no tumba el envío completo.

## 7. Salida

**Respuesta de POST /operaciones (200):**

```
{ "dispositivo_id": "android-luis-01", "recibidas": 2,
  "resumen": { "aceptada": 1, "conflicto": 1, "rechazada": 0, "reintentar": 0 },
  "repetidas": 0,
  "resultados": [
    { "id_operacion": "6f1c...", "tipo": "estado_recoleccion", "estado": "aceptada",
      "repetida": false, "devolucion_id": 40,
      "respuesta": { "recoleccion_id": 12, "estado_anterior": "asignada", "estado": "en_transito" } },
    { "id_operacion": "9a2b...", "tipo": "estado_recoleccion", "estado": "conflicto",
      "repetida": false,
      "motivo": { "codigo": 409, "tipo": "conflicto_estado",
                  "mensaje": "La recoleccion cambio en el servidor mientras el dispositivo estaba sin conexion.",
                  "detalles": { "estado_esperado": "asignada", "estado_servidor": "fallida" } } } ] }
```

| Endpoint | Respuesta exitosa |
|---|---|
| POST /operaciones | 200 con un resultado por operación, en el mismo orden |
| GET /operaciones | 200: `{ datos: [...], paginacion: {...} }` |
| GET /operaciones/{id} | 200: estado, envíos, fechas y resultado guardado |
| GET /tipos | 200: tipos, roles permitidos, operaciones solo en línea y límites |

**Errores del envío completo:**

| Código | Tipo | Cuándo ocurre |
|---|---|---|
| 400 | validacion, xml_invalido, xml_no_cumple_xsd | dispositivo_id inválido, lista vacía o de más de 50 |
| 401 | no_autenticado, token_invalido, token_expirado | Token ausente o no válido |
| 403 | sin_permiso | Rol sin operaciones offline (por ejemplo, Cliente) |
| 413 | — | Envío de más de 16 MB |
| 429 | demasiadas_peticiones | Más de 30 envíos por minuto del mismo usuario |

**Motivos por operación (dentro de `resultados`):**

| Estado | Tipo | Cuándo |
|---|---|---|
| conflicto | conflicto_estado, estado_no_permite, recepcion_duplicada | El servidor cambió mientras el dispositivo no tenía red |
| rechazada | requiere_conexion | Operación que solo se hace en línea (reembolsos, autorizaciones, disposiciones) |
| rechazada | sin_permiso, fuera_de_sucursal | Rol o sucursal no permitidos |
| rechazada | captura_invalida | Captura de más de 7 días o con fecha en el futuro |
| rechazada | archivo_corrupto, archivo_grande, formato_no_soportado | La foto no coincide con su SHA-256, pasa de 5 MB o no es JPG, PNG o PDF |
| rechazada | id_reutilizado | El mismo id llegó con otros datos |
| reintentar | error_temporal | Falla temporal; la app la reenvía con el mismo id |

## 8. Seguridad

| Tipo de operación | Recolector | Operador de Almacén | Encargado del Centro | Coordinador |
|---|---|---|---|---|
| estado_recoleccion | Sí | No | No | Sí |
| recepcion | No | Sí | Sí | No |
| evidencia | Sí (etapa recolección) | Sí (etapa recepción) | Sí (etapa recepción) | No |

- **Solo en línea:** autorizar devolución, programar recolección, aprobar reembolso, aprobar disposición, reincorporar inventario y cerrar investigación se rechazan siempre con `requiere_conexion`.
- **Control por sucursal:** un usuario con sucursal solo opera devoluciones de su tienda (`fuera_de_sucursal`).
- **La etapa la decide el servidor:** la etapa de la evidencia sale del rol, no del dispositivo.
- **Privacidad entre usuarios:** cada quien ve solo sus operaciones; consultar la de otro responde 404 (no se confirma que exista). Un id reutilizado por otro usuario no revela el contenido original.
- **Rate limiting:** 30 envíos por minuto por usuario; 16 MB por envío; 5 MB por archivo.
- **Inyección SQL y XML:** parámetros ligados (RNF-11) y lector XML sin entidades externas (XXE).

## 9. Persistencia

**PostgreSQL. Tabla nueva `operaciones_offline` (migración 017):**

| Columna | Uso |
|---|---|
| `id_operacion` (UUID, PK) | Llave de idempotencia |
| `usuario_id`, `dispositivo_id` | Quién y desde qué equipo |
| `tipo`, `devolucion_id` | Qué operación y sobre qué devolución |
| `huella` | SHA-256 del contenido |
| `estado`, `resultado` (JSONB) | Decisión guardada y respuesta completa |
| `capturado_en`, `recibido_en`, `envios` | Cuándo se capturó, cuándo llegó y cuántas veces se envió |

| Tabla | Operación | Uso |
|---|---|---|
| recolecciones | Consulta con bloqueo y actualización | Avance de la recolección |
| recepciones, devoluciones | Inserción y actualización | Recepción en el centro; la devolución pasa a `recibida` |
| evidencias | Inserción | Comentario o foto de campo |
| bitacora | Inserción | Cada operación aceptada, con la fecha de captura y el GPS |

**MongoDB:** `evidencias_metadatos` (metadatos de la foto con `id_operacion` como llave, para no duplicarse) y `eventos` (`operacion_offline_aceptada`).

**Redis:** sesión y revocación del JWT, y `devoluciones:limite:usuario<id>:sincronizacion` (60 s).

**Volumen Docker `evidencias_data`:** el mismo del servicio de evidencias, con el mismo formato de nombre de archivo, para que una foto sincronizada se descargue igual que una subida en línea.

## 10. Integración

```
App Android / escritorio --JWT--> sincronizacion (8020) --> PostgreSQL (operaciones_offline, recolecciones,
       (cola local)                     |                     recepciones, evidencias, bitacora)
                                        |--> MongoDB (evidencias_metadatos, eventos)
                                        |--> Volumen evidencias_data (fotos)
                                        \--> Redis (sesion, limite)
auth (8001) emite el JWT       integraciones-monitoreo (8021) vigila la cola (conflictos, reintentos)
```

| Componente | Integración |
|---|---|
| auth | Emite los tokens; el servicio los valida con `shared/seguridad.py` |
| logística | Mismas transiciones de la recolección; lo sincronizado aparece en sus listados |
| evidencias | Mismo volumen y formato: la foto se consulta con los enlaces firmados de evidencias |
| integraciones-monitoreo | Cuenta conflictos y reintentos de las últimas 24 h y alerta si hay más de 10 conflictos |
| Apps Android y escritorio | Guía de uso en `docs/GUIA_SINCRONIZACION.md` |

## 11. Despliegue

| Elemento | Valor |
|---|---|
| Servicio / contenedor | `sincronizacion` / `devoluciones_sincronizacion` |
| Puerto | 8020 (host) → 8000 (contenedor) |
| Dependencias | postgres, redis y mongo en estado healthy |
| Healthcheck | GET /health cada 15 s, 3 reintentos |
| Volumen | `evidencias_data` en `/srv/evidencias_privadas` |
| Variables | Desde `.env`: JWT_SECRET, POSTGRES_*, REDIS_*, MONGO_*; `EVIDENCIAS_DIR` |
| Migración | `017_operaciones_offline.sql` |

```
docker compose up -d --build sincronizacion
docker compose exec app python scripts/migrate.py
curl "http://localhost:$(grep ^PROXY_HTTP_PORT .env | cut -d= -f2)/servicios/sincronizacion/health"
docker compose logs -f sincronizacion
```

## 12. Evidencias

Capturas por tomar con Postman o Swagger contra la VM (tokens ocultos). Nombre: `NN_sincronizacion_<endpoint>_<metodo>_<codigo>_<caso>.png`.

| Endpoint | Caso | Código |
|---|---|---|
| GET /health | Servicio y sus tres bases en línea | 200 |
| GET /tipos | Catálogo visto por el Recolector | 200 |
| POST /operaciones | Envío con 3 operaciones aceptadas (avance, evidencia, avance) | 200 |
| POST /operaciones | **El mismo envío otra vez: las 3 vuelven con `repetida: true`** | 200 |
| POST /operaciones | Conflicto: la recolección cambió en el servidor | 200 (conflicto) |
| POST /operaciones | `aprobar_reembolso` rechazada con `requiere_conexion` | 200 (rechazada) |
| POST /operaciones | Envío en XML | 200 |
| POST /operaciones | Cliente intenta sincronizar | 403 |
| GET /operaciones/{id} | Consulta de una operación (envíos = 2) | 200 |
| Base de datos | `SELECT` de `operaciones_offline` mostrando una sola fila con `envios = 2` | — |

## 13. Pruebas

| Tipo | Archivo | Resultado |
|---|---|---|
| Unitarias de reglas | `tests/test_reglas.py` | 16 passed |
| Unitarias de endpoints | `tests/test_api.py` | 8 passed |
| Integración (VM) | `tests/test_integracion.py` | 9 passed |
| Recuperación (VM) | `scripts/prueba_recuperacion.py`, escenario 2 | OK |

**Casos de integración:**

| Prueba | Qué comprueba |
|---|---|
| test_1 | Tres operaciones aceptadas; al reenviarlas, `repetida: true` y una sola evidencia |
| test_2 | El mismo id con otros datos se rechaza (`id_reutilizado`) |
| test_3 | Dos envíos simultáneos del mismo id: solo uno se aplica |
| test_4 | Conflicto cuando el servidor cambió; el reintento recibe el mismo conflicto |
| test_5 | Recepción con la fecha de captura y foto verificada con SHA-256; la foto alterada se rechaza |
| test_6 | Operación solo en línea, rol equivocado y captura de hace 8 días: rechazadas |
| test_7 | Devolución de otra sucursal: rechazada |
| test_8 | Envío en XML |
| test_9 | Consulta de una operación; otro usuario recibe 404 |
