# Ejecuciones reales - `logistica`

Salida de `newman run docs/postman/logistica.postman_collection.json` contra la VM (2026-10-22 00:38 UTC). Verificaciones: 102 (0 fallidas). Tokens, contrasenas e IP de la VM estan ocultos (`***jwt***`, `***`, `{{vm_host}}`).

## 053_logistica_get_health_200

Carpeta: 00 Preparacion (requiere devolucion_id autorizada: coleccion devoluciones) - Caso: health 200

`GET http://{{vm_host}}:8003/health`

**Request - headers:**

```http
Accept: application/json
```

**Response - 200 OK** (170 ms, 142 bytes):

```http
Content-Type: application/json
Content-Length: 142
X-Correlation-ID: b5348d48cf3a4ca1
```

```json
{
  "servicio": "logistica",
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
    }
  }
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: postgresql ok
- ok: redis ok

## 054_logistica_post_recolecciones_401

Carpeta: 01 Programar recoleccion (POST) - Caso: programar 401 sin token

`POST http://{{vm_host}}:8003/api/v1/logistica/recolecciones`

**Request - headers:**

```http
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 81,
  "fecha_programada": "2026-10-29",
  "lugar": "Domicilio del cliente"
}
```

**Response - 401 UNAUTHORIZED** (167 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: 8dc84cd4d8b24947
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "8dc84cd4d8b24947"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = no_autenticado
- ok: Trae X-Correlation-ID

## 055_logistica_post_recolecciones_401

Carpeta: 01 Programar recoleccion (POST) - Caso: programar 401 token invalido

`POST http://{{vm_host}}:8003/api/v1/logistica/recolecciones`

**Request - headers:**

```http
Authorization: Bearer esto-no-es-un-token
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 81,
  "fecha_programada": "2026-10-29",
  "lugar": "Domicilio del cliente"
}
```

**Response - 401 UNAUTHORIZED** (97 ms, 136 bytes):

```http
Content-Type: application/json
Content-Length: 136
X-Correlation-ID: d93bf10f850944be
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "token_invalido",
    "mensaje": "El token no es valido.",
    "detalles": null,
    "correlation_id": "d93bf10f850944be"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = token_invalido
- ok: Trae X-Correlation-ID

## 056_logistica_post_recolecciones_403

Carpeta: 01 Programar recoleccion (POST) - Caso: programar 403 centro sin permiso

`POST http://{{vm_host}}:8003/api/v1/logistica/recolecciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 81,
  "fecha_programada": "2026-10-29",
  "lugar": "Domicilio del cliente"
}
```

**Response - 403 FORBIDDEN** (91 ms, 245 bytes):

```http
Content-Type: application/json
Content-Length: 245
X-Correlation-ID: 9ad226928f12444e
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "Tu rol no tiene permiso para esta operacion.",
    "detalles": {
      "rol": "Encargado del Centro de Devoluciones",
      "roles_permitidos": [
        "Coordinador de Logistica"
      ]
    },
    "correlation_id": "9ad226928f12444e"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 057_logistica_post_recolecciones_400

Carpeta: 01 Programar recoleccion (POST) - Caso: programar 400 devolucion_id invalido

`POST http://{{vm_host}}:8003/api/v1/logistica/recolecciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": "abc",
  "fecha_programada": "2026-10-29",
  "lugar": "Domicilio del cliente"
}
```

**Response - 400 BAD REQUEST** (77 ms, 200 bytes):

```http
Content-Type: application/json
Content-Length: 200
X-Correlation-ID: 7469e21a013e4766
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Datos de logistica invalidos.",
    "detalles": [
      {
        "campo": "devolucion_id",
        "problema": "debe ser entero positivo"
      }
    ],
    "correlation_id": "7469e21a013e4766"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 058_logistica_post_recolecciones_404

Carpeta: 01 Programar recoleccion (POST) - Caso: programar 404 devolucion inexistente

`POST http://{{vm_host}}:8003/api/v1/logistica/recolecciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 999999,
  "fecha_programada": "2026-10-29",
  "lugar": "Domicilio del cliente"
}
```

**Response - 404 NOT FOUND** (179 ms, 144 bytes):

```http
Content-Type: application/json
Content-Length: 144
X-Correlation-ID: ced276a0b06744b6
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe la devolucion 999999.",
    "detalles": null,
    "correlation_id": "ced276a0b06744b6"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 059_logistica_post_recolecciones_400

