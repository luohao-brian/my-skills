#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import mimetypes
import os
import re
import sys
from pathlib import Path
from typing import Any


# Official contract: https://www.volcengine.com/docs/82379/1541523?lang=zh
DEFAULT_BACKEND = "ark-agent-plan"
DEFAULT_RESOLUTION = "2K"
DEFAULT_OUTPUT_DIR = Path.home() / "Documents" / "hermes-workspace" / "images"
REQUEST_TIMEOUT_SECONDS = 180
PRO_MODEL = "doubao-seedream-5-0-pro-260628"
ASPECT_RATIOS = ("1:1", "3:4", "4:3", "3:2", "2:3", "16:9", "9:16", "21:9")
SIZE_ALIASES = {value: value for value in ASPECT_RATIOS}

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
    "ark-api": ("doubao-seedream-5-0-260128", PRO_MODEL),
}
MODEL_CAPABILITIES = {
    "doubao-seedream-5.0-lite": {
        "resolutions": ("2K", "3K", "4K"),
        "max_references": 14,
        "max_images": 15,
        "multi_image": True,
        "web_search": True,
        "layer_decomposition": False,
    },
    "doubao-seedream-5-0-260128": {
        "resolutions": ("2K", "3K", "4K"),
        "max_references": 14,
        "max_images": 15,
        "multi_image": True,
        "web_search": True,
        "layer_decomposition": False,
    },
    PRO_MODEL: {
        "resolutions": ("1K", "1.5K", "2K"),
        "max_references": 10,
        "max_images": 1,
        "multi_image": False,
        "web_search": False,
        "layer_decomposition": True,
    },
}


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


def normalize_resolution(value: str, *, allow_auto: bool = False) -> str:
    normalized = value.strip().upper()
    allowed = {"1K", "1.5K", "2K", "3K", "4K"}
    if allow_auto:
        allowed.add("AUTO")
    if normalized not in allowed:
        raise ValueError(f"Unsupported resolution: {value}")
    return "auto" if normalized == "AUTO" else normalized


def normalize_size(value: str) -> str:
    """Normalize the deprecated --size compatibility input."""
    size = value.strip()
    if size in ASPECT_RATIOS:
        return size
    if size.lower() in {"1k", "1.5k", "2k", "3k", "4k", "auto"}:
        return normalize_resolution(size, allow_auto=True)
    if re.fullmatch(r"\d+[xX]\d+", size):
        return size.lower()
    return size


def resolve_size(aspect_ratio: str, resolution: str) -> str:
    """Return a provider-native tier; aspect ratio is expressed in the prompt."""
    if aspect_ratio not in ASPECT_RATIOS:
        raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")
    return normalize_resolution(resolution)


def prompt_with_aspect_ratio(prompt: str, aspect_ratio: str) -> str:
    text = prompt.strip()
    if not text:
        return text
    if aspect_ratio.replace(" ", "") in text.replace(" ", ""):
        return text
    return f"{text.rstrip('。.!！')}，画面宽高比为 {aspect_ratio}。"


def infer_backend(model: str) -> str:
    return "ark-agent-plan" if model == "doubao-seedream-5.0-lite" else "ark-api"


def validate_pixel_size(model: str, value: str) -> None:
    match = re.fullmatch(r"(\d+)x(\d+)", value)
    if not match:
        raise ValueError(f"Invalid pixel size: {value}; expected WIDTHxHEIGHT")
    width, height = (int(part) for part in match.groups())
    ratio = width / height
    if not 1 / 16 <= ratio <= 16:
        raise ValueError("Pixel size aspect ratio must be between 1:16 and 16:1")
    if model == PRO_MODEL:
        pixels = width * height
        if not 921_600 <= pixels <= 4_624_220:
            raise ValueError("Seedream 5.0 Pro pixel size must contain 921600 to 4624220 pixels")


