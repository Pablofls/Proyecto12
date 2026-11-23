"""Extrae muestras CSS limitadas del formato de diferencias del worker."""
import json
import re
from pathlib import PurePosixPath

_COLOR = r"(?:#[0-9a-fA-F]{3,8}|[a-zA-Z]{1,24})"
_LENGTH = r"(?:0|[0-9]{1,3}(?:\.[0-9]{1,2})?(?:px|rem|em|%))"
_VALUES = {
    "color": _COLOR,
    "background-color": _COLOR,
    "border-color": _COLOR,
    "border-radius": _LENGTH,
    "font-size": _LENGTH,
    "font-weight": r"(?:[1-9]00|normal|bold)",
    "padding": rf"{_LENGTH}(?: +{_LENGTH}){{0,3}}",
}
_DECLARATION = re.compile(r"\s*([a-z-]+)\s*:\s*([^;{}]+)")
_INLINE_RULE = re.compile(r"\s*[.#a-zA-Z][\w .#,:>+-]*\{([^{}]+)\}\s*")


def _added_declarations(line):
    inline = _INLINE_RULE.fullmatch(line)
    if inline:
        return inline[1].split(";")
    if line.rstrip().endswith(";"):
        return [line.rstrip()[:-1]]
    return []


def css_samples(job):
    """Muestra declaraciones añadidas, cada una aplicada a una muestra fija."""
    if (job.get("state") not in {"ready", "tests_failed"}
            or job.get("diff_truncated") is not False
            or not job.get("changed")
            or not isinstance(job.get("diff"), str)):
        return []

    files = set()
    samples = []
    current = None
    in_hunk = False
    for line in job["diff"].split("\n"):
        if line.startswith("Archivo "):
            label = line.removeprefix("Archivo ")
            if label in {"nuevo", "eliminado"}:
                continue
            try:
                current = json.loads(label)
            except ValueError:
                return []
            if not isinstance(current, str) or PurePosixPath(current).suffix != ".css" or current in files:
                return []
            files.add(current)
            in_hunk = False
        elif line.startswith("Permiso de ejecución:") or line == "Contenido binario modificado":
            return []
        elif line.startswith("@@ "):
            in_hunk = True
        elif current and in_hunk and line.startswith("+"):
            for declaration in _added_declarations(line[1:]):
                match = _DECLARATION.fullmatch(declaration)
                if match:
                    prop, value = match.groups()
                    value = value.strip()
                    if prop in _VALUES and re.fullmatch(_VALUES[prop], value) and len(samples) < 24:
                        samples.append({"file": current, "property": prop, "value": value})
    return samples if len(files) == job["changed"] else []
