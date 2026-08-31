#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any


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
MODEL_PROFILES: dict[str, dict[str, Any]] = {
    "doubao-seedance-2.0-fast": {
        "max_duration": 15,
        "resolutions": ("480p", "720p"),
        "max_reference_images": 9,
        "max_reference_videos": 3,
        "max_reference_audios": 3,
        "output_formats": (),
    },
    "doubao-seedance-2.0": {
        "max_duration": 15,
        "resolutions": ("480p", "720p", "1080p", "4k"),
        "max_reference_images": 9,
        "max_reference_videos": 3,
        "max_reference_audios": 3,
        "output_formats": (),
    },
    "doubao-seedance-2-5-260628": {
        "max_duration": 30,
        "resolutions": ("480p", "720p", "1080p"),
        "max_reference_images": 30,
        "max_reference_videos": 10,
        "max_reference_audios": 10,
        "max_reference_total": 50,
        "output_formats": ("mp4", "mov"),
        "task_types": ("auto", "reference", "edit", "extend"),
    },
    "doubao-seedance-2-0-fast-260128": {
        "max_duration": 15,
        "resolutions": ("480p", "720p"),
        "max_reference_images": 9,
        "max_reference_videos": 3,
        "max_reference_audios": 3,
        "output_formats": (),
    },
    "doubao-seedance-2-0-mini-260615": {
        "max_duration": 15,
        "resolutions": ("480p", "720p"),
        "max_reference_images": 9,
        "max_reference_videos": 3,
        "max_reference_audios": 3,
        "output_formats": (),
    },
    "doubao-seedance-2-0-260128": {
        "max_duration": 15,
        "resolutions": ("480p", "720p", "1080p", "4k"),
        "max_reference_images": 9,
        "max_reference_videos": 3,
        "max_reference_audios": 3,
        "output_formats": (),
    },
}
DEFAULT_DURATION_SECONDS = 5
DEFAULT_ASPECT_RATIO = "16:9"
DEFAULT_RESOLUTION = "720p"
SUPPORTED_ASPECT_RATIOS = ("16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive")
SUPPORTED_RESOLUTIONS = ("480p", "720p", "1080p", "4k")
TERMINAL_FAILURE_STATUSES = {"failed", "cancelled", "expired"}
DEFAULT_TIMEOUT_SECONDS = 600
DEFAULT_POLL_INTERVAL_SECONDS = 5.0
MAX_DOWNLOAD_BYTES = 500 * 1024 * 1024
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif", ".heic", ".heif"}
AUDIO_EXTENSIONS = {".wav", ".mp3"}


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def resolve_backend(name: str) -> tuple[dict[str, str], str]:
    profile = BACKENDS.get(name)
    if profile is None:
        raise ValueError(f"Unsupported backend: {name}")
    api_key_env = profile["api_key_env"]
    api_key = os.getenv(api_key_env, "").strip()
    if not api_key:
        raise ValueError(f"Missing {api_key_env} for backend {name}")
    return profile, api_key


def _is_passthrough_source(value: str) -> bool:
    return value.startswith(("http://", "https://", "data:", "asset://"))


