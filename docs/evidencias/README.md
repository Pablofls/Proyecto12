# Guia de captura de evidencias en la VM

Cubre el apartado 5 del enunciado (evidencias request/response, 15%) y los
puntos de MongoDB y Redis. Todo lo de este archivo **se ejecuta en la VM de GCP**
(o desde una laptop apuntando a la VM); nadie levanta bases en su laptop
(CLAUDE.md, restriccion 1).

Hasta que alguien haga estos pasos, `docs/EVIDENCIAS.md` conserva los marcadores
`<!-- CAPTURA PENDIENTE: id -->`. **No se pega ninguna respuesta que no se haya
ejecutado de verdad.**

## 0. Antes de empezar

1. Rama con este material en la VM (despues de integrada a `main`, `git pull`):
   ```bash
   cd ~/Proyecto12 && git pull && docker compose ps
   ```
   Los 12 contenedores (postgres, redis, mongo, app y los 8 servicios) deben estar `healthy`.
2. Datos de demostracion cargados (`scripts/seed_demo.py`, ver `docs/SETUP.md`).
3. Instala Newman en la maquina desde donde correras las colecciones:
   ```bash
   npm install -g newman
   ```
4. Las contrasenas **no estan en el repositorio**. Pide `PASSWORD_DEMO` al equipo y exportala solo en tu terminal:
   ```bash
   read -rs PASSWORD_DEMO && export PASSWORD_DEMO
   export VM_HOST=<IP-DE-LA-VM>
   ```
5. Las capturas muestran peticiones con `Authorization: Bearer ...`. **Tapa o recorta el token** antes de guardar
   la imagen (dura 15 minutos, pero igual no debe quedar en git). Nunca captures `password_demo`.
6. Guarda las imagenes en `docs/evidencias/capturas/` con el nombre `NNN_servicio_metodo_endpoint_codigo[_xml].png`.
   La lista completa (240 nombres) esta en [CHECKLIST_CAPTURAS.md](CHECKLIST_CAPTURAS.md); es la misma numeracion que
   los marcadores de `docs/EVIDENCIAS.md`. Ejemplo: `061_logistica_post_recolecciones_201.png`.

## 1. Colecciones Postman (request/response) - capturas 001 a 240

Importa en Postman `docs/postman/vm.postman_environment.json` y las 8 colecciones `docs/postman/*.postman_collection.json`.
En el environment llena `vm_host` y `password_demo` (Current value; no se versiona).

**Orden de corrida** (reproduce el proceso completo de una devolucion; cada coleccion deja ids en el environment
para la siguiente):

| Orden | Coleccion | Deja para las demas |
|---|---|---|
| 1 | `auth` | (los tokens de las demas se obtienen en su propia carpeta `00`) |
| 2 | `ventas_catalogos` | `ruta_id`, `transportista_id`, `venta_id` |
| 3 | `devoluciones` | `devolucion_id` (autorizada) |
| 4 | `logistica` | devolucion en `recibida` |
| 5 | `inspecciones` | devolucion `resuelta`, `disposicion_id` |
| 6 | `evidencias` | (crea y cancela su propia devolucion; usa `devolucion_id` solo en la carpeta 04) |
| 7 | `reembolsos_costos` | devolucion `cerrada` |
| 8 | `analisis_auditoria` | - |

Reglas practicas:
- Los logins estan limitados a **10 por minuto por IP** (RNF-13). Entre colecciones espera ~60 s o corre una sola a la vez.
- `auth`, carpeta `06`, **bloquea la cuenta de Sofia 15 min** y agota el limite de login: correla al final y aparte.
  Para desbloquear antes: `docker compose exec redis redis-cli DEL devoluciones:bloqueo:sofia.cliente@demo.mx devoluciones:intentos:sofia.cliente@demo.mx`
  y `UPDATE usuarios SET bloqueado_hasta = NULL WHERE email = 'sofia.cliente@demo.mx';`.
