# Ejecuciones reales - `analisis_auditoria`

Salida de `newman run docs/postman/analisis_auditoria.postman_collection.json` contra la VM (2026-10-22 00:43 UTC). Verificaciones: 101 (0 fallidas). Tokens, contrasenas e IP de la VM estan ocultos (`***jwt***`, `***`, `{{vm_host}}`).

## 209_analisis_auditoria_get_health_200

Carpeta: 00 Preparacion (tokens) - Caso: health 200

`GET http://{{vm_host}}:8008/health`

**Request - headers:**

```http
Accept: application/json
```

**Response - 200 OK** (97 ms, 186 bytes):

```http
Content-Type: application/json
Content-Length: 186
X-Correlation-ID: c1acf032e1db4765
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
  }
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: postgresql ok
- ok: redis ok
- ok: mongodb ok

## 210_analisis_auditoria_post_clasificar_motivo_200

Carpeta: 01 Clasificar motivo (POST) - Caso: clasificar 200 cliente

`POST http://{{vm_host}}:8008/api/v1/analisis/clasificar-motivo`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "descripcion": "El producto llego roto y el empaque aplastado por el golpe."
}
```

**Response - 200 OK** (166 ms, 220 bytes):

```http
Content-Type: application/json
Content-Length: 220
X-Correlation-ID: 69c1fa8d8da64385
```

```json
{
  "sugerencias": [
    {
      "motivo": "Producto danado",
      "puntaje": 3,
      "coincidencias": [
        "aplastado",
        "golpe",
        "roto"
      ],
      "motivo_id": 1
    }
  ],
  "requiere_confirmacion": true,
  "explicacion": "La clasificacion orienta; el usuario confirma el motivo."
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: requiere confirmacion

## 211_analisis_auditoria_post_clasificar_motivo_200_xml

Carpeta: 01 Clasificar motivo (POST) - Caso: clasificar 200 analista XML

`POST http://{{vm_host}}:8008/api/v1/analisis/clasificar-motivo`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/xml
Accept: application/xml
```

**Request - body:**

```
<clasificacion>
  <descripcion>La leche llego caliente, la temperatura estaba alta.</descripcion>
</clasificacion>
```

**Response - 200 OK** (119 ms, 400 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 400
X-Correlation-ID: b2bdf0e9e7874c55
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<clasificacion><sugerencias><item><motivo>Cadena de frio rota</motivo><puntaje>2</puntaje><coincidencias><item>caliente</item><item>temperatura</item></coincidencias><motivo_id>4</motivo_id></item></sugerencias><requiere_confirmacion>true</requiere_confirmacion><explicacion>La clasificacion orienta; el usuario confirma el motivo.</explicacion></clasificacion>
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 212_analisis_auditoria_post_clasificar_motivo_400

Carpeta: 01 Clasificar motivo (POST) - Caso: clasificar 400 descripcion corta

`POST http://{{vm_host}}:8008/api/v1/analisis/clasificar-motivo`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "descripcion": "roto"
}
```

**Response - 400 BAD REQUEST** (77 ms, 163 bytes):

```http
Content-Type: application/json
Content-Length: 163
X-Correlation-ID: 163addd945734d36
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "descripcion debe contener entre 10 y 2000 caracteres.",
    "detalles": null,
    "correlation_id": "163addd945734d36"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 213_analisis_auditoria_post_clasificar_motivo_401

Carpeta: 01 Clasificar motivo (POST) - Caso: clasificar 401 sin token

`POST http://{{vm_host}}:8008/api/v1/analisis/clasificar-motivo`

**Request - headers:**

```http
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "descripcion": "El producto llego roto y el empaque aplastado por el golpe."
}
```

**Response - 401 UNAUTHORIZED** (75 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: e987ac94c5a14569
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "e987ac94c5a14569"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = no_autenticado
- ok: Trae X-Correlation-ID

## 214_analisis_auditoria_post_clasificar_motivo_403

Carpeta: 01 Clasificar motivo (POST) - Caso: clasificar 403 centro

`POST http://{{vm_host}}:8008/api/v1/analisis/clasificar-motivo`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "descripcion": "El producto llego roto y el empaque aplastado por el golpe."
}
```

**Response - 403 FORBIDDEN** (168 ms, 271 bytes):

```http
Content-Type: application/json
Content-Length: 271
X-Correlation-ID: 0ec624c8ec184535
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
        "Cliente",
        "Administrador",
        "Analista de Devoluciones"
      ]
    },
    "correlation_id": "0ec624c8ec184535"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 215_analisis_auditoria_post_sincronizar_403

