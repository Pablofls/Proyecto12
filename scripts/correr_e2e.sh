#!/usr/bin/env bash
# Corre la suite E2E y las pruebas de integracion por servicio EN LA VM (RNF-28).
#
# Requiere el entorno levantado (docker compose up -d --build), migraciones y
# seed_demo aplicados, y PASSWORD_DEMO en el .env (lo lee el compose).
# Guarda la salida completa en docs/pruebas/salida_<fecha>.txt para pegarla en
# docs/pruebas/resultado_<fecha>.md (ver docs/PRUEBAS.md).
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

correr() {
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

echo
echo "Salida guardada en $SALIDA ($fallos bloque(s) con fallos)."
echo "Pega lo relevante en docs/pruebas/resultado_${FECHA}.md y actualiza docs/PRUEBAS.md."
exit "$fallos"
