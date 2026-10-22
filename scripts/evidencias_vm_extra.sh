#!/usr/bin/env bash
# Evidencia EN LA VM que faltaba en el documento tecnico (apartado 19.3):
#   EV-03  clave jwt_revocado:* en Redis tras un logout
#   EV-06  migraciones aplicadas y tablas
#   EV-20  pruebas unitarias dentro de cada contenedor
#   EV-25  build y arranque del Compose
#   13.1   bloqueo 423 al quinto intento fallido (y se desbloquea la cuenta)
#
#   bash scripts/evidencias_vm_extra.sh            # todo
#   bash scripts/evidencias_vm_extra.sh jwt        # solo uno: jwt | migraciones | unitarias | build | bloqueo
#
# Escribe transcripciones reales en docs/evidencias/bases/. Requiere PASSWORD_DEMO
# en el .env (no se imprime). Oculta JWT al final y aborta si aparece la contrasena.
# Trazabilidad: RNF-08, RNF-12, RNF-27, RNF-28.
set -uo pipefail
cd "$(dirname "$0")/.."
SAL="docs/evidencias/bases"; mkdir -p "$SAL"
FECHA="$(date -u '+%Y-%m-%d %H:%M UTC')"
QUE="${1:-todo}"
PASS="$(grep -E '^PASSWORD_DEMO=' .env | head -1 | cut -d= -f2-)"
cab() { printf '# %s\n\nCapturado en la VM el %s con scripts/evidencias_vm_extra.sh. Salida real, sin editar.\n' "$1" "$FECHA"; }
login() { curl -s -m 10 -X POST http://localhost:8001/api/v1/auth/login -H 'Content-Type: application/json' \
          -d "{\"email\":\"$1\",\"password\":\"$2\"}"; }
tok()   { python3 -c 'import sys,json; print(json.load(sys.stdin).get("access_token",""))' 2>/dev/null; }
quiere() { [ "$QUE" = "todo" ] || [ "$QUE" = "$1" ]; }

if quiere jwt; then
  {
    cab "EV-03: lista negra de JWT en Redis tras el logout"
    T="$(login carla.reembolsos@demo.mx "$PASS" | tok)"
    printf '\n>>> POST /auth/logout (cierra la sesion de Carla)\n'
    curl -s -m 10 -i -X POST http://localhost:8001/api/v1/auth/logout -H "Authorization: Bearer $T" | sed -n '1p;$p'
    printf '\n>>> GET /auth/sesion con el mismo token (debe ser 401 token_revocado)\n'
    curl -s -m 10 -i http://localhost:8001/api/v1/auth/sesion -H "Authorization: Bearer $T" | sed -n '1p;$p'
    printf '\n>>> redis-cli --scan --pattern devoluciones:jwt_revocado:*\n'
    K="$(docker compose exec -T redis redis-cli --scan --pattern 'devoluciones:jwt_revocado:*' | tr -d '\r')"
    echo "$K"
    for k in $(echo "$K" | head -1); do
      printf '\n>>> GET / TTL %s\n' "$k"
      docker compose exec -T redis redis-cli GET "$k"; docker compose exec -T redis redis-cli TTL "$k"
    done
  } > "$SAL/jwt_revocado.txt" 2>&1
fi

if quiere migraciones; then
  {
    cab "EV-06: migraciones aplicadas y tablas de PostgreSQL"
    printf '\n>>> python scripts/migrate.py --estado\n'
    docker compose exec -T app python scripts/migrate.py --estado 2>&1
    printf '\n>>> \\dt\n'
    docker compose exec -T postgres psql -U devoluciones_app -d devoluciones -P pager=off -c '\dt' 2>&1
  } > "$SAL/migraciones.txt"
fi

if quiere unitarias; then
  {
    cab "EV-20: pruebas unitarias dentro de cada contenedor (sin INTEGRACION)"
    for s in auth ventas-catalogos devoluciones evidencias logistica inspecciones reembolsos-costos analisis-auditoria; do
      printf '\n>>> docker compose run --rm --no-deps %s python -m pytest -q -p no:cacheprovider\n' "$s"
      docker compose run --rm --no-deps "$s" python -m pytest -q -p no:cacheprovider 2>&1 | tail -8
    done
  } > "$SAL/unitarias_contenedores.txt"
fi

if quiere build; then
  {
    cab "EV-25: build y arranque de Compose"
    printf '\n>>> docker compose up -d --build\n'
    docker compose up -d --build 2>&1 | tail -40
    printf '\n>>> docker compose ps\n'
    docker compose ps 2>&1
  } > "$SAL/build.txt"
fi

if quiere bloqueo; then
  {
    cab "Apartado 13.1: 423 al quinto intento fallido (RNF-12)"
    CORREO="sofia.cliente@demo.mx"
    for i in 1 2 3 4 5 6; do
      printf '\n>>> intento %s con contrasena incorrecta\n' "$i"
      curl -s -m 10 -i -X POST http://localhost:8001/api/v1/auth/login -H 'Content-Type: application/json' \
           -d "{\"email\":\"$CORREO\",\"password\":\"incorrecta-$i\"}" | sed -n '1p;$p'
    done
    printf '\n>>> intentos y bloqueo en Redis\n'
    docker compose exec -T redis redis-cli GET "devoluciones:intentos:$CORREO"
    docker compose exec -T redis redis-cli TTL "devoluciones:bloqueo:$CORREO"
    printf '\n>>> se desbloquea la cuenta para no dejarla bloqueada 15 min\n'
    docker compose exec -T redis redis-cli DEL "devoluciones:bloqueo:$CORREO" "devoluciones:intentos:$CORREO"
    docker compose exec -T postgres psql -U devoluciones_app -d devoluciones -c "UPDATE usuarios SET bloqueado_hasta = NULL WHERE email = '$CORREO'" 2>&1
  } > "$SAL/bloqueo_423.txt"
fi

sed -i -E 's/eyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]*/***jwt***/g' "$SAL"/*.txt
if [ -n "$PASS" ] && grep -qF "$PASS" "$SAL"/*.txt; then
  echo "ALERTA: la contrasena demo aparece en la salida; borra $SAL antes de commitear."; exit 2
fi
echo "Listo: $SAL/ (jwt_revocado, migraciones, unitarias_contenedores, build, bloqueo_423 segun lo pedido)."
