# Ejecuciones reales - `auth`

Salida de `newman run docs/postman/auth.postman_collection.json` contra la VM (2026-10-22 00:31 UTC). Verificaciones: 75 (0 fallidas). Tokens, contrasenas e IP de la VM estan ocultos (`***jwt***`, `***`, `{{vm_host}}`).

## 001_auth_get_health_200

Carpeta: 00 Salud y contratos - Caso: health 200

`GET http://{{vm_host}}:8001/health`

**Request - headers:**

```http
Accept: application/json
```

**Response - 200 OK** (99 ms, 137 bytes):

```http
Content-Type: application/json
Content-Length: 137
X-Correlation-ID: d4ede279f4f24100
```

```json
{
  "servicio": "auth",
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

## 002_auth_get_health_200_xml

Carpeta: 00 Salud y contratos - Caso: health 200 XML

`GET http://{{vm_host}}:8001/health`

**Request - headers:**

```http
Accept: application/xml
```

**Response - 200 OK** (83 ms, 240 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 240
X-Correlation-ID: de76ceed2c614d3d
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<respuesta><servicio>auth</servicio><version>v1</version><estado>ok</estado><dependencias><postgresql><ok>true</ok><error /></postgresql><redis><ok>true</ok><error /></redis></dependencias></respuesta>
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: estado ok

## 003_auth_post_login_200

Carpeta: 01 Login - Caso: login 200 exitoso

`POST http://{{vm_host}}:8001/api/v1/auth/login`

**Request - headers:**

```http
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "email": "josue.analista@demo.mx",
  "password": "***"
}
```

**Response - 200 OK** (244 ms, 985 bytes):

```http
Content-Type: application/json
Content-Length: 985
X-Correlation-ID: a880dfea42a14259
```

```json
{
  "token_type": "Bearer",
  "access_token": "***jwt***",
  "expires_in": 900,
  "refresh_token": "***jwt***",
  "refresh_expires_in": 28800,
  "usuario": {
    "id": 16,
    "nombre": "Josue Berdeal",
    "email": "josue.analista@demo.mx",
    "rol": "Analista de Devoluciones"
  }
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: emite el par de tokens
- ok: el rol viaja en la respuesta

## 004_auth_post_login_200_xml

Carpeta: 01 Login - Caso: login 200 XML (admin)

`POST http://{{vm_host}}:8001/api/v1/auth/login`

**Request - headers:**

```http
Content-Type: application/xml
Accept: application/xml
```

**Request - body:**

```
<login>
  <email>pablo.admin@demo.mx</email>
  <password>***</password>
</login>
```

**Response - 200 OK** (228 ms, 1081 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 1081
X-Correlation-ID: 634a1ce737cf4cff
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<respuesta><token_type>Bearer</token_type><access_token>***jwt***</access_token><expires_in>900</expires_in><refresh_token>***jwt***</refresh_token><refresh_expires_in>28800</refresh_expires_in><usuario><id>18</id><nombre>Pablo Flores</nombre><email>pablo.admin@demo.mx</email><rol>Administrador</rol></usuario></respuesta>
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: trae access_token

## 005_auth_post_login_400

Carpeta: 01 Login - Caso: login 400 datos invalidos

`POST http://{{vm_host}}:8001/api/v1/auth/login`

**Request - headers:**

```http
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "email": "no-es-correo",
  "password": "***"
}
```

**Response - 400 BAD REQUEST** (81 ms, 232 bytes):

```http
Content-Type: application/json
Content-Length: 232
X-Correlation-ID: dbd49720932b47b8
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Datos de acceso incompletos.",
    "detalles": [
      {
        "campo": "email",
        "problema": "formato invalido"
      },
      {
        "campo": "password",
        "problema": "es obligatorio"
      }
    ],
    "correlation_id": "dbd49720932b47b8"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 006_auth_post_login_401

Carpeta: 01 Login - Caso: login 401 credenciales invalidas

`POST http://{{vm_host}}:8001/api/v1/auth/login`

**Request - headers:**

```http
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "email": "nadie@demo.mx",
  "password": "***"
}
```

**Response - 401 UNAUTHORIZED** (93 ms, 154 bytes):

```http
Content-Type: application/json
Content-Length: 154
X-Correlation-ID: 0f5be23fde49497a
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "credenciales_invalidas",
    "mensaje": "Correo o contrasena incorrectos.",
    "detalles": null,
    "correlation_id": "0f5be23fde49497a"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = credenciales_invalidas
- ok: Trae X-Correlation-ID

## 007_auth_post_login_415

Carpeta: 01 Login - Caso: login 415 formato no soportado

`POST http://{{vm_host}}:8001/api/v1/auth/login`

**Request - headers:**

```http
Content-Type: text/plain
Accept: application/json
```

**Request - body:**

```
email=x
```

**Response - 415 UNSUPPORTED MEDIA TYPE** (80 ms, 172 bytes):

```http
Content-Type: application/json
Content-Length: 172
X-Correlation-ID: 4d75b746b77144e8
```

```json
{
  "error": {
    "codigo": 415,
    "tipo": "formato_no_soportado",
    "mensaje": "Usa Content-Type application/json o application/xml.",
    "detalles": null,
    "correlation_id": "4d75b746b77144e8"
  }
}
```

**Verificaciones:**

- ok: HTTP 415
- ok: error.tipo = formato_no_soportado
- ok: Trae X-Correlation-ID

## 008_auth_post_login_400_xml

Carpeta: 01 Login - Caso: login 400 XML mal formado

`POST http://{{vm_host}}:8001/api/v1/auth/login`

**Request - headers:**

```http
Content-Type: application/xml
Accept: application/xml
```

**Request - body:**

```
<login><email>x</login>
```

**Response - 400 BAD REQUEST** (154 ms, 280 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 280
X-Correlation-ID: 876ddf0293bf4b2c
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<error><codigo>400</codigo><tipo>xml_invalido</tipo><mensaje>El cuerpo no es un documento XML bien formado.</mensaje><detalles><item>mismatched tag: line 1, column 17</item></detalles><correlation_id>876ddf0293bf4b2c</correlation_id></error>
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = xml_invalido
- ok: Trae X-Correlation-ID

## 009_auth_post_login_400_xml

Carpeta: 01 Login - Caso: login 400 XML no cumple XSD

`POST http://{{vm_host}}:8001/api/v1/auth/login`

**Request - headers:**

```http
Content-Type: application/xml
Accept: application/xml
```

**Request - body:**

```
<login>
  <email>josue.analista@demo.mx</email>
</login>
```

**Response - 400 BAD REQUEST** (78 ms, 353 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 353
X-Correlation-ID: 39c75575a88a4d1e
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<error><codigo>400</codigo><tipo>xml_no_cumple_xsd</tipo><mensaje>El XML no cumple el contrato del endpoint.</mensaje><detalles><item><linea>1</linea><problema>Element 'login': Missing child element(s). Expected is ( password ).</problema></item></detalles><correlation_id>39c75575a88a4d1e</correlation_id></error>
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = xml_no_cumple_xsd
- ok: Trae X-Correlation-ID

## 010_auth_get_sesion_200

Carpeta: 02 Sesion - Caso: sesion 200 exitoso

`GET http://{{vm_host}}:8001/api/v1/auth/sesion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (82 ms, 199 bytes):

```http
Content-Type: application/json
Content-Length: 199
X-Correlation-ID: 255ffa2192404251
```

```json
{
  "usuario": {
    "id": 16,
    "rol": "Analista de Devoluciones",
    "nombre": "Josue Berdeal"
  },
  "sesion_id": "9e3a11b507a440129d18c8a9a3ffe7cb",
  "sesion_expira_en_seg": 28799,
  "token_expira": "2026-10-22T00:46:36+00:00"
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: trae sesion_id y usuario

## 011_auth_get_sesion_200_xml

Carpeta: 02 Sesion - Caso: sesion 200 XML

`GET http://{{vm_host}}:8001/api/v1/auth/sesion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/xml
```

**Response - 200 OK** (81 ms, 316 bytes):

```http
Content-Type: application/xml; charset=utf-8
Content-Length: 316
X-Correlation-ID: 564e754958204005
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<respuesta><usuario><id>16</id><rol>Analista de Devoluciones</rol><nombre>Josue Berdeal</nombre></usuario><sesion_id>9e3a11b507a440129d18c8a9a3ffe7cb</sesion_id><sesion_expira_en_seg>28799</sesion_expira_en_seg><token_expira>2026-10-22T00:46:36+00:00</token_expira></respuesta>
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: trae sesion_id

## 012_auth_get_sesion_401

Carpeta: 02 Sesion - Caso: sesion 401 sin token

`GET http://{{vm_host}}:8001/api/v1/auth/sesion`

**Request - headers:**

```http
Accept: application/json
```

**Response - 401 UNAUTHORIZED** (160 ms, 162 bytes):

```http
Content-Type: application/json
Content-Length: 162
X-Correlation-ID: 222eb4545b8f4afc
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "no_autenticado",
    "mensaje": "Falta el header 'Authorization: Bearer <token>'.",
    "detalles": null,
    "correlation_id": "222eb4545b8f4afc"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = no_autenticado
- ok: Trae X-Correlation-ID

## 013_auth_get_sesion_401

Carpeta: 02 Sesion - Caso: sesion 401 token invalido

`GET http://{{vm_host}}:8001/api/v1/auth/sesion`

**Request - headers:**

```http
Authorization: Bearer esto-no-es-un-token
Accept: application/json
```

**Response - 401 UNAUTHORIZED** (77 ms, 136 bytes):

```http
Content-Type: application/json
Content-Length: 136
X-Correlation-ID: 633fded0ffea4a6d
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "token_invalido",
    "mensaje": "El token no es valido.",
    "detalles": null,
    "correlation_id": "633fded0ffea4a6d"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = token_invalido
- ok: Trae X-Correlation-ID

## 014_auth_post_refresh_200

Carpeta: 03 Refresh - Caso: refresh 200 exitoso

`POST http://{{vm_host}}:8001/api/v1/auth/refresh`

**Request - headers:**

```http
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "refresh_token": "***jwt***"
}
```

**Response - 200 OK** (77 ms, 443 bytes):

```http
Content-Type: application/json
Content-Length: 443
X-Correlation-ID: 295ba7b8c9294851
```

```json
{
  "token_type": "Bearer",
  "access_token": "***jwt***",
  "expires_in": 900
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: access nuevo

## 015_auth_post_refresh_401

Carpeta: 03 Refresh - Caso: refresh 401 con access token

`POST http://{{vm_host}}:8001/api/v1/auth/refresh`

**Request - headers:**

```http
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "refresh_token": "***jwt***"
}
```

**Response - 401 UNAUTHORIZED** (79 ms, 153 bytes):

```http
Content-Type: application/json
Content-Length: 153
X-Correlation-ID: 9289d1647f0c4f85
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "token_invalido",
    "mensaje": "Se esperaba un token de tipo 'refresh'.",
    "detalles": null,
    "correlation_id": "9289d1647f0c4f85"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = token_invalido
- ok: Trae X-Correlation-ID

## 016_auth_post_refresh_400

Carpeta: 03 Refresh - Caso: refresh 400 sin refresh_token

`POST http://{{vm_host}}:8001/api/v1/auth/refresh`

**Request - headers:**

```http
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{}
```

**Response - 400 BAD REQUEST** (79 ms, 181 bytes):

```http
Content-Type: application/json
Content-Length: 181
X-Correlation-ID: d57d0f475e804cd1
```

```json
{
  "error": {
    "codigo": 400,
    "tipo": "validacion",
    "mensaje": "Falta refresh_token.",
    "detalles": [
      {
        "campo": "refresh_token",
        "problema": "es obligatorio"
      }
    ],
    "correlation_id": "d57d0f475e804cd1"
  }
}
```

**Verificaciones:**

- ok: HTTP 400
- ok: error.tipo = validacion
- ok: Trae X-Correlation-ID

## 017_auth_delete_usuarios_id_sesiones_403

Carpeta: 04 Administracion de sesiones - Caso: cerrar sesiones 403 rol sin permiso

`DELETE http://{{vm_host}}:8001/api/v1/auth/usuarios/16/sesiones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 403 FORBIDDEN** (153 ms, 222 bytes):

```http
Content-Type: application/json
Content-Length: 222
X-Correlation-ID: 39b3001839fa4f0f
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
    "correlation_id": "39b3001839fa4f0f"
  }
}
```

**Verificaciones:**

- ok: HTTP 403
- ok: error.tipo = sin_permiso
- ok: Trae X-Correlation-ID

## 018_auth_delete_usuarios_id_sesiones_404

Carpeta: 04 Administracion de sesiones - Caso: cerrar sesiones 404 usuario inexistente

`DELETE http://{{vm_host}}:8001/api/v1/auth/usuarios/999999/sesiones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 404 NOT FOUND** (82 ms, 141 bytes):

```http
Content-Type: application/json
Content-Length: 141
X-Correlation-ID: 875532dded3b48a6
```

```json
{
  "error": {
    "codigo": 404,
    "tipo": "no_encontrado",
    "mensaje": "No existe el usuario 999999.",
    "detalles": null,
    "correlation_id": "875532dded3b48a6"
  }
}
```

**Verificaciones:**

- ok: HTTP 404
- ok: error.tipo = no_encontrado
- ok: Trae X-Correlation-ID

## 019_auth_post_logout_200

Carpeta: 05 Revocacion - Caso: logout 200 exitoso

`POST http://{{vm_host}}:8001/api/v1/auth/logout`

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

**Response - 200 OK** (106 ms, 56 bytes):

```http
Content-Type: application/json
Content-Length: 56
X-Correlation-ID: c9c3ea5ae8444d01
```

```json
{
  "mensaje": "Sesion cerrada. El token ya no es valido."
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID

## 020_auth_get_sesion_401

Carpeta: 05 Revocacion - Caso: sesion 401 token revocado

`GET http://{{vm_host}}:8001/api/v1/auth/sesion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 401 UNAUTHORIZED** (78 ms, 160 bytes):

```http
Content-Type: application/json
Content-Length: 160
X-Correlation-ID: 1da89e8b24af4344
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "token_revocado",
    "mensaje": "El token fue revocado. Inicia sesion de nuevo.",
    "detalles": null,
    "correlation_id": "1da89e8b24af4344"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = token_revocado
- ok: Trae X-Correlation-ID

## 021_auth_post_refresh_401

Carpeta: 05 Revocacion - Caso: refresh 401 sesion inactiva

`POST http://{{vm_host}}:8001/api/v1/auth/refresh`

**Request - headers:**

```http
Content-Type: application/json
Accept: application/json
```

**Request - body:**

```
{
  "refresh_token": "***jwt***"
}
```

**Response - 401 UNAUTHORIZED** (152 ms, 167 bytes):

```http
Content-Type: application/json
Content-Length: 167
X-Correlation-ID: 1f6ea2d0c00341bc
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "sesion_inactiva",
    "mensaje": "La sesion ya no esta activa. Inicia sesion de nuevo.",
    "detalles": null,
    "correlation_id": "1f6ea2d0c00341bc"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = sesion_inactiva
- ok: Trae X-Correlation-ID

## 022_auth_delete_usuarios_id_sesiones_200

Carpeta: 05 Revocacion - Caso: cerrar sesiones 200 admin

`DELETE http://{{vm_host}}:8001/api/v1/auth/usuarios/16/sesiones`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 200 OK** (90 ms, 40 bytes):

```http
Content-Type: application/json
Content-Length: 40
X-Correlation-ID: 0ce20eff754a4688
```

```json
{
  "usuario_id": 16,
  "sesiones_cerradas": 1
}
```

**Verificaciones:**

- ok: HTTP 200
- ok: Trae X-Correlation-ID
- ok: cerro al menos una

## 023_auth_get_sesion_401

Carpeta: 05 Revocacion - Caso: sesion 401 sesion inactiva

`GET http://{{vm_host}}:8001/api/v1/auth/sesion`

**Request - headers:**

```http
Authorization: Bearer ***jwt***
Accept: application/json
```

**Response - 401 UNAUTHORIZED** (73 ms, 167 bytes):

```http
Content-Type: application/json
Content-Length: 167
X-Correlation-ID: fc800d5c55d940e8
```

```json
{
  "error": {
    "codigo": 401,
    "tipo": "sesion_inactiva",
    "mensaje": "La sesion ya no esta activa. Inicia sesion de nuevo.",
    "detalles": null,
    "correlation_id": "fc800d5c55d940e8"
  }
}
```

**Verificaciones:**

- ok: HTTP 401
- ok: error.tipo = sesion_inactiva
- ok: Trae X-Correlation-ID

