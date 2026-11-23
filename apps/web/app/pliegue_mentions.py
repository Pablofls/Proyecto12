"""Catálogo privado de referencias de Pliegue. Solo lee código y contratos locales."""
import ast
import hashlib
import json
import re
from functools import lru_cache
from inspect import unwrap
from pathlib import Path

import yaml
from flask import current_app, request
from werkzeug.exceptions import HTTPException

from app.microservicios import SERVICIOS
from app.security import ADMINISTRADOR

ROOT = Path(__file__).resolve().parents[3]
WEB = "apps/web/app/"
LIMIT = 8
HTTP = {"get", "post", "put", "patch", "delete", "head", "options"}
# Etiquetas de navegación para las rutas registradas de cada aplicación.
SIDEBAR = {
    "panel.principal": "Panel", "ventas.listar": "Ventas", "devoluciones.listar": "Devoluciones",
    "logistica.listar": "Recolecciones", "inspecciones.listar": "Inspecciones",
    "inspecciones.inventario": "Inventario", "reembolsos.listar": "Reembolsos",
    "panel.causas": "Causas", "panel.costos": "Costos", "catalogos.indice": "Catálogos",
    "usuarios.listar": "Usuarios", "panel.bitacora": "Bitácora", "integracion.servicios": "Servicios",
    "returns_dashboard.dashboard": "Estadísticas de devoluciones", "lab_home": "Laboratorio",
    "lab_demo": "Ejemplo de dashboard", "pliegue.code_page": "Pliegue · Código",
}
DASHBOARD = WEB + "templates/devoluciones/dashboard.html"
DASHBOARD_FILES = (DASHBOARD, WEB + "returns_dashboard.py", WEB + "returns_dashboard.json",
                   WEB + "static/css/returns-dashboard.css", WEB + "static/js/returns-dashboard.js")


def digest(data):
    return hashlib.sha256(data).hexdigest()


@lru_cache(maxsize=64)
def service_operations(source, contract):
    tree = ast.parse(source)
    prefixes = {}
    registered = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name) and node.value.func.id == "Blueprint"):
            prefix = next((kw.value for kw in node.value.keywords if kw.arg == "url_prefix"), None)
            if isinstance(prefix, ast.Constant) and isinstance(prefix.value, str):
                prefixes.update({target.id: prefix.value for target in node.targets if isinstance(target, ast.Name)})
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
              and node.func.attr == "register_blueprint" and node.args and isinstance(node.args[0], ast.Name)):
            registered.add(node.args[0].id)
    routes = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for call in node.decorator_list:
            if (not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute)
                    or not isinstance(call.func.value, ast.Name) or not call.args
                    or not isinstance(call.args[0], ast.Constant) or not isinstance(call.args[0].value, str)):
                continue
            owner = call.func.value.id
            if owner != "app" and (owner not in registered or owner not in prefixes):
                continue
            path = re.sub(r"<(?:[^:<>]+:)?([^<>]+)>", r"{\1}", prefixes.get(owner, "") + call.args[0].value)
            method = call.func.attr
            methods = [method]
            if method == "route":
                methods = next(([arg.value.lower() for arg in kw.value.elts
                                 if isinstance(arg, ast.Constant) and isinstance(arg.value, str)]
                                for kw in call.keywords if kw.arg == "methods"
                                and isinstance(kw.value, (ast.List, ast.Tuple))), ["get"])
            routes.update((path, m) for m in methods if m in HTTP)

    spec = yaml.safe_load(contract)
    result = []
    for path, method in sorted(routes):
        operation = spec.get("paths", {}).get(path, {}).get(method)
        if not isinstance(operation, dict):
            continue
        # Los punteros y nombres de esquema identifican el contrato sin copiar ejemplos,
        # credenciales, valores por defecto ni URLs de infraestructura.
        name = path.replace("~", "~0").replace("/", "~1")
        schemas = re.findall(r"#/components/schemas/([\w.-]{1,80})", json.dumps(operation))
        result.append((path, method.upper(), f"#/paths/{name}/{method}", sorted(set(schemas))))
    return result


@lru_cache(maxsize=128)
def templates(source, function):
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef) and node.name == function:
            return sorted({call.args[0].value for call in ast.walk(node)
                           if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                           and call.func.id == "render_template" and call.args
                           and isinstance(call.args[0], ast.Constant)
                           and isinstance(call.args[0].value, str)
                           and re.fullmatch(r"[a-z0-9_/-]+/[a-z0-9_-]+\.html", call.args[0].value)})
    return []