Carpeta: 01 Programar recoleccion (POST) - Caso: programar 400 fecha en el pasado

`POST http://{{vm_host}}:8003/api/v1/logistica/recolecciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 81,
  "fecha_programada": "2020-01-01",
  "lugar": "Domicilio del cliente"
}
```

**Response - 400 BAD REQUEST** (87 ms, 155 bytes):

```http
Content-Type: application/json
Content-Length: 155
X-Correlation-ID: f96b48cded3544de
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "fecha_programada no puede estar en el pasado.",
    "detalles": null,
    "correlation_id": "f96b48cded3544de"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 060_logistica_post_recolecciones_400_xml

Carpeta: 01 Programar recoleccion (POST) - Caso: programar 400 XML no cumple XSD

`POST http://{{vm_host}}:8003/api/v1/logistica/recolecciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/xml
Accept: application/xml
```

**Request - body:**

```
<recoleccion>
  <devolucion_id>81</devolucion_id>
  <lugar>Domicilio</lugar>
</recoleccion>
```

**Response - 400 BAD REQUEST** (130 ms, 365 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 365
X-Correlation-ID: cda1444e7000443d
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<error><codigo>400</codigo><tipo>xml_no_cumple_xsd</tipo><mensaje>El XML no cumple el contrato del endpoint.</mensaje><detalles><item><linea>3</linea><problema>Element 'lugar': This element is not expected. Expected is ( fecha_programada ).</problema></item></detalles><correlation_id>cda1444e7000443d</correlation_id></error>
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = xml_no_cumple_xsd
- ok: Trae X-Correlation-ID

## 061_logistica_post_recolecciones_201

Carpeta: 01 Programar recoleccion (POST) - Caso: programar 201 exitoso

`POST http://{{vm_host}}:8003/api/v1/logistica/recolecciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 81,
  "fecha_programada": "2026-10-29",
  "lugar": "Domicilio del cliente"
}
```

**Response - 201 CREATED** (147 ms, 115 bytes):

```http
Content-Type: application/json
Content-Length: 115
Location: /api/v1/logistica/recolecciones/29
X-Correlation-ID: ceaa44e98a9c447f
```

```json
{
  "id": 29,
  "devolucion_id": 81,
  "fecha_programada": "2026-10-29",
  "lugar": "Domicilio del cliente",
  "estado": "programada"
}
```

**Verificaciones:**

- ok: HTTP 201
- ok: Trae X-Correlation-ID
- ok: estado programada

## 062_logistica_post_recolecciones_409

Carpeta: 01 Programar recoleccion (POST) - Caso: programar 409 ya programada

`POST http://{{vm_host}}:8003/api/v1/logistica/recolecciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 81,
  "fecha_programada": "2026-10-29",
  "lugar": "Domicilio del cliente"
}
```

**Response - 409 CONFLICT** (99 ms, 190 bytes):

```http
Content-Type: application/json
Content-Length: 190
X-Correlation-ID: 37b28b8a67214c72
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "estado_no_permite",
    "mensaje": "Solo se programan devoluciones autorizadas.",
    "detalles": {
      "estado_actual": "en_recoleccion"
    },
    "correlation_id": "37b28b8a67214c72"
  }
}
```

**Verificaciones:**

- ok: HTTP 409
- ok: error.tipo = estado_no_permite
- ok: Trae X-Correlation-ID

## 063_logistica_get_recolecciones_200

Carpeta: 02 Consulta (GET) - Caso: listar 200 coordinador

`GET http://{{vm_host}}:8003/api/v1/logistica/recolecciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (114 ms, 6400 bytes):

```http
Content-Type: application/json
Content-Length: 6400
X-Correlation-ID: 61652c55f78d478f
```

