"""Genera postman/devoluciones.postman_collection.json (Postman v2.1).

Cada peticion lleva verificaciones automaticas (codigo HTTP, error.tipo,
X-Correlation-ID) para que el Collection Runner sirva como evidencia.
Para otro servicio: copiar este archivo y cambiar las peticiones.

    python3 postman/generar_devoluciones.py
"""
import json
import os

AUTH = "{{auth_url}}/api/v1/auth"
DEV = "{{base_url}}/api/v1/devoluciones"
SALIDA = os.path.join(os.path.dirname(__file__), "devoluciones.postman_collection.json")


def h(clave, valor):
    return {"key": clave, "value": valor}


JSON_CT, XML_CT = h("Content-Type", "application/json"), h("Content-Type", "application/xml")
ACC_JSON, ACC_XML = h("Accept", "application/json"), h("Accept", "application/xml")


def bearer(variable):
    return h("Authorization", "Bearer {{" + variable + "}}")


def req(nombre, metodo, url, descripcion, headers=(), body=None, lenguaje="json", tests=()):
    peticion = {"method": metodo, "header": list(headers), "url": url,
                "description": descripcion}
    if body is not None:
        texto = body if isinstance(body, str) else json.dumps(body, indent=2, ensure_ascii=False)
        peticion["body"] = {"mode": "raw", "raw": texto,
                            "options": {"raw": {"language": lenguaje}}}
    item = {"name": nombre, "request": peticion}
    if tests:
        item["event"] = [{"listen": "test",
                          "script": {"type": "text/javascript", "exec": list(tests)}}]
    return item


def espera(codigo, tipo=None, xml=False):
    lineas = [f'pm.test("HTTP {codigo}", () => pm.response.to.have.status({codigo}));']
    if tipo:
        leer = ("xml2Json(pm.response.text()).error.tipo" if xml
                else "pm.response.json().error.tipo")
        lineas.append(f'pm.test("error.tipo = {tipo}", () => pm.expect({leer}).to.eql("{tipo}"));')
    lineas.append('pm.test("Trae X-Correlation-ID", () => '
                  'pm.response.to.have.header("X-Correlation-ID"));')
    return lineas


def guardar(variable, expresion):
    return f'pm.collectionVariables.set("{variable}", {expresion});'


def login(nombre, email_var, token_var):
    return req(nombre, "POST", AUTH + "/login",
               "Obtiene el JWT en el servicio auth (puerto 8001).",
               [JSON_CT, ACC_JSON],
               {"email": "{{" + email_var + "}}", "password": "{{password_demo}}"},
               tests=espera(200) + [guardar(token_var, "pm.response.json().access_token")])


NUEVA = {"venta_detalle_id": "{{venta_detalle_id}}", "motivo_id": "{{motivo_id}}",
         "descripcion_problema": "El empaque llego roto y el producto derramado.",
         "cantidad_devuelta": 1}
# En JSON los ids deben ir como numero: se quitan las comillas de las variables.
NUEVA_JSON = (json.dumps(NUEVA, indent=2, ensure_ascii=False)
              .replace('"{{venta_detalle_id}}"', "{{venta_detalle_id}}")
              .replace('"{{motivo_id}}"', "{{motivo_id}}"))

