"""Pliegue: consultas operativas explícitas por rol y preferencias personales.

Las consultas son SQL parametrizadas de SOLO LECTURA. Los usuarios no administradores
NO pasan su pregunta a Codex: el servidor decide fuente y ámbito mediante sesión.
Los temas no soportados se rechazan sin ejecutar SQL ni revelar datos ajenos.
"""
import hashlib
import json
import os
import re
import secrets
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, abort, g, jsonify, request, session
from app.db import consultar
from app.security import (
    ADMINISTRADOR, ANALISTA, CLIENTE, INSPECTOR, ENCARGADO_CENTRO,
    COORDINADOR, ENCARGADO_REEMBOLSOS, rol_actual, usuario_actual,
)

bp = Blueprint("pliegue_roles", __name__, url_prefix="/pliegue-asistente")

# Roles adicionales comprobados en la BD (22-nov-2026). Se mantienen
# encapsulados aquí: NO se amplía app.security.INTERNOS ni otros endpoints.
OPERADOR_ALMACEN = "Operador de Almacen"
RECOLECTOR = "Recolector"
SUPERVISOR = "Supervisor"

ROLE_TOPICS = {
    CLIENTE: ("mis devoluciones", "mis ventas", "mi folio", "ayuda"),
    INSPECTOR: ("inspecciones pendientes", "mis inspecciones", "ayuda"),
    ENCARGADO_CENTRO: ("inspecciones", "recolecciones", "ayuda"),
    COORDINADOR: ("mis recolecciones", "pendientes por programar", "ayuda"),
    ANALISTA: ("devoluciones", "inspecciones", "reembolsos", "costos", "ventas", "ayuda"),
    ENCARGADO_REEMBOLSOS: ("reembolsos", "costos", "ayuda"),
    ADMINISTRADOR: ("devoluciones", "inspecciones", "recolecciones", "reembolsos", "ventas", "costos", "usuarios", "ayuda"),
    # No se permite información ajena ni financiera por inferencia del nombre.
    OPERADOR_ALMACEN: ("inventario recuperado por estado", "ayuda"),
    RECOLECTOR: ("mis recolecciones asignadas", "ayuda"),
    SUPERVISOR: ("resumen de devoluciones", "inspecciones pendientes", "inventario recuperado", "ayuda"),
}
PALETTES = {
    "esmeralda": ("#087f5b", "#e5f5ed"),
    "azul": ("#2563eb", "#eaf1ff"),
    "morado": ("#7545b8", "#f1eaff"),
    "grafito": ("#334155", "#eff2f5"),
    "turquesa": ("#087f8c", "#e4f7f8"),
}
FONTS = {"inter": 'Inter, "Segoe UI", sans-serif', "sistema": 'system-ui, sans-serif', "serif": 'Georgia, serif'}


def _plain(text):
    s = unicodedata.normalize("NFKD", str(text or "").casefold())
    return "".join(c for c in s if not unicodedata.combining(c))


def _user():
    u = usuario_actual()
    if not isinstance(u, dict) or not u.get("id"):
        abort(401)
    if rol_actual() not in ROLE_TOPICS:
        abort(403)
    return u


def _write_guard():
    token = session.get("pliegue_roles_csrf")
    header = request.headers.get("X-Pliegue-Roles-CSRF", "")
    if not token or not header or not secrets.compare_digest(token, header):
        abort(403)
    if not request.is_json or request.content_length is None or request.content_length > 4096:
        abort(415)


def _theme_file():
    user = _user()
    root = Path(os.environ.get("PLIEGUE_ROLE_PREFERENCES", str(Path.home() / ".pliegue_role_preferences")))
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if root.is_symlink():
        abort(503)
    slug = hashlib.sha256(str(user["id"]).encode("utf-8")).hexdigest()
    result = root / (slug + ".json")
    if result.is_symlink():
        abort(503)
    return result


def _read_theme():
    p = _theme_file()
    if not p.exists():
        return {"palette": "esmeralda", "font": "inter", "radius": "suave"}
    try:
        v = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {"palette": "esmeralda", "font": "inter", "radius": "suave"}
    if not isinstance(v, dict):
        return {"palette": "esmeralda", "font": "inter", "radius": "suave"}
    return {
        "palette": v.get("palette") if v.get("palette") in PALETTES else "esmeralda",
        "font": v.get("font") if v.get("font") in FONTS else "inter",
        "radius": v.get("radius") if v.get("radius") in ("suave", "recto") else "suave",
    }


