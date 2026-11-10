#!/usr/bin/env bash
# Corre la suite E2E y las pruebas de integracion por servicio EN LA VM (RNF-28).
#
# Requiere el entorno levantado (docker compose up -d --build), migraciones y
# seed_demo aplicados, y PASSWORD_DEMO en el .env (lo lee el compose).
# Guarda la salida completa en docs/pruebas/salida_<fecha>.txt para pegarla en
# docs/pruebas/resultado_<fecha>.md (ver docs/PRUEBAS.md).
# Entre bloques limpia el rate limit de login en Redis (ver liberar_limite_login).
#
#   bash scripts/correr_e2e.sh            # E2E + integracion por servicio
#   bash scripts/correr_e2e.sh e2e        # solo la suite E2E
#   bash scripts/correr_e2e.sh servicios  # solo la integracion por servicio
set -uo pipefail

cd "$(dirname "$0")/.."
FECHA="$(date +%F)"
SALIDA="docs/pruebas/salida_${FECHA}.txt"
MODO="${1:-todo}"
mkdir -p docs/pruebas
: > "$SALIDA"
fallos=0

# Encabezado de la corrida: la retroalimentacion del segundo parcial pide que cada
# resultado identifique commit, fecha y entorno, sin mezclar versiones. Todo sale
# del propio entorno; no se escribe a mano.
{
  echo "# Corrida de pruebas"
  echo "Fecha (UTC): $(date -u '+%Y-%m-%d %H:%M:%S')"
  echo "Rama: $(git rev-parse --abbrev-ref HEAD)"
  echo "Commit: $(git rev-parse HEAD)"
  echo "Commit (mensaje): $(git log -1 --format=%s)"
  if git diff --quiet HEAD -- . ':(exclude)docs/pruebas'; then
    echo "Arbol de trabajo: limpio"
  else
    echo "Arbol de trabajo: CON CAMBIOS SIN COMMIT (el resultado no corresponde exactamente al commit)"
  fi
  echo "Host: $(uname -n) ($(uname -sr))"
  echo "Docker: $(docker version --format '{{.Server.Version}}' 2>/dev/null)"
  echo "Docker Compose: $(docker compose version --short 2>/dev/null)"
  echo "PostgreSQL: $(docker compose exec -T postgres postgres --version 2>/dev/null)"
  echo "Redis: $(docker compose exec -T redis redis-server --version 2>/dev/null | cut -d' ' -f3)"
  echo "MongoDB: $(docker compose exec -T mongo mongod --version 2>/dev/null | head -1)"
  echo "Migraciones aplicadas: $(docker compose exec -T postgres psql -U "${POSTGRES_USER:-devoluciones_app}" -d "${POSTGRES_DB:-devoluciones}" -tA -c 'SELECT max(version) FROM schema_migrations' 2>/dev/null)"
  echo "Modo: $MODO"
  echo
} | tee -a "$SALIDA"

# El login esta limitado a LOGIN_MAX_POR_MINUTO por IP (RNF-13, H-07) y todos los
# bloques salen de la misma IP del compose. test_99 llega al 429 a proposito y cada
# suite hace varios logins, asi que se borran los contadores antes de cada bloque.
# Solo claves de limite: no toca sesiones, intentos fallidos ni bloqueos de cuentas.
liberar_limite_login() {
  docker compose exec -T redis redis-cli --scan --pattern 'devoluciones:limite:*:login' \
    | while read -r clave; do
        [ -n "$clave" ] && docker compose exec -T redis redis-cli DEL "$clave" > /dev/null
      done
}

correr() {
  liberar_limite_login
  echo "=== $* ===" | tee -a "$SALIDA"
  "$@" 2>&1 | tee -a "$SALIDA"
  [ "${PIPESTATUS[0]}" -eq 0 ] || fallos=$((fallos + 1))
}

if [ "$MODO" = "todo" ] || [ "$MODO" = "e2e" ]; then
  # El repositorio se monta en /repo para que la suite vea tests/, shared/ y los XSD.
  correr docker compose run --rm -v "$PWD":/repo -w /repo -e PYTHONPATH=/repo \
    -e INTEGRACION=1 devoluciones python -m pytest -v -s -p no:cacheprovider tests/e2e
fi

if [ "$MODO" = "todo" ] || [ "$MODO" = "servicios" ]; then
  for servicio in auth ventas-catalogos devoluciones evidencias logistica \
                  inspecciones reembolsos-costos analisis-auditoria; do
    correr docker compose run --rm -e INTEGRACION=1 "$servicio" \
      python -m pytest -v -p no:cacheprovider tests/test_integracion.py
  done
fi

echo | tee -a "$SALIDA"
echo "=== Resumen ===" | tee -a "$SALIDA"
grep -E "^(=== |=+ .*(passed|failed|error|skipped).* =+$)" "$SALIDA" | grep -v "=== Resumen" | tee -a "$SALIDA.resumen" > /dev/null
cat "$SALIDA.resumen" >> "$SALIDA"; rm -f "$SALIDA.resumen"
echo "Bloques con fallos: $fallos" | tee -a "$SALIDA"
echo
echo "Salida guardada en $SALIDA ($fallos bloque(s) con fallos)."
echo "Pega lo relevante en docs/pruebas/resultado_${FECHA}.md y actualiza docs/PRUEBAS.md."
exit "$fallos"
