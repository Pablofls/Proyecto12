# Ejecuciones reales - `evidencias`

Salida de `newman run docs/postman/evidencias.postman_collection.json` contra la VM (2026-10-22 00:40 UTC). Verificaciones: 121 (0 fallidas). Tokens, contrasenas e IP de la VM estan ocultos (`***jwt***`, `***`, `{{vm_host}}`).

## 173_evidencias_get_health_200

Carpeta: 00 Preparacion (crea una devolucion propia para adjuntar) - Caso: health 200

`GET http://{{vm_host}}:8007/health`

**Request - headers:**

```http
Accept: application/json
```

**Response - 200 OK** (99 ms, 221 bytes):

```http
Content-Type: application/json
Content-Length: 221
X-Correlation-ID: e53ede69f7ad4aed
```

```json
{
  "servicio": "evidencias",
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
    },
    "almacen_privado": {
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
- ok: mongodb ok
- ok: almacen_privado ok

## 174_evidencias_post_raiz_201

Carpeta: 01 Alta (POST) - Caso: alta 201 comentario JSON

`POST http://{{vm_host}}:8007/api/v1/evidencias`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 83,
  "tipo": "comentario",
  "etapa": "solicitud",
  "comentario": "El sello del empaque llego roto."
}
```

**Response - 201 CREATED** (100 ms, 91 bytes):

```http
Content-Type: application/json
Content-Length: 91
Location: /api/v1/evidencias/14
X-Correlation-ID: 0d5128a315cb423e
```

```json
{
  "id": 14,
  "devolucion_id": 83,
  "tipo": "comentario",
  "metadatos_id": "6ad95b931f4384d46cf80035"
}
```

**Verificaciones:**

- ok: HTTP 201
- ok: Trae X-Correlation-ID
- ok: tipo comentario

## 175_evidencias_post_raiz_201_xml

Carpeta: 01 Alta (POST) - Caso: alta 201 comentario XML

`POST http://{{vm_host}}:8007/api/v1/evidencias`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/xml
Accept: application/xml
```

**Request - body:**

```
<evidencia>
  <devolucion_id>83</devolucion_id>
  <tipo>comentario</tipo>
  <etapa>solicitud</etapa>
  <comentario>Segundo comentario en XML.</comentario>
</evidencia>
```

**Response - 201 CREATED** (199 ms, 182 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 182
Location: /api/v1/evidencias/15
X-Correlation-ID: 4e0483edbac14c0b
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<evidencia><id>15</id><devolucion_id>83</devolucion_id><tipo>comentario</tipo><metadatos_id>6ad95b93c703a34b44966136</metadatos_id></evidencia>
```

**Verificaciones:**

- ok: HTTP 201
- ok: Trae X-Correlation-ID

## 176_evidencias_post_raiz_201

Carpeta: 01 Alta (POST) - Caso: alta 201 archivo PNG

`POST http://{{vm_host}}:8007/api/v1/evidencias`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Request - body:**

```
devolucion_id: 83
etapa: solicitud
archivo: (archivo) evidencia_prueba.png
```

**Response - 201 CREATED** (155 ms, 91 bytes):

```http
Content-Type: application/json
Content-Length: 91
Location: /api/v1/evidencias/16
X-Correlation-ID: f43b72be18d74808
```

```json
{
  "id": 16,
  "devolucion_id": 83,
  "tipo": "fotografia",
  "metadatos_id": "6ad95b931f4384d46cf80036"
}
```

**Verificaciones:**

- ok: HTTP 201
- ok: Trae X-Correlation-ID
- ok: es fotografia

## 177_evidencias_post_raiz_400

Carpeta: 01 Alta (POST) - Caso: alta 400 comentario vacio

`POST http://{{vm_host}}:8007/api/v1/evidencias`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 83,
  "tipo": "comentario",
  "etapa": "solicitud",
  "comentario": ""
}
```

**Response - 400 BAD REQUEST** (89 ms, 133 bytes):

```http
Content-Type: application/json
Content-Length: 133
X-Correlation-ID: 86f3de960df44fea
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Comentario obligatorio.",
    "detalles": null,
    "correlation_id": "86f3de960df44fea"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 178_evidencias_post_raiz_400

Carpeta: 01 Alta (POST) - Caso: alta 400 tipo no permitido en JSON

