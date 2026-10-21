"""Seguridad y errores transversales sobre los ocho servicios (HTTP real).

401 (sin token, mal formado, expirado, firma ajena, revocado), 403 por rol en
cada servicio, 400/404/409 y trazabilidad por X-Correlation-ID.

Trazabilidad: RNF-28; RNF-08, RNF-09, RNF-11, RNF-13, RNF-16, RNF-23; RN-03,
RN-06, RN-07, RN-13.
"""
import os
import time
import uuid

import jwt
import pytest

from . import cliente as c
from . import flujo

P = c.PREFIJO_API

# (servicio, metodo, ruta) de un endpoint protegido por JWT en cada servicio.
PROTEGIDOS = [
    ("auth", "GET", P["auth"] + "/sesion"),
    ("devoluciones", "GET", P["devoluciones"]),
    ("logistica", "GET", P["logistica"] + "/recolecciones"),
    ("inspecciones", "GET", P["inspecciones"] + "/1"),
    ("reembolsos", "GET", P["reembolsos"] + "/reembolsos"),
    ("ventas", "GET", P["ventas"]),
    ("evidencias", "GET", P["evidencias"] + "?devolucion_id=1"),
    ("analisis", "GET", P["analisis"] + "/resumen"),
]
IDS = [p[0] for p in PROTEGIDOS]


@pytest.fixture(autouse=True, scope="module")
def _sin_limite_previo(ctx):
    c.liberar_limite_login()


def _token_firmado(secreto, exp_delta):
    ahora = int(time.time())
    return jwt.encode({"iss": "devoluciones-auth", "sub": "1", "rol": c.ADMINISTRADOR,
                       "sid": uuid.uuid4().hex, "jti": uuid.uuid4().hex, "typ": "access",
                       "iat": ahora - 3600, "exp": ahora + exp_delta},
                      secreto, algorithm="HS256")


# --------------------------------------------------------------------------- #
# 401
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("servicio,metodo,ruta", PROTEGIDOS, ids=IDS)
def test_sin_token_responde_401(ctx, servicio, metodo, ruta):
    resp = c.llamar(servicio, metodo, ruta)
    assert resp.status == 401 and c.error_tipo(resp) == "no_autenticado"


@pytest.mark.parametrize("servicio,metodo,ruta", PROTEGIDOS, ids=IDS)
def test_token_mal_formado_responde_401(ctx, servicio, metodo, ruta):
    resp = c.llamar(servicio, metodo, ruta, token="esto.no.es-un-jwt")
    assert resp.status == 401 and c.error_tipo(resp) == "token_invalido"


@pytest.mark.parametrize("servicio,metodo,ruta", PROTEGIDOS, ids=IDS)
def test_token_expirado_responde_401(ctx, servicio, metodo, ruta):
    from shared.seguridad import secreto
    resp = c.llamar(servicio, metodo, ruta, token=_token_firmado(secreto(), -60))
    assert resp.status == 401 and c.error_tipo(resp) == "token_expirado"


@pytest.mark.parametrize("servicio,metodo,ruta", PROTEGIDOS, ids=IDS)
def test_token_firmado_con_otra_llave_responde_401(ctx, servicio, metodo, ruta):
    resp = c.llamar(servicio, metodo, ruta, token=_token_firmado("x" * 40, 600))
    assert resp.status == 401 and c.error_tipo(resp) == "token_invalido"


@pytest.mark.parametrize("servicio,metodo,ruta", PROTEGIDOS, ids=IDS)
def test_token_revocado_responde_401_en_cada_servicio(ctx, servicio, metodo, ruta):
    token = getattr(ctx, "token_efimero", None)
    if not token:
        pytest.skip("El paso 1 del proceso completo no creo la sesion efimera")
    jti = jwt.decode(token, options={"verify_signature": False})["jti"]
    if not c.redis_cli().exists(f"devoluciones:jwt_revocado:{jti}"):
        pytest.skip("El paso 11 (logout) no reboco el token; correr test_01 primero")
    resp = c.llamar(servicio, metodo, ruta, token=token)
    assert resp.status == 401 and c.error_tipo(resp) == "token_revocado"