- `devoluciones` consume una unidad de la linea de venta `72` (3 unidades). Si responde `409 sin_disponible`, cambia
  `venta_detalle_id` en el environment por otra compra de Miguel (ver `GET /api/v1/ventas/{id}`, campo `disponible`).
- En `evidencias`, las peticiones multipart piden elegir el archivo una vez: `docs/postman/fixtures/evidencia_prueba.png`
  y `docs/postman/fixtures/no_es_imagen.txt`.
- Si una peticion falla por datos (no por el codigo), corrige el dato y repite: lo que se captura es la ejecucion que
  cumple las verificaciones (pestana Test Results en verde).

Captura por peticion: pantalla de Postman con **URL, headers, body, respuesta, codigo y Test Results**. Nombra con el id
del checklist.

Corrida completa por consola (verificaciones sin capturas, util para dejar un reporte):

```bash
mkdir -p ~/evidencias_vm && cd ~/Proyecto12
for c in auth ventas_catalogos devoluciones logistica inspecciones evidencias reembolsos_costos analisis_auditoria; do
  newman run docs/postman/$c.postman_collection.json \
    -e docs/postman/vm.postman_environment.json \
    --working-dir docs/postman \
    --env-var vm_host=$VM_HOST --env-var password_demo=$PASSWORD_DEMO \
    --export-environment ~/evidencias_vm/entorno_$c.json \
    -r cli,json --reporter-json-export ~/evidencias_vm/$c.json
  sleep 60
done
```
`auth` incluye la carpeta `06` (bloqueo y limite): si no la quieres, ejecuta `auth` con `--folder` para cada carpeta de 00 a 05.
`--export-environment` guarda tokens e ids: **no lo subas a git** (esta fuera del repo, en `~/evidencias_vm`).
Captura la salida final de cada corrida (`cli`) con el nombre `newman_<coleccion>.png`.

## 2. Swagger `/docs` de cada servicio con Bearer real

Para cada servicio abre `http://<IP-DE-LA-VM>:<puerto>/docs` (8001 auth, 8002 devoluciones, 8003 logistica, 8004 inspecciones,
8005 reembolsos_costos, 8006 ventas_catalogos, 8007 evidencias, 8008 analisis_auditoria).

1. Obtén un token: `curl -s -X POST http://<IP>:8001/api/v1/auth/login -H 'Content-Type: application/json' -d '{"email":"josue.analista@demo.mx","password":"'"$PASSWORD_DEMO"'"}'` y copia `access_token`.
2. En Swagger: **Authorize** -> pega el token (sin la palabra Bearer) -> Authorize.
3. Ejecuta con **Try it out** al menos un `GET` exitoso y un error (por ejemplo `404` con un id inexistente) del servicio.
4. Captura la lista de endpoints del servicio y la respuesta de la ejecucion. Nombres: `swagger_<servicio>_endpoints.png` y `swagger_<servicio>_try.png`.

## 3. PostgreSQL (`psql`): filas tocadas por el proceso completo

Despues de correr las colecciones 3 a 7. Entra al cliente:
```bash
cd ~/Proyecto12 && docker compose exec postgres psql -U devoluciones_app -d devoluciones
```
Ejecuta y captura cada consulta (`pg_NN_<tabla>.png`); sustituye `<ID>` por el `devolucion_id` del environment:

```sql
-- pg_01 devolucion y su avance
SELECT id, folio_devolucion, estado, cantidad_devuelta, fecha_solicitud, fecha_cierre FROM devoluciones WHERE id = <ID>;
-- pg_02 recoleccion y recepcion
SELECT id, devolucion_id, estado, fecha_programada, lugar, ruta_id, transportista_id FROM recolecciones WHERE devolucion_id = <ID>;
SELECT id, devolucion_id, coincide_expediente, fecha_recepcion FROM recepciones WHERE devolucion_id = <ID>;
-- pg_03 inspeccion (la referencia; el detalle esta en MongoDB) y disposicion
SELECT id, devolucion_id, resultado_general, apto_para_inventario, mongo_doc_id FROM inspecciones_ref WHERE devolucion_id = <ID>;
SELECT id, devolucion_id, destino, justificacion FROM disposiciones WHERE devolucion_id = <ID>;
SELECT id, disposicion_id, etiqueta_codigo FROM inventario_recuperado ORDER BY id DESC LIMIT 3;
-- pg_04 reembolso y costos
SELECT id, devolucion_id, monto, metodo, estado, fecha_resolucion FROM reembolsos WHERE devolucion_id = <ID>;
SELECT etapa, SUM(monto) AS subtotal FROM costos WHERE devolucion_id = <ID> GROUP BY etapa ORDER BY etapa;
SELECT * FROM vista_costo_devolucion WHERE devolucion_id = <ID>;
-- pg_05 evidencias (de la devolucion de la coleccion evidencias: usa devolucion_ev_id)
SELECT id, devolucion_id, tipo, etapa, nombre_original, mime_type, tamano_bytes, eliminado_en FROM evidencias ORDER BY id DESC LIMIT 6;
-- pg_06 bitacora del proceso (RF-30, RN-12)
SELECT fecha, accion, entidad, entidad_id, detalle, correlation_id FROM bitacora WHERE entidad = 'devoluciones' AND entidad_id = <ID> ORDER BY fecha;
-- pg_07 notificaciones generadas (RF-29)
SELECT usuario_id, tipo, mensaje, url, fecha_creacion FROM notificaciones WHERE devolucion_id = <ID> ORDER BY id;
-- pg_08 intentos de acceso y bloqueo (RNF-12)
SELECT email, exitoso, ip_origen, fecha FROM intentos_acceso ORDER BY id DESC LIMIT 10;
SELECT email, bloqueado_hasta FROM usuarios WHERE email = 'sofia.cliente@demo.mx';
```
Si una consulta marca "column does not exist", corrige el nombre contra `db/migrations/` y deja la correccion en esta guia.

## 4. MongoDB (`mongosh`)

Colecciones e indices reales de `db/mongo/init.js`: `inspecciones` (`idx_devolucion`, y `uq_inspeccion_devolucion` que crea el servicio),
`evidencias_metadatos` (`idx_devolucion`), `eventos` (`idx_correlation`, `idx_fecha`), `resultados_analisis` (`idx_tipo_fecha`,
`idx_snapshot_devolucion_unico`). Entra:
```bash
cd ~/Proyecto12 && docker compose exec mongo sh -c 'mongosh -u "$MONGO_APP_USER" -p "$MONGO_APP_PASSWORD" --authenticationDatabase "$MONGO_DB" "$MONGO_DB"'
```
Captura cada bloque (`mongo_NN_<operacion>.png`). Usa un `devolucion_id` real del proceso:

