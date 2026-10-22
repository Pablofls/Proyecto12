# Ejecuciones reales - `reembolsos_costos`

Salida de `newman run docs/postman/reembolsos_costos.postman_collection.json` contra la VM (2026-10-22 00:41 UTC). Verificaciones: 89 (0 fallidas). Tokens, contrasenas e IP de la VM estan ocultos (`***jwt***`, `***`, `{{vm_host}}`).

## 111_reembolsos_costos_get_health_200

Carpeta: 00 Preparacion (requiere devolucion_id autorizada o resuelta) - Caso: health 200

`GET http://{{vm_host}}:8005/health`

**Request - headers:**

```http
Accept: application/json
```

**Response - 200 OK** (97 ms, 150 bytes):

```http
Content-Type: application/json
Content-Length: 150
X-Correlation-ID: efb5e89085f84b17
```

```json
{
  "servicio": "reembolsos-costos",
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

## 112_reembolsos_costos_post_costos_401

Carpeta: 01 Costos (POST) - Caso: costo 401 sin token

`POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/costos`

**Request - headers:**

```http
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 81,
  "etapa": "transporte",
  "monto": 150.5
}
```

**Response - 401 UNAUTHORIZED** (78 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: c724eaa4999946ee
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "c724eaa4999946ee"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = no_autenticado
- ok: Trae X-Correlation-ID

## 113_reembolsos_costos_post_costos_403

Carpeta: 01 Costos (POST) - Caso: costo 403 cliente

`POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/costos`

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
  "etapa": "transporte",
  "monto": 150.5
}
```

**Response - 403 FORBIDDEN** (107 ms, 320 bytes):

```http
Content-Type: application/json
Content-Length: 320
X-Correlation-ID: 83568e1dd3bc462b
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
        "Encargado del Centro de Devoluciones",
        "Inspector",
        "Analista de Devoluciones",
        "Encargado de Reembolsos"
      ]
    },
    "correlation_id": "83568e1dd3bc462b"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 114_reembolsos_costos_post_costos_403

Carpeta: 01 Costos (POST) - Caso: costo 403 etapa de otro rol

`POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/costos`

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
  "etapa": "reembolso",
  "monto": 150.5
}
```

**Response - 403 FORBIDDEN** (176 ms, 158 bytes):

```http
Content-Type: application/json
Content-Length: 158
X-Correlation-ID: 19f8712ddd35468d
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "Tu rol no puede registrar costos de esta etapa.",
    "detalles": null,
    "correlation_id": "19f8712ddd35468d"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 115_reembolsos_costos_post_costos_400

Carpeta: 01 Costos (POST) - Caso: costo 400 monto negativo

`POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/costos`

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
  "etapa": "transporte",
  "monto": -5
}
```

**Response - 400 BAD REQUEST** (77 ms, 161 bytes):

```http
Content-Type: application/json
Content-Length: 161
X-Correlation-ID: 73051ed6d3a34227
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "monto debe ser un monto decimal finito no negativo.",
    "detalles": null,
    "correlation_id": "73051ed6d3a34227"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 116_reembolsos_costos_post_costos_400

Carpeta: 01 Costos (POST) - Caso: costo 400 etapa invalida

`POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/costos`

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
  "etapa": "viaje",
  "monto": 150.5
}
```

**Response - 400 BAD REQUEST** (76 ms, 134 bytes):

```http
Content-Type: application/json
Content-Length: 134
X-Correlation-ID: 1fa3246c193d4980
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Etapa de costo invalida.",
    "detalles": null,
    "correlation_id": "1fa3246c193d4980"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 117_reembolsos_costos_post_costos_400

Carpeta: 01 Costos (POST) - Caso: costo 400 devolucion_id invalido

`POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/costos`

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
  "etapa": "transporte",
  "monto": 150.5
}
```

**Response - 400 BAD REQUEST** (74 ms, 140 bytes):

```http
Content-Type: application/json
Content-Length: 140
X-Correlation-ID: 8cbe5ff9448b4b09
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "devolucion_id debe ser entero.",
    "detalles": null,
    "correlation_id": "8cbe5ff9448b4b09"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 118_reembolsos_costos_post_costos_400_xml

Carpeta: 01 Costos (POST) - Caso: costo 400 XML no cumple XSD

`POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/costos`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/xml
Accept: application/xml
```

**Request - body:**

```
<costo>
  <devolucion_id>81</devolucion_id>
</costo>
```