```json
{
  "datos": [
    {
      "id": 29,
      "devolucion_id": 81,
      "fecha_programada": "2026-10-29",
      "lugar": "Domicilio del cliente",
      "ruta_id": null,
      "transportista_id": null,
      "coordinador_id": 15,
      "estado": "programada",
      "folio_devolucion": "DEV-2026-0081",
      "ruta": " -> ",
      "transportista": null
    },
    {
      "id": 21,
      "devolucion_id": 37,
      "fecha_programada": "2026-10-21",
      "lugar": "domicilio",
      "ruta_id": 4,
      "transportista_id": 3,
      "coordinador_id": 15,
      "estado": "asignada",
      "folio_devolucion": "DEV-2026-0037",
      "ruta": "Domicilio del cliente -> Centro de Devoluciones Norte",
      "transportista": "Carlos Medina"
    },
    {
      "id": 20,
      "devolucion_id": 35,
      "fecha_programada": "2026-09-07",
      "lugar": "Tienda valle oriente",
      "ruta_id": 2,
      "transportista_id": 4,
      "coordinador_id": 15,
      "estado": "completada",
      "folio_devolucion": "DEV-2026-0035",
      "ruta": "Tienda Valle Oriente -> Centro de Devoluciones Norte",
      "transportista": "Laura Cruz"
    },
    {
      "id": 19,
      "devolucion_id": 33,
      "fecha_programada": "2026-09-09",
      "lugar": "Domicilio de la clienta, San Pedro",
      "ruta_id": 4,
      "transportista_id": 3,
      "coordinador_id": 15,
      "estado": "completada",
      "folio_devolucion": "DEV-2026-0033",
      "ruta": "Domicilio del cliente -> Centro de Devoluciones Norte",
      "transportista": "Carlos Medina"
    },
    {
      "id": 18,
      "devolucion_id": 32,
      "fecha_programada": "2026-09-03",
      "lugar": "Domicilio del cliente",
      "ruta_id": 3,
      "transportista_id": 4,
      "coordinador_id": 15,
      "estado": "completada",
      "folio_devolucion": "DEV-2026-0032",
      "ruta": "Tienda Cumbres -> Centro de Devoluciones Norte",
      "transportista": "Laura Cruz"
    },
    {
      "id": 17,
      "devolucion_id": 31,
      "fecha_programada": "2026-09-03",
      "lugar": "Domicilio del cliente",
      "ruta_id": 4,
      "transportista_id": 2,
      "coordinador_id": 15,
      "estado": "completada",
      "folio_devolucion": "DEV-2026-0031",
      "ruta": "Domicilio del cliente -> Centro de Devoluciones Norte",
      "transportista": "Maria Gonzalez"
    },
    {
      "id": 16,
      "devolucion_id": 30,
      "fecha_programada": "2026-09-03",
      "lugar": "Domicilio del cliente",
      "ruta_id": 3,
      "transportista_id": 1,

... (recortado, 8563 caracteres en total)
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: trae datos

## 064_logistica_get_recolecciones_200_xml

Carpeta: 02 Consulta (GET) - Caso: listar 200 centro XML con filtro

`GET http://{{vm_host}}:8003/api/v1/logistica/recolecciones?estado=programada`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/xml
```

**Response - 200 OK** (120 ms, 397 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 397
X-Correlation-ID: f33d479d99834bef
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<respuesta><datos><item><id>29</id><devolucion_id>81</devolucion_id><fecha_programada>2026-10-29</fecha_programada><lugar>Domicilio del cliente</lugar><ruta_id /><transportista_id /><coordinador_id>15</coordinador_id><estado>programada</estado><folio_devolucion>DEV-2026-0081</folio_devolucion><ruta> -&gt; </ruta><transportista /></item></datos></respuesta>
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 065_logistica_get_recolecciones_400

Carpeta: 02 Consulta (GET) - Caso: listar 400 estado invalido

`GET http://{{vm_host}}:8003/api/v1/logistica/recolecciones?estado=volando`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 400 BAD REQUEST** (143 ms, 141 bytes):