```js
// mongo_01 insercion: la hizo el servicio al registrar la inspeccion (POST /inspecciones). Se demuestra el documento:
db.inspecciones.findOne({ devolucion_id: <ID> })
// insercion directa de un evento de prueba (queda marcado como prueba)
db.eventos.insertOne({ servicio: "evidencias_vm", tipo: "captura_manual", datos: { nota: "prueba de insercion" }, correlation_id: "captura-vm-01", fecha: new Date() })

// mongo_02 consulta
db.eventos.find({ servicio: "devoluciones" }, { datos: 0 }).sort({ fecha: -1 }).limit(5)
db.evidencias_metadatos.find({ devolucion_id: <ID_EV> }).pretty()

// mongo_03 actualizacion (el PATCH /inspecciones/{id} hace esto; aqui se ve el resultado y se repite a mano)
db.inspecciones.updateOne({ devolucion_id: <ID> }, { $set: { observaciones: "actualizacion manual para captura" } })
db.inspecciones.findOne({ devolucion_id: <ID> }, { observaciones: 1, "condiciones.estado_empaque": 1 })

// mongo_04 filtro
db.inspecciones.find({ "resultado.apto_para_inventario": true }, { devolucion_id: 1, "condiciones.estado_empaque": 1 })
db.eventos.find({ correlation_id: "captura-vm-01" })

// mongo_05 agregacion con pipeline (es la del Pareto de GET /analisis/pareto)
db.resultados_analisis.aggregate([
  { $match: { tipo_analisis: "snapshot_devolucion", vigente: true } },
  { $group: { _id: "$motivo", total: { $sum: 1 }, casos: { $sum: 1 } } },
  { $sort: { total: -1, _id: 1 } }
])

// mongo_06 indices
db.inspecciones.getIndexes()
db.evidencias_metadatos.getIndexes()
db.eventos.getIndexes()
db.resultados_analisis.getIndexes()

// mongo_07 explain: la consulta usa el indice (busca IXSCAN, no COLLSCAN)
db.eventos.find({ correlation_id: "captura-vm-01" }).explain("executionStats")
db.inspecciones.find({ devolucion_id: <ID> }).explain("executionStats")
db.resultados_analisis.find({ tipo_analisis: "snapshot_devolucion" }).explain("executionStats")

// mongo_08 limpieza del evento de prueba
db.eventos.deleteMany({ correlation_id: "captura-vm-01" })
```
Para `explain` captura `winningPlan.stage`, `totalDocsExamined` y `totalKeysExamined`. Si sale `COLLSCAN` en alguna, anotalo en
`docs/EVIDENCIAS.md`: es un hallazgo, no se oculta. El `.explain` de `resultados_analisis` por `tipo_analisis` usa el indice compuesto
`idx_tipo_fecha` solo si el filtro incluye el prefijo `tipo_analisis`.

## 5. Redis (`redis-cli`)

Patrones y TTL reales: `docs/diagramas/redis_claves.md`. Entra:
```bash
cd ~/Proyecto12 && docker compose exec redis redis-cli
```
Captura cada bloque (`redis_NN_<tema>.png`). Redis 7 de este proyecto no tiene contrasena (`docker-compose.yml`).

```text
# redis_01 sesion (despues de un login, antes de cerrar sesion)
SCAN 0 MATCH devoluciones:sesion_api:* COUNT 100
HGETALL devoluciones:sesion_api:<sid>
TTL devoluciones:sesion_api:<sid>            # cerca de 28800 (8 h)
SMEMBERS devoluciones:sesiones_usuario:<usuario_id>

# redis_02 blacklist tras logout (haz POST /auth/logout con ese token y vuelve a mirar)
SCAN 0 MATCH devoluciones:jwt_revocado:* COUNT 100
GET devoluciones:jwt_revocado:<jti>          # "1"
TTL devoluciones:jwt_revocado:<jti>          # vida restante del token (<= 900)
EXISTS devoluciones:sesion_api:<sid>         # 0

# redis_03 rate limit (despues de varios logins seguidos)
SCAN 0 MATCH devoluciones:limite:* COUNT 100
GET devoluciones:limite:<ip>:login
TTL devoluciones:limite:<ip>:login           # <= 60

# redis_04 intentos y bloqueo (despues de la carpeta 06 de auth)
GET devoluciones:intentos:sofia.cliente@demo.mx
GET devoluciones:bloqueo:sofia.cliente@demo.mx
TTL devoluciones:bloqueo:sofia.cliente@demo.mx   # <= 900

# redis_05 cache de Pareto (despues de correr analisis_auditoria)
SCAN 0 MATCH devoluciones:cache:causas:* COUNT 100
GET devoluciones:cache:causas:<hash>
TTL devoluciones:cache:causas:<hash>         # <= 600
GET devoluciones:analisis:version

# redis_06 lock de reembolso. Con el lock puesto, el POST /reembolsos debe responder 409 reembolso_en_proceso:
SET devoluciones:lock:reembolso:<ID_OTRA_DEVOLUCION> x NX EX 30
TTL devoluciones:lock:reembolso:<ID_OTRA_DEVOLUCION>
#   (en los 30 s siguientes: POST /api/v1/reembolsos-costos/reembolsos con ese devolucion_id -> 409; captura peticion y respuesta)
```
Para el lock usa una devolucion **distinta** de la ya reembolsada, para que la prueba apunte al candado y no a `reembolso_duplicado`.

