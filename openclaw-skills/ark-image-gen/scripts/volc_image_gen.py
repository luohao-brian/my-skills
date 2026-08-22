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
    "3:4": "1728x2304",
    "4:3": "2304x1728",
    "3:2": "2496x1664",
    "2:3": "1664x2496",
    "16:9": "2848x1600",
    "9:16": "1600x2848",
    "21:9": "3136x1344",
}
# Official image generation request contract:
# https://www.volcengine.com/docs/82379/1541523?lang=zh
# Agent Plan exposes the same resource under the fixed /api/plan/v3 base.
DEFAULT_BACKEND = "ark-agent-plan"
BACKENDS = {
    "ark-agent-plan": {
        "base_url": "https://ark.cn-beijing.volces.com/api/plan/v3",
        "api_key_env": "ARK_AGENT_PLAN_API_KEY",
        "model": "doubao-seedream-5.0-lite",
    },
    "ark-api": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_key_env": "ARK_API_KEY",
        "model": "doubao-seedream-5-0-260128",
    },
}
BACKEND_MODELS = {
    "ark-agent-plan": ("doubao-seedream-5.0-lite",),
    "ark-api": (
        "doubao-seedream-5-0-260128",
        "doubao-seedream-5-0-pro-260628",
    ),
}
PRO_MODEL = "doubao-seedream-5-0-pro-260628"
DEFAULT_RESOLUTION = "2K"
REQUEST_TIMEOUT_SECONDS = 180


def resolve_backend(name: str) -> tuple[dict[str, str], str]:
    profile = BACKENDS.get(name)
    if profile is None:
        raise ValueError(f"Unsupported backend: {name}")
    api_key_env = profile["api_key_env"]
    api_key = os.getenv(api_key_env, "").strip()
    if not api_key:
        raise ValueError(f"Missing {api_key_env} for backend {name}")
    return profile, api_key


def require_requests():
    try:
        import requests
    except ImportError:
        print("Error: requests is unavailable in the caller-selected Python environment", file=sys.stderr)
        sys.exit(1)
    return requests


def normalize_resolution(value: str) -> str:
    normalized = value.strip().upper()
    if normalized == "1.5K":
        return normalized
    if normalized in {"1K", "2K", "3K", "4K"}:
        return normalized
    raise ValueError(f"Unsupported resolution: {value}")


def resolve_size(aspect_ratio: str, resolution: str) -> str:
    base = SIZE_ALIASES.get(aspect_ratio.strip())
    if base is None:
        # Preserve the old --size escape hatch for a provider-native WIDTHxHEIGHT.
        if "x" in aspect_ratio.lower():
            return aspect_ratio.lower()
        raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")
    width, height = (int(part) for part in base.split("x", 1))
    scale = {"1K": 0.5, "1.5K": 0.75, "2K": 1.0, "3K": 1.5, "4K": 2.0}[
        normalize_resolution(resolution)
    ]
    return f"{round(width * scale)}x{round(height * scale)}"


def normalize_size(value: str) -> str:
    """Backward-compatible normalizer used by older callers and tests."""
    size = value.strip()
    alias = SIZE_ALIASES.get(size)
    if alias:
        return alias
    if size.lower() in {"1k", "1.5k", "2k", "3k", "4k"}:
        return size.upper()
    return size


def validate_request(backend: str, model: str, resolution: str, count: int) -> None:
    if model not in BACKEND_MODELS[backend]:
        raise ValueError(f"Model {model} is not supported by backend {backend}")
    normalized_resolution = normalize_resolution(resolution)
    if model == PRO_MODEL:
        if count != 1:
            raise ValueError(f"Model {PRO_MODEL} supports exactly one output image")
        if normalized_resolution not in {"1K", "1.5K", "2K"}:
            raise ValueError(f"Model {PRO_MODEL} supports 1K, 1.5K, or 2K")
    elif normalized_resolution not in {"2K", "3K", "4K"}:
        raise ValueError(f"Model {model} supports 2K, 3K, or 4K")
    if not 1 <= count <= 15:
        raise ValueError("Image count must be between 1 and 15")


def build_payload(
    *,
    model: str,
    prompt: str,
    images: list[str],
    aspect_ratio: str,
    resolution: str,
    count: int,
) -> dict[str, Any]:
    validate_request("ark-api" if model in BACKEND_MODELS["ark-api"] else "ark-agent-plan", model, resolution, count)
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "size": resolve_size(aspect_ratio, resolution),
        "response_format": "url",
        "stream": False,
        "watermark": False,
    }
    if images:
        payload["image"] = images[0] if len(images) == 1 else images
    if model != PRO_MODEL:
        payload["sequential_image_generation"] = "auto" if count > 1 else "disabled"
        if count > 1:
            payload["sequential_image_generation_options"] = {"max_images": count}
    return payload


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