carpetas = [
    {"name": "00 Preparacion (tokens)", "item": [
        req("health 200", "GET", "{{base_url}}/health",
            "RNF-22: el servicio y sus tres bases (PostgreSQL, Redis, MongoDB).",
            [ACC_JSON], tests=espera(200) + [
                'pm.test("mongodb ok", () => pm.expect(pm.response.json().dependencias.mongodb.ok).to.be.true);']),
        login("login cliente (dueno de la compra)", "email_cliente", "token_cliente"),
        login("login otro cliente", "email_otro_cliente", "token_otro"),
        login("login analista", "email_analista", "token_analista"),
    ]},
    {"name": "01 Registro (POST)", "item": [
        req("registrar 409 cantidad excedida", "POST", DEV,
            "Regla de negocio (RN-01): no se puede devolver mas de lo comprado. Va primero: si la linea ya no tuviera unidades, la respuesta seria sin_disponible.",
            [bearer("token_cliente"), JSON_CT, ACC_JSON],
            NUEVA_JSON.replace('"cantidad_devuelta": 1', '"cantidad_devuelta": 999'),
            tests=espera(409, "cantidad_excedida")),
        req("registrar 201 exitoso", "POST", DEV,
            "RF-07, RN-01: el cliente registra una devolucion sobre su compra. "
            "Crea la fila en PostgreSQL, la bitacora y un evento en MongoDB.",
            [bearer("token_cliente"), JSON_CT, ACC_JSON], NUEVA_JSON,
            tests=espera(201) + [
                guardar("devolucion_id", "pm.response.json().id"),
                guardar("folio", "pm.response.json().folio_devolucion"),
                'pm.test("estado solicitada", () => pm.expect(pm.response.json().estado).to.eql("solicitada"));',
                'pm.test("Location al expediente", () => pm.expect(pm.response.headers.get("Location")).to.include("/api/v1/devoluciones/"));']),
        req("registrar 201 XML", "POST", DEV,
            "Contrato XML: cuerpo validado contra devolucion_nueva.xsd y respuesta en XML.",
            [bearer("token_cliente"), XML_CT, ACC_XML],
            "<devolucion>\n  <venta_detalle_id>{{venta_detalle_id}}</venta_detalle_id>\n"
            "  <motivo_id>{{motivo_id}}</motivo_id>\n"
            "  <descripcion_problema>Caja golpeada, el producto llego aplastado.</descripcion_problema>\n"
            "</devolucion>", "xml",
            tests=espera(201) + [guardar("devolucion_xml_id",
                                         "xml2Json(pm.response.text()).respuesta.id")]),
        req("registrar 400 datos invalidos", "POST", DEV,
            "Validacion: id no numerico, motivo ausente y descripcion corta.",
            [bearer("token_cliente"), JSON_CT, ACC_JSON],
            {"venta_detalle_id": "abc", "descripcion_problema": "roto"},
            tests=espera(400, "validacion")),
        req("registrar 400 XML no cumple XSD", "POST", DEV,
            "El XML esta bien formado pero le faltan campos obligatorios del contrato.",
            [bearer("token_cliente"), XML_CT, ACC_XML],
            "<devolucion>\n  <motivo_id>{{motivo_id}}</motivo_id>\n</devolucion>", "xml",
            tests=espera(400, "xml_no_cumple_xsd", xml=True)),
        req("registrar 403 compra de otro cliente", "POST", DEV,
            "Autorizacion por recurso: no se puede devolver una compra ajena.",
            [bearer("token_cliente"), JSON_CT, ACC_JSON],
            NUEVA_JSON.replace("{{venta_detalle_id}}", "{{venta_detalle_ajena}}"),
            tests=espera(403, "sin_permiso")),
        req("registrar 404 linea inexistente", "POST", DEV,
            "Registro inexistente: la linea de venta no existe.",
            [bearer("token_cliente"), JSON_CT, ACC_JSON],
            NUEVA_JSON.replace("{{venta_detalle_id}}", "999999"),
            tests=espera(404, "no_encontrado")),
    ]},
    {"name": "02 Consulta (GET)", "item": [
        req("listar 200 cliente paginado", "GET", DEV + "?pagina=1&por_pagina=5",
            "RF-11: el cliente solo ve sus devoluciones; bloque paginacion.",
            [bearer("token_cliente"), ACC_JSON], tests=espera(200) + [
                'pm.test("trae paginacion", () => pm.expect(pm.response.json().paginacion.por_pagina).to.eql(5));']),
        req("listar 200 analista filtro XML", "GET", DEV + "?estado=solicitada&por_pagina=5",
            "Filtro por estado y respuesta en XML.",
            [bearer("token_analista"), ACC_XML], tests=espera(200)),
        req("listar 400 estado invalido", "GET", DEV + "?estado=perdida",
            "Parametro de consulta invalido.",
            [bearer("token_analista"), ACC_JSON], tests=espera(400, "validacion")),
        req("listar 401 sin token", "GET", DEV, "Endpoint protegido sin Authorization.",
            [ACC_JSON], tests=espera(401, "no_autenticado")),
        req("detalle 200 exitoso", "GET", DEV + "/{{devolucion_id}}",
            "Expediente con historial (bitacora) y eventos (MongoDB).",
            [bearer("token_cliente"), ACC_JSON], tests=espera(200) + [
                'pm.test("trae eventos de MongoDB", () => pm.expect(pm.response.json().eventos.length).to.be.above(0));']),
        req("detalle 403 otro cliente", "GET", DEV + "/{{devolucion_id}}",
            "Un cliente no puede ver la devolucion de otro (queda en la bitacora).",
            [bearer("token_otro"), ACC_JSON], tests=espera(403, "sin_permiso")),
        req("detalle 404 inexistente", "GET", DEV + "/999999",
            "Registro inexistente.", [bearer("token_analista"), ACC_JSON],
            tests=espera(404, "no_encontrado")),
    ]},
    {"name": "03 Revision (PATCH y PUT)", "item": [
        req("resolver 403 cliente sin permiso", "PATCH", DEV + "/{{devolucion_id}}/resolucion",
            "RNF-09: solo el Analista de Devoluciones resuelve.",
            [bearer("token_cliente"), JSON_CT, ACC_JSON], {"decision": "autorizar"},
            tests=espera(403, "sin_permiso")),
        req("resolver 400 rechazo sin justificacion", "PATCH", DEV + "/{{devolucion_id}}/resolucion",
            "Rechazar exige justificacion (RN-12).",
            [bearer("token_analista"), JSON_CT, ACC_JSON], {"decision": "rechazar"},
            tests=espera(400, "validacion")),
        req("resolver 200 pedir informacion", "PATCH", DEV + "/{{devolucion_id}}/resolucion",
            "RF-10: pasa a en_revision y notifica al cliente (RF-29).",
            [bearer("token_analista"), JSON_CT, ACC_JSON],
            {"decision": "informacion", "justificacion": "Describe el estado del sello."},
            tests=espera(200) + [
                'pm.test("en_revision", () => pm.expect(pm.response.json().estado).to.eql("en_revision"));']),
        req("corregir 200 PUT", "PUT", DEV + "/{{devolucion_id}}",
            "El cliente responde corrigiendo su solicitud.",
            [bearer("token_cliente"), JSON_CT, ACC_JSON],
            '{\n  "motivo_id": {{motivo_id}},\n  "descripcion_problema": "El sello venia abierto desde la tienda.",\n  "cantidad_devuelta": 1\n}',
            tests=espera(200)),
        req("cancelar 409 ya revisada", "DELETE", DEV + "/{{devolucion_id}}",
            "Regla de negocio: no se cancela algo que un analista ya reviso.",
            [bearer("token_cliente"), ACC_JSON], tests=espera(409, "estado_no_permite")),
        req("resolver 200 autorizar XML", "PATCH", DEV + "/{{devolucion_id}}/resolucion",
            "Autorizacion con cuerpo y respuesta XML (resolucion.xsd).",
            [bearer("token_analista"), XML_CT, ACC_XML],
            "<resolucion>\n  <decision>autorizar</decision>\n"
            "  <justificacion>Evidencia suficiente.</justificacion>\n</resolucion>", "xml",
            tests=espera(200) + [
                'pm.test("autorizada", () => pm.expect(xml2Json(pm.response.text()).respuesta.estado).to.eql("autorizada"));']),
        req("resolver 409 ya resuelta", "PATCH", DEV + "/{{devolucion_id}}/resolucion",
            "Regla de negocio: solo se resuelve lo que sigue en revision.",
            [bearer("token_analista"), JSON_CT, ACC_JSON],
            {"decision": "rechazar", "justificacion": "Intento tardio."},
            tests=espera(409, "estado_no_permite")),
        req("detalle 200 historial completo", "GET", DEV + "/{{devolucion_id}}",
            "Historial con alta, solicitud de informacion, correccion y autorizacion.",
            [bearer("token_analista"), ACC_JSON], tests=espera(200)),
    ]},
    {"name": "04 Cancelacion (DELETE)", "item": [
        req("cancelar 200 exitoso", "DELETE", DEV + "/{{devolucion_xml_id}}",
            "RNF-30: eliminacion logica de una devolucion sin revisar.",
            [bearer("token_cliente"), ACC_JSON], tests=espera(200)),
        req("detalle 404 cancelada", "GET", DEV + "/{{devolucion_xml_id}}",
            "La devolucion cancelada ya no se expone por la API.",
            [bearer("token_cliente"), ACC_JSON], tests=espera(404, "no_encontrado")),
    ]},
]