`POST http://{{vm_host}}:8007/api/v1/evidencias`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 83,
  "tipo": "fotografia",
  "etapa": "solicitud",
  "comentario": "El sello del empaque llego roto."
}
```

**Response - 400 BAD REQUEST** (80 ms, 180 bytes):

```http
Content-Type: application/json
Content-Length: 180
X-Correlation-ID: 7d49519ce4aa46cc
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Para archivos usa multipart/form-data; JSON/XML solo para comentarios.",
    "detalles": null,
    "correlation_id": "7d49519ce4aa46cc"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 179_evidencias_post_raiz_400

Carpeta: 01 Alta (POST) - Caso: alta 400 etapa invalida

`POST http://{{vm_host}}:8007/api/v1/evidencias`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 83,
  "tipo": "comentario",
  "etapa": "volando",
  "comentario": "El sello del empaque llego roto."
}
```

**Response - 400 BAD REQUEST** (93 ms, 129 bytes):

```http
Content-Type: application/json
Content-Length: 129
X-Correlation-ID: 36906c24aa374840
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Etapa no permitida.",
    "detalles": null,
    "correlation_id": "36906c24aa374840"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 180_evidencias_post_raiz_400

Carpeta: 01 Alta (POST) - Caso: alta 400 multipart sin archivo

`POST http://{{vm_host}}:8007/api/v1/evidencias`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Request - body:**

```
devolucion_id: 83
```

**Response - 400 BAD REQUEST** (76 ms, 133 bytes):

```http
Content-Type: application/json
Content-Length: 133
X-Correlation-ID: 87eec874930e442e
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Falta el campo archivo.",
    "detalles": null,
    "correlation_id": "87eec874930e442e"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 181_evidencias_post_raiz_401

Carpeta: 01 Alta (POST) - Caso: alta 401 sin token

`POST http://{{vm_host}}:8007/api/v1/evidencias`

**Request - headers:**

```http
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 83,
  "tipo": "comentario",
  "etapa": "solicitud",
  "comentario": "El sello del empaque llego roto."
}
```

**Response - 401 UNAUTHORIZED** (142 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: 0c6c83cd7ca14596
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "0c6c83cd7ca14596"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = no_autenticado
- ok: Trae X-Correlation-ID

## 182_evidencias_post_raiz_401

Carpeta: 01 Alta (POST) - Caso: alta 401 token invalido

`POST http://{{vm_host}}:8007/api/v1/evidencias`

**Request - headers:**

```http
Authorization: Bearer esto-no-es-un-token
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 83,
  "tipo": "comentario",
  "etapa": "solicitud",
  "comentario": "El sello del empaque llego roto."
}
```

**Response - 401 UNAUTHORIZED** (75 ms, 136 bytes):

```http
Content-Type: application/json
Content-Length: 136
X-Correlation-ID: fcc14a01d0c14060
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "token_invalido",
    "mensaje": "El token no es valido.",
    "detalles": null,
    "correlation_id": "fcc14a01d0c14060"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = token_invalido
- ok: Trae X-Correlation-ID

## 183_evidencias_post_raiz_403

Carpeta: 01 Alta (POST) - Caso: alta 403 analista

`POST http://{{vm_host}}:8007/api/v1/evidencias`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 83,
  "tipo": "comentario",
  "etapa": "solicitud",
  "comentario": "El sello del empaque llego roto."
}
```

**Response - 403 FORBIDDEN** (74 ms, 228 bytes):

```http
Content-Type: application/json
Content-Length: 228
X-Correlation-ID: 4155461251fa42c5
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
        "Cliente",
        "Inspector"
      ]
    },
    "correlation_id": "4155461251fa42c5"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 184_evidencias_post_raiz_403

Carpeta: 01 Alta (POST) - Caso: alta 403 otro cliente

`POST http://{{vm_host}}:8007/api/v1/evidencias`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 83,
  "tipo": "comentario",
  "etapa": "solicitud",
  "comentario": "El sello del empaque llego roto."
}
```

**Response - 403 FORBIDDEN** (88 ms, 145 bytes):

```http
Content-Type: application/json
Content-Length: 145
X-Correlation-ID: e474c073db1d4760
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "No tienes acceso a esa devolucion.",
    "detalles": null,
    "correlation_id": "e474c073db1d4760"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 185_evidencias_post_raiz_403