## 6. Contenedores, recursos y volumenes

```bash
docker compose ps                         # captura: docker_01_ps.png   (todos healthy)
docker stats --no-stream                  # captura: docker_02_stats.png
docker volume ls                          # captura: docker_03_volumes.png (postgres_data, redis_data, mongo_data, evidencias_data)
docker compose logs --tail=20 devoluciones # captura opcional: se ve el X-Correlation-ID (RNF-23)
```

## 7. Archivo guardado en el volumen privado de evidencias

Despues de la peticion `alta 201 archivo PNG` de la coleccion `evidencias`:
```bash
cd ~/Proyecto12 && docker compose exec evidencias sh -c 'ls -l /srv/evidencias_privadas && stat -c "%a %n" /srv/evidencias_privadas/*'
docker volume inspect proyecto12_evidencias_data   # el nombre exacto sale de `docker volume ls`
```
Captura: `evidencias_01_volumen.png`. Debe verse el archivo con **nombre aleatorio de 32 hex** y permisos `600`, y que el
directorio **no se sirve por HTTP** (`curl -i http://<IP>:8007/uploads/` responde 404). Captura tambien ese `curl` como
`evidencias_02_sin_ruta_publica.png`.

## 8. Al terminar

1. Revisa que ninguna imagen muestre un token completo ni `password_demo`.
2. Reemplaza en `docs/EVIDENCIAS.md` cada `<!-- CAPTURA PENDIENTE: id -->` por la imagen (`![id](evidencias/capturas/id.png)`)
   y pega debajo la respuesta real. **El archivo esta generado por `docs/postman/generar_colecciones.py`**: si lo regeneras
   se pierden esas ediciones. Convencion: edita `EVIDENCIAS.md` a mano solo despues del ultimo regenerado y no vuelvas a correr el
   generador sin avisar al equipo.
3. Marca `[x]` en `CHECKLIST_CAPTURAS.md` y commitea las imagenes en tu rama (`pablo/...`, `roberto/...`, etc.) con mensaje
   `docs(evidencias): capturas de <servicio> (RNF-05, RF-31)`.

## Volcar la corrida de Newman a la evidencia (sin capturas a mano)

Despues de correr cada coleccion con Newman y `--reporter-json-export ~/evidencias_vm/<coleccion>.json`
(ver la seccion 1), desde la raiz del repo:

```bash
python3 docs/postman/volcar_ejecuciones.py ~/evidencias_vm
```

Genera `docs/evidencias/ejecuciones/<coleccion>.md` con cada peticion y su respuesta real (metodo, URL,
headers, body, codigo, cuerpo, tiempo y verificaciones), con los JWT, el campo `password` y la IP de la VM
ocultos, y reemplaza en `docs/EVIDENCIAS.md` y en el checklist los marcadores de los casos ejecutados por un
enlace a su transcripcion. Es repetible; si regeneras `EVIDENCIAS.md` con `generar_colecciones.py`, vuelve a
correr este script. No sube los JSON de Newman ni los environments exportados (llevan tokens): se quedan en
`~/evidencias_vm`.

La carpeta `06` de auth (bloqueo 423 y limite 429) no se corre en la primera pasada y sus dos casos siguen como
`CAPTURA PENDIENTE`.