def catalog(path, worker):
    active, status = worker("/active")
    base = ({key: active.get(key) for key in ("revision", "generation")} if status == 200 else None)
    if status != 200:
        worker_status, code = worker("/status")
        state = worker_status.get("lab_revision") if code == 200 else None
        if isinstance(state, dict):
            base = {key: state.get(key) for key in ("revision", "generation")}
    entries = {}
    files = {}

    def read(name):
        if name not in files:
            file = ROOT / name
            try:
                files[name] = file.read_bytes() if file.resolve() == file and file.is_file() else None
            except OSError:
                files[name] = None
        return files[name]

    def add(kind, identity, label, detail, description, contract, sources=(), *, scope=None):
        hashes = {name: digest(data) for name in sources if (data := read(name)) is not None}
        record = {"kind": kind, "label": label, **contract}
        key = digest(json.dumps([kind, identity, scope]).encode())[:32]
        version = digest(json.dumps([record, hashes, base], sort_keys=True).encode())
        entries[key] = (dict(id=key, revision=version, kind=kind, label=label, detail=detail,
                             description=description, service=contract.get("service")),
                        record, hashes)

    def add_file(name, route):
        if read(name) is not None:
            add("file", name, name.rsplit("/", 1)[-1], name, "Archivo de origen", {"file": name, "route": route}, [name])

    try:
        matched, _ = current_app.url_map.bind_to_environ(request.environ).match(path, method="GET", return_rule=True)
    except HTTPException:
        matched = None
    applications = [current_app]
    if reference_app := current_app.extensions.get("pliegue_orvia_routes"):
        applications.append(reference_app)
    for rule, view in ((rule, app.view_functions[rule.endpoint])
                       for app in applications for rule in app.url_map.iter_rules()):
        endpoint = rule.endpoint
        allowed = getattr(view, "orvia_roles", None)
        if allowed is not None and ADMINISTRADOR not in allowed:
            continue
        module = ("app.pliegue_lab" if endpoint in {"lab_home", "lab_demo"}
                  and current_app.config.get("PLIEGUE_LAB") else view.__module__)
        if endpoint == "static" or (endpoint.startswith("pliegue.") and endpoint != "pliegue.code_page"):
            continue
        if not module.startswith(("app.blueprints.", "app.pliegue_lab")):
            continue
        name = SIDEBAR.get(endpoint) or endpoint.rsplit(".", 1)[-1].replace("_", " ").capitalize()
        source = f"{module.replace('app.', WEB, 1).replace('.', '/')}.py"
        sources = [source]
        if endpoint in {"lab_page", "pliegue_orvia.active_page"}:
            continue
        route = rule.rule
        contract = {"endpoint": endpoint, "route": route, "methods": sorted(rule.methods - {"HEAD", "OPTIONS"}),
                    "file": source}
        detail = route if "GET" in rule.methods else f"{', '.join(contract['methods'])} {route}"
        add("web", [endpoint, route], name, detail, "Ruta web Flask", contract, sources)
        if endpoint in SIDEBAR and "GET" in rule.methods:
            add("sidebar", endpoint, name, route, "Sección de navegación", contract, sources)
        if matched is rule:
            program = read(source)
            page_templates = [WEB + "templates/" + name for name in templates(program, unwrap(view).__name__)] if program else []
            if endpoint == "panel.principal":
                page_templates = [WEB + "templates/panel/interno.html"]
            if endpoint == "returns_dashboard.dashboard":
                page_templates = [DASHBOARD]
                sources.extend(DASHBOARD_FILES)
            sources.extend(name for name in page_templates if name not in sources)
            for file in sources:
                add_file(file, route)
            for name in page_templates:
                data = read(name)
                if not data:
                    continue
                identifiers = set(re.findall(rb"""<[^<>]+?\s+id=["']([a-zA-Z][a-zA-Z0-9_-]{0,79})["']""", data))
                components = {"#" + item.decode("ascii"): item.decode("ascii") for item in sorted(identifiers)}
                if name == DASHBOARD:
                    if "#returns-title" in components:
                        components["#returns-title"] = "Título de estadísticas"
                    if b'class="returns-filters"' in data:
                        components[".returns-filters"] = "Filtros de devoluciones"
                for selector, label in components.items():
                    add("component", [name, selector], label, route, "Componente de la página",
                        {"file": name, "route": route, "selector": selector}, [name], scope=route)

    pages_enabled = ("lab_page" in current_app.view_functions
                     or current_app.config.get("PLIEGUE_FASE6") and "pliegue_orvia.active_page" in current_app.view_functions)
    if pages_enabled and base and base["revision"]:
        for slug, page in active.get("pages", {}).items():
            if not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", slug):
                continue
            file = f"{WEB}pliegue_pages/{slug}.json"
            route = f"/laboratorio/paginas/{slug}"
            contract = {"file": file, "route": route, "slug": slug}
            sidebar = page["sidebar"]
            add("page", slug, page["title"], route, "Página aprobada de Pliegue", contract)
            add("sidebar", slug, sidebar, route, "Sección de navegación", contract)
        match = re.fullmatch(r"/laboratorio/paginas/([a-z][a-z0-9-]{0,39})", path)
        if match:
            slug = match[1]
            if slug in active.get("pages", {}):
                file = f"{WEB}pliegue_pages/{slug}.json"
                add("file", file, f"{slug}.json", file, "Documento aprobado de Pliegue", {"file": file, "route": path})
                page, code = worker(f"/visual/{slug}")
                selection = page.get("selection", {}) if code == 200 else {}
                revision = selection.get("revision", {})
                if revision and all(revision.get(key) == value for key, value in base.items()):
                    for identity, element in selection.get("elements", {}).items():
                        if not element.get("label"):
                            continue
                        contract = {key: element[key] for key in ("file", "location", "tag") if key in element}
                        contract.update(route=path, element=identity, **({"part": element["part"]} if "part" in element else {}))
                        add("component", identity, element["label"], path, element["type"], contract, scope=path)

    for configured, _, _ in SERVICIOS:
        service = configured.replace("-", "_")
        source = f"services/{service}/app.py"
        contract_file = f"services/{service}/openapi.yaml"
        program, spec = read(source), read(contract_file)
        if not program or not spec:
            continue
        operations = service_operations(program, spec)
        contract = {"service": service, "file": source, "openapi": contract_file}
        add("service", service, service, f"{len(operations)} endpoints", "Microservicio", contract, [source, contract_file])
        for route, method, pointer, schemas in operations:
            label = f"{method} {route}"
            description = f"Endpoint de {service}"
            if schemas:
                description += " · Esquemas " + ", ".join(schemas)
            add("endpoint", [service, method, route], label, f"{service} · OpenAPI", description,
                {**contract, "method": method, "route": route, "operation": pointer, "schemas": schemas},
                [source, contract_file])
    return entries, base