**Response - 400 BAD REQUEST** (171 ms, 350 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 350
X-Correlation-ID: 2709955e3ea54475
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<error><codigo>400</codigo><tipo>xml_no_cumple_xsd</tipo><mensaje>El XML no cumple el contrato del endpoint.</mensaje><detalles><item><linea>1</linea><problema>Element 'costo': Missing child element(s). Expected is ( etapa ).</problema></item></detalles><correlation_id>2709955e3ea54475</correlation_id></error>
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = xml_no_cumple_xsd
- ok: Trae X-Correlation-ID

## 119_reembolsos_costos_post_costos_404

Carpeta: 01 Costos (POST) - Caso: costo 404 devolucion inexistente

`POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/costos`

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
  "etapa": "transporte",
  "monto": 150.5
}
```

**Response - 404 NOT FOUND** (88 ms, 144 bytes):

```http
Content-Type: application/json
Content-Length: 144
X-Correlation-ID: df6f50bc67d74ba9
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe la devolucion 999999.",
    "detalles": null,
    "correlation_id": "df6f50bc67d74ba9"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 120_reembolsos_costos_post_costos_201

Carpeta: 01 Costos (POST) - Caso: costo 201 transporte JSON

`POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/costos`

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
  "etapa": "transporte",
  "monto": 150.5
}
```

**Response - 201 CREATED** (95 ms, 85 bytes):

```http
Content-Type: application/json
Content-Length: 85
X-Correlation-ID: c8c0e626b3804e9d
```

```json
{
  "id": 46,
  "devolucion_id": 81,
  "etapa": "transporte",
  "monto": 150.5,
  "fecha": "2026-10-22"
}
```

**Verificaciones:**

- ok: HTTP 201
- ok: Trae X-Correlation-ID

## 121_reembolsos_costos_post_costos_201_xml

Carpeta: 01 Costos (POST) - Caso: costo 201 almacenamiento XML

`POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/costos`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/xml
Accept: application/xml
```

**Request - body:**

```
<costo>
  <devolucion_id>81</devolucion_id>
  <etapa>almacenamiento</etapa>
  <monto>45.00</monto>
</costo>
```

