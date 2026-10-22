# Ejecuciones reales - `devoluciones`

Salida de `newman run docs/postman/devoluciones.postman_collection.json` contra la VM (2026-10-22 00:37 UTC). Verificaciones: 85 (0 fallidas). Tokens, contrasenas e IP de la VM estan ocultos (`***jwt***`, `***`, `{{vm_host}}`).

## 026_devoluciones_get_health_200

Carpeta: 00 Preparacion (tokens) - Caso: health 200

`GET http://{{vm_host}}:8002/health`

**Request - headers:**

```http
Accept: application/json
```

**Response - 200 OK** (96 ms, 180 bytes):

```http
Content-Type: application/json
Content-Length: 180
X-Correlation-ID: c6d063c0b2ba4648
```

```json
{
  "servicio": "devoluciones",
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
  }
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: postgresql ok
- ok: redis ok
- ok: mongodb ok

## 027_devoluciones_post_raiz_409

Carpeta: 01 Registro (POST) - Caso: registrar 409 cantidad excedida

`POST http://{{vm_host}}:8002/api/v1/devoluciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "venta_detalle_id": 72,
  "motivo_id": 1,
  "descripcion_problema": "El empaque llego roto y el producto derramado.",
  "cantidad_devuelta": 999
}
```

**Response - 409 CONFLICT** (163 ms, 198 bytes):

```http
Content-Type: application/json
Content-Length: 198
X-Correlation-ID: ef767389cf774f09
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "cantidad_excedida",
    "mensaje": "Solo se pueden devolver 3 articulo(s) de esta linea.",
    "detalles": {
      "disponible": 3,
      "solicitada": 999
    },
    "correlation_id": "ef767389cf774f09"
  }
}
```

**Verificaciones:**

- ok: HTTP 409
- ok: error.tipo = cantidad_excedida
- ok: Trae X-Correlation-ID

## 028_devoluciones_post_raiz_201

Carpeta: 01 Registro (POST) - Caso: registrar 201 exitoso

`POST http://{{vm_host}}:8002/api/v1/devoluciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "venta_detalle_id": 72,
  "motivo_id": 1,
  "descripcion_problema": "El empaque llego roto y el producto derramado.",
  "cantidad_devuelta": 1
}
```

**Response - 201 CREATED** (103 ms, 250 bytes):

```http
Content-Type: application/json
Content-Length: 250
Location: /api/v1/devoluciones/81
X-Correlation-ID: f09c57e7806e439c
```

```json
{
  "id": 81,
  "folio_devolucion": "DEV-2026-0081",
  "estado": "solicitada",
  "fecha_solicitud": "2026-10-22T00:37:25.634753+00:00",
  "venta_detalle_id": 72,
  "motivo_id": 1,
  "descripcion_problema": "El empaque llego roto y el producto derramado.",
  "cantidad_devuelta": 1
}
```

**Verificaciones:**

- ok: HTTP 201
- ok: Trae X-Correlation-ID
- ok: estado solicitada
- ok: Location al expediente

## 029_devoluciones_post_raiz_201_xml

Carpeta: 01 Registro (POST) - Caso: registrar 201 XML

`POST http://{{vm_host}}:8002/api/v1/devoluciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/xml
Accept: application/xml
```

**Request - body:**

```
<devolucion>
  <venta_detalle_id>72</venta_detalle_id>
  <motivo_id>1</motivo_id>
  <descripcion_problema>Caja golpeada, el producto llego aplastado.</descripcion_problema>
</devolucion>
```

**Response - 201 CREATED** (132 ms, 408 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 408
Location: /api/v1/devoluciones/82
X-Correlation-ID: 6952287b6688443f
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<respuesta><id>82</id><folio_devolucion>DEV-2026-0082</folio_devolucion><estado>solicitada</estado><fecha_solicitud>2026-10-22T00:37:25.789330+00:00</fecha_solicitud><venta_detalle_id>72</venta_detalle_id><motivo_id>1</motivo_id><descripcion_problema>Caja golpeada, el producto llego aplastado.</descripcion_problema><cantidad_devuelta>1</cantidad_devuelta></respuesta>
```

**Verificaciones:**

- ok: HTTP 201
- ok: Trae X-Correlation-ID

## 030_devoluciones_post_raiz_400

Carpeta: 01 Registro (POST) - Caso: registrar 400 datos invalidos

