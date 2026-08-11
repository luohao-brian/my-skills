"""Volcengine Seed-TTS backend with Ark API and Agent Plan profiles."""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from tts_backends.backend_common import publish_audio_bytes


FINISH_CODE = 20_000_000
DEFAULT_MODEL = "seed-tts-2.0"
DEFAULT_VOICE = "zh_female_vv_uranus_bigtts"
DEFAULT_FORMAT = "mp3"
DEFAULT_SAMPLE_RATE = 24000
MAX_TEXT_LENGTH = 4000
REQUEST_TIMEOUT_SECONDS = 120


@dataclass(frozen=True)
class TtsProfile:
    name: str
    provider: str
    api_key: str
    base_url: str
    model: str


FIXED_PROFILE = "ark-agent-plan"
FIXED_PROVIDER = "volc-ark-agent-plan"
FIXED_ENDPOINT = "https://openspeech.bytedance.com/api/v3/plan/tts/unidirectional"
SUPPORTED_PROFILES = (FIXED_PROFILE,)


def resolve_profile(profile_name: str | None = None) -> TtsProfile:
    name = (profile_name or FIXED_PROFILE).strip().lower()
    if name != FIXED_PROFILE:
        raise RuntimeError(
            f"PPT Master TTS is fixed to {FIXED_PROFILE}; received '{name}'."
        )
    api_key = os.environ.get("ARK_AGENT_PLAN_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing Agent Plan TTS credential. Set ARK_AGENT_PLAN_API_KEY=<key>.")

    return TtsProfile(
        name=name,
        provider=FIXED_PROVIDER,
        api_key=api_key,
        base_url=FIXED_ENDPOINT,
        model=DEFAULT_MODEL,
    )


def output_extension(audio_format: str = DEFAULT_FORMAT) -> str:
    normalized = audio_format.strip().lower()
    if normalized != "mp3":
        raise RuntimeError("Volcengine narration currently publishes mp3 only.")
    return ".mp3"


def build_payload(
    text: str,
    *,
    voice_id: str,
    audio_format: str,
    sample_rate: int,
) -> dict[str, Any]:
    additions = {"disable_markdown_filter": True}
    return {
        "user": {"uid": "ppt-master"},
        "req_params": {
            "text": text,
            "speaker": voice_id,
            "audio_params": {
                "format": audio_format,
                "sample_rate": sample_rate,
                "enable_subtitle": True,
            },
            "additions": json.dumps(additions, ensure_ascii=False),
        },
    }


def _iter_json_items(response: Any) -> Iterator[dict[str, Any]]:
    decoder = json.JSONDecoder()
    buffer = ""
    for chunk in response.iter_content(chunk_size=4096, decode_unicode=True):
        if not chunk:
            continue
        if isinstance(chunk, bytes):
            chunk = chunk.decode("utf-8")
        buffer += chunk
        while True:
            buffer = buffer.lstrip()
            if not buffer:
                break
            try:
                item, offset = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                break
            if not isinstance(item, dict):
                raise RuntimeError(f"Volcengine TTS returned a non-object chunk: {item!r}")
            yield item
            buffer = buffer[offset:]
    if buffer.strip():
        raise RuntimeError("Volcengine TTS ended with an incomplete JSON chunk")


def _parse_audio(response: Any) -> bytes:
    chunks: list[bytes] = []
    for item in _iter_json_items(response):
        code = int(item.get("code", 0))
        if code == 0 and item.get("data"):
            chunks.append(base64.b64decode(item["data"], validate=True))
        elif code == FINISH_CODE:
            break
        elif code > 0:
            raise RuntimeError(f"Volcengine TTS error chunk: {item}")
    if not chunks:
        raise RuntimeError("Volcengine TTS finished without audio")
    return b"".join(chunks)


def generate(
    text: str,
    output_path: Path,
    *,
    profile: TtsProfile,
    voice_id: str = DEFAULT_VOICE,
    audio_format: str = DEFAULT_FORMAT,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> None:
    if not text.strip():
        raise RuntimeError("Volcengine TTS text must not be empty")
    if len(text) > MAX_TEXT_LENGTH:
        raise RuntimeError(
            f"Volcengine TTS text exceeds the {MAX_TEXT_LENGTH}-character per-slide limit"
        )
    output_extension(audio_format)

    import requests

    response = requests.post(
        profile.base_url,
        headers={
            "X-Api-Key": profile.api_key,
            "X-Api-Resource-Id": profile.model,
            "Content-Type": "application/json",
            "Connection": "keep-alive",
            "X-Control-Require-Usage-Tokens-Return": "*",
        },
        json=build_payload(
            text,
            voice_id=voice_id,
            audio_format=audio_format,
            sample_rate=sample_rate,
        ),
        stream=True,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    try:
        if response.status_code >= 400:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:500]}")
        publish_audio_bytes(_parse_audio(response), output_path)
    finally:
        response.close()


def print_voices() -> None:
    print("Volcengine Seed-TTS voices are selected by speaker ID.")
    print(f"Default: {DEFAULT_VOICE}")
    print("Override with --voice-id or TTS_VOICE.")