```http
Content-Type: application/json
Content-Length: 141
X-Correlation-ID: 9b70523fc20e4cb6
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Estado de recoleccion invalido.",
    "detalles": null,
    "correlation_id": "9b70523fc20e4cb6"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 066_logistica_get_recolecciones_403

Carpeta: 02 Consulta (GET) - Caso: listar 403 cliente

`GET http://{{vm_host}}:8003/api/v1/logistica/recolecciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 403 FORBIDDEN** (75 ms, 255 bytes):

```http
Content-Type: application/json
Content-Length: 255
X-Correlation-ID: c1418db98a3f436c
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
        "Coordinador de Logistica",
        "Encargado del Centro de Devoluciones"
      ]
    },
    "correlation_id": "c1418db98a3f436c"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 067_logistica_get_recolecciones_401

Carpeta: 02 Consulta (GET) - Caso: listar 401 sin token

`GET http://{{vm_host}}:8003/api/v1/logistica/recolecciones`

**Request - headers:**

```http
Accept: application/json
```

**Response - 401 UNAUTHORIZED** (75 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: 2c4984f67ac64bbc
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "2c4984f67ac64bbc"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = no_autenticado
- ok: Trae X-Correlation-ID

## 068_logistica_patch_recolecciones_id_asignacion_403

Carpeta: 03 Asignar ruta y transportista (PATCH) - Caso: asignar 403 centro sin permiso

`PATCH http://{{vm_host}}:8003/api/v1/logistica/recolecciones/29/asignacion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "ruta_id": 4,
  "transportista_id": 4
}
```

**Response - 403 FORBIDDEN** (75 ms, 245 bytes):

```http
Content-Type: application/json
Content-Length: 245
X-Correlation-ID: d274c938c3d24c5a
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "Tu rol no tiene permiso para esta operacion.",
    "detalles": {
      "rol": "Encargado del Centro de Devoluciones",
      "roles_permitidos": [
        "Coordinador de Logistica"
      ]
    },
    "correlation_id": "d274c938c3d24c5a"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 069_logistica_patch_recolecciones_id_asignacion_400

Carpeta: 03 Asignar ruta y transportista (PATCH) - Caso: asignar 400 ruta invalida

`PATCH http://{{vm_host}}:8003/api/v1/logistica/recolecciones/29/asignacion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "ruta_id": 0,
  "transportista_id": 4
}
```

**Response - 400 BAD REQUEST** (162 ms, 194 bytes):

```http
Content-Type: application/json
Content-Length: 194
X-Correlation-ID: d29f44607903498f
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Datos de logistica invalidos.",
    "detalles": [
      {
        "campo": "ruta_id",
        "problema": "debe ser entero positivo"
      }
    ],
    "correlation_id": "d29f44607903498f"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 070_logistica_patch_recolecciones_id_asignacion_400

Carpeta: 03 Asignar ruta y transportista (PATCH) - Caso: asignar 400 ruta inexistente

`PATCH http://{{vm_host}}:8003/api/v1/logistica/recolecciones/29/asignacion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "ruta_id": 999999,
  "transportista_id": 4
}
```

**Response - 400 BAD REQUEST** (86 ms, 152 bytes):

```http
Content-Type: application/json
Content-Length: 152
X-Correlation-ID: 5058766fdf5d4245
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Ruta o transportista inexistente/inactivo.",
    "detalles": null,
    "correlation_id": "5058766fdf5d4245"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 071_logistica_patch_recolecciones_id_asignacion_404

Carpeta: 03 Asignar ruta y transportista (PATCH) - Caso: asignar 404 recoleccion inexistente

`PATCH http://{{vm_host}}:8003/api/v1/logistica/recolecciones/999999/asignacion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "ruta_id": 4,
  "transportista_id": 4
}
```

**Response - 404 NOT FOUND** (84 ms, 145 bytes):

```http
Content-Type: application/json
Content-Length: 145
X-Correlation-ID: de0f54f0b02c4241
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe la recoleccion 999999.",
    "detalles": null,
    "correlation_id": "de0f54f0b02c4241"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 072_logistica_patch_recolecciones_id_asignacion_200_xml

