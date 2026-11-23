"""Extract bounded text references from untrusted attachments."""
import base64
import binascii
import io
import re
import stat
import subprocess
import sys
import sysconfig
import tempfile
import xml.etree.ElementTree as ET
import zipfile
import zlib
from pathlib import Path, PurePath

from pliegue_worker.media_decode import IMAGE_FORMATS
from pliegue_worker.process_output import run_render

TEXT_TYPES = frozenset(".txt .md .csv .json .xml .py .js .ts .html .css .sql .yaml .yml".split())
MAX_FILES = 4
MAX_BYTES = 3072
MAX_OFFICE_BYTES = 65_536
MAX_IMAGE_BYTES = 196_608
MAX_ATTACHMENT_REQUEST = 393_216
WORD = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
CONTENT_TYPES = "{http://schemas.openxmlformats.org/package/2006/content-types}"
SHEET = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
SLIDES = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
DRAWING = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
RELATIONSHIP = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
PACKAGE_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"
OFFICE_TYPES = {
    ".docx": ("word/document.xml", "wordprocessingml.document"),
    ".xlsx": ("xl/workbook.xml", "spreadsheetml.sheet"),
    ".pptx": ("ppt/presentation.xml", "presentationml.presentation"),
}


def decode_media(raw, extension):
    interpreter = Path(sys.base_prefix) / "bin" / f"python{sys.version_info.major}.{sys.version_info.minor}"
    dependencies = sysconfig.get_path("purelib")
    decoder = Path(__file__).with_name("media_decode.py").resolve()
    command = ["/usr/bin/prlimit", "--cpu=3", "--as=402653184", "--fsize=262144", "--core=0", "--",
               "/usr/bin/bwrap", "--unshare-all", "--die-with-parent", "--cap-drop", "ALL", "--clearenv",
               "--ro-bind", "/usr", "/usr", "--ro-bind", sys.base_prefix, "/python",
               "--ro-bind", dependencies, "/deps", "--ro-bind", str(decoder), "/decoder.py",
               "--dev", "/dev", "--tmpfs", "/tmp", "--chdir", "/tmp"]
    for path in ("/lib", "/lib64"):
        if Path(path).exists():
            command.extend(("--ro-bind", path, path))
    try:
        with tempfile.TemporaryFile() as output:
            code = run_render(command + ["--", f"/python/bin/{interpreter.name}", "-I", "-S", "-B",
                                         "/decoder.py", extension], input=raw, timeout=5, stdout=output,
                              stderr=subprocess.DEVNULL, env={})
            output.seek(0)
            result = output.read(MAX_IMAGE_BYTES + 1)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError("El procesador aislado de adjuntos no está disponible.") from exc
    if code or not result or len(result) > MAX_IMAGE_BYTES:
        raise ValueError("No se pudo validar el medio en el procesador aislado. Comprueba su formato y tamaño.")
    return result


def document_xml(archive, name):
    data = archive.read(name).decode("utf-8")
    if "<!" in data:
        raise ValueError("Declaraciones XML no admitidas en documentos de Office.")
    return ET.fromstring(data)


def relationship_parts(archive, main, kind, pattern):
    folder, leaf = main.split("/")
    root = document_xml(archive, f"{folder}/_rels/{leaf}.rels")
    result = {}
    used_paths = set()
    for relation in root.findall(PACKAGE_REL):
        if relation.get("Type") != f"http://schemas.openxmlformats.org/officeDocument/2006/relationships/{kind}":
            continue
        target = relation.get("Target", "")
        path = target[1:] if target.startswith("/") else f"{folder}/{target}"
        key = relation.get("Id")
        if (relation.get("TargetMode") not in (None, "Internal") or not key
                or key in result or path in used_paths or not re.fullmatch(pattern, path)
                or len(result) >= 128):
            raise ValueError("El archivo de Office contiene una relación de documento no admitida.")
        result[key] = path
        used_paths.add(path)
    return result


def text_parts(node, tag):
    return "".join(part.text or "" for part in node.iter(tag))


def sheet_text(archive, main, workbook):
    if workbook.tag != SHEET + "workbook":
        raise ValueError("El XLSX no contiene un libro válido.")
    parts = relationship_parts(archive, main, "worksheet", r"xl/worksheets/sheet[1-9][0-9]*\.xml")
    shared = []
    if "xl/sharedStrings.xml" in archive.namelist():
        strings = document_xml(archive, "xl/sharedStrings.xml")
        shared = [text_parts(item, SHEET + "t") for item in strings.findall(SHEET + "si")]
    for sheet in workbook.findall(f"{SHEET}sheets/{SHEET}sheet"):
        data = document_xml(archive, parts.pop(sheet.get(RELATIONSHIP)))
        if data.tag != SHEET + "worksheet":
            raise ValueError("El XLSX no contiene una hoja válida.")
        heading = sheet.get("name", "Hoja")
        for cell in data.iter(SHEET + "c"):
            kind = cell.get("t")
            value = cell.findtext(SHEET + "v", "")
            if kind == "inlineStr":
                value = text_parts(cell, SHEET + "t")
            elif kind == "s":
                index = int(value)
                if not 0 <= index < len(shared):
                    raise ValueError("El XLSX contiene una referencia de texto inválida.")
                value = shared[index]
            if value:
                if heading is not None:
                    yield heading
                    heading = None
                yield f'{cell.get("r", "")}: {value}'


def slides_text(archive, main, presentation):
    if presentation.tag != SLIDES + "presentation":
        raise ValueError("El PPTX no contiene una presentación válida.")
    parts = relationship_parts(archive, main, "slide", r"ppt/slides/slide[1-9][0-9]*\.xml")
    for index, slide in enumerate(presentation.findall(f"{SLIDES}sldIdLst/{SLIDES}sldId"), start=1):
        data = document_xml(archive, parts.pop(slide.get(RELATIONSHIP)))
        if data.tag != SLIDES + "sld":
            raise ValueError("El PPTX no contiene una diapositiva válida.")
        heading = f"Diapositiva {index}"
        for paragraph in data.iter(DRAWING + "p"):
            value = text_parts(paragraph, DRAWING + "t")
            if value.strip():
                if heading is not None:
                    yield heading
                    heading = None
                yield value


def word_text(doc):
    body = doc.find(WORD + "body")
    if doc.tag != WORD + "document" or body is None:
        raise ValueError("El DOCX no contiene un cuerpo de texto válido.")
    for paragraph in body.iter(WORD + "p"):
        yield text_parts(paragraph, WORD + "t")


def bounded_text(parts):
    lines = []
    size = 0
    for part in parts:
        if part.strip():
            size += len(part.encode("utf-8")) + bool(lines)
            if size > MAX_BYTES:
                raise ValueError("El texto extraído supera el límite de 3 KiB.")
            lines.append(part)
    return "\n".join(lines).strip()


def extract_office(raw, extension):
    main, category = OFFICE_TYPES[extension]
    if not raw.startswith(b"PK\x03\x04"):
        raise ValueError("El archivo no comienza con un contenedor de Office válido.")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries = archive.infolist()
            names = {entry.filename for entry in entries}
            if (len(entries) > 128 or len(entries) != len(names)
                    or sum(entry.file_size for entry in entries) > 512 * 1024):
                raise ValueError("El documento supera los límites de su contenedor.")
            for entry in entries:
                name = entry.filename
                if (name != entry.orig_filename or name.startswith("/") or "\\" in name or ":" in name
                        or any(part in {"", ".", ".."} for part in name.rstrip("/").split("/"))
                        or stat.S_ISLNK(entry.external_attr >> 16) or entry.flag_bits & 1
                        or entry.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
                        or any(part in name.lower().split("/") for part in ("embeddings", "activex", "vbaproject.bin"))):
                    raise ValueError("El contenedor incluye una entrada no admitida.")
            types = document_xml(archive, "[Content_Types].xml")
            if not any(part.get("PartName") == "/" + main and part.get("ContentType") ==
                       f"application/vnd.openxmlformats-officedocument.{category}.main+xml"
                       for part in types.findall(CONTENT_TYPES + "Override")):
                raise ValueError("El tipo real del documento de Office no coincide con su extensión.")
            document = document_xml(archive, main)
            if extension == ".xlsx":
                return bounded_text(sheet_text(archive, main, document))
            if extension == ".pptx":
                return bounded_text(slides_text(archive, main, document))
            return bounded_text(word_text(document))
    except (KeyError, UnicodeError, ET.ParseError, zipfile.BadZipFile, zlib.error,
            RuntimeError, NotImplementedError, EOFError) as exc:
        raise ValueError("No se pudo leer el contenido del documento de Office.") from exc


def validate_attachments(value):
    if not isinstance(value, list) or len(value) > MAX_FILES:
        raise ValueError("Puedes adjuntar hasta cuatro archivos.")
    size = 0
    result = []
    binary_size = 0
    image_size = 0
    normalized_size = 0
    for file in value:
        if not isinstance(file, dict) or set(file) not in ({"name", "text"}, {"name", "base64"}):
            raise ValueError("Referencia adjunta inválida.")
        name = file["name"]
        if not isinstance(name, str) or not re.fullmatch(r"[\w][\w .()-]{0,99}", name):
            raise ValueError("Nombre o extensión de archivo no admitidos.")
        extension = PurePath(name).suffix.lower()
        if "base64" in file and (extension in OFFICE_TYPES or extension in IMAGE_FORMATS or extension == ".pdf"):
            encoded = file["base64"]
            is_image = extension in IMAGE_FORMATS
            maximum = MAX_IMAGE_BYTES if is_image else MAX_OFFICE_BYTES
            if not isinstance(encoded, str) or len(encoded) > 4 * ((maximum + 2) // 3):
                raise ValueError("El adjunto supera el límite de su formato.")
            try:
                raw = base64.b64decode(encoded, validate=True)
            except (ValueError, binascii.Error) as exc:
                raise ValueError("Codificación de documento inválida.") from exc
            if is_image:
                image_size += len(raw)
                if not raw or image_size > MAX_IMAGE_BYTES:
                    raise ValueError("Las imágenes deben sumar como máximo 192 KiB.")
                clean = decode_media(raw, extension)
                normalized_size += len(clean)
                if normalized_size > MAX_IMAGE_BYTES:
                    raise ValueError("Las imágenes procesadas superan el límite de 192 KiB.")
                result.append({"name": name, "bytes": len(raw), "kind": "image",
                               "image": base64.b64encode(clean).decode("ascii")})
                continue
            binary_size += len(raw)
            if not raw or binary_size > MAX_OFFICE_BYTES:
                raise ValueError("Los documentos deben sumar como máximo 64 KiB.")
            content = decode_media(raw, extension).decode("utf-8") if extension == ".pdf" else extract_office(raw, extension)
        elif extension in TEXT_TYPES and "text" in file:
            content = file["text"]
        else:
            raise ValueError("Nombre o extensión de archivo no admitidos.")
        if not isinstance(content, str) or any(
            not char.isprintable() and char not in "\t\n\r" for char in content
        ):
            raise ValueError("El archivo debe contener texto UTF-8 válido.")
        length = len(content.encode("utf-8"))
        size += length
        if length == 0 or size > MAX_BYTES:
            raise ValueError("Los adjuntos deben contener texto y sumar como máximo 3 KiB.")
        result.append({"name": name, "text": content, "bytes": length})
    return result
