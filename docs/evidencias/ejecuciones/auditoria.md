# Evidencia con curl - `analisis-auditoria`

Ejecutada en la VM el 2026-11-22 19:05 UTC con `scripts/evidencias/ejecutar.py auditoria` (commit `8a99bbb`).
Casos: **32**, correctos: **32**, con falla: **0**. Los tokens y la contrasena de demo estan ocultos; la IP de la VM se muestra como `$VM_HOST`.

Cada respuesta es la que devolvio el servicio: nada se pego a mano. Un caso que no cumple lo esperado queda marcado como falla, no se omite.

## Preparacion

```bash
export VM_HOST=<IP-DE-LA-VM>      # o 127.0.0.1 si corres los comandos dentro de la VM
export PASSWORD_DEMO=...                 # la de las cuentas de demo; no se versiona
login() { curl -s -X POST "http://$VM_HOST:8001/api/v1/auth/login" -H 'Content-Type: application/json' \
  -d "{\"email\":\"$1\",\"password\":\"$PASSWORD_DEMO\"}" | jq -r .access_token; }
export TOKEN_ADMIN=$(login pablo.admin@demo.mx)
export TOKEN_ANALISTA=$(login josue.analista@demo.mx)
export TOKEN_CLIENTE=$(login ana.cliente@demo.mx)
export TOKEN_SUPERVISOR=$(login jorge.supervisor@demo.mx)
```

El login admite 10 intentos por minuto por IP (RNF-13); el token dura 15 minutos.

## Resumen

