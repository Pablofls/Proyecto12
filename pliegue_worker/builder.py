"""Validated page documents for the private Pliegue laboratory."""
import base64
import html
import json
import math
import re
from pathlib import Path
from xml.etree import ElementTree

from pliegue_worker.page_extensions import ATTRIBUTES, validate_attribute

PREFIX = "apps/web/app/pliegue_pages/"
PAGE = re.compile(re.escape(PREFIX) + r"([a-z][a-z0-9-]{0,39})\.json")
ICONS = {"chart": "▥", "form": "▤", "page": "◇", "grid": "▦"}
TAGS = frozenset("""
a nav article aside section header footer div span p h1 h2 h3 h4 h5 h6 small strong em
b i mark output code pre blockquote time figure figcaption ul ol li dl dt dd table
caption thead tbody tfoot tr th td details summary dialog progress meter hr br img
form fieldset legend label input select option textarea button
""".split())
VOID = {"img", "hr", "br", "input"}
ATTRS = frozenset("""
class id role title hidden tabindex aria-label aria-labelledby aria-describedby aria-live
open required disabled checked selected multiple placeholder min max step minlength maxlength
name value rows cols colspan rowspan scope for alt width height data-filter data-group
data-value data-tabs data-tab data-panel data-open data-close
""".split())
INPUT_TYPES = {"text", "email", "number", "date", "checkbox", "radio", "range", "tel"}
CHARTS = {"bars", "bars-3d", "lines", "pie", "area", "scatter"}
ASSETS = {"orvia": Path(__file__).with_name("orvia-mark.svg")}
ABSENT = "<main><p>Esta página no existe en esta versión.</p></main>"


class GeneratedScript(ValueError):
    """A page can be shown without its prohibited executable markup."""


def escape(value):
    return html.escape(str(value), quote=True)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Clave duplicada: {key}.")
        result[key] = value
    return result


def css_text(source):
    if not isinstance(source, str) or len(source) > 16000:
        raise ValueError("CSS de página inválido o demasiado largo.")
    flat = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    if re.search(r"[<\\\x00]|\b(?:url|image-set|image|src)\s*\(|@(?!media\b|keyframes\b|supports\b)", flat, re.I) or "<" in source:
        raise ValueError("El CSS contiene marcado, escapes o carga de recursos no compatible.")
    return source