`POST http://{{vm_host}}:8002/api/v1/devoluciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "venta_detalle_id": "abc",
  "descripcion_problema": "roto"
}
```

**Response - 400 BAD REQUEST** (166 ms, 332 bytes):

```http
Content-Type: application/json
Content-Length: 332
X-Correlation-ID: 36f40ca16c464b15
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Datos de la devolucion incompletos.",
    "detalles": [
      {
        "campo": "venta_detalle_id",
        "problema": "debe ser un entero mayor que 0"
      },
      {
        "campo": "motivo_id",
        "problema": "es obligatorio"
      },
      {
        "campo": "descripcion_problema",
        "problema": "minimo 10 caracteres"
      }
    ],
    "correlation_id": "36f40ca16c464b15"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 031_devoluciones_post_raiz_400_xml

Carpeta: 01 Registro (POST) - Caso: registrar 400 XML no cumple XSD

`POST http://{{vm_host}}:8002/api/v1/devoluciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/xml
Accept: application/xml
```

**Request - body:**

```
<devolucion>
  <motivo_id>1</motivo_id>
</devolucion>
```

**Response - 400 BAD REQUEST** (78 ms, 414 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 414
X-Correlation-ID: 7cc61646aaa342b1
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<error><codigo>400</codigo><tipo>xml_no_cumple_xsd</tipo><mensaje>El XML no cumple el contrato del endpoint.</mensaje><detalles><item><linea>1</linea><problema>Element 'devolucion': Missing child element(s). Expected is one of ( venta_detalle_id, descripcion_problema, cantidad_devuelta ).</problema></item></detalles><correlation_id>7cc61646aaa342b1</correlation_id></error>
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = xml_no_cumple_xsd
- ok: Trae X-Correlation-ID

## 032_devoluciones_post_raiz_401

Carpeta: 01 Registro (POST) - Caso: registrar 401 sin token

`POST http://{{vm_host}}:8002/api/v1/devoluciones`

**Request - headers:**

```http
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "venta_detalle_id": 72,
  "motivo_id": 1,
  "descripcion_problema": "El empaque llego roto y el producto derramado.",
  "cantidad_devuelta": 1
}
```

**Response - 401 UNAUTHORIZED** (72 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: 3d230a73d4d24c2c
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "3d230a73d4d24c2c"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = no_autenticado
- ok: Trae X-Correlation-ID

## 033_devoluciones_post_raiz_403

Carpeta: 01 Registro (POST) - Caso: registrar 403 compra de otro cliente

`POST http://{{vm_host}}:8002/api/v1/devoluciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "venta_detalle_id": 85,
  "motivo_id": 1,
  "descripcion_problema": "El empaque llego roto y el producto derramado.",
  "cantidad_devuelta": 1
}
```

**Response - 403 FORBIDDEN** (98 ms, 146 bytes):

```http
Content-Type: application/json
Content-Length: 146
X-Correlation-ID: 588610a405a8410c
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "La compra no pertenece a tu cuenta.",
    "detalles": null,
    "correlation_id": "588610a405a8410c"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 034_devoluciones_post_raiz_404

Carpeta: 01 Registro (POST) - Caso: registrar 404 linea inexistente

`POST http://{{vm_host}}:8002/api/v1/devoluciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "venta_detalle_id": 999999,
  "motivo_id": 1,
  "descripcion_problema": "El empaque llego roto y el producto derramado.",
  "cantidad_devuelta": 1
}
```

**Response - 404 NOT FOUND** (144 ms, 148 bytes):

```http
Content-Type: application/json
Content-Length: 148
X-Correlation-ID: 5aa7f0e8fc1d4469
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe la linea de venta 999999.",
    "detalles": null,
    "correlation_id": "5aa7f0e8fc1d4469"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 035_devoluciones_get_raiz_200

Carpeta: 02 Consulta (GET) - Caso: listar 200 cliente paginado

`GET http://{{vm_host}}:8002/api/v1/devoluciones?pagina=1&por_pagina=5`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (93 ms, 1734 bytes):

```http
Content-Type: application/json
Content-Length: 1734
X-Correlation-ID: 46dcdab61c7c4cdc
```

