"""Chequeo de salud de toda la plataforma (dominio 22).

No usa el contexto de Flask (g): lo llama tanto un endpoint como el hilo que
revisa cada minuto en segundo plano.

Guarda en MongoDB:
- monitoreo_chequeos: cada chequeo (se borran solos a los 7 dias).
- alertas_operativas: una alerta activa por (tipo, recurso); se resuelve sola
  cuando el recurso vuelve a estar bien.
"""
import json
import logging
import os
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras

import reglas
from shared import mongo
from shared.infra import PREFIJO, get_redis

log = logging.getLogger("servicio")

SERVICIOS_DEFECTO = (
    "web=http://app:8000,auth=http://auth:8000,ventas-catalogos=http://ventas-catalogos:8000,"
    "proveedores=http://proveedores:8000,"
    "devoluciones=http://devoluciones:8000,evidencias=http://evidencias:8000,"
    "reportes-analitica=http://reportes-analitica:8000,"
    "logistica=http://logistica:8000,inspecciones=http://inspecciones:8000,"
    "disposicion-inventario=http://disposicion-inventario:8000,"
    "causa-raiz=http://causa-raiz:8000,"
    "reembolsos-costos=http://reembolsos-costos:8000,analisis-auditoria=http://analisis-auditoria:8000,"
    "sincronizacion=http://sincronizacion:8000,"
    "clasificacion-motivos=http://clasificacion-motivos:8000"
)
DIAS_HISTORIAL = 7
_indices_listos = False


def servicios_configurados():
    """{nombre: url_base} desde MONITOREO_SERVICIOS (nombre=url,nombre=url)."""
    texto = os.environ.get("MONITOREO_SERVICIOS") or SERVICIOS_DEFECTO
    servicios = {}
    for parte in texto.split(","):
        if "=" in parte:
            nombre, url = parte.split("=", 1)
            servicios[nombre.strip()] = url.strip().rstrip("/")
    return servicios


def _ms(inicio):
    return round((time.perf_counter() - inicio) * 1000)


def revisar_servicio(nombre, url, timeout=3):
    """GET /health de un servicio; nunca lanza excepcion."""
    inicio = time.perf_counter()
    codigo, cuerpo, error = None, None, None
    try:
        peticion = urllib.request.Request(url + "/health", headers={"Accept": "application/json"})
        with urllib.request.urlopen(peticion, timeout=timeout) as resp:
            codigo, cuerpo = resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        codigo = exc.code
        try:
            cuerpo = json.loads(exc.read() or b"{}")
        except ValueError:
            cuerpo = None
    except Exception as exc:  # noqa: BLE001 - sin red, DNS, timeout: el servicio esta caido
        error = type(exc).__name__
    dependencias = {}
    if isinstance(cuerpo, dict):
        for dep, valor in (cuerpo.get("dependencias") or {}).items():
            dependencias[dep] = bool(valor.get("ok")) if isinstance(valor, dict) else bool(valor)
    return {"servicio": nombre, "estado": reglas.estado_servicio(codigo, cuerpo), "codigo": codigo,
            "ms": _ms(inicio) if error is None else None, "error": error, "dependencias": dependencias}


def _conexion_pg():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        dbname=os.environ.get("POSTGRES_DB", "devoluciones"),
        user=os.environ.get("POSTGRES_USER", "devoluciones_app"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        cursor_factory=psycopg2.extras.RealDictCursor, connect_timeout=3)


def _probar(prueba):
    inicio = time.perf_counter()
    try:
        prueba()
        return {"ok": True, "ms": _ms(inicio), "error": None}
    except Exception as exc:  # noqa: BLE001
        log.warning("Base no disponible: %s", type(exc).__name__)
        return {"ok": False, "ms": None, "error": "no responde"}


def _ping_pg():
    conn = _conexion_pg()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
    finally:
        conn.close()


def revisar_bases():
    return {
        "postgresql": _probar(_ping_pg),
        "redis": _probar(lambda: get_redis().ping()),
        "mongodb": _probar(lambda: mongo.get_mongo().command("ping")),
    }


