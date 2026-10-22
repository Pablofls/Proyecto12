# Ejecuciones reales - `ventas_catalogos`

Salida de `newman run docs/postman/ventas_catalogos.postman_collection.json` contra la VM (2026-10-22 00:36 UTC). Verificaciones: 106 (0 fallidas). Tokens, contrasenas e IP de la VM estan ocultos (`***jwt***`, `***`, `{{vm_host}}`).

## 138_ventas_catalogos_get_health_200

Carpeta: 00 Preparacion (tokens) - Caso: health 200

`GET http://{{vm_host}}:8006/health`

**Request - headers:**

```http
Accept: application/json
```

**Response - 200 OK** (99 ms, 149 bytes):

```http
Content-Type: application/json
Content-Length: 149
X-Correlation-ID: 044cb003e6114b4d
```

```json
{
  "servicio": "ventas-catalogos",
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

## 139_ventas_catalogos_get_raiz_200

Carpeta: 01 Ventas - Caso: ventas 200 cliente paginado

`GET http://{{vm_host}}:8006/api/v1/ventas?pagina=1&por_pagina=5`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (101 ms, 913 bytes):

```http
Content-Type: application/json
Content-Length: 913
X-Correlation-ID: 2c7f3330ba7143aa
```

```json
{
  "datos": [
    {
      "id": 29,
      "folio_venta": "VTA-2026-0004",
      "cliente_id": 11,
      "fecha_venta": "2026-08-31",
      "cliente": "Miguel Ramos Soto",
      "tienda": "Tienda Valle Oriente",
      "lineas": 1,
      "total": 506.12
    },
    {
      "id": 39,
      "folio_venta": "VTA-2026-0014",
      "cliente_id": 11,
      "fecha_venta": "2026-08-29",
      "cliente": "Miguel Ramos Soto",
      "tienda": "Tienda Cumbres",
      "lineas": 2,
      "total": 883.65
    },
    {
      "id": 38,
      "folio_venta": "VTA-2026-0013",
      "cliente_id": 11,
      "fecha_venta": "2026-08-29",
      "cliente": "Miguel Ramos Soto",
      "tienda": "Tienda Cumbres",
      "lineas": 3,
      "total": 1125.39
    },
    {
      "id": 42,
      "folio_venta": "VTA-2026-0017",
      "cliente_id": 11,
      "fecha_venta": "2026-08-25",
      "cliente": "Miguel Ramos Soto",
      "tienda": "Tienda Centro",
      "lineas": 4,
      "total": 1427.75
    },
    {
      "id": 32,
      "folio_venta": "VTA-2026-0007",
      "cliente_id": 11,
      "fecha_venta": "2026-08-22",
      "cliente": "Miguel Ramos Soto",
      "tienda": "Tienda Valle Oriente",
      "lineas": 1,
      "total": 99.13
    }
  ],
  "paginacion": {
    "pagina": 1,
    "por_pagina": 5,
    "total": 10,
    "paginas": 2
  }
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: trae paginacion

## 140_ventas_catalogos_get_raiz_200_xml

Carpeta: 01 Ventas - Caso: ventas 200 analista XML

`GET http://{{vm_host}}:8006/api/v1/ventas?pagina=1&por_pagina=5`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/xml
```

**Response - 200 OK** (101 ms, 1350 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 1350
X-Correlation-ID: c383c593931143df
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<ventas><datos><item><id>29</id><folio_venta>VTA-2026-0004</folio_venta><cliente_id>11</cliente_id><fecha_venta>2026-08-31</fecha_venta><cliente>Miguel Ramos Soto</cliente><tienda>Tienda Valle Oriente</tienda><lineas>1</lineas><total>506.12</total></item><item><id>39</id><folio_venta>VTA-2026-0014</folio_venta><cliente_id>11</cliente_id><fecha_venta>2026-08-29</fecha_venta><cliente>Miguel Ramos Soto</cliente><tienda>Tienda Cumbres</tienda><lineas>2</lineas><total>883.65</total></item><item><id>38</id><folio_venta>VTA-2026-0013</folio_venta><cliente_id>11</cliente_id><fecha_venta>2026-08-29</fecha_venta><cliente>Miguel Ramos Soto</cliente><tienda>Tienda Cumbres</tienda><lineas>3</lineas><total>1125.39</total></item><item><id>50</id><folio_venta>VTA-2026-0025</folio_venta><cliente_id>12</cliente_id><fecha_venta>2026-08-27</fecha_venta><cliente>Sofia Herrera</cliente><tienda>Tienda Cumbres</tienda><lineas>2</lineas><total>335.88</total></item><item><id>42</id><folio_venta>VTA-2026-0017</folio_venta><cliente_id>11</cliente_id><fecha_venta>2026-08-25</fecha_venta><cliente>Miguel Ramos Soto</cliente><tienda>Tienda Centro</tienda><lineas>4</lineas><total>1427.75</total></item></datos><paginacion><pagina>1</pagina><por_pagina>5</por_pagina><total>25</total><paginas>5</paginas></paginacion></ventas>
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 141_ventas_catalogos_get_raiz_400

Carpeta: 01 Ventas - Caso: ventas 400 paginacion invalida

`GET http://{{vm_host}}:8006/api/v1/ventas?por_pagina=0`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 400 BAD REQUEST** (155 ms, 209 bytes):