def file_to_data_url(path: str, *, media_kind: str = "image") -> str:
    source = Path(path).expanduser()
    if not source.is_file():
        raise ValueError(f"{media_kind} file does not exist: {path}")
    extension = source.suffix.lower()
    if media_kind == "image":
        allowed_extensions = IMAGE_EXTENSIONS
        max_bytes = 30 * 1024 * 1024
    elif media_kind == "audio":
        allowed_extensions = AUDIO_EXTENSIONS
        max_bytes = 15 * 1024 * 1024
    else:
        raise ValueError(f"Unsupported data URL media kind: {media_kind}")
    if extension not in allowed_extensions:
        raise ValueError(f"Unsupported {media_kind} format: {extension or 'unknown'}")
    size = source.stat().st_size
    if size >= max_bytes:
        raise ValueError(f"{media_kind} file must be smaller than {max_bytes // (1024 * 1024)} MB")
    mime = mimetypes.guess_type(source.name)[0]
    if not mime:
        mime = "image/jpeg" if media_kind == "image" else "audio/mpeg"
    payload = base64.b64encode(source.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def normalize_media_input(value: str, media_kind: str) -> str:
    source = value.strip()
    if not source:
        raise ValueError(f"Empty {media_kind} input")
    if source.startswith("file-"):
        raise ValueError(
            f"Ark video generation does not accept Files API file_id for reference {media_kind}; "
            "use an HTTP(S) URL, a documented data URL, or asset://"
        )
    if source.startswith("data:"):
        expected = f"data:{media_kind}/"
        if not source.startswith(expected):
            raise ValueError(f"Expected a {media_kind} data URL")
        return source
    if source.startswith(("http://", "https://", "asset://")):
        return source
    if media_kind == "video":
        raise ValueError(
            "Local reference videos are not accepted directly; provide a provider-readable HTTP(S) URL or asset:// ID. "
            "Ark Files API file_id is valid for video understanding but is not a Seedance reference URL"
        )
    return file_to_data_url(source, media_kind=media_kind)


def model_profile(model: str) -> dict[str, Any]:
    try:
        return MODEL_PROFILES[model]
    except KeyError as exc:
        raise ValueError(f"Unsupported Seedance model: {model}") from exc


def build_generation_settings(
    *,
    resolution: str,
    aspect_ratio: str,
    duration: int,
    generate_audio: bool,
    output_format: str | None = None,
    return_last_frame: bool = False,
    task_type: str | None = None,
) -> dict[str, Any]:
    settings: dict[str, Any] = {
        "generate_audio": generate_audio,
        "resolution": resolution,
        "ratio": aspect_ratio,
        "duration": duration,
        "watermark": False,
    }
    if output_format:
        settings["output_format"] = output_format
    if return_last_frame:
        settings["return_last_frame"] = True
    if task_type:
        settings["omni_reference_task_type"] = task_type
    return settings


def validate_generation(
    backend: str,
    model: str,
    duration: int,
    resolution: str,
    *,
    aspect_ratio: str = DEFAULT_ASPECT_RATIO,
    first_frame: str | None = None,
    last_frame: str | None = None,
    reference_images: list[str] | None = None,
    reference_videos: list[str] | None = None,
    reference_audios: list[str] | None = None,
    output_format: str | None = None,
    task_type: str | None = None,
) -> None:
    if backend not in BACKEND_MODELS:
        raise ValueError(f"Unsupported backend: {backend}")
    if model not in BACKEND_MODELS[backend]:
        raise ValueError(f"Model {model} is not supported by backend {backend}")
    profile = model_profile(model)
    max_duration = int(profile["max_duration"])
    if duration != -1 and not 4 <= duration <= max_duration:
        raise ValueError(f"Model {model} supports 4-{max_duration} seconds or -1 smart duration")
    resolutions = tuple(profile["resolutions"])
    if resolution not in resolutions:
        raise ValueError(f"Model {model} supports resolutions: {', '.join(resolutions)}")
    if aspect_ratio not in SUPPORTED_ASPECT_RATIOS:
        raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")

    images = reference_images or []
    videos = reference_videos or []
    audios = reference_audios or []
    if last_frame and not first_frame:
        raise ValueError("--last-frame requires --first-frame")
    if first_frame and (images or videos or audios):
        raise ValueError("First/last-frame mode cannot be combined with reference-image, reference-video, or reference-audio")
    if (first_frame or last_frame) and aspect_ratio != "adaptive":
        raise ValueError("First/last-frame generation requires --aspect-ratio adaptive")
    if len(images) > int(profile["max_reference_images"]):
        raise ValueError(f"Model {model} accepts at most {profile['max_reference_images']} reference images")
    if len(videos) > int(profile["max_reference_videos"]):
        raise ValueError(f"Model {model} accepts at most {profile['max_reference_videos']} reference videos")
    if len(audios) > int(profile["max_reference_audios"]):
        raise ValueError(f"Model {model} accepts at most {profile['max_reference_audios']} reference audios")
    max_total = profile.get("max_reference_total")
    if max_total is not None and len(images) + len(videos) + len(audios) > int(max_total):
        raise ValueError(f"Model {model} accepts at most {max_total} total reference assets")
    if not profile.get("task_types") and audios and not (images or videos):
        raise ValueError("Seedance 2.0 reference audio must be combined with a reference image or video")

    allowed_formats = tuple(profile.get("output_formats") or ())
    if output_format and output_format not in allowed_formats:
        supported = ", ".join(allowed_formats) if allowed_formats else "no configurable output format"
        raise ValueError(f"Model {model} supports output formats: {supported}")
    task_types = tuple(profile.get("task_types") or ())
    if task_type and task_type not in task_types:
        raise ValueError(f"Model {model} does not support omni reference task type {task_type}")
    if task_type == "reference" and not (images or videos or audios):
        raise ValueError("Reference task requires at least one reference asset")
    if task_type == "edit":
        if not videos:
            raise ValueError("Edit task requires at least one reference video")
        if aspect_ratio != "adaptive" or duration != -1:
            raise ValueError("Edit task requires --aspect-ratio adaptive and --duration -1")
    if task_type == "extend":
        if not videos:
            raise ValueError("Extend task requires at least one reference video")
        if aspect_ratio != "adaptive":
            raise ValueError("Extend task requires --aspect-ratio adaptive")


def build_content(
    prompt: str,
    *,
    first_frame: str | None = None,
    last_frame: str | None = None,
    reference_images: list[str] | None = None,
    reference_videos: list[str] | None = None,
    reference_audios: list[str] | None = None,
) -> list[dict[str, Any]]:
    text = prompt.strip()
    if not text:
        raise ValueError("Prompt must not be empty")
    content: list[dict[str, Any]] = [{"type": "text", "text": text}]
    if first_frame:
        content.append({"type": "image_url", "image_url": {"url": first_frame}, "role": "first_frame"})
    if last_frame:
        content.append({"type": "image_url", "image_url": {"url": last_frame}, "role": "last_frame"})
    for source in reference_images or []:
        content.append({"type": "image_url", "image_url": {"url": source}, "role": "reference_image"})
    for source in reference_videos or []:
        content.append({"type": "video_url", "video_url": {"url": source}, "role": "reference_video"})
    for source in reference_audios or []:
        content.append({"type": "audio_url", "audio_url": {"url": source}, "role": "reference_audio"})
    return content


def build_request(
    *,
    backend: str,
    model: str,
    prompt: str,
    duration: int,
    aspect_ratio: str,
    resolution: str,
    generate_audio: bool,
    image_url: str | None = None,
    first_frame: str | None = None,
    last_frame: str | None = None,
    reference_images: list[str] | None = None,
    reference_videos: list[str] | None = None,
    reference_audios: list[str] | None = None,
    output_format: str | None = None,
    return_last_frame: bool = False,
    task_type: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if image_url and first_frame:
        raise ValueError("image_url and first_frame are aliases and cannot both be set")
    resolved_first_frame = first_frame or image_url
    validate_generation(
        backend,
        model,
        duration,
        resolution,
        aspect_ratio=aspect_ratio,
        first_frame=resolved_first_frame,
        last_frame=last_frame,
        reference_images=reference_images,
        reference_videos=reference_videos,
        reference_audios=reference_audios,
        output_format=output_format,
        task_type=task_type,
    )
    return (
        build_content(
            prompt,
            first_frame=resolved_first_frame,
            last_frame=last_frame,
            reference_images=reference_images,
            reference_videos=reference_videos,
            reference_audios=reference_audios,
        ),
        build_generation_settings(
            resolution=resolution,
            aspect_ratio=aspect_ratio,
            duration=duration,
            generate_audio=generate_audio,
            output_format=output_format,
            return_last_frame=return_last_frame,
            task_type=task_type,
        ),
    )


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool, list, dict)):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return str(value)


