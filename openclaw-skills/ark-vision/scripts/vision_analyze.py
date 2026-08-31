#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DEFAULT_BACKEND = "ark-agent-plan"
BACKENDS = {
    "ark-agent-plan": {
        "base_url": "https://ark.cn-beijing.volces.com/api/plan/v3",
        "api_key_env": "ARK_AGENT_PLAN_API_KEY",
        "model": "doubao-seed-2.0-lite",
    },
    "ark-api": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_key_env": "ARK_API_KEY",
        "model": "doubao-seed-2-0-lite-260428",
    },
}
BACKEND_MODELS = {
    "ark-agent-plan": ("doubao-seed-2.0-lite", "doubao-seed-2.0-mini"),
    "ark-api": ("doubao-seed-2-0-lite-260428", "doubao-seed-2-0-mini-260428"),
}
ARK_FILES_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
MAX_OUTPUT_TOKENS = 2000
TEMPERATURE = 0.1
REQUEST_TIMEOUT_SECONDS = 300
MAX_INLINE_IMAGE_BYTES = 20 * 1024 * 1024
MAX_INLINE_VIDEO_BYTES = 50 * 1024 * 1024
MAX_INLINE_PDF_BYTES = 50 * 1024 * 1024
IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff",
    ".ico", ".icns", ".sgi", ".jp2", ".heic", ".heif",
}
VIDEO_EXTENSIONS = {".avi", ".mkv", ".mov", ".mp4", ".webm", ".m4v"}
PDF_EXTENSIONS = {".pdf"}
MEDIA_TYPES = ("auto", "image", "video", "pdf")


def _require_requests():
    try:
        import requests
    except ImportError:
        print("Error: requests is unavailable in the caller-selected Python environment", file=sys.stderr)
        raise SystemExit(1)
    return requests


def resolve_backend(name: str) -> tuple[dict[str, str], str]:
    profile = BACKENDS.get(name)
    if profile is None:
        raise ValueError(f"Unsupported backend: {name}")
    api_key_env = profile["api_key_env"]
    api_key = os.getenv(api_key_env, "").strip()
    if not api_key:
        raise ValueError(f"Missing {api_key_env} for backend {name}")
    return profile, api_key


def response_error(response: Any) -> str:
    message = ""
    try:
        payload = response.json()
        error = payload.get("error") if isinstance(payload, dict) else None
        if isinstance(error, dict) and error.get("message"):
            message = str(error["message"])
        elif isinstance(error, str) and error:
            message = error
    except Exception:
        pass
    if not message:
        message = response.text[:800]
    request_id = response.headers.get("x-request-id") or response.headers.get("x-client-request-id")
    return f"HTTP {response.status_code}: {message[:800]}" + (f"; request_id={request_id}" if request_id else "")


def is_file_id(reference: str) -> bool:
    return reference.strip().startswith("file-")


def extension_media_type(extension: str) -> str | None:
    suffix = extension.lower()
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix in VIDEO_EXTENSIONS:
        return "video"
    if suffix in PDF_EXTENSIONS:
        return "pdf"
    return None


def infer_media_type(reference: str) -> str:
    value = reference.strip()
    lowered = value.lower()
    if lowered.startswith("data:image/"):
        return "image"
    if lowered.startswith("data:video/"):
        return "video"
    if lowered.startswith("data:application/pdf"):
        return "pdf"
    if is_file_id(value):
        raise ValueError("A file_id requires --media-type or ARK_API_KEY metadata access")
    path_text = urlparse(value).path if lowered.startswith(("http://", "https://")) else value
    kind = extension_media_type(Path(path_text).suffix)
    if kind:
        return kind
    raise ValueError("Cannot infer media type; pass --media-type image, video, or pdf")


def file_id_media_type(file_id: str) -> str:
    key = os.getenv("ARK_API_KEY", "").strip()
    if not key:
        raise ValueError("A file_id requires --media-type when ARK_API_KEY is unavailable")
    requests = _require_requests()
    response = requests.get(
        f"{ARK_FILES_BASE_URL}/files/{file_id}",
        headers={"Authorization": f"Bearer {key}"},
        timeout=60,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Cannot retrieve file metadata: {response_error(response)}")
    body = response.json()
    status = str(body.get("status") or "").lower()
    if status and status != "active":
        raise ValueError(f"File {file_id} is not active; current status={status}")
    mime = str(body.get("mime_type") or body.get("content_type") or "").lower()
    if mime.startswith("image/"):
        return "image"
    if mime.startswith("video/"):
        return "video"
    if mime == "application/pdf":
        return "pdf"
    filename = str(body.get("filename") or "")
    kind = extension_media_type(Path(filename).suffix)
    if kind:
        return kind
    raise ValueError(f"Unsupported or unknown file media type: {mime or filename or 'unknown'}")


def resolve_media_type(reference: str, explicit: str = "auto") -> str:
    if explicit != "auto":
        return explicit
    if is_file_id(reference):
        return file_id_media_type(reference.strip())
    return infer_media_type(reference)


def expected_data_prefix(kind: str) -> str:
    if kind == "image":
        return "data:image/"
    if kind == "video":
        return "data:video/"
    return "data:application/pdf"


def file_to_data_url(path_text: str, kind: str) -> str:
    path = Path(path_text).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"media file not found: {path_text}")
    size = path.stat().st_size
    limit = {
        "image": MAX_INLINE_IMAGE_BYTES,
        "video": MAX_INLINE_VIDEO_BYTES,
        "pdf": MAX_INLINE_PDF_BYTES,
    }[kind]
    if size > limit:
        raise ValueError(
            f"Local {kind} exceeds the {limit // (1024 * 1024)} MB inline limit; "
            "upload it with ark-file and pass the returned file_id"
        )
    mime = mimetypes.guess_type(path.name)[0]
    if kind == "pdf":
        mime = "application/pdf"
    elif not mime:
        mime = "image/jpeg" if kind == "image" else "video/mp4"
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def normalize_media(reference: str, kind: str) -> str:
    value = reference.strip()
    if is_file_id(value):
        return value
    lowered = value.lower()
    if lowered.startswith(("http://", "https://")):
        return value
    if lowered.startswith("data:"):
        if not lowered.startswith(expected_data_prefix(kind)):
            raise ValueError(f"Expected a {kind} data URL")
        return value
    return file_to_data_url(value, kind)