```http
Content-Type: application/json
Content-Length: 209
X-Correlation-ID: 37e02186d00246a8
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Parametro de paginacion invalido.",
    "detalles": [
      {
        "campo": "por_pagina",
        "problema": "debe ser un entero entre 1 y 100"
      }
    ],
    "correlation_id": "37e02186d00246a8"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 142_ventas_catalogos_get_raiz_401

Carpeta: 01 Ventas - Caso: ventas 401 sin token

`GET http://{{vm_host}}:8006/api/v1/ventas`

**Request - headers:**

```http
Accept: application/json
```

**Response - 401 UNAUTHORIZED** (79 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: 34720737f9de4ecd
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "34720737f9de4ecd"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = no_autenticado
- ok: Trae X-Correlation-ID

## 143_ventas_catalogos_get_raiz_401

Carpeta: 01 Ventas - Caso: ventas 401 token invalido

`GET http://{{vm_host}}:8006/api/v1/ventas`

**Request - headers:**

```http
Authorization: Bearer esto-no-es-un-token
Accept: application/json
```

**Response - 401 UNAUTHORIZED** (78 ms, 136 bytes):

```http
Content-Type: application/json
Content-Length: 136
X-Correlation-ID: df2c6e0c3e9844dd
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "token_invalido",
    "mensaje": "El token no es valido.",
    "detalles": null,
    "correlation_id": "df2c6e0c3e9844dd"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = token_invalido
- ok: Trae X-Correlation-ID

## 144_ventas_catalogos_get_id_200

Carpeta: 01 Ventas - Caso: venta 200 detalle

`GET http://{{vm_host}}:8006/api/v1/ventas/29`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (96 ms, 455 bytes):

```http
Content-Type: application/json
Content-Length: 455
X-Correlation-ID: 98c80637bbc14415
```

```json
{
  "id": 29,
  "folio_venta": "VTA-2026-0004",
  "fecha_venta": "2026-08-31",
  "cliente_id": 11,
  "cliente": "Miguel Ramos Soto",
  "tienda": "Tienda Valle Oriente",
  "lineas": [
    {
      "id": 69,
      "lote_id": 11,
      "cantidad": 2,
      "precio_unitario": 253.06,
      "numero_lote": "L-2026-312",
      "fecha_caducidad": "2027-01-01",
      "producto_id": 10,
      "producto": "Galletas surtidas 600 g",
      "sku": "ABA-003",
      "clasificacion_temperatura": "no_refrigerado",
      "proveedor": "Abarrotes Monterrey",
      "ya_devuelto": 1,
      "disponible": 1
    }
  ]
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: trae lineas

## 145_ventas_catalogos_get_id_200_xml

Carpeta: 01 Ventas - Caso: venta 200 detalle XML

`GET http://{{vm_host}}:8006/api/v1/ventas/29`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/xml
```

**Response - 200 OK** (143 ms, 705 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 705
X-Correlation-ID: b50b9100d7544b57
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<venta><id>29</id><folio_venta>VTA-2026-0004</folio_venta><fecha_venta>2026-08-31</fecha_venta><cliente_id>11</cliente_id><cliente>Miguel Ramos Soto</cliente><tienda>Tienda Valle Oriente</tienda><lineas><item><id>69</id><lote_id>11</lote_id><cantidad>2</cantidad><precio_unitario>253.06</precio_unitario><numero_lote>L-2026-312</numero_lote><fecha_caducidad>2027-01-01</fecha_caducidad><producto_id>10</producto_id><producto>Galletas surtidas 600 g</producto><sku>ABA-003</sku><clasificacion_temperatura>no_refrigerado</clasificacion_temperatura><proveedor>Abarrotes Monterrey</proveedor><ya_devuelto>1</ya_devuelto><disponible>1</disponible></item></lineas></venta>
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 146_ventas_catalogos_get_id_403

Carpeta: 01 Ventas - Caso: venta 403 de otro cliente

`GET http://{{vm_host}}:8006/api/v1/ventas/29`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 403 FORBIDDEN** (107 ms, 136 bytes):

```http
Content-Type: application/json
Content-Length: 136
X-Correlation-ID: 546730f466bd4f13
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "La venta no te pertenece.",
    "detalles": null,
    "correlation_id": "546730f466bd4f13"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 147_ventas_catalogos_get_id_404

Carpeta: 01 Ventas - Caso: venta 404 inexistente

`GET http://{{vm_host}}:8006/api/v1/ventas/999999`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 404 NOT FOUND** (117 ms, 131 bytes):

```http
Content-Type: application/json
Content-Length: 131
X-Correlation-ID: 0abc7be861ea4d30
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Venta inexistente.",
    "detalles": null,
    "correlation_id": "0abc7be861ea4d30"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 148_ventas_catalogos_get_catalogos_200

Carpeta: 02 Catalogos (lectura) - Caso: catalogos 200 lista

`GET http://{{vm_host}}:8006/api/v1/catalogos`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (77 ms, 95 bytes):

```http
Content-Type: application/json
Content-Length: 95
X-Correlation-ID: 6f3d749056224f6e
```

```json
{
  "catalogos": [
    "lotes",
    "motivos",
    "productos",
    "proveedores",
    "rutas",
    "tiendas",
    "transportistas"
  ]
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: siete catalogos

## 149_ventas_catalogos_get_catalogos_403

Carpeta: 02 Catalogos (lectura) - Caso: catalogos 403 cliente

`GET http://{{vm_host}}:8006/api/v1/catalogos`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 403 FORBIDDEN** (146 ms, 232 bytes):

```http
Content-Type: application/json
Content-Length: 232
X-Correlation-ID: bc9302e35c6a46e3
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
    "correlation_id": "bc9302e35c6a46e3"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 150_ventas_catalogos_get_catalogos_nombre_200

Carpeta: 02 Catalogos (lectura) - Caso: catalogo motivos 200 cliente

`GET http://{{vm_host}}:8006/api/v1/catalogos/motivos?pagina=1&por_pagina=5`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (88 ms, 675 bytes):

```http
Content-Type: application/json
Content-Length: 675
X-Correlation-ID: 1e882ee6ada343a8
```

```json
{
  "datos": [
    {
      "id": 8,
      "nombre": "Producto incompleto",
      "descripcion": "Falta parte del contenido declarado",
      "activo": true
    },
    {
      "id": 7,
      "nombre": "Etiqueta incorrecta",
      "descripcion": "La informacion de la etiqueta no coincide con el producto",
      "activo": true
    },
    {
      "id": 6,
      "nombre": "Calidad inferior",
      "descripcion": "El producto no cumple con los estandares de calidad esperados",
      "activo": true
    },
    {
      "id": 5,
      "nombre": "Error en el pedido",
      "descripcion": "Se entrego un producto diferente al solicitado",
      "activo": true
    },
    {
      "id": 4,
      "nombre": "Cadena de frio rota",
      "descripcion": "El producto refrigerado no conservo su temperatura",
      "activo": true
    }
  ],
  "paginacion": {
    "pagina": 1,
    "por_pagina": 5,
    "total": 8,
    "paginas": 2
  }
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: trae datos

## 151_ventas_catalogos_get_catalogos_nombre_200_xml

Carpeta: 02 Catalogos (lectura) - Caso: catalogo motivos 200 XML con inactivos

`GET http://{{vm_host}}:8006/api/v1/catalogos/motivos?solo_activos=false`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/xml
```

**Response - 200 OK** (83 ms, 1411 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 1411
X-Correlation-ID: f0c4c948f9b14e7d
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<catalogo><datos><item><id>8</id><nombre>Producto incompleto</nombre><descripcion>Falta parte del contenido declarado</descripcion><activo>true</activo></item><item><id>7</id><nombre>Etiqueta incorrecta</nombre><descripcion>La informacion de la etiqueta no coincide con el producto</descripcion><activo>true</activo></item><item><id>6</id><nombre>Calidad inferior</nombre><descripcion>El producto no cumple con los estandares de calidad esperados</descripcion><activo>true</activo></item><item><id>5</id><nombre>Error en el pedido</nombre><descripcion>Se entrego un producto diferente al solicitado</descripcion><activo>true</activo></item><item><id>4</id><nombre>Cadena de frio rota</nombre><descripcion>El producto refrigerado no conservo su temperatura</descripcion><activo>true</activo></item><item><id>3</id><nombre>Caducidad proxima</nombre><descripcion>El producto esta proximo a vencer y no puede comercializarse</descripcion><activo>true</activo></item><item><id>2</id><nombre>Caducidad vencida</nombre><descripcion>El producto supero su fecha de caducidad</descripcion><activo>true</activo></item><item><id>1</id><nombre>Producto danado</nombre><descripcion>El empaque o el producto llego danado</descripcion><activo>true</activo></item></datos><paginacion><pagina>1</pagina><por_pagina>20</por_pagina><total>8</total><paginas>1</paginas></paginacion></catalogo>
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 152_ventas_catalogos_get_catalogos_nombre_403

Carpeta: 02 Catalogos (lectura) - Caso: catalogo productos 403 cliente

`GET http://{{vm_host}}:8006/api/v1/catalogos/productos`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 403 FORBIDDEN** (75 ms, 145 bytes):

```http
Content-Type: application/json
Content-Length: 145
X-Correlation-ID: 100005ad3a584eb5
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "No puedes consultar este catalogo.",
    "detalles": null,
    "correlation_id": "100005ad3a584eb5"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 153_ventas_catalogos_get_catalogos_nombre_404

Carpeta: 02 Catalogos (lectura) - Caso: catalogo inexistente 404

`GET http://{{vm_host}}:8006/api/v1/catalogos/inexistente`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 404 NOT FOUND** (73 ms, 136 bytes):

```http
Content-Type: application/json
Content-Length: 136
X-Correlation-ID: f142d6621aba41ae
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe ese catalogo.",
    "detalles": null,
    "correlation_id": "f142d6621aba41ae"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 154_ventas_catalogos_get_catalogos_nombre_200

Carpeta: 02 Catalogos (lectura) - Caso: catalogo rutas 200

`GET http://{{vm_host}}:8006/api/v1/catalogos/rutas?por_pagina=1`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (165 ms, 172 bytes):

```http
Content-Type: application/json
Content-Length: 172
X-Correlation-ID: 39a7fd1b63624371
```

```json
{
  "datos": [
    {
      "id": 4,
      "origen": "Domicilio del cliente",
      "destino": "Centro de Devoluciones Norte",
      "activo": true
    }
  ],
  "paginacion": {
    "pagina": 1,
    "por_pagina": 1,
    "total": 4,
    "paginas": 4
  }
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 155_ventas_catalogos_get_catalogos_nombre_200

Carpeta: 02 Catalogos (lectura) - Caso: catalogo transportistas 200

`GET http://{{vm_host}}:8006/api/v1/catalogos/transportistas?por_pagina=1`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (86 ms, 149 bytes):

```http
Content-Type: application/json
Content-Length: 149
X-Correlation-ID: 1725d29531004853
```

```json
{
  "datos": [
    {
      "id": 4,
      "nombre": "Laura Cruz",
      "empresa": "Fletes del Norte",
      "activo": true
    }
  ],
  "paginacion": {
    "pagina": 1,
    "por_pagina": 1,
    "total": 4,
    "paginas": 4
  }
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 156_ventas_catalogos_get_catalogos_nombre_registro_id_200

Carpeta: 02 Catalogos (lectura) - Caso: registro 200 detalle

`GET http://{{vm_host}}:8006/api/v1/catalogos/motivos/8`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (84 ms, 106 bytes):

```http
Content-Type: application/json
Content-Length: 106
X-Correlation-ID: 7db1071311a24b53
```

```json
{
  "id": 8,
  "nombre": "Producto incompleto",
  "descripcion": "Falta parte del contenido declarado",
  "activo": true
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 157_ventas_catalogos_get_catalogos_nombre_registro_id_404

Carpeta: 02 Catalogos (lectura) - Caso: registro 404 inexistente

`GET http://{{vm_host}}:8006/api/v1/catalogos/motivos/999999`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 404 NOT FOUND** (87 ms, 134 bytes):

```http
Content-Type: application/json
Content-Length: 134
X-Correlation-ID: d7421069da434cac
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Registro inexistente.",
    "detalles": null,
    "correlation_id": "d7421069da434cac"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 158_ventas_catalogos_post_catalogos_nombre_201

Carpeta: 03 Catalogos (escritura, Administrador) - Caso: alta 201 JSON

`POST http://{{vm_host}}:8006/api/v1/catalogos/motivos`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "nombre": "Motivo Postman 1792629377",
  "descripcion": "Alta de prueba desde Postman"
}
```

**Response - 201 CREATED** (137 ms, 31 bytes):

```http
Content-Type: application/json
Content-Length: 31
Location: /api/v1/catalogos/motivos/12
X-Correlation-ID: 94ea64a2ac284391
```

```json
{
  "id": 12,
  "catalogo": "motivos"
}
```

**Verificaciones:**

- ok: HTTP 201
- ok: Trae X-Correlation-ID
- ok: Location

## 159_ventas_catalogos_post_catalogos_nombre_201_xml

Carpeta: 03 Catalogos (escritura, Administrador) - Caso: alta 201 XML

`POST http://{{vm_host}}:8006/api/v1/catalogos/motivos`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/xml
Accept: application/xml
```

**Request - body:**

```
<catalogo>
  <nombre>Motivo XML 1792629377</nombre>
  <descripcion>Alta de prueba XML</descripcion>
