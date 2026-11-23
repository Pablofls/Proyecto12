#!/usr/bin/env bash
# Pruebas de carga con Locust EN LA VM (RNF-29). Ver tests/carga/locustfile.py.
#
# Locust corre en un contenedor dentro de la red del compose: mide la plataforma,
# no el internet. Requiere el entorno levantado, seed_demo aplicado y PASSWORD_DEMO
# en el .env. Tres escenarios seguidos con la misma mezcla de perfiles:
#
#   humo    5 usuarios,  30 s   comprueba que todo responde antes de cargar
#   normal  25 usuarios, 2 min  un dia normal de operacion
#   pico    60 usuarios, 2 min  hora pico (cierre de mes, campana)
#
#   bash scripts/correr_carga.sh            # los tres
#   bash scripts/correr_carga.sh normal     # solo uno
#
# Deja CSV y reporte HTML por escenario en docs/pruebas/carga_<fecha>/ y el uso de
# CPU y memoria de los contenedores al final de cada escenario.
set -uo pipefail

cd "$(dirname "$0")/.."
IMAGEN="locustio/locust:2.31.8"
FECHA="$(date +%F)"
DIR="docs/pruebas/carga_${FECHA}"
mkdir -p "$DIR"
RED="$(docker inspect "$(docker compose ps -q auth)" \
        -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}')"
PASSWORD_DEMO="$(grep -E '^PASSWORD_DEMO=' "${APP_ENV_FILE:-.env}" | cut -d= -f2-)"
SOLO="${1:-todos}"

{
  echo "# Pruebas de carga"
  echo "Fecha (UTC): $(date -u '+%Y-%m-%d %H:%M:%S')"
  echo "Rama: $(git rev-parse --abbrev-ref HEAD)"
  echo "Commit: $(git rev-parse HEAD)"
  echo "Host: $(uname -n), $(nproc) CPU, $(free -h | awk '/Mem:/{print $2}') de RAM"
  echo "Locust: $IMAGEN, red $RED"
} | tee "$DIR/encabezado.txt"

# Solo contadores de limite (login, sugerencias, sincronizacion): no toca sesiones.
liberar_limites() {
  docker compose exec -T redis sh -c \
    "redis-cli --scan --pattern 'devoluciones:limite:*' | xargs -r redis-cli DEL" > /dev/null
}

escenario() {
  local nombre="$1" usuarios="$2" ritmo="$3" duracion="$4"
  [ "$SOLO" = "todos" ] || [ "$SOLO" = "$nombre" ] || return 0
  echo; echo "=== Escenario $nombre: $usuarios usuarios, $ritmo/s, $duracion ===" | tee -a "$DIR/encabezado.txt"
  liberar_limites
  docker run --rm --network "$RED" \
    -e PASSWORD_DEMO="$PASSWORD_DEMO" \
    -v "$PWD/tests/carga:/carga:ro" -v "$PWD/$DIR:/salida" \
    "$IMAGEN" -f /carga/locustfile.py --headless \
    -u "$usuarios" -r "$ritmo" -t "$duracion" --stop-timeout 10 \
    --csv "/salida/$nombre" --html "/salida/$nombre.html" --only-summary \
    2>&1 | tee "$DIR/$nombre.txt"
  # Uso de recursos justo al terminar (la carga ya bajo, pero muestra la memoria).
  docker stats --no-stream --format "{{.Name}} {{.CPUPerc}} {{.MemUsage}}" > "$DIR/${nombre}_recursos.txt"
}

escenario humo 5 5 30s
escenario normal 25 5 2m
escenario pico 60 10 2m
liberar_limites

# El lote del movil usa un id fijo: se borra al terminar para no dejar rastro.
docker compose exec -T postgres sh -c \
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -qc "DELETE FROM operaciones_offline WHERE id_operacion = '"'"'00000000-0000-4000-8000-00000000ca29'"'"'"' \
  > /dev/null 2>&1 || true

echo; echo "Resultados en $DIR/"