Carpeta: 01 Alta (POST) - Caso: alta 403 inspector sin inspeccion

`POST http://{{vm_host}}:8007/api/v1/evidencias`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 83,
  "tipo": "comentario",
  "etapa": "inspeccion",
  "comentario": "El sello del empaque llego roto."
}
```

**Response - 403 FORBIDDEN** (176 ms, 155 bytes):

```http
Content-Type: application/json
Content-Length: 155
X-Correlation-ID: cf3c75df49834900
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "La inspeccion no esta asignada a tu usuario.",
    "detalles": null,
    "correlation_id": "cf3c75df49834900"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 186_evidencias_post_raiz_404

Carpeta: 01 Alta (POST) - Caso: alta 404 devolucion inexistente

`POST http://{{vm_host}}:8007/api/v1/evidencias`

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
  "tipo": "comentario",
  "etapa": "solicitud",
  "comentario": "El sello del empaque llego roto."
}
```

**Response - 404 NOT FOUND** (87 ms, 137 bytes):

```http
Content-Type: application/json
Content-Length: 137
X-Correlation-ID: 1313c6542a224c74
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "La devolucion no existe.",
    "detalles": null,
    "correlation_id": "1313c6542a224c74"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 187_evidencias_post_raiz_409

Carpeta: 01 Alta (POST) - Caso: alta 409 etapa no permitida al cliente

`POST http://{{vm_host}}:8007/api/v1/evidencias`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 83,
  "tipo": "comentario",
  "etapa": "recoleccion",
  "comentario": "El sello del empaque llego roto."
}
```

**Response - 409 CONFLICT** (85 ms, 173 bytes):

```http
Content-Type: application/json
Content-Length: 173
X-Correlation-ID: 692dcfae7ecc4576
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "estado_no_permite",
    "mensaje": "El cliente solo adjunta durante la solicitud o revision.",
    "detalles": null,
    "correlation_id": "692dcfae7ecc4576"
  }
}
```

**Verificaciones:**

- ok: HTTP 409
- ok: error.tipo = estado_no_permite
- ok: Trae X-Correlation-ID

## 188_evidencias_post_raiz_415

Carpeta: 01 Alta (POST) - Caso: alta 415 archivo no soportado

`POST http://{{vm_host}}:8007/api/v1/evidencias`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Request - body:**

```
devolucion_id: 83
etapa: solicitud
archivo: (archivo) no_es_imagen.txt
```

**Response - 415 UNSUPPORTED MEDIA TYPE** (87 ms, 159 bytes):

```http
Content-Type: application/json
Content-Length: 159
X-Correlation-ID: 878e4e26b2ef4160
```

```json
{
  "error": {
    "codigo": 415,
    "tipo": "formato_no_soportado",
    "mensaje": "Solo se permiten JPG, PNG o PDF reales.",
    "detalles": null,
    "correlation_id": "878e4e26b2ef4160"
  }
}
```

**Verificaciones:**

- ok: HTTP 415
- ok: error.tipo = formato_no_soportado
- ok: Trae X-Correlation-ID

## 189_evidencias_get_raiz_200

Carpeta: 02 Consulta (GET) - Caso: listar 200 cliente

`GET http://{{vm_host}}:8007/api/v1/evidencias?devolucion_id=83&pagina=1&por_pagina=5`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (151 ms, 797 bytes):

```http
Content-Type: application/json
Content-Length: 797
X-Correlation-ID: f748685423b3477c
```

