"""Ark implementation for Hermes `video_generate`."""

from __future__ import annotations

from typing import Any, Optional

from agent.video_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    DEFAULT_RESOLUTION,
    VideoGenProvider,
    error_response,
    save_url_video,
    success_response,
)

BACKEND_MODELS = {
    "ark-agent-plan": ("doubao-seedance-2.0-fast", "doubao-seedance-2.0"),
    "ark-api": (
        "doubao-seedance-2-5-260628",
        "doubao-seedance-2-0-fast-260128",
        "doubao-seedance-2-0-mini-260615",
        "doubao-seedance-2-0-260128",
    ),
}
MODEL_PROFILES: dict[str, dict[str, Any]] = {
    "doubao-seedance-2.0-fast": {"max_duration": 15, "resolutions": ["480p", "720p"], "max_reference_images": 9},
    "doubao-seedance-2.0": {"max_duration": 15, "resolutions": ["480p", "720p", "1080p", "4k"], "max_reference_images": 9},
    "doubao-seedance-2-5-260628": {"max_duration": 30, "resolutions": ["480p", "720p", "1080p"], "max_reference_images": 30},
    "doubao-seedance-2-0-fast-260128": {"max_duration": 15, "resolutions": ["480p", "720p"], "max_reference_images": 9},
    "doubao-seedance-2-0-mini-260615": {"max_duration": 15, "resolutions": ["480p", "720p"], "max_reference_images": 9},
    "doubao-seedance-2-0-260128": {"max_duration": 15, "resolutions": ["480p", "720p", "1080p", "4k"], "max_reference_images": 9},
}
ASPECT_RATIOS = ["16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "adaptive"]
TERMINAL_FAILURES = {"failed", "cancelled", "expired"}


def _profile(model: str) -> dict[str, Any]:
    try:
        return MODEL_PROFILES[model]
    except KeyError as exc:
        raise ValueError(f"unsupported Seedance model: {model}") from exc


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool, list, dict)):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return str(value)


