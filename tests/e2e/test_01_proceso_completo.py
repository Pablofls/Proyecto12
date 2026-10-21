"""Proceso de negocio completo, encadenado, contra los contenedores reales.

Cada paso usa el id del anterior y verifica el EFECTO en PostgreSQL, MongoDB o
Redis, no solo el codigo HTTP. Si un paso falla, los siguientes se saltan.

Ejecutar en la VM (ver docs/PRUEBAS.md):
    docker compose run --rm -v "$PWD":/repo -w /repo -e PYTHONPATH=/repo \
        -e INTEGRACION=1 devoluciones python -m pytest -v -s tests/e2e

Trazabilidad: RNF-28; RF-07, RF-10, RF-11, RF-12 a RF-21, RF-23 a RF-25, RF-28, RF-29;
RN-01 a RN-07, RN-11, RN-12; RNF-08, RNF-09, RNF-23.
"""
import re
import uuid
from datetime import date, timedelta

import jwt
import pytest

from . import cliente as c
from . import flujo

# PNG minimo real (1x1): pasa la validacion de firma de evidencias.
PNG = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
       b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff"
       b"\xff?\x00\x05\xfe\x02\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82")

E = {}  # estado entre pasos de esta corrida


def requiere(*claves):
    faltan = [k for k in claves if k not in E]
    if faltan:
        pytest.skip(f"Depende de pasos previos que no completaron: {faltan}")


def test_paso_01_auth_login_sesion_en_redis(ctx):
    """Login real y GET protegido; la sesion vive en Redis con TTL (RNF-08)."""
    E["correlation_id"] = "e2e-" + uuid.uuid4().hex[:12]
    # Segunda sesion del cliente: la revoca el paso 11 sin tocar el resto.
    ctx.token_efimero = c.iniciar_sesion(ctx.emails[c.CLIENTE])
    resp = c.llamar("auth", "GET", c.PREFIJO_API["auth"] + "/sesion",
                    token=ctx.token_efimero)
    assert resp.status == 200
    assert resp.datos["usuario"]["rol"] == c.CLIENTE
    sid = resp.datos["sesion_id"]
    r = c.redis_cli()
    assert r.exists(f"devoluciones:sesion_api:{sid}") == 1
    assert 0 < r.ttl(f"devoluciones:sesion_api:{sid}") <= 8 * 3600
    assert resp.datos["sesion_expira_en_seg"] > 0
    E["sid_efimero"] = sid


def test_paso_02_ventas_localiza_linea_con_paginacion(ctx):
    resp = c.llamar("ventas", "GET",
                    f"{c.PREFIJO_API['ventas']}?q={ctx.linea['folio_venta']}&por_pagina=5",
                    token=ctx.h(c.CLIENTE))
    assert resp.status == 200
    assert {"pagina", "por_pagina", "total", "paginas"} <= set(resp.datos["paginacion"])
    assert ctx.linea["venta_id"] in [v["id"] for v in resp.datos["datos"]]
    det = c.llamar("ventas", "GET", f"{c.PREFIJO_API['ventas']}/{ctx.linea['venta_id']}",
                   token=ctx.h(c.CLIENTE))
    assert det.status == 200
    linea = next(x for x in det.datos["lineas"] if x["id"] == ctx.linea["id"])
    assert linea["disponible"] >= 2 and linea["clasificacion_temperatura"] == "refrigerado"


def test_paso_03_clasificar_motivo_es_solo_sugerencia(ctx):
    """RN-11: sugiere, exige confirmacion y no modifica nada."""
    antes = c.sql("SELECT COUNT(*) AS n, COALESCE(MAX(id),0) AS m FROM devoluciones", uno=True)
    resp = c.llamar("analisis", "POST", c.PREFIJO_API["analisis"] + "/clasificar-motivo",
                    {"descripcion": flujo.DESCRIPCION}, token=ctx.h(c.CLIENTE))
    assert resp.status == 200
    assert resp.datos["requiere_confirmacion"] is True
    assert resp.datos["sugerencias"], "debe sugerir al menos un motivo"
    assert resp.datos["sugerencias"][0]["motivo"] == "Producto danado"
    despues = c.sql("SELECT COUNT(*) AS n, COALESCE(MAX(id),0) AS m FROM devoluciones", uno=True)
    assert antes == despues, "la clasificacion no debe crear ni cambiar devoluciones"


