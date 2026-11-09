from io import BytesIO
from pathlib import PurePosixPath

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image, ImageOps

WIDTHS = (480, 800, 1200, 1800)
QUALITY = 80


def variant_name(original_name, width):
    stem = PurePosixPath(original_name).with_suffix("")
    return f"cache/{stem}-{width}w.webp"


def build_variant(field_file, width):
    name = variant_name(field_file.name, width)
    if default_storage.exists(name):
        return default_storage.url(name)
    try:
        with default_storage.open(field_file.name, "rb") as source:
            image = Image.open(source)
            image = ImageOps.exif_transpose(image)
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGBA" if image.mode in ("LA", "P") else "RGB")
            if image.width > width:
                height = round(image.height * width / image.width)
                image = image.resize((width, height), Image.Resampling.LANCZOS)
            buffer = BytesIO()
            image.save(buffer, "WEBP", quality=QUALITY, method=6)
    except (OSError, ValueError):
        return None
    saved = default_storage.save(name, ContentFile(buffer.getvalue()))
    return default_storage.url(saved)


def responsive_sources(field_file):
    try:
        original_width = field_file.width
    except (OSError, ValueError):
        return []
    widths = sorted({w for w in WIDTHS if w < original_width} | {min(original_width, WIDTHS[-1])})
    sources = []
    for width in widths:
        url = build_variant(field_file, width)
        if url:
            sources.append((url, width))
    return sources