def poll_task(client: Any, task_id: str, *, timeout: float, poll_interval: float, initial_status: str = "created") -> tuple[Any | None, str]:
    deadline = time.monotonic() + timeout
    last_status = initial_status
    while time.monotonic() < deadline:
        task = client.content_generation.tasks.get(task_id=task_id)
        last_status = str(getattr(task, "status", "unknown")).lower()
        if last_status == "succeeded" or last_status in TERMINAL_FAILURE_STATUSES:
            return task, last_status
        time.sleep(poll_interval)
    return None, last_status


def default_output_path(task_id: str, output_format: str | None, video_url: str) -> Path:
    extension = (output_format or "").lower()
    if extension not in {"mp4", "mov"}:
        clean_url = video_url.split("?", 1)[0].lower()
        extension = "mov" if clean_url.endswith(".mov") else "mp4"
    return Path.home() / "Documents" / "hermes-workspace" / "videos" / f"{task_id}.{extension}"


def download_video(url: str, output: Path, *, timeout: float) -> Path:
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "ark-video-gen/1.0"})
    written = 0
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response, output.open("wb") as target:
            while True:
                chunk = response.read(256 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > MAX_DOWNLOAD_BYTES:
                    raise ValueError("Generated video exceeds the 500 MB download limit")
                target.write(chunk)
        if written == 0:
            raise ValueError("Generated video download was empty")
    except Exception:
        try:
            output.unlink()
        except OSError:
            pass
        raise
    return output


def task_result(
    task: Any,
    *,
    backend: str,
    task_id: str,
    prompt: str,
    requested_model: str | None,
    output_path: str | None,
    download_timeout: float,
) -> dict[str, Any]:
    status = str(getattr(task, "status", "unknown")).lower()
    model = getattr(task, "model", None) or requested_model
    if status in TERMINAL_FAILURE_STATUSES:
        return {
            "success": False,
            "backend": backend,
            "task_id": task_id,
            "status": status,
            "model": model,
            "error": _jsonable(getattr(task, "error", None)),
            "request_id": getattr(task, "request_id", None),
        }
    content = getattr(task, "content", None)
    video_url = getattr(content, "video_url", None) if content is not None else None
    if not video_url:
        return {
            "success": False,
            "backend": backend,
            "task_id": task_id,
            "status": status,
            "model": model,
            "error": "Task succeeded without video_url",
            "request_id": getattr(task, "request_id", None),
        }
    last_frame_url = getattr(content, "last_frame_url", None)
    warnings: list[str] = []
    local_path: str | None = None
    target = Path(output_path) if output_path else default_output_path(
        task_id,
        getattr(task, "output_format", None),
        video_url,
    )
    try:
        local_path = str(download_video(video_url, target, timeout=download_timeout))
    except Exception as exc:
        warnings.append(f"Video generated but local download failed: {exc}")
    return {
        "success": True,
        "type": "video",
        "backend": backend,
        "task_id": task_id,
        "status": status,
        "video_url": video_url,
        "local_path": local_path,
        "last_frame_url": last_frame_url,
        "model": model,
        "prompt": prompt,
        "duration": getattr(task, "duration", None),
        "aspect_ratio": getattr(task, "ratio", None),
        "resolution": getattr(task, "resolution", None),
        "generate_audio": getattr(task, "generate_audio", None),
        "usage": _jsonable(getattr(task, "usage", None)),
        "request_id": getattr(task, "request_id", None),
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or resume Seedance video tasks with Ark")
    parser.add_argument("prompt", nargs="?", default="", help="Final compiled Seedance prompt")
    parser.add_argument("--image", help="Deprecated alias for --first-frame")
    parser.add_argument("--first-frame", help="First-frame image path, URL, data URL, or asset ID")
    parser.add_argument("--last-frame", help="Last-frame image path, URL, data URL, or asset ID")
    parser.add_argument("--reference-image", action="append", default=[], help="Reference image; repeat in prompt order")
    parser.add_argument("--reference-video", action="append", default=[], help="Reference video HTTP(S) URL or asset ID; repeat in prompt order")
    parser.add_argument("--reference-audio", action="append", default=[], help="Reference audio path, URL, data URL, or asset ID; repeat in prompt order")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION_SECONDS)
    parser.add_argument("--aspect-ratio", choices=SUPPORTED_ASPECT_RATIOS)
    parser.add_argument("--resolution", choices=SUPPORTED_RESOLUTIONS, default=DEFAULT_RESOLUTION)
    parser.add_argument("--audio", action="store_true", help="Set generate_audio=true")
    parser.add_argument("--model", help="Backend-compatible model override")
    parser.add_argument("--backend", choices=BACKENDS, default=DEFAULT_BACKEND)
    parser.add_argument("--task-type", choices=("auto", "reference", "edit", "extend"))
    parser.add_argument("--output-format", choices=("mp4", "mov"))
    parser.add_argument("--return-last-frame", action="store_true")
    parser.add_argument("--output", help="Local video output path")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL_SECONDS)
    parser.add_argument("--resume-task", help="Poll an existing task without creating a new one")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print the request without credentials or submission")
    args = parser.parse_args()

    if args.timeout <= 0 or args.poll_interval <= 0:
        print_json({"success": False, "backend": args.backend, "error": "timeout and poll interval must be positive"})
        return 2
    if args.image and args.first_frame:
        print_json({"success": False, "backend": args.backend, "error": "--image and --first-frame cannot both be used"})
        return 2
    if args.image:
        print("warning: --image is deprecated; use --first-frame", file=sys.stderr)

    profile = BACKENDS[args.backend]
    model = args.model or profile["model"]
    try:
        if args.resume_task:
            if args.dry_run:
                print_json({"success": True, "dry_run": True, "backend": args.backend, "resume_task": args.resume_task})
                return 0
            backend_profile, api_key = resolve_backend(args.backend)
            from volcenginesdkarkruntime import Ark

            client = Ark(base_url=backend_profile["base_url"], api_key=api_key)
            task, last_status = poll_task(
                client,
                args.resume_task,
                timeout=args.timeout,
                poll_interval=args.poll_interval,
                initial_status="resumed",
            )
            if task is None:
                print_json({
                    "success": False,
                    "backend": args.backend,
                    "task_id": args.resume_task,
                    "status": last_status,
                    "error": "task polling timed out",
                })
                return 1
            result = task_result(
                task,
                backend=args.backend,
                task_id=args.resume_task,
                prompt=args.prompt,
                requested_model=args.model,
                output_path=args.output,
                download_timeout=args.timeout,
            )
            print_json(result)
            return 0 if result["success"] else 1

        first_frame_raw = args.first_frame or args.image
        first_frame = normalize_media_input(first_frame_raw, "image") if first_frame_raw else None
        last_frame = normalize_media_input(args.last_frame, "image") if args.last_frame else None
        reference_images = [normalize_media_input(value, "image") for value in args.reference_image]
        reference_videos = [normalize_media_input(value, "video") for value in args.reference_video]
        reference_audios = [normalize_media_input(value, "audio") for value in args.reference_audio]
        aspect_ratio = args.aspect_ratio or ("adaptive" if first_frame else DEFAULT_ASPECT_RATIO)
        content, settings = build_request(
            backend=args.backend,
            model=model,
            prompt=args.prompt,
            first_frame=first_frame,
            last_frame=last_frame,
            reference_images=reference_images,
            reference_videos=reference_videos,
            reference_audios=reference_audios,
            duration=args.duration,
            aspect_ratio=aspect_ratio,
            resolution=args.resolution,
            generate_audio=bool(args.audio),
            output_format=args.output_format,
            return_last_frame=bool(args.return_last_frame),
            task_type=args.task_type,
        )
        if args.dry_run:
            print_json({
                "success": True,
                "dry_run": True,
                "backend": args.backend,
                "model": model,
                "content": content,
                "settings": settings,
            })
            return 0

        backend_profile, api_key = resolve_backend(args.backend)
        from volcenginesdkarkruntime import Ark

        client = Ark(base_url=backend_profile["base_url"], api_key=api_key)
        created = client.content_generation.tasks.create(model=model, content=content, **settings)
        task_id = str(created.id)
        initial_status = str(getattr(created, "status", "created"))
        task, last_status = poll_task(
            client,
            task_id,
            timeout=args.timeout,
            poll_interval=args.poll_interval,
            initial_status=initial_status,
        )
        if task is None:
            print_json({
                "success": False,
                "backend": args.backend,
                "task_id": task_id,
                "status": last_status,
                "model": model,
                "error": "task polling timed out",
            })
            return 1
        result = task_result(
            task,
            backend=args.backend,
            task_id=task_id,
            prompt=args.prompt,
            requested_model=model,
            output_path=args.output,
            download_timeout=args.timeout,
        )
        print_json(result)
        return 0 if result["success"] else 1
    except Exception as exc:
        print_json({
            "success": False,
            "backend": args.backend,
            "model": model,
            "task_id": args.resume_task,
            "error": str(exc),
        })
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
