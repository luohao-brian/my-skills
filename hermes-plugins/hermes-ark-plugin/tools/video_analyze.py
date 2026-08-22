"""Ark override for Hermes ``video_analyze`` with host-owned media safety."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from tools.vision_tools import VIDEO_ANALYZE_SCHEMA

MAX_VIDEO_DATA_URL_BYTES = 50 * 1024 * 1024


def check_ark_video() -> bool:
    from ..common.config import section_api_key
    return bool(section_api_key("video_analyze"))


async def ark_video_analyze(args: dict[str, Any], **kw: Any) -> str:
    from tools.image_source import ResolveContext, resolve_image_source
    from tools.interrupt import is_interrupted
    from ..common.auth import require_api_key
    from ..common.client import bytes_to_data_url, extract_chat_text, post_json, response_error
    from ..common.config import ark_base_url, section, section_backend, timeout_seconds

    cfg = section("video_analyze")
    backend = section_backend("video_analyze")
    default_model = "doubao-seed-2.0-lite" if backend == "ark-agent-plan" else "doubao-seed-2-0-lite-260428"
    model = str(cfg.get("model") or default_model)
    if is_interrupted():
        return json.dumps({"success": False, "analysis": "", "error": "Interrupted", "provider": "ark"})
    try:
        resolved = await resolve_image_source(
            str(args.get("video_url") or ""),
            ResolveContext(task_id=kw.get("task_id")),
            permitted=("video",),
        )
        video_url = bytes_to_data_url(resolved.data, resolved.mime)
        if len(video_url) > MAX_VIDEO_DATA_URL_BYTES:
            raise ValueError("Video base64 payload exceeds the 50 MB Hermes limit")
        response = await asyncio.to_thread(
            post_json,
            ark_base_url("video_analyze"),
            "chat/completions",
            require_api_key("video_analyze"),
            {
                "model": model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "video_url", "video_url": {"url": video_url}},
                        {"type": "text", "text": str(args.get("question") or "")},
                    ],
                }],
                "temperature": float(cfg.get("temperature", 0.1)),
                "max_tokens": int(cfg.get("max_tokens", 4000)),
            },
            timeout=max(timeout_seconds("video_analyze", 300), 60),
        )
        if response.status_code >= 400:
            raise RuntimeError(response_error(response))
        text = extract_chat_text(response.json())
        if not text:
            raise RuntimeError("Ark video response contained no analysis text")
        return json.dumps({"success": True, "analysis": text, "model": model, "provider": "ark", "backend": backend}, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"success": False, "analysis": "", "error": str(exc), "model": model, "provider": "ark", "backend": backend}, ensure_ascii=False)
