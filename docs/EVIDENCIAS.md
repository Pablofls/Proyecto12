# Evidencias request/response por servicio (apartado 5)

<!-- Generado por docs/postman/generar_colecciones.py; no editar a mano. Para cambiar algo, edita docs/postman/especificaciones.py y regenera. -->

Cada endpoint sigue la plantilla del apartado 5: URL y metodo, objetivo, parametros, headers, body, respuesta, codigo, explicacion, evidencia en PostgreSQL / MongoDB / Redis, error controlado y captura.

**Que es real y que esta pendiente.** URL, metodo, headers, body y la explicacion salen del codigo del servicio y de su `openapi.yaml`. La **respuesta** y la **captura** solo existen despues de ejecutar en la VM: hasta entonces estan marcadas `<!-- CAPTURA PENDIENTE: id -->`. Las respuestas marcadas `ejecucion real` salen de una corrida de Newman contra la VM (transcripciones en `docs/evidencias/ejecuciones/`); las que siguen en `CAPTURA PENDIENTE` no se han ejecutado todavia. Como capturarlas: [docs/evidencias/README.md](evidencias/README.md); lista de archivos esperados: [docs/evidencias/CHECKLIST_CAPTURAS.md](evidencias/CHECKLIST_CAPTURAS.md).

Las variables `{{...}}` son las del environment `docs/postman/vm.postman_environment.json`.

## Indice

- [Autenticacion (`auth`, puerto 8001)](#auth) - 25 capturas
- [Devoluciones (`devoluciones`, puerto 8002)](#devoluciones) - 27 capturas
- [Logistica inversa (`logistica`, puerto 8003)](#logistica) - 31 capturas
- [Inspecciones y disposicion (`inspecciones`, puerto 8004)](#inspecciones) - 27 capturas
- [Reembolsos y costos (`reembolsos_costos`, puerto 8005)](#reembolsos_costos) - 27 capturas
- [Ventas y catalogos (`ventas_catalogos`, puerto 8006)](#ventas_catalogos) - 35 capturas
- [Evidencias (`evidencias`, puerto 8007)](#evidencias) - 36 capturas
- [Analisis y auditoria (`analisis_auditoria`, puerto 8008)](#analisis_auditoria) - 32 capturas

## auth

**Autenticacion** - puerto 8001 - coleccion `docs/postman/auth.postman_collection.json` - Swagger en `/docs` del servicio.

### GET /health

*openapi.yaml:* Estado del servicio y sus dependencias

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{auth_url}}/health` |
| Objetivo | RNF-22, RF-32: el servicio responde y reporta el estado de sus dependencias. |
| Parametros | Ninguno |
| Headers | `Accept: application/json` |
| Roles (caso exitoso) | Sin autenticacion |
| Codigo HTTP esperado | 200 |
| Explicacion | RNF-22, RF-32: el servicio responde y reporta el estado de sus dependencias. |
| Evidencia en PostgreSQL | `SELECT 1;` desde el contenedor; el servicio hace la misma comprobacion. |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | `redis-cli PING` responde PONG. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/auth.md#001_auth_get_health_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 1 | health 200 | JSON | ninguno | 200 | - | `[ejecucion real](evidencias/ejecuciones/auth.md#001_auth_get_health_200)` |
| 2 | health 200 XML | XML | ninguno | 200 | - | `[ejecucion real](evidencias/ejecuciones/auth.md#002_auth_get_health_200_xml)` |

### POST /api/v1/auth/login

*openapi.yaml:* Iniciar sesion y obtener tokens

| Campo | Detalle |
|---|---|
| URL y metodo | `POST {{auth_url}}/api/v1/auth/login` |
| Objetivo | RF-01, HU-01: el analista inicia sesion y recibe access_token y refresh_token (JWT). |
| Parametros | Ninguno |
| Headers | `Content-Type: application/json`; `Accept: application/json` |
| Roles (caso exitoso) | Sin autenticacion |
| Codigo HTTP esperado | 200 |
| Explicacion | Valida correo y contrasena, abre la sesion en Redis y firma access (corto) y refresh (8 h) con HS256. |
| Evidencia en PostgreSQL | `SELECT email, exitoso, ip_origen, fecha FROM intentos_acceso ORDER BY id DESC LIMIT 3;` y bitacora `login_api`: `SELECT accion, entidad, entidad_id, detalle FROM bitacora ORDER BY id DESC LIMIT 3;` (RF-30). |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | `redis-cli --scan --pattern 'devoluciones:sesion_api:*'`; `HGETALL` de la clave (usuario_id, rol, ip) y `TTL` (cerca de 28800 s); `SMEMBERS devoluciones:sesiones_usuario:<id>`; `GET devoluciones:limite:<ip>:login` (contador de la ventana de 60 s). |

**Body de ejemplo** (caso login 200 exitoso):

```json
{
  "email": "{{email_analista}}",
  "password": "{{password_demo}}"
}
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/auth.md#003_auth_post_login_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 3 | login 200 exitoso | JSON | ninguno | 200 | - | `[ejecucion real](evidencias/ejecuciones/auth.md#003_auth_post_login_200)` |
| 4 | login 200 XML (admin) | XML | ninguno | 200 | - | `[ejecucion real](evidencias/ejecuciones/auth.md#004_auth_post_login_200_xml)` |
| 5 | login 400 datos invalidos | JSON | ninguno | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/auth.md#005_auth_post_login_400)` |
| 6 | login 401 credenciales invalidas | JSON | ninguno | 401 | credenciales_invalidas | `[ejecucion real](evidencias/ejecuciones/auth.md#006_auth_post_login_401)` |
| 7 | login 415 formato no soportado | JSON | ninguno | 415 | formato_no_soportado | `[ejecucion real](evidencias/ejecuciones/auth.md#007_auth_post_login_415)` |
| 8 | login 400 XML mal formado | XML | ninguno | 400 | xml_invalido | `[ejecucion real](evidencias/ejecuciones/auth.md#008_auth_post_login_400_xml)` |
| 9 | login 400 XML no cumple XSD | XML | ninguno | 400 | xml_no_cumple_xsd | `[ejecucion real](evidencias/ejecuciones/auth.md#009_auth_post_login_400_xml)` |
| 24 | login 423 cuenta bloqueada | JSON | ninguno | 423 | cuenta_bloqueada | `<!-- CAPTURA PENDIENTE: 024_auth_post_login_423 -->` |
| 25 | login 429 rate limit | JSON | ninguno | 429 | demasiadas_peticiones | `<!-- CAPTURA PENDIENTE: 025_auth_post_login_429 -->` |

**Errores controlados:**

- **400 `validacion`** - login 400 datos invalidos: Validacion: correo mal formado y contrasena vacia.
- **401 `credenciales_invalidas`** - login 401 credenciales invalidas: RNF-16: el mensaje es generico, no revela si el correo existe. Se usa un correo inexistente para no bloquear usuarios reales.
- **415 `formato_no_soportado`** - login 415 formato no soportado: Content-Type distinto de JSON/XML.
- **400 `xml_invalido`** - login 400 XML mal formado: XML que no esta bien formado.
- **400 `xml_no_cumple_xsd`** - login 400 XML no cumple XSD: XML bien formado al que le falta password (login.xsd).
- **423 `cuenta_bloqueada`** - login 423 cuenta bloqueada: RNF-12: tras 5 intentos fallidos la cuenta se bloquea 15 min; la peticion se repite sola hasta recibir 423. Usa email_bloqueo (Sofia) para no bloquear a los usuarios de las demas colecciones. Para desbloquear antes: `redis-cli DEL devoluciones:bloqueo:<correo> devoluciones:intentos:<correo>` y `UPDATE usuarios SET bloqueado_hasta = NULL WHERE email = '<correo>';`.
- **429 `demasiadas_peticiones`** - login 429 rate limit: RNF-13: mas de 10 logins por minuto desde la misma IP; se repite sola hasta recibir 429 y se revisa Retry-After.

### GET /api/v1/auth/sesion

*openapi.yaml:* Consultar la sesion actual

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{auth_url}}/api/v1/auth/sesion` |
| Objetivo | Datos de la sesion vigente y segundos que le quedan. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_analista}}`; `Accept: application/json` |
| Roles (caso exitoso) | Analista de Devoluciones |
| Codigo HTTP esperado | 200 |
| Explicacion | Datos de la sesion vigente y segundos que le quedan. |
| Evidencia en PostgreSQL | No aplica a este endpoint. |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | `TTL devoluciones:sesion_api:<sesion_id>` coincide con `sesion_expira_en_seg`. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/auth.md#010_auth_get_sesion_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 10 | sesion 200 exitoso | JSON | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/auth.md#010_auth_get_sesion_200)` |
| 11 | sesion 200 XML | XML | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/auth.md#011_auth_get_sesion_200_xml)` |
| 12 | sesion 401 sin token | JSON | ninguno | 401 | no_autenticado | `[ejecucion real](evidencias/ejecuciones/auth.md#012_auth_get_sesion_401)` |
| 13 | sesion 401 token invalido | JSON | Token invalido (cadena sin firma) | 401 | token_invalido | `[ejecucion real](evidencias/ejecuciones/auth.md#013_auth_get_sesion_401)` |
| 20 | sesion 401 token revocado | JSON | Analista de Devoluciones | 401 | token_revocado | `[ejecucion real](evidencias/ejecuciones/auth.md#020_auth_get_sesion_401)` |
| 23 | sesion 401 sesion inactiva | JSON | Analista de Devoluciones | 401 | sesion_inactiva | `[ejecucion real](evidencias/ejecuciones/auth.md#023_auth_get_sesion_401)` |

**Errores controlados:**

- **401 `no_autenticado`** - sesion 401 sin token: Endpoint protegido sin Authorization.
- **401 `token_invalido`** - sesion 401 token invalido: RNF-07: un JWT sin firma valida se rechaza.
- **401 `token_revocado`** - sesion 401 token revocado: El mismo token ya no sirve tras el logout.
- **401 `sesion_inactiva`** - sesion 401 sesion inactiva: El token sigue firmado pero su sesion ya no existe en Redis.

### POST /api/v1/auth/refresh

*openapi.yaml:* Obtener un nuevo access token

| Campo | Detalle |
|---|---|
| URL y metodo | `POST {{auth_url}}/api/v1/auth/refresh` |
| Objetivo | Cambia el refresh_token por un access_token nuevo. |
| Parametros | Ninguno |
| Headers | `Content-Type: application/json`; `Accept: application/json` |
| Roles (caso exitoso) | Sin autenticacion |
| Codigo HTTP esperado | 200 |
| Explicacion | Cambia el refresh_token por un access_token nuevo. |
| Evidencia en PostgreSQL | No aplica a este endpoint. |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | `GET devoluciones:limite:<ip>:refresh` (maximo 30 por minuto). |

**Body de ejemplo** (caso refresh 200 exitoso):

```json
{
  "refresh_token": "{{refresh_token}}"
}
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/auth.md#014_auth_post_refresh_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 14 | refresh 200 exitoso | JSON | ninguno | 200 | - | `[ejecucion real](evidencias/ejecuciones/auth.md#014_auth_post_refresh_200)` |
| 15 | refresh 401 con access token | JSON | ninguno | 401 | token_invalido | `[ejecucion real](evidencias/ejecuciones/auth.md#015_auth_post_refresh_401)` |
| 16 | refresh 400 sin refresh_token | JSON | ninguno | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/auth.md#016_auth_post_refresh_400)` |
| 21 | refresh 401 sesion inactiva | JSON | ninguno | 401 | sesion_inactiva | `[ejecucion real](evidencias/ejecuciones/auth.md#021_auth_post_refresh_401)` |

**Errores controlados:**

- **401 `token_invalido`** - refresh 401 con access token: Un access token no sirve como refresh (claim typ).
- **400 `validacion`** - refresh 400 sin refresh_token: Falta el campo obligatorio.
- **401 `sesion_inactiva`** - refresh 401 sesion inactiva: El refresh de una sesion cerrada tampoco sirve.

### DELETE /api/v1/auth/usuarios/{id}/sesiones

*openapi.yaml:* Cerrar todas las sesiones de un usuario (Administrador)

| Campo | Detalle |
|---|---|
| URL y metodo | `DELETE {{auth_url}}/api/v1/auth/usuarios/{{analista_id}}/sesiones` |
| Objetivo | RNF-08: el administrador cierra todas las sesiones de un usuario sin esperar a que expiren. |
| Parametros | `usuario_id` (path) |
| Headers | `Authorization: Bearer {{token_admin}}`; `Accept: application/json` |
| Roles (caso exitoso) | Administrador |
| Codigo HTTP esperado | 200 |
| Explicacion | RNF-08: el administrador cierra todas las sesiones de un usuario sin esperar a que expiren. |
| Evidencia en PostgreSQL | Bitacora `revocar_sesiones`: `SELECT accion, entidad, entidad_id, detalle FROM bitacora ORDER BY id DESC LIMIT 3;` (RF-30). |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | `SMEMBERS devoluciones:sesiones_usuario:<id>` queda vacio y `EXISTS devoluciones:sesion_api:<sid>` -> 0. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/auth.md#022_auth_delete_usuarios_id_sesiones_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 22 | cerrar sesiones 200 admin | JSON | Administrador | 200 | - | `[ejecucion real](evidencias/ejecuciones/auth.md#022_auth_delete_usuarios_id_sesiones_200)` |
| 17 | cerrar sesiones 403 rol sin permiso | JSON | Analista de Devoluciones | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/auth.md#017_auth_delete_usuarios_id_sesiones_403)` |
| 18 | cerrar sesiones 404 usuario inexistente | JSON | Administrador | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/auth.md#018_auth_delete_usuarios_id_sesiones_404)` |

**Errores controlados:**

- **403 `sin_permiso`** - cerrar sesiones 403 rol sin permiso: RNF-09: solo el Administrador cierra sesiones ajenas.
- **404 `no_encontrado`** - cerrar sesiones 404 usuario inexistente: Usuario que no existe.

### POST /api/v1/auth/logout

*openapi.yaml:* Cerrar sesion

| Campo | Detalle |
|---|---|
| URL y metodo | `POST {{auth_url}}/api/v1/auth/logout` |
| Objetivo | RNF-08: revoca el token y cierra la sesion. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_analista}}`; `Content-Type: application/json`; `Accept: application/json` |
| Roles (caso exitoso) | Analista de Devoluciones |
| Codigo HTTP esperado | 200 |
| Explicacion | Agrega el jti del access token a la lista negra con TTL igual a su vida restante y borra la sesion. |
| Evidencia en PostgreSQL | Bitacora `logout_api`: `SELECT accion, entidad, entidad_id, detalle FROM bitacora ORDER BY id DESC LIMIT 3;` (RF-30). |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | `GET devoluciones:jwt_revocado:<jti>` -> "1" con `TTL` > 0; la clave `devoluciones:sesion_api:<sid>` ya no existe (`EXISTS` -> 0). |

**Body de ejemplo** (caso logout 200 exitoso):

```json
{}
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/auth.md#019_auth_post_logout_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 19 | logout 200 exitoso | JSON | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/auth.md#019_auth_post_logout_200)` |

## devoluciones

**Devoluciones** - puerto 8002 - coleccion `docs/postman/devoluciones.postman_collection.json` - Swagger en `/docs` del servicio.

### GET /health

*openapi.yaml:* Estado del servicio, PostgreSQL, Redis y MongoDB

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{devoluciones_url}}/health` |
| Objetivo | RNF-22, RF-32: el servicio responde y reporta el estado de sus dependencias. |
| Parametros | Ninguno |
| Headers | `Accept: application/json` |
| Roles (caso exitoso) | Sin autenticacion |
| Codigo HTTP esperado | 200 |
| Explicacion | RNF-22, RF-32: el servicio responde y reporta el estado de sus dependencias. |
| Evidencia en PostgreSQL | `SELECT 1;` desde el contenedor; el servicio hace la misma comprobacion. |
| Evidencia en MongoDB | `mongosh --eval "db.runCommand({ping:1})"` |
| Evidencia en Redis | `redis-cli PING` responde PONG. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/devoluciones.md#026_devoluciones_get_health_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 26 | health 200 | JSON | ninguno | 200 | - | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#026_devoluciones_get_health_200)` |

### POST /api/v1/devoluciones

*openapi.yaml:* Registrar una devolucion (Cliente o Analista)

| Campo | Detalle |
|---|---|
| URL y metodo | `POST {{devoluciones_url}}/api/v1/devoluciones` |
| Objetivo | RF-07, RN-01: el cliente registra una devolucion sobre su compra. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_cliente}}`; `Content-Type: application/json`; `Accept: application/json` |
| Roles (caso exitoso) | Cliente (dueno de la compra) |
| Codigo HTTP esperado | 201 |
| Explicacion | Valida la compra (es del cliente, hay unidades), inserta la devolucion en estado `solicitada`, escribe bitacora y publica el evento `devolucion_registrada`. Limite: 20 por minuto por usuario. |
| Evidencia en PostgreSQL | `SELECT id, folio_devolucion, estado, cantidad_devuelta FROM devoluciones ORDER BY id DESC LIMIT 1;` y `SELECT accion, entidad, entidad_id, detalle FROM bitacora ORDER BY id DESC LIMIT 3;` (RF-30). |
| Evidencia en MongoDB | `db.eventos.find({servicio:'devoluciones'}).sort({fecha:-1}).limit(2)` (RNF-23). Debe verse `tipo: 'devolucion_registrada'`. |
| Evidencia en Redis | `GET devoluciones:limite:usuario<id>:crear_devolucion` (contador, `TTL` <= 60). |

**Body de ejemplo** (caso registrar 201 exitoso):

```json
{
  "venta_detalle_id": {{venta_detalle_id}},
  "motivo_id": {{motivo_id}},
  "descripcion_problema": "El empaque llego roto y el producto derramado.",
  "cantidad_devuelta": 1
}
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/devoluciones.md#028_devoluciones_post_raiz_201)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 28 | registrar 201 exitoso | JSON | Cliente (dueno de la compra) | 201 | - | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#028_devoluciones_post_raiz_201)` |
| 29 | registrar 201 XML | XML | Cliente (dueno de la compra) | 201 | - | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#029_devoluciones_post_raiz_201_xml)` |
| 27 | registrar 409 cantidad excedida | JSON | Cliente (dueno de la compra) | 409 | cantidad_excedida | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#027_devoluciones_post_raiz_409)` |
| 30 | registrar 400 datos invalidos | JSON | Cliente (dueno de la compra) | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#030_devoluciones_post_raiz_400)` |
| 31 | registrar 400 XML no cumple XSD | XML | Cliente (dueno de la compra) | 400 | xml_no_cumple_xsd | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#031_devoluciones_post_raiz_400_xml)` |
| 32 | registrar 401 sin token | JSON | ninguno | 401 | no_autenticado | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#032_devoluciones_post_raiz_401)` |
| 33 | registrar 403 compra de otro cliente | JSON | Cliente (dueno de la compra) | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#033_devoluciones_post_raiz_403)` |
| 34 | registrar 404 linea inexistente | JSON | Cliente (dueno de la compra) | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#034_devoluciones_post_raiz_404)` |

**Errores controlados:**

- **409 `cantidad_excedida`** - registrar 409 cantidad excedida: Regla de negocio RN-01: no se devuelve mas de lo comprado. Va primero: si la linea ya no tuviera unidades la respuesta seria sin_disponible.
- **400 `validacion`** - registrar 400 datos invalidos: Validacion: id no numerico, motivo ausente y descripcion corta.
- **400 `xml_no_cumple_xsd`** - registrar 400 XML no cumple XSD: XML bien formado al que le faltan campos del contrato.
- **401 `no_autenticado`** - registrar 401 sin token: Endpoint protegido sin Authorization.
- **403 `sin_permiso`** - registrar 403 compra de otro cliente: Autorizacion por recurso: no se devuelve una compra ajena.
- **404 `no_encontrado`** - registrar 404 linea inexistente: La linea de venta no existe.

### GET /api/v1/devoluciones

*openapi.yaml:* Listar devoluciones con filtros y paginacion

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{devoluciones_url}}/api/v1/devoluciones?pagina=1&por_pagina=5` |
| Objetivo | RF-11: el cliente solo ve sus devoluciones. |
| Parametros | `estado` (query), `pagina` (query), `por_pagina` (query), `q` (query) |
| Headers | `Authorization: Bearer {{token_cliente}}`; `Accept: application/json` |
| Roles (caso exitoso) | Analista de Devoluciones, Cliente (dueno de la compra) |
| Codigo HTTP esperado | 200 |
| Explicacion | RF-11: el cliente solo ve sus devoluciones. |
| Evidencia en PostgreSQL | No aplica a este endpoint. |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/devoluciones.md#035_devoluciones_get_raiz_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 35 | listar 200 cliente paginado | JSON | Cliente (dueno de la compra) | 200 | - | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#035_devoluciones_get_raiz_200)` |
| 36 | listar 200 analista filtro XML | XML | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#036_devoluciones_get_raiz_200_xml)` |
| 37 | listar 400 estado invalido | JSON | Analista de Devoluciones | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#037_devoluciones_get_raiz_400)` |
| 38 | listar 401 sin token | JSON | ninguno | 401 | no_autenticado | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#038_devoluciones_get_raiz_401)` |
| 39 | listar 401 token invalido | JSON | Token invalido (cadena sin firma) | 401 | token_invalido | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#039_devoluciones_get_raiz_401)` |

**Errores controlados:**

- **400 `validacion`** - listar 400 estado invalido: Parametro de consulta invalido.
- **401 `no_autenticado`** - listar 401 sin token: Endpoint protegido sin Authorization.
- **401 `token_invalido`** - listar 401 token invalido: JWT sin firma valida.

### GET /api/v1/devoluciones/{id}

*openapi.yaml:* Expediente con historial (bitacora) y eventos (MongoDB)

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{devoluciones_url}}/api/v1/devoluciones/{{devolucion_id}}` |
| Objetivo | Expediente con historial (bitacora) y eventos (MongoDB). |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_cliente}}`; `Accept: application/json` |
| Roles (caso exitoso) | Analista de Devoluciones, Cliente (dueno de la compra) |
| Codigo HTTP esperado | 200 |
| Explicacion | Expediente con historial (bitacora) y eventos (MongoDB). |
| Evidencia en PostgreSQL | No aplica a este endpoint. |
| Evidencia en MongoDB | `db.eventos.find({servicio:'devoluciones'}).sort({fecha:-1}).limit(2)` (RNF-23). |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/devoluciones.md#040_devoluciones_get_id_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 40 | detalle 200 exitoso | JSON | Cliente (dueno de la compra) | 200 | - | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#040_devoluciones_get_id_200)` |
| 50 | detalle 200 historial completo | JSON | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#050_devoluciones_get_id_200)` |
| 41 | detalle 403 otro cliente | JSON | Cliente distinto al dueno | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#041_devoluciones_get_id_403)` |
| 42 | detalle 404 inexistente | JSON | Analista de Devoluciones | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#042_devoluciones_get_id_404)` |
| 52 | detalle 404 cancelada | JSON | Cliente (dueno de la compra) | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#052_devoluciones_get_id_404)` |

**Errores controlados:**

- **403 `sin_permiso`** - detalle 403 otro cliente: Un cliente no ve la devolucion de otro.
- **404 `no_encontrado`** - detalle 404 inexistente: Registro inexistente.
- **404 `no_encontrado`** - detalle 404 cancelada: La devolucion cancelada ya no se expone por la API.

### PATCH /api/v1/devoluciones/{id}/resolucion

*openapi.yaml:* Autorizar, rechazar o pedir informacion (Analista)

| Campo | Detalle |
|---|---|
| URL y metodo | `PATCH {{devoluciones_url}}/api/v1/devoluciones/{{devolucion_id}}/resolucion` |
| Objetivo | RF-10: pasa a en_revision y notifica al cliente (RF-29). |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_analista}}`; `Content-Type: application/json`; `Accept: application/json` |
| Roles (caso exitoso) | Analista de Devoluciones |
| Codigo HTTP esperado | 200 |
| Explicacion | RF-10: pasa a en_revision y notifica al cliente (RF-29). |
| Evidencia en PostgreSQL | `SELECT estado FROM devoluciones WHERE id = <id>;` y `SELECT tipo, mensaje, url FROM notificaciones ORDER BY id DESC LIMIT 2;` |
| Evidencia en MongoDB | `db.eventos.find({servicio:'devoluciones'}).sort({fecha:-1}).limit(2)` (RNF-23). |
| Evidencia en Redis | No aplica a este endpoint. |

**Body de ejemplo** (caso resolver 200 pedir informacion):

```json
{
  "decision": "informacion",
  "justificacion": "Describe el estado del sello."
}
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/devoluciones.md#045_devoluciones_patch_id_resolucion_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 45 | resolver 200 pedir informacion | JSON | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#045_devoluciones_patch_id_resolucion_200)` |
| 48 | resolver 200 autorizar XML | XML | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#048_devoluciones_patch_id_resolucion_200_xml)` |
| 43 | resolver 403 cliente sin permiso | JSON | Cliente (dueno de la compra) | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#043_devoluciones_patch_id_resolucion_403)` |
| 44 | resolver 400 rechazo sin justificacion | JSON | Analista de Devoluciones | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#044_devoluciones_patch_id_resolucion_400)` |
| 49 | resolver 409 ya resuelta | JSON | Analista de Devoluciones | 409 | estado_no_permite | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#049_devoluciones_patch_id_resolucion_409)` |

