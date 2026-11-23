"""Pliegue: revisiones visuales y acceso privado a borradores de código del worker."""
import copy
import hashlib
import fcntl
from contextlib import contextmanager
import json
import os
import re
import secrets
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

from flask import Blueprint, abort, current_app, g, jsonify, render_template, request, session, url_for
from werkzeug.wsgi import get_input_stream
from app.pliegue_preview import css_samples
from app.pliegue_worker import worker_request
from app.security import ADMINISTRADOR, rol_actual, usuario_actual

bp = Blueprint("pliegue", __name__, url_prefix="/pliegue")
orvia = Blueprint("pliegue_orvia", __name__)
_lock = RLock()


@contextmanager
def _exclusive():
    """Bloqueo entre workers Gunicorn del mismo host Linux."""
    with _lock:
        with (_store() / ".lock").open("a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _fingerprint(config):
    return hashlib.sha256(json.dumps(config, sort_keys=True).encode("utf-8")).hexdigest()


def _store():
    # En WSL, /srv/app no suele existir; conservar la ruta Docker original.
    default = ("/srv/app/.pliegue_runtime" if Path("/srv/app").is_dir()
               else str(Path.home() / "Orvia-Pliegue20/.pliegue_runtime/visual"))
    loc = Path(os.environ.get("PLIEGUE_STORE", default))
    loc.mkdir(parents=True, exist_ok=True)
    return loc


def _read():
    f = _store() / "state.json"
    if not f.exists():
        return {"published": {"title_color": None, "group_returns": False}, "version": 0, "history": [], "drafts": [], "events": []}
    return json.loads(f.read_text(encoding="utf-8"))


def _save(value):
    dest = _store() / "state.json"
    fd, tmp = tempfile.mkstemp(dir=dest.parent, prefix=".pliegue-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(value, out, ensure_ascii=False, indent=2)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _admin():
    # A diferencia de una restricción visual, este guard se aplica a CADA petición.
    if not usuario_actual():
        abort(401)
    if rol_actual() != ADMINISTRADOR:
        abort(403)


def _csrf():
    expected = session.get("pliegue_csrf")
    got = request.headers.get("X-Pliegue-CSRF")
    if not expected or not got or not got.isascii() or not secrets.compare_digest(str(expected), got):
        abort(403)
    if request.mimetype != "application/json":
        abort(415)


def _owner():
    return str(usuario_actual()["id"])


def _find(state, draft_id):
    return next((d for d in state["drafts"] if d["id"] == draft_id and d["owner"] == _owner()), None)


def _record(state, action, value=None):
    state["events"].append({"at": datetime.now(timezone.utc).isoformat(), "actor": _owner(), "action": action, "revision": value})
    state["events"] = state["events"][-500:]


# Cambios declarativos de DOM: no ejecutan código arbitrario ni modifican bases de datos.
_ALLOWED_SELECTOR = re.compile(r"^main(?: > [a-z][a-z0-9-]*:nth-of-type\([1-9][0-9]*\)){1,14}$")
_COLORS = {
    "azul": "#2563eb", "verde": "#00875e", "verde esmeralda": "#00875e",
    "rojo": "#dc2626", "naranja": "#ea580c", "morado": "#7c3aed",
    "negro": "#102746", "gris": "#64748b", "blanco": "#ffffff",
}


def _interpret(prompt, settings, target=None, page=""):
    text = prompt.casefold().strip()
    result = copy.deepcopy(settings)
    result.setdefault("edits", [])
    actions = []
    # Conservar la configuración existente y los dos ejemplos originales.
    if any(word in text for word in ("titulo", "título", "panel general")) and not target:
        if any(word in text for word in ("original", "anterior", "regresa", "restaura", "restablece")):
            result["title_color"] = None
            actions.append("Se restauró el color original del título de Panel.")
        elif "azul" in text:
            result["title_color"] = "#2563eb"
            actions.append("El título de Panel se verá azul.")
    if "devolucion" in text or "devolució" in text or "agrup" in text:
        if "desagrupar" in text or "sin agrupar" in text:
            result["group_returns"] = False
            actions.append("Se quitó la agrupación visual de devoluciones.")
        elif "agrup" in text and ("estado" in text or "inspecci" in text):
            result["group_returns"] = True
            actions.append("Las devoluciones se ordenarán visualmente por estado, primero inspección.")
    if target and isinstance(target, dict):
        selector = str(target.get("selector", ""))
        label = str(target.get("label", ""))[:160]
        page = str(page)[:180]
        if not _ALLOWED_SELECTOR.fullmatch(selector) or not page.startswith("/") or page.startswith("//"):
            return result, []
        key = page + "::" + selector
        edits = result["edits"]
        # Seleccionar un nuevo elemento no borra las modificaciones a otros elementos.
        def put(kind, value):
            edits[:] = [e for e in edits if not (e.get("key") == key and e.get("kind") == kind)]
            edits.append({"key": key, "page": page, "selector": selector, "kind": kind, "value": value})
        if any(w in text for w in ("oculta", "ocúltalo", "ocultalo", "ocultar", "esconde", "elimina", "elimínalo", "eliminar", "quita", "quitar")):
            put("hidden", True)
            actions.append("El elemento seleccionado estará oculto en esta pantalla (reversible).")
        elif any(w in text for w in ("muestra", "mostrar", "recupera", "restaura elemento")):
            put("hidden", False)
            actions.append("El elemento seleccionado volverá a mostrarse.")
        elif any(w in text for w in ("renombra", "renombrar", "cambia el texto", "cambiar el texto", "cambia el título", "cambiar el título", "reemplaza", "sustituye")):
            # Acepta texto entre comillas, o instrucción '... por ...'.
            quoted = re.findall(r'[“"«](.*?)[”"»]', prompt)
            if quoted:
                new_text = quoted[-1].strip()
            else:
                m = re.search(r"(?:\bpor\b|\ba\b|\bcomo\b)\s+(.+)$", prompt, re.IGNORECASE)
                new_text = m.group(1).strip() if m else ""
            if new_text and len(new_text) <= 160:
                put("text", new_text)
                actions.append("El texto del elemento seleccionado se cambiará a: " + new_text)
        elif any(w in text for w in ("agrega", "añade", "insertar", "inserta")):
            quoted = re.findall(r'[“"«](.*?)[”"»]', prompt)
            m = re.search(r"(?:texto|mensaje)\s*[:：]\s*(.+)$", prompt, re.IGNORECASE)
            new_text = (quoted[-1] if quoted else m.group(1) if m else "").strip()
            if new_text and len(new_text) <= 500:
                put("note", new_text)
                actions.append("Se agregará una nota de texto después del elemento seleccionado.")
        else:
            original = any(w in text for w in ("original", "anterior", "restaura", "restablece", "regresa"))
            color = next((code for name,code in sorted(_COLORS.items(), key=lambda x:-len(x[0])) if name in text), None)
            if original and any(w in text for w in ("color", "titulo", "título")):
                put("color", None)
                actions.append("El elemento seleccionado recuperará su color original.")
            elif color and any(w in text for w in ("color", "hazlo", "ponlo", "píntalo", "pintalo", "cambia", "verde", "azul", "rojo")):
                put("color", color)
                actions.append("El elemento seleccionado cambiará de color.")
    return result, actions


_CODE_ENDPOINTS = {
    "pliegue.code_page", "pliegue.codex_status", "pliegue.code_drafts", "pliegue.code_visual",
    "pliegue.code_create", "pliegue.code_draft", "pliegue.code_preview", "pliegue.code_cancel",
    "pliegue.code_comparison", "pliegue.code_decision", "pliegue.code_active",
    "pliegue.code_rollback", "pliegue.code_redo", "pliegue.code_mentions", "pliegue.codex_session",
}


@bp.before_request
def access_check():
    safe_visual = {
        "pliegue.status", "pliegue.chat", "pliegue.draft", "pliegue.preview",
        "pliegue.apply", "pliegue.discard", "pliegue.undo", "pliegue.live",
    }
    if current_app.config.get("PLIEGUE_LAB") and request.endpoint not in _CODE_ENDPOINTS | safe_visual:
        abort(404)
    if request.endpoint == "pliegue.live":
        if not usuario_actual(): abort(401)
        return
    _admin()
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        _csrf()


@bp.get("/status")
def status():
    with _exclusive():
        s = _read()
        if "pliegue_csrf" not in session:
            session["pliegue_csrf"] = secrets.token_urlsafe(32)
        own = [d for d in s["drafts"] if d["owner"] == _owner()]
        return jsonify(version=s["version"], published=s["published"], drafts=own, csrf=session["pliegue_csrf"])


@bp.post("/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    prompt = str(payload.get("message", ""))[:1000]
    target = payload.get("target")
    if not isinstance(target, (dict, list)):
        target = None
    if isinstance(target, list):
        if not 1 <= len(target) <= 8 or not all(isinstance(t, dict) and
                set(t).issubset({"selector", "label"}) and "selector" in t for t in target):
            return jsonify(error="Selección múltiple inválida."), 400
        if len({t["selector"] for t in target}) != len(target):
            return jsonify(error="Elementos duplicados en la selección."), 400
    page = str(payload.get("path", ""))[:180]
    if not prompt.strip():
        return jsonify(error="Escribe una petición"), 400
    draft_id = str(payload.get("draft_id", ""))
    with _exclusive():
        s = _read()
        draft = _find(s, draft_id)
        if draft_id and not draft:
            return jsonify(error="Borrador no encontrado o no autorizado"), 404
        if not draft:
            draft = {"id": secrets.token_urlsafe(18), "owner": _owner(), "base": s["version"], "config": copy.deepcopy(s["published"]), "messages": [], "previewed_hash": None}
            s["drafts"].append(draft)
        if isinstance(target, list):
            result = copy.deepcopy(draft["config"])
            actions = []
            for selected in target:
                result, updates = _interpret(prompt, result, selected, page)
                if not updates:
                    return jsonify(error="Hay un elemento sin cambio visual permitido."), 422
                actions.extend(updates)
        else:
            result, actions = _interpret(prompt, draft["config"], target, page)
        if not actions:
            return jsonify(error="No pude interpretar esa petición como edición visual segura. Selecciona un título o texto y pide: cambia el texto por «Nuevo texto», hazlo azul, ocúltalo o agrega texto: «Nota». Los cambios funcionales de código requieren un entorno aislado de Codex."), 422
        draft["config"] = result
        draft["previewed_hash"] = None
        draft["messages"].append({"input": prompt, "result": actions})
        _record(s, "draft_edit", draft["id"])
        _save(s)
        return jsonify(draft=draft, reply=" ".join(actions))


@bp.get("/draft/<draft_id>")
def draft(draft_id):
    with _exclusive():
        d = _find(_read(), draft_id)
        if not d: abort(404)
        return jsonify(d)


@bp.post("/preview/<draft_id>")
def preview(draft_id):
    """Marca solo el snapshot que el administrador abrió en la vista privada."""
    with _exclusive():
        s = _read()
        d = _find(s, draft_id)
        if not d: abort(404)
        d["previewed_hash"] = _fingerprint(d["config"])
        _record(s, "preview", draft_id)
        _save(s)
        return jsonify(ok=True, previewed_hash=d["previewed_hash"])


@bp.post("/apply/<draft_id>")
def apply(draft_id):
    with _exclusive():
        s = _read()
        d = _find(s, draft_id)
        if not d: abort(404)
        if d.get("previewed_hash") != _fingerprint(d["config"]):
            return jsonify(error="Debes abrir y verificar esta revisión en Vista previa antes de aplicar"), 409
        if d["base"] != s["version"]:
            return jsonify(error="La versión publicada cambió. Descarta y crea un borrador nuevo."), 409
        # Guardar la versión anterior, y publicar de forma atómica solo el snapshot probado.
        s["history"].append({"version": s["version"], "config": copy.deepcopy(s["published"]), "actor": _owner()})
        s["published"] = copy.deepcopy(d["config"])
        s["version"] += 1
        s["drafts"] = [x for x in s["drafts"] if x["id"] != d["id"]]
        _record(s, "publish", s["version"])
        _save(s)
        return jsonify(ok=True, version=s["version"])


@bp.post("/discard/<draft_id>")
def discard(draft_id):
    with _exclusive():
        s = _read()
        if not _find(s, draft_id): abort(404)
        s["drafts"] = [x for x in s["drafts"] if x["id"] != draft_id]
        _record(s, "discard", draft_id)
        _save(s)
        return jsonify(ok=True)


@bp.post("/undo")
def undo():
    with _exclusive():
        s = _read()
        if not s["history"]: return jsonify(error="No hay revisión anterior"), 409
        previous = s["history"].pop()
        s["published"] = previous["config"]
        s["version"] += 1
        s["drafts"] = []
        _record(s, "undo", s["version"])
        _save(s)
        return jsonify(ok=True, version=s["version"])


def public_context():
    # NO devuelve borradores de otros usuarios, ni tokens, ni historial privado.
    try:
        s = _read()
        result = {"published": s["published"], "version": s["version"]}
        if rol_actual() == ADMINISTRADOR:
            requested = request.args.get("pliegue_preview", "")
            d = _find(s, requested) if requested else None
            if d:
                result["draft"] = d["config"]
                result["draft_id"] = d["id"]
        return result
    except (OSError, ValueError, KeyError):
        return {"published": {"title_color": None, "group_returns": False}, "version": 0}


@bp.get("/live")
def live():
    with _exclusive():
        s = _read()
        response = jsonify(published=s["published"], version=s["version"])
        response.headers["Cache-Control"] = "no-store"
        return response


def _worker_response(method, path, payload=None):
    return _private_json(*worker_request(method, path, _owner(), payload))


def _private_json(data, status_code):
    response = jsonify(data)
    response.status_code = status_code
    response.headers["Cache-Control"] = "no-store"
    return response


def code_csrf():
    if "pliegue_csrf" not in session:
        session["pliegue_csrf"] = secrets.token_urlsafe(32)
    return session["pliegue_csrf"]


@bp.get("/codigo")
def code_page():
    return render_template("pliegue/codigo.html", csrf=code_csrf()), 200, {
        "Cache-Control": "no-store",
    }


@bp.get("/codex")
def codex_status():
    return _worker_response("GET", "/status")


@bp.route("/codex/session", methods=["GET", "POST"])
def codex_session():
    if not (current_app.config.get("PLIEGUE_LAB") and current_app.config.get("PLIEGUE_VISUAL")):
        abort(404)
    payload = None
    if request.method == "POST":
        if not request.is_json:
            abort(415)
        if not request.content_length or request.content_length > 256:
            abort(400)
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or set(payload) != {"action"} or payload["action"] not in ("login", "logout"):
            abort(400)
    # The one-time code is visible only to the browser session that requested it.
    scope = hashlib.sha256(f"{_owner()}:{code_csrf()}".encode()).hexdigest()
    return _private_json(*worker_request(request.method, "/codex-session", scope, payload))


def orvia_pages():
    if not current_app.config.get("PLIEGUE_FASE6") or rol_actual() != ADMINISTRADOR:
        return {}
    if "pliegue_orvia_pages" not in g:
        data, status = worker_request("GET", "/active", _owner())
        g.pliegue_orvia_pages = data.get("pages", {}) if status == 200 else {}
    return g.pliegue_orvia_pages


@orvia.get("/laboratorio/paginas/<slug>")
def active_page(slug):
    if not current_app.config.get("PLIEGUE_FASE6"):
        abort(404)
    _admin()
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", slug):
        abort(404)
    page = orvia_pages().get(slug)
    if page is None:
        abort(404)
    return render_template("pliegue/lab_page.html", page=page,
                           page_layout="panel/interno.html", pliegue_workspace=True), 200, {
        "Cache-Control": "no-store",
        "Referrer-Policy": "no-referrer",
    }


def _mention_catalog(path):
    from app.pliegue_mentions import catalog
    return catalog(path, lambda endpoint: worker_request("GET", endpoint, _owner()))


def _mention_path(path):
    return isinstance(path, str) and len(path) <= 512 and path.startswith("/") and not path.startswith("//")


@bp.get("/codex/mentions")
def code_mentions():
    path = request.args.get("path", "/")
    if not _mention_path(path):
        return _private_json({"error": "Página de referencia inválida."}, 400)
    entries, _ = _mention_catalog(path)
    return _private_json({"items": [public for public, _, _ in entries.values()]}, 200)


@bp.get("/codex/drafts")
def code_drafts():
    return _worker_response("GET", "/jobs")


@bp.post("/codex/drafts")
def code_create():
    limit = 376_832
    if not request.content_length or request.content_length > limit:
        return jsonify(error="Tamaño de solicitud inválido."), 413
    if request.content_length <= 8192:
        payload = request.get_json(silent=True)
    else:
        # This authenticated JSON endpoint has its own bounded binary envelope.
        try:
            payload = json.loads(get_input_stream(request.environ, max_content_length=limit).read(limit + 1))
        except (ValueError, RecursionError):
            payload = None
        if not isinstance(payload, dict) or not isinstance(payload.get("attachments"), list) or not any(
            isinstance(file, dict) and "base64" in file for file in payload["attachments"]
        ):
            return _private_json({"error": "Tamaño de solicitud inválido."}, 413)
    message = payload.get("message") if isinstance(payload, dict) else None
    if not isinstance(message, str) or not message.strip() or len(message) > 1000:
        return jsonify(error="Escribe una petición de hasta 1000 caracteres."), 400
    # Defensa en profundidad: un #datos jamás se convierte en edición de Codex
    # aunque el navegador no cargue JS o se seleccione Editar.
    if re.search(r"(?:^|\s)#(?:datos|postgres|bd)(?=\s|:|$)", message, re.I):
        return _private_json({"error": "#datos es una consulta en vivo de PostgreSQL. Usa Pliegue Consultar; no se envió a Codex ni a una copia."}, 422)
    mode = payload.get("mode", "edit")
    if mode not in ("consult", "edit"):
        return _private_json({"error": "Modo de Pliegue inválido."}, 400)
    job = {"message": message.strip()}
    if "request_id" in payload:
        request_id = payload["request_id"]
        if not isinstance(request_id, str) or not re.fullmatch(r"[0-9a-f]{32}", request_id):
            return _private_json({"error": "Identificador de solicitud inválido."}, 400)
        job["request_id"] = request_id
    if "continuation" in payload:
        if not isinstance(payload["continuation"], str) or not re.fullmatch(r"[0-9a-f]{32}", payload["continuation"]):
            return _private_json({"error": "Borrador de origen inválido."}, 400)
        job["continuation"] = payload["continuation"]
    if "attachments" in payload:
        job["attachments"] = payload["attachments"]
    if mode == "consult":
        job["mode"] = mode
    references = payload.get("mentions", [])
    if references != []:
        from app.pliegue_mentions import LIMIT
        path = payload.get("mention_page")
        if (not isinstance(references, list) or not 0 < len(references) <= LIMIT
                or not _mention_path(path)):
            return _private_json({"error": "Referencias inválidas."}, 400)
        entries, base = _mention_catalog(path)
        resolved, seen = [], set()
        for reference in references:
            if (not isinstance(reference, dict) or set(reference) != {"id", "revision"}
                    or not isinstance(reference["id"], str) or not isinstance(reference["revision"], str)):
                return _private_json({"error": "Referencia inválida."}, 400)
            key = reference["id"]
            if key in seen or key not in entries or entries[key][0]["revision"] != reference["revision"]:
                return _private_json({"error": "La referencia ya no está disponible en esta revisión. Quita el chip y vuelve a seleccionarlo."}, 409)
            seen.add(key)
            _, record, hashes = entries[key]
            resolved.append({"resource": record, "sources": hashes})
        job["mention_context"] = {"base": base, "references": resolved}
    if "selection" in payload:
        if not current_app.config.get("PLIEGUE_VISUAL"):
            abort(404)
        if not isinstance(payload["selection"], dict):
            abort(400)
        job.update(selection=payload["selection"], allow_behavior=payload.get("allow_behavior") is True)
    return _worker_response("POST", "/jobs", job)


@bp.get("/codex/visual/<slug>", defaults={"draft_id": None})
@bp.get("/codex/visual/<slug>/<draft_id>")
def code_visual(slug, draft_id):
    if (not current_app.config.get("PLIEGUE_VISUAL")
            or not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", slug)
            or (draft_id is not None and not re.fullmatch(r"[0-9a-f]{32}", draft_id))):
        abort(404)
    return _worker_response("GET", f"/visual/{slug}" + (f"/{draft_id}" if draft_id else ""))


@bp.get("/codex/drafts/<draft_id>")
def code_draft(draft_id):
    if not re.fullmatch(r"[0-9a-f]{32}", draft_id):
        abort(404)
    data, status = worker_request("GET", "/jobs/" + draft_id, _owner(), None)
    if status == 200 and css_samples(data):
        data["preview_url"] = url_for("pliegue.code_preview", draft_id=draft_id)
    if status == 200 and data.get("state") in {"ready", "tests_failed", "approved", "rejected", "reverted"}:
        visual = data.get("visual_preview") or {}
        data["comparison_reason"] = visual.get("limitation", "")
        version = visual.get("version", "")
        if re.fullmatch(r"[0-9a-f]{64}", version):
            data["comparison_url"] = url_for("pliegue.code_comparison", draft_id=draft_id, version=version)
        else:
            data["comparison_reason"] = visual.get("reason") or (
                "Este borrador se creó sin una captura original para la comparación de la pantalla."
            )
    return _private_json(data, status)


@bp.post("/codex/drafts/<draft_id>/cancel")
def code_cancel(draft_id):
    if not re.fullmatch(r"[0-9a-f]{32}", draft_id):
        abort(404)
    return _worker_response("POST", f"/jobs/{draft_id}/cancel", {})


@bp.post("/codex/drafts/<draft_id>/comparison/<version>")
def code_comparison(draft_id, version):
    if not re.fullmatch(r"[0-9a-f]{32}", draft_id) or not re.fullmatch(r"[0-9a-f]{64}", version):
        abort(404)
    response = _worker_response("GET", f"/jobs/{draft_id}/comparison/{version}")
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.get("/codex/drafts/<draft_id>/preview")
def code_preview(draft_id):
    if not re.fullmatch(r"[0-9a-f]{32}", draft_id):
        abort(404)
    data, status = worker_request("GET", "/jobs/" + draft_id, _owner(), None)
    if status != 200:
        return _private_json(data, status)
    samples = css_samples(data)
    if not samples:
        abort(404)
    return render_template("pliegue/css_preview.html", samples=samples), 200, {
        "Cache-Control": "no-store",
        "Content-Security-Policy": (
            "sandbox; default-src 'none'; style-src 'unsafe-inline'; "
            "base-uri 'none'; form-action 'none'; frame-ancestors 'self'"
        ),
        "Referrer-Policy": "no-referrer",
        "X-Content-Type-Options": "nosniff",
    }


def _require_revisions():
    # Fase 5 tiene revisiones reales del worker. Autorizar solo cuando el
    # socket autentificado confirme ese soporte; no fingirlo con un flag JS.
    if (current_app.config.get("PLIEGUE_FASE6") or
            (current_app.config.get("PLIEGUE_LAB") and current_app.config.get("PLIEGUE_REVISIONS"))):
        return
    data, code = worker_request("GET", "/status", _owner())
    if code != 200 or not isinstance(data.get("lab_revision"), dict):
        abort(404)


def _decision_payload():
    if request.content_length is None or request.content_length > 8192:
        abort(413)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        abort(400)
    return payload


@bp.post("/codex/drafts/<draft_id>/<any(approve,reject):action>")
def code_decision(draft_id, action):
    _require_revisions()
    if not re.fullmatch(r"[0-9a-f]{32}", draft_id):
        abort(404)
    return _worker_response("POST", f"/jobs/{draft_id}/{action}", _decision_payload())


@bp.get("/codex/active")
def code_active():
    _require_revisions()
    response = _worker_response("GET", "/active")
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.post("/codex/rollback")
def code_rollback():
    _require_revisions()
    return _worker_response("POST", "/rollback", _decision_payload())


@bp.post("/codex/redo")
def code_redo():
    _require_revisions()
    return _worker_response("POST", "/redo", _decision_payload())
