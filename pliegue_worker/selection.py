"""Server-issued references and scope checks for declarative visual edits."""
import hashlib
import hmac
import json
import re
from collections import Counter

from pliegue_worker.builder import parse_markup, render_markup
from pliegue_worker.page_extensions import ATTRIBUTES
from pliegue_worker.revisions import Conflict

COMPONENTS = {
    "a": "Enlace", "nav": "Navegación", "aside": "Barra lateral",
    "article": "Tarjeta / Artículo", "section": "Sección", "div": "Contenedor",
    "header": "Encabezado", "footer": "Pie", "button": "Botón", "input": "Campo",
    "select": "Selector", "textarea": "Área de texto", "form": "Formulario",
    "table": "Tabla", "tr": "Fila", "td": "Celda", "th": "Encabezado de tabla",
    "img": "Imagen / Icono", "orvia-chart": "Gráfica", "dialog": "Diálogo",
    "details": "Panel desplegable", "p": "Párrafo",
    **{f"h{i}": "Título" if i == 1 else "Subtítulo" for i in range(1, 7)},
}
FEATURE_TAGS = {
    "table", "thead", "tbody", "tfoot", "tr", "th", "td", "form", "input",
    "select", "option", "textarea", "button", "a", "dialog", "details", "summary",
    "orvia-chart", "img", "progress", "meter",
}
PRESERVED_TAGS = FEATURE_TAGS | {"h1", "h2", "h3", "h4", "h5", "h6", "p", "section", "article", "nav", "aside"}
LABEL_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "button", "legend", "summary"}
BINDINGS = {
    "id", "name", "type", "required", "disabled", "multiple", "min", "max", "step",
    "hidden", "open", "checked", "selected", "value",
    "minlength", "maxlength", "data-filter", "data-group", "data-value", "data-tabs",
    "data-tab", "data-panel", "data-open", "data-close", "href", "for", "interactive", *ATTRIBUTES,
}
CHART_PARTS = {"title": "Título de gráfica", "legend": "Leyenda de gráfica", "controls": "Control de gráfica"}
CHART_PROPERTIES = {"title": {"title"}, "legend": {"group", "interactive"}, "controls": {"group", "interactive"}}
LOCAL_ID = re.compile(r"pliegue-visual-[0-9a-f]{12}")
REFERENCE = re.compile(r"[0-9a-f]{32}\.[0-9a-f]{64}")


def page_index(page, tree):
    config = json.loads(tree[page["file"]][0])
    root = parse_markup(config["html"])
    records, keys = {}, {}

    def visit(parent, location=(), hierarchy=(), anchor=()):
        occurrences = Counter()
        for index, node in enumerate(parent):
            path = location + (index,)
            occurrences[node.tag] += 1
            structural = anchor + (f"{node.tag}[{occurrences[node.tag]}]",)
            if node.get("id"):
                structural = (f"id:{node.get('id')}",)
            if node.tag == "orvia-chart" and node.get("key"):
                structural = (f"chart-key:{node.get('key')}",)
            key = hashlib.sha256(json.dumps([page["file"], structural]).encode()).hexdigest()[:32]
            descriptor = {
                "id": key, "type": COMPONENTS.get(node.tag, node.tag),
                "tag": node.tag, "location": list(path), "parents": list(hierarchy),
                "file": page["file"], "route": page["route"], "page": page["title"],
                "style": {name: node.get(name) for name in ("id", "class", "style", "role")
                          if node.get(name) and len(node.get(name)) <= 500},
            }
            if node.tag == "orvia-chart":
                descriptor["chart"] = {name: node.get(name) for name in
                                       ("key", "title", "kind", "dataset", "x", "y", "group", "color", "interactive")}
                descriptor["sources"] = ["pliegue_worker/builder.py", "pliegue_worker/PAGINAS.txt"]
            elif node.tag == "table":
                caption = node.find("caption")
                if caption is not None:
                    descriptor["label"] = " ".join("".join(caption.itertext()).split())[:80]
                descriptor["sources"] = ["pliegue_worker/PAGINAS.txt", "pliegue_worker/page_extensions.py"]
            records[key] = descriptor
            keys[path] = key
            if node.tag == "orvia-chart":
                for part, label in CHART_PARTS.items():
                    part_key = chart_part_id(key, part)
                    records[part_key] = {**descriptor, "id": part_key, "type": label,
                                         "part": part, "parents": list(hierarchy) + [key]}
            visit(node, path, hierarchy + (key,), structural)

    visit(root)
    for key, kind in (("page", "Página / Contenedor principal"), ("sidebar", "Enlace de la barra lateral")):
        identifier = hashlib.sha256(f"{page['file']}:{key}".encode()).hexdigest()[:32]
        records[identifier] = {
            "id": identifier, "type": kind, "tag": key, "location": [],
            "parents": [], "file": page["file"], "route": page["route"], "page": page["title"],
        }
        if key == "page":
            keys[()] = identifier
    for record in records.values():
        if record["location"]:
            record["parents"].insert(0, keys[()])
    return config, records, keys