</catalogo>
```

**Response - 201 CREATED** (504 ms, 99 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 99
Location: /api/v1/catalogos/motivos/13
X-Correlation-ID: 5429549a44e1475a
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<registro><id>13</id><catalogo>motivos</catalogo></registro>
```

**Verificaciones:**

- ok: HTTP 201
- ok: Trae X-Correlation-ID

## 160_ventas_catalogos_post_catalogos_nombre_400

Carpeta: 03 Catalogos (escritura, Administrador) - Caso: alta 400 sin nombre

`POST http://{{vm_host}}:8006/api/v1/catalogos/motivos`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "nombre": ""
}
```

**Response - 400 BAD REQUEST** (82 ms, 168 bytes):

```http
Content-Type: application/json
Content-Length: 168
X-Correlation-ID: 0f58c6f58a064cc2
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Campos invalidos.",
    "detalles": [
      {
        "campo": "nombre",
        "problema": "obligatorio"
      }
    ],
    "correlation_id": "0f58c6f58a064cc2"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 161_ventas_catalogos_post_catalogos_nombre_401

Carpeta: 03 Catalogos (escritura, Administrador) - Caso: alta 401 sin token

`POST http://{{vm_host}}:8006/api/v1/catalogos/motivos`

**Request - headers:**

```http
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "nombre": "Motivo Postman 1792629378",
  "descripcion": "Alta de prueba desde Postman"
}
```

