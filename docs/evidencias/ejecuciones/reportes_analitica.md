# Evidencia con curl - `reportes-analitica`

Ejecutada en la VM el 2026-11-22 18:34 UTC con `scripts/evidencias/ejecutar.py reportes` (commit `79dabf1`).
Casos: **60**, correctos: **60**, con falla: **0**. Los tokens y la contrasena de demo estan ocultos; la IP de la VM se muestra como `$VM_HOST`.

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
export TOKEN_INSPECTOR=$(login valentina.inspector@demo.mx)
export TOKEN_REEMBOLSOS=$(login carla.reembolsos@demo.mx)
export TOKEN_SUPERVISOR=$(login jorge.supervisor@demo.mx)
```

El login admite 10 intentos por minuto por IP (RNF-13); el token dura 15 minutos.

## Resumen

| Caso | Resultado | HTTP | Descripcion |
|---|---|---|---|
| [P4-REP-01](#p4-rep-01) | correcto | 200 | salud 200 JSON |
| [P4-REP-02](#p4-rep-02) | correcto | 200 | salud 200 XML |
| [P4-REP-03](#p4-rep-03) | correcto | 200 | Swagger: documentacion de la API |
| [P4-REP-04](#p4-rep-04) | correcto | 200 | Swagger: especificacion OpenAPI |
| [P4-REP-05](#p4-rep-05) | correcto | 401 | sin token: 401 |
| [P4-REP-06](#p4-rep-06) | correcto | 401 | token invalido: 401 |
| [P4-REP-07](#p4-rep-07) | correcto | 403 | cliente: 403 |
| [P4-REP-08](#p4-rep-08) | correcto | 403 | inspector: 403 en analitica |
| [P4-REP-09](#p4-rep-09) | correcto | 200 | catalogo 200 |
| [P4-REP-10](#p4-rep-10) | correcto | 200 | reporte de devoluciones 200 JSON |
| [P4-REP-11](#p4-rep-11) | correcto | 200 | reporte de devoluciones 200 XML |
| [P4-REP-12](#p4-rep-12) | correcto | 200 | reporte de devoluciones filtrado por estado y fechas |
| [P4-REP-13](#p4-rep-13) | correcto | 200 | reporte de costos 200 |
| [P4-REP-14](#p4-rep-14) | correcto | 200 | reporte de tasas 200 por proveedor |
| [P4-REP-15](#p4-rep-15) | correcto | 200 | reporte de tasas 200 por tienda |
| [P4-REP-16](#p4-rep-16) | correcto | 200 | reporte pareto 200 por motivo |
| [P4-REP-17](#p4-rep-17) | correcto | 200 | reporte pareto 200 por proveedor y costo |
| [P4-REP-18](#p4-rep-18) | correcto | 200 | reporte de tendencia 200 |
| [P4-REP-19](#p4-rep-19) | correcto | 404 | reporte 404 inexistente |
| [P4-REP-20](#p4-rep-20) | correcto | 400 | reporte 400 formato invalido |
| [P4-REP-21](#p4-rep-21) | correcto | 400 | reporte 400 parametro desconocido |
| [P4-REP-22](#p4-rep-22) | correcto | 400 | reporte 400 fecha invalida |
| [P4-REP-23](#p4-rep-23) | correcto | 400 | reporte 400 hasta antes de desde |
| [P4-REP-24](#p4-rep-24) | correcto | 400 | reporte 400 estado desconocido |
| [P4-REP-25](#p4-rep-25) | correcto | 400 | tendencia 400 meses fuera de rango |
| [P4-REP-26](#p4-rep-26) | correcto | 400 | tendencia 400 dimension sin referencia |
| [P4-REP-27](#p4-rep-27) | correcto | 404 | tendencia 404 objeto inexistente |
| [P4-REP-28](#p4-rep-28) | correcto | 200 | descarga CSV de devoluciones |
| [P4-REP-29](#p4-rep-29) | correcto | 200 | descarga Excel de devoluciones |
| [P4-REP-30](#p4-rep-30) | correcto | 200 | descarga PDF de devoluciones |
| [P4-REP-31](#p4-rep-31) | correcto | 200 | descarga CSV de costos |
| [P4-REP-32](#p4-rep-32) | correcto | 200 | descarga Excel de tasas |
| [P4-REP-33](#p4-rep-33) | correcto | 200 | descarga PDF de Pareto |
| [P4-REP-34](#p4-rep-34) | correcto | 200 | descarga CSV de la tendencia de un proveedor |
| [P4-REP-35](#p4-rep-35) | correcto | 429 | descarga 429 tras 20 en un minuto |
| [P4-REP-36](#p4-rep-36) | correcto | 200 | JSON no cuenta para el limite de descargas |
| [P4-REP-37](#p4-rep-37) | correcto | 200 | grafica Pareto 200 |
| [P4-REP-38](#p4-rep-38) | correcto | 200 | grafica de tasas 200 |
| [P4-REP-39](#p4-rep-39) | correcto | 200 | grafica de tendencia 200 |
| [P4-REP-40](#p4-rep-40) | correcto | 406 | grafica 406 en XML |
| [P4-REP-41](#p4-rep-41) | correcto | 404 | grafica 404 inexistente |
| [P4-REP-42](#p4-rep-42) | correcto | 400 | grafica 400 horizonte fuera de rango |
| [P4-REP-43](#p4-rep-43) | correcto | 200 | tendencias 200 |
| [P4-REP-44](#p4-rep-44) | correcto | 200 | tendencias 200 XML |
| [P4-REP-45](#p4-rep-45) | correcto | 200 | tendencias 200 de un proveedor |
| [P4-REP-46](#p4-rep-46) | correcto | 200 | pronosticos 200 |
| [P4-REP-47](#p4-rep-47) | correcto | 400 | pronosticos 400 horizonte invalido |
| [P4-REP-48](#p4-rep-48) | correcto | 200 | anomalias 200 entre proveedores |
| [P4-REP-49](#p4-rep-49) | correcto | 200 | anomalias 200 entre lotes |
| [P4-REP-50](#p4-rep-50) | correcto | 200 | anomalias 200 entre meses |
| [P4-REP-51](#p4-rep-51) | correcto | 400 | anomalias 400 tipo invalido |
| [P4-REP-52](#p4-rep-52) | correcto | 200 | alertas de fraude 200 |
| [P4-REP-53](#p4-rep-53) | correcto | 403 | alertas de fraude 403 supervisor |
| [P4-REP-54](#p4-rep-54) | correcto | 200 | factores 200: proveedor por tienda |
| [P4-REP-55](#p4-rep-55) | correcto | 200 | factores 200: el lote problematico destaca |
| [P4-REP-56](#p4-rep-56) | correcto | 200 | factores 200 XML |
| [P4-REP-57](#p4-rep-57) | correcto | 400 | factores 400 mismo factor dos veces |
| [P4-REP-58](#p4-rep-58) | correcto | 400 | factores 400 ruta no tiene ventas |
| [P4-REP-59](#p4-rep-59) | correcto | 400 | factores 400 limite fuera de rango |
| [P4-REP-60](#p4-rep-60) | correcto | 403 | factores 403 cliente |

## P4-REP-01

**salud 200 JSON**

Objetivo: El servicio informa su estado y el de PostgreSQL y Redis (RF-32).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/health" \
  -H "Accept: application/json"
```

Respuesta - **200 OK** (17 ms, 151 bytes):

```http
Content-Type: application/json
Content-Length: 151
X-Correlation-ID: 8f33f4b683c14040
```

```json
{
  "servicio": "reportes-analitica",
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

Verificaciones:

- ok: HTTP 200
- ok: estado ok
- ok: PostgreSQL ok
- ok: Redis ok

## P4-REP-02

**salud 200 XML**

Objetivo: El mismo endpoint responde XML (RF-31).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/health" \
  -H "Accept: application/xml"
```

Respuesta - **200 OK** (15 ms, 254 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 254
X-Correlation-ID: d7f724b154174db9
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<respuesta><servicio>reportes-analitica</servicio><version>v1</version><estado>ok</estado><dependencias><postgresql><ok>true</ok><error /></postgresql><redis><ok>true</ok><error /></redis></dependencias></respuesta>
```

Verificaciones:

- ok: HTTP 200
- ok: es XML
- ok: estado ok

## P4-REP-03

**Swagger: documentacion de la API**

Objetivo: La API publica su documentacion Swagger.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/docs" \
  -H "Accept: text/html"
```

Respuesta - **200 OK** (8 ms, 430 bytes):

```http
Content-Type: text/html; charset=utf-8
Content-Length: 430
X-Correlation-ID: fb7142b66e474612
```

```text
<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Reportes y analitica</title>
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

## P4-REP-04

**Swagger: especificacion OpenAPI**

Objetivo: La especificacion lista reportes, graficas y analitica.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/openapi.json" \
  -H "Accept: application/json"
```

Respuesta - **200 OK** (7 ms, 9667 bytes):

```http
Content-Type: application/json
Content-Length: 9667
X-Correlation-ID: e6607835b89243d7
```

```json
{
  "openapi": "3.0.3",
  "info": {
    "title": "Reportes y analitica",
    "version": "v1",
    "description": "Reportes en JSON, XML, CSV, Excel y PDF, datos para Highcharts, tendencias, pronosticos y anomalias. Solo lectura. La estadistica es explicable y orienta la revision humana; no determina causas (RN-09)."
  },
  "servers": [
    {
      "url": "http://localhost:8018"
    }
  ],
  "paths": {
    "/health": {
      "get": {
        "summary": "Estado del servicio y sus dependencias",
        "responses": {
          "200": {
            "description": "Servicio ok"
          },
          "503": {
            "description": "Servicio degradado"
          }
        }
      }
    },
    "/api/v1/reportes": {
      "get": {
        "summary": "Catalogo de reportes con sus filtros y formatos",
        "responses": {
          "200": {
            "description": "Reportes disponibles"
          },
          "401": {
            "description": "Sin token"
          },
          "403": {
            "description": "Rol sin permiso"
          }
        },
        "security": [
          {
            "bearerAuth": []
          }
        ]
      }
    },
    "/api/v1/reportes/{nombre}": {
      "get": {
        "summary": "Un reporte en JSON, XML, CSV, Excel o PDF",
        "description": "Reportes: devoluciones, costos, tasas, pareto y tendencia (ver el catalogo para los filtros de cada uno). formato=json (por omision, con pagina y por_pagina) o xml segun Accept; formato=csv, xlsx o pdf descargan el archivo. Limites: csv y xlsx 50000 filas, pdf 3000; si se pasa, 422 y se acota con desde y hasta. Las descargas se limitan a 20 por minuto por usuario y quedan en la bitacora (reporte, formato y numero de filas; nunca los datos). Los archivos no se cachean.",
        "parameters": [
          {
            "name": "nombre",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string"
            }
          },
          {
            "name": "formato",
            "in": "query",
            "schema": {
              "type": "string",
              "enum": [
                "json",
                "csv",
                "xlsx",
                "pdf"
... (recortado: 624 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: incluye reportes
- ok: incluye alertas de fraude

## P4-REP-05

**sin token: 401**

Objetivo: Un endpoint protegido exige JWT (RNF-09).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes" \
  -H "Accept: application/json"
```

Respuesta - **401 UNAUTHORIZED** (7 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: 75af15d59eaa4b57
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "75af15d59eaa4b57"
  }
}
```

Verificaciones:

- ok: HTTP 401
- ok: tipo no_autenticado

## P4-REP-06

**token invalido: 401**

Objetivo: Un token alterado se rechaza (RNF-09).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer no.es.un.jwt"
```

