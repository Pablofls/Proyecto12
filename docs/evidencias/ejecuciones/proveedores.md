# Evidencia con curl - `proveedores`

Ejecutada en la VM el 2026-11-22 18:02 UTC con `scripts/evidencias/ejecutar.py proveedores` (commit `f704f96`).
Casos: **49**, correctos: **49**, con falla: **0**. Los tokens y la contrasena de demo estan ocultos; la IP de la VM se muestra como `$VM_HOST`.

Cada respuesta es la que devolvio el servicio: nada se pego a mano. Un caso que no cumple lo esperado queda marcado como falla, no se omite.

## Preparacion

```bash
export VM_HOST=<IP-DE-LA-VM>      # o 127.0.0.1 si corres los comandos dentro de la VM
export PASSWORD_DEMO=...                 # la de las cuentas de demo; no se versiona
login() { curl -s -X POST "http://$VM_HOST:8001/api/v1/auth/login" -H 'Content-Type: application/json' \
  -d "{\"email\":\"$1\",\"password\":\"$PASSWORD_DEMO\"}" | jq -r .access_token; }
export TOKEN_ANALISTA=$(login josue.analista@demo.mx)
export TOKEN_CLIENTE=$(login ana.cliente@demo.mx)
export TOKEN_INSPECTOR=$(login valentina.inspector@demo.mx)
export TOKEN_SUPERVISOR=$(login jorge.supervisor@demo.mx)
```

El login admite 10 intentos por minuto por IP (RNF-13); el token dura 15 minutos.

## Resumen