def chart(node, datasets, summary, marker="", parts=None):
    parts = parts or {}
    required = {"dataset", "kind", "x", "y", "title", "color"}
    attrs = node.attrib
    if not required <= attrs.keys() or attrs.keys() - required - {"group", "interactive", "key"}:
        raise ValueError("La gráfica requiere dataset, kind, x, y, title y color. group, interactive y key son opcionales.")
    if attrs.get("interactive", "false") not in {"true", "false"}:
        raise ValueError("interactive debe ser true o false.")
    interactive = attrs.get("interactive") == "true"
    dataset = attrs["dataset"]
    kind, x, y = (attrs[key] for key in ("kind", "x", "y"))
    group = attrs.get("group")
    color = attrs["color"]
    if kind not in CHARTS or not re.fullmatch(
        r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})|[a-zA-Z]{1,24}|(?:rgba?|hsla?)\([+\- .0-9,%/]+\)", color
    ):
        raise ValueError("Tipo de gráfica o color inválido. Usa HEX, nombre, RGB o HSL.")
    if dataset not in datasets:
        raise ValueError(f"Dataset ficticio inexistente: {dataset}.")
    rows = datasets[dataset]
    for key in (x, y, group):
        if key is not None and any(key not in row for row in rows):
            raise ValueError(f"Variable inexistente en {dataset}: {key}.")
    values = [row[y] for row in rows]
    if any(type(v) not in (int, float) or abs(v) > 1e12 for v in values):
        raise ValueError(f"La variable {y} debe contener números finitos de magnitud admisible.")
    if kind == "scatter" and any(type(row[x]) not in (int, float) or abs(row[x]) > 1e12 for row in rows):
        raise ValueError(f"La variable {x} debe ser numérica para dispersión.")
    if kind == "pie" and (any(v < 0 for v in values) or not sum(values)):
        raise ValueError(f"La gráfica de pastel requiere valores positivos en {y}.")
    summary.append({"title": attrs["title"], "color": color, "type": kind, "x": x, "y": y, "group": group, "dataset": dataset, "interactive": interactive})
    groups = {}
    for row in rows:
        groups.setdefault(str(row[group]) if group else "", []).append(row)
    filter_name = f"_orvia-chart-{len(summary)}" if group and interactive else ""
    y_range = (min(0, min(values)), max(0, max(values)))
    x_range = (min(row[x] for row in rows), max(row[x] for row in rows)) if kind == "scatter" else None
    body = "".join(plot(series, kind, x, y, color, label, filter_name, interactive, x_range, y_range, parts.get("legend", ""))
                   for label, series in groups.items())
    if filter_name:
        options = "".join(f'<option value="{escape(label)}">{escape(label)}</option>' for label in groups)
        body = (f'<label>{escape(group)} <select data-filter="{filter_name}"{parts.get("controls", "")}>'
                f'<option value="">Todos</option>{options}</select></label>{body}')
    title, title_marker = escape(attrs["title"]), parts.get("title", "")
    depth_note = " · Profundidad geométrica" if kind == "bars-3d" else ""
    return (f'<figure class="orvia-chart"{marker}><figcaption{title_marker}><strong>{title}</strong>'
            f'<small>Datos ficticios · X: {escape(x)} · Y: {escape(y)}{depth_note}</small></figcaption>{body}</figure>')


def projected_column(center, value_y, zero_y, step, tooltip):
    """Project three visible faces of a cuboid; depth is purely geometric."""
    left, right = center - step * .28, center + step * .28
    top, bottom = sorted((value_y, zero_y))
    depth = min(10, step * .23)

    def face(name, vertices, opacity="1"):
        points = " ".join(f"{x + z * .8:.3f},{y - z * .6:.3f}" for x, y, z in vertices)
        return f'<polygon data-face="{name}" points="{points}" fill-opacity="{opacity}"/>'

    if top == bottom:
        return f'<path d="M{left:.3f} {top:.3f} H{right:.3f}" stroke="currentColor"/>'
    return (f'<g data-geometry="cuboid"><title>{escape(tooltip)}</title>'
            + face("front", [(left, top, 0), (right, top, 0), (right, bottom, 0), (left, bottom, 0)])
            + face("side", [(right, top, 0), (right, top, depth), (right, bottom, depth), (right, bottom, 0)], ".57")
            + face("top", [(left, top, 0), (left, top, depth), (right, top, depth), (right, top, 0)], ".77")
            + '</g>')


