# Ejecuciones reales - `inspecciones`

Salida de `newman run docs/postman/inspecciones.postman_collection.json` contra la VM (2026-10-22 00:39 UTC). Verificaciones: 88 (0 fallidas). Tokens, contrasenas e IP de la VM estan ocultos (`***jwt***`, `***`, `{{vm_host}}`).

## 084_inspecciones_get_health_200

Carpeta: 00 Preparacion (requiere devolucion_id recibida: coleccion logistica) - Caso: health 200

`GET http://{{vm_host}}:8004/health`

**Request - headers:**

```http
Accept: application/json
```

**Response - 200 OK** (120 ms, 180 bytes):

```http
Content-Type: application/json
Content-Length: 180
X-Correlation-ID: ff03d5f140874c0c
```

```json
{
  "servicio": "inspecciones",
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

## 085_inspecciones_post_raiz_401

Carpeta: 01 Registrar inspeccion (POST) - Caso: registrar 401 sin token

`POST http://{{vm_host}}:8004/api/v1/inspecciones`

**Request - headers:**

```http
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "devolucion_id": 81,
  "estado_empaque": "Empaque intacto, sello cerrado",
  "danos": false,
  "caducidad_vencida": false,
  "cadena_frio_rota": false,
  "minutos_fuera_refrigeracion": 10,
  "temperatura_recepcion": 4.5,
  "observaciones": "Inspeccion de prueba desde Postman"
}
```

**Response - 401 UNAUTHORIZED** (78 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: 658ac8531ff24c46
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "658ac8531ff24c46"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = no_autenticado
- ok: Trae X-Correlation-ID

## 086_inspecciones_post_raiz_403

Carpeta: 01 Registrar inspeccion (POST) - Caso: registrar 403 analista

`POST http://{{vm_host}}:8004/api/v1/inspecciones`

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
  "estado_empaque": "Empaque intacto, sello cerrado",
  "danos": false,
  "caducidad_vencida": false,
  "cadena_frio_rota": false,
  "minutos_fuera_refrigeracion": 10,
  "temperatura_recepcion": 4.5,
  "observaciones": "Inspeccion de prueba desde Postman"
}
```

**Response - 403 FORBIDDEN** (81 ms, 218 bytes):

```http
Content-Type: application/json
Content-Length: 218
X-Correlation-ID: 5bf1332dc0ea4141
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
        "Inspector"
      ]
    },
    "correlation_id": "5bf1332dc0ea4141"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 087_inspecciones_post_raiz_400

Carpeta: 01 Registrar inspeccion (POST) - Caso: registrar 400 devolucion_id invalido

`POST http://{{vm_host}}:8004/api/v1/inspecciones`

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
  "estado_empaque": "Empaque intacto, sello cerrado",
  "danos": false,
  "caducidad_vencida": false,
  "cadena_frio_rota": false,
  "minutos_fuera_refrigeracion": 10,
  "temperatura_recepcion": 4.5,
  "observaciones": "Inspeccion de prueba desde Postman"
}
```

**Response - 400 BAD REQUEST** (152 ms, 174 bytes):

```http
Content-Type: application/json
Content-Length: 174
X-Correlation-ID: 73c05b1f72304313
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "devolucion_id debe ser positivo y minutos no puede ser negativo.",
    "detalles": null,
    "correlation_id": "73c05b1f72304313"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 088_inspecciones_post_raiz_404

Carpeta: 01 Registrar inspeccion (POST) - Caso: registrar 404 devolucion inexistente

`POST http://{{vm_host}}:8004/api/v1/inspecciones`

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
  "estado_empaque": "Empaque intacto, sello cerrado",
  "danos": false,
  "caducidad_vencida": false,
  "cadena_frio_rota": false,
  "minutos_fuera_refrigeracion": 10,
  "temperatura_recepcion": 4.5,
  "observaciones": "Inspeccion de prueba desde Postman"
}
```

**Response - 404 NOT FOUND** (89 ms, 144 bytes):

```http
Content-Type: application/json
Content-Length: 144
X-Correlation-ID: b1e20a8d97ee44f4
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe la devolucion 999999.",
    "detalles": null,
    "correlation_id": "b1e20a8d97ee44f4"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 089_inspecciones_post_raiz_400_xml

