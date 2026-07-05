"""Ark implementation for Hermes `text_to_speech`."""

from __future__ import annotations

import base64
import json
import re
from typing import Any, Optional

import requests

from agent.tts_provider import TTSProvider

TTS_FINISH_CODE = 20_000_000


def _iter_tts_items(response: requests.Response):
    decoder = json.JSONDecoder()
    buffer = ""
    for chunk in response.iter_content(chunk_size=4096, decode_unicode=True):
        if not chunk:
            continue
        buffer += chunk
        while True:
            buffer = buffer.lstrip()
            if not buffer:
                break
            try:
                item, offset = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                break
            yield item
            buffer = buffer[offset:]


def _infer_language(text: str) -> str:
    if re.search(r"[\u3040-\u30ff]", text):
        return "ja"
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    return ""


def _subtitle_flag(resource_id: str, voice: str) -> str:
    if "2.0" in resource_id or "_uranus_" in voice or voice.startswith("S_"):
        return "enable_subtitle"
    return "enable_timestamp"


def _tts_payload(
    text: str,
    voice: str,
    fmt: str,
    sample_rate: int = 24000,
    language: str = "",
    subtitle_flag: str = "enable_subtitle",
) -> dict[str, Any]:
    additions = {
        "disable_markdown_filter": True,
        subtitle_flag: True,
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
                subtitle_flag: True,
            },
            "additions": json.dumps(additions, ensure_ascii=False),
        },
    }


def _words_to_segment(sentence: dict[str, Any], segment_id: int) -> dict[str, Any] | None:
    words = sentence.get("words")
    if not isinstance(words, list):
        return None
    timed_words = [
        word for word in words
        if isinstance(word, dict)
        and isinstance(word.get("startTime"), (int, float))
        and isinstance(word.get("endTime"), (int, float))
        and word.get("startTime") >= 0
        and word.get("endTime") >= 0
    ]
    if not timed_words:
        return None
    text = str(sentence.get("text") or "").strip()
    if not text:
        text = "".join(str(word.get("word") or "") for word in timed_words).strip()
    if not text:
        return None
    return {
        "id": segment_id,
        "text": text,
        "start": round(float(timed_words[0]["startTime"]), 3),
        "end": round(float(timed_words[-1]["endTime"]), 3),
    }


def _parse_tts_stream(response: requests.Response) -> tuple[bytes, list[dict[str, Any]]]:
    chunks: list[bytes] = []
    transcript: list[dict[str, Any]] = []
    for item in _iter_tts_items(response):
        code = int(item.get("code", 0))
        if code == 0 and item.get("data"):
            chunks.append(base64.b64decode(item["data"]))
        elif code == 0 and isinstance(item.get("sentence"), dict):
            segment = _words_to_segment(item["sentence"], len(transcript))
            if segment is not None:
                transcript.append(segment)
        elif code == TTS_FINISH_CODE:
            break
        elif code > 0:
            raise RuntimeError(f"TTS error chunk: {item}")
    if not chunks:
        raise RuntimeError("TTS finished without audio")
    return b"".join(chunks), transcript


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
        subtitle_flag = _subtitle_flag(resource_id, voice_id)

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
                json=_tts_payload(
                    text,
                    voice_id,
                    output_format,
                    language=explicit_language,
                    subtitle_flag=subtitle_flag,
                ),
                stream=True,
                timeout=max(timeout_seconds("text_to_speech", 120), 120),
            )
            if response.status_code >= 400:
                raise RuntimeError(response_error(response))
            audio, transcript = _parse_tts_stream(response)
            path.write_bytes(audio)
            transcript_path = path.with_suffix(".transcript.json")
            if transcript:
                transcript_path.write_text(
                    json.dumps(transcript, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            elif transcript_path.exists():
                transcript_path.unlink()
            return str(path)
        finally:
            if response is not None:
                response.close()
