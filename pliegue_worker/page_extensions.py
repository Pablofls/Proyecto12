"""Trusted declarative extensions shared by rendering and selection checks."""


def form_message(node, value):
    return bool(value.strip()) and len(value) <= 160 and value.isprintable()


def interactive_table(node, value):
    heads, bodies = node.findall("thead"), node.findall("tbody")
    if not value.strip() or len(value) > 80 or not value.isprintable():
        return False
    if len(heads) != 1 or len(bodies) != 1 or len(heads[0]) != 1:
        return False
    head = heads[0][0]
    rows = list(bodies[0])
    return (
        head.tag == "tr" and 1 <= len(head) <= 12 and 1 <= len(rows) <= 100
        and all(child.tag in {"caption", "thead", "tbody", "tfoot"} for child in node)
        and sum(1 for _ in node.iter("table")) == 1
        and all(cell.tag == "th" and len(cell) == 0 and (cell.text or "").strip()
                and not {"colspan", "rowspan"} & cell.attrib.keys() for cell in head)
        and all(row.tag == "tr" and len(row) == len(head)
                and all(cell.tag == "td" and not {"colspan", "rowspan"} & cell.attrib.keys() for cell in row)
                for row in rows)
    )


# Registration belongs to the worker deployment. Drafts supply only values.
ATTRIBUTES = {
    "data-success-message": ("form", "confirmación de formulario", form_message),
    "data-interactive-table": ("table", "tabla interactiva", interactive_table),
}


def validate_attribute(node, key, value):
    tag, feature, validate = ATTRIBUTES[key]
    if node.tag != tag or not validate(node, value):
        raise ValueError(f"Valor o estructura inválida para {key} en {node.tag}.")
    return feature