Carpeta: 01 Registrar inspeccion (POST) - Caso: registrar 400 XML no cumple XSD

`POST http://{{vm_host}}:8004/api/v1/inspecciones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/xml
Accept: application/xml
```

**Request - body:**

```
<inspeccion>
  <devolucion_id>81</devolucion_id>
</inspeccion>
```

**Response - 400 BAD REQUEST** (122 ms, 364 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 364
X-Correlation-ID: 1a4e4ef91a2b43cb
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<error><codigo>400</codigo><tipo>xml_no_cumple_xsd</tipo><mensaje>El XML no cumple el contrato del endpoint.</mensaje><detalles><item><linea>1</linea><problema>Element 'inspeccion': Missing child element(s). Expected is ( estado_empaque ).</problema></item></detalles><correlation_id>1a4e4ef91a2b43cb</correlation_id></error>
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = xml_no_cumple_xsd
- ok: Trae X-Correlation-ID

## 090_inspecciones_post_raiz_400

Carpeta: 01 Registrar inspeccion (POST) - Caso: registrar 400 empaque sin describir

`POST http://{{vm_host}}:8004/api/v1/inspecciones`

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
  "estado_empaque": "x",
  "danos": false,
  "caducidad_vencida": false,
  "cadena_frio_rota": false,
  "minutos_fuera_refrigeracion": 10,
  "temperatura_recepcion": 4.5,
  "observaciones": "Inspeccion de prueba desde Postman"
}
```

**Response - 400 BAD REQUEST** (165 ms, 141 bytes):

```http
Content-Type: application/json
Content-Length: 141
X-Correlation-ID: 4f4b65a5ae32448f
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Describe el estado del empaque.",
    "detalles": null,
    "correlation_id": "4f4b65a5ae32448f"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 091_inspecciones_post_raiz_400

Carpeta: 01 Registrar inspeccion (POST) - Caso: registrar 400 booleano invalido

`POST http://{{vm_host}}:8004/api/v1/inspecciones`

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
  "estado_empaque": "Empaque intacto, sello cerrado",
  "danos": "quizas",
  "caducidad_vencida": false,
  "cadena_frio_rota": false,
  "minutos_fuera_refrigeracion": 10,
  "temperatura_recepcion": 4.5,
  "observaciones": "Inspeccion de prueba desde Postman"
}
```

**Response - 400 BAD REQUEST** (91 ms, 134 bytes):

```http
Content-Type: application/json
Content-Length: 134
X-Correlation-ID: 36f6c2c883214fa1
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "danos debe ser booleano.",
    "detalles": null,
    "correlation_id": "36f6c2c883214fa1"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 092_inspecciones_post_raiz_201

Carpeta: 01 Registrar inspeccion (POST) - Caso: registrar 201 exitoso

