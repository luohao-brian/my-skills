"""Ark implementation for Hermes `video_generate`."""

from __future__ import annotations

from typing import Any, Optional

from agent.video_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    DEFAULT_RESOLUTION,
    VideoGenProvider,
    error_response,
    success_response,
    save_url_video,
)

BACKEND_MODELS = {
    "ark-agent-plan": ("doubao-seedance-2.0-fast", "doubao-seedance-2.0"),
    "ark-api": (
        "doubao-seedance-2-5-260628", "doubao-seedance-2-0-fast-260128",
        "doubao-seedance-2-0-mini-260615", "doubao-seedance-2-0-260128",
    ),
}
TERMINAL_FAILURES = {"failed", "cancelled", "expired"}


def _profile(model: str) -> tuple[int, list[str]]:
    normalized = model.lower()
    seedance_25 = "seedance-2-5" in normalized or "seedance-2.5" in normalized
    fast_or_mini = any(value in normalized for value in (
        "seedance-2-0-fast", "seedance-2.0-fast", "seedance-2-0-mini", "seedance-2.0-mini",
    ))
    return (30 if seedance_25 else 15), (["480p", "720p"] if seedance_25 or fast_or_mini else ["480p", "720p", "1080p", "4k"])


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

    def capabilities(self) -> dict[str, Any]:
        return {
            "modalities": ["text", "image"],
            "aspect_ratios": ["16:9", "9:16", "1:1", "4:3", "3:4", "21:9"],
            "resolutions": ["480p", "720p", "1080p", "4k"],
            "max_duration": 30,
            "min_duration": 4,
            "supports_audio": True,
            "supports_negative_prompt": False,
            "max_reference_images": 1,
        }

    def list_models(self) -> list[dict[str, Any]]:
        from ..common.config import section_backend
        return [{"id": model, "display": model, "modalities": ["text", "image"]} for model in BACKEND_MODELS[section_backend("video_generate")]]

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
        timeout = max(timeout_seconds("video_generate", 300), 60)
        poll_interval = float(cfg.get("poll_interval_seconds") or 5)
        dur = int(duration if duration is not None else 5)
        max_duration, allowed_resolutions = _profile(selected_model)
        if selected_model not in BACKEND_MODELS[backend]:
            return error_response(error=f"model {selected_model} is not supported by backend {backend}", error_type="invalid_model", provider=self.name, model=selected_model, prompt=prompt, aspect_ratio=aspect_ratio)
        if dur != -1 and not 4 <= dur <= max_duration:
            return error_response(error=f"model {selected_model} supports 4-{max_duration} seconds or -1", error_type="invalid_duration", provider=self.name, model=selected_model, prompt=prompt, aspect_ratio=aspect_ratio)
        if resolution not in allowed_resolutions:
            return error_response(error=f"model {selected_model} supports {allowed_resolutions}", error_type="invalid_resolution", provider=self.name, model=selected_model, prompt=prompt, aspect_ratio=aspect_ratio)
        prompt_parts = [prompt.strip()]
        if backend == "ark-agent-plan":
            prompt_parts.extend([f"--dur {dur}", f"--ratio {aspect_ratio}", f"--rs {resolution}"])
        full_prompt = " ".join(part for part in prompt_parts if part)

        try:
            client = Ark(base_url=ark_base_url("video_generate"), api_key=require_api_key("video_generate"))
            content: list[dict[str, Any]] = [{"type": "text", "text": full_prompt}]
            if image_url:
                resolved_image = image_url
                if not image_url.startswith(("http://", "https://", "data:")):
                    from agent.file_safety import raise_if_read_blocked
                    from ..common.client import file_to_data_url
                    raise_if_read_blocked(image_url)
                    resolved_image = file_to_data_url(image_url, "image/png")
                content.append({"type": "image_url", "image_url": {"url": resolved_image}})
            extra_body = {"generate_audio": bool(audio) if audio is not None else False}
            if backend == "ark-api":
                extra_body.update({"duration": dur, "ratio": aspect_ratio, "resolution": resolution, "watermark": False})
            create_result = client.content_generation.tasks.create(
                model=selected_model,
                content=content,
                extra_body=extra_body,
            )
            task_id = create_result.id
            deadline = time.time() + timeout
            last_status = getattr(create_result, "status", "created")
            while time.time() < deadline:
                task = client.content_generation.tasks.get(task_id=task_id)
                last_status = task.status
                if task.status == "succeeded":
                    video_url = task.content.video_url
                    if not video_url:
                        return error_response(error=f"task_id={task_id}; succeeded without video_url", error_type="unexpected_response", provider=self.name, model=selected_model, prompt=prompt, aspect_ratio=aspect_ratio)
                    local_path = save_url_video(video_url, prefix="ark_seedance", timeout=timeout)
                    return success_response(
                        video=str(local_path),
                        model=selected_model,
                        prompt=prompt,
                        modality="image" if image_url else "text",
                        aspect_ratio=aspect_ratio,
                        duration=dur,
                        provider=self.name,
                        extra={"task_id": task_id, "status": task.status, "source_url": video_url, "backend": backend, "resolution": resolution},
                    )
                if str(task.status).lower() in TERMINAL_FAILURES:
                    return error_response(
                        error=f"task_id={task_id}; error={task.error}",
                        error_type="task_failed",
                        provider=self.name,
                        model=selected_model,
                        prompt=prompt,
                        aspect_ratio=aspect_ratio,
                    )
                time.sleep(poll_interval)
            return error_response(
                error=f"task timed out; task_id={task_id}; last_status={last_status}",
                error_type="timeout",
                provider=self.name,
                model=selected_model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )
        except Exception as exc:
            return error_response(
                error=str(exc),
                error_type="provider_exception",
                provider=self.name,
                model=selected_model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )
