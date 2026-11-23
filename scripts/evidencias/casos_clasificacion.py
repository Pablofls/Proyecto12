"""Casos de evidencia de clasificacion-motivos (8010): RF-22, RN-09, RN-11, RN-12, RN-13, RNF-09.

Cubre cada endpoint con exito en JSON y en XML y con errores controlados. Los datos que crea
(submotivos `evid_p4_*` y clasificaciones) se borran al final; la bitacora se conserva.
"""
SERVICIO = "clasificacion-motivos"
SIGLA = "CLA"
TITULO = "Clasificacion de motivos"
PUERTO = 8010
ARCHIVO = "clasificacion_motivos"

API = "/api/v1/motivos"
DESCRIPCION_FRIO = "El producto llego tibio y la temperatura era muy alta"
SQL_DEVOLUCION_DEL_LOTE = ("SELECT d.id FROM devoluciones d JOIN venta_detalle vd ON vd.id = d.venta_detalle_id "
                           "JOIN lotes l ON l.id = vd.lote_id WHERE l.numero_lote = 'L-2026-PROB-01' "
                           "AND d.eliminado_en IS NULL ORDER BY d.id LIMIT 1")


def tipo_error(r):
    return r.json["error"]["tipo"]


def ejecutar(c):
    dev = c.valor(SQL_DEVOLUCION_DEL_LOTE)
    if not dev:
        raise SystemExit("Falta el lote de demo L-2026-PROB-01 (corre scripts/seed_demo.py).")
    c.ctx["dev_id"] = int(dev)
    c.ctx["dev_antes"] = c.valor("SELECT estado || '/' || motivo_id FROM devoluciones WHERE id = {dev_id}")
    # Orden: primero las clasificaciones (referencian submotivos), luego las versiones y por ultimo los submotivos.
    c.limpieza += [
        "DELETE FROM submotivos_versiones WHERE submotivo_id IN (SELECT id FROM submotivos WHERE codigo LIKE 'evid_p4_%')",
        "DELETE FROM submotivos WHERE codigo LIKE 'evid_p4_%'",
    ]

    def devolucion_intacta(_):
        return c.valor("SELECT estado || '/' || motivo_id FROM devoluciones WHERE id = {dev_id}".format(**c.ctx)) \
            == c.ctx["dev_antes"]

    def registrar_limpieza(clave):
        c.limpieza.insert(0, f"DELETE FROM clasificaciones_motivo WHERE id = {c.ctx[clave]}")

    # ---------------------------------------------------------------- salud, contratos y Swagger
    c.caso("salud 200 JSON", "GET", "/health", objetivo="El servicio informa su estado y el de PostgreSQL y Redis (RF-32).",
           verifica=[("estado ok", lambda r: r.json["estado"] == "ok"),
                     ("PostgreSQL ok", lambda r: r.json["dependencias"]["postgresql"]["ok"] is True),
                     ("Redis ok", lambda r: r.json["dependencias"]["redis"]["ok"] is True)])
    c.caso("salud 200 XML", "GET", "/health", accept="application/xml", objetivo="El mismo endpoint responde XML (RF-31).",
           verifica=[("es XML", lambda r: r.tipo.startswith("application/xml")),
                     ("estado ok", lambda r: "<estado>ok</estado>" in r.texto)])
    c.caso("Swagger: documentacion de la API", "GET", "/docs", accept="text/html",
           objetivo="La API publica su documentacion Swagger.",
           verifica=[("HTML de Swagger UI", lambda r: "swagger" in r.texto.lower())])
    c.caso("Swagger: especificacion OpenAPI", "GET", "/openapi.json", objetivo="La especificacion lista todos los endpoints.",
           verifica=[("incluye /sugerencias", lambda r: f"{API}/sugerencias" in r.json["paths"]),
                     ("incluye la revision", lambda r: f"{API}/clasificaciones/{{id}}/revision" in r.json["paths"])])
    c.caso("contrato XSD publicado", "GET", "/contratos/revision.xsd", accept="application/xml",
           objetivo="El contrato XML de la revision se publica para que los clientes lo validen (RF-31).",
           verifica=[("es un esquema XSD", lambda r: "xs:schema" in r.texto and 'name="decision"' in r.texto)])

    # ---------------------------------------------------------------- autenticacion
    c.caso("sin token: 401", "GET", f"{API}/categorias", espera=401, objetivo="Un endpoint protegido exige JWT (RNF-09).",
           verifica=[("tipo no_autenticado", lambda r: tipo_error(r) == "no_autenticado")])
    c.caso("token invalido: 401", "GET", f"{API}/categorias", espera=401, token="no.es.un.jwt",
           objetivo="Un token alterado se rechaza (RNF-09).",
           verifica=[("tipo token_invalido", lambda r: tipo_error(r) == "token_invalido")])

    # ---------------------------------------------------------------- categorias y submotivos
    c.caso("categorias 200", "GET", f"{API}/categorias", rol="analista",
           objetivo="Las cinco categorias de origen de la falla (RF-22).",
           guarda={"cat_transporte": lambda r: next(x["id"] for x in r.json["datos"] if x["codigo"] == "transporte")},
           verifica=[("son 5", lambda r: r.json["total"] == 5),
                     ("origenes esperados", lambda r: {x["codigo"] for x in r.json["datos"]} ==
                      {"falla_producto", "empaque", "transporte", "error_comercial", "mal_uso"})])
    c.caso("categorias 403 cliente", "GET", f"{API}/categorias", rol="cliente", espera=403,
           objetivo="El catalogo interno no lo lee un cliente (RN-13).",
           verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])
    c.caso("submotivos 200 paginado", "GET", f"{API}/submotivos?por_pagina=5", rol="analista",
           objetivo="Listado de submotivos vigentes con paginacion.",
           verifica=[("5 por pagina", lambda r: len(r.json["datos"]) == 5),
                     ("al menos 12 en total", lambda r: r.json["paginacion"]["total"] >= 12)])
    c.caso("submotivos 200 filtrado por categoria", "GET", f"{API}/submotivos?categoria_id={{cat_transporte}}", rol="analista",
           objetivo="Filtra por categoria de origen.",
           guarda={"sub_frio": lambda r: next(x["id"] for x in r.json["datos"] if x["codigo"] == "cadena_frio")},
           verifica=[("todos de transporte", lambda r: {x["categoria_codigo"] for x in r.json["datos"]} == {"transporte"}),
                     ("incluye la cadena de frio", lambda r: "cadena_frio" in {x["codigo"] for x in r.json["datos"]})])
    c.caso("submotivos 200 XML", "GET", f"{API}/submotivos?por_pagina=2", rol="analista", accept="application/xml",
           objetivo="El listado responde XML (RF-31).",
           verifica=[("es XML", lambda r: r.tipo.startswith("application/xml")),
                     ("raiz submotivos", lambda r: "<submotivos>" in r.texto)])
    c.caso("submotivos 400 filtro invalido", "GET", f"{API}/submotivos?categoria_id=abc", rol="analista", espera=400,
           objetivo="Un filtro mal formado se rechaza, no se ignora.",
           verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("submotivo 200 con su historial", "GET", f"{API}/submotivos/{{sub_frio}}", rol="analista",
           objetivo="El detalle trae el historial de versiones (RF-22, RN-12).",
           verifica=[("tiene al menos la version 1", lambda r: len(r.json["versiones"]) >= 1),
                     ("version inicial del catalogo", lambda r: r.json["versiones"][-1]["motivo_cambio"] == "Catalogo inicial")])
    c.caso("submotivo 404", "GET", f"{API}/submotivos/999999", rol="analista", espera=404,
           objetivo="Un submotivo inexistente responde 404.",
           verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])

    # ---------------------------------------------------------------- alta
    c.caso("alta 201 JSON (administrador)", "POST", f"{API}/submotivos", rol="admin", espera=201,
           json_cuerpo={"categoria_id": c.ctx["cat_transporte"], "codigo": "evid_p4_humedad", "nombre": "Humedad en el almacen",
                        "descripcion": "Producto mojado por goteras o humedad", "palabras_clave": ["humedad", "goteras", "mojado"]},
           objetivo="Un administrador da de alta un submotivo; nace en la version 1 (RF-22).",
           guarda={"sub_id": lambda r: r.json["id"]},
           verifica=[("version 1", lambda r: r.json["version"] == 1), ("trae Location", lambda r: "location" in r.cabeceras)],
           efecto=[("el submotivo y su version 1", "SELECT s.codigo, s.version, s.activo, v.version AS version_guardada, v.motivo_cambio "
                    "FROM submotivos s JOIN submotivos_versiones v ON v.submotivo_id = s.id WHERE s.id = {sub_id}")])
    c.caso("alta 201 XML (supervisor)", "POST", f"{API}/submotivos", rol="supervisor", espera=201, accept="application/xml",
           xml=("<submotivo><categoria_id>%d</categoria_id><codigo>evid_p4_xml</codigo><nombre>Alta enviada por XML</nombre>"
                "<palabras_clave><item>xml</item><item>contrato</item></palabras_clave></submotivo>" % c.ctx["cat_transporte"]),
           objetivo="El mismo alta en XML, validado contra su XSD (RF-31). El Supervisor tambien puede dar de alta.",
           guarda={"sub_xml_id": lambda r: int(r.texto.split("<id>")[1].split("</id>")[0])},
           verifica=[("version 1", lambda r: "<version>1</version>" in r.texto)])
    c.caso("alta 400 codigo con formato invalido", "POST", f"{API}/submotivos", rol="admin", espera=400,
           json_cuerpo={"categoria_id": c.ctx["cat_transporte"], "codigo": "Mal Codigo", "nombre": "x"},
           objetivo="El codigo debe ser minusculas, numeros y guion bajo.",
           verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion"),
                     ("senala el campo codigo", lambda r: any(d["campo"] == "codigo" for d in r.json["error"]["detalles"]))])
    c.caso("alta 400 XML que no cumple el XSD", "POST", f"{API}/submotivos", rol="admin", espera=400, accept="application/xml",
           xml="<submotivo><nombre>Sin categoria</nombre></submotivo>",
           objetivo="Un XML que no cumple el contrato se rechaza antes de procesarse (RF-31).",
           verifica=[("tipo xml_no_cumple_xsd", lambda r: "xml_no_cumple_xsd" in r.texto)])
    c.caso("alta 409 codigo duplicado", "POST", f"{API}/submotivos", rol="admin", espera=409,
           json_cuerpo={"categoria_id": c.ctx["cat_transporte"], "codigo": "evid_p4_humedad", "nombre": "Repetido"},
           objetivo="Dos submotivos no comparten codigo.",
           verifica=[("tipo codigo_duplicado", lambda r: tipo_error(r) == "codigo_duplicado")])
    c.caso("alta 409 categoria inexistente", "POST", f"{API}/submotivos", rol="admin", espera=409,
           json_cuerpo={"categoria_id": 99999, "codigo": "evid_p4_huerfano", "nombre": "Sin categoria real"},
           objetivo="No se acepta una referencia que no existe.",
           verifica=[("tipo referencia_invalida", lambda r: tipo_error(r) == "referencia_invalida")])
    c.caso("alta 403 analista", "POST", f"{API}/submotivos", rol="analista", espera=403,
           json_cuerpo={"categoria_id": c.ctx["cat_transporte"], "codigo": "evid_p4_prohibido", "nombre": "x"},
           objetivo="Solo Administrador y Supervisor editan el catalogo (RN-13).",
           verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")],
           efecto=[("no se creo ninguna fila", "SELECT count(*) AS filas FROM submotivos WHERE codigo = 'evid_p4_prohibido'")])

    # ---------------------------------------------------------------- edicion y versiones
    cuerpo_edicion = {"categoria_id": c.ctx["cat_transporte"], "nombre": "Humedad o goteras en el almacen",
                      "descripcion": "Producto mojado por goteras o humedad", "palabras_clave": ["humedad", "goteras", "mojado", "filtracion"],
                      "motivo_cambio": "Se agrega la palabra filtracion"}
    c.caso("edicion 200: crea la version 2", "PUT", f"{API}/submotivos/{{sub_id}}", rol="supervisor", json_cuerpo=cuerpo_edicion,
           objetivo="Cada cambio crea una version nueva y exige explicar por que (RF-22, RN-12).",
           verifica=[("version 2", lambda r: r.json["version"] == 2)],
           efecto=[("la version anterior se conserva", "SELECT version, nombre, motivo_cambio FROM submotivos_versiones "
                    "WHERE submotivo_id = {sub_id} ORDER BY version")])
    c.caso("edicion 200: sin cambios no crea version", "PUT", f"{API}/submotivos/{{sub_id}}", rol="supervisor", json_cuerpo=cuerpo_edicion,
           objetivo="Repetir lo mismo es idempotente: no ensucia el historial.",
           verifica=[("sin_cambios", lambda r: r.json["sin_cambios"] is True), ("sigue en la version 2", lambda r: r.json["version"] == 2)],
           efecto=[("solo hay 2 versiones", "SELECT count(*) AS versiones FROM submotivos_versiones WHERE submotivo_id = {sub_id}")])
    c.caso("edicion 400 sin explicar el cambio", "PUT", f"{API}/submotivos/{{sub_id}}", rol="supervisor", espera=400,
           json_cuerpo={k: v for k, v in cuerpo_edicion.items() if k != "motivo_cambio"},
           objetivo="Sin motivo del cambio no se edita.",
           verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("edicion 404", "PUT", f"{API}/submotivos/999999", rol="supervisor", espera=404, json_cuerpo=cuerpo_edicion,
           objetivo="Editar un submotivo inexistente responde 404.",
           verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])
    c.caso("estado 200: desactivar crea la version 3", "PATCH", f"{API}/submotivos/{{sub_id}}/estado", rol="admin",
           json_cuerpo={"activo": False, "motivo_cambio": "Se retira porque era solo de prueba"},
           objetivo="Activar o desactivar tambien es un cambio versionado (RF-22).",
           verifica=[("version 3", lambda r: r.json["version"] == 3), ("activo false", lambda r: r.json["activo"] is False)],
           efecto=[("queda inactivo y con 3 versiones", "SELECT s.activo, s.version, count(v.*) AS versiones FROM submotivos s "
                    "JOIN submotivos_versiones v ON v.submotivo_id = s.id WHERE s.id = {sub_id} GROUP BY s.activo, s.version")])
    c.caso("estado 400 valor invalido", "PATCH", f"{API}/submotivos/{{sub_id}}/estado", rol="admin", espera=400,
           json_cuerpo={"activo": "quiza", "motivo_cambio": "Valor que no es booleano"},
           objetivo="activo debe ser booleano.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("estado 404", "PATCH", f"{API}/submotivos/999999/estado", rol="admin", espera=404,
           json_cuerpo={"activo": False, "motivo_cambio": "No existe este submotivo"},
           objetivo="Un submotivo inexistente responde 404.", verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])

    # ---------------------------------------------------------------- sugerencia de texto (cualquier rol)
    c.caso("sugerencia 200 (cliente)", "POST", f"{API}/sugerencias", rol="cliente", json_cuerpo={"descripcion": DESCRIPCION_FRIO},
           objetivo="Un cliente pide una sugerencia para su formulario; es solo una propuesta (RN-11).",
           verifica=[("exige confirmacion", lambda r: r.json["requiere_confirmacion"] is True),
                     ("sugiere cadena de frio", lambda r: r.json["sugerencias"][0]["codigo"] == "cadena_frio"),
                     ("no revela las palabras clave", lambda r: "coincidencias" not in r.json["sugerencias"][0])])
    c.caso("sugerencia 200 XML", "POST", f"{API}/sugerencias", rol="supervisor", accept="application/xml",
           xml=f"<sugerencia><descripcion>{DESCRIPCION_FRIO}</descripcion></sugerencia>",
           objetivo="La sugerencia en XML. Un Supervisor tambien puede pedirla (corregido en el PR #33).",
           verifica=[("es XML", lambda r: r.tipo.startswith("application/xml")), ("cadena_frio", lambda r: "cadena_frio" in r.texto)])
    c.caso("sugerencia 200: sin coincidencias no inventa", "POST", f"{API}/sugerencias", rol="cliente",
           json_cuerpo={"descripcion": "No me gusto para nada lo que compre ayer"},
           objetivo="Si ninguna palabra coincide, no se inventa una sugerencia.",
           verifica=[("lista vacia", lambda r: r.json["sugerencias"] == [])])
    c.caso("sugerencia 400 descripcion corta", "POST", f"{API}/sugerencias", rol="cliente", espera=400,
           json_cuerpo={"descripcion": "corta"}, objetivo="La descripcion exige entre 10 y 2000 caracteres.",
           verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("sugerencia 401 sin token", "POST", f"{API}/sugerencias", espera=401, json_cuerpo={"descripcion": DESCRIPCION_FRIO},
           objetivo="Tambien la sugerencia exige sesion.", verifica=[("tipo no_autenticado", lambda r: tipo_error(r) == "no_autenticado")])

    # ---------------------------------------------------------------- clasificaciones y revision humana
    c.caso("clasificacion 201: queda pendiente", "POST", f"{API}/clasificaciones", rol="analista", espera=201,
           json_cuerpo={"devolucion_id": c.ctx["dev_id"]},
           objetivo="Se propone un submotivo para una devolucion y queda PENDIENTE de revision humana (RN-11).",
           guarda={"cla_id": lambda r: r.json["id"]},
           verifica=[("estado pendiente", lambda r: r.json["estado"] == "pendiente"),
                     ("pide revision humana", lambda r: r.json["requiere_revision_humana"] is True),
                     ("sugiere cadena de frio", lambda r: "cadena_frio" in [s["codigo"] for s in r.json["sugerencias"]]),
                     ("la devolucion no cambio", devolucion_intacta)],
           efecto=[("fila pendiente y devolucion intacta", "SELECT cm.estado, cm.revisado_por, ss.codigo AS sugerido, "
                    "d.estado AS estado_devolucion, d.motivo_id AS motivo_devolucion FROM clasificaciones_motivo cm "
                    "JOIN devoluciones d ON d.id = cm.devolucion_id LEFT JOIN submotivos ss ON ss.id = cm.submotivo_sugerido_id "
                    "WHERE cm.id = {cla_id}")])
    registrar_limpieza("cla_id")
    c.caso("clasificacion 409: ya hay una pendiente", "POST", f"{API}/clasificaciones", rol="analista", espera=409,
           json_cuerpo={"devolucion_id": c.ctx["dev_id"]}, objetivo="Una sola sugerencia pendiente por devolucion.",
           verifica=[("tipo clasificacion_pendiente", lambda r: tipo_error(r) == "clasificacion_pendiente")])
    c.caso("clasificacion 404 devolucion inexistente", "POST", f"{API}/clasificaciones", rol="analista", espera=404,
           json_cuerpo={"devolucion_id": 99999999}, objetivo="No se clasifica lo que no existe.",
           verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])
    c.caso("clasificacion 400 identificador invalido", "POST", f"{API}/clasificaciones", rol="analista", espera=400,
           json_cuerpo={"devolucion_id": "abc"}, objetivo="devolucion_id debe ser un entero positivo.",
           verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("clasificacion 403 cliente", "POST", f"{API}/clasificaciones", rol="cliente", espera=403,
           json_cuerpo={"devolucion_id": c.ctx["dev_id"]}, objetivo="Un cliente no propone clasificaciones (RN-13).",
           verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])
    c.caso("cola 200: pendientes de revision", "GET", f"{API}/clasificaciones?estado=pendiente", rol="analista",
           objetivo="La cola de sugerencias por revisar.",
           verifica=[("incluye la recien creada", lambda r: c.ctx["cla_id"] in [x["id"] for x in r.json["datos"]])])
    c.caso("cola 400 estado desconocido", "GET", f"{API}/clasificaciones?estado=inventado", rol="analista", espera=400,
           objetivo="Un estado que no existe se rechaza.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("revision 400: corregir sin comentario ni submotivo", "POST", f"{API}/clasificaciones/{{cla_id}}/revision", rol="analista",
           espera=400, json_cuerpo={"decision": "corregir"},
           objetivo="Quien contradice a la sugerencia debe elegir el submotivo y explicar por que (RN-11).",
           verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("revision 403 cliente", "POST", f"{API}/clasificaciones/{{cla_id}}/revision", rol="cliente", espera=403,
           json_cuerpo={"decision": "confirmar"}, objetivo="Un cliente no revisa (RN-13).",
           verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])
    c.caso("revision 200: confirmar", "POST", f"{API}/clasificaciones/{{cla_id}}/revision", rol="analista",
           json_cuerpo={"decision": "confirmar"},
           objetivo="Una persona confirma la sugerencia. La revision NO modifica la devolucion (RN-11).",
           verifica=[("estado confirmada", lambda r: r.json["estado"] == "confirmada"),
                     ("no se aplico a la devolucion", lambda r: r.json["aplicado_a_devolucion"] is False),
                     ("queda quien reviso", lambda r: r.json["revisado_por"] is not None),
                     ("la devolucion sigue igual", devolucion_intacta)],
           efecto=[("responsable, version y devolucion intacta", "SELECT cm.estado, u.nombre AS revisado_por, cm.version_final, "
                    "d.estado AS estado_devolucion, d.motivo_id AS motivo_devolucion FROM clasificaciones_motivo cm "
                    "JOIN usuarios u ON u.id = cm.revisado_por JOIN devoluciones d ON d.id = cm.devolucion_id WHERE cm.id = {cla_id}")])
    c.caso("revision 409: ya fue revisada", "POST", f"{API}/clasificaciones/{{cla_id}}/revision", rol="analista", espera=409,
           json_cuerpo={"decision": "descartar", "comentario": "Intento de cambiar una decision ya tomada"},
           objetivo="Una clasificacion revisada no se vuelve a revisar.",
           verifica=[("tipo ya_revisada", lambda r: tipo_error(r) == "ya_revisada")])
    c.caso("revision 404", "POST", f"{API}/clasificaciones/99999999/revision", rol="analista", espera=404,
           json_cuerpo={"decision": "confirmar"}, objetivo="Una clasificacion inexistente responde 404.",
           verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])

    # otra sugerencia sobre la misma devolucion (ya no hay pendiente) para mostrar las otras dos decisiones
    c.caso("clasificacion 201: nueva sugerencia tras la revision", "POST", f"{API}/clasificaciones", rol="analista", espera=201,
           json_cuerpo={"devolucion_id": c.ctx["dev_id"]},
           objetivo="Resuelta la anterior, se puede proponer otra.", guarda={"cla2_id": lambda r: r.json["id"]},
           verifica=[("estado pendiente", lambda r: r.json["estado"] == "pendiente")])
    c.limpieza.insert(0, f"DELETE FROM clasificaciones_motivo WHERE id = {c.ctx['cla2_id']}")
    c.caso("revision 200 XML: corregir", "POST", f"{API}/clasificaciones/{{cla2_id}}/revision", rol="supervisor", accept="application/xml",
           xml=("<revision><decision>corregir</decision><submotivo_id>%d</submotivo_id>"
                "<comentario>La causa fue el golpe, no el frio</comentario></revision>" % c.ctx["sub_xml_id"]),
           objetivo="Corregir: una persona elige otro submotivo y explica por que. En XML, validado contra su XSD.",
           verifica=[("estado corregida", lambda r: "<estado>corregida</estado>" in r.texto)],
           efecto=[("submotivo final y comentario", "SELECT cm.estado, sf.codigo AS submotivo_final, cm.version_final, cm.comentario "
                    "FROM clasificaciones_motivo cm JOIN submotivos sf ON sf.id = cm.submotivo_final_id WHERE cm.id = {cla2_id}")])
    c.caso("clasificacion 201: tercera sugerencia", "POST", f"{API}/clasificaciones", rol="analista", espera=201,
           json_cuerpo={"devolucion_id": c.ctx["dev_id"]}, objetivo="Otra sugerencia pendiente, para descartarla.",
           guarda={"cla3_id": lambda r: r.json["id"]})
    c.limpieza.insert(0, f"DELETE FROM clasificaciones_motivo WHERE id = {c.ctx['cla3_id']}")
    c.caso("revision 200: descartar", "POST", f"{API}/clasificaciones/{{cla3_id}}/revision", rol="admin",
           json_cuerpo={"decision": "descartar", "comentario": "La descripcion no alcanza para clasificar el caso"},
           objetivo="Descartar exige comentario; no se asigna ningun submotivo final.",
           verifica=[("estado descartada", lambda r: r.json["estado"] == "descartada"),
                     ("sin submotivo final", lambda r: r.json["submotivo_final"] is None),
                     ("la devolucion sigue igual", devolucion_intacta)],
           efecto=[("descartada, con responsable y sin submotivo final", "SELECT estado, submotivo_final_id, revisado_por IS NOT NULL AS tiene_responsable "
                    "FROM clasificaciones_motivo WHERE id = {cla3_id}")])