**Errores controlados:**

- **403 `sin_permiso`** - resolver 403 cliente sin permiso: RNF-09: solo el Analista de Devoluciones resuelve.
- **400 `validacion`** - resolver 400 rechazo sin justificacion: Rechazar exige justificacion (RN-12).
- **409 `estado_no_permite`** - resolver 409 ya resuelta: Regla de negocio: solo se resuelve lo que sigue en revision.

### PUT /api/v1/devoluciones/{id}

*openapi.yaml:* Corregir la solicitud (Cliente)

| Campo | Detalle |
|---|---|
| URL y metodo | `PUT {{devoluciones_url}}/api/v1/devoluciones/{{devolucion_id}}` |
| Objetivo | El cliente responde corrigiendo su solicitud. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_cliente}}`; `Content-Type: application/json`; `Accept: application/json` |
| Roles (caso exitoso) | Cliente (dueno de la compra) |
| Codigo HTTP esperado | 200 |
| Explicacion | El cliente responde corrigiendo su solicitud. |
| Evidencia en PostgreSQL | No aplica a este endpoint. |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Body de ejemplo** (caso corregir 200 PUT):

```json
{
  "motivo_id": {{motivo_id}},
  "descripcion_problema": "El sello venia abierto desde la tienda.",
  "cantidad_devuelta": 1
}
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/devoluciones.md#046_devoluciones_put_id_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 46 | corregir 200 PUT | JSON | Cliente (dueno de la compra) | 200 | - | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#046_devoluciones_put_id_200)` |

### DELETE /api/v1/devoluciones/{id}

*openapi.yaml:* Cancelar la devolucion (Cliente, eliminacion logica)

| Campo | Detalle |
|---|---|
| URL y metodo | `DELETE {{devoluciones_url}}/api/v1/devoluciones/{{devolucion_xml_id}}` |
| Objetivo | RNF-30: eliminacion logica de una devolucion sin revisar. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_cliente}}`; `Accept: application/json` |
| Roles (caso exitoso) | Cliente (dueno de la compra) |
| Codigo HTTP esperado | 200 |
| Explicacion | RNF-30: eliminacion logica de una devolucion sin revisar. |
| Evidencia en PostgreSQL | `SELECT id, estado, eliminado_en FROM devoluciones WHERE id = <id>;` (eliminado_en con fecha; la fila no se borra). |
| Evidencia en MongoDB | `db.eventos.find({servicio:'devoluciones'}).sort({fecha:-1}).limit(2)` (RNF-23). Debe verse `devolucion_cancelada`. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/devoluciones.md#051_devoluciones_delete_id_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 51 | cancelar 200 exitoso | JSON | Cliente (dueno de la compra) | 200 | - | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#051_devoluciones_delete_id_200)` |
| 47 | cancelar 409 ya revisada | JSON | Cliente (dueno de la compra) | 409 | estado_no_permite | `[ejecucion real](evidencias/ejecuciones/devoluciones.md#047_devoluciones_delete_id_409)` |

**Errores controlados:**

- **409 `estado_no_permite`** - cancelar 409 ya revisada: Regla de negocio: no se cancela lo que un analista ya reviso.

## logistica

**Logistica inversa** - puerto 8003 - coleccion `docs/postman/logistica.postman_collection.json` - Swagger en `/docs` del servicio.

### GET /health