def pdf_filename(reference: str) -> str:
    value = reference.strip()
    if value.lower().startswith(("http://", "https://")):
        name = Path(urlparse(value).path).name
        return name if name.lower().endswith(".pdf") else "document.pdf"
    if value.lower().startswith("data:"):
        return "document.pdf"
    name = Path(value).name
    return name if name.lower().endswith(".pdf") else "document.pdf"


def build_media_content(reference: str, explicit_type: str = "auto") -> tuple[dict[str, Any], str]:
    kind = resolve_media_type(reference, explicit_type)
    normalized = normalize_media(reference, kind)
    if is_file_id(normalized):
        if kind == "image":
            return {"type": "image_url", "image_url": {"file_id": normalized}}, kind
        if kind == "video":
            return {"type": "video_url", "video_url": {"file_id": normalized}}, kind
        return {"type": "file", "file": {"file_id": normalized}}, kind
    if kind == "image":
        return {"type": "image_url", "image_url": {"url": normalized}}, kind
    if kind == "video":
        return {"type": "video_url", "video_url": {"url": normalized}}, kind
    if normalized.lower().startswith(("http://", "https://")):
        return {"type": "file", "file": {"file_url": normalized}}, kind
    return {
        "type": "file",
        "file": {"file_data": normalized, "filename": pdf_filename(reference)},
    }, kind


def extract_chat_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not isinstance(choices, list) or not choices:
        return ""
    content = (choices[0].get("message") or {}).get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "\n".join(
            str(item.get("text") or "").strip()
            for item in content
            if isinstance(item, dict) and str(item.get("text") or "").strip()
        ).strip()
    return ""


def safe_source(reference: str) -> str:
    if reference.startswith("data:"):
        return "<data-url>"
    return reference


def analyze_media(args: argparse.Namespace) -> dict[str, Any]:
    requests = _require_requests()
    profile, key = resolve_backend(args.backend)
    model = args.model or profile["model"]
    if model not in BACKEND_MODELS[args.backend]:
        raise ValueError(f"Model {model} is not supported by backend {args.backend}")

    media_content, input_type = build_media_content(args.media, args.media_type)
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    media_content,
                    {"type": "text", "text": args.question},
                ],
            }
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_OUTPUT_TOKENS,
    }
    response = requests.post(
        f"{profile['base_url']}/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if response.status_code >= 400:
        raise RuntimeError(response_error(response))

    body = response.json()
    analysis = extract_chat_text(body)
    if not analysis:
        raise RuntimeError("Vision response contained no analysis text")
    result: dict[str, Any] = {
        "success": True,
        "type": "vision",
        "backend": args.backend,
        "media_type": input_type,
        "analysis": analysis,
        "model": model,
        "media": safe_source(args.media),
    }
    if is_file_id(args.media):
        result["file_id"] = args.media.strip()
    if args.raw:
        result["raw"] = body
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze images, videos, PDFs, or Ark file IDs")
    parser.add_argument("media", help="Local path, HTTP(S) URL, data URL, or Ark file_id")
    parser.add_argument("question", help="Question or extraction instruction about the media")
    parser.add_argument("--media-type", choices=MEDIA_TYPES, default="auto", help="Required for ambiguous URLs/file IDs without ARK_API_KEY")
    parser.add_argument("--json", action="store_true", help="Print structured JSON instead of plain analysis text")
    parser.add_argument("--raw", action="store_true", help="Include raw provider response in JSON output")
    parser.add_argument("--model", help="Backend-compatible model override")
    parser.add_argument("--backend", choices=BACKENDS, default=DEFAULT_BACKEND)
    args = parser.parse_args()

    try:
        result = analyze_media(args)
    except Exception as exc:
        try:
            input_type = resolve_media_type(args.media, args.media_type)
        except Exception:
            input_type = args.media_type
        error = {
            "success": False,
            "type": "vision",
            "backend": args.backend,
            "media_type": input_type,
            "error": str(exc),
            "model": args.model or BACKENDS[args.backend]["model"],
            "media": safe_source(args.media),
        }
        print(json.dumps(error, ensure_ascii=False), file=sys.stderr)
        return 1

    if args.json or args.raw:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["analysis"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
