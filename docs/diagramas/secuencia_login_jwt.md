# Secuencia: login, JWT, verificacion entre servicios y revocacion

Verificado contra `services/auth/app.py` y `shared/seguridad.py`. Las claves
Redis llevan el prefijo `devoluciones:` (ver `redis_claves.md`).

Trazabilidad: RF-01, RNF-07, RNF-08, RNF-09, RNF-12, RNF-13, RNF-16, RNF-21.

## 1. Login y emision de tokens

```mermaid
sequenceDiagram
    autonumber
    actor C as Cliente HTTP (web o app)
    participant A as auth :8001
    participant R as Redis
    participant P as PostgreSQL

    C->>A: POST /api/v1/auth/login (email, password) JSON o XML
    A->>R: INCR limite:IP:login (TTL 60 s, maximo 10 por minuto)
    alt supera el limite
        A-->>C: 429 demasiadas_peticiones + Retry-After
    end
    A->>A: valida cuerpo (y XSD login.xsd si es XML)
    A->>P: SELECT usuario + rol (eliminado_en IS NULL)
    A->>R: TTL bloqueo:email
    alt cuenta bloqueada (Redis o usuarios.bloqueado_hasta)
        A->>P: INSERT intentos_acceso (exitoso = false) y bitacora
        A-->>C: 423 cuenta_bloqueada
    end
    alt usuario inexistente, inactivo o password incorrecta
        A->>P: INSERT intentos_acceso (exitoso = false)
        A->>R: INCR intentos:email (TTL = minutos de bloqueo)
        opt intentos >= 5
            A->>R: SETEX bloqueo:email
            A->>P: UPDATE usuarios SET bloqueado_hasta
        end
        A-->>C: 401 credenciales_invalidas (mensaje generico)
    else credenciales validas
        A->>R: DEL intentos:email y bloqueo:email
        A->>P: UPDATE bloqueado_hasta = NULL, INSERT intentos_acceso (exitoso = true)
        A->>R: HSET sesion_api:SID (usuario_id, rol, ip, creada) + EXPIRE 8 h
        A->>R: SADD sesiones_usuario:ID SID + EXPIRE 8 h
        A->>A: firma access (typ=access, 15 min) y refresh (typ=refresh, 8 h) HS256
        A->>P: INSERT bitacora (login_api)
        A-->>C: 200 access_token, refresh_token, expires_in, usuario
    end
```

Los claims de ambos tokens son `iss`, `sub`, `rol`, `nombre`, `sid`, `jti`,
`typ`, `iat` y `exp`. El `sid` enlaza el token con su sesion en Redis; el `jti`
identifica al token individual para poder revocarlo.

## 2. Verificacion en cualquier otro servicio

Es el decorador `requiere_jwt(*roles)`; lo ejecutan los ocho servicios en cada
endpoint protegido.

```mermaid
sequenceDiagram
    autonumber
    actor C as Cliente HTTP
    participant S as Servicio X (p. ej. devoluciones :8002)
    participant R as Redis

    C->>S: GET /api/v1/... con Authorization Bearer ACCESS
    S->>S: falta o malformado el header -> 401 no_autenticado
    S->>S: decodifica HS256, exige iss, exp, iat, sub, jti, sid, typ
    alt expirado
        S-->>C: 401 token_expirado
    else firma o claims invalidos, o typ distinto de access
        S-->>C: 401 token_invalido
    end
    S->>R: EXISTS jwt_revocado:JTI
    S->>R: EXISTS sesion_api:SID
    alt Redis no responde
        S-->>C: 503 seguridad_no_disponible (falla cerrada)
    else token en la lista de revocados
        S-->>C: 401 token_revocado
    else la sesion ya no existe
        S-->>C: 401 sesion_inactiva
    end
    S->>S: el rol del token esta en los roles permitidos?
    alt rol no permitido
        S-->>C: 403 sin_permiso (rol y roles_permitidos)
    else permitido
        S-->>C: respuesta del endpoint (200, 201...)
    end
```

## 3. Renovacion, logout y revocacion

```mermaid
sequenceDiagram
    autonumber
    actor C as Cliente HTTP
    actor ADM as Administrador
    participant A as auth :8001
    participant R as Redis
    participant S as Otro servicio

    Note over C,A: Renovacion
    C->>A: POST /api/v1/auth/refresh (refresh_token)
    A->>A: decodifica con typ=refresh
    A->>R: EXISTS jwt_revocado y sesion_api del refresh
    A-->>C: 200 nuevo access_token (la sesion y el refresh no cambian)

    Note over C,A: Logout
    C->>A: POST /api/v1/auth/logout con Bearer ACCESS
    A->>R: SETEX jwt_revocado:JTI con el tiempo restante del token
    A->>R: DEL sesion_api:SID y SREM sesiones_usuario:ID SID
    A-->>C: 200 sesion cerrada
    C->>S: GET con el mismo ACCESS
    S->>R: EXISTS jwt_revocado:JTI
    S-->>C: 401 token_revocado
    C->>A: POST /refresh con el refresh de esa sesion
    A->>R: EXISTS sesion_api:SID
    A-->>C: 401 sesion_inactiva (el refresh muere con la sesion)

    Note over ADM,A: Revocacion global de un usuario
    ADM->>A: DELETE /api/v1/auth/usuarios/ID/sesiones
    A->>R: SMEMBERS sesiones_usuario:ID, DEL de cada sesion_api:SID y de la lista
    A-->>ADM: 200 sesiones_cerradas = N
```

Notas verificadas en el codigo:

- El logout solo agrega a la lista negra el `jti` del **access** token que se
  presento; el refresh queda inutil porque se borra la sesion `sesion_api:<sid>`
  que `refresh` exige.
- La revocacion global usa `SMEMBERS` sobre `sesiones_usuario:<id>`; los
  access tokens ya emitidos dejan de servir sin esperar su vencimiento porque
  su `sid` ya no tiene sesion.
- Los tiempos salen de `JWT_MINUTOS_ACCESO` (15) y `JWT_HORAS_REFRESH` (8);
  el limite de login de `LOGIN_MAX_POR_MINUTO` (10) y `refresh` tiene un
  limite fijo de 30 por minuto.

> **EVIDENCIA PENDIENTE [EV-03]:** captura del login real con su respuesta y de
> `redis-cli` mostrando `sesion_api:*` con TTL y, tras el logout, el
> `jwt_revocado:*` correspondiente.
> <!-- EVIDENCIA PENDIENTE: EV-03 login, sesion y blacklist en Redis -->