Carpeta: 03 Asignar ruta y transportista (PATCH) - Caso: asignar 200 XML

`PATCH http://{{vm_host}}:8003/api/v1/logistica/recolecciones/29/asignacion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/xml
Accept: application/xml
```

**Request - body:**

```
<asignacion>
  <ruta_id>4</ruta_id>
  <transportista_id>4</transportista_id>
</asignacion>
```

**Response - 200 OK** (94 ms, 156 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 156
X-Correlation-ID: cd63209b770a41a8
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<respuesta><id>29</id><estado>asignada</estado><ruta_id>4</ruta_id><transportista_id>4</transportista_id></respuesta>
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: asignada

## 073_logistica_patch_recolecciones_id_estado_409

Carpeta: 04 Estado de la recoleccion (PATCH) - Caso: estado 409 transicion invalida

`PATCH http://{{vm_host}}:8003/api/v1/logistica/recolecciones/29/estado`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "estado": "completada"
}
```

**Response - 409 CONFLICT** (84 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: 1f57a087fc844914
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "transicion_invalida",
    "mensaje": "No se puede pasar de asignada a completada.",
    "detalles": null,
    "correlation_id": "1f57a087fc844914"
  }
}
```

**Verificaciones:**

- ok: HTTP 409
- ok: error.tipo = transicion_invalida
- ok: Trae X-Correlation-ID

## 074_logistica_patch_recolecciones_id_estado_404

Carpeta: 04 Estado de la recoleccion (PATCH) - Caso: estado 404 inexistente

`PATCH http://{{vm_host}}:8003/api/v1/logistica/recolecciones/999999/estado`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "estado": "en_transito"
}
```

**Response - 404 NOT FOUND** (163 ms, 145 bytes):

```http
Content-Type: application/json
Content-Length: 145
X-Correlation-ID: a8b9d88fc7cc425d
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe la recoleccion 999999.",
    "detalles": null,
    "correlation_id": "a8b9d88fc7cc425d"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 075_logistica_patch_recolecciones_id_estado_200

Carpeta: 04 Estado de la recoleccion (PATCH) - Caso: estado 200 en_transito

`PATCH http://{{vm_host}}:8003/api/v1/logistica/recolecciones/29/estado`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "estado": "en_transito"
}
```

**Response - 200 OK** (86 ms, 33 bytes):

```http
Content-Type: application/json
Content-Length: 33
X-Correlation-ID: 5ddcdd20429b43ce
```

```json
{
  "id": 29,
  "estado": "en_transito"
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: en_transito

## 076_logistica_patch_recolecciones_id_asignacion_409

Carpeta: 04 Estado de la recoleccion (PATCH) - Caso: asignar 409 ya inicio

`PATCH http://{{vm_host}}:8003/api/v1/logistica/recolecciones/29/asignacion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "ruta_id": 4,
  "transportista_id": 4
}
```

**Response - 409 CONFLICT** (87 ms, 142 bytes):

```http
Content-Type: application/json
Content-Length: 142
X-Correlation-ID: 60ac27a671bb4c5e
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "estado_no_permite",
    "mensaje": "La recoleccion ya inicio.",
    "detalles": null,
    "correlation_id": "60ac27a671bb4c5e"
  }
}
```

**Verificaciones:**

- ok: HTTP 409
- ok: error.tipo = estado_no_permite
- ok: Trae X-Correlation-ID

## 077_logistica_patch_recolecciones_id_estado_200_xml

Carpeta: 04 Estado de la recoleccion (PATCH) - Caso: estado 200 completada XML

`PATCH http://{{vm_host}}:8003/api/v1/logistica/recolecciones/29/estado`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/xml
Accept: application/xml
```

**Request - body:**

```
<estado_recoleccion>
  <estado>completada</estado>
</estado_recoleccion>
```

**Response - 200 OK** (86 ms, 100 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 100
X-Correlation-ID: ec66b5aa4d9c4a7c
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<respuesta><id>29</id><estado>completada</estado></respuesta>
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: completada

## 078_logistica_post_recepciones_403

Carpeta: 05 Recepcion en el centro (POST) - Caso: recepcion 403 coordinador

`POST http://{{vm_host}}:8003/api/v1/logistica/recepciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 81,
  "coincide_expediente": true
}
```

**Response - 403 FORBIDDEN** (144 ms, 245 bytes):

```http
Content-Type: application/json
Content-Length: 245
X-Correlation-ID: 171741af21cb4c46
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "Tu rol no tiene permiso para esta operacion.",
    "detalles": {
      "rol": "Coordinador de Logistica",
      "roles_permitidos": [
        "Encargado del Centro de Devoluciones"
      ]
    },
    "correlation_id": "171741af21cb4c46"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 079_logistica_post_recepciones_400