*openapi.yaml:* Salud de PostgreSQL y Redis

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{logistica_url}}/health` |
| Objetivo | RNF-22, RF-32: el servicio responde y reporta el estado de sus dependencias. |
| Parametros | Ninguno |
| Headers | `Accept: application/json` |
| Roles (caso exitoso) | Sin autenticacion |
| Codigo HTTP esperado | 200 |
| Explicacion | RNF-22, RF-32: el servicio responde y reporta el estado de sus dependencias. |
| Evidencia en PostgreSQL | `SELECT 1;` desde el contenedor; el servicio hace la misma comprobacion. |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | `redis-cli PING` responde PONG. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/logistica.md#053_logistica_get_health_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 53 | health 200 | JSON | ninguno | 200 | - | `[ejecucion real](evidencias/ejecuciones/logistica.md#053_logistica_get_health_200)` |

### POST /api/v1/logistica/recolecciones

*openapi.yaml:* Programar recoleccion

| Campo | Detalle |
|---|---|
| URL y metodo | `POST {{logistica_url}}/api/v1/logistica/recolecciones` |
| Objetivo | RF-12: programa la recoleccion de una devolucion autorizada. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_coordinador}}`; `Content-Type: application/json`; `Accept: application/json` |
| Roles (caso exitoso) | Coordinador de Logistica |
| Codigo HTTP esperado | 201 |
| Explicacion | Bloquea la fila de la devolucion (FOR UPDATE), exige estado `autorizada`, inserta la recoleccion y pasa la devolucion a `en_recoleccion`. |
| Evidencia en PostgreSQL | `SELECT id, devolucion_id, estado, fecha_programada, lugar FROM recolecciones ORDER BY id DESC LIMIT 1;` y `SELECT estado FROM devoluciones WHERE id = <devolucion_id>;` -> en_recoleccion. `SELECT accion, entidad, entidad_id, detalle FROM bitacora ORDER BY id DESC LIMIT 3;` (RF-30). |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Body de ejemplo** (caso programar 201 exitoso):

```json
{
  "devolucion_id": {{devolucion_id}},
  "fecha_programada": "{{fecha_futura}}",
  "lugar": "Domicilio del cliente"
}
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/logistica.md#061_logistica_post_recolecciones_201)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 61 | programar 201 exitoso | JSON | Coordinador de Logistica | 201 | - | `[ejecucion real](evidencias/ejecuciones/logistica.md#061_logistica_post_recolecciones_201)` |
| 54 | programar 401 sin token | JSON | ninguno | 401 | no_autenticado | `[ejecucion real](evidencias/ejecuciones/logistica.md#054_logistica_post_recolecciones_401)` |
| 55 | programar 401 token invalido | JSON | Token invalido (cadena sin firma) | 401 | token_invalido | `[ejecucion real](evidencias/ejecuciones/logistica.md#055_logistica_post_recolecciones_401)` |
| 56 | programar 403 centro sin permiso | JSON | Encargado del Centro de Devoluciones | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/logistica.md#056_logistica_post_recolecciones_403)` |
| 57 | programar 400 devolucion_id invalido | JSON | Coordinador de Logistica | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/logistica.md#057_logistica_post_recolecciones_400)` |
| 58 | programar 404 devolucion inexistente | JSON | Coordinador de Logistica | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/logistica.md#058_logistica_post_recolecciones_404)` |
| 59 | programar 400 fecha en el pasado | JSON | Coordinador de Logistica | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/logistica.md#059_logistica_post_recolecciones_400)` |
| 60 | programar 400 XML no cumple XSD | XML | Coordinador de Logistica | 400 | xml_no_cumple_xsd | `[ejecucion real](evidencias/ejecuciones/logistica.md#060_logistica_post_recolecciones_400_xml)` |
| 62 | programar 409 ya programada | JSON | Coordinador de Logistica | 409 | estado_no_permite | `[ejecucion real](evidencias/ejecuciones/logistica.md#062_logistica_post_recolecciones_409)` |

**Errores controlados:**

- **401 `no_autenticado`** - programar 401 sin token: Endpoint protegido sin Authorization.
- **401 `token_invalido`** - programar 401 token invalido: JWT sin firma valida.
- **403 `sin_permiso`** - programar 403 centro sin permiso: Solo el Coordinador de Logistica programa.
- **400 `validacion`** - programar 400 devolucion_id invalido: devolucion_id debe ser entero positivo.
- **404 `no_encontrado`** - programar 404 devolucion inexistente: La devolucion no existe.
- **400 `validacion`** - programar 400 fecha en el pasado: fecha_programada no puede ser anterior a hoy (RF-12).
- **400 `xml_no_cumple_xsd`** - programar 400 XML no cumple XSD: Falta fecha_programada (recoleccion.xsd).
- **409 `estado_no_permite`** - programar 409 ya programada: La devolucion ya no esta autorizada: no se programa dos veces.

### GET /api/v1/logistica/recolecciones

*openapi.yaml:* Listar recolecciones

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{logistica_url}}/api/v1/logistica/recolecciones` |
| Objetivo | Recolecciones con folio, ruta y transportista. |
| Parametros | `estado` (query) |
| Headers | `Authorization: Bearer {{token_coordinador}}`; `Accept: application/json` |
| Roles (caso exitoso) | Coordinador de Logistica, Encargado del Centro de Devoluciones |
| Codigo HTTP esperado | 200 |
| Explicacion | Recolecciones con folio, ruta y transportista. |
| Evidencia en PostgreSQL | `SELECT r.id, d.folio_devolucion, r.estado FROM recolecciones r JOIN devoluciones d ON d.id = r.devolucion_id ORDER BY r.id DESC LIMIT 5;` |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/logistica.md#063_logistica_get_recolecciones_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 63 | listar 200 coordinador | JSON | Coordinador de Logistica | 200 | - | `[ejecucion real](evidencias/ejecuciones/logistica.md#063_logistica_get_recolecciones_200)` |
| 64 | listar 200 centro XML con filtro | XML | Encargado del Centro de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/logistica.md#064_logistica_get_recolecciones_200_xml)` |
| 65 | listar 400 estado invalido | JSON | Coordinador de Logistica | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/logistica.md#065_logistica_get_recolecciones_400)` |
| 66 | listar 403 cliente | JSON | Cliente (dueno de la compra) | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/logistica.md#066_logistica_get_recolecciones_403)` |
| 67 | listar 401 sin token | JSON | ninguno | 401 | no_autenticado | `[ejecucion real](evidencias/ejecuciones/logistica.md#067_logistica_get_recolecciones_401)` |

**Errores controlados:**

- **400 `validacion`** - listar 400 estado invalido: Estado de recoleccion fuera del catalogo.
- **403 `sin_permiso`** - listar 403 cliente: El cliente no consulta recolecciones.
- **401 `no_autenticado`** - listar 401 sin token: Endpoint protegido sin Authorization.

### PATCH /api/v1/logistica/recolecciones/{id}/asignacion

*openapi.yaml:* Asignar ruta y transportista

| Campo | Detalle |
|---|---|
| URL y metodo | `PATCH {{logistica_url}}/api/v1/logistica/recolecciones/{{recoleccion_id}}/asignacion` |
| Objetivo | RF-13: asigna ruta y transportista (asignacion.xsd). |
| Parametros | `recoleccion_id` (path) |
| Headers | `Authorization: Bearer {{token_coordinador}}`; `Content-Type: application/xml`; `Accept: application/xml` |
| Roles (caso exitoso) | Coordinador de Logistica |
| Codigo HTTP esperado | 200 |
| Explicacion | RF-13: asigna ruta y transportista (asignacion.xsd). |
| Evidencia en PostgreSQL | `SELECT id, estado, ruta_id, transportista_id FROM recolecciones WHERE id = <id>;` `SELECT accion, entidad, entidad_id, detalle FROM bitacora ORDER BY id DESC LIMIT 3;` (RF-30). |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Body de ejemplo** (caso asignar 200 XML):

```xml
<asignacion>
  <ruta_id>{{ruta_id}}</ruta_id>
  <transportista_id>{{transportista_id}}</transportista_id>
</asignacion>
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/logistica.md#072_logistica_patch_recolecciones_id_asignacion_200_xml)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 72 | asignar 200 XML | XML | Coordinador de Logistica | 200 | - | `[ejecucion real](evidencias/ejecuciones/logistica.md#072_logistica_patch_recolecciones_id_asignacion_200_xml)` |
| 68 | asignar 403 centro sin permiso | JSON | Encargado del Centro de Devoluciones | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/logistica.md#068_logistica_patch_recolecciones_id_asignacion_403)` |
| 69 | asignar 400 ruta invalida | JSON | Coordinador de Logistica | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/logistica.md#069_logistica_patch_recolecciones_id_asignacion_400)` |
| 70 | asignar 400 ruta inexistente | JSON | Coordinador de Logistica | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/logistica.md#070_logistica_patch_recolecciones_id_asignacion_400)` |
| 71 | asignar 404 recoleccion inexistente | JSON | Coordinador de Logistica | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/logistica.md#071_logistica_patch_recolecciones_id_asignacion_404)` |
| 76 | asignar 409 ya inicio | JSON | Coordinador de Logistica | 409 | estado_no_permite | `[ejecucion real](evidencias/ejecuciones/logistica.md#076_logistica_patch_recolecciones_id_asignacion_409)` |

**Errores controlados:**

- **403 `sin_permiso`** - asignar 403 centro sin permiso: Solo el Coordinador asigna.
- **400 `validacion`** - asignar 400 ruta invalida: ruta_id debe ser entero positivo.
- **400 `validacion`** - asignar 400 ruta inexistente: La ruta no existe o esta inactiva.
- **404 `no_encontrado`** - asignar 404 recoleccion inexistente: La recoleccion no existe.
- **409 `estado_no_permite`** - asignar 409 ya inicio: Una recoleccion en transito ya no se reasigna.

### PATCH /api/v1/logistica/recolecciones/{id}/estado

*openapi.yaml:* Avanzar estado de recoleccion

| Campo | Detalle |
|---|---|
| URL y metodo | `PATCH {{logistica_url}}/api/v1/logistica/recolecciones/{{recoleccion_id}}/estado` |
| Objetivo | RF-14: el producto va en camino. |
| Parametros | `recoleccion_id` (path) |
| Headers | `Authorization: Bearer {{token_coordinador}}`; `Content-Type: application/json`; `Accept: application/json` |
| Roles (caso exitoso) | Coordinador de Logistica |
| Codigo HTTP esperado | 200 |
| Explicacion | RF-14: el producto va en camino. |
| Evidencia en PostgreSQL | `SELECT id, estado FROM recolecciones WHERE id = <id>;` `SELECT accion, entidad, entidad_id, detalle FROM bitacora ORDER BY id DESC LIMIT 3;` (RF-30). |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Body de ejemplo** (caso estado 200 en_transito):

```json
{
  "estado": "en_transito"
}
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/logistica.md#075_logistica_patch_recolecciones_id_estado_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 75 | estado 200 en_transito | JSON | Coordinador de Logistica | 200 | - | `[ejecucion real](evidencias/ejecuciones/logistica.md#075_logistica_patch_recolecciones_id_estado_200)` |
| 77 | estado 200 completada XML | XML | Coordinador de Logistica | 200 | - | `[ejecucion real](evidencias/ejecuciones/logistica.md#077_logistica_patch_recolecciones_id_estado_200_xml)` |
| 73 | estado 409 transicion invalida | JSON | Coordinador de Logistica | 409 | transicion_invalida | `[ejecucion real](evidencias/ejecuciones/logistica.md#073_logistica_patch_recolecciones_id_estado_409)` |
| 74 | estado 404 inexistente | JSON | Coordinador de Logistica | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/logistica.md#074_logistica_patch_recolecciones_id_estado_404)` |

**Errores controlados:**

- **409 `transicion_invalida`** - estado 409 transicion invalida: De asignada solo se pasa a en_transito o fallida.
- **404 `no_encontrado`** - estado 404 inexistente: La recoleccion no existe.

### POST /api/v1/logistica/recepciones

*openapi.yaml:* Confirmar recepcion

| Campo | Detalle |
|---|---|
| URL y metodo | `POST {{logistica_url}}/api/v1/logistica/recepciones` |
| Objetivo | RF-15: el centro confirma que recibio el producto. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_centro}}`; `Content-Type: application/json`; `Accept: application/json` |
| Roles (caso exitoso) | Encargado del Centro de Devoluciones |
| Codigo HTTP esperado | 201 |
| Explicacion | Exige recoleccion `completada`, inserta la recepcion y pasa la devolucion a `recibida`. |
| Evidencia en PostgreSQL | `SELECT id, devolucion_id, coincide_expediente, fecha_recepcion FROM recepciones ORDER BY id DESC LIMIT 1;` y `SELECT estado FROM devoluciones WHERE id = <devolucion_id>;` -> recibida. `SELECT accion, entidad, entidad_id, detalle FROM bitacora ORDER BY id DESC LIMIT 3;` (RF-30). |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Body de ejemplo** (caso recepcion 201 exitoso):

```json
{
  "devolucion_id": {{devolucion_id}},
  "coincide_expediente": true
}
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/logistica.md#082_logistica_post_recepciones_201)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 82 | recepcion 201 exitoso | JSON | Encargado del Centro de Devoluciones | 201 | - | `[ejecucion real](evidencias/ejecuciones/logistica.md#082_logistica_post_recepciones_201)` |
| 78 | recepcion 403 coordinador | JSON | Coordinador de Logistica | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/logistica.md#078_logistica_post_recepciones_403)` |
| 79 | recepcion 400 devolucion invalida | JSON | Encargado del Centro de Devoluciones | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/logistica.md#079_logistica_post_recepciones_400)` |
| 80 | recepcion 404 inexistente | JSON | Encargado del Centro de Devoluciones | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/logistica.md#080_logistica_post_recepciones_404)` |
| 81 | recepcion 400 booleano invalido | JSON | Encargado del Centro de Devoluciones | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/logistica.md#081_logistica_post_recepciones_400)` |
| 83 | recepcion 409 duplicada | JSON | Encargado del Centro de Devoluciones | 409 | recepcion_duplicada | `[ejecucion real](evidencias/ejecuciones/logistica.md#083_logistica_post_recepciones_409)` |

**Errores controlados:**

- **403 `sin_permiso`** - recepcion 403 coordinador: Solo el Encargado del Centro recibe.
- **400 `validacion`** - recepcion 400 devolucion invalida: devolucion_id debe ser entero positivo.
- **404 `no_encontrado`** - recepcion 404 inexistente: La devolucion no existe.
- **400 `validacion`** - recepcion 400 booleano invalido: coincide_expediente debe ser booleano.
- **409 `recepcion_duplicada`** - recepcion 409 duplicada: La devolucion ya fue recibida.

## inspecciones

**Inspecciones y disposicion** - puerto 8004 - coleccion `docs/postman/inspecciones.postman_collection.json` - Swagger en `/docs` del servicio.

### GET /health

*openapi.yaml:* Salud de PostgreSQL Redis y MongoDB

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{inspecciones_url}}/health` |
| Objetivo | RNF-22, RF-32: el servicio responde y reporta el estado de sus dependencias. |
| Parametros | Ninguno |
| Headers | `Accept: application/json` |
| Roles (caso exitoso) | Sin autenticacion |
| Codigo HTTP esperado | 200 |
| Explicacion | RNF-22, RF-32: el servicio responde y reporta el estado de sus dependencias. |
| Evidencia en PostgreSQL | `SELECT 1;` desde el contenedor; el servicio hace la misma comprobacion. |
| Evidencia en MongoDB | `mongosh --eval "db.runCommand({ping:1})"` |
| Evidencia en Redis | `redis-cli PING` responde PONG. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/inspecciones.md#084_inspecciones_get_health_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 84 | health 200 | JSON | ninguno | 200 | - | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#084_inspecciones_get_health_200)` |

