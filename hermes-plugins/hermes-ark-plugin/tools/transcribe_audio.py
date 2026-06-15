"""Ark-backed top-level Hermes `transcribe_audio` tool."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


TRANSCRIBE_AUDIO_SCHEMA: dict[str, Any] = {
    "name": "transcribe_audio",
    "description": "Transcribe an audio file with the configured Ark STT provider.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute or relative path to the audio file to transcribe.",
            },
            "model": {
                "type": "string",
                "description": "Optional STT model override.",
            },
            "language": {
                "type": "string",
                "description": "Optional language hint.",
            },
        },
        "required": ["file_path"],
    },
}


def check_ark_transcribe_audio() -> bool:
    from ..common.config import api_key

    return bool(api_key())


def ark_transcribe_audio(args: dict[str, Any], **_kw: Any) -> str:
    from tools.transcription_tools import transcribe_audio

    file_path = str(args.get("file_path") or args.get("path") or "")
    if not file_path:
        return json.dumps(
            {"success": False, "transcript": "", "provider": "ark", "error": "file_path is required"},
            ensure_ascii=False,
        )
    resolved = Path(file_path).expanduser()
    result = transcribe_audio(str(resolved), model=args.get("model") or None)
    if args.get("language") and isinstance(result, dict):
        result.setdefault("language", args.get("language"))
    return json.dumps(result, ensure_ascii=False)