def test_paso_04_cliente_registra_solicitud(ctx):
    resp = flujo.registrar(ctx, correlation_id=E["correlation_id"])
    assert resp.status == 201, resp.texto
    dev = resp.datos
    E["dev_id"], E["folio"] = dev["id"], dev["folio_devolucion"]
    assert re.fullmatch(r"DEV-\d{4}-\d+", E["folio"])
    assert resp.headers["Location"] == f"{c.PREFIJO_API['devoluciones']}/{dev['id']}"
    # RN-02: folio unico.
    assert c.sql("SELECT COUNT(*) AS n FROM devoluciones WHERE folio_devolucion = %s",
                 (E["folio"],), uno=True)["n"] == 1
    assert c.sql("SELECT estado FROM devoluciones WHERE id = %s", (dev["id"],),
                 uno=True)["estado"] == "solicitada"
    evento = c.mongo_db().eventos.find_one(
        {"datos.devolucion_id": dev["id"], "tipo": "devolucion_registrada"})
    assert evento and evento["servicio"] == "devoluciones"
    # RNF-23: el mismo id viaja por la respuesta, la bitacora y el evento.
    assert resp.headers["X-Correlation-ID"] == E["correlation_id"]
    assert evento["correlation_id"] == E["correlation_id"]
    assert c.sql("SELECT 1 FROM bitacora WHERE accion = 'alta_devolucion' "
                 "AND entidad_id = %s AND correlation_id = %s",
                 (dev["id"], E["correlation_id"]), uno=True)


def test_paso_05_evidencias_comentario_xml_y_archivo(ctx):
    """El cliente solo adjunta mientras la solicitud sigue en revision, por eso
    va antes de autorizar (evidencias/app.py, regla del cliente)."""
    requiere("dev_id")
    pref = c.PREFIJO_API["evidencias"]
    xml = (f"<evidencia><devolucion_id>{E['dev_id']}</devolucion_id>"
           "<tipo>comentario</tipo><etapa>solicitud</etapa>"
           "<comentario>El sello llego abierto.</comentario></evidencia>")
    resp = c.llamar("evidencias", "POST", pref, xml=xml, token=ctx.h(c.CLIENTE),
                    accept="application/xml")
    assert resp.status == 201, resp.texto
    assert resp.datos is not None and resp.datos.tag == "evidencia"
    com_id = int(resp.datos.findtext("id"))
    assert c.sql("SELECT tipo, comentario FROM evidencias WHERE id = %s", (com_id,),
                 uno=True) == {"tipo": "comentario", "comentario": "El sello llego abierto."}

    resp = c.llamar("evidencias", "POST", pref, token=ctx.h(c.CLIENTE),
                    multipart=("archivo", "foto_e2e.png", PNG,
                               {"devolucion_id": E["dev_id"], "etapa": "solicitud",
                                "comentario": "Foto del empaque"}))
    assert resp.status == 201, resp.texto
    E["evidencia_id"] = resp.datos["id"]
    fila = c.sql("SELECT tipo, mime_type, tamano_bytes, objeto FROM evidencias WHERE id = %s",
                 (E["evidencia_id"],), uno=True)
    assert fila["tipo"] == "fotografia" and fila["mime_type"] == "image/png"
    assert fila["tamano_bytes"] == len(PNG)
    assert c.mongo_db().evidencias_metadatos.find_one({"evidencia_id": E["evidencia_id"]})
    # El archivo vive en el volumen del contenedor de evidencias: se comprueba
    # descargandolo por el enlace temporal firmado (RN-14).
    enlace = c.llamar("evidencias", "GET", f"{pref}/{E['evidencia_id']}/enlace",
                      token=ctx.h(c.CLIENTE))
    assert enlace.status == 200 and enlace.datos["vigencia_segundos"] <= 900
    archivo = c.llamar("evidencias", "GET", enlace.datos["url_relativa"])
    assert archivo.status == 200
    assert int(archivo.headers["Content-Length"]) == len(PNG)