### POST /api/v1/inspecciones

*openapi.yaml:* Registrar inspeccion en PostgreSQL y MongoDB

| Campo | Detalle |
|---|---|
| URL y metodo | `POST {{inspecciones_url}}/api/v1/inspecciones` |
| Objetivo | RF-16, RF-17: inspeccion con detalle en MongoDB y referencia en PostgreSQL. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_inspector}}`; `Content-Type: application/json`; `Accept: application/json` |
| Roles (caso exitoso) | Inspector |
| Codigo HTTP esperado | 201 |
| Explicacion | Inserta el documento en MongoDB (`inspecciones`), la referencia en `inspecciones_ref` y pasa la devolucion a `en_inspeccion`. Aptitud: sin danos, sin caducidad vencida, cadena de frio integra y <= 30 min fuera de refrigeracion (RN-05, RN-06). |
| Evidencia en PostgreSQL | `SELECT id, devolucion_id, resultado_general, mongo_doc_id, apto_para_inventario FROM inspecciones_ref ORDER BY id DESC LIMIT 1;` y `SELECT estado FROM devoluciones WHERE id = <devolucion_id>;` -> en_inspeccion. `SELECT accion, entidad, entidad_id, detalle FROM bitacora ORDER BY id DESC LIMIT 3;` (RF-30). |
| Evidencia en MongoDB | `db.inspecciones.find({devolucion_id: <id>}).pretty()` (condiciones, resultado.apto_para_inventario) y `db.inspecciones.getIndexes()` (indice unico uq_inspeccion_devolucion). |
| Evidencia en Redis | No aplica a este endpoint. |

**Body de ejemplo** (caso registrar 201 exitoso):

```json
{
  "devolucion_id": {{devolucion_id}},
  "estado_empaque": "Empaque intacto, sello cerrado",
  "danos": false,
  "caducidad_vencida": false,
  "cadena_frio_rota": false,
  "minutos_fuera_refrigeracion": 10,
  "temperatura_recepcion": 4.5,
  "observaciones": "Inspeccion de prueba desde Postman"
}
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/inspecciones.md#092_inspecciones_post_raiz_201)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 92 | registrar 201 exitoso | JSON | Inspector | 201 | - | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#092_inspecciones_post_raiz_201)` |
| 85 | registrar 401 sin token | JSON | ninguno | 401 | no_autenticado | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#085_inspecciones_post_raiz_401)` |
| 86 | registrar 403 analista | JSON | Analista de Devoluciones | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#086_inspecciones_post_raiz_403)` |
| 87 | registrar 400 devolucion_id invalido | JSON | Inspector | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#087_inspecciones_post_raiz_400)` |
| 88 | registrar 404 devolucion inexistente | JSON | Inspector | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#088_inspecciones_post_raiz_404)` |
| 89 | registrar 400 XML no cumple XSD | XML | Inspector | 400 | xml_no_cumple_xsd | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#089_inspecciones_post_raiz_400_xml)` |
| 90 | registrar 400 empaque sin describir | JSON | Inspector | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#090_inspecciones_post_raiz_400)` |
| 91 | registrar 400 booleano invalido | JSON | Inspector | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#091_inspecciones_post_raiz_400)` |
| 93 | registrar 409 duplicada | JSON | Inspector | 409 | inspeccion_duplicada | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#093_inspecciones_post_raiz_409)` |

**Errores controlados:**

- **401 `no_autenticado`** - registrar 401 sin token: Endpoint protegido sin Authorization.
- **403 `sin_permiso`** - registrar 403 analista: Solo el Inspector registra la inspeccion.
- **400 `validacion`** - registrar 400 devolucion_id invalido: devolucion_id debe ser positivo.
- **404 `no_encontrado`** - registrar 404 devolucion inexistente: La devolucion no existe.
- **400 `xml_no_cumple_xsd`** - registrar 400 XML no cumple XSD: Faltan campos obligatorios (inspeccion.xsd).
- **400 `validacion`** - registrar 400 empaque sin describir: estado_empaque exige al menos 3 caracteres.
- **400 `validacion`** - registrar 400 booleano invalido: danos debe ser booleano.
- **409 `inspeccion_duplicada`** - registrar 409 duplicada: La devolucion ya tiene inspeccion.

### GET /api/v1/inspecciones/{id}

*openapi.yaml:* Consultar referencia y documento MongoDB

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{inspecciones_url}}/api/v1/inspecciones/{{devolucion_id}}` |
| Objetivo | Referencia (PostgreSQL) y detalle (MongoDB) de la inspeccion. |
| Parametros | `devolucion_id` (path) |
| Headers | `Authorization: Bearer {{token_inspector}}`; `Accept: application/json` |
| Roles (caso exitoso) | Analista de Devoluciones, Inspector |
| Codigo HTTP esperado | 200 |
| Explicacion | Referencia (PostgreSQL) y detalle (MongoDB) de la inspeccion. |
| Evidencia en PostgreSQL | No aplica a este endpoint. |
| Evidencia en MongoDB | `db.inspecciones.findOne({devolucion_id: <id>})` coincide con `detalle`. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/inspecciones.md#094_inspecciones_get_id_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 94 | detalle 200 inspector | JSON | Inspector | 200 | - | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#094_inspecciones_get_id_200)` |
| 95 | detalle 200 analista XML | XML | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#095_inspecciones_get_id_200_xml)` |
| 96 | detalle 403 cliente | JSON | Cliente (dueno de la compra) | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#096_inspecciones_get_id_403)` |
| 97 | detalle 404 inexistente | JSON | Inspector | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#097_inspecciones_get_id_404)` |
| 98 | detalle 401 token invalido | JSON | Token invalido (cadena sin firma) | 401 | token_invalido | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#098_inspecciones_get_id_401)` |

**Errores controlados:**

- **403 `sin_permiso`** - detalle 403 cliente: El cliente no consulta inspecciones.
- **404 `no_encontrado`** - detalle 404 inexistente: No hay inspeccion para esa devolucion.
- **401 `token_invalido`** - detalle 401 token invalido: JWT sin firma valida.

### PATCH /api/v1/inspecciones/{id}

*openapi.yaml:* Actualizar detalle semiestructurado

| Campo | Detalle |
|---|---|
| URL y metodo | `PATCH {{inspecciones_url}}/api/v1/inspecciones/{{devolucion_id}}` |
| Objetivo | Actualiza observaciones en MongoDB; XML (inspeccion_actualizacion.xsd). |
| Parametros | `devolucion_id` (path) |
| Headers | `Authorization: Bearer {{token_inspector}}`; `Content-Type: application/xml`; `Accept: application/xml` |
| Roles (caso exitoso) | Inspector |
| Codigo HTTP esperado | 200 |
| Explicacion | Actualiza observaciones en MongoDB; XML (inspeccion_actualizacion.xsd). |
| Evidencia en PostgreSQL | Bitacora `inspeccion_actualizada`: `SELECT accion, entidad, entidad_id, detalle FROM bitacora ORDER BY id DESC LIMIT 3;` (RF-30). |
| Evidencia en MongoDB | `db.inspecciones.findOne({devolucion_id: <id>}, {observaciones: 1})` muestra el texto nuevo. |
| Evidencia en Redis | No aplica a este endpoint. |

**Body de ejemplo** (caso actualizar 200 XML):

```xml
<inspeccion_actualizacion>
  <observaciones>Observacion actualizada desde Postman</observaciones>
</inspeccion_actualizacion>
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/inspecciones.md#102_inspecciones_patch_id_200_xml)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 102 | actualizar 200 XML | XML | Inspector | 200 | - | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#102_inspecciones_patch_id_200_xml)` |
| 99 | actualizar 400 sin cambios | JSON | Inspector | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#099_inspecciones_patch_id_400)` |
| 100 | actualizar 403 analista | JSON | Analista de Devoluciones | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#100_inspecciones_patch_id_403)` |
| 101 | actualizar 404 inexistente | JSON | Inspector | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#101_inspecciones_patch_id_404)` |

**Errores controlados:**

- **400 `validacion`** - actualizar 400 sin cambios: No hay campos actualizables.
- **403 `sin_permiso`** - actualizar 403 analista: Solo el Inspector actualiza.
- **404 `no_encontrado`** - actualizar 404 inexistente: No hay inspeccion para actualizar.

### POST /api/v1/inspecciones/{id}/disposicion

*openapi.yaml:* Determinar destino del producto

| Campo | Detalle |
|---|---|
| URL y metodo | `POST {{inspecciones_url}}/api/v1/inspecciones/{{devolucion_id}}/disposicion` |
| Objetivo | RF-18: destino del producto (disposicion.xsd). Guarda disposicion_id. |
| Parametros | `devolucion_id` (path) |
| Headers | `Authorization: Bearer {{token_analista}}`; `Content-Type: application/xml`; `Accept: application/xml` |
| Roles (caso exitoso) | Analista de Devoluciones |
| Codigo HTTP esperado | 201 |
| Explicacion | Exige inspeccion previa (RN-07) y, para `inventario`, que el producto sea apto. Pasa la devolucion a `resuelta`. |
| Evidencia en PostgreSQL | `SELECT id, devolucion_id, destino, justificacion FROM disposiciones ORDER BY id DESC LIMIT 1;` y `SELECT estado FROM devoluciones WHERE id = <devolucion_id>;` -> resuelta. `SELECT accion, entidad, entidad_id, detalle FROM bitacora ORDER BY id DESC LIMIT 3;` (RF-30). |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Body de ejemplo** (caso disposicion 201 XML):

```xml
<disposicion>
  <destino>inventario</destino>
  <justificacion>Producto apto, regresa a inventario.</justificacion>
</disposicion>
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/inspecciones.md#106_inspecciones_post_id_disposicion_201_xml)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 106 | disposicion 201 XML | XML | Analista de Devoluciones | 201 | - | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#106_inspecciones_post_id_disposicion_201_xml)` |
| 103 | disposicion 403 inspector | JSON | Inspector | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#103_inspecciones_post_id_disposicion_403)` |
| 104 | disposicion 400 destino invalido | JSON | Analista de Devoluciones | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#104_inspecciones_post_id_disposicion_400)` |
| 105 | disposicion 404 inexistente | JSON | Analista de Devoluciones | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#105_inspecciones_post_id_disposicion_404)` |
| 107 | disposicion 409 duplicada | JSON | Analista de Devoluciones | 409 | disposicion_duplicada | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#107_inspecciones_post_id_disposicion_409)` |

**Errores controlados:**

- **403 `sin_permiso`** - disposicion 403 inspector: Solo el Analista decide el destino.
- **400 `validacion`** - disposicion 400 destino invalido: Destino fuera del catalogo de siete.
- **404 `no_encontrado`** - disposicion 404 inexistente: La devolucion no existe.
- **409 `disposicion_duplicada`** - disposicion 409 duplicada: Ya existe una disposicion para la devolucion.

### POST /api/v1/inspecciones/inventario/{id}/etiqueta

*openapi.yaml:* Etiquetar producto recuperable

| Campo | Detalle |
|---|---|
| URL y metodo | `POST {{inspecciones_url}}/api/v1/inspecciones/inventario/{{disposicion_id}}/etiqueta` |
| Objetivo | RF-19: etiqueta el producto recuperable. |
| Parametros | `disposicion_id` (path) |
| Headers | `Authorization: Bearer {{token_centro}}`; `Content-Type: application/json`; `Accept: application/json` |
| Roles (caso exitoso) | Encargado del Centro de Devoluciones |
| Codigo HTTP esperado | 201 |
| Explicacion | RF-19: etiqueta el producto recuperable. |
| Evidencia en PostgreSQL | `SELECT id, disposicion_id, producto_id, etiqueta_codigo FROM inventario_recuperado ORDER BY id DESC LIMIT 1;` `SELECT accion, entidad, entidad_id, detalle FROM bitacora ORDER BY id DESC LIMIT 3;` (RF-30). |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Body de ejemplo** (caso etiqueta 201 exitoso):

```json
{}
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/inspecciones.md#110_inspecciones_post_inventario_id_etiqueta_201)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 110 | etiqueta 201 exitoso | JSON | Encargado del Centro de Devoluciones | 201 | - | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#110_inspecciones_post_inventario_id_etiqueta_201)` |
| 108 | etiqueta 403 inspector | JSON | Inspector | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#108_inspecciones_post_inventario_id_etiqueta_403)` |
| 109 | etiqueta 404 inexistente | JSON | Encargado del Centro de Devoluciones | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/inspecciones.md#109_inspecciones_post_inventario_id_etiqueta_404)` |

**Errores controlados:**

- **403 `sin_permiso`** - etiqueta 403 inspector: Solo el Encargado del Centro etiqueta.
- **404 `no_encontrado`** - etiqueta 404 inexistente: La disposicion no existe.

## reembolsos_costos

**Reembolsos y costos** - puerto 8005 - coleccion `docs/postman/reembolsos_costos.postman_collection.json` - Swagger en `/docs` del servicio.

### GET /health

