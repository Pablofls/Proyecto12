"""Transactional, private storage for the laboratory's approved snapshots."""
import base64
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from difflib import unified_diff
import hashlib
from html.parser import HTMLParser
import json
import os
import re
import sqlite3
import uuid
import zlib

from pliegue_worker.builder import PAGE, PREFIX, page_changes
from pliegue_worker.preview_renderer import style_tag
from pliegue_worker.visual_preview import VISUAL_FILES

PANEL = VISUAL_FILES["templates"]["panel/interno.html"]
STYLES = set(VISUAL_FILES["styles"].values())
JINJA = re.compile(r"{%.*?%}|{{.*?}}|{#.*?#}", re.S)
MARKER = re.compile(r"PLIEGUEJINJATOKEN\d+END", re.I)
CSS_RESOURCE = re.compile(r"\\|@|\b(?:url|image-set|image|src)\s*\(", re.I)


class Conflict(ValueError):
    pass


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def manifest(tree):
    return {name: [digest(data), executable] for name, (data, executable) in sorted(tree.items())}


def fingerprint(tree):
    return digest(json.dumps(manifest(tree)).encode())


CSS_SYNTAX = re.compile(
    r'''/\*.*?\*/|/(?!\*)|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[{}()[\]]|[^/"'{}()[\]]+''',
    re.S,
)


def checked_css(before, after):
    # Existing resource directives may remain. Changed lines cannot introduce them.
    for line in list(unified_diff(before.splitlines(), after.splitlines(), n=0))[2:]:
        if line.startswith(("-", "+")) and CSS_RESOURCE.search(line[1:]):
            raise Conflict("Los cambios CSS con recursos o directivas externas no son compatibles.")
    if "</style" in after.lower() or "\x00" in after:
        raise Conflict("El marcado dentro de los estilos no es compatible.")
    stack = []
    position = 0
    pairs = {"}": "{", ")": "(", "]": "["}
    for token in CSS_SYNTAX.finditer(after):
        value = token[0]
        if token.start() != position:
            raise Conflict("Los estilos contienen comentarios o cadenas incompletas.")
        position = token.end()
        if value in pairs.values():
            stack.append(value)
        elif value in pairs and (not stack or stack.pop() != pairs[value]):
            raise Conflict("Los estilos contienen delimitadores sin pareja.")
    if stack or position != len(after):
        raise Conflict("Los estilos contienen sintaxis incompleta.")


class PanelStructure(HTMLParser):
    """Compare template structure, bindings and script bodies without executing them."""

    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.tokens = []
        self.styles = []
        self.inside = None
        self.feed(source)
        self.close()

    def handle_starttag(self, tag, attrs):
        self.tokens.append((tag, tuple(
            (name, tuple(MARKER.findall(value or "")) if name in {"style", "class"} else value)
            for name, value in attrs if name != "style" or MARKER.search(value or "")
        )))
        for name, value in attrs:
            if name == "style":
                checked_css("", value or "")
        if tag in {"script", "style"}:
            self.inside = tag
            if tag == "style":
                self.styles.append("")

    def handle_endtag(self, tag):
        self.tokens.append(("/" + tag,))
        if tag == self.inside:
            self.inside = None

    def handle_data(self, data):
        if self.inside == "style":
            self.styles[-1] += data
        if self.inside == "script":
            self.tokens.append(("script", data))
        else:
            self.tokens.extend(MARKER.findall(data))

    def handle_comment(self, data):
        self.tokens.append(("comment", data))

    def handle_decl(self, decl):
        self.tokens.append(("decl", decl))

    def handle_pi(self, data):
        self.tokens.append(("pi", data))


def check_changes(before, after, pair=None):
    changed = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
    if not changed:
        raise Conflict("El borrador no contiene diferencias.")
    # Native Flask templates: audited static comparison for code drafts.
    # Approved revisions still live ONLY in the private lab snapshot; this
    # branch never writes back to the Flask repository or PostgreSQL.
    if pair and pair.get("generic_screens"):
        screens = pair["generic_screens"]
        if (pair.get("reviewed_paths") != changed
                or pair.get("reviewed_before") != fingerprint(before)
                or pair.get("reviewed_after") != fingerprint(after)
                or not isinstance(screens, list) or not 1 <= len(screens) <= 3):
            raise Conflict("El contenido aprobado no coincide con los archivos de la comparación.")
        for screen in screens:
            if (not isinstance(screen, dict) or not isinstance(screen.get("title"), str)
                    or not isinstance(screen.get("before"), str)
                    or not isinstance(screen.get("after"), str)
                    or not screen.get("before") or not screen.get("after")
                    or screen["before"] == screen["after"] or screen.get("static") is not True):
                raise Conflict("Falta una comparación visual estática válida.")
            name = "apps/web/app/templates/" + screen["title"]
            if name not in changed or name not in after:
                raise Conflict("La vista previa no corresponde a un HTML modificado.")
        restricted = (
            "apps/web/app/security.py", "apps/web/app/db.py", "apps/web/app/config.py",
            "apps/web/app/__init__.py", "apps/web/app/pliegue_asistente_roles.py",
            "apps/web/app/blueprints/pliegue.py", "apps/web/app/blueprints/auth.py",
        )
        if any(name.startswith("pliegue_worker/") or name in restricted
               or name.startswith(("db/", "services/", "shared/")) for name in changed):
            raise Conflict("Autenticación, bases, migraciones y microservicios requieren revisión funcional independiente.")
        for name in changed:
            if name in after and name.endswith(".css"):
                # New feature CSS may legitimately use @media/@supports. Forbid
                # network/resource directives, not ordinary CSS at-rules.
                new_css = after[name][0].decode("utf-8")
                if re.search(r"@(?:import|font-face|namespace)\b|(?:url|image-set|src)\s*\(", new_css, re.I) or "</style" in new_css.lower() or "\x00" in new_css:
                    raise Conflict("No se permiten recursos externos ni HTML dentro de CSS del borrador.")
            if name in after and name.endswith(".py"):
                new_source = after[name][0].decode("utf-8")
                old_source = before[name][0].decode("utf-8") if name in before else ""
                broad_roles = re.compile(r"@roles_required\s*\(\s*\*\s*TODOS(?:_LOS_ROLES)?\b")
                if broad_roles.search(new_source) and not broad_roles.search(old_source):
                    raise Conflict("No es seguro exponer una ruta nueva a todos los roles sin validar el ámbito de datos.")
        return changed
    page_files = [name for name in changed if name.startswith(PREFIX)]
    if page_files:
        if any(not PAGE.fullmatch(name) for name in page_files):
            raise Conflict("Solo se admiten documentos JSON de página con rutas válidas.")
        try:
            pages = page_changes(before, after)
        except ValueError as exc:
            raise Conflict(str(exc)) from exc
        if not pair or pages != pair.get("pages"):
            raise Conflict("Los documentos de página no coinciden con la comparación revisada.")
    for name in changed:
        if name in page_files:
            continue
        if pair and pair.get('panel') is False:
            raise Conflict(f'El cambio en {name} no aparece en la comparación revisada.')
        if name not in STYLES | {PANEL} or name not in before or name not in after:
            raise Conflict(f"Solo se admiten cambios visuales revisados. Archivo fuera del alcance aprobable: {name}.")
        old, old_exec = before[name]
        new, new_exec = after[name]
        if old_exec != new_exec or b"\0" in new:
            raise Conflict("El archivo visual debe ser texto y conservar sus permisos originales.")
        old, new = old.decode(), new.decode()
        if name in STYLES:
            checked_css(old, new)
            if pair and (style_tag(old) not in pair["before"] or style_tag(new) not in pair["after"]):
                raise Conflict("La pantalla revisada no incluye una de las hojas de estilo modificadas.")
            continue
        structures = []
        bindings = []
        for source in (old, new):
            if MARKER.search(source):
                raise Conflict("La plantilla contiene marcadores reservados.")
            source = source.replace("\r\n", "\n")
            tokens = JINJA.findall(source)
            markers = iter(range(len(tokens)))
            structures.append(PanelStructure(JINJA.sub(lambda _: f"PLIEGUEJINJATOKEN{next(markers)}END", source)))
            bindings.append(tokens)
        first, second = structures
        if bindings[0] != bindings[1] or first.tokens != second.tokens or second.inside:
            raise Conflict("El HTML solo admite cambios de texto, clases y estilos que conservan la estructura, Jinja y los scripts.")
        for a, b in zip(first.styles, second.styles, strict=True):
            checked_css(a, b)
    return changed


class Revisions:
    def __init__(self, directory):
        self.path = directory / "revisions.sqlite3"
        fd = os.open(self.path, os.O_CREAT | os.O_NOFOLLOW | os.O_RDWR, 0o600)
        os.close(fd)
        with self.transaction() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS revisions (
                id TEXT PRIMARY KEY, previous TEXT REFERENCES revisions(id), snapshot BLOB NOT NULL,
                manifest TEXT NOT NULL, preview TEXT NOT NULL, preview_hash TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS events (
                number INTEGER PRIMARY KEY, state TEXT NOT NULL, draft TEXT UNIQUE,
                owner TEXT NOT NULL, at TEXT NOT NULL,
                previous TEXT REFERENCES revisions(id), revision TEXT REFERENCES revisions(id),
                files TEXT, review TEXT, reason TEXT, warnings TEXT)""")
            db.execute("""CREATE TABLE IF NOT EXISTS active (
                singleton INTEGER PRIMARY KEY CHECK(singleton = 1), revision TEXT REFERENCES revisions(id),
                generation INTEGER NOT NULL)""")
            db.execute("INSERT OR IGNORE INTO active VALUES (1, NULL, 0)")
            for table in ("revisions", "events"):
                for operation in ("UPDATE", "DELETE"):
                    db.execute(f"""CREATE TRIGGER IF NOT EXISTS {table}_no_{operation.lower()}
                               BEFORE {operation} ON {table}
                               BEGIN SELECT RAISE(ABORT, 'Registro inmutable'); END""")

    @contextmanager
    def transaction(self, write=True):
        with closing(sqlite3.connect(self.path, timeout=3)) as db, db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA synchronous=FULL")
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield db

    def status(self, db):
        row = db.execute("""SELECT a.revision, a.generation, r.previous
                            FROM active a LEFT JOIN revisions r ON a.revision = r.id""").fetchone()
        return dict(row)

    def snapshot(self, db, revision):
        row = db.execute("SELECT * FROM revisions WHERE id = ?", (revision,)).fetchone()
        if row is None:
            raise Conflict("La revisión guardada no está disponible.")
        try:
            tree = {name: (base64.b64decode(data, validate=True), mode)
                    for name, (data, mode) in json.loads(zlib.decompress(row["snapshot"])).items()}
            valid = (manifest(tree) == json.loads(row["manifest"])
                     and digest(row["preview"].encode()) == row["preview_hash"])
        except (AttributeError, ValueError, TypeError, zlib.error):
            valid = False
        if not valid:
            raise Conflict("El contenido de la revisión guardada no coincide con su manifiesto.")
        return tree, row["preview"]

    def insert(self, db, previous, tree, preview):
        revision = uuid.uuid4().hex
        data = {name: [base64.b64encode(content).decode("ascii"), mode]
                for name, (content, mode) in tree.items()}
        db.execute("INSERT INTO revisions VALUES (?, ?, ?, ?, ?, ?)",
                   (revision, previous, zlib.compress(json.dumps(data).encode()),
                    json.dumps(manifest(tree)), preview, digest(preview.encode())))
        return revision

    def activate(self, db, revision):
        db.execute("UPDATE active SET revision = ?, generation = generation + 1", (revision,))

    def event(self, db, state, owner, *, draft=None, previous=None, revision=None,
              files=None, review=None, reason=None, warnings=None):
        db.execute("""INSERT INTO events (state, draft, owner, at, previous, revision, files,
                      review, reason, warnings) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                   (state, draft, owner, timestamp(), previous, revision,
                    json.dumps(files), review, reason, json.dumps(warnings)))

    def decision(self, db, draft):
        row = db.execute("SELECT * FROM events WHERE draft = ?", (draft,)).fetchone()
        if row is None:
            return {}
        state = row["state"]
        reversal = db.execute("SELECT * FROM events WHERE state = 'reverted' AND previous = ? ORDER BY number DESC LIMIT 1",
                              (row["revision"],)).fetchone() if state == "approved" else None
        if reversal:
            restored = db.execute("SELECT number FROM events WHERE state = 'redone' AND revision = ? AND number > ? ORDER BY number DESC LIMIT 1",
                                  (row["revision"], reversal["number"])).fetchone()
            if restored:
                reversal = None
        return {"state": "reverted" if reversal else state, "decision": {
            "at": row["at"], "owner": row["owner"], "reason": row["reason"],
            "revision": row["revision"], "previous": row["previous"],
            "reverted_at": reversal["at"] if reversal else None,
            "reverted_by": reversal["owner"] if reversal else None,
        }}