Respuesta - **401 UNAUTHORIZED** (7 ms, 136 bytes):

```http
Content-Type: application/json
Content-Length: 136
X-Correlation-ID: 8e0937b097a34b8e
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "token_invalido",
    "mensaje": "El token no es valido.",
    "detalles": null,
    "correlation_id": "8e0937b097a34b8e"
  }
}
```

Verificaciones:

- ok: HTTP 401
- ok: tipo token_invalido

## P4-REP-07

**cliente: 403**

Objetivo: Los reportes con costos y proveedores no los ve un cliente (RN-13).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_CLIENTE"
```

Respuesta - **403 FORBIDDEN** (10 ms, 271 bytes):

```http
Content-Type: application/json
Content-Length: 271
X-Correlation-ID: c1b31e1427a8464b
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
        "Analista de Devoluciones",
        "Supervisor",
        "Encargado de Reembolsos"
      ]
    },
    "correlation_id": "c1b31e1427a8464b"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-REP-08

**inspector: 403 en analitica**

Objetivo: La lectura es de Administrador, Analista, Supervisor y Encargado de Reembolsos.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/analitica/tendencias" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_INSPECTOR"
```

Respuesta - **403 FORBIDDEN** (9 ms, 273 bytes):

```http
Content-Type: application/json
Content-Length: 273
X-Correlation-ID: aae53d28917a41a4
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "Tu rol no tiene permiso para esta operacion.",
    "detalles": {
      "rol": "Inspector",
      "roles_permitidos": [
        "Administrador",
        "Analista de Devoluciones",
        "Supervisor",
        "Encargado de Reembolsos"
      ]
    },
    "correlation_id": "aae53d28917a41a4"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-REP-09

**catalogo 200**

Objetivo: El catalogo dice que reportes hay, sus filtros y los formatos de descarga (RF-28).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (9 ms, 2160 bytes):

```http
Content-Type: application/json
Content-Length: 2160
X-Correlation-ID: d74383c8d0d14ad8
```

