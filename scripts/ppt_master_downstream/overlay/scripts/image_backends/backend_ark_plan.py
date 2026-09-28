"""Ark Agent Plan image adapter for PPT Master's image workflow."""

from __future__ import annotations

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
from image_backends.backend_volcengine import ASPECT_RATIO_SIZE_MAP


ENDPOINT = "https://ark.cn-beijing.volces.com/api/plan/v3/images/generations"
MODEL = "doubao-seedream-5.0-lite"


def generate(
    prompt: str,
    aspect_ratio: str = "1:1",
    image_size: str = "2K",
    output_dir: str | None = None,
    filename: str | None = None,
    model: str | None = None,
    max_retries: int = MAX_RETRIES,
) -> str:
    """Generate one image with the Agent Plan image credential."""
    selected_model = model or MODEL
    if selected_model != MODEL:
        raise ValueError(f"Unsupported Agent Plan image model: {selected_model}")
    size = ASPECT_RATIO_SIZE_MAP.get(normalize_image_size(image_size), {}).get(aspect_ratio)
    if not size:
        raise ValueError(f"Unsupported Agent Plan image size or aspect ratio: {image_size}, {aspect_ratio}")
    api_key = require_api_key(
        "ARK_AGENT_PLAN_API_KEY",
        message="No Agent Plan image key found. Set ARK_AGENT_PLAN_API_KEY.",
    )
    payload = {
        "model": selected_model,
        "prompt": prompt,
        "size": size,
        "response_format": "url",
        "watermark": False,
    }
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                ENDPOINT,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=300,
            )
            if response.status_code != 200:
                raise http_error(response, "Agent Plan image generation")
            data = response.json()
            items = data.get("data") or []
            image_url = items[0].get("url") if items else None
            if not image_url:
                raise RuntimeError(f"Agent Plan response missing image URL: {data}")
            path = resolve_output_path(prompt, output_dir, filename, ".jpeg")
            return download_image(image_url, path)
        except Exception as exc:
            last_error = exc
            if is_permanent_error(exc) or "quota" in str(exc).lower():
                raise
            if attempt >= max_retries:
                break
            time.sleep(retry_delay(attempt, rate_limited=is_rate_limit_error(exc)))
    raise RuntimeError(f"Agent Plan image generation failed: {last_error}") from last_error
