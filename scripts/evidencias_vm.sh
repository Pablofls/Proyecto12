#!/usr/bin/env bash
# Captura EN LA VM la evidencia de Docker, PostgreSQL, MongoDB y Redis como
# transcripciones de texto con la salida real de cada comando (apartados 7, 8 y
# 11 del enunciado). Escribe en docs/evidencias/bases/ para versionarlas.
#
#   bash scripts/evidencias_vm.sh
#
# Requiere el entorno levantado, haber corrido antes las colecciones de Newman
# (para que haya una devolucion con inspeccion, reembolso y evidencias) y
# PASSWORD_DEMO en el .env (solo se usa para el login del caso del candado de
# Redis; no se imprime). Los JWT que pudieran aparecer se ocultan al final.
#
# Por que texto y no solo imagenes: la transcripcion sale de la ejecucion y es
# repetible. Las capturas de pantalla de estas mismas salidas siguen siendo
# opcionales (docs/evidencias/README.md).
#
# Trazabilidad: RNF-06, RNF-12, RNF-13, RNF-22, RNF-27, RF-30.
set -uo pipefail
cd "$(dirname "$0")/.."

SAL="docs/evidencias/bases"
mkdir -p "$SAL"
FECHA="$(date -u '+%Y-%m-%d %H:%M UTC')"
PG='docker compose exec -T postgres psql -U devoluciones_app -d devoluciones -P pager=off'

cabecera() { printf '# %s\n\nCapturado en la VM el %s con scripts/evidencias_vm.sh. Salida real, sin editar.\n' "$1" "$FECHA"; }
pg()  { printf '\n>>> %s\n' "$1"; $PG -c "$1" 2>&1; }
mg()  { printf '\n>>> %s\n' "$1"
        docker compose exec -T mongo sh -c \
          'mongosh --quiet -u "$MONGO_APP_USER" -p "$MONGO_APP_PASSWORD" --authenticationDatabase "$MONGO_DB" "$MONGO_DB" --eval "$0"' "$1" 2>&1; }
rc()  { printf '\n>>> redis-cli %s\n' "$*"; docker compose exec -T redis redis-cli "$@" 2>&1; }
una() { $PG -tA -c "$1" 2>/dev/null | head -1; }   # un valor de PostgreSQL

# Devolucion del proceso completo (la ultima con reembolso) y la de evidencias.
ID="$(una "SELECT devolucion_id FROM reembolsos ORDER BY id DESC LIMIT 1")"
ID_EV="$(una "SELECT devolucion_id FROM evidencias ORDER BY id DESC LIMIT 1")"
echo "devolucion del proceso: ${ID:-?}   devolucion con evidencias: ${ID_EV:-?}"
[ -n "$ID" ] || { echo "No hay reembolsos: corre antes las colecciones de Newman."; exit 1; }

# ------------------------------------------------------------------ Docker
{
  cabecera "Docker: contenedores, recursos y volumenes"
  printf '\n>>> docker compose ps\n';           docker compose ps 2>&1
  printf '\n>>> docker stats --no-stream\n';    docker stats --no-stream 2>&1
  printf '\n>>> docker volume ls\n';             docker volume ls 2>&1
  printf '\n>>> health de los servicios (desde la VM)\n'
  for p in 8000 8001 8002 8003 8004 8005 8006 8007 8008; do
    printf '%s: ' "$p"; curl -s -m 5 -o /dev/null -w '%{http_code}\n' "http://localhost:$p/health"
  done
  printf '\n>>> docker compose logs --tail=15 devoluciones (se ve el X-Correlation-ID)\n'
  docker compose logs --tail=15 devoluciones 2>&1
} > "$SAL/docker.txt"

