# Evidencia con curl - `clasificacion-motivos`

Ejecutada en la VM el 2026-11-22 18:01 UTC con `scripts/evidencias/ejecutar.py clasificacion` (commit `f704f96`).
Casos: **50**, correctos: **50**, con falla: **0**. Los tokens y la contrasena de demo estan ocultos; la IP de la VM se muestra como `$VM_HOST`.

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
| [P4-CLA-01](#p4-cla-01) | correcto | 200 | salud 200 JSON |
| [P4-CLA-02](#p4-cla-02) | correcto | 200 | salud 200 XML |
| [P4-CLA-03](#p4-cla-03) | correcto | 200 | Swagger: documentacion de la API |
| [P4-CLA-04](#p4-cla-04) | correcto | 200 | Swagger: especificacion OpenAPI |
| [P4-CLA-05](#p4-cla-05) | correcto | 200 | contrato XSD publicado |
| [P4-CLA-06](#p4-cla-06) | correcto | 401 | sin token: 401 |
| [P4-CLA-07](#p4-cla-07) | correcto | 401 | token invalido: 401 |
| [P4-CLA-08](#p4-cla-08) | correcto | 200 | categorias 200 |
| [P4-CLA-09](#p4-cla-09) | correcto | 403 | categorias 403 cliente |
| [P4-CLA-10](#p4-cla-10) | correcto | 200 | submotivos 200 paginado |
| [P4-CLA-11](#p4-cla-11) | correcto | 200 | submotivos 200 filtrado por categoria |
| [P4-CLA-12](#p4-cla-12) | correcto | 200 | submotivos 200 XML |
| [P4-CLA-13](#p4-cla-13) | correcto | 400 | submotivos 400 filtro invalido |
| [P4-CLA-14](#p4-cla-14) | correcto | 200 | submotivo 200 con su historial |
| [P4-CLA-15](#p4-cla-15) | correcto | 404 | submotivo 404 |
| [P4-CLA-16](#p4-cla-16) | correcto | 201 | alta 201 JSON (administrador) |
| [P4-CLA-17](#p4-cla-17) | correcto | 201 | alta 201 XML (supervisor) |
| [P4-CLA-18](#p4-cla-18) | correcto | 400 | alta 400 codigo con formato invalido |
| [P4-CLA-19](#p4-cla-19) | correcto | 400 | alta 400 XML que no cumple el XSD |
| [P4-CLA-20](#p4-cla-20) | correcto | 409 | alta 409 codigo duplicado |
| [P4-CLA-21](#p4-cla-21) | correcto | 409 | alta 409 categoria inexistente |
| [P4-CLA-22](#p4-cla-22) | correcto | 403 | alta 403 analista |
| [P4-CLA-23](#p4-cla-23) | correcto | 200 | edicion 200: crea la version 2 |
| [P4-CLA-24](#p4-cla-24) | correcto | 200 | edicion 200: sin cambios no crea version |
| [P4-CLA-25](#p4-cla-25) | correcto | 400 | edicion 400 sin explicar el cambio |
| [P4-CLA-26](#p4-cla-26) | correcto | 404 | edicion 404 |
| [P4-CLA-27](#p4-cla-27) | correcto | 200 | estado 200: desactivar crea la version 3 |
| [P4-CLA-28](#p4-cla-28) | correcto | 400 | estado 400 valor invalido |
| [P4-CLA-29](#p4-cla-29) | correcto | 404 | estado 404 |
| [P4-CLA-30](#p4-cla-30) | correcto | 200 | sugerencia 200 (cliente) |
| [P4-CLA-31](#p4-cla-31) | correcto | 200 | sugerencia 200 XML |
| [P4-CLA-32](#p4-cla-32) | correcto | 200 | sugerencia 200: sin coincidencias no inventa |
| [P4-CLA-33](#p4-cla-33) | correcto | 400 | sugerencia 400 descripcion corta |
| [P4-CLA-34](#p4-cla-34) | correcto | 401 | sugerencia 401 sin token |
| [P4-CLA-35](#p4-cla-35) | correcto | 201 | clasificacion 201: queda pendiente |
| [P4-CLA-36](#p4-cla-36) | correcto | 409 | clasificacion 409: ya hay una pendiente |
| [P4-CLA-37](#p4-cla-37) | correcto | 404 | clasificacion 404 devolucion inexistente |
| [P4-CLA-38](#p4-cla-38) | correcto | 400 | clasificacion 400 identificador invalido |
| [P4-CLA-39](#p4-cla-39) | correcto | 403 | clasificacion 403 cliente |
| [P4-CLA-40](#p4-cla-40) | correcto | 200 | cola 200: pendientes de revision |
| [P4-CLA-41](#p4-cla-41) | correcto | 400 | cola 400 estado desconocido |
| [P4-CLA-42](#p4-cla-42) | correcto | 400 | revision 400: corregir sin comentario ni submotivo |
| [P4-CLA-43](#p4-cla-43) | correcto | 403 | revision 403 cliente |
| [P4-CLA-44](#p4-cla-44) | correcto | 200 | revision 200: confirmar |
| [P4-CLA-45](#p4-cla-45) | correcto | 409 | revision 409: ya fue revisada |
| [P4-CLA-46](#p4-cla-46) | correcto | 404 | revision 404 |
| [P4-CLA-47](#p4-cla-47) | correcto | 201 | clasificacion 201: nueva sugerencia tras la revision |
| [P4-CLA-48](#p4-cla-48) | correcto | 200 | revision 200 XML: corregir |
| [P4-CLA-49](#p4-cla-49) | correcto | 201 | clasificacion 201: tercera sugerencia |
| [P4-CLA-50](#p4-cla-50) | correcto | 200 | revision 200: descartar |

## P4-CLA-01

**salud 200 JSON**

Objetivo: El servicio informa su estado y el de PostgreSQL y Redis (RF-32).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8010/health" \
  -H "Accept: application/json"
```

Respuesta - **200 OK** (18 ms, 154 bytes):

```http
Content-Type: application/json
Content-Length: 154
X-Correlation-ID: 92aa9504fa2244a8
```

```json
{
  "servicio": "clasificacion-motivos",
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

## P4-CLA-02

**salud 200 XML**

Objetivo: El mismo endpoint responde XML (RF-31).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8010/health" \
  -H "Accept: application/xml"
```

Respuesta - **200 OK** (18 ms, 257 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 257
X-Correlation-ID: 93a67daf05dd496e
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<respuesta><servicio>clasificacion-motivos</servicio><version>v1</version><estado>ok</estado><dependencias><postgresql><ok>true</ok><error /></postgresql><redis><ok>true</ok><error /></redis></dependencias></respuesta>
```

Verificaciones:

- ok: HTTP 200
- ok: es XML
- ok: estado ok

## P4-CLA-03

**Swagger: documentacion de la API**

Objetivo: La API publica su documentacion Swagger.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8010/docs" \
  -H "Accept: text/html"
```

Respuesta - **200 OK** (9 ms, 434 bytes):

```http
Content-Type: text/html; charset=utf-8
Content-Length: 434
X-Correlation-ID: b35af77648b94e22
```

```text
<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Clasificacion de motivos</title>
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

## P4-CLA-04

**Swagger: especificacion OpenAPI**

Objetivo: La especificacion lista todos los endpoints.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8010/openapi.json" \
  -H "Accept: application/json"
```

Respuesta - **200 OK** (8 ms, 6629 bytes):

```http
Content-Type: application/json
Content-Length: 6629
X-Correlation-ID: b3b3c8fbe2ac4179
```

```json
{
  "openapi": "3.0.3",
  "info": {
    "title": "Clasificacion de motivos",
    "version": "v1",
    "description": "Motivos y submotivos por origen de la falla (producto, empaque, transporte, error comercial, mal uso), con versiones y revision humana. La sugerencia automatica es solo una propuesta y nunca modifica la devolucion (RN-11). Responde JSON o XML segun Accept; el XML se valida con los XSD de /contratos."
  },
  "servers": [
    {
      "url": "http://localhost:8010"
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
    "/api/v1/motivos/categorias": {
      "get": {
        "summary": "Categorias de origen de la falla",
        "responses": {
          "200": {
            "description": "Lista de categorias"
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
    "/api/v1/motivos/submotivos": {
      "get": {
        "summary": "Submotivos vigentes",
        "parameters": [
          {
            "name": "categoria_id",
            "in": "query",
            "schema": {
              "type": "integer"
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
            "name": "limite",
            "in": "query",
            "schema": {
... (recortado: 448 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: incluye /sugerencias
- ok: incluye la revision

## P4-CLA-05

**contrato XSD publicado**

Objetivo: El contrato XML de la revision se publica para que los clientes lo validen (RF-31).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8010/contratos/revision.xsd" \
  -H "Accept: application/xml"
```

Respuesta - **200 OK** (8 ms, 882 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 882
X-Correlation-ID: f5b014bfb6ad4e7e
Content-Disposition: inline; filename=revision.xsd
Cache-Control: no-cache
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Decision humana sobre una sugerencia (POST /clasificaciones/{id}/revision):
     confirmar, corregir (con submotivo_id y comentario) o descartar (con comentario). -->
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="revision">
    <xs:complexType>
      <xs:all>
        <xs:element name="decision">
          <xs:simpleType>
            <xs:restriction base="xs:string">
              <xs:enumeration value="confirmar"/>
              <xs:enumeration value="corregir"/>
              <xs:enumeration value="descartar"/>
            </xs:restriction>
          </xs:simpleType>
        </xs:element>
        <xs:element name="submotivo_id" type="xs:string" minOccurs="0"/>
        <xs:element name="comentario" type="xs:string" minOccurs="0"/>
      </xs:all>
    </xs:complexType>
  </xs:element>
</xs:schema>

```

Verificaciones:

- ok: HTTP 200
- ok: es un esquema XSD

## P4-CLA-06

**sin token: 401**

Objetivo: Un endpoint protegido exige JWT (RNF-09).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8010/api/v1/motivos/categorias" \
  -H "Accept: application/json"
```

Respuesta - **401 UNAUTHORIZED** (8 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: e4bd34abc11d4554
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "e4bd34abc11d4554"
  }
}
```

Verificaciones:

- ok: HTTP 401
- ok: tipo no_autenticado

## P4-CLA-07

**token invalido: 401**

Objetivo: Un token alterado se rechaza (RNF-09).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8010/api/v1/motivos/categorias" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer no.es.un.jwt"
```

Respuesta - **401 UNAUTHORIZED** (8 ms, 136 bytes):

```http
Content-Type: application/json
Content-Length: 136
X-Correlation-ID: b3ac5e07f34c471e
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "token_invalido",
    "mensaje": "El token no es valido.",
    "detalles": null,
    "correlation_id": "b3ac5e07f34c471e"
  }
}
```

Verificaciones:

- ok: HTTP 401
- ok: tipo token_invalido

## P4-CLA-08

**categorias 200**

Objetivo: Las cinco categorias de origen de la falla (RF-22).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8010/api/v1/motivos/categorias" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (20 ms, 767 bytes):

```http
Content-Type: application/json
Content-Length: 767
X-Correlation-ID: ef7c5da2c06a49b2
```

```json
{
  "datos": [
    {
      "id": 1,
      "codigo": "falla_producto",
      "nombre": "Falla del producto",
      "descripcion": "El producto salio de fabrica o del proveedor con un defecto",
      "submotivos_activos": 3
    },
    {
      "id": 2,
      "codigo": "empaque",
      "nombre": "Empaque",
      "descripcion": "El envase o empaque no protegio el producto",
      "submotivos_activos": 2
    },
    {
      "id": 3,
      "codigo": "transporte",
      "nombre": "Transporte",
      "descripcion": "El dano ocurrio durante el traslado o la cadena de frio",
      "submotivos_activos": 2
    },
    {
      "id": 4,
      "codigo": "error_comercial",
      "nombre": "Error comercial",
      "descripcion": "Se entrego, etiqueto o cobro algo distinto a lo pactado",
      "submotivos_activos": 3
    },
    {
      "id": 5,
      "codigo": "mal_uso",
      "nombre": "Mal uso",
      "descripcion": "El problema se origino en el manejo posterior a la entrega",
      "submotivos_activos": 2
    }
  ],
  "total": 5
}
```

Verificaciones:

- ok: HTTP 200
- ok: son 5
- ok: origenes esperados

## P4-CLA-09

**categorias 403 cliente**

Objetivo: El catalogo interno no lo lee un cliente (RN-13).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8010/api/v1/motivos/categorias" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_CLIENTE"
```

Respuesta - **403 FORBIDDEN** (10 ms, 345 bytes):

```http
Content-Type: application/json
Content-Length: 345
X-Correlation-ID: 245f0ac628d2453b
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
        "Inspector",
        "Encargado del Centro de Devoluciones",
        "Coordinador de Logistica",
        "Operador de Almacen"
      ]
    },
    "correlation_id": "245f0ac628d2453b"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-CLA-10

**submotivos 200 paginado**

Objetivo: Listado de submotivos vigentes con paginacion.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8010/api/v1/motivos/submotivos?por_pagina=5" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (22 ms, 1778 bytes):

```http
Content-Type: application/json
Content-Length: 1778
X-Correlation-ID: 4d814ff8557e4ca4
```

```json
{
  "datos": [
    {
      "id": 1,
      "codigo": "contaminacion",
      "nombre": "Contaminacion o cuerpo extrano",
      "descripcion": "Moho, insectos u objetos dentro del producto",
      "palabras_clave": [
        "moho",
        "hongo",
        "insecto",
        "cuerpo extrano",
        "pelo",
        "contaminad"
      ],
      "version": 1,
      "activo": true,
      "motivo_id": 6,
      "motivo": "Calidad inferior",
      "categoria_id": 1,
      "categoria_codigo": "falla_producto",
      "categoria": "Falla del producto"
    },
    {
      "id": 2,
      "codigo": "caducado",
      "nombre": "Caducado o proximo a vencer",
      "descripcion": "Fecha de caducidad vencida al recibirlo",
      "palabras_clave": [
        "caduc",
        "vencido",
        "expirado",
        "fecha de caducidad"
      ],
      "version": 1,
      "activo": true,
      "motivo_id": 2,
      "motivo": "Caducidad vencida",
      "categoria_id": 1,
      "categoria_codigo": "falla_producto",
      "categoria": "Falla del producto"
    },
    {
      "id": 3,
      "codigo": "mal_olor_sabor",
      "nombre": "Mal olor o sabor",
      "descripcion": "Olor, sabor o textura fuera de lo normal",
      "palabras_clave": [
        "olor",
        "sabor",
        "rancio",
        "podrido",
        "textura",
        "agrio"
      ],
      "version": 1,
      "activo": true,
      "motivo_id": 6,
      "motivo": "Calidad inferior",
      "categoria_id": 1,
      "categoria_codigo": "falla_producto",
      "categoria": "Falla del producto"
    },
    {
      "id": 4,
      "codigo": "sello_danado",
      "nombre": "Sello o tapa danada",
      "descripcion": "Sello de seguridad o tapa en mal estado",
      "palabras_clave": [
        "sello",
... (recortado: 41 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: 5 por pagina
- ok: al menos 12 en total

## P4-CLA-11

**submotivos 200 filtrado por categoria**

Objetivo: Filtra por categoria de origen.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8010/api/v1/motivos/submotivos?categoria_id=3" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (21 ms, 792 bytes):

```http
Content-Type: application/json
Content-Length: 792
X-Correlation-ID: 4b92bd9cf9ad429b
```

```json
{
  "datos": [
    {
      "id": 6,
      "codigo": "golpe_traslado",
      "nombre": "Golpe durante el traslado",
      "descripcion": "Producto aplastado o golpeado en el transporte",
      "palabras_clave": [
        "aplastado",
        "golpe",
        "maltratado",
        "transporte",
        "caja mojada"
      ],
      "version": 1,
      "activo": true,
      "motivo_id": 1,
      "motivo": "Producto danado",
      "categoria_id": 3,
      "categoria_codigo": "transporte",
      "categoria": "Transporte"
    },
    {
      "id": 7,
      "codigo": "cadena_frio",
      "nombre": "Cadena de frio rota",
      "descripcion": "Producto refrigerado que llego tibio o descongelado",
      "palabras_clave": [
        "caliente",
        "tibio",
        "temperatura",
        "descongelado",
        "refriger",
        "frio"
      ],
      "version": 1,
      "activo": true,
      "motivo_id": 4,
      "motivo": "Cadena de frio rota",
      "categoria_id": 3,
      "categoria_codigo": "transporte",
      "categoria": "Transporte"
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
- ok: todos de transporte
- ok: incluye la cadena de frio

## P4-CLA-12

**submotivos 200 XML**

Objetivo: El listado responde XML (RF-31).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8010/api/v1/motivos/submotivos?por_pagina=2" \
  -H "Accept: application/xml" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (22 ms, 1233 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 1233
X-Correlation-ID: 28f4e440eb694edf
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<submotivos><datos><item><id>1</id><codigo>contaminacion</codigo><nombre>Contaminacion o cuerpo extrano</nombre><descripcion>Moho, insectos u objetos dentro del producto</descripcion><palabras_clave><item>moho</item><item>hongo</item><item>insecto</item><item>cuerpo extrano</item><item>pelo</item><item>contaminad</item></palabras_clave><version>1</version><activo>true</activo><motivo_id>6</motivo_id><motivo>Calidad inferior</motivo><categoria_id>1</categoria_id><categoria_codigo>falla_producto</categoria_codigo><categoria>Falla del producto</categoria></item><item><id>2</id><codigo>caducado</codigo><nombre>Caducado o proximo a vencer</nombre><descripcion>Fecha de caducidad vencida al recibirlo</descripcion><palabras_clave><item>caduc</item><item>vencido</item><item>expirado</item><item>fecha de caducidad</item></palabras_clave><version>1</version><activo>true</activo><motivo_id>2</motivo_id><motivo>Caducidad vencida</motivo><categoria_id>1</categoria_id><categoria_codigo>falla_producto</categoria_codigo><categoria>Falla del producto</categoria></item></datos><paginacion><pagina>1</pagina><por_pagina>2</por_pagina><total>12</total><paginas>6</paginas></paginacion></submotivos>
```

Verificaciones:

- ok: HTTP 200
- ok: es XML
- ok: raiz submotivos

## P4-CLA-13

**submotivos 400 filtro invalido**

Objetivo: Un filtro mal formado se rechaza, no se ignora.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8010/api/v1/motivos/submotivos?categoria_id=abc" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (11 ms, 151 bytes):

```http
Content-Type: application/json
Content-Length: 151
X-Correlation-ID: b81e7b25e6934132
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "categoria_id debe ser un entero positivo.",
    "detalles": null,
    "correlation_id": "b81e7b25e6934132"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CLA-14

**submotivo 200 con su historial**

Objetivo: El detalle trae el historial de versiones (RF-22, RN-12).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8010/api/v1/motivos/submotivos/7" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (24 ms, 685 bytes):

```http
Content-Type: application/json
Content-Length: 685
X-Correlation-ID: 022c8a9bd3a0461c
```

```json
{
  "id": 7,
  "codigo": "cadena_frio",
  "nombre": "Cadena de frio rota",
  "descripcion": "Producto refrigerado que llego tibio o descongelado",
  "palabras_clave": [
    "caliente",
    "tibio",
    "temperatura",
    "descongelado",
    "refriger",
    "frio"
  ],
  "version": 1,
  "activo": true,
  "motivo_id": 4,
  "motivo": "Cadena de frio rota",
  "categoria_id": 3,
  "categoria_codigo": "transporte",
  "categoria": "Transporte",
  "versiones": [
    {
      "version": 1,
      "nombre": "Cadena de frio rota",
      "descripcion": "Producto refrigerado que llego tibio o descongelado",
      "palabras_clave": [
        "caliente",
        "tibio",
        "temperatura",
        "descongelado",
        "refriger",
        "frio"
      ],
      "activo": true,
      "motivo_cambio": "Catalogo inicial",
      "fecha": "2026-11-22T00:59:40.220920+00:00",
      "cambiado_por": null
    }
  ]
}
```

Verificaciones:

- ok: HTTP 200
- ok: tiene al menos la version 1
- ok: version inicial del catalogo

## P4-CLA-15

**submotivo 404**

Objetivo: Un submotivo inexistente responde 404.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8010/api/v1/motivos/submotivos/999999" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **404 NOT FOUND** (23 ms, 135 bytes):

```http
Content-Type: application/json
Content-Length: 135
X-Correlation-ID: 2860e1f136dd4cf2
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Submotivo inexistente.",
    "detalles": null,
    "correlation_id": "2860e1f136dd4cf2"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-CLA-16

**alta 201 JSON (administrador)**

Objetivo: Un administrador da de alta un submotivo; nace en la version 1 (RF-22).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/submotivos" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"categoria_id":3,"codigo":"evid_p4_humedad","nombre":"Humedad en el almacen","descripcion":"Producto mojado por goteras o humedad","palabras_clave":["humedad","goteras","mojado"]}'
```

Respuesta - **201 CREATED** (28 ms, 22 bytes):

```http
Content-Type: application/json
Content-Length: 22
X-Correlation-ID: 216f1137e91b4575
Location: /api/v1/motivos/submotivos/16
```

```json
{
  "id": 16,
  "version": 1
}
```

Verificaciones:

- ok: HTTP 201
- ok: version 1
- ok: trae Location

Efecto en PostgreSQL - el submotivo y su version 1:

```sql
SELECT s.codigo, s.version, s.activo, v.version AS version_guardada, v.motivo_cambio FROM submotivos s JOIN submotivos_versiones v ON v.submotivo_id = s.id WHERE s.id = 16
```

```text
codigo | version | activo | version_guardada | motivo_cambio
evid_p4_humedad | 1 | t | 1 | Alta del submotivo
```

## P4-CLA-17

**alta 201 XML (supervisor)**

Objetivo: El mismo alta en XML, validado contra su XSD (RF-31). El Supervisor tambien puede dar de alta.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/submotivos" \
  -H "Accept: application/xml" \
  -H "Content-Type: application/xml" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '<submotivo><categoria_id>3</categoria_id><codigo>evid_p4_xml</codigo><nombre>Alta enviada por XML</nombre><palabras_clave><item>xml</item><item>contrato</item></palabras_clave></submotivo>'
```

Respuesta - **201 CREATED** (26 ms, 93 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 93
X-Correlation-ID: 9e7ba0b0733d4291
Location: /api/v1/motivos/submotivos/17
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<submotivo><id>17</id><version>1</version></submotivo>
```

Verificaciones:

- ok: HTTP 201
- ok: version 1

## P4-CLA-18

**alta 400 codigo con formato invalido**

Objetivo: El codigo debe ser minusculas, numeros y guion bajo.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/submotivos" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"categoria_id":3,"codigo":"Mal Codigo","nombre":"x"}'
```

Respuesta - **400 BAD REQUEST** (9 ms, 208 bytes):

```http
Content-Type: application/json
Content-Length: 208
X-Correlation-ID: e2207690fdb74b5c
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Campos invalidos.",
    "detalles": [
      {
        "campo": "codigo",
        "problema": "3 a 40 caracteres: minusculas, numeros y guion bajo"
      }
    ],
    "correlation_id": "e2207690fdb74b5c"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion
- ok: senala el campo codigo

## P4-CLA-19

**alta 400 XML que no cumple el XSD**

Objetivo: Un XML que no cumple el contrato se rechaza antes de procesarse (RF-31).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/submotivos" \
  -H "Accept: application/xml" \
  -H "Content-Type: application/xml" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '<submotivo><nombre>Sin categoria</nombre></submotivo>'
```

Respuesta - **400 BAD REQUEST** (9 ms, 431 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 431
X-Correlation-ID: 0c530a90d3b14835
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<error><codigo>400</codigo><tipo>xml_no_cumple_xsd</tipo><mensaje>El XML no cumple el contrato del endpoint.</mensaje><detalles><item><linea>1</linea><problema>Element 'submotivo': Missing child element(s). Expected is one of ( categoria_id, motivo_id, codigo, descripcion, motivo_cambio, palabras_clave ).</problema></item></detalles><correlation_id>0c530a90d3b14835</correlation_id></error>
```

Verificaciones:

- ok: HTTP 400
- ok: tipo xml_no_cumple_xsd

## P4-CLA-20

**alta 409 codigo duplicado**

Objetivo: Dos submotivos no comparten codigo.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/submotivos" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"categoria_id":3,"codigo":"evid_p4_humedad","nombre":"Repetido"}'
```

Respuesta - **409 CONFLICT** (18 ms, 154 bytes):

```http
Content-Type: application/json
Content-Length: 154
X-Correlation-ID: f080ae633d884d9f
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "codigo_duplicado",
    "mensaje": "Ya existe un submotivo con ese codigo.",
    "detalles": null,
    "correlation_id": "f080ae633d884d9f"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo codigo_duplicado

## P4-CLA-21

**alta 409 categoria inexistente**

Objetivo: No se acepta una referencia que no existe.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/submotivos" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"categoria_id":99999,"codigo":"evid_p4_huerfano","nombre":"Sin categoria real"}'
```

Respuesta - **409 CONFLICT** (16 ms, 142 bytes):

```http
Content-Type: application/json
Content-Length: 142
X-Correlation-ID: 736ad6c3918049d6
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "referencia_invalida",
    "mensaje": "La categoria no existe.",
    "detalles": null,
    "correlation_id": "736ad6c3918049d6"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo referencia_invalida

## P4-CLA-22

**alta 403 analista**

Objetivo: Solo Administrador y Supervisor editan el catalogo (RN-13).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/submotivos" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"categoria_id":3,"codigo":"evid_p4_prohibido","nombre":"x"}'
```

Respuesta - **403 FORBIDDEN** (9 ms, 235 bytes):

```http
Content-Type: application/json
Content-Length: 235
X-Correlation-ID: f8e64e87af424b01
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
        "Supervisor"
      ]
    },
    "correlation_id": "f8e64e87af424b01"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

Efecto en PostgreSQL - no se creo ninguna fila:

```sql
SELECT count(*) AS filas FROM submotivos WHERE codigo = 'evid_p4_prohibido'
```

```text
filas
0
```

## P4-CLA-23

**edicion 200: crea la version 2**

Objetivo: Cada cambio crea una version nueva y exige explicar por que (RF-22, RN-12).

Comando:

```bash
curl -sS -i -X PUT "http://$VM_HOST:8010/api/v1/motivos/submotivos/16" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"categoria_id":3,"nombre":"Humedad o goteras en el almacen","descripcion":"Producto mojado por goteras o humedad","palabras_clave":["humedad","goteras","mojado","filtracion"],"motivo_cambio":"Se agrega la palabra filtracion"}'
```

Respuesta - **200 OK** (24 ms, 22 bytes):

```http
Content-Type: application/json
Content-Length: 22
X-Correlation-ID: 0ff41c7c1be543fc
```

```json
{
  "id": 16,
  "version": 2
}
```

Verificaciones:

- ok: HTTP 200
- ok: version 2

Efecto en PostgreSQL - la version anterior se conserva:

```sql
SELECT version, nombre, motivo_cambio FROM submotivos_versiones WHERE submotivo_id = 16 ORDER BY version
```

```text
version | nombre | motivo_cambio
1 | Humedad en el almacen | Alta del submotivo
2 | Humedad o goteras en el almacen | Se agrega la palabra filtracion
```

## P4-CLA-24

**edicion 200: sin cambios no crea version**

Objetivo: Repetir lo mismo es idempotente: no ensucia el historial.

Comando:

```bash
curl -sS -i -X PUT "http://$VM_HOST:8010/api/v1/motivos/submotivos/16" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"categoria_id":3,"nombre":"Humedad o goteras en el almacen","descripcion":"Producto mojado por goteras o humedad","palabras_clave":["humedad","goteras","mojado","filtracion"],"motivo_cambio":"Se agrega la palabra filtracion"}'
```

Respuesta - **200 OK** (20 ms, 41 bytes):

```http
Content-Type: application/json
Content-Length: 41
X-Correlation-ID: f9a45bed92744d99
```

```json
{
  "id": 16,
  "version": 2,
  "sin_cambios": true
}
```

Verificaciones:

- ok: HTTP 200
- ok: sin_cambios
- ok: sigue en la version 2

Efecto en PostgreSQL - solo hay 2 versiones:

```sql
SELECT count(*) AS versiones FROM submotivos_versiones WHERE submotivo_id = 16
```

```text
versiones
2
```

## P4-CLA-25

**edicion 400 sin explicar el cambio**

Objetivo: Sin motivo del cambio no se edita.

Comando:

```bash
curl -sS -i -X PUT "http://$VM_HOST:8010/api/v1/motivos/submotivos/16" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"categoria_id":3,"nombre":"Humedad o goteras en el almacen","descripcion":"Producto mojado por goteras o humedad","palabras_clave":["humedad","goteras","mojado","filtracion"]}'
```

Respuesta - **400 BAD REQUEST** (9 ms, 175 bytes):

```http
Content-Type: application/json
Content-Length: 175
X-Correlation-ID: 0e4d03d672094717
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Campos invalidos.",
    "detalles": [
      {
        "campo": "motivo_cambio",
        "problema": "obligatorio"
      }
    ],
    "correlation_id": "0e4d03d672094717"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CLA-26

**edicion 404**

Objetivo: Editar un submotivo inexistente responde 404.

Comando:

```bash
curl -sS -i -X PUT "http://$VM_HOST:8010/api/v1/motivos/submotivos/999999" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"categoria_id":3,"nombre":"Humedad o goteras en el almacen","descripcion":"Producto mojado por goteras o humedad","palabras_clave":["humedad","goteras","mojado","filtracion"],"motivo_cambio":"Se agrega la palabra filtracion"}'
```

Respuesta - **404 NOT FOUND** (17 ms, 135 bytes):

```http
Content-Type: application/json
Content-Length: 135
X-Correlation-ID: d2503efe1b7f4f1d
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Submotivo inexistente.",
    "detalles": null,
    "correlation_id": "d2503efe1b7f4f1d"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-CLA-27

**estado 200: desactivar crea la version 3**

Objetivo: Activar o desactivar tambien es un cambio versionado (RF-22).

Comando:

```bash
curl -sS -i -X PATCH "http://$VM_HOST:8010/api/v1/motivos/submotivos/16/estado" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"activo":false,"motivo_cambio":"Se retira porque era solo de prueba"}'
```

Respuesta - **200 OK** (22 ms, 37 bytes):

```http
Content-Type: application/json
Content-Length: 37
X-Correlation-ID: 02ef40304cc1446d
```

```json
{
  "id": 16,
  "version": 3,
  "activo": false
}
```

Verificaciones:

- ok: HTTP 200
- ok: version 3
- ok: activo false

Efecto en PostgreSQL - queda inactivo y con 3 versiones:

```sql
SELECT s.activo, s.version, count(v.*) AS versiones FROM submotivos s JOIN submotivos_versiones v ON v.submotivo_id = s.id WHERE s.id = 16 GROUP BY s.activo, s.version
```

```text
activo | version | versiones
f | 3 | 3
```

## P4-CLA-28

**estado 400 valor invalido**

Objetivo: activo debe ser booleano.

Comando:

```bash
curl -sS -i -X PATCH "http://$VM_HOST:8010/api/v1/motivos/submotivos/16/estado" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"activo":"quiza","motivo_cambio":"Valor que no es booleano"}'
```

Respuesta - **400 BAD REQUEST** (9 ms, 135 bytes):

```http
Content-Type: application/json
Content-Length: 135
X-Correlation-ID: 42b904e7fb1d4133
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "activo debe ser booleano.",
    "detalles": null,
    "correlation_id": "42b904e7fb1d4133"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CLA-29

**estado 404**

Objetivo: Un submotivo inexistente responde 404.

Comando:

```bash
curl -sS -i -X PATCH "http://$VM_HOST:8010/api/v1/motivos/submotivos/999999/estado" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"activo":false,"motivo_cambio":"No existe este submotivo"}'
```

Respuesta - **404 NOT FOUND** (16 ms, 135 bytes):

```http
Content-Type: application/json
Content-Length: 135
X-Correlation-ID: 8a675535fc584046
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Submotivo inexistente.",
    "detalles": null,
    "correlation_id": "8a675535fc584046"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-CLA-30

**sugerencia 200 (cliente)**

Objetivo: Un cliente pide una sugerencia para su formulario; es solo una propuesta (RN-11).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/sugerencias" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_CLIENTE" \
  -d '{"descripcion":"El producto llego tibio y la temperatura era muy alta"}'
```

Respuesta - **200 OK** (20 ms, 257 bytes):

```http
Content-Type: application/json
Content-Length: 257
X-Correlation-ID: 7b3f58d47aaa4112
```

```json
{
  "sugerencias": [
    {
      "submotivo_id": 7,
      "codigo": "cadena_frio",
      "submotivo": "Cadena de frio rota",
      "categoria": "Transporte",
      "motivo_id": 4,
      "version": 1,
      "puntaje": 2
    }
  ],
  "requiere_confirmacion": true,
  "explicacion": "La sugerencia orienta; una persona confirma el motivo."
}
```

Verificaciones:

- ok: HTTP 200
- ok: exige confirmacion
- ok: sugiere cadena de frio
- ok: no revela las palabras clave

## P4-CLA-31

**sugerencia 200 XML**

Objetivo: La sugerencia en XML. Un Supervisor tambien puede pedirla (corregido en el PR #33).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/sugerencias" \
  -H "Accept: application/xml" \
  -H "Content-Type: application/xml" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '<sugerencia><descripcion>El producto llego tibio y la temperatura era muy alta</descripcion></sugerencia>'
```

Respuesta - **200 OK** (21 ms, 435 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 435
X-Correlation-ID: 42dfb2df87624f4e
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<sugerencias><sugerencias><item><submotivo_id>7</submotivo_id><codigo>cadena_frio</codigo><submotivo>Cadena de frio rota</submotivo><categoria>Transporte</categoria><motivo_id>4</motivo_id><version>1</version><puntaje>2</puntaje></item></sugerencias><requiere_confirmacion>true</requiere_confirmacion><explicacion>La sugerencia orienta; una persona confirma el motivo.</explicacion></sugerencias>
```

Verificaciones:

- ok: HTTP 200
- ok: es XML
- ok: cadena_frio

## P4-CLA-32

**sugerencia 200: sin coincidencias no inventa**

Objetivo: Si ninguna palabra coincide, no se inventa una sugerencia.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/sugerencias" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_CLIENTE" \
  -d '{"descripcion":"No me gusto para nada lo que compre ayer"}'
```

Respuesta - **200 OK** (19 ms, 119 bytes):

```http
Content-Type: application/json
Content-Length: 119
X-Correlation-ID: 62f1ea49cfef485b
```

```json
{
  "sugerencias": [],
  "requiere_confirmacion": true,
  "explicacion": "La sugerencia orienta; una persona confirma el motivo."
}
```

Verificaciones:

- ok: HTTP 200
- ok: lista vacia

## P4-CLA-33

**sugerencia 400 descripcion corta**

Objetivo: La descripcion exige entre 10 y 2000 caracteres.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/sugerencias" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_CLIENTE" \
  -d '{"descripcion":"corta"}'
```

Respuesta - **400 BAD REQUEST** (9 ms, 163 bytes):

```http
Content-Type: application/json
Content-Length: 163
X-Correlation-ID: 3073b54ad49141d8
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "descripcion debe contener entre 10 y 2000 caracteres.",
    "detalles": null,
    "correlation_id": "3073b54ad49141d8"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CLA-34

**sugerencia 401 sin token**

Objetivo: Tambien la sugerencia exige sesion.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/sugerencias" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"descripcion":"El producto llego tibio y la temperatura era muy alta"}'
```

Respuesta - **401 UNAUTHORIZED** (7 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: 26a0edb5a6e24148
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "26a0edb5a6e24148"
  }
}
```

Verificaciones:

- ok: HTTP 401
- ok: tipo no_autenticado

## P4-CLA-35

**clasificacion 201: queda pendiente**

Objetivo: Se propone un submotivo para una devolucion y queda PENDIENTE de revision humana (RN-11).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/clasificaciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"devolucion_id":105}'
```

Respuesta - **201 CREATED** (26 ms, 463 bytes):

```http
Content-Type: application/json
Content-Length: 463
X-Correlation-ID: 96b381e5eea94055
```

```json
{
  "id": 6,
  "estado": "pendiente",
  "sugerencias": [
    {
      "submotivo_id": 7,
      "codigo": "cadena_frio",
      "submotivo": "Cadena de frio rota",
      "categoria": "Transporte",
      "motivo_id": 4,
      "version": 1,
      "puntaje": 1,
      "coincidencias": [
        "tibio"
      ]
    },
    {
      "submotivo_id": 3,
      "codigo": "mal_olor_sabor",
      "submotivo": "Mal olor o sabor",
      "categoria": "Falla del producto",
      "motivo_id": 6,
      "version": 1,
      "puntaje": 1,
      "coincidencias": [
        "olor"
      ]
    }
  ],
  "requiere_revision_humana": true,
  "aviso": "No se modifico la devolucion (RN-11)."
}
```

Verificaciones:

- ok: HTTP 201
- ok: estado pendiente
- ok: pide revision humana
- ok: sugiere cadena de frio
- ok: la devolucion no cambio

Efecto en PostgreSQL - fila pendiente y devolucion intacta:

```sql
SELECT cm.estado, cm.revisado_por, ss.codigo AS sugerido, d.estado AS estado_devolucion, d.motivo_id AS motivo_devolucion FROM clasificaciones_motivo cm JOIN devoluciones d ON d.id = cm.devolucion_id LEFT JOIN submotivos ss ON ss.id = cm.submotivo_sugerido_id WHERE cm.id = 6
```

```text
estado | revisado_por | sugerido | estado_devolucion | motivo_devolucion
pendiente |  | cadena_frio | cerrada | 4
```

## P4-CLA-36

**clasificacion 409: ya hay una pendiente**

Objetivo: Una sola sugerencia pendiente por devolucion.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/clasificaciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"devolucion_id":105}'
```

Respuesta - **409 CONFLICT** (33 ms, 185 bytes):

```http
Content-Type: application/json
Content-Length: 185
X-Correlation-ID: 956e425311e94da3
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "clasificacion_pendiente",
    "mensaje": "Esta devolucion ya tiene una sugerencia pendiente de revision.",
    "detalles": null,
    "correlation_id": "956e425311e94da3"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo clasificacion_pendiente

## P4-CLA-37

**clasificacion 404 devolucion inexistente**

Objetivo: No se clasifica lo que no existe.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/clasificaciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"devolucion_id":99999999}'
```

Respuesta - **404 NOT FOUND** (24 ms, 136 bytes):

```http
Content-Type: application/json
Content-Length: 136
X-Correlation-ID: 877b9facb59b4032
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Devolucion inexistente.",
    "detalles": null,
    "correlation_id": "877b9facb59b4032"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-CLA-38

**clasificacion 400 identificador invalido**

Objetivo: devolucion_id debe ser un entero positivo.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/clasificaciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"devolucion_id":"abc"}'
```

Respuesta - **400 BAD REQUEST** (13 ms, 152 bytes):

```http
Content-Type: application/json
Content-Length: 152
X-Correlation-ID: 9bf24bdfec6a4012
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "devolucion_id debe ser un entero positivo.",
    "detalles": null,
    "correlation_id": "9bf24bdfec6a4012"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CLA-39

**clasificacion 403 cliente**

Objetivo: Un cliente no propone clasificaciones (RN-13).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/clasificaciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_CLIENTE" \
  -d '{"devolucion_id":105}'
```

Respuesta - **403 FORBIDDEN** (11 ms, 245 bytes):

```http
Content-Type: application/json
Content-Length: 245
X-Correlation-ID: e2a00c862c7c41a0
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
        "Analista de Devoluciones",
        "Supervisor",
        "Administrador"
      ]
    },
    "correlation_id": "e2a00c862c7c41a0"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-CLA-40

**cola 200: pendientes de revision**

Objetivo: La cola de sugerencias por revisar.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8010/api/v1/motivos/clasificaciones?estado=pendiente" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (33 ms, 494 bytes):

```http
Content-Type: application/json
Content-Length: 494
X-Correlation-ID: 39fd7447b1d1430a
```

```json
{
  "datos": [
    {
      "id": 6,
      "devolucion_id": 105,
      "folio_devolucion": "DEV-2026-0105",
      "estado": "pendiente",
      "puntaje": 1,
      "coincidencias": [
        "tibio"
      ],
      "submotivo_sugerido_id": 7,
      "submotivo_sugerido": "Cadena de frio rota",
      "version_sugerida": 1,
      "submotivo_final_id": null,
      "submotivo_final": null,
      "version_final": null,
      "motivo_id_final": null,
      "comentario": null,
      "fecha_creacion": "2026-11-22T18:01:37.592114+00:00",
      "fecha_revision": null,
      "revisado_por": null
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
- ok: incluye la recien creada

## P4-CLA-41

**cola 400 estado desconocido**

Objetivo: Un estado que no existe se rechaza.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8010/api/v1/motivos/clasificaciones?estado=inventado" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (13 ms, 129 bytes):

```http
Content-Type: application/json
Content-Length: 129
X-Correlation-ID: 730a1e23f3224f40
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "estado desconocido.",
    "detalles": null,
    "correlation_id": "730a1e23f3224f40"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CLA-42

**revision 400: corregir sin comentario ni submotivo**

Objetivo: Quien contradice a la sugerencia debe elegir el submotivo y explicar por que (RN-11).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/clasificaciones/6/revision" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"decision":"corregir"}'
```

Respuesta - **400 BAD REQUEST** (14 ms, 172 bytes):

```http
Content-Type: application/json
Content-Length: 172
X-Correlation-ID: f0cc0a06d5a94130
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
    "correlation_id": "f0cc0a06d5a94130"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CLA-43

**revision 403 cliente**

Objetivo: Un cliente no revisa (RN-13).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/clasificaciones/6/revision" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_CLIENTE" \
  -d '{"decision":"confirmar"}'
```

Respuesta - **403 FORBIDDEN** (13 ms, 245 bytes):

```http
Content-Type: application/json
Content-Length: 245
X-Correlation-ID: e75d0f01bcda4bab
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
        "Analista de Devoluciones",
        "Supervisor",
        "Administrador"
      ]
    },
    "correlation_id": "e75d0f01bcda4bab"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-CLA-44

**revision 200: confirmar**

Objetivo: Una persona confirma la sugerencia. La revision NO modifica la devolucion (RN-11).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/clasificaciones/6/revision" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"decision":"confirmar"}'
```

Respuesta - **200 OK** (36 ms, 595 bytes):

```http
Content-Type: application/json
Content-Length: 595
X-Correlation-ID: ffea4d9cf55c452e
```

```json
{
  "id": 6,
  "devolucion_id": 105,
  "folio_devolucion": "DEV-2026-0105",
  "estado": "confirmada",
  "puntaje": 1,
  "coincidencias": [
    "tibio"
  ],
  "submotivo_sugerido_id": 7,
  "submotivo_sugerido": "Cadena de frio rota",
  "version_sugerida": 1,
  "submotivo_final_id": 7,
  "submotivo_final": "Cadena de frio rota",
  "version_final": 1,
  "motivo_id_final": 4,
  "comentario": null,
  "fecha_creacion": "2026-11-22T18:01:37.592114+00:00",
  "fecha_revision": "2026-11-22T18:01:38.105768+00:00",
  "revisado_por": "Josue Berdeal",
  "aplicado_a_devolucion": false,
  "aviso": "La revision no modifica la devolucion; cambiar su motivo es una accion aparte (RN-11)."
}
```

Verificaciones:

- ok: HTTP 200
- ok: estado confirmada
- ok: no se aplico a la devolucion
- ok: queda quien reviso
- ok: la devolucion sigue igual

Efecto en PostgreSQL - responsable, version y devolucion intacta:

```sql
SELECT cm.estado, u.nombre AS revisado_por, cm.version_final, d.estado AS estado_devolucion, d.motivo_id AS motivo_devolucion FROM clasificaciones_motivo cm JOIN usuarios u ON u.id = cm.revisado_por JOIN devoluciones d ON d.id = cm.devolucion_id WHERE cm.id = 6
```

```text
estado | revisado_por | version_final | estado_devolucion | motivo_devolucion
confirmada | Josue Berdeal | 1 | cerrada | 4
```

## P4-CLA-45

**revision 409: ya fue revisada**

Objetivo: Una clasificacion revisada no se vuelve a revisar.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/clasificaciones/6/revision" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"decision":"descartar","comentario":"Intento de cambiar una decision ya tomada"}'
```

Respuesta - **409 CONFLICT** (21 ms, 146 bytes):

```http
Content-Type: application/json
Content-Length: 146
X-Correlation-ID: 20e381720c394e4b
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "ya_revisada",
    "mensaje": "La clasificacion ya fue confirmada.",
    "detalles": null,
    "correlation_id": "20e381720c394e4b"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo ya_revisada

## P4-CLA-46

**revision 404**

Objetivo: Una clasificacion inexistente responde 404.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/clasificaciones/99999999/revision" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"decision":"confirmar"}'
```

Respuesta - **404 NOT FOUND** (20 ms, 139 bytes):

```http
Content-Type: application/json
Content-Length: 139
X-Correlation-ID: befc1be33a924008
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Clasificacion inexistente.",
    "detalles": null,
    "correlation_id": "befc1be33a924008"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-CLA-47

**clasificacion 201: nueva sugerencia tras la revision**

Objetivo: Resuelta la anterior, se puede proponer otra.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/clasificaciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"devolucion_id":105}'
```

Respuesta - **201 CREATED** (29 ms, 463 bytes):

```http
Content-Type: application/json
Content-Length: 463
X-Correlation-ID: 4b25c0b207ef4279
```

```json
{
  "id": 7,
  "estado": "pendiente",
  "sugerencias": [
    {
      "submotivo_id": 7,
      "codigo": "cadena_frio",
      "submotivo": "Cadena de frio rota",
      "categoria": "Transporte",
      "motivo_id": 4,
      "version": 1,
      "puntaje": 1,
      "coincidencias": [
        "tibio"
      ]
    },
    {
      "submotivo_id": 3,
      "codigo": "mal_olor_sabor",
      "submotivo": "Mal olor o sabor",
      "categoria": "Falla del producto",
      "motivo_id": 6,
      "version": 1,
      "puntaje": 1,
      "coincidencias": [
        "olor"
      ]
    }
  ],
  "requiere_revision_humana": true,
  "aviso": "No se modifico la devolucion (RN-11)."
}
```

Verificaciones:

- ok: HTTP 201
- ok: estado pendiente

## P4-CLA-48

**revision 200 XML: corregir**

Objetivo: Corregir: una persona elige otro submotivo y explica por que. En XML, validado contra su XSD.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/clasificaciones/7/revision" \
  -H "Accept: application/xml" \
  -H "Content-Type: application/xml" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '<revision><decision>corregir</decision><submotivo_id>17</submotivo_id><comentario>La causa fue el golpe, no el frio</comentario></revision>'
```

Respuesta - **200 OK** (26 ms, 937 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 937
X-Correlation-ID: 01694c7fbd9d4ed8
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<clasificacion><id>7</id><devolucion_id>105</devolucion_id><folio_devolucion>DEV-2026-0105</folio_devolucion><estado>corregida</estado><puntaje>1</puntaje><coincidencias><item>tibio</item></coincidencias><submotivo_sugerido_id>7</submotivo_sugerido_id><submotivo_sugerido>Cadena de frio rota</submotivo_sugerido><version_sugerida>1</version_sugerida><submotivo_final_id>17</submotivo_final_id><submotivo_final>Alta enviada por XML</submotivo_final><version_final>1</version_final><motivo_id_final /><comentario>La causa fue el golpe, no el frio</comentario><fecha_creacion>2026-11-22T18:01:38.731044+00:00</fecha_creacion><fecha_revision>2026-11-22T18:01:38.759733+00:00</fecha_revision><revisado_por>Jorge Salinas</revisado_por><aplicado_a_devolucion>false</aplicado_a_devolucion><aviso>La revision no modifica la devolucion; cambiar su motivo es una accion aparte (RN-11).</aviso></clasificacion>
```

Verificaciones:

- ok: HTTP 200
- ok: estado corregida

Efecto en PostgreSQL - submotivo final y comentario:

```sql
SELECT cm.estado, sf.codigo AS submotivo_final, cm.version_final, cm.comentario FROM clasificaciones_motivo cm JOIN submotivos sf ON sf.id = cm.submotivo_final_id WHERE cm.id = 7
```

```text
estado | submotivo_final | version_final | comentario
corregida | evid_p4_xml | 1 | La causa fue el golpe, no el frio
```

## P4-CLA-49

**clasificacion 201: tercera sugerencia**

Objetivo: Otra sugerencia pendiente, para descartarla.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/clasificaciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"devolucion_id":105}'
```

Respuesta - **201 CREATED** (80 ms, 463 bytes):

```http
Content-Type: application/json
Content-Length: 463
X-Correlation-ID: 25c63bbedbaf4c50
```

```json
{
  "id": 8,
  "estado": "pendiente",
  "sugerencias": [
    {
      "submotivo_id": 7,
      "codigo": "cadena_frio",
      "submotivo": "Cadena de frio rota",
      "categoria": "Transporte",
      "motivo_id": 4,
      "version": 1,
      "puntaje": 1,
      "coincidencias": [
        "tibio"
      ]
    },
    {
      "submotivo_id": 3,
      "codigo": "mal_olor_sabor",
      "submotivo": "Mal olor o sabor",
      "categoria": "Falla del producto",
      "motivo_id": 6,
      "version": 1,
      "puntaje": 1,
      "coincidencias": [
        "olor"
      ]
    }
  ],
  "requiere_revision_humana": true,
  "aviso": "No se modifico la devolucion (RN-11)."
}
```

Verificaciones:

- ok: HTTP 201

## P4-CLA-50

**revision 200: descartar**

Objetivo: Descartar exige comentario; no se asigna ningun submotivo final.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8010/api/v1/motivos/clasificaciones/8/revision" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -d '{"decision":"descartar","comentario":"La descripcion no alcanza para clasificar el caso"}'
```

Respuesta - **200 OK** (63 ms, 633 bytes):

```http
Content-Type: application/json
Content-Length: 633
X-Correlation-ID: 94158ffbe3cc4769
```

```json
{
  "id": 8,
  "devolucion_id": 105,
  "folio_devolucion": "DEV-2026-0105",
  "estado": "descartada",
  "puntaje": 1,
  "coincidencias": [
    "tibio"
  ],
  "submotivo_sugerido_id": 7,
  "submotivo_sugerido": "Cadena de frio rota",
  "version_sugerida": 1,
  "submotivo_final_id": null,
  "submotivo_final": null,
  "version_final": null,
  "motivo_id_final": null,
  "comentario": "La descripcion no alcanza para clasificar el caso",
  "fecha_creacion": "2026-11-22T18:01:39.110425+00:00",
  "fecha_revision": "2026-11-22T18:01:39.189227+00:00",
  "revisado_por": "Pablo Flores",
  "aplicado_a_devolucion": false,
  "aviso": "La revision no modifica la devolucion; cambiar su motivo es una accion aparte (RN-11)."
}
```

Verificaciones:

- ok: HTTP 200
- ok: estado descartada
- ok: sin submotivo final
- ok: la devolucion sigue igual

Efecto en PostgreSQL - descartada, con responsable y sin submotivo final:

```sql
SELECT estado, submotivo_final_id, revisado_por IS NOT NULL AS tiene_responsable FROM clasificaciones_motivo WHERE id = 8
```

```text
estado | submotivo_final_id | tiene_responsable
descartada |  | t
```

## Limpieza

Al terminar se borraron los datos que creo esta corrida, para no dejar basura en la base de demostracion. **La bitacora no se toca**: es de solo agregar (migracion 045).