coleccion = {
    "info": {
        "name": "Devoluciones - devoluciones (v1)",
        "description": "Evidencias request/response del microservicio de devoluciones. "
                       "Antes de correr: base_url y auth_url con la IP de la VM y "
                       "password_demo en Current value. Cada corrida crea devoluciones "
                       "reales; si la linea de venta se agota (409 sin_disponible), "
                       "cambia venta_detalle_id por otra compra del mismo cliente.",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "variable": [{"key": k, "value": v} for k, v in [
        ("base_url", "http://IP-DE-LA-VM:8002"),
        ("auth_url", "http://IP-DE-LA-VM:8001"),
        ("email_cliente", "miguel.cliente@demo.mx"),
        ("email_otro_cliente", "ana.cliente@demo.mx"),
        ("email_analista", "josue.analista@demo.mx"),
        ("password_demo", ""),
        ("venta_detalle_id", "72"),       # compra de Miguel (3 unidades)
        ("venta_detalle_ajena", "85"),    # compra de Ana
        ("motivo_id", "1"),
        ("token_cliente", ""), ("token_otro", ""), ("token_analista", ""),
        ("devolucion_id", ""), ("devolucion_xml_id", ""), ("folio", ""),
    ]],
    "item": carpetas,
}

with open(SALIDA, "w", encoding="utf-8") as f:
    json.dump(coleccion, f, ensure_ascii=False, indent=2)
print(SALIDA, sum(len(c["item"]) for c in carpetas), "peticiones")
