"""Convierte la salida real de Newman en evidencia versionable (apartado 5).

    newman run ... --reporter-json-export ~/evidencias_vm/<coleccion>.json
    python3 docs/postman/volcar_ejecuciones.py ~/evidencias_vm

Escribe docs/evidencias/ejecuciones/<coleccion>.md con cada peticion y su
respuesta REAL (metodo, URL, headers, body, codigo, cuerpo, tiempo y
verificaciones) y reemplaza en docs/EVIDENCIAS.md y en el checklist los
marcadores `CAPTURA PENDIENTE: <id>` de los casos que si se ejecutaron por un
enlace a esa transcripcion. Los casos que no estan en el JSON (por ejemplo la
carpeta 06 de auth, que bloquea una cuenta) siguen pendientes.

Por que un script y no pegar a mano: la transcripcion sale de la ejecucion y no
se puede editar sin que se note; y es repetible si se regenera EVIDENCIAS.md.

Seguridad (RNF-16): los JWT, el campo password y la IP de la VM se ocultan. Si
la variable de entorno PASSWORD_DEMO esta definida y su valor aparece en la
salida, el script se detiene sin escribir nada.

Solo libreria estandar.
"""
import datetime
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
EVIDENCIAS = os.path.join(RAIZ, "docs", "EVIDENCIAS.md")
CHECKLIST = os.path.join(RAIZ, "docs", "evidencias", "CHECKLIST_CAPTURAS.md")
SALIDA = os.path.join(RAIZ, "docs", "evidencias", "ejecuciones")
MAX_CUERPO = 2500

COLECCIONES = ["auth", "devoluciones", "logistica", "inspecciones",
               "reembolsos_costos", "ventas_catalogos", "evidencias",
               "analisis_auditoria"]
HEADERS_RESPUESTA = ("content-type", "x-correlation-id", "location", "retry-after",
                     "content-disposition", "content-length")

JWT = re.compile(r"eyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]*")
PASSWORD_JSON = re.compile(r'("password"\s*:\s*)"[^"]*"')
PASSWORD_XML = re.compile(r"(<password>)[^<]*(</password>)")
MARCADOR = re.compile(r"<!-- CAPTURA PENDIENTE: ([0-9]{3}_[a-z0-9_]+) -->")


def ocultar(texto, vm_host=None):
    texto = JWT.sub("***jwt***", texto)
    texto = PASSWORD_JSON.sub(r'\1"***"', texto)
    texto = PASSWORD_XML.sub(r"\1***\2", texto)
    if vm_host:
        texto = texto.replace(vm_host, "{{vm_host}}")
    return texto


def leer_checklist():
    """id, carpeta y caso de cada captura, agrupados por coleccion y en orden."""
    por_coleccion, actual = {}, None
    for linea in open(CHECKLIST, encoding="utf-8"):
        if linea.startswith("## "):
            actual = linea[3:].strip()
            por_coleccion[actual] = []
        elif actual and linea.startswith("| [") and "`" in linea:
            celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
            por_coleccion[actual].append(
                {"id": celdas[1].strip("`").removesuffix(".png"),
                 "carpeta": celdas[2], "caso": celdas[3]})
    return por_coleccion


def cuerpo_texto(respuesta):
    flujo = respuesta.get("stream") or {}
    datos = bytes(flujo.get("data", [])) if isinstance(flujo, dict) else b""
    texto = datos.decode("utf-8", errors="replace")
    try:
        texto = json.dumps(json.loads(texto), indent=2, ensure_ascii=False)
    except ValueError:
        pass
    if len(texto) > MAX_CUERPO:
        texto = texto[:MAX_CUERPO] + f"\n... (recortado, {len(texto)} caracteres en total)"
    return texto


def url_de(req):
    u = req["url"]
    base = f"{u.get('protocol', 'http')}://{'.'.join(u['host'])}"
    if u.get("port"):
        base += f":{u['port']}"
    ruta = "/" + "/".join(u.get("path", []))
    consulta = "&".join(f"{q['key']}={q.get('value', '')}" for q in u.get("query", [])
                        if not q.get("disabled"))
    return base + ruta + ("?" + consulta if consulta else "")


def cuerpo_peticion(req):
    cuerpo = req.get("body") or {}
    if cuerpo.get("mode") == "raw":
        return cuerpo.get("raw", "")
    if cuerpo.get("mode") == "formdata":
        filas = []
        for campo in cuerpo.get("formdata", []):
            if campo.get("type") == "file":
                src = campo.get("src")
                nombre = os.path.basename(src[0] if isinstance(src, list) else str(src))
                filas.append(f"{campo['key']}: (archivo) {nombre}")
            else:
                filas.append(f"{campo['key']}: {campo.get('value', '')}")
        return "\n".join(filas)
    return ""


def bloque(ejecucion, vm_host):
    req, resp = ejecucion["request"], ejecucion["response"]
    encabezados = [f"{h['key']}: {h['value']}" for h in req.get("header", [])
                   if not h.get("system") and not h.get("disabled")]
    cuerpo_req = cuerpo_peticion(req)
    ctype = ""
    for h in resp.get("header", []):
        if h["key"].lower() == "content-type":
            ctype = h["value"]
    lenguaje = "xml" if "xml" in ctype else "json"
    cab_resp = [f"{h['key']}: {h['value']}" for h in resp.get("header", [])
                if h["key"].lower() in HEADERS_RESPUESTA]
    verifs = "\n".join(
        f"- {'ok' if not a.get('error') and not a.get('skipped') else 'FALLO'}: {a['assertion']}"
        for a in ejecucion.get("assertions", []))
    L = [f"`{req['method']} {ocultar(url_de(req), vm_host)}`", "",
         "**Request - headers:**", "", "```http",
         *(ocultar(x, vm_host) for x in (encabezados or ["(sin headers propios)"])), "```"]
    if cuerpo_req:
        L += ["", "**Request - body:**", "", "```", ocultar(cuerpo_req, vm_host), "```"]
    L += ["", f"**Response - {resp['code']} {resp['status']}** "
              f"({resp.get('responseTime', '?')} ms, {resp.get('responseSize', '?')} bytes):", "",
          "```http", *(ocultar(x, vm_host) for x in cab_resp), "```", "", f"```{lenguaje}",
          ocultar(cuerpo_texto(resp), vm_host), "```", "", "**Verificaciones:**", "", verifs, ""]
    return "\n".join(L)


def main(carpeta):
    checklist = leer_checklist()
    textos, ejecutados, sin_resultado = {}, set(), []
    vm_host = None
    for col in COLECCIONES:
        ruta = os.path.join(carpeta, col + ".json")
        if not os.path.exists(ruta):
            sin_resultado += [c["id"] for c in checklist.get(col, [])]
            continue
        corrida = json.load(open(ruta, encoding="utf-8"))["run"]
        inicio = corrida["timings"].get("started")
        fecha = (datetime.datetime.fromtimestamp(inicio / 1000, datetime.timezone.utc)
                 .strftime("%Y-%m-%d %H:%M UTC") if inicio else "?")
        pendientes = {}
        for e in corrida["executions"]:
            pendientes.setdefault(e["item"]["name"], []).append(e)
            if vm_host is None:
                vm_host = ".".join(e["request"]["url"]["host"])
        L = [f"# Ejecuciones reales - `{col}`", "",
             f"Salida de `newman run docs/postman/{col}.postman_collection.json` contra la VM "
             f"({fecha}). Verificaciones: {corrida['stats']['assertions']['total']} "
             f"({corrida['stats']['assertions']['failed']} fallidas). Tokens, contrasenas e IP de "
             f"la VM estan ocultos (`***jwt***`, `***`, `{{{{vm_host}}}}`).", ""]
        for fila in checklist.get(col, []):
            cola = pendientes.get(fila["caso"])
            if not cola:
                sin_resultado.append(fila["id"])
                continue
            L += [f"## {fila['id']}", "",
                  f"Carpeta: {fila['carpeta']} - Caso: {fila['caso']}", "",
                  bloque(cola.pop(0), vm_host)]
            ejecutados.add(fila["id"])
        textos[col] = "\n".join(L)
    salida_total = "\n".join(textos.values())
    clave = os.environ.get("PASSWORD_DEMO")
    if clave and clave in salida_total:
        sys.exit("ABORTADO: PASSWORD_DEMO aparece en la salida; no se escribio nada.")
    if JWT.search(salida_total):
        sys.exit("ABORTADO: queda un JWT sin ocultar; no se escribio nada.")
    os.makedirs(SALIDA, exist_ok=True)
    for col, texto in textos.items():
        with open(os.path.join(SALIDA, col + ".md"), "w", encoding="utf-8") as f:
            f.write(texto + "\n")
    col_de = {c["id"]: col for col, filas in checklist.items() for c in filas}

    def enlace(m):
        id_ = m.group(1)
        if id_ in ejecutados:
            return f"[ejecucion real](evidencias/ejecuciones/{col_de[id_]}.md#{id_})"
        return m.group(0)

    texto = open(EVIDENCIAS, encoding="utf-8").read()
    texto = texto.replace(
        "Ninguna respuesta de este archivo fue ejecutada.",
        "Las respuestas marcadas `ejecucion real` salen de una corrida de Newman contra la VM "
        "(transcripciones en `docs/evidencias/ejecuciones/`); las que siguen en "
        "`CAPTURA PENDIENTE` no se han ejecutado todavia.")
    open(EVIDENCIAS, "w", encoding="utf-8").write(MARCADOR.sub(enlace, texto))
    lista = open(CHECKLIST, encoding="utf-8").read()
    for id_ in ejecutados:
        lista = lista.replace(f"| [ ] | `{id_}.png` |", f"| [x] | `{id_}.png` |")
    open(CHECKLIST, "w", encoding="utf-8").write(lista)
    print(f"ejecutados con transcripcion: {len(ejecutados)}")
    print(f"sin resultado (siguen pendientes): {len(sin_resultado)}")
    for id_ in sin_resultado:
        print("  ", id_)


if __name__ == "__main__":
    main(os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/evidencias_vm"))
