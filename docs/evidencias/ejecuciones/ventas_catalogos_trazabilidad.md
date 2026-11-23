# Evidencia con curl - `ventas-catalogos (trazabilidad)`

Ejecutada en la VM el 2026-11-22 18:24 UTC con `scripts/evidencias/ejecutar.py trazabilidad` (commit `f627d72`).
Casos: **51**, correctos: **51**, con falla: **0**. Los tokens y la contrasena de demo estan ocultos; la IP de la VM se muestra como `$VM_HOST`.

Cada respuesta es la que devolvio el servicio: nada se pego a mano. Un caso que no cumple lo esperado queda marcado como falla, no se omite.

## Preparacion

```bash
export VM_HOST=<IP-DE-LA-VM>      # o 127.0.0.1 si corres los comandos dentro de la VM
export PASSWORD_DEMO=...                 # la de las cuentas de demo; no se versiona
login() { curl -s -X POST "http://$VM_HOST:8001/api/v1/auth/login" -H 'Content-Type: application/json' \
  -d "{\"email\":\"$1\",\"password\":\"$PASSWORD_DEMO\"}" | jq -r .access_token; }
export TOKEN_ADMIN=$(login pablo.admin@demo.mx)
export TOKEN_ALMACEN=$(login marta.almacen@demo.mx)
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
| [P4-TRZ-01](#p4-trz-01) | correcto | 200 | salud 200 JSON |
| [P4-TRZ-02](#p4-trz-02) | correcto | 200 | Swagger: especificacion OpenAPI |
| [P4-TRZ-03](#p4-trz-03) | correcto | 200 | contrato XSD de series publicado |
| [P4-TRZ-04](#p4-trz-04) | correcto | 401 | sin token: 401 |
| [P4-TRZ-05](#p4-trz-05) | correcto | 403 | cliente: 403 |
| [P4-TRZ-06](#p4-trz-06) | correcto | 403 | encargado de reembolsos: 403 |
| [P4-TRZ-07](#p4-trz-07) | correcto | 200 | lotes 200: el lote problematico sube al inicio |
| [P4-TRZ-08](#p4-trz-08) | correcto | 200 | lotes 200 XML |
| [P4-TRZ-09](#p4-trz-09) | correcto | 200 | lotes 200 busqueda por numero de lote |
| [P4-TRZ-10](#p4-trz-10) | correcto | 200 | lotes 200 solo con devoluciones y de un proveedor |
| [P4-TRZ-11](#p4-trz-11) | correcto | 400 | lotes 400 proveedor_id no numerico |
| [P4-TRZ-12](#p4-trz-12) | correcto | 400 | lotes 400 busqueda demasiado larga |
| [P4-TRZ-13](#p4-trz-13) | correcto | 200 | lotes 200 con intento de inyeccion SQL |
| [P4-TRZ-14](#p4-trz-14) | correcto | 200 | trazabilidad de un lote 200 |
| [P4-TRZ-15](#p4-trz-15) | correcto | 200 | trazabilidad de un lote 200 XML |
| [P4-TRZ-16](#p4-trz-16) | correcto | 404 | trazabilidad de un lote 404 |
| [P4-TRZ-17](#p4-trz-17) | correcto | 403 | series 403 analista |
| [P4-TRZ-18](#p4-trz-18) | correcto | 201 | series 201 alta de tres |
| [P4-TRZ-19](#p4-trz-19) | correcto | 201 | series 201 idempotente |
| [P4-TRZ-20](#p4-trz-20) | correcto | 201 | series 201 XML |
| [P4-TRZ-21](#p4-trz-21) | correcto | 400 | series 400 formato invalido |
| [P4-TRZ-22](#p4-trz-22) | correcto | 400 | series 400 repetidas en la lista |
| [P4-TRZ-23](#p4-trz-23) | correcto | 404 | series 404 lote inexistente |
| [P4-TRZ-24](#p4-trz-24) | correcto | 201 | series 201 en el lote de la demo (para la linea saturada) |
| [P4-TRZ-25](#p4-trz-25) | correcto | 201 | series 201 en otro lote (prepara el conflicto) |
| [P4-TRZ-26](#p4-trz-26) | correcto | 409 | series 409 ya pertenece a otro lote |
| [P4-TRZ-27](#p4-trz-27) | correcto | 200 | serie 200 en almacen |
| [P4-TRZ-28](#p4-trz-28) | correcto | 400 | serie 400 formato invalido |
| [P4-TRZ-29](#p4-trz-29) | correcto | 404 | serie 404 inexistente |
| [P4-TRZ-30](#p4-trz-30) | correcto | 403 | vincular serie 403 analista |
| [P4-TRZ-31](#p4-trz-31) | correcto | 400 | vincular serie 400 id invalido |
| [P4-TRZ-32](#p4-trz-32) | correcto | 404 | vincular serie 404 linea inexistente |
| [P4-TRZ-33](#p4-trz-33) | correcto | 409 | vincular serie 409 linea de otro lote |
| [P4-TRZ-34](#p4-trz-34) | correcto | 409 | vincular serie 409 linea sin cupo |
| [P4-TRZ-35](#p4-trz-35) | correcto | 200 | vincular serie 200 por el Operador de Almacen |
| [P4-TRZ-36](#p4-trz-36) | correcto | 200 | vincular serie 200 idempotente |
| [P4-TRZ-37](#p4-trz-37) | correcto | 200 | vincular serie 200 XML |
| [P4-TRZ-38](#p4-trz-38) | correcto | 409 | vincular serie 409 ya ligada a otra venta |
| [P4-TRZ-39](#p4-trz-39) | correcto | 200 | serie 200 devuelta: recorrido completo |
| [P4-TRZ-40](#p4-trz-40) | correcto | 200 | serie 200 de otra serie ligada |
| [P4-TRZ-41](#p4-trz-41) | correcto | 200 | tasas 200 por proveedor |
| [P4-TRZ-42](#p4-trz-42) | correcto | 200 | tasas 200 por tienda |
| [P4-TRZ-43](#p4-trz-43) | correcto | 200 | tasas 200 por producto |
| [P4-TRZ-44](#p4-trz-44) | correcto | 200 | tasas 200 por lote |
| [P4-TRZ-45](#p4-trz-45) | correcto | 200 | tasas 200 por ruta |
| [P4-TRZ-46](#p4-trz-46) | correcto | 200 | tasas 200: el lote problematico contra la base |
| [P4-TRZ-47](#p4-trz-47) | correcto | 200 | tasas 200 en un periodo |
| [P4-TRZ-48](#p4-trz-48) | correcto | 200 | tasas 200 XML |
| [P4-TRZ-49](#p4-trz-49) | correcto | 400 | tasas 400 dimension invalida |
| [P4-TRZ-50](#p4-trz-50) | correcto | 400 | tasas 400 fecha invalida |
| [P4-TRZ-51](#p4-trz-51) | correcto | 400 | tasas 400 hasta antes de desde |

## P4-TRZ-01

**salud 200 JSON**

Objetivo: El servicio informa su estado y el de PostgreSQL y Redis (RF-32).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/health" \
  -H "Accept: application/json"
```

Respuesta - **200 OK** (17 ms, 149 bytes):

```http
Content-Type: application/json
Content-Length: 149
X-Correlation-ID: 81e271f85fe44770
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

Verificaciones:

- ok: HTTP 200
- ok: estado ok
- ok: PostgreSQL ok

## P4-TRZ-02

**Swagger: especificacion OpenAPI**

Objetivo: La especificacion incluye la trazabilidad.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/openapi.json" \
  -H "Accept: application/json"
```

Respuesta - **200 OK** (10 ms, 12448 bytes):

```http
Content-Type: application/json
Content-Length: 12448
X-Correlation-ID: 5807deb1f71b4189
```

```json
{
  "openapi": "3.0.3",
  "info": {
    "title": "Servicio de ventas y catalogos - Plataforma de devoluciones",
    "version": "1.0.0",
    "description": "Consulta de ventas y lineas con cantidad disponible, y administracion de los siete catalogos. JSON/XML, JWT y PostgreSQL. RF-05, RF-06."
  },
  "servers": [
    {
      "url": "/"
    }
  ],
  "paths": {
    "/health": {
      "get": {
        "summary": "Estado del servicio",
        "responses": {
          "200": {
            "description": "Estado del servicio",
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
    "/api/v1/ventas": {
      "get": {
        "summary": "Listar ventas, solo las propias para cliente",
        "responses": {
          "200": {
            "description": "Listar ventas, solo las propias para cliente",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object"
                }
... (recortado: 919 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: incluye lotes
- ok: incluye tasas

## P4-TRZ-03

**contrato XSD de series publicado**

Objetivo: El contrato XML del alta de series se publica (RF-31).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/contratos/series.xsd" \
  -H "Accept: application/xml"
```

