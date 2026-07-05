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
DEFAULT_BASE_URL = "https://openspeech.bytedance.com/api/v3/plan/tts/unidirectional"
DEFAULT_RESOURCE_ID = "seed-tts-2.0"
DEFAULT_VOICE = "zh_female_vv_uranus_bigtts"


def strip_scalar(value: str) -> str:
    return value.strip().strip('"').strip("'")


def dotenv_value(name: str) -> str:
    for env_path in (Path.cwd() / ".env", Path.home() / ".hermes/.env"):
        try:
            lines = env_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == name:
                return strip_scalar(value)
    return ""


def env_value(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    return dotenv_value(name)


def resolve_secret(value: str) -> str:
    raw = str(value or "").strip()
    if raw.startswith("${") and raw.endswith("}"):
        return env_value(raw[2:-1])
    return raw


def parse_simple_yaml(path: Path) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    for raw_line in lines:
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if not key or key.startswith("-"):
            continue
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1] if stack else root
        value = value.strip()
        if value:
            parent[key] = strip_scalar(value)
        else:
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
    return root


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception:
        return parse_simple_yaml(path)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return parse_simple_yaml(path)
    return data if isinstance(data, dict) else {}


def nested_dict(data: dict[str, Any], path: list[str]) -> dict[str, Any]:
    cursor: Any = data
    for key in path:
        if not isinstance(cursor, dict):
            return {}
        cursor = cursor.get(key)
    return cursor if isinstance(cursor, dict) else {}


def hermes_ark_config() -> dict[str, Any]:
    config = load_yaml(Path.home() / ".hermes/config.yaml")
    return nested_dict(config, ["plugins", "entries", "ark"])


def hermes_tts_config(ark_config: dict[str, Any]) -> dict[str, Any]:
    value = ark_config.get("text_to_speech")
    return value if isinstance(value, dict) else {}


def api_key_value() -> str:
    return env_value("ARK_AGENT_PLAN_API_KEY")


def option_value(configured: str | None, default: str) -> str:
    configured = resolve_secret(str(configured or ""))
    if configured:
        return configured
    return default


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


def subtitle_flag_for(resource_id: str, voice: str) -> str:
    if "2.0" in resource_id or "_uranus_" in voice or voice.startswith("S_"):
        return "enable_subtitle"
    return "enable_timestamp"


def build_payload(
    text: str,
    voice: str,
    fmt: str,
    sample_rate: int,
    language: str,
    subtitle_flag: str,
) -> dict[str, Any]:
    additions: dict[str, Any] = {
        "disable_markdown_filter": True,
        subtitle_flag: True,
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
                subtitle_flag: True,
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


def main() -> int:
    ark_config = hermes_ark_config()
    tts_config = hermes_tts_config(ark_config)

    parser = argparse.ArgumentParser(description="Generate speech with Volcengine Ark TTS")
    parser.add_argument("text", help="Text to synthesize")
    parser.add_argument("--output", help="Output audio path")
    parser.add_argument("--voice", default=option_value(str(tts_config.get("voice") or ""), DEFAULT_VOICE))
    parser.add_argument("--format", default=option_value(str(tts_config.get("output_format") or ""), "mp3"))
    parser.add_argument("--sample-rate", type=int, default=int(option_value(str(tts_config.get("sample_rate") or ""), "24000")))
    parser.add_argument("--language", default=option_value(str(tts_config.get("language") or ""), "auto"))
    parser.add_argument("--resource-id", default=option_value(str(tts_config.get("resource_id") or ""), DEFAULT_RESOURCE_ID))
    parser.add_argument("--base-url", default=option_value(str(tts_config.get("base_url") or ""), DEFAULT_BASE_URL))
    parser.add_argument("--timeout", type=float, default=float(option_value(str(tts_config.get("timeout_seconds") or ""), "120")))
    parser.add_argument("--max-chars", type=int, default=int(option_value(str(tts_config.get("max_text_length") or ""), "4000")))
    args = parser.parse_args()

    api_key = api_key_value()
    if not api_key:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "Missing ARK_AGENT_PLAN_API_KEY",
                    "env": "ARK_AGENT_PLAN_API_KEY",
                    "env_files": [".env", "~/.hermes/.env"],
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2

    import requests

    fmt = args.format.lower().strip(".")
    output_path = Path(args.output).expanduser() if args.output else default_output(fmt)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = args.text[: args.max_chars]
    subtitle_flag = subtitle_flag_for(args.resource_id, args.voice)

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
            json=build_payload(
                text,
                args.voice,
                fmt,
                args.sample_rate,
                args.language,
                subtitle_flag,
            ),
            stream=True,
            timeout=max(args.timeout, 120),
        )
        if response.status_code >= 400:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:500]}")
        audio, transcript = parse_stream(response)
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
            "local_path": str(output_path),
            "transcript_path": str(transcript_path) if transcript else None,
            "transcript_segments": len(transcript),
            "format": fmt,
            "bytes": len(audio),
            "speaker": args.voice,
            "sample_rate": args.sample_rate,
            "resource_id": args.resource_id,
            "subtitle_flag": subtitle_flag,
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