def plot(rows, kind, x, y, color, label, filter_name, interactive, x_range, y_range, legend_marker=""):
    values = [row[y] for row in rows]
    lower, upper = y_range

    def y_at(value):
        return 124 - 106 * (value - lower) / (upper - lower or 1)

    step = 264 / len(rows)
    x_positions = [36 + step * (i + .5) for i in range(len(rows))]
    if x_range:
        low, high = x_range
        x_positions = [36 + 264 * (row[x] - low) / (high - low) if high != low else 168 for row in rows]
    coords = [(px, y_at(value)) for px, value in zip(x_positions, values)]
    points = " ".join(f"{px:.3f},{py:.3f}" for px, py in coords)
    baseline = y_at(0)
    shapes = []
    if kind == "bars":
        shapes = [f'<rect x="{px-step*.3:.3f}" y="{min(py, baseline):.3f}" width="{step*.6:.3f}" height="{abs(py-baseline):.3f}" rx="2"/>'
                  for px, py in coords]
    elif kind == "bars-3d":
        shapes = [projected_column(px, py, baseline, step, f"{row[x]}: {row[y]}")
                  for (px, py), row in zip(coords, rows, strict=True)]
    elif kind in {"lines", "area"}:
        if kind == "area":
            shapes.append(f'<polygon points="{coords[0][0]},{baseline} {points} {coords[-1][0]},{baseline}" fill-opacity=".25"/>')
        shapes.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.5"/>')
    if kind in {"scatter", "lines", "area"}:
        shapes.extend(f'<circle cx="{px:.3f}" cy="{py:.3f}" r="3.5"/>' for px, py in coords)
    if kind == "pie":
        total = sum(values)
        if total:
            offset = 0
            for i, value in enumerate(values):
                fraction = value / total * 100
                shapes.append(f'<circle cx="160" cy="72" r="44" pathLength="100" fill="none" stroke="{color}" '
                              f'stroke-width="34" opacity="{max(.25, 1-i*.1)}" stroke-dasharray="{fraction:.6f} 100" '
                              f'stroke-dashoffset="{-offset:.6f}" transform="rotate(-90 160 72)"/>')
                offset += fraction
    legend = "".join(f'<li>{escape(row[x])}: {escape(row[y])}</li>' for row in rows)
    points_labels = "".join(
        f'<text x="{px:.3f}" y="141" text-anchor="middle">{escape(str(row[x])[:16])}</text>'
        for (px, _), row in zip(coords, rows)
    ) if kind != "pie" and len(rows) <= 8 else ""
    ticks = "".join(f'<text x="32" y="{y_at(value) + 3:.3f}" text-anchor="end">{value:.3g}</text>'
                    for value in sorted({lower, 0, upper}))
    axis = (f'<path d="M36 10 V124 H304 M36 {baseline:.3f} H304" fill="none" stroke="currentColor" opacity=".45"/>'
            f'<g fill="currentColor" font-size="8">{ticks}{points_labels}</g>') if kind != "pie" else ""
    filters = f' data-group="{filter_name}" data-value="{escape(label)}"' if filter_name else ""
    legend = (f'<details{legend_marker}><summary>Valores de la gráfica</summary><ul>{legend}</ul></details>'
              if interactive else f'<ul{legend_marker} aria-label="Valores de la gráfica">{legend}</ul>')
    return (f'<div class="orvia-plot"{filters}><strong>{escape(label)}</strong><svg viewBox="0 0 320 145" '
            f'aria-hidden="true" fill="{color}">{axis}{"".join(shapes)}</svg>'
            f'{legend}</div>')


def parse_markup(source):
    if not isinstance(source, str) or len(source) > 28000:
        raise ValueError("El HTML de página supera el límite o no es texto.")
    if "<!" in source or "<?" in source:
        raise ValueError("El fragmento HTML no admite declaraciones ni directivas XML.")
    try:
        return ElementTree.fromstring(f"<fragment>{source}</fragment>")
    except ElementTree.ParseError as exc:
        raise ValueError(f"HTML mal formado. Cierra las etiquetas y escapa &: {exc}.") from exc


