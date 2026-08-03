#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import mimetypes
import os
import sys
from pathlib import Path
from typing import Any

SIZE_ALIASES = {
    "1:1": "2048x2048",
    "3:4": "1536x2048",
    "4:3": "2048x1536",
    "16:9": "2048x1152",
    "9:16": "1152x2048",
    "21:9": "2560x1080",
}
BASE_URL = "https://ark.cn-beijing.volces.com/api/plan/v3"
MODEL_ID = "doubao-seedream-5.0-lite"
DEFAULT_SIZE = "2k"
REQUEST_TIMEOUT_SECONDS = 180


def api_key_value() -> str:
    return os.getenv("ARK_AGENT_PLAN_API_KEY", "").strip()


def require_requests():
    try:
        import requests
    except ImportError:
        print("Error: requests is unavailable in the caller-selected Python environment", file=sys.stderr)
        sys.exit(1)
    return requests


def normalize_size(value: str) -> str:
    size = value.strip()
    alias = SIZE_ALIASES.get(size)
    if alias:
        return alias
    if size.lower() in {"2k", "3k", "4k"}:
        return size.lower()
    return size


def file_to_data_url(path: str) -> str:
    p = Path(path).expanduser()
    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    payload = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def image_ext(raw: bytes, fallback: str = "png") -> str:
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
        return "webp"
    return fallback


def output_path(output: str | None, ext: str) -> Path:
    if output:
        path = Path(output).expanduser()
        suffix_ext = "jpg" if path.suffix.lower() in {".jpg", ".jpeg"} else path.suffix.lower().lstrip(".")
        if suffix_ext != ext:
            path = path.with_suffix(f".{ext}")
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    directory = Path("outputs") / "images"
    directory.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return directory / f"ark_image_{stamp}.{ext}"


def save_b64(value: str, output: str | None) -> Path:
    payload = value.split(",", 1)[1] if value.startswith("data:") and "," in value else value
    raw = base64.b64decode(payload)
    path = output_path(output, image_ext(raw))
    path.write_bytes(raw)
    return path


def save_url(url: str, output: str | None) -> Path:
    requests = require_requests()

    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    fallback = "jpg" if "jpeg" in content_type else "webp" if "webp" in content_type else "png"
    path = output_path(output, image_ext(response.content, fallback))
    path.write_bytes(response.content)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate images with Ark Agent Plan")
    parser.add_argument("prompt")
    parser.add_argument("--image", help="Optional local reference image path or data URL")
    parser.add_argument("--size", default=DEFAULT_SIZE)
    parser.add_argument("--output", help="Output image path")
    args = parser.parse_args()

    api_key = api_key_value()
    if not api_key:
        print(json.dumps({"success": False, "error": "Missing ARK_AGENT_PLAN_API_KEY"}, ensure_ascii=False), file=sys.stderr)
        return 2

    requests = require_requests()

    payload: dict[str, Any] = {
        "model": MODEL_ID,
        "prompt": args.prompt,
        "size": normalize_size(args.size),
        "response_format": "b64_json",
        "stream": False,
        "watermark": False,
    }
    if args.image:
        payload["image"] = args.image if args.image.startswith("data:") else file_to_data_url(args.image)

    try:
        response = requests.post(
            f"{BASE_URL}/images/generations",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:500]}")
        body = response.json()
        item = (body.get("data") or [{}])[0]
        remote_url = item.get("url")
        if item.get("b64_json"):
            path = save_b64(item["b64_json"], args.output)
        elif remote_url:
            path = save_url(remote_url, args.output)
        else:
            raise RuntimeError(f"No image in response: {json.dumps(body, ensure_ascii=False)[:800]}")
        print(json.dumps({
            "success": True,
            "type": "image",
            "local_path": str(path),
            "remote_url": remote_url,
            "model": MODEL_ID,
            "prompt": args.prompt,
            "size": normalize_size(args.size),
            "used_reference_image": bool(args.image),
        }, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