def _write_theme(theme):
    p = _theme_file()
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".perfil-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(theme, out, ensure_ascii=False)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _read_sql(sql, args=(), single=False):
    """SQL parametrizado bajo transacción READ ONLY; fuente app.db de Flask."""
    from app.db import get_conn
    if not g.get("pliegue_sql_read_only"):
        with get_conn().cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
        g.pliegue_sql_read_only = True
    return consultar(sql, tuple(args), uno=single)


def _counts(rows):
    return {str(r["estado"]): int(r["total"]) for r in rows}


def _describe_counts(label, rows):
    values = _counts(rows)
    total = sum(values.values())
    detail = ", ".join(f"{state.replace('_', ' ')}: {value}" for state, value in sorted(values.items()))
    return f"{label}: {total} en total. " + ("Por estado: " + detail + "." if detail else "No hay registros.")


def _returns(role, user, question):
    # El filtro por usuario se ejecuta en SQL, no en JS ni en el prompt de Codex.
    if role == CLIENTE:
        folio = re.search(r"\bDEV[-_][A-Z0-9-]{3,40}\b", question, re.I)
        if folio:
            row = _read_sql("""SELECT d.folio_devolucion, d.estado, d.fecha_solicitud
                 FROM devoluciones d JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
                 JOIN ventas v ON v.id = vd.venta_id
                 WHERE v.cliente_id = %s AND d.eliminado_en IS NULL AND UPPER(d.folio_devolucion) = UPPER(%s)""",
                 (user["id"], folio.group(0)), single=True)
            if not row:
                return "No encuentro ese folio entre tus devoluciones autorizadas."
            return f"Tu devolución {row['folio_devolucion']} tiene estado: {str(row['estado']).replace('_', ' ')}."
        rows = _read_sql("""SELECT d.estado, COUNT(*) AS total FROM devoluciones d
             JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
             JOIN ventas v ON v.id = vd.venta_id
             WHERE v.cliente_id = %s AND d.eliminado_en IS NULL GROUP BY d.estado""", (user["id"],))
        return _describe_counts("Tus devoluciones", rows)
    if role not in (ANALISTA, ADMINISTRADOR):
        abort(403)
    rows = _read_sql("SELECT estado, COUNT(*) AS total FROM devoluciones WHERE eliminado_en IS NULL GROUP BY estado")
    return _describe_counts("Devoluciones registradas", rows)


def _sales(role, user):
    if role == CLIENTE:
        row = _read_sql("SELECT COUNT(*) AS total FROM ventas WHERE cliente_id = %s AND eliminado_en IS NULL", (user["id"],), single=True)
        return f"Tienes {int(row['total'])} ventas registradas."
    if role not in (ANALISTA, ADMINISTRADOR):
        abort(403)
    row = _read_sql("SELECT COUNT(*) AS total FROM ventas WHERE eliminado_en IS NULL", single=True)
    return f"Ventas registradas: {int(row['total'])}."


def _inspections(role, user):
    if role not in (INSPECTOR, ENCARGADO_CENTRO, ANALISTA, ADMINISTRADOR):
        abort(403)
    row = _read_sql("""SELECT COUNT(*) AS total FROM devoluciones d
        WHERE d.estado IN ('recibida','en_inspeccion') AND d.eliminado_en IS NULL
        AND NOT EXISTS (SELECT 1 FROM inspecciones_ref i WHERE i.devolucion_id = d.id)""", single=True)
    pending = int(row["total"])
    if role == INSPECTOR:
        done = _read_sql("SELECT COUNT(*) AS total FROM inspecciones_ref WHERE inspector_id = %s", (user["id"],), single=True)
        return f"Inspecciones pendientes en la cola: {pending}. Inspecciones registradas por ti: {int(done['total'])}."
    return f"Inspecciones pendientes: {pending}."