```json
{
  "datos": [
    {
      "id": 16,
      "devolucion_id": 83,
      "usuario_id": 11,
      "tipo": "fotografia",
      "etapa": "solicitud",
      "comentario": null,
      "nombre_original": "evidencia_prueba.png",
      "mime_type": "image/png",
      "tamano_bytes": 70,
      "fecha_registro": "2026-10-22T00:40:51.955850+00:00"
    },
    {
      "id": 15,
      "devolucion_id": 83,
      "usuario_id": 11,
      "tipo": "comentario",
      "etapa": "solicitud",
      "comentario": "Segundo comentario en XML.",
      "nombre_original": null,
      "mime_type": null,
      "tamano_bytes": null,
      "fecha_registro": "2026-10-22T00:40:51.822996+00:00"
    },
    {
      "id": 14,
      "devolucion_id": 83,
      "usuario_id": 11,
      "tipo": "comentario",
      "etapa": "solicitud",
      "comentario": "El sello del empaque llego roto.",
      "nombre_original": null,
      "mime_type": null,
      "tamano_bytes": null,
      "fecha_registro": "2026-10-22T00:40:51.599811+00:00"
    }
  ],
  "paginacion": {
    "pagina": 1,
    "por_pagina": 5,
    "total": 3,
    "paginas": 1
  }
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: trae las tres

## 190_evidencias_get_raiz_200_xml

Carpeta: 02 Consulta (GET) - Caso: listar 200 analista XML

`GET http://{{vm_host}}:8007/api/v1/evidencias?devolucion_id=83`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/xml
```

**Response - 200 OK** (88 ms, 1109 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 1109
X-Correlation-ID: 48315d42b5c34de9
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<evidencias><datos><item><id>16</id><devolucion_id>83</devolucion_id><usuario_id>11</usuario_id><tipo>fotografia</tipo><etapa>solicitud</etapa><comentario /><nombre_original>evidencia_prueba.png</nombre_original><mime_type>image/png</mime_type><tamano_bytes>70</tamano_bytes><fecha_registro>2026-10-22T00:40:51.955850+00:00</fecha_registro></item><item><id>15</id><devolucion_id>83</devolucion_id><usuario_id>11</usuario_id><tipo>comentario</tipo><etapa>solicitud</etapa><comentario>Segundo comentario en XML.</comentario><nombre_original /><mime_type /><tamano_bytes /><fecha_registro>2026-10-22T00:40:51.822996+00:00</fecha_registro></item><item><id>14</id><devolucion_id>83</devolucion_id><usuario_id>11</usuario_id><tipo>comentario</tipo><etapa>solicitud</etapa><comentario>El sello del empaque llego roto.</comentario><nombre_original /><mime_type /><tamano_bytes /><fecha_registro>2026-10-22T00:40:51.599811+00:00</fecha_registro></item></datos><paginacion><pagina>1</pagina><por_pagina>20</por_pagina><total>3</total><paginas>1</paginas></paginacion></evidencias>
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 191_evidencias_get_raiz_400

Carpeta: 02 Consulta (GET) - Caso: listar 400 sin devolucion_id

`GET http://{{vm_host}}:8007/api/v1/evidencias`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 400 BAD REQUEST** (76 ms, 149 bytes):

```http
Content-Type: application/json
Content-Length: 149
X-Correlation-ID: f58ca140db534742
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "devolucion_id debe ser entero positivo.",
    "detalles": null,
    "correlation_id": "f58ca140db534742"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 192_evidencias_get_raiz_403

Carpeta: 02 Consulta (GET) - Caso: listar 403 otro cliente

`GET http://{{vm_host}}:8007/api/v1/evidencias?devolucion_id=83`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 403 FORBIDDEN** (97 ms, 145 bytes):

```http
Content-Type: application/json
Content-Length: 145
X-Correlation-ID: c0c26e1cb9b0492e
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "No tienes acceso a esa devolucion.",
    "detalles": null,
    "correlation_id": "c0c26e1cb9b0492e"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 193_evidencias_get_raiz_404

Carpeta: 02 Consulta (GET) - Caso: listar 404 devolucion inexistente

`GET http://{{vm_host}}:8007/api/v1/evidencias?devolucion_id=999999`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 404 NOT FOUND** (182 ms, 137 bytes):

```http
Content-Type: application/json
Content-Length: 137
X-Correlation-ID: 20de74c6801a4ba8
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "La devolucion no existe.",
    "detalles": null,
    "correlation_id": "20de74c6801a4ba8"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 194_evidencias_get_id_200

Carpeta: 02 Consulta (GET) - Caso: detalle 200 con metadatos

`GET http://{{vm_host}}:8007/api/v1/evidencias/14`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (95 ms, 398 bytes):

```http
Content-Type: application/json
Content-Length: 398
X-Correlation-ID: b8a2d5b87769485b
```