# ------------------------------------------------------------- PostgreSQL
{
  cabecera "PostgreSQL: filas del proceso completo (devolucion $ID)"
  pg "SELECT id, folio_devolucion, estado, cantidad_devuelta, fecha_solicitud, fecha_cierre FROM devoluciones WHERE id = $ID"
  pg "SELECT id, devolucion_id, estado, fecha_programada, lugar, ruta_id, transportista_id FROM recolecciones WHERE devolucion_id = $ID"
  pg "SELECT id, devolucion_id, coincide_expediente, fecha_recepcion FROM recepciones WHERE devolucion_id = $ID"
  pg "SELECT id, devolucion_id, resultado_general, apto_para_inventario, mongo_doc_id FROM inspecciones_ref WHERE devolucion_id = $ID"
  pg "SELECT id, devolucion_id, destino, justificacion FROM disposiciones WHERE devolucion_id = $ID"
  pg "SELECT id, disposicion_id, etiqueta_codigo FROM inventario_recuperado ORDER BY id DESC LIMIT 3"
  pg "SELECT id, devolucion_id, monto, metodo, estado, fecha_resolucion FROM reembolsos WHERE devolucion_id = $ID"
  pg "SELECT etapa, SUM(monto) AS subtotal FROM costos WHERE devolucion_id = $ID GROUP BY etapa ORDER BY etapa"
  pg "SELECT * FROM vista_costo_devolucion WHERE devolucion_id = $ID"
  pg "SELECT id, devolucion_id, tipo, etapa, nombre_original, mime_type, tamano_bytes, eliminado_en FROM evidencias ORDER BY id DESC LIMIT 6"
  pg "SELECT fecha, accion, entidad, entidad_id, detalle, correlation_id FROM bitacora WHERE entidad = 'devoluciones' AND entidad_id = $ID ORDER BY fecha"
  pg "SELECT usuario_id, tipo, mensaje, url, fecha_creacion FROM notificaciones WHERE devolucion_id = $ID ORDER BY id"
  pg "SELECT email, exitoso, ip_origen, fecha FROM intentos_acceso ORDER BY id DESC LIMIT 10"
  pg "SELECT version FROM schema_migrations ORDER BY 1 DESC LIMIT 3"
} > "$SAL/postgresql.txt"

# ---------------------------------------------------------------- MongoDB
{
  cabecera "MongoDB: insercion, consulta, actualizacion, filtro, agregacion, indices y explain"
  mg "printjson(db.getCollectionNames())"
  mg "printjson(db.eventos.insertOne({ servicio: 'evidencias_vm', tipo: 'captura_manual', datos: { nota: 'prueba de insercion' }, correlation_id: 'captura-vm-01', fecha: new Date() }))"
  mg "printjson(db.inspecciones.findOne({ devolucion_id: $ID }))"
  mg "printjson(db.eventos.find({ servicio: 'devoluciones' }, { datos: 0 }).sort({ fecha: -1 }).limit(5).toArray())"
  mg "printjson(db.evidencias_metadatos.find({ devolucion_id: ${ID_EV:-0} }).toArray())"
  mg "printjson(db.inspecciones.updateOne({ devolucion_id: $ID }, { \$set: { observaciones: 'actualizacion manual para captura' } }))"
  mg "printjson(db.inspecciones.findOne({ devolucion_id: $ID }, { observaciones: 1 }))"
  mg "printjson(db.inspecciones.find({ 'resultado.apto_para_inventario': true }, { devolucion_id: 1 }).limit(5).toArray())"
  mg "printjson(db.eventos.find({ correlation_id: 'captura-vm-01' }).toArray())"
  mg "printjson(db.resultados_analisis.aggregate([{ \$match: { tipo_analisis: 'snapshot_devolucion', vigente: true } }, { \$group: { _id: '\$motivo', total: { \$sum: 1 } } }, { \$sort: { total: -1, _id: 1 } }]).toArray())"
  for col in inspecciones evidencias_metadatos eventos resultados_analisis; do
    mg "printjson(db.$col.getIndexes())"
  done
  mg "var e = db.eventos.find({ correlation_id: 'captura-vm-01' }).explain('executionStats'); printjson({ plan: e.queryPlanner.winningPlan, docsExaminados: e.executionStats.totalDocsExamined, clavesExaminadas: e.executionStats.totalKeysExamined })"
  mg "var e = db.inspecciones.find({ devolucion_id: $ID }).explain('executionStats'); printjson({ plan: e.queryPlanner.winningPlan, docsExaminados: e.executionStats.totalDocsExamined, clavesExaminadas: e.executionStats.totalKeysExamined })"
  mg "var e = db.resultados_analisis.find({ tipo_analisis: 'snapshot_devolucion' }).explain('executionStats'); printjson({ plan: e.queryPlanner.winningPlan, docsExaminados: e.executionStats.totalDocsExamined, clavesExaminadas: e.executionStats.totalKeysExamined })"
  mg "printjson(db.eventos.deleteMany({ correlation_id: 'captura-vm-01' }))"
} > "$SAL/mongodb.txt"