def _logistics(role, user):
    if role not in (COORDINADOR, ENCARGADO_CENTRO, ADMINISTRADOR):
        abort(403)
    if role == COORDINADOR:
        rows = _read_sql("SELECT estado, COUNT(*) AS total FROM recolecciones WHERE coordinador_id = %s GROUP BY estado", (user["id"],))
        msg = _describe_counts("Tus recolecciones coordinadas", rows)
    else:
        rows = _read_sql("SELECT estado, COUNT(*) AS total FROM recolecciones GROUP BY estado")
        msg = _describe_counts("Recolecciones registradas", rows)
    if role in (COORDINADOR, ADMINISTRADOR):
        pending = _read_sql("""SELECT COUNT(*) AS total FROM devoluciones d
          WHERE d.estado = 'autorizada' AND d.eliminado_en IS NULL
          AND NOT EXISTS (SELECT 1 FROM recolecciones r WHERE r.devolucion_id = d.id)""", single=True)
        msg += f" Pendientes por programar: {int(pending['total'])}."
    return msg


def _column_available(table, column):
    """Únicamente se consulta metadato de las dos relaciones previstas."""
    if (table, column) not in {
        ("recolecciones", "recolector_id"),
        ("transportistas", "usuario_id"),
    }:
        raise ValueError("Metadato de asignación no permitido")
    row = _read_sql("""SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = ANY(current_schemas(false))
          AND table_name = %s AND column_name = %s
    ) AS disponible""", (table, column), single=True)
    return bool(row and row["disponible"])


def _pickups_for_collector(role, user):
    """Solo asignaciones verificablemente vinculadas al usuario de la sesión.

    Nunca equiparar transportista_id (FK a transportistas) con usuario.id.
    """
    if role != RECOLECTOR:
        abort(403)
    if _column_available("recolecciones", "recolector_id"):
        rows = _read_sql("""SELECT estado, COUNT(*) AS total
            FROM recolecciones WHERE recolector_id = %s GROUP BY estado""", (user["id"],))
        return _describe_counts("Tus recolecciones asignadas", rows)
    if _column_available("transportistas", "usuario_id"):
        rows = _read_sql("""SELECT r.estado, COUNT(*) AS total
            FROM recolecciones r JOIN transportistas t ON t.id = r.transportista_id
            WHERE t.usuario_id = %s GROUP BY r.estado""", (user["id"],))
        return _describe_counts("Tus recolecciones asignadas", rows)
    return ("No puedo mostrarte asignaciones personales todavía: la base no "
            "contiene un vínculo verificable entre tu usuario y las "
            "recolecciones. Por seguridad no mostraré rutas de otros usuarios.")


def _inventory_summary(role):
    """Solo conteos por estado, sin productos, clientes ni etiquetas."""
    if role not in (OPERADOR_ALMACEN, SUPERVISOR):
        abort(403)
    rows = _read_sql("""SELECT estado, COUNT(*) AS total
        FROM inventario_recuperado GROUP BY estado""")
    return _describe_counts("Inventario recuperado", rows)


def _supervisor_returns(role):
    if role != SUPERVISOR:
        abort(403)
    rows = _read_sql("""SELECT estado, COUNT(*) AS total
        FROM devoluciones WHERE eliminado_en IS NULL GROUP BY estado""")
    return _describe_counts("Resumen de devoluciones", rows)


def _supervisor_inspections(role):
    if role != SUPERVISOR:
        abort(403)
    row = _read_sql("""SELECT COUNT(*) AS total FROM devoluciones d
        WHERE d.estado IN ('recibida', 'en_inspeccion') AND d.eliminado_en IS NULL
        AND NOT EXISTS (SELECT 1 FROM inspecciones_ref i WHERE i.devolucion_id = d.id)""", single=True)
    return f"Inspecciones pendientes en la cola: {int(row['total'])}."


def _refunds(role, user):
    if role not in (ENCARGADO_REEMBOLSOS, ANALISTA, ADMINISTRADOR):
        abort(403)
    if role == ENCARGADO_REEMBOLSOS:
        rows = _read_sql("SELECT estado, COUNT(*) AS total FROM reembolsos WHERE eliminado_en IS NULL AND encargado_id = %s GROUP BY estado", (user["id"],))
        msg = _describe_counts("Tus reembolsos registrados", rows)
    else:
        rows = _read_sql("SELECT estado, COUNT(*) AS total FROM reembolsos WHERE eliminado_en IS NULL GROUP BY estado")
        msg = _describe_counts("Reembolsos registrados", rows)
    pending = _read_sql("""SELECT COUNT(*) AS total FROM devoluciones d
      WHERE d.estado IN ('autorizada','en_recoleccion','recibida','en_inspeccion','resuelta')
        AND d.eliminado_en IS NULL AND NOT EXISTS (
        SELECT 1 FROM reembolsos rb WHERE rb.devolucion_id = d.id AND rb.eliminado_en IS NULL)""", single=True)
    return msg + f" Devoluciones pendientes de reembolso: {int(pending['total'])}."