```json
{
  "id": 14,
  "devolucion_id": 83,
  "usuario_id": 11,
  "tipo": "comentario",
  "etapa": "solicitud",
  "comentario": "El sello del empaque llego roto.",
  "nombre_original": null,
  "mime_type": null,
  "tamano_bytes": null,
  "fecha_registro": "2026-10-22T00:40:51.599811+00:00",
  "metadatos": [
    {
      "evidencia_id": 14,
      "devolucion_id": 83,
      "tipo": "comentario",
      "etapa": "solicitud",
      "nombre_original": null,
      "mime_type": null,
      "tamano_bytes": null
    }
  ]
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: no expone bucket ni objeto
- ok: trae metadatos

## 195_evidencias_get_id_404

Carpeta: 02 Consulta (GET) - Caso: detalle 404 inexistente

`GET http://{{vm_host}}:8007/api/v1/evidencias/999999`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 404 NOT FOUND** (86 ms, 135 bytes):

```http
Content-Type: application/json
Content-Length: 135
X-Correlation-ID: 14d1543f9c4b416c
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Evidencia inexistente.",
    "detalles": null,
    "correlation_id": "14d1543f9c4b416c"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 196_evidencias_get_id_403

Carpeta: 02 Consulta (GET) - Caso: detalle 403 otro cliente

`GET http://{{vm_host}}:8007/api/v1/evidencias/14`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 403 FORBIDDEN** (85 ms, 145 bytes):

```http
Content-Type: application/json
Content-Length: 145
X-Correlation-ID: 5246b7c32df64bd4
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "No tienes acceso a esa devolucion.",
    "detalles": null,
    "correlation_id": "5246b7c32df64bd4"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 197_evidencias_get_id_enlace_200

Carpeta: 02 Consulta (GET) - Caso: enlace 200 firmado

`GET http://{{vm_host}}:8007/api/v1/evidencias/16/enlace`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (88 ms, 159 bytes):

```http
Content-Type: application/json
Content-Length: 159
X-Correlation-ID: cbcec27243764258
```

```json
{
  "url_relativa": "/api/v1/evidencias/16/archivo?exp=1792630554&firma=7b315686252752c15e4aa739b5205aa0bb15c4bc49b9cdc20c5ac870809b33b7",
  "vigencia_segundos": 900
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: vigencia 900 s

## 198_evidencias_get_id_enlace_409

Carpeta: 02 Consulta (GET) - Caso: enlace 409 comentario sin archivo

`GET http://{{vm_host}}:8007/api/v1/evidencias/14/enlace`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 409 CONFLICT** (174 ms, 151 bytes):

```http
Content-Type: application/json
Content-Length: 151
X-Correlation-ID: bf3169d97cd04c20
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "sin_archivo",
    "mensaje": "Un comentario no tiene archivo asociado.",
    "detalles": null,
    "correlation_id": "bf3169d97cd04c20"
  }
}
```

**Verificaciones:**

- ok: HTTP 409
- ok: error.tipo = sin_archivo
- ok: Trae X-Correlation-ID

## 199_evidencias_get_evidencia_id_archivo_200

Carpeta: 02 Consulta (GET) - Caso: archivo 200 con enlace firmado

`GET http://{{vm_host}}:8007/api/v1/evidencias/16/archivo?exp=1792630554&firma=7b315686252752c15e4aa739b5205aa0bb15c4bc49b9cdc20c5ac870809b33b7`

**Request - headers:**

```http
Accept: application/json
```

**Response - 200 OK** (86 ms, 70 bytes):

```http
Content-Disposition: attachment; filename=evidencia_prueba.png
Content-Type: image/png
Content-Length: 70
X-Correlation-ID: 2bfa3f8247314372
```

```json
�PNG

   IHDR         ĉ   IDATx�c���P �����!    IEND�B`�
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: es una imagen PNG

## 200_evidencias_get_id_archivo_200

Carpeta: 02 Consulta (GET) - Caso: archivo 200 con Bearer

`GET http://{{vm_host}}:8007/api/v1/evidencias/16/archivo`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (91 ms, 70 bytes):

```http
Content-Disposition: attachment; filename=evidencia_prueba.png
Content-Type: image/png
Content-Length: 70
X-Correlation-ID: 865a88a89aba46f7
```

```json
�PNG

   IHDR         ĉ   IDATx�c���P �����!    IEND�B`�
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: es una imagen PNG

