"""Ark override for Hermes ``vision_analyze`` with host-owned media safety."""

from __future__ import annotations

import asyncio
import io
import json
from typing import Any

from tools.vision_tools import VISION_ANALYZE_SCHEMA


def check_ark_vision() -> bool:
    from ..common.config import section_api_key
    return bool(section_api_key("vision_analyze"))


def _crop(data: bytes, region: Any) -> tuple[bytes, str]:
    if not isinstance(region, list) or len(region) != 4:
        return data, ""
    from PIL import Image
    with Image.open(io.BytesIO(data)) as image:
        x1, y1, x2, y2 = (int(value) for value in region)
        left, right = sorted((max(0, min(image.width, x1)), max(0, min(image.width, x2))))
        top, bottom = sorted((max(0, min(image.height, y1)), max(0, min(image.height, y2))))
        if right <= left or bottom <= top:
            raise ValueError("region does not overlap the image")
        cropped = image.crop((left, top, right, bottom)).convert("RGB")
        buffer = io.BytesIO()
        cropped.save(buffer, format="JPEG", quality=92)
        return buffer.getvalue(), "image/jpeg"


async def ark_vision_analyze(args: dict[str, Any], **kw: Any) -> str:
    from tools.image_source import ResolveContext, resolve_image_source
    from tools.interrupt import is_interrupted
    from ..common.auth import require_api_key
    from ..common.client import bytes_to_data_url, extract_chat_text, post_json, response_error
    from ..common.config import ark_base_url, section, section_backend, timeout_seconds

    cfg = section("vision_analyze")
    backend = section_backend("vision_analyze")
    default_model = "doubao-seed-2.0-lite" if backend == "ark-agent-plan" else "doubao-seed-2-0-lite-260428"
    model = str(cfg.get("model") or default_model)
    if is_interrupted():
        return json.dumps({"success": False, "analysis": "", "error": "Interrupted", "provider": "ark"})
    try:
        resolved = await resolve_image_source(
            str(args.get("image_url") or ""),
            ResolveContext(task_id=kw.get("task_id")),
        )
        data, cropped_mime = await asyncio.to_thread(_crop, resolved.data, args.get("region"))
        image_url = bytes_to_data_url(data, cropped_mime or resolved.mime)
        response = await asyncio.to_thread(
            post_json,
            ark_base_url("vision_analyze"),
            "chat/completions",
            require_api_key("vision_analyze"),
            {
                "model": model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text", "text": str(args.get("question") or "")},
                    ],
                }],
                "temperature": float(cfg.get("temperature", 0.1)),
                "max_tokens": int(cfg.get("max_tokens", 2000)),
            },
            timeout=max(timeout_seconds("vision_analyze", 300), 60),
        )
        if response.status_code >= 400:
            raise RuntimeError(response_error(response))
        text = extract_chat_text(response.json())
        if not text:
            raise RuntimeError("Ark vision response contained no analysis text")
        return json.dumps({"success": True, "analysis": text, "model": model, "provider": "ark", "backend": backend}, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"success": False, "analysis": "", "error": str(exc), "model": model, "provider": "ark", "backend": backend}, ensure_ascii=False)