Respuesta - **200 OK** (11 ms, 813 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 813
X-Correlation-ID: 381a8741d7484bf7
Content-Disposition: inline; filename=series.xsd
Cache-Control: no-cache
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Alta de numeros de serie de un lote (POST /api/v1/trazabilidad/lotes/{id}/series). -->
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="lote_series">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="series">
          <xs:complexType>
            <xs:sequence>
              <xs:element name="item" minOccurs="1" maxOccurs="500">
                <xs:simpleType>
                  <xs:restriction base="xs:string">
                    <xs:pattern value="[A-Za-z0-9._\-]{1,60}"/>
                  </xs:restriction>
                </xs:simpleType>
              </xs:element>
            </xs:sequence>
          </xs:complexType>
        </xs:element>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>

```

Verificaciones:

- ok: HTTP 200
- ok: es un esquema XSD

## P4-TRZ-04

**sin token: 401**

Objetivo: Un endpoint protegido exige JWT (RNF-09).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/lotes" \
  -H "Accept: application/json"
```

Respuesta - **401 UNAUTHORIZED** (8 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: 66481350a56246a9
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "66481350a56246a9"
  }
}
```

Verificaciones:

- ok: HTTP 401
- ok: tipo no_autenticado

## P4-TRZ-05

**cliente: 403**

Objetivo: Los clientes no consultan trazabilidad: expone proveedores y costos internos (RN-13, RN-15).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/lotes" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_CLIENTE"
```

Respuesta - **403 FORBIDDEN** (10 ms, 345 bytes):

```http
Content-Type: application/json
Content-Length: 345
X-Correlation-ID: 0aa2f84abd874422
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
        "Inspector",
        "Encargado del Centro de Devoluciones",
        "Coordinador de Logistica",
        "Operador de Almacen",
        "Supervisor"
      ]
    },
    "correlation_id": "0aa2f84abd874422"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-TRZ-06

**encargado de reembolsos: 403**

Objetivo: Tampoco es un rol de trazabilidad.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/tasas" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_REEMBOLSOS"
```

Respuesta - **403 FORBIDDEN** (10 ms, 361 bytes):

