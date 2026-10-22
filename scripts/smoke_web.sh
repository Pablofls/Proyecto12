#!/usr/bin/env bash
# Prueba de humo del monolito web EN LA VM: inicia sesion por el formulario real con
# tres roles y pide las pantallas principales. Falla si alguna no responde 200, si el
# cuerpo trae un error de plantilla o de servidor, o si falta un elemento clave
# (campanita, formularios de resolucion). Sirve para comprobar un cambio de interfaz
# antes y despues de integrarlo (RNF-25, RNF-26, RF-29).
#
#   bash scripts/smoke_web.sh                 # contra http://localhost:8000
#   WEB=http://34.51.108.167:8000 bash scripts/smoke_web.sh
#
# Requiere PASSWORD_DEMO en el .env (no se imprime). No modifica datos: solo GET.
set -uo pipefail
cd "$(dirname "$0")/.."
WEB="${WEB:-http://localhost:8000}"
PASS="$(grep -E '^PASSWORD_DEMO=' .env | head -1 | cut -d= -f2-)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
fallos=0; total=0
PG='docker compose exec -T postgres psql -U devoluciones_app -d devoluciones -tA -c'

entrar() {   # entrar <alias> <correo>
  curl -s -m 10 -c "$TMP/$1" -o /dev/null -w '' "$WEB/login"
  local c
  c="$(curl -s -m 10 -b "$TMP/$1" -c "$TMP/$1" -o /dev/null -w '%{http_code}' \
      --data-urlencode "email=$2" --data-urlencode "password=$PASS" "$WEB/login")"
  [ "$c" = "302" ] || { echo "LOGIN FALLO ($2): HTTP $c"; fallos=$((fallos+1)); }
}
ver() {      # ver <alias> <ruta> [texto que debe aparecer]
  total=$((total+1))
  local cuerpo="$TMP/cuerpo" c
  c="$(curl -s -m 15 -b "$TMP/$1" -o "$cuerpo" -w '%{http_code}' "$WEB$2")"
  local malo=""
  if [ "$c" != "200" ]; then malo="HTTP $c"
  elif grep -qiE 'Traceback|Internal Server Error|TemplateSyntaxError|UndefinedError|jinja2\.exceptions' "$cuerpo"; then malo="error de servidor/plantilla en el cuerpo"
  elif [ -n "${3:-}" ] && ! grep -qiF "$3" "$cuerpo"; then malo="no aparece '$3'"
  fi
  if [ -z "$malo" ]; then printf 'OK     %-5s %s\n' "$1" "$2"
  else printf 'FALLO  %-5s %s  -> %s\n' "$1" "$2" "$malo"; fallos=$((fallos+1)); fi
}

DEV="$($PG "SELECT id FROM devoluciones WHERE eliminado_en IS NULL ORDER BY id DESC LIMIT 1" 2>/dev/null | head -1)"
DEV_CLI="$($PG "SELECT d.id FROM devoluciones d JOIN venta_detalle vd ON vd.id=d.venta_detalle_id JOIN ventas v ON v.id=vd.venta_id JOIN usuarios u ON u.id=v.cliente_id WHERE u.email='miguel.cliente@demo.mx' AND d.eliminado_en IS NULL ORDER BY d.id DESC LIMIT 1" 2>/dev/null | head -1)"
USR="$($PG "SELECT id FROM usuarios WHERE email='miguel.cliente@demo.mx'" 2>/dev/null | head -1)"
echo "devolucion: ${DEV:-?}  devolucion de Miguel: ${DEV_CLI:-?}  usuario: ${USR:-?}"

entrar adm pablo.admin@demo.mx
entrar ana josue.analista@demo.mx
entrar cli miguel.cliente@demo.mx

# Administrador
ver adm /panel "bell\|campan\|notificaciones"
ver adm /ventas
ver adm /devoluciones/
ver adm "/devoluciones/$DEV"
ver adm /catalogos/
ver adm /catalogos/motivos
ver adm /usuarios/
ver adm /usuarios/nuevo
ver adm "/usuarios/$USR/editar"
ver adm /panel/causas
ver adm /panel/costos
ver adm /bitacora
ver adm /integracion/servicios
ver adm /integracion/servicios/estado '"disponibles"'
ver adm /notificaciones/
# Analista (resuelve solicitudes: el expediente debe traer su formulario)
ver ana /panel
ver ana /devoluciones/
ver ana "/devoluciones/$DEV" "resolucion"
ver ana /panel/causas
ver ana /panel/costos
ver ana /bitacora
ver ana /notificaciones/
# Cliente
ver cli /panel
ver cli /ventas
ver cli /devoluciones/
[ -n "$DEV_CLI" ] && ver cli "/devoluciones/$DEV_CLI"
ver cli /notificaciones/

echo
echo "$((total-fallos)) de $total pantallas OK; fallos: $fallos"
[ "$fallos" -eq 0 ]
