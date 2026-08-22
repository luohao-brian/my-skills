"""Ark implementation for Hermes `image_generate`."""

from __future__ import annotations

from typing import Any, Optional

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    ImageGenProvider,
    error_response,
    save_url_image,
    success_response,
)


ASPECT_SIZES = {
    "landscape": "2848x1600",
    "square": "2048x2048",
    "portrait": "1600x2848",
    "16:9": "2848x1600",
    "1:1": "2048x2048",
    "9:16": "1600x2848",
}
PRO_MODEL = "doubao-seedream-5-0-pro-260628"
BACKEND_MODELS = {
    "ark-agent-plan": ("doubao-seedream-5.0-lite",),
    "ark-api": ("doubao-seedream-5-0-260128", PRO_MODEL),
}


def _seedream_size(aspect_ratio: str, resolution: str = "2K") -> str:
    base = ASPECT_SIZES.get(aspect_ratio, ASPECT_SIZES["landscape"])
    width, height = (int(part) for part in base.split("x", 1))
    scale = {"1K": 0.5, "1.5K": 0.75, "2K": 1.0, "3K": 1.5, "4K": 2.0}.get(resolution.upper())
    if scale is None:
        raise ValueError(f"unsupported Seedream resolution: {resolution}")
    return f"{round(width * scale)}x{round(height * scale)}"


def _reference(value: str) -> str:
    if value.startswith(("http://", "https://", "data:")):
        return value
    from agent.file_safety import raise_if_read_blocked
    from ..common.client import file_to_data_url
    raise_if_read_blocked(value)
    return file_to_data_url(value, "image/png")


class ArkImageGenerateProvider(ImageGenProvider):
    @property
    def name(self) -> str:
        return "ark"

    @property
    def display_name(self) -> str:
        return "Volcengine Ark"

    def is_available(self) -> bool:
        from ..common.config import section_api_key

        return bool(section_api_key("image_generate"))

    def list_models(self) -> list[dict[str, Any]]:
        from ..common.config import section_backend
        return [{"id": model, "display": model} for model in BACKEND_MODELS[section_backend("image_generate")]]

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        *,
        image_url: Optional[str] = None,
        reference_image_urls: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        from ..common.auth import require_api_key
        from ..common.client import post_json, response_error, save_b64_image_detected
        from ..common.config import ark_base_url, section, section_backend, timeout_seconds

        cfg = section("image_generate")
        backend = section_backend("image_generate")
        default_model = "doubao-seedream-5.0-lite" if backend == "ark-agent-plan" else "doubao-seedream-5-0-260128"
        model = str(kwargs.get("model") or cfg.get("model") or default_model)
        resolution = str(kwargs.get("resolution") or cfg.get("resolution") or "2K").upper()
        refs = [value for value in [image_url, *(reference_image_urls or [])] if value]
        try:
            if model not in BACKEND_MODELS[backend]:
                raise ValueError(f"model {model} is not supported by backend {backend}")
            if model == PRO_MODEL and resolution not in {"1K", "1.5K", "2K"}:
                raise ValueError(f"{PRO_MODEL} supports 1K, 1.5K, or 2K")
            if model != PRO_MODEL and resolution not in {"2K", "3K", "4K"}:
                raise ValueError(f"{model} supports 2K, 3K, or 4K")
            request_payload: dict[str, Any] = {
                "model": model,
                "prompt": prompt,
                "size": str(cfg.get("size") or _seedream_size(aspect_ratio, resolution)),
                "response_format": "url",
                "stream": False,
                "watermark": False,
            }
            if refs:
                encoded = [_reference(value) for value in refs[:10]]
                request_payload["image"] = encoded[0] if len(encoded) == 1 else encoded
            if model != PRO_MODEL:
                request_payload["sequential_image_generation"] = "disabled"
            response = post_json(
                ark_base_url("image_generate"),
                "images/generations",
                require_api_key("image_generate"),
                request_payload,
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
                    extra={"response_format": "b64_json", "detected_format": detected_format, "backend": backend},
                )
            if item.get("url"):
                path = save_url_image(item["url"], prefix="ark_seedream", timeout=max(timeout_seconds("image_generate", 180), 180))
                return success_response(
                    image=str(path),
                    model=model,
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                    provider=self.name,
                    extra={"source_url": item["url"], "backend": backend, "resolution": resolution},
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
