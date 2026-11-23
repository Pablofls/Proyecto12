"""Decode media inside the bounded, offline attachment sandbox."""
import io
import sys
import warnings

IMAGE_FORMATS = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".webp": "WEBP"}


def decode_image(raw, extension):
    from PIL import Image, ImageOps

    expected = IMAGE_FORMATS[extension]
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(raw), formats=[expected]) as source:
            if source.format != expected or source.width * source.height > 4_000_000 or getattr(source, "n_frames", 1) != 1:
                raise ValueError("Dimensiones o formato no admitidos")
            image = ImageOps.exif_transpose(source)
            image.thumbnail((1280, 1280))
            # A fresh image drops EXIF, ICC profiles and other source metadata.
            output = Image.new("RGB", image.size, "white")
            rgba = image.convert("RGBA")
            output.paste(rgba, mask=rgba.getchannel("A"))
            buffer = io.BytesIO()
            output.save(buffer, "JPEG", quality=80)
            return buffer.getvalue()


def decode_pdf(raw):
    from pypdf import PdfReader

    if not raw.startswith(b"%PDF-"):
        raise ValueError("Firma PDF inválida")
    reader = PdfReader(io.BytesIO(raw), strict=True)
    if reader.is_encrypted or not 1 <= len(reader.pages) <= 12:
        raise ValueError("PDF cifrado o con demasiadas páginas")
    fragments = []
    length = 0
    for page in reader.pages:
        text = (page.extract_text() or "").strip()
        length += len(text.encode()) + 1
        if length > 3072:
            raise ValueError("PDF supera el límite de texto")
        fragments.append(text)
    result = "\n".join(fragments).strip().encode()
    if not result:
        raise ValueError("PDF sin texto digital")
    return result


if __name__ == "__main__":
    sys.path.insert(0, "/deps")
    extension = sys.argv[1]
    content = sys.stdin.buffer.read(196_609)
    try:
        result = decode_pdf(content) if extension == ".pdf" else decode_image(content, extension)
    except Exception:
        raise SystemExit(2) from None
    sys.stdout.buffer.write(result)