**Response - 201 CREATED** (134 ms, 179 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 179
X-Correlation-ID: aceae34fe9524a98
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<respuesta><id>47</id><devolucion_id>81</devolucion_id><etapa>almacenamiento</etapa><monto>45.0</monto><fecha>2026-10-22</fecha></respuesta>
```

**Verificaciones:**

- ok: HTTP 201
- ok: Trae X-Correlation-ID

## 122_reembolsos_costos_post_reembolsos_403

Carpeta: 02 Reembolsos (POST) - Caso: reembolso 403 analista

`POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/reembolsos`

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
  "estado": "aprobado",
  "metodo": "transferencia",
  "monto": 1.0
}
```

**Response - 403 FORBIDDEN** (160 ms, 232 bytes):

```http
Content-Type: application/json
Content-Length: 232
X-Correlation-ID: 55d666b54710413a
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "Tu rol no tiene permiso para esta operacion.",
    "detalles": {
      "rol": "Analista de Devoluciones",
      "roles_permitidos": [
        "Encargado de Reembolsos"
      ]
    },
    "correlation_id": "55d666b54710413a"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 123_reembolsos_costos_post_reembolsos_400

Carpeta: 02 Reembolsos (POST) - Caso: reembolso 400 estado invalido

`POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/reembolsos`

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
  "estado": "quizas",
  "metodo": "transferencia",
  "monto": 1.0
}
```

**Response - 400 BAD REQUEST** (81 ms, 147 bytes):

```http
Content-Type: application/json
Content-Length: 147
X-Correlation-ID: 20e5134a4e5c4014
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "estado debe ser aprobado o rechazado.",
    "detalles": null,
    "correlation_id": "20e5134a4e5c4014"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 124_reembolsos_costos_post_reembolsos_400

Carpeta: 02 Reembolsos (POST) - Caso: reembolso 400 metodo invalido

`POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/reembolsos`

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
  "estado": "aprobado",
  "metodo": "cheque",
  "monto": 1.0
}
```

**Response - 400 BAD REQUEST** (77 ms, 139 bytes):

```http
Content-Type: application/json
Content-Length: 139
X-Correlation-ID: ed27ea16edb9494c
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Metodo de reembolso invalido.",
    "detalles": null,
    "correlation_id": "ed27ea16edb9494c"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 125_reembolsos_costos_post_reembolsos_400

Carpeta: 02 Reembolsos (POST) - Caso: reembolso 400 devolucion_id invalido

`POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/reembolsos`

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
  "estado": "aprobado",
  "metodo": "transferencia",
  "monto": 1.0
}
```

**Response - 400 BAD REQUEST** (74 ms, 149 bytes):

```http
Content-Type: application/json
Content-Length: 149
X-Correlation-ID: a14237b96aaf4a28
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "devolucion_id debe ser entero positivo.",
    "detalles": null,
    "correlation_id": "a14237b96aaf4a28"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 126_reembolsos_costos_post_reembolsos_404

Carpeta: 02 Reembolsos (POST) - Caso: reembolso 404 devolucion inexistente

`POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/reembolsos`

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
  "estado": "aprobado",
  "metodo": "transferencia",
  "monto": 1.0
}
```

**Response - 404 NOT FOUND** (177 ms, 144 bytes):

```http
Content-Type: application/json
Content-Length: 144
X-Correlation-ID: fec817b68cde47ee
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe la devolucion 999999.",
    "detalles": null,
    "correlation_id": "fec817b68cde47ee"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 127_reembolsos_costos_post_reembolsos_409

Carpeta: 02 Reembolsos (POST) - Caso: reembolso 409 monto excedido

`POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/reembolsos`

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
  "estado": "aprobado",
  "metodo": "transferencia",
  "monto": 9999999.99
}
```

**Response - 409 CONFLICT** (99 ms, 165 bytes):

```http
Content-Type: application/json
Content-Length: 165
X-Correlation-ID: 5fc7df7722014db0
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "monto_excedido",
    "mensaje": "El reembolso excede el valor devuelto.",
    "detalles": {
      "maximo": 193.77
    },
    "correlation_id": "5fc7df7722014db0"
  }
}
```

**Verificaciones:**

- ok: HTTP 409
- ok: error.tipo = monto_excedido
- ok: Trae X-Correlation-ID
- ok: informa el maximo

## 128_reembolsos_costos_post_reembolsos_201

Carpeta: 02 Reembolsos (POST) - Caso: reembolso 201 aprobado

`POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/reembolsos`

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
  "estado": "aprobado",
  "metodo": "transferencia",
  "monto": 1.0
}
```

**Response - 201 CREATED** (119 ms, 140 bytes):

```http
Content-Type: application/json
Content-Length: 140
Location: /api/v1/reembolsos-costos/reembolsos/11
X-Correlation-ID: 7e31dbd2d3dc462e
```

```json
{
  "id": 11,
  "devolucion_id": 81,
  "monto": 1.0,
  "metodo": "transferencia",
  "estado": "aprobado",
  "fecha_resolucion": "2026-10-22T00:42:03.019623+00:00"
}
```

**Verificaciones:**

- ok: HTTP 201
- ok: Trae X-Correlation-ID
- ok: aprobado

## 129_reembolsos_costos_post_reembolsos_409_xml

Carpeta: 02 Reembolsos (POST) - Caso: reembolso 409 duplicado XML

`POST http://{{vm_host}}:8005/api/v1/reembolsos-costos/reembolsos`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/xml
Accept: application/xml
```

**Request - body:**

```
<reembolso>
  <devolucion_id>81</devolucion_id>
  <monto>1.00</monto>
  <metodo>transferencia</metodo>
  <estado>aprobado</estado>
</reembolso>
```

**Response - 409 CONFLICT** (91 ms, 229 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 229
X-Correlation-ID: 38448f016c7449dc
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<error><codigo>409</codigo><tipo>reembolso_duplicado</tipo><mensaje>La devolucion ya tiene un reembolso valido.</mensaje><detalles /><correlation_id>38448f016c7449dc</correlation_id></error>
```

**Verificaciones:**

- ok: HTTP 409
- ok: error.tipo = reembolso_duplicado
- ok: Trae X-Correlation-ID

## 130_reembolsos_costos_get_reembolsos_200

Carpeta: 03 Consulta (GET) - Caso: reembolsos 200 lista

`GET http://{{vm_host}}:8005/api/v1/reembolsos-costos/reembolsos`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (141 ms, 1626 bytes):

```http
Content-Type: application/json
Content-Length: 1626
X-Correlation-ID: d60f809c77114ef6
```

