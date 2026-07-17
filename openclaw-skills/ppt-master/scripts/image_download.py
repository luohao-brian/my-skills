"""Format-safe image download helper used by web image search."""

from __future__ import annotations

import io
from pathlib import Path

import requests
from PIL import Image

CONTENT_TYPE_TO_EXT = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/bmp": ".bmp",
    "image/tiff": ".tiff",
}

EXT_TO_FORMAT = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".webp": "WEBP",
    ".gif": "GIF",
    ".bmp": "BMP",
    ".tiff": "TIFF",
    ".tif": "TIFF",
}


def detect_extension(data: bytes, content_type: str | None) -> str | None:
    if content_type:
        matched = CONTENT_TYPE_TO_EXT.get(content_type.split(";", 1)[0].strip().lower())
        if matched:
            return matched
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return ".webp"
    if data.startswith(b"BM"):
        return ".bmp"
    if data.startswith((b"II*\x00", b"MM\x00*")):
        return ".tiff"
    return None


def download_image(url: str, path: str, headers: dict | None = None, timeout: int = 180) -> str:
    response = requests.get(url, headers=headers or {}, timeout=timeout)
    response.raise_for_status()
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target_ext = target.suffix.lower()
    actual_ext = detect_extension(response.content, response.headers.get("Content-Type"))
    if target_ext == ".jpeg":
        target_ext = ".jpg"
    if actual_ext == target_ext:
        target.write_bytes(response.content)
        return str(target)

    output_format = EXT_TO_FORMAT.get(target.suffix.lower())
    if output_format is None:
        raise ValueError(f"unsupported image extension: {target.suffix}")
    with Image.open(io.BytesIO(response.content)) as image:
        if output_format == "JPEG" and image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGB")
        image.save(target, format=output_format)
    return str(target)
