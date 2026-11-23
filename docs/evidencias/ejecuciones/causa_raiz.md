# Evidencia con curl - `causa-raiz`

Ejecutada en la VM el 2026-11-22 18:13 UTC con `scripts/evidencias/ejecutar.py causa_raiz` (commit `c866e90`).
Casos: **100**, correctos: **100**, con falla: **0**. Los tokens y la contrasena de demo estan ocultos; la IP de la VM se muestra como `$VM_HOST`.

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
| [P4-CR-01](#p4-cr-01) | correcto | 200 | salud 200 JSON |
| [P4-CR-02](#p4-cr-02) | correcto | 200 | salud 200 XML |
| [P4-CR-03](#p4-cr-03) | correcto | 200 | Swagger: documentacion de la API |
| [P4-CR-04](#p4-cr-04) | correcto | 200 | Swagger: especificacion OpenAPI |
| [P4-CR-05](#p4-cr-05) | correcto | 200 | contrato XSD publicado |
| [P4-CR-06](#p4-cr-06) | correcto | 401 | sin token: 401 |
| [P4-CR-07](#p4-cr-07) | correcto | 401 | token invalido: 401 |
| [P4-CR-08](#p4-cr-08) | correcto | 403 | cliente: 403 en alertas |
| [P4-CR-09](#p4-cr-09) | correcto | 403 | inspector: 403 en investigaciones |
| [P4-CR-10](#p4-cr-10) | correcto | 200 | detectar patrones 200 |
| [P4-CR-11](#p4-cr-11) | correcto | 200 | alertas 200: lote de la demo |
| [P4-CR-12](#p4-cr-12) | correcto | 200 | alertas 200 XML |
| [P4-CR-13](#p4-cr-13) | correcto | 400 | alertas 400 dimension desconocida |
| [P4-CR-14](#p4-cr-14) | correcto | 400 | descartar alerta 400 comentario corto |
| [P4-CR-15](#p4-cr-15) | correcto | 404 | descartar alerta 404 |
| [P4-CR-16](#p4-cr-16) | correcto | 200 | descartar alerta 200 |
| [P4-CR-17](#p4-cr-17) | correcto | 409 | descartar alerta 409 ya resuelta |
| [P4-CR-18](#p4-cr-18) | correcto | 409 | investigar alerta descartada: 409 |
| [P4-CR-19](#p4-cr-19) | correcto | 400 | investigar alerta 400 campo no permitido |
| [P4-CR-20](#p4-cr-20) | correcto | 201 | investigar alerta 201 |
| [P4-CR-21](#p4-cr-21) | correcto | 409 | investigar alerta 409 ya en investigacion |
| [P4-CR-22](#p4-cr-22) | correcto | 409 | investigacion manual 409 objeto ya investigado |
| [P4-CR-23](#p4-cr-23) | correcto | 400 | investigacion manual 400 dimension invalida |
| [P4-CR-24](#p4-cr-24) | correcto | 404 | investigacion manual 404 objeto inexistente |
| [P4-CR-25](#p4-cr-25) | correcto | 200 | listado de investigaciones 200 |
| [P4-CR-26](#p4-cr-26) | correcto | 200 | listado de investigaciones 200 XML |
| [P4-CR-27](#p4-cr-27) | correcto | 400 | listado de investigaciones 400 estado desconocido |
| [P4-CR-28](#p4-cr-28) | correcto | 404 | detalle de investigacion 404 |
| [P4-CR-29](#p4-cr-29) | correcto | 400 | hipotesis 400 tipo invalido |
| [P4-CR-30](#p4-cr-30) | correcto | 201 | hipotesis 201: primer porque |
| [P4-CR-31](#p4-cr-31) | correcto | 201 | hipotesis 201: segundo porque |
| [P4-CR-32](#p4-cr-32) | correcto | 409 | hipotesis 409 porque ya con continuacion |
| [P4-CR-33](#p4-cr-33) | correcto | 409 | hipotesis 409 porque padre inexistente |
| [P4-CR-34](#p4-cr-34) | correcto | 400 | hipotesis 400 Ishikawa sin categoria |
| [P4-CR-35](#p4-cr-35) | correcto | 201 | hipotesis 201: Ishikawa |
| [P4-CR-36](#p4-cr-36) | correcto | 201 | hipotesis 201 XML: libre |
| [P4-CR-37](#p4-cr-37) | correcto | 400 | evidencia 400 devolucion sin devolucion_id |
| [P4-CR-38](#p4-cr-38) | correcto | 409 | evidencia 409 devolucion de otro lote |
| [P4-CR-39](#p4-cr-39) | correcto | 409 | evidencia 409 hipotesis ajena |
| [P4-CR-40](#p4-cr-40) | correcto | 201 | evidencia 201: devolucion del lote |
| [P4-CR-41](#p4-cr-41) | correcto | 201 | evidencia 201: nota |
| [P4-CR-42](#p4-cr-42) | correcto | 200 | detalle de investigacion 200 |
| [P4-CR-43](#p4-cr-43) | correcto | 409 | concluir 409 sin pasar por verificacion |
| [P4-CR-44](#p4-cr-44) | correcto | 200 | iniciar verificacion 200 |
| [P4-CR-45](#p4-cr-45) | correcto | 409 | iniciar verificacion 409 repetida |
| [P4-CR-46](#p4-cr-46) | correcto | 409 | concluir 409 sin hipotesis verificada |
| [P4-CR-47](#p4-cr-47) | correcto | 400 | verificar hipotesis 400 resultado invalido |
| [P4-CR-48](#p4-cr-48) | correcto | 404 | verificar hipotesis 404 inexistente |
| [P4-CR-49](#p4-cr-49) | correcto | 200 | verificar hipotesis 200: verificada |
| [P4-CR-50](#p4-cr-50) | correcto | 409 | verificar hipotesis 409 ya verificada |
| [P4-CR-51](#p4-cr-51) | correcto | 200 | verificar hipotesis 200: descartada |
| [P4-CR-52](#p4-cr-52) | correcto | 400 | concluir 400 causa confirmada sin causa |
| [P4-CR-53](#p4-cr-53) | correcto | 400 | concluir 400 inconclusa con causa |
| [P4-CR-54](#p4-cr-54) | correcto | 200 | concluir 200 causa confirmada |
| [P4-CR-55](#p4-cr-55) | correcto | 409 | hipotesis 409 investigacion concluida |
| [P4-CR-56](#p4-cr-56) | correcto | 409 | accion 409 responsable no interno |
| [P4-CR-57](#p4-cr-57) | correcto | 400 | accion 400 fecha pasada |
| [P4-CR-58](#p4-cr-58) | correcto | 201 | accion 201: correctiva |
| [P4-CR-59](#p4-cr-59) | correcto | 201 | accion 201: preventiva |
| [P4-CR-60](#p4-cr-60) | correcto | 200 | acciones 200: las ve un operador |
| [P4-CR-61](#p4-cr-61) | correcto | 200 | acciones 200: cada responsable ve solo las suyas |
| [P4-CR-62](#p4-cr-62) | correcto | 200 | acciones 200: vencidas |
| [P4-CR-63](#p4-cr-63) | correcto | 400 | acciones 400 estado desconocido |
| [P4-CR-64](#p4-cr-64) | correcto | 200 | accion 200: detalle por su responsable |
| [P4-CR-65](#p4-cr-65) | correcto | 404 | accion 404 ajena: no revela que existe |
| [P4-CR-66](#p4-cr-66) | correcto | 409 | medir 409 accion no implementada |
| [P4-CR-67](#p4-cr-67) | correcto | 409 | cierre 409 con acciones sin medir |
| [P4-CR-68](#p4-cr-68) | correcto | 409 | accion 409 saltar a implementada |
| [P4-CR-69](#p4-cr-69) | correcto | 404 | accion 404 ajena no se mueve |
| [P4-CR-70](#p4-cr-70) | correcto | 200 | accion 200: en curso por su responsable |
| [P4-CR-71](#p4-cr-71) | correcto | 400 | accion 400 implementada en fecha futura |
| [P4-CR-72](#p4-cr-72) | correcto | 200 | accion 200: implementada |
| [P4-CR-73](#p4-cr-73) | correcto | 400 | accion 400 cancelar sin comentario |
| [P4-CR-74](#p4-cr-74) | correcto | 200 | accion 200: cancelada con motivo |
| [P4-CR-75](#p4-cr-75) | correcto | 403 | medir 403 inspector |
| [P4-CR-76](#p4-cr-76) | correcto | 400 | medir 400 ventana invalida |
| [P4-CR-77](#p4-cr-77) | correcto | 201 | medir 201: antes contra despues |
| [P4-CR-78](#p4-cr-78) | correcto | 200 | accion 200: detalle con su medicion |
| [P4-CR-79](#p4-cr-79) | correcto | 403 | cierre 403 analista |
| [P4-CR-80](#p4-cr-80) | correcto | 403 | cierre 403 sin reconfirmar la contrasena |
| [P4-CR-81](#p4-cr-81) | correcto | 403 | autorizar operacion 403 analista |
| [P4-CR-82](#p4-cr-82) | correcto | 401 | autorizar operacion 401 contrasena incorrecta |
| [P4-CR-83](#p4-cr-83) | correcto | 201 | autorizar operacion 201 sobre otro registro |
| [P4-CR-84](#p4-cr-84) | correcto | 403 | cierre 403 permiso de otro registro |
| [P4-CR-85](#p4-cr-85) | correcto | 201 | autorizar operacion 201 |
| [P4-CR-86](#p4-cr-86) | correcto | 400 | cierre 400 comentario corto |
| [P4-CR-87](#p4-cr-87) | correcto | 200 | cierre 200 por un supervisor distinto del analista |
| [P4-CR-88](#p4-cr-88) | correcto | 409 | cierre 409 ya cerrada |
| [P4-CR-89](#p4-cr-89) | correcto | 200 | detalle final: linea de tiempo completa |
| [P4-CR-90](#p4-cr-90) | correcto | 201 | investigacion manual 201 XML |
| [P4-CR-91](#p4-cr-91) | correcto | 409 | iniciar verificacion 409 sin hipotesis |
| [P4-CR-92](#p4-cr-92) | correcto | 201 | hipotesis 201 en la segunda investigacion |
| [P4-CR-93](#p4-cr-93) | correcto | 200 | iniciar verificacion 200 en la segunda |
| [P4-CR-94](#p4-cr-94) | correcto | 200 | verificar hipotesis 200: descartada en la segunda |
| [P4-CR-95](#p4-cr-95) | correcto | 409 | concluir 409 confirmar sin evidencia |
| [P4-CR-96](#p4-cr-96) | correcto | 200 | concluir 200 inconclusa |
| [P4-CR-97](#p4-cr-97) | correcto | 409 | accion 409 sin causa confirmada |
| [P4-CR-98](#p4-cr-98) | correcto | 409 | cierre 409 el analista no cierra lo suyo |
| [P4-CR-99](#p4-cr-99) | correcto | 200 | reabrir 200 una inconclusa |
| [P4-CR-100](#p4-cr-100) | correcto | 409 | reabrir 409 si no esta concluida inconclusa |

## P4-CR-01

**salud 200 JSON**

Objetivo: El servicio informa su estado y el de PostgreSQL y Redis (RF-32).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/health" \
  -H "Accept: application/json"
```

Respuesta - **200 OK** (16 ms, 143 bytes):

```http
Content-Type: application/json
Content-Length: 143
X-Correlation-ID: 913e3431b1384f96
```

```json
{
  "servicio": "causa-raiz",
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

## P4-CR-02

**salud 200 XML**

Objetivo: El mismo endpoint responde XML (RF-31).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/health" \
  -H "Accept: application/xml"
```

Respuesta - **200 OK** (16 ms, 246 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 246
X-Correlation-ID: ab9a668c2a7540ce
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<respuesta><servicio>causa-raiz</servicio><version>v1</version><estado>ok</estado><dependencias><postgresql><ok>true</ok><error /></postgresql><redis><ok>true</ok><error /></redis></dependencias></respuesta>
```

Verificaciones:

- ok: HTTP 200
- ok: es XML
- ok: estado ok

## P4-CR-03

**Swagger: documentacion de la API**

Objetivo: La API publica su documentacion Swagger.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/docs" \
  -H "Accept: text/html"
```

Respuesta - **200 OK** (9 ms, 443 bytes):

```http
Content-Type: text/html; charset=utf-8
Content-Length: 443
X-Correlation-ID: a62bdc7ce1f54e53
```

```text
<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Causa raiz y acciones correctivas</title>
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

## P4-CR-04

**Swagger: especificacion OpenAPI**

Objetivo: La especificacion lista el flujo completo de la investigacion.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/openapi.json" \
  -H "Accept: application/json"
```

Respuesta - **200 OK** (11 ms, 13457 bytes):

```http
Content-Type: application/json
Content-Length: 13457
X-Correlation-ID: 96b8d26f88554369
```

```json
{
  "openapi": "3.0.3",
  "info": {
    "title": "Causa raiz y acciones correctivas",
    "version": "v1",
    "description": "Flujo de investigacion de causa raiz de 9 pasos con acciones CAPA y medicion de eficacia. El analisis apoya; cada decision es humana (RN-09, RN-11). JSON o XML segun Accept; el XML se valida con los XSD de /contratos."
  },
  "servers": [
    {
      "url": "http://localhost:8011"
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
    "/api/v1/causa-raiz/alertas/detectar": {
      "post": {
        "summary": "Busca patrones y deja alertas (paso 1 y 2)",
        "description": "Una alerta exige tasa de al menos 2 veces el promedio, 20 unidades vendidas y 3 casos. Repetir la deteccion actualiza las alertas abiertas, no las duplica. Las alertas proponen; no abren investigaciones.",
        "responses": {
          "200": {
            "description": "Alertas nuevas y actualizadas"
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
    "/api/v1/causa-raiz/alertas": {
      "get": {
        "summary": "Alertas",
        "parameters": [
          {
            "name": "estado",
            "in": "query",
            "schema": {
              "type": "string",
              "enum": [
                "abierta",
                "investigando",
                "descartada"
              ]
            }
          },
          {
            "name": "dimension",
            "in": "query",
            "schema": {
              "type": "string",
              "enum": [
... (recortado: 1012 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: incluye el cierre
- ok: incluye la medicion

## P4-CR-05

**contrato XSD publicado**

Objetivo: El contrato XML de la investigacion se publica para que los clientes lo validen (RF-31).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/contratos/investigacion.xsd" \
  -H "Accept: application/xml"
```

Respuesta - **200 OK** (9 ms, 786 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 786
X-Correlation-ID: f09b2d316aff4430
Content-Disposition: inline; filename=investigacion.xsd
Cache-Control: no-cache
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Abrir una investigacion manual sobre un lote, proveedor, tienda o producto (POST /investigaciones). -->
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="investigacion">
    <xs:complexType>
      <xs:all>
        <xs:element name="dimension"><xs:simpleType><xs:restriction base="xs:string"><xs:enumeration value="lote"/><xs:enumeration value="proveedor"/><xs:enumeration value="tienda"/><xs:enumeration value="producto"/></xs:restriction></xs:simpleType></xs:element>
        <xs:element name="referencia_id" type="xs:positiveInteger"/>
        <xs:element name="titulo" type="xs:string"/>
        <xs:element name="descripcion" type="xs:string"/>
      </xs:all>
    </xs:complexType>
  </xs:element>
</xs:schema>

```

Verificaciones:

- ok: HTTP 200
- ok: es un esquema XSD

## P4-CR-06

**sin token: 401**

Objetivo: Un endpoint protegido exige JWT (RNF-09).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/api/v1/causa-raiz/alertas" \
  -H "Accept: application/json"
```

Respuesta - **401 UNAUTHORIZED** (8 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: eac5941d719e46f3
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "eac5941d719e46f3"
  }
}
```

Verificaciones:

- ok: HTTP 401
- ok: tipo no_autenticado

## P4-CR-07

**token invalido: 401**

Objetivo: Un token alterado se rechaza (RNF-09).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/api/v1/causa-raiz/alertas" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer no.es.un.jwt"
```

Respuesta - **401 UNAUTHORIZED** (7 ms, 136 bytes):

```http
Content-Type: application/json
Content-Length: 136
X-Correlation-ID: a53f6612dce843c8
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "token_invalido",
    "mensaje": "El token no es valido.",
    "detalles": null,
    "correlation_id": "a53f6612dce843c8"
  }
}
```

Verificaciones:

- ok: HTTP 401
- ok: tipo token_invalido

## P4-CR-08

**cliente: 403 en alertas**

Objetivo: Las alertas y las investigaciones son de Administrador, Analista y Supervisor (RN-13).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/api/v1/causa-raiz/alertas" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_CLIENTE"
```

Respuesta - **403 FORBIDDEN** (10 ms, 245 bytes):

```http
Content-Type: application/json
Content-Length: 245
X-Correlation-ID: db38144383fb4084
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
    "correlation_id": "db38144383fb4084"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-CR-09

**inspector: 403 en investigaciones**

Objetivo: El Inspector ve solo las acciones que se le asignan, no las investigaciones.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_INSPECTOR"
```

Respuesta - **403 FORBIDDEN** (10 ms, 247 bytes):

```http
Content-Type: application/json
Content-Length: 247
X-Correlation-ID: 28951aa12e5f47a1
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
        "Supervisor"
      ]
    },
    "correlation_id": "28951aa12e5f47a1"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-CR-10

**detectar patrones 200**

Objetivo: Paso 1: el sistema busca patrones raros (tasa >= 2x el promedio, 20 unidades, 3 casos). Repetirlo no duplica alertas.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/alertas/detectar" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (46 ms, 243 bytes):

```http
Content-Type: application/json
Content-Length: 243
X-Correlation-ID: 0909d61b629748a4
```

```json
{
  "alertas_nuevas": 0,
  "alertas_actualizadas": 1,
  "tasa_promedio_pct": 28.86,
  "criterio": {
    "veces_promedio_minimo": 2.0,
    "unidades_minimas": 20,
    "casos_minimos": 3
  },
  "aviso": "Las alertas proponen investigar; no abren investigaciones ni determinan causas."
}
```

Verificaciones:

- ok: HTTP 200
- ok: cuenta alertas nuevas
- ok: declara el criterio
- ok: aclara que no abre investigaciones

Efecto en PostgreSQL - alertas abiertas por dimension:

```sql
SELECT dimension, count(*) AS abiertas FROM alertas_patron WHERE estado = 'abierta' GROUP BY dimension ORDER BY 1
```

```text
dimension | abiertas
lote | 1
```

## P4-CR-11

**alertas 200: lote de la demo**

Objetivo: Paso 2: la alerta PROPONE investigar; ninguna investigacion se abre sola.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/api/v1/causa-raiz/alertas?estado=abierta&dimension=lote" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (22 ms, 459 bytes):

```http
Content-Type: application/json
Content-Length: 459
X-Correlation-ID: 70026137ba8b48c5
```

```json
{
  "datos": [
    {
      "id": 3,
      "dimension": "lote",
      "referencia_id": 15,
      "etiqueta": "L-2026-PROB-01 (Leche entera 1 L)",
      "unidades_vendidas": 24,
      "unidades_devueltas": 16,
      "casos": 4,
      "tasa_pct": 66.67,
      "tasa_promedio_pct": 28.86,
      "veces_promedio": 2.31,
      "estado": "abierta",
      "comentario": null,
      "fecha_deteccion": "2026-11-22T01:17:14.153886+00:00",
      "fecha_actualizacion": "2026-11-22T18:13:25.299567+00:00",
      "resuelta_por": null
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
- ok: incluye la alerta del lote de la demo
- ok: todas abiertas y de lotes
- ok: cumple el criterio de alerta

Efecto en PostgreSQL - ninguna investigacion existe aun sobre el lote:

```sql
SELECT count(*) AS investigaciones_del_lote FROM investigaciones WHERE dimension = 'lote' AND referencia_id = 15
```

```text
investigaciones_del_lote
0
```

## P4-CR-12

**alertas 200 XML**

Objetivo: El listado de alertas responde XML (RF-31).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/api/v1/causa-raiz/alertas?por_pagina=2" \
  -H "Accept: application/xml" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR"
```

Respuesta - **200 OK** (20 ms, 718 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 718
X-Correlation-ID: 06ecca03406e4017
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<alertas><datos><item><id>3</id><dimension>lote</dimension><referencia_id>15</referencia_id><etiqueta>L-2026-PROB-01 (Leche entera 1 L)</etiqueta><unidades_vendidas>24</unidades_vendidas><unidades_devueltas>16</unidades_devueltas><casos>4</casos><tasa_pct>66.67</tasa_pct><tasa_promedio_pct>28.86</tasa_promedio_pct><veces_promedio>2.31</veces_promedio><estado>abierta</estado><comentario /><fecha_deteccion>2026-11-22T01:17:14.153886+00:00</fecha_deteccion><fecha_actualizacion>2026-11-22T18:13:25.299567+00:00</fecha_actualizacion><resuelta_por /></item></datos><paginacion><pagina>1</pagina><por_pagina>2</por_pagina><total>1</total><paginas>1</paginas></paginacion></alertas>
```

Verificaciones:

- ok: HTTP 200
- ok: es XML
- ok: raiz alertas

## P4-CR-13

**alertas 400 dimension desconocida**

Objetivo: Un filtro fuera del catalogo se rechaza.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/api/v1/causa-raiz/alertas?dimension=planeta" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (9 ms, 132 bytes):

```http
Content-Type: application/json
Content-Length: 132
X-Correlation-ID: f53bfa0e5a1b4a16
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "dimension desconocido.",
    "detalles": null,
    "correlation_id": "f53bfa0e5a1b4a16"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CR-14

**descartar alerta 400 comentario corto**

Objetivo: Descartar una alerta exige explicar por que (minimo 10 caracteres).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/alertas/3/descartar" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"comentario":"no"}'
```

Respuesta - **400 BAD REQUEST** (10 ms, 186 bytes):

```http
Content-Type: application/json
Content-Length: 186
X-Correlation-ID: c6f4ebf961084245
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
        "problema": "entre 10 y 500 caracteres"
      }
    ],
    "correlation_id": "c6f4ebf961084245"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CR-15

**descartar alerta 404**

Objetivo: Una alerta inexistente responde 404.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/alertas/999999/descartar" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"comentario":"La alerta no existe en la base"}'
```

Respuesta - **404 NOT FOUND** (26 ms, 132 bytes):

```http
Content-Type: application/json
Content-Length: 132
X-Correlation-ID: 03ee786b80464540
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Alerta inexistente.",
    "detalles": null,
    "correlation_id": "03ee786b80464540"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-CR-16

**descartar alerta 200**

Objetivo: Una persona puede descartar una alerta con comentario; queda registrado quien.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/alertas/3/descartar" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"comentario":"Prueba de evidencia: se descarta y luego se restablece para seguir el flujo"}'
```

Respuesta - **200 OK** (31 ms, 31 bytes):

```http
Content-Type: application/json
Content-Length: 31
X-Correlation-ID: 220ba4618d0a4bc2
```

```json
{
  "id": 3,
  "estado": "descartada"
}
```

Verificaciones:

- ok: HTTP 200
- ok: queda descartada

Efecto en PostgreSQL - estado y autor de la alerta:

```sql
SELECT id, estado, comentario, resuelta_por FROM alertas_patron WHERE id = 3
```

```text
id | estado | comentario | resuelta_por
3 | descartada | Prueba de evidencia: se descarta y luego se restablece para seguir el flujo | 16
```

## P4-CR-17

**descartar alerta 409 ya resuelta**

Objetivo: Una alerta ya resuelta no se vuelve a resolver.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/alertas/3/descartar" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"comentario":"Segundo intento sobre la misma alerta"}'
```

Respuesta - **409 CONFLICT** (35 ms, 144 bytes):

```http
Content-Type: application/json
Content-Length: 144
X-Correlation-ID: 4f31642fad0b40ba
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "alerta_resuelta",
    "mensaje": "La alerta ya esta descartada.",
    "detalles": null,
    "correlation_id": "4f31642fad0b40ba"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo alerta_resuelta

## P4-CR-18

**investigar alerta descartada: 409**

Objetivo: Una alerta descartada ya no genera investigacion.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/alertas/3/investigar" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"titulo":"Evidencia P4: alerta descartada","descripcion":"No debe abrirse desde una alerta descartada"}'
```

Respuesta - **409 CONFLICT** (35 ms, 144 bytes):

```http
Content-Type: application/json
Content-Length: 144
X-Correlation-ID: 71a7de3f7b8c4ed8
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "alerta_resuelta",
    "mensaje": "La alerta ya esta descartada.",
    "detalles": null,
    "correlation_id": "71a7de3f7b8c4ed8"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo alerta_resuelta

Efecto en PostgreSQL - paso preparatorio de la evidencia: la alerta vuelve a abierta para continuar el flujo:

```sql
UPDATE alertas_patron SET estado = 'abierta', comentario = NULL, resuelta_por = NULL WHERE id = 3 RETURNING id, estado
```

```text
id | estado
3 | abierta
UPDATE 1
```

## P4-CR-19

**investigar alerta 400 campo no permitido**

Objetivo: Desde una alerta el objeto ya viene dado; mandar otro se rechaza.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/alertas/3/investigar" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"titulo":"Evidencia P4: lote","descripcion":"El objeto lo define la alerta, no el cliente","dimension":"proveedor"}'
```

Respuesta - **400 BAD REQUEST** (23 ms, 178 bytes):

```http
Content-Type: application/json
Content-Length: 178
X-Correlation-ID: ac1365d06a584f77
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Campos invalidos.",
    "detalles": [
      {
        "campo": "dimension",
        "problema": "campo no permitido"
      }
    ],
    "correlation_id": "ac1365d06a584f77"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CR-20

**investigar alerta 201**

Objetivo: Paso 3: una persona decide abrir la investigacion que la alerta propone. Queda con folio y linea base.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/alertas/3/investigar" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"titulo":"Evidencia P4: leche del lote de la demo","descripcion":"Cuatro ventas del mismo lote concentran las devoluciones; se investiga la cadena de frio"}'
```

Respuesta - **201 CREATED** (65 ms, 186 bytes):

```http
Content-Type: application/json
Content-Length: 186
X-Correlation-ID: f1157cd1ff254da5
Location: /api/v1/causa-raiz/investigaciones/6
```

```json
{
  "id": 6,
  "folio": "INV-2026-0006",
  "estado": "abierta",
  "linea_base": {
    "unidades_vendidas": 24,
    "unidades_devueltas": 16,
    "casos": 4,
    "tasa_pct": 66.67,
    "fecha_corte": "2026-11-22",
    "origen": "alerta"
  }
}
```

Verificaciones:

- ok: HTTP 201
- ok: nace abierta
- ok: folio INV-
- ok: guarda la linea base
- ok: trae Location

Efecto en PostgreSQL - investigacion, alerta enlazada y primer evento de la linea de tiempo:

```sql
SELECT i.folio, i.estado, i.dimension, i.alerta_id, a.estado AS estado_alerta, (SELECT count(*) FROM seguimiento_investigacion s WHERE s.investigacion_id = i.id) AS eventos FROM investigaciones i JOIN alertas_patron a ON a.id = i.alerta_id WHERE i.id = 6
```

```text
folio | estado | dimension | alerta_id | estado_alerta | eventos
INV-2026-0006 | abierta | lote | 3 | investigando | 1
```

## P4-CR-21

**investigar alerta 409 ya en investigacion**

Objetivo: Una alerta se investiga una sola vez.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/alertas/3/investigar" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"titulo":"Evidencia P4: duplicada","descripcion":"La alerta ya tiene una investigacion en curso"}'
```

Respuesta - **409 CONFLICT** (22 ms, 146 bytes):

```http
Content-Type: application/json
Content-Length: 146
X-Correlation-ID: b8ec1da6b4474e96
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "alerta_resuelta",
    "mensaje": "La alerta ya esta investigando.",
    "detalles": null,
    "correlation_id": "b8ec1da6b4474e96"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo alerta_resuelta

## P4-CR-22

**investigacion manual 409 objeto ya investigado**

Objetivo: Un objeto no tiene dos investigaciones sin cerrar.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"dimension":"lote","referencia_id":15,"titulo":"Evidencia P4: duplicada manual","descripcion":"Intento de abrir otra investigacion sobre el mismo lote"}'
```

Respuesta - **409 CONFLICT** (21 ms, 169 bytes):

```http
Content-Type: application/json
Content-Length: 169
X-Correlation-ID: 61932ceff2bb4e17
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "investigacion_activa",
    "mensaje": "Ese objeto ya tiene una investigacion sin cerrar.",
    "detalles": null,
    "correlation_id": "61932ceff2bb4e17"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo investigacion_activa

## P4-CR-23

**investigacion manual 400 dimension invalida**

Objetivo: La dimension debe ser lote, proveedor, tienda o producto.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"dimension":"planeta","referencia_id":1,"titulo":"Evidencia P4: invalida","descripcion":"La dimension no existe en el catalogo"}'
```

Respuesta - **400 BAD REQUEST** (10 ms, 203 bytes):

```http
Content-Type: application/json
Content-Length: 203
X-Correlation-ID: fce4e2be9aeb4d76
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Campos invalidos.",
    "detalles": [
      {
        "campo": "dimension",
        "problema": "debe ser: lote, proveedor, tienda, producto"
      }
    ],
    "correlation_id": "fce4e2be9aeb4d76"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CR-24

**investigacion manual 404 objeto inexistente**

Objetivo: No se investiga un objeto que no existe.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"dimension":"lote","referencia_id":999999,"titulo":"Evidencia P4: lote fantasma","descripcion":"El lote no existe en la base"}'
```

Respuesta - **404 NOT FOUND** (19 ms, 139 bytes):

```http
Content-Type: application/json
Content-Length: 139
X-Correlation-ID: 754a2db2a6ff45e5
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe lote con ese id.",
    "detalles": null,
    "correlation_id": "754a2db2a6ff45e5"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-CR-25

**listado de investigaciones 200**

Objetivo: Listado filtrable con conteo de hipotesis, evidencias y acciones.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones?estado=abierta&dimension=lote" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (26 ms, 463 bytes):

```http
Content-Type: application/json
Content-Length: 463
X-Correlation-ID: 1ec201027cc04b52
```

```json
{
  "datos": [
    {
      "id": 6,
      "folio": "INV-2026-0006",
      "titulo": "Evidencia P4: leche del lote de la demo",
      "dimension": "lote",
      "referencia_id": 15,
      "etiqueta": "L-2026-PROB-01 (Leche entera 1 L)",
      "estado": "abierta",
      "conclusion": null,
      "veredicto_final": null,
      "analista_id": 16,
      "analista": "Josue Berdeal",
      "fecha_creacion": "2026-11-22T18:13:26.676471+00:00",
      "fecha_cierre": null,
      "hipotesis": 0,
      "evidencias": 0,
      "acciones": 0
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
- ok: incluye la investigacion
- ok: trae conteos

## P4-CR-26

**listado de investigaciones 200 XML**

Objetivo: El listado responde XML (RF-31).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones?por_pagina=2" \
  -H "Accept: application/xml" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR"
```

Respuesta - **200 OK** (25 ms, 688 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 688
X-Correlation-ID: 94b9d9c40c2849c5
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<investigaciones><datos><item><id>6</id><folio>INV-2026-0006</folio><titulo>Evidencia P4: leche del lote de la demo</titulo><dimension>lote</dimension><referencia_id>15</referencia_id><etiqueta>L-2026-PROB-01 (Leche entera 1 L)</etiqueta><estado>abierta</estado><conclusion /><veredicto_final /><analista_id>16</analista_id><analista>Josue Berdeal</analista><fecha_creacion>2026-11-22T18:13:26.676471+00:00</fecha_creacion><fecha_cierre /><hipotesis>0</hipotesis><evidencias>0</evidencias><acciones>0</acciones></item></datos><paginacion><pagina>1</pagina><por_pagina>2</por_pagina><total>1</total><paginas>1</paginas></paginacion></investigaciones>
```

Verificaciones:

- ok: HTTP 200
- ok: es XML

## P4-CR-27

**listado de investigaciones 400 estado desconocido**

Objetivo: Un estado fuera del catalogo se rechaza.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones?estado=dormida" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (9 ms, 129 bytes):

```http
Content-Type: application/json
Content-Length: 129
X-Correlation-ID: 45d5e4cf77b14ade
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "estado desconocido.",
    "detalles": null,
    "correlation_id": "45d5e4cf77b14ade"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CR-28

**detalle de investigacion 404**

Objetivo: Una investigacion inexistente responde 404.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/999999" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **404 NOT FOUND** (18 ms, 139 bytes):

```http
Content-Type: application/json
Content-Length: 139
X-Correlation-ID: 1ea3c36f1e574e3b
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Investigacion inexistente.",
    "detalles": null,
    "correlation_id": "1ea3c36f1e574e3b"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-CR-29

**hipotesis 400 tipo invalido**

Objetivo: El tipo es cinco_porques, ishikawa o libre.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/hipotesis" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"tipo":"adivinanza","descripcion":"Esto no es un tipo valido de hipotesis"}'
```

Respuesta - **400 BAD REQUEST** (21 ms, 156 bytes):

```http
Content-Type: application/json
Content-Length: 156
X-Correlation-ID: 5a785dc10d62487a
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "tipo debe ser: cinco_porques, ishikawa, libre.",
    "detalles": null,
    "correlation_id": "5a785dc10d62487a"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CR-30

**hipotesis 201: primer porque**

Objetivo: Paso 4: el primer porque es el nivel 1; el nivel lo calcula el servicio.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/hipotesis" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"tipo":"cinco_porques","descripcion":"Las devoluciones se concentran en el lote porque la leche llego tibia"}'
```

Respuesta - **201 CREATED** (24 ms, 43 bytes):

```http
Content-Type: application/json
Content-Length: 43
X-Correlation-ID: 18a04f448b2e4fa7
```

```json
{
  "id": 14,
  "tipo": "cinco_porques",
  "nivel": 1
}
```

Verificaciones:

- ok: HTTP 201
- ok: nivel 1

## P4-CR-31

**hipotesis 201: segundo porque**

Objetivo: Un porque con padre es el nivel siguiente.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/hipotesis" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"tipo":"cinco_porques","padre_id":14,"descripcion":"Llego tibia porque el camion no mantuvo la cadena de frio"}'
```

Respuesta - **201 CREATED** (25 ms, 43 bytes):

```http
Content-Type: application/json
Content-Length: 43
X-Correlation-ID: 6d1e52f8b7414d41
```

```json
{
  "id": 15,
  "tipo": "cinco_porques",
  "nivel": 2
}
```

Verificaciones:

- ok: HTTP 201
- ok: nivel 2

## P4-CR-32

**hipotesis 409 porque ya con continuacion**

Objetivo: La cadena no se ramifica: cada porque tiene una sola continuacion.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/hipotesis" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"tipo":"cinco_porques","padre_id":14,"descripcion":"Otro porque para el mismo padre, sin ramificar"}'
```

Respuesta - **409 CONFLICT** (23 ms, 160 bytes):

```http
Content-Type: application/json
Content-Length: 160
X-Correlation-ID: 140174bf3b394267
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "porque_con_continuacion",
    "mensaje": "Ese porque ya tiene una continuacion.",
    "detalles": null,
    "correlation_id": "140174bf3b394267"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo porque_con_continuacion

## P4-CR-33

**hipotesis 409 porque padre inexistente**

Objetivo: El porque anterior debe existir en esta investigacion.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/hipotesis" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"tipo":"cinco_porques","padre_id":999999,"descripcion":"Continuacion de un porque que no existe"}'
```

Respuesta - **409 CONFLICT** (20 ms, 165 bytes):

```http
Content-Type: application/json
Content-Length: 165
X-Correlation-ID: c6aa00dcdae54d0d
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "padre_invalido",
    "mensaje": "El porque anterior no existe en esta investigacion.",
    "detalles": null,
    "correlation_id": "c6aa00dcdae54d0d"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo padre_invalido

## P4-CR-34

**hipotesis 400 Ishikawa sin categoria**

Objetivo: Una hipotesis Ishikawa indica su categoria (6M).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/hipotesis" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"tipo":"ishikawa","descripcion":"Falta decir a que rama del diagrama pertenece"}'
```

Respuesta - **400 BAD REQUEST** (21 ms, 244 bytes):

```http
Content-Type: application/json
Content-Length: 244
X-Correlation-ID: 0577b4ca6d3e45ca
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Campos invalidos.",
    "detalles": [
      {
        "campo": "categoria_ishikawa",
        "problema": "debe ser: material, metodo, maquina, mano_de_obra, medicion, medio_ambiente"
      }
    ],
    "correlation_id": "0577b4ca6d3e45ca"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CR-35

**hipotesis 201: Ishikawa**

Objetivo: Hipotesis en una rama del diagrama de Ishikawa.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/hipotesis" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"tipo":"ishikawa","categoria_ishikawa":"metodo","descripcion":"El metodo de carga no respeta el tiempo maximo fuera de refrigeracion"}'
```

Respuesta - **201 CREATED** (24 ms, 41 bytes):

```http
Content-Type: application/json
Content-Length: 41
X-Correlation-ID: f4a56d9915f14514
```

```json
{
  "id": 16,
  "tipo": "ishikawa",
  "nivel": null
}
```

Verificaciones:

- ok: HTTP 201
- ok: sin nivel de porque

## P4-CR-36

**hipotesis 201 XML: libre**

Objetivo: La misma alta en XML, validada contra su XSD (RF-31).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/hipotesis" \
  -H "Accept: application/xml" \
  -H "Content-Type: application/xml" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '<hipotesis><tipo>libre</tipo><descripcion>Un lote de empaque defectuoso podria explicar las bolsas danadas</descripcion></hipotesis>'
```

Respuesta - **201 CREATED** (24 ms, 100 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 100
X-Correlation-ID: 8f0969168e47457f
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<hipotesis><id>17</id><tipo>libre</tipo><nivel /></hipotesis>
```

Verificaciones:

- ok: HTTP 201
- ok: es XML

## P4-CR-37

**evidencia 400 devolucion sin devolucion_id**

Objetivo: Una evidencia de tipo devolucion o inspeccion apunta a una devolucion.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/evidencias" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"tipo":"devolucion","descripcion":"Falta indicar cual devolucion respalda"}'
```

Respuesta - **400 BAD REQUEST** (9 ms, 190 bytes):

```http
Content-Type: application/json
Content-Length: 190
X-Correlation-ID: 330d4c2279134b5c
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Campos invalidos.",
    "detalles": [
      {
        "campo": "devolucion_id",
        "problema": "obligatorio para este tipo"
      }
    ],
    "correlation_id": "330d4c2279134b5c"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CR-38

**evidencia 409 devolucion de otro lote**

Objetivo: La evidencia debe pertenecer al objeto que se investiga.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/evidencias" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"tipo":"devolucion","descripcion":"Devolucion que no es de este lote","devolucion_id":1}'
```

Respuesta - **409 CONFLICT** (23 ms, 182 bytes):

```http
Content-Type: application/json
Content-Length: 182
X-Correlation-ID: a03e72655eb04015
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "devolucion_ajena",
    "mensaje": "La devolucion no pertenece al objeto que se investiga o no existe.",
    "detalles": null,
    "correlation_id": "a03e72655eb04015"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo devolucion_ajena

## P4-CR-39

**evidencia 409 hipotesis ajena**

Objetivo: Una evidencia solo se liga a hipotesis de su investigacion.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/evidencias" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"tipo":"nota","descripcion":"Apunta a una hipotesis que no es de esta investigacion","hipotesis_id":999999}'
```

Respuesta - **409 CONFLICT** (22 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: a344c02367b04b76
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "hipotesis_ajena",
    "mensaje": "La hipotesis no pertenece a esta investigacion.",
    "detalles": null,
    "correlation_id": "a344c02367b04b76"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo hipotesis_ajena

## P4-CR-40

**evidencia 201: devolucion del lote**

Objetivo: Evidencia ligada a una devolucion real del lote y a la primera hipotesis.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/evidencias" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"tipo":"devolucion","descripcion":"Devolucion del lote reportada con producto tibio al recibirlo","devolucion_id":105,"hipotesis_id":14}'
```

Respuesta - **201 CREATED** (48 ms, 29 bytes):

```http
Content-Type: application/json
Content-Length: 29
X-Correlation-ID: 04348762762b4f7f
```

```json
{
  "id": 6,
  "tipo": "devolucion"
}
```

Verificaciones:

- ok: HTTP 201

Efecto en PostgreSQL - la evidencia guardada:

```sql
SELECT id, tipo, hipotesis_id, devolucion_id FROM evidencias_investigacion WHERE id = 6
```

```text
id | tipo | hipotesis_id | devolucion_id
6 | devolucion | 14 | 105
```

## P4-CR-41

**evidencia 201: nota**

Objetivo: Una nota de campo con referencia externa.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/evidencias" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"tipo":"nota","descripcion":"El chofer confirma que la unidad estuvo detenida 40 minutos sin refrigeracion","referencia_externa":"bitacora-ruta-0412"}'
```

Respuesta - **201 CREATED** (61 ms, 23 bytes):

```http
Content-Type: application/json
Content-Length: 23
X-Correlation-ID: 736be450afdd4198
```

```json
{
  "id": 7,
  "tipo": "nota"
}
```

Verificaciones:

- ok: HTTP 201
- ok: tipo nota

## P4-CR-42

**detalle de investigacion 200**

Objetivo: Una sola respuesta reune hipotesis, evidencias, acciones y linea de tiempo; recuerda que la conclusion es humana (RN-09).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (83 ms, 2670 bytes):

```http
Content-Type: application/json
Content-Length: 2670
X-Correlation-ID: 121be0569fdf439d
```

```json
{
  "id": 6,
  "folio": "INV-2026-0006",
  "alerta_id": 3,
  "dimension": "lote",
  "referencia_id": 15,
  "etiqueta": "L-2026-PROB-01 (Leche entera 1 L)",
  "titulo": "Evidencia P4: leche del lote de la demo",
  "descripcion": "Cuatro ventas del mismo lote concentran las devoluciones; se investiga la cadena de frio",
  "estado": "abierta",
  "analista_id": 16,
  "linea_base": {
    "casos": 4,
    "origen": "alerta",
    "tasa_pct": 66.67,
    "fecha_corte": "2026-11-22",
    "unidades_vendidas": 24,
    "unidades_devueltas": 16
  },
  "conclusion": null,
  "causa_raiz": null,
  "justificacion": null,
  "fecha_conclusion": null,
  "cerrada_por": null,
  "comentario_cierre": null,
  "veredicto_final": null,
  "fecha_creacion": "2026-11-22T18:13:26.676471+00:00",
  "fecha_cierre": null,
  "analista": "Josue Berdeal",
  "cerrada_por_nombre": null,
  "hipotesis": [
    {
      "id": 14,
      "tipo": "cinco_porques",
      "nivel": 1,
      "padre_id": null,
      "categoria_ishikawa": null,
      "descripcion": "Las devoluciones se concentran en el lote porque la leche llego tibia",
      "estado": "propuesta",
      "resultado_verificacion": null,
      "fecha_verificacion": null,
      "verificada_por": null
    },
    {
      "id": 15,
      "tipo": "cinco_porques",
      "nivel": 2,
      "padre_id": 14,
      "categoria_ishikawa": null,
      "descripcion": "Llego tibia porque el camion no mantuvo la cadena de frio",
      "estado": "propuesta",
      "resultado_verificacion": null,
      "fecha_verificacion": null,
      "verificada_por": null
    },
    {
      "id": 16,
      "tipo": "ishikawa",
      "nivel": null,
      "padre_id": null,
      "categoria_ishikawa": "metodo",
      "descripcion": "El metodo de carga no respeta el tiempo maximo fuera de refrigeracion",
      "estado": "propuesta",
      "resultado_verificacion": null,
      "fecha_verificacion": null,
      "verificada_por": null
    },
    {
      "id": 17,
      "tipo": "libre",
... (recortado: 46 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: 4 hipotesis
- ok: 2 evidencias
- ok: la evidencia trae el folio de la devolucion
- ok: aviso de RN-09

## P4-CR-43

**concluir 409 sin pasar por verificacion**

Objetivo: No se salta de abierta a concluida: el estado avanza paso a paso.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/conclusion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"conclusion":"inconclusa","justificacion":"Todavia no se verifico ninguna hipotesis"}'
```

Respuesta - **409 CONFLICT** (42 ms, 174 bytes):

```http
Content-Type: application/json
Content-Length: 174
X-Correlation-ID: 1d5110eb5d6a4811
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "transicion_invalida",
    "mensaje": "La investigacion no puede pasar de abierta a concluida.",
    "detalles": null,
    "correlation_id": "1d5110eb5d6a4811"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo transicion_invalida

## P4-CR-44

**iniciar verificacion 200**

Objetivo: Paso 5: pasa de juntar evidencia a verificar las hipotesis.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/verificacion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{}'
```

Respuesta - **200 OK** (43 ms, 36 bytes):

```http
Content-Type: application/json
Content-Length: 36
X-Correlation-ID: 1dbc6745abf94291
```

```json
{
  "id": 6,
  "estado": "en_verificacion"
}
```

Verificaciones:

- ok: HTTP 200
- ok: en_verificacion

## P4-CR-45

**iniciar verificacion 409 repetida**

Objetivo: No se puede iniciar dos veces.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/verificacion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{}'
```

Respuesta - **409 CONFLICT** (27 ms, 188 bytes):

```http
Content-Type: application/json
Content-Length: 188
X-Correlation-ID: 051b8fbfaec64e20
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "transicion_invalida",
    "mensaje": "La investigacion no puede pasar de en_verificacion a en_verificacion.",
    "detalles": null,
    "correlation_id": "051b8fbfaec64e20"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo transicion_invalida

## P4-CR-46

**concluir 409 sin hipotesis verificada**

Objetivo: Confirmar una causa exige al menos una hipotesis verificada (RN-09).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/conclusion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"conclusion":"causa_confirmada","causa_raiz":"El camion no mantuvo la cadena de frio","justificacion":"Hay evidencia pero ninguna hipotesis verificada"}'
```

Respuesta - **409 CONFLICT** (26 ms, 184 bytes):

```http
Content-Type: application/json
Content-Length: 184
X-Correlation-ID: 05a8001068014c84
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "sin_hipotesis_verificada",
    "mensaje": "Confirmar una causa exige al menos una hipotesis verificada.",
    "detalles": null,
    "correlation_id": "05a8001068014c84"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo sin_hipotesis_verificada

## P4-CR-47

**verificar hipotesis 400 resultado invalido**

Objetivo: El resultado es verificada o descartada.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/hipotesis/14/verificacion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"resultado":"quizas","resultado_verificacion":"El resultado no es verificada ni descartada"}'
```

Respuesta - **400 BAD REQUEST** (10 ms, 153 bytes):

```http
Content-Type: application/json
Content-Length: 153
X-Correlation-ID: ad3b2e1dacf64082
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "resultado debe ser verificada o descartada.",
    "detalles": null,
    "correlation_id": "ad3b2e1dacf64082"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CR-48

**verificar hipotesis 404 inexistente**

Objetivo: Solo se verifican hipotesis de la propia investigacion.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/hipotesis/999999/verificacion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"resultado":"verificada","resultado_verificacion":"La hipotesis no existe en esta investigacion"}'
```

Respuesta - **404 NOT FOUND** (23 ms, 157 bytes):

```http
Content-Type: application/json
Content-Length: 157
X-Correlation-ID: 5b939b1f6e8b4cd5
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Hipotesis inexistente en esta investigacion.",
    "detalles": null,
    "correlation_id": "5b939b1f6e8b4cd5"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-CR-49

**verificar hipotesis 200: verificada**

Objetivo: La hipotesis se verifica con informacion adicional; queda quien y cuando.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/hipotesis/14/verificacion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"resultado":"verificada","resultado_verificacion":"El registro del termometro del camion confirma 14 C durante 40 minutos"}'
```

Respuesta - **200 OK** (23 ms, 32 bytes):

```http
Content-Type: application/json
Content-Length: 32
X-Correlation-ID: 64dac20447aa43cc
```

```json
{
  "id": 14,
  "estado": "verificada"
}
```

Verificaciones:

- ok: HTTP 200
- ok: verificada

Efecto en PostgreSQL - estado de las hipotesis:

```sql
SELECT id, tipo, nivel, estado, verificada_por IS NOT NULL AS tiene_autor FROM hipotesis WHERE investigacion_id = 6 ORDER BY id
```

```text
id | tipo | nivel | estado | tiene_autor
14 | cinco_porques | 1 | verificada | t
15 | cinco_porques | 2 | propuesta | f
16 | ishikawa |  | propuesta | f
17 | libre |  | propuesta | f
```

## P4-CR-50

**verificar hipotesis 409 ya verificada**

Objetivo: Una hipotesis verificada no se reescribe.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/hipotesis/14/verificacion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"resultado":"descartada","resultado_verificacion":"Intento de cambiar una hipotesis ya verificada"}'
```

Respuesta - **409 CONFLICT** (20 ms, 145 bytes):

```http
Content-Type: application/json
Content-Length: 145
X-Correlation-ID: 390d4b4625094062
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "ya_verificada",
    "mensaje": "La hipotesis ya esta verificada.",
    "detalles": null,
    "correlation_id": "390d4b4625094062"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo ya_verificada

## P4-CR-51

**verificar hipotesis 200: descartada**

Objetivo: Descartar tambien es un resultado valido y queda asentado.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/hipotesis/17/verificacion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"resultado":"descartada","resultado_verificacion":"El empaque del lote cumple con la inspeccion de recepcion"}'
```

Respuesta - **200 OK** (23 ms, 32 bytes):

```http
Content-Type: application/json
Content-Length: 32
X-Correlation-ID: 814bd6902305408a
```

```json
{
  "id": 17,
  "estado": "descartada"
}
```

Verificaciones:

- ok: HTTP 200
- ok: descartada

## P4-CR-52

**concluir 400 causa confirmada sin causa**

Objetivo: Confirmar una causa exige describirla.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/conclusion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"conclusion":"causa_confirmada","justificacion":"Falta declarar cual es la causa raiz"}'
```

Respuesta - **400 BAD REQUEST** (28 ms, 172 bytes):

```http
Content-Type: application/json
Content-Length: 172
X-Correlation-ID: 57d178f7bebb4c72
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Campos invalidos.",
    "detalles": [
      {
        "campo": "causa_raiz",
        "problema": "obligatorio"
      }
    ],
    "correlation_id": "57d178f7bebb4c72"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CR-53

**concluir 400 inconclusa con causa**

Objetivo: Una investigacion inconclusa no inventa una causa (RN-09).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/conclusion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"conclusion":"inconclusa","causa_raiz":"No deberia declarar causa","justificacion":"Una inconclusa no declara causa"}'
```

Respuesta - **400 BAD REQUEST** (29 ms, 206 bytes):

```http
Content-Type: application/json
Content-Length: 206
X-Correlation-ID: ccca4b1b86a84db1
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Campos invalidos.",
    "detalles": [
      {
        "campo": "causa_raiz",
        "problema": "una investigacion inconclusa no declara causa"
      }
    ],
    "correlation_id": "ccca4b1b86a84db1"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CR-54

**concluir 200 causa confirmada**

Objetivo: Paso 6: causa confirmada, con evidencia y una hipotesis verificada. La decide una persona, no el sistema.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/conclusion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"conclusion":"causa_confirmada","causa_raiz":"El camion de reparto no mantuvo la cadena de frio durante una parada de 40 minutos","justificacion":"Hipotesis verificada con el termometro del camion y una devolucion del lote con producto tibio"}'
```

Respuesta - **200 OK** (40 ms, 62 bytes):

```http
Content-Type: application/json
Content-Length: 62
X-Correlation-ID: d4e02fec50424f80
```

```json
{
  "id": 6,
  "estado": "concluida",
  "conclusion": "causa_confirmada"
}
```

Verificaciones:

- ok: HTTP 200
- ok: concluida
- ok: causa confirmada

## P4-CR-55

**hipotesis 409 investigacion concluida**

Objetivo: Una investigacion concluida deja de editarse.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/hipotesis" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"tipo":"libre","descripcion":"Ya no se agregan hipotesis tras concluir"}'
```

Respuesta - **409 CONFLICT** (28 ms, 194 bytes):

```http
Content-Type: application/json
Content-Length: 194
X-Correlation-ID: 695c4c494f024ad4
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "investigacion_no_editable",
    "mensaje": "No se agregan hipotesis ni evidencias en una investigacion concluida.",
    "detalles": null,
    "correlation_id": "695c4c494f024ad4"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo investigacion_no_editable

## P4-CR-56

**accion 409 responsable no interno**

Objetivo: El responsable debe ser personal interno activo (RN-13).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/acciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"tipo":"correctiva","descripcion":"Responsable que es un cliente, no personal interno","responsable_id":10,"fecha_compromiso":"2026-12-22"}'
```

Respuesta - **409 CONFLICT** (30 ms, 168 bytes):

```http
Content-Type: application/json
Content-Length: 168
X-Correlation-ID: 2e92dd54b44a4261
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "responsable_invalido",
    "mensaje": "El responsable debe ser personal interno activo.",
    "detalles": null,
    "correlation_id": "2e92dd54b44a4261"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo responsable_invalido

## P4-CR-57

**accion 400 fecha pasada**

Objetivo: Toda accion tiene fecha compromiso futura.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/acciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"tipo":"correctiva","descripcion":"La fecha compromiso no puede estar en el pasado","responsable_id":13,"fecha_compromiso":"2020-01-01"}'
```

Respuesta - **400 BAD REQUEST** (10 ms, 201 bytes):

```http
Content-Type: application/json
Content-Length: 201
X-Correlation-ID: 439022df96c946a3
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Campos invalidos.",
    "detalles": [
      {
        "campo": "fecha_compromiso",
        "problema": "fecha AAAA-MM-DD que no sea pasada"
      }
    ],
    "correlation_id": "439022df96c946a3"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CR-58

**accion 201: correctiva**

Objetivo: Paso 7: accion CAPA con responsable, fecha compromiso y meta medible. La investigacion pasa a en_accion.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/acciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"tipo":"correctiva","descripcion":"Exigir registro de temperatura en cada parada del camion de reparto","responsable_id":13,"fecha_compromiso":"2026-12-22","meta_reduccion_pct":"30"}'
```

Respuesta - **201 CREATED** (28 ms, 57 bytes):

```http
Content-Type: application/json
Content-Length: 57
X-Correlation-ID: 136662fa03d141a3
Location: /api/v1/causa-raiz/acciones/6
```

```json
{
  "id": 6,
  "folio": "CAPA-2026-0006",
  "estado": "planificada"
}
```

Verificaciones:

- ok: HTTP 201
- ok: folio CAPA-
- ok: planificada

Efecto en PostgreSQL - la investigacion avanza a en_accion:

```sql
SELECT folio, estado FROM investigaciones WHERE id = 6
```

```text
folio | estado
INV-2026-0006 | en_accion
```

## P4-CR-59

**accion 201: preventiva**

Objetivo: Una accion preventiva; sin meta, usa la predeterminada de 30%.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/acciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"tipo":"preventiva","descripcion":"Auditar trimestralmente los termometros de la flota","responsable_id":17,"fecha_compromiso":"2026-12-22"}'
```

Respuesta - **201 CREATED** (32 ms, 57 bytes):

```http
Content-Type: application/json
Content-Length: 57
X-Correlation-ID: b08e689a4cd64c94
Location: /api/v1/causa-raiz/acciones/7
```

```json
{
  "id": 7,
  "folio": "CAPA-2026-0007",
  "estado": "planificada"
}
```

Verificaciones:

- ok: HTTP 201

## P4-CR-60

**acciones 200: las ve un operador**

Objetivo: Los operadores ven todas las acciones de una investigacion.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/api/v1/causa-raiz/acciones?investigacion_id=6" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (28 ms, 930 bytes):

```http
Content-Type: application/json
Content-Length: 930
X-Correlation-ID: db9371e7f72849ec
```

```json
{
  "datos": [
    {
      "id": 6,
      "folio": "CAPA-2026-0006",
      "investigacion_id": 6,
      "tipo": "correctiva",
      "descripcion": "Exigir registro de temperatura en cada parada del camion de reparto",
      "responsable_id": 13,
      "responsable": "Valentina Perez",
      "fecha_compromiso": "2026-12-22",
      "estado": "planificada",
      "meta_reduccion_pct": 30.0,
      "fecha_implementacion": null,
      "comentario_cierre": null,
      "vencida": false,
      "ultimo_veredicto": null,
      "ultima_reduccion_pct": null,
      "ultima_medicion": null
    },
    {
      "id": 7,
      "folio": "CAPA-2026-0007",
      "investigacion_id": 6,
      "tipo": "preventiva",
      "descripcion": "Auditar trimestralmente los termometros de la flota",
      "responsable_id": 17,
      "responsable": "Carla Trevino",
      "fecha_compromiso": "2026-12-22",
      "estado": "planificada",
      "meta_reduccion_pct": 30.0,
      "fecha_implementacion": null,
      "comentario_cierre": null,
      "vencida": false,
      "ultimo_veredicto": null,
      "ultima_reduccion_pct": null,
      "ultima_medicion": null
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
- ok: dos acciones
- ok: traen responsable

## P4-CR-61

**acciones 200: cada responsable ve solo las suyas**

Objetivo: El Inspector, responsable de una accion, ve solo la suya (RN-13).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/api/v1/causa-raiz/acciones" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_INSPECTOR"
```

Respuesta - **200 OK** (26 ms, 512 bytes):

```http
Content-Type: application/json
Content-Length: 512
X-Correlation-ID: 5db8e942a3a34806
```

```json
{
  "datos": [
    {
      "id": 6,
      "folio": "CAPA-2026-0006",
      "investigacion_id": 6,
      "tipo": "correctiva",
      "descripcion": "Exigir registro de temperatura en cada parada del camion de reparto",
      "responsable_id": 13,
      "responsable": "Valentina Perez",
      "fecha_compromiso": "2026-12-22",
      "estado": "planificada",
      "meta_reduccion_pct": 30.0,
      "fecha_implementacion": null,
      "comentario_cierre": null,
      "vencida": false,
      "ultimo_veredicto": null,
      "ultima_reduccion_pct": null,
      "ultima_medicion": null
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
- ok: solo acciones suyas

## P4-CR-62

**acciones 200: vencidas**

Objetivo: Filtra las acciones con fecha compromiso pasada y sin terminar.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/api/v1/causa-raiz/acciones?vencidas=true" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **200 OK** (26 ms, 77 bytes):

```http
Content-Type: application/json
Content-Length: 77
X-Correlation-ID: c6433c6c97df496b
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
- ok: todas marcadas vencidas

## P4-CR-63

**acciones 400 estado desconocido**

Objetivo: Un estado fuera del catalogo se rechaza.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/api/v1/causa-raiz/acciones?estado=dormida" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA"
```

Respuesta - **400 BAD REQUEST** (9 ms, 129 bytes):

```http
Content-Type: application/json
Content-Length: 129
X-Correlation-ID: 17d1f6a56223410d
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "estado desconocido.",
    "detalles": null,
    "correlation_id": "17d1f6a56223410d"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CR-64

**accion 200: detalle por su responsable**

Objetivo: El responsable consulta su accion con sus mediciones.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/api/v1/causa-raiz/acciones/6" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_INSPECTOR"
```

Respuesta - **200 OK** (24 ms, 452 bytes):

```http
Content-Type: application/json
Content-Length: 452
X-Correlation-ID: 04544c2ee46a4698
```

```json
{
  "id": 6,
  "folio": "CAPA-2026-0006",
  "investigacion_id": 6,
  "tipo": "correctiva",
  "descripcion": "Exigir registro de temperatura en cada parada del camion de reparto",
  "responsable_id": 13,
  "responsable": "Valentina Perez",
  "fecha_compromiso": "2026-12-22",
  "estado": "planificada",
  "meta_reduccion_pct": 30.0,
  "fecha_implementacion": null,
  "comentario_cierre": null,
  "vencida": false,
  "ultimo_veredicto": null,
  "ultima_reduccion_pct": null,
  "ultima_medicion": null,
  "mediciones": []
}
```

Verificaciones:

- ok: HTTP 200
- ok: es la accion pedida
- ok: aun sin mediciones

## P4-CR-65

**accion 404 ajena: no revela que existe**

Objetivo: Una accion de otra persona responde 404 y no 403, para no confirmar que existe (RN-13).

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/api/v1/causa-raiz/acciones/7" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_INSPECTOR"
```

Respuesta - **404 NOT FOUND** (19 ms, 132 bytes):

```http
Content-Type: application/json
Content-Length: 132
X-Correlation-ID: 59690f2173a64866
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Accion inexistente.",
    "detalles": null,
    "correlation_id": "59690f2173a64866"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-CR-66

**medir 409 accion no implementada**

Objetivo: Solo se mide una accion que ya se implemento.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/acciones/6/mediciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{}'
```

Respuesta - **409 CONFLICT** (22 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: 85aae3b62cdf4c86
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "accion_no_implementada",
    "mensaje": "Solo se mide una accion ya implementada.",
    "detalles": null,
    "correlation_id": "85aae3b62cdf4c86"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo accion_no_implementada

## P4-CR-67

**cierre 409 con acciones sin medir**

Objetivo: No se cierra mientras haya acciones sin medir: el cierre no esconde si algo funciono.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/cierre" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"comentario":"Intento de cerrar antes de medir la eficacia"}'
```

Respuesta - **409 CONFLICT** (26 ms, 166 bytes):

```http
Content-Type: application/json
Content-Length: 166
X-Correlation-ID: 6404b5600fad437e
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "requiere_medicion",
    "mensaje": "Mide la eficacia de las acciones antes de cerrar.",
    "detalles": null,
    "correlation_id": "6404b5600fad437e"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo requiere_medicion

## P4-CR-68

**accion 409 saltar a implementada**

Objetivo: La accion avanza planificada, en curso, implementada; no se salta un paso.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/acciones/6/estado" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_INSPECTOR" \
  -d '{"estado":"implementada"}'
```

Respuesta - **409 CONFLICT** (19 ms, 174 bytes):

```http
Content-Type: application/json
Content-Length: 174
X-Correlation-ID: c4a5e7ea99d3479b
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "transicion_invalida",
    "mensaje": "La accion no puede pasar de planificada a implementada.",
    "detalles": null,
    "correlation_id": "c4a5e7ea99d3479b"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo transicion_invalida

## P4-CR-69

**accion 404 ajena no se mueve**

Objetivo: Quien no es responsable ni operador no puede mover la accion.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/acciones/7/estado" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_INSPECTOR" \
  -d '{"estado":"en_curso"}'
```

Respuesta - **404 NOT FOUND** (18 ms, 132 bytes):

```http
Content-Type: application/json
Content-Length: 132
X-Correlation-ID: 4a7c15a29a9045dc
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "Accion inexistente.",
    "detalles": null,
    "correlation_id": "4a7c15a29a9045dc"
  }
}
```

Verificaciones:

- ok: HTTP 404
- ok: tipo no_encontrado

## P4-CR-70

**accion 200: en curso por su responsable**

Objetivo: El responsable avanza su accion.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/acciones/6/estado" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_INSPECTOR" \
  -d '{"estado":"en_curso"}'
```

Respuesta - **200 OK** (22 ms, 82 bytes):

```http
Content-Type: application/json
Content-Length: 82
X-Correlation-ID: 3fb1980ccc304e8c
```

```json
{
  "id": 6,
  "folio": "CAPA-2026-0006",
  "estado": "en_curso",
  "fecha_implementacion": null
}
```

Verificaciones:

- ok: HTTP 200
- ok: en_curso

## P4-CR-71

**accion 400 implementada en fecha futura**

Objetivo: No se declara implementada una accion con fecha futura.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/acciones/6/estado" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_INSPECTOR" \
  -d '{"estado":"implementada","fecha_implementacion":"2026-11-27"}'
```

Respuesta - **400 BAD REQUEST** (19 ms, 193 bytes):

```http
Content-Type: application/json
Content-Length: 193
X-Correlation-ID: dc0047ae5f2d4c0b
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "fecha_implementacion debe ser una fecha AAAA-MM-DD, no futura y de menos de un ano.",
    "detalles": null,
    "correlation_id": "dc0047ae5f2d4c0b"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CR-72

**accion 200: implementada**

Objetivo: Se implementa con su fecha real; de ella dependen los periodos de la medicion.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/acciones/6/estado" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_INSPECTOR" \
  -d '{"estado":"implementada","fecha_implementacion":"2026-10-08"}'
```

Respuesta - **200 OK** (22 ms, 94 bytes):

```http
Content-Type: application/json
Content-Length: 94
X-Correlation-ID: 2ea14fb02f1145ca
```

```json
{
  "id": 6,
  "folio": "CAPA-2026-0006",
  "estado": "implementada",
  "fecha_implementacion": "2026-10-08"
}
```

Verificaciones:

- ok: HTTP 200
- ok: implementada

## P4-CR-73

**accion 400 cancelar sin comentario**

Objetivo: Cancelar una accion exige explicar por que.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/acciones/7/estado" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"estado":"cancelada"}'
```

Respuesta - **400 BAD REQUEST** (19 ms, 172 bytes):

```http
Content-Type: application/json
Content-Length: 172
X-Correlation-ID: 26299c246fd742c6
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
    "correlation_id": "26299c246fd742c6"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CR-74

**accion 200: cancelada con motivo**

Objetivo: Una accion cancelada no cuenta para el cierre.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/acciones/7/estado" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"estado":"cancelada","comentario":"Se difiere a la siguiente auditoria anual"}'
```

Respuesta - **200 OK** (23 ms, 83 bytes):

```http
Content-Type: application/json
Content-Length: 83
X-Correlation-ID: 3d28d05ceec44e0b
```

```json
{
  "id": 7,
  "folio": "CAPA-2026-0007",
  "estado": "cancelada",
  "fecha_implementacion": null
}
```

Verificaciones:

- ok: HTTP 200
- ok: cancelada

## P4-CR-75

**medir 403 inspector**

Objetivo: Medir es de Administrador, Analista y Supervisor.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/acciones/6/mediciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_INSPECTOR" \
  -d '{}'
```

Respuesta - **403 FORBIDDEN** (9 ms, 247 bytes):

```http
Content-Type: application/json
Content-Length: 247
X-Correlation-ID: af57e4dfa53440ba
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
        "Supervisor"
      ]
    },
    "correlation_id": "af57e4dfa53440ba"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-CR-76

**medir 400 ventana invalida**

Objetivo: La ventana de comparacion es de 7 a 365 dias.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/acciones/6/mediciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"ventana_antes_dias":3}'
```

Respuesta - **400 BAD REQUEST** (8 ms, 154 bytes):

```http
Content-Type: application/json
Content-Length: 154
X-Correlation-ID: 75ce6516ad1d4797
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "ventana_antes_dias debe estar entre 7 y 365.",
    "detalles": null,
    "correlation_id": "75ce6516ad1d4797"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CR-77

**medir 201: antes contra despues**

Objetivo: Paso 8: tasa de lo vendido antes contra lo vendido despues, sin contar lo que aun puede devolverse. Con poca muestra el veredicto es sin_datos, nunca efectiva.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/acciones/6/mediciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"ventana_antes_dias":90}'
```

Respuesta - **201 CREATED** (35 ms, 519 bytes):

```http
Content-Type: application/json
Content-Length: 519
X-Correlation-ID: 7330df7dfcf84072
```

```json
{
  "id": 5,
  "accion_id": 6,
  "antes": {
    "desde": "2026-07-10",
    "hasta": "2026-10-07",
    "unidades_vendidas": 24,
    "unidades_devueltas": 16,
    "casos": 4,
    "tasa_pct": 66.67
  },
  "despues": {
    "desde": "2026-10-08",
    "hasta": "2026-10-23",
    "unidades_vendidas": 0,
    "unidades_devueltas": 0,
    "casos": 0,
    "tasa_pct": null
  },
  "reduccion_pct": null,
  "meta_reduccion_pct": 30.0,
  "veredicto": "sin_datos",
  "motivo_sin_datos": "Despues hay 0 unidades vendidas; se requieren al menos 20.",
  "aviso": "Compara cohortes de venta; un buen resultado orienta, no prueba causalidad (RN-09)."
}
```

Verificaciones:

- ok: HTTP 201
- ok: veredicto conocido
- ok: sin_datos explica por que
- ok: aclara que no prueba causalidad

Efecto en PostgreSQL - la medicion y el nuevo estado de la investigacion:

```sql
SELECT m.veredicto, m.antes_vendidas, m.antes_devueltas, m.despues_vendidas, m.meta_reduccion_pct, i.estado FROM mediciones_eficacia m JOIN acciones_capa a ON a.id = m.accion_id JOIN investigaciones i ON i.id = a.investigacion_id WHERE m.id = 5
```

```text
veredicto | antes_vendidas | antes_devueltas | despues_vendidas | meta_reduccion_pct | estado
sin_datos | 24 | 16 | 0 | 30.00 | en_medicion
```

## P4-CR-78

**accion 200: detalle con su medicion**

Objetivo: El responsable ve el resultado de la medicion de su accion.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/api/v1/causa-raiz/acciones/6" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_INSPECTOR"
```

Respuesta - **200 OK** (23 ms, 982 bytes):

```http
Content-Type: application/json
Content-Length: 982
X-Correlation-ID: c6ef31a0b38b4421
```

```json
{
  "id": 6,
  "folio": "CAPA-2026-0006",
  "investigacion_id": 6,
  "tipo": "correctiva",
  "descripcion": "Exigir registro de temperatura en cada parada del camion de reparto",
  "responsable_id": 13,
  "responsable": "Valentina Perez",
  "fecha_compromiso": "2026-12-22",
  "estado": "implementada",
  "meta_reduccion_pct": 30.0,
  "fecha_implementacion": "2026-10-08",
  "comentario_cierre": null,
  "vencida": false,
  "ultimo_veredicto": "sin_datos",
  "ultima_reduccion_pct": null,
  "ultima_medicion": "2026-11-22T18:13:29.010109+00:00",
  "mediciones": [
    {
      "id": 5,
      "accion_id": 6,
      "antes_desde": "2026-07-10",
      "antes_hasta": "2026-10-07",
      "despues_desde": "2026-10-08",
      "despues_hasta": "2026-10-23",
      "antes_vendidas": 24,
      "antes_devueltas": 16,
      "antes_tasa_pct": 66.67,
      "despues_vendidas": 0,
      "despues_devueltas": 0,
      "despues_tasa_pct": null,
      "reduccion_pct": null,
      "meta_reduccion_pct": 30.0,
      "veredicto": "sin_datos",
      "motivo_sin_datos": "Despues hay 0 unidades vendidas; se requieren al menos 20.",
      "medido_por": 16,
      "fecha_medicion": "2026-11-22T18:13:29.010109+00:00"
    }
  ]
}
```

Verificaciones:

- ok: HTTP 200
- ok: una medicion

## P4-CR-79

**cierre 403 analista**

Objetivo: Cerrar es solo de un Supervisor (RN-13).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/cierre" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"comentario":"El analista no puede cerrar investigaciones"}'
```

Respuesta - **403 FORBIDDEN** (9 ms, 219 bytes):

```http
Content-Type: application/json
Content-Length: 219
X-Correlation-ID: 4084381b49da4b03
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
        "Supervisor"
      ]
    },
    "correlation_id": "4084381b49da4b03"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-CR-80

**cierre 403 sin reconfirmar la contrasena**

Objetivo: Aunque todo lo demas este en orden, cerrar exige reconfirmar la contrasena (operacion critica).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/cierre" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"comentario":"Cierre sin permiso de operacion critica"}'
```

Respuesta - **403 FORBIDDEN** (25 ms, 306 bytes):

```http
Content-Type: application/json
Content-Length: 306
X-Correlation-ID: 3034e618af474997
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "autorizacion_operacion_requerida",
    "mensaje": "Esta operacion requiere confirmar tu contrasena en POST /api/v1/auth/autorizar-operacion.",
    "detalles": {
      "operacion": "cerrar_investigacion",
      "recurso_id": "6",
      "header": "X-Autorizacion-Operacion"
    },
    "correlation_id": "3034e618af474997"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo autorizacion_operacion_requerida

## P4-CR-81

**autorizar operacion 403 analista**

Objetivo: Solo un Supervisor puede autorizar el cierre de una investigacion.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8001/api/v1/auth/autorizar-operacion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"operacion":"cerrar_investigacion","recurso_id":"6","password":"$PASSWORD_DEMO"}'
```

Respuesta - **403 FORBIDDEN** (10 ms, 251 bytes):

```http
Content-Type: application/json
Content-Length: 251
X-Correlation-ID: d7a3e1c7e85c45cc
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "sin_permiso",
    "mensaje": "Tu rol no puede autorizar esta operacion.",
    "detalles": {
      "rol": "Analista de Devoluciones",
      "operacion": "cerrar_investigacion",
      "roles_permitidos": [
        "Supervisor"
      ]
    },
    "correlation_id": "d7a3e1c7e85c45cc"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo sin_permiso

## P4-CR-82

**autorizar operacion 401 contrasena incorrecta**

Objetivo: Una contrasena equivocada no emite permiso; el intento queda en la bitacora.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8001/api/v1/auth/autorizar-operacion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"operacion":"cerrar_investigacion","recurso_id":"6","password":"contrasena-incorrecta-de-prueba"}'
```

Respuesta - **401 UNAUTHORIZED** (115 ms, 144 bytes):

```http
Content-Type: application/json
Content-Length: 144
X-Correlation-ID: ed840cfda1a5414c
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "credenciales_invalidas",
    "mensaje": "Contrasena incorrecta.",
    "detalles": null,
    "correlation_id": "ed840cfda1a5414c"
  }
}
```

Verificaciones:

- ok: HTTP 401
- ok: tipo credenciales_invalidas

## P4-CR-83

**autorizar operacion 201 sobre otro registro**

Objetivo: Un permiso se emite para UN registro; este es de otro, para probar que no sirve aqui.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8001/api/v1/auth/autorizar-operacion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"operacion":"cerrar_investigacion","recurso_id":"999999","password":"$PASSWORD_DEMO"}'
```

Respuesta - **201 CREATED** (109 ms, 588 bytes):

```http
Content-Type: application/json
Content-Length: 588
X-Correlation-ID: 5068b1a81c6740ae
```

```json
{
  "token_operacion": "***oculto***",
  "expires_in": 300,
  "operacion": "cerrar_investigacion",
  "recurso_id": "999999",
  "header": "X-Autorizacion-Operacion"
}
```

Verificaciones:

- ok: HTTP 201
- ok: vigencia 5 minutos

## P4-CR-84

**cierre 403 permiso de otro registro**

Objetivo: El permiso vale para un solo registro.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/cierre" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -H "X-Autorizacion-Operacion: ***oculto***" \
  -d '{"comentario":"Intento de cerrar con el permiso de otro registro"}'
```

Respuesta - **403 FORBIDDEN** (26 ms, 195 bytes):

```http
Content-Type: application/json
Content-Length: 195
X-Correlation-ID: 628e27e52e1b4145
```

```json
{
  "error": {
    "codigo": 403,
    "tipo": "autorizacion_operacion_invalida",
    "mensaje": "La autorizacion corresponde a otra operacion, registro o sesion.",
    "detalles": null,
    "correlation_id": "628e27e52e1b4145"
  }
}
```

Verificaciones:

- ok: HTTP 403
- ok: tipo autorizacion_operacion_invalida

## P4-CR-85

**autorizar operacion 201**

Objetivo: El supervisor reconfirma su contrasena y recibe un permiso de un solo uso para esta investigacion.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8001/api/v1/auth/autorizar-operacion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"operacion":"cerrar_investigacion","recurso_id":"6","password":"$PASSWORD_DEMO"}'
```

Respuesta - **201 CREATED** (109 ms, 576 bytes):

```http
Content-Type: application/json
Content-Length: 576
X-Correlation-ID: b7548cb0b287428a
```

```json
{
  "token_operacion": "***oculto***",
  "expires_in": 300,
  "operacion": "cerrar_investigacion",
  "recurso_id": "6",
  "header": "X-Autorizacion-Operacion"
}
```

Verificaciones:

- ok: HTTP 201

Efecto en PostgreSQL - la autorizacion queda en la bitacora, sin la contrasena:

```sql
SELECT accion, entidad, detalle FROM bitacora WHERE accion = 'autorizacion_operacion' ORDER BY id DESC LIMIT 1
```

```text
accion | entidad | detalle
autorizacion_operacion | usuarios | Autorizo cerrar_investigacion sobre 6
```

## P4-CR-86

**cierre 400 comentario corto**

Objetivo: La validacion ocurre antes de consumir el permiso: un error de captura no lo gasta.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/cierre" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -H "X-Autorizacion-Operacion: ***oculto***" \
  -d '{"comentario":"ok"}'
```

Respuesta - **400 BAD REQUEST** (10 ms, 187 bytes):

```http
Content-Type: application/json
Content-Length: 187
X-Correlation-ID: 9976727ca7a84e87
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
        "problema": "entre 10 y 2000 caracteres"
      }
    ],
    "correlation_id": "9976727ca7a84e87"
  }
}
```

Verificaciones:

- ok: HTTP 400
- ok: tipo validacion

## P4-CR-87

**cierre 200 por un supervisor distinto del analista**

Objetivo: Paso 9: lo cierra un supervisor distinto del analista, con permiso de un solo uso. El veredicto sale de las mediciones, no del cierre.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/cierre" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -H "X-Autorizacion-Operacion: ***oculto***" \
  -d '{"comentario":"Medicion revisada; se cierra la investigacion con el veredicto que arrojo la medicion"}'
```

Respuesta - **200 OK** (33 ms, 58 bytes):

```http
Content-Type: application/json
Content-Length: 58
X-Correlation-ID: 6c352cc42c0f427e
```

```json
{
  "id": 6,
  "estado": "cerrada",
  "veredicto_final": "sin_datos"
}
```

Verificaciones:

- ok: HTTP 200
- ok: cerrada
- ok: veredicto conocido

Efecto en PostgreSQL - investigacion cerrada y quien la cerro:

```sql
SELECT folio, estado, veredicto_final, cerrada_por IS NOT NULL AS tiene_autor_del_cierre, cerrada_por <> analista_id AS cierra_otra_persona FROM investigaciones WHERE id = 6
```

```text
folio | estado | veredicto_final | tiene_autor_del_cierre | cierra_otra_persona
INV-2026-0006 | cerrada | sin_datos | t | t
```

Efecto en PostgreSQL - el cierre en la bitacora:

```sql
SELECT accion, entidad, detalle FROM bitacora WHERE accion = 'cierre_investigacion' ORDER BY id DESC LIMIT 1
```

```text
accion | entidad | detalle
cierre_investigacion | investigaciones | INV-2026-0006: sin_datos
```

## P4-CR-88

**cierre 409 ya cerrada**

Objetivo: Una investigacion cerrada no vuelve a abrirse ni a cerrarse.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6/cierre" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"comentario":"Segundo intento de cerrar la misma investigacion"}'
```

Respuesta - **409 CONFLICT** (22 ms, 172 bytes):

```http
Content-Type: application/json
Content-Length: 172
X-Correlation-ID: 83a2b675eb574d06
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "transicion_invalida",
    "mensaje": "La investigacion no puede pasar de cerrada a cerrada.",
    "detalles": null,
    "correlation_id": "83a2b675eb574d06"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo transicion_invalida

## P4-CR-89

**detalle final: linea de tiempo completa**

Objetivo: La linea de tiempo registra cada cambio de estado, en orden.

Comando:

```bash
curl -sS -i -X GET "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/6" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR"
```

Respuesta - **200 OK** (34 ms, 5048 bytes):

```http
Content-Type: application/json
Content-Length: 5048
X-Correlation-ID: 39c55f55151e471b
```

```json
{
  "id": 6,
  "folio": "INV-2026-0006",
  "alerta_id": 3,
  "dimension": "lote",
  "referencia_id": 15,
  "etiqueta": "L-2026-PROB-01 (Leche entera 1 L)",
  "titulo": "Evidencia P4: leche del lote de la demo",
  "descripcion": "Cuatro ventas del mismo lote concentran las devoluciones; se investiga la cadena de frio",
  "estado": "cerrada",
  "analista_id": 16,
  "linea_base": {
    "casos": 4,
    "origen": "alerta",
    "tasa_pct": 66.67,
    "fecha_corte": "2026-11-22",
    "unidades_vendidas": 24,
    "unidades_devueltas": 16
  },
  "conclusion": "causa_confirmada",
  "causa_raiz": "El camion de reparto no mantuvo la cadena de frio durante una parada de 40 minutos",
  "justificacion": "Hipotesis verificada con el termometro del camion y una devolucion del lote con producto tibio",
  "fecha_conclusion": "2026-11-22T18:13:28.337367+00:00",
  "cerrada_por": 40,
  "comentario_cierre": "Medicion revisada; se cierra la investigacion con el veredicto que arrojo la medicion",
  "veredicto_final": "sin_datos",
  "fecha_creacion": "2026-11-22T18:13:26.676471+00:00",
  "fecha_cierre": "2026-11-22T18:13:29.802457+00:00",
  "analista": "Josue Berdeal",
  "cerrada_por_nombre": "Jorge Salinas",
  "hipotesis": [
    {
      "id": 14,
      "tipo": "cinco_porques",
      "nivel": 1,
      "padre_id": null,
      "categoria_ishikawa": null,
      "descripcion": "Las devoluciones se concentran en el lote porque la leche llego tibia",
      "estado": "verificada",
      "resultado_verificacion": "El registro del termometro del camion confirma 14 C durante 40 minutos",
      "fecha_verificacion": "2026-11-22T18:13:28.055931+00:00",
      "verificada_por": "Josue Berdeal"
    },
    {
      "id": 15,
      "tipo": "cinco_porques",
      "nivel": 2,
      "padre_id": 14,
      "categoria_ishikawa": null,
      "descripcion": "Llego tibia porque el camion no mantuvo la cadena de frio",
      "estado": "propuesta",
      "resultado_verificacion": null,
      "fecha_verificacion": null,
      "verificada_por": null
    },
    {
      "id": 16,
      "tipo": "ishikawa",
      "nivel": null,
      "padre_id": null,
      "categoria_ishikawa": "metodo",
      "descripcion": "El metodo de carga no respeta el tiempo maximo fuera de refrigeracion",
      "estado": "propuesta",
      "resultado_verificacion": null,
      "fecha_verificacion": null,
      "verificada_por": null
    },
    {
      "id": 17,
      "tipo": "libre",
... (recortado: 118 lineas mas)
```

Verificaciones:

- ok: HTTP 200
- ok: termina cerrada
- ok: 6 eventos: uno por estado
- ok: pasa por todos los estados

## P4-CR-90

**investigacion manual 201 XML**

Objetivo: Una investigacion manual, sin alerta previa, por contrato XML (RF-31).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones" \
  -H "Accept: application/xml" \
  -H "Content-Type: application/xml" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '<investigacion><dimension>proveedor</dimension><referencia_id>1</referencia_id><titulo>Evidencia P4: proveedor del lote de la demo</titulo><descripcion>Investigacion abierta a mano sobre el proveedor, enviada por XML</descripcion></investigacion>'
```

Respuesta - **201 CREATED** (51 ms, 344 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 344
X-Correlation-ID: 94092b5c85064245
Location: /api/v1/causa-raiz/investigaciones/7
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<investigacion><id>7</id><folio>INV-2026-0007</folio><estado>abierta</estado><linea_base><unidades_vendidas>89</unidades_vendidas><unidades_devueltas>33</unidades_devueltas><casos>21</casos><tasa_pct>37.08</tasa_pct><fecha_corte>2026-11-22</fecha_corte><origen>manual</origen></linea_base></investigacion>
```

Verificaciones:

- ok: HTTP 201
- ok: trae folio

Efecto en PostgreSQL - nace sin alerta y a nombre de quien la abre:

```sql
SELECT folio, dimension, alerta_id, estado, linea_base->>'origen' AS origen FROM investigaciones WHERE id = 7
```

```text
folio | dimension | alerta_id | estado | origen
INV-2026-0007 | proveedor |  | abierta | manual
```

## P4-CR-91

**iniciar verificacion 409 sin hipotesis**

Objetivo: No se verifica sin haber escrito al menos una hipotesis.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/7/verificacion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{}'
```

Respuesta - **409 CONFLICT** (33 ms, 163 bytes):

```http
Content-Type: application/json
Content-Length: 163
X-Correlation-ID: 1b009a31ee694356
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "sin_hipotesis",
    "mensaje": "Escribe al menos una hipotesis antes de verificar.",
    "detalles": null,
    "correlation_id": "1b009a31ee694356"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo sin_hipotesis

## P4-CR-92

**hipotesis 201 en la segunda investigacion**

Objetivo: Hipotesis libre.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/7/hipotesis" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"tipo":"libre","descripcion":"El proveedor cambio de planta de envasado este trimestre"}'
```

Respuesta - **201 CREATED** (34 ms, 38 bytes):

```http
Content-Type: application/json
Content-Length: 38
X-Correlation-ID: 51f48261f1ad4d8e
```

```json
{
  "id": 18,
  "tipo": "libre",
  "nivel": null
}
```

Verificaciones:

- ok: HTTP 201

## P4-CR-93

**iniciar verificacion 200 en la segunda**

Objetivo: Pasa a verificacion.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/7/verificacion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{}'
```

Respuesta - **200 OK** (39 ms, 36 bytes):

```http
Content-Type: application/json
Content-Length: 36
X-Correlation-ID: af1b0d4547954951
```

```json
{
  "id": 7,
  "estado": "en_verificacion"
}
```

Verificaciones:

- ok: HTTP 200
- ok: en_verificacion

## P4-CR-94

**verificar hipotesis 200: descartada en la segunda**

Objetivo: La unica hipotesis se descarta.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/7/hipotesis/18/verificacion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"resultado":"descartada","resultado_verificacion":"El proveedor confirma que la planta de envasado no cambio"}'
```

Respuesta - **200 OK** (33 ms, 32 bytes):

```http
Content-Type: application/json
Content-Length: 32
X-Correlation-ID: 2f79a68169f14a47
```

```json
{
  "id": 18,
  "estado": "descartada"
}
```

Verificaciones:

- ok: HTTP 200
- ok: descartada

## P4-CR-95

**concluir 409 confirmar sin evidencia**

Objetivo: Confirmar exige evidencia (RN-09); aqui no hay ninguna.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/7/conclusion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"conclusion":"causa_confirmada","causa_raiz":"Cambio de planta del proveedor","justificacion":"Sin evidencia ni hipotesis verificada"}'
```

Respuesta - **409 CONFLICT** (33 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: 4e2a2261fb694933
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "sin_evidencia",
    "mensaje": "Confirmar una causa exige al menos una evidencia.",
    "detalles": null,
    "correlation_id": "4e2a2261fb694933"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo sin_evidencia

## P4-CR-96

**concluir 200 inconclusa**

Objetivo: El sistema acepta que no se encontro la causa: concluir inconclusa es valido y honesto (RN-09).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/7/conclusion" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"conclusion":"inconclusa","justificacion":"No se hallo evidencia suficiente para atribuir la causa al proveedor"}'
```

Respuesta - **200 OK** (28 ms, 56 bytes):

```http
Content-Type: application/json
Content-Length: 56
X-Correlation-ID: c3de874ca5d543ea
```

```json
{
  "id": 7,
  "estado": "concluida",
  "conclusion": "inconclusa"
}
```

Verificaciones:

- ok: HTTP 200
- ok: inconclusa

## P4-CR-97

**accion 409 sin causa confirmada**

Objetivo: Las acciones se crean cuando la causa esta confirmada.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/7/acciones" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"tipo":"correctiva","descripcion":"No se corrige una causa que no se confirmo","responsable_id":13,"fecha_compromiso":"2026-12-22"}'
```

Respuesta - **409 CONFLICT** (22 ms, 174 bytes):

```http
Content-Type: application/json
Content-Length: 174
X-Correlation-ID: 87a6ec61910c4605
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "sin_causa_confirmada",
    "mensaje": "Las acciones se crean cuando la causa esta confirmada.",
    "detalles": null,
    "correlation_id": "87a6ec61910c4605"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo sin_causa_confirmada

## P4-CR-98

**cierre 409 el analista no cierra lo suyo**

Objetivo: Quien lleva la investigacion no puede cerrarla: lo hace otro supervisor (separacion de funciones).

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/7/cierre" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_SUPERVISOR" \
  -d '{"comentario":"El mismo supervisor que la lleva intenta cerrarla"}'
```

Respuesta - **409 CONFLICT** (21 ms, 192 bytes):

```http
Content-Type: application/json
Content-Length: 192
X-Correlation-ID: 594db3a293f44bf0
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "cierre_independiente",
    "mensaje": "Quien lleva la investigacion no puede cerrarla; lo hace otro supervisor.",
    "detalles": null,
    "correlation_id": "594db3a293f44bf0"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo cierre_independiente

## P4-CR-99

**reabrir 200 una inconclusa**

Objetivo: Una inconclusa vuelve a verificacion si aparece mas informacion.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/7/reabrir" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"comentario":"Llego informacion nueva del proveedor"}'
```

Respuesta - **200 OK** (27 ms, 36 bytes):

```http
Content-Type: application/json
Content-Length: 36
X-Correlation-ID: 7f77fd6fdd3a4e15
```

```json
{
  "id": 7,
  "estado": "en_verificacion"
}
```

Verificaciones:

- ok: HTTP 200
- ok: en_verificacion

Efecto en PostgreSQL - la conclusion se limpia y queda en la linea de tiempo:

```sql
SELECT i.estado, i.conclusion, (SELECT count(*) FROM seguimiento_investigacion s WHERE s.investigacion_id = i.id) AS eventos FROM investigaciones i WHERE i.id = 7
```

```text
estado | conclusion | eventos
en_verificacion |  | 4
```

## P4-CR-100

**reabrir 409 si no esta concluida inconclusa**

Objetivo: Solo se reabre una investigacion concluida como inconclusa.

Comando:

```bash
curl -sS -i -X POST "http://$VM_HOST:8011/api/v1/causa-raiz/investigaciones/7/reabrir" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN_ANALISTA" \
  -d '{"comentario":"Ya esta reabierta, no hay nada que reabrir"}'
```

Respuesta - **409 CONFLICT** (20 ms, 171 bytes):

```http
Content-Type: application/json
Content-Length: 171
X-Correlation-ID: 94ecbf9dfba14ae8
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "no_reabrible",
    "mensaje": "Solo se reabre una investigacion concluida como inconclusa.",
    "detalles": null,
    "correlation_id": "94ecbf9dfba14ae8"
  }
}
```

Verificaciones:

- ok: HTTP 409
- ok: tipo no_reabrible

## Limpieza

Al terminar se borraron los datos que creo esta corrida, para no dejar basura en la base de demostracion. **La bitacora no se toca**: es de solo agregar (migracion 045).

