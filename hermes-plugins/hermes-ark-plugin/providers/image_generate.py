"""Ark implementation for Hermes `image_generate`."""

from __future__ import annotations

from typing import Any

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    ImageGenProvider,
    error_response,
    save_url_image,
    success_response,
)


def _seedream_size(aspect_ratio: str) -> str:
    # Agent Plan demo uses "2K"; keep that default because Seedream accepts it
    # across the common Hermes aspect ratio labels.
    return "2K"


class ArkImageGenerateProvider(ImageGenProvider):
    @property
    def name(self) -> str:
        return "ark"

    @property
    def display_name(self) -> str:
        return "Volcengine Ark"

    def is_available(self) -> bool:
        from ..common.config import api_key

        return bool(api_key())

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        **kwargs: Any,
    ) -> dict[str, Any]:
        from ..common.auth import require_api_key
        from ..common.client import post_json, response_error, save_b64_image_detected
        from ..common.config import ark_base_url, section, timeout_seconds

        cfg = section("image_generate")
        model = str(kwargs.get("model") or cfg.get("model") or "doubao-seedream-5.0-lite")
        try:
            response = post_json(
                ark_base_url(),
                "images/generations",
                require_api_key(),
                {
                    "model": model,
                    "prompt": prompt,
                    "size": str(cfg.get("size") or _seedream_size(aspect_ratio)),
                    "response_format": "b64_json",
                    "stream": False,
                    "watermark": False,
                },
                timeout=max(timeout_seconds("image_generate", 180), 180),
            )
            if response.status_code >= 400:
                return error_response(
                    error=response_error(response),
                    error_type="http_error",
                    provider=self.name,
                    model=model,
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                )
            payload = response.json()
            item = (payload.get("data") or [{}])[0]
            if item.get("b64_json"):
                path, detected_format = save_b64_image_detected(item["b64_json"], prefix="ark_seedream")
                return success_response(
                    image=str(path),
                    model=model,
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                    provider=self.name,
                    extra={"response_format": "b64_json", "detected_format": detected_format},
                )
            if item.get("url"):
                path = save_url_image(item["url"], prefix="ark_seedream", timeout=max(timeout_seconds("image_generate", 180), 180))
                return success_response(
                    image=str(path),
                    model=model,
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                    provider=self.name,
                    extra={"source_url": item["url"]},
                )
            return error_response(
                error=f"unexpected image response: {payload}",
                error_type="unexpected_response",
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )
        except Exception as exc:
            return error_response(
                error=str(exc),
                error_type="provider_exception",
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )
