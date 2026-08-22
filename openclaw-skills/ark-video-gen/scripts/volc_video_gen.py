#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
from pathlib import Path
from typing import Any


# Official create/get task contracts:
# https://api.volcengine.com/api-docs/view?action=CreateContentsGenerationsTasks&serviceCode=ark&version=2024-01-01
# https://api.volcengine.com/api-docs/view?action=GetContentsGenerationsTask&serviceCode=ark&version=2024-01-01
# Agent Plan exposes the same task resources under the fixed /api/plan/v3 base.
DEFAULT_BACKEND = "ark-agent-plan"
BACKENDS = {
    "ark-agent-plan": {
        "base_url": "https://ark.cn-beijing.volces.com/api/plan/v3",
        "api_key_env": "ARK_AGENT_PLAN_API_KEY",
        "model": "doubao-seedance-2.0-fast",
    },
    "ark-api": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_key_env": "ARK_API_KEY",
        "model": "doubao-seedance-2-5-260628",
    },
}
BACKEND_MODELS = {
    "ark-agent-plan": (
        "doubao-seedance-2.0-fast",
        "doubao-seedance-2.0",
    ),
    "ark-api": (
        "doubao-seedance-2-5-260628",
        "doubao-seedance-2-0-fast-260128",
        "doubao-seedance-2-0-mini-260615",
        "doubao-seedance-2-0-260128",
    ),
}
DEFAULT_DURATION_SECONDS = 5
DEFAULT_ASPECT_RATIO = "16:9"
DEFAULT_RESOLUTION = "720p"
SUPPORTED_ASPECT_RATIOS = ("16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive")
SUPPORTED_RESOLUTIONS = ("480p", "720p", "1080p", "4k")
TASK_TIMEOUT_SECONDS = 300
POLL_INTERVAL_SECONDS = 5
TERMINAL_FAILURE_STATUSES = {"failed", "cancelled", "expired"}


def resolve_backend(name: str) -> tuple[dict[str, str], str]:
    profile = BACKENDS.get(name)
    if profile is None:
        raise ValueError(f"Unsupported backend: {name}")
    api_key_env = profile["api_key_env"]
    api_key = os.getenv(api_key_env, "").strip()
    if not api_key:
        raise ValueError(f"Missing {api_key_env} for backend {name}")
    return profile, api_key


def file_to_data_url(path: str) -> str:
    p = Path(path).expanduser()
    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    payload = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def build_generation_settings(
    *,
    resolution: str,
    aspect_ratio: str,
    duration: int,
    generate_audio: bool,
) -> dict[str, Any]:
    """Return provider-native top-level task fields.

    ``extra_body`` is used at the SDK call site only as a compatibility bridge:
    the Ark SDK serializes these entries at the top level of the JSON request.
    """
    return {
        "generate_audio": generate_audio,
        "resolution": resolution,
        "ratio": aspect_ratio,
        "duration": duration,
        "watermark": False,
    }


def model_profile(model: str) -> tuple[int, tuple[str, ...]]:
    normalized = model.lower()
    seedance_25 = "seedance-2-5" in normalized or "seedance-2.5" in normalized
    fast_or_mini = any(token in normalized for token in (
        "seedance-2-0-fast", "seedance-2.0-fast", "seedance-2-0-mini", "seedance-2.0-mini",
    ))
    max_duration = 30 if seedance_25 else 15
    resolutions = ("480p", "720p") if seedance_25 or fast_or_mini else SUPPORTED_RESOLUTIONS
    return max_duration, resolutions


def validate_generation(backend: str, model: str, duration: int, resolution: str) -> None:
    if model not in BACKEND_MODELS[backend]:
        raise ValueError(f"Model {model} is not supported by backend {backend}")
    max_duration, resolutions = model_profile(model)
    if duration != -1 and not 4 <= duration <= max_duration:
        raise ValueError(f"Model {model} supports 4-{max_duration} seconds or -1 smart duration")
    if resolution not in resolutions:
        raise ValueError(f"Model {model} supports resolutions: {', '.join(resolutions)}")