def revisar_colas():
    """Estado de la cola de sincronizacion offline en las ultimas 24 h."""
    try:
        conn = _conexion_pg()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT count(*) FILTER (WHERE estado = 'aceptada')  AS aceptada_24h,
                           count(*) FILTER (WHERE estado = 'conflicto') AS conflicto_24h,
                           count(*) FILTER (WHERE estado = 'rechazada') AS rechazada_24h,
                           count(*) FILTER (WHERE envios > 1)           AS reintentos_24h
                      FROM operaciones_offline
                     WHERE recibido_en > now() - interval '24 hours'""")
                offline = dict(cur.fetchone())
        finally:
            conn.close()
    except Exception:  # noqa: BLE001 - si PostgreSQL cae ya hay alerta de base
        offline = None
    return {"operaciones_offline": offline}


def _asegurar_indices(db):
    global _indices_listos
    if _indices_listos:
        return
    db.monitoreo_chequeos.create_index("fecha", expireAfterSeconds=DIAS_HISTORIAL * 86400)
    db.alertas_operativas.create_index([("estado", 1), ("tipo", 1), ("recurso", 1)])
    _indices_listos = True


def actualizar_alertas(db, chequeo, ahora):
    """Abre las alertas nuevas, cuenta las repetidas y resuelve las que ya no
    aparecen. Devuelve las alertas activas de los recursos revisados."""
    detectadas = reglas.alertas_detectadas(chequeo)
    claves = set()
    for alerta in detectadas:
        claves.add((alerta["tipo"], alerta["recurso"]))
        db.alertas_operativas.update_one(
            {"tipo": alerta["tipo"], "recurso": alerta["recurso"], "estado": "activa"},
            {"$set": {"severidad": alerta["severidad"], "mensaje": alerta["mensaje"], "ultima_vez": ahora},
             "$inc": {"veces": 1},
             "$setOnInsert": {"primera_vez": ahora}},
            upsert=True)
    revisados = reglas.recursos_revisados(chequeo)
    for activa in db.alertas_operativas.find({"estado": "activa", "recurso": {"$in": list(revisados)}}):
        if (activa["tipo"], activa["recurso"]) not in claves:
            db.alertas_operativas.update_one({"_id": activa["_id"]},
                                             {"$set": {"estado": "resuelta", "resuelta_en": ahora}})
    return detectadas


def chequear(servicios=None, guardar=True):
    """Revisa servicios, bases y colas en paralelo y actualiza las alertas."""
    servicios = servicios if servicios is not None else servicios_configurados()
    ahora = datetime.now(timezone.utc)
    with ThreadPoolExecutor(max_workers=max(1, len(servicios))) as pool:
        futuros = [pool.submit(revisar_servicio, n, u) for n, u in servicios.items()]
        bases = revisar_bases()
        colas = revisar_colas()
        resultados = [f.result() for f in futuros]
    chequeo = {"fecha": ahora, "servicios": resultados, "bases": bases, "colas": colas}
    alertas = []
    if guardar:
        try:
            db = mongo.get_mongo()
            _asegurar_indices(db)
            db.monitoreo_chequeos.insert_one(dict(chequeo))
            alertas = actualizar_alertas(db, chequeo, ahora)
        except Exception:  # noqa: BLE001 - sin MongoDB igual se responde el chequeo
            log.exception("No se pudo guardar el chequeo de monitoreo")
            alertas = reglas.alertas_detectadas(chequeo)
    else:
        alertas = reglas.alertas_detectadas(chequeo)
    estados = [s["estado"] for s in resultados] + ["ok" if b["ok"] else "caido" for b in bases.values()]
    chequeo["resumen"] = {
        "estado": "ok" if all(e == "ok" for e in estados) else "con_fallas",
        "servicios_ok": sum(1 for s in resultados if s["estado"] == "ok"),
        "servicios_total": len(resultados),
        "alertas": len(alertas),
    }
    chequeo["alertas"] = alertas
    return chequeo


def iniciar_en_segundo_plano(intervalo):
    """Un chequeo cada `intervalo` segundos. Gunicorn arranca varios workers:
    un candado en Redis hace que solo uno revise en cada turno."""
    def ciclo():
        while True:
            time.sleep(intervalo)
            try:
                if get_redis().set(f"{PREFIJO}monitoreo:turno", "1", nx=True, ex=max(intervalo - 5, 5)):
                    chequear()
            except Exception:  # noqa: BLE001 - el hilo nunca debe morir
                log.exception("Fallo el chequeo automatico")
    hilo = threading.Thread(target=ciclo, name="monitoreo", daemon=True)
    hilo.start()
    return hilo