**Response - 401 UNAUTHORIZED** (74 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: 4c54633e6bd440da
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "4c54633e6bd440da"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = no_autenticado
- ok: Trae X-Correlation-ID

## 162_ventas_catalogos_post_catalogos_nombre_403

Carpeta: 03 Catalogos (escritura, Administrador) - Caso: alta 403 analista

`POST http://{{vm_host}}:8006/api/v1/catalogos/motivos`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "nombre": "Motivo Postman 1792629378",
  "descripcion": "Alta de prueba desde Postman"
}
```

**Response - 403 FORBIDDEN** (77 ms, 222 bytes):

```http
Content-Type: application/json
Content-Length: 222
X-Correlation-ID: 95109928f4d14c62
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
        "Administrador"
      ]
    },
    "correlation_id": "95109928f4d14c62"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 163_ventas_catalogos_post_catalogos_nombre_404

Carpeta: 03 Catalogos (escritura, Administrador) - Caso: alta 404 catalogo inexistente

`POST http://{{vm_host}}:8006/api/v1/catalogos/inexistente`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "nombre": "Motivo Postman 1792629378",
  "descripcion": "Alta de prueba desde Postman"
}
```

**Response - 404 NOT FOUND** (74 ms, 136 bytes):

```http
Content-Type: application/json
Content-Length: 136
X-Correlation-ID: 85d9770eb48f4d9d
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe ese catalogo.",
    "detalles": null,
    "correlation_id": "85d9770eb48f4d9d"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 164_ventas_catalogos_post_catalogos_nombre_409