def validate_request(
    backend: str,
    model: str,
    resolution: str,
    count: int,
    *,
    image_count: int = 0,
    layer_decomposition: bool = False,
    web_search: bool = False,
    provider_size: str | None = None,
    prompt: str = "prompt",
) -> None:
    if model not in BACKEND_MODELS[backend]:
        raise ValueError(f"Model {model} is not supported by backend {backend}")
    capabilities = MODEL_CAPABILITIES[model]

    if layer_decomposition:
        if not capabilities["layer_decomposition"]:
            raise ValueError("Layer decomposition requires Seedream 5.0 Pro")
        if image_count != 1:
            raise ValueError("Layer decomposition requires exactly one input image")
        if count != 1:
            raise ValueError("Layer decomposition does not accept multiple output requests")
        if provider_size is not None:
            raise ValueError("Layer decomposition accepts only 1K, 1.5K, 2K, or auto")
        normalized = normalize_resolution(resolution, allow_auto=True)
        if normalized not in {"1K", "1.5K", "2K", "auto"}:
            raise ValueError("Layer decomposition accepts only 1K, 1.5K, 2K, or auto")
    else:
        if not prompt.strip():
            raise ValueError("Prompt is required for image generation")
        normalized = normalize_resolution(resolution)
        if provider_size is None and normalized not in capabilities["resolutions"]:
            values = ", ".join(capabilities["resolutions"])
            raise ValueError(f"Model {model} supports {values}")
        if provider_size is not None:
            validate_pixel_size(model, provider_size)

    if web_search and not capabilities["web_search"]:
        raise ValueError(f"Model {model} does not support web search")
    if image_count > capabilities["max_references"]:
        raise ValueError(f"Model {model} accepts at most {capabilities['max_references']} reference images")
    if not 1 <= count <= capabilities["max_images"]:
        raise ValueError(f"Model {model} accepts 1 to {capabilities['max_images']} output images")
    if capabilities["multi_image"] and image_count + count > 15:
        raise ValueError("Reference image count plus maximum output images must not exceed 15")


def build_payload(
    *,
    model: str,
    prompt: str,
    images: list[str],
    aspect_ratio: str,
    resolution: str,
    count: int,
    backend: str | None = None,
    provider_size: str | None = None,
    output_format: str = "png",
    response_format: str = "url",
    web_search: bool = False,
    layer_decomposition: bool = False,
) -> dict[str, Any]:
    selected_backend = backend or infer_backend(model)
    validate_request(
        selected_backend,
        model,
        resolution,
        count,
        image_count=len(images),
        layer_decomposition=layer_decomposition,
        web_search=web_search,
        provider_size=provider_size,
        prompt=prompt,
    )
    effective_prompt = prompt.strip()
    if not layer_decomposition:
        effective_prompt = prompt_with_aspect_ratio(effective_prompt, aspect_ratio)

    payload: dict[str, Any] = {
        "model": model,
        "size": provider_size or normalize_resolution(resolution, allow_auto=layer_decomposition),
        "output_format": output_format,
        "response_format": response_format,
        "watermark": False,
    }
    if effective_prompt:
        payload["prompt"] = effective_prompt
    if images:
        payload["image"] = images[0] if len(images) == 1 else images
    if layer_decomposition:
        payload["layer_decomposition"] = True
    elif model != PRO_MODEL:
        payload["sequential_image_generation"] = "auto" if count > 1 else "disabled"
        if count > 1:
            payload["sequential_image_generation_options"] = {"max_images": count}
    if web_search:
        payload["tools"] = [{"type": "web_search"}]
    return payload