```json
{
  "datos": [
    {
      "id": 11,
      "devolucion_id": 81,
      "monto": 1.0,
      "metodo": "transferencia",
      "estado": "aprobado",
      "fecha_resolucion": "2026-10-22T00:42:03.019623+00:00",
      "folio_devolucion": "DEV-2026-0081",
      "encargado": "Carla Trevino"
    },
    {
      "id": 8,
      "devolucion_id": 35,
      "monto": 112.1,
      "metodo": "tarjeta",
      "estado": "aprobado",
      "fecha_resolucion": "2026-09-07T14:26:38.215023+00:00",
      "folio_devolucion": "DEV-2026-0035",
      "encargado": "Carla Trevino"
    },
    {
      "id": 7,
      "devolucion_id": 33,
      "monto": 236.45,
      "metodo": "transferencia",
      "estado": "aprobado",
      "fecha_resolucion": "2026-09-06T23:38:34.507396+00:00",
      "folio_devolucion": "DEV-2026-0033",
      "encargado": "Carla Trevino"
    },
    {
      "id": 5,
      "devolucion_id": 32,
      "monto": 57.29,
      "metodo": "tarjeta",
      "estado": "aprobado",
      "fecha_resolucion": "2026-09-06T23:20:35.290510+00:00",
      "folio_devolucion": "DEV-2026-0032",
      "encargado": "Carla Trevino"
    },
    {
      "id": 4,
      "devolucion_id": 31,
      "monto": 81.3,
      "metodo": "tarjeta",
      "estado": "aprobado",
      "fecha_resolucion": "2026-09-06T23:20:35.290510+00:00",
      "folio_devolucion": "DEV-2026-0031",
      "encargado": "Carla Trevino"
    },
    {
      "id": 3,
      "devolucion_id": 30,
      "monto": 116.62,
      "metodo": "transferencia",
      "estado": "aprobado",
      "fecha_resolucion": "2026-09-06T23:20:35.290510+00:00",
      "folio_devolucion": "DEV-2026-0030",
      "encargado": "Carla Trevino"
    },
    {
      "id": 2,
      "devolucion_id": 29,
      "monto": 161.8,
      "metodo": "transferencia",
      "estado": "aprobado",
      "fecha_resolucion": "2026-09-06T23:20:35.290510+00:00",
      "folio_devolucion": "DEV-2026-0029",
      "encargado": "Carla Trevino"
    },
    {
      "id": 1,
      "devolucion_id": 28,
      "monto": 25.92,
      "metodo": "transferencia",
      "estado": "aprobado",
      "fecha_resolucion": "2026-09-06T23:20:35.290510+00:00",
      "folio_devolucion": "DEV-2026-0028",
      "encargado": "Carla Trevino"
    }
  ]
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: trae datos

## 131_reembolsos_costos_get_reembolsos_200_xml

Carpeta: 03 Consulta (GET) - Caso: reembolsos 200 analista XML

`GET http://{{vm_host}}:8005/api/v1/reembolsos-costos/reembolsos`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/xml
```

**Response - 200 OK** (84 ms, 2347 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 2347
X-Correlation-ID: 7c71b9b0bf224f72
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<respuesta><datos><item><id>11</id><devolucion_id>81</devolucion_id><monto>1.0</monto><metodo>transferencia</metodo><estado>aprobado</estado><fecha_resolucion>2026-10-22T00:42:03.019623+00:00</fecha_resolucion><folio_devolucion>DEV-2026-0081</folio_devolucion><encargado>Carla Trevino</encargado></item><item><id>8</id><devolucion_id>35</devolucion_id><monto>112.1</monto><metodo>tarjeta</metodo><estado>aprobado</estado><fecha_resolucion>2026-09-07T14:26:38.215023+00:00</fecha_resolucion><folio_devolucion>DEV-2026-0035</folio_devolucion><encargado>Carla Trevino</encargado></item><item><id>7</id><devolucion_id>33</devolucion_id><monto>236.45</monto><metodo>transferencia</metodo><estado>aprobado</estado><fecha_resolucion>2026-09-06T23:38:34.507396+00:00</fecha_resolucion><folio_devolucion>DEV-2026-0033</folio_devolucion><encargado>Carla Trevino</encargado></item><item><id>5</id><devolucion_id>32</devolucion_id><monto>57.29</monto><metodo>tarjeta</metodo><estado>aprobado</estado><fecha_resolucion>2026-09-06T23:20:35.290510+00:00</fecha_resolucion><folio_devolucion>DEV-2026-0032</folio_devolucion><encargado>Carla Trevino</encargado></item><item><id>4</id><devolucion_id>31</devolucion_id><monto>81.3</monto><metodo>tarjeta</metodo><estado>aprobado</estado><fecha_resolucion>2026-09-06T23:20:35.290510+00:00</fecha_resolucion><folio_devolucion>DEV-2026-0031</folio_devolucion><encargado>Carla Trevino</encargado></item><item><id>3</id><devolucion_id>30</devolucion_id><monto>116.62</monto><metodo>transferencia</metodo><estado>aprobado</estado><fecha_resolucion>2026-09-06T23:20:35.290510+00:00</fecha_resolucion><folio_devolucion>DEV-2026-0030</folio_devolucion><encargado>Carla Trevino</encargado></item><item><id>2</id><devolucion_id>29</devolucion_id><monto>161.8</monto><metodo>transferencia</metodo><estado>aprobado</estado><fecha_resolucion>2026-09-06T23:20:35.290510+00:00</fecha_resolucion><folio_devolucion>DEV-2026-0029</folio_devolucion><encargado>Carla Trevino</encargado></item><item><id>1</id><devolucion_id>28</devolucion_id><monto>25.92</monto><metodo>transferencia</metodo><estado>aprobado</estado><fecha_resolucion>2026-09-06T23:20:35.290510+00:00</fecha_resolucion><folio_devolucion>DEV-2026-0028</folio_devolucion><encargado>Carla Trevino</encargado></item></datos></respuesta>
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 132_reembolsos_costos_get_reembolsos_403

Carpeta: 03 Consulta (GET) - Caso: reembolsos 403 cliente

`GET http://{{vm_host}}:8005/api/v1/reembolsos-costos/reembolsos`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 403 FORBIDDEN** (78 ms, 242 bytes):

