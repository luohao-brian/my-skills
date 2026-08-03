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


BASE_URL = "https://ark.cn-beijing.volces.com/api/plan/v3"
MODEL_ID = "doubao-seedance-2.0-fast"
DEFAULT_DURATION_SECONDS = 5
DEFAULT_ASPECT_RATIO = "16:9"
DEFAULT_RESOLUTION = "720p"
TASK_TIMEOUT_SECONDS = 300
POLL_INTERVAL_SECONDS = 5


def api_key_value() -> str:
    return os.getenv("ARK_AGENT_PLAN_API_KEY", "").strip()


def file_to_data_url(path: str) -> str:
    p = Path(path).expanduser()
    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    payload = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate video with Ark Agent Plan")
    parser.add_argument("prompt")
    parser.add_argument("--image", help="Optional first-frame image path, data URL, or remote URL")
    parser.add_argument("--duration", type=int, choices=range(5, 13), default=DEFAULT_DURATION_SECONDS)
    parser.add_argument("--aspect-ratio", default=DEFAULT_ASPECT_RATIO)
    parser.add_argument("--resolution", default=DEFAULT_RESOLUTION)
    parser.add_argument("--audio", action="store_true")
    args = parser.parse_args()

    api_key = api_key_value()
    if not api_key:
        print(json.dumps({"success": False, "error": "Missing ARK_AGENT_PLAN_API_KEY"}, ensure_ascii=False), file=sys.stderr)
        return 2

    from volcenginesdkarkruntime import Ark

    duration = args.duration
    full_prompt = " ".join([
        args.prompt.strip(),
        f"--rs {args.resolution}",
        f"--rt {args.aspect_ratio}",
        "--fps 24",
        f"--dur {duration}",
        "--wm false",
    ])

    try:
        client = Ark(base_url=BASE_URL, api_key=api_key)
        content: list[dict[str, Any]] = [{"type": "text", "text": full_prompt}]
        if args.image:
            image_url = args.image
            if not (image_url.startswith("http://") or image_url.startswith("https://") or image_url.startswith("data:")):
                image_url = file_to_data_url(image_url)
            content.append({"type": "image_url", "image_url": {"url": image_url}})

        created = client.content_generation.tasks.create(
            model=MODEL_ID,
            content=content,
            extra_body={"generate_audio": bool(args.audio)},
        )
        task_id = created.id
        last_status = getattr(created, "status", "created")
        deadline = time.time() + TASK_TIMEOUT_SECONDS
        while time.time() < deadline:
            task = client.content_generation.tasks.get(task_id=task_id)
            last_status = task.status
            if task.status == "succeeded":
                video_url = task.content.video_url
                print(json.dumps({
                    "success": True,
                    "type": "video",
                    "task_id": task_id,
                    "status": task.status,
                    "video_url": video_url,
                    "model": MODEL_ID,
                    "prompt": args.prompt,
                    "duration": duration,
                    "aspect_ratio": args.aspect_ratio,
                    "resolution": args.resolution,
                    "used_reference_image": bool(args.image),
                }, ensure_ascii=False, indent=2))
                return 0
            if task.status == "failed":
                raise RuntimeError(f"task_id={task_id}; error={task.error}")
            time.sleep(POLL_INTERVAL_SECONDS)
        print(json.dumps({
            "success": False,
            "error": "task timed out",
            "task_id": task_id,
            "last_status": last_status,
            "model": MODEL_ID,
        }, ensure_ascii=False), file=sys.stderr)
        return 1
    except Exception as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