def build_request(
    *,
    backend: str,
    model: str,
    prompt: str,
    image_url: str | None,
    duration: int,
    aspect_ratio: str,
    resolution: str,
    generate_audio: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    validate_generation(backend, model, duration, resolution)
    text = prompt.strip()
    settings: dict[str, Any] = {"generate_audio": generate_audio}
    if backend == "ark-agent-plan":
        text += f" --dur {duration} --ratio {aspect_ratio} --rs {resolution}"
    else:
        settings.update(build_generation_settings(
            resolution=resolution,
            aspect_ratio=aspect_ratio,
            duration=duration,
            generate_audio=generate_audio,
        ))
    content: list[dict[str, Any]] = [{"type": "text", "text": text}]
    if image_url:
        content.append({"type": "image_url", "image_url": {"url": image_url}})
    return content, settings


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate video with Ark")
    parser.add_argument("prompt")
    parser.add_argument("--image", help="Optional first-frame image path, data URL, or remote URL")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION_SECONDS)
    parser.add_argument("--aspect-ratio", choices=SUPPORTED_ASPECT_RATIOS, default=DEFAULT_ASPECT_RATIO)
    parser.add_argument("--resolution", choices=SUPPORTED_RESOLUTIONS, default=DEFAULT_RESOLUTION)
    parser.add_argument("--audio", action="store_true")
    parser.add_argument("--model", help="Backend-compatible model override")
    parser.add_argument("--backend", choices=BACKENDS, default=DEFAULT_BACKEND)
    args = parser.parse_args()

    try:
        profile, api_key = resolve_backend(args.backend)
    except ValueError as exc:
        print(json.dumps({"success": False, "backend": args.backend, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    duration = args.duration
    model = args.model or profile["model"]

    task_id: str | None = None
    last_status = "not_submitted"
    try:
        from volcenginesdkarkruntime import Ark
        client = Ark(base_url=profile["base_url"], api_key=api_key)
        image_url = None
        if args.image:
            image_url = args.image
            if not (image_url.startswith("http://") or image_url.startswith("https://") or image_url.startswith("data:")):
                image_url = file_to_data_url(image_url)
        content, generation_settings = build_request(
            backend=args.backend,
            model=model,
            prompt=args.prompt,
            image_url=image_url,
            duration=duration,
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
            generate_audio=bool(args.audio),
        )

        created = client.content_generation.tasks.create(
            model=model,
            content=content,
            extra_body=generation_settings,
        )
        task_id = created.id
        last_status = getattr(created, "status", "created")
        deadline = time.time() + TASK_TIMEOUT_SECONDS
        while time.time() < deadline:
            task = client.content_generation.tasks.get(task_id=task_id)
            last_status = str(task.status)
            if last_status == "succeeded":
                video_url = task.content.video_url
                if not video_url:
                    raise RuntimeError(f"task_id={task_id}; succeeded without video_url")
                actual_generate_audio = getattr(task, "generate_audio", None)
                print(json.dumps({
                    "success": True,
                    "type": "video",
                    "backend": args.backend,
                    "task_id": task_id,
                    "status": last_status,
                    "video_url": video_url,
                    "model": model,
                    "prompt": args.prompt,
                    "duration": getattr(task, "duration", None) or duration,
                    "aspect_ratio": getattr(task, "ratio", None) or args.aspect_ratio,
                    "resolution": getattr(task, "resolution", None) or args.resolution,
                    "generate_audio": actual_generate_audio if actual_generate_audio is not None else bool(args.audio),
                    "used_reference_image": bool(args.image),
                }, ensure_ascii=False, indent=2))
                return 0
            if last_status in TERMINAL_FAILURE_STATUSES:
                raise RuntimeError(
                    f"task_id={task_id}; status={last_status}; error={getattr(task, 'error', None)}"
                )
            time.sleep(POLL_INTERVAL_SECONDS)
        print(json.dumps({
            "success": False,
            "error": "task timed out",
            "task_id": task_id,
            "status": last_status,
            "backend": args.backend,
            "model": model,
        }, ensure_ascii=False), file=sys.stderr)
        return 1
    except Exception as exc:
        print(json.dumps({
            "success": False,
            "error": str(exc),
            "task_id": task_id,
            "status": last_status,
            "backend": args.backend,
            "model": model,
        }, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