def chart_part_id(key, part):
    return hashlib.sha256(f"{key}:{part}".encode()).hexdigest()[:32]


def reference(secret, owner, revision, slug, key):
    message = json.dumps([owner, revision, slug, key], sort_keys=True).encode()
    return key + "." + hmac.digest(secret, message, "sha256").hex()


def decorate(page, tree, secret, owner, revision, slug):
    config, records, keys = page_index(page, tree)
    if len(records) > 1000 or len(json.dumps(records)) > 800_000:
        return {**page, "selection_reason": "La página supera el límite de elementos identificables. Divide el documento y vuelve a seleccionar."}
    content, _ = render_markup(config["html"], config["datasets"], [],
                               identify=lambda node, location: keys[location],
                               chart_parts=lambda location: {
                                   part: f' data-pliegue-element="{chart_part_id(keys[location], part)}"'
                                   for part in CHART_PARTS
                               })

    def display_labels(root, location=()):
        for index, node in enumerate(root):
            path = location + (index,)
            key = keys[path]
            label = node.get("aria-label") or node.get("id")
            if node.tag == "orvia-chart":
                label = node.get("title")
                records[chart_part_id(key, "title")]["label"] = label[:80]
            elif node.tag in LABEL_TAGS:
                label = " ".join("".join(node.itertext()).split()) or label
            elif node.tag == "article" and not node.get("aria-label"):
                heading = next((child for child in node if child.tag in LABEL_TAGS | {"small", "figcaption"}), None)
                if heading is not None:
                    label = " ".join("".join(heading.itertext()).split())
            if label:
                records[key]["label"] = label[:80]
            display_labels(node, path)

    display_labels(parse_markup(config["html"]))
    for record in records.values():
        if record["tag"] == "sidebar":
            record["label"] = page["sidebar"]
    return {
        **page,
        "markup": f'<style>{config["css"]}</style><main data-pliegue-element="{keys[()]}">{content}</main>',
        "selection": {
            "slug": slug, "revision": revision,
            "elements": {key: {**record, "ref": reference(secret, owner, revision, slug, key)}
                         for key, record in records.items()},
        },
    }


def resolve(payload, page, tree, secret, owner, revision):
    if not isinstance(payload, dict) or set(payload) != {"slug", "revision", "refs"}:
        raise Conflict("Selecciona un elemento válido.")
    if json.dumps(payload["revision"], sort_keys=True) != json.dumps(revision, sort_keys=True):
        raise Conflict("La revisión cambió. Vuelve a abrir la página y selecciona el elemento.")
    refs = payload["refs"]
    if not isinstance(refs, list) or not 1 <= len(refs) <= 8 or any(
        not isinstance(ref, str) or not REFERENCE.fullmatch(ref) for ref in refs
    ) or len(set(refs)) != len(refs):
        raise Conflict("Selecciona de uno a ocho elementos válidos.")
    _, records, _ = page_index(page, tree)
    targets = []
    for ref in refs:
        key = ref.split(".")[0]
        if key not in records or not hmac.compare_digest(ref, reference(secret, owner, revision, payload["slug"], key)):
            raise Conflict("No se pudo verificar el origen. Vuelve a seleccionar el elemento.")
        targets.append(records[key])
    return targets


def structure(node, ignore_attributes=()):
    return node.tag, sorted((key, value) for key, value in node.attrib.items()
                            if key not in ignore_attributes), node.text or "", [
        (structure(child, ignore_attributes), child.tail or "") for child in node
    ]


def mask(node, paths, current=()):
    if current in paths:
        return
    for index, child in enumerate(node):
        path = current + (index,)
        if path in paths:
            tail = child.tail
            child.clear()
            child.tag = "pliegue-selection"
            child.tail = tail
        else:
            mask(child, paths, path)


def capabilities(root, added_ids=(), enhanced_tables=()):
    return Counter((node.tag, tuple(sorted((key, value) for key, value in node.attrib.items()
                                          if key in BINDINGS and not (key == "id" and value in added_ids)
                                          and not (key == "data-interactive-table" and node in enhanced_tables))))
                   for node in root.iter()
                   if node.tag in PRESERVED_TAGS or any(key in BINDINGS for key in node.attrib))


def at_location(root, location):
    for index in location:
        root = root[index]
    return root


def check_selected_tables(original, updated, locations):
    error = "La tabla debe conservar registros, estructura y relaciones. Autoriza el cambio funcional para modificarlos."
    enhanced = set()

    def visit(node, location):
        if node.tag == "table" and any(location[:len(target)] == target
                                       or target[:len(location)] == location for target in locations):
            try:
                candidate = at_location(updated, location)
            except IndexError as exc:
                raise Conflict(error) from exc
            presentation = {"style", "class", "data-interactive-table"}
            if structure(node, presentation) != structure(candidate, presentation):
                raise Conflict(error)
            if "data-interactive-table" not in node.attrib and "data-interactive-table" in candidate.attrib:
                enhanced.add(candidate)
        for index, child in enumerate(node):
            visit(child, location + (index,))

    visit(original, ())
    return enhanced