*openapi.yaml:* Salud de PostgreSQL y Redis

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{reembolsos_url}}/health` |
| Objetivo | RNF-22, RF-32: el servicio responde y reporta el estado de sus dependencias. |
| Parametros | Ninguno |
| Headers | `Accept: application/json` |
| Roles (caso exitoso) | Sin autenticacion |
| Codigo HTTP esperado | 200 |
| Explicacion | RNF-22, RF-32: el servicio responde y reporta el estado de sus dependencias. |
| Evidencia en PostgreSQL | `SELECT 1;` desde el contenedor; el servicio hace la misma comprobacion. |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | `redis-cli PING` responde PONG. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#111_reembolsos_costos_get_health_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 111 | health 200 | JSON | ninguno | 200 | - | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#111_reembolsos_costos_get_health_200)` |

### POST /api/v1/reembolsos-costos/costos

*openapi.yaml:* Registrar costo por etapa

| Campo | Detalle |
|---|---|
| URL y metodo | `POST {{reembolsos_url}}/api/v1/reembolsos-costos/costos` |
| Objetivo | RF-27: el coordinador registra el costo de transporte. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_coordinador}}`; `Content-Type: application/json`; `Accept: application/json` |
| Roles (caso exitoso) | Coordinador de Logistica, Encargado del Centro de Devoluciones |
| Codigo HTTP esperado | 201 |
| Explicacion | Cada rol solo registra las etapas de su area (RN-04): coordinador=transporte, centro=almacenamiento, inspector=inspeccion, analista=reacondicionamiento/destruccion/otros, reembolsos=reembolso. |
| Evidencia en PostgreSQL | `SELECT id, devolucion_id, etapa, monto, fecha FROM costos ORDER BY id DESC LIMIT 2;` `SELECT accion, entidad, entidad_id, detalle FROM bitacora ORDER BY id DESC LIMIT 3;` (RF-30). |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Body de ejemplo** (caso costo 201 transporte JSON):

```json
{
  "devolucion_id": {{devolucion_id}},
  "etapa": "transporte",
  "monto": 150.5
}
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#120_reembolsos_costos_post_costos_201)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 120 | costo 201 transporte JSON | JSON | Coordinador de Logistica | 201 | - | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#120_reembolsos_costos_post_costos_201)` |
| 121 | costo 201 almacenamiento XML | XML | Encargado del Centro de Devoluciones | 201 | - | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#121_reembolsos_costos_post_costos_201_xml)` |
| 112 | costo 401 sin token | JSON | ninguno | 401 | no_autenticado | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#112_reembolsos_costos_post_costos_401)` |
| 113 | costo 403 cliente | JSON | Cliente (dueno de la compra) | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#113_reembolsos_costos_post_costos_403)` |
| 114 | costo 403 etapa de otro rol | JSON | Coordinador de Logistica | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#114_reembolsos_costos_post_costos_403)` |
| 115 | costo 400 monto negativo | JSON | Coordinador de Logistica | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#115_reembolsos_costos_post_costos_400)` |
| 116 | costo 400 etapa invalida | JSON | Coordinador de Logistica | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#116_reembolsos_costos_post_costos_400)` |
| 117 | costo 400 devolucion_id invalido | JSON | Coordinador de Logistica | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#117_reembolsos_costos_post_costos_400)` |
| 118 | costo 400 XML no cumple XSD | XML | Coordinador de Logistica | 400 | xml_no_cumple_xsd | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#118_reembolsos_costos_post_costos_400_xml)` |
| 119 | costo 404 devolucion inexistente | JSON | Coordinador de Logistica | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#119_reembolsos_costos_post_costos_404)` |

**Errores controlados:**

- **401 `no_autenticado`** - costo 401 sin token: Endpoint protegido sin Authorization.
- **403 `sin_permiso`** - costo 403 cliente: El cliente no registra costos.
- **403 `sin_permiso`** - costo 403 etapa de otro rol: El coordinador solo registra costos de transporte.
- **400 `validacion`** - costo 400 monto negativo: monto debe ser decimal no negativo.
- **400 `validacion`** - costo 400 etapa invalida: Etapa fuera del catalogo.
- **400 `validacion`** - costo 400 devolucion_id invalido: devolucion_id debe ser entero.
- **400 `xml_no_cumple_xsd`** - costo 400 XML no cumple XSD: Faltan etapa y monto (costo.xsd).
- **404 `no_encontrado`** - costo 404 devolucion inexistente: La devolucion no existe.

### POST /api/v1/reembolsos-costos/reembolsos

*openapi.yaml:* Resolver reembolso con exclusion mutua Redis

| Campo | Detalle |
|---|---|
| URL y metodo | `POST {{reembolsos_url}}/api/v1/reembolsos-costos/reembolsos` |
| Objetivo | RF-20, RF-21: aprueba el reembolso con monto y metodo. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_reembolsos}}`; `Content-Type: application/json`; `Accept: application/json` |
| Roles (caso exitoso) | Encargado de Reembolsos |
| Codigo HTTP esperado | 201 |
| Explicacion | Toma un candado en Redis (SET NX EX 30) para que dos personas no resuelvan a la vez, valida el maximo con Decimal, inserta el reembolso y el costo de etapa `reembolso`, cierra la devolucion si estaba `resuelta` y notifica al cliente. |
| Evidencia en PostgreSQL | `SELECT id, devolucion_id, monto, metodo, estado FROM reembolsos ORDER BY id DESC LIMIT 1;`, `SELECT etapa, monto FROM costos WHERE devolucion_id = <id>;` y `SELECT estado, fecha_cierre FROM devoluciones WHERE id = <id>;` -> cerrada. `SELECT accion, entidad, entidad_id, detalle FROM bitacora ORDER BY id DESC LIMIT 3;` (RF-30). |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | Durante la peticion existe `devoluciones:lock:reembolso:<id>` (TTL <= 30 s); al terminar ya no existe. Para ver el 409 reembolso_en_proceso: `SET devoluciones:lock:reembolso:<id> x NX EX 30` y repetir el POST. |

**Body de ejemplo** (caso reembolso 201 aprobado):

```json
{
  "devolucion_id": {{devolucion_id}},
  "estado": "aprobado",
  "metodo": "transferencia",
  "monto": 1.0
}
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#128_reembolsos_costos_post_reembolsos_201)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 128 | reembolso 201 aprobado | JSON | Encargado de Reembolsos | 201 | - | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#128_reembolsos_costos_post_reembolsos_201)` |
| 122 | reembolso 403 analista | JSON | Analista de Devoluciones | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#122_reembolsos_costos_post_reembolsos_403)` |
| 123 | reembolso 400 estado invalido | JSON | Encargado de Reembolsos | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#123_reembolsos_costos_post_reembolsos_400)` |
| 124 | reembolso 400 metodo invalido | JSON | Encargado de Reembolsos | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#124_reembolsos_costos_post_reembolsos_400)` |
| 125 | reembolso 400 devolucion_id invalido | JSON | Encargado de Reembolsos | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#125_reembolsos_costos_post_reembolsos_400)` |
| 126 | reembolso 404 devolucion inexistente | JSON | Encargado de Reembolsos | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#126_reembolsos_costos_post_reembolsos_404)` |
| 127 | reembolso 409 monto excedido | JSON | Encargado de Reembolsos | 409 | monto_excedido | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#127_reembolsos_costos_post_reembolsos_409)` |
| 129 | reembolso 409 duplicado XML | XML | Encargado de Reembolsos | 409 | reembolso_duplicado | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#129_reembolsos_costos_post_reembolsos_409_xml)` |

**Errores controlados:**

- **403 `sin_permiso`** - reembolso 403 analista: Solo el Encargado de Reembolsos resuelve.
- **400 `validacion`** - reembolso 400 estado invalido: estado debe ser aprobado o rechazado.
- **400 `validacion`** - reembolso 400 metodo invalido: Un reembolso aprobado exige metodo valido.
- **400 `validacion`** - reembolso 400 devolucion_id invalido: devolucion_id debe ser entero positivo.
- **404 `no_encontrado`** - reembolso 404 devolucion inexistente: La devolucion no existe.
- **409 `monto_excedido`** - reembolso 409 monto excedido: RN-03: el reembolso no puede superar el valor devuelto.
- **409 `reembolso_duplicado`** - reembolso 409 duplicado XML: La devolucion ya tiene un reembolso valido; error en XML.

### GET /api/v1/reembolsos-costos/reembolsos

*openapi.yaml:* Listar reembolsos

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{reembolsos_url}}/api/v1/reembolsos-costos/reembolsos` |
| Objetivo | Ultimos 100 reembolsos. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_reembolsos}}`; `Accept: application/json` |
| Roles (caso exitoso) | Analista de Devoluciones, Encargado de Reembolsos |
| Codigo HTTP esperado | 200 |
| Explicacion | Ultimos 100 reembolsos. |
| Evidencia en PostgreSQL | No aplica a este endpoint. |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#130_reembolsos_costos_get_reembolsos_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 130 | reembolsos 200 lista | JSON | Encargado de Reembolsos | 200 | - | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#130_reembolsos_costos_get_reembolsos_200)` |
| 131 | reembolsos 200 analista XML | XML | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#131_reembolsos_costos_get_reembolsos_200_xml)` |
| 132 | reembolsos 403 cliente | JSON | Cliente (dueno de la compra) | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#132_reembolsos_costos_get_reembolsos_403)` |
| 133 | reembolsos 401 token invalido | JSON | Token invalido (cadena sin firma) | 401 | token_invalido | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#133_reembolsos_costos_get_reembolsos_401)` |

**Errores controlados:**

- **403 `sin_permiso`** - reembolsos 403 cliente: El cliente no lista reembolsos.
- **401 `token_invalido`** - reembolsos 401 token invalido: JWT sin firma valida.

### GET /api/v1/reembolsos-costos/costos/{id}

*openapi.yaml:* Desglose y total de costos

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{reembolsos_url}}/api/v1/reembolsos-costos/costos/{{devolucion_id}}` |
| Objetivo | RF-27: costo por etapa y total de la devolucion. |
| Parametros | `devolucion_id` (path) |
| Headers | `Authorization: Bearer {{token_reembolsos}}`; `Accept: application/json` |
| Roles (caso exitoso) | Analista de Devoluciones, Encargado de Reembolsos |
| Codigo HTTP esperado | 200 |
| Explicacion | RF-27: costo por etapa y total de la devolucion. |
| Evidencia en PostgreSQL | `SELECT etapa, SUM(monto) FROM costos WHERE devolucion_id = <id> GROUP BY etapa;` y `SELECT * FROM vista_costo_devolucion WHERE devolucion_id = <id>;` |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#134_reembolsos_costos_get_costos_id_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 134 | costos 200 desglose | JSON | Encargado de Reembolsos | 200 | - | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#134_reembolsos_costos_get_costos_id_200)` |
| 135 | costos 200 analista XML | XML | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#135_reembolsos_costos_get_costos_id_200_xml)` |
| 136 | costos 403 centro | JSON | Encargado del Centro de Devoluciones | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#136_reembolsos_costos_get_costos_id_403)` |
| 137 | costos 404 devolucion inexistente | JSON | Encargado de Reembolsos | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/reembolsos_costos.md#137_reembolsos_costos_get_costos_id_404)` |

**Errores controlados:**

- **403 `sin_permiso`** - costos 403 centro: El centro registra costos pero no consulta el total.
- **404 `no_encontrado`** - costos 404 devolucion inexistente: La devolucion no existe.

## ventas_catalogos

**Ventas y catalogos** - puerto 8006 - coleccion `docs/postman/ventas_catalogos.postman_collection.json` - Swagger en `/docs` del servicio.

### GET /health

*openapi.yaml:* Estado del servicio

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{ventas_url}}/health` |
| Objetivo | RNF-22, RF-32: el servicio responde y reporta el estado de sus dependencias. |
| Parametros | Ninguno |
| Headers | `Accept: application/json` |
| Roles (caso exitoso) | Sin autenticacion |
| Codigo HTTP esperado | 200 |
| Explicacion | RNF-22, RF-32: el servicio responde y reporta el estado de sus dependencias. |
| Evidencia en PostgreSQL | `SELECT 1;` desde el contenedor; el servicio hace la misma comprobacion. |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | `redis-cli PING` responde PONG. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#138_ventas_catalogos_get_health_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 138 | health 200 | JSON | ninguno | 200 | - | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#138_ventas_catalogos_get_health_200)` |

### GET /api/v1/ventas

*openapi.yaml:* Listar ventas, solo las propias para cliente

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{ventas_url}}/api/v1/ventas?pagina=1&por_pagina=5` |
| Objetivo | Un cliente solo ve sus compras. Guarda venta_id para el detalle. |
| Parametros | `pagina` (query), `por_pagina` (query), `q` (query) |
| Headers | `Authorization: Bearer {{token_cliente}}`; `Accept: application/json` |
| Roles (caso exitoso) | Analista de Devoluciones, Cliente (dueno de la compra) |
| Codigo HTTP esperado | 200 |
| Explicacion | Un cliente solo ve sus compras. Guarda venta_id para el detalle. |
| Evidencia en PostgreSQL | `SELECT v.id, v.folio_venta, v.cliente_id FROM ventas v WHERE v.cliente_id = <id> ORDER BY v.fecha_venta DESC LIMIT 5;` |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#139_ventas_catalogos_get_raiz_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 139 | ventas 200 cliente paginado | JSON | Cliente (dueno de la compra) | 200 | - | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#139_ventas_catalogos_get_raiz_200)` |
| 140 | ventas 200 analista XML | XML | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#140_ventas_catalogos_get_raiz_200_xml)` |
| 141 | ventas 400 paginacion invalida | JSON | Cliente (dueno de la compra) | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#141_ventas_catalogos_get_raiz_400)` |
| 142 | ventas 401 sin token | JSON | ninguno | 401 | no_autenticado | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#142_ventas_catalogos_get_raiz_401)` |
| 143 | ventas 401 token invalido | JSON | Token invalido (cadena sin firma) | 401 | token_invalido | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#143_ventas_catalogos_get_raiz_401)` |

**Errores controlados:**

- **400 `validacion`** - ventas 400 paginacion invalida: por_pagina fuera de rango (1 a 100).
- **401 `no_autenticado`** - ventas 401 sin token: Endpoint protegido sin Authorization.
- **401 `token_invalido`** - ventas 401 token invalido: JWT sin firma valida.

### GET /api/v1/ventas/{id}