def file_to_data_url(path: str) -> str:
    source = Path(path).expanduser()
    if not source.is_file():
        raise ValueError(f"Reference image does not exist: {path}")
    mime = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
    payload = base64.b64encode(source.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def normalize_image_input(value: str) -> str:
    source = value.strip()
    if source.startswith("file-"):
        raise ValueError(
            "Ark image generation does not accept Files API file_id references; "
            "use an HTTP(S) image URL or a local image/data URL"
        )
    if source.startswith(("https://", "http://", "data:")):
        return source
    return file_to_data_url(source)


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
    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_{index + 1}" if index else ""
    return DEFAULT_OUTPUT_DIR / f"ark_image_{stamp}{suffix}.{ext}"


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


def public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    image = result.get("image")
    if isinstance(image, str) and image.startswith("data:"):
        result["image"] = "<local-image-data>"
    elif isinstance(image, list):
        result["image"] = ["<local-image-data>" if value.startswith("data:") else value for value in image]
    return result


def request_id_from(response: Any, body: dict[str, Any]) -> str | None:
    return body.get("request_id") or response.headers.get("x-request-id") or response.headers.get("x-tt-logid")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or decompose images with Ark Seedream")
    parser.add_argument("prompt", nargs="?", default="")
    parser.add_argument("--image", action="append", default=[], help="Reference image path, URL, or data URL; repeat in prompt order")
    parser.add_argument("--aspect-ratio", default="1:1", choices=ASPECT_RATIOS)
    parser.add_argument("--resolution", help="Resolution tier; defaults to 2K, or auto for layers")
    parser.add_argument("--size", help="Deprecated alias: aspect ratio, resolution, or WIDTHxHEIGHT")
    parser.add_argument("--max-images", type=int, help="Maximum Lite output count")
    parser.add_argument("--count", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--model", help="Backend-compatible model override")
    parser.add_argument("--output", help="Output image path")
    parser.add_argument("--output-format", choices=("png", "jpeg"), default="png")
    parser.add_argument("--response-format", choices=("url", "b64_json"), default="url")
    parser.add_argument("--web-search", action="store_true", help="Enable Lite web search")
    parser.add_argument("--layer-decomposition", action="store_true", help="Use Pro to split one input into a base image and layers")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print the request without calling Ark")
    parser.add_argument("--backend", choices=BACKENDS, default=DEFAULT_BACKEND)
    args = parser.parse_args()

    if args.max_images is not None and args.count is not None:
        parser.error("use --max-images or the deprecated --count alias, not both")
    max_images = args.max_images if args.max_images is not None else args.count or 1
    model = args.model or BACKENDS[args.backend]["model"]
    aspect_ratio = args.aspect_ratio
    resolution = args.resolution or ("auto" if args.layer_decomposition else DEFAULT_RESOLUTION)
    provider_size: str | None = None

    try:
        if args.size:
            normalized = normalize_size(args.size)
            if normalized in ASPECT_RATIOS:
                aspect_ratio = normalized
            elif normalized in {"1K", "1.5K", "2K", "3K", "4K", "auto"}:
                resolution = normalized
            elif re.fullmatch(r"\d+x\d+", normalized):
                provider_size = normalized
            else:
                raise ValueError(f"Unsupported --size value: {args.size}")
        images = [normalize_image_input(value) for value in args.image]
        payload = build_payload(
            backend=args.backend,
            model=model,
            prompt=args.prompt,
            images=images,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            count=max_images,
            provider_size=provider_size,
            output_format=args.output_format,
            response_format=args.response_format,
            web_search=args.web_search,
            layer_decomposition=args.layer_decomposition,
        )
    except Exception as exc:
        print(json.dumps({"success": False, "backend": args.backend, "model": model, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    if args.dry_run:
        print(json.dumps({"success": True, "dry_run": True, "backend": args.backend, "request": public_payload(payload)}, ensure_ascii=False, indent=2))
        return 0

    try:
        profile, api_key = resolve_backend(args.backend)
        requests = require_requests()
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
            output = {
                "local_path": str(path.resolve()),
                "remote_url": remote_url,
                "size": item.get("size"),
                "output_format": item.get("output_format"),
            }
            for field in ("z_index", "bounding_box", "name", "description"):
                if field in item:
                    output[field] = item[field]
            outputs.append(output)
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
            "prompt": payload.get("prompt", ""),
            "aspect_ratio": None if args.layer_decomposition else aspect_ratio,
            "resolution": resolution,
            "size": payload["size"],
            "used_reference_image": bool(images),
            "layer_decomposition": args.layer_decomposition,
            "usage": body.get("usage"),
            "request_id": request_id_from(response, body),
        }, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"success": False, "backend": args.backend, "model": model, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
