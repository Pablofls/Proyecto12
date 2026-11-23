"""Casos de evidencia de proveedores (8013): RF-24, RF-26, RN-09, RN-12, RN-13, RNF-09.

Cubre cada endpoint con exito en JSON y en XML y con errores controlados. Las reclamaciones que
crea llevan el asunto "Evidencia P4..." y se borran al final por ese marcador; la bitacora se conserva.
"""
from datetime import date, timedelta

SERVICIO = "proveedores"
SIGLA = "PRO"
TITULO = "Proveedores, indicadores y reclamaciones"
PUERTO = 8013
ARCHIVO = "proveedores"

API = "/api/v1/proveedores"
LOTE = "L-2026-PROB-01"
DEVOLUCION_N = ("SELECT d.id FROM devoluciones d JOIN venta_detalle vd ON vd.id = d.venta_detalle_id "
                "JOIN lotes l ON l.id = vd.lote_id WHERE l.numero_lote = '" + LOTE + "' "
                "AND d.eliminado_en IS NULL ORDER BY d.id OFFSET %d LIMIT 1")
SEMAFOROS = ("normal", "atencion", "critico", "sin_datos")


def tipo_error(r):
    return r.json["error"]["tipo"]


def ejecutar(c):
    c.ctx["prov"] = int(c.valor(f"SELECT proveedor_id FROM lotes WHERE numero_lote = '{LOTE}'"))
    c.ctx["lote"] = int(c.valor(f"SELECT id FROM lotes WHERE numero_lote = '{LOTE}'"))
    c.ctx["otro"] = int(c.valor("SELECT id FROM proveedores WHERE id <> {prov} ORDER BY id LIMIT 1"))
    c.ctx["nombre"] = c.valor("SELECT nombre FROM proveedores WHERE id = {prov}")
    c.ctx["busqueda"] = c.ctx["nombre"].split()[0].lower()
    for n in (1, 2, 3):
        c.ctx[f"dev{n}"] = int(c.valor(DEVOLUCION_N % (n - 1)))
    limite = (date.today() + timedelta(days=14)).isoformat()
    marcador = "Evidencia P4"
    c.limpieza += [
        f"DELETE FROM seguimiento_reclamacion WHERE reclamacion_id IN (SELECT id FROM reclamaciones_proveedor WHERE asunto LIKE '{marcador}%')",
        f"DELETE FROM reclamacion_devoluciones WHERE reclamacion_id IN (SELECT id FROM reclamaciones_proveedor WHERE asunto LIKE '{marcador}%')",
        f"DELETE FROM reclamaciones_proveedor WHERE asunto LIKE '{marcador}%'",
    ]

    # ---------------------------------------------------------------- salud, contratos y Swagger
    c.caso("salud 200 JSON", "GET", "/health", objetivo="El servicio informa su estado y el de PostgreSQL y Redis (RF-32).",
           verifica=[("estado ok", lambda r: r.json["estado"] == "ok"),
                     ("PostgreSQL ok", lambda r: r.json["dependencias"]["postgresql"]["ok"] is True)])
    c.caso("salud 200 XML", "GET", "/health", accept="application/xml", objetivo="El mismo endpoint responde XML (RF-31).",
           verifica=[("es XML", lambda r: r.tipo.startswith("application/xml")), ("estado ok", lambda r: "<estado>ok</estado>" in r.texto)])
    c.caso("Swagger: documentacion de la API", "GET", "/docs", accept="text/html", objetivo="La API publica su documentacion Swagger.",
           verifica=[("HTML de Swagger UI", lambda r: "swagger" in r.texto.lower())])
    c.caso("Swagger: especificacion OpenAPI", "GET", "/openapi.json", objetivo="La especificacion lista los endpoints de proveedores y reclamaciones.",
           verifica=[("incluye las reclamaciones", lambda r: f"{API}/reclamaciones" in r.json["paths"]),
                     ("incluye el seguimiento", lambda r: f"{API}/reclamaciones/{{id}}/seguimiento" in r.json["paths"])])
    c.caso("contrato XSD publicado", "GET", "/contratos/reclamacion.xsd", accept="application/xml",
           objetivo="El contrato XML de la reclamacion se publica para que los clientes lo validen (RF-31).",
           verifica=[("es un esquema XSD", lambda r: "xs:schema" in r.texto and 'name="devolucion_ids"' in r.texto)])

    # ---------------------------------------------------------------- autenticacion y permisos
    c.caso("sin token: 401", "GET", API, espera=401, objetivo="Un endpoint protegido exige JWT (RNF-09).",
           verifica=[("tipo no_autenticado", lambda r: tipo_error(r) == "no_autenticado")])
    c.caso("token invalido: 401", "GET", API, espera=401, token="no.es.un.jwt", objetivo="Un token alterado se rechaza (RNF-09).",
           verifica=[("tipo token_invalido", lambda r: tipo_error(r) == "token_invalido")])
    c.caso("cliente: 403", "GET", API, rol="cliente", espera=403,
           objetivo="Los indicadores de calidad y los costos no los ve un cliente (RN-13).",
           verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])
    c.caso("inspector: 403", "GET", f"{API}/{{prov}}/indicadores", rol="inspector", espera=403,
           objetivo="Tampoco el Inspector: la lectura es de Administrador, Analista, Supervisor y Encargado de Reembolsos.",
           verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])

    # ---------------------------------------------------------------- listado, detalle e indicadores
    c.caso("listado 200 con indicadores", "GET", f"{API}?por_pagina=5", rol="analista",
           objetivo="Proveedores de mayor a menor tasa de devolucion, con semaforo (RF-24, RF-26).",
           verifica=[("trae el promedio general", lambda r: isinstance(r.json["tasa_promedio_pct"], (int, float))),
                     ("cada fila trae semaforo", lambda r: all(f["semaforo"] in SEMAFOROS for f in r.json["datos"])),
                     ("ordenado por tasa", lambda r: [f["tasa_pct"] or 0 for f in r.json["datos"]] ==
                      sorted((f["tasa_pct"] or 0 for f in r.json["datos"]), reverse=True))])
    c.caso("listado 200 XML", "GET", f"{API}?por_pagina=2", rol="analista", accept="application/xml",
           objetivo="El listado responde XML (RF-31).",
           verifica=[("es XML", lambda r: r.tipo.startswith("application/xml")), ("raiz proveedores", lambda r: "<proveedores>" in r.texto)])
    c.caso("listado 200 con busqueda por nombre", "GET", f"{API}?q={{busqueda}}", rol="supervisor",
           objetivo="Busca por nombre sin distinguir mayusculas.",
           verifica=[("encuentra al proveedor", lambda r: c.ctx["prov"] in [f["id"] for f in r.json["datos"]])])
    c.caso("listado 400 fecha invalida", "GET", f"{API}?desde=ayer", rol="analista", espera=400,
           objetivo="Una fecha mal formada se rechaza.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("detalle 200 del proveedor", "GET", f"{API}/{{prov}}", rol="analista",
           objetivo="Proveedor con sus indicadores, lo que surte y sus reclamaciones recientes (RF-24).",
           verifica=[("es el proveedor pedido", lambda r: r.json["id"] == c.ctx["prov"]),
                     ("trae indicadores", lambda r: r.json["indicadores"]["unidades_vendidas"] > 0),
                     ("trae productos", lambda r: len(r.json["productos"]) >= 1),
                     ("recuerda que no determina responsabilidad", lambda r: "RN-09" in r.json["aviso"])])
    c.caso("detalle 404", "GET", f"{API}/999999", rol="analista", espera=404, objetivo="Un proveedor inexistente responde 404.",
           verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])
    c.caso("productos 200", "GET", f"{API}/{{prov}}/productos", rol="analista",
           objetivo="Productos que surte, como proveedor principal o por lotes.",
           verifica=[("total coincide con la lista", lambda r: r.json["total"] == len(r.json["datos"]) >= 1)])
    c.caso("productos 404", "GET", f"{API}/999999/productos", rol="analista", espera=404, objetivo="Un proveedor inexistente responde 404.",
           verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])
    sql_vendidas = ("SELECT COALESCE(SUM(vd.cantidad), 0) FROM venta_detalle vd JOIN ventas v ON v.id = vd.venta_id "
                    "JOIN lotes l ON l.id = vd.lote_id WHERE v.eliminado_en IS NULL AND l.proveedor_id = {prov}")
    sql_devueltas = ("SELECT COALESCE(SUM(d.cantidad_devuelta), 0) FROM devoluciones d JOIN venta_detalle vd ON vd.id = d.venta_detalle_id "
                     "JOIN ventas v ON v.id = vd.venta_id JOIN lotes l ON l.id = vd.lote_id "
                     "WHERE d.eliminado_en IS NULL AND v.eliminado_en IS NULL AND l.proveedor_id = {prov}")
    c.caso("indicadores 200: coinciden con la base", "GET", f"{API}/{{prov}}/indicadores", rol="analista",
           objetivo="La tasa es unidades devueltas entre vendidas; se contrasta con consultas independientes (RF-26).",
           verifica=[("vendidas = la base", lambda r: r.json["unidades_vendidas"] == int(c.valor(sql_vendidas))),
                     ("devueltas = la base", lambda r: r.json["unidades_devueltas"] == int(c.valor(sql_devueltas))),
                     ("tasa = devueltas / vendidas", lambda r: r.json["tasa_pct"] == round(r.json["unidades_devueltas"] * 100.0 / r.json["unidades_vendidas"], 2)),
                     ("semaforo conocido", lambda r: r.json["semaforo"] in SEMAFOROS),
                     ("declara la muestra minima", lambda r: r.json["muestra_minima_unidades"] == 20)],
           efecto=[("unidades vendidas y devueltas calculadas aparte", "SELECT (" + sql_vendidas + ") AS vendidas, (" + sql_devueltas + ") AS devueltas")])
    c.caso("indicadores 200 en un rango de fechas", "GET", f"{API}/{{prov}}/indicadores?desde=2026-01-01&hasta={date.today().isoformat()}",
           rol="supervisor", objetivo="Los indicadores se pueden acotar por periodo.",
           verifica=[("trae la tasa", lambda r: "tasa_pct" in r.json)])
    c.caso("indicadores 400 fecha invalida", "GET", f"{API}/{{prov}}/indicadores?desde=2026-13-01", rol="analista", espera=400,
           objetivo="Una fecha imposible se rechaza.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("indicadores 404", "GET", f"{API}/999999/indicadores", rol="analista", espera=404, objetivo="Un proveedor inexistente responde 404.",
           verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])

    # ---------------------------------------------------------------- alta de reclamaciones
    c.caso("reclamacion 201 de un lote y dos devoluciones", "POST", f"{API}/reclamaciones", rol="analista", espera=201,
           json_cuerpo={"proveedor_id": c.ctx["prov"], "lote_id": c.ctx["lote"], "devolucion_ids": [c.ctx["dev1"], c.ctx["dev2"]],
                        "asunto": "Evidencia P4: leche tibia en el lote de la demo",
                        "descripcion": "Varias devoluciones del mismo lote llegaron sin la cadena de frio",
                        "monto_reclamado": "1500.00", "fecha_limite_respuesta": limite},
           objetivo="Una reclamacion formal con folio, respaldada por devoluciones del propio lote (RF-24).",
           guarda={"rec1": lambda r: r.json["id"]},
           verifica=[("folio RCL-AAAA-####", lambda r: r.json["folio"].startswith("RCL-")), ("nace abierta", lambda r: r.json["estado"] == "abierta"),
                     ("trae Location", lambda r: "location" in r.cabeceras)],
           efecto=[("la reclamacion, sus devoluciones y su primer evento", "SELECT r.folio, r.estado, r.monto_reclamado, count(rd.*) AS devoluciones, "
                    "(SELECT count(*) FROM seguimiento_reclamacion s WHERE s.reclamacion_id = r.id) AS eventos "
                    "FROM reclamaciones_proveedor r LEFT JOIN reclamacion_devoluciones rd ON rd.reclamacion_id = r.id "
                    "WHERE r.id = {rec1} GROUP BY r.id")])
    c.caso("reclamacion 201 XML", "POST", f"{API}/reclamaciones", rol="supervisor", espera=201, accept="application/xml",
           xml=("<reclamacion><proveedor_id>%d</proveedor_id><asunto>Evidencia P4: reclamacion enviada por XML</asunto>"
                "<descripcion>Reclamacion de una sola devolucion, por contrato XML</descripcion>"
                "<devolucion_ids><item>%d</item></devolucion_ids></reclamacion>" % (c.ctx["prov"], c.ctx["dev3"])),
           objetivo="La misma alta en XML, validada contra su XSD (RF-31).",
           guarda={"rec2": lambda r: int(r.texto.split("<id>")[1].split("</id>")[0])},
           verifica=[("trae folio", lambda r: "<folio>RCL-" in r.texto)])
    c.caso("reclamacion 400 sin lote ni devoluciones", "POST", f"{API}/reclamaciones", rol="analista", espera=400,
           json_cuerpo={"proveedor_id": c.ctx["prov"], "asunto": "Evidencia P4: sin origen", "descripcion": "No indica de donde sale el reclamo"},
           objetivo="Toda reclamacion exige un lote o al menos una devolucion que la respalde.",
           verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("reclamacion 400 XML que no cumple el XSD", "POST", f"{API}/reclamaciones", rol="analista", espera=400, accept="application/xml",
           xml="<reclamacion><asunto>Sin proveedor</asunto></reclamacion>", objetivo="Un XML que no cumple el contrato se rechaza (RF-31).",
           verifica=[("tipo xml_no_cumple_xsd", lambda r: "xml_no_cumple_xsd" in r.texto)])
    c.caso("reclamacion 409 lote de otro proveedor", "POST", f"{API}/reclamaciones", rol="analista", espera=409,
           json_cuerpo={"proveedor_id": c.ctx["otro"], "lote_id": c.ctx["lote"], "asunto": "Evidencia P4: lote ajeno",
                        "descripcion": "Se reclama a quien no surtio el lote"},
           objetivo="No se le reclama a un proveedor un lote que no surtio.",
           verifica=[("tipo lote_ajeno", lambda r: tipo_error(r) == "lote_ajeno")])
    c.caso("reclamacion 409 devolucion de otro proveedor", "POST", f"{API}/reclamaciones", rol="analista", espera=409,
           json_cuerpo={"proveedor_id": c.ctx["otro"], "devolucion_ids": [c.ctx["dev1"]], "asunto": "Evidencia P4: devolucion ajena",
                        "descripcion": "La devolucion es de un lote de otro proveedor"},
           objetivo="Las devoluciones que respaldan el reclamo deben ser de lotes del proveedor.",
           verifica=[("tipo devolucion_ajena", lambda r: tipo_error(r) == "devolucion_ajena")])
    c.caso("reclamacion 404 devolucion inexistente", "POST", f"{API}/reclamaciones", rol="analista", espera=404,
           json_cuerpo={"proveedor_id": c.ctx["prov"], "devolucion_ids": [99999999], "asunto": "Evidencia P4: devolucion inexistente",
                        "descripcion": "La devolucion indicada no existe"},
           objetivo="No se reclama con una devolucion que no existe.", verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])
    c.caso("reclamacion 409 devolucion ya reclamada", "POST", f"{API}/reclamaciones", rol="analista", espera=409,
           json_cuerpo={"proveedor_id": c.ctx["prov"], "devolucion_ids": [c.ctx["dev1"]], "asunto": "Evidencia P4: devolucion repetida",
                        "descripcion": "La devolucion ya esta en una reclamacion abierta"},
           objetivo="Una devolucion no puede estar en dos reclamaciones abiertas.",
           verifica=[("tipo devolucion_reclamada", lambda r: tipo_error(r) == "devolucion_reclamada"),
                     ("no se creo una tercera reclamacion", lambda r: c.valor(
                         "SELECT count(*) FROM reclamaciones_proveedor WHERE asunto LIKE 'Evidencia P4%'") == "2")],
           efecto=[("solo existen las 2 reclamaciones creadas antes", "SELECT count(*) AS reclamaciones_de_prueba FROM reclamaciones_proveedor WHERE asunto LIKE 'Evidencia P4%'")])
    c.caso("reclamacion 403 cliente", "POST", f"{API}/reclamaciones", rol="cliente", espera=403,
           json_cuerpo={"proveedor_id": c.ctx["prov"], "lote_id": c.ctx["lote"], "asunto": "Evidencia P4: cliente",
                        "descripcion": "Un cliente no crea reclamaciones a proveedores"},
           objetivo="Crear reclamaciones es de Administrador, Analista y Supervisor (RN-13).",
           verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])

    # ---------------------------------------------------------------- consulta de reclamaciones
    c.caso("reclamaciones 200 filtradas", "GET", f"{API}/reclamaciones?proveedor_id={{prov}}&estado=abierta", rol="analista",
           objetivo="Listado de reclamaciones por proveedor y estado.",
           verifica=[("incluye la recien creada", lambda r: c.ctx["rec1"] in [x["id"] for x in r.json["datos"]]),
                     ("todas abiertas", lambda r: {x["estado"] for x in r.json["datos"]} == {"abierta"})])
    c.caso("reclamaciones 400 estado desconocido", "GET", f"{API}/reclamaciones?estado=inventado", rol="analista", espera=400,
           objetivo="Un estado que no existe se rechaza.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("reclamaciones 200 vencidas", "GET", f"{API}/reclamaciones?vencidas=true", rol="supervisor",
           objetivo="Las enviadas o en analisis cuya fecha limite ya paso.", verifica=[("trae paginacion", lambda r: "paginacion" in r.json)])
    c.caso("reclamacion 200: detalle con su linea de tiempo", "GET", f"{API}/reclamaciones/{{rec1}}", rol="analista",
           objetivo="La reclamacion con sus devoluciones y su historial (RN-12).",
           verifica=[("dos devoluciones", lambda r: len(r.json["devoluciones"]) == 2),
                     ("un evento: abierta", lambda r: [s["estado_nuevo"] for s in r.json["seguimiento"]] == ["abierta"])])
    c.caso("reclamacion 404", "GET", f"{API}/reclamaciones/999999", rol="analista", espera=404, objetivo="Una reclamacion inexistente responde 404.",
           verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])

    # ---------------------------------------------------------------- seguimiento: estados controlados
    seg = f"{API}/reclamaciones/{{rec1}}/seguimiento"
    c.caso("seguimiento 409: no se salta un paso", "POST", seg, rol="analista", espera=409, json_cuerpo={"estado": "respondida"},
           objetivo="De abierta no se pasa a respondida: antes hay que enviarla.",
           verifica=[("tipo transicion_invalida", lambda r: tipo_error(r) == "transicion_invalida")])
    c.caso("seguimiento 400 campo no permitido", "POST", f"{API}/reclamaciones/{{rec2}}/seguimiento", rol="analista", espera=400,
           json_cuerpo={"estado": "enviada", "usuario_id": 1}, objetivo="Solo se aceptan los campos del contrato.",
           verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("seguimiento 403 cliente", "POST", seg, rol="cliente", espera=403, json_cuerpo={"estado": "enviada"},
           objetivo="Dar seguimiento es de Administrador, Analista y Supervisor (RN-13).",
           verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])
    c.caso("seguimiento 404", "POST", f"{API}/reclamaciones/999999/seguimiento", rol="analista", espera=404, json_cuerpo={"estado": "enviada"},
           objetivo="Una reclamacion inexistente responde 404.", verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])
    c.caso("seguimiento 200: enviada", "POST", seg, rol="analista", json_cuerpo={"estado": "enviada", "comentario": "Se envia al proveedor por correo"},
           objetivo="Primer paso del ciclo: abierta a enviada.", verifica=[("estado enviada", lambda r: r.json["estado"] == "enviada")])
    c.caso("seguimiento 200: respondida", "POST", seg, rol="analista", json_cuerpo={"estado": "respondida", "comentario": "Respondio ofreciendo nota de credito"},
           objetivo="El proveedor respondio.", verifica=[("estado respondida", lambda r: r.json["estado"] == "respondida")])
    c.caso("seguimiento 400 cerrar sin comentario", "POST", seg, rol="analista", espera=400,
           json_cuerpo={"estado": "cerrada", "resolucion": "parcial", "monto_recuperado": "600.00"},
           objetivo="Cerrar exige explicar como termino.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("seguimiento 409 no se recupera mas de lo reclamado", "POST", seg, rol="analista", espera=409,
           json_cuerpo={"estado": "cerrada", "resolucion": "aceptada", "monto_recuperado": "1500.01", "comentario": "Intento de recuperar de mas"},
           objetivo="El monto recuperado no puede superar el reclamado (1500.00).",
           verifica=[("tipo monto_excedido", lambda r: tipo_error(r) == "monto_excedido")])
    c.caso("seguimiento 200: cierre parcial", "POST", seg, rol="analista",
           json_cuerpo={"estado": "cerrada", "resolucion": "parcial", "monto_recuperado": "600.00", "comentario": "Nota de credito por una parte del lote"},
           objetivo="Se cierra con resolucion y monto recuperado; el cierre queda fechado (RN-12).",
           verifica=[("estado cerrada", lambda r: r.json["estado"] == "cerrada"), ("resolucion parcial", lambda r: r.json["resolucion"] == "parcial"),
                     ("recupero 600", lambda r: float(r.json["monto_recuperado"]) == 600.0)],
           efecto=[("la reclamacion cerrada", "SELECT estado, resolucion, monto_reclamado, monto_recuperado, fecha_cierre IS NOT NULL AS tiene_fecha_cierre "
                    "FROM reclamaciones_proveedor WHERE id = {rec1}"),
                   ("su linea de tiempo", "SELECT estado_anterior, estado_nuevo FROM seguimiento_reclamacion WHERE reclamacion_id = {rec1} ORDER BY id")])
    c.caso("seguimiento 409: cerrada es definitiva", "POST", seg, rol="analista", espera=409, json_cuerpo={"estado": "enviada"},
           objetivo="Una reclamacion cerrada no vuelve a abrirse.", verifica=[("tipo transicion_invalida", lambda r: tipo_error(r) == "transicion_invalida")])
    seg2 = f"{API}/reclamaciones/{{rec2}}/seguimiento"
    c.caso("seguimiento 200: enviada (segunda reclamacion)", "POST", seg2, rol="supervisor", json_cuerpo={"estado": "enviada"},
           objetivo="La segunda reclamacion se envia, pero el proveedor no responde.", verifica=[("estado enviada", lambda r: r.json["estado"] == "enviada")])
    c.caso("seguimiento 409: no se acepta lo que nadie respondio", "POST", seg2, rol="supervisor", espera=409,
           json_cuerpo={"estado": "cerrada", "resolucion": "aceptada", "monto_recuperado": "10", "comentario": "Intento sin respuesta del proveedor"},
           objetivo="Aceptar, aceptar parcialmente o rechazar exige que el proveedor haya respondido.",
           verifica=[("tipo sin_respuesta", lambda r: tipo_error(r) == "sin_respuesta")])
    c.caso("seguimiento 200: retirada sin respuesta", "POST", seg2, rol="supervisor",
           json_cuerpo={"estado": "cerrada", "resolucion": "retirada", "comentario": "Ya no procede la reclamacion"},
           objetivo="Retirar una reclamacion si se puede en cualquier momento; no recupera nada.",
           verifica=[("resolucion retirada", lambda r: r.json["resolucion"] == "retirada"),
                     ("no recupera nada", lambda r: float(r.json["monto_recuperado"]) == 0.0)],
           efecto=[("la reclamacion retirada", "SELECT estado, resolucion, monto_recuperado FROM reclamaciones_proveedor WHERE id = {rec2}")])
    c.caso("indicadores 200 tras las reclamaciones", "GET", f"{API}/{{prov}}/indicadores", rol="analista",
           objetivo="El proveedor ya cuenta sus reclamaciones y lo recuperado.",
           verifica=[("2 reclamaciones al menos", lambda r: r.json["reclamaciones"] >= 2),
                     ("recupero al menos 600", lambda r: float(r.json["monto_recuperado"]) >= 600.0)])