```http
Content-Type: application/json
Content-Length: 242
X-Correlation-ID: fa8d83dbf4f64cdf
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
        "Encargado de Reembolsos",
        "Analista de Devoluciones"
      ]
    },
    "correlation_id": "fa8d83dbf4f64cdf"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 133_reembolsos_costos_get_reembolsos_401

Carpeta: 03 Consulta (GET) - Caso: reembolsos 401 token invalido

`GET http://{{vm_host}}:8005/api/v1/reembolsos-costos/reembolsos`

**Request - headers:**

```http
Authorization: Bearer esto-no-es-un-token
Accept: application/json
```

**Response - 401 UNAUTHORIZED** (75 ms, 136 bytes):

```http
Content-Type: application/json
Content-Length: 136
X-Correlation-ID: a3fc806aad8d4599
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "token_invalido",
    "mensaje": "El token no es valido.",
    "detalles": null,
    "correlation_id": "a3fc806aad8d4599"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = token_invalido
- ok: Trae X-Correlation-ID

## 134_reembolsos_costos_get_costos_id_200

Carpeta: 03 Consulta (GET) - Caso: costos 200 desglose

`GET http://{{vm_host}}:8005/api/v1/reembolsos-costos/costos/81`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (96 ms, 174 bytes):

```http
Content-Type: application/json
Content-Length: 174
X-Correlation-ID: e23feccfc6564031
```

```json
{
  "devolucion_id": 81,
  "desglose": [
    {
      "etapa": "almacenamiento",
      "subtotal": 45.0
    },
    {
      "etapa": "reembolso",
      "subtotal": 1.0
    },
    {
      "etapa": "transporte",
      "subtotal": 150.5
    }
  ],
  "costo_total": 196.5
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: desglose y total

## 135_reembolsos_costos_get_costos_id_200_xml

Carpeta: 03 Consulta (GET) - Caso: costos 200 analista XML

`GET http://{{vm_host}}:8005/api/v1/reembolsos-costos/costos/81`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/xml
```

**Response - 200 OK** (181 ms, 340 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 340
X-Correlation-ID: 070d74faaa1a465d
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<respuesta><devolucion_id>81</devolucion_id><desglose><item><etapa>almacenamiento</etapa><subtotal>45.0</subtotal></item><item><etapa>reembolso</etapa><subtotal>1.0</subtotal></item><item><etapa>transporte</etapa><subtotal>150.5</subtotal></item></desglose><costo_total>196.5</costo_total></respuesta>
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 136_reembolsos_costos_get_costos_id_403

Carpeta: 03 Consulta (GET) - Caso: costos 403 centro

`GET http://{{vm_host}}:8005/api/v1/reembolsos-costos/costos/81`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 403 FORBIDDEN** (73 ms, 271 bytes):

```http
Content-Type: application/json
Content-Length: 271
X-Correlation-ID: 89589552b31b43f0
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
        "Encargado de Reembolsos",
        "Analista de Devoluciones"
      ]
    },
    "correlation_id": "89589552b31b43f0"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 137_reembolsos_costos_get_costos_id_404

Carpeta: 03 Consulta (GET) - Caso: costos 404 devolucion inexistente

`GET http://{{vm_host}}:8005/api/v1/reembolsos-costos/costos/999999`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 404 NOT FOUND** (86 ms, 144 bytes):

```http
Content-Type: application/json
Content-Length: 144
X-Correlation-ID: 154f10a16cb54dba
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe la devolucion 999999.",
    "detalles": null,
    "correlation_id": "154f10a16cb54dba"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

