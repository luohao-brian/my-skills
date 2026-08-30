#!/usr/bin/env python3
"""
Volcengine Seedream image generation backend.

Configuration keys:
  ARK_AGENT_PLAN_API_KEY             (required)
"""

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

configure_utf8_stdio()

if __name__ == "__main__":
    print(__doc__)
    print("Use via: python3 {baseDir}/scripts/image_gen.py \"prompt\"")
    raise SystemExit(0 if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]) else 1)

import time

import requests

from image_backends.backend_common import (
    MAX_RETRIES,
    download_image,
    http_error,
    is_permanent_error,
    is_rate_limit_error,
    normalize_image_size,
    require_api_key,
    resolve_output_path,
    retry_delay,
)


ARK_AGENT_PLAN_ENDPOINT = "https://ark.cn-beijing.volces.com/api/plan/v3"
ARK_AGENT_PLAN_MODEL = "doubao-seedream-5.0-lite"
DEFAULT_IMAGE_SIZE = "2K"
FIXED_PROFILE = "ark-agent-plan"
FIXED_PROVIDER = "volc-ark-agent-plan"

ARK_ASPECT_RATIO_SIZE_MAP = {
    "1:1": (2048, 2048),
    "3:4": (1728, 2304),
    "4:3": (2304, 1728),
    "16:9": (2848, 1600),
    "9:16": (1600, 2848),
    "3:2": (2496, 1664),
    "2:3": (1664, 2496),
    "21:9": (3136, 1344),
}
ARK_SIZE_SCALE = {"512px": 1.0, "1K": 1.0, "2K": 1.0, "4K": 1.0}


def _resolve_url(base_url: str) -> str:
    """Resolve the Volcengine generation endpoint."""
    base = base_url.rstrip("/")
    if base.endswith("/images/generations"):
        return base
    if base.endswith(("/api/v3", "/api/plan/v3")):
        return base + "/images/generations"
    return base + "/api/v1/images/generations"


def _resolve_size(aspect_ratio: str, image_size: str) -> str:
    """Resolve the Agent Plan target resolution for a ratio and size preset."""
    normalized = normalize_image_size(image_size)
    dimensions = ARK_ASPECT_RATIO_SIZE_MAP.get(aspect_ratio)
    scale = ARK_SIZE_SCALE.get(normalized)
    if dimensions and scale:
        width, height = dimensions
        return f"{round(width * scale)}x{round(height * scale)}"
    supported = sorted(ARK_ASPECT_RATIO_SIZE_MAP)
    raise ValueError(
        f"Unsupported aspect ratio '{aspect_ratio}' for Ark image generation. "
        f"Supported: {supported}"
    )


def _generate_image(api_key: str, prompt: str,
                    aspect_ratio: str = "1:1", image_size: str = DEFAULT_IMAGE_SIZE,
                    output_dir: str = None, filename: str = None,
                    model: str = ARK_AGENT_PLAN_MODEL,
                    base_url: str = ARK_AGENT_PLAN_ENDPOINT) -> str:
    """Generate one image with the Volcengine backend."""
    size = _resolve_size(aspect_ratio, image_size)
    url = _resolve_url(base_url)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "response_format": "url",
        "watermark": False,
    }

    print("[Volcengine Seedream]")
    print(f"  Model:        {model}")
    print(f"  Prompt:       {prompt[:120]}{'...' if len(prompt) > 120 else ''}")
    print(f"  Aspect Ratio: {aspect_ratio}")
    print(f"  Resolution:   {size}")
    print()
    print("  [..] Generating...", end="", flush=True)
    start = time.time()
    response = requests.post(url, headers=headers, json=payload, timeout=300)
    elapsed = time.time() - start
    print(f"\n  [DONE] Response received ({elapsed:.1f}s)")

    if response.status_code != 200:
        raise http_error(response, "Volcengine image generation")

    data = response.json()
    items = data.get("data") or []
    image_url = items[0].get("url") if items else None
    if not image_url:
        raise RuntimeError(f"Volcengine response missing image URL: {data}")

    path = resolve_output_path(prompt, output_dir, filename, ".jpeg")
    return download_image(image_url, path)


def _resolve_profile(model: str = None) -> dict[str, object]:
    """Resolve the fixed Ark Agent Plan image profile."""
    api_key = require_api_key(
        "ARK_AGENT_PLAN_API_KEY",
        message="No Agent Plan image key found. Configure ARK_AGENT_PLAN_API_KEY.",
    )
    return {
        "profile": FIXED_PROFILE,
        "provider": FIXED_PROVIDER,
        "api_key": api_key,
        "base_url": ARK_AGENT_PLAN_ENDPOINT,
        "model": model or ARK_AGENT_PLAN_MODEL,
    }


def generate(prompt: str,
             aspect_ratio: str = "1:1", image_size: str = DEFAULT_IMAGE_SIZE,
             output_dir: str = None, filename: str = None,
             model: str = None, max_retries: int = MAX_RETRIES) -> str:
    """Generate an image with retries using the Volcengine backend."""
    profile = _resolve_profile(model)
    normalized_size = normalize_image_size(image_size)
    _resolve_size(aspect_ratio, normalized_size)

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return _generate_image(
                api_key=str(profile["api_key"]),
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                image_size=normalized_size,
                output_dir=output_dir,
                filename=filename,
                model=str(profile["model"]),
                base_url=str(profile["base_url"]),
            )
        except Exception as exc:
            last_error = exc
            if is_permanent_error(exc):
                raise
            if attempt >= max_retries:
                break
            limited = is_rate_limit_error(exc)
            delay = retry_delay(attempt, rate_limited=limited)
            label = "Rate limit hit" if limited else f"Error: {exc}"
            print(f"\n  [WARN] {label}. Retrying in {delay}s...")
            time.sleep(delay)

    raise RuntimeError(f"Failed after {max_retries + 1} attempts. Last error: {last_error}")