| Caso | Resultado | HTTP | Descripcion |
|---|---|---|---|
| [P4-PRO-01](#p4-pro-01) | correcto | 200 | salud 200 JSON |
| [P4-PRO-02](#p4-pro-02) | correcto | 200 | salud 200 XML |
| [P4-PRO-03](#p4-pro-03) | correcto | 200 | Swagger: documentacion de la API |
| [P4-PRO-04](#p4-pro-04) | correcto | 200 | Swagger: especificacion OpenAPI |
| [P4-PRO-05](#p4-pro-05) | correcto | 200 | contrato XSD publicado |
| [P4-PRO-06](#p4-pro-06) | correcto | 401 | sin token: 401 |
| [P4-PRO-07](#p4-pro-07) | correcto | 401 | token invalido: 401 |
| [P4-PRO-08](#p4-pro-08) | correcto | 403 | cliente: 403 |
| [P4-PRO-09](#p4-pro-09) | correcto | 403 | inspector: 403 |
| [P4-PRO-10](#p4-pro-10) | correcto | 200 | listado 200 con indicadores |
| [P4-PRO-11](#p4-pro-11) | correcto | 200 | listado 200 XML |
| [P4-PRO-12](#p4-pro-12) | correcto | 200 | listado 200 con busqueda por nombre |
| [P4-PRO-13](#p4-pro-13) | correcto | 400 | listado 400 fecha invalida |
| [P4-PRO-14](#p4-pro-14) | correcto | 200 | detalle 200 del proveedor |
| [P4-PRO-15](#p4-pro-15) | correcto | 404 | detalle 404 |
| [P4-PRO-16](#p4-pro-16) | correcto | 200 | productos 200 |
| [P4-PRO-17](#p4-pro-17) | correcto | 404 | productos 404 |
| [P4-PRO-18](#p4-pro-18) | correcto | 200 | indicadores 200: coinciden con la base |
| [P4-PRO-19](#p4-pro-19) | correcto | 200 | indicadores 200 en un rango de fechas |
| [P4-PRO-20](#p4-pro-20) | correcto | 400 | indicadores 400 fecha invalida |
| [P4-PRO-21](#p4-pro-21) | correcto | 404 | indicadores 404 |
| [P4-PRO-22](#p4-pro-22) | correcto | 201 | reclamacion 201 de un lote y dos devoluciones |
| [P4-PRO-23](#p4-pro-23) | correcto | 201 | reclamacion 201 XML |
| [P4-PRO-24](#p4-pro-24) | correcto | 400 | reclamacion 400 sin lote ni devoluciones |
| [P4-PRO-25](#p4-pro-25) | correcto | 400 | reclamacion 400 XML que no cumple el XSD |
| [P4-PRO-26](#p4-pro-26) | correcto | 409 | reclamacion 409 lote de otro proveedor |
| [P4-PRO-27](#p4-pro-27) | correcto | 409 | reclamacion 409 devolucion de otro proveedor |
| [P4-PRO-28](#p4-pro-28) | correcto | 404 | reclamacion 404 devolucion inexistente |
| [P4-PRO-29](#p4-pro-29) | correcto | 409 | reclamacion 409 devolucion ya reclamada |
| [P4-PRO-30](#p4-pro-30) | correcto | 403 | reclamacion 403 cliente |
| [P4-PRO-31](#p4-pro-31) | correcto | 200 | reclamaciones 200 filtradas |
| [P4-PRO-32](#p4-pro-32) | correcto | 400 | reclamaciones 400 estado desconocido |
| [P4-PRO-33](#p4-pro-33) | correcto | 200 | reclamaciones 200 vencidas |
| [P4-PRO-34](#p4-pro-34) | correcto | 200 | reclamacion 200: detalle con su linea de tiempo |
| [P4-PRO-35](#p4-pro-35) | correcto | 404 | reclamacion 404 |
| [P4-PRO-36](#p4-pro-36) | correcto | 409 | seguimiento 409: no se salta un paso |
| [P4-PRO-37](#p4-pro-37) | correcto | 400 | seguimiento 400 campo no permitido |
| [P4-PRO-38](#p4-pro-38) | correcto | 403 | seguimiento 403 cliente |
| [P4-PRO-39](#p4-pro-39) | correcto | 404 | seguimiento 404 |
| [P4-PRO-40](#p4-pro-40) | correcto | 200 | seguimiento 200: enviada |
| [P4-PRO-41](#p4-pro-41) | correcto | 200 | seguimiento 200: respondida |
| [P4-PRO-42](#p4-pro-42) | correcto | 400 | seguimiento 400 cerrar sin comentario |
| [P4-PRO-43](#p4-pro-43) | correcto | 409 | seguimiento 409 no se recupera mas de lo reclamado |
| [P4-PRO-44](#p4-pro-44) | correcto | 200 | seguimiento 200: cierre parcial |
| [P4-PRO-45](#p4-pro-45) | correcto | 409 | seguimiento 409: cerrada es definitiva |
| [P4-PRO-46](#p4-pro-46) | correcto | 200 | seguimiento 200: enviada (segunda reclamacion) |
| [P4-PRO-47](#p4-pro-47) | correcto | 409 | seguimiento 409: no se acepta lo que nadie respondio |
| [P4-PRO-48](#p4-pro-48) | correcto | 200 | seguimiento 200: retirada sin respuesta |
| [P4-PRO-49](#p4-pro-49) | correcto | 200 | indicadores 200 tras las reclamaciones |

## P4-PRO-01

**salud 200 JSON**

Objetivo: El servicio informa su estado y el de PostgreSQL y Redis (RF-32).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/health" \
  -H "Accept: application/json"
```

Respuesta - **200 OK** (27 ms, 144 bytes):

```http
Content-Type: application/json
Content-Length: 144
X-Correlation-ID: 0b140fd9e3304ca3
```

```json
{
  "servicio": "proveedores",
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

## P4-PRO-02

**salud 200 XML**

Objetivo: El mismo endpoint responde XML (RF-31).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/health" \
  -H "Accept: application/xml"
```

Respuesta - **200 OK** (23 ms, 247 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 247
X-Correlation-ID: 76adfdc26fd0432c
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<respuesta><servicio>proveedores</servicio><version>v1</version><estado>ok</estado><dependencias><postgresql><ok>true</ok><error /></postgresql><redis><ok>true</ok><error /></redis></dependencias></respuesta>
```

Verificaciones:

- ok: HTTP 200
- ok: es XML
- ok: estado ok

## P4-PRO-03

**Swagger: documentacion de la API**

Objetivo: La API publica su documentacion Swagger.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/docs" \
  -H "Accept: text/html"
```

Respuesta - **200 OK** (14 ms, 421 bytes):

```http
Content-Type: text/html; charset=utf-8
Content-Length: 421
X-Correlation-ID: c42c1885bb7d4dca
```

```text
<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Proveedores</title>
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

## P4-PRO-04

**Swagger: especificacion OpenAPI**

Objetivo: La especificacion lista los endpoints de proveedores y reclamaciones.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/openapi.json" \
  -H "Accept: application/json"
```

Respuesta - **200 OK** (15 ms, 6490 bytes):

```http
Content-Type: application/json
Content-Length: 6490
X-Correlation-ID: 3d9e188ac935468f
```

```json
{
  "openapi": "3.0.3",
  "info": {
    "title": "Proveedores",
    "version": "v1",
    "description": "Proveedores con lo que surten e indicadores de calidad, y reclamaciones con seguimiento. Los indicadores orientan la revision humana; no determinan responsabilidad (RN-09). El alta del catalogo de proveedores sigue en ventas-catalogos (8006). Responde JSON o XML segun Accept."
  },
  "servers": [
    {
      "url": "http://localhost:8013"
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
    "/api/v1/proveedores": {
      "get": {
        "summary": "Proveedores con indicadores, de mayor a menor tasa de devolucion",
        "description": "Roles Administrador, Analista, Supervisor y Encargado de Reembolsos.",
        "parameters": [
          {
            "name": "q",
            "in": "query",
            "schema": {
              "type": "string"
            }
          },
          {
            "name": "solo_activos",
            "in": "query",
            "schema": {
              "type": "boolean",
              "default": true
            }
          },
          {
            "name": "desde",
            "in": "query",
            "schema": {
              "type": "string",
              "format": "date"
            }
          },
          {
            "name": "hasta",
            "in": "query",
            "schema": {
              "type": "string",
              "format": "date"
            }
          },
          {
            "name": "limite",
            "in": "query",
            "schema": {
              "type": "integer"
            }
          },
          {
... (recortado: 410 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: incluye las reclamaciones
- ok: incluye el seguimiento

## P4-PRO-05

**contrato XSD publicado**

Objetivo: El contrato XML de la reclamacion se publica para que los clientes lo validen (RF-31).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/contratos/reclamacion.xsd" \
  -H "Accept: application/xml"
```

Respuesta - **200 OK** (63 ms, 1076 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 1076
X-Correlation-ID: e130e2624afb4d49
Content-Disposition: inline; filename=reclamacion.xsd
Cache-Control: no-cache
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Alta de una reclamacion a proveedor (POST /api/v1/proveedores/reclamaciones).
     Se indica el lote, las devoluciones que la respaldan, o ambos. -->
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="reclamacion">
    <xs:complexType>
      <xs:all>
        <xs:element name="proveedor_id" type="xs:positiveInteger"/>
        <xs:element name="lote_id" type="xs:string" minOccurs="0"/>
        <xs:element name="asunto" type="xs:string"/>
        <xs:element name="descripcion" type="xs:string"/>
        <xs:element name="monto_reclamado" type="xs:string" minOccurs="0"/>
        <xs:element name="fecha_limite_respuesta" type="xs:string" minOccurs="0"/>
        <xs:element name="devolucion_ids" minOccurs="0">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="item" type="xs:positiveInteger" minOccurs="0" maxOccurs="100"/>
            </xs:sequence>
          </xs:complexType>
        </xs:element>
      </xs:all>
    </xs:complexType>
  </xs:element>
</xs:schema>

```

Verificaciones:

- ok: HTTP 200
- ok: es un esquema XSD

## P4-PRO-06

**sin token: 401**

Objetivo: Un endpoint protegido exige JWT (RNF-09).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores" \
  -H "Accept: application/json"
```

Respuesta - **401 UNAUTHORIZED** (12 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: ec95149b78754165
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "ec95149b78754165"
  }
}
```

Verificaciones:

- ok: HTTP 401
- ok: tipo no_autenticado

## P4-PRO-07

**token invalido: 401**

Objetivo: Un token alterado se rechaza (RNF-09).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer no.es.un.jwt"
```

Respuesta - **401 UNAUTHORIZED** (12 ms, 136 bytes):

```http
Content-Type: application/json
Content-Length: 136
X-Correlation-ID: 6078ef59b2004ddb
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "token_invalido",
    "mensaje": "El token no es valido.",
    "detalles": null,
    "correlation_id": "6078ef59b2004ddb"
  }
}
```

Verificaciones:

- ok: HTTP 401
- ok: tipo token_invalido

## P4-PRO-08

**cliente: 403**

Objetivo: Los indicadores de calidad y los costos no los ve un cliente (RN-13).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_CLIENTE"
```

Respuesta - **403 FORBIDDEN** (14 ms, 271 bytes):

```http
Content-Type: application/json
Content-Length: 271
X-Correlation-ID: 58ee1161243547f7
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
    "correlation_id": "58ee1161243547f7"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-PRO-09

**inspector: 403**

Objetivo: Tampoco el Inspector: la lectura es de Administrador, Analista, Supervisor y Encargado de Reembolsos.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores/1/indicadores" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_INSPECTOR"
```

Respuesta - **403 FORBIDDEN** (11 ms, 273 bytes):

```http
Content-Type: application/json
Content-Length: 273
X-Correlation-ID: 4d336935ce944d88
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
    "correlation_id": "4d336935ce944d88"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-PRO-10

**listado 200 con indicadores**

Objetivo: Proveedores de mayor a menor tasa de devolucion, con semaforo (RF-24, RF-26).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores?por_pagina=5" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (38 ms, 1646 bytes):

```http
Content-Type: application/json
Content-Length: 1646
X-Correlation-ID: f4aa71c86f8640c0
```

```json
{
  "datos": [
    {
      "id": 1,
      "nombre": "Lacteos del Norte",
      "activo": true,
      "unidades_vendidas": 89,
      "unidades_devueltas": 33.0,
      "devoluciones": 21.0,
      "inspeccionadas": 11,
      "no_aptas": 9,
      "costo_devoluciones": 2318.03,
      "reclamaciones": 0,
      "reclamaciones_abiertas": 0,
      "monto_reclamado": 0.0,
      "monto_recuperado": 0.0,
      "dias_respuesta_promedio": null,
      "tasa_pct": 37.08,
      "veces_promedio": 1.28,
      "semaforo": "atencion",
      "tasa_no_apto_pct": 81.82
    },
    {
      "id": 2,
      "nombre": "CampoVerde Agricola",
      "activo": true,
      "unidades_vendidas": 42,
      "unidades_devueltas": 11.0,
      "devoluciones": 11.0,
      "inspeccionadas": 2,
      "no_aptas": 1,
      "costo_devoluciones": 612.21,
      "reclamaciones": 0,
      "reclamaciones_abiertas": 0,
      "monto_reclamado": 0.0,
      "monto_recuperado": 0.0,
      "dias_respuesta_promedio": null,
      "tasa_pct": 26.19,
      "veces_promedio": 0.91,
      "semaforo": "normal",
      "tasa_no_apto_pct": 50.0
    },
    {
      "id": 4,
      "nombre": "Abarrotes Monterrey",
      "activo": true,
      "unidades_vendidas": 54,
      "unidades_devueltas": 11.0,
      "devoluciones": 11.0,
      "inspeccionadas": 5,
      "no_aptas": 3,
      "costo_devoluciones": 1408.79,
      "reclamaciones": 0,
      "reclamaciones_abiertas": 0,
      "monto_reclamado": 0.0,
      "monto_recuperado": 0.0,
      "dias_respuesta_promedio": null,
      "tasa_pct": 20.37,
      "veces_promedio": 0.71,
      "semaforo": "normal",
      "tasa_no_apto_pct": 60.0
    },
    {
      "id": 3,
      "nombre": "Avicola Real",
      "activo": true,
      "unidades_vendidas": 16,
      "unidades_devueltas": 3.0,
      "devoluciones": 3.0,
      "inspeccionadas": 1,
... (recortado: 21 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: trae el promedio general
- ok: cada fila trae semaforo
- ok: ordenado por tasa

## P4-PRO-11

**listado 200 XML**

Objetivo: El listado responde XML (RF-31).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores?por_pagina=2" \
  -H "Accept: application/xml" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (34 ms, 1473 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 1473
X-Correlation-ID: 4366a3bee4c04569
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<proveedores><datos><item><id>1</id><nombre>Lacteos del Norte</nombre><activo>true</activo><unidades_vendidas>89</unidades_vendidas><unidades_devueltas>33.0</unidades_devueltas><devoluciones>21.0</devoluciones><inspeccionadas>11</inspeccionadas><no_aptas>9</no_aptas><costo_devoluciones>2318.03</costo_devoluciones><reclamaciones>0</reclamaciones><reclamaciones_abiertas>0</reclamaciones_abiertas><monto_reclamado>0.0</monto_reclamado><monto_recuperado>0.0</monto_recuperado><dias_respuesta_promedio /><tasa_pct>37.08</tasa_pct><veces_promedio>1.28</veces_promedio><semaforo>atencion</semaforo><tasa_no_apto_pct>81.82</tasa_no_apto_pct></item><item><id>2</id><nombre>CampoVerde Agricola</nombre><activo>true</activo><unidades_vendidas>42</unidades_vendidas><unidades_devueltas>11.0</unidades_devueltas><devoluciones>11.0</devoluciones><inspeccionadas>2</inspeccionadas><no_aptas>1</no_aptas><costo_devoluciones>612.21</costo_devoluciones><reclamaciones>0</reclamaciones><reclamaciones_abiertas>0</reclamaciones_abiertas><monto_reclamado>0.0</monto_reclamado><monto_recuperado>0.0</monto_recuperado><dias_respuesta_promedio /><tasa_pct>26.19</tasa_pct><veces_promedio>0.91</veces_promedio><semaforo>normal</semaforo><tasa_no_apto_pct>50.0</tasa_no_apto_pct></item></datos><paginacion><pagina>1</pagina><por_pagina>2</por_pagina><total>4</total><paginas>2</paginas></paginacion><tasa_promedio_pct>28.86</tasa_promedio_pct></proveedores>
```

Verificaciones:

- ok: HTTP 200
- ok: es XML
- ok: raiz proveedores

## P4-PRO-12

**listado 200 con busqueda por nombre**

Objetivo: Busca por nombre sin distinguir mayusculas.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores?q=lacteos" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR"
```

Respuesta - **200 OK** (32 ms, 492 bytes):

```http
Content-Type: application/json
Content-Length: 492
X-Correlation-ID: 947a9cfa7217400c
```

```json
{
  "datos": [
    {
      "id": 1,
      "nombre": "Lacteos del Norte",
      "activo": true,
      "unidades_vendidas": 89,
      "unidades_devueltas": 33.0,
      "devoluciones": 21.0,
      "inspeccionadas": 11,
      "no_aptas": 9,
      "costo_devoluciones": 2318.03,
      "reclamaciones": 0,
      "reclamaciones_abiertas": 0,
      "monto_reclamado": 0.0,
      "monto_recuperado": 0.0,
      "dias_respuesta_promedio": null,
      "tasa_pct": 37.08,
      "veces_promedio": 1.28,
      "semaforo": "atencion",
      "tasa_no_apto_pct": 81.82
    }
  ],
  "paginacion": {
    "pagina": 1,
    "por_pagina": 20,
    "total": 1,
    "paginas": 1
  },
  "tasa_promedio_pct": 28.86
}
```

Verificaciones:

- ok: HTTP 200
- ok: encuentra al proveedor

## P4-PRO-13

**listado 400 fecha invalida**

Objetivo: Una fecha mal formada se rechaza.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores?desde=ayer" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (9 ms, 146 bytes):

```http
Content-Type: application/json
Content-Length: 146
X-Correlation-ID: db5b23ae84b0420b
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "desde debe tener formato AAAA-MM-DD.",
    "detalles": null,
    "correlation_id": "db5b23ae84b0420b"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-PRO-14

**detalle 200 del proveedor**

Objetivo: Proveedor con sus indicadores, lo que surte y sus reclamaciones recientes (RF-24).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores/1" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (35 ms, 1090 bytes):

```http
Content-Type: application/json
Content-Length: 1090
X-Correlation-ID: 14299087deaa4703
```

```json
{
  "id": 1,
  "nombre": "Lacteos del Norte",
  "contacto": "contacto@lacteosnorte.mx",
  "activo": true,
  "indicadores": {
    "id": 1,
    "nombre": "Lacteos del Norte",
    "activo": true,
    "unidades_vendidas": 89,
    "unidades_devueltas": 33.0,
    "devoluciones": 21.0,
    "inspeccionadas": 11,
    "no_aptas": 9,
    "costo_devoluciones": 2318.03,
    "reclamaciones": 0,
    "reclamaciones_abiertas": 0,
    "monto_reclamado": 0.0,
    "monto_recuperado": 0.0,
    "dias_respuesta_promedio": null,
    "tasa_pct": 37.08,
    "veces_promedio": 1.28,
    "semaforo": "atencion",
    "tasa_no_apto_pct": 81.82
  },
  "tasa_promedio_pct": 28.86,
  "productos": [
    {
      "id": 1,
      "sku": "LAC-001",
      "nombre": "Leche entera 1 L",
      "clasificacion_temperatura": "refrigerado",
      "activo": true,
      "proveedor_principal": true,
      "lotes": 3
    },
    {
      "id": 3,
      "sku": "LAC-003",
      "nombre": "Queso panela 400 g",
      "clasificacion_temperatura": "refrigerado",
      "activo": true,
      "proveedor_principal": true,
      "lotes": 1
    },
    {
      "id": 2,
      "sku": "LAC-002",
      "nombre": "Yogurt natural 125 g",
      "clasificacion_temperatura": "refrigerado",
      "activo": true,
      "proveedor_principal": true,
      "lotes": 1
    }
  ],
  "reclamaciones_recientes": [],
  "aviso": "Indicadores para revision humana; no determinan responsabilidad (RN-09)."
}
```

Verificaciones:

- ok: HTTP 200
- ok: es el proveedor pedido
- ok: trae indicadores
- ok: trae productos
- ok: recuerda que no determina responsabilidad

## P4-PRO-15

**detalle 404**

Objetivo: Un proveedor inexistente responde 404.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores/999999" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **404 NOT FOUND** (17 ms, 135 bytes):

```http
Content-Type: application/json
Content-Length: 135
X-Correlation-ID: d58af7a8f2f84f2e
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Proveedor inexistente.",
    "detalles": null,
    "correlation_id": "d58af7a8f2f84f2e"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-PRO-16

**productos 200**

Objetivo: Productos que surte, como proveedor principal o por lotes.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores/1/productos" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (22 ms, 466 bytes):

```http
Content-Type: application/json
Content-Length: 466
X-Correlation-ID: 90781a7d94bd4bf3
```

```json
{
  "datos": [
    {
      "id": 1,
      "sku": "LAC-001",
      "nombre": "Leche entera 1 L",
      "clasificacion_temperatura": "refrigerado",
      "activo": true,
      "proveedor_principal": true,
      "lotes": 3
    },
    {
      "id": 3,
      "sku": "LAC-003",
      "nombre": "Queso panela 400 g",
      "clasificacion_temperatura": "refrigerado",
      "activo": true,
      "proveedor_principal": true,
      "lotes": 1
    },
    {
      "id": 2,
      "sku": "LAC-002",
      "nombre": "Yogurt natural 125 g",
      "clasificacion_temperatura": "refrigerado",
      "activo": true,
      "proveedor_principal": true,
      "lotes": 1
    }
  ],
  "total": 3
}
```

Verificaciones:

- ok: HTTP 200
- ok: total coincide con la lista

## P4-PRO-17

**productos 404**

Objetivo: Un proveedor inexistente responde 404.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores/999999/productos" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **404 NOT FOUND** (18 ms, 135 bytes):

```http
Content-Type: application/json
Content-Length: 135
X-Correlation-ID: ba438dfd49b143c5
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Proveedor inexistente.",
    "detalles": null,
    "correlation_id": "ba438dfd49b143c5"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-PRO-18

**indicadores 200: coinciden con la base**

Objetivo: La tasa es unidades devueltas entre vendidas; se contrasta con consultas independientes (RF-26).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores/1/indicadores" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (34 ms, 528 bytes):

```http
Content-Type: application/json
Content-Length: 528
X-Correlation-ID: d91bbee1e0034433
```

```json
{
  "id": 1,
  "nombre": "Lacteos del Norte",
  "activo": true,
  "unidades_vendidas": 89,
  "unidades_devueltas": 33.0,
  "devoluciones": 21.0,
  "inspeccionadas": 11,
  "no_aptas": 9,
  "costo_devoluciones": 2318.03,
  "reclamaciones": 0,
  "reclamaciones_abiertas": 0,
  "monto_reclamado": 0.0,
  "monto_recuperado": 0.0,
  "dias_respuesta_promedio": null,
  "tasa_pct": 37.08,
  "veces_promedio": 1.28,
  "semaforo": "atencion",
  "tasa_no_apto_pct": 81.82,
  "tasa_promedio_pct": 28.86,
  "muestra_minima_unidades": 20,
  "interpretacion": "Patrones para revision humana; no confirman causalidad (RN-09)."
}
```

Verificaciones:

- ok: HTTP 200
- ok: vendidas = la base
- ok: devueltas = la base
- ok: tasa = devueltas / vendidas
- ok: semaforo conocido
- ok: declara la muestra minima

Efecto en PostgreSQL - unidades vendidas y devueltas calculadas aparte:

```sql
SELECT (SELECT COALESCE(SUM(vd.cantidad), 0) FROM venta_detalle vd JOIN ventas v ON v.id = vd.venta_id JOIN lotes l ON l.id = vd.lote_id WHERE v.eliminado_en IS NULL AND l.proveedor_id = 1) AS vendidas, (SELECT COALESCE(SUM(d.cantidad_devuelta), 0) FROM devoluciones d JOIN venta_detalle vd ON vd.id = d.venta_detalle_id JOIN ventas v ON v.id = vd.venta_id JOIN lotes l ON l.id = vd.lote_id WHERE d.eliminado_en IS NULL AND v.eliminado_en IS NULL AND l.proveedor_id = 1) AS devueltas
```

```text
vendidas | devueltas
89 | 33
```

## P4-PRO-19

**indicadores 200 en un rango de fechas**

Objetivo: Los indicadores se pueden acotar por periodo.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores/1/indicadores?desde=2026-01-01&hasta=2026-11-22" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR"
```

Respuesta - **200 OK** (53 ms, 528 bytes):

```http
Content-Type: application/json
Content-Length: 528
X-Correlation-ID: d7f1763a5b4e47a1
```

```json
{
  "id": 1,
  "nombre": "Lacteos del Norte",
  "activo": true,
  "unidades_vendidas": 89,
  "unidades_devueltas": 33.0,
  "devoluciones": 21.0,
  "inspeccionadas": 11,
  "no_aptas": 9,
  "costo_devoluciones": 2318.03,
  "reclamaciones": 0,
  "reclamaciones_abiertas": 0,
  "monto_reclamado": 0.0,
  "monto_recuperado": 0.0,
  "dias_respuesta_promedio": null,
  "tasa_pct": 37.08,
  "veces_promedio": 1.28,
  "semaforo": "atencion",
  "tasa_no_apto_pct": 81.82,
  "tasa_promedio_pct": 28.86,
  "muestra_minima_unidades": 20,
  "interpretacion": "Patrones para revision humana; no confirman causalidad (RN-09)."
}
```

Verificaciones:

- ok: HTTP 200
- ok: trae la tasa

## P4-PRO-20

**indicadores 400 fecha invalida**

Objetivo: Una fecha imposible se rechaza.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores/1/indicadores?desde=2026-13-01" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (28 ms, 146 bytes):

```http
Content-Type: application/json
Content-Length: 146
X-Correlation-ID: 33549e2c7b0e4180
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "desde debe tener formato AAAA-MM-DD.",
    "detalles": null,
    "correlation_id": "33549e2c7b0e4180"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-PRO-21

**indicadores 404**

Objetivo: Un proveedor inexistente responde 404.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores/999999/indicadores" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **404 NOT FOUND** (25 ms, 135 bytes):

```http
Content-Type: application/json
Content-Length: 135
X-Correlation-ID: 36d606d826374ecc
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Proveedor inexistente.",
    "detalles": null,
    "correlation_id": "36d606d826374ecc"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-PRO-22

**reclamacion 201 de un lote y dos devoluciones**

Objetivo: Una reclamacion formal con folio, respaldada por devoluciones del propio lote (RF-24).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"proveedor_id":1,"lote_id":15,"devolucion_ids":[105,106],"asunto":"Evidencia P4: leche tibia en el lote de la demo","descripcion":"Varias devoluciones del mismo lote llegaron sin la cadena de frio","monto_reclamado":"1500.00","fecha_limite_respuesta":"2026-12-06"}'
```

Respuesta - **201 CREATED** (73 ms, 52 bytes):

```http
Content-Type: application/json
Content-Length: 52
X-Correlation-ID: 1931e580b0dc4cf7
Location: /api/v1/proveedores/reclamaciones/4
```

```json
{
  "id": 4,
  "folio": "RCL-2026-0004",
  "estado": "abierta"
}
```

Verificaciones:

- ok: HTTP 201
- ok: folio RCL-AAAA-####
- ok: nace abierta
- ok: trae Location

Efecto en PostgreSQL - la reclamacion, sus devoluciones y su primer evento:

```sql
SELECT r.folio, r.estado, r.monto_reclamado, count(rd.*) AS devoluciones, (SELECT count(*) FROM seguimiento_reclamacion s WHERE s.reclamacion_id = r.id) AS eventos FROM reclamaciones_proveedor r LEFT JOIN reclamacion_devoluciones rd ON rd.reclamacion_id = r.id WHERE r.id = 4 GROUP BY r.id
```

```text
folio | estado | monto_reclamado | devoluciones | eventos
RCL-2026-0004 | abierta | 1500.00 | 2 | 1
```

## P4-PRO-23

**reclamacion 201 XML**

Objetivo: La misma alta en XML, validada contra su XSD (RF-31).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones" \
  -H "Accept: application/xml" \
  -H "Content-Type: application/xml" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '<reclamacion><proveedor_id>1</proveedor_id><asunto>Evidencia P4: reclamacion enviada por XML</asunto><descripcion>Reclamacion de una sola devolucion, por contrato XML</descripcion><devolucion_ids><item>107</item></devolucion_ids></reclamacion>'
```

Respuesta - **201 CREATED** (93 ms, 128 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 128
X-Correlation-ID: de67fa9118a447ed
Location: /api/v1/proveedores/reclamaciones/5
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<reclamacion><id>5</id><folio>RCL-2026-0005</folio><estado>abierta</estado></reclamacion>
```

Verificaciones:

- ok: HTTP 201
- ok: trae folio

## P4-PRO-24

**reclamacion 400 sin lote ni devoluciones**

Objetivo: Toda reclamacion exige un lote o al menos una devolucion que la respalde.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"proveedor_id":1,"asunto":"Evidencia P4: sin origen","descripcion":"No indica de donde sale el reclamo"}'
```

Respuesta - **400 BAD REQUEST** (17 ms, 198 bytes):

```http
Content-Type: application/json
Content-Length: 198
X-Correlation-ID: 8b7380020f8d437a
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Campos invalidos.",
    "detalles": [
      {
        "campo": "lote_id",
        "problema": "indica un lote o al menos una devolucion"
      }
    ],
    "correlation_id": "8b7380020f8d437a"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-PRO-25

**reclamacion 400 XML que no cumple el XSD**

Objetivo: Un XML que no cumple el contrato se rechaza (RF-31).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones" \
  -H "Accept: application/xml" \
  -H "Content-Type: application/xml" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '<reclamacion><asunto>Sin proveedor</asunto></reclamacion>'
```

Respuesta - **400 BAD REQUEST** (14 ms, 449 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 449
X-Correlation-ID: 598f9982822346b2
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<error><codigo>400</codigo><tipo>xml_no_cumple_xsd</tipo><mensaje>El XML no cumple el contrato del endpoint.</mensaje><detalles><item><linea>1</linea><problema>Element 'reclamacion': Missing child element(s). Expected is one of ( proveedor_id, lote_id, descripcion, monto_reclamado, fecha_limite_respuesta, devolucion_ids ).</problema></item></detalles><correlation_id>598f9982822346b2</correlation_id></error>
```

Verificaciones:

- ok: HTTP 400
- ok: tipo xml_no_cumple_xsd

## P4-PRO-26

**reclamacion 409 lote de otro proveedor**

Objetivo: No se le reclama a un proveedor un lote que no surtio.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"proveedor_id":2,"lote_id":15,"asunto":"Evidencia P4: lote ajeno","descripcion":"Se reclama a quien no surtio el lote"}'
```

Respuesta - **409 CONFLICT** (20 ms, 145 bytes):

```http
Content-Type: application/json
Content-Length: 145
X-Correlation-ID: b63d81d633b84bdd
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "lote_ajeno",
    "mensaje": "El lote pertenece a otro proveedor.",
    "detalles": null,
    "correlation_id": "b63d81d633b84bdd"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo lote_ajeno

## P4-PRO-27

**reclamacion 409 devolucion de otro proveedor**

Objetivo: Las devoluciones que respaldan el reclamo deben ser de lotes del proveedor.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"proveedor_id":2,"devolucion_ids":[105],"asunto":"Evidencia P4: devolucion ajena","descripcion":"La devolucion es de un lote de otro proveedor"}'
```

Respuesta - **409 CONFLICT** (22 ms, 201 bytes):

```http
Content-Type: application/json
Content-Length: 201
X-Correlation-ID: ce9a719d945a496d
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "devolucion_ajena",
    "mensaje": "Hay devoluciones de lotes de otro proveedor.",
    "detalles": [
      {
        "campo": "devolucion_ids",
        "problema": "105"
      }
    ],
    "correlation_id": "ce9a719d945a496d"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo devolucion_ajena

## P4-PRO-28

**reclamacion 404 devolucion inexistente**

Objetivo: No se reclama con una devolucion que no existe.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"proveedor_id":1,"devolucion_ids":[99999999],"asunto":"Evidencia P4: devolucion inexistente","descripcion":"La devolucion indicada no existe"}'
```

Respuesta - **404 NOT FOUND** (24 ms, 185 bytes):

```http
Content-Type: application/json
Content-Length: 185
X-Correlation-ID: 91a0fa6d66cb41fd
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Devoluciones inexistentes.",
    "detalles": [
      {
        "campo": "devolucion_ids",
        "problema": "99999999"
      }
    ],
    "correlation_id": "91a0fa6d66cb41fd"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-PRO-29

**reclamacion 409 devolucion ya reclamada**

Objetivo: Una devolucion no puede estar en dos reclamaciones abiertas.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"proveedor_id":1,"devolucion_ids":[105],"asunto":"Evidencia P4: devolucion repetida","descripcion":"La devolucion ya esta en una reclamacion abierta"}'
```

Respuesta - **409 CONFLICT** (26 ms, 218 bytes):

```http
Content-Type: application/json
Content-Length: 218
X-Correlation-ID: e32a217c18844cd3
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "devolucion_reclamada",
    "mensaje": "Hay devoluciones que ya estan en una reclamacion abierta.",
    "detalles": [
      {
        "campo": "devolucion_ids",
        "problema": "105"
      }
    ],
    "correlation_id": "e32a217c18844cd3"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo devolucion_reclamada
- ok: no se creo una tercera reclamacion

Efecto en PostgreSQL - solo existen las 2 reclamaciones creadas antes:

```sql
SELECT count(*) AS reclamaciones_de_prueba FROM reclamaciones_proveedor WHERE asunto LIKE 'Evidencia P4%'
```

```text
reclamaciones_de_prueba
2
```

## P4-PRO-30

**reclamacion 403 cliente**

Objetivo: Crear reclamaciones es de Administrador, Analista y Supervisor (RN-13).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_CLIENTE" \
  -d '{"proveedor_id":1,"lote_id":15,"asunto":"Evidencia P4: cliente","descripcion":"Un cliente no crea reclamaciones a proveedores"}'
```

Respuesta - **403 FORBIDDEN** (10 ms, 245 bytes):

```http
Content-Type: application/json
Content-Length: 245
X-Correlation-ID: 95c33d30abf14b8c
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
        "Supervisor"
      ]
    },
    "correlation_id": "95c33d30abf14b8c"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-PRO-31

**reclamaciones 200 filtradas**

Objetivo: Listado de reclamaciones por proveedor y estado.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones?proveedor_id=1&estado=abierta" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (25 ms, 844 bytes):

```http
Content-Type: application/json
Content-Length: 844
X-Correlation-ID: fbdc93aa81d54df5
```

```json
{
  "datos": [
    {
      "id": 5,
      "folio": "RCL-2026-0005",
      "proveedor_id": 1,
      "proveedor": "Lacteos del Norte",
      "lote_id": null,
      "numero_lote": null,
      "asunto": "Evidencia P4: reclamacion enviada por XML",
      "estado": "abierta",
      "resolucion": null,
      "monto_reclamado": null,
      "monto_recuperado": null,
      "fecha_limite_respuesta": null,
      "fecha_creacion": "2026-11-22T18:02:47.003996+00:00",
      "fecha_cierre": null,
      "vencida": false
    },
    {
      "id": 4,
      "folio": "RCL-2026-0004",
      "proveedor_id": 1,
      "proveedor": "Lacteos del Norte",
      "lote_id": 15,
      "numero_lote": "L-2026-PROB-01",
      "asunto": "Evidencia P4: leche tibia en el lote de la demo",
      "estado": "abierta",
      "resolucion": null,
      "monto_reclamado": 1500.0,
      "monto_recuperado": null,
      "fecha_limite_respuesta": "2026-12-06",
      "fecha_creacion": "2026-11-22T18:02:46.550222+00:00",
      "fecha_cierre": null,
      "vencida": false
    }
  ],
  "paginacion": {
    "pagina": 1,
    "por_pagina": 20,
    "total": 2,
    "paginas": 1
  }
}
```

Verificaciones:

- ok: HTTP 200
- ok: incluye la recien creada
- ok: todas abiertas

## P4-PRO-32

**reclamaciones 400 estado desconocido**

Objetivo: Un estado que no existe se rechaza.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones?estado=inventado" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (9 ms, 129 bytes):

```http
Content-Type: application/json
Content-Length: 129
X-Correlation-ID: bf43a1701d404c73
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "estado desconocido.",
    "detalles": null,
    "correlation_id": "bf43a1701d404c73"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-PRO-33

**reclamaciones 200 vencidas**

Objetivo: Las enviadas o en analisis cuya fecha limite ya paso.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones?vencidas=true" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR"
```

Respuesta - **200 OK** (24 ms, 77 bytes):

```http
Content-Type: application/json
Content-Length: 77
X-Correlation-ID: dbca0533314d4e2b
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
- ok: trae paginacion

## P4-PRO-34

**reclamacion 200: detalle con su linea de tiempo**

Objetivo: La reclamacion con sus devoluciones y su historial (RN-12).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones/4" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (29 ms, 839 bytes):

```http
Content-Type: application/json
Content-Length: 839
X-Correlation-ID: 50bce241e70a46a1
```

```json
{
  "id": 4,
  "folio": "RCL-2026-0004",
  "proveedor_id": 1,
  "proveedor": "Lacteos del Norte",
  "lote_id": 15,
  "numero_lote": "L-2026-PROB-01",
  "asunto": "Evidencia P4: leche tibia en el lote de la demo",
  "descripcion": "Varias devoluciones del mismo lote llegaron sin la cadena de frio",
  "estado": "abierta",
  "resolucion": null,
  "monto_reclamado": 1500.0,
  "monto_recuperado": null,
  "fecha_limite_respuesta": "2026-12-06",
  "fecha_creacion": "2026-11-22T18:02:46.550222+00:00",
  "fecha_cierre": null,
  "vencida": false,
  "devoluciones": [
    {
      "id": 105,
      "folio_devolucion": "DEV-2026-0105",
      "estado": "cerrada",
      "cantidad_devuelta": 4
    },
    {
      "id": 106,
      "folio_devolucion": "DEV-2026-0106",
      "estado": "cerrada",
      "cantidad_devuelta": 4
    }
  ],
  "seguimiento": [
    {
      "estado_anterior": null,
      "estado_nuevo": "abierta",
      "comentario": "Reclamacion creada",
      "fecha": "2026-11-22T18:02:46.550222+00:00",
      "usuario": "Josue Berdeal"
    }
  ]
}
```

Verificaciones:

- ok: HTTP 200
- ok: dos devoluciones
- ok: un evento: abierta

## P4-PRO-35

**reclamacion 404**

Objetivo: Una reclamacion inexistente responde 404.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones/999999" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **404 NOT FOUND** (20 ms, 137 bytes):

```http
Content-Type: application/json
Content-Length: 137
X-Correlation-ID: 83ebe72e44d64d6a
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Reclamacion inexistente.",
    "detalles": null,
    "correlation_id": "83ebe72e44d64d6a"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-PRO-36

**seguimiento 409: no se salta un paso**

Objetivo: De abierta no se pasa a respondida: antes hay que enviarla.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones/4/seguimiento" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"estado":"respondida"}'
```

Respuesta - **409 CONFLICT** (19 ms, 161 bytes):

```http
Content-Type: application/json
Content-Length: 161
X-Correlation-ID: e6de376893ca429f
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "transicion_invalida",
    "mensaje": "No se puede pasar de abierta a respondida.",
    "detalles": null,
    "correlation_id": "e6de376893ca429f"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo transicion_invalida

## P4-PRO-37

**seguimiento 400 campo no permitido**

Objetivo: Solo se aceptan los campos del contrato.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones/5/seguimiento" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"estado":"enviada","usuario_id":1}'
```

Respuesta - **400 BAD REQUEST** (17 ms, 179 bytes):

```http
Content-Type: application/json
Content-Length: 179
X-Correlation-ID: 0bceac83b4b84da3
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Campos invalidos.",
    "detalles": [
      {
        "campo": "usuario_id",
        "problema": "campo no permitido"
      }
    ],
    "correlation_id": "0bceac83b4b84da3"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-PRO-38

**seguimiento 403 cliente**

Objetivo: Dar seguimiento es de Administrador, Analista y Supervisor (RN-13).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones/4/seguimiento" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_CLIENTE" \
  -d '{"estado":"enviada"}'
```

Respuesta - **403 FORBIDDEN** (9 ms, 245 bytes):

```http
Content-Type: application/json
Content-Length: 245
X-Correlation-ID: 14e0ca9fc34743e1
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
        "Supervisor"
      ]
    },
    "correlation_id": "14e0ca9fc34743e1"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-PRO-39

**seguimiento 404**

Objetivo: Una reclamacion inexistente responde 404.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones/999999/seguimiento" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"estado":"enviada"}'
```

Respuesta - **404 NOT FOUND** (20 ms, 137 bytes):

```http
Content-Type: application/json
Content-Length: 137
X-Correlation-ID: 19ea2b00eedf4ecb
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Reclamacion inexistente.",
    "detalles": null,
    "correlation_id": "19ea2b00eedf4ecb"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-PRO-40

**seguimiento 200: enviada**

Objetivo: Primer paso del ciclo: abierta a enviada.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones/4/seguimiento" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"estado":"enviada","comentario":"Se envia al proveedor por correo"}'
```

Respuesta - **200 OK** (22 ms, 94 bytes):

```http
Content-Type: application/json
Content-Length: 94
X-Correlation-ID: 325f378c1af24bc5
```

```json
{
  "id": 4,
  "folio": "RCL-2026-0004",
  "estado": "enviada",
  "resolucion": null,
  "monto_recuperado": null
}
```

Verificaciones:

- ok: HTTP 200
- ok: estado enviada

## P4-PRO-41

**seguimiento 200: respondida**

Objetivo: El proveedor respondio.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones/4/seguimiento" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"estado":"respondida","comentario":"Respondio ofreciendo nota de credito"}'
```

Respuesta - **200 OK** (24 ms, 97 bytes):

```http
Content-Type: application/json
Content-Length: 97
X-Correlation-ID: 33601b2f79b347e4
```

```json
{
  "id": 4,
  "folio": "RCL-2026-0004",
  "estado": "respondida",
  "resolucion": null,
  "monto_recuperado": null
}
```

Verificaciones:

- ok: HTTP 200
- ok: estado respondida

## P4-PRO-42

**seguimiento 400 cerrar sin comentario**

Objetivo: Cerrar exige explicar como termino.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones/4/seguimiento" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"estado":"cerrada","resolucion":"parcial","monto_recuperado":"600.00"}'
```

Respuesta - **400 BAD REQUEST** (20 ms, 172 bytes):

```http
Content-Type: application/json
Content-Length: 172
X-Correlation-ID: 313994c59d124a9c
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Campos invalidos.",
    "detalles": [
      {
        "campo": "comentario",
        "problema": "obligatorio"
      }
    ],
    "correlation_id": "313994c59d124a9c"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-PRO-43

**seguimiento 409 no se recupera mas de lo reclamado**

Objetivo: El monto recuperado no puede superar el reclamado (1500.00).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones/4/seguimiento" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"estado":"cerrada","resolucion":"aceptada","monto_recuperado":"1500.01","comentario":"Intento de recuperar de mas"}'
```

Respuesta - **409 CONFLICT** (18 ms, 156 bytes):

```http
Content-Type: application/json
Content-Length: 156
X-Correlation-ID: 3d93f6622d874b34
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "monto_excedido",
    "mensaje": "No se puede recuperar mas de lo reclamado.",
    "detalles": null,
    "correlation_id": "3d93f6622d874b34"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo monto_excedido

## P4-PRO-44

**seguimiento 200: cierre parcial**

Objetivo: Se cierra con resolucion y monto recuperado; el cierre queda fechado (RN-12).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones/4/seguimiento" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"estado":"cerrada","resolucion":"parcial","monto_recuperado":"600.00","comentario":"Nota de credito por una parte del lote"}'
```

Respuesta - **200 OK** (23 ms, 100 bytes):

```http
Content-Type: application/json
Content-Length: 100
X-Correlation-ID: 90b0364048ca4f9a
```

```json
{
  "id": 4,
  "folio": "RCL-2026-0004",
  "estado": "cerrada",
  "resolucion": "parcial",
  "monto_recuperado": 600.0
}
```

Verificaciones:

- ok: HTTP 200
- ok: estado cerrada
- ok: resolucion parcial
- ok: recupero 600

Efecto en PostgreSQL - la reclamacion cerrada:

```sql
SELECT estado, resolucion, monto_reclamado, monto_recuperado, fecha_cierre IS NOT NULL AS tiene_fecha_cierre FROM reclamaciones_proveedor WHERE id = 4
```

```text
estado | resolucion | monto_reclamado | monto_recuperado | tiene_fecha_cierre
cerrada | parcial | 1500.00 | 600.00 | t
```

Efecto en PostgreSQL - su linea de tiempo:

```sql
SELECT estado_anterior, estado_nuevo FROM seguimiento_reclamacion WHERE reclamacion_id = 4 ORDER BY id
```

```text
estado_anterior | estado_nuevo
 | abierta
abierta | enviada
enviada | respondida
respondida | cerrada
```

## P4-PRO-45

**seguimiento 409: cerrada es definitiva**

Objetivo: Una reclamacion cerrada no vuelve a abrirse.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones/4/seguimiento" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"estado":"enviada"}'
```

Respuesta - **409 CONFLICT** (21 ms, 158 bytes):

```http
Content-Type: application/json
Content-Length: 158
X-Correlation-ID: c936bfe4838b453a
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "transicion_invalida",
    "mensaje": "No se puede pasar de cerrada a enviada.",
    "detalles": null,
    "correlation_id": "c936bfe4838b453a"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo transicion_invalida

## P4-PRO-46

**seguimiento 200: enviada (segunda reclamacion)**

Objetivo: La segunda reclamacion se envia, pero el proveedor no responde.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones/5/seguimiento" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"estado":"enviada"}'
```

Respuesta - **200 OK** (24 ms, 94 bytes):

```http
Content-Type: application/json
Content-Length: 94
X-Correlation-ID: 1464da901de0484f
```

```json
{
  "id": 5,
  "folio": "RCL-2026-0005",
  "estado": "enviada",
  "resolucion": null,
  "monto_recuperado": null
}
```

Verificaciones:

- ok: HTTP 200
- ok: estado enviada

## P4-PRO-47

**seguimiento 409: no se acepta lo que nadie respondio**

Objetivo: Aceptar, aceptar parcialmente o rechazar exige que el proveedor haya respondido.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones/5/seguimiento" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"estado":"cerrada","resolucion":"aceptada","monto_recuperado":"10","comentario":"Intento sin respuesta del proveedor"}'
```

Respuesta - **409 CONFLICT** (20 ms, 179 bytes):

```http
Content-Type: application/json
Content-Length: 179
X-Correlation-ID: afaca5cab2794ac7
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "sin_respuesta",
    "mensaje": "Solo se cierra como aceptada despues de que el proveedor responda.",
    "detalles": null,
    "correlation_id": "afaca5cab2794ac7"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo sin_respuesta

## P4-PRO-48

**seguimiento 200: retirada sin respuesta**

Objetivo: Retirar una reclamacion si se puede en cualquier momento; no recupera nada.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8013/api/v1/proveedores/reclamaciones/5/seguimiento" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"estado":"cerrada","resolucion":"retirada","comentario":"Ya no procede la reclamacion"}'
```

Respuesta - **200 OK** (22 ms, 99 bytes):

```http
Content-Type: application/json
Content-Length: 99
X-Correlation-ID: f2ce6bffa574463f
```

```json
{
  "id": 5,
  "folio": "RCL-2026-0005",
  "estado": "cerrada",
  "resolucion": "retirada",
  "monto_recuperado": 0.0
}
```

Verificaciones:

- ok: HTTP 200
- ok: resolucion retirada
- ok: no recupera nada

Efecto en PostgreSQL - la reclamacion retirada:

```sql
SELECT estado, resolucion, monto_recuperado FROM reclamaciones_proveedor WHERE id = 5
```

```text
estado | resolucion | monto_recuperado
cerrada | retirada | 0.00
```

## P4-PRO-49

**indicadores 200 tras las reclamaciones**

Objetivo: El proveedor ya cuenta sus reclamaciones y lo recuperado.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8013/api/v1/proveedores/1/indicadores" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (34 ms, 532 bytes):

```http
Content-Type: application/json
Content-Length: 532
X-Correlation-ID: fc0958192a3d4772
```

```json
{
  "id": 1,
  "nombre": "Lacteos del Norte",
  "activo": true,
  "unidades_vendidas": 89,
  "unidades_devueltas": 33.0,
  "devoluciones": 21.0,
  "inspeccionadas": 11,
  "no_aptas": 9,
  "costo_devoluciones": 2318.03,
  "reclamaciones": 2,
  "reclamaciones_abiertas": 0,
  "monto_reclamado": 1500.0,
  "monto_recuperado": 600.0,
  "dias_respuesta_promedio": 0.0,
  "tasa_pct": 37.08,
  "veces_promedio": 1.28,
  "semaforo": "atencion",
  "tasa_no_apto_pct": 81.82,
  "tasa_promedio_pct": 28.86,
  "muestra_minima_unidades": 20,
  "interpretacion": "Patrones para revision humana; no confirman causalidad (RN-09)."
}
```

Verificaciones:

- ok: HTTP 200
- ok: 2 reclamaciones al menos
- ok: recupero al menos 600

## Limpieza

Al terminar se borraron los datos que creo esta corrida, para no dejar basura en la base de demostracion. **La bitacora no se toca**: es de solo agregar (migracion 045).