*openapi.yaml:* Consulta una venta y las líneas con cantidad disponible

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{ventas_url}}/api/v1/ventas/{{venta_id}}` |
| Objetivo | Lineas de la venta con unidades ya devueltas y disponibles. |
| Parametros | `id` (path) |
| Headers | `Authorization: Bearer {{token_cliente}}`; `Accept: application/json` |
| Roles (caso exitoso) | Cliente (dueno de la compra) |
| Codigo HTTP esperado | 200 |
| Explicacion | Lineas de la venta con unidades ya devueltas y disponibles. |
| Evidencia en PostgreSQL | `SELECT vd.id, vd.cantidad, vd.precio_unitario FROM venta_detalle vd WHERE vd.venta_id = <venta_id>;` |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#144_ventas_catalogos_get_id_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 144 | venta 200 detalle | JSON | Cliente (dueno de la compra) | 200 | - | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#144_ventas_catalogos_get_id_200)` |
| 145 | venta 200 detalle XML | XML | Cliente (dueno de la compra) | 200 | - | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#145_ventas_catalogos_get_id_200_xml)` |
| 146 | venta 403 de otro cliente | JSON | Cliente distinto al dueno | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#146_ventas_catalogos_get_id_403)` |
| 147 | venta 404 inexistente | JSON | Analista de Devoluciones | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#147_ventas_catalogos_get_id_404)` |

**Errores controlados:**

- **403 `sin_permiso`** - venta 403 de otro cliente: La venta no pertenece al cliente que consulta.
- **404 `no_encontrado`** - venta 404 inexistente: Venta inexistente.

### GET /api/v1/catalogos

*openapi.yaml:* Tipos de catálogos disponibles

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{ventas_url}}/api/v1/catalogos` |
| Objetivo | Nombres de los siete catalogos. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_admin}}`; `Accept: application/json` |
| Roles (caso exitoso) | Administrador |
| Codigo HTTP esperado | 200 |
| Explicacion | Nombres de los siete catalogos. |
| Evidencia en PostgreSQL | No aplica a este endpoint. |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#148_ventas_catalogos_get_catalogos_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 148 | catalogos 200 lista | JSON | Administrador | 200 | - | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#148_ventas_catalogos_get_catalogos_200)` |
| 149 | catalogos 403 cliente | JSON | Cliente (dueno de la compra) | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#149_ventas_catalogos_get_catalogos_403)` |

**Errores controlados:**

- **403 `sin_permiso`** - catalogos 403 cliente: Solo Administrador y Analista listan catalogos.

### GET /api/v1/catalogos/{nombre}

*openapi.yaml:* Listar registros (el cliente solo ve motivos activos)

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{ventas_url}}/api/v1/catalogos/motivos?pagina=1&por_pagina=5` |
| Objetivo | El cliente solo lee motivos (para solicitar devoluciones). Guarda un id para el detalle. |
| Parametros | `nombre` (path), `pagina` (query), `por_pagina` (query) |
| Headers | `Authorization: Bearer {{token_cliente}}`; `Accept: application/json` |
| Roles (caso exitoso) | Analista de Devoluciones, Cliente (dueno de la compra) |
| Codigo HTTP esperado | 200 |
| Explicacion | El cliente solo lee motivos (para solicitar devoluciones). Guarda un id para el detalle. |
| Evidencia en PostgreSQL | `SELECT id, nombre, activo FROM motivos ORDER BY id DESC LIMIT 5;` |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#150_ventas_catalogos_get_catalogos_nombre_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 150 | catalogo motivos 200 cliente | JSON | Cliente (dueno de la compra) | 200 | - | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#150_ventas_catalogos_get_catalogos_nombre_200)` |
| 151 | catalogo motivos 200 XML con inactivos | XML | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#151_ventas_catalogos_get_catalogos_nombre_200_xml)` |
| 154 | catalogo rutas 200 | JSON | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#154_ventas_catalogos_get_catalogos_nombre_200)` |
| 155 | catalogo transportistas 200 | JSON | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#155_ventas_catalogos_get_catalogos_nombre_200)` |
| 152 | catalogo productos 403 cliente | JSON | Cliente (dueno de la compra) | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#152_ventas_catalogos_get_catalogos_nombre_403)` |
| 153 | catalogo inexistente 404 | JSON | Administrador | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#153_ventas_catalogos_get_catalogos_nombre_404)` |

**Errores controlados:**

- **403 `sin_permiso`** - catalogo productos 403 cliente: El cliente no consulta otros catalogos.
- **404 `no_encontrado`** - catalogo inexistente 404: El nombre no esta en la lista blanca de catalogos.

### GET /api/v1/catalogos/{nombre}/{registro_id}

*openapi.yaml:* Detalle de un registro

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{ventas_url}}/api/v1/catalogos/motivos/{{catalogo_registro_id}}` |
| Objetivo | Un registro del catalogo. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_cliente}}`; `Accept: application/json` |
| Roles (caso exitoso) | Cliente (dueno de la compra) |
| Codigo HTTP esperado | 200 |
| Explicacion | Un registro del catalogo. |
| Evidencia en PostgreSQL | No aplica a este endpoint. |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#156_ventas_catalogos_get_catalogos_nombre_registro_id_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 156 | registro 200 detalle | JSON | Cliente (dueno de la compra) | 200 | - | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#156_ventas_catalogos_get_catalogos_nombre_registro_id_200)` |
| 157 | registro 404 inexistente | JSON | Cliente (dueno de la compra) | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#157_ventas_catalogos_get_catalogos_nombre_registro_id_404)` |

**Errores controlados:**

- **404 `no_encontrado`** - registro 404 inexistente: Registro inexistente.

### POST /api/v1/catalogos/{nombre}

*openapi.yaml:* Crear catálogo; administrador

| Campo | Detalle |
|---|---|
| URL y metodo | `POST {{ventas_url}}/api/v1/catalogos/motivos` |
| Objetivo | Alta de un motivo de prueba. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_admin}}`; `Content-Type: application/json`; `Accept: application/json` |
| Roles (caso exitoso) | Administrador |
| Codigo HTTP esperado | 201 |
| Explicacion | Valida contra la lista blanca de campos del catalogo y inserta con SQL parametrizado (RNF-11). |
| Evidencia en PostgreSQL | `SELECT id, nombre, activo FROM motivos ORDER BY id DESC LIMIT 2;` y `SELECT accion, entidad, entidad_id, detalle FROM bitacora ORDER BY id DESC LIMIT 3;` (RF-30). |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Body de ejemplo** (caso alta 201 JSON):

```json
{
  "nombre": "Motivo Postman {{$timestamp}}",
  "descripcion": "Alta de prueba desde Postman"
}
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#158_ventas_catalogos_post_catalogos_nombre_201)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 158 | alta 201 JSON | JSON | Administrador | 201 | - | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#158_ventas_catalogos_post_catalogos_nombre_201)` |
| 159 | alta 201 XML | XML | Administrador | 201 | - | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#159_ventas_catalogos_post_catalogos_nombre_201_xml)` |
| 160 | alta 400 sin nombre | JSON | Administrador | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#160_ventas_catalogos_post_catalogos_nombre_400)` |
| 161 | alta 401 sin token | JSON | ninguno | 401 | no_autenticado | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#161_ventas_catalogos_post_catalogos_nombre_401)` |
| 162 | alta 403 analista | JSON | Analista de Devoluciones | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#162_ventas_catalogos_post_catalogos_nombre_403)` |
| 163 | alta 404 catalogo inexistente | JSON | Administrador | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#163_ventas_catalogos_post_catalogos_nombre_404)` |
| 164 | alta 409 referencia inactiva | JSON | Administrador | 409 | referencia_inactiva | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#164_ventas_catalogos_post_catalogos_nombre_409)` |

**Errores controlados:**

- **400 `validacion`** - alta 400 sin nombre: Campo obligatorio vacio.
- **401 `no_autenticado`** - alta 401 sin token: Endpoint protegido sin Authorization.
- **403 `sin_permiso`** - alta 403 analista: Solo el Administrador da de alta.
- **404 `no_encontrado`** - alta 404 catalogo inexistente: Catalogo fuera de la lista blanca.
- **409 `referencia_inactiva`** - alta 409 referencia inactiva: El producto apunta a un proveedor que no existe o esta inactivo.

### PUT /api/v1/catalogos/{nombre}/{registro_id}

*openapi.yaml:* Reemplazar campos permitidos del registro; administrador

| Campo | Detalle |
|---|---|
| URL y metodo | `PUT {{ventas_url}}/api/v1/catalogos/motivos/{{catalogo_registro_id}}` |
| Objetivo | Reemplaza los campos del registro. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_admin}}`; `Content-Type: application/json`; `Accept: application/json` |
| Roles (caso exitoso) | Administrador |
| Codigo HTTP esperado | 200 |
| Explicacion | Reemplaza los campos del registro. |
| Evidencia en PostgreSQL | `SELECT id, nombre FROM motivos WHERE id = <id>;` (nombre nuevo). |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Body de ejemplo** (caso edicion 200 PUT):

```json
{
  "nombre": "Motivo editado {{$timestamp}}",
  "descripcion": "Editado desde Postman"
}
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#165_ventas_catalogos_put_catalogos_nombre_registro_id_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 165 | edicion 200 PUT | JSON | Administrador | 200 | - | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#165_ventas_catalogos_put_catalogos_nombre_registro_id_200)` |
| 166 | edicion 400 tipo invalido | JSON | Administrador | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#166_ventas_catalogos_put_catalogos_nombre_registro_id_400)` |
| 167 | edicion 404 inexistente | JSON | Administrador | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#167_ventas_catalogos_put_catalogos_nombre_registro_id_404)` |

**Errores controlados:**

- **400 `validacion`** - edicion 400 tipo invalido: El nombre debe ser texto.
- **404 `no_encontrado`** - edicion 404 inexistente: Registro inexistente.

### PATCH /api/v1/catalogos/{nombre}/{id}/estado

*openapi.yaml:* Establecer estado booleano activo

| Campo | Detalle |
|---|---|
| URL y metodo | `PATCH {{ventas_url}}/api/v1/catalogos/motivos/{{catalogo_registro_id}}/estado` |
| Objetivo | Activa o desactiva un registro. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_admin}}`; `Content-Type: application/json`; `Accept: application/json` |
| Roles (caso exitoso) | Administrador |
| Codigo HTTP esperado | 200 |
| Explicacion | Activa o desactiva un registro. |
| Evidencia en PostgreSQL | `SELECT id, activo FROM motivos WHERE id = <id>;` -> f. |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Body de ejemplo** (caso estado 200 desactivar):

```json
{
  "activo": false
}
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#168_ventas_catalogos_patch_catalogos_nombre_id_estado_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 168 | estado 200 desactivar | JSON | Administrador | 200 | - | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#168_ventas_catalogos_patch_catalogos_nombre_id_estado_200)` |
| 169 | estado 400 booleano invalido | JSON | Administrador | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#169_ventas_catalogos_patch_catalogos_nombre_id_estado_400)` |
| 170 | estado 404 inexistente | JSON | Administrador | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#170_ventas_catalogos_patch_catalogos_nombre_id_estado_404)` |

**Errores controlados:**

- **400 `validacion`** - estado 400 booleano invalido: activo debe ser booleano.
- **404 `no_encontrado`** - estado 404 inexistente: Registro inexistente.

### DELETE /api/v1/catalogos/{nombre}/{registro_id}

*openapi.yaml:* Desactivar sin borrar historia

| Campo | Detalle |
|---|---|
| URL y metodo | `DELETE {{ventas_url}}/api/v1/catalogos/motivos/{{catalogo_xml_id}}` |
| Objetivo | Baja logica del registro creado en XML. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_admin}}`; `Accept: application/json` |
| Roles (caso exitoso) | Administrador |
| Codigo HTTP esperado | 200 |
| Explicacion | Baja logica del registro creado en XML. |
| Evidencia en PostgreSQL | `SELECT id, activo FROM motivos WHERE id = <id>;` -> f (la fila sigue existiendo). |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#171_ventas_catalogos_delete_catalogos_nombre_registro_id_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 171 | baja 200 desactivar | JSON | Administrador | 200 | - | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#171_ventas_catalogos_delete_catalogos_nombre_registro_id_200)` |
| 172 | baja 404 inexistente | JSON | Administrador | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/ventas_catalogos.md#172_ventas_catalogos_delete_catalogos_nombre_registro_id_404)` |

**Errores controlados:**

- **404 `no_encontrado`** - baja 404 inexistente: Registro inexistente.

## evidencias

**Evidencias** - puerto 8007 - coleccion `docs/postman/evidencias.postman_collection.json` - Swagger en `/docs` del servicio.

### GET /health

