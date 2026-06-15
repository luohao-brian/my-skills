"""Ark override for Hermes `video_analyze`."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


VIDEO_ANALYZE_SCHEMA: dict[str, Any] = {
    "name": "video_analyze",
    "description": "Analyze a video with the configured Ark video model.",
    "parameters": {
        "type": "object",
        "properties": {
            "video_url": {
                "type": "string",
                "description": "Video URL, local file path, or data URL to analyze.",
            },
            "question": {
                "type": "string",
                "description": "Question or instruction about the video.",
            },
            "model": {
                "type": "string",
                "description": "Optional model override.",
            },
        },
        "required": ["video_url", "question"],
    },
}


def check_ark_video() -> bool:
    from ..common.config import api_key

    return bool(api_key())


async def ark_video_analyze(args: dict[str, Any], **_kw: Any) -> str:
    from ..common.auth import require_api_key
    from ..common.client import extract_responses_text, file_to_data_url, post_json, response_error
    from ..common.config import ark_base_url, section, timeout_seconds

    cfg = section("video_analyze")
    video_url = str(args.get("video_url") or "")
    question = str(args.get("question") or "")
    source_path = Path(video_url).expanduser()
    resolved_video = file_to_data_url(source_path, "video/mp4") if source_path.is_file() else video_url
    model = str(args.get("model") or cfg.get("model") or "doubao-seed-2.0-lite")
    try:
        response = post_json(
            ark_base_url(),
            "responses",
            require_api_key(),
            {
                "model": model,
                "input": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_video",
                                "video_url": resolved_video,
                                "fps": int(cfg.get("fps", 1)),
                            },
                            {"type": "input_text", "text": question},
                        ],
                    }
                ],
                "temperature": float(cfg.get("temperature", 0.1)),
                "max_output_tokens": int(cfg.get("max_tokens", 4000)),
            },
            timeout=max(timeout_seconds("video_analyze", 300), 60),
        )
        if response.status_code >= 400:
            return json.dumps({"success": False, "analysis": "", "error": response_error(response), "model": model}, ensure_ascii=False)
        text = extract_responses_text(response.json())
        return json.dumps({"success": True, "analysis": text, "model": model, "provider": "ark"}, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"success": False, "analysis": "", "error": str(exc), "model": model, "provider": "ark"}, ensure_ascii=False)