## 201_evidencias_get_id_archivo_401

Carpeta: 02 Consulta (GET) - Caso: archivo 401 sin firma ni token

`GET http://{{vm_host}}:8007/api/v1/evidencias/16/archivo`

**Request - headers:**

```http
Accept: application/json
```

**Response - 401 UNAUTHORIZED** (73 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: 108b5692ab3c47cc
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "108b5692ab3c47cc"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = no_autenticado
- ok: Trae X-Correlation-ID

## 202_evidencias_get_id_archivo_404

Carpeta: 02 Consulta (GET) - Caso: archivo 404 inexistente

`GET http://{{vm_host}}:8007/api/v1/evidencias/999999/archivo`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 404 NOT FOUND** (143 ms, 135 bytes):

```http
Content-Type: application/json
Content-Length: 135
X-Correlation-ID: be4d869e8fdf48bb
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Evidencia inexistente.",
    "detalles": null,
    "correlation_id": "be4d869e8fdf48bb"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 203_evidencias_delete_id_403

Carpeta: 03 Retiro (DELETE) - Caso: retiro 403 analista

`DELETE http://{{vm_host}}:8007/api/v1/evidencias/15`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 403 FORBIDDEN** (72 ms, 228 bytes):

```http
Content-Type: application/json
Content-Length: 228
X-Correlation-ID: ec4dc1d8014a4112
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
        "Cliente",
        "Inspector"
      ]
    },
    "correlation_id": "ec4dc1d8014a4112"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 204_evidencias_delete_id_403

Carpeta: 03 Retiro (DELETE) - Caso: retiro 403 otro cliente

`DELETE http://{{vm_host}}:8007/api/v1/evidencias/15`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 403 FORBIDDEN** (88 ms, 145 bytes):

```http
Content-Type: application/json
Content-Length: 145
X-Correlation-ID: 2d96c9ac8b514514
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "No tienes acceso a esa devolucion.",
    "detalles": null,
    "correlation_id": "2d96c9ac8b514514"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 205_evidencias_delete_id_200

Carpeta: 03 Retiro (DELETE) - Caso: retiro 200 exitoso

`DELETE http://{{vm_host}}:8007/api/v1/evidencias/15`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (90 ms, 27 bytes):

```http
Content-Type: application/json
Content-Length: 27
X-Correlation-ID: b7c705483d3e45c7
```

```json
{
  "id": 15,
  "eliminada": true
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: eliminada

## 206_evidencias_delete_id_404

Carpeta: 03 Retiro (DELETE) - Caso: retiro 404 ya retirada

`DELETE http://{{vm_host}}:8007/api/v1/evidencias/15`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 404 NOT FOUND** (158 ms, 135 bytes):

```http
Content-Type: application/json
Content-Length: 135
X-Correlation-ID: 889977d0e3c7463e
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Evidencia inexistente.",
    "detalles": null,
    "correlation_id": "889977d0e3c7463e"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 207_evidencias_delete_id_404

Carpeta: 03 Retiro (DELETE) - Caso: retiro 404 inexistente

`DELETE http://{{vm_host}}:8007/api/v1/evidencias/999999`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 404 NOT FOUND** (93 ms, 135 bytes):

```http
Content-Type: application/json
Content-Length: 135
X-Correlation-ID: 1e3406717b4d4fe1
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Evidencia inexistente.",
    "detalles": null,
    "correlation_id": "1e3406717b4d4fe1"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 208_evidencias_post_raiz_201

Carpeta: 04 Inspector (requiere haber corrido la coleccion inspecciones) - Caso: alta 201 inspector en etapa inspeccion

`POST http://{{vm_host}}:8007/api/v1/evidencias`

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
  "tipo": "comentario",
  "etapa": "inspeccion",
  "comentario": "Verificacion visual del empaque."
}
```

**Response - 201 CREATED** (91 ms, 91 bytes):

```http
Content-Type: application/json
Content-Length: 91
Location: /api/v1/evidencias/17
X-Correlation-ID: 7dfd8629407b4e80
```

```json
{
  "id": 17,
  "devolucion_id": 81,
  "tipo": "comentario",
  "metadatos_id": "6ad95b97c703a34b44966137"
}
```

**Verificaciones:**

- ok: HTTP 201
- ok: Trae X-Correlation-ID