Carpeta: 02 Sincronizar y Pareto - Caso: sincronizar 403 cliente

`POST http://{{vm_host}}:8008/api/v1/analisis/sincronizar`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{}
```

**Response - 403 FORBIDDEN** (70 ms, 232 bytes):

```http
Content-Type: application/json
Content-Length: 232
X-Correlation-ID: 9f4121c5c634409d
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
    "correlation_id": "9f4121c5c634409d"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 216_analisis_auditoria_post_sincronizar_401

Carpeta: 02 Sincronizar y Pareto - Caso: sincronizar 401 sin token

`POST http://{{vm_host}}:8008/api/v1/analisis/sincronizar`

**Request - headers:**

```http
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{}
```

**Response - 401 UNAUTHORIZED** (71 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: 9d5fc5911bb14275
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "9d5fc5911bb14275"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = no_autenticado
- ok: Trae X-Correlation-ID

## 217_analisis_auditoria_post_sincronizar_200

Carpeta: 02 Sincronizar y Pareto - Caso: sincronizar 200 exitoso

`POST http://{{vm_host}}:8008/api/v1/analisis/sincronizar`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{}
```

**Response - 200 OK** (109 ms, 119 bytes):

```http
Content-Type: application/json
Content-Length: 119
X-Correlation-ID: 6034e0ffb849484f
```

```json
{
  "casos_sincronizados": 38,
  "version_cache": 7,
  "fecha": "2026-10-22T00:43:11.774152+00:00",
  "solo_lectura_postgresql": true
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: sincronizo casos

## 218_analisis_auditoria_get_pareto_200

Carpeta: 02 Sincronizar y Pareto - Caso: pareto 200 miss

`GET http://{{vm_host}}:8008/api/v1/analisis/pareto?dimension=motivo&medida=frecuencia`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (84 ms, 912 bytes):

```http
Content-Type: application/json
Content-Length: 912
X-Correlation-ID: c1d6c60438414978
```

```json
{
  "dimension": "motivo",
  "medida": "frecuencia",
  "total_general": 38.0,
  "categorias": [
    {
      "etiqueta": "Cadena de frio rota",
      "total": 12.0,
      "casos": 12,
      "porcentaje": 31.58,
      "porcentaje_acumulado": 31.58
    },
    {
      "etiqueta": "Caducidad proxima",
      "total": 8.0,
      "casos": 8,
      "porcentaje": 21.05,
      "porcentaje_acumulado": 52.63
    },
    {
      "etiqueta": "Etiqueta incorrecta",
      "total": 7.0,
      "casos": 7,
      "porcentaje": 18.42,
      "porcentaje_acumulado": 71.05
    },
    {
      "etiqueta": "Caducidad vencida",
      "total": 3.0,
      "casos": 3,
      "porcentaje": 7.89,
      "porcentaje_acumulado": 78.95
    },
    {
      "etiqueta": "Calidad inferior",
      "total": 3.0,
      "casos": 3,
      "porcentaje": 7.89,
      "porcentaje_acumulado": 86.84
    },
    {
      "etiqueta": "Producto danado",
      "total": 3.0,
      "casos": 3,
      "porcentaje": 7.89,
      "porcentaje_acumulado": 94.74
    },
    {
      "etiqueta": "Error en el pedido",
      "total": 2.0,
      "casos": 2,
      "porcentaje": 5.26,
      "porcentaje_acumulado": 100.0
    }
  ],
  "interpretacion": "Patrones para revision humana; no confirman causalidad.",
  "cache": "miss",
  "version_datos": "7"
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: cache miss

## 219_analisis_auditoria_get_pareto_200

Carpeta: 02 Sincronizar y Pareto - Caso: pareto 200 hit

`GET http://{{vm_host}}:8008/api/v1/analisis/pareto?dimension=motivo&medida=frecuencia`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (162 ms, 911 bytes):

```http
Content-Type: application/json
Content-Length: 911
X-Correlation-ID: d82bc42a455641c5
```

```json
{
  "dimension": "motivo",
  "medida": "frecuencia",
  "total_general": 38.0,
  "categorias": [
    {
      "etiqueta": "Cadena de frio rota",
      "total": 12.0,
      "casos": 12,
      "porcentaje": 31.58,
      "porcentaje_acumulado": 31.58
    },
    {
      "etiqueta": "Caducidad proxima",
      "total": 8.0,
      "casos": 8,
      "porcentaje": 21.05,
      "porcentaje_acumulado": 52.63
    },
    {
      "etiqueta": "Etiqueta incorrecta",
      "total": 7.0,
      "casos": 7,
      "porcentaje": 18.42,
      "porcentaje_acumulado": 71.05
    },
    {
      "etiqueta": "Caducidad vencida",
      "total": 3.0,
      "casos": 3,
      "porcentaje": 7.89,
      "porcentaje_acumulado": 78.95
    },
    {
      "etiqueta": "Calidad inferior",
      "total": 3.0,
      "casos": 3,
      "porcentaje": 7.89,
      "porcentaje_acumulado": 86.84
    },
    {
      "etiqueta": "Producto danado",
      "total": 3.0,
      "casos": 3,
      "porcentaje": 7.89,
      "porcentaje_acumulado": 94.74
    },
    {
      "etiqueta": "Error en el pedido",
      "total": 2.0,
      "casos": 2,
      "porcentaje": 5.26,
      "porcentaje_acumulado": 100.0
    }
  ],
  "interpretacion": "Patrones para revision humana; no confirman causalidad.",
  "cache": "hit",
  "version_datos": "7"
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: cache hit

## 220_analisis_auditoria_get_pareto_200_xml

Carpeta: 02 Sincronizar y Pareto - Caso: pareto 200 XML por proveedor y costo

`GET http://{{vm_host}}:8008/api/v1/analisis/pareto?dimension=proveedor&medida=costo`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/xml
```

**Response - 200 OK** (82 ms, 986 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 986
X-Correlation-ID: 73e58c3d3a3047cf
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<pareto><dimension>proveedor</dimension><medida>costo</medida><total_general>4003.78</total_general><categorias><item><etiqueta>Lacteos del Norte</etiqueta><total>1705.93</total><casos>16</casos><porcentaje>42.61</porcentaje><porcentaje_acumulado>42.61</porcentaje_acumulado></item><item><etiqueta>Abarrotes Monterrey</etiqueta><total>1408.79</total><casos>9</casos><porcentaje>35.19</porcentaje><porcentaje_acumulado>77.79</porcentaje_acumulado></item><item><etiqueta>CampoVerde Agricola</etiqueta><total>542.68</total><casos>10</casos><porcentaje>13.55</porcentaje><porcentaje_acumulado>91.35</porcentaje_acumulado></item><item><etiqueta>Avicola Real</etiqueta><total>346.38</total><casos>3</casos><porcentaje>8.65</porcentaje><porcentaje_acumulado>100.0</porcentaje_acumulado></item></categorias><interpretacion>Patrones para revision humana; no confirman causalidad.</interpretacion><cache>miss</cache><version_datos>7</version_datos></pareto>
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 221_analisis_auditoria_get_pareto_400

Carpeta: 02 Sincronizar y Pareto - Caso: pareto 400 dimension desconocida

`GET http://{{vm_host}}:8008/api/v1/analisis/pareto?dimension=color`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 400 BAD REQUEST** (74 ms, 141 bytes):

```http
Content-Type: application/json
Content-Length: 141
X-Correlation-ID: 5e1f748fa7b9434f
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Dimension o medida desconocida.",
    "detalles": null,
    "correlation_id": "5e1f748fa7b9434f"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 222_analisis_auditoria_get_pareto_400

Carpeta: 02 Sincronizar y Pareto - Caso: pareto 400 fecha invalida

`GET http://{{vm_host}}:8008/api/v1/analisis/pareto?desde=ayer`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 400 BAD REQUEST** (75 ms, 146 bytes):

```http
Content-Type: application/json
Content-Length: 146
X-Correlation-ID: 8cdbd64d22d046be
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "desde debe tener formato AAAA-MM-DD.",
    "detalles": null,
    "correlation_id": "8cdbd64d22d046be"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 223_analisis_auditoria_get_pareto_400

Carpeta: 02 Sincronizar y Pareto - Caso: pareto 400 rango invertido

`GET http://{{vm_host}}:8008/api/v1/analisis/pareto?desde=2026-12-31&hasta=2026-01-01`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 400 BAD REQUEST** (151 ms, 145 bytes):

```http
Content-Type: application/json
Content-Length: 145
X-Correlation-ID: c704d71e5f804ce8
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "hasta no puede ser menor que desde.",
    "detalles": null,
    "correlation_id": "c704d71e5f804ce8"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 224_analisis_auditoria_get_pareto_403

Carpeta: 02 Sincronizar y Pareto - Caso: pareto 403 cliente

`GET http://{{vm_host}}:8008/api/v1/analisis/pareto`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 403 FORBIDDEN** (73 ms, 232 bytes):

```http
Content-Type: application/json
Content-Length: 232
X-Correlation-ID: ab2d16ab54a64e13
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
    "correlation_id": "ab2d16ab54a64e13"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 225_analisis_auditoria_get_pareto_401

Carpeta: 02 Sincronizar y Pareto - Caso: pareto 401 token invalido

`GET http://{{vm_host}}:8008/api/v1/analisis/pareto`

**Request - headers:**

```http
Authorization: Bearer esto-no-es-un-token
Accept: application/json
```

**Response - 401 UNAUTHORIZED** (76 ms, 136 bytes):

```http
Content-Type: application/json
Content-Length: 136
X-Correlation-ID: ede8629c88b2496a
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "token_invalido",
    "mensaje": "El token no es valido.",
    "detalles": null,
    "correlation_id": "ede8629c88b2496a"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = token_invalido
- ok: Trae X-Correlation-ID

## 226_analisis_auditoria_get_resumen_200

Carpeta: 03 Resumen, alertas y eventos - Caso: resumen 200

`GET http://{{vm_host}}:8008/api/v1/analisis/resumen`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (74 ms, 90 bytes):

```http
Content-Type: application/json
Content-Length: 90
X-Correlation-ID: 35c64d7317da4801
```

```json
{
  "casos_sincronizados": 38,
  "reportes_pareto": 6,
  "nota": "No implica causa raiz comprobada."
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: trae contadores

## 227_analisis_auditoria_get_resumen_403

Carpeta: 03 Resumen, alertas y eventos - Caso: resumen 403 cliente

`GET http://{{vm_host}}:8008/api/v1/analisis/resumen`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 403 FORBIDDEN** (74 ms, 232 bytes):

```http
Content-Type: application/json
Content-Length: 232
X-Correlation-ID: 9ab9eec80728458f
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
    "correlation_id": "9ab9eec80728458f"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 228_analisis_auditoria_get_alertas_fraude_200

Carpeta: 03 Resumen, alertas y eventos - Caso: alertas 200

`GET http://{{vm_host}}:8008/api/v1/analisis/alertas-fraude`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (139 ms, 690 bytes):

```http
Content-Type: application/json
Content-Length: 690
X-Correlation-ID: d84efc2e33f04ca6
```

```json
{
  "datos": [
    {
      "cliente_id": 10,
      "cliente": "Ana Lopez Garcia",
      "devoluciones_90_dias": 13,
      "rechazadas": 0,
      "monto_reembolsado": 405.84,
      "razones": [
        "frecuencia alta en 90 dias"
      ],
      "requiere_revision_humana": true
    },
    {
      "cliente_id": 11,
      "cliente": "Miguel Ramos Soto",
      "devoluciones_90_dias": 13,
      "rechazadas": 2,
      "monto_reembolsado": 108.22,
      "razones": [
        "frecuencia alta en 90 dias",
        "multiples solicitudes rechazadas"
      ],
      "requiere_revision_humana": true
    },
    {
      "cliente_id": 12,
      "cliente": "Sofia Herrera",
      "devoluciones_90_dias": 12,
      "rechazadas": 0,
      "monto_reembolsado": 278.42,
      "razones": [
        "frecuencia alta en 90 dias"
      ],
      "requiere_revision_humana": true
    }
  ],
  "total": 3,
  "aviso": "Son indicadores preventivos, no una determinacion de fraude."
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: aviso de no determinacion

## 229_analisis_auditoria_get_alertas_fraude_200_xml

Carpeta: 03 Resumen, alertas y eventos - Caso: alertas 200 XML

`GET http://{{vm_host}}:8008/api/v1/analisis/alertas-fraude`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/xml
```

**Response - 200 OK** (93 ms, 1145 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 1145
X-Correlation-ID: bb7252163ddc447a
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<alertas_fraude><datos><item><cliente_id>10</cliente_id><cliente>Ana Lopez Garcia</cliente><devoluciones_90_dias>13</devoluciones_90_dias><rechazadas>0</rechazadas><monto_reembolsado>405.84</monto_reembolsado><razones><item>frecuencia alta en 90 dias</item></razones><requiere_revision_humana>true</requiere_revision_humana></item><item><cliente_id>11</cliente_id><cliente>Miguel Ramos Soto</cliente><devoluciones_90_dias>13</devoluciones_90_dias><rechazadas>2</rechazadas><monto_reembolsado>108.22</monto_reembolsado><razones><item>frecuencia alta en 90 dias</item><item>multiples solicitudes rechazadas</item></razones><requiere_revision_humana>true</requiere_revision_humana></item><item><cliente_id>12</cliente_id><cliente>Sofia Herrera</cliente><devoluciones_90_dias>12</devoluciones_90_dias><rechazadas>0</rechazadas><monto_reembolsado>278.42</monto_reembolsado><razones><item>frecuencia alta en 90 dias</item></razones><requiere_revision_humana>true</requiere_revision_humana></item></datos><total>3</total><aviso>Son indicadores preventivos, no una determinacion de fraude.</aviso></alertas_fraude>
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 230_analisis_auditoria_get_alertas_fraude_403

Carpeta: 03 Resumen, alertas y eventos - Caso: alertas 403 cliente

`GET http://{{vm_host}}:8008/api/v1/analisis/alertas-fraude`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 403 FORBIDDEN** (76 ms, 232 bytes):

```http
Content-Type: application/json
Content-Length: 232
X-Correlation-ID: ec9c037ef7bd4f1f
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
    "correlation_id": "ec9c037ef7bd4f1f"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 231_analisis_auditoria_get_eventos_200

Carpeta: 03 Resumen, alertas y eventos - Caso: eventos 200 paginado

`GET http://{{vm_host}}:8008/api/v1/analisis/eventos?pagina=1&por_pagina=5`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (75 ms, 1005 bytes):

```http
Content-Type: application/json
Content-Length: 1005
X-Correlation-ID: f58c19a571c44d05
```

```json
{
  "datos": [
    {
      "id": "6ad95b98e8c6892d152d3f05",
      "servicio": "devoluciones",
      "tipo": "devolucion_cancelada",
      "usuario_id": 11,
      "correlation_id": "b4c2cb4c21b24e7e",
      "fecha": "2026-10-22T00:40:56.020000+00:00"
    },
    {
      "id": "6ad95b93e8c6892d152d3f04",
      "servicio": "devoluciones",
      "tipo": "devolucion_registrada",
      "usuario_id": 11,
      "correlation_id": "f30a1513ec204262",
      "fecha": "2026-10-22T00:40:51.428000+00:00"
    },
    {
      "id": "6ad95ac80194762f256264d2",
      "servicio": "devoluciones",
      "tipo": "devolucion_cancelada",
      "usuario_id": 11,
      "correlation_id": "426efbdc1104455d",
      "fecha": "2026-10-22T00:37:28.699000+00:00"
    },
    {
      "id": "6ad95ac8e8c6892d152d3f03",
      "servicio": "devoluciones",
      "tipo": "devolucion_autorizacion",
      "usuario_id": 16,
      "correlation_id": "feca4df0209d4877",
      "fecha": "2026-10-22T00:37:28.264000+00:00"
    },
    {
      "id": "6ad95ac70194762f256264d1",
      "servicio": "devoluciones",
      "tipo": "devolucion_corregida",
      "usuario_id": 11,
      "correlation_id": "3b9720bb9dc84aaa",
      "fecha": "2026-10-22T00:37:27.964000+00:00"
    }
  ],
  "paginacion": {
    "pagina": 1,
    "por_pagina": 5,
    "total": 12,
    "paginas": 3
  }
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: trae paginacion

## 232_analisis_auditoria_get_eventos_200_xml

Carpeta: 03 Resumen, alertas y eventos - Caso: eventos 200 XML

`GET http://{{vm_host}}:8008/api/v1/analisis/eventos?servicio=devoluciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/xml
```

**Response - 200 OK** (75 ms, 3026 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 3026
X-Correlation-ID: dc28822cd7944334
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<eventos><datos><item><id>6ad95b98e8c6892d152d3f05</id><servicio>devoluciones</servicio><tipo>devolucion_cancelada</tipo><usuario_id>11</usuario_id><correlation_id>b4c2cb4c21b24e7e</correlation_id><fecha>2026-10-22T00:40:56.020000+00:00</fecha></item><item><id>6ad95b93e8c6892d152d3f04</id><servicio>devoluciones</servicio><tipo>devolucion_registrada</tipo><usuario_id>11</usuario_id><correlation_id>f30a1513ec204262</correlation_id><fecha>2026-10-22T00:40:51.428000+00:00</fecha></item><item><id>6ad95ac80194762f256264d2</id><servicio>devoluciones</servicio><tipo>devolucion_cancelada</tipo><usuario_id>11</usuario_id><correlation_id>426efbdc1104455d</correlation_id><fecha>2026-10-22T00:37:28.699000+00:00</fecha></item><item><id>6ad95ac8e8c6892d152d3f03</id><servicio>devoluciones</servicio><tipo>devolucion_autorizacion</tipo><usuario_id>16</usuario_id><correlation_id>feca4df0209d4877</correlation_id><fecha>2026-10-22T00:37:28.264000+00:00</fecha></item><item><id>6ad95ac70194762f256264d1</id><servicio>devoluciones</servicio><tipo>devolucion_corregida</tipo><usuario_id>11</usuario_id><correlation_id>3b9720bb9dc84aaa</correlation_id><fecha>2026-10-22T00:37:27.964000+00:00</fecha></item><item><id>6ad95ac70194762f256264d0</id><servicio>devoluciones</servicio><tipo>devolucion_solicitud_informacion</tipo><usuario_id>16</usuario_id><correlation_id>4c1c883a2bc949ef</correlation_id><fecha>2026-10-22T00:37:27.841000+00:00</fecha></item><item><id>6ad95ac5e8c6892d152d3f02</id><servicio>devoluciones</servicio><tipo>devolucion_registrada</tipo><usuario_id>11</usuario_id><correlation_id>6952287b6688443f</correlation_id><fecha>2026-10-22T00:37:25.802000+00:00</fecha></item><item><id>6ad95ac50194762f256264cf</id><servicio>devoluciones</servicio><tipo>devolucion_registrada</tipo><usuario_id>11</usuario_id><correlation_id>f09c57e7806e439c</correlation_id><fecha>2026-10-22T00:37:25.650000+00:00</fecha></item><item><id>6ad8f4297446290945431fba</id><servicio>devoluciones</servicio><tipo>devolucion_autorizacion</tipo><usuario_id>16</usuario_id><correlation_id>189b811d970e4994</correlation_id><fecha>2026-10-21T17:19:37.834000+00:00</fecha></item><item><id>6ad8f3ec7446290945431fb9</id><servicio>devoluciones</servicio><tipo>devolucion_registrada</tipo><usuario_id>10</usuario_id><correlation_id>b741f3e0b06a4cd1</correlation_id><fecha>2026-10-21T17:18:36.306000+00:00</fecha></item><item><id>6ad8dfff8ade38c566776546</id><servicio>devoluciones</servicio><
... (recortado, 3026 caracteres en total)
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 233_analisis_auditoria_get_eventos_400

Carpeta: 03 Resumen, alertas y eventos - Caso: eventos 400 correlation_id largo

`GET http://{{vm_host}}:8008/api/v1/analisis/eventos?correlation_id=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 400 BAD REQUEST** (158 ms, 141 bytes):

```http
Content-Type: application/json
Content-Length: 141
X-Correlation-ID: 027f7ac457a74c76
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "correlation_id demasiado largo.",
    "detalles": null,
    "correlation_id": "027f7ac457a74c76"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 234_analisis_auditoria_get_eventos_400

Carpeta: 03 Resumen, alertas y eventos - Caso: eventos 400 paginacion invalida

`GET http://{{vm_host}}:8008/api/v1/analisis/eventos?por_pagina=0`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 400 BAD REQUEST** (74 ms, 209 bytes):

```http
Content-Type: application/json
Content-Length: 209
X-Correlation-ID: caed47e715834ed3
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
    "correlation_id": "caed47e715834ed3"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 235_analisis_auditoria_get_eventos_403

Carpeta: 03 Resumen, alertas y eventos - Caso: eventos 403 cliente

`GET http://{{vm_host}}:8008/api/v1/analisis/eventos`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 403 FORBIDDEN** (75 ms, 232 bytes):

```http
Content-Type: application/json
Content-Length: 232
X-Correlation-ID: cb8278a4ad60443c
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
    "correlation_id": "cb8278a4ad60443c"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 236_analisis_auditoria_get_auditoria_200

Carpeta: 04 Auditoria (bitacora) - Caso: bitacora 200 paginada

`GET http://{{vm_host}}:8008/api/v1/auditoria?pagina=1&por_pagina=5`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (83 ms, 1225 bytes):

```http
Content-Type: application/json
Content-Length: 1225
X-Correlation-ID: 950d2943b29e4923
```

```json
{
  "datos": [
    {
      "id": 535,
      "accion": "analisis_sincronizado",
      "entidad": "resultados_analisis",
      "entidad_id": null,
      "detalle": "Actualizados 38 casos en MongoDB",
      "correlation_id": "6034e0ffb849484f",
      "fecha": "2026-10-22T00:43:11.757430+00:00",
      "usuario": "Josue Berdeal"
    },
    {
      "id": 534,
      "accion": "login_api",
      "entidad": "usuarios",
      "entidad_id": 14,
      "detalle": "Inicio de sesion por API, JWT emitido",
      "correlation_id": "b70e2d5684e748b0",
      "fecha": "2026-10-22T00:43:10.668578+00:00",
      "usuario": "Roberto Sandoval"
    },
    {
      "id": 533,
      "accion": "login_api",
      "entidad": "usuarios",
      "entidad_id": 18,
      "detalle": "Inicio de sesion por API, JWT emitido",
      "correlation_id": "d15da017e6b44170",
      "fecha": "2026-10-22T00:43:10.467235+00:00",
      "usuario": "Pablo Flores"
    },
    {
      "id": 532,
      "accion": "login_api",
      "entidad": "usuarios",
      "entidad_id": 16,
      "detalle": "Inicio de sesion por API, JWT emitido",
      "correlation_id": "3dcada4d12c44e6a",
      "fecha": "2026-10-22T00:43:10.175850+00:00",
      "usuario": "Josue Berdeal"
    },
    {
      "id": 531,
      "accion": "login_api",
      "entidad": "usuarios",
      "entidad_id": 11,
      "detalle": "Inicio de sesion por API, JWT emitido",
      "correlation_id": "a196f36f6d524109",
      "fecha": "2026-10-22T00:43:09.977766+00:00",
      "usuario": "Miguel Ramos Soto"
    }
  ],
  "paginacion": {
    "pagina": 1,
    "por_pagina": 5,
    "total": 535,
    "paginas": 107
  }
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: trae paginacion

## 237_analisis_auditoria_get_auditoria_200_xml

Carpeta: 04 Auditoria (bitacora) - Caso: bitacora 200 filtro XML

`GET http://{{vm_host}}:8008/api/v1/auditoria?accion=alta_devolucion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/xml
```

**Response - 200 OK** (168 ms, 6982 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 6982
X-Correlation-ID: 533b42cb29614cf9
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<bitacora><datos><item><id>516</id><accion>alta_devolucion</accion><entidad>devoluciones</entidad><entidad_id>83</entidad_id><detalle>Se registro la devolucion DEV-2026-0083 sobre la venta VTA-2026-0006 (API)</detalle><correlation_id>f30a1513ec204262</correlation_id><fecha>2026-10-22T00:40:51.416461+00:00</fecha><usuario>Miguel Ramos Soto</usuario></item><item><id>489</id><accion>alta_devolucion</accion><entidad>devoluciones</entidad><entidad_id>82</entidad_id><detalle>Se registro la devolucion DEV-2026-0082 sobre la venta VTA-2026-0006 (API)</detalle><correlation_id>6952287b6688443f</correlation_id><fecha>2026-10-22T00:37:25.789330+00:00</fecha><usuario>Miguel Ramos Soto</usuario></item><item><id>488</id><accion>alta_devolucion</accion><entidad>devoluciones</entidad><entidad_id>81</entidad_id><detalle>Se registro la devolucion DEV-2026-0081 sobre la venta VTA-2026-0006 (API)</detalle><correlation_id>f09c57e7806e439c</correlation_id><fecha>2026-10-22T00:37:25.634753+00:00</fecha><usuario>Miguel Ramos Soto</usuario></item><item><id>466</id><accion>alta_devolucion</accion><entidad>devoluciones</entidad><entidad_id>80</entidad_id><detalle>Se registro la devolucion DEV-2026-0080 sobre la venta VTA-2026-0001 (API)</detalle><correlation_id>6f5bff2895db49ac</correlation_id><fecha>2026-10-21T18:29:32.819430+00:00</fecha><usuario>Miguel Ramos Soto</usuario></item><item><id>461</id><accion>alta_devolucion</accion><entidad>devoluciones</entidad><entidad_id>79</entidad_id><detalle>Se registro la devolucion DEV-2026-0079 sobre la venta VTA-2026-0001 (API)</detalle><correlation_id>c748e09318a24fd9</correlation_id><fecha>2026-10-21T18:29:32.507123+00:00</fecha><usuario>Miguel Ramos Soto</usuario></item><item><id>405</id><accion>alta_devolucion</accion><entidad>devoluciones</entidad><entidad_id>66</entidad_id><detalle>Se registro la devolucion DEV-2026-0066 sobre la venta VTA-2026-0001 (API)</detalle><correlation_id>389220671aed43b9</correlation_id><fecha>2026-10-21T18:22:21.520706+00:00</fecha><usuario>Miguel Ramos Soto</usuario></item><item><id>400</id><accion>alta_devolucion</accion><entidad>devoluciones</entidad><entidad_id>65</entidad_id><detalle>Se registro la devolucion DEV-2026-0065 sobre la venta VTA-2026-0001 (API)</detalle><correlation_id>8853996027f54414</correlation_id><fecha>2026-10-21T18:22:21.214355+00:00</fecha><usuario>Miguel Ramos Soto</usuario></item><item><id>360</id><accion>alta_devolucion</accion><entidad>devol
... (recortado, 6982 caracteres en total)
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 238_analisis_auditoria_get_auditoria_400

Carpeta: 04 Auditoria (bitacora) - Caso: bitacora 400 filtro largo

`GET http://{{vm_host}}:8008/api/v1/auditoria?accion=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 400 BAD REQUEST** (76 ms, 140 bytes):

```http
Content-Type: application/json
Content-Length: 140
X-Correlation-ID: ddee5095a7c64ae1
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Filtro accion demasiado largo.",
    "detalles": null,
    "correlation_id": "ddee5095a7c64ae1"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 239_analisis_auditoria_get_auditoria_403

Carpeta: 04 Auditoria (bitacora) - Caso: bitacora 403 cliente

`GET http://{{vm_host}}:8008/api/v1/auditoria`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 403 FORBIDDEN** (74 ms, 232 bytes):

```http
Content-Type: application/json
Content-Length: 232
X-Correlation-ID: c2f9572a4a5f453a
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
    "correlation_id": "c2f9572a4a5f453a"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 240_analisis_auditoria_get_auditoria_401

Carpeta: 04 Auditoria (bitacora) - Caso: bitacora 401 sin token

`GET http://{{vm_host}}:8008/api/v1/auditoria`

**Request - headers:**

```http
Accept: application/json
```

**Response - 401 UNAUTHORIZED** (72 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: 2947590dd2084f58
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "2947590dd2084f58"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = no_autenticado
- ok: Trae X-Correlation-ID