def test_paso_06_analista_autoriza(ctx):
    requiere("dev_id")
    resp = flujo.autorizar(ctx, E["dev_id"])
    assert resp.status == 200, resp.texto
    assert resp.datos["estado"] == "autorizada"
    fila = c.sql("SELECT estado, fecha_autorizacion FROM devoluciones WHERE id = %s",
                 (E["dev_id"],), uno=True)
    assert fila["estado"] == "autorizada" and fila["fecha_autorizacion"] is not None
    nota = c.sql("SELECT tipo FROM notificaciones WHERE devolucion_id = %s", (E["dev_id"],))
    tipos = [n["tipo"] for n in nota]
    # RF-29: aviso al cliente y, ademas, uno por coordinador (destinatarios en el paso 6b).
    assert tipos.count("autorizacion") == 1
    assert set(tipos) == {"autorizacion", "autorizacion_logistica"}
    assert c.sql("SELECT 1 FROM bitacora WHERE accion = 'autorizacion' AND entidad_id = %s",
                 (E["dev_id"],), uno=True)


def test_paso_06b_notificaciones_por_rol_y_campanita(ctx):
    """RF-29, UC-25, RN-13: al autorizar, el microservicio avisa al cliente y al
    coordinador; la campanita del web lo muestra solo a su dueno."""
    requiere("dev_id")
    dev_id, folio = E["dev_id"], E["folio"]
    filas = c.sql("""SELECT n.usuario_id, n.tipo, n.url, n.leido, r.nombre AS rol
                       FROM notificaciones n JOIN usuarios u ON u.id = n.usuario_id
                       JOIN roles r ON r.id = u.rol_id
                      WHERE n.devolucion_id = %s""", (dev_id,))
    por_tipo = {}
    for f in filas:
        por_tipo.setdefault(f["tipo"], []).append(f)

    # Destinatarios: el cliente dueno y TODOS los coordinadores activos; nadie mas.
    assert [f["rol"] for f in por_tipo["autorizacion"]] == [c.CLIENTE]
    assert por_tipo["autorizacion"][0]["url"] == f"/devoluciones/{dev_id}"
    coordinadores = {f["usuario_id"] for f in c.sql(
        """SELECT u.id AS usuario_id FROM usuarios u JOIN roles r ON r.id = u.rol_id
            WHERE r.nombre = %s AND u.estado = 'activo' AND u.eliminado_en IS NULL""",
        (c.COORDINADOR,))}
    avisados = {f["usuario_id"] for f in por_tipo["autorizacion_logistica"]}
    assert coordinadores and avisados == coordinadores
    assert all(f["url"].startswith("/logistica/") for f in por_tipo["autorizacion_logistica"])
    # Quien autoriza no se avisa a si mismo, ni se avisa a roles ajenos al paso.
    assert {f["rol"] for f in filas} <= {c.CLIENTE, c.COORDINADOR}

    # Campanita del cliente: contador y ultimas salen de sus propias filas.
    cliente = c.SesionWeb(ctx.emails[c.CLIENTE])
    coord = c.SesionWeb(ctx.emails[c.COORDINADOR])
    otro = c.SesionWeb(ctx.otro_cliente)
    try:
        resumen = cliente.get("/notificaciones/resumen")
        assert resumen.status == 200 and resumen.headers["Cache-Control"] == "no-store"
        propias = c.sql("""SELECT COUNT(*) AS n FROM notificaciones n JOIN usuarios u
                            ON u.id = n.usuario_id WHERE u.email = %s AND NOT n.leido""",
                        (ctx.emails[c.CLIENTE],), uno=True)["n"]
        assert resumen.datos["no_leidas"] == propias >= 1
        nota = next(n for n in resumen.datos["ultimas"] if folio in n["mensaje"])
        assert "autorizada" in nota["mensaje"] and nota["leido"] is False

        # RN-13: otro cliente no puede abrir ni marcar la notificacion ajena.
        assert otro.post(nota["leer"]).status == 404
        assert c.sql("SELECT leido FROM notificaciones WHERE id = %s", (nota["id"],),
                     uno=True)["leido"] is False

        # El dueno la abre: 302 al expediente y queda leida (con bitacora).
        abierta = cliente.post(nota["leer"])
        assert abierta.status == 302 and abierta.headers["Location"] == f"/devoluciones/{dev_id}"
        assert c.sql("SELECT leido FROM notificaciones WHERE id = %s", (nota["id"],),
                     uno=True)["leido"] is True
        assert c.sql("SELECT 1 FROM bitacora WHERE accion = 'leer_notificacion' "
                     "AND entidad_id = %s", (nota["id"],), uno=True)
        assert cliente.get("/notificaciones/resumen").datos["no_leidas"] == propias - 1

        # El coordinador ve el aviso con enlace a programar la recoleccion.
        aviso = next(n for n in coord.get("/notificaciones/resumen").datos["ultimas"]
                     if folio in n["mensaje"])
        assert "programa la recoleccion" in aviso["mensaje"]
        destino = coord.post(aviso["leer"])
        assert destino.status == 302 and destino.headers["Location"].startswith("/logistica/")
    finally:
        for sesion in (cliente, coord, otro):
            sesion.cerrar()


