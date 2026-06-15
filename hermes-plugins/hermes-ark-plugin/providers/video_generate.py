"""Ark implementation for Hermes `video_generate`."""

from __future__ import annotations

from typing import Any, Optional

from agent.video_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    DEFAULT_RESOLUTION,
    VideoGenProvider,
    error_response,
    success_response,
)


class ArkVideoGenerateProvider(VideoGenProvider):
    @property
    def name(self) -> str:
        return "ark"

    @property
    def display_name(self) -> str:
        return "Volcengine Ark"

    def is_available(self) -> bool:
        from ..common.config import api_key

        if not api_key():
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
            "resolutions": ["480p", "720p", "1080p"],
            "max_duration": 12,
            "min_duration": 5,
            "supports_audio": True,
            "supports_negative_prompt": False,
            "max_reference_images": 1,
        }

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
        from ..common.config import ark_base_url, section, timeout_seconds

        cfg = section("video_generate")
        selected_model = model or str(cfg.get("model") or "doubao-seedance-2.0-fast")
        timeout = max(timeout_seconds("video_generate", 300), 60)
        poll_interval = float(cfg.get("poll_interval_seconds") or 5)
        dur = max(5, min(int(duration or 5), 12))
        prompt_parts = [prompt.strip()]
        if resolution:
            prompt_parts.append(f"--rs {resolution}")
        if aspect_ratio:
            prompt_parts.append(f"--rt {aspect_ratio}")
        prompt_parts.extend([f"--fps 24", f"--dur {dur}", "--wm false"])
        full_prompt = " ".join(part for part in prompt_parts if part)

        try:
            client = Ark(base_url=ark_base_url(), api_key=require_api_key())
            content: list[dict[str, Any]] = [{"type": "text", "text": full_prompt}]
            if image_url:
                content.append({"type": "image_url", "image_url": {"url": image_url}})
            create_result = client.content_generation.tasks.create(
                model=selected_model,
                content=content,
                extra_body={"generate_audio": bool(audio) if audio is not None else False},
            )
            task_id = create_result.id
            deadline = time.time() + timeout
            last_status = getattr(create_result, "status", "created")
            while time.time() < deadline:
                task = client.content_generation.tasks.get(task_id=task_id)
                last_status = task.status
                if task.status == "succeeded":
                    video_url = task.content.video_url
                    return success_response(
                        video=video_url,
                        model=selected_model,
                        prompt=prompt,
                        modality="image" if image_url else "text",
                        aspect_ratio=aspect_ratio,
                        duration=dur,
                        provider=self.name,
                        extra={"task_id": task_id, "status": task.status},
                    )
                if task.status == "failed":
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