`POST http://{{vm_host}}:8004/api/v1/inspecciones`

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
  "estado_empaque": "Empaque intacto, sello cerrado",
  "danos": false,
  "caducidad_vencida": false,
  "cadena_frio_rota": false,
  "minutos_fuera_refrigeracion": 10,
  "temperatura_recepcion": 4.5,
  "observaciones": "Inspeccion de prueba desde Postman"
}
```

**Response - 201 CREATED** (97 ms, 659 bytes):

```http
Content-Type: application/json
Content-Length: 659
Location: /api/v1/inspecciones/81
X-Correlation-ID: 8c29b283310d4dd1
```

```json
{
  "id": 21,
  "devolucion_id": 81,
  "resultado_general": "apto",
  "mongo_doc_id": "6ad95b4fdc019a2bc7393ae6",
  "apto_para_inventario": true,
  "fecha_inspeccion": "2026-10-22T00:39:43.019119+00:00",
  "detalle": {
    "devolucion_id": 81,
    "inspector_id": 13,
    "fecha": "2026-10-22T00:39:43.025668+00:00",
    "producto": {
      "clasificacion_temperatura": "refrigerado"
    },
    "condiciones": {
      "estado_empaque": "Empaque intacto, sello cerrado",
      "danos": false,
      "caducidad_vencida": false,
      "cadena_frio_rota": false,
      "minutos_fuera_refrigeracion": 10,
      "temperatura_recepcion": 4.5
    },
    "observaciones": "Inspeccion de prueba desde Postman",
    "resultado": {
      "apto_para_inventario": true,
      "motivos": []
    },
    "id": "6ad95b4fdc019a2bc7393ae6"
  }
}
```

**Verificaciones:**

- ok: HTTP 201
- ok: Trae X-Correlation-ID
- ok: aptitud calculada

## 093_inspecciones_post_raiz_409

Carpeta: 01 Registrar inspeccion (POST) - Caso: registrar 409 duplicada

`POST http://{{vm_host}}:8004/api/v1/inspecciones`

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
  "estado_empaque": "Empaque intacto, sello cerrado",
  "danos": false,
  "caducidad_vencida": false,
  "cadena_frio_rota": false,
  "minutos_fuera_refrigeracion": 10,
  "temperatura_recepcion": 4.5,
  "observaciones": "Inspeccion de prueba desde Postman"
}
```

**Response - 409 CONFLICT** (89 ms, 154 bytes):

```http
Content-Type: application/json
Content-Length: 154
X-Correlation-ID: 8e14860c86a744fc
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "inspeccion_duplicada",
    "mensaje": "La devolucion ya tiene inspeccion.",
    "detalles": null,
    "correlation_id": "8e14860c86a744fc"
  }
}
```

**Verificaciones:**

- ok: HTTP 409
- ok: error.tipo = inspeccion_duplicada
- ok: Trae X-Correlation-ID

## 094_inspecciones_get_id_200

Carpeta: 02 Consulta (GET) - Caso: detalle 200 inspector

`GET http://{{vm_host}}:8004/api/v1/inspecciones/81`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (166 ms, 692 bytes):

```http
Content-Type: application/json
Content-Length: 692
X-Correlation-ID: 78dcb55fe17c4497
```

```json
{
  "referencia": {
    "id": 21,
    "devolucion_id": 81,
    "inspector_id": 13,
    "fecha_inspeccion": "2026-10-22T00:39:43.019119+00:00",
    "resultado_general": "apto",
    "mongo_doc_id": "6ad95b4fdc019a2bc7393ae6",
    "apto_para_inventario": true
  },
  "detalle": {
    "id": "6ad95b4fdc019a2bc7393ae6",
    "devolucion_id": 81,
    "inspector_id": 13,
    "fecha": "2026-10-22T00:39:43.025000+00:00",
    "producto": {
      "clasificacion_temperatura": "refrigerado"
    },
    "condiciones": {
      "estado_empaque": "Empaque intacto, sello cerrado",
      "danos": false,
      "caducidad_vencida": false,
      "cadena_frio_rota": false,
      "minutos_fuera_refrigeracion": 10,
      "temperatura_recepcion": 4.5
    },
    "observaciones": "Inspeccion de prueba desde Postman",
    "resultado": {
      "apto_para_inventario": true,
      "motivos": []
    }
  }
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: une las dos bases

## 095_inspecciones_get_id_200_xml

Carpeta: 02 Consulta (GET) - Caso: detalle 200 analista XML

`GET http://{{vm_host}}:8004/api/v1/inspecciones/81`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/xml
```

**Response - 200 OK** (102 ms, 1081 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 1081
X-Correlation-ID: 555b140bc1014bc9
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<respuesta><referencia><id>21</id><devolucion_id>81</devolucion_id><inspector_id>13</inspector_id><fecha_inspeccion>2026-10-22T00:39:43.019119+00:00</fecha_inspeccion><resultado_general>apto</resultado_general><mongo_doc_id>6ad95b4fdc019a2bc7393ae6</mongo_doc_id><apto_para_inventario>true</apto_para_inventario></referencia><detalle><id>6ad95b4fdc019a2bc7393ae6</id><devolucion_id>81</devolucion_id><inspector_id>13</inspector_id><fecha>2026-10-22T00:39:43.025000+00:00</fecha><producto><clasificacion_temperatura>refrigerado</clasificacion_temperatura></producto><condiciones><estado_empaque>Empaque intacto, sello cerrado</estado_empaque><danos>false</danos><caducidad_vencida>false</caducidad_vencida><cadena_frio_rota>false</cadena_frio_rota><minutos_fuera_refrigeracion>10</minutos_fuera_refrigeracion><temperatura_recepcion>4.5</temperatura_recepcion></condiciones><observaciones>Inspeccion de prueba desde Postman</observaciones><resultado><apto_para_inventario>true</apto_para_inventario><motivos /></resultado></detalle></respuesta>
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 096_inspecciones_get_id_403

Carpeta: 02 Consulta (GET) - Caso: detalle 403 cliente

`GET http://{{vm_host}}:8004/api/v1/inspecciones/81`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 403 FORBIDDEN** (81 ms, 267 bytes):

```http
Content-Type: application/json
Content-Length: 267
X-Correlation-ID: dbd56d7bf4794262
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
        "Inspector",
        "Analista de Devoluciones",
        "Encargado del Centro de Devoluciones"
      ]
    },
    "correlation_id": "dbd56d7bf4794262"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 097_inspecciones_get_id_404

Carpeta: 02 Consulta (GET) - Caso: detalle 404 inexistente

`GET http://{{vm_host}}:8004/api/v1/inspecciones/999999`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 404 NOT FOUND** (90 ms, 160 bytes):

```http
Content-Type: application/json
Content-Length: 160
X-Correlation-ID: 194950d835c14654
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe inspeccion para la devolucion 999999.",
    "detalles": null,
    "correlation_id": "194950d835c14654"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 098_inspecciones_get_id_401

Carpeta: 02 Consulta (GET) - Caso: detalle 401 token invalido

`GET http://{{vm_host}}:8004/api/v1/inspecciones/81`

**Request - headers:**

```http
Authorization: Bearer esto-no-es-un-token
Accept: application/json
```

**Response - 401 UNAUTHORIZED** (79 ms, 136 bytes):

```http
Content-Type: application/json
Content-Length: 136
X-Correlation-ID: b764c2ef41274fc8
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "token_invalido",
    "mensaje": "El token no es valido.",
    "detalles": null,
    "correlation_id": "b764c2ef41274fc8"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = token_invalido
- ok: Trae X-Correlation-ID

## 099_inspecciones_patch_id_400

Carpeta: 03 Actualizar detalle (PATCH) - Caso: actualizar 400 sin cambios

`PATCH http://{{vm_host}}:8004/api/v1/inspecciones/81`

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

**Response - 400 BAD REQUEST** (162 ms, 138 bytes):

```http
Content-Type: application/json
Content-Length: 138
X-Correlation-ID: ff4f6c216bdc42f8
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "No hay campos actualizables.",
    "detalles": null,
    "correlation_id": "ff4f6c216bdc42f8"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 100_inspecciones_patch_id_403

Carpeta: 03 Actualizar detalle (PATCH) - Caso: actualizar 403 analista

`PATCH http://{{vm_host}}:8004/api/v1/inspecciones/81`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "observaciones": "x"
}
```

**Response - 403 FORBIDDEN** (78 ms, 218 bytes):

```http
Content-Type: application/json
Content-Length: 218
X-Correlation-ID: 42afe140ad094959
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
        "Inspector"
      ]
    },
    "correlation_id": "42afe140ad094959"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 101_inspecciones_patch_id_404

Carpeta: 03 Actualizar detalle (PATCH) - Caso: actualizar 404 inexistente

`PATCH http://{{vm_host}}:8004/api/v1/inspecciones/999999`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "observaciones": "x"
}
```

**Response - 404 NOT FOUND** (83 ms, 160 bytes):

```http
Content-Type: application/json
Content-Length: 160
X-Correlation-ID: 5a3ed98c640f4c59
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe inspeccion para la devolucion 999999.",
    "detalles": null,
    "correlation_id": "5a3ed98c640f4c59"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 102_inspecciones_patch_id_200_xml

Carpeta: 03 Actualizar detalle (PATCH) - Caso: actualizar 200 XML

`PATCH http://{{vm_host}}:8004/api/v1/inspecciones/81`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/xml
Accept: application/xml
```

**Request - body:**

```
<inspeccion_actualizacion>
  <observaciones>Observacion actualizada desde Postman</observaciones>
</inspeccion_actualizacion>
```

**Response - 200 OK** (127 ms, 1084 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 1084
X-Correlation-ID: 6ffbda7400e94ee4
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<respuesta><referencia><id>21</id><devolucion_id>81</devolucion_id><inspector_id>13</inspector_id><fecha_inspeccion>2026-10-22T00:39:43.019119+00:00</fecha_inspeccion><resultado_general>apto</resultado_general><mongo_doc_id>6ad95b4fdc019a2bc7393ae6</mongo_doc_id><apto_para_inventario>true</apto_para_inventario></referencia><detalle><id>6ad95b4fdc019a2bc7393ae6</id><devolucion_id>81</devolucion_id><inspector_id>13</inspector_id><fecha>2026-10-22T00:39:43.025000+00:00</fecha><producto><clasificacion_temperatura>refrigerado</clasificacion_temperatura></producto><condiciones><estado_empaque>Empaque intacto, sello cerrado</estado_empaque><danos>false</danos><caducidad_vencida>false</caducidad_vencida><cadena_frio_rota>false</cadena_frio_rota><minutos_fuera_refrigeracion>10</minutos_fuera_refrigeracion><temperatura_recepcion>4.5</temperatura_recepcion></condiciones><observaciones>Observacion actualizada desde Postman</observaciones><resultado><apto_para_inventario>true</apto_para_inventario><motivos /></resultado></detalle></respuesta>
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 103_inspecciones_post_id_disposicion_403

Carpeta: 04 Disposicion (POST) - Caso: disposicion 403 inspector

`POST http://{{vm_host}}:8004/api/v1/inspecciones/81/disposicion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "destino": "inventario",
  "justificacion": "Producto apto, regresa a inventario."
}
```

**Response - 403 FORBIDDEN** (144 ms, 218 bytes):

```http
Content-Type: application/json
Content-Length: 218
X-Correlation-ID: 54327769e5b44c62
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
        "Analista de Devoluciones"
      ]
    },
    "correlation_id": "54327769e5b44c62"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 104_inspecciones_post_id_disposicion_400

Carpeta: 04 Disposicion (POST) - Caso: disposicion 400 destino invalido

`POST http://{{vm_host}}:8004/api/v1/inspecciones/81/disposicion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "destino": "tirar"
}
```

**Response - 400 BAD REQUEST** (74 ms, 127 bytes):

```http
Content-Type: application/json
Content-Length: 127
X-Correlation-ID: bd2d5c36dcdb41fc
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Destino invalido.",
    "detalles": null,
    "correlation_id": "bd2d5c36dcdb41fc"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 105_inspecciones_post_id_disposicion_404

Carpeta: 04 Disposicion (POST) - Caso: disposicion 404 inexistente

`POST http://{{vm_host}}:8004/api/v1/inspecciones/999999/disposicion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "destino": "inventario",
  "justificacion": "Producto apto, regresa a inventario."
}
```

**Response - 404 NOT FOUND** (85 ms, 144 bytes):

```http
Content-Type: application/json
Content-Length: 144
X-Correlation-ID: 1c1e450524a6459a
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe la devolucion 999999.",
    "detalles": null,
    "correlation_id": "1c1e450524a6459a"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 106_inspecciones_post_id_disposicion_201_xml