*openapi.yaml:* Estado PostgreSQL, Redis, MongoDB y volumen

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{evidencias_url}}/health` |
| Objetivo | RNF-22, RF-32: el servicio responde y reporta el estado de sus dependencias. |
| Parametros | Ninguno |
| Headers | `Accept: application/json` |
| Roles (caso exitoso) | Sin autenticacion |
| Codigo HTTP esperado | 200 |
| Explicacion | RNF-22, RF-32: el servicio responde y reporta el estado de sus dependencias. |
| Evidencia en PostgreSQL | `SELECT 1;` desde el contenedor; el servicio hace la misma comprobacion. |
| Evidencia en MongoDB | `mongosh --eval "db.runCommand({ping:1})"` |
| Evidencia en Redis | `redis-cli PING` responde PONG. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/evidencias.md#173_evidencias_get_health_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 173 | health 200 | JSON | ninguno | 200 | - | `[ejecucion real](evidencias/ejecuciones/evidencias.md#173_evidencias_get_health_200)` |

### POST /api/v1/evidencias

*openapi.yaml:* Adjunta archivo privado o comentario

| Campo | Detalle |
|---|---|
| URL y metodo | `POST {{evidencias_url}}/api/v1/evidencias` |
| Objetivo | RF-09: el cliente agrega un comentario a su devolucion. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_cliente}}`; `Content-Type: application/json`; `Accept: application/json` |
| Roles (caso exitoso) | Cliente (dueno de la compra), Inspector |
| Codigo HTTP esperado | 201 |
| Explicacion | Inserta la fila en `evidencias` (PostgreSQL) y el documento de metadatos en MongoDB; si Mongo falla se hace rollback. |
| Evidencia en PostgreSQL | `SELECT id, devolucion_id, tipo, etapa, comentario FROM evidencias ORDER BY id DESC LIMIT 1;` `SELECT accion, entidad, entidad_id, detalle FROM bitacora ORDER BY id DESC LIMIT 3;` (RF-30). |
| Evidencia en MongoDB | `db.evidencias_metadatos.find({evidencia_id: <id>}).pretty()` y `db.evidencias_metadatos.getIndexes()` (idx_devolucion). |
| Evidencia en Redis | No aplica a este endpoint. |

**Body de ejemplo** (caso alta 201 comentario JSON):

```json
{
  "devolucion_id": {{devolucion_ev_id}},
  "tipo": "comentario",
  "etapa": "solicitud",
  "comentario": "El sello del empaque llego roto."
}
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/evidencias.md#174_evidencias_post_raiz_201)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 174 | alta 201 comentario JSON | JSON | Cliente (dueno de la compra) | 201 | - | `[ejecucion real](evidencias/ejecuciones/evidencias.md#174_evidencias_post_raiz_201)` |
| 175 | alta 201 comentario XML | XML | Cliente (dueno de la compra) | 201 | - | `[ejecucion real](evidencias/ejecuciones/evidencias.md#175_evidencias_post_raiz_201_xml)` |
| 176 | alta 201 archivo PNG | JSON | Cliente (dueno de la compra) | 201 | - | `[ejecucion real](evidencias/ejecuciones/evidencias.md#176_evidencias_post_raiz_201)` |
| 208 | alta 201 inspector en etapa inspeccion | JSON | Inspector | 201 | - | `[ejecucion real](evidencias/ejecuciones/evidencias.md#208_evidencias_post_raiz_201)` |
| 177 | alta 400 comentario vacio | JSON | Cliente (dueno de la compra) | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/evidencias.md#177_evidencias_post_raiz_400)` |
| 178 | alta 400 tipo no permitido en JSON | JSON | Cliente (dueno de la compra) | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/evidencias.md#178_evidencias_post_raiz_400)` |
| 179 | alta 400 etapa invalida | JSON | Cliente (dueno de la compra) | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/evidencias.md#179_evidencias_post_raiz_400)` |
| 180 | alta 400 multipart sin archivo | JSON | Cliente (dueno de la compra) | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/evidencias.md#180_evidencias_post_raiz_400)` |
| 181 | alta 401 sin token | JSON | ninguno | 401 | no_autenticado | `[ejecucion real](evidencias/ejecuciones/evidencias.md#181_evidencias_post_raiz_401)` |
| 182 | alta 401 token invalido | JSON | Token invalido (cadena sin firma) | 401 | token_invalido | `[ejecucion real](evidencias/ejecuciones/evidencias.md#182_evidencias_post_raiz_401)` |
| 183 | alta 403 analista | JSON | Analista de Devoluciones | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/evidencias.md#183_evidencias_post_raiz_403)` |
| 184 | alta 403 otro cliente | JSON | Cliente distinto al dueno | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/evidencias.md#184_evidencias_post_raiz_403)` |
| 185 | alta 403 inspector sin inspeccion | JSON | Inspector | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/evidencias.md#185_evidencias_post_raiz_403)` |
| 186 | alta 404 devolucion inexistente | JSON | Cliente (dueno de la compra) | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/evidencias.md#186_evidencias_post_raiz_404)` |
| 187 | alta 409 etapa no permitida al cliente | JSON | Cliente (dueno de la compra) | 409 | estado_no_permite | `[ejecucion real](evidencias/ejecuciones/evidencias.md#187_evidencias_post_raiz_409)` |
| 188 | alta 415 archivo no soportado | JSON | Cliente (dueno de la compra) | 415 | formato_no_soportado | `[ejecucion real](evidencias/ejecuciones/evidencias.md#188_evidencias_post_raiz_415)` |

**Errores controlados:**

- **400 `validacion`** - alta 400 comentario vacio: Un comentario sin texto.
- **400 `validacion`** - alta 400 tipo no permitido en JSON: JSON solo sirve para comentarios; los archivos van en multipart.
- **400 `validacion`** - alta 400 etapa invalida: Etapa fuera de solicitud/recoleccion/recepcion/inspeccion.
- **400 `validacion`** - alta 400 multipart sin archivo: Falta el campo archivo.
- **401 `no_autenticado`** - alta 401 sin token: Endpoint protegido sin Authorization.
- **401 `token_invalido`** - alta 401 token invalido: JWT sin firma valida.
- **403 `sin_permiso`** - alta 403 analista: Solo cliente e inspector adjuntan.
- **403 `sin_permiso`** - alta 403 otro cliente: No se adjunta a la devolucion de otra persona.
- **403 `sin_permiso`** - alta 403 inspector sin inspeccion: La inspeccion no esta asignada a este inspector.
- **404 `no_encontrado`** - alta 404 devolucion inexistente: La devolucion no existe.
- **409 `estado_no_permite`** - alta 409 etapa no permitida al cliente: El cliente solo adjunta en la etapa de solicitud.
- **415 `formato_no_soportado`** - alta 415 archivo no soportado: Un .txt no es JPG, PNG ni PDF reales. Selecciona fixtures/no_es_imagen.txt.

### GET /api/v1/evidencias

*openapi.yaml:* Lista las evidencias visibles del expediente

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{evidencias_url}}/api/v1/evidencias?devolucion_id={{devolucion_ev_id}}&pagina=1&por_pagina=5` |
| Objetivo | Evidencias de la devolucion, paginadas. |
| Parametros | `devolucion_id` (query) |
| Headers | `Authorization: Bearer {{token_cliente}}`; `Accept: application/json` |
| Roles (caso exitoso) | Analista de Devoluciones, Cliente (dueno de la compra) |
| Codigo HTTP esperado | 200 |
| Explicacion | Evidencias de la devolucion, paginadas. |
| Evidencia en PostgreSQL | No aplica a este endpoint. |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/evidencias.md#189_evidencias_get_raiz_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 189 | listar 200 cliente | JSON | Cliente (dueno de la compra) | 200 | - | `[ejecucion real](evidencias/ejecuciones/evidencias.md#189_evidencias_get_raiz_200)` |
| 190 | listar 200 analista XML | XML | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/evidencias.md#190_evidencias_get_raiz_200_xml)` |
| 191 | listar 400 sin devolucion_id | JSON | Cliente (dueno de la compra) | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/evidencias.md#191_evidencias_get_raiz_400)` |
| 192 | listar 403 otro cliente | JSON | Cliente distinto al dueno | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/evidencias.md#192_evidencias_get_raiz_403)` |
| 193 | listar 404 devolucion inexistente | JSON | Analista de Devoluciones | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/evidencias.md#193_evidencias_get_raiz_404)` |

**Errores controlados:**

- **400 `validacion`** - listar 400 sin devolucion_id: devolucion_id es obligatorio.
- **403 `sin_permiso`** - listar 403 otro cliente: No se ven las evidencias de otro cliente.
- **404 `no_encontrado`** - listar 404 devolucion inexistente: La devolucion no existe.

### GET /api/v1/evidencias/{id}

*openapi.yaml:* Metadatos protegidos

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{evidencias_url}}/api/v1/evidencias/{{evidencia_id}}` |
| Objetivo | Detalle de la evidencia mas sus metadatos de MongoDB. |
| Parametros | `evidencia_id` (path) |
| Headers | `Authorization: Bearer {{token_cliente}}`; `Accept: application/json` |
| Roles (caso exitoso) | Cliente (dueno de la compra) |
| Codigo HTTP esperado | 200 |
| Explicacion | Detalle de la evidencia mas sus metadatos de MongoDB. |
| Evidencia en PostgreSQL | No aplica a este endpoint. |
| Evidencia en MongoDB | `db.evidencias_metadatos.find({evidencia_id: <id>})` coincide con `metadatos`. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/evidencias.md#194_evidencias_get_id_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 194 | detalle 200 con metadatos | JSON | Cliente (dueno de la compra) | 200 | - | `[ejecucion real](evidencias/ejecuciones/evidencias.md#194_evidencias_get_id_200)` |
| 195 | detalle 404 inexistente | JSON | Cliente (dueno de la compra) | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/evidencias.md#195_evidencias_get_id_404)` |
| 196 | detalle 403 otro cliente | JSON | Cliente distinto al dueno | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/evidencias.md#196_evidencias_get_id_403)` |

**Errores controlados:**

- **404 `no_encontrado`** - detalle 404 inexistente: Evidencia inexistente.
- **403 `sin_permiso`** - detalle 403 otro cliente: Evidencia de otro cliente.

### GET /api/v1/evidencias/{id}/enlace

*openapi.yaml:* Genera enlace temporal privado de 15 minutos

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{evidencias_url}}/api/v1/evidencias/{{evidencia_archivo_id}}/enlace` |
| Objetivo | Enlace firmado que caduca en 900 s (15 min). |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_cliente}}`; `Accept: application/json` |
| Roles (caso exitoso) | Cliente (dueno de la compra) |
| Codigo HTTP esperado | 200 |
| Explicacion | HMAC-SHA256 sobre `id:vencimiento` con el secreto JWT; el archivo nunca se sirve desde una ruta publica. |
| Evidencia en PostgreSQL | No aplica a este endpoint. |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/evidencias.md#197_evidencias_get_id_enlace_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 197 | enlace 200 firmado | JSON | Cliente (dueno de la compra) | 200 | - | `[ejecucion real](evidencias/ejecuciones/evidencias.md#197_evidencias_get_id_enlace_200)` |
| 198 | enlace 409 comentario sin archivo | JSON | Cliente (dueno de la compra) | 409 | sin_archivo | `[ejecucion real](evidencias/ejecuciones/evidencias.md#198_evidencias_get_id_enlace_409)` |

**Errores controlados:**

- **409 `sin_archivo`** - enlace 409 comentario sin archivo: Un comentario no tiene archivo.

### GET /api/v1/evidencias/{evidencia_id}/archivo

*openapi.yaml:* Descarga binaria con firma temporal o JWT

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{evidencias_url}}/api/v1/evidencias/{{evidencia_archivo_id}}/archivo?{{url_enlace_consulta}}` |
| Objetivo | Descarga con el enlace firmado, sin Bearer. |
| Parametros | `exp` (query), `firma` (query) |
| Headers | `Accept: application/json` |
| Roles (caso exitoso) | Sin autenticacion |
| Codigo HTTP esperado | 200 |
| Explicacion | Descarga con el enlace firmado, sin Bearer. |
| Evidencia en PostgreSQL | No aplica a este endpoint. |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/evidencias.md#199_evidencias_get_evidencia_id_archivo_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 199 | archivo 200 con enlace firmado | JSON | ninguno | 200 | - | `[ejecucion real](evidencias/ejecuciones/evidencias.md#199_evidencias_get_evidencia_id_archivo_200)` |

### GET /api/v1/evidencias/{id}/archivo

*openapi.yaml:* Descarga binaria con firma temporal o JWT

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{evidencias_url}}/api/v1/evidencias/{{evidencia_archivo_id}}/archivo` |
| Objetivo | Descarga autenticada por JWT (sin firma). |
| Parametros | `exp` (query), `firma` (query) |
| Headers | `Authorization: Bearer {{token_cliente}}`; `Accept: application/json` |
| Roles (caso exitoso) | Cliente (dueno de la compra) |
| Codigo HTTP esperado | 200 |
| Explicacion | Descarga autenticada por JWT (sin firma). |
| Evidencia en PostgreSQL | No aplica a este endpoint. |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/evidencias.md#200_evidencias_get_id_archivo_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 200 | archivo 200 con Bearer | JSON | Cliente (dueno de la compra) | 200 | - | `[ejecucion real](evidencias/ejecuciones/evidencias.md#200_evidencias_get_id_archivo_200)` |
| 201 | archivo 401 sin firma ni token | JSON | ninguno | 401 | no_autenticado | `[ejecucion real](evidencias/ejecuciones/evidencias.md#201_evidencias_get_id_archivo_401)` |
| 202 | archivo 404 inexistente | JSON | Cliente (dueno de la compra) | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/evidencias.md#202_evidencias_get_id_archivo_404)` |

**Errores controlados:**

- **401 `no_autenticado`** - archivo 401 sin firma ni token: Sin firma valida ni Bearer no se entrega nada.
- **404 `no_encontrado`** - archivo 404 inexistente: Evidencia inexistente.

### DELETE /api/v1/evidencias/{id}

*openapi.yaml:* Eliminación lógica autorizada

| Campo | Detalle |
|---|---|
| URL y metodo | `DELETE {{evidencias_url}}/api/v1/evidencias/{{evidencia_xml_id}}` |
| Objetivo | Retiro logico (RN-12): el archivo se conserva para auditoria. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_cliente}}`; `Accept: application/json` |
| Roles (caso exitoso) | Cliente (dueno de la compra) |
| Codigo HTTP esperado | 200 |
| Explicacion | Retiro logico (RN-12): el archivo se conserva para auditoria. |
| Evidencia en PostgreSQL | `SELECT id, eliminado_en FROM evidencias WHERE id = <id>;` (eliminado_en con fecha) y `SELECT accion, entidad, entidad_id, detalle FROM bitacora ORDER BY id DESC LIMIT 3;` (RF-30). |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/evidencias.md#205_evidencias_delete_id_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 205 | retiro 200 exitoso | JSON | Cliente (dueno de la compra) | 200 | - | `[ejecucion real](evidencias/ejecuciones/evidencias.md#205_evidencias_delete_id_200)` |
| 203 | retiro 403 analista | JSON | Analista de Devoluciones | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/evidencias.md#203_evidencias_delete_id_403)` |
| 204 | retiro 403 otro cliente | JSON | Cliente distinto al dueno | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/evidencias.md#204_evidencias_delete_id_403)` |
| 206 | retiro 404 ya retirada | JSON | Cliente (dueno de la compra) | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/evidencias.md#206_evidencias_delete_id_404)` |
| 207 | retiro 404 inexistente | JSON | Cliente (dueno de la compra) | 404 | no_encontrado | `[ejecucion real](evidencias/ejecuciones/evidencias.md#207_evidencias_delete_id_404)` |

**Errores controlados:**

- **403 `sin_permiso`** - retiro 403 analista: Solo cliente e inspector retiran evidencias.
- **403 `sin_permiso`** - retiro 403 otro cliente: Solo se retiran evidencias propias.
- **404 `no_encontrado`** - retiro 404 ya retirada: La evidencia retirada ya no se encuentra.
- **404 `no_encontrado`** - retiro 404 inexistente: Evidencia inexistente.

## analisis_auditoria

**Analisis y auditoria** - puerto 8008 - coleccion `docs/postman/analisis_auditoria.postman_collection.json` - Swagger en `/docs` del servicio.

### GET /health

*openapi.yaml:* Estado PostgreSQL MongoDB Redis

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{analisis_url}}/health` |
| Objetivo | RNF-22, RF-32: el servicio responde y reporta el estado de sus dependencias. |
| Parametros | Ninguno |
| Headers | `Accept: application/json` |
| Roles (caso exitoso) | Sin autenticacion |
| Codigo HTTP esperado | 200 |
| Explicacion | RNF-22, RF-32: el servicio responde y reporta el estado de sus dependencias. |
| Evidencia en PostgreSQL | `SELECT 1;` desde el contenedor; el servicio hace la misma comprobacion. |
| Evidencia en MongoDB | `mongosh --eval "db.runCommand({ping:1})"` |
| Evidencia en Redis | `redis-cli PING` responde PONG. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#209_analisis_auditoria_get_health_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 209 | health 200 | JSON | ninguno | 200 | - | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#209_analisis_auditoria_get_health_200)` |