```json
{
  "datos": [
    {
      "id": 82,
      "folio_devolucion": "DEV-2026-0082",
      "estado": "solicitada",
      "fecha_solicitud": "2026-10-22T00:37:25.789330+00:00",
      "cantidad_devuelta": 1,
      "motivo": "Producto danado",
      "producto": "Pechuga de pollo 1 kg",
      "clasificacion_temperatura": "refrigerado",
      "numero_lote": "L-2026-201",
      "cliente": "Miguel Ramos Soto",
      "folio_venta": "VTA-2026-0006"
    },
    {
      "id": 81,
      "folio_devolucion": "DEV-2026-0081",
      "estado": "solicitada",
      "fecha_solicitud": "2026-10-22T00:37:25.634753+00:00",
      "cantidad_devuelta": 1,
      "motivo": "Producto danado",
      "producto": "Pechuga de pollo 1 kg",
      "clasificacion_temperatura": "refrigerado",
      "numero_lote": "L-2026-201",
      "cliente": "Miguel Ramos Soto",
      "folio_venta": "VTA-2026-0006"
    },
    {
      "id": 31,
      "folio_devolucion": "DEV-2026-0031",
      "estado": "cerrada",
      "fecha_solicitud": "2026-09-06T23:20:35.290510+00:00",
      "cantidad_devuelta": 1,
      "motivo": "Caducidad proxima",
      "producto": "Frijol envasado 900 g",
      "clasificacion_temperatura": "no_refrigerado",
      "numero_lote": "L-2026-125",
      "cliente": "Miguel Ramos Soto",
      "folio_venta": "VTA-2026-0006"
    },
    {
      "id": 28,
      "folio_devolucion": "DEV-2026-0028",
      "estado": "cerrada",
      "fecha_solicitud": "2026-09-06T23:20:35.290510+00:00",
      "cantidad_devuelta": 1,
      "motivo": "Caducidad vencida",
      "producto": "Leche entera 1 L",
      "clasificacion_temperatura": "refrigerado",
      "numero_lote": "L-2026-045",
      "cliente": "Miguel Ramos Soto",
      "folio_venta": "VTA-2026-0008"
    },
    {
      "id": 25,
      "folio_devolucion": "DEV-2026-0025",
      "estado": "resuelta",
      "fecha_solicitud": "2026-09-06T23:20:35.290510+00:00",
      "cantidad_devuelta": 1,
      "motivo": "Cadena de frio rota",
      "producto": "Leche entera 1 L",
      "clasificacion_temperatura": "refrigerado",
      "numero_lote": "L-2026-045",
      "cliente": "Miguel Ramos Soto",
      "folio_venta": "VTA-2026-0006"
    }
  ],
  "paginacion": {
    "pagina": 1,
    "por_pagina": 5,
    "total": 14,
    "paginas": 3
  }
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: trae paginacion

## 036_devoluciones_get_raiz_200_xml

Carpeta: 02 Consulta (GET) - Caso: listar 200 analista filtro XML

`GET http://{{vm_host}}:8002/api/v1/devoluciones?estado=solicitada&por_pagina=5`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/xml
```

**Response - 200 OK** (101 ms, 2480 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 2480
X-Correlation-ID: 9c167944aca54537
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<respuesta><datos><item><id>82</id><folio_devolucion>DEV-2026-0082</folio_devolucion><estado>solicitada</estado><fecha_solicitud>2026-10-22T00:37:25.789330+00:00</fecha_solicitud><cantidad_devuelta>1</cantidad_devuelta><motivo>Producto danado</motivo><producto>Pechuga de pollo 1 kg</producto><clasificacion_temperatura>refrigerado</clasificacion_temperatura><numero_lote>L-2026-201</numero_lote><cliente>Miguel Ramos Soto</cliente><folio_venta>VTA-2026-0006</folio_venta></item><item><id>81</id><folio_devolucion>DEV-2026-0081</folio_devolucion><estado>solicitada</estado><fecha_solicitud>2026-10-22T00:37:25.634753+00:00</fecha_solicitud><cantidad_devuelta>1</cantidad_devuelta><motivo>Producto danado</motivo><producto>Pechuga de pollo 1 kg</producto><clasificacion_temperatura>refrigerado</clasificacion_temperatura><numero_lote>L-2026-201</numero_lote><cliente>Miguel Ramos Soto</cliente><folio_venta>VTA-2026-0006</folio_venta></item><item><id>5</id><folio_devolucion>DEV-2026-0005</folio_devolucion><estado>solicitada</estado><fecha_solicitud>2026-09-06T23:20:35.290510+00:00</fecha_solicitud><cantidad_devuelta>1</cantidad_devuelta><motivo>Etiqueta incorrecta</motivo><producto>Lechuga romana</producto><clasificacion_temperatura>refrigerado</clasificacion_temperatura><numero_lote>L-2026-112</numero_lote><cliente>Miguel Ramos Soto</cliente><folio_venta>VTA-2026-0014</folio_venta></item><item><id>4</id><folio_devolucion>DEV-2026-0004</folio_devolucion><estado>solicitada</estado><fecha_solicitud>2026-09-06T23:20:35.290510+00:00</fecha_solicitud><cantidad_devuelta>1</cantidad_devuelta><motivo>Cadena de frio rota</motivo><producto>Queso panela 400 g</producto><clasificacion_temperatura>refrigerado</clasificacion_temperatura><numero_lote>L-2026-070</numero_lote><cliente>Ana Lopez Garcia</cliente><folio_venta>VTA-2026-0011</folio_venta></item><item><id>3</id><folio_devolucion>DEV-2026-0003</folio_devolucion><estado>solicitada</estado><fecha_solicitud>2026-09-06T23:20:35.290510+00:00</fecha_solicitud><cantidad_devuelta>1</cantidad_devuelta><motivo>Error en el pedido</motivo><producto>Tomate saladette 1 kg</producto><clasificacion_temperatura>refrigerado</clasificacion_temperatura><numero_lote>L-2026-118</numero_lote><cliente>Sofia Herrera</cliente><folio_venta>VTA-2026-0022</folio_venta></item></datos><paginacion><pagina>1</pagina><por_pagina>5</por_pagina><total>7</total><paginas>2</paginas></paginacion></respuesta>
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 037_devoluciones_get_raiz_400

Carpeta: 02 Consulta (GET) - Caso: listar 400 estado invalido

`GET http://{{vm_host}}:8002/api/v1/devoluciones?estado=perdida`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 400 BAD REQUEST** (77 ms, 290 bytes):