Carpeta: 05 Recepcion en el centro (POST) - Caso: recepcion 400 devolucion invalida

`POST http://{{vm_host}}:8003/api/v1/logistica/recepciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 0,
  "coincide_expediente": true
}
```

**Response - 400 BAD REQUEST** (75 ms, 200 bytes):

```http
Content-Type: application/json
Content-Length: 200
X-Correlation-ID: 10f9b092d76c4ebf
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Datos de logistica invalidos.",
    "detalles": [
      {
        "campo": "devolucion_id",
        "problema": "debe ser entero positivo"
      }
    ],
    "correlation_id": "10f9b092d76c4ebf"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 080_logistica_post_recepciones_404

Carpeta: 05 Recepcion en el centro (POST) - Caso: recepcion 404 inexistente

`POST http://{{vm_host}}:8003/api/v1/logistica/recepciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 999999,
  "coincide_expediente": true
}
```

**Response - 404 NOT FOUND** (82 ms, 144 bytes):

```http
Content-Type: application/json
Content-Length: 144
X-Correlation-ID: 92798f9249894f96
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe la devolucion 999999.",
    "detalles": null,
    "correlation_id": "92798f9249894f96"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 081_logistica_post_recepciones_400

Carpeta: 05 Recepcion en el centro (POST) - Caso: recepcion 400 booleano invalido

`POST http://{{vm_host}}:8003/api/v1/logistica/recepciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 81,
  "coincide_expediente": "quizas"
}
```

**Response - 400 BAD REQUEST** (85 ms, 148 bytes):

```http
Content-Type: application/json
Content-Length: 148
X-Correlation-ID: 9f8d8b706b0042f9
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "coincide_expediente debe ser booleano.",
    "detalles": null,
    "correlation_id": "9f8d8b706b0042f9"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 082_logistica_post_recepciones_201

Carpeta: 05 Recepcion en el centro (POST) - Caso: recepcion 201 exitoso

`POST http://{{vm_host}}:8003/api/v1/logistica/recepciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 81,
  "coincide_expediente": true
}
```

**Response - 201 CREATED** (178 ms, 109 bytes):

```http
Content-Type: application/json
Content-Length: 109
X-Correlation-ID: de3c11a62a2d469b
```

```json
{
  "id": 23,
  "devolucion_id": 81,
  "fecha_recepcion": "2026-10-22T00:38:37.180712+00:00",
  "coincide_expediente": true
}
```

**Verificaciones:**

- ok: HTTP 201
- ok: Trae X-Correlation-ID

## 083_logistica_post_recepciones_409

Carpeta: 05 Recepcion en el centro (POST) - Caso: recepcion 409 duplicada

`POST http://{{vm_host}}:8003/api/v1/logistica/recepciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 81,
  "coincide_expediente": true
}
```

**Response - 409 CONFLICT** (87 ms, 149 bytes):

```http
Content-Type: application/json
Content-Length: 149
X-Correlation-ID: 9c3f7b1be5fe4876
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "recepcion_duplicada",
    "mensaje": "La devolucion ya fue recibida.",
    "detalles": null,
    "correlation_id": "9c3f7b1be5fe4876"
  }
}
```

**Verificaciones:**

- ok: HTTP 409
- ok: error.tipo = recepcion_duplicada
- ok: Trae X-Correlation-ID