def _costs(role):
    if role not in (ENCARGADO_REEMBOLSOS, ANALISTA, ADMINISTRADOR):
        abort(403)
    row = _read_sql("SELECT COALESCE(SUM(monto),0) AS total FROM costos", single=True)
    return f"Costo agregado registrado: ${row['total']}."


def _users(role):
    if role != ADMINISTRADOR:
        abort(403)
    row = _read_sql("SELECT COUNT(*) AS total FROM usuarios", single=True)
    return f"Usuarios registrados: {int(row['total'])}."


def _answer(q, role, user):
    plain = _plain(q)
    sensitive = ("contrasena", "password", "token", "secreto", "credencial", "borrar", "eliminar", "modificar", "actualizar datos", "cambia la base")
    if any(part in plain for part in sensitive):
        return "Esta conversación es de solo lectura. Para modificar datos o código se necesita la herramienta administrativa y aprobación específica.", "política de Pliegue"
    # Tres roles de BD adicionales. Autorizar exclusivamente resúmenes sin PII
    # o pertenencia verificable. No se envía ninguna pregunta a Codex.
    if role == RECOLECTOR:
        if any(k in plain for k in ("recolec", "ruta", "entrega", "asignacion", "asignad", "trabajo")):
            return _pickups_for_collector(role, user), "PostgreSQL · asignaciones verificadas por usuario"
        return ("Solo puedo consultar tus recolecciones asignadas cuando la "
                "base confirme que te pertenecen. No puedo consultar usuarios, "
                "datos de clientes ni información financiera."), "permisos por rol"
    if role == OPERADOR_ALMACEN:
        if any(k in plain for k in ("inventario", "almacen", "existencia", "stock", "disponib", "reservad")):
            return _inventory_summary(role), "PostgreSQL · inventario agregado por estado"
        return ("Puedo consultar el inventario recuperado agrupado por estado. "
                "No puedo consultar clientes, reembolsos ni el inventario de personas específicas."), "permisos por rol"
    if role == SUPERVISOR:
        # Usar límites de palabra para «venta»: «inventario» contiene esa
        # secuencia de letras, pero no es información comercial.
        if (any(k in plain for k in ("usuarios", "cuentas", "empleados", "correo", "contrasena", "credencial", "costo", "monto", "reembolso"))
                or re.search(r"\bventas?\b", plain)):
            return "Ese detalle no está incluido en tu acceso de supervisión.", "permisos por rol"
        if any(k in plain for k in ("inventario", "almacen", "stock", "existencia")):
            return _inventory_summary(role), "PostgreSQL · inventario agregado por estado"
        if any(k in plain for k in ("inspecc", "revision")):
            return _supervisor_inspections(role), "PostgreSQL · cola de inspecciones"
        if any(k in plain for k in ("devoluc", "casos", "solicitud", "estado", "resumen")):
            return _supervisor_returns(role), "PostgreSQL · resumen de estados"
        return ("Puedo ofrecer resúmenes agregados de devoluciones, "
                "inspecciones pendientes e inventario; no registros personales, "
                "financieros ni administración de usuarios."), "permisos por rol"
    # Si se pregunta por devoluciones que están *en inspección/recolección*,
    # corresponde usar d.estado como en el Panel, no el total de operaciones logísticas.
    if ("en inspeccion" in plain and "recoleccion" in plain and role in (ANALISTA, ADMINISTRADOR)):
        return _returns(role, user, q), "PostgreSQL · estados de devoluciones"
    if any(k in plain for k in ("devoluc", "folio")) and role in (CLIENTE, ANALISTA, ADMINISTRADOR):
        return _returns(role, user, q), "PostgreSQL · devoluciones visibles"
    topics = [
        (("usuarios", "empleados", "cuentas"), "usuarios", lambda: _users(role)),
        (("reembolso", "rembolso", "devolucion de dinero"), "reembolsos", lambda: _refunds(role, user)),
        (("costo", "gasto", "importe"), "costos", lambda: _costs(role)),
        (("recolec", "transporte", "logistica", "ruta", "recolect"), "recolecciones", lambda: _logistics(role, user)),
        (("inspecc", "inspector", "revision de productos"), "inspecciones", lambda: _inspections(role, user)),
        (("venta", "compra"), "ventas", lambda: _sales(role, user)),
        (("devoluc", "folio", "solicitud", "estado", "caso"), "devoluciones", lambda: _returns(role, user, q)),
    ]
    for keywords, topic, action in topics:
        if any(k in plain for k in keywords):
            allowed = {
                "usuarios": (ADMINISTRADOR,),
                "reembolsos": (ENCARGADO_REEMBOLSOS, ANALISTA, ADMINISTRADOR),
                "costos": (ENCARGADO_REEMBOLSOS, ANALISTA, ADMINISTRADOR),
                "recolecciones": (COORDINADOR, ENCARGADO_CENTRO, ADMINISTRADOR),
                "inspecciones": (INSPECTOR, ENCARGADO_CENTRO, ANALISTA, ADMINISTRADOR),
                "ventas": (CLIENTE, ANALISTA, ADMINISTRADOR),
                "devoluciones": (CLIENTE, ANALISTA, ADMINISTRADOR),
            }
            if role not in allowed[topic]:
                return "Esa información no está incluida en tus permisos de Pliegue. Puedes consultar únicamente datos de tu función.", "permisos por rol"
            return action(), "PostgreSQL · consulta autorizada"
    return ("Puedo consultar: " + ", ".join(ROLE_TOPICS[role]) + ". "
            "Los datos proceden de consultas en vivo y se limitan a tu rol."), "permisos por rol"