| Caso | Resultado | HTTP | Descripcion |
|---|---|---|---|
| [P4-AUD-01](#p4-aud-01) | correcto | 200 | salud 200 con las tres dependencias |
| [P4-AUD-02](#p4-aud-02) | correcto | 200 | Swagger: documentacion de la API |
| [P4-AUD-03](#p4-aud-03) | correcto | 200 | Swagger: especificacion OpenAPI |
| [P4-AUD-04](#p4-aud-04) | correcto | 401 | sin token: 401 |
| [P4-AUD-05](#p4-aud-05) | correcto | 401 | token invalido: 401 |
| [P4-AUD-06](#p4-aud-06) | correcto | 403 | cliente: 403 |
| [P4-AUD-07](#p4-aud-07) | correcto | 403 | supervisor: 403 |
| [P4-AUD-08](#p4-aud-08) | correcto | 200 | bitacora 200: lo mas reciente primero |
| [P4-AUD-09](#p4-aud-09) | correcto | 200 | bitacora 200 XML |
| [P4-AUD-10](#p4-aud-10) | correcto | 200 | bitacora 200 por correlation id |
| [P4-AUD-11](#p4-aud-11) | correcto | 200 | bitacora 200 por usuario |
| [P4-AUD-12](#p4-aud-12) | correcto | 200 | bitacora 200 por entidad y accion |
| [P4-AUD-13](#p4-aud-13) | correcto | 200 | bitacora 200 por periodo |
| [P4-AUD-14](#p4-aud-14) | correcto | 200 | bitacora 200 con intento de inyeccion SQL |
| [P4-AUD-15](#p4-aud-15) | correcto | 400 | bitacora 400 fecha invalida |
| [P4-AUD-16](#p4-aud-16) | correcto | 400 | bitacora 400 hasta antes de desde |
| [P4-AUD-17](#p4-aud-17) | correcto | 400 | bitacora 400 usuario no numerico |
| [P4-AUD-18](#p4-aud-18) | correcto | 400 | bitacora 400 filtro demasiado largo |
| [P4-AUD-19](#p4-aud-19) | correcto | 405 | la bitacora no se escribe por la API: POST |
| [P4-AUD-20](#p4-aud-20) | correcto | 404 | la bitacora no se escribe por la API: PATCH |
| [P4-AUD-21](#p4-aud-21) | correcto | 200 | estado 200: la base protege la bitacora |
| [P4-AUD-22](#p4-aud-22) | correcto | 200 | eventos 200 de MongoDB |
| [P4-AUD-23](#p4-aud-23) | correcto | 200 | eventos 200 por servicio |
| [P4-AUD-24](#p4-aud-24) | correcto | 200 | eventos 200 XML |
| [P4-AUD-25](#p4-aud-25) | correcto | 400 | eventos 400 filtro demasiado largo |
| [P4-AUD-26](#p4-aud-26) | correcto | 410 | retirada: clasificar motivo |
| [P4-AUD-27](#p4-aud-27) | correcto | 410 | retirada: alertas de fraude |
| [P4-AUD-28](#p4-aud-28) | correcto | 410 | retirada: Pareto |
| [P4-AUD-29](#p4-aud-29) | correcto | 410 | retirada: sincronizar |
| [P4-AUD-30](#p4-aud-30) | correcto | 410 | retirada: resumen |
| [P4-AUD-31](#p4-aud-31) | correcto | 410 | retirada: alias de eventos |
| [P4-AUD-32](#p4-aud-32) | correcto | 200 | la auditoria sigue en pie tras el corte |

## P4-AUD-01

**salud 200 con las tres dependencias**

Objetivo: El servicio informa PostgreSQL, Redis y MongoDB, y que el analisis esta retirado (RF-32).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/health" \
  -H "Accept: application/json"
```

Respuesta - **200 OK** (26 ms, 208 bytes):

```http
Content-Type: application/json
Content-Length: 208
X-Correlation-ID: aa1e93fb76004881
```

```json
{
  "servicio": "analisis-auditoria",
  "version": "v1",
  "estado": "ok",
  "dependencias": {
    "postgresql": {
      "ok": true,
      "error": null
    },
    "redis": {
      "ok": true,
      "error": null
    },
    "mongodb": {
      "ok": true,
      "error": null
    }
  },
  "analisis": "retirado"
}
```

Verificaciones:

- ok: HTTP 200
- ok: estado ok
- ok: MongoDB ok
- ok: analisis retirado

## P4-AUD-02

**Swagger: documentacion de la API**

Objetivo: La API publica su documentacion Swagger.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/docs" \
  -H "Accept: text/html"
```

Respuesta - **200 OK** (11 ms, 460 bytes):

```http
Content-Type: text/html; charset=utf-8
Content-Length: 460
X-Correlation-ID: a9d18749409c4c2b
```

```text
<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Servicio de auditoria - Plataforma de devoluciones</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui.css">
</head><body><div id="swagger"></div>
<script src="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script>
<script>SwaggerUIBundle({url: "openapi.json", dom_id: "#swagger",
  persistAuthorization: true});</script>
</body></html>
```

Verificaciones:

- ok: HTTP 200
- ok: HTML de Swagger UI

## P4-AUD-03

**Swagger: especificacion OpenAPI**

Objetivo: La especificacion incluye la auditoria.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/openapi.json" \
  -H "Accept: application/json"
```

Respuesta - **200 OK** (12 ms, 8361 bytes):

```http
Content-Type: application/json
Content-Length: 8361
X-Correlation-ID: f75a9ec6591649bf
```

```json
{
  "openapi": "3.0.3",
  "info": {
    "title": "Servicio de auditoria - Plataforma de devoluciones",
    "version": "1.0.0",
    "description": "Auditoria: consulta de la bitacora (solo lectura, solo agrega) y eventos por correlation id. RF-30, RN-12, RNF-23. El analisis (clasificar motivo, Pareto, alertas de fraude, sincronizar, resumen) se separo: su sucesor es clasificacion-motivos (8010) y reportes-analitica (8018). Sus rutas fueron retiradas y responden 410. JSON/XML y JWT."
  },
  "servers": [
    {
      "url": "/"
    }
  ],
  "paths": {
    "/health": {
      "get": {
        "summary": "Estado PostgreSQL MongoDB Redis",
        "responses": {
          "200": {
            "description": "Estado PostgreSQL MongoDB Redis",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object"
                }
              },
              "application/xml": {
                "schema": {
                  "type": "object"
                }
              }
            }
          },
          "400": {
            "description": "Parámetros inválidos"
          },
          "401": {
            "description": "Token inválido"
          },
          "403": {
            "description": "Sin permisos"
          },
          "404": {
            "description": "No encontrado"
          },
          "409": {
            "description": "Conflicto de negocio"
          },
          "415": {
            "description": "Formato no permitido"
          },
          "500": {
            "description": "Error interno"
          },
          "503": {
            "description": "Dependencia no disponible"
          }
        }
      }
    },
    "/api/v1/analisis/{ruta}": {
      "get": {
        "summary": "RETIRADO - el analisis ya no se ofrece aqui (410)",
        "description": "El analisis (clasificar motivo, Pareto, alertas de fraude, sincronizar, resumen y el alias de eventos) se separo de la auditoria y su codigo se retiro. Cualquier metodo y cualquier ruta bajo /api/v1/analisis responde 410 servicio_movido, aun sin token, con los sucesores en detalles: clasificacion-motivos (8010) POST /api/v1/motivos/sugerencias, reportes-analitica (8018) GET /api/v1/analitica/alertas-fraude y GET /api/v1/reportes/pareto, y esta misma API GET /api/v1/auditoria/eventos. Lleva Deprecation: true.",
        "parameters": [
          {
            "name": "ruta",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string"
... (recortado: 332 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: incluye la bitacora
- ok: incluye el estado

## P4-AUD-04

**sin token: 401**

Objetivo: La auditoria exige JWT (RNF-09).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria" \
  -H "Accept: application/json"
```

Respuesta - **401 UNAUTHORIZED** (13 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: 00e261cad6f640d1
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "00e261cad6f640d1"
  }
}
```

Verificaciones:

- ok: HTTP 401
- ok: tipo no_autenticado

## P4-AUD-05

**token invalido: 401**

Objetivo: Un token alterado se rechaza.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer no.es.un.jwt"
```

Respuesta - **401 UNAUTHORIZED** (11 ms, 136 bytes):

```http
Content-Type: application/json
Content-Length: 136
X-Correlation-ID: 6b78388b13df4370
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "token_invalido",
    "mensaje": "El token no es valido.",
    "detalles": null,
    "correlation_id": "6b78388b13df4370"
  }
}
```

Verificaciones:

- ok: HTTP 401
- ok: tipo token_invalido

## P4-AUD-06

**cliente: 403**

Objetivo: La bitacora no la lee un cliente (RN-13).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_CLIENTE"
```

Respuesta - **403 FORBIDDEN** (9 ms, 232 bytes):

```http
Content-Type: application/json
Content-Length: 232
X-Correlation-ID: 5d8628aafa364647
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "Tu rol no tiene permiso para esta operacion.",
    "detalles": {
      "rol": "Cliente",
      "roles_permitidos": [
        "Administrador",
        "Analista de Devoluciones"
      ]
    },
    "correlation_id": "5d8628aafa364647"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-AUD-07

**supervisor: 403**

Objetivo: Auditar es de Administrador y Analista; la separacion de funciones evita que quien opera revise su propio rastro (RN-12).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria/estado" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR"
```

Respuesta - **403 FORBIDDEN** (10 ms, 235 bytes):

```http
Content-Type: application/json
Content-Length: 235
X-Correlation-ID: 703dbdd44cdc4c27
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "Tu rol no tiene permiso para esta operacion.",
    "detalles": {
      "rol": "Supervisor",
      "roles_permitidos": [
        "Administrador",
        "Analista de Devoluciones"
      ]
    },
    "correlation_id": "703dbdd44cdc4c27"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-AUD-08

**bitacora 200: lo mas reciente primero**

Objetivo: La bitacora registra quien hizo que y cuando (RF-30), ordenada de lo mas reciente a lo mas antiguo.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria?por_pagina=10" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

Respuesta - **200 OK** (24 ms, 2436 bytes):

```http
Content-Type: application/json
Content-Length: 2436
X-Correlation-ID: dafb7fcc6f2e4ed3
```

```json
{
  "datos": [
    {
      "id": 1690,
      "accion": "login_api",
      "entidad": "usuarios",
      "entidad_id": 18,
      "detalle": "Inicio de sesion por API, JWT emitido",
      "correlation_id": "2066af003f4e4e24",
      "fecha": "2026-11-22T19:05:32.764389+00:00",
      "usuario": "Pablo Flores"
    },
    {
      "id": 1689,
      "accion": "login_api",
      "entidad": "usuarios",
      "entidad_id": 40,
      "detalle": "Inicio de sesion por API, JWT emitido",
      "correlation_id": "5534354edd9e43c8",
      "fecha": "2026-11-22T19:05:32.637847+00:00",
      "usuario": "Jorge Salinas"
    },
    {
      "id": 1688,
      "accion": "login_api",
      "entidad": "usuarios",
      "entidad_id": 10,
      "detalle": "Inicio de sesion por API, JWT emitido",
      "correlation_id": "3c88f88ac5b0486b",
      "fecha": "2026-11-22T19:05:32.476943+00:00",
      "usuario": "Ana Lopez Garcia"
    },
    {
      "id": 1687,
      "accion": "logout_api",
      "entidad": "usuarios",
      "entidad_id": 10,
      "detalle": "Cierre de sesion por API: token y sesion revocados",
      "correlation_id": "99b582453c2e44e6",
      "fecha": "2026-11-22T19:04:26.509343+00:00",
      "usuario": "Ana Lopez Garcia"
    },
    {
      "id": 1686,
      "accion": "logout_api",
      "entidad": "usuarios",
      "entidad_id": 18,
      "detalle": "Cierre de sesion por API: token y sesion revocados",
      "correlation_id": "98cb1d0fc6df4552",
      "fecha": "2026-11-22T19:04:26.496428+00:00",
      "usuario": "Pablo Flores"
    },
    {
      "id": 1685,
      "accion": "logout_api",
      "entidad": "usuarios",
      "entidad_id": 17,
      "detalle": "Cierre de sesion por API: token y sesion revocados",
      "correlation_id": "463ddf54b3ac4633",
      "fecha": "2026-11-22T19:04:26.483026+00:00",
      "usuario": "Carla Trevino"
    },
    {
      "id": 1684,
      "accion": "logout_api",
      "entidad": "usuarios",
      "entidad_id": 13,
      "detalle": "Cierre de sesion por API: token y sesion revocados",
      "correlation_id": "fdab347eff9f4b7a",
      "fecha": "2026-11-22T19:04:26.469146+00:00",
... (recortado: 40 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: hay registros
- ok: trae usuario, accion y fecha
- ok: orden descendente por id
- ok: sin tokens ni hashes

Efecto en PostgreSQL - registros de la bitacora, para contrastar el total:

```sql
SELECT count(*) AS registros FROM bitacora
```

```text
registros
1690
```

## P4-AUD-09

**bitacora 200 XML**

Objetivo: La bitacora responde XML (RF-31).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria?por_pagina=3" \
  -H "Accept: application/xml" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (25 ms, 1054 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 1054
X-Correlation-ID: 3fa4e390a3954617
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<bitacora><datos><item><id>1691</id><accion>login_api</accion><entidad>usuarios</entidad><entidad_id>16</entidad_id><detalle>Inicio de sesion por API, JWT emitido</detalle><correlation_id>4c5990fc0bd741e4</correlation_id><fecha>2026-11-22T19:05:33.069352+00:00</fecha><usuario>Josue Berdeal</usuario></item><item><id>1690</id><accion>login_api</accion><entidad>usuarios</entidad><entidad_id>18</entidad_id><detalle>Inicio de sesion por API, JWT emitido</detalle><correlation_id>2066af003f4e4e24</correlation_id><fecha>2026-11-22T19:05:32.764389+00:00</fecha><usuario>Pablo Flores</usuario></item><item><id>1689</id><accion>login_api</accion><entidad>usuarios</entidad><entidad_id>40</entidad_id><detalle>Inicio de sesion por API, JWT emitido</detalle><correlation_id>5534354edd9e43c8</correlation_id><fecha>2026-11-22T19:05:32.637847+00:00</fecha><usuario>Jorge Salinas</usuario></item></datos><paginacion><pagina>1</pagina><por_pagina>3</por_pagina><total>1691</total><paginas>564</paginas></paginacion></bitacora>
```

Verificaciones:

- ok: HTTP 200
- ok: es XML
- ok: raiz bitacora

## P4-AUD-10

**bitacora 200 por correlation id**

Objetivo: Todo lo que dejo una misma peticion, de punta a punta, se sigue con su correlation id.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria?correlation_id=99b582453c2e44e6" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

Respuesta - **200 OK** (25 ms, 318 bytes):

```http
Content-Type: application/json
Content-Length: 318
X-Correlation-ID: 467690899bda4491
```

```json
{
  "datos": [
    {
      "id": 1687,
      "accion": "logout_api",
      "entidad": "usuarios",
      "entidad_id": 10,
      "detalle": "Cierre de sesion por API: token y sesion revocados",
      "correlation_id": "99b582453c2e44e6",
      "fecha": "2026-11-22T19:04:26.509343+00:00",
      "usuario": "Ana Lopez Garcia"
    }
  ],
  "paginacion": {
    "pagina": 1,
    "por_pagina": 20,
    "total": 1,
    "paginas": 1
  }
}
```

Verificaciones:

- ok: HTTP 200
- ok: todas con ese id

## P4-AUD-11

**bitacora 200 por usuario**

Objetivo: Lo que hizo una persona.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria?usuario_id=10&por_pagina=20" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

Respuesta - **200 OK** (24 ms, 4813 bytes):

```http
Content-Type: application/json
Content-Length: 4813
X-Correlation-ID: 0d4f6b08a1384520
```

```json
{
  "datos": [
    {
      "id": 1688,
      "accion": "login_api",
      "entidad": "usuarios",
      "entidad_id": 10,
      "detalle": "Inicio de sesion por API, JWT emitido",
      "correlation_id": "3c88f88ac5b0486b",
      "fecha": "2026-11-22T19:05:32.476943+00:00",
      "usuario": "Ana Lopez Garcia"
    },
    {
      "id": 1687,
      "accion": "logout_api",
      "entidad": "usuarios",
      "entidad_id": 10,
      "detalle": "Cierre de sesion por API: token y sesion revocados",
      "correlation_id": "99b582453c2e44e6",
      "fecha": "2026-11-22T19:04:26.509343+00:00",
      "usuario": "Ana Lopez Garcia"
    },
    {
      "id": 1650,
      "accion": "acceso_denegado",
      "entidad": "devoluciones",
      "entidad_id": 178,
      "detalle": "Intento de acceder a una devolucion de otro cliente (API)",
      "correlation_id": "4b15993cf1c54814",
      "fecha": "2026-11-22T19:04:24.304350+00:00",
      "usuario": "Ana Lopez Garcia"
    },
    {
      "id": 1634,
      "accion": "logout_api",
      "entidad": "usuarios",
      "entidad_id": 10,
      "detalle": "Cierre de sesion por API: token y sesion revocados",
      "correlation_id": "c5195a6a02464613",
      "fecha": "2026-11-22T19:04:23.146225+00:00",
      "usuario": "Ana Lopez Garcia"
    },
    {
      "id": 1629,
      "accion": "login_api",
      "entidad": "usuarios",
      "entidad_id": 10,
      "detalle": "Inicio de sesion por API, JWT emitido",
      "correlation_id": "3ed10da062264f18",
      "fecha": "2026-11-22T19:04:22.602981+00:00",
      "usuario": "Ana Lopez Garcia"
    },
    {
      "id": 1621,
      "accion": "login_api",
      "entidad": "usuarios",
      "entidad_id": 10,
      "detalle": "Inicio de sesion por API, JWT emitido",
      "correlation_id": "c2b40065e26d4185",
      "fecha": "2026-11-22T19:04:21.774690+00:00",
      "usuario": "Ana Lopez Garcia"
    },
    {
      "id": 1611,
      "accion": "logout_api",
      "entidad": "usuarios",
      "entidad_id": 10,
      "detalle": "Cierre de sesion por API: token y sesion revocados",
      "correlation_id": "abe5bf5370e84fc1",
      "fecha": "2026-11-22T19:03:02.099570+00:00",
... (recortado: 140 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: hay registros

## P4-AUD-12

**bitacora 200 por entidad y accion**

Objetivo: Filtros por entidad y accion; las reconfirmaciones de contrasena quedan asentadas.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria?entidad=usuarios&accion=autorizacion_operacion" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (24 ms, 1753 bytes):

```http
Content-Type: application/json
Content-Length: 1753
X-Correlation-ID: cb108a5bc7584ff9
```

```json
{
  "datos": [
    {
      "id": 1313,
      "accion": "autorizacion_operacion",
      "entidad": "usuarios",
      "entidad_id": 40,
      "detalle": "Autorizo cerrar_investigacion sobre 9",
      "correlation_id": "4190a90480a74cc4",
      "fecha": "2026-11-22T18:29:59.283348+00:00",
      "usuario": "Jorge Salinas"
    },
    {
      "id": 1128,
      "accion": "autorizacion_operacion",
      "entidad": "usuarios",
      "entidad_id": 17,
      "detalle": "Autorizo aprobar_reembolso sobre 999999",
      "correlation_id": "516a2ebbe3994372",
      "fecha": "2026-11-22T18:29:02.029354+00:00",
      "usuario": "Carla Trevino"
    },
    {
      "id": 1050,
      "accion": "autorizacion_operacion",
      "entidad": "usuarios",
      "entidad_id": 40,
      "detalle": "Autorizo cerrar_investigacion sobre 6",
      "correlation_id": "b7548cb0b287428a",
      "fecha": "2026-11-22T18:13:29.521343+00:00",
      "usuario": "Jorge Salinas"
    },
    {
      "id": 1049,
      "accion": "autorizacion_operacion",
      "entidad": "usuarios",
      "entidad_id": 40,
      "detalle": "Autorizo cerrar_investigacion sobre 999999",
      "correlation_id": "5068b1a81c6740ae",
      "fecha": "2026-11-22T18:13:29.384955+00:00",
      "usuario": "Jorge Salinas"
    },
    {
      "id": 1017,
      "accion": "autorizacion_operacion",
      "entidad": "usuarios",
      "entidad_id": 40,
      "detalle": "Autorizo cerrar_investigacion sobre 4",
      "correlation_id": "9040bddad5df4848",
      "fecha": "2026-11-22T18:11:56.392445+00:00",
      "usuario": "Jorge Salinas"
    },
    {
      "id": 1016,
      "accion": "autorizacion_operacion",
      "entidad": "usuarios",
      "entidad_id": 40,
      "detalle": "Autorizo cerrar_investigacion sobre 999999",
      "correlation_id": "e82fc147895846af",
      "fecha": "2026-11-22T18:11:56.255320+00:00",
      "usuario": "Jorge Salinas"
    },
    {
      "id": 846,
      "accion": "autorizacion_operacion",
      "entidad": "usuarios",
      "entidad_id": 40,
      "detalle": "Autorizo cerrar_investigacion sobre 3",
      "correlation_id": "220bd476e8374577",
      "fecha": "2026-11-22T01:17:15.293117+00:00",
... (recortado: 10 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: todas coinciden

## P4-AUD-13

**bitacora 200 por periodo**

Objetivo: El periodo incluye todo el dia final.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria?desde=2026-01-01&hasta=2026-12-31&por_pagina=5" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

Respuesta - **200 OK** (25 ms, 1224 bytes):

```http
Content-Type: application/json
Content-Length: 1224
X-Correlation-ID: 021428b2366445fe
```

```json
{
  "datos": [
    {
      "id": 1691,
      "accion": "login_api",
      "entidad": "usuarios",
      "entidad_id": 16,
      "detalle": "Inicio de sesion por API, JWT emitido",
      "correlation_id": "4c5990fc0bd741e4",
      "fecha": "2026-11-22T19:05:33.069352+00:00",
      "usuario": "Josue Berdeal"
    },
    {
      "id": 1690,
      "accion": "login_api",
      "entidad": "usuarios",
      "entidad_id": 18,
      "detalle": "Inicio de sesion por API, JWT emitido",
      "correlation_id": "2066af003f4e4e24",
      "fecha": "2026-11-22T19:05:32.764389+00:00",
      "usuario": "Pablo Flores"
    },
    {
      "id": 1689,
      "accion": "login_api",
      "entidad": "usuarios",
      "entidad_id": 40,
      "detalle": "Inicio de sesion por API, JWT emitido",
      "correlation_id": "5534354edd9e43c8",
      "fecha": "2026-11-22T19:05:32.637847+00:00",
      "usuario": "Jorge Salinas"
    },
    {
      "id": 1688,
      "accion": "login_api",
      "entidad": "usuarios",
      "entidad_id": 10,
      "detalle": "Inicio de sesion por API, JWT emitido",
      "correlation_id": "3c88f88ac5b0486b",
      "fecha": "2026-11-22T19:05:32.476943+00:00",
      "usuario": "Ana Lopez Garcia"
    },
    {
      "id": 1687,
      "accion": "logout_api",
      "entidad": "usuarios",
      "entidad_id": 10,
      "detalle": "Cierre de sesion por API: token y sesion revocados",
      "correlation_id": "99b582453c2e44e6",
      "fecha": "2026-11-22T19:04:26.509343+00:00",
      "usuario": "Ana Lopez Garcia"
    }
  ],
  "paginacion": {
    "pagina": 1,
    "por_pagina": 5,
    "total": 1691,
    "paginas": 339
  }
}
```

Verificaciones:

- ok: HTTP 200
- ok: hay registros

## P4-AUD-14

**bitacora 200 con intento de inyeccion SQL**

Objetivo: Un filtro con SQL se trata como texto (parametros ligados, RNF-11): no devuelve toda la bitacora.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria?accion=x%27%20OR%20%271%27%3D%271" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

Respuesta - **200 OK** (27 ms, 77 bytes):

```http
Content-Type: application/json
Content-Length: 77
X-Correlation-ID: a71168d4d7bd47b5
```

```json
{
  "datos": [],
  "paginacion": {
    "pagina": 1,
    "por_pagina": 20,
    "total": 0,
    "paginas": 0
  }
}
```

Verificaciones:

- ok: HTTP 200
- ok: sin resultados

## P4-AUD-15

**bitacora 400 fecha invalida**

Objetivo: Las fechas son AAAA-MM-DD.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria?desde=ayer" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

Respuesta - **400 BAD REQUEST** (14 ms, 146 bytes):

```http
Content-Type: application/json
Content-Length: 146
X-Correlation-ID: d8601bffe490407c
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "desde debe tener formato AAAA-MM-DD.",
    "detalles": null,
    "correlation_id": "d8601bffe490407c"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-AUD-16

**bitacora 400 hasta antes de desde**

Objetivo: Un periodo al reves se rechaza.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria?desde=2026-06-01&hasta=2026-01-01" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

Respuesta - **400 BAD REQUEST** (15 ms, 145 bytes):

```http
Content-Type: application/json
Content-Length: 145
X-Correlation-ID: fcb6f89ef70c44b7
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "hasta no puede ser menor que desde.",
    "detalles": null,
    "correlation_id": "fcb6f89ef70c44b7"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-AUD-17

**bitacora 400 usuario no numerico**

Objetivo: El filtro numerico se valida.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria?usuario_id=abc" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

Respuesta - **400 BAD REQUEST** (12 ms, 149 bytes):

```http
Content-Type: application/json
Content-Length: 149
X-Correlation-ID: 66743903ef834d22
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "usuario_id debe ser un entero positivo.",
    "detalles": null,
    "correlation_id": "66743903ef834d22"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-AUD-18

**bitacora 400 filtro demasiado largo**

Objetivo: Un filtro de texto tiene un maximo de 100 caracteres.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria?accion=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

Respuesta - **400 BAD REQUEST** (12 ms, 140 bytes):

```http
Content-Type: application/json
Content-Length: 140
X-Correlation-ID: 19b541eb69b24f17
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Filtro accion demasiado largo.",
    "detalles": null,
    "correlation_id": "19b541eb69b24f17"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-AUD-19

**la bitacora no se escribe por la API: POST**

Objetivo: La auditoria solo se consulta: no existe una ruta para agregar o alterar registros (RN-12). Los demas servicios escriben directo en la base.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8008/api/v1/auditoria" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"accion":"falsa","entidad":"x"}'
```

Respuesta - **405 METHOD NOT ALLOWED** (11 ms, 167 bytes):

```http
Content-Type: application/json
Content-Length: 167
X-Correlation-ID: 6869c8b7a3984ad5
```

```json
{
  "error": {
    "codigo": 405,
    "tipo": "metodo_no_permitido",
    "mensaje": "The method is not allowed for the requested URL.",
    "detalles": null,
    "correlation_id": "6869c8b7a3984ad5"
  }
}
```

Verificaciones:

- ok: HTTP 405
- ok: metodo no permitido

## P4-AUD-20

**la bitacora no se escribe por la API: PATCH**

Objetivo: Tampoco hay ruta para modificar un registro.

Comando:

```bash
curl -sS -i -X PATCH "http://$VM_HOST:8008/api/v1/auditoria/1" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"detalle":"alterado"}'
```

Respuesta - **404 NOT FOUND** (13 ms, 233 bytes):

```http
Content-Type: application/json
Content-Length: 233
X-Correlation-ID: b77a91b22cdf4741
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.",
    "detalles": null,
    "correlation_id": "b77a91b22cdf4741"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: la ruta no existe

## P4-AUD-21

**estado 200: la base protege la bitacora**

Objetivo: Informa si la base rechaza UPDATE, DELETE y TRUNCATE (migracion 045) y avisa hasta donde llega esa proteccion.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria/estado" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (20 ms, 358 bytes):

```http
Content-Type: application/json
Content-Length: 358
X-Correlation-ID: 9651202dd5a34a02
```

```json
{
  "registros": 1691,
  "primero": "2026-09-06T23:20:35.290510+00:00",
  "ultimo": "2026-11-22T19:05:33.069352+00:00",
  "proteccion": {
    "actualizar_y_borrar_bloqueados": true,
    "vaciar_bloqueado": true,
    "completa": true
  },
  "aviso": "La bitacora solo admite agregar registros. Esta proteccion es del esquema de la base; no sustituye el control de acceso al servidor de PostgreSQL."
}
```

Verificaciones:

- ok: HTTP 200
- ok: proteccion completa
- ok: hay registros
- ok: no promete mas de lo que hace

Efecto en PostgreSQL - los triggers que la protegen:

```sql
SELECT tgname FROM pg_trigger WHERE tgrelid = 'bitacora'::regclass AND NOT tgisinternal ORDER BY 1
```

```text
tgname
trg_bitacora_inmutable
trg_bitacora_sin_truncate
```

## P4-AUD-22

**eventos 200 de MongoDB**

Objetivo: Traza de eventos entre servicios. Nunca incluye el campo `datos` (puede traer cuerpos de peticiones, RNF-16).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria/eventos?por_pagina=5" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

Respuesta - **200 OK** (12 ms, 1021 bytes):

```http
Content-Type: application/json
Content-Length: 1021
X-Correlation-ID: 77313bfbd66640c3
```

```json
{
  "datos": [
    {
      "id": "6b0337fab29f09f2d6b3b7cc",
      "servicio": "devoluciones",
      "tipo": "devolucion_registrada",
      "usuario_id": 11,
      "correlation_id": "6646b2aace514c2c",
      "fecha": "2026-11-22T18:44:10.938000+00:00"
    },
    {
      "id": "6b0337fa39e349dccf13fbe1",
      "servicio": "devoluciones",
      "tipo": "devolucion_registrada",
      "usuario_id": 11,
      "correlation_id": "25aeb7fa817a4425",
      "fecha": "2026-11-22T18:44:10.888000+00:00"
    },
    {
      "id": "6b03349864e8f88c00ab6b6d",
      "servicio": "integraciones-monitoreo",
      "tipo": "venta_importada",
      "usuario_id": 18,
      "correlation_id": "a9e29d4812964df0",
      "fecha": "2026-11-22T18:29:44.565000+00:00"
    },
    {
      "id": "6b033498a7125e1ee88f2f0b",
      "servicio": "integraciones-monitoreo",
      "tipo": "venta_importada",
      "usuario_id": 18,
      "correlation_id": "2b8829a81e724032",
      "fecha": "2026-11-22T18:29:44.494000+00:00"
    },
    {
      "id": "6b033498a7125e1ee88f2f0a",
      "servicio": "integraciones-monitoreo",
      "tipo": "venta_importada",
      "usuario_id": 18,
      "correlation_id": "448abad358df4dce",
      "fecha": "2026-11-22T18:29:44.405000+00:00"
    }
  ],
  "paginacion": {
    "pagina": 1,
    "por_pagina": 5,
    "total": 32,
    "paginas": 7
  }
}
```

Verificaciones:

- ok: HTTP 200
- ok: trae paginacion
- ok: ningun evento trae `datos`

## P4-AUD-23

**eventos 200 por servicio**

Objetivo: Filtra los eventos por servicio.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria/eventos?servicio=auth" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (9 ms, 77 bytes):

```http
Content-Type: application/json
Content-Length: 77
X-Correlation-ID: 5ae62f9d7cc84560
```

```json
{
  "datos": [],
  "paginacion": {
    "pagina": 1,
    "por_pagina": 20,
    "total": 0,
    "paginas": 0
  }
}
```

Verificaciones:

- ok: HTTP 200
- ok: todos del servicio

## P4-AUD-24

**eventos 200 XML**

Objetivo: La traza responde XML (RF-31).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria/eventos?por_pagina=2" \
  -H "Accept: application/xml" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (10 ms, 652 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 652
X-Correlation-ID: 9756629403a347eb
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<eventos><datos><item><id>6b0337fab29f09f2d6b3b7cc</id><servicio>devoluciones</servicio><tipo>devolucion_registrada</tipo><usuario_id>11</usuario_id><correlation_id>6646b2aace514c2c</correlation_id><fecha>2026-11-22T18:44:10.938000+00:00</fecha></item><item><id>6b0337fa39e349dccf13fbe1</id><servicio>devoluciones</servicio><tipo>devolucion_registrada</tipo><usuario_id>11</usuario_id><correlation_id>25aeb7fa817a4425</correlation_id><fecha>2026-11-22T18:44:10.888000+00:00</fecha></item></datos><paginacion><pagina>1</pagina><por_pagina>2</por_pagina><total>32</total><paginas>16</paginas></paginacion></eventos>
```

Verificaciones:

- ok: HTTP 200
- ok: es XML

## P4-AUD-25

**eventos 400 filtro demasiado largo**

Objetivo: Un filtro de texto tiene un maximo.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria/eventos?servicio=sssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

Respuesta - **400 BAD REQUEST** (8 ms, 142 bytes):

```http
Content-Type: application/json
Content-Length: 142
X-Correlation-ID: a3e7828d483b4909
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Filtro servicio demasiado largo.",
    "detalles": null,
    "correlation_id": "a3e7828d483b4909"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-AUD-26

**retirada: clasificar motivo**

Objetivo: La clasificacion de motivos vive ahora en clasificacion-motivos (8010). Esta ruta responde 410 aun sin token y dice donde.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8008/api/v1/analisis/clasificar-motivo" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"descripcion":"El producto llego con el empaque roto"}'
```

Respuesta - **410 GONE** (8 ms, 455 bytes):

```http
Content-Type: application/json
Content-Length: 455
X-Correlation-ID: bb86e26cefda450f
Deprecation: true
```

```json
{
  "error": {
    "codigo": 410,
    "tipo": "servicio_movido",
    "mensaje": "El analisis ya no se ofrece en analisis-auditoria; solo queda la auditoria.",
    "detalles": {
      "clasificar-motivo": "http://clasificacion-motivos:8000/api/v1/motivos/sugerencias",
      "alertas-fraude": "http://reportes-analitica:8000/api/v1/analitica/alertas-fraude",
      "pareto": "http://reportes-analitica:8000/api/v1/reportes/pareto",
      "eventos": "/api/v1/auditoria/eventos"
    },
    "correlation_id": "bb86e26cefda450f"
  }
}
```

Verificaciones:

- ok: HTTP 410
- ok: 410 servicio_movido
- ok: nombra al sucesor
- ok: lleva Deprecation: true

## P4-AUD-27

**retirada: alertas de fraude**

Objetivo: Las alertas de fraude viven en reportes-analitica (8018). Ni un Analista con token las obtiene aqui.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/analisis/alertas-fraude" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **410 GONE** (10 ms, 455 bytes):

```http
Content-Type: application/json
Content-Length: 455
X-Correlation-ID: 0fffab27cbef46ed
Deprecation: true
```

```json
{
  "error": {
    "codigo": 410,
    "tipo": "servicio_movido",
    "mensaje": "El analisis ya no se ofrece en analisis-auditoria; solo queda la auditoria.",
    "detalles": {
      "clasificar-motivo": "http://clasificacion-motivos:8000/api/v1/motivos/sugerencias",
      "alertas-fraude": "http://reportes-analitica:8000/api/v1/analitica/alertas-fraude",
      "pareto": "http://reportes-analitica:8000/api/v1/reportes/pareto",
      "eventos": "/api/v1/auditoria/eventos"
    },
    "correlation_id": "0fffab27cbef46ed"
  }
}
```

Verificaciones:

- ok: HTTP 410
- ok: 410 servicio_movido
- ok: nombra al sucesor
- ok: lleva Deprecation: true

## P4-AUD-28

**retirada: Pareto**

Objetivo: El Pareto vive en reportes-analitica (8018), calculado directo en PostgreSQL.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/analisis/pareto?dimension=motivo" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **410 GONE** (8 ms, 455 bytes):

```http
Content-Type: application/json
Content-Length: 455
X-Correlation-ID: 786e319dbc5742a8
Deprecation: true
```

```json
{
  "error": {
    "codigo": 410,
    "tipo": "servicio_movido",
    "mensaje": "El analisis ya no se ofrece en analisis-auditoria; solo queda la auditoria.",
    "detalles": {
      "clasificar-motivo": "http://clasificacion-motivos:8000/api/v1/motivos/sugerencias",
      "alertas-fraude": "http://reportes-analitica:8000/api/v1/analitica/alertas-fraude",
      "pareto": "http://reportes-analitica:8000/api/v1/reportes/pareto",
      "eventos": "/api/v1/auditoria/eventos"
    },
    "correlation_id": "786e319dbc5742a8"
  }
}
```

Verificaciones:

- ok: HTTP 410
- ok: 410 servicio_movido
- ok: nombra al sucesor
- ok: lleva Deprecation: true

## P4-AUD-29

**retirada: sincronizar**

Objetivo: Sincronizar ya no hace falta: 8018 calcula directo en PostgreSQL y siempre esta al dia. No escribe nada.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8008/api/v1/analisis/sincronizar" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{}'
```

Respuesta - **410 GONE** (8 ms, 455 bytes):

```http
Content-Type: application/json
Content-Length: 455
X-Correlation-ID: 09b4225b27794e10
Deprecation: true
```

```json
{
  "error": {
    "codigo": 410,
    "tipo": "servicio_movido",
    "mensaje": "El analisis ya no se ofrece en analisis-auditoria; solo queda la auditoria.",
    "detalles": {
      "clasificar-motivo": "http://clasificacion-motivos:8000/api/v1/motivos/sugerencias",
      "alertas-fraude": "http://reportes-analitica:8000/api/v1/analitica/alertas-fraude",
      "pareto": "http://reportes-analitica:8000/api/v1/reportes/pareto",
      "eventos": "/api/v1/auditoria/eventos"
    },
    "correlation_id": "09b4225b27794e10"
  }
}
```

Verificaciones:

- ok: HTTP 410
- ok: 410 servicio_movido

## P4-AUD-30

**retirada: resumen**

Objetivo: El resumen solo contaba snapshots y no tiene sucesor.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/analisis/resumen" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **410 GONE** (8 ms, 455 bytes):

```http
Content-Type: application/json
Content-Length: 455
X-Correlation-ID: f1a5d8b2aac04345
Deprecation: true
```

```json
{
  "error": {
    "codigo": 410,
    "tipo": "servicio_movido",
    "mensaje": "El analisis ya no se ofrece en analisis-auditoria; solo queda la auditoria.",
    "detalles": {
      "clasificar-motivo": "http://clasificacion-motivos:8000/api/v1/motivos/sugerencias",
      "alertas-fraude": "http://reportes-analitica:8000/api/v1/analitica/alertas-fraude",
      "pareto": "http://reportes-analitica:8000/api/v1/reportes/pareto",
      "eventos": "/api/v1/auditoria/eventos"
    },
    "correlation_id": "f1a5d8b2aac04345"
  }
}
```

Verificaciones:

- ok: HTTP 410
- ok: 410 servicio_movido

## P4-AUD-31

**retirada: alias de eventos**

Objetivo: La traza por correlation id es auditoria: el sucesor es /api/v1/auditoria/eventos, que sigue en 200 (ver arriba).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/analisis/eventos?por_pagina=2" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

Respuesta - **410 GONE** (9 ms, 455 bytes):

```http
Content-Type: application/json
Content-Length: 455
X-Correlation-ID: e397bd2abfe24a5d
Deprecation: true
```

```json
{
  "error": {
    "codigo": 410,
    "tipo": "servicio_movido",
    "mensaje": "El analisis ya no se ofrece en analisis-auditoria; solo queda la auditoria.",
    "detalles": {
      "clasificar-motivo": "http://clasificacion-motivos:8000/api/v1/motivos/sugerencias",
      "alertas-fraude": "http://reportes-analitica:8000/api/v1/analitica/alertas-fraude",
      "pareto": "http://reportes-analitica:8000/api/v1/reportes/pareto",
      "eventos": "/api/v1/auditoria/eventos"
    },
    "correlation_id": "e397bd2abfe24a5d"
  }
}
```

Verificaciones:

- ok: HTTP 410
- ok: 410 servicio_movido
- ok: nombra al sucesor
- ok: lleva Deprecation: true

## P4-AUD-32

**la auditoria sigue en pie tras el corte**

Objetivo: Retirar el analisis no toca la auditoria: la separacion que pidio el profe.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8008/api/v1/auditoria/estado" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (23 ms, 358 bytes):

```http
Content-Type: application/json
Content-Length: 358
X-Correlation-ID: ccf560d7d844495e
```

```json
{
  "registros": 1691,
  "primero": "2026-09-06T23:20:35.290510+00:00",
  "ultimo": "2026-11-22T19:05:33.069352+00:00",
  "proteccion": {
    "actualizar_y_borrar_bloqueados": true,
    "vaciar_bloqueado": true,
    "completa": true
  },
  "aviso": "La bitacora solo admite agregar registros. Esta proteccion es del esquema de la base; no sustituye el control de acceso al servidor de PostgreSQL."
}
```

Verificaciones:

- ok: HTTP 200
- ok: proteccion completa