```http
Content-Type: application/json
Content-Length: 290
X-Correlation-ID: e41b8dc2bad2496e
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Filtro invalido.",
    "detalles": [
      {
        "campo": "estado",
        "problema": "valor desconocido; validos: solicitada, en_revision, autorizada, rechazada, en_recoleccion, recibida, en_inspeccion, resuelta, cerrada"
      }
    ],
    "correlation_id": "e41b8dc2bad2496e"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 038_devoluciones_get_raiz_401

Carpeta: 02 Consulta (GET) - Caso: listar 401 sin token

`GET http://{{vm_host}}:8002/api/v1/devoluciones`

**Request - headers:**

```http
Accept: application/json
```

**Response - 401 UNAUTHORIZED** (167 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: e733ba0fd3e74c59
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "e733ba0fd3e74c59"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = no_autenticado
- ok: Trae X-Correlation-ID

## 039_devoluciones_get_raiz_401

Carpeta: 02 Consulta (GET) - Caso: listar 401 token invalido

`GET http://{{vm_host}}:8002/api/v1/devoluciones`

**Request - headers:**

```http
Authorization: Bearer esto-no-es-un-token
Accept: application/json
```

**Response - 401 UNAUTHORIZED** (72 ms, 136 bytes):

```http
Content-Type: application/json
Content-Length: 136
X-Correlation-ID: 93c56f4b4f4d4264
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "token_invalido",
    "mensaje": "El token no es valido.",
    "detalles": null,
    "correlation_id": "93c56f4b4f4d4264"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = token_invalido
- ok: Trae X-Correlation-ID

## 040_devoluciones_get_id_200

Carpeta: 02 Consulta (GET) - Caso: detalle 200 exitoso

`GET http://{{vm_host}}:8002/api/v1/devoluciones/81`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (98 ms, 1082 bytes):

```http
Content-Type: application/json
Content-Length: 1082
X-Correlation-ID: 67ba1b0091494bca
```

```json
{
  "id": 81,
  "folio_devolucion": "DEV-2026-0081",
  "estado": "solicitada",
  "descripcion_problema": "El empaque llego roto y el producto derramado.",
  "cantidad_devuelta": 1,
  "fecha_solicitud": "2026-10-22T00:37:25.634753+00:00",
  "fecha_autorizacion": null,
  "fecha_cierre": null,
  "motivo_id": 1,
  "motivo": "Producto danado",
  "venta_detalle_id": 72,
  "cantidad_comprada": 3,
  "precio_unitario": 193.77,
  "valor_devuelto": 193.77,
  "folio_venta": "VTA-2026-0006",
  "cliente_id": 11,
  "cliente": "Miguel Ramos Soto",
  "producto": "Pechuga de pollo 1 kg",
  "sku": "AVI-001",
  "clasificacion_temperatura": "refrigerado",
  "numero_lote": "L-2026-201",
  "analista_id": null,
  "analista": null,
  "historial": [
    {
      "fecha": "2026-10-22T00:37:25.634753+00:00",
      "accion": "alta_devolucion",
      "detalle": "Se registro la devolucion DEV-2026-0081 sobre la venta VTA-2026-0006 (API)",
      "usuario": "Miguel Ramos Soto"
    }
  ],
  "eventos": [
    {
      "servicio": "devoluciones",
      "tipo": "devolucion_registrada",
      "datos": {
        "devolucion_id": 81,
        "folio": "DEV-2026-0081",
        "venta_detalle_id": 72,
        "cantidad": 1
      },
      "usuario_id": 11,
      "correlation_id": "f09c57e7806e439c",
      "fecha": "2026-10-22T00:37:25.650000+00:00"
    }
  ]
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: trae eventos de MongoDB

## 041_devoluciones_get_id_403

Carpeta: 02 Consulta (GET) - Caso: detalle 403 otro cliente

`GET http://{{vm_host}}:8002/api/v1/devoluciones/81`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 403 FORBIDDEN** (89 ms, 150 bytes):

```http
Content-Type: application/json
Content-Length: 150
X-Correlation-ID: ec46ff33240d4a86
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "La devolucion no pertenece a tu cuenta.",
    "detalles": null,
    "correlation_id": "ec46ff33240d4a86"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 042_devoluciones_get_id_404

Carpeta: 02 Consulta (GET) - Caso: detalle 404 inexistente

`GET http://{{vm_host}}:8002/api/v1/devoluciones/999999`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 404 NOT FOUND** (146 ms, 144 bytes):

```http
Content-Type: application/json
Content-Length: 144
X-Correlation-ID: 02a7c9202e7244af
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe la devolucion 999999.",
    "detalles": null,
    "correlation_id": "02a7c9202e7244af"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 043_devoluciones_patch_id_resolucion_403

Carpeta: 03 Revision (PATCH y PUT) - Caso: resolver 403 cliente sin permiso

`PATCH http://{{vm_host}}:8002/api/v1/devoluciones/81/resolucion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "decision": "autorizar"
}
```

**Response - 403 FORBIDDEN** (74 ms, 216 bytes):

```http
Content-Type: application/json
Content-Length: 216
X-Correlation-ID: 428d0d5b164544f2
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
        "Analista de Devoluciones"
      ]
    },
    "correlation_id": "428d0d5b164544f2"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 044_devoluciones_patch_id_resolucion_400

