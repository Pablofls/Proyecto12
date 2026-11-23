"""Casos de evidencia de la trazabilidad de ventas-catalogos (8006): RF-05, RF-23, RF-24, RN-09, RN-10, RN-13, RNF-11.

Lectura de lotes, series y tasas con el lote de la demo, y el alta y vinculacion de series (lo unico que
escribe). Las series de la corrida llevan el prefijo "EVID-P4-" y se borran al final; la bitacora se conserva.
"""
SERVICIO = "ventas-catalogos (trazabilidad)"
SIGLA = "TRZ"
TITULO = "Lotes, series y trazabilidad"
PUERTO = 8006
ARCHIVO = "ventas_catalogos_trazabilidad"

API = "/api/v1/trazabilidad"
LOTE = "L-2026-PROB-01"
PREFIJO = "EVID-P4-"
DIMENSIONES = ("proveedor", "tienda", "producto", "lote", "ruta")


def tipo_error(r):
    return r.json["error"]["tipo"]


def ordenado_por_tasa(filas):
    tasas = [f["tasa_pct"] if f["tasa_pct"] is not None else -1 for f in filas]
    return tasas == sorted(tasas, reverse=True)


def ejecutar(c):
    c.ctx["lote"] = int(c.valor(f"SELECT id FROM lotes WHERE numero_lote = '{LOTE}'"))
    c.ctx["prov"] = int(c.valor("SELECT proveedor_id FROM lotes WHERE id = {lote}"))
    # Las lineas del lote de la demo ya tienen todas sus series (las carga seed_demo); las nuevas se ligan en un lote con cupo.
    cupo = "vd.cantidad - (SELECT count(*) FROM series_producto s WHERE s.venta_detalle_id = vd.id)"
    c.ctx["libre1"] = int(c.valor(f"SELECT vd.id FROM venta_detalle vd WHERE {cupo} >= 3 AND EXISTS (SELECT 1 FROM devoluciones d "
                                  "WHERE d.venta_detalle_id = vd.id AND d.eliminado_en IS NULL) ORDER BY vd.id LIMIT 1"))
    c.ctx["lote_v"] = int(c.valor("SELECT lote_id FROM venta_detalle WHERE id = {libre1}"))
    c.ctx["numero_v"] = c.valor("SELECT numero_lote FROM lotes WHERE id = {lote_v}")
    c.ctx["libre2"] = int(c.valor(f"SELECT vd.id FROM venta_detalle vd WHERE vd.lote_id = {{lote_v}} AND vd.id <> {{libre1}} AND {cupo} >= 1 ORDER BY vd.id LIMIT 1"))
    c.ctx["otro_lote"] = int(c.valor("SELECT id FROM lotes WHERE id NOT IN ({lote}, {lote_v}) AND activo ORDER BY id LIMIT 1"))
    c.ctx["det1"] = int(c.valor("SELECT d.venta_detalle_id FROM devoluciones d JOIN venta_detalle vd ON vd.id = d.venta_detalle_id "
                                "WHERE vd.lote_id = {lote} AND d.eliminado_en IS NULL ORDER BY d.id LIMIT 1"))
    c.ctx["det_otro"] = int(c.valor("SELECT id FROM venta_detalle WHERE lote_id <> {lote_v} ORDER BY id LIMIT 1"))
    c.limpieza += [f"DELETE FROM series_producto WHERE numero_serie LIKE '{PREFIJO}%'"]
    vendidas = "SELECT COALESCE(SUM(vd.cantidad), 0) FROM venta_detalle vd JOIN ventas v ON v.id = vd.venta_id WHERE vd.lote_id = {lote} AND v.eliminado_en IS NULL"
    devueltas = ("SELECT COALESCE(SUM(d.cantidad_devuelta), 0) FROM devoluciones d JOIN venta_detalle vd ON vd.id = d.venta_detalle_id "
                 "WHERE vd.lote_id = {lote} AND d.eliminado_en IS NULL")

    # ---------------------------------------------------------------- salud, contratos y Swagger
    c.caso("salud 200 JSON", "GET", "/health", objetivo="El servicio informa su estado y el de PostgreSQL y Redis (RF-32).",
           verifica=[("estado ok", lambda r: r.json["estado"] == "ok"), ("PostgreSQL ok", lambda r: r.json["dependencias"]["postgresql"]["ok"] is True)])
    c.caso("Swagger: especificacion OpenAPI", "GET", "/openapi.json", objetivo="La especificacion incluye la trazabilidad.",
           verifica=[("incluye lotes", lambda r: f"{API}/lotes/{{lote_id}}" in r.json["paths"] or any(p.startswith(f"{API}/lotes/") for p in r.json["paths"])),
                     ("incluye tasas", lambda r: f"{API}/tasas" in r.json["paths"])])
    c.caso("contrato XSD de series publicado", "GET", "/contratos/series.xsd", accept="application/xml",
           objetivo="El contrato XML del alta de series se publica (RF-31).", verifica=[("es un esquema XSD", lambda r: "xs:schema" in r.texto and "lote_series" in r.texto)])

    # ---------------------------------------------------------------- autenticacion y permisos
    c.caso("sin token: 401", "GET", f"{API}/lotes", espera=401, objetivo="Un endpoint protegido exige JWT (RNF-09).",
           verifica=[("tipo no_autenticado", lambda r: tipo_error(r) == "no_autenticado")])
    c.caso("cliente: 403", "GET", f"{API}/lotes", rol="cliente", espera=403,
           objetivo="Los clientes no consultan trazabilidad: expone proveedores y costos internos (RN-13, RN-15).",
           verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])
    c.caso("encargado de reembolsos: 403", "GET", f"{API}/tasas", rol="reembolsos", espera=403,
           objetivo="Tampoco es un rol de trazabilidad.", verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])

    # ---------------------------------------------------------------- lotes
    c.caso("lotes 200: el lote problematico sube al inicio", "GET", f"{API}/lotes?por_pagina=5", rol="analista",
           objetivo="Lotes ordenados por tasa de devolucion, para encontrar los de problemas recurrentes (RF-23).",
           verifica=[("ordenado por tasa", lambda r: ordenado_por_tasa(r.json["datos"])),
                     ("la tasa es devueltas/vendidas", lambda r: all(f["tasa_pct"] is None or f["tasa_pct"] == round(f["unidades_devueltas"] * 100.0 / f["unidades_vendidas"], 2)
                                                                     for f in r.json["datos"]))])
    c.caso("lotes 200 XML", "GET", f"{API}/lotes?por_pagina=2", rol="supervisor", accept="application/xml", objetivo="El listado responde XML (RF-31).",
           verifica=[("es XML", lambda r: r.tipo.startswith("application/xml")), ("raiz lotes", lambda r: "<lotes>" in r.texto)])
    c.caso("lotes 200 busqueda por numero de lote", "GET", f"{API}/lotes?q={LOTE}", rol="inspector",
           objetivo="Busca por numero de lote o por producto (lo consulta tambien el Inspector).",
           verifica=[("encuentra el lote", lambda r: c.ctx["lote"] in [f["id"] for f in r.json["datos"]])])
    c.caso("lotes 200 solo con devoluciones y de un proveedor", "GET", f"{API}/lotes?solo_con_devoluciones=true&proveedor_id={{prov}}", rol="analista",
           objetivo="Filtros combinados.", verifica=[("todos con devoluciones", lambda r: all(f["devoluciones"] > 0 for f in r.json["datos"])),
                                                    ("todos del proveedor", lambda r: all(f["proveedor_id"] == c.ctx["prov"] for f in r.json["datos"]))])
    c.caso("lotes 400 proveedor_id no numerico", "GET", f"{API}/lotes?proveedor_id=abc", rol="analista", espera=400,
           objetivo="El filtro numerico se valida (RNF-11).", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("lotes 400 busqueda demasiado larga", "GET", f"{API}/lotes?q={'x' * 101}", rol="analista", espera=400,
           objetivo="La busqueda tiene un maximo de 100 caracteres.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("lotes 200 con intento de inyeccion SQL", "GET", f"{API}/lotes?q=%27%3B%20DROP%20TABLE%20lotes%3B--", rol="analista",
           objetivo="Una busqueda con SQL se trata como texto (parametros ligados, RNF-11): no hay resultados y la tabla sigue ahi.",
           verifica=[("sin resultados", lambda r: r.json["paginacion"]["total"] == 0)],
           efecto=[("la tabla de lotes sigue intacta", "SELECT count(*) AS lotes FROM lotes")])
    c.caso("trazabilidad de un lote 200", "GET", f"{API}/lotes/{{lote}}", rol="analista",
           objetivo="Todo lo de un lote: resumen de tasas, tiendas, series y el recorrido de cada devolucion (recoleccion, ruta, inspeccion, disposicion).",
           verifica=[("vendidas = la base", lambda r: r.json["resumen"]["unidades_vendidas"] == int(c.valor(vendidas))),
                     ("devueltas = la base", lambda r: r.json["resumen"]["unidades_devueltas"] == int(c.valor(devueltas))),
                     ("supera el doble del promedio", lambda r: r.json["resumen"]["veces_promedio"] >= 2),
                     ("trae tiendas", lambda r: len(r.json["tiendas"]) >= 1),
                     ("cada devolucion trae su recorrido", lambda r: len(r.json["devoluciones"]) >= 1 and all("recorrido" in d for d in r.json["devoluciones"])),
                     ("recuerda que no confirma causalidad", lambda r: "RN-09" in r.json["aviso"])],
           efecto=[("unidades vendidas y devueltas del lote, calculadas aparte", f"SELECT ({vendidas}) AS vendidas, ({devueltas}) AS devueltas")])
    c.caso("trazabilidad de un lote 200 XML", "GET", f"{API}/lotes/{{lote}}", rol="inspector", accept="application/xml", objetivo="La misma consulta en XML.",
           verifica=[("es XML", lambda r: r.tipo.startswith("application/xml")), ("raiz lote", lambda r: "<lote>" in r.texto)])
    c.caso("trazabilidad de un lote 404", "GET", f"{API}/lotes/999999", rol="analista", espera=404, objetivo="Un lote inexistente responde 404.",
           verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])

    # ---------------------------------------------------------------- alta de series
    c.caso("series 403 analista", "POST", f"{API}/lotes/{{lote_v}}/series", rol="analista", espera=403,
           json_cuerpo={"series": [PREFIJO + "X"]}, objetivo="Dar de alta series es del Administrador.", verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])
    c.caso("series 201 alta de tres", "POST", f"{API}/lotes/{{lote_v}}/series", rol="admin", espera=201,
           json_cuerpo={"series": [PREFIJO + "001", PREFIJO + "002", PREFIJO + "003"]},
           objetivo="Alta de numeros de serie de un lote (RF-05).", verifica=[("3 registradas", lambda r: r.json["registradas"] == 3)],
           efecto=[("las series quedan sin venta", f"SELECT numero_serie, lote_id, venta_detalle_id FROM series_producto WHERE numero_serie LIKE '{PREFIJO}%' ORDER BY 1"),
                   ("la alta queda en la bitacora", "SELECT accion, entidad, detalle FROM bitacora WHERE accion = 'alta_series' ORDER BY id DESC LIMIT 1")])
    c.caso("series 201 idempotente", "POST", f"{API}/lotes/{{lote_v}}/series", rol="admin", espera=201,
           json_cuerpo={"series": [PREFIJO + "001", PREFIJO + "002", PREFIJO + "003"]},
           objetivo="Repetir el envio no duplica ni falla: 0 nuevas, 3 que ya existian.",
           verifica=[("0 registradas", lambda r: r.json["registradas"] == 0), ("3 ya existian", lambda r: r.json["ya_existian"] == 3)])
    c.caso("series 201 XML", "POST", f"{API}/lotes/{{lote_v}}/series", rol="admin", espera=201, accept="application/xml",
           xml="<lote_series><series><item>%s004</item></series></lote_series>" % PREFIJO,
           objetivo="La misma alta en XML, validada contra su XSD (RF-31).", verifica=[("1 registrada", lambda r: "<registradas>1</registradas>" in r.texto)])
    c.caso("series 400 formato invalido", "POST", f"{API}/lotes/{{lote_v}}/series", rol="admin", espera=400,
           json_cuerpo={"series": ["serie con espacios", PREFIJO + "OK"]}, objetivo="Cada serie son 1 a 60 caracteres: letras, numeros, punto, guion.",
           verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion"), ("senala la posicion", lambda r: r.json["error"]["detalles"][0]["campo"] == "series[0]")])
    c.caso("series 400 repetidas en la lista", "POST", f"{API}/lotes/{{lote_v}}/series", rol="admin", espera=400,
           json_cuerpo={"series": [PREFIJO + "R", PREFIJO + "R"]}, objetivo="Una lista con series repetidas se rechaza.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("series 404 lote inexistente", "POST", f"{API}/lotes/999999/series", rol="admin", espera=404,
           json_cuerpo={"series": [PREFIJO + "Z"]}, objetivo="No se dan de alta series en un lote que no existe.", verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])
    c.caso("series 201 en el lote de la demo (para la linea saturada)", "POST", f"{API}/lotes/{{lote}}/series", rol="admin", espera=201,
           json_cuerpo={"series": [PREFIJO + "SAT"]}, objetivo="Una serie del lote problematico, cuyas lineas de venta ya tienen todas sus series.",
           verifica=[("1 registrada", lambda r: r.json["registradas"] == 1)])
    c.caso("series 201 en otro lote (prepara el conflicto)", "POST", f"{API}/lotes/{{otro_lote}}/series", rol="admin", espera=201,
           json_cuerpo={"series": [PREFIJO + "AJENA"]}, objetivo="Una serie de otro lote, para probar que no se puede reasignar.", verifica=[("1 registrada", lambda r: r.json["registradas"] == 1)])
    c.caso("series 409 ya pertenece a otro lote", "POST", f"{API}/lotes/{{lote_v}}/series", rol="admin", espera=409,
           json_cuerpo={"series": [PREFIJO + "AJENA"]}, objetivo="Un numero de serie es unico: no se mueve de un lote a otro (RN-10).",
           verifica=[("tipo serie_duplicada", lambda r: tipo_error(r) == "serie_duplicada")])

    # ---------------------------------------------------------------- consulta y vinculacion de series
    c.caso("serie 200 en almacen", "GET", f"{API}/series/{PREFIJO}001", rol="analista",
           objetivo="Una serie sin venta esta en almacen: su recorrido termina en el lote.",
           verifica=[("estado en_almacen", lambda r: r.json["estado"] == "en_almacen"), ("sin venta", lambda r: r.json["venta"] is None),
                     ("trae lote y proveedor", lambda r: r.json["numero_lote"] == c.ctx["numero_v"] and r.json["proveedor"])])
    c.caso("serie 400 formato invalido", "GET", f"{API}/series/serie%20invalida", rol="analista", espera=400,
           objetivo="El numero de serie se valida antes de consultar (RNF-11).", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("serie 404 inexistente", "GET", f"{API}/series/NO-EXISTE-999", rol="analista", espera=404, objetivo="Una serie inexistente responde 404.",
           verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])
    c.caso("vincular serie 403 analista", "PATCH", f"{API}/series/{PREFIJO}001/venta", rol="analista", espera=403,
           json_cuerpo={"venta_detalle_id": c.ctx["libre1"]}, objetivo="Ligar una serie a una venta es de Administrador y Operador de Almacen.",
           verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])
    c.caso("vincular serie 400 id invalido", "PATCH", f"{API}/series/{PREFIJO}001/venta", rol="almacen", espera=400,
           json_cuerpo={"venta_detalle_id": "uno"}, objetivo="El id de la linea es un entero positivo.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("vincular serie 404 linea inexistente", "PATCH", f"{API}/series/{PREFIJO}001/venta", rol="almacen", espera=404,
           json_cuerpo={"venta_detalle_id": 999999}, objetivo="La linea de venta debe existir.", verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])
    c.caso("vincular serie 409 linea de otro lote", "PATCH", f"{API}/series/{PREFIJO}002/venta", rol="almacen", espera=409,
           json_cuerpo={"venta_detalle_id": c.ctx["det_otro"]}, objetivo="Una serie solo se liga a una venta de su propio lote (RN-10).",
           verifica=[("tipo lote_distinto", lambda r: tipo_error(r) == "lote_distinto")])
    c.caso("vincular serie 409 linea sin cupo", "PATCH", f"{API}/series/{PREFIJO}SAT/venta", rol="almacen", espera=409,
           json_cuerpo={"venta_detalle_id": c.ctx["det1"]}, objetivo="No hay mas series que unidades vendidas en una linea (RN-10): esa linea ya tiene todas las suyas.",
           verifica=[("tipo sin_unidades", lambda r: tipo_error(r) == "sin_unidades")])
    c.caso("vincular serie 200 por el Operador de Almacen", "PATCH", f"{API}/series/{PREFIJO}001/venta", rol="almacen",
           json_cuerpo={"venta_detalle_id": c.ctx["libre1"]}, objetivo="La serie sale en una venta concreta; de ahi se llega a la tienda y a la devolucion.",
           verifica=[("queda ligada", lambda r: r.json["venta_detalle_id"] == c.ctx["libre1"])],
           efecto=[("la serie ligada", f"SELECT numero_serie, venta_detalle_id FROM series_producto WHERE numero_serie = '{PREFIJO}001'"),
                   ("la vinculacion en la bitacora", "SELECT accion, entidad, detalle FROM bitacora WHERE accion = 'serie_vendida' ORDER BY id DESC LIMIT 1")])
    c.caso("vincular serie 200 idempotente", "PATCH", f"{API}/series/{PREFIJO}001/venta", rol="admin",
           json_cuerpo={"venta_detalle_id": c.ctx["libre1"]}, objetivo="Repetir la misma vinculacion no cambia nada.", verifica=[("sin cambios", lambda r: r.json["sin_cambios"] is True)])
    c.caso("vincular serie 200 XML", "PATCH", f"{API}/series/{PREFIJO}003/venta", rol="admin", accept="application/xml",
           xml="<serie_venta><venta_detalle_id>%d</venta_detalle_id></serie_venta>" % c.ctx["libre1"],
           objetivo="La misma vinculacion en XML.", verifica=[("es XML", lambda r: r.tipo.startswith("application/xml"))])
    c.caso("vincular serie 409 ya ligada a otra venta", "PATCH", f"{API}/series/{PREFIJO}001/venta", rol="admin", espera=409,
           json_cuerpo={"venta_detalle_id": c.ctx["libre2"]}, objetivo="Una serie vendida no se reasigna a otra venta.",
           verifica=[("tipo serie_vendida", lambda r: tipo_error(r) == "serie_vendida")])
    c.caso("serie 200 devuelta: recorrido completo", "GET", f"{API}/series/{PREFIJO}001", rol="inspector",
           objetivo="Del numero de serie a la tienda, la venta y todo el recorrido de su devolucion: la trazabilidad de punta a punta (RF-05).",
           verifica=[("estado devuelta", lambda r: r.json["estado"] == "devuelta"), ("trae la venta y la tienda", lambda r: r.json["venta"]["tienda"] and r.json["venta"]["folio_venta"]),
                     ("trae el recorrido de la devolucion", lambda r: len(r.json["devoluciones"]) >= 1 and "recorrido" in r.json["devoluciones"][0])])
    c.caso("serie 200 de otra serie ligada", "GET", f"{API}/series/{PREFIJO}003", rol="analista",
           objetivo="Una serie ligada a una venta sin devoluciones esta vendida (o devuelta si esa linea ya tuvo una).",
           verifica=[("estado vendida o devuelta", lambda r: r.json["estado"] in ("vendida", "devuelta")), ("trae la venta", lambda r: r.json["venta"] is not None)])

    # ---------------------------------------------------------------- tasas
    for por in DIMENSIONES:
        c.caso(f"tasas 200 por {por}", "GET", f"{API}/tasas?por={por}", rol="analista",
               objetivo=("Tasa = unidades devueltas entre vendidas, base del analisis causal (RF-23, RF-24)." if por != "ruta" else
                         "Por ruta se mide el dano: inspecciones no aptas entre inspeccionadas, porque no existe 'vendido por ruta'."),
               verifica=[("ordenado por tasa", lambda r: ordenado_por_tasa(r.json["datos"])),
                         ("trae promedio y advertencia", lambda r: "tasa_promedio_pct" in r.json and "no confirman causalidad" in r.json["interpretacion"])])
    c.caso("tasas 200: el lote problematico contra la base", "GET", f"{API}/tasas?por=lote", rol="analista",
           objetivo="La fila del lote de la demo coincide con lo que dice la base.",
           verifica=[("devueltas = la base", lambda r: next(f for f in r.json["datos"] if f["id"] == c.ctx["lote"])["unidades_devueltas"] == int(c.valor(devueltas))),
                     ("al menos el doble del promedio", lambda r: next(f for f in r.json["datos"] if f["id"] == c.ctx["lote"])["veces_promedio"] >= 2)])
    c.caso("tasas 200 en un periodo", "GET", f"{API}/tasas?por=proveedor&desde=2026-01-01&hasta=2026-12-31", rol="supervisor",
           objetivo="Los indicadores se acotan por periodo.", verifica=[("trae datos", lambda r: "datos" in r.json)])
    c.caso("tasas 200 XML", "GET", f"{API}/tasas?por=tienda", rol="analista", accept="application/xml", objetivo="Las tasas responden XML (RF-31).",
           verifica=[("es XML", lambda r: r.tipo.startswith("application/xml")), ("raiz tasas", lambda r: "<tasas>" in r.texto)])
    c.caso("tasas 400 dimension invalida", "GET", f"{API}/tasas?por=planeta", rol="analista", espera=400, objetivo="La dimension sale de una lista cerrada (RNF-11).",
           verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("tasas 400 fecha invalida", "GET", f"{API}/tasas?desde=ayer", rol="analista", espera=400, objetivo="Las fechas son AAAA-MM-DD.",
           verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("tasas 400 hasta antes de desde", "GET", f"{API}/tasas?desde=2026-06-01&hasta=2026-01-01", rol="analista", espera=400, objetivo="Un periodo al reves se rechaza.",
           verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
