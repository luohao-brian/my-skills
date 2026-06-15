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


def env_first(names: list[str]) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def endpoint(base_url: str, suffix: str) -> str:
    base = base_url.strip().rstrip("/")
    suffix = suffix.strip("/")
    if base.endswith(f"/{suffix}"):
        return base
    return f"{base}/{suffix}"


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


def output_path(out_dir: str, ext: str, filename: str | None) -> Path:
    directory = Path(out_dir).expanduser()
    directory.mkdir(parents=True, exist_ok=True)
    if filename:
        path = Path(filename)
        return path if path.is_absolute() else directory / path
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return directory / f"ark_image_{stamp}.{ext}"


def save_b64(value: str, out_dir: str, filename: str | None) -> Path:
    payload = value.split(",", 1)[1] if value.startswith("data:") and "," in value else value
    raw = base64.b64decode(payload)
    path = output_path(out_dir, image_ext(raw), filename)
    path.write_bytes(raw)
    return path


def save_url(url: str, out_dir: str, filename: str | None, timeout: float) -> Path:
    import requests

    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    fallback = "jpg" if "jpeg" in content_type else "webp" if "webp" in content_type else "png"
    path = output_path(out_dir, image_ext(response.content, fallback), filename)
    path.write_bytes(response.content)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate images with Volcengine Ark")
    parser.add_argument("prompt")
    parser.add_argument("--image", help="Optional local reference image path or data URL")
    parser.add_argument("--size", default=os.getenv("VOLC_IMAGE_SIZE", "2K"))
    parser.add_argument("--model", default=os.getenv("VOLC_IMAGE_MODEL_ID", "doubao-seedream-5.0-lite"))
    parser.add_argument("--base-url", default=os.getenv("VOLC_ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/plan/v3"))
    parser.add_argument("--output-dir", default=os.getenv("VOLC_IMAGE_OUTPUT_DIR", "outputs/images"))
    parser.add_argument("--filename")
    parser.add_argument("--timeout", type=float, default=float(os.getenv("VOLC_IMAGE_TIMEOUT", "180")))
    args = parser.parse_args()

    import requests

    api_key = env_first(["VOLC_AGENT_PLAN_API_KEY", "ARK_API_KEY", "OPENAPI_API_KEY"])
    if not api_key:
        print(json.dumps({"success": False, "error": "Missing VOLC_AGENT_PLAN_API_KEY"}, ensure_ascii=False), file=sys.stderr)
        return 2

    payload: dict[str, Any] = {
        "model": args.model,
        "prompt": args.prompt,
        "size": args.size,
        "response_format": "b64_json",
        "stream": False,
        "watermark": False,
    }
    if args.image:
        payload["image"] = args.image if args.image.startswith("data:") else file_to_data_url(args.image)

    try:
        response = requests.post(
            endpoint(args.base_url, "images/generations"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=max(args.timeout, 60),
        )
        if response.status_code >= 400:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:500]}")
        body = response.json()
        item = (body.get("data") or [{}])[0]
        remote_url = item.get("url")
        if item.get("b64_json"):
            path = save_b64(item["b64_json"], args.output_dir, args.filename)
        elif remote_url:
            path = save_url(remote_url, args.output_dir, args.filename, max(args.timeout, 60))
        else:
            raise RuntimeError(f"No image in response: {json.dumps(body, ensure_ascii=False)[:800]}")
        print(json.dumps({
            "success": True,
            "type": "image",
            "local_path": str(path),
            "remote_url": remote_url,
            "model": args.model,
            "prompt": args.prompt,
            "size": args.size,
            "used_reference_image": bool(args.image),
        }, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