# ------------------------------------------------------------------ Redis
primera() { docker compose exec -T redis redis-cli --scan --pattern "$1" 2>/dev/null | head -1 | tr -d '\r'; }
{
  cabecera "Redis: sesiones, lista negra, limite de login, cache y candado"
  rc PING
  rc --scan --pattern 'devoluciones:*'
  S="$(primera 'devoluciones:sesion_api:*')"
  if [ -n "$S" ]; then rc HGETALL "$S"; rc TTL "$S"; else echo "(no hay sesiones activas ahora mismo)"; fi
  J="$(primera 'devoluciones:jwt_revocado:*')"
  if [ -n "$J" ]; then rc GET "$J"; rc TTL "$J"; else echo "(no hay tokens revocados vigentes: duran 15 min)"; fi
  L="$(primera 'devoluciones:limite:*')"
  if [ -n "$L" ]; then rc GET "$L"; rc TTL "$L"; else echo "(no hay contador de limite vigente: dura 60 s)"; fi
  C="$(primera 'devoluciones:cache:causas:*')"
  if [ -n "$C" ]; then rc TTL "$C"; else echo "(no hay cache del Pareto vigente: dura 10 min)"; fi
  rc GET devoluciones:analisis:version
  # Candado de reembolso: con el lock puesto, el POST responde 409 reembolso_en_proceso
  # (el candado se revisa antes de buscar la devolucion).
  rc SET devoluciones:lock:reembolso:999999 x NX EX 30
  rc TTL devoluciones:lock:reembolso:999999
  PASS="$(grep -E '^PASSWORD_DEMO=' .env | head -1 | cut -d= -f2-)"
  TOK="$(curl -s -m 10 -X POST http://localhost:8001/api/v1/auth/login -H 'Content-Type: application/json' \
        -d "{\"email\":\"carla.reembolsos@demo.mx\",\"password\":\"$PASS\"}" \
        | python3 -c 'import sys,json; print(json.load(sys.stdin).get("access_token",""))' 2>/dev/null)"
  printf '\n>>> POST /api/v1/reembolsos-costos/reembolsos con el candado puesto (devolucion_id 999999)\n'
  curl -s -m 10 -i -X POST http://localhost:8005/api/v1/reembolsos-costos/reembolsos \
       -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' \
       -d '{"devolucion_id":999999,"estado":"aprobado","metodo":"transferencia","monto":1}' 2>&1 | sed -n '1p;/^X-Correlation-ID/p;$p'
  rc DEL devoluciones:lock:reembolso:999999
} > "$SAL/redis.txt"

# ------------------------------------------------------ Volumen de archivos
{
  cabecera "Volumen privado de evidencias (RN-14)"
  printf '\n>>> docker compose exec evidencias ls -l /srv/evidencias_privadas\n'
  docker compose exec -T evidencias sh -c 'ls -l /srv/evidencias_privadas 2>&1 | head -12' 2>&1
  printf '\n>>> docker volume inspect (nombre desde docker volume ls)\n'
  docker volume inspect "$(docker volume ls -q | grep evidencias_data | head -1)" 2>&1
  printf '\n>>> el directorio no se sirve por HTTP: curl -i /uploads/\n'
  curl -s -m 5 -i http://localhost:8007/uploads/ 2>&1 | head -3
} > "$SAL/volumen.txt"

# Oculta cualquier JWT que haya quedado y avisa si aparece la contrasena demo.
sed -i -E 's/eyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]*/***jwt***/g' "$SAL"/*.txt
if [ -n "${PASS:-}" ] && grep -qF "$PASS" "$SAL"/*.txt; then
  echo "ALERTA: la contrasena demo aparece en la salida; borra $SAL antes de commitear."; exit 2
fi
echo "Listo. Revisa y versiona: $SAL/ (docker, postgresql, mongodb, redis, volumen)."