@bp.get("/conexion")
def conexion():
    """Comprobación real del PostgreSQL configurado para Flask; sin secretos."""
    _user()
    try:
        row = _read_sql("SELECT 1 AS ok", single=True)
        connected = bool(row and row["ok"] == 1)
    except Exception:
        connected = False
    return jsonify(connected=connected, source="PostgreSQL", read_only=True,
                   checked_at=datetime.now(timezone.utc).isoformat(timespec="seconds")), (200 if connected else 503), {"Cache-Control": "no-store"}


@bp.get("/config")
def config():
    user = _user()
    csrf = session.setdefault("pliegue_roles_csrf", secrets.token_urlsafe(32))
    return jsonify(role=rol_actual(), is_admin=(rol_actual() == ADMINISTRADOR),
                   user_id=str(user["id"]), csrf=csrf,
                   topics=ROLE_TOPICS[rol_actual()], theme=_read_theme()), 200, {"Cache-Control": "no-store"}


@bp.post("/consulta")
def consulta():
    user = _user()
    _write_guard()
    payload = request.get_json(silent=True)
    question = payload.get("message") if isinstance(payload, dict) else None
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 600:
        return jsonify(error="Escribe una pregunta de hasta 600 caracteres."), 400
    try:
        answer, source = _answer(question.strip(), rol_actual(), user)
    except Exception:
        # Fallo cerrado: sin trazas SQL, datos parciales ni secretos en la respuesta.
        return jsonify(error="La fuente de datos no está disponible. No se devolvieron cifras sin verificar."), 503
    return jsonify(reply=answer, source=source, as_of=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   role=rol_actual(), read_only=True), 200, {"Cache-Control": "no-store"}


@bp.get("/tema")
def tema_get():
    _user()
    return jsonify(theme=_read_theme()), 200, {"Cache-Control": "no-store"}


@bp.put("/tema")
def tema_put():
    _user()
    _write_guard()
    theme = request.get_json(silent=True)
    if not isinstance(theme, dict) or set(theme) != {"palette", "font", "radius"}:
        return jsonify(error="Ajuste visual no permitido."), 400
    if theme["palette"] not in PALETTES or theme["font"] not in FONTS or theme["radius"] not in ("suave", "recto"):
        return jsonify(error="Solo se permiten paleta, tipografía y bordes seguros."), 400
    _write_theme(theme)
    return jsonify(ok=True, theme=theme), 200, {"Cache-Control": "no-store"}


@bp.delete("/tema")
def tema_reset():
    _user()
    _write_guard()
    p = _theme_file()
    if p.exists():
        p.unlink()
    return jsonify(ok=True, theme=_read_theme()), 200, {"Cache-Control": "no-store"}