def test_refresh_token_no_sirve_como_access(ctx):
    c.liberar_limite_login()
    login = c.llamar("auth", "POST", P["auth"] + "/login",
                     {"email": ctx.emails[c.CLIENTE], "password": os.environ["PASSWORD_DEMO"]})
    assert login.status == 200
    resp = c.llamar("devoluciones", "GET", P["devoluciones"],
                    token=login.datos["refresh_token"])
    assert resp.status == 401 and c.error_tipo(resp) == "token_invalido"
    c.cerrar_sesion(login.datos["access_token"])


def test_login_con_credenciales_malas_no_revela_si_existe_el_correo(ctx):
    c.liberar_limite_login()
    inexistente = f"nadie.{uuid.uuid4().hex[:8]}@demo.mx"
    resp = c.llamar("auth", "POST", P["auth"] + "/login",
                    {"email": inexistente, "password": "incorrecta-123"})
    assert resp.status == 401 and c.error_tipo(resp) == "credenciales_invalidas"
    assert inexistente not in resp.texto  # RNF-16: sin eco del correo


# --------------------------------------------------------------------------- #
# 403 por rol: un endpoint protegido de CADA servicio
# --------------------------------------------------------------------------- #
ROL_INCORRECTO = [
    ("auth", "DELETE", P["auth"] + "/usuarios/1/sesiones", c.CLIENTE),
    ("devoluciones", "PATCH", P["devoluciones"] + "/1/resolucion", c.CLIENTE),
    ("logistica", "POST", P["logistica"] + "/recolecciones", c.CLIENTE),
    ("inspecciones", "POST", P["inspecciones"], c.CLIENTE),
    ("reembolsos", "POST", P["reembolsos"] + "/reembolsos", c.CLIENTE),
    ("ventas", "POST", "/api/v1/catalogos/motivos", c.CLIENTE),
    ("evidencias", "POST", P["evidencias"], c.ANALISTA),
    ("analisis", "GET", P["analisis"] + "/alertas-fraude", c.CLIENTE),
]


@pytest.mark.parametrize("servicio,metodo,ruta,rol", ROL_INCORRECTO,
                         ids=[r[0] for r in ROL_INCORRECTO])
def test_rol_incorrecto_responde_403(ctx, servicio, metodo, ruta, rol):
    resp = c.llamar(servicio, metodo, ruta, cuerpo={} if metodo != "GET" else None,
                    token=ctx.h(rol), absoluta=False)
    assert resp.status == 403 and c.error_tipo(resp) == "sin_permiso"
    assert rol == resp.datos["error"]["detalles"]["rol"]


def test_cliente_no_ve_la_devolucion_de_otro_y_queda_en_bitacora(ctx):
    resp = flujo.registrar(ctx)
    assert resp.status == 201
    dev_id = resp.datos["id"]
    ajena = c.llamar("devoluciones", "GET", f"{P['devoluciones']}/{dev_id}",
                     token=ctx.token_otro_cliente)
    assert ajena.status == 403
    assert c.sql("SELECT 1 FROM bitacora WHERE accion = 'acceso_denegado' "
                 "AND entidad_id = %s", (dev_id,), uno=True)


# --------------------------------------------------------------------------- #
# 400 / 404
# --------------------------------------------------------------------------- #
INVALIDOS = [
    ("devoluciones", "GET", P["devoluciones"] + "?por_pagina=0", None, c.CLIENTE),
    ("devoluciones", "POST", P["devoluciones"], {"motivo_id": 1}, c.CLIENTE),
    ("inspecciones", "POST", P["inspecciones"] + "/1/disposicion",
     {"destino": "al-espacio"}, c.ANALISTA),
    ("reembolsos", "POST", P["reembolsos"] + "/reembolsos",
     {"devolucion_id": 1, "estado": "aprobado", "metodo": "tarjeta", "monto": -5},
     c.ENCARGADO_REEMBOLSOS),
    ("ventas", "GET", P["ventas"] + "?q=" + "a" * 101, None, c.CLIENTE),
    ("evidencias", "GET", P["evidencias"], None, c.CLIENTE),
    ("analisis", "GET", P["analisis"] + "/pareto?dimension=inexistente", None, c.ANALISTA),
    ("analisis", "POST", P["analisis"] + "/clasificar-motivo", {"descripcion": "corta"}, c.CLIENTE),
    ("auth", "POST", P["auth"] + "/login", {"email": "no-es-correo", "password": "x"}, None),
]


@pytest.mark.parametrize("servicio,metodo,ruta,cuerpo,rol", INVALIDOS,
                         ids=[f"{i[0]}-{n}" for n, i in enumerate(INVALIDOS)])