def check_local_styles(old, new, targets, original, updated):
    # Appended selectors can match only a verified selected node.
    if old == new:
        return
    if not isinstance(new, str) or not new.startswith(old):
        raise Conflict("Conserva el CSS compartido en una edición de elementos.")
    prefixes = "|".join(target["id"][:12] for target in targets)
    frames = re.compile(
        r"\s*@keyframes\s+pliegue-(?:" + prefixes + r")-[a-z0-9-]{1,40}\s*"
        r"\{(?:\s*(?:from|to|[0-9.]+%)\s*\{[^{}]*\})+\s*\}"
    )
    allowed_ids = set()
    for target in targets:
        if not target["location"] or "part" in target:
            continue
        try:
            previous = at_location(original, target["location"]).get("id")
            current = at_location(updated, target["location"]).get("id")
        except IndexError:
            continue
        local_id = "pliegue-visual-" + target["id"][:12]
        if current and (current == previous or (not previous and current == local_id)):
            if re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_-]{0,79}", current):
                allowed_ids.add(current)
    rules = re.compile(r"#([a-zA-Z_][a-zA-Z0-9_-]*)(?::(?:hover|focus-visible))?\s*\{[^{}]*\}")
    remaining = new[len(old):].strip()
    while remaining:
        match = frames.match(remaining)
        if not match:
            match = rules.match(remaining)
            if not match or match[1] not in allowed_ids:
                raise Conflict("Agrega solo reglas con el ID exacto del elemento seleccionado o keyframes con su prefijo.")
        remaining = remaining[match.end():].strip()


def check_scope(before, after, targets, allow_behavior=False):
    path = targets[0]["file"]
    if path not in after or any(before.get(name) != after.get(name)
                                for name in before.keys() | after.keys() if name != path):
        raise Conflict("La edición visual solo puede cambiar el documento seleccionado.")
    old, new = (json.loads(tree[path][0]) for tree in (before, after))
    tags = {target["tag"] for target in targets}
    locations = {tuple(target["location"]) for target in targets if target["location"]}
    allowed = ({"sidebar", "icon"} if "sidebar" in tags else set())
    if locations or "page" in tags:
        allowed.add("html")
    if "page" in tags:
        allowed.update(("title", "css"))
    elif locations:
        allowed.add("css")
    if any(old[key] != new.get(key) for key in old.keys() - allowed):
        raise Conflict("El borrador cambió metadatos, CSS compartido o datos fuera de la selección.")
    original, updated = (parse_markup(config["html"]) for config in (old, new))
    enhanced_tables = set()
    if locations and "page" not in tags:
        check_local_styles(old["css"], new.get("css"), targets, original, updated)
        if not allow_behavior:
            enhanced_tables = check_selected_tables(original, updated, locations)
    for location in locations:
        selection = [target for target in targets if tuple(target["location"]) == location]
        if "page" in tags or any("part" not in target for target in selection) or any(
            location[:len(ancestor)] == ancestor and ancestor != location for ancestor in locations
        ):
            continue
        old_node, new_node = original, updated
        try:
            for index in location:
                old_node, new_node = old_node[index], new_node[index]
        except IndexError as exc:
            raise Conflict("La gráfica seleccionada desapareció.") from exc
        properties = set().union(*(CHART_PROPERTIES[target["part"]] for target in selection))
        if (old_node.tag != new_node.tag or any(old_node.get(name) != new_node.get(name)
                for name in (old_node.attrib.keys() | new_node.attrib.keys()) - properties)):
            raise Conflict("Los cambios exceden la parte seleccionada de la gráfica. Selecciona la gráfica completa.")
    original_ids = {node.get("id") for node in original.iter()}
    added_ids = {node.get("id") for node in updated.iter()
                 if node.get("id") and LOCAL_ID.fullmatch(node.get("id")) and node.get("id") not in original_ids}
    removed = capabilities(original) - capabilities(updated, added_ids, enhanced_tables)
    if removed and not allow_behavior:
        affected = ", ".join(sorted({tag for tag, _ in removed}))
        raise Conflict(f"Cambios de comportamiento o eliminaciones detectados ({affected}). "
                       "Conserva estos componentes o autoriza expresamente el cambio funcional al enviar.")
    if "page" not in tags:
        for location in locations:
            if any(location[:len(ancestor)] == ancestor and ancestor != location for ancestor in locations):
                continue
            node = updated
            try:
                for index in location:
                    node = node[index]
            except IndexError as exc:
                raise Conflict("El elemento seleccionado desapareció; modifica su contenedor para eliminarlo.") from exc
        mask(original, locations)
        mask(updated, locations)
        if structure(original) != structure(updated):
            raise Conflict("Se detectaron cambios fuera de los elementos seleccionados.")
