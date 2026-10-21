# Pruebas (RNF-28, apartado 12 del enunciado)

Documento de casos de prueba del segundo parcial. Una fila por caso con el
formato pedido: ID, servicio, objetivo, entradas, resultado esperado, resultado
obtenido, estado y evidencia.

**Regla de honestidad del documento.** Una prueba solo figura como `paso` si hay
salida real de `pytest -v`. Lo que necesita PostgreSQL, MongoDB y Redis solo
corre en la VM (CLAUDE.md, restriccion 1), asi que sus tres ultimas columnas
estan como `<!-- EJECUTAR EN VM -->` hasta que alguien pegue la salida real (ver "Como registrar el
resultado de la VM").

## Resumen

| Grupo | Casos | Donde corre | Estado |
|---|---|---|---|
| Unitarias (con dobles) | 119 | Local y VM | **119 passed** en local (`docs/pruebas/resultado_2026-10-21_local.md`) |
| E2E: proceso completo de 11 pasos + notificaciones (6b) | 12 | Solo VM | VM 2026-10-21: **12 de 12 pasan** en la 2a corrida (la 1a fallo E2E-06 por prueba desactualizada y E2E-09 por el bug H-11, ya corregidos) |
| E2E: seguridad y errores | 23 filas (80 casos con parametros) | Solo VM | VM 2026-10-21: **23 de 23 pasan** en la 2a corrida (SEG-15 a SEG-20 habian fallado en cascada por `sin_disponible`) |
| E2E: JSON/XML y XSD | 8 | Solo VM | VM 2026-10-21: **8 de 8 pasan** en la 2a corrida (FMT-04 habia fallado en cascada) |
| Integracion por servicio | 30 nuevas + 4 previas de devoluciones | Solo VM | VM 2026-10-21: **8 de 8 servicios pasan**: auth 5/5, ventas 4/4, evidencias 4/4, logistica 3/3, inspecciones 5/5, reembolsos 5/5, analisis 4/4 y devoluciones 4/4 (tras PR #8 y PR #9) |

Validado localmente sin bases: compilacion (`py_compile`), descubrimiento
(`pytest --collect-only`) y las unitarias. La suite E2E descubre **100** pruebas
y las pruebas de integracion por servicio descubren 34 mas (30 nuevas y las 4
previas de devoluciones); sin `INTEGRACION=1` todas se saltan.

**Corridas en la VM (2026-10-21, `scripts/correr_e2e.sh`):**

| Corrida | Resultado |
|---|---|
| 1a (`main` con las sesiones 01 a 03) | E2E 91 de 100: 2 fallos reales (E2E-06 prueba desactualizada, E2E-09 bug H-11) y 7 en cascada por agotar la linea de venta. Integracion: auth, ventas y evidencias pasan; devoluciones 3/4; logistica, inspecciones, reembolsos y analisis sin resultado por 429 (H-07) |
| 1b (`correr_e2e.sh servicios`, limite de login subido temporalmente) | logistica 3/3, inspecciones 5/5 y analisis 4/4 pasan; reembolsos 4/5 (el bug H-11 de nuevo); devoluciones con 401 al iniciar (cuenta real `prueba@gmail.com`, sin contrasena demo) |
| 2a (tras PR #8: bug H-11 y ajustes de la suite) | **E2E 100 de 100 (100 passed in 5.84 s)**; integracion: 7 de 8 servicios sin fallos, devoluciones con un fallo porque la imagen aun traia la prueba vieja |
| 3a (tras PR #9 e imagen de `devoluciones` reconstruida) | devoluciones **4 passed in 1.33 s** |

Resultado final: **E2E 100/100 e integracion por servicio 8/8**. Cada correccion
quedo reconfirmada en la VM con la misma suite. Detalle de la primera corrida y
sus causas en `docs/pruebas/resultado_2026-10-21.md`; la salida completa de la
VM esta en `docs/pruebas/salida_2026-10-21.txt` (2a corrida) y
`docs/pruebas/salida_2026-10-21_servicios.txt` (1b), cuando se versionan desde la VM.

## Como ejecutar

### Unitarias (local o VM, no necesitan bases)

Cada servicio importa su propio `app.py`, asi que se corren por carpeta:

```bash
pip install -r services/auth/requirements.txt pytest   # una vez, en un entorno virtual
for s in services/*/; do (cd "$s" && PYTHONPATH="$OLDPWD:." python -m pytest -q tests); done
(cd apps/web && PYTHONPATH="$OLDPWD:." python -m pytest -q app/tests)
```

### Todo contra el entorno real (solo en la VM)

Requisitos: `git pull` de la rama, `docker compose up -d --build`, migraciones y
`seed_demo.py` aplicados, y `PASSWORD_DEMO` en el `.env`.

```bash
bash scripts/correr_e2e.sh            # E2E + integracion por servicio, guarda docs/pruebas/salida_<fecha>.txt
bash scripts/correr_e2e.sh e2e        # solo la suite E2E
bash scripts/correr_e2e.sh servicios  # solo integracion por servicio
```

Comandos individuales (los que usa el script):

```bash
# Suite E2E: el repositorio se monta para que vea tests/, shared/ y los XSD
docker compose run --rm -v "$PWD":/repo -w /repo -e PYTHONPATH=/repo -e INTEGRACION=1 devoluciones python -m pytest -v -s tests/e2e

# Integracion de un servicio (ejemplo)
docker compose run --rm -e INTEGRACION=1 logistica python -m pytest -v tests/test_integracion.py
```

`-s` deja ver las lineas `[E2E] METODO ruta -> codigo cuerpo`, que sirven como
evidencia. Nunca contienen tokens ni contrasenas (RNF-16). Los nombres de
servicio del compose son: `auth`, `ventas-catalogos`, `devoluciones`,
`evidencias`, `logistica`, `inspecciones`, `reembolsos-costos`,
`analisis-auditoria`.

### Variables de entorno de la suite E2E

| Variable | Por defecto | Uso |
|---|---|---|
| `INTEGRACION` | — | Debe ser `1`; sin ella todo se salta |
| `PASSWORD_DEMO` | del `.env` | Contrasena de las cuentas del seed; nunca se escribe en el repositorio |
| `AUTH_URL`, `DEVOLUCIONES_URL`, `LOGISTICA_URL`, `INSPECCIONES_URL`, `REEMBOLSOS_URL`, `VENTAS_URL`, `EVIDENCIAS_URL`, `ANALISIS_URL` | `http://<servicio>:8000` | URL de cada contenedor dentro de la red del compose |
| `POSTGRES_*`, `MONGO_*`, `REDIS_*`, `JWT_SECRET` | del `.env` | Los inyecta `env_file` del compose; la suite verifica efectos y firma tokens de prueba |
| `WEB_URL` | `http://app:8000` | Monolito web, solo para el paso 6b (campanita) |
| `LOGIN_MAX_POR_MINUTO` | 10 | Solo para que la prueba de 429 sepa cuantos intentos hacer |

Dependencias: las de la imagen de `devoluciones` (`psycopg2`, `pymongo`,
`redis`, `PyJWT`, `lxml`, `pytest`); no se agrego ninguna.

### Como registrar el resultado de la VM

1. Corre `bash scripts/correr_e2e.sh` (genera `docs/pruebas/salida_<fecha>.txt`).
2. Copia `docs/pruebas/resultado_plantilla.md` a `docs/pruebas/resultado_AAAA-MM-DD.md`
   y pega ahi el resumen final de cada `pytest -v` y las lineas `[E2E]` de los pasos
   que se citaran en el documento tecnico.
3. En este archivo reemplaza cada `<!-- EJECUTAR EN VM -->` por el resultado real (`passed` o el
   error), el estado (`paso`/`fallo`) y la ruta de la evidencia. Si algo falla,
   no lo marques `paso`: agrega el hallazgo abajo.
4. La sesion 01 (campanita) ya esta en `main`: el paso 6b del E2E la cubre; no hay
   pasos pendientes por integracion de otras sesiones.

## Pruebas unitarias (119)

| ID | Servicio | Objetivo | Entradas | Resultado esperado | Resultado obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|---|
| UT-01 | auth | Login, refresh, logout, revocacion, bloqueo y rate limit con dobles de Redis/PostgreSQL (RNF-08, RNF-12, RNF-13) | `services/auth/tests/test_auth.py`: 27 casos, con dobles, sin bases | Los 27 casos pasan | 27 passed | paso | `docs/pruebas/resultado_2026-10-21_local.md` |
| UT-02 | devoluciones | Endpoints de devoluciones con dobles (roles, validacion, JSON/XML) (RF-07, RF-10, RN-13) | `services/devoluciones/tests/test_api.py`: 13 casos, con dobles, sin bases | Los 13 casos pasan | 13 passed | paso | `docs/pruebas/resultado_2026-10-21_local.md` |
| UT-03 | devoluciones | Validaciones puras de solicitud, edicion y resolucion (RF-07, RF-10, RN-01) | `services/devoluciones/tests/test_reglas.py`: 11 casos, con dobles, sin bases | Los 11 casos pasan | 11 passed | paso | `docs/pruebas/resultado_2026-10-21_local.md` |
| UT-04 | evidencias | Firma real del archivo, enlaces firmados y nombre seguro (RN-14, RNF-10) | `services/evidencias/tests/test_seguridad_archivos.py`: 3 casos, con dobles, sin bases | Los 3 casos pasan | 3 passed | paso | `docs/pruebas/resultado_2026-10-21_local.md` |
| UT-05 | inspecciones | `evaluar_aptitud`: danos, caducidad, cadena de frio y 30 minutos (RN-05, RN-06, RN-07) | `services/inspecciones/tests/test_reglas.py`: 5 casos, con dobles, sin bases | Los 5 casos pasan | 5 passed | paso | `docs/pruebas/resultado_2026-10-21_local.md` |
| UT-06 | logistica | Transiciones de recoleccion y validaciones con dobles (RF-12 a RF-15, RN-08) | `services/logistica/tests/test_api.py`: 5 casos, con dobles, sin bases | Los 5 casos pasan | 5 passed | paso | `docs/pruebas/resultado_2026-10-21_local.md` |
| UT-07 | reembolsos_costos | Reembolso, lock, costos por rol y montos con dobles (RF-20, RF-27, RN-03, RN-04) | `services/reembolsos_costos/tests/test_api.py`: 6 casos, con dobles, sin bases | Los 6 casos pasan | 6 passed | paso | `docs/pruebas/resultado_2026-10-21_local.md` |
| UT-08 | ventas_catalogos | Validacion de catalogos y permisos de lectura (RF-04 a RF-06) | `services/ventas_catalogos/tests/test_reglas.py`: 8 casos, con dobles, sin bases | Los 8 casos pasan | 8 passed | paso | `docs/pruebas/resultado_2026-10-21_local.md` |
| UT-09 | analisis_auditoria | Pareto y clasificador de motivos (sin bases) (RF-23, RN-09, RN-11) | `services/analisis_auditoria/tests/test_pareto.py`: 4 casos, con dobles, sin bases | Los 4 casos pasan | 4 passed | paso | `docs/pruebas/resultado_2026-10-21_local.md` |
| UT-10 | web | Cliente HTTP del monolito hacia los microservicios (JWT, correlation id) (RNF-23) | `apps/web/app/tests/test_api_client.py`: 3 casos, con dobles, sin bases | Los 3 casos pasan | 3 passed | paso | `docs/pruebas/resultado_2026-10-21_local.md` |
| UT-11 | web | Panel de microservicios y manejo de caidas (RF-31) | `apps/web/app/tests/test_microservicios.py`: 3 casos, con dobles, sin bases | Los 3 casos pasan | 3 passed | paso | `docs/pruebas/resultado_2026-10-21_local.md` |
| UT-12 | web | Exportacion CSV: BOM, streaming y escape de formulas (RF-28, UC-24) | `apps/web/app/tests/test_exportacion.py`: 16 casos, con dobles, sin bases | Los 16 casos pasan | 16 passed | paso | `docs/pruebas/resultado_2026-10-21_local.md` |
| UT-13 | web | Matriz de destinatarios, bandeja y campanita por rol (sesion 01) (RF-29, UC-25, RN-13) | `apps/web/app/tests/test_notificaciones.py`: 15 casos, con dobles, sin bases | Los 15 casos pasan | 15 passed | paso | `docs/pruebas/resultado_2026-10-21_local.md` |

Salida local (2026-10-21, Python 3.13, `pytest` 8.3.3, sin bases, rama ya fusionada con `main` incluida la sesion 01): 119 passed, 0 failed; el detalle caso por caso esta en `docs/pruebas/resultado_2026-10-21_local.md`. La
cifra de 84 que citaba el brief es anterior a la sesion 01; el conteo real de `pytest
--collect-only` por archivo es el de la tabla. Las pruebas de integracion de
cada carpeta (`test_integracion.py`) se cuentan abajo y se saltan en local.

## Pruebas de integracion y E2E

Estas pruebas usan HTTP real, PostgreSQL, MongoDB y Redis. Prefijos: `E2E` (proceso
completo), `SEG` (seguridad y errores), `FMT` (JSON/XML/XSD), `INT-xxx` (por servicio).

### E2E — proceso completo de 11 pasos (`tests/e2e/test_01_proceso_completo.py`)

| ID | Servicio | Objetivo | Entradas | Resultado esperado | Resultado obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|---|
| E2E-01 | auth | Paso 1: login real y GET protegido; sesion en Redis con TTL | POST /auth/login (cliente del seed), GET /auth/sesion | 200; `devoluciones:sesion_api:<sid>` existe con 0 < TTL <= 8 h | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| E2E-02 | ventas-catalogos | Paso 2: localizar linea vendida del cliente con paginacion | GET /ventas?q=<folio>, GET /ventas/{id} | 200; `paginacion` completa; la linea tiene `disponible` >= 2 y es refrigerada | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| E2E-03 | analisis-auditoria | Paso 3: clasificar motivo es solo sugerencia (RN-11) | POST /analisis/clasificar-motivo con descripcion | 200; `requiere_confirmacion=true`; primera sugerencia `Producto danado`; `devoluciones` sin cambios | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| E2E-04 | devoluciones | Paso 4: el cliente registra la solicitud (RF-07, RN-02) | POST /devoluciones con `X-Correlation-ID` | 201; folio `DEV-AAAA-n` unico; fila `solicitada` en PostgreSQL; evento `devolucion_registrada` en Mongo; mismo correlation id en respuesta, evento y bitacora | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| E2E-05 | evidencias | Paso 5: comentario en XML y archivo PNG (RN-14) | POST /evidencias (XML), POST /evidencias multipart, GET /enlace, GET url firmada | 201 x2; filas en `evidencias`; metadatos en Mongo; descarga por enlace firmado con el mismo tamano | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| E2E-06 | devoluciones | Paso 6: el analista autoriza (RF-10, RF-29) | PATCH /devoluciones/{id}/resolucion `autorizar` | 200 `autorizada`; `fecha_autorizacion` no nula; notificacion `autorizacion`; bitacora | 1a corrida: Fallo: esperaba solo `autorizacion` y la fila trae ademas `autorizacion_logistica` (aviso al Coordinador, a proposito, sesion 01). Prueba desactualizada; corregida. Reconfirmado en la VM, 2a corrida (18:22 UTC, tras PR #8, E2E 100 de 100): pasa. | paso | `docs/pruebas/resultado_2026-10-21.md` |
| E2E-06b | devoluciones / web | Paso 6b (sesion 01): notificaciones por rol y campanita (RF-29, UC-25, RN-13) | Filas de `notificaciones` tras autorizar; web `GET /notificaciones/resumen` y `POST /notificaciones/{id}/leer` con sesion de cliente, coordinador y otro cliente | Destinatarios: el cliente dueno (`autorizacion`, url `/devoluciones/{id}`) y todos los coordinadores activos (`autorizacion_logistica`, url `/logistica/...`); nadie mas; contador de la campanita = filas propias sin leer; otro cliente 404 y no marca; el dueno recibe 302 al expediente y la fila queda leida con bitacora; el coordinador ve el aviso con enlace a logistica | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| E2E-07 | logistica / reembolsos-costos | Paso 7: programar, asignar, transito, completada, recepcion y costo | POST /recolecciones, PATCH asignacion, PATCH estado x2, PATCH invalido, POST /recepciones, POST /costos | 201/200/200/200; retroceso 409; devolucion `recibida`; costo `transporte` 120.50 en PostgreSQL | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| E2E-08 | inspecciones | Paso 8: inspeccion con cadena de frio, disposicion y etiqueta (RN-05..RN-07) | POST /inspecciones, POST /disposicion `inventario`, POST /inventario/{id}/etiqueta | 201 x3; documento en Mongo enlazado por `mongo_doc_id`; `apto=true`; devolucion `resuelta`; etiqueta `REC-...` | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| E2E-09 | reembolsos-costos | Paso 9: reembolso unico con lock de Redis (RN-03) | POST /reembolsos x2 y con el lock tomado | 201; notificacion `reembolso_aprobado` al cliente; segundo 409 `reembolso_duplicado`; con lock 409 `reembolso_en_proceso`; una sola fila; devolucion `cerrada` | 1a corrida: Fallo: 409 `monto_excedido` con `maximo` 227.17 al reembolsar exactamente 227.17 (Decimal contra float). Bug de producto H-11; corregido. Reconfirmado en la VM, 2a corrida (18:22 UTC, tras PR #8, E2E 100 de 100): pasa. | paso | `docs/pruebas/resultado_2026-10-21.md` |
| E2E-10 | analisis-auditoria | Paso 10: sincronizar, Pareto dos veces, alertas, eventos por correlation id | POST /sincronizar, GET /pareto x2, GET /alertas-fraude, GET /eventos?correlation_id= | 1a `cache=miss`, 2a `cache=hit`; clave `cache:causas:*` con TTL <= 600; el evento del paso 4 aparece | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| E2E-11 | auth | Paso 11: logout revoca el token en todos los servicios (RNF-08) | POST /auth/logout y GET en auth, devoluciones y ventas | 200; `jwt_revocado:<jti>` en Redis; sesion borrada; 401 `token_revocado` en los tres | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |

El paso 6b exige que la sesion 01 este en la rama y que el contenedor `app` (web)
responda en `WEB_URL` (por defecto `http://app:8000`); inicia sesion por el
formulario real del web, igual que un navegador.

Orden real frente al brief: la evidencia (paso 5) va antes de autorizar porque
`evidencias` solo deja al cliente adjuntar mientras la solicitud sigue en
`solicitada` o `en_revision`.

### E2E — seguridad y errores (`tests/e2e/test_02_seguridad_y_errores.py`, `test_99_rate_limit.py`)

| ID | Servicio | Objetivo | Entradas | Resultado esperado | Resultado obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|---|
| SEG-01 | los 8 servicios | Sin token -> 401 | GET protegido de cada servicio sin Authorization | 401 `no_autenticado` (8 casos) | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-02 | los 8 servicios | Token mal formado -> 401 | `Authorization: Bearer esto.no.es-un-jwt` | 401 `token_invalido` (8 casos) | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-03 | los 8 servicios | Token expirado -> 401 | JWT firmado con la llave real y `exp` pasado | 401 `token_expirado` (8 casos) | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-04 | los 8 servicios | Token con firma ajena -> 401 | JWT firmado con otra llave | 401 `token_invalido` (8 casos) | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-05 | los 8 servicios | Token revocado -> 401 (reusa el logout del E2E-11) | Token de la sesion efimera ya cerrada | 401 `token_revocado` (8 casos; se salta si E2E-11 no corrio) | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-06 | devoluciones | El refresh token no sirve como access | GET /devoluciones con refresh token | 401 `token_invalido` | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-07 | auth | Credenciales malas sin revelar si existe el correo (RNF-16) | POST /login con correo inexistente | 401 `credenciales_invalidas`; el correo no aparece en la respuesta | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-08 | los 8 servicios | Rol incorrecto -> 403 en un endpoint de cada servicio | auth DELETE sesiones, devoluciones PATCH resolucion, logistica POST, inspecciones POST, reembolsos POST, catalogos POST, evidencias POST (analista), analisis GET alertas | 403 `sin_permiso` con el rol en `detalles` (8 casos) | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-09 | devoluciones | Un cliente no ve la devolucion de otro (RN-13, RN-15) | GET /devoluciones/{id} con el token de otro cliente | 403 y fila `acceso_denegado` en bitacora | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-10 | varios | Parametros invalidos -> 400 | paginacion 0, cuerpo incompleto, destino invalido, monto negativo, busqueda de 101 caracteres, sin `devolucion_id`, dimension desconocida, descripcion corta, correo mal formado | 400 `validacion` (9 casos) | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-11 | logistica | Fecha pasada -> 400 (con devolucion autorizada) | POST /recolecciones `2020-01-01` | 400 `validacion` | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-12 | devoluciones | JSON malformado -> 400 y Content-Type no soportado -> 415 | cuerpo `{no es json` y `text/plain` | 400 `json_invalido`; 415 | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-13 | varios | Recurso inexistente -> 404 | id 99999999 en devoluciones, inspecciones, ventas, evidencias, costos y catalogos; asignacion de logistica | 404 `no_encontrado` (7 casos) | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-14 | devoluciones | El error trae el correlation id de la peticion (RNF-23) | GET inexistente con `X-Correlation-ID` | Header y `error.correlation_id` iguales al enviado | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-15 | devoluciones | Cantidad excedida -> 409 (RN-01) | POST con cantidad = disponible + 5 | 409 `cantidad_excedida` | 1a corrida: Fallo en cascada: 409 `sin_disponible` en lugar de `cantidad_excedida` (la suite agoto la linea de venta). Corregido en la suite. Reconfirmado en la VM, 2a corrida (18:22 UTC, tras PR #8, E2E 100 de 100): pasa. | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-16 | reembolsos-costos | Reembolso sin autorizar -> 409 (RN-04) | POST /reembolsos sobre devolucion `solicitada` | 409 `estado_no_permite`; sin fila en `reembolsos` | 1a corrida: Fallo en cascada: el registro previo respondio 409 `sin_disponible`. Corregido en la suite. Reconfirmado en la VM, 2a corrida (18:22 UTC, tras PR #8, E2E 100 de 100): pasa. | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-17 | devoluciones | Rechazar sin justificacion -> 400 (RN-12) | PATCH resolucion `rechazar` sin texto | 400 `validacion` | 1a corrida: Fallo en cascada: el registro previo respondio 409 `sin_disponible`. Corregido en la suite. Reconfirmado en la VM, 2a corrida (18:22 UTC, tras PR #8, E2E 100 de 100): pasa. | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-18 | logistica | Solo se programan devoluciones autorizadas -> 409 | POST /recolecciones sobre devolucion `solicitada` | 409 `estado_no_permite` | 1a corrida: Fallo en cascada: el registro previo respondio 409 `sin_disponible`. Corregido en la suite. Reconfirmado en la VM, 2a corrida (18:22 UTC, tras PR #8, E2E 100 de 100): pasa. | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-19 | inspecciones | Cadena de frio rota impide inventario -> 409 (RN-06, RN-07) | Inspeccion con cadena rota; disposicion `inventario`; despues `desecho`; segunda inspeccion | `apto=false`; 409 `no_apto_inventario`; `desecho` 201; reinspeccion 409 | 1a corrida: Fallo en cascada: el registro previo respondio 409 `sin_disponible`. Corregido en la suite. Reconfirmado en la VM, 2a corrida (18:22 UTC, tras PR #8, E2E 100 de 100): pasa. | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-20 | inspecciones | Refrigerado sin temperatura -> 400 (RN-05) | POST /inspecciones sin temperatura ni minutos | 400 `validacion` | 1a corrida: Fallo en cascada: el registro previo respondio 409 `sin_disponible`. Corregido en la suite. Reconfirmado en la VM, 2a corrida (18:22 UTC, tras PR #8, E2E 100 de 100): pasa. | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-21 | bitacora | La bitacora no guarda tokens (RNF-16) | Busqueda de `eyJ` y `bearer` en `bitacora.detalle` | Cero filas | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-22 | ventas-catalogos | Inyeccion SQL en la busqueda no hace dano (RNF-11) | GET /ventas?q=`'; DROP TABLE ventas;--` | 200, total 0 y la tabla `ventas` intacta | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| SEG-23 | auth | Rate limiting de login: 429 (RNF-13) | Maximo + 1 logins con correos distintos | Los primeros 401, el siguiente 429 con `Retry-After`; limpia las claves al terminar | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |

### E2E — JSON, XML y XSD (`tests/e2e/test_03_json_y_xml.py`)

| ID | Servicio | Objetivo | Entradas | Resultado esperado | Resultado obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|---|
| FMT-01 | auth | Login en XML y respuesta validada contra `tokens.xsd` y `sesion.xsd` | POST /login con `login.xsd`; GET /sesion `Accept: application/xml` | 200 XML; `shared/xsd.py` no reporta errores | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| FMT-02 | ventas-catalogos | El mismo listado en JSON y en XML coincide | GET /ventas con `Accept` JSON y XML | Ambos 200; mismo `paginacion/total` | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| FMT-03 | devoluciones | Error en XML con el formato comun | GET inexistente `Accept: application/xml` | 404 con raiz `error`, `tipo` y `correlation_id` iguales al header | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| FMT-04 | devoluciones / logistica / reembolsos-costos | Cuerpos XML conformes a su XSD en cuatro servicios | devolucion, resolucion, recoleccion, asignacion, estado, costo (validados contra su XSD antes de enviar) | 201/200 con respuesta XML bien formada | 1a corrida: Fallo en cascada: el registro de la devolucion por XML respondio 409 `sin_disponible`. Corregido en la suite. Reconfirmado en la VM, 2a corrida (18:22 UTC, tras PR #8, E2E 100 de 100): pasa. | paso | `docs/pruebas/resultado_2026-10-21.md` |
| FMT-05 | devoluciones | XML que no cumple el XSD -> 400 | devolucion sin `motivo_id` | 400 `xml_no_cumple_xsd` | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| FMT-06 | devoluciones | XML mal formado -> 400 | `<devolucion><x>` | 400 `xml_invalido` | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| FMT-07 | auth | XML con entidad externa no lee archivos (XXE) | `<!ENTITY x SYSTEM "file:///etc/passwd">` | 400 o 401 y sin `root:` en la respuesta | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |
| FMT-08 | suite | La suite no contiene la contrasena de demo (RNF-16) | Busqueda de `PASSWORD_DEMO` en `tests/e2e/*.py` | No aparece | Pasa en la VM (2026-10-21): tambien en la 2a corrida (100 de 100 E2E pasan); sin salida por caso en el repo | paso | `docs/pruebas/resultado_2026-10-21.md` |

### Integracion por servicio (`services/*/tests/test_integracion.py`)

| ID | Servicio | Objetivo | Entradas | Resultado esperado | Resultado obtenido | Estado | Evidencia |
|---|---|---|---|---|---|---|---|
| INT-AUTH-1 | auth | Login crea sesion en Redis, historial y bitacora sin guardar el token | login real; Redis `sesion_api`, `sesiones_usuario`; `intentos_acceso`; `bitacora` | TTL > 0; filas presentes; el token no esta en `bitacora` | Pasa en la VM (2026-10-21): bloque del servicio sin fallos | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-AUTH-2 | auth | Logout revoca el token y borra la sesion | POST /logout y GET /sesion | 200; clave `jwt_revocado`; sesion borrada; 401 `token_revocado` | Pasa en la VM (2026-10-21): bloque del servicio sin fallos | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-AUTH-3 | auth | Refresh emite un access de la misma sesion | POST /refresh con refresh y con access | 200 mismo `sid`; con access 401 | Pasa en la VM (2026-10-21): bloque del servicio sin fallos | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-AUTH-4 | auth | El administrador cierra todas las sesiones de un usuario (RNF-08) | DELETE /usuarios/{id}/sesiones; cliente intenta lo mismo | 200 `sesiones_cerradas` >= 1; token de la victima 401 `sesion_inactiva`; cliente 403 | Pasa en la VM (2026-10-21): bloque del servicio sin fallos | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-AUTH-5 | auth | Credenciales malas quedan en el historial; login valido reinicia intentos (RNF-12) | login con password incorrecta y luego correcta | 401; fila `NOT exitoso`; `intentos:<email>` borrada | Pasa en la VM (2026-10-21): bloque del servicio sin fallos | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-VEN-1 | ventas-catalogos | El cliente solo ve sus ventas | GET /ventas?por_pagina=100 | Total = ventas propias en PostgreSQL | Pasa en la VM (2026-10-21): bloque del servicio sin fallos | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-VEN-2 | ventas-catalogos | El cliente no abre la venta de otro | GET /ventas/{id ajeno} | 403 | Pasa en la VM (2026-10-21): bloque del servicio sin fallos | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-VEN-3 | ventas-catalogos | Alta, edicion y baja logica de catalogo | POST/PUT/DELETE /catalogos/motivos (admin) | 201; nombre cambia; `activo=false` (la fila sigue); bitacora | Pasa en la VM (2026-10-21): bloque del servicio sin fallos | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-VEN-4 | ventas-catalogos | Catalogo inexistente y roles sin permiso | GET /catalogos/no_existe; analista POST; cliente GET productos | 404; 403; 403 | Pasa en la VM (2026-10-21): bloque del servicio sin fallos | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-DEV-1..4 | devoluciones | Ya existente (`test_integracion.py` previo): flujo registro/revision/autorizacion, cancelacion logica, listado del cliente, logout revoca en devoluciones | Ver el archivo | Ver el archivo (4 casos) | Corrida 1a: 3 de 4 (test_1 no esperaba la notificacion `autorizacion_logistica` al Coordinador, agregada en la sesion 01). Corrida 1b: errores de login 401 al elegir como otro cliente una cuenta real (`prueba@gmail.com`) que no usa la contrasena demo. Corrida 2a: fallo porque la imagen aun traia la prueba vieja; la prueba se limito a cuentas `@demo.mx` (PR #9). Corrida 3a (tras PR #9 y reconstruir la imagen): 4 de 4 pasan. | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-EVI-1 | evidencias | Comentario JSON y archivo PNG: PostgreSQL, Mongo y enlace firmado (RN-14) | POST comentario, POST multipart, GET /enlace, GET url firmada | 201 x2; fila con mime y tamano; metadatos con `_id` = `metadatos_id`; descarga igual al PNG | Pasa en la VM (2026-10-21): bloque del servicio sin fallos | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-EVI-2 | evidencias | Archivo que no es imagen ni PDF se rechaza (RNF-10) | multipart `falso.png` con bytes de ejecutable | 415; sin fila | Pasa en la VM (2026-10-21): bloque del servicio sin fallos | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-EVI-3 | evidencias | Otro rol no adjunta | POST como analista | 403 | Pasa en la VM (2026-10-21): bloque del servicio sin fallos | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-EVI-4 | evidencias | Descarga sin firma ni token | GET /1/archivo sin credenciales | 401 | Pasa en la VM (2026-10-21): bloque del servicio sin fallos | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-LOG-1 | logistica | Programar, asignar, transitar, completar y recibir sobre PostgreSQL | API de logistica con devolucion sembrada `autorizada` | Estados y FK correctos; salto asignada->completada 409; devolucion `recibida`; bitacora | 1a corrida: no corrio (login 429, H-07). Reconfirmado en la VM (2026-10-21): pasa en la corrida completa con el script corregido (el bloque del servicio termina sin fallos). | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-LOG-2 | logistica | No se programa una devolucion sin autorizar | POST /recolecciones sobre `solicitada` | 409; sin fila en `recolecciones` | 1a corrida: no corrio (login 429, H-07). Reconfirmado en la VM (2026-10-21): pasa en la corrida completa con el script corregido (el bloque del servicio termina sin fallos). | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-LOG-3 | logistica | El cliente no puede programar | POST como cliente | 403 | 1a corrida: no corrio (login 429, H-07). Reconfirmado en la VM (2026-10-21): pasa en la corrida completa con el script corregido (el bloque del servicio termina sin fallos). | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-INS-1 | inspecciones | Inspeccion apta: Mongo + PostgreSQL + PATCH + disposicion + etiqueta | API con devolucion sembrada `recibida` | Documento en Mongo; `mongo_doc_id` enlaza; PATCH solo cambia Mongo; etiqueta en `inventario_recuperado` | 1a corrida: no corrio (login 429, H-07). Reconfirmado en la VM (2026-10-21): pasa en la corrida completa con el script corregido (el bloque del servicio termina sin fallos). | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-INS-2 | inspecciones | Cadena rota no vuelve a inventario (RN-06, RN-07) | Inspeccion con cadena rota y disposicion `inventario` | `apto=false`; 409 `no_apto_inventario`; sin disposicion | 1a corrida: no corrio (login 429, H-07). Reconfirmado en la VM (2026-10-21): pasa en la corrida completa con el script corregido (el bloque del servicio termina sin fallos). | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-INS-3 | inspecciones | Refrigerado exige temperatura y tiempo (RN-05) | POST sin esos campos | 400; sin documento en Mongo | 1a corrida: no corrio (login 429, H-07). Reconfirmado en la VM (2026-10-21): pasa en la corrida completa con el script corregido (el bloque del servicio termina sin fallos). | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-INS-4 | inspecciones | Solo se inspecciona lo recibido | POST sobre `autorizada` | 409 | 1a corrida: no corrio (login 429, H-07). Reconfirmado en la VM (2026-10-21): pasa en la corrida completa con el script corregido (el bloque del servicio termina sin fallos). | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-INS-5 | inspecciones | El cliente no inspecciona | POST como cliente | 403 | 1a corrida: no corrio (login 429, H-07). Reconfirmado en la VM (2026-10-21): pasa en la corrida completa con el script corregido (el bloque del servicio termina sin fallos). | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-REE-1 | reembolsos-costos | Un solo reembolso por devolucion (RN-03) | POST /reembolsos x2 sobre `resuelta` | 201 y cierre + notificacion; segundo 409; una fila | 1a corrida: no corrio (login 429, H-07). Reconfirmado en la VM (2026-10-21): pasa en la corrida completa con el script corregido (el bloque del servicio termina sin fallos). | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-REE-2 | reembolsos-costos | El lock de Redis bloquea la resolucion concurrente | Lock tomado manualmente y POST | 409 `reembolso_en_proceso`; no libera el lock ajeno; sin fila | 1a corrida: no corrio (login 429, H-07). Reconfirmado en la VM (2026-10-21): pasa en la corrida completa con el script corregido (el bloque del servicio termina sin fallos). | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-REE-3 | reembolsos-costos | No reembolsa sin autorizar ni mas del valor (RN-04) | POST sobre `solicitada` y con monto + 1000 | 409 `estado_no_permite`; 409 `monto_excedido` | 1a corrida: no corrio (login 429, H-07). Reconfirmado en la VM (2026-10-21): pasa en la corrida completa con el script corregido (el bloque del servicio termina sin fallos). | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-REE-4 | reembolsos-costos | Costos por etapa y por rol, y total (RF-27) | POST /costos como coordinador y analista; GET /costos/{id} | 201/403/201; total 120.5 igual a la suma en PostgreSQL | 1a corrida: no corrio (login 429, H-07). Reconfirmado en la VM (2026-10-21): pasa en la corrida completa con el script corregido (el bloque del servicio termina sin fallos). | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-REE-5 | reembolsos-costos | El cliente no reembolsa | POST como cliente | 403 | 1a corrida: no corrio (login 429, H-07). Reconfirmado en la VM (2026-10-21): pasa en la corrida completa con el script corregido (el bloque del servicio termina sin fallos). | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-ANA-1 | analisis-auditoria | Sincronizar proyecta PostgreSQL en Mongo sin modificar PostgreSQL | POST /sincronizar | Snapshots vigentes = devoluciones; conteo y max id de PostgreSQL intactos | 1a corrida: no corrio (login 429, H-07). Reconfirmado en la VM (2026-10-21): pasa en la corrida completa con el script corregido (el bloque del servicio termina sin fallos). | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-ANA-2 | analisis-auditoria | Pareto: miss, luego hit con TTL en Redis; resultado guardado en Mongo | POST /sincronizar; GET /pareto x2 | miss/hit; clave `cache:causas:*` con TTL <= 600; acumulado termina en 100 | 1a corrida: no corrio (login 429, H-07). Reconfirmado en la VM (2026-10-21): pasa en la corrida completa con el script corregido (el bloque del servicio termina sin fallos). | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-ANA-3 | analisis-auditoria | Clasificar motivo solo sugiere (RN-11) | POST /clasificar-motivo | `requiere_confirmacion=true`; `devoluciones` sin cambios | 1a corrida: no corrio (login 429, H-07). Reconfirmado en la VM (2026-10-21): pasa en la corrida completa con el script corregido (el bloque del servicio termina sin fallos). | paso | `docs/pruebas/resultado_2026-10-21.md` |
| INT-ANA-4 | analisis-auditoria | Auditoria y eventos solo para analista o admin | GET /auditoria y /analisis/eventos como cliente | Analista 200 con total = `bitacora`; cliente 403 | 1a corrida: no corrio (login 429, H-07). Reconfirmado en la VM (2026-10-21): pasa en la corrida completa con el script corregido (el bloque del servicio termina sin fallos). | paso | `docs/pruebas/resultado_2026-10-21.md` |

## Hallazgos

Observados al leer el codigo para escribir las pruebas; **no se corrigieron** (esta
sesion no toca servicios). Los que dependen de la ejecucion se confirman en la VM.

Estado de todos (salvo lo indicado abajo): **por confirmar en la VM** (se detectaron leyendo el codigo; ninguno se
ha reproducido contra los contenedores porque aqui no hay bases).

| ID | Servicio | Hallazgo | Severidad | Evidencia en codigo | Sugerencia |
|---|---|---|---|---|---|
| H-01 | evidencias | Las etapas `recoleccion` y `recepcion` son inalcanzables: el cliente solo puede adjuntar con `etapa=solicitud`, el inspector solo con `etapa=inspeccion` y los demas roles reciben 403, asi que nadie puede registrar evidencia en esas dos etapas aunque `ETAPAS` las acepta | Media (RF de evidencias por etapa incompleto) | `services/evidencias/app.py`: `crear()` y `contexto(lectura=False)` | Decidir que rol adjunta en recoleccion y recepcion (coordinador y encargado del centro) y abrirlo, o quitar las etapas |
| H-02 | todos menos auth | Solo `auth` publica XSD de **respuesta** (`tokens.xsd`, `sesion.xsd`); los otros siete servicios solo tienen XSD de peticion, por lo que sus respuestas XML no se pueden validar contra un esquema como pedia el brief | Media (cobertura de seccion 6) | `services/*/contratos/` | Definir XSD de respuesta de los endpoints mas usados, o documentar que el contrato XML es solo de entrada. La suite hoy valida la peticion contra su XSD antes de enviarla y comprueba que la respuesta sea XML bien formado con la raiz esperada |
| H-03 | evidencias | El cliente solo puede adjuntar mientras la devolucion este `solicitada` o `en_revision`; el brief ordenaba adjuntar despues de autorizar. Parece intencional, pero obligo a mover la evidencia antes de la autorizacion en el E2E | Baja (diseno) | `services/evidencias/app.py:crear` | Confirmar que es la regla querida y reflejarla en el documento |
| H-04 | logistica | `POST /recolecciones` valida la devolucion (404/409) antes de validar fecha y lugar: una fecha pasada sobre una devolucion no autorizada responde 409 en lugar de 400 | Baja (orden de validacion) | `services/logistica/app.py:programar` | Validar el cuerpo antes de consultar la devolucion |
| H-05 | inspecciones | `POST /inventario/{id}/etiqueta` responde 201 tambien al repetir (usa `ON CONFLICT DO UPDATE`): es idempotente pero no distingue creacion de repeticion | Baja | `services/inspecciones/app.py:etiquetar` | Responder 200 cuando la etiqueta ya existia |
| H-06 | reembolsos-costos | RN-04 solo exige que la devolucion no este `solicitada`, `en_revision` ni `rechazada`; permite aprobar un reembolso estando `en_recoleccion` o `recibida`, antes de recibir el producto. Y solo cierra la devolucion si estaba `resuelta`; en cualquier otro estado queda abierta con reembolso | Baja (a confirmar con el negocio) | `services/reembolsos_costos/app.py:registrar_reembolso` | Confirmar si el reembolso puede anticiparse a la recepcion y que estado debe quedar |
| H-07 | auth | El rate limit de login (10 por minuto) es por IP y cuenta tambien los intentos validos: con varios usuarios detras de la misma IP (red del compose, NAT de la universidad) se llega al 429 rapido. La suite lo evita borrando las claves `devoluciones:limite:*:login`. **Confirmado en la VM (2026-10-21)**: tras `test_99` (429 a proposito), logistica, inspecciones, reembolsos y analisis no pudieron iniciar sesion. `scripts/correr_e2e.sh` ahora borra las claves `devoluciones:limite:*:login` antes de cada bloque; el limite en `auth` no se toco | Baja (operativa) | `services/auth/app.py:login`, `shared/infra.py:limitar` | Considerar un limite mayor por IP o contar solo los fallos |
| H-08 | contratos | Los XSD de devoluciones usan `xs:all` (cualquier orden) y los de logistica, reembolsos, inspecciones y evidencias usan `xs:sequence` (orden fijo): un cliente que envie los mismos elementos en otro orden recibe 400 solo en unos servicios | Baja (consistencia) | `services/*/contratos/*.xsd` | Unificar a `xs:all` o documentar el orden en cada `openapi.yaml` |
| H-09 | brief | El brief decia 84 unitarias; tras fusionar la sesion 01 el conteo real es **119** (`pytest` por servicio y web) | Informativa | Tabla de unitarias | Actualizar el brief |
| H-10 | logistica, inspecciones, reembolsos-costos | Por la API distribuida solo `devoluciones` (cliente y coordinador al autorizar) y `reembolsos-costos` (cliente, sin `url`) escriben notificaciones. Recoleccion programada, en transito, completada, recepcion, inspeccion, disposicion y cierre solo notifican si el paso se hace desde el web (`apps/web/app/notificaciones.py`). Quien opere solo por API no genera avisos a inspector, analista, encargado del centro ni al cliente en esos pasos, y los reembolsos por API no avisan al analista ni cierran con `caso_cerrado` | Media (RF-29 incompleto en la ruta API) | `services/logistica/app.py`, `services/inspecciones/app.py`, `services/reembolsos_costos/app.py` frente a `EVENTOS` | Insertar las mismas notificaciones desde cada microservicio (con `url`), o documentar que la campanita solo cubre el flujo por web. El E2E 6b verifica lo que hoy si existe |
| H-11 | reembolsos-costos | Un reembolso por el monto maximo exacto se rechazaba con 409 `monto_excedido` (y `detalles.maximo` igual al monto enviado): `registrar_reembolso` comparaba un `Decimal` cuantizado contra `float(valor_devuelto)`, y `Decimal("227.17") > float(227.17)` es verdadero. Hallado por E2E-09 en la VM el 2026-10-21 | Media (rechaza una operacion valida, RN-04) | `services/reembolsos_costos/app.py:registrar_reembolso` | **Corregido** (compara Decimal con Decimal) con dos pruebas unitarias; **reconfirmado en la VM (2026-10-21)**: E2E-09 aprueba el reembolso de 227.17 con 201 y INT-REE-1 pasa |