def test_parametro_invalido_responde_400(ctx, servicio, metodo, ruta, cuerpo, rol):
    c.liberar_limite_login()
    resp = c.llamar(servicio, metodo, ruta, cuerpo=cuerpo, token=ctx.h(rol) if rol else None)
    assert resp.status == 400 and c.error_tipo(resp) == "validacion"


def test_logistica_fecha_pasada_responde_400(ctx):
    # El servicio valida la devolucion antes que la fecha: hace falta una autorizada.
    dev_id = flujo.registrar(ctx).datos["id"]
    assert flujo.autorizar(ctx, dev_id).status == 200
    resp = c.llamar("logistica", "POST", P["logistica"] + "/recolecciones",
                    {"devolucion_id": dev_id, "fecha_programada": "2020-01-01",
                     "lugar": "Tienda de prueba"}, token=ctx.h(c.COORDINADOR))
    assert resp.status == 400 and c.error_tipo(resp) == "validacion"


def test_json_malformado_responde_400(ctx):
    resp = c.llamar("devoluciones", "POST", P["devoluciones"], token=ctx.h(c.CLIENTE),
                    cabeceras={"Content-Type": "application/json"}, xml=b"{no es json")
    # `xml=` fuerza el cuerpo crudo; la cabecera de arriba pisa el Content-Type XML.
    assert resp.status == 400 and c.error_tipo(resp) == "json_invalido"


def test_content_type_no_soportado_responde_415(ctx):
    resp = c.llamar("devoluciones", "POST", P["devoluciones"], token=ctx.h(c.CLIENTE),
                    cabeceras={"Content-Type": "text/plain"}, xml=b"hola")
    assert resp.status == 415


INEXISTENTES = [
    ("devoluciones", "GET", P["devoluciones"] + "/99999999", c.ANALISTA),
    ("inspecciones", "GET", P["inspecciones"] + "/99999999", c.ANALISTA),
    ("ventas", "GET", P["ventas"] + "/99999999", c.ANALISTA),
    ("evidencias", "GET", P["evidencias"] + "/99999999", c.CLIENTE),
    ("reembolsos", "GET", P["reembolsos"] + "/costos/99999999", c.ANALISTA),
    ("ventas", "GET", "/api/v1/catalogos/motivos/99999999", c.ANALISTA),
]


@pytest.mark.parametrize("servicio,metodo,ruta,rol", INEXISTENTES,
                         ids=[f"{i[0]}-{n}" for n, i in enumerate(INEXISTENTES)])
def test_recurso_inexistente_responde_404(ctx, servicio, metodo, ruta, rol):
    resp = c.llamar(servicio, metodo, ruta, token=ctx.h(rol))
    assert resp.status == 404 and c.error_tipo(resp) == "no_encontrado"


def test_logistica_recoleccion_inexistente_responde_404(ctx):
    ruta, transp = flujo.ruta_y_transportista()
    resp = c.llamar("logistica", "PATCH",
                    P["logistica"] + "/recolecciones/99999999/asignacion",
                    {"ruta_id": ruta, "transportista_id": transp},
                    token=ctx.h(c.COORDINADOR))
    assert resp.status == 404


def test_error_incluye_el_correlation_id_de_la_peticion(ctx):
    cid = "e2e-err-" + uuid.uuid4().hex[:8]
    resp = c.llamar("devoluciones", "GET", P["devoluciones"] + "/99999999",
                    token=ctx.h(c.ANALISTA), correlation_id=cid)
    assert resp.headers["X-Correlation-ID"] == cid
    assert resp.datos["error"]["correlation_id"] == cid


# --------------------------------------------------------------------------- #
# 409: reglas de negocio
# --------------------------------------------------------------------------- #
def test_cantidad_excedida_responde_409(ctx):  # RN-01
    # Se lee lo disponible ahora: ctx.linea["disponible"] es el de antes de la corrida.
    disponible = flujo.disponible_actual(ctx)
    assert disponible > 0, "la prueba necesita unidades: debe fallar por cantidad, no por sin_disponible"
    resp = flujo.registrar(ctx, cantidad=disponible + 1)
    assert resp.status == 409 and c.error_tipo(resp) == "cantidad_excedida"