Carpeta: 03 Catalogos (escritura, Administrador) - Caso: alta 409 referencia inactiva

`POST http://{{vm_host}}:8006/api/v1/catalogos/productos`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "sku": "PM-1792629378",
  "nombre": "Producto Postman",
  "clasificacion_temperatura": "refrigerado",
  "proveedor_id": 999999
}
```

**Response - 409 CONFLICT** (163 ms, 174 bytes):

```http
Content-Type: application/json
Content-Length: 174
X-Correlation-ID: 6c3f4825d3794973
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "referencia_inactiva",
    "mensaje": "El campo proveedor_id no referencia un registro activo.",
    "detalles": null,
    "correlation_id": "6c3f4825d3794973"
  }
}
```

**Verificaciones:**

- ok: HTTP 409
- ok: error.tipo = referencia_inactiva
- ok: Trae X-Correlation-ID

## 165_ventas_catalogos_put_catalogos_nombre_registro_id_200

Carpeta: 03 Catalogos (escritura, Administrador) - Caso: edicion 200 PUT

`PUT http://{{vm_host}}:8006/api/v1/catalogos/motivos/12`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "nombre": "Motivo editado 1792629378",
  "descripcion": "Editado desde Postman"
}
```

**Response - 200 OK** (89 ms, 50 bytes):

```http
Content-Type: application/json
Content-Length: 50
X-Correlation-ID: bfc4fa90d93d4c18
```

```json
{
  "id": 12,
  "catalogo": "motivos",
  "actualizado": true
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: actualizado

## 166_ventas_catalogos_put_catalogos_nombre_registro_id_400

Carpeta: 03 Catalogos (escritura, Administrador) - Caso: edicion 400 tipo invalido

`PUT http://{{vm_host}}:8006/api/v1/catalogos/motivos/12`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "nombre": 123
}
```

**Response - 400 BAD REQUEST** (74 ms, 171 bytes):

```http
Content-Type: application/json
Content-Length: 171
X-Correlation-ID: 13b93a43b5cc4978
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Campos invalidos.",
    "detalles": [
      {
        "campo": "nombre",
        "problema": "debe ser texto"
      }
    ],
    "correlation_id": "13b93a43b5cc4978"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 167_ventas_catalogos_put_catalogos_nombre_registro_id_404