def output_path(output: str | None, ext: str, index: int = 0) -> Path:
    if output:
        path = Path(output).expanduser()
        suffix_ext = "jpg" if path.suffix.lower() in {".jpg", ".jpeg"} else path.suffix.lower().lstrip(".")
        if suffix_ext != ext:
            path = path.with_suffix(f".{ext}")
        path.parent.mkdir(parents=True, exist_ok=True)
        if index:
            path = path.with_name(f"{path.stem}_{index + 1}{path.suffix}")
        return path
    directory = Path("outputs") / "images"
    directory.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_{index + 1}" if index else ""
    return directory / f"ark_image_{stamp}{suffix}.{ext}"


def save_b64(value: str, output: str | None, index: int = 0) -> Path:
    payload = value.split(",", 1)[1] if value.startswith("data:") and "," in value else value
    raw = base64.b64decode(payload)
    path = output_path(output, image_ext(raw), index)
    path.write_bytes(raw)
    return path


def save_url(url: str, output: str | None, index: int = 0) -> Path:
    requests = require_requests()

    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    fallback = "jpg" if "jpeg" in content_type else "webp" if "webp" in content_type else "png"
    path = output_path(output, image_ext(response.content, fallback), index)
    path.write_bytes(response.content)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate images with Ark")
    parser.add_argument("prompt")
    parser.add_argument("--image", action="append", default=[], help="Reference image path/data URL; repeat for multiple images")
    parser.add_argument("--aspect-ratio", default="1:1", choices=SIZE_ALIASES)
    parser.add_argument("--resolution", default=DEFAULT_RESOLUTION)
    parser.add_argument("--size", help="Deprecated alias: aspect ratio, resolution, or WIDTHxHEIGHT")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--model", help="Backend-compatible model override")
    parser.add_argument("--output", help="Output image path")
    parser.add_argument("--backend", choices=BACKENDS, default=DEFAULT_BACKEND)
    args = parser.parse_args()

    try:
        profile, api_key = resolve_backend(args.backend)
    except ValueError as exc:
        print(json.dumps({"success": False, "backend": args.backend, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    requests = require_requests()
    model = args.model or profile["model"]
    aspect_ratio = args.aspect_ratio
    resolution = args.resolution
    provider_size: str | None = None
    try:
        if args.size:
            normalized = normalize_size(args.size)
            if args.size in SIZE_ALIASES:
                aspect_ratio = args.size
            elif normalized in {"1K", "1.5K", "2K", "3K", "4K"}:
                resolution = normalized
            elif "x" in normalized.lower():
                provider_size = normalized
            else:
                raise ValueError(f"Unsupported --size value: {args.size}")
        images = [value if value.startswith("data:") else file_to_data_url(value) for value in args.image]
    except Exception as exc:
        print(json.dumps({"success": False, "backend": args.backend, "model": model, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    try:
        validate_request(args.backend, model, resolution, args.count)
        payload = build_payload(
            model=model,
            prompt=args.prompt,
            images=images,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            count=args.count,
        )
        if provider_size:
            payload["size"] = provider_size
        response = requests.post(
            f"{profile['base_url']}/images/generations",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:500]}")
        body = response.json()
        items = body.get("data") or []
        if not isinstance(items, list) or not items:
            raise RuntimeError(f"No image in response: {json.dumps(body, ensure_ascii=False)[:800]}")
        outputs = []
        for index, item in enumerate(items):
            remote_url = item.get("url")
            if item.get("b64_json"):
                path = save_b64(item["b64_json"], args.output, index)
            elif remote_url:
                path = save_url(remote_url, args.output, index)
            else:
                continue
            outputs.append({"local_path": str(path), "remote_url": remote_url})
        if not outputs:
            raise RuntimeError(f"No usable image in response: {json.dumps(body, ensure_ascii=False)[:800]}")
        print(json.dumps({
            "success": True,
            "type": "image",
            "backend": args.backend,
            "local_path": outputs[0]["local_path"],
            "remote_url": outputs[0]["remote_url"],
            "images": outputs,
            "count": len(outputs),
            "model": model,
            "prompt": args.prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": normalize_resolution(resolution),
            "size": payload["size"],
            "used_reference_image": bool(images),
        }, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({
            "success": False,
            "backend": args.backend,
            "model": model,
            "error": str(exc),
        }, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