Carpeta: 03 Revision (PATCH y PUT) - Caso: resolver 400 rechazo sin justificacion

`PATCH http://{{vm_host}}:8002/api/v1/devoluciones/81/resolucion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "decision": "rechazar"
}
```

**Response - 400 BAD REQUEST** (73 ms, 197 bytes):

```http
Content-Type: application/json
Content-Length: 197
X-Correlation-ID: 1a08064a7a424bf2
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Resolucion incompleta.",
    "detalles": [
      {
        "campo": "justificacion",
        "problema": "es obligatoria para rechazar"
      }
    ],
    "correlation_id": "1a08064a7a424bf2"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 045_devoluciones_patch_id_resolucion_200

Carpeta: 03 Revision (PATCH y PUT) - Caso: resolver 200 pedir informacion

`PATCH http://{{vm_host}}:8002/api/v1/devoluciones/81/resolucion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "decision": "informacion",
  "justificacion": "Describe el estado del sello."
}
```

**Response - 200 OK** (98 ms, 238 bytes):

```http
Content-Type: application/json
Content-Length: 238
X-Correlation-ID: 4c1c883a2bc949ef
```

```json
{
  "id": 81,
  "folio_devolucion": "DEV-2026-0081",
  "estado": "en_revision",
  "decision": "informacion",
  "analista": "Josue Berdeal",
  "notificacion_cliente": "Necesitamos mas informacion sobre tu devolucion DEV-2026-0081. Describe el estado del sello."
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: en_revision

## 046_devoluciones_put_id_200

Carpeta: 03 Revision (PATCH y PUT) - Caso: corregir 200 PUT

`PUT http://{{vm_host}}:8002/api/v1/devoluciones/81`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "motivo_id": 1,
  "descripcion_problema": "El sello venia abierto desde la tienda.",
  "cantidad_devuelta": 1
}
```

**Response - 200 OK** (102 ms, 628 bytes):

```http
Content-Type: application/json
Content-Length: 628
X-Correlation-ID: 3b9720bb9dc84aaa
```

```json
{
  "id": 81,
  "folio_devolucion": "DEV-2026-0081",
  "estado": "en_revision",
  "descripcion_problema": "El sello venia abierto desde la tienda.",
  "cantidad_devuelta": 1,
  "fecha_solicitud": "2026-10-22T00:37:25.634753+00:00",
  "fecha_autorizacion": null,
  "fecha_cierre": null,
  "motivo_id": 1,
  "motivo": "Producto danado",
  "venta_detalle_id": 72,
  "cantidad_comprada": 3,
  "precio_unitario": 193.77,
  "valor_devuelto": 193.77,
  "folio_venta": "VTA-2026-0006",
  "cliente_id": 11,
  "cliente": "Miguel Ramos Soto",
  "producto": "Pechuga de pollo 1 kg",
  "sku": "AVI-001",
  "clasificacion_temperatura": "refrigerado",
  "numero_lote": "L-2026-201",
  "analista_id": 16,
  "analista": "Josue Berdeal"
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 047_devoluciones_delete_id_409

Carpeta: 03 Revision (PATCH y PUT) - Caso: cancelar 409 ya revisada

`DELETE http://{{vm_host}}:8002/api/v1/devoluciones/81`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 409 CONFLICT** (163 ms, 204 bytes):

```http
Content-Type: application/json
Content-Length: 204
X-Correlation-ID: 4a1b150cec754d24
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "estado_no_permite",
    "mensaje": "Solo se puede cancelar una devolucion que nadie ha revisado.",
    "detalles": {
      "estado_actual": "en_revision"
    },
    "correlation_id": "4a1b150cec754d24"
  }
}
```

**Verificaciones:**

- ok: HTTP 409
- ok: error.tipo = estado_no_permite
- ok: Trae X-Correlation-ID

## 048_devoluciones_patch_id_resolucion_200_xml

Carpeta: 03 Revision (PATCH y PUT) - Caso: resolver 200 autorizar XML

`PATCH http://{{vm_host}}:8002/api/v1/devoluciones/81/resolucion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/xml
Accept: application/xml
```

**Request - body:**

```
<resolucion>
  <decision>autorizar</decision>
  <justificacion>Evidencia suficiente.</justificacion>
</resolucion>
```

**Response - 200 OK** (101 ms, 339 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 339
X-Correlation-ID: feca4df0209d4877
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<respuesta><id>81</id><folio_devolucion>DEV-2026-0081</folio_devolucion><estado>autorizada</estado><decision>autorizar</decision><analista>Josue Berdeal</analista><notificacion_cliente>Tu devolucion DEV-2026-0081 fue autorizada. Pronto programaremos la recoleccion.</notificacion_cliente></respuesta>
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: autorizada

## 049_devoluciones_patch_id_resolucion_409

Carpeta: 03 Revision (PATCH y PUT) - Caso: resolver 409 ya resuelta

`PATCH http://{{vm_host}}:8002/api/v1/devoluciones/81/resolucion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "decision": "rechazar",
  "justificacion": "Intento tardio."
}
```

**Response - 409 CONFLICT** (90 ms, 180 bytes):

```http
Content-Type: application/json
Content-Length: 180
X-Correlation-ID: 0caca97b3c0a47fc
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "estado_no_permite",
    "mensaje": "La devolucion ya no esta en revision.",
    "detalles": {
      "estado_actual": "autorizada"
    },
    "correlation_id": "0caca97b3c0a47fc"
  }
}
```

**Verificaciones:**

- ok: HTTP 409
- ok: error.tipo = estado_no_permite
- ok: Trae X-Correlation-ID

## 050_devoluciones_get_id_200

Carpeta: 03 Revision (PATCH y PUT) - Caso: detalle 200 historial completo

`GET http://{{vm_host}}:8002/api/v1/devoluciones/81`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (189 ms, 2599 bytes):

```http
Content-Type: application/json
Content-Length: 2599
X-Correlation-ID: cc125b3b674e42ce
```

```json
{
  "id": 81,
  "folio_devolucion": "DEV-2026-0081",
  "estado": "autorizada",
  "descripcion_problema": "El sello venia abierto desde la tienda.",
  "cantidad_devuelta": 1,
  "fecha_solicitud": "2026-10-22T00:37:25.634753+00:00",
  "fecha_autorizacion": "2026-10-22T00:37:28.248568+00:00",
  "fecha_cierre": null,
  "motivo_id": 1,
  "motivo": "Producto danado",
  "venta_detalle_id": 72,
  "cantidad_comprada": 3,
  "precio_unitario": 193.77,
  "valor_devuelto": 193.77,
  "folio_venta": "VTA-2026-0006",
  "cliente_id": 11,
  "cliente": "Miguel Ramos Soto",
  "producto": "Pechuga de pollo 1 kg",
  "sku": "AVI-001",
  "clasificacion_temperatura": "refrigerado",
  "numero_lote": "L-2026-201",
  "analista_id": 16,
  "analista": "Josue Berdeal",
  "historial": [
    {
      "fecha": "2026-10-22T00:37:28.248568+00:00",
      "accion": "autorizacion",
      "detalle": "Decision 'autorizar' por API. Evidencia suficiente.",
      "usuario": "Josue Berdeal"
    },
    {
      "fecha": "2026-10-22T00:37:27.949793+00:00",
      "accion": "actualizacion_solicitud",
      "detalle": "El cliente corrigio la solicitud (API)",
      "usuario": "Miguel Ramos Soto"
    },
    {
      "fecha": "2026-10-22T00:37:27.827236+00:00",
      "accion": "solicitud_informacion",
      "detalle": "Decision 'informacion' por API. Describe el estado del sello.",
      "usuario": "Josue Berdeal"
    },
    {
      "fecha": "2026-10-22T00:37:27.362837+00:00",
      "accion": "acceso_denegado",
      "detalle": "Intento de acceder a una devolucion de otro cliente (API)",
      "usuario": "Ana Lopez Garcia"
    },
    {
      "fecha": "2026-10-22T00:37:25.634753+00:00",
      "accion": "alta_devolucion",
      "detalle": "Se registro la devolucion DEV-2026-0081 sobre la venta VTA-2026-0006 (API)",
      "usuario": "Miguel Ramos Soto"
    }
  ],
  "eventos": [
    {
      "servicio": "devoluciones",
      "tipo": "devolucion_autorizacion",
      "datos": {
        "devolucion_id": 81,
        "folio": "DEV-2026-0081",
        "decision": "autorizar",
        "analista_id": 16
      },
      "usuario_id": 16,
      "correlation_id": "feca4df0209d4877",
      "fecha": "2026-10-22T00:37:28.264000+00:00"
    },
    {
      "servicio": "devoluciones",
      "tipo": "devolucion_corregida",
      "datos": {
        "devolucion_id": 81,
        "folio": "DEV-2026-0081",
        "motivo_id": 1,
        "descripcion_problema": "El sello venia abierto desde la tienda.",
        "cantidad_devuelta": 1
     
... (recortado, 3345 caracteres en total)
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 051_devoluciones_delete_id_200

Carpeta: 04 Cancelacion (DELETE) - Caso: cancelar 200 exitoso

`DELETE http://{{vm_host}}:8002/api/v1/devoluciones/82`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (94 ms, 79 bytes):

```http
Content-Type: application/json
Content-Length: 79
X-Correlation-ID: 426efbdc1104455d
```

```json
{
  "id": 82,
  "folio_devolucion": "DEV-2026-0082",
  "mensaje": "Devolucion cancelada."
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 052_devoluciones_get_id_404

Carpeta: 04 Cancelacion (DELETE) - Caso: detalle 404 cancelada

`GET http://{{vm_host}}:8002/api/v1/devoluciones/82`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 404 NOT FOUND** (96 ms, 140 bytes):

```http
Content-Type: application/json
Content-Length: 140
X-Correlation-ID: 08d6771d45514f86
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe la devolucion 82.",
    "detalles": null,
    "correlation_id": "08d6771d45514f86"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

