#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any

FINISH_CODE = 20_000_000
# Official V3 HTTP chunked protocol and payload fields:
# https://www.volcengine.com/docs/6561/1598757?lang=zh
# Agent Plan exposes the same protocol through the fixed /api/v3/plan route.
DEFAULT_BACKEND = "ark-agent-plan"
BACKENDS = {
    "ark-agent-plan": {
        "endpoint": "https://openspeech.bytedance.com/api/v3/plan/tts/unidirectional",
        "api_key_env": "ARK_AGENT_PLAN_API_KEY",
    },
    "ark-api": {
        "endpoint": "https://openspeech.bytedance.com/api/v3/tts/unidirectional",
        "api_key_env": "ARK_TTS_X_API_KEY",
    },
}
RESOURCE_ID = "seed-tts-2.0"
DEFAULT_VOICE = "zh_female_vv_uranus_bigtts"
REQUEST_TIMEOUT_SECONDS = 120


def resolve_backend(name: str) -> tuple[dict[str, str], str]:
    profile = BACKENDS.get(name)
    if profile is None:
        raise ValueError(f"Unsupported backend: {name}")
    api_key_env = profile["api_key_env"]
    api_key = os.getenv(api_key_env, "").strip()
    if not api_key:
        raise ValueError(f"Missing {api_key_env} for backend {name}")
    return profile, api_key


def default_output(fmt: str) -> Path:
    out_dir = Path("outputs") / "tts"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return out_dir / f"tts_{stamp}.{fmt}"


def build_payload(
    text: str,
    voice: str,
    fmt: str,
    sample_rate: int,
) -> dict[str, Any]:
    additions: dict[str, Any] = {
        "disable_markdown_filter": True,
    }
    return {
        "user": {"uid": "ark-tts"},
        "req_params": {
            "text": text,
            "speaker": voice,
            "audio_params": {
                "format": fmt,
                "sample_rate": sample_rate,
                "enable_subtitle": True,
            },
            "additions": json.dumps(additions, ensure_ascii=False),
        },
    }


def iter_tts_items(response: Any):
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


def words_to_segment(sentence: dict[str, Any], segment_id: int) -> dict[str, Any] | None:
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


def parse_stream(response: Any) -> tuple[bytes, list[dict[str, Any]]]:
    chunks: list[bytes] = []
    transcript: list[dict[str, Any]] = []
    for item in iter_tts_items(response):
        code = int(item.get("code", 0))
        if code == 0 and item.get("data"):
            chunks.append(base64.b64decode(item["data"]))
        elif code == 0 and isinstance(item.get("sentence"), dict):
            segment = words_to_segment(item["sentence"], len(transcript))
            if segment is not None:
                transcript.append(segment)
        elif code == FINISH_CODE:
            break
        elif code > 0:
            raise RuntimeError(f"TTS error chunk: {item}")
    if not chunks:
        raise RuntimeError("TTS finished without audio")
    return b"".join(chunks), transcript


def synthesize(
    *,
    requests: Any,
    endpoint: str,
    api_key: str,
    text: str,
    voice: str,
    fmt: str,
    sample_rate: int,
) -> tuple[bytes, list[dict[str, Any]]]:
    response = requests.post(
        endpoint,
        headers={
            "X-Api-Key": api_key,
            "X-Api-Resource-Id": RESOURCE_ID,
            "Content-Type": "application/json",
            "Connection": "keep-alive",
            "X-Control-Require-Usage-Tokens-Return": "*",
        },
        json=build_payload(text, voice, fmt, sample_rate),
        stream=True,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    try:
        if response.status_code >= 400:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:500]}")
        audio, transcript = parse_stream(response)
        return audio, transcript
    finally:
        response.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate speech with Ark TTS")
    parser.add_argument("text", help="Text to synthesize")
    parser.add_argument("--output", help="Output audio path")
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--format", choices=["mp3", "ogg_opus", "pcm"], default="mp3")
    parser.add_argument("--backend", choices=BACKENDS, default=DEFAULT_BACKEND)
    parser.add_argument(
        "--sample-rate",
        type=int,
        choices=[8000, 16000, 22050, 24000, 32000, 44100, 48000],
        default=24000,
    )
    args = parser.parse_args()

    try:
        profile, api_key = resolve_backend(args.backend)
    except ValueError as exc:
        print(
            json.dumps({"success": False, "backend": args.backend, "error": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 2

    import requests

    fmt = args.format.lower().strip(".")
    output_path = Path(args.output).expanduser() if args.output else default_output(fmt)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = args.text
    try:
        audio, transcript = synthesize(
            requests=requests,
            endpoint=profile["endpoint"],
            api_key=api_key,
            text=text,
            voice=args.voice,
            fmt=fmt,
            sample_rate=args.sample_rate,
        )
        output_path.write_bytes(audio)
        transcript_path = output_path.with_suffix(".transcript.json")
        if transcript:
            transcript_path.write_text(
                json.dumps(transcript, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        elif transcript_path.exists():
            transcript_path.unlink()
        print(json.dumps({
            "success": True,
            "type": "audio",
            "backend": args.backend,
            "resource_id": RESOURCE_ID,
            "local_path": str(output_path),
            "transcript_path": str(transcript_path) if transcript else None,
            "transcript_segments": len(transcript),
            "format": fmt,
            "bytes": len(audio),
            "speaker": args.voice,
            "sample_rate": args.sample_rate,
        }, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({
            "success": False,
            "backend": args.backend,
            "resource_id": RESOURCE_ID,
            "error": str(exc),
        }, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