def test_paso_07_logistica_hasta_recepcion_y_costo(ctx):
    requiere("dev_id")
    pref = c.PREFIJO_API["logistica"]
    coord = ctx.h(c.COORDINADOR)
    resp = c.llamar("logistica", "POST", f"{pref}/recolecciones",
                    {"devolucion_id": E["dev_id"],
                     "fecha_programada": (date.today() + timedelta(days=1)).isoformat(),
                     "lugar": "Tienda de prueba E2E"}, token=coord)
    assert resp.status == 201, resp.texto
    rec_id = resp.datos["id"]
    assert c.sql("SELECT estado FROM devoluciones WHERE id = %s", (E["dev_id"],),
                 uno=True)["estado"] == "en_recoleccion"

    ruta, transp = flujo.ruta_y_transportista()
    resp = c.llamar("logistica", "PATCH", f"{pref}/recolecciones/{rec_id}/asignacion",
                    {"ruta_id": ruta, "transportista_id": transp}, token=coord)
    assert resp.status == 200 and resp.datos["estado"] == "asignada"
    for estado in ("en_transito", "completada"):
        resp = c.llamar("logistica", "PATCH", f"{pref}/recolecciones/{rec_id}/estado",
                        {"estado": estado}, token=coord)
        assert resp.status == 200 and resp.datos["estado"] == estado
        assert c.sql("SELECT estado FROM recolecciones WHERE id = %s", (rec_id,),
                     uno=True)["estado"] == estado
    # Una recoleccion completada no retrocede.
    assert c.llamar("logistica", "PATCH", f"{pref}/recolecciones/{rec_id}/estado",
                    {"estado": "en_transito"}, token=coord).status == 409

    resp = c.llamar("logistica", "POST", f"{pref}/recepciones",
                    {"devolucion_id": E["dev_id"], "coincide_expediente": True},
                    token=ctx.h(c.ENCARGADO_CENTRO))
    assert resp.status == 201, resp.texto
    assert c.sql("SELECT estado FROM devoluciones WHERE id = %s", (E["dev_id"],),
                 uno=True)["estado"] == "recibida"

    # Costo de logistica (RF-27): el coordinador solo registra la etapa transporte.
    resp = c.llamar("reembolsos", "POST", c.PREFIJO_API["reembolsos"] + "/costos",
                    {"devolucion_id": E["dev_id"], "etapa": "transporte", "monto": 120.50},
                    token=coord)
    assert resp.status == 201, resp.texto
    assert float(c.sql("SELECT monto FROM costos WHERE devolucion_id = %s AND etapa = 'transporte'",
                       (E["dev_id"],), uno=True)["monto"]) == 120.50
    E["recoleccion_id"] = rec_id