class ArkVideoGenerateProvider(VideoGenProvider):
    @property
    def name(self) -> str:
        return "ark"

    @property
    def display_name(self) -> str:
        return "Volcengine Ark"

    def is_available(self) -> bool:
        from ..common.config import section_api_key

        if not section_api_key("video_generate"):
            return False
        try:
            import volcenginesdkarkruntime  # noqa: F401
        except Exception:
            return False
        return True

    def _configured_model(self) -> str:
        from ..common.config import section, section_backend

        backend = section_backend("video_generate")
        default = "doubao-seedance-2.0-fast" if backend == "ark-agent-plan" else "doubao-seedance-2-5-260628"
        return str(section("video_generate").get("model") or default)

    def capabilities(self) -> dict[str, Any]:
        try:
            model = self._configured_model()
            profile = _profile(model)
        except Exception:
            model = "doubao-seedance-2.0-fast"
            profile = _profile(model)
        return {
            "modalities": ["text", "image"],
            "aspect_ratios": ASPECT_RATIOS,
            "resolutions": list(profile["resolutions"]),
            "max_duration": profile["max_duration"],
            "min_duration": 4,
            "supports_audio": True,
            "supports_negative_prompt": False,
            "max_reference_images": profile["max_reference_images"],
        }

    def list_models(self) -> list[dict[str, Any]]:
        from ..common.config import section_backend

        models = []
        for model in BACKEND_MODELS[section_backend("video_generate")]:
            profile = _profile(model)
            models.append({
                "id": model,
                "display": model,
                "modalities": ["text", "image"],
                "min_duration": 4,
                "max_duration": profile["max_duration"],
                "resolutions": list(profile["resolutions"]),
                "max_reference_images": profile["max_reference_images"],
            })
        return models

    def generate(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        image_url: Optional[str] = None,
        reference_image_urls: Optional[list[str]] = None,
        duration: Optional[int] = None,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        resolution: str = DEFAULT_RESOLUTION,
        negative_prompt: Optional[str] = None,
        audio: Optional[bool] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        import time

        from volcenginesdkarkruntime import Ark

        from ..common.auth import require_api_key
        from ..common.config import ark_base_url, section, section_backend, timeout_seconds

        cfg = section("video_generate")
        backend = section_backend("video_generate")
        default_model = "doubao-seedance-2.0-fast" if backend == "ark-agent-plan" else "doubao-seedance-2-5-260628"
        selected_model = model or str(cfg.get("model") or default_model)
        refs = list(reference_image_urls or [])
        timeout = max(timeout_seconds("video_generate", 300), 60)
        poll_interval = float(cfg.get("poll_interval_seconds") or 5)
        dur = int(duration if duration is not None else 5)
        effective_ratio = "adaptive" if image_url else aspect_ratio
        task_id: str | None = None
        last_status = "not_submitted"

        if selected_model not in BACKEND_MODELS.get(backend, ()):
            return error_response(error=f"model {selected_model} is not supported by backend {backend}", error_type="invalid_model", provider=self.name, model=selected_model, prompt=prompt, aspect_ratio=effective_ratio)
        profile = _profile(selected_model)
        if dur != -1 and not 4 <= dur <= int(profile["max_duration"]):
            return error_response(error=f"model {selected_model} supports 4-{profile['max_duration']} seconds or -1", error_type="invalid_duration", provider=self.name, model=selected_model, prompt=prompt, aspect_ratio=effective_ratio)
        if resolution not in profile["resolutions"]:
            return error_response(error=f"model {selected_model} supports {profile['resolutions']}", error_type="invalid_resolution", provider=self.name, model=selected_model, prompt=prompt, aspect_ratio=effective_ratio)
        if effective_ratio not in ASPECT_RATIOS:
            return error_response(error=f"unsupported aspect ratio {effective_ratio}", error_type="invalid_aspect_ratio", provider=self.name, model=selected_model, prompt=prompt, aspect_ratio=effective_ratio)
        if image_url and refs:
            return error_response(error="image_url and reference_image_urls are mutually exclusive for Ark Seedance", error_type="invalid_reference_mode", provider=self.name, model=selected_model, prompt=prompt, aspect_ratio=effective_ratio)
        if len(refs) > int(profile["max_reference_images"]):
            return error_response(error=f"model {selected_model} accepts at most {profile['max_reference_images']} reference images", error_type="too_many_references", provider=self.name, model=selected_model, prompt=prompt, aspect_ratio=effective_ratio)
        if seed is not None:
            return error_response(error="Seedance 2.x does not support seed", error_type="unsupported_parameter", provider=self.name, model=selected_model, prompt=prompt, aspect_ratio=effective_ratio)

        def resolve_image(source: str) -> str:
            if source.startswith(("http://", "https://", "data:", "asset://")):
                return source
            from agent.file_safety import raise_if_read_blocked
            from ..common.client import file_to_data_url

            raise_if_read_blocked(source)
            return file_to_data_url(source, "image/png")

        try:
            client = Ark(base_url=ark_base_url("video_generate"), api_key=require_api_key("video_generate"))
            content: list[dict[str, Any]] = [{"type": "text", "text": prompt.strip()}]
            if image_url:
                content.append({"type": "image_url", "image_url": {"url": resolve_image(image_url)}, "role": "first_frame"})
            for reference in refs:
                content.append({"type": "image_url", "image_url": {"url": resolve_image(reference)}, "role": "reference_image"})
            create_result = client.content_generation.tasks.create(
                model=selected_model,
                content=content,
                duration=dur,
                ratio=effective_ratio,
                resolution=resolution,
                generate_audio=bool(audio) if audio is not None else False,
                watermark=False,
            )
            task_id = str(create_result.id)
            last_status = str(getattr(create_result, "status", "created"))
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                task = client.content_generation.tasks.get(task_id=task_id)
                last_status = str(task.status).lower()
                if last_status == "succeeded":
                    video_url = getattr(task.content, "video_url", None)
                    if not video_url:
                        return error_response(error=f"task_id={task_id}; succeeded without video_url", error_type="unexpected_response", provider=self.name, model=selected_model, prompt=prompt, aspect_ratio=effective_ratio)
                    warnings: list[str] = []
                    try:
                        local_path = str(save_url_video(video_url, prefix="ark_seedance", timeout=timeout))
                    except Exception as exc:
                        local_path = video_url
                        warnings.append(f"video generated but local download failed: {exc}")
                    actual_ratio = getattr(task, "ratio", None) or ""
                    actual_duration = getattr(task, "duration", None)
                    return success_response(
                        video=local_path,
                        model=getattr(task, "model", None) or selected_model,
                        prompt=prompt,
                        modality="image" if image_url or refs else "text",
                        aspect_ratio=actual_ratio,
                        duration=actual_duration or 0,
                        provider=self.name,
                        extra={
                            "task_id": task_id,
                            "status": last_status,
                            "source_url": video_url,
                            "last_frame_url": getattr(task.content, "last_frame_url", None),
                            "backend": backend,
                            "resolution": getattr(task, "resolution", None),
                            "generate_audio": getattr(task, "generate_audio", None),
                            "usage": _jsonable(getattr(task, "usage", None)),
                            "request_id": getattr(task, "request_id", None),
                            "warnings": warnings,
                        },
                    )
                if last_status in TERMINAL_FAILURES:
                    return error_response(error=f"task_id={task_id}; status={last_status}; error={_jsonable(getattr(task, 'error', None))}", error_type="task_failed", provider=self.name, model=selected_model, prompt=prompt, aspect_ratio=effective_ratio)
                time.sleep(poll_interval)
            return error_response(error=f"task timed out; task_id={task_id}; last_status={last_status}", error_type="timeout", provider=self.name, model=selected_model, prompt=prompt, aspect_ratio=effective_ratio)
        except Exception as exc:
            task_context = f"task_id={task_id}; " if task_id else ""
            return error_response(error=f"{task_context}{exc}", error_type="provider_exception", provider=self.name, model=selected_model, prompt=prompt, aspect_ratio=effective_ratio)