def render_markup(source, datasets, charts, *, static_fallback=False, identify=None, chart_parts=None):
    root = parse_markup(source)
    for parent in root.iter():
        previous = None
        for child in list(parent):
            if child.tag.lower() != "script":
                previous = child
                continue
            if not static_fallback:
                raise GeneratedScript("Etiqueta no compatible: script. JavaScript generado está bloqueado.")
            if previous is None:
                parent.text = (parent.text or "") + (child.tail or "")
            else:
                previous.tail = (previous.tail or "") + (child.tail or "")
            parent.remove(child)
        for key in list(parent.attrib):
            if key.lower().startswith("on"):
                if not static_fallback:
                    raise GeneratedScript(f"Atributo no compatible: {key}. JavaScript generado está bloqueado.")
                del parent.attrib[key]
    features = set()
    ids = set()
    chart_keys = set()
    for node in root.iter():
        if node.tag == "form" and not any(
            child.tag == "button" and child.get("type") == "submit" for child in node.iter()
        ):
            raise ValueError("Cada formulario de demostración requiere un botón de envío.")
        if node.tag == "select" and "data-filter" in node.attrib and not any(
            child.get("data-group") == node.get("data-filter") and "data-value" in child.attrib
            for child in root.iter()
        ):
            raise ValueError(f"El filtro {node.get('data-filter')} no tiene elementos asociados.")
        if node.tag == "button" and "data-open" in node.attrib and not any(
            child.tag == "dialog" and child.get("id") == node.get("data-open") for child in root.iter()
        ):
            raise ValueError(f"Modal inexistente: {node.get('data-open')}.")
        if "data-tabs" in node.attrib:
            buttons = {child.get("data-tab") for child in node.iter("button")
                       if "data-tab" in child.attrib and child.get("type") == "button"}
            panels = {child.get("data-panel") for child in node.iter() if "data-panel" in child.attrib}
            if not buttons or buttons != panels:
                raise ValueError("Cada pestaña requiere un botón y un panel con la misma clave.")

    def render(node, depth, location):
        marker = f' data-pliegue-element="{identify(node, location)}"' if identify else ""
        tag = node.tag
        if depth > 30:
            raise ValueError("El HTML contiene demasiados niveles anidados.")
        if tag == "orvia-chart":
            key = node.get("key")
            if key is not None:
                if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", key) or key in chart_keys:
                    raise ValueError("Clave de gráfica inválida o duplicada.")
                chart_keys.add(key)
            if len(node) or node.text:
                raise ValueError("orvia-chart no admite contenido interno.")
            return chart(node, datasets, charts, marker, chart_parts(location) if chart_parts else None)
        if tag not in TAGS:
            raise ValueError(f"Etiqueta no compatible: {tag}. JavaScript generado está bloqueado.")
        if tag in {"details", "form", "dialog"}:
            features.add(tag)
        result = [marker]
        for key, value in node.attrib.items():
            if key == "style":
                css_text(value)
            elif key == "id":
                if value in ids:
                    raise ValueError(f"ID duplicado: {value}.")
                ids.add(value)
            elif key == "type" and (tag == "input" and value in INPUT_TYPES or tag == "button" and value in {"button", "submit", "reset"}):
                pass
            elif key == "href" and tag == "a" and re.fullmatch(r"#[a-zA-Z][a-zA-Z0-9_-]{0,79}", value):
                pass
            elif key == "asset" and tag == "img" and value in ASSETS:
                data = base64.b64encode(ASSETS[value].read_bytes()).decode("ascii")
                result.append(f' src="data:image/svg+xml;base64,{data}"')
                continue
            elif key in ATTRIBUTES:
                features.add(validate_attribute(node, key, value))
            elif key not in ATTRS:
                raise ValueError(f"Atributo no compatible en {tag}: {key}.")
            if key in {"data-filter", "data-group"} and value.startswith("_orvia-chart-"):
                raise ValueError("Los identificadores _orvia-chart- están reservados.")
            if key in {"data-filter", "data-tab"}:
                features.add(key)
            result.append(f' {key}="{escape(value)}"')
        if tag == "img" and ("asset" not in node.attrib or "alt" not in node.attrib):
            raise ValueError("Usa un asset local autorizado y un atributo alt en cada imagen.")
        if tag in VOID:
            if len(node) or node.text:
                raise ValueError(f"{tag} no admite contenido.")
            return f'<{tag}{"".join(result)}>'
        content = escape(node.text or "") + "".join(render(child, depth + 1, location + (index,)) + escape(child.tail or "") for index, child in enumerate(node))
        if tag == "form":
            content = '<p><small>Formulario de demostración. El envío se valida localmente.</small></p>' + content + '<p data-form-result="" role="status"></p>'
        return f'<{tag}{"".join(result)}>{content}</{tag}>'

    markup = escape(root.text or "") + "".join(render(node, 1, (index,)) + escape(node.tail or "") for index, node in enumerate(root))
    return markup, sorted(features)