def test_paso_08_inspeccion_disposicion_y_etiqueta(ctx):
    requiere("dev_id", "recoleccion_id")
    resp = flujo.inspeccionar(ctx, E["dev_id"])
    assert resp.status == 201, resp.texto
    assert resp.datos["apto_para_inventario"] is True
    doc = c.mongo_db().inspecciones.find_one({"devolucion_id": E["dev_id"]})
    assert doc and doc["condiciones"]["temperatura_recepcion"] == 4.0  # RN-05
    ref = c.sql("SELECT mongo_doc_id, apto_para_inventario FROM inspecciones_ref "
                "WHERE devolucion_id = %s", (E["dev_id"],), uno=True)
    assert ref["mongo_doc_id"] == str(doc["_id"]) and ref["apto_para_inventario"] is True

    resp = c.llamar("inspecciones", "POST",
                    f"{c.PREFIJO_API['inspecciones']}/{E['dev_id']}/disposicion",
                    {"destino": "inventario", "justificacion": "Producto apto"},
                    token=ctx.h(c.ANALISTA))
    assert resp.status == 201, resp.texto
    disp_id = resp.datos["id"]
    assert c.sql("SELECT estado FROM devoluciones WHERE id = %s", (E["dev_id"],),
                 uno=True)["estado"] == "resuelta"

    resp = c.llamar("inspecciones", "POST",
                    f"{c.PREFIJO_API['inspecciones']}/inventario/{disp_id}/etiqueta",
                    token=ctx.h(c.ENCARGADO_CENTRO))
    assert resp.status == 201, resp.texto
    etiqueta = c.sql("SELECT etiqueta_codigo FROM inventario_recuperado WHERE disposicion_id = %s",
                     (disp_id,), uno=True)["etiqueta_codigo"]
    assert etiqueta == "REC-" + E["folio"].replace("DEV-", "")
    E["disposicion_id"] = disp_id


def test_paso_09_reembolso_unico_con_lock(ctx):
    requiere("dev_id", "disposicion_id")
    pref = c.PREFIJO_API["reembolsos"] + "/reembolsos"
    maximo = c.sql("""SELECT vd.precio_unitario * d.cantidad_devuelta AS valor
                        FROM devoluciones d JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
                       WHERE d.id = %s""", (E["dev_id"],), uno=True)["valor"]
    cuerpo = {"devolucion_id": E["dev_id"], "estado": "aprobado",
              "metodo": "transferencia", "monto": float(maximo)}
    token = ctx.h(c.ENCARGADO_REEMBOLSOS)
    resp = c.llamar("reembolsos", "POST", pref, cuerpo, token=token)
    assert resp.status == 201, resp.texto
    assert c.sql("SELECT COUNT(*) AS n FROM reembolsos WHERE devolucion_id = %s",
                 (E["dev_id"],), uno=True)["n"] == 1
    assert c.sql("SELECT estado FROM devoluciones WHERE id = %s", (E["dev_id"],),
                 uno=True)["estado"] == "cerrada"
    nota = c.sql("SELECT n.usuario_id, n.url FROM notificaciones n WHERE n.devolucion_id = %s "
                 "AND n.tipo = 'reembolso_aprobado'", (E["dev_id"],), uno=True)
    assert nota, "falta la notificacion al cliente (RF-29)"
    assert nota["usuario_id"] == c.sql("SELECT id FROM usuarios WHERE email = %s",
                                       (ctx.emails[c.CLIENTE],), uno=True)["id"]

    # RN-03: repetir -> 409 y sigue habiendo una sola fila.
    resp = c.llamar("reembolsos", "POST", pref, cuerpo, token=token)
    assert resp.status == 409 and c.error_tipo(resp) == "reembolso_duplicado"
    assert c.sql("SELECT COUNT(*) AS n FROM reembolsos WHERE devolucion_id = %s",
                 (E["dev_id"],), uno=True)["n"] == 1

    # Lock de Redis: con el candado tomado por otro proceso responde 409 sin tocar nada.
    llave = f"devoluciones:lock:reembolso:{E['dev_id']}"
    r = c.redis_cli()
    r.set(llave, "otro-proceso", ex=30)
    try:
        resp = c.llamar("reembolsos", "POST", pref, cuerpo, token=token)
        assert resp.status == 409 and c.error_tipo(resp) == "reembolso_en_proceso"
    finally:
        r.delete(llave)
    # Tras un reembolso el servicio libera su propio lock.
    assert r.exists(llave) == 0