### POST /api/v1/analisis/clasificar-motivo

*openapi.yaml:* Sugiere motivos de forma explicable; requiere confirmacion humana

| Campo | Detalle |
|---|---|
| URL y metodo | `POST {{analisis_url}}/api/v1/analisis/clasificar-motivo` |
| Objetivo | RF-24, RN-11: sugiere un motivo; el usuario siempre confirma. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_cliente}}`; `Content-Type: application/json`; `Accept: application/json` |
| Roles (caso exitoso) | Analista de Devoluciones, Cliente (dueno de la compra) |
| Codigo HTTP esperado | 200 |
| Explicacion | Ranking explicable por palabras clave; nunca decide la causa (RN-09, RN-11). |
| Evidencia en PostgreSQL | `SELECT id, nombre FROM motivos WHERE activo;` (los motivos sugeridos salen de aqui). |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Body de ejemplo** (caso clasificar 200 cliente):

```json
{
  "descripcion": "El producto llego roto y el empaque aplastado por el golpe."
}
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#210_analisis_auditoria_post_clasificar_motivo_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 210 | clasificar 200 cliente | JSON | Cliente (dueno de la compra) | 200 | - | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#210_analisis_auditoria_post_clasificar_motivo_200)` |
| 211 | clasificar 200 analista XML | XML | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#211_analisis_auditoria_post_clasificar_motivo_200_xml)` |
| 212 | clasificar 400 descripcion corta | JSON | Cliente (dueno de la compra) | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#212_analisis_auditoria_post_clasificar_motivo_400)` |
| 213 | clasificar 401 sin token | JSON | ninguno | 401 | no_autenticado | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#213_analisis_auditoria_post_clasificar_motivo_401)` |
| 214 | clasificar 403 centro | JSON | Encargado del Centro de Devoluciones | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#214_analisis_auditoria_post_clasificar_motivo_403)` |

**Errores controlados:**

- **400 `validacion`** - clasificar 400 descripcion corta: La descripcion exige entre 10 y 2000 caracteres.
- **401 `no_autenticado`** - clasificar 401 sin token: Endpoint protegido sin Authorization.
- **403 `sin_permiso`** - clasificar 403 centro: Rol sin permiso.

### POST /api/v1/analisis/sincronizar

*openapi.yaml:* Actualiza MongoDB desde PostgreSQL sin modificar transacciones

| Campo | Detalle |
|---|---|
| URL y metodo | `POST {{analisis_url}}/api/v1/analisis/sincronizar` |
| Objetivo | RF-23: proyecta las devoluciones de PostgreSQL a MongoDB (snapshots). |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_analista}}`; `Content-Type: application/json`; `Accept: application/json` |
| Roles (caso exitoso) | Analista de Devoluciones |
| Codigo HTTP esperado | 200 |
| Explicacion | No modifica PostgreSQL. Hace upsert por devolucion en `resultados_analisis`, marca no vigentes los desaparecidos y sube la version del cache en Redis, lo que invalida el Pareto anterior. |
| Evidencia en PostgreSQL | `SELECT count(*) FROM devoluciones WHERE eliminado_en IS NULL;` (debe coincidir con `casos_sincronizados`). |
| Evidencia en MongoDB | `db.resultados_analisis.countDocuments({tipo_analisis:'snapshot_devolucion', vigente:true})` y `db.resultados_analisis.getIndexes()` (idx_snapshot_devolucion_unico, idx_tipo_fecha). |
| Evidencia en Redis | `GET devoluciones:analisis:version` aumento en 1; `TTL` cerca de 86400 s. |

**Body de ejemplo** (caso sincronizar 200 exitoso):

```json
{}
```

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#217_analisis_auditoria_post_sincronizar_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 217 | sincronizar 200 exitoso | JSON | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#217_analisis_auditoria_post_sincronizar_200)` |
| 215 | sincronizar 403 cliente | JSON | Cliente (dueno de la compra) | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#215_analisis_auditoria_post_sincronizar_403)` |
| 216 | sincronizar 401 sin token | JSON | ninguno | 401 | no_autenticado | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#216_analisis_auditoria_post_sincronizar_401)` |

**Errores controlados:**

- **403 `sin_permiso`** - sincronizar 403 cliente: Solo Administrador y Analista.
- **401 `no_autenticado`** - sincronizar 401 sin token: Endpoint protegido sin Authorization.

### GET /api/v1/analisis/pareto

*openapi.yaml:* Pareto MongoDB mediante pipeline; Redis TTL 600s

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{analisis_url}}/api/v1/analisis/pareto?dimension=motivo&medida=frecuencia` |
| Objetivo | RF-25, RNF-19: primer calculo tras sincronizar, con aggregate real en MongoDB. |
| Parametros | `desde` (query), `dimension` (query), `hasta` (query), `medida` (query) |
| Headers | `Authorization: Bearer {{token_analista}}`; `Accept: application/json` |
| Roles (caso exitoso) | Administrador, Analista de Devoluciones |
| Codigo HTTP esperado | 200 |
| Explicacion | Pipeline `$match` -> `$group` -> `$sort` sobre los snapshots vigentes; guarda el resultado en MongoDB y en Redis (10 min). |
| Evidencia en PostgreSQL | No aplica a este endpoint. |
| Evidencia en MongoDB | `db.resultados_analisis.aggregate([{$match:{tipo_analisis:'snapshot_devolucion',vigente:true}},{$group:{_id:'$motivo',total:{$sum:1}}},{$sort:{total:-1}}])` y `db.resultados_analisis.find({tipo_analisis:'pareto'}).sort({fecha_calculo:-1}).limit(1)`. |
| Evidencia en Redis | `KEYS devoluciones:cache:causas:*`, `GET` de la clave (JSON) y `TTL` <= 600. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#218_analisis_auditoria_get_pareto_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 218 | pareto 200 miss | JSON | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#218_analisis_auditoria_get_pareto_200)` |
| 219 | pareto 200 hit | JSON | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#219_analisis_auditoria_get_pareto_200)` |
| 220 | pareto 200 XML por proveedor y costo | XML | Administrador | 200 | - | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#220_analisis_auditoria_get_pareto_200_xml)` |
| 221 | pareto 400 dimension desconocida | JSON | Analista de Devoluciones | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#221_analisis_auditoria_get_pareto_400)` |
| 222 | pareto 400 fecha invalida | JSON | Analista de Devoluciones | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#222_analisis_auditoria_get_pareto_400)` |
| 223 | pareto 400 rango invertido | JSON | Analista de Devoluciones | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#223_analisis_auditoria_get_pareto_400)` |
| 224 | pareto 403 cliente | JSON | Cliente (dueno de la compra) | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#224_analisis_auditoria_get_pareto_403)` |
| 225 | pareto 401 token invalido | JSON | Token invalido (cadena sin firma) | 401 | token_invalido | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#225_analisis_auditoria_get_pareto_401)` |

**Errores controlados:**

- **400 `validacion`** - pareto 400 dimension desconocida: Dimension fuera de la lista.
- **400 `validacion`** - pareto 400 fecha invalida: desde debe usar AAAA-MM-DD.
- **400 `validacion`** - pareto 400 rango invertido: hasta no puede ser menor que desde.
- **403 `sin_permiso`** - pareto 403 cliente: Solo Administrador y Analista.
- **401 `token_invalido`** - pareto 401 token invalido: JWT sin firma valida.

### GET /api/v1/analisis/resumen

*openapi.yaml:* Resumen de analítica guardada en MongoDB

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{analisis_url}}/api/v1/analisis/resumen` |
| Objetivo | Cuantos casos y reportes hay en MongoDB. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_analista}}`; `Accept: application/json` |
| Roles (caso exitoso) | Analista de Devoluciones |
| Codigo HTTP esperado | 200 |
| Explicacion | Cuantos casos y reportes hay en MongoDB. |
| Evidencia en PostgreSQL | No aplica a este endpoint. |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#226_analisis_auditoria_get_resumen_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 226 | resumen 200 | JSON | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#226_analisis_auditoria_get_resumen_200)` |
| 227 | resumen 403 cliente | JSON | Cliente (dueno de la compra) | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#227_analisis_auditoria_get_resumen_403)` |

**Errores controlados:**

- **403 `sin_permiso`** - resumen 403 cliente: Rol sin permiso.

### GET /api/v1/analisis/alertas-fraude

*openapi.yaml:* Detecta indicadores preventivos para revision humana

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{analisis_url}}/api/v1/analisis/alertas-fraude` |
| Objetivo | RF-25, RN-09: senales de revision humana; no acusan ni bloquean. |
| Parametros | Ninguno |
| Headers | `Authorization: Bearer {{token_analista}}`; `Accept: application/json` |
| Roles (caso exitoso) | Administrador, Analista de Devoluciones |
| Codigo HTTP esperado | 200 |
| Explicacion | RF-25, RN-09: senales de revision humana; no acusan ni bloquean. |
| Evidencia en PostgreSQL | Misma agregacion sobre `devoluciones` y `reembolsos` de los ultimos 90 dias. |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#228_analisis_auditoria_get_alertas_fraude_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 228 | alertas 200 | JSON | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#228_analisis_auditoria_get_alertas_fraude_200)` |
| 229 | alertas 200 XML | XML | Administrador | 200 | - | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#229_analisis_auditoria_get_alertas_fraude_200_xml)` |
| 230 | alertas 403 cliente | JSON | Cliente (dueno de la compra) | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#230_analisis_auditoria_get_alertas_fraude_403)` |

**Errores controlados:**

- **403 `sin_permiso`** - alertas 403 cliente: Rol sin permiso.

### GET /api/v1/analisis/eventos

*openapi.yaml:* Consulta eventos de auditoría MongoDB

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{analisis_url}}/api/v1/analisis/eventos?pagina=1&por_pagina=5` |
| Objetivo | RNF-23: eventos publicados por los servicios. |
| Parametros | `correlation_id` (query), `servicio` (query) |
| Headers | `Authorization: Bearer {{token_analista}}`; `Accept: application/json` |
| Roles (caso exitoso) | Administrador, Analista de Devoluciones |
| Codigo HTTP esperado | 200 |
| Explicacion | RNF-23: eventos publicados por los servicios. |
| Evidencia en PostgreSQL | No aplica a este endpoint. |
| Evidencia en MongoDB | `db.eventos.find({}, {datos: 0}).sort({fecha: -1}).limit(5)` y `db.eventos.getIndexes()` (idx_correlation, idx_fecha). |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#231_analisis_auditoria_get_eventos_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 231 | eventos 200 paginado | JSON | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#231_analisis_auditoria_get_eventos_200)` |
| 232 | eventos 200 XML | XML | Administrador | 200 | - | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#232_analisis_auditoria_get_eventos_200_xml)` |
| 233 | eventos 400 correlation_id largo | JSON | Analista de Devoluciones | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#233_analisis_auditoria_get_eventos_400)` |
| 234 | eventos 400 paginacion invalida | JSON | Analista de Devoluciones | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#234_analisis_auditoria_get_eventos_400)` |
| 235 | eventos 403 cliente | JSON | Cliente (dueno de la compra) | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#235_analisis_auditoria_get_eventos_403)` |

**Errores controlados:**

- **400 `validacion`** - eventos 400 correlation_id largo: El filtro no puede superar 100 caracteres.
- **400 `validacion`** - eventos 400 paginacion invalida: por_pagina fuera de rango.
- **403 `sin_permiso`** - eventos 403 cliente: Rol sin permiso.

### GET /api/v1/auditoria

*openapi.yaml:* Consulta bitácora transaccional PostgreSQL

| Campo | Detalle |
|---|---|
| URL y metodo | `GET {{analisis_url}}/api/v1/auditoria?pagina=1&por_pagina=5` |
| Objetivo | RF-30, RN-12: bitacora de operaciones. |
| Parametros | `accion` (query), `correlation_id` (query), `entidad` (query) |
| Headers | `Authorization: Bearer {{token_analista}}`; `Accept: application/json` |
| Roles (caso exitoso) | Administrador, Analista de Devoluciones |
| Codigo HTTP esperado | 200 |
| Explicacion | RF-30, RN-12: bitacora de operaciones. |
| Evidencia en PostgreSQL | `SELECT id, accion, entidad, correlation_id, fecha FROM bitacora ORDER BY fecha DESC LIMIT 5;` |
| Evidencia en MongoDB | No aplica a este endpoint. |
| Evidencia en Redis | No aplica a este endpoint. |

**Respuesta (caso exitoso):**

[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#236_analisis_auditoria_get_auditoria_200)

**Casos de la coleccion** (cada uno con su captura):

| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |
|---|---|---|---|---|---|---|
| 236 | bitacora 200 paginada | JSON | Analista de Devoluciones | 200 | - | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#236_analisis_auditoria_get_auditoria_200)` |
| 237 | bitacora 200 filtro XML | XML | Administrador | 200 | - | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#237_analisis_auditoria_get_auditoria_200_xml)` |
| 238 | bitacora 400 filtro largo | JSON | Analista de Devoluciones | 400 | validacion | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#238_analisis_auditoria_get_auditoria_400)` |
| 239 | bitacora 403 cliente | JSON | Cliente (dueno de la compra) | 403 | sin_permiso | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#239_analisis_auditoria_get_auditoria_403)` |
| 240 | bitacora 401 sin token | JSON | ninguno | 401 | no_autenticado | `[ejecucion real](evidencias/ejecuciones/analisis_auditoria.md#240_analisis_auditoria_get_auditoria_401)` |

**Errores controlados:**

- **400 `validacion`** - bitacora 400 filtro largo: El filtro no puede superar 100 caracteres.
- **403 `sin_permiso`** - bitacora 403 cliente: Rol sin permiso.
- **401 `no_autenticado`** - bitacora 401 sin token: Endpoint protegido sin Authorization.

