# Comunicacion del web con los microservicios

Describe como `apps/web/app/api_client.py` llama a las API. Verificado contra
ese modulo, `apps/web/app/config.py`, `apps/web/app/blueprints/auth.py`,
`apps/web/app/microservicios.py` y `apps/web/app/security.py`.

Trazabilidad: RF-31, RF-32, RNF-04, RNF-08, RNF-22, RNF-23.

```mermaid
sequenceDiagram
    autonumber
    actor U as Usuario (navegador)
    participant W as Web Flask :8000
    participant RS as Redis (sesion del web)
    participant A as auth
    participant S as Servicio de negocio

    U->>W: POST /login (formulario)
    W->>A: POST /api/v1/auth/login<br/>Accept application/json + X-Correlation-ID
    A-->>W: access_token, refresh_token, usuario
    W->>RS: Flask-Session guarda usuario, access y refresh<br/>(clave devoluciones:sesion:ID, cookie firmada HttpOnly)
    W-->>U: 302 al panel (los JWT nunca llegan al navegador)

    U->>W: accion de negocio (p. ej. resolver una devolucion)
    W->>RS: lee la sesion
    W->>S: PATCH /api/v1/devoluciones/ID/resolucion<br/>Authorization Bearer ACCESS<br/>X-Correlation-ID, timeout 5 s
    alt 2xx
        S-->>W: JSON
        W-->>U: redireccion con mensaje
    else 401 y hay refresh_token (un solo reintento)
        S-->>W: 401 token_expirado
        W->>A: POST /api/v1/auth/refresh (refresh_token)
        alt renovacion correcta
            A-->>W: nuevo access_token
            W->>RS: actualiza access_token en la sesion
            W->>S: repite la peticion original (reintentar = false)
            S-->>W: JSON
            W-->>U: redireccion con mensaje
        else renovacion rechazada
            A-->>W: 401
            W->>RS: session.clear()
            W-->>U: error de sesion, hay que iniciar sesion
        end
    else 4xx o 5xx de negocio
        S-->>W: error JSON uniforme
        W-->>U: el mensaje del servicio (ErrorServicio conserva tipo, detalles y correlation_id)
    else servicio sin respuesta o timeout
        W-->>U: 503 servicio_no_disponible (sin fallback silencioso)
    end
```

## Encabezados y formato

| Aspecto | Lo que hace el codigo |
|---|---|
| Autenticacion | `Authorization: Bearer <access_token>` tomado de la sesion del servidor (`session["access_token"]`). |
| Correlacion | `X-Correlation-ID` con `security.correlation_id()`: un identificador de 16 caracteres por peticion web. El servicio lo respeta (`shared/respuestas.py`) y lo devuelve en la respuesta y en la bitacora. |
| Formato | El web envia y pide **JSON** (`Accept` y `Content-Type: application/json`). No negocia XML. |
| Renovacion | Un solo reintento tras un 401; si `refresh` falla se limpia la sesion. |
| Timeout | `MICROSERVICE_TIMEOUT` (5 s por defecto). Errores de red se convierten en `ErrorServicio` 503 `servicio_no_disponible`. |
| Direcciones | `SERVICE_URLS` de `config.py`, por ejemplo `http://auth:8000` (DNS interno de Compose). |
| Salud | `microservicios.estado_arquitectura()` consulta `GET /health` de los ocho servicios con timeout de 2 s para el panel `/integracion/servicios` (solo Administrador). |
| Contingencia | `USE_MICROSERVICES=false` devuelve las rutas a su logica de monolito. No hay fallback automatico. |

## Negociacion JSON / XML (lado servidor)

El XML existe para el cliente de escritorio, no para el web. El servidor decide
el formato de la respuesta con `Accept` (`shared/respuestas.py:quiere_xml`) y
acepta cuerpos `application/json` o `application/xml`.

```mermaid
flowchart LR
    REQ["Peticion con Accept y Content-Type"] --> CT{"Content-Type"}
    CT -->|application/json| J["JSON a dict"]
    CT -->|"application/xml o text/xml"| X{"el endpoint declara XSD?"}
    X -->|si| V["shared/xsd.py valida contra el XSD<br/>sin entidades externas ni red"]
    X -->|no| P["ElementTree a dict"]
    V -->|invalido| E400["400 xml_no_cumple_xsd<br/>linea y problema"]
    V -->|valido| P
    CT -->|otro| E415["415 formato_no_soportado"]
    J --> L["logica del endpoint"]
    P --> L
    L --> AC{"Accept"}
    AC -->|"application/json o ausente"| RJ["respuesta JSON"]
    AC -->|"application/xml"| RX["respuesta XML con declaracion UTF-8"]
```

> **EVIDENCIA PENDIENTE [EV-05]:** captura de la bitacora o de los logs de dos
> servicios con el mismo `correlation_id` originado en una accion del web.
> <!-- EVIDENCIA PENDIENTE: EV-05 correlation_id de punta a punta -->
