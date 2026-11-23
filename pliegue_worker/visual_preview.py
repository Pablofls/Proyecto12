"""Build the immutable visual comparison outside the Codex workspace."""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from pliegue_worker.builder import ABSENT, PREFIX, GeneratedScript, page_changes
from pliegue_worker.preview_renderer import MAX_BUNDLE, STYLES, TEMPLATES
from pliegue_worker.process_output import run_render

WEB = "apps/web/app/"
GENERIC_RENDERER = Path(__file__).with_name("preview_generic_renderer.py").resolve()
MAX_GENERIC_TEMPLATES = 24

VISUAL_FILES = {
    "templates": {name: WEB + "templates/" + name for name in TEMPLATES},
    "styles": {name: WEB + "static/css/" + name for name in STYLES},
}
RENDERER = Path(__file__).with_name("preview_renderer.py").resolve()
UNSUPPORTED = "La comparación admite el Panel general y los documentos validados de página."



def _tree_fingerprint(tree):
    """Same deterministic manifest digest as revisions.fingerprint, without imports."""
    manifest = {name: [hashlib.sha256(blob).hexdigest(), executable]
                for name, (blob, executable) in sorted(tree.items())}
    return hashlib.sha256(json.dumps(manifest).encode()).hexdigest()


def prepare_preview(folder, job, before, after, functional=None, functional_reason=None):
    pages, reason, static = {}, None, False
    if any(path.startswith(PREFIX) and before.get(path) != after.get(path)
           for path in before.keys() | after.keys()):
        try:
            pages = page_changes(before, after)
        except GeneratedScript as exc:
            reason = str(exc)
            try:
                pages = page_changes(before, after, static_fallback=True)
                static = bool(pages)
                if static:
                    reason += " Se muestra una vista estática con el código ejecutable omitido."
            except ValueError as fallback:
                reason += f" {fallback}"
        except ValueError as exc:
            reason = str(exc)
    panel = panel_preview(folder, before, after)
    # Fallback for native Flask HTML views created by Codex. This preview is
    # inert and illustrative; it never runs Flask, routes, scripts or SQL.
    generic = []
    if not pages and not functional:
        generic = generic_preview(folder, before, after)
    reason = functional_reason or reason
    if not pages and not functional and not generic and "before" not in panel:
        if not reason and panel["reason"] == UNSUPPORTED:
            changed = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
            reason = f"Archivos fuera de la vista previa: {', '.join(changed[:6])}. " + UNSUPPORTED if changed else UNSUPPORTED
        return {"reason": reason or panel["reason"]}
    comparison = panel if "before" in panel else {"before": ABSENT, "after": ABSENT}
    if functional:
        comparison.update(functional=functional, panel="before" in panel)
    if generic:
        comparison.update(generic_screens=generic, panel="before" in panel,
                          reviewed_before=_tree_fingerprint(before), reviewed_after=_tree_fingerprint(after),
                          reviewed_paths=sorted(name for name in before.keys() | after.keys()
                          if before.get(name) != after.get(name)))
    if pages:
        comparison.update(pages=pages, panel="before" in panel)
        if static:
            comparison["static_pages"] = True
        if not reason and "before" not in panel and panel["reason"] != UNSUPPORTED:
            reason = panel["reason"]
    if reason:
        comparison["limitation"] = reason
    rendered = json.dumps(comparison).encode()
    if len(rendered) > MAX_BUNDLE:
        return {"reason": "La comparación multipágina supera el límite de tamaño."}
    version = hashlib.sha256(f'{job["owner"]}:{job["id"]}:'.encode() + rendered).hexdigest()
    temporary = folder / "comparison.tmp"
    temporary.write_bytes(rendered)
    temporary.chmod(0o600)
    temporary.replace(folder / "comparison.json")
    result = {"version": version}
    if generic:
        result["generic_screens"] = [{"title": item["title"], "static": True} for item in generic]
    if pages:
        result["pages"] = [{**value["page"], "features": [], "static": True} if static else value["page"]
                           for value in pages.values()]
    if reason:
        result["limitation"] = reason
    return result