def test_paso_10_analisis_sincroniza_pareto_y_cache(ctx):
    requiere("dev_id")
    pref = c.PREFIJO_API["analisis"]
    analista = ctx.h(c.ANALISTA)
    resp = c.llamar("analisis", "POST", pref + "/sincronizar", token=analista)
    assert resp.status == 200 and resp.datos["casos_sincronizados"] >= 1
    assert c.mongo_db().resultados_analisis.find_one(
        {"tipo_analisis": "snapshot_devolucion", "devolucion_id": E["dev_id"]})

    primera = c.llamar("analisis", "GET", pref + "/pareto?dimension=motivo&medida=frecuencia",
                       token=analista)
    assert primera.status == 200 and primera.datos["cache"] == "miss"
    assert primera.datos["categorias"]
    segunda = c.llamar("analisis", "GET", pref + "/pareto?dimension=motivo&medida=frecuencia",
                       token=analista)
    assert segunda.status == 200 and segunda.datos["cache"] == "hit"
    assert segunda.datos["categorias"] == primera.datos["categorias"]
    r = c.redis_cli()
    claves = list(r.scan_iter("devoluciones:cache:causas:*"))
    assert claves and all(0 < r.ttl(k) <= 600 for k in claves)

    alertas = c.llamar("analisis", "GET", pref + "/alertas-fraude", token=analista)
    assert alertas.status == 200 and "aviso" in alertas.datos  # RN-09: indicadores, no veredicto

    # RNF-23: la operacion del paso 4 se reconstruye por su correlation id.
    eventos = c.llamar("analisis", "GET",
                       f"{pref}/eventos?correlation_id={E['correlation_id']}",
                       token=analista)
    assert eventos.status == 200 and eventos.datos["paginacion"]["total"] >= 1


def test_paso_11_logout_revoca_el_token_en_todos_los_servicios(ctx):
    requiere("sid_efimero")
    token = ctx.token_efimero
    sesion = c.PREFIJO_API["auth"] + "/sesion"
    assert c.llamar("auth", "GET", sesion, token=token).status == 200
    assert c.llamar("devoluciones", "GET", c.PREFIJO_API["devoluciones"],
                    token=token).status == 200
    jti = jwt.decode(token, options={"verify_signature": False})["jti"]

    assert c.llamar("auth", "POST", c.PREFIJO_API["auth"] + "/logout", token=token).status == 200
    r = c.redis_cli()
    assert r.exists(f"devoluciones:jwt_revocado:{jti}") == 1
    assert r.exists(f"devoluciones:sesion_api:{E['sid_efimero']}") == 0
    for servicio in ("auth", "devoluciones", "ventas"):
        ruta = sesion if servicio == "auth" else c.PREFIJO_API[servicio]
        resp = c.llamar(servicio, "GET", ruta, token=token)
        assert resp.status == 401 and c.error_tipo(resp) == "token_revocado", servicio
