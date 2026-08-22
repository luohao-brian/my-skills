"""Shared Ark Agent Plan API helpers."""

from __future__ import annotations

import base64
import contextlib
import datetime
import mimetypes
from pathlib import Path
from typing import Any
import uuid

import requests


def endpoint(base_url: str, suffix: str) -> str:
    base = base_url.strip().rstrip("/")
    suffix = suffix.strip("/")
    if base.endswith(f"/{suffix}"):
        return base
    if base.endswith("/chat/completions") and suffix != "chat/completions":
        base = base[: -len("/chat/completions")]
    return f"{base}/{suffix}"


def bearer_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def post_json(
    base_url: str,
    suffix: str,
    api_key: str,
    payload: dict[str, Any],
    *,
    timeout: float,
) -> requests.Response:
    return requests.post(
        endpoint(base_url, suffix),
        headers=bearer_headers(api_key),
        json=payload,
        timeout=timeout,
    )


def response_error(response: requests.Response) -> str:
    message = ""
    with contextlib.suppress(Exception):
        payload = response.json()
        error = payload.get("error")
        if isinstance(error, dict):
            message = str(error.get("message") or error.get("code") or "")
        elif isinstance(error, str):
            message = error
    if not message:
        message = response.text[:500]
    request_id = (
        response.headers.get("x-request-id")
        or response.headers.get("x-tt-logid")
        or response.headers.get("x-client-request-id")
    )
    suffix = f"; request_id={request_id}" if request_id else ""
    return f"HTTP {response.status_code}: {message[:500]}{suffix}"


def extract_chat_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not isinstance(choices, list) or not choices:
        return ""
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "\n".join(
            str(item.get("text") or "").strip()
            for item in content
            if isinstance(item, dict) and str(item.get("text") or "").strip()
        ).strip()
    return ""


def bytes_to_data_url(data: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def file_to_data_url(path: str | Path, fallback_mime: str = "application/octet-stream") -> str:
    p = Path(path).expanduser()
    mime = mimetypes.guess_type(str(p))[0] or fallback_mime
    encoded = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def image_extension_from_bytes(raw: bytes, fallback: str = "png") -> str:
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
        return "webp"
    if raw.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    return fallback.strip(".").lower() or "png"


def save_b64_image_detected(b64_data: str, *, prefix: str = "image") -> tuple[Path, str]:
    from hermes_constants import get_hermes_home

    payload = b64_data.split(",", 1)[1] if b64_data.startswith("data:") and "," in b64_data else b64_data
    raw = base64.b64decode(payload)
    extension = image_extension_from_bytes(raw)
    cache_dir = get_hermes_home() / "cache" / "images"
    cache_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    short = uuid.uuid4().hex[:8]
    path = cache_dir / f"{prefix}_{ts}_{short}.{extension}"
    path.write_bytes(raw)
    return path, extension
