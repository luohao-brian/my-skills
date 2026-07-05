"""Ark implementation for Hermes `text_to_speech`."""

from __future__ import annotations

import base64
import json
import re
from typing import Any, Optional

import requests

from agent.tts_provider import TTSProvider

TTS_FINISH_CODE = 20_000_000


def _infer_language(text: str) -> str:
    if re.search(r"[\u3040-\u30ff]", text):
        return "ja"
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    return ""


def _tts_payload(text: str, voice: str, fmt: str, sample_rate: int = 24000, language: str = "") -> dict[str, Any]:
    additions = {
        "disable_markdown_filter": True,
        "enable_timestamp": True,
    }
    if language:
        additions["explicit_language"] = language
    return {
        "user": {"uid": "hermes-ark-plugin"},
        "req_params": {
            "text": text,
            "speaker": voice,
            "audio_params": {
                "format": fmt,
                "sample_rate": sample_rate,
                "enable_timestamp": True,
            },
            "additions": json.dumps(additions, ensure_ascii=False),
        },
    }


def _parse_tts_stream(response: requests.Response) -> bytes:
    chunks: list[bytes] = []
    for raw_line in response.iter_lines(decode_unicode=True):
        if not raw_line:
            continue
        item = json.loads(raw_line)
        code = int(item.get("code", 0))
        if code == 0 and item.get("data"):
            chunks.append(base64.b64decode(item["data"]))
        elif code == TTS_FINISH_CODE:
            break
        elif code > 0:
            raise RuntimeError(f"TTS error chunk: {item}")
    if not chunks:
        raise RuntimeError("TTS finished without audio")
    return b"".join(chunks)


class ArkTextToSpeechProvider(TTSProvider):
    @property
    def name(self) -> str:
        return "ark"

    @property
    def display_name(self) -> str:
        return "Volcengine Ark"

    def is_available(self) -> bool:
        from ..common.config import api_key

        return bool(api_key())

    def synthesize(
        self,
        text: str,
        output_path: str,
        *,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        speed: Optional[float] = None,
        format: str = "mp3",
        **extra: Any,
    ) -> str:
        from pathlib import Path

        from ..common.client import response_error
        from ..common.config import section, section_api_key, timeout_seconds

        cfg = section("text_to_speech")
        api_key = section_api_key("text_to_speech")
        if not api_key:
            raise RuntimeError("Ark TTS API key is not configured")
        url = str(cfg.get("base_url") or "https://openspeech.bytedance.com/api/v3/plan/tts/unidirectional")
        resource_id = str(cfg.get("resource_id") or "seed-tts-2.0")
        voice_id = voice or str(cfg.get("voice") or "zh_female_vv_uranus_bigtts")
        language = str(extra.get("language") or cfg.get("language") or "auto").strip().lower()
        output_format = (format or str(cfg.get("output_format") or "mp3")).lower()
        max_text_length = int(cfg.get("max_text_length") or 4000)
        text = text[:max_text_length]
        explicit_language = _infer_language(text) if language in {"", "auto"} else language

        path = Path(output_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        response = None
        try:
            response = requests.post(
                url,
                headers={
                    "X-Api-Key": api_key,
                    "X-Api-Resource-Id": resource_id,
                    "Content-Type": "application/json",
                    "Connection": "keep-alive",
                    "X-Control-Require-Usage-Tokens-Return": "*",
                },
                json=_tts_payload(text, voice_id, output_format, language=explicit_language),
                stream=True,
                timeout=max(timeout_seconds("text_to_speech", 120), 120),
            )
            if response.status_code >= 400:
                raise RuntimeError(response_error(response))
            audio = _parse_tts_stream(response)
            path.write_bytes(audio)
            return str(path)
        finally:
            if response is not None:
                response.close()
