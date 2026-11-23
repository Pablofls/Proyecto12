"""Approval gate and offline behavioral probes for known full-stack entry points."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from pliegue_worker.builder import css_text
from pliegue_worker.preview_renderer import InertHTML, style_tag
from pliegue_worker.process_output import run_render
from pliegue_worker.revisions import Conflict

WEB = "apps/web/app/"
CSS = WEB + "static/css/returns-dashboard.css"
JS = WEB + "static/js/returns-dashboard.js"
CONFIG = WEB + "returns_dashboard.json"
DASHBOARD = {
    CSS, JS, CONFIG, WEB + "returns_dashboard.py",
    WEB + "blueprints/returns_dashboard.py", WEB + "templates/devoluciones/dashboard.html",
}
FRAGMENT = WEB + "templates/devoluciones/dashboard_fragment.html"
SUPPORT = {WEB + name for name in ("__init__.py", "config.py", "cache.py", "db.py", "security.py", "api_client.py")}
SUPPORT |= {FRAGMENT, "shared/__init__.py", "shared/devoluciones_contract.py"}
CHECKS = Path(__file__).parent
LIMIT = 300_000


def functional_paths(before, after):
    changed = {path for path in before.keys() | after.keys() if before.get(path) != after.get(path)}
    return changed if changed & DASHBOARD else set()


def check_candidate(before, after):
    changed = functional_paths(before, after)
    if not changed <= DASHBOARD or not DASHBOARD <= after.keys() or any(after[path][1] for path in DASHBOARD):
        raise Conflict("La revisión funcional solo admite el ámbito verificado del dashboard. "
                       "Servicios, autenticación, migraciones, infraestructura y cambios sin pruebas específicas requieren revisión aparte.")
    try:
        config = json.loads(after[CONFIG][0], object_pairs_hook=no_duplicates)
        if (not isinstance(config, dict) or set(config) != {"title", "page_size"}
                or not isinstance(config["title"], str) or not 1 <= len(config["title"].strip()) <= 80
                or type(config["page_size"]) is not int or not 1 <= config["page_size"] <= 50):
            raise ValueError
        css_text(after[CSS][0].decode())
    except (ValueError, UnicodeError) as exc:
        raise Conflict("El CSS o el esquema JSON del dashboard no es válido.") from exc
    return sorted(changed), config


def no_duplicates(pairs):
    data = dict(pairs)
    if len(data) != len(pairs):
        raise ValueError("Clave JSON duplicada.")
    return data


def sandbox(root, stage, entry, payload=None):
    if entry == "phase7_probe.py":
        executable = Path(sys.executable).resolve()
        deps = next(iter((root / ".venv/lib").glob("python*/site-packages")), None)
        if not deps:
            raise Conflict("Faltan las dependencias aisladas de Flask de .venv.")
        mounts = ["--ro-bind", sys.base_prefix, "/python", "--ro-bind", str(deps), "/deps"]
        args = ["/python/bin/" + executable.name, "-I", "-S", "-B", "/checks/" + entry]
    else:
        node = next((path for path in (
            Path("/usr/bin/node"), root / ".pliegue_runtime/fase65-tools/python/playwright/driver/node",
        ) if path.is_file() and os.access(path, os.X_OK)), None)
        if not node:
            raise Conflict("Node no está disponible para probar el comportamiento JavaScript.")
        mounts = ["--ro-bind", str(node.resolve()), "/node"]
        args = ["/node", "--permission", "--allow-fs-read=/checks", "--allow-fs-read=/workspace",
                "--max-old-space-size=96", "/checks/" + entry]
    command = ["/usr/bin/prlimit", "--cpu=6", f"--fsize={LIMIT}", "--as=2147483648", "--nofile=64",
               "--core=0", "--", "/usr/bin/bwrap", "--unshare-all", "--die-with-parent",
               "--cap-drop", "ALL", "--clearenv", "--setenv", "LANG", "C.UTF-8", "--chdir", "/workspace",
               "--ro-bind", "/usr", "/usr", "--dev", "/dev",
               "--ro-bind", str(stage), "/workspace",
               "--ro-bind", str(CHECKS / entry), "/checks/" + entry, *mounts]
    for directory in ("/lib", "/lib64", "/bin"):
        if Path(directory).exists():
            command += ["--ro-bind", directory, directory]
    with tempfile.TemporaryFile(dir=stage.parent) as output:
        try:
            code = run_render(command + ["--", *args], input=json.dumps(payload).encode(),
                                    stdout=output, stderr=output, close_fds=True, timeout=12, env={})
            output.seek(0)
            raw = output.read(LIMIT + 1)
            if code or len(raw) > LIMIT:
                raise Conflict(f"Falló la ejecución aislada de {entry} (código {code}).")
            return json.loads(raw)
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            if isinstance(exc, Conflict):
                raise
            raise Conflict(f"No se completó la ejecución aislada de {entry}.") from exc


def cases():
    rows = [{"id": i, "folio_devolucion": f"FIXTURE-{i}", "producto": "Producto de contrato",
             "fecha_solicitud": f"2025-{'01' if i <= 100 else '02'}-01T00:00:00+00:00",
             "estado": "cerrada" if i <= 100 else "solicitada", "cantidad_devuelta": i}
            for i in range(1, 102)]
    admin = {"role": "Administrador", "rows": rows}
    requests = [
        {**admin, "paths": ["datos?mes=2025-02&q=folio", "datos?estado=cerrada", "datos?pagina=2",
                            "datos?estado=falso", "datos?mes=2025-42", "datos?pagina=999", "datos?mes=2026-01"]},
        {"rows": rows, "paths": ["datos"]},
        {"role": "Cliente", "rows": rows, "paths": ["datos", ""]},
        {**admin, "paths": ["datos"], "no_token": True},
        *[{**admin, "paths": ["datos"], "mode": mode}
          for mode in ("forbidden", "timeout", "malformed", "excess", "changed")],
        {**admin, "rows": rows[-3:], "paths": [""]},
    ]
    return requests


def require(condition, reason):
    if not condition:
        raise Conflict("Prueba de contrato del dashboard fallida: " + reason)


def verify_contract(result, page_size):
    public, anonymous, client, missing_token, forbidden, timeout, malformed, excess, changed, render = result
    month, state, second, invalid, bad_month, bad_page, empty = public
    require([entry["status"] for entry in public] == [200, 200, 200, 400, 400, 400, 200], "estado HTTP y filtros")
    for outcome, status in ((anonymous, 401), (client, 403), (missing_token, 503), (forbidden, 403),
                            (timeout, 503), (malformed, 502), (excess, 422), (changed, 502)):
        require(all(entry["status"] == status for entry in outcome), "autorización y errores")
    require(not any(entry["calls"] for entry in anonymous + client + missing_token + [invalid, bad_month]),
            "un inválido o un usuario sin permiso no debe consultar el servicio")
    calls = month["calls"]
    require(calls == [["GET", "/api/v1/devoluciones", "Bearer jwt-ficticio-prueba-contrato",
                       {"q": ["folio"], "pagina": [str(index)], "por_pagina": ["100"]}, 1, True] for index in (1, 2)],
            "JWT, ruta, filtros y contrato de paginación")
    require(state["calls"][0][3].get("estado") == ["cerrada"], "propagación del estado")
    for entry, total, units, states, first_id in (
        (month, 1, 101, {"solicitada": 1}, 101), (state, 100, 5050, {"cerrada": 100}, 1),
        (second, 101, 5151, {"cerrada": 100, "solicitada": 1}, 1 + page_size),
        (empty, 0, 0, {}, None),
    ):
        data = entry["json"]["datos"]
        require((data["total"], data["unidades"], data["estados"]) == (total, units, states), "consistencia KPI y gráfica")
        require(len(data["filas"]) == min(page_size, max(0, total - (data["pagina"] - 1) * page_size)), "tabla paginada")
        if first_id:
            require(data["filas"][0]["id"] == first_id and "cliente" not in data["filas"][0], "filas y minimización")
    rendered = render[0]
    require(rendered["status"] == 200 and "FIXTURE-99" in rendered["html"] and "<table" in rendered["html"]
            and "data-returns-chart" in rendered["html"] and "name=\"estado\"" in rendered["html"],
            "render, filtros, navegación y gráfica")
    return rendered["html"]


def execute(root, directory, tree, trusted, *, verify=True):
    with tempfile.TemporaryDirectory(dir=directory, prefix=".phase7-") as tmp:
        stage = Path(tmp)
        for path in sorted(DASHBOARD | SUPPORT):
            data, _ = (tree if path in DASHBOARD else trusted)[path]
            target = stage / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        result = sandbox(root, stage, "phase7_probe.py", cases())
        _, config = check_candidate(tree, tree)
        markup = verify_contract(result, config["page_size"])
        if verify:
            js = sandbox(root, stage, "phase7_probe.js")
            require(js == [[False, "true", "33.3%", "66.7%", "Mostrar cantidades"],
                           [False, "false", "1", "2", "Mostrar porcentajes"]], "interacción JavaScript de gráfica")
        parser = InertHTML({})
        parser.feed(markup)
        parser.close()
        require(not parser.dropped and parser.css is None, "sanitización de la captura")
        return style_tag(tree[CSS][0].decode()) + "".join(parser.parts)


def comparison(root, directory, before, after):
    try:
        paths, _ = check_candidate(before, after)
        previous = execute(root, directory, before, before, verify=False)
        candidate = execute(root, directory, after, before)
    except (Conflict, KeyError, OSError, TypeError, IndexError, ValueError) as exc:
        return None, str(exc) if isinstance(exc, Conflict) else "No se verificó el contrato funcional en el entorno aislado."
    return {"before": previous, "after": candidate, "paths": paths,
            "evidence": "Flask real en Bubblewrap con contrato HTTP simulado y sin red. "
                        "Node probó el control de la gráfica con un DOM de prueba. Capturas inertes con datos ficticios."}, None
