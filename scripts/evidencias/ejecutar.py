#!/usr/bin/env python3
"""Genera la evidencia con curl de un servicio: python3 scripts/evidencias/ejecutar.py <servicio>

Corre EN LA VM, desde la raiz del repositorio, con los servicios levantados y los datos de
demo cargados (docs/SETUP.md). Escribe docs/evidencias/ejecuciones/<archivo>.md y termina con
codigo distinto de cero si algun caso no cumple lo esperado.

    python3 scripts/evidencias/ejecutar.py clasificacion
    python3 scripts/evidencias/ejecutar.py todos          # uno tras otro, con pausa por el limite de login

Servicios: clasificacion, proveedores, causa_raiz, reportes, trazabilidad, auditoria, ...  (cada uno es un modulo casos_<servicio>.py de esta carpeta).
Trazabilidad: RNF-28, RF-31.
"""
import importlib
import os
import subprocess
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from motor import Corrida  # noqa: E402

SERVICIOS = ("clasificacion", "proveedores", "causa_raiz", "reportes", "trazabilidad", "auditoria")   # se amplia a medida que se agregan modulos casos_*.py
SALIDA = os.path.join("docs", "evidencias", "ejecuciones")
PAUSA_LOGIN = 62                 # el login admite 10 por minuto por IP (RNF-13)


def commit_actual():
    r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def correr(nombre):
    modulo = importlib.import_module(f"casos_{nombre}")
    corrida = Corrida(modulo.SERVICIO, modulo.SIGLA, modulo.TITULO, modulo.PUERTO,
                      via_proxy=os.environ.get("EVIDENCIAS_PUERTOS_DIRECTOS") != "1")
    corrida.nombre_cli = nombre
    interrupcion = None
    try:
        modulo.ejecutar(corrida)
    except Exception as exc:  # se escribe lo que se alcanzo a ejecutar y se muestra el error; no se pierde la evidencia
        interrupcion = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            corrida.limpiar()   # aunque falle algo, no se deja basura en la base de demostracion
        except Exception as exc:
            print(f"  AVISO: la limpieza fallo ({exc}); revisa la base de demostracion.")
    os.makedirs(SALIDA, exist_ok=True)
    ruta = os.path.join(SALIDA, f"{modulo.ARCHIVO}.md")
    fallas = corrida.escribir(ruta, commit_actual(), interrupcion)
    print(f"{modulo.SERVICIO}: {len(corrida.casos)} casos, {fallas} con falla -> {ruta}")
    if interrupcion:
        print(f"  INTERRUMPIDA tras el caso {len(corrida.casos)}: {interrupcion}")
        fallas += 1
    for c in corrida.casos:
        if not c["ok"]:
            malas = [t for t, ok in c["verificaciones"] if not ok]
            print(f"  FALLA {c['id']} {c['titulo']}: {'; '.join(malas)} (HTTP {c['resp'].estado})")
    return fallas


def main(argumentos):
    if not argumentos or argumentos[0] not in SERVICIOS + ("todos",):
        print(__doc__)
        return 2
    nombres = SERVICIOS if argumentos[0] == "todos" else (argumentos[0],)
    total = 0
    for i, nombre in enumerate(nombres):
        if i:
            time.sleep(PAUSA_LOGIN)
        total += correr(nombre)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
