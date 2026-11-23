"""Auditoria: la bitacora y la traza de eventos, de solo lectura.

Este servicio queda solo con auditoria (el analisis se separo y su codigo se retiro: ver
retirado.py y docs/MIGRACION_ANALISIS_8008.md). Reglas de este modulo:

 - NO importa nada de analisis ni de calculo: cambiar el analisis no puede tocar la
   auditoria. Hay una prueba que lo comprueba.
 - Solo hay rutas GET: la auditoria se consulta, no se modifica (RN-12). Otra
   prueba lo comprueba. Quienes escriben en la bitacora son los demas servicios,
   directo en PostgreSQL con shared.infra.registrar_bitacora.
 - Ademas, la base protege la bitacora: desde la migracion 045 no admite UPDATE,
   DELETE ni TRUNCATE (solo agregar). GET /estado dice si esa proteccion esta puesta.
 - Nunca devuelve el campo `datos` de los eventos de MongoDB (puede traer cuerpos
   de peticiones); solo sus metadatos (RNF-16).

Trazabilidad: RF-30, RN-12, RN-13, RNF-16, RNF-23.
"""
from datetime import date

from flask import Blueprint, request

from shared import mongo
from shared.infra import consultar
from shared.paginacion import leer_paginacion, paginar
from shared.respuestas import ErrorApi, responder
from shared.seguridad import ADMINISTRADOR, ANALISTA, requiere_jwt

bp = Blueprint("auditoria", __name__, url_prefix="/api/v1/auditoria")
LECTORES = (ADMINISTRADOR, ANALISTA)
FILTROS_TEXTO = ("accion", "entidad", "correlation_id")
MAX_TEXTO = 100


def _texto(nombre, maximo=MAX_TEXTO):
    valor = (request.args.get(nombre) or "").strip()
    if len(valor) > maximo:
        raise ErrorApi(400, "validacion", f"Filtro {nombre} demasiado largo.")
    return valor


def _entero(nombre):
    valor = (request.args.get(nombre) or "").strip()
    if not valor:
        return None
    if not valor.isdigit() or not 0 < int(valor) <= 2147483647:
        raise ErrorApi(400, "validacion", f"{nombre} debe ser un entero positivo.")
    return int(valor)


def _fecha(nombre):
    valor = (request.args.get(nombre) or "").strip()
    if not valor:
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise ErrorApi(400, "validacion", f"{nombre} debe tener formato AAAA-MM-DD.")


def condiciones_bitacora():
    """WHERE de la bitacora con parametros ligados; los nombres de columna son fijos."""
    condiciones, parametros = ["1=1"], []
    for campo in FILTROS_TEXTO:
        valor = _texto(campo)
        if valor:
            condiciones.append(f"b.{campo}=%s")
            parametros.append(valor)
    for campo in ("entidad_id", "usuario_id"):
        valor = _entero(campo)
        if valor is not None:
            condiciones.append(f"b.{campo}=%s")
            parametros.append(valor)
    desde, hasta = _fecha("desde"), _fecha("hasta")
    if desde and hasta and hasta < desde:
        raise ErrorApi(400, "validacion", "hasta no puede ser menor que desde.")
    if desde:
        condiciones.append("b.fecha >= %s")
        parametros.append(desde)
    if hasta:  # incluye todo el dia indicado
        condiciones.append("b.fecha < (%s::date + INTERVAL '1 day')")
        parametros.append(hasta)
    return " AND ".join(condiciones), parametros


@bp.get("")
@requiere_jwt(*LECTORES)
def bitacora():
    pag = leer_paginacion()
    where, parametros = condiciones_bitacora()
    total = consultar(f"SELECT COUNT(*) AS n FROM bitacora b WHERE {where}",
                      tuple(parametros), uno=True)["n"]
    filas = consultar(f"""
        SELECT b.id, b.accion, b.entidad, b.entidad_id, b.detalle,
               b.correlation_id, b.fecha, u.nombre AS usuario
          FROM bitacora b LEFT JOIN usuarios u ON u.id = b.usuario_id
         WHERE {where} ORDER BY b.fecha DESC, b.id DESC LIMIT %s OFFSET %s
    """, tuple(parametros) + (pag.limite, pag.desplazamiento))
    return responder(paginar(filas, total, pag), raiz="bitacora")


def listar_eventos():
    """Eventos de MongoDB por correlation id o servicio. Sin el campo `datos` (RNF-16)."""
    pag = leer_paginacion()
    filtro = {}
    cid = _texto("correlation_id")
    if cid:
        filtro["correlation_id"] = cid
    servicio = _texto("servicio", 60)
    if servicio:
        filtro["servicio"] = servicio
    coleccion = mongo.get_mongo().eventos
    total = coleccion.count_documents(filtro)
    docs_mongo = list(coleccion.find(filtro, {"datos": 0})
                      .sort("fecha", -1).skip(pag.desplazamiento).limit(pag.limite))
    return responder(paginar(mongo.a_json(docs_mongo), total, pag), raiz="eventos")


@bp.get("/eventos")
@requiere_jwt(*LECTORES)
def eventos():
    return listar_eventos()


@bp.get("/estado")
@requiere_jwt(*LECTORES)
def estado():
    """Resumen de la bitacora y si la base la protege contra modificaciones.

    La proteccion es un trigger del esquema (migracion 045): frena a la aplicacion,
    a una inyeccion SQL o a un descuido, pero no a un administrador de la base que
    lo desactive a proposito; por eso se informa el estado y no se promete mas.
    """
    resumen = consultar("SELECT COUNT(*) AS registros, MIN(fecha) AS primero, MAX(fecha) AS ultimo "
                        "FROM bitacora", uno=True)
    triggers = {f["tgname"] for f in consultar("""
        SELECT tgname FROM pg_trigger
         WHERE tgrelid = 'bitacora'::regclass AND NOT tgisinternal AND tgenabled IN ('O', 'A')""")}
    protegida = "trg_bitacora_inmutable" in triggers
    sin_vaciar = "trg_bitacora_sin_truncate" in triggers
    return responder({**resumen,
                      "proteccion": {"actualizar_y_borrar_bloqueados": protegida,
                                     "vaciar_bloqueado": sin_vaciar,
                                     "completa": protegida and sin_vaciar},
                      "aviso": ("La bitacora solo admite agregar registros. Esta proteccion es del esquema "
                                "de la base; no sustituye el control de acceso al servidor de PostgreSQL.")},
                     raiz="estado_auditoria")
