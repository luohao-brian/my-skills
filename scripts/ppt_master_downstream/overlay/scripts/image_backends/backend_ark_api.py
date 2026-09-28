"""Ark API image generation adapter for PPT Master's image workflow."""

from __future__ import annotations

import os
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


ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
MODEL = "doubao-seedream-5-0-260128"
ASPECT_RATIOS = {"1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9", "21:9"}
SIZES = {"2K", "4K"}


def generate(
    prompt: str,
    aspect_ratio: str = "1:1",
    image_size: str = "2K",
    output_dir: str | None = None,
    filename: str | None = None,
    model: str | None = None,
    max_retries: int = MAX_RETRIES,
) -> str:
    """Generate one image through the standard Ark API, never Agent Plan."""
    selected_model = model or MODEL
    if selected_model != MODEL:
        raise ValueError(f"Unsupported Ark API model: {selected_model}")
    size = normalize_image_size(image_size)
    if size not in SIZES:
        raise ValueError(f"Unsupported Ark API image size: {image_size}")
    if aspect_ratio not in ASPECT_RATIOS:
        raise ValueError(f"Unsupported Ark API aspect ratio: {aspect_ratio}")
    api_key = require_api_key(
        "ARK_API_KEY", message="No Ark API image key found. Set ARK_API_KEY."
    )
    payload = {
        "model": selected_model,
        "prompt": f"{prompt}\nGenerate an image with a {aspect_ratio} aspect ratio.",
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
                raise http_error(response, "Ark API image generation")
            data = response.json()
            items = data.get("data") or []
            image_url = items[0].get("url") if items else None
            if not image_url:
                raise RuntimeError(f"Ark API response missing image URL: {data}")
            path = resolve_output_path(prompt, output_dir, filename, ".jpeg")
            return download_image(image_url, path)
        except Exception as exc:
            last_error = exc
            if is_permanent_error(exc):
                raise
            if attempt >= max_retries:
                break
            time.sleep(retry_delay(attempt, rate_limited=is_rate_limit_error(exc)))
    raise RuntimeError(f"Ark API image generation failed: {last_error}") from last_error