Carpeta: 04 Disposicion (POST) - Caso: disposicion 201 XML

`POST http://{{vm_host}}:8004/api/v1/inspecciones/81/disposicion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/xml
Accept: application/xml
```

**Request - body:**

```
<disposicion>
  <destino>inventario</destino>
  <justificacion>Producto apto, regresa a inventario.</justificacion>
</disposicion>
```

**Response - 201 CREATED** (99 ms, 296 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 296
X-Correlation-ID: ac5eb74b3c634ddd
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<respuesta><id>16</id><devolucion_id>81</devolucion_id><analista_id>16</analista_id><destino>inventario</destino><justificacion>Producto apto, regresa a inventario.</justificacion><fecha_decision>2026-10-22T00:39:44.746378+00:00</fecha_decision></respuesta>
```

**Verificaciones:**

- ok: HTTP 201
- ok: Trae X-Correlation-ID

## 107_inspecciones_post_id_disposicion_409

Carpeta: 04 Disposicion (POST) - Caso: disposicion 409 duplicada

`POST http://{{vm_host}}:8004/api/v1/inspecciones/81/disposicion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "destino": "reciclaje"
}
```

**Response - 409 CONFLICT** (174 ms, 147 bytes):

```http
Content-Type: application/json
Content-Length: 147
X-Correlation-ID: 4697c0604dd94792
```

```json
{
  "error": {
    "codigo": 409,
    "tipo": "disposicion_duplicada",
    "mensaje": "Ya existe una disposicion.",
    "detalles": null,
    "correlation_id": "4697c0604dd94792"
  }
}
```

**Verificaciones:**

- ok: HTTP 409
- ok: error.tipo = disposicion_duplicada
- ok: Trae X-Correlation-ID

## 108_inspecciones_post_inventario_id_etiqueta_403

Carpeta: 05 Etiqueta de inventario (POST) - Caso: etiqueta 403 inspector

`POST http://{{vm_host}}:8004/api/v1/inspecciones/inventario/16/etiqueta`

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

**Response - 403 FORBIDDEN** (77 ms, 230 bytes):

```http
Content-Type: application/json
Content-Length: 230
X-Correlation-ID: fb5c44b153ea4572
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
        "Encargado del Centro de Devoluciones"
      ]
    },
    "correlation_id": "fb5c44b153ea4572"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 109_inspecciones_post_inventario_id_etiqueta_404

Carpeta: 05 Etiqueta de inventario (POST) - Caso: etiqueta 404 inexistente

`POST http://{{vm_host}}:8004/api/v1/inspecciones/inventario/999999/etiqueta`

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

**Response - 404 NOT FOUND** (86 ms, 145 bytes):

```http
Content-Type: application/json
Content-Length: 145
X-Correlation-ID: fee8982a25094c14
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe la disposicion 999999.",
    "detalles": null,
    "correlation_id": "fee8982a25094c14"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 110_inspecciones_post_inventario_id_etiqueta_201

Carpeta: 05 Etiqueta de inventario (POST) - Caso: etiqueta 201 exitoso

`POST http://{{vm_host}}:8004/api/v1/inspecciones/inventario/16/etiqueta`

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

**Response - 201 CREATED** (89 ms, 152 bytes):

```http
Content-Type: application/json
Content-Length: 152
X-Correlation-ID: 765a58ac8bf949e4
```

```json
{
  "id": 5,
  "disposicion_id": 16,
  "producto_id": 7,
  "etiqueta_codigo": "REC-2026-0081",
  "fecha_ingreso": "2026-10-22T00:39:45.250034+00:00",
  "estado": "disponible"
}
```

**Verificaciones:**

- ok: HTTP 201
- ok: Trae X-Correlation-ID
- ok: etiqueta REC-