Carpeta: 03 Catalogos (escritura, Administrador) - Caso: edicion 404 inexistente

`PUT http://{{vm_host}}:8006/api/v1/catalogos/motivos/999999`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "nombre": "Motivo fantasma"
}
```

**Response - 404 NOT FOUND** (90 ms, 134 bytes):

```http
Content-Type: application/json
Content-Length: 134
X-Correlation-ID: 3105123c859347bb
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Registro inexistente.",
    "detalles": null,
    "correlation_id": "3105123c859347bb"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 168_ventas_catalogos_patch_catalogos_nombre_id_estado_200

Carpeta: 03 Catalogos (escritura, Administrador) - Caso: estado 200 desactivar

`PATCH http://{{vm_host}}:8006/api/v1/catalogos/motivos/12/estado`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "activo": false
}
```

**Response - 200 OK** (149 ms, 25 bytes):

```http
Content-Type: application/json
Content-Length: 25
X-Correlation-ID: 093ee868f7fb44f8
```

```json
{
  "id": 12,
  "activo": false
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: inactivo

## 169_ventas_catalogos_patch_catalogos_nombre_id_estado_400

Carpeta: 03 Catalogos (escritura, Administrador) - Caso: estado 400 booleano invalido

`PATCH http://{{vm_host}}:8006/api/v1/catalogos/motivos/12/estado`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "activo": "quizas"
}
```

**Response - 400 BAD REQUEST** (76 ms, 135 bytes):

```http
Content-Type: application/json
Content-Length: 135
X-Correlation-ID: 7345fc6af4f24bfc
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "activo debe ser booleano.",
    "detalles": null,
    "correlation_id": "7345fc6af4f24bfc"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 170_ventas_catalogos_patch_catalogos_nombre_id_estado_404