```json
{
  "datos": [
    {
      "nombre": "devoluciones",
      "titulo": "Reporte de devoluciones",
      "formatos": [
        "json",
        "csv",
        "xlsx",
        "pdf"
      ],
      "filtros": [
        {
          "nombre": "desde",
          "tipo": "fecha",
          "opciones": null,
          "por_omision": null
        },
        {
          "nombre": "hasta",
          "tipo": "fecha",
          "opciones": null,
          "por_omision": null
        },
        {
          "nombre": "estado",
          "tipo": "enum",
          "opciones": [
            "solicitada",
            "en_revision",
            "autorizada",
            "rechazada",
            "en_recoleccion",
            "recibida",
            "en_inspeccion",
            "resuelta",
            "cerrada"
          ],
          "por_omision": null
        },
        {
          "nombre": "proveedor_id",
          "tipo": "entero",
          "opciones": null,
          "por_omision": null
        },
        {
          "nombre": "tienda_id",
          "tipo": "entero",
          "opciones": null,
          "por_omision": null
        }
      ]
    },
    {
      "nombre": "costos",
      "titulo": "Costos por devolucion y etapa",
      "formatos": [
        "json",
        "csv",
        "xlsx",
        "pdf"
      ],
      "filtros": [
        {
          "nombre": "desde",
          "tipo": "fecha",
          "opciones": null,
          "por_omision": null
        },
... (recortado: 140 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: cinco reportes
- ok: cinco formatos

## P4-REP-10

**reporte de devoluciones 200 JSON**

Objetivo: Reporte tabular paginado, con sus columnas y los filtros aplicados (RF-28).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/devoluciones?por_pagina=5" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (38 ms, 2077 bytes):

```http
Content-Type: application/json
Content-Length: 2077
X-Correlation-ID: 8662572e7de64697
```

```json
{
  "reporte": "devoluciones",
  "titulo": "Reporte de devoluciones",
  "generado_en": "2026-11-22T18:34:48+00:00",
  "filtros": {},
  "columnas": [
    {
      "clave": "folio",
      "titulo": "Folio",
      "tipo": "texto"
    },
    {
      "clave": "fecha_solicitud",
      "titulo": "Fecha",
      "tipo": "fecha"
    },
    {
      "clave": "estado",
      "titulo": "Estado",
      "tipo": "texto"
    },
    {
      "clave": "motivo",
      "titulo": "Motivo",
      "tipo": "texto"
    },
    {
      "clave": "producto",
      "titulo": "Producto",
      "tipo": "texto"
    },
    {
      "clave": "lote",
      "titulo": "Lote",
      "tipo": "texto"
    },
    {
      "clave": "proveedor",
      "titulo": "Proveedor",
      "tipo": "texto"
    },
    {
      "clave": "tienda",
      "titulo": "Tienda",
      "tipo": "texto"
    },
    {
      "clave": "cantidad_devuelta",
      "titulo": "Unidades",
      "tipo": "entero"
    },
    {
      "clave": "costo_total",
      "titulo": "Costo total",
      "tipo": "dinero"
    }
  ],
  "datos": [
    {
      "folio": "DEV-2026-0087",
      "fecha_solicitud": "2026-10-23",
      "estado": "solicitada",
      "motivo": "Cadena de frio rota",
      "producto": "Arroz blanco 1 kg",
      "lote": "L-2026-301",
      "proveedor": "Abarrotes Monterrey",
      "tienda": "Tienda Valle Oriente",
      "cantidad_devuelta": 1,
      "costo_total": 0.0
    },
... (recortado: 56 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: trae columnas
- ok: hay filas
- ok: a lo mas 5 por pagina
- ok: trae paginacion

Efecto en PostgreSQL - devoluciones vigentes en la base, para contrastar el total:

```sql
SELECT count(*) AS devoluciones FROM devoluciones WHERE eliminado_en IS NULL
```

```text
devoluciones
46
```

## P4-REP-11

**reporte de devoluciones 200 XML**

Objetivo: El mismo reporte en XML (RF-31).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/devoluciones?por_pagina=3" \
  -H "Accept: application/xml" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR"
```

Respuesta - **200 OK** (41 ms, 2194 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 2194
X-Correlation-ID: 2c3f02c45ac442ff
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<reporte><reporte>devoluciones</reporte><titulo>Reporte de devoluciones</titulo><generado_en>2026-11-22T18:34:49+00:00</generado_en><filtros /><columnas><item><clave>folio</clave><titulo>Folio</titulo><tipo>texto</tipo></item><item><clave>fecha_solicitud</clave><titulo>Fecha</titulo><tipo>fecha</tipo></item><item><clave>estado</clave><titulo>Estado</titulo><tipo>texto</tipo></item><item><clave>motivo</clave><titulo>Motivo</titulo><tipo>texto</tipo></item><item><clave>producto</clave><titulo>Producto</titulo><tipo>texto</tipo></item><item><clave>lote</clave><titulo>Lote</titulo><tipo>texto</tipo></item><item><clave>proveedor</clave><titulo>Proveedor</titulo><tipo>texto</tipo></item><item><clave>tienda</clave><titulo>Tienda</titulo><tipo>texto</tipo></item><item><clave>cantidad_devuelta</clave><titulo>Unidades</titulo><tipo>entero</tipo></item><item><clave>costo_total</clave><titulo>Costo total</titulo><tipo>dinero</tipo></item></columnas><datos><item><folio>DEV-2026-0087</folio><fecha_solicitud>2026-10-23</fecha_solicitud><estado>solicitada</estado><motivo>Cadena de frio rota</motivo><producto>Arroz blanco 1 kg</producto><lote>L-2026-301</lote><proveedor>Abarrotes Monterrey</proveedor><tienda>Tienda Valle Oriente</tienda><cantidad_devuelta>1</cantidad_devuelta><costo_total>0.0</costo_total></item><item><folio>DEV-2026-0086</folio><fecha_solicitud>2026-10-23</fecha_solicitud><estado>cerrada</estado><motivo>Caducidad vencida</motivo><producto>Yogurt natural 125 g</producto><lote>L-2026-061</lote><proveedor>Lacteos del Norte</proveedor><tienda>Tienda Valle Oriente</tienda><cantidad_devuelta>1</cantidad_devuelta><costo_total>192.1</costo_total></item><item><folio>DEV-2026-0085</folio><fecha_solicitud>2026-10-22</fecha_solicitud><estado>solicitada</estado><motivo>Calidad inferior</motivo><producto>Arroz blanco 1 kg</producto><lote>L-2026-301</lote><proveedor>Abarrotes Monterrey</proveedor><tienda>Tienda Valle Oriente</tienda><cantidad_devuelta>1</cantidad_devuelta><costo_total>0.0</costo_total></item></datos><paginacion><pagina>1</pagina><por_pagina>3</por_pagina><total>46</total><paginas>16</paginas></paginacion></reporte>
```

Verificaciones:

- ok: HTTP 200
- ok: es XML
- ok: raiz reporte

## P4-REP-12

**reporte de devoluciones filtrado por estado y fechas**

Objetivo: Los filtros acotan el reporte; se devuelven tal como se aplicaron.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/devoluciones?desde=2026-01-01&hasta=2026-11-22&estado=resuelta" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (38 ms, 1603 bytes):

```http
Content-Type: application/json
Content-Length: 1603
X-Correlation-ID: a23662e6e710440a
```

```json
{
  "reporte": "devoluciones",
  "titulo": "Reporte de devoluciones",
  "generado_en": "2026-11-22T18:34:49+00:00",
  "filtros": {
    "desde": "2026-01-01",
    "hasta": "2026-11-22",
    "estado": "resuelta"
  },
  "columnas": [
    {
      "clave": "folio",
      "titulo": "Folio",
      "tipo": "texto"
    },
    {
      "clave": "fecha_solicitud",
      "titulo": "Fecha",
      "tipo": "fecha"
    },
    {
      "clave": "estado",
      "titulo": "Estado",
      "tipo": "texto"
    },
    {
      "clave": "motivo",
      "titulo": "Motivo",
      "tipo": "texto"
    },
    {
      "clave": "producto",
      "titulo": "Producto",
      "tipo": "texto"
    },
    {
      "clave": "lote",
      "titulo": "Lote",
      "tipo": "texto"
    },
    {
      "clave": "proveedor",
      "titulo": "Proveedor",
      "tipo": "texto"
    },
    {
      "clave": "tienda",
      "titulo": "Tienda",
      "tipo": "texto"
    },
    {
      "clave": "cantidad_devuelta",
      "titulo": "Unidades",
      "tipo": "entero"
    },
    {
      "clave": "costo_total",
      "titulo": "Costo total",
      "tipo": "dinero"
    }
  ],
  "datos": [
    {
      "folio": "DEV-2026-0027",
      "fecha_solicitud": "2026-09-06",
      "estado": "resuelta",
      "motivo": "Etiqueta incorrecta",
      "producto": "Aceite vegetal 1 L",
      "lote": "L-2026-305",
      "proveedor": "Abarrotes Monterrey",
... (recortado: 36 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: filtro estado aplicado
- ok: todas las filas son resueltas

## P4-REP-13

**reporte de costos 200**

Objetivo: Costos de transporte, inspeccion y almacenamiento por devolucion; lo ve el Encargado de Reembolsos.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/costos?por_pagina=5" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_REEMBOLSOS"
```

Respuesta - **200 OK** (23 ms, 2110 bytes):

```http
Content-Type: application/json
Content-Length: 2110
X-Correlation-ID: 8372174e9731419b
```

```json
{
  "reporte": "costos",
  "titulo": "Costos por devolucion y etapa",
  "generado_en": "2026-11-22T18:34:49+00:00",
  "filtros": {},
  "columnas": [
    {
      "clave": "folio",
      "titulo": "Folio",
      "tipo": "texto"
    },
    {
      "clave": "fecha_solicitud",
      "titulo": "Fecha",
      "tipo": "fecha"
    },
    {
      "clave": "costo_transporte",
      "titulo": "Transporte",
      "tipo": "dinero"
    },
    {
      "clave": "costo_inspeccion",
      "titulo": "Inspeccion",
      "tipo": "dinero"
    },
    {
      "clave": "costo_almacenamiento",
      "titulo": "Almacenamiento",
      "tipo": "dinero"
    },
    {
      "clave": "costo_reacondicionamiento",
      "titulo": "Reacondicionamiento",
      "tipo": "dinero"
    },
    {
      "clave": "costo_destruccion",
      "titulo": "Destruccion",
      "tipo": "dinero"
    },
    {
      "clave": "monto_reembolsado",
      "titulo": "Reembolso",
      "tipo": "dinero"
    },
    {
      "clave": "costo_otros",
      "titulo": "Otros",
      "tipo": "dinero"
    },
    {
      "clave": "costo_total",
      "titulo": "Total",
      "tipo": "dinero"
    }
  ],
  "datos": [
    {
      "folio": "DEV-2026-0086",
      "fecha_solicitud": "2026-10-23",
      "costo_transporte": 0.0,
      "costo_inspeccion": 0.0,
      "costo_almacenamiento": 80.0,
      "costo_reacondicionamiento": 0.0,
      "costo_destruccion": 0.0,
      "monto_reembolsado": 112.1,
      "costo_otros": 0.0,
      "costo_total": 192.1
    },
... (recortado: 56 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: trae columnas de costo

## P4-REP-14

**reporte de tasas 200 por proveedor**

Objetivo: Tasa de devolucion = unidades devueltas entre vendidas (RF-26).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/tasas?por=proveedor" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (27 ms, 1016 bytes):

```http
Content-Type: application/json
Content-Length: 1016
X-Correlation-ID: 006167980a3d4193
```

```json
{
  "reporte": "tasas",
  "titulo": "Tasa de devolucion",
  "generado_en": "2026-11-22T18:34:49+00:00",
  "filtros": {
    "por": "proveedor"
  },
  "columnas": [
    {
      "clave": "etiqueta",
      "titulo": "Nombre",
      "tipo": "texto"
    },
    {
      "clave": "unidades_vendidas",
      "titulo": "Unidades vendidas",
      "tipo": "entero"
    },
    {
      "clave": "unidades_devueltas",
      "titulo": "Unidades devueltas",
      "tipo": "entero"
    },
    {
      "clave": "devoluciones",
      "titulo": "Casos",
      "tipo": "entero"
    },
    {
      "clave": "tasa_pct",
      "titulo": "Tasa (%)",
      "tipo": "decimal"
    }
  ],
  "datos": [
    {
      "id": 1,
      "etiqueta": "Lacteos del Norte",
      "unidades_vendidas": 89,
      "unidades_devueltas": 33,
      "devoluciones": 21,
      "tasa_pct": 37.08
    },
    {
      "id": 2,
      "etiqueta": "CampoVerde Agricola",
      "unidades_vendidas": 42,
      "unidades_devueltas": 11,
      "devoluciones": 11,
      "tasa_pct": 26.19
    },
    {
      "id": 4,
      "etiqueta": "Abarrotes Monterrey",
      "unidades_vendidas": 54,
      "unidades_devueltas": 11,
      "devoluciones": 11,
      "tasa_pct": 20.37
    },
    {
      "id": 3,
      "etiqueta": "Avicola Real",
      "unidades_vendidas": 16,
      "unidades_devueltas": 3,
      "devoluciones": 3,
      "tasa_pct": 18.75
    }
  ],
  "paginacion": {
    "pagina": 1,
... (recortado: 5 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: hay filas

## P4-REP-15

**reporte de tasas 200 por tienda**

Objetivo: La misma tasa agrupada por tienda.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/tasas?por=tienda" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (25 ms, 890 bytes):

```http
Content-Type: application/json
Content-Length: 890
X-Correlation-ID: 532d5c252b6746e5
```

```json
{
  "reporte": "tasas",
  "titulo": "Tasa de devolucion",
  "generado_en": "2026-11-22T18:34:49+00:00",
  "filtros": {
    "por": "tienda"
  },
  "columnas": [
    {
      "clave": "etiqueta",
      "titulo": "Nombre",
      "tipo": "texto"
    },
    {
      "clave": "unidades_vendidas",
      "titulo": "Unidades vendidas",
      "tipo": "entero"
    },
    {
      "clave": "unidades_devueltas",
      "titulo": "Unidades devueltas",
      "tipo": "entero"
    },
    {
      "clave": "devoluciones",
      "titulo": "Casos",
      "tipo": "entero"
    },
    {
      "clave": "tasa_pct",
      "titulo": "Tasa (%)",
      "tipo": "decimal"
    }
  ],
  "datos": [
    {
      "id": 2,
      "etiqueta": "Tienda Valle Oriente",
      "unidades_vendidas": 51,
      "unidades_devueltas": 19,
      "devoluciones": 16,
      "tasa_pct": 37.25
    },
    {
      "id": 1,
      "etiqueta": "Tienda Centro",
      "unidades_vendidas": 57,
      "unidades_devueltas": 19,
      "devoluciones": 10,
      "tasa_pct": 33.33
    },
    {
      "id": 3,
      "etiqueta": "Tienda Cumbres",
      "unidades_vendidas": 93,
      "unidades_devueltas": 20,
      "devoluciones": 20,
      "tasa_pct": 21.51
    }
  ],
  "paginacion": {
    "pagina": 1,
    "por_pagina": 20,
    "total": 3,
    "paginas": 1
  }
}
```

Verificaciones:

- ok: HTTP 200
- ok: hay filas

## P4-REP-16

**reporte pareto 200 por motivo**

Objetivo: Pareto de devoluciones por motivo: ordenado de mayor a menor con % acumulado.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/pareto?dimension=motivo&medida=frecuencia" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (30 ms, 1255 bytes):

```http
Content-Type: application/json
Content-Length: 1255
X-Correlation-ID: 268c4120a9404168
```

```json
{
  "reporte": "pareto",
  "titulo": "Pareto de devoluciones",
  "generado_en": "2026-11-22T18:34:49+00:00",
  "filtros": {
    "dimension": "motivo",
    "medida": "frecuencia"
  },
  "columnas": [
    {
      "clave": "etiqueta",
      "titulo": "Categoria",
      "tipo": "texto"
    },
    {
      "clave": "total",
      "titulo": "Total",
      "tipo": "decimal"
    },
    {
      "clave": "casos",
      "titulo": "Casos",
      "tipo": "entero"
    },
    {
      "clave": "porcentaje",
      "titulo": "% del total",
      "tipo": "decimal"
    },
    {
      "clave": "porcentaje_acumulado",
      "titulo": "% acumulado",
      "tipo": "decimal"
    }
  ],
  "datos": [
    {
      "etiqueta": "Cadena de frio rota",
      "total": 16.0,
      "casos": 16,
      "porcentaje": 34.78,
      "porcentaje_acumulado": 34.78
    },
    {
      "etiqueta": "Caducidad proxima",
      "total": 8.0,
      "casos": 8,
      "porcentaje": 17.39,
      "porcentaje_acumulado": 52.17
    },
    {
      "etiqueta": "Etiqueta incorrecta",
      "total": 7.0,
      "casos": 7,
      "porcentaje": 15.22,
      "porcentaje_acumulado": 67.39
    },
    {
      "etiqueta": "Caducidad vencida",
      "total": 5.0,
      "casos": 5,
      "porcentaje": 10.87,
      "porcentaje_acumulado": 78.26
    },
    {
      "etiqueta": "Calidad inferior",
      "total": 4.0,
      "casos": 4,
      "porcentaje": 8.7,
      "porcentaje_acumulado": 86.96
... (recortado: 23 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: hay filas

## P4-REP-17

**reporte pareto 200 por proveedor y costo**

Objetivo: El mismo Pareto con otra dimension y otra medida.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/pareto?dimension=proveedor&medida=costo" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (31 ms, 960 bytes):

```http
Content-Type: application/json
Content-Length: 960
X-Correlation-ID: dba90ccba27c4c4e
```

```json
{
  "reporte": "pareto",
  "titulo": "Pareto de devoluciones",
  "generado_en": "2026-11-22T18:34:49+00:00",
  "filtros": {
    "dimension": "proveedor",
    "medida": "costo"
  },
  "columnas": [
    {
      "clave": "etiqueta",
      "titulo": "Categoria",
      "tipo": "texto"
    },
    {
      "clave": "total",
      "titulo": "Total",
      "tipo": "decimal"
    },
    {
      "clave": "casos",
      "titulo": "Casos",
      "tipo": "entero"
    },
    {
      "clave": "porcentaje",
      "titulo": "% del total",
      "tipo": "decimal"
    },
    {
      "clave": "porcentaje_acumulado",
      "titulo": "% acumulado",
      "tipo": "decimal"
    }
  ],
  "datos": [
    {
      "etiqueta": "Lacteos del Norte",
      "total": 2318.03,
      "casos": 21,
      "porcentaje": 49.47,
      "porcentaje_acumulado": 49.47
    },
    {
      "etiqueta": "Abarrotes Monterrey",
      "total": 1408.79,
      "casos": 11,
      "porcentaje": 30.07,
      "porcentaje_acumulado": 79.54
    },
    {
      "etiqueta": "CampoVerde Agricola",
      "total": 612.21,
      "casos": 11,
      "porcentaje": 13.07,
      "porcentaje_acumulado": 92.61
    },
    {
      "etiqueta": "Avicola Real",
      "total": 346.38,
      "casos": 3,
      "porcentaje": 7.39,
      "porcentaje_acumulado": 100.0
    }
  ],
  "paginacion": {
    "pagina": 1,
    "por_pagina": 20,
    "total": 4,
    "paginas": 1
... (recortado: 2 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: hay filas

## P4-REP-18

**reporte de tendencia 200**

Objetivo: Serie mensual de las ultimas 12 meses.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/tendencia?medida=devoluciones&meses=12" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (27 ms, 1611 bytes):

```http
Content-Type: application/json
Content-Length: 1611
X-Correlation-ID: 814b019f475740a4
```

```json
{
  "reporte": "tendencia",
  "titulo": "Tendencia mensual",
  "generado_en": "2026-11-22T18:34:49+00:00",
  "filtros": {
    "medida": "devoluciones",
    "meses": 12
  },
  "columnas": [
    {
      "clave": "mes",
      "titulo": "Mes",
      "tipo": "texto"
    },
    {
      "clave": "unidades_vendidas",
      "titulo": "Unidades vendidas",
      "tipo": "entero"
    },
    {
      "clave": "unidades_devueltas",
      "titulo": "Unidades devueltas",
      "tipo": "entero"
    },
    {
      "clave": "valor",
      "titulo": "Valor",
      "tipo": "decimal"
    },
    {
      "clave": "estado",
      "titulo": "Estado del dato",
      "tipo": "texto"
    }
  ],
  "datos": [
    {
      "mes": "2025-11",
      "unidades_vendidas": 0,
      "unidades_devueltas": 0,
      "valor": 0.0,
      "estado": "ok"
    },
    {
      "mes": "2025-12",
      "unidades_vendidas": 0,
      "unidades_devueltas": 0,
      "valor": 0.0,
      "estado": "ok"
    },
    {
      "mes": "2026-01",
      "unidades_vendidas": 0,
      "unidades_devueltas": 0,
      "valor": 0.0,
      "estado": "ok"
    },
    {
      "mes": "2026-02",
      "unidades_vendidas": 0,
      "unidades_devueltas": 0,
      "valor": 0.0,
      "estado": "ok"
    },
    {
      "mes": "2026-03",
      "unidades_vendidas": 0,
      "unidades_devueltas": 0,
      "valor": 0.0,
      "estado": "ok"
... (recortado: 58 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: doce meses

## P4-REP-19

**reporte 404 inexistente**

Objetivo: Un reporte que no existe responde 404.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/inventado" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **404 NOT FOUND** (9 ms, 135 bytes):

```http
Content-Type: application/json
Content-Length: 135
X-Correlation-ID: 75d2e8c8db434f1e
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe ese reporte.",
    "detalles": null,
    "correlation_id": "75d2e8c8db434f1e"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-REP-20

**reporte 400 formato invalido**

Objetivo: El formato debe ser uno de los publicados.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/costos?formato=docx" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (8 ms, 149 bytes):

```http
Content-Type: application/json
Content-Length: 149
X-Correlation-ID: 556fb706de1349a3
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "formato debe ser: json, csv, xlsx, pdf.",
    "detalles": null,
    "correlation_id": "556fb706de1349a3"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-REP-21

**reporte 400 parametro desconocido**

Objetivo: Un parametro que ese reporte no admite se rechaza, no se ignora en silencio.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/costos?proveedor_id=1" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (8 ms, 197 bytes):

```http
Content-Type: application/json
Content-Length: 197
X-Correlation-ID: b64192cb72634796
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Parametros desconocidos.",
    "detalles": [
      {
        "campo": "proveedor_id",
        "problema": "no existe para este reporte"
      }
    ],
    "correlation_id": "b64192cb72634796"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-REP-22

**reporte 400 fecha invalida**

Objetivo: Las fechas son AAAA-MM-DD.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/devoluciones?desde=ayer" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (8 ms, 146 bytes):

```http
Content-Type: application/json
Content-Length: 146
X-Correlation-ID: 55c017b4b4c14b43
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "desde debe tener formato AAAA-MM-DD.",
    "detalles": null,
    "correlation_id": "55c017b4b4c14b43"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-REP-23

**reporte 400 hasta antes de desde**

Objetivo: Un periodo al reves se rechaza.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/devoluciones?desde=2026-06-01&hasta=2026-01-01" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (8 ms, 145 bytes):

```http
Content-Type: application/json
Content-Length: 145
X-Correlation-ID: 72b69d2090f6421f
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "hasta no puede ser menor que desde.",
    "detalles": null,
    "correlation_id": "72b69d2090f6421f"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-REP-24

**reporte 400 estado desconocido**

Objetivo: Un estado fuera del catalogo se rechaza.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/devoluciones?estado=dormida" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (8 ms, 241 bytes):

```http
Content-Type: application/json
Content-Length: 241
X-Correlation-ID: 07ed9e3efdf34254
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "estado debe ser uno de: solicitada, en_revision, autorizada, rechazada, en_recoleccion, recibida, en_inspeccion, resuelta, cerrada.",
    "detalles": null,
    "correlation_id": "07ed9e3efdf34254"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-REP-25

**tendencia 400 meses fuera de rango**

Objetivo: La serie admite de 6 a 36 meses.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/tendencia?meses=2" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (7 ms, 148 bytes):

```http
Content-Type: application/json
Content-Length: 148
X-Correlation-ID: 737927e64c854efc
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "meses debe ser un entero entre 6 y 36.",
    "detalles": null,
    "correlation_id": "737927e64c854efc"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-REP-26

**tendencia 400 dimension sin referencia**

Objetivo: La dimension y su referencia_id van juntas.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/tendencia?dimension=proveedor" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (8 ms, 154 bytes):

```http
Content-Type: application/json
Content-Length: 154
X-Correlation-ID: 5e7dba99e2c54575
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "dimension y referencia_id se indican juntas.",
    "detalles": null,
    "correlation_id": "5e7dba99e2c54575"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-REP-27

**tendencia 404 objeto inexistente**

Objetivo: No se grafica un objeto que no existe.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/tendencia?dimension=proveedor&referencia_id=999999" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **404 NOT FOUND** (16 ms, 144 bytes):

```http
Content-Type: application/json
Content-Length: 144
X-Correlation-ID: a1748f58509d4e5f
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe proveedor con ese id.",
    "detalles": null,
    "correlation_id": "a1748f58509d4e5f"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-REP-28

**descarga CSV de devoluciones**

Objetivo: Archivo CSV con encabezados de descarga y sin cache, porque son datos de negocio (RF-28).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/devoluciones?formato=csv" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (45 ms, 6007 bytes):

```http
Content-Type: text/csv; charset=utf-8
Content-Length: 6007
X-Correlation-ID: b7829d4db0ed442a
Content-Disposition: attachment; filename="reporte_devoluciones_20261122.csv"
Cache-Control: no-store
X-Content-Type-Options: nosniff
```

```text
﻿Folio,Fecha,Estado,Motivo,Producto,Lote,Proveedor,Tienda,Unidades,Costo total
DEV-2026-0087,2026-10-23,solicitada,Cadena de frio rota,Arroz blanco 1 kg,L-2026-301,Abarrotes Monterrey,Tienda Valle Oriente,1,0
DEV-2026-0086,2026-10-23,cerrada,Caducidad vencida,Yogurt natural 125 g,L-2026-061,Lacteos del Norte,Tienda Valle Oriente,1,192.10
DEV-2026-0085,2026-10-22,solicitada,Calidad inferior,Arroz blanco 1 kg,L-2026-301,Abarrotes Monterrey,Tienda Valle Oriente,1,0
DEV-2026-0084,2026-10-22,en_recoleccion,Caducidad vencida,Tomate saladette 1 kg,L-2026-118,CampoVerde Agricola,Tienda Centro,1,0
DEV-2026-0081,2026-10-22,cerrada,Producto danado,Pechuga de pollo 1 kg,L-2026-201,Avicola Real,Tienda Cumbres,1,196.50
DEV-2026-0037,2026-10-21,en_recoleccion,Cadena de frio rota,Queso panela 400 g,L-2026-070,Lacteos del Norte,Tienda Valle Oriente,1,0
DEV-2026-0036,2026-10-21,autorizada,Cadena de frio rota,Queso panela 400 g,L-2026-070,Lacteos del Norte,Tienda Valle Oriente,1,0
DEV-2026-0108,2026-10-06,autorizada,Cadena de frio rota,Leche entera 1 L,L-2026-PROB-01,Lacteos del Norte,Tienda Valle Oriente,4,0
DEV-2026-0107,2026-10-05,en_inspeccion,Producto danado,Leche entera 1 L,L-2026-PROB-01,Lacteos del Norte,Tienda Centro,4,140.00
DEV-2026-0106,2026-10-04,cerrada,Cadena de frio rota,Leche entera 1 L,L-2026-PROB-01,Lacteos del Norte,Tienda Centro,4,140.00
DEV-2026-0105,2026-10-03,cerrada,Cadena de frio rota,Leche entera 1 L,L-2026-PROB-01,Lacteos del Norte,Tienda Centro,4,140.00
DEV-2026-0035,2026-09-07,en_inspeccion,Cadena de frio rota,Yogurt natural 125 g,L-2026-061,Lacteos del Norte,Tienda Valle Oriente,1,112.10
DEV-2026-0034,2026-09-07,cerrada,Caducidad proxima,Tomate saladette 1 kg,L-2026-118,CampoVerde Agricola,Tienda Valle Oriente,1,69.53
DEV-2026-0033,2026-09-06,cerrada,Cadena de frio rota,Queso panela 400 g,L-2026-070,Lacteos del Norte,Tienda Valle Oriente,1,236.45
DEV-2026-0032,2026-09-06,cerrada,Cadena de frio rota,Arroz blanco 1 kg,L-2026-301,Abarrotes Monterrey,Tienda Valle Oriente,1,261.07
DEV-2026-0031,2026-09-06,cerrada,Caducidad proxima,Frijol envasado 900 g,L-2026-125,CampoVerde Agricola,Tienda Cumbres,1,265.30
DEV-2026-0030,2026-09-06,cerrada,Calidad inferior,Galletas surtidas 600 g,L-2026-312,Abarrotes Monterrey,Tienda Cumbres,1,381.03
DEV-2026-0029,2026-09-06,cerrada,Cadena de frio rota,Leche entera 1 L,L-2026-045,Lacteos del Norte,Tienda Cumbres,1,377.80
DEV-2026-0028,2026-09-06,cerrada,Caducidad vencida,Leche entera 1 L,L-2026-045,Lacteos del Norte,Tienda Cumbres,1,235.30
DEV-2026-0027,2026-09-06,resuelta,Etiqueta incorrecta,Aceite vegetal 1 L,L-2026-305,Abarrotes Monterrey,Tienda Cumbres,1,166.15
DEV-2026-0026,2026-09-06,resuelta,Caducidad proxima,Queso panela 400 g,L-2026-070,Lacteos del Norte,Tienda Cumbres,1,178.35
DEV-2026-0025,2026-09-06,resuelta,Cadena de frio rota,Leche entera 1 L,L-2026-045,Lacteos del Norte,Tienda Cumbres,1,137.89
DEV-2026-0024,2026-09-06,en_inspeccion,Etiqueta incorrecta,Leche entera 1 L,L-2026-052,Lacteos del Norte,Tienda Cumbres,1,169.38
DEV-2026-0023,2026-09-06,en_inspeccion,Caducidad proxima,Galletas surtidas 600 g,L-2026-312,Abarrotes Monterrey,Tienda Valle Oriente,1,182.90
DEV-2026-0022,2026-09-06,en_inspeccion,Caducidad proxima,Arroz blanco 1 kg,L-2026-301,Abarrotes Monterrey,Tienda Cumbres,1,210.19
DEV-2026-0021,2026-09-06,recibida,Caducidad vencida,Galletas surtidas 600 g,L-2026-312,Abarrotes Monterrey,Tienda Cumbres,1,145.90
DEV-2026-0020,2026-09-06,recibida,Etiqueta incorrecta,Aceite vegetal 1 L,L-2026-305,Abarrotes Monterrey,Tienda Centro,1,61.55
DEV-2026-0019,2026-09-06,recibida,Etiqueta incorrecta,Pechuga de pollo 1 kg,L-2026-201,Avicola Real,Tienda Valle Oriente,1,149.88
DEV-2026-0018,2026-09-06,en_recoleccion,Producto danado,Queso panela 400 g,L-2026-070,Lacteos del Norte,Tienda Cumbres,1,152.50
DEV-2026-0017,2026-09-06,en_recoleccion,Etiqueta incorrecta,Tomate saladette 1 kg,L-2026-118,CampoVerde Agricola,Tienda Valle Oriente,1,122.73
DEV-2026-0016,2026-09-06,en_recoleccion,Cadena de frio rota,Frijol envasado 900 g,L-2026-125,CampoVerde Agricola,Tienda Cumbres,1,154.65
DEV-2026-0015,2026-09-06,en_recoleccion,Caducidad proxima,Leche entera 1 L,L-2026-045,Lacteos del Norte,Tienda Valle Oriente,1,106.16
DEV-2026-0014,2026-09-06,rechazada,Calidad inferior,Leche entera 1 L,L-2026-052,Lacteos del Norte,Tienda Valle Oriente,1,0
DEV-2026-0013,2026-09-06,rechazada,Cadena de frio rota,Tomate saladette 1 kg,L-2026-118,CampoVerde Agricola,Tienda Centro,1,0
DEV-2026-0012,2026-09-06,autorizada,Cadena de frio rota,Arroz blanco 1 kg,L-2026-301,Abarrotes Monterrey,Tienda Cumbres,1,0
DEV-2026-0011,2026-09-06,autorizada,Etiqueta incorrecta,Lechuga romana,L-2026-112,CampoVerde Agricola,Tienda Cumbres,1,0
DEV-2026-0010,2026-09-06,autorizada,Calidad inferior,Frijol envasado 900 g,L-2026-125,CampoVerde Agricola,Tienda Cumbres,1,0
DEV-2026-0009,2026-09-06,autorizada,Producto danado,Pechuga de pollo 1 kg,L-2026-201,Avicola Real,Tienda Centro,1,0
DEV-2026-0008,2026-09-06,en_revision,Caducidad proxima,Galletas surtidas 600 g,L-2026-312,Abarrotes Monterrey,Tienda Centro,1,0
DEV-2026-0007,2026-09-06,en_revision,Caducidad vencida,Leche entera 1 L,L-2026-052,Lacteos del Norte,Tienda Centro,1,0
DEV-2026-0006,2026-09-06,en_revision,Error en el pedido,Leche entera 1 L,L-2026-045,Lacteos del Norte,Tienda Centro,1,0
DEV-2026-0005,2026-09-06,solicitada,Etiqueta incorrecta,Lechuga romana,L-2026-112,CampoVerde Agricola,Tienda Cumbres,1,0
DEV-2026-0004,2026-09-06,solicitada,Cadena de frio rota,Queso panela 400 g,L-2026-070,Lacteos del Norte,Tienda Cumbres,1,0
DEV-2026-0003,2026-09-06,solicitada,Error en el pedido,Tomate saladette 1 kg,L-2026-118,CampoVerde Agricola,Tienda Cumbres,1,0
DEV-2026-0002,2026-09-06,solicitada,Cadena de frio rota,Queso panela 400 g,L-2026-070,Lacteos del Norte,Tienda Cumbres,1,0
DEV-2026-0001,2026-09-06,solicitada,Caducidad proxima,Tomate saladette 1 kg,L-2026-118,CampoVerde Agricola,Tienda Valle Oriente,1,0

```

Verificaciones:

- ok: HTTP 200
- ok: tipo text/csv
- ok: se descarga como adjunto
- ok: no se guarda en cache
- ok: primera linea con encabezados

Efecto en PostgreSQL - la descarga queda en la bitacora con reporte, formato y filas; sin los datos:

```sql
SELECT accion, detalle FROM bitacora WHERE accion = 'exportar_reporte' ORDER BY id DESC LIMIT 1
```

```text
accion | detalle
exportar_reporte | devoluciones csv filas=46 filtros=sin filtros
```

## P4-REP-29

**descarga Excel de devoluciones**

Objetivo: Libro de Excel (.xlsx) escrito con la biblioteca estandar.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/devoluciones?formato=xlsx" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (47 ms, 5652 bytes):

```http
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Length: 5652
X-Correlation-ID: 97d80c8c16104cb7
Content-Disposition: attachment; filename="reporte_devoluciones_20261122.xlsx"
Cache-Control: no-store
X-Content-Type-Options: nosniff
```

```text
(contenido binario de 5652 bytes; empieza con b'PK\x03\x04\x14\x00\x00\x00')
```

Verificaciones:

- ok: HTTP 200
- ok: tipo de hoja de calculo
- ok: es un zip (PK)
- ok: adjunto .xlsx

## P4-REP-30

**descarga PDF de devoluciones**

Objetivo: Documento PDF listo para imprimir.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/devoluciones?formato=pdf" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (43 ms, 10927 bytes):

```http
Content-Type: application/pdf
Content-Length: 10927
X-Correlation-ID: 6af47b4ad8b34ea8
Content-Disposition: attachment; filename="reporte_devoluciones_20261122.pdf"
Cache-Control: no-store
X-Content-Type-Options: nosniff
```

```text
(contenido binario de 10927 bytes; empieza con b'%PDF-1.4')
```

Verificaciones:

- ok: HTTP 200
- ok: tipo application/pdf
- ok: empieza con %PDF
- ok: termina con %%EOF

## P4-REP-31

**descarga CSV de costos**

Objetivo: El Encargado de Reembolsos descarga los costos.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/costos?formato=csv" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_REEMBOLSOS"
```

Respuesta - **200 OK** (27 ms, 1542 bytes):

```http
Content-Type: text/csv; charset=utf-8
Content-Length: 1542
X-Correlation-ID: c1529276eeb944a1
Content-Disposition: attachment; filename="reporte_costos_20261122.csv"
Cache-Control: no-store
X-Content-Type-Options: nosniff
```

```text
﻿Folio,Fecha,Transporte,Inspeccion,Almacenamiento,Reacondicionamiento,Destruccion,Reembolso,Otros,Total
DEV-2026-0086,2026-10-23,0,0,80.00,0,0,112.10,0,192.10
DEV-2026-0081,2026-10-22,150.50,0,45.00,0,0,1.00,0,196.50
DEV-2026-0107,2026-10-05,95.00,45.00,0,0,0,0,0,140.00
DEV-2026-0106,2026-10-04,95.00,45.00,0,0,0,0,0,140.00
DEV-2026-0105,2026-10-03,95.00,45.00,0,0,0,0,0,140.00
DEV-2026-0035,2026-09-07,0,0,0,0,0,112.10,0,112.10
DEV-2026-0034,2026-09-07,0,0,1.00,0,0,68.53,0,69.53
DEV-2026-0033,2026-09-06,0,0,0,0,0,236.45,0,236.45
DEV-2026-0032,2026-09-06,150.88,52.90,0,0,0,57.29,0,261.07
DEV-2026-0031,2026-09-06,140.29,43.71,0,0,0,81.30,0,265.30
DEV-2026-0030,2026-09-06,178.41,86.00,0,0,0,116.62,0,381.03
DEV-2026-0029,2026-09-06,137.99,78.01,0,0,0,161.80,0,377.80
DEV-2026-0028,2026-09-06,131.18,78.20,0,0,0,25.92,0,235.30
DEV-2026-0027,2026-09-06,87.80,78.35,0,0,0,0,0,166.15
DEV-2026-0026,2026-09-06,125.85,52.50,0,0,0,0,0,178.35
DEV-2026-0025,2026-09-06,62.46,75.43,0,0,0,0,0,137.89
DEV-2026-0024,2026-09-06,116.07,53.31,0,0,0,0,0,169.38
DEV-2026-0023,2026-09-06,113.81,69.09,0,0,0,0,0,182.90
DEV-2026-0022,2026-09-06,125.54,84.65,0,0,0,0,0,210.19
DEV-2026-0021,2026-09-06,145.90,0,0,0,0,0,0,145.90
DEV-2026-0020,2026-09-06,61.55,0,0,0,0,0,0,61.55
DEV-2026-0019,2026-09-06,149.88,0,0,0,0,0,0,149.88
DEV-2026-0018,2026-09-06,152.50,0,0,0,0,0,0,152.50
DEV-2026-0017,2026-09-06,122.73,0,0,0,0,0,0,122.73
DEV-2026-0016,2026-09-06,154.65,0,0,0,0,0,0,154.65
DEV-2026-0015,2026-09-06,106.16,0,0,0,0,0,0,106.16

```

Verificaciones:

- ok: HTTP 200
- ok: tipo text/csv

## P4-REP-32

**descarga Excel de tasas**

Objetivo: Tasas por lote en Excel.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/tasas?por=lote&formato=xlsx" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (30 ms, 3370 bytes):

```http
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Length: 3370
X-Correlation-ID: afd9fbed888f4981
Content-Disposition: attachment; filename="reporte_tasas_20261122.xlsx"
Cache-Control: no-store
X-Content-Type-Options: nosniff
```

```text
(contenido binario de 3370 bytes; empieza con b'PK\x03\x04\x14\x00\x00\x00')
```

Verificaciones:

- ok: HTTP 200
- ok: es un zip (PK)

## P4-REP-33

**descarga PDF de Pareto**

Objetivo: Pareto por transportista en PDF.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/pareto?dimension=transportista&medida=cantidad&formato=pdf" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR"
```

Respuesta - **200 OK** (35 ms, 1754 bytes):

```http
Content-Type: application/pdf
Content-Length: 1754
X-Correlation-ID: 07f677560d184c14
Content-Disposition: attachment; filename="reporte_pareto_20261122.pdf"
Cache-Control: no-store
X-Content-Type-Options: nosniff
```

```text
(contenido binario de 1754 bytes; empieza con b'%PDF-1.4')
```

Verificaciones:

- ok: HTTP 200
- ok: empieza con %PDF

## P4-REP-34

**descarga CSV de la tendencia de un proveedor**

Objetivo: Serie mensual de un proveedor en CSV.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/tendencia?dimension=proveedor&referencia_id=1&meses=12&formato=csv" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (29 ms, 476 bytes):

```http
Content-Type: text/csv; charset=utf-8
Content-Length: 476
X-Correlation-ID: 6faf1a61ddd34451
Content-Disposition: attachment; filename="reporte_tendencia_20261122.csv"
Cache-Control: no-store
X-Content-Type-Options: nosniff
```

```text
﻿Mes,Unidades vendidas,Unidades devueltas,Valor,Estado del dato
2025-10,0,0,,muestra_insuficiente
2025-11,0,0,,muestra_insuficiente
2025-12,0,0,,muestra_insuficiente
2026-01,0,0,,muestra_insuficiente
2026-02,0,0,,muestra_insuficiente
2026-03,0,0,,muestra_insuficiente
2026-04,0,0,,muestra_insuficiente
2026-05,0,0,,muestra_insuficiente
2026-06,0,0,,muestra_insuficiente
2026-07,0,0,,muestra_insuficiente
2026-08,47,17,36.17,ok
2026-09,0,0,,muestra_insuficiente

```

Verificaciones:

- ok: HTTP 200
- ok: tipo text/csv

## P4-REP-35

**descarga 429 tras 20 en un minuto**

Objetivo: Un archivo cuesta mas que una pagina: tras 20 descargas en un minuto el usuario recibe 429 con Retry-After.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/costos?formato=csv" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

Respuesta - **429 TOO MANY REQUESTS** (7 ms, 179 bytes):

```http
Content-Type: application/json
Content-Length: 179
X-Correlation-ID: 70595a218fb9492d
Retry-After: 20
```

```json
{
  "error": {
    "codigo": 429,
    "tipo": "demasiadas_peticiones",
    "mensaje": "Limite de 20 peticiones en 60 s. Intenta de nuevo en 20 s.",
    "detalles": null,
    "correlation_id": "70595a218fb9492d"
  }
}
```

Verificaciones:

- ok: HTTP 429
- ok: tipo demasiadas_peticiones
- ok: indica cuanto esperar

## P4-REP-36

**JSON no cuenta para el limite de descargas**

Objetivo: Solo los archivos tienen cuota; consultar en JSON sigue funcionando.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/reportes/costos?por_pagina=1" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN"
```

Respuesta - **200 OK** (21 ms, 1110 bytes):

```http
Content-Type: application/json
Content-Length: 1110
X-Correlation-ID: a77b3bb98e06409d
```

```json
{
  "reporte": "costos",
  "titulo": "Costos por devolucion y etapa",
  "generado_en": "2026-11-22T18:34:50+00:00",
  "filtros": {},
  "columnas": [
    {
      "clave": "folio",
      "titulo": "Folio",
      "tipo": "texto"
    },
    {
      "clave": "fecha_solicitud",
      "titulo": "Fecha",
      "tipo": "fecha"
    },
    {
      "clave": "costo_transporte",
      "titulo": "Transporte",
      "tipo": "dinero"
    },
    {
      "clave": "costo_inspeccion",
      "titulo": "Inspeccion",
      "tipo": "dinero"
    },
    {
      "clave": "costo_almacenamiento",
      "titulo": "Almacenamiento",
      "tipo": "dinero"
    },
    {
      "clave": "costo_reacondicionamiento",
      "titulo": "Reacondicionamiento",
      "tipo": "dinero"
    },
    {
      "clave": "costo_destruccion",
      "titulo": "Destruccion",
      "tipo": "dinero"
    },
    {
      "clave": "monto_reembolsado",
      "titulo": "Reembolso",
      "tipo": "dinero"
    },
    {
      "clave": "costo_otros",
      "titulo": "Otros",
      "tipo": "dinero"
    },
    {
      "clave": "costo_total",
      "titulo": "Total",
      "tipo": "dinero"
    }
  ],
  "datos": [
    {
      "folio": "DEV-2026-0086",
      "fecha_solicitud": "2026-10-23",
      "costo_transporte": 0.0,
      "costo_inspeccion": 0.0,
      "costo_almacenamiento": 80.0,
      "costo_reacondicionamiento": 0.0,
      "costo_destruccion": 0.0,
      "monto_reembolsado": 112.1,
      "costo_otros": 0.0,
      "costo_total": 192.1
    }
... (recortado: 8 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: hay filas o vacio sin error

## P4-REP-37

**grafica Pareto 200**

Objetivo: Opciones listas para `Highcharts.chart(contenedor, opciones)`: columnas y linea de % acumulado.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/graficas/pareto?dimension=motivo" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (29 ms, 714 bytes):

```http
Content-Type: application/json
Content-Length: 714
X-Correlation-ID: e223c95a85ed4ecc
```

```json
{
  "opciones": {
    "chart": {
      "zoomType": "xy"
    },
    "title": {
      "text": "Pareto por motivo"
    },
    "credits": {
      "enabled": false
    },
    "xAxis": {
      "categories": [
        "Cadena de frio rota",
        "Caducidad proxima",
        "Etiqueta incorrecta",
        "Caducidad vencida",
        "Calidad inferior",
        "Producto danado",
        "Error en el pedido"
      ],
      "crosshair": true
    },
    "yAxis": [
      {
        "title": {
          "text": "Devoluciones"
        }
      },
      {
        "title": {
          "text": "% acumulado"
        },
        "min": 0,
        "max": 100,
        "opposite": true
      }
    ],
    "tooltip": {
      "shared": true
    },
    "series": [
      {
        "type": "column",
        "name": "Total",
        "data": [
          16.0,
          8.0,
          7.0,
          5.0,
          4.0,
          4.0,
          2.0
        ]
      },
      {
        "type": "line",
        "name": "% acumulado",
        "yAxis": 1,
        "data": [
          34.78,
          52.17,
          67.39,
          78.26,
          86.96,
          95.65,
          100.0
        ],
        "tooltip": {
          "valueSuffix": " %"
... (recortado: 6 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: trae series
- ok: columna y linea

## P4-REP-38

**grafica de tasas 200**

Objetivo: Barras con la tasa por proveedor.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/graficas/tasas?por=proveedor" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (25 ms, 476 bytes):

```http
Content-Type: application/json
Content-Length: 476
X-Correlation-ID: 4642dcd5233642d8
```

```json
{
  "opciones": {
    "chart": {
      "type": "bar"
    },
    "title": {
      "text": "Tasa de devolucion por proveedor"
    },
    "credits": {
      "enabled": false
    },
    "xAxis": {
      "categories": [
        "Lacteos del Norte",
        "CampoVerde Agricola",
        "Abarrotes Monterrey",
        "Avicola Real"
      ]
    },
    "yAxis": {
      "min": 0,
      "title": {
        "text": "Tasa de devolucion (%)"
      }
    },
    "tooltip": {
      "valueSuffix": " %"
    },
    "legend": {
      "enabled": false
    },
    "series": [
      {
        "name": "Tasa",
        "data": [
          37.08,
          26.19,
          20.37,
          18.75
        ]
      }
    ]
  },
  "nota": "Pasa `opciones` tal cual a Highcharts.chart(contenedor, opciones)."
}
```

Verificaciones:

- ok: HTTP 200
- ok: grafica de barras

## P4-REP-39

**grafica de tendencia 200**

Objetivo: Serie observada, linea de tendencia y pronostico con banda.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/graficas/tendencia?medida=tasa&meses=12&horizonte=3" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (26 ms, 536 bytes):

```http
Content-Type: application/json
Content-Length: 536
X-Correlation-ID: 7a0994f558544120
```

```json
{
  "opciones": {
    "chart": {
      "type": "line"
    },
    "title": {
      "text": "Tasa de devolucion (%): todos"
    },
    "credits": {
      "enabled": false
    },
    "xAxis": {
      "categories": [
        "2025-10",
        "2025-11",
        "2025-12",
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
        "2026-05",
        "2026-06",
        "2026-07",
        "2026-08",
        "2026-09"
      ]
    },
    "yAxis": {
      "min": 0,
      "title": {
        "text": "Tasa de devolucion (%)"
      }
    },
    "tooltip": {
      "shared": true
    },
    "series": [
      {
        "name": "Observado",
        "data": [
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          null,
          34.15,
          null
        ],
        "zIndex": 3
      }
    ]
  },
  "nota": "Pasa `opciones` tal cual a Highcharts.chart(contenedor, opciones)."
}
```

Verificaciones:

- ok: HTTP 200
- ok: trae la serie observada

## P4-REP-40

**grafica 406 en XML**

Objetivo: Las opciones de Highcharts solo se entregan en JSON.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/graficas/pareto" \
  -H "Accept: application/xml" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **406 NOT ACCEPTABLE** (9 ms, 228 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 228
X-Correlation-ID: 398dc62cdba44eda
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<error><codigo>406</codigo><tipo>solo_json</tipo><mensaje>Las opciones de Highcharts solo se entregan en JSON.</mensaje><detalles /><correlation_id>398dc62cdba44eda</correlation_id></error>
```

Verificaciones:

- ok: HTTP 406
- ok: tipo solo_json

## P4-REP-41

**grafica 404 inexistente**

Objetivo: Solo hay pareto, tendencia y tasas.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/graficas/dona" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **404 NOT FOUND** (8 ms, 160 bytes):

```http
Content-Type: application/json
Content-Length: 160
X-Correlation-ID: afeeb24da9a04dc8
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Graficas disponibles: pareto, tendencia, tasas.",
    "detalles": null,
    "correlation_id": "afeeb24da9a04dc8"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-REP-42

**grafica 400 horizonte fuera de rango**

Objetivo: El horizonte del pronostico tiene un maximo.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/graficas/tendencia?horizonte=0" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (24 ms, 151 bytes):

```http
Content-Type: application/json
Content-Length: 151
X-Correlation-ID: 217aec6bedf34e36
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "horizonte debe ser un entero entre 1 y 6.",
    "detalles": null,
    "correlation_id": "217aec6bedf34e36"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-REP-43

**tendencias 200**

Objetivo: Regresion lineal sobre los meses con datos: pendiente, R2 y si es distinguible del ruido (RN-09). Con pocos datos dice sin_datos y por que.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/analitica/tendencias?medida=devoluciones&meses=12" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (25 ms, 1615 bytes):

```http
Content-Type: application/json
Content-Length: 1615
X-Correlation-ID: 8ff588b70b8f4a6f
```

```json
{
  "medida": "devoluciones",
  "dimension": null,
  "referencia_id": null,
  "objeto": "todos",
  "meses": [
    "2025-11",
    "2025-12",
    "2026-01",
    "2026-02",
    "2026-03",
    "2026-04",
    "2026-05",
    "2026-06",
    "2026-07",
    "2026-08",
    "2026-09",
    "2026-10"
  ],
  "serie": [
    {
      "mes": "2025-11",
      "unidades_vendidas": 0,
      "unidades_devueltas": 0,
      "valor": 0.0,
      "estado": "ok"
    },
    {
      "mes": "2025-12",
      "unidades_vendidas": 0,
      "unidades_devueltas": 0,
      "valor": 0.0,
      "estado": "ok"
    },
    {
      "mes": "2026-01",
      "unidades_vendidas": 0,
      "unidades_devueltas": 0,
      "valor": 0.0,
      "estado": "ok"
    },
    {
      "mes": "2026-02",
      "unidades_vendidas": 0,
      "unidades_devueltas": 0,
      "valor": 0.0,
      "estado": "ok"
    },
    {
      "mes": "2026-03",
      "unidades_vendidas": 0,
      "unidades_devueltas": 0,
      "valor": 0.0,
      "estado": "ok"
    },
    {
      "mes": "2026-04",
      "unidades_vendidas": 0,
      "unidades_devueltas": 0,
      "valor": 0.0,
      "estado": "ok"
    },
    {
      "mes": "2026-05",
      "unidades_vendidas": 0,
      "unidades_devueltas": 0,
      "valor": 0.0,
      "estado": "ok"
    },
    {
... (recortado: 46 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: estado ok o sin_datos explicado
- ok: trae la serie

## P4-REP-44

**tendencias 200 XML**

Objetivo: La misma tendencia en XML.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/analitica/tendencias?meses=6" \
  -H "Accept: application/xml" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (26 ms, 1478 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 1478
X-Correlation-ID: b1ff1bae362a4526
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<tendencias><medida>tasa</medida><dimension /><referencia_id /><objeto>todos</objeto><meses><item>2026-04</item><item>2026-05</item><item>2026-06</item><item>2026-07</item><item>2026-08</item><item>2026-09</item></meses><serie><item><mes>2026-04</mes><unidades_vendidas>0</unidades_vendidas><unidades_devueltas>0</unidades_devueltas><valor /><estado>muestra_insuficiente</estado></item><item><mes>2026-05</mes><unidades_vendidas>0</unidades_vendidas><unidades_devueltas>0</unidades_devueltas><valor /><estado>muestra_insuficiente</estado></item><item><mes>2026-06</mes><unidades_vendidas>0</unidades_vendidas><unidades_devueltas>0</unidades_devueltas><valor /><estado>muestra_insuficiente</estado></item><item><mes>2026-07</mes><unidades_vendidas>0</unidades_vendidas><unidades_devueltas>0</unidades_devueltas><valor /><estado>muestra_insuficiente</estado></item><item><mes>2026-08</mes><unidades_vendidas>123</unidades_vendidas><unidades_devueltas>42</unidades_devueltas><valor>34.15</valor><estado>ok</estado></item><item><mes>2026-09</mes><unidades_vendidas>0</unidades_vendidas><unidades_devueltas>0</unidades_devueltas><valor /><estado>muestra_insuficiente</estado></item></serie><tendencia><estado>sin_datos</estado><motivo>Se requieren al menos 6 meses con datos suficientes.</motivo></tendencia><nota>Los meses con menos de 20 unidades vendidas y los que aun pueden recibir devoluciones no se usan para la tasa.</nota></tendencias>
```

Verificaciones:

- ok: HTTP 200
- ok: es XML

## P4-REP-45

**tendencias 200 de un proveedor**

Objetivo: La tendencia de la tasa de un proveedor concreto.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/analitica/tendencias?medida=tasa&dimension=proveedor&referencia_id=1" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR"
```

Respuesta - **200 OK** (25 ms, 1729 bytes):

```http
Content-Type: application/json
Content-Length: 1729
X-Correlation-ID: 1cc875c8436e4ed9
```

```json
{
  "medida": "tasa",
  "dimension": "proveedor",
  "referencia_id": 1,
  "objeto": "Lacteos del Norte",
  "meses": [
    "2025-10",
    "2025-11",
    "2025-12",
    "2026-01",
    "2026-02",
    "2026-03",
    "2026-04",
    "2026-05",
    "2026-06",
    "2026-07",
    "2026-08",
    "2026-09"
  ],
  "serie": [
    {
      "mes": "2025-10",
      "unidades_vendidas": 0,
      "unidades_devueltas": 0,
      "valor": null,
      "estado": "muestra_insuficiente"
    },
    {
      "mes": "2025-11",
      "unidades_vendidas": 0,
      "unidades_devueltas": 0,
      "valor": null,
      "estado": "muestra_insuficiente"
    },
    {
      "mes": "2025-12",
      "unidades_vendidas": 0,
      "unidades_devueltas": 0,
      "valor": null,
      "estado": "muestra_insuficiente"
    },
    {
      "mes": "2026-01",
      "unidades_vendidas": 0,
      "unidades_devueltas": 0,
      "valor": null,
      "estado": "muestra_insuficiente"
    },
    {
      "mes": "2026-02",
      "unidades_vendidas": 0,
      "unidades_devueltas": 0,
      "valor": null,
      "estado": "muestra_insuficiente"
    },
    {
      "mes": "2026-03",
      "unidades_vendidas": 0,
      "unidades_devueltas": 0,
      "valor": null,
      "estado": "muestra_insuficiente"
    },
    {
      "mes": "2026-04",
      "unidades_vendidas": 0,
      "unidades_devueltas": 0,
      "valor": null,
      "estado": "muestra_insuficiente"
    },
    {
... (recortado: 41 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: estado ok o sin_datos explicado
- ok: nombra el objeto

## P4-REP-46

**pronosticos 200**

Objetivo: Pronostico con intervalo de prediccion del 95%; aclara que es de los meses siguientes al ultimo mes utilizable.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/analitica/pronosticos?medida=devoluciones&horizonte=3" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (28 ms, 888 bytes):

```http
Content-Type: application/json
Content-Length: 888
X-Correlation-ID: c42869dc20e84c8f
```

```json
{
  "medida": "devoluciones",
  "dimension": null,
  "referencia_id": null,
  "objeto": "todos",
  "meses": [
    "2025-11",
    "2025-12",
    "2026-01",
    "2026-02",
    "2026-03",
    "2026-04",
    "2026-05",
    "2026-06",
    "2026-07",
    "2026-08",
    "2026-09",
    "2026-10"
  ],
  "horizonte": 3,
  "pronostico": {
    "estado": "ok",
    "metodo": "regresion_lineal",
    "confianza_pct": 95,
    "meses_usados": 12,
    "r2": 0.284,
    "confiable": false,
    "puntos": [
      {
        "paso": 1,
        "valor": 13.74,
        "limite_inferior": 0.0,
        "limite_superior": 37.68,
        "mes": "2026-11"
      },
      {
        "paso": 2,
        "valor": 15.27,
        "limite_inferior": 0.0,
        "limite_superior": 40.04,
        "mes": "2026-12"
      },
      {
        "paso": 3,
        "valor": 16.79,
        "limite_inferior": 0.0,
        "limite_superior": 42.49,
        "mes": "2027-01"
      }
    ],
    "advertencia": "Extrapolacion lineal de la serie historica; no considera estacionalidad ni cambios futuros. Usala como referencia, no como compromiso."
  },
  "referencia_promedio_movil_3": 15.33,
  "nota": "Pronostico de los meses siguientes al ultimo mes utilizable, no de hoy."
}
```

Verificaciones:

- ok: HTTP 200
- ok: estado ok o sin_datos explicado
- ok: horizonte 3

## P4-REP-47

**pronosticos 400 horizonte invalido**

Objetivo: El horizonte tiene un maximo.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/analitica/pronosticos?horizonte=99" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (9 ms, 151 bytes):

```http
Content-Type: application/json
Content-Length: 151
X-Correlation-ID: ce5ffb71942b4b6d
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "horizonte debe ser un entero entre 1 y 6.",
    "detalles": null,
    "correlation_id": "ce5ffb71942b4b6d"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-REP-48

**anomalias 200 entre proveedores**

Objetivo: Puntaje z robusto (mediana y MAD): marca proveedores distintos de sus pares, sin decir por que (RN-09).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/analitica/anomalias?tipo=objetos&por=proveedor" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (25 ms, 317 bytes):

```http
Content-Type: application/json
Content-Length: 317
X-Correlation-ID: a18a7ef4f7f44757
```

```json
{
  "tipo": "objetos",
  "por": "proveedor",
  "estado": "sin_datos",
  "omitidos_por_muestra": 1,
  "motivo": "Se requieren al menos 5 objetos con 20 unidades vendidas o mas.",
  "datos": [],
  "metodo": "puntaje z robusto (mediana y MAD); anomalia con |z| >= 3.5",
  "nota": "Una anomalia es un dato distinto de sus pares, no una causa (RN-09)."
}
```

Verificaciones:

- ok: HTTP 200
- ok: estado ok o sin_datos explicado
- ok: declara el umbral
- ok: aclara que no es una causa

## P4-REP-49

**anomalias 200 entre lotes**

Objetivo: Lo mismo entre lotes.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/analitica/anomalias?tipo=objetos&por=lote" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (27 ms, 313 bytes):

```http
Content-Type: application/json
Content-Length: 313
X-Correlation-ID: 5c39d12c3d2d421b
```

```json
{
  "tipo": "objetos",
  "por": "lote",
  "estado": "sin_datos",
  "omitidos_por_muestra": 10,
  "motivo": "Se requieren al menos 5 objetos con 20 unidades vendidas o mas.",
  "datos": [],
  "metodo": "puntaje z robusto (mediana y MAD); anomalia con |z| >= 3.5",
  "nota": "Una anomalia es un dato distinto de sus pares, no una causa (RN-09)."
}
```

Verificaciones:

- ok: HTTP 200
- ok: estado ok o sin_datos

## P4-REP-50

**anomalias 200 entre meses**

Objetivo: Meses que se alejan de la tendencia lineal.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/analitica/anomalias?tipo=meses&medida=devoluciones&meses=12" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (27 ms, 1382 bytes):

```http
Content-Type: application/json
Content-Length: 1382
X-Correlation-ID: 03a5a2b11d06417a
```

```json
{
  "tipo": "meses",
  "medida": "devoluciones",
  "dimension": null,
  "referencia_id": null,
  "objeto": "todos",
  "meses": [
    "2025-11",
    "2025-12",
    "2026-01",
    "2026-02",
    "2026-03",
    "2026-04",
    "2026-05",
    "2026-06",
    "2026-07",
    "2026-08",
    "2026-09",
    "2026-10"
  ],
  "estado": "ok",
  "umbral_z": 3.5,
  "datos": [
    {
      "valor": 0.0,
      "esperado": -4.55,
      "z_robusto": 1.05,
      "anomalia": false,
      "mes": "2025-11"
    },
    {
      "valor": 0.0,
      "esperado": -3.03,
      "z_robusto": 0.78,
      "anomalia": false,
      "mes": "2025-12"
    },
    {
      "valor": 0.0,
      "esperado": -1.5,
      "z_robusto": 0.51,
      "anomalia": false,
      "mes": "2026-01"
    },
    {
      "valor": 0.0,
      "esperado": 0.02,
      "z_robusto": 0.24,
      "anomalia": false,
      "mes": "2026-02"
    },
    {
      "valor": 0.0,
      "esperado": 1.55,
      "z_robusto": -0.03,
      "anomalia": false,
      "mes": "2026-03"
    },
    {
      "valor": 0.0,
      "esperado": 3.07,
      "z_robusto": -0.3,
      "anomalia": false,
      "mes": "2026-04"
    },
    {
      "valor": 0.0,
      "esperado": 4.6,
      "z_robusto": -0.57,
      "anomalia": false,
... (recortado: 41 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: estado ok o sin_datos

## P4-REP-51

**anomalias 400 tipo invalido**

Objetivo: El tipo es objetos o meses.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/analitica/anomalias?tipo=planetas" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (9 ms, 147 bytes):

```http
Content-Type: application/json
Content-Length: 147
X-Correlation-ID: 3c18ef03f7624166
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "tipo debe ser uno de: objetos, meses.",
    "detalles": null,
    "correlation_id": "3c18ef03f7624166"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-REP-52

**alertas de fraude 200**

Objetivo: Senales explicables de posible fraude; advierten que no acusan ni bloquean (RF-25). Nombran clientes, por eso son solo de analisis (RN-15).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/analitica/alertas-fraude" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (29 ms, 690 bytes):

```http
Content-Type: application/json
Content-Length: 690
X-Correlation-ID: 1ee326983f7242c1
```

```json
{
  "datos": [
    {
      "cliente_id": 10,
      "cliente": "Ana Lopez Garcia",
      "devoluciones_90_dias": 19,
      "rechazadas": 0,
      "monto_reembolsado": 586.47,
      "razones": [
        "frecuencia alta en 90 dias"
      ],
      "requiere_revision_humana": true
    },
    {
      "cliente_id": 11,
      "cliente": "Miguel Ramos Soto",
      "devoluciones_90_dias": 14,
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
      "devoluciones_90_dias": 13,
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

Verificaciones:

- ok: HTTP 200
- ok: aviso preventivo
- ok: total coincide

Efecto en PostgreSQL - la consulta queda en la bitacora, solo con el numero de alertas:

```sql
SELECT accion, detalle FROM bitacora WHERE accion = 'consulta_alertas_fraude' ORDER BY id DESC LIMIT 1
```

```text
accion | detalle
consulta_alertas_fraude | 3 alertas
```

## P4-REP-53

**alertas de fraude 403 supervisor**

Objetivo: Nombran clientes: las ven Administrador y Analista, no el Supervisor (RN-15).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/analitica/alertas-fraude" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR"
```

Respuesta - **403 FORBIDDEN** (10 ms, 235 bytes):

```http
Content-Type: application/json
Content-Length: 235
X-Correlation-ID: cbeb002974014a75
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
    "correlation_id": "cbeb002974014a75"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-REP-54

**factores 200: proveedor por tienda**

Objetivo: Cruza dos factores: la tasa de cada combinacion con su intervalo de Wilson del 95 % y la tasa de cada factor por separado (RF-23, RF-24).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/analitica/factores?por=proveedor&con=tienda&limite=5" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (27 ms, 2407 bytes):

```http
Content-Type: application/json
Content-Length: 2407
X-Correlation-ID: ebf45915c8914c64
```

```json
{
  "por": "proveedor",
  "con": "tienda",
  "estado": "ok",
  "tasa_promedio_pct": 28.86,
  "muestra_minima_unidades": 20,
  "omitidas_por_muestra": 7,
  "distinguibles": 2,
  "celdas": [
    {
      "a_id": 1,
      "a_etiqueta": "Lacteos del Norte",
      "b_id": 2,
      "b_etiqueta": "Tienda Valle Oriente",
      "unidades_vendidas": 21,
      "unidades_devueltas": 11,
      "devoluciones": 8,
      "tasa_pct": 52.38,
      "veces_promedio": 1.81,
      "intervalo_95_pct": {
        "bajo": 32.37,
        "alto": 71.66
      },
      "tasa_factor_a_pct": 37.08,
      "tasa_factor_b_pct": 37.25,
      "distinguible": true,
      "lectura": "sin_atribucion",
      "lectura_texto": "La combinacion destaca, pero ningun factor por separado explica el exceso con esta muestra."
    },
    {
      "a_id": 1,
      "a_etiqueta": "Lacteos del Norte",
      "b_id": 1,
      "b_etiqueta": "Tienda Centro",
      "unidades_vendidas": 31,
      "unidades_devueltas": 14,
      "devoluciones": 5,
      "tasa_pct": 45.16,
      "veces_promedio": 1.56,
      "intervalo_95_pct": {
        "bajo": 29.16,
        "alto": 62.23
      },
      "tasa_factor_a_pct": 37.08,
      "tasa_factor_b_pct": 33.33,
      "distinguible": true,
      "lectura": "sin_atribucion",
      "lectura_texto": "La combinacion destaca, pero ningun factor por separado explica el exceso con esta muestra."
    },
    {
      "a_id": 2,
      "a_etiqueta": "CampoVerde Agricola",
      "b_id": 3,
      "b_etiqueta": "Tienda Cumbres",
      "unidades_vendidas": 20,
      "unidades_devueltas": 6,
      "devoluciones": 6,
      "tasa_pct": 30.0,
      "veces_promedio": 1.04,
      "intervalo_95_pct": {
        "bajo": 14.55,
        "alto": 51.9
      },
      "tasa_factor_a_pct": 26.19,
      "tasa_factor_b_pct": 21.51,
      "distinguible": false,
      "lectura": null,
      "lectura_texto": null
    },
    {
... (recortado: 44 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: estado ok o sin_datos explicado
- ok: a lo mas 5 combinaciones
- ok: ordenadas por tasa
- ok: el intervalo envuelve a la tasa
- ok: aclara que no es una causa

## P4-REP-55

**factores 200: el lote problematico destaca**

Objetivo: El lote de la demo (24 unidades, 16 devueltas) es distinguible del promedio y trae su lectura de donde viene el exceso.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/analitica/factores?por=lote&con=proveedor&solo_distinguibles=true" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (28 ms, 963 bytes):

```http
Content-Type: application/json
Content-Length: 963
X-Correlation-ID: b78240d0191a49a6
```

```json
{
  "por": "lote",
  "con": "proveedor",
  "estado": "ok",
  "tasa_promedio_pct": 28.86,
  "muestra_minima_unidades": 20,
  "omitidas_por_muestra": 10,
  "distinguibles": 1,
  "celdas": [
    {
      "a_id": 15,
      "a_etiqueta": "L-2026-PROB-01 (Leche entera 1 L)",
      "b_id": 1,
      "b_etiqueta": "Lacteos del Norte",
      "unidades_vendidas": 24,
      "unidades_devueltas": 16,
      "devoluciones": 4,
      "tasa_pct": 66.67,
      "veces_promedio": 2.31,
      "intervalo_95_pct": {
        "bajo": 46.71,
        "alto": 82.03
      },
      "tasa_factor_a_pct": 66.67,
      "tasa_factor_b_pct": 37.08,
      "distinguible": true,
      "lectura": "factor_a",
      "lectura_texto": "El primer factor ya tiene una tasa alta en conjunto y el segundo no: el exceso parece venir del primero."
    }
  ],
  "total_celdas": 1,
  "metodo": "tasa = unidades devueltas / vendidas por combinacion; intervalo de Wilson del 95 %; una combinacion es distinguible si el extremo bajo del intervalo supera la tasa promedio",
  "nota": "Es una senal para revisar donde investigar, no una causa (RN-09). Solo se juzgan combinaciones con 20 unidades vendidas o mas."
}
```

Verificaciones:

- ok: HTTP 200
- ok: aparece el lote de la demo
- ok: es distinguible y trae lectura
- ok: supera el doble del promedio

## P4-REP-56

**factores 200 XML**

Objetivo: El mismo analisis en XML (RF-31).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/analitica/factores?por=producto&con=tienda&limite=3" \
  -H "Accept: application/xml" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR"
```

Respuesta - **200 OK** (27 ms, 1318 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 1318
X-Correlation-ID: 47921f4c175342fa
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<factores><por>producto</por><con>tienda</con><estado>ok</estado><tasa_promedio_pct>28.86</tasa_promedio_pct><muestra_minima_unidades>20</muestra_minima_unidades><omitidas_por_muestra>27</omitidas_por_muestra><distinguibles>1</distinguibles><celdas><item><a_id>1</a_id><a_etiqueta>Leche entera 1 L</a_etiqueta><b_id>1</b_id><b_etiqueta>Tienda Centro</b_etiqueta><unidades_vendidas>28</unidades_vendidas><unidades_devueltas>14</unidades_devueltas><devoluciones>5</devoluciones><tasa_pct>50.0</tasa_pct><veces_promedio>1.73</veces_promedio><intervalo_95_pct><bajo>32.63</bajo><alto>67.37</alto></intervalo_95_pct><tasa_factor_a_pct>42.86</tasa_factor_a_pct><tasa_factor_b_pct>33.33</tasa_factor_b_pct><distinguible>true</distinguible><lectura>factor_a</lectura><lectura_texto>El primer factor ya tiene una tasa alta en conjunto y el segundo no: el exceso parece venir del primero.</lectura_texto></item></celdas><total_celdas>1</total_celdas><metodo>tasa = unidades devueltas / vendidas por combinacion; intervalo de Wilson del 95 %; una combinacion es distinguible si el extremo bajo del intervalo supera la tasa promedio</metodo><nota>Es una senal para revisar donde investigar, no una causa (RN-09). Solo se juzgan combinaciones con 20 unidades vendidas o mas.</nota></factores>
```

Verificaciones:

- ok: HTTP 200
- ok: es XML
- ok: raiz factores

## P4-REP-57

**factores 400 mismo factor dos veces**

Objetivo: Un cruce necesita dos factores distintos.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/analitica/factores?por=tienda&con=tienda" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (9 ms, 149 bytes):

```http
Content-Type: application/json
Content-Length: 149
X-Correlation-ID: ec27388a9076492a
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "por y con deben ser factores distintos.",
    "detalles": null,
    "correlation_id": "ec27388a9076492a"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-REP-58

**factores 400 ruta no tiene ventas**

Objetivo: Ruta y transportista no se cruzan: no existe 'vendido por ruta' para calcular la tasa.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/analitica/factores?por=ruta" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (8 ms, 165 bytes):

```http
Content-Type: application/json
Content-Length: 165
X-Correlation-ID: 77d98a28a5b14288
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "por debe ser uno de: proveedor, tienda, producto, lote.",
    "detalles": null,
    "correlation_id": "77d98a28a5b14288"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-REP-59

**factores 400 limite fuera de rango**

Objetivo: El limite va de 1 a 100.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/analitica/factores?limite=0" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (8 ms, 150 bytes):

```http
Content-Type: application/json
Content-Length: 150
X-Correlation-ID: 7611f422da7e407c
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "limite debe ser un entero entre 1 y 100.",
    "detalles": null,
    "correlation_id": "7611f422da7e407c"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-REP-60

**factores 403 cliente**

Objetivo: Como el resto de la analitica, no es para clientes (RN-13).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8018/api/v1/analitica/factores" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_CLIENTE"
```

Respuesta - **403 FORBIDDEN** (9 ms, 271 bytes):

```http
Content-Type: application/json
Content-Length: 271
X-Correlation-ID: 717c6ebe9bd8468b
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
        "Analista de Devoluciones",
        "Supervisor",
        "Encargado de Reembolsos"
      ]
    },
    "correlation_id": "717c6ebe9bd8468b"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