```http
Content-Type: application/json
Content-Length: 361
X-Correlation-ID: 1505f26ad21b4387
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "Tu rol no tiene permiso para esta operacion.",
    "detalles": {
      "rol": "Encargado de Reembolsos",
      "roles_permitidos": [
        "Administrador",
        "Analista de Devoluciones",
        "Inspector",
        "Encargado del Centro de Devoluciones",
        "Coordinador de Logistica",
        "Operador de Almacen",
        "Supervisor"
      ]
    },
    "correlation_id": "1505f26ad21b4387"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-TRZ-07

**lotes 200: el lote problematico sube al inicio**

Objetivo: Lotes ordenados por tasa de devolucion, para encontrar los de problemas recurrentes (RF-23).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/lotes?por_pagina=5" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (26 ms, 1362 bytes):

```http
Content-Type: application/json
Content-Length: 1362
X-Correlation-ID: 4372cbad79a64276
```

```json
{
  "datos": [
    {
      "id": 15,
      "numero_lote": "L-2026-PROB-01",
      "producto_id": 1,
      "producto": "Leche entera 1 L",
      "clasificacion_temperatura": "refrigerado",
      "proveedor_id": 1,
      "proveedor": "Lacteos del Norte",
      "unidades_vendidas": 24,
      "unidades_devueltas": 16,
      "devoluciones": 4,
      "tasa_pct": 66.67
    },
    {
      "id": 6,
      "numero_lote": "L-2026-118",
      "producto_id": 5,
      "producto": "Tomate saladette 1 kg",
      "clasificacion_temperatura": "refrigerado",
      "proveedor_id": 2,
      "proveedor": "CampoVerde Agricola",
      "unidades_vendidas": 14,
      "unidades_devueltas": 6,
      "devoluciones": 6,
      "tasa_pct": 42.86
    },
    {
      "id": 4,
      "numero_lote": "L-2026-070",
      "producto_id": 3,
      "producto": "Queso panela 400 g",
      "clasificacion_temperatura": "refrigerado",
      "proveedor_id": 1,
      "proveedor": "Lacteos del Norte",
      "unidades_vendidas": 18,
      "unidades_devueltas": 7,
      "devoluciones": 7,
      "tasa_pct": 38.89
    },
    {
      "id": 9,
      "numero_lote": "L-2026-301",
      "producto_id": 8,
      "producto": "Arroz blanco 1 kg",
      "clasificacion_temperatura": "no_refrigerado",
      "proveedor_id": 4,
      "proveedor": "Abarrotes Monterrey",
      "unidades_vendidas": 15,
      "unidades_devueltas": 5,
      "devoluciones": 5,
      "tasa_pct": 33.33
    },
    {
      "id": 1,
      "numero_lote": "L-2026-045",
      "producto_id": 1,
      "producto": "Leche entera 1 L",
      "clasificacion_temperatura": "refrigerado",
      "proveedor_id": 1,
      "proveedor": "Lacteos del Norte",
      "unidades_vendidas": 18,
      "unidades_devueltas": 5,
      "devoluciones": 5,
      "tasa_pct": 27.78
    }
  ],
  "paginacion": {
    "pagina": 1,
... (recortado: 5 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: ordenado por tasa
- ok: la tasa es devueltas/vendidas

## P4-TRZ-08

**lotes 200 XML**

Objetivo: El listado responde XML (RF-31).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/lotes?por_pagina=2" \
  -H "Accept: application/xml" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR"
```

Respuesta - **200 OK** (27 ms, 988 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 988
X-Correlation-ID: 608150ce201f4e56
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<lotes><datos><item><id>15</id><numero_lote>L-2026-PROB-01</numero_lote><producto_id>1</producto_id><producto>Leche entera 1 L</producto><clasificacion_temperatura>refrigerado</clasificacion_temperatura><proveedor_id>1</proveedor_id><proveedor>Lacteos del Norte</proveedor><unidades_vendidas>24</unidades_vendidas><unidades_devueltas>16</unidades_devueltas><devoluciones>4</devoluciones><tasa_pct>66.67</tasa_pct></item><item><id>6</id><numero_lote>L-2026-118</numero_lote><producto_id>5</producto_id><producto>Tomate saladette 1 kg</producto><clasificacion_temperatura>refrigerado</clasificacion_temperatura><proveedor_id>2</proveedor_id><proveedor>CampoVerde Agricola</proveedor><unidades_vendidas>14</unidades_vendidas><unidades_devueltas>6</unidades_devueltas><devoluciones>6</devoluciones><tasa_pct>42.86</tasa_pct></item></datos><paginacion><pagina>1</pagina><por_pagina>2</por_pagina><total>12</total><paginas>6</paginas></paginacion></lotes>
```

Verificaciones:

- ok: HTTP 200
- ok: es XML
- ok: raiz lotes

## P4-TRZ-09

**lotes 200 busqueda por numero de lote**

Objetivo: Busca por numero de lote o por producto (lo consulta tambien el Inspector).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/lotes?q=L-2026-PROB-01" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_INSPECTOR"
```

Respuesta - **200 OK** (27 ms, 335 bytes):

```http
Content-Type: application/json
Content-Length: 335
X-Correlation-ID: 1bacd9bca73846d2
```

```json
{
  "datos": [
    {
      "id": 15,
      "numero_lote": "L-2026-PROB-01",
      "producto_id": 1,
      "producto": "Leche entera 1 L",
      "clasificacion_temperatura": "refrigerado",
      "proveedor_id": 1,
      "proveedor": "Lacteos del Norte",
      "unidades_vendidas": 24,
      "unidades_devueltas": 16,
      "devoluciones": 4,
      "tasa_pct": 66.67
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
- ok: encuentra el lote

## P4-TRZ-10

**lotes 200 solo con devoluciones y de un proveedor**

Objetivo: Filtros combinados.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/lotes?solo_con_devoluciones=true&proveedor_id=1" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (26 ms, 1353 bytes):

```http
Content-Type: application/json
Content-Length: 1353
X-Correlation-ID: 9f8f7b6d426349bf
```

```json
{
  "datos": [
    {
      "id": 15,
      "numero_lote": "L-2026-PROB-01",
      "producto_id": 1,
      "producto": "Leche entera 1 L",
      "clasificacion_temperatura": "refrigerado",
      "proveedor_id": 1,
      "proveedor": "Lacteos del Norte",
      "unidades_vendidas": 24,
      "unidades_devueltas": 16,
      "devoluciones": 4,
      "tasa_pct": 66.67
    },
    {
      "id": 4,
      "numero_lote": "L-2026-070",
      "producto_id": 3,
      "producto": "Queso panela 400 g",
      "clasificacion_temperatura": "refrigerado",
      "proveedor_id": 1,
      "proveedor": "Lacteos del Norte",
      "unidades_vendidas": 18,
      "unidades_devueltas": 7,
      "devoluciones": 7,
      "tasa_pct": 38.89
    },
    {
      "id": 1,
      "numero_lote": "L-2026-045",
      "producto_id": 1,
      "producto": "Leche entera 1 L",
      "clasificacion_temperatura": "refrigerado",
      "proveedor_id": 1,
      "proveedor": "Lacteos del Norte",
      "unidades_vendidas": 18,
      "unidades_devueltas": 5,
      "devoluciones": 5,
      "tasa_pct": 27.78
    },
    {
      "id": 2,
      "numero_lote": "L-2026-052",
      "producto_id": 1,
      "producto": "Leche entera 1 L",
      "clasificacion_temperatura": "refrigerado",
      "proveedor_id": 1,
      "proveedor": "Lacteos del Norte",
      "unidades_vendidas": 14,
      "unidades_devueltas": 3,
      "devoluciones": 3,
      "tasa_pct": 21.43
    },
    {
      "id": 3,
      "numero_lote": "L-2026-061",
      "producto_id": 2,
      "producto": "Yogurt natural 125 g",
      "clasificacion_temperatura": "refrigerado",
      "proveedor_id": 1,
      "proveedor": "Lacteos del Norte",
      "unidades_vendidas": 15,
      "unidades_devueltas": 2,
      "devoluciones": 2,
      "tasa_pct": 13.33
    }
  ],
  "paginacion": {
    "pagina": 1,
... (recortado: 5 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: todos con devoluciones
- ok: todos del proveedor

## P4-TRZ-11

**lotes 400 proveedor_id no numerico**

Objetivo: El filtro numerico se valida (RNF-11).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/lotes?proveedor_id=abc" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (10 ms, 142 bytes):

```http
Content-Type: application/json
Content-Length: 142
X-Correlation-ID: e8a07ce42c374cdd
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "proveedor_id debe ser un entero.",
    "detalles": null,
    "correlation_id": "e8a07ce42c374cdd"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-TRZ-12

**lotes 400 busqueda demasiado larga**

Objetivo: La busqueda tiene un maximo de 100 caracteres.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/lotes?q=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (8 ms, 154 bytes):

```http
Content-Type: application/json
Content-Length: 154
X-Correlation-ID: 36ae09577b214d0a
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "La busqueda no puede superar 100 caracteres.",
    "detalles": null,
    "correlation_id": "36ae09577b214d0a"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-TRZ-13

**lotes 200 con intento de inyeccion SQL**

Objetivo: Una busqueda con SQL se trata como texto (parametros ligados, RNF-11): no hay resultados y la tabla sigue ahi.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/lotes?q=%27%3B%20DROP%20TABLE%20lotes%3B--" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (24 ms, 77 bytes):

```http
Content-Type: application/json
Content-Length: 77
X-Correlation-ID: 37a8f0a03e9a4637
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

Efecto en PostgreSQL - la tabla de lotes sigue intacta:

```sql
SELECT count(*) AS lotes FROM lotes
```

```text
lotes
12
```

## P4-TRZ-14

**trazabilidad de un lote 200**

Objetivo: Todo lo de un lote: resumen de tasas, tiendas, series y el recorrido de cada devolucion (recoleccion, ruta, inspeccion, disposicion).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/lotes/15" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (40 ms, 4670 bytes):

```http
Content-Type: application/json
Content-Length: 4670
X-Correlation-ID: ea47179e43134ef7
```

```json
{
  "id": 15,
  "numero_lote": "L-2026-PROB-01",
  "fecha_fabricacion": "2026-09-20",
  "fecha_caducidad": "2026-11-30",
  "activo": true,
  "producto_id": 1,
  "sku": "LAC-001",
  "producto": "Leche entera 1 L",
  "clasificacion_temperatura": "refrigerado",
  "proveedor_id": 1,
  "proveedor": "Lacteos del Norte",
  "resumen": {
    "unidades_vendidas": 24,
    "unidades_devueltas": 16,
    "devoluciones": 4,
    "tasa_pct": 66.67,
    "tasa_global_pct": 28.86,
    "veces_promedio": 2.31
  },
  "tiendas": [
    {
      "id": 1,
      "tienda": "Tienda Centro",
      "ventas": 3,
      "unidades_vendidas": 18,
      "unidades_devueltas": 12.0,
      "tasa_pct": 66.67
    },
    {
      "id": 2,
      "tienda": "Tienda Valle Oriente",
      "ventas": 1,
      "unidades_vendidas": 6,
      "unidades_devueltas": 4.0,
      "tasa_pct": 66.67
    }
  ],
  "series": {
    "total": 24,
    "muestra": [
      {
        "numero_serie": "PROB01-0001",
        "vendida": true,
        "folio_venta": "VTA-PROB-01"
      },
      {
        "numero_serie": "PROB01-0002",
        "vendida": true,
        "folio_venta": "VTA-PROB-01"
      },
      {
        "numero_serie": "PROB01-0003",
        "vendida": true,
        "folio_venta": "VTA-PROB-01"
      },
      {
        "numero_serie": "PROB01-0004",
        "vendida": true,
        "folio_venta": "VTA-PROB-01"
      },
      {
        "numero_serie": "PROB01-0005",
        "vendida": true,
        "folio_venta": "VTA-PROB-01"
      },
      {
        "numero_serie": "PROB01-0006",
        "vendida": true,
        "folio_venta": "VTA-PROB-01"
... (recortado: 177 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: vendidas = la base
- ok: devueltas = la base
- ok: supera el doble del promedio
- ok: trae tiendas
- ok: cada devolucion trae su recorrido
- ok: recuerda que no confirma causalidad

Efecto en PostgreSQL - unidades vendidas y devueltas del lote, calculadas aparte:

```sql
SELECT (SELECT COALESCE(SUM(vd.cantidad), 0) FROM venta_detalle vd JOIN ventas v ON v.id = vd.venta_id WHERE vd.lote_id = 15 AND v.eliminado_en IS NULL) AS vendidas, (SELECT COALESCE(SUM(d.cantidad_devuelta), 0) FROM devoluciones d JOIN venta_detalle vd ON vd.id = d.venta_detalle_id WHERE vd.lote_id = 15 AND d.eliminado_en IS NULL) AS devueltas
```

```text
vendidas | devueltas
24 | 16
```

## P4-TRZ-15

**trazabilidad de un lote 200 XML**

Objetivo: La misma consulta en XML.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/lotes/15" \
  -H "Accept: application/xml" \
  -H "Authorization: Bearer $TOKEN_INSPECTOR"
```

Respuesta - **200 OK** (44 ms, 6814 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 6814
X-Correlation-ID: 37f4aaed8ad84549
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<lote><id>15</id><numero_lote>L-2026-PROB-01</numero_lote><fecha_fabricacion>2026-09-20</fecha_fabricacion><fecha_caducidad>2026-11-30</fecha_caducidad><activo>true</activo><producto_id>1</producto_id><sku>LAC-001</sku><producto>Leche entera 1 L</producto><clasificacion_temperatura>refrigerado</clasificacion_temperatura><proveedor_id>1</proveedor_id><proveedor>Lacteos del Norte</proveedor><resumen><unidades_vendidas>24</unidades_vendidas><unidades_devueltas>16</unidades_devueltas><devoluciones>4</devoluciones><tasa_pct>66.67</tasa_pct><tasa_global_pct>28.86</tasa_global_pct><veces_promedio>2.31</veces_promedio></resumen><tiendas><item><id>1</id><tienda>Tienda Centro</tienda><ventas>3</ventas><unidades_vendidas>18</unidades_vendidas><unidades_devueltas>12.0</unidades_devueltas><tasa_pct>66.67</tasa_pct></item><item><id>2</id><tienda>Tienda Valle Oriente</tienda><ventas>1</ventas><unidades_vendidas>6</unidades_vendidas><unidades_devueltas>4.0</unidades_devueltas><tasa_pct>66.67</tasa_pct></item></tiendas><series><total>24</total><muestra><item><numero_serie>PROB01-0001</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-01</folio_venta></item><item><numero_serie>PROB01-0002</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-01</folio_venta></item><item><numero_serie>PROB01-0003</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-01</folio_venta></item><item><numero_serie>PROB01-0004</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-01</folio_venta></item><item><numero_serie>PROB01-0005</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-01</folio_venta></item><item><numero_serie>PROB01-0006</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-01</folio_venta></item><item><numero_serie>PROB01-0007</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-02</folio_venta></item><item><numero_serie>PROB01-0008</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-02</folio_venta></item><item><numero_serie>PROB01-0009</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-02</folio_venta></item><item><numero_serie>PROB01-0010</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-02</folio_venta></item><item><numero_serie>PROB01-0011</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-02</folio_venta></item><item><numero_serie>PROB01-0012</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-02</folio_venta></item><item><numero_serie>PROB01-0013</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-03</folio_venta></item><item><numero_serie>PROB01-0014</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-03</folio_venta></item><item><numero_serie>PROB01-0015</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-03</folio_venta></item><item><numero_serie>PROB01-0016</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-03</folio_venta></item><item><numero_serie>PROB01-0017</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-03</folio_venta></item><item><numero_serie>PROB01-0018</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-03</folio_venta></item><item><numero_serie>PROB01-0019</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-04</folio_venta></item><item><numero_serie>PROB01-0020</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-04</folio_venta></item><item><numero_serie>PROB01-0021</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-04</folio_venta></item><item><numero_serie>PROB01-0022</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-04</folio_venta></item><item><numero_serie>PROB01-0023</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-04</folio_venta></item><item><numero_serie>PROB01-0024</numero_serie><vendida>true</vendida><folio_venta>VTA-PROB-04</folio_venta></item></muestra></series><devoluciones><item><devolucion_id>108</devolucion_id><folio_devolucion>DEV-2026-0108</folio_devolucion><estado>autorizada</estado><fecha_solicitud>2026-10-06T00:00:00+00:00</fecha_solicitud><cantidad_devuelta>4</cantidad_devuelta><motivo>Cadena de frio rota</motivo><tienda>Tienda Valle Oriente</tienda><folio_venta>VTA-PROB-04</folio_venta><numero_lote>L-2026-PROB-01</numero_lote><recorrido><ruta /><transportista /><estado_recoleccion /><fecha_recepcion /><resultado_inspeccion /><apto_para_inventario /><destino_disposicion /></recorrido></item><item><devolucion_id>107</devolucion_id><folio_devolucion>DEV-2026-0107</folio_devolucion><estado>en_inspeccion</estado><fecha_solicitud>2026-10-05T00:00:00+00:00</fecha_solicitud><cantidad_devuelta>4</cantidad_devuelta><motivo>Producto danado</motivo><tienda>Tienda Centro</tienda><folio_venta>VTA-PROB-03</folio_venta><numero_lote>L-2026-PROB-01</numero_lote><recorrido><ruta>Tienda Centro -&gt; Centro de Devoluciones Norte</ruta><transportista>Juan Perez</transportista><estado_recoleccion>completada</estado_recoleccion><fecha_recepcion>2026-11-22T01:16:01.466586+00:00</fecha_recepcion><resultado_inspeccion>no apto: cadena de frio rota</resultado_inspeccion><apto_para_inventario>false</apto_para_inventario><destino_disposicion /></recorrido></item><item><devolucion_id>106</devolucion_id><folio_devolucion>DEV-2026-0106</folio_devolucion><estado>cerrada</estado><fecha_solicitud>2026-10-04T00:00:00+00:00</fecha_solicitud><cantidad_devuelta>4</cantidad_devuelta><motivo>Cadena de frio rota</motivo><tienda>Tienda Centro</tienda><folio_venta>VTA-PROB-02</folio_venta><numero_lote>L-2026-PROB-01</numero_lote><recorrido><ruta>Tienda Centro -&gt; Centro de Devoluciones Norte</ruta><transportista>Juan Perez</transportista><estado_recoleccion>completada</estado_recoleccion><fecha_recepcion>2026-11-22T01:16:01.466586+00:00</fecha_recepcion><resultado_inspeccion>no apto: cadena de frio rota</resultado_inspeccion><apto_para_inventario>false</apto_para_inventario><destino_disposicion>desecho</destino_disposicion></recorrido></item><item><devolucion_id>105</devolucion_id><folio_devolucion>DEV-2026-0105</folio_devolucion><estado>cerrada</estado><fecha_solicitud>2026-10-03T00:00:00+00:00</fecha_solicitud><cantidad_devuelta>4</cantidad_devuelta><motivo>Cadena de frio rota</motivo><tienda>Tienda Centro</tienda><folio_venta>VTA-PROB-01</folio_venta><numero_lote>L-2026-PROB-01</numero_lote><recorrido><ruta>Tienda Centro -&gt; Centro de Devoluciones Norte</ruta><transportista>Juan Perez</transportista><estado_recoleccion>completada</estado_recoleccion><fecha_recepcion>2026-11-22T01:16:01.466586+00:00</fecha_recepcion><resultado_inspeccion>no apto: cadena de frio rota</resultado_inspeccion><apto_para_inventario>false</apto_para_inventario><destino_disposicion>desecho</destino_disposicion></recorrido></item></devoluciones><aviso>Patron para revision humana; no confirma causalidad (RN-09).</aviso></lote>
```

Verificaciones:

- ok: HTTP 200
- ok: es XML
- ok: raiz lote

## P4-TRZ-16

**trazabilidad de un lote 404**

Objetivo: Un lote inexistente responde 404.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/lotes/999999" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **404 NOT FOUND** (20 ms, 130 bytes):

```http
Content-Type: application/json
Content-Length: 130
X-Correlation-ID: b2d0e2dcb2b34583
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Lote inexistente.",
    "detalles": null,
    "correlation_id": "b2d0e2dcb2b34583"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-TRZ-17

**series 403 analista**

Objetivo: Dar de alta series es del Administrador.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8006/api/v1/trazabilidad/lotes/7/series" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"series":["EVID-P4-X"]}'
```

Respuesta - **403 FORBIDDEN** (9 ms, 222 bytes):

```http
Content-Type: application/json
Content-Length: 222
X-Correlation-ID: 03a9147123fc4b86
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
    "correlation_id": "03a9147123fc4b86"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-TRZ-18

**series 201 alta de tres**

Objetivo: Alta de numeros de serie de un lote (RF-05).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8006/api/v1/trazabilidad/lotes/7/series" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"series":["EVID-P4-001","EVID-P4-002","EVID-P4-003"]}'
```

Respuesta - **201 CREATED** (25 ms, 46 bytes):

```http
Content-Type: application/json
Content-Length: 46
X-Correlation-ID: 100209b1c0954f83
```

```json
{
  "lote_id": 7,
  "registradas": 3,
  "ya_existian": 0
}
```

Verificaciones:

- ok: HTTP 201
- ok: 3 registradas

Efecto en PostgreSQL - las series quedan sin venta:

```sql
SELECT numero_serie, lote_id, venta_detalle_id FROM series_producto WHERE numero_serie LIKE 'EVID-P4-%' ORDER BY 1
```

```text
numero_serie | lote_id | venta_detalle_id
EVID-P4-001 | 7 | 
EVID-P4-002 | 7 | 
EVID-P4-003 | 7 |
```

Efecto en PostgreSQL - la alta queda en la bitacora:

```sql
SELECT accion, entidad, detalle FROM bitacora WHERE accion = 'alta_series' ORDER BY id DESC LIMIT 1
```

```text
accion | entidad | detalle
alta_series | lotes | Series nuevas: 3
```

## P4-TRZ-19

**series 201 idempotente**

Objetivo: Repetir el envio no duplica ni falla: 0 nuevas, 3 que ya existian.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8006/api/v1/trazabilidad/lotes/7/series" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"series":["EVID-P4-001","EVID-P4-002","EVID-P4-003"]}'
```

Respuesta - **201 CREATED** (24 ms, 46 bytes):

```http
Content-Type: application/json
Content-Length: 46
X-Correlation-ID: 6fad9b66758e4909
```

```json
{
  "lote_id": 7,
  "registradas": 0,
  "ya_existian": 3
}
```

Verificaciones:

- ok: HTTP 201
- ok: 0 registradas
- ok: 3 ya existian

## P4-TRZ-20

**series 201 XML**

Objetivo: La misma alta en XML, validada contra su XSD (RF-31).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8006/api/v1/trazabilidad/lotes/7/series" \
  -H "Accept: application/xml" \
  -H "Content-Type: application/xml" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '<lote_series><series><item>EVID-P4-004</item></series></lote_series>'
```

Respuesta - **201 CREATED** (23 ms, 142 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 142
X-Correlation-ID: ea7f56f0d3e04427
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<lote_series><lote_id>7</lote_id><registradas>1</registradas><ya_existian>0</ya_existian></lote_series>
```

Verificaciones:

- ok: HTTP 201
- ok: 1 registrada

## P4-TRZ-21

**series 400 formato invalido**

Objetivo: Cada serie son 1 a 60 caracteres: letras, numeros, punto, guion.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8006/api/v1/trazabilidad/lotes/7/series" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"series":["serie con espacios","EVID-P4-OK"]}'
```

Respuesta - **400 BAD REQUEST** (10 ms, 208 bytes):

```http
Content-Type: application/json
Content-Length: 208
X-Correlation-ID: 9bbe0648e44744c8
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Series invalidas.",
    "detalles": [
      {
        "campo": "series[0]",
        "problema": "1 a 60 caracteres: letras, numeros, punto, guion"
      }
    ],
    "correlation_id": "9bbe0648e44744c8"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion
- ok: senala la posicion

## P4-TRZ-22

**series 400 repetidas en la lista**

Objetivo: Una lista con series repetidas se rechaza.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8006/api/v1/trazabilidad/lotes/7/series" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"series":["EVID-P4-R","EVID-P4-R"]}'
```

Respuesta - **400 BAD REQUEST** (10 ms, 141 bytes):

```http
Content-Type: application/json
Content-Length: 141
X-Correlation-ID: e19734d7040949ff
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "La lista trae series repetidas.",
    "detalles": null,
    "correlation_id": "e19734d7040949ff"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-TRZ-23

**series 404 lote inexistente**

Objetivo: No se dan de alta series en un lote que no existe.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8006/api/v1/trazabilidad/lotes/999999/series" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"series":["EVID-P4-Z"]}'
```

Respuesta - **404 NOT FOUND** (18 ms, 141 bytes):

```http
Content-Type: application/json
Content-Length: 141
X-Correlation-ID: 326fc450c6e0416d
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Lote inexistente o inactivo.",
    "detalles": null,
    "correlation_id": "326fc450c6e0416d"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-TRZ-24

**series 201 en el lote de la demo (para la linea saturada)**

Objetivo: Una serie del lote problematico, cuyas lineas de venta ya tienen todas sus series.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8006/api/v1/trazabilidad/lotes/15/series" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"series":["EVID-P4-SAT"]}'
```

Respuesta - **201 CREATED** (27 ms, 47 bytes):

```http
Content-Type: application/json
Content-Length: 47
X-Correlation-ID: 06111c8941a442cc
```

```json
{
  "lote_id": 15,
  "registradas": 1,
  "ya_existian": 0
}
```

Verificaciones:

- ok: HTTP 201
- ok: 1 registrada

## P4-TRZ-25

**series 201 en otro lote (prepara el conflicto)**

Objetivo: Una serie de otro lote, para probar que no se puede reasignar.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8006/api/v1/trazabilidad/lotes/1/series" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"series":["EVID-P4-AJENA"]}'
```

Respuesta - **201 CREATED** (29 ms, 46 bytes):

```http
Content-Type: application/json
Content-Length: 46
X-Correlation-ID: eb5cccc1f87540f6
```

```json
{
  "lote_id": 1,
  "registradas": 1,
  "ya_existian": 0
}
```

Verificaciones:

- ok: HTTP 201
- ok: 1 registrada

## P4-TRZ-26

**series 409 ya pertenece a otro lote**

Objetivo: Un numero de serie es unico: no se mueve de un lote a otro (RN-10).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8006/api/v1/trazabilidad/lotes/7/series" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"series":["EVID-P4-AJENA"]}'
```

Respuesta - **409 CONFLICT** (21 ms, 199 bytes):

```http
Content-Type: application/json
Content-Length: 199
X-Correlation-ID: 93597e7837174212
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "serie_duplicada",
    "mensaje": "Hay series que ya pertenecen a otro lote.",
    "detalles": [
      {
        "campo": "series",
        "problema": "EVID-P4-AJENA"
      }
    ],
    "correlation_id": "93597e7837174212"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo serie_duplicada

## P4-TRZ-27

**serie 200 en almacen**

Objetivo: Una serie sin venta esta en almacen: su recorrido termina en el lote.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/series/EVID-P4-001" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (21 ms, 255 bytes):

```http
Content-Type: application/json
Content-Length: 255
X-Correlation-ID: b8916cd938764b09
```

```json
{
  "numero_serie": "EVID-P4-001",
  "lote_id": 7,
  "activo": true,
  "numero_lote": "L-2026-125",
  "producto_id": 6,
  "sku": "AGR-003",
  "producto": "Frijol envasado 900 g",
  "proveedor_id": 2,
  "proveedor": "CampoVerde Agricola",
  "venta": null,
  "devoluciones": [],
  "estado": "en_almacen"
}
```

Verificaciones:

- ok: HTTP 200
- ok: estado en_almacen
- ok: sin venta
- ok: trae lote y proveedor

## P4-TRZ-28

**serie 400 formato invalido**

Objetivo: El numero de serie se valida antes de consultar (RNF-11).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/series/serie%20invalida" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (8 ms, 147 bytes):

```http
Content-Type: application/json
Content-Length: 147
X-Correlation-ID: bc43d8e41dc94598
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Numero de serie con formato invalido.",
    "detalles": null,
    "correlation_id": "bc43d8e41dc94598"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-TRZ-29

**serie 404 inexistente**

Objetivo: Una serie inexistente responde 404.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/series/NO-EXISTE-999" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **404 NOT FOUND** (20 ms, 131 bytes):

```http
Content-Type: application/json
Content-Length: 131
X-Correlation-ID: 45f8f3f201f54a50
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Serie inexistente.",
    "detalles": null,
    "correlation_id": "45f8f3f201f54a50"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-TRZ-30

**vincular serie 403 analista**

Objetivo: Ligar una serie a una venta es de Administrador y Operador de Almacen.

Comando:

```bash
curl -sS -i -X PATCH "http://$VM_HOST:8006/api/v1/trazabilidad/series/EVID-P4-001/venta" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"venta_detalle_id":62}'
```

Respuesta - **403 FORBIDDEN** (9 ms, 244 bytes):

```http
Content-Type: application/json
Content-Length: 244
X-Correlation-ID: 7847e64ebf864d74
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
        "Administrador",
        "Operador de Almacen"
      ]
    },
    "correlation_id": "7847e64ebf864d74"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-TRZ-31

**vincular serie 400 id invalido**

Objetivo: El id de la linea es un entero positivo.

Comando:

```bash
curl -sS -i -X PATCH "http://$VM_HOST:8006/api/v1/trazabilidad/series/EVID-P4-001/venta" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ALMACEN" \
  -d '{"venta_detalle_id":"uno"}'
```

Respuesta - **400 BAD REQUEST** (9 ms, 155 bytes):

```http
Content-Type: application/json
Content-Length: 155
X-Correlation-ID: e3d8bbac7ace45e6
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "venta_detalle_id debe ser un entero positivo.",
    "detalles": null,
    "correlation_id": "e3d8bbac7ace45e6"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-TRZ-32

**vincular serie 404 linea inexistente**

Objetivo: La linea de venta debe existir.

Comando:

```bash
curl -sS -i -X PATCH "http://$VM_HOST:8006/api/v1/trazabilidad/series/EVID-P4-001/venta" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ALMACEN" \
  -d '{"venta_detalle_id":999999}'
```

Respuesta - **404 NOT FOUND** (19 ms, 140 bytes):

```http
Content-Type: application/json
Content-Length: 140
X-Correlation-ID: 1344465fdc4241ca
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Linea de venta inexistente.",
    "detalles": null,
    "correlation_id": "1344465fdc4241ca"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-TRZ-33

**vincular serie 409 linea de otro lote**

Objetivo: Una serie solo se liga a una venta de su propio lote (RN-10).

Comando:

```bash
curl -sS -i -X PATCH "http://$VM_HOST:8006/api/v1/trazabilidad/series/EVID-P4-002/venta" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ALMACEN" \
  -d '{"venta_detalle_id":61}'
```

Respuesta - **409 CONFLICT** (19 ms, 147 bytes):

```http
Content-Type: application/json
Content-Length: 147
X-Correlation-ID: bb5a574e8e844e27
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "lote_distinto",
    "mensaje": "La linea de venta es de otro lote.",
    "detalles": null,
    "correlation_id": "bb5a574e8e844e27"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo lote_distinto

## P4-TRZ-34

**vincular serie 409 linea sin cupo**

Objetivo: No hay mas series que unidades vendidas en una linea (RN-10): esa linea ya tiene todas las suyas.

Comando:

```bash
curl -sS -i -X PATCH "http://$VM_HOST:8006/api/v1/trazabilidad/series/EVID-P4-SAT/venta" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ALMACEN" \
  -d '{"venta_detalle_id":153}'
```

Respuesta - **409 CONFLICT** (21 ms, 158 bytes):

```http
Content-Type: application/json
Content-Length: 158
X-Correlation-ID: ae678b3aa55a4b3c
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "sin_unidades",
    "mensaje": "La linea ya tiene tantas series como unidades.",
    "detalles": null,
    "correlation_id": "ae678b3aa55a4b3c"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo sin_unidades

## P4-TRZ-35

**vincular serie 200 por el Operador de Almacen**

Objetivo: La serie sale en una venta concreta; de ahi se llega a la tienda y a la devolucion.

Comando:

```bash
curl -sS -i -X PATCH "http://$VM_HOST:8006/api/v1/trazabilidad/series/EVID-P4-001/venta" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ALMACEN" \
  -d '{"venta_detalle_id":62}'
```

Respuesta - **200 OK** (23 ms, 53 bytes):

```http
Content-Type: application/json
Content-Length: 53
X-Correlation-ID: feac40bef5eb4425
```

```json
{
  "numero_serie": "EVID-P4-001",
  "venta_detalle_id": 62
}
```

Verificaciones:

- ok: HTTP 200
- ok: queda ligada

Efecto en PostgreSQL - la serie ligada:

```sql
SELECT numero_serie, venta_detalle_id FROM series_producto WHERE numero_serie = 'EVID-P4-001'
```

```text
numero_serie | venta_detalle_id
EVID-P4-001 | 62
```

Efecto en PostgreSQL - la vinculacion en la bitacora:

```sql
SELECT accion, entidad, detalle FROM bitacora WHERE accion = 'serie_vendida' ORDER BY id DESC LIMIT 1
```

```text
accion | entidad | detalle
serie_vendida | series_producto | Serie EVID-P4-001 ligada a la linea 62
```

## P4-TRZ-36

**vincular serie 200 idempotente**

Objetivo: Repetir la misma vinculacion no cambia nada.

Comando:

```bash
curl -sS -i -X PATCH "http://$VM_HOST:8006/api/v1/trazabilidad/series/EVID-P4-001/venta" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"venta_detalle_id":62}'
```

Respuesta - **200 OK** (19 ms, 72 bytes):

```http
Content-Type: application/json
Content-Length: 72
X-Correlation-ID: 018a2498504d458b
```

```json
{
  "numero_serie": "EVID-P4-001",
  "venta_detalle_id": 62,
  "sin_cambios": true
}
```

Verificaciones:

- ok: HTTP 200
- ok: sin cambios

## P4-TRZ-37

**vincular serie 200 XML**

Objetivo: La misma vinculacion en XML.

Comando:

```bash
curl -sS -i -X PATCH "http://$VM_HOST:8006/api/v1/trazabilidad/series/EVID-P4-003/venta" \
  -H "Accept: application/xml" \
  -H "Content-Type: application/xml" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '<serie_venta><venta_detalle_id>62</venta_detalle_id></serie_venta>'
```

Respuesta - **200 OK** (25 ms, 133 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 133
X-Correlation-ID: e9782bd3be31418f
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<serie><numero_serie>EVID-P4-003</numero_serie><venta_detalle_id>62</venta_detalle_id></serie>
```

Verificaciones:

- ok: HTTP 200
- ok: es XML

## P4-TRZ-38

**vincular serie 409 ya ligada a otra venta**

Objetivo: Una serie vendida no se reasigna a otra venta.

Comando:

```bash
curl -sS -i -X PATCH "http://$VM_HOST:8006/api/v1/trazabilidad/series/EVID-P4-001/venta" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"venta_detalle_id":67}'
```

Respuesta - **409 CONFLICT** (21 ms, 150 bytes):

```http
Content-Type: application/json
Content-Length: 150
X-Correlation-ID: 7134997d99d34a81
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "serie_vendida",
    "mensaje": "La serie ya esta ligada a otra venta.",
    "detalles": null,
    "correlation_id": "7134997d99d34a81"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo serie_vendida

## P4-TRZ-39

**serie 200 devuelta: recorrido completo**

Objetivo: Del numero de serie a la tienda, la venta y todo el recorrido de su devolucion: la trazabilidad de punta a punta (RF-05).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/series/EVID-P4-001" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_INSPECTOR"
```

Respuesta - **200 OK** (35 ms, 881 bytes):

```http
Content-Type: application/json
Content-Length: 881
X-Correlation-ID: 8f896e364ff0431f
```

```json
{
  "numero_serie": "EVID-P4-001",
  "lote_id": 7,
  "activo": true,
  "numero_lote": "L-2026-125",
  "producto_id": 6,
  "sku": "AGR-003",
  "producto": "Frijol envasado 900 g",
  "proveedor_id": 2,
  "proveedor": "CampoVerde Agricola",
  "venta": {
    "venta_id": 26,
    "folio_venta": "VTA-2026-0001",
    "fecha_venta": "2026-08-09",
    "tienda_id": 3,
    "tienda": "Tienda Cumbres"
  },
  "devoluciones": [
    {
      "devolucion_id": 16,
      "folio_devolucion": "DEV-2026-0016",
      "estado": "en_recoleccion",
      "fecha_solicitud": "2026-09-06T23:20:35.290510+00:00",
      "cantidad_devuelta": 1,
      "motivo": "Cadena de frio rota",
      "tienda": "Tienda Cumbres",
      "folio_venta": "VTA-2026-0001",
      "numero_lote": "L-2026-125",
      "recorrido": {
        "ruta": "Tienda Valle Oriente -> Centro de Devoluciones Norte",
        "transportista": "Maria Gonzalez",
        "estado_recoleccion": "en_transito",
        "fecha_recepcion": null,
        "resultado_inspeccion": null,
        "apto_para_inventario": null,
        "destino_disposicion": null
      }
    }
  ],
  "estado": "devuelta"
}
```

Verificaciones:

- ok: HTTP 200
- ok: estado devuelta
- ok: trae la venta y la tienda
- ok: trae el recorrido de la devolucion

## P4-TRZ-40

**serie 200 de otra serie ligada**

Objetivo: Una serie ligada a una venta sin devoluciones esta vendida (o devuelta si esa linea ya tuvo una).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/series/EVID-P4-003" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (35 ms, 881 bytes):

```http
Content-Type: application/json
Content-Length: 881
X-Correlation-ID: 02686af9e6e745dd
```

```json
{
  "numero_serie": "EVID-P4-003",
  "lote_id": 7,
  "activo": true,
  "numero_lote": "L-2026-125",
  "producto_id": 6,
  "sku": "AGR-003",
  "producto": "Frijol envasado 900 g",
  "proveedor_id": 2,
  "proveedor": "CampoVerde Agricola",
  "venta": {
    "venta_id": 26,
    "folio_venta": "VTA-2026-0001",
    "fecha_venta": "2026-08-09",
    "tienda_id": 3,
    "tienda": "Tienda Cumbres"
  },
  "devoluciones": [
    {
      "devolucion_id": 16,
      "folio_devolucion": "DEV-2026-0016",
      "estado": "en_recoleccion",
      "fecha_solicitud": "2026-09-06T23:20:35.290510+00:00",
      "cantidad_devuelta": 1,
      "motivo": "Cadena de frio rota",
      "tienda": "Tienda Cumbres",
      "folio_venta": "VTA-2026-0001",
      "numero_lote": "L-2026-125",
      "recorrido": {
        "ruta": "Tienda Valle Oriente -> Centro de Devoluciones Norte",
        "transportista": "Maria Gonzalez",
        "estado_recoleccion": "en_transito",
        "fecha_recepcion": null,
        "resultado_inspeccion": null,
        "apto_para_inventario": null,
        "destino_disposicion": null
      }
    }
  ],
  "estado": "devuelta"
}
```

Verificaciones:

- ok: HTTP 200
- ok: estado vendida o devuelta
- ok: trae la venta

## P4-TRZ-41

**tasas 200 por proveedor**

Objetivo: Tasa = unidades devueltas entre vendidas, base del analisis causal (RF-23, RF-24).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/tasas?por=proveedor" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (25 ms, 768 bytes):

```http
Content-Type: application/json
Content-Length: 768
X-Correlation-ID: c25a499758b94b27
```

```json
{
  "por": "proveedor",
  "medida": "unidades_devueltas/unidades_vendidas",
  "tasa_promedio_pct": 28.86,
  "datos": [
    {
      "id": 1,
      "etiqueta": "Lacteos del Norte",
      "unidades_vendidas": 89,
      "unidades_devueltas": 33.0,
      "devoluciones": 21.0,
      "tasa_pct": 37.08,
      "veces_promedio": 1.28
    },
    {
      "id": 2,
      "etiqueta": "CampoVerde Agricola",
      "unidades_vendidas": 42,
      "unidades_devueltas": 11.0,
      "devoluciones": 11.0,
      "tasa_pct": 26.19,
      "veces_promedio": 0.91
    },
    {
      "id": 4,
      "etiqueta": "Abarrotes Monterrey",
      "unidades_vendidas": 54,
      "unidades_devueltas": 11.0,
      "devoluciones": 11.0,
      "tasa_pct": 20.37,
      "veces_promedio": 0.71
    },
    {
      "id": 3,
      "etiqueta": "Avicola Real",
      "unidades_vendidas": 16,
      "unidades_devueltas": 3.0,
      "devoluciones": 3.0,
      "tasa_pct": 18.75,
      "veces_promedio": 0.65
    }
  ],
  "interpretacion": "Patrones para revision humana; no confirman causalidad."
}
```

Verificaciones:

- ok: HTTP 200
- ok: ordenado por tasa
- ok: trae promedio y advertencia

## P4-TRZ-42

**tasas 200 por tienda**

Objetivo: Tasa = unidades devueltas entre vendidas, base del analisis causal (RF-23, RF-24).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/tasas?por=tienda" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (40 ms, 616 bytes):

```http
Content-Type: application/json
Content-Length: 616
X-Correlation-ID: 0ffcb844d5d046ce
```

```json
{
  "por": "tienda",
  "medida": "unidades_devueltas/unidades_vendidas",
  "tasa_promedio_pct": 28.86,
  "datos": [
    {
      "id": 2,
      "etiqueta": "Tienda Valle Oriente",
      "unidades_vendidas": 51,
      "unidades_devueltas": 19.0,
      "devoluciones": 16.0,
      "tasa_pct": 37.25,
      "veces_promedio": 1.29
    },
    {
      "id": 1,
      "etiqueta": "Tienda Centro",
      "unidades_vendidas": 57,
      "unidades_devueltas": 19.0,
      "devoluciones": 10.0,
      "tasa_pct": 33.33,
      "veces_promedio": 1.15
    },
    {
      "id": 3,
      "etiqueta": "Tienda Cumbres",
      "unidades_vendidas": 93,
      "unidades_devueltas": 20.0,
      "devoluciones": 20.0,
      "tasa_pct": 21.51,
      "veces_promedio": 0.75
    }
  ],
  "interpretacion": "Patrones para revision humana; no confirman causalidad."
}
```

Verificaciones:

- ok: HTTP 200
- ok: ordenado por tasa
- ok: trae promedio y advertencia

## P4-TRZ-43

**tasas 200 por producto**

Objetivo: Tasa = unidades devueltas entre vendidas, base del analisis causal (RF-23, RF-24).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/tasas?por=producto" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (42 ms, 1655 bytes):

```http
Content-Type: application/json
Content-Length: 1655
X-Correlation-ID: ada6af7c142d49d9
```

```json
{
  "por": "producto",
  "medida": "unidades_devueltas/unidades_vendidas",
  "tasa_promedio_pct": 28.86,
  "datos": [
    {
      "id": 1,
      "etiqueta": "Leche entera 1 L",
      "unidades_vendidas": 56,
      "unidades_devueltas": 24.0,
      "devoluciones": 12.0,
      "tasa_pct": 42.86,
      "veces_promedio": 1.49
    },
    {
      "id": 5,
      "etiqueta": "Tomate saladette 1 kg",
      "unidades_vendidas": 14,
      "unidades_devueltas": 6.0,
      "devoluciones": 6.0,
      "tasa_pct": 42.86,
      "veces_promedio": 1.49
    },
    {
      "id": 3,
      "etiqueta": "Queso panela 400 g",
      "unidades_vendidas": 18,
      "unidades_devueltas": 7.0,
      "devoluciones": 7.0,
      "tasa_pct": 38.89,
      "veces_promedio": 1.35
    },
    {
      "id": 8,
      "etiqueta": "Arroz blanco 1 kg",
      "unidades_vendidas": 15,
      "unidades_devueltas": 5.0,
      "devoluciones": 5.0,
      "tasa_pct": 33.33,
      "veces_promedio": 1.15
    },
    {
      "id": 10,
      "etiqueta": "Galletas surtidas 600 g",
      "unidades_vendidas": 16,
      "unidades_devueltas": 4.0,
      "devoluciones": 4.0,
      "tasa_pct": 25.0,
      "veces_promedio": 0.87
    },
    {
      "id": 6,
      "etiqueta": "Frijol envasado 900 g",
      "unidades_vendidas": 14,
      "unidades_devueltas": 3.0,
      "devoluciones": 3.0,
      "tasa_pct": 21.43,
      "veces_promedio": 0.74
    },
    {
      "id": 7,
      "etiqueta": "Pechuga de pollo 1 kg",
      "unidades_vendidas": 16,
      "unidades_devueltas": 3.0,
      "devoluciones": 3.0,
      "tasa_pct": 18.75,
      "veces_promedio": 0.65
    },
    {
      "id": 4,
... (recortado: 28 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: ordenado por tasa
- ok: trae promedio y advertencia

## P4-TRZ-44

**tasas 200 por lote**

Objetivo: Tasa = unidades devueltas entre vendidas, base del analisis causal (RF-23, RF-24).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/tasas?por=lote" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (38 ms, 2102 bytes):

```http
Content-Type: application/json
Content-Length: 2102
X-Correlation-ID: a6e797581bf04b83
```

```json
{
  "por": "lote",
  "medida": "unidades_devueltas/unidades_vendidas",
  "tasa_promedio_pct": 28.86,
  "datos": [
    {
      "id": 15,
      "etiqueta": "L-2026-PROB-01 (Leche entera 1 L)",
      "unidades_vendidas": 24,
      "unidades_devueltas": 16.0,
      "devoluciones": 4.0,
      "tasa_pct": 66.67,
      "veces_promedio": 2.31
    },
    {
      "id": 6,
      "etiqueta": "L-2026-118 (Tomate saladette 1 kg)",
      "unidades_vendidas": 14,
      "unidades_devueltas": 6.0,
      "devoluciones": 6.0,
      "tasa_pct": 42.86,
      "veces_promedio": 1.49
    },
    {
      "id": 4,
      "etiqueta": "L-2026-070 (Queso panela 400 g)",
      "unidades_vendidas": 18,
      "unidades_devueltas": 7.0,
      "devoluciones": 7.0,
      "tasa_pct": 38.89,
      "veces_promedio": 1.35
    },
    {
      "id": 9,
      "etiqueta": "L-2026-301 (Arroz blanco 1 kg)",
      "unidades_vendidas": 15,
      "unidades_devueltas": 5.0,
      "devoluciones": 5.0,
      "tasa_pct": 33.33,
      "veces_promedio": 1.15
    },
    {
      "id": 1,
      "etiqueta": "L-2026-045 (Leche entera 1 L)",
      "unidades_vendidas": 18,
      "unidades_devueltas": 5.0,
      "devoluciones": 5.0,
      "tasa_pct": 27.78,
      "veces_promedio": 0.96
    },
    {
      "id": 11,
      "etiqueta": "L-2026-312 (Galletas surtidas 600 g)",
      "unidades_vendidas": 16,
      "unidades_devueltas": 4.0,
      "devoluciones": 4.0,
      "tasa_pct": 25.0,
      "veces_promedio": 0.87
    },
    {
      "id": 2,
      "etiqueta": "L-2026-052 (Leche entera 1 L)",
      "unidades_vendidas": 14,
      "unidades_devueltas": 3.0,
      "devoluciones": 3.0,
      "tasa_pct": 21.43,
      "veces_promedio": 0.74
    },
    {
      "id": 7,
... (recortado: 46 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: ordenado por tasa
- ok: trae promedio y advertencia

## P4-TRZ-45

**tasas 200 por ruta**

Objetivo: Por ruta se mide el dano: inspecciones no aptas entre inspeccionadas, porque no existe 'vendido por ruta'.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/tasas?por=ruta" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (37 ms, 823 bytes):

```http
Content-Type: application/json
Content-Length: 823
X-Correlation-ID: 05df141579354345
```

```json
{
  "por": "ruta",
  "medida": "inspecciones_no_aptas/inspecciones_realizadas",
  "tasa_promedio_pct": 68.42,
  "datos": [
    {
      "id": 1,
      "etiqueta": "Tienda Centro -> Centro de Devoluciones Norte",
      "recolecciones": 7,
      "inspeccionadas": 6,
      "con_dano": 5,
      "tasa_pct": 83.33,
      "veces_promedio": 1.22
    },
    {
      "id": 3,
      "etiqueta": "Tienda Cumbres -> Centro de Devoluciones Norte",
      "recolecciones": 7,
      "inspeccionadas": 4,
      "con_dano": 3,
      "tasa_pct": 75.0,
      "veces_promedio": 1.1
    },
    {
      "id": 4,
      "etiqueta": "Domicilio del cliente -> Centro de Devoluciones Norte",
      "recolecciones": 10,
      "inspeccionadas": 7,
      "con_dano": 5,
      "tasa_pct": 71.43,
      "veces_promedio": 1.04
    },
    {
      "id": 2,
      "etiqueta": "Tienda Valle Oriente -> Centro de Devoluciones Norte",
      "recolecciones": 4,
      "inspeccionadas": 2,
      "con_dano": 0,
      "tasa_pct": 0.0,
      "veces_promedio": 0.0
    }
  ],
  "interpretacion": "Patrones para revision humana; no confirman causalidad."
}
```

Verificaciones:

- ok: HTTP 200
- ok: ordenado por tasa
- ok: trae promedio y advertencia

## P4-TRZ-46

**tasas 200: el lote problematico contra la base**

Objetivo: La fila del lote de la demo coincide con lo que dice la base.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/tasas?por=lote" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (41 ms, 2102 bytes):

```http
Content-Type: application/json
Content-Length: 2102
X-Correlation-ID: 7a0a925158794349
```

```json
{
  "por": "lote",
  "medida": "unidades_devueltas/unidades_vendidas",
  "tasa_promedio_pct": 28.86,
  "datos": [
    {
      "id": 15,
      "etiqueta": "L-2026-PROB-01 (Leche entera 1 L)",
      "unidades_vendidas": 24,
      "unidades_devueltas": 16.0,
      "devoluciones": 4.0,
      "tasa_pct": 66.67,
      "veces_promedio": 2.31
    },
    {
      "id": 6,
      "etiqueta": "L-2026-118 (Tomate saladette 1 kg)",
      "unidades_vendidas": 14,
      "unidades_devueltas": 6.0,
      "devoluciones": 6.0,
      "tasa_pct": 42.86,
      "veces_promedio": 1.49
    },
    {
      "id": 4,
      "etiqueta": "L-2026-070 (Queso panela 400 g)",
      "unidades_vendidas": 18,
      "unidades_devueltas": 7.0,
      "devoluciones": 7.0,
      "tasa_pct": 38.89,
      "veces_promedio": 1.35
    },
    {
      "id": 9,
      "etiqueta": "L-2026-301 (Arroz blanco 1 kg)",
      "unidades_vendidas": 15,
      "unidades_devueltas": 5.0,
      "devoluciones": 5.0,
      "tasa_pct": 33.33,
      "veces_promedio": 1.15
    },
    {
      "id": 1,
      "etiqueta": "L-2026-045 (Leche entera 1 L)",
      "unidades_vendidas": 18,
      "unidades_devueltas": 5.0,
      "devoluciones": 5.0,
      "tasa_pct": 27.78,
      "veces_promedio": 0.96
    },
    {
      "id": 11,
      "etiqueta": "L-2026-312 (Galletas surtidas 600 g)",
      "unidades_vendidas": 16,
      "unidades_devueltas": 4.0,
      "devoluciones": 4.0,
      "tasa_pct": 25.0,
      "veces_promedio": 0.87
    },
    {
      "id": 2,
      "etiqueta": "L-2026-052 (Leche entera 1 L)",
      "unidades_vendidas": 14,
      "unidades_devueltas": 3.0,
      "devoluciones": 3.0,
      "tasa_pct": 21.43,
      "veces_promedio": 0.74
    },
    {
      "id": 7,
... (recortado: 46 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: devueltas = la base
- ok: al menos el doble del promedio

## P4-TRZ-47

**tasas 200 en un periodo**

Objetivo: Los indicadores se acotan por periodo.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/tasas?por=proveedor&desde=2026-01-01&hasta=2026-12-31" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR"
```

Respuesta - **200 OK** (32 ms, 768 bytes):

```http
Content-Type: application/json
Content-Length: 768
X-Correlation-ID: 7d42955ca2fd487e
```

```json
{
  "por": "proveedor",
  "medida": "unidades_devueltas/unidades_vendidas",
  "tasa_promedio_pct": 28.86,
  "datos": [
    {
      "id": 1,
      "etiqueta": "Lacteos del Norte",
      "unidades_vendidas": 89,
      "unidades_devueltas": 33.0,
      "devoluciones": 21.0,
      "tasa_pct": 37.08,
      "veces_promedio": 1.28
    },
    {
      "id": 2,
      "etiqueta": "CampoVerde Agricola",
      "unidades_vendidas": 42,
      "unidades_devueltas": 11.0,
      "devoluciones": 11.0,
      "tasa_pct": 26.19,
      "veces_promedio": 0.91
    },
    {
      "id": 4,
      "etiqueta": "Abarrotes Monterrey",
      "unidades_vendidas": 54,
      "unidades_devueltas": 11.0,
      "devoluciones": 11.0,
      "tasa_pct": 20.37,
      "veces_promedio": 0.71
    },
    {
      "id": 3,
      "etiqueta": "Avicola Real",
      "unidades_vendidas": 16,
      "unidades_devueltas": 3.0,
      "devoluciones": 3.0,
      "tasa_pct": 18.75,
      "veces_promedio": 0.65
    }
  ],
  "interpretacion": "Patrones para revision humana; no confirman causalidad."
}
```

Verificaciones:

- ok: HTTP 200
- ok: trae datos

## P4-TRZ-48

**tasas 200 XML**

Objetivo: Las tasas responden XML (RF-31).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/tasas?por=tienda" \
  -H "Accept: application/xml" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (25 ms, 996 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 996
X-Correlation-ID: 1517f8fe620f4432
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<tasas><por>tienda</por><medida>unidades_devueltas/unidades_vendidas</medida><tasa_promedio_pct>28.86</tasa_promedio_pct><datos><item><id>2</id><etiqueta>Tienda Valle Oriente</etiqueta><unidades_vendidas>51</unidades_vendidas><unidades_devueltas>19.0</unidades_devueltas><devoluciones>16.0</devoluciones><tasa_pct>37.25</tasa_pct><veces_promedio>1.29</veces_promedio></item><item><id>1</id><etiqueta>Tienda Centro</etiqueta><unidades_vendidas>57</unidades_vendidas><unidades_devueltas>19.0</unidades_devueltas><devoluciones>10.0</devoluciones><tasa_pct>33.33</tasa_pct><veces_promedio>1.15</veces_promedio></item><item><id>3</id><etiqueta>Tienda Cumbres</etiqueta><unidades_vendidas>93</unidades_vendidas><unidades_devueltas>20.0</unidades_devueltas><devoluciones>20.0</devoluciones><tasa_pct>21.51</tasa_pct><veces_promedio>0.75</veces_promedio></item></datos><interpretacion>Patrones para revision humana; no confirman causalidad.</interpretacion></tasas>
```

Verificaciones:

- ok: HTTP 200
- ok: es XML
- ok: raiz tasas

## P4-TRZ-49

**tasas 400 dimension invalida**

Objetivo: La dimension sale de una lista cerrada (RNF-11).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/tasas?por=planeta" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (10 ms, 171 bytes):

```http
Content-Type: application/json
Content-Length: 171
X-Correlation-ID: 4d5b4b6d38ae4f54
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "por debe ser una de: proveedor, tienda, producto, lote, ruta.",
    "detalles": null,
    "correlation_id": "4d5b4b6d38ae4f54"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-TRZ-50

**tasas 400 fecha invalida**

Objetivo: Las fechas son AAAA-MM-DD.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/tasas?desde=ayer" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (8 ms, 146 bytes):

```http
Content-Type: application/json
Content-Length: 146
X-Correlation-ID: bbca1c4bb9c64023
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "desde debe tener formato AAAA-MM-DD.",
    "detalles": null,
    "correlation_id": "bbca1c4bb9c64023"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-TRZ-51

**tasas 400 hasta antes de desde**

Objetivo: Un periodo al reves se rechaza.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8006/api/v1/trazabilidad/tasas?desde=2026-06-01&hasta=2026-01-01" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (8 ms, 145 bytes):

```http
Content-Type: application/json
Content-Length: 145
X-Correlation-ID: a9f99fc1836e4625
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "hasta no puede ser menor que desde.",
    "detalles": null,
    "correlation_id": "a9f99fc1836e4625"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## Limpieza

Al terminar se borraron los datos que creo esta corrida, para no dejar basura en la base de demostracion. **La bitacora no se toca**: es de solo agregar (migracion 045).