Carpeta: 03 Catalogos (escritura, Administrador) - Caso: estado 404 inexistente

`PATCH http://{{vm_host}}:8006/api/v1/catalogos/motivos/999999/estado`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "activo": true
}
```

**Response - 404 NOT FOUND** (84 ms, 134 bytes):

```http
Content-Type: application/json
Content-Length: 134
X-Correlation-ID: 94eb75246dfe437c
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Registro inexistente.",
    "detalles": null,
    "correlation_id": "94eb75246dfe437c"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 171_ventas_catalogos_delete_catalogos_nombre_registro_id_200

Carpeta: 03 Catalogos (escritura, Administrador) - Caso: baja 200 desactivar

`DELETE http://{{vm_host}}:8006/api/v1/catalogos/motivos/13`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (87 ms, 25 bytes):

```http
Content-Type: application/json
Content-Length: 25
X-Correlation-ID: 12f54746a5e548a4
```

```json
{
  "id": 13,
  "activo": false
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 172_ventas_catalogos_delete_catalogos_nombre_registro_id_404

Carpeta: 03 Catalogos (escritura, Administrador) - Caso: baja 404 inexistente

`DELETE http://{{vm_host}}:8006/api/v1/catalogos/motivos/999999`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 404 NOT FOUND** (82 ms, 134 bytes):

```http
Content-Type: application/json
Content-Length: 134
X-Correlation-ID: cbc783a48c2641c0
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Registro inexistente.",
    "detalles": null,
    "correlation_id": "cbc783a48c2641c0"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

