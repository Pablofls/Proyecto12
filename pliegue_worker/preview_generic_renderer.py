"""Trusted entry point for offline rendering. Draft input arrives only over stdin."""
import ctypes
import errno
import json
import os
import re
import resource
import sys
from datetime import datetime
from html import escape
from html.parser import HTMLParser

SCREEN = "panel/interno.html"
TEMPLATES = {SCREEN, "base.html", "_sidebar.html", "_campanita.html", "_topbar.html"}
STYLES = {"estilos.css", "sidebar-orvia.css", "pliegue.css", "topbar-orvia.css", "pliegue-roles.css", "pliegue-acabado.css", "pliegue-revision-v7.css"}
MAX_BUNDLE = 650_000

# No file opens, process creation, sockets, ioctl, or new descriptors. The
# launcher supplies only standard descriptors and closes all inherited descriptors.
SYSCALLS = """
read write close brk mmap munmap mprotect mremap madvise
rt_sigaction rt_sigprocmask rt_sigreturn sigaltstack
clock_gettime futex getpid gettid exit exit_group
""".split()


def isolate():
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_BUNDLE, MAX_BUNDLE))
    sec = ctypes.CDLL("libseccomp.so.2")
    sec.seccomp_init.argtypes = [ctypes.c_uint32]
    sec.seccomp_init.restype = ctypes.c_void_p
    sec.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    sec.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    sec.seccomp_load.argtypes = [ctypes.c_void_p]
    sec.seccomp_release.argtypes = [ctypes.c_void_p]
    context = sec.seccomp_init(0x00050000 | errno.EPERM)
    if not context:
        raise RuntimeError("seccomp")
    try:
        for name in SYSCALLS:
            syscall = sec.seccomp_syscall_resolve_name(name.encode())
            if syscall < 0 or sec.seccomp_rule_add(context, 0x7FFF0000, syscall, 0):
                raise RuntimeError("seccomp")
        # libseccomp also sets no_new_privs before installing the filter.
        if sec.seccomp_load(context):
            raise RuntimeError("seccomp")
    finally:
        sec.seccomp_release(context)


TAGS = set("""
body main header footer aside nav section article div span p h1 h2 h3 h4 h5 h6
a button label input select option optgroup textarea fieldset legend
table caption colgroup col thead tbody tfoot tr td th
ul ol li dl dt dd strong em b i small time br hr figure figcaption
details summary code pre blockquote mark img
svg g defs lineargradient radialgradient stop path circle rect line polyline polygon ellipse text tspan
""".split())
ATTRS = set("""
class id title role style hidden lang dir tabindex type name value placeholder
disabled checked selected multiple colspan rowspan scope width height
viewbox d x y x1 y1 x2 y2 cx cy r rx ry points offset stop-color stop-opacity
fill fill-rule fill-opacity stroke stroke-width stroke-linecap stroke-linejoin
stroke-dasharray stroke-opacity opacity transform gradientunits gradienttransform
preserveaspectratio
""".split())
VOID = {"br", "hr", "img", "input", "col"}
DROP = {"script", "iframe", "object", "embed", "template", "noscript", "title"}
RASTER = re.compile(r"data:image/(?:png|jpeg|webp|gif);base64,[A-Za-z0-9+/=]+")
STYLESHEET = re.compile(r"/preview-css/([a-z0-9-]+\.css)")


def style_tag(css):
    if "</style" in css.lower():
        raise ValueError("CSS no compatible")
    return "<style>" + css + "</style>"


class InertHTML(HTMLParser):
    def __init__(self, styles):
        super().__init__(convert_charrefs=True)
        self.styles = styles
        self.parts = []
        self.dropped = []
        self.css = None

    def handle_starttag(self, tag, attrs):
        if self.dropped:
            if tag in DROP and tag != "embed":
                self.dropped.append(tag)
            return
        if tag in DROP:
            if tag != "embed":
                self.dropped.append(tag)
            return
        attrs = dict(attrs)
        if tag == "link" and "stylesheet" in (attrs.get("rel") or "").lower().split():
            match = STYLESHEET.fullmatch(attrs.get("href") or "")
            if not match or match[1] not in self.styles:
                raise ValueError("Hoja de estilo no compatible")
            self.parts.append(style_tag(self.styles[match[1]]))
        elif tag == "style":
            self.css = []
        elif tag in TAGS:
            safe = {
                key: value or "" for key, value in attrs.items()
                if key in ATTRS or key.startswith(("aria-", "data-")) and re.fullmatch(r"[a-z0-9_-]+", key)
            }
            if tag == "body":
                safe["class"] = (safe.get("class", "") + " ov-panel-ready").strip()
            if tag == "input" and safe.get("type", "").lower() not in {
                "text", "search", "number", "checkbox", "radio", "date",
                "email", "hidden", "range", "button", "submit",
            }:
                safe["type"] = "text"
            if tag == "img" and RASTER.fullmatch(attrs.get("src") or ""):
                safe["src"] = attrs["src"]
                safe["alt"] = attrs.get("alt") or ""
            attributes = "".join(f' {key}="{escape(value, quote=True)}"' for key, value in safe.items())
            self.parts.append(f"<{tag}{attributes}>")

    def handle_endtag(self, tag):
        if self.dropped:
            if tag == self.dropped[-1]:
                self.dropped.pop()
            return
        if tag == "style" and self.css is not None:
            self.parts.append(style_tag("".join(self.css)))
            self.css = None
        elif tag in TAGS - VOID:
            self.parts.append(f"</{tag}>")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, text):
        if self.dropped:
            return
        if self.css is not None:
            self.css.append(text)
        else:
            self.parts.append(escape(text))


def fake_url(endpoint, **fields):
    if endpoint == "static":
        filename = fields.get("filename", "")
        if filename.startswith("css/"):
            return "/preview-css/" + filename[4:]
    return "#"


def fixture():
    states = ("en_inspeccion", "en_recoleccion", "cerrada")
    rows = [
        dict(id=i, folio_devolucion=f"DEMO-{i:03}", estado=state, producto=product,
             cliente=f"Cliente de muestra {i}", motivo=reason,
             clasificacion_temperatura="refrigerado" if i == 1 else "no_refrigerado",
             fecha_solicitud=datetime(2026, 11, 20 - i, 10, 30), ruta_recoleccion="Ruta demo")
        for i, (state, product, reason) in enumerate(zip(
            states, ("Pechuga de pollo", "Frijol", "Galletas"), ("Empaque", "Pedido", "Calidad")
        ), 1)
    ]
    return dict(
        usuario_actual={"nombre": "Andrea Demo"}, rol_actual="Administrador",
        resumen=[{"estado": state, "total": count} for state, count in zip(states, (7, 5, 12))],
        total=24, recientes=rows, modo_distribuido=False, pliegue_lab=False,
        pliegue_boot={}, lab_csrf="", TODOS=("Administrador",),
        request={"endpoint": "panel.principal"}, url_for=fake_url,
        get_flashed_messages=lambda **_: [],
    )


def render(sources):
    from jinja2 import DictLoader, StrictUndefined, select_autoescape
    from jinja2.sandbox import ImmutableSandboxedEnvironment

    env = ImmutableSandboxedEnvironment(
        loader=DictLoader(sources["templates"]), undefined=StrictUndefined,
        autoescape=select_autoescape(("html",)),
    )
    html = env.get_template(SCREEN).render(**fixture())
    original_nav = re.search(r'<nav class="menu">(.*?)</nav>', html, flags=re.S)
    if original_nav:
        links = original_nav[1].replace('class="activo"', 'class="activo" aria-current="page"')
        html = re.sub(r'(<nav id="ov-side-links"[^>]*>)(</nav>)',
                      lambda match: match[1] + links + match[2], html, count=1)
    bell = re.search(r'<div class="campanita".*?</a>', html, flags=re.S)
    if bell:
        html = html.replace('aria-label="Notificaciones"></div>',
                            'aria-label="Notificaciones">' + bell[0] + '</div></div>', 1)
    html = html.replace('id="ov-today-value">Fecha actual<', 'id="ov-today-value">20 nov 2026<')
    parser = InertHTML(sources["styles"])
    parser.feed(html)
    parser.close()
    if parser.dropped or parser.css is not None:
        raise ValueError("Marcado incompleto")
    return "".join(parser.parts)


from types import SimpleNamespace
class GenericHTML(InertHTML):
    def handle_starttag(self, tag, attrs):
        if tag == "link":
            values = dict(attrs)
            if "stylesheet" in str(values.get("rel", "")).lower().split():
                if not str(values.get("href", "")).startswith("/preview-css/"):
                    return  # External CSS is never used in static preview.
        super().handle_starttag(tag, attrs)

MAX_INPUT = 2_300_000
MAX_CSS = 210_000
CSS_DANGEROUS = re.compile(r"@import\b|url\s*\(|image-set\s*\(|expression\s*\(|</style", re.I)


def inert_style(css):
    if not isinstance(css, str) or len(css) > MAX_CSS or CSS_DANGEROUS.search(css):
        return ""  # CSS unsafe or externally linked: omit, never fetch.
    return css


def sample_rows():
    return [dict(
        id=1, folio_devolucion="EJEMPLO-001", estado="en_inspeccion",
        estado_recoleccion="pendiente", nombre="Registro ilustrativo",
        producto="Producto de muestra", motivo="Demostración",
        cliente="Cliente de ejemplo", capturado_en=datetime(2026, 11, 20, 10, 30),
        fecha_solicitud=datetime(2026, 11, 20, 10, 30), ubicacion=None,
        total=1, cantidad=1,
    )]


def render_markup(blob, name):
    if name not in blob.get("templates", {}):
        return ('<main class="pliegue-generic-empty"><h1>Página nueva</h1>'
                '<p>Esta pantalla no existía en la revisión anterior.</p></main>')
    from jinja2 import ChainableUndefined, DictLoader
    from jinja2.sandbox import ImmutableSandboxedEnvironment

    templates = blob["templates"]
    env = ImmutableSandboxedEnvironment(loader=DictLoader(templates), undefined=ChainableUndefined,
                                        autoescape=True)
    # Compile Jinja strictly: invalid template syntax fails closed (not disguised as HTML).
    for template in templates.values():
        env.parse(template)
    rows = sample_rows()
    user = {"id": 1, "nombre": "Administración (ejemplo)", "rol": "Administrador"}
    context = dict(
        url_for=fake_url, usuario_actual=user, rol_actual="Administrador", usuario=user,
        user=user, g=SimpleNamespace(user=user), session={},
        config={"PLIEGUE_LAB": False, "PLIEGUE_VISUAL": False, "PLIEGUE_GLOBAL_CODE": False},
        request=SimpleNamespace(endpoint="panel.principal", path="/panel", args={}),
        get_flashed_messages=lambda **_: [], csrf_token=lambda: "",
        devoluciones=rows, recientes=rows, ventas=rows, recolecciones=rows,
        total=1, resumen=[{"estado": "en_inspeccion", "total": 1}],
        rol="Administrador", TODOS=("Administrador",), modo_distribuido=False,
        pliegue_lab=False, pliegue_boot={}, lab_csrf="", pliegue_screen="",
    )
    html = env.get_template(name).render(**context)
    styles = {key: inert_style(value) for key, value in blob.get("styles", {}).items()}
    parser = GenericHTML(styles)
    parser.feed(html)
    parser.close()
    if parser.dropped or parser.css is not None:
        raise ValueError("HTML incompleto")
    markup = "".join(parser.parts)
    # Inline the changed stylesheet if the template did not reference it.
    # Inert iframe CSP disables all scripts, network requests and form submission.
    for css_name in sorted(blob.get("modified_styles", ())):
        css = styles.get(css_name)
        if css and f"{css}</style>" not in markup:
            markup = "<style>" + css + "</style>" + markup
    return markup


def main():
    try:
        # Load trusted modules BEFORE isolation shuts down opens.
        import jinja2.sandbox, jinja2.debug, jinja2.filters
        b"safe".decode("unicode-escape")
        isolate()
        raw = bytearray()
        while chunk := os.read(0, 65536):
            raw.extend(chunk)
            if len(raw) > MAX_INPUT:
                return 1
        request = json.loads(raw)
        name = request["target"]
        if not re.fullmatch(r"[a-z0-9_/-]+\.html", name) or ".." in name.split("/"):
            return 1
        before = render_markup(request["before"], name)
        after = render_markup(request["after"], name)
        if before == after:
            return 2
        payload = json.dumps({"before": before, "after": after, "title": name, "static": True}).encode()
        if len(payload) > MAX_BUNDLE:
            return 1
        remain = memoryview(payload)
        while remain:
            remain = remain[os.write(1, remain):]
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