def documents(tree, *, static_fallback=False):
    pages = {}
    labels = {"laboratorio", "ejemplo de dashboard"}
    for path, (data, executable) in sorted(tree.items()):
        if not path.startswith(PREFIX):
            continue
        match = PAGE.fullmatch(path)
        try:
            if not match or executable or len(data) > 40000:
                raise ValueError("Nombre, tamaño o permisos de archivo de página no admitidos.")
            slug = match[1]
            config = json.loads(data.decode("utf-8"), object_pairs_hook=unique_object,
                                parse_constant=lambda value: None)
            if not isinstance(config, dict) or set(config) != {"title", "sidebar", "icon", "html", "css", "datasets"}:
                raise ValueError("La página debe declarar title, sidebar, icon, html, css y datasets.")
            title, label, icon = (config[key] for key in ("title", "sidebar", "icon"))
            if any(not isinstance(v, str) or not v.strip() or len(v) > 80 for v in (title, label)):
                raise ValueError("El título y el nombre del sidebar deben tener entre 1 y 80 caracteres.")
            normalized = " ".join(label.casefold().split())
            if normalized in labels:
                raise ValueError(f"Nombre de sidebar duplicado: {label}.")
            labels.add(normalized)
            if not isinstance(icon, str) or icon not in ICONS:
                raise ValueError("Icono no autorizado. Usa chart, form, page o grid.")
            datasets = config["datasets"]
            if not isinstance(datasets, dict) or len(datasets) > 10:
                raise ValueError("Formato de datasets ficticios inválido.")
            for rows in datasets.values():
                if not isinstance(rows, list) or not 1 <= len(rows) <= 32 or any(
                    not isinstance(row, dict) or len(row) > 16 or any(
                        type(v) not in (str, int, float) or isinstance(v, float) and not math.isfinite(v)
                        for v in row.values()
                    ) for row in rows
                ):
                    raise ValueError("Cada dataset ficticio debe contener de 1 a 32 filas de valores simples.")
            charts = []
            content, features = render_markup(config["html"], datasets, charts, static_fallback=static_fallback)
            style = css_text(config["css"])
            pages[slug] = {
                "title": title, "sidebar": label, "icon": ICONS[icon], "charts": charts, "features": sorted(set(features) | ({"gráficas interactivas"} if any(c["interactive"] for c in charts) else set())),
                "route": "/laboratorio/paginas/" + slug, "file": path,
                "markup": f'<style>{style}</style><main>{content}</main>',
            }
        except GeneratedScript as exc:
            raise GeneratedScript(f"{path}: {exc}") from exc
        except (OSError, ValueError, RecursionError) as exc:
            raise ValueError(f"{path}: {exc}") from exc
    if len(pages) > 24 or len(json.dumps(pages)) > 600_000:
        raise ValueError("El conjunto de páginas supera el límite del laboratorio.")
    return pages


def page_changes(before, after, *, static_fallback=False):
    old = documents(before)
    new = documents(after, static_fallback=static_fallback)
    return {
        slug: {"before": old.get(slug, {}).get("markup", ABSENT),
               "after": new.get(slug, {}).get("markup", ABSENT),
               "page": {k: v for k, v in (new.get(slug) or old[slug]).items() if k != "markup"},
               "sidebar_before": old.get(slug, {}).get("sidebar"), "sidebar_after": new.get(slug, {}).get("sidebar"),
               "icon_before": old.get(slug, {}).get("icon"), "icon_after": new.get(slug, {}).get("icon")}
        for slug in sorted(old.keys() | new.keys())
        if before.get((new.get(slug) or old[slug])["file"]) != after.get((new.get(slug) or old[slug])["file"])
    }
