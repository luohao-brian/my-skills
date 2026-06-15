#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

FINISH_CODE = 20_000_000


def env_first(names: list[str]) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def infer_language(text: str) -> str:
    if re.search(r"[\u3040-\u30ff]", text):
        return "ja"
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    return ""


def default_output(fmt: str) -> Path:
    out_dir = Path("outputs") / "tts"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return out_dir / f"tts_{stamp}.{fmt}"


def build_payload(text: str, voice: str, fmt: str, sample_rate: int, language: str) -> dict[str, Any]:
    additions: dict[str, Any] = {
        "disable_markdown_filter": True,
        "enable_timestamp": True,
    }
    explicit_language = infer_language(text) if language in {"", "auto"} else language
    if explicit_language:
        additions["explicit_language"] = explicit_language
    return {
        "user": {"uid": "openclaw-tts"},
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


def parse_stream(response: Any) -> bytes:
    chunks: list[bytes] = []
    for raw_line in response.iter_lines(decode_unicode=True):
        if not raw_line:
            continue
        item = json.loads(raw_line)
        code = int(item.get("code", 0))
        if code == 0 and item.get("data"):
            chunks.append(base64.b64decode(item["data"]))
        elif code == FINISH_CODE:
            break
        elif code > 0:
            raise RuntimeError(f"TTS error chunk: {item}")
    if not chunks:
        raise RuntimeError("TTS finished without audio")
    return b"".join(chunks)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate speech with Volcengine Ark TTS")
    parser.add_argument("text", help="Text to synthesize")
    parser.add_argument("--output", help="Output audio path")
    parser.add_argument("--voice", default=os.getenv("VOLC_TTS_VOICE", "zh_female_vv_uranus_bigtts"))
    parser.add_argument("--format", default=os.getenv("VOLC_TTS_FORMAT", "mp3"))
    parser.add_argument("--sample-rate", type=int, default=int(os.getenv("VOLC_TTS_SAMPLE_RATE", "24000")))
    parser.add_argument("--language", default=os.getenv("VOLC_TTS_LANGUAGE", "auto"))
    parser.add_argument("--resource-id", default=os.getenv("VOLC_TTS_RESOURCE_ID", "seed-tts-2.0"))
    parser.add_argument("--base-url", default=os.getenv("VOLC_TTS_BASE_URL", "https://openspeech.bytedance.com/api/v3/plan/tts/unidirectional"))
    parser.add_argument("--timeout", type=float, default=float(os.getenv("VOLC_TTS_TIMEOUT", "120")))
    parser.add_argument("--max-chars", type=int, default=int(os.getenv("VOLC_TTS_MAX_CHARS", "4000")))
    args = parser.parse_args()

    import requests

    api_key = env_first(["VOLC_AGENT_PLAN_API_KEY", "ARK_API_KEY", "OPENAPI_API_KEY"])
    if not api_key:
        print(json.dumps({"success": False, "error": "Missing VOLC_AGENT_PLAN_API_KEY"}, ensure_ascii=False), file=sys.stderr)
        return 2

    fmt = args.format.lower().strip(".")
    output_path = Path(args.output).expanduser() if args.output else default_output(fmt)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = args.text[: args.max_chars]

    response = None
    try:
        response = requests.post(
            args.base_url,
            headers={
                "X-Api-Key": api_key,
                "X-Api-Resource-Id": args.resource_id,
                "Content-Type": "application/json",
                "Connection": "keep-alive",
                "X-Control-Require-Usage-Tokens-Return": "*",
            },
            json=build_payload(text, args.voice, fmt, args.sample_rate, args.language),
            stream=True,
            timeout=max(args.timeout, 120),
        )
        if response.status_code >= 400:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:500]}")
        audio = parse_stream(response)
        output_path.write_bytes(audio)
        print(json.dumps({
            "success": True,
            "type": "audio",
            "local_path": str(output_path),
            "format": fmt,
            "bytes": len(audio),
            "speaker": args.voice,
            "sample_rate": args.sample_rate,
            "resource_id": args.resource_id,
        }, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    finally:
        if response is not None:
            response.close()


if __name__ == "__main__":
    raise SystemExit(main())