def test_reembolso_sin_autorizar_responde_409(ctx):  # RN-04
    resp = flujo.registrar(ctx)
    assert resp.status == 201
    dev_id = resp.datos["id"]
    r = c.llamar("reembolsos", "POST", P["reembolsos"] + "/reembolsos",
                 {"devolucion_id": dev_id, "estado": "aprobado",
                  "metodo": "tarjeta", "monto": 1},
                 token=ctx.h(c.ENCARGADO_REEMBOLSOS))
    assert r.status == 409 and c.error_tipo(r) == "estado_no_permite"
    assert c.sql("SELECT COUNT(*) AS n FROM reembolsos WHERE devolucion_id = %s",
                 (dev_id,), uno=True)["n"] == 0


def test_rechazo_exige_justificacion(ctx):  # RN-12
    resp = flujo.registrar(ctx)
    dev_id = resp.datos["id"]
    r = c.llamar("devoluciones", "PATCH", f"{P['devoluciones']}/{dev_id}/resolucion",
                 {"decision": "rechazar"}, token=ctx.h(c.ANALISTA))
    assert r.status == 400 and c.error_tipo(r) == "validacion"


def test_logistica_solo_programa_devoluciones_autorizadas_409(ctx):
    resp = flujo.registrar(ctx)
    dev_id = resp.datos["id"]
    from datetime import date, timedelta
    r = c.llamar("logistica", "POST", P["logistica"] + "/recolecciones",
                 {"devolucion_id": dev_id,
                  "fecha_programada": (date.today() + timedelta(days=1)).isoformat(),
                  "lugar": "Tienda"}, token=ctx.h(c.COORDINADOR))
    assert r.status == 409 and c.error_tipo(r) == "estado_no_permite"


def test_cadena_de_frio_rota_impide_inventario_409(ctx):  # RN-06, RN-07
    dev_id = flujo.hasta_recibida(ctx)
    insp = flujo.inspeccionar(ctx, dev_id, cadena_frio_rota=True, minutos_fuera_refrigeracion=45)
    assert insp.status == 201 and insp.datos["apto_para_inventario"] is False
    assert c.sql("SELECT apto_para_inventario FROM inspecciones_ref WHERE devolucion_id = %s",
                 (dev_id,), uno=True)["apto_para_inventario"] is False
    # La inspeccion no se puede duplicar.
    assert flujo.inspeccionar(ctx, dev_id).status == 409

    ruta = f"{P['inspecciones']}/{dev_id}/disposicion"
    analista = ctx.h(c.ANALISTA)
    r = c.llamar("inspecciones", "POST", ruta, {"destino": "inventario"}, token=analista)
    assert r.status == 409 and c.error_tipo(r) == "no_apto_inventario"
    assert c.sql("SELECT COUNT(*) AS n FROM disposiciones WHERE devolucion_id = %s",
                 (dev_id,), uno=True)["n"] == 0
    # El destino correcto para un producto no apto si se permite.
    r = c.llamar("inspecciones", "POST", ruta,
                 {"destino": "desecho", "justificacion": "Cadena de frio rota"}, token=analista)
    assert r.status == 201


def test_refrigerado_sin_temperatura_responde_400(ctx):  # RN-05
    dev_id = flujo.hasta_recibida(ctx)
    r = c.llamar("inspecciones", "POST", P["inspecciones"],
                 {"devolucion_id": dev_id, "estado_empaque": "Caja abierta",
                  "danos": False, "caducidad_vencida": False},
                 token=ctx.h(c.INSPECTOR))
    assert r.status == 400 and c.error_tipo(r) == "validacion"


# --------------------------------------------------------------------------- #
# Datos sensibles y SQL
# --------------------------------------------------------------------------- #
def test_bitacora_no_guarda_tokens(ctx):  # RNF-16
    filas = c.sql("SELECT 1 FROM bitacora WHERE detalle ILIKE '%%eyJ%%' "
                  "OR detalle ILIKE '%%bearer %%' LIMIT 1")
    assert filas == []


def test_busqueda_con_inyeccion_sql_no_rompe_nada(ctx):  # RNF-11
    antes = c.sql("SELECT COUNT(*) AS n FROM ventas", uno=True)["n"]
    resp = c.llamar("ventas", "GET", P["ventas"] + "?q=%27%3B%20DROP%20TABLE%20ventas%3B--",
                    token=ctx.h(c.ANALISTA))
    assert resp.status == 200 and resp.datos["paginacion"]["total"] == 0
    assert c.sql("SELECT COUNT(*) AS n FROM ventas", uno=True)["n"] == antes