def generic_preview(folder, before, after):
    """Render native Jinja pages from both snapshots, offline and inert.

    Every visual mock is marked as simulated. A missing or invalid render
    does not produce an approval proof. This cannot establish backend safety.
    """
    changed = sorted(name for name in before.keys() | after.keys()
                     if before.get(name) != after.get(name))
    template_prefix = WEB + "templates/"
    html = [name for name in changed if name.startswith(template_prefix) and name.endswith(".html")
            and name not in {template_prefix + "base.html", template_prefix + "_sidebar.html",
                             template_prefix + "_topbar.html"}]
    if not html or len(html) > 3:
        return []
    targets = sorted(html, key=lambda path: (path in before, path))

    def sources(tree, changed_styles):
        # Supply common Jinja includes plus each modified page. No arbitrary
        # paths can be loaded by the isolated render; DictLoader only.
        names = {"base.html", "_sidebar.html", "_topbar.html", "_campanita.html", "componentes.html"}
        names.update(path.removeprefix(template_prefix) for path in targets)
        available = {name: tree[template_prefix + name][0].decode("utf-8")
                     for name in names if template_prefix + name in tree}
        if sum(len(s) for s in available.values()) > 800_000:
            raise ValueError("La página necesita separar la revisión en partes")
        styles = {path.removeprefix(WEB + "static/css/"): item[0].decode("utf-8")
                  for path, item in tree.items() if path.startswith(WEB + "static/css/")
                  and path.endswith(".css") and len(item[0]) < 190_000}
        if sum(len(s) for s in styles.values()) > 550_000:
            styles = {name: code for name, code in styles.items() if name in STYLES}
        return {"templates": available, "styles": styles,
                "modified_styles": changed_styles}

    changed_styles = [name.removeprefix(WEB + "static/css/") for name in changed
                      if name.startswith(WEB + "static/css/") and name.endswith(".css")]
    output = []
    for target in targets:
        try:
            payload = json.dumps({"target": target.removeprefix(template_prefix),
                "before": sources(before, changed_styles), "after": sources(after, changed_styles)}).encode()
            if len(payload) > 2_300_000:
                return []
            venv_python = GENERIC_RENDERER.parents[1] / ".venv/bin/python"
            interpreter = str(venv_python) if venv_python.is_file() else sys.executable
            with tempfile.TemporaryFile(dir=folder) as stream:
                status = run_render([interpreter, "-I", "-B", str(GENERIC_RENDERER)],
                    input=payload, stdout=stream, stderr=subprocess.DEVNULL,
                    env={"LANG": "C.UTF-8"}, cwd=folder, close_fds=True, timeout=12)
                stream.seek(0)
                raw = stream.read(MAX_BUNDLE + 1)
            if status or len(raw) > MAX_BUNDLE:
                return []
            result = json.loads(raw)
            if not all(isinstance(result.get(x), str) for x in ("before", "after")):
                return []
            output.append({"title": result["title"], "before": result["before"],
                           "after": result["after"], "static": True})
        except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired):
            return []
    return output


def panel_preview(folder, before, after):
    paths = {path for group in VISUAL_FILES.values() for path in group.values()}
    if not any(before.get(path) != after.get(path) for path in paths):
        return {"reason": UNSUPPORTED}

    def sources(tree):
        return {
            kind: {
                name: tree[path][0].decode("utf-8")
                for name, path in sorted(files.items()) if path in tree
            }
            for kind, files in VISUAL_FILES.items()
        }

    try:
        payload = json.dumps({"before": sources(before), "after": sources(after)}).encode()
        if len(payload) > 2_000_000:
            return {"reason": "Los archivos de la pantalla superan el límite de la vista previa."}
        venv_python = RENDERER.parents[1] / ".venv/bin/python"
        interpreter = str(venv_python) if venv_python.is_file() else sys.executable
        with tempfile.TemporaryFile(dir=folder) as output:
            code = run_render(
                [interpreter, "-I", "-B", str(RENDERER)], input=payload,
                stdout=output, stderr=subprocess.DEVNULL, env={"LANG": "C.UTF-8"},
                cwd=folder, close_fds=True, timeout=10,
            )
            output.seek(0)
            rendered = output.read(MAX_BUNDLE + 1)
        if code == 2:
            return {"reason": "Los cambios compatibles no producen una diferencia en el documento estático."}
        if code or len(rendered) > MAX_BUNDLE:
            raise ValueError
        comparison = json.loads(rendered)
        if not all(isinstance(comparison.get(key), str) for key in ("before", "after")):
            raise ValueError
        return comparison
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {"reason": "No se pudo generar de forma aislada. La pantalla usa recursos o plantillas no compatibles, o el aislamiento no está disponible."}


def read_preview(folder, owner, job, version):
    if job["state"] not in {"ready", "tests_failed", "approved", "rejected", "reverted"} or job.get("visual_preview", {}).get("version") != version:
        return None
    try:
        with (folder / "comparison.json").open("rb") as stream:
            data = stream.read(MAX_BUNDLE + 1)
        if len(data) > MAX_BUNDLE:
            return None
        expected = hashlib.sha256(f'{owner}:{job["id"]}:'.encode() + data).hexdigest()
        return json.loads(data) if expected == version else None
    except (OSError, ValueError):
        return None
