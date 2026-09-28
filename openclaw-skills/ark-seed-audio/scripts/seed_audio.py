#!/usr/bin/env python3
"""Generate speech, sound effects, or a full audio scene with Seed Audio 1.0."""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request
import uuid


ENDPOINT = "https://openspeech.bytedance.com/api/v3/tts/create"
MODEL = "seed-audio-1.0"
FORMATS = ("mp3", "wav", "pcm", "ogg_opus")
SAMPLE_RATES = (8000, 16000, 24000, 32000, 44100, 48000)
SUFFIXES = {"ogg_opus": ".ogg", "pcm": ".pcm"}
PRESETS_PATH = Path(__file__).resolve().parent.parent / "references/preset-voices.json"


def list_voices(query: str = "") -> list[dict[str, str]]:
    voices = json.loads(PRESETS_PATH.read_text(encoding="utf-8"))["voices"]
    query = query.casefold()
    return [voice for voice in voices if query in voice["name"].casefold() or query in voice["id"].casefold() or query in voice["scenario"].casefold()]


def get_api_key() -> str:
    key = os.environ.get("ARK_SEED_AUDIO_API_KEY", "").strip()
    if not key:
        raise ValueError("missing ARK_SEED_AUDIO_API_KEY")
    return key


def build_payload(prompt: str, voices: list[str], audio_format: str, sample_rate: int) -> dict:
    if not prompt.strip():
        raise ValueError("prompt is empty")
    if len(voices) > 3:
        raise ValueError("at most 3 preset voices are supported")
    presets = {voice["id"] for voice in list_voices()}
    for voice in voices:
        if voice not in presets:
            raise ValueError(f"unknown preset voice ID: {voice}; see references/preset-voices.json")
    labels = {int(index) for index in re.findall(r"@(?:音频|Audio)([1-9]\d*)", prompt)}
    expected = set(range(1, len(voices) + 1))
    if labels - expected or (len(voices) > 1 and labels != expected):
        raise ValueError(f"prompt voice labels must match the {len(voices)} --voice values as @音频1...@音频{len(voices)}")
    payload = {
        "model": MODEL,
        "text_prompt": prompt,
        "audio_config": {"format": audio_format, "sample_rate": sample_rate, "enable_subtitle": True},
    }
    if voices:
        payload["references"] = [{"speaker": voice} for voice in voices]
    return payload


def generate(payload: dict, key: str, timeout: int) -> dict:
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Api-Key": key, "X-Api-Request-Id": str(uuid.uuid4())},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read(4000).decode("utf-8", "replace").replace(key, "[REDACTED]")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("provider returned a non-object response")
    if data.get("code") not in (None, 0):
        raise RuntimeError(f"provider code {data['code']}: {data.get('message', '')}")
    if not data.get("audio"):
        raise RuntimeError(f"provider returned no audio: {data.get('message', '')}")
    return data


def save_result(data: dict, output: Path, audio_format: str, sample_rate: int) -> dict:
    try:
        audio = base64.b64decode(data["audio"], validate=True)
    except (ValueError, binascii.Error) as exc:
        raise RuntimeError("provider returned invalid Base64 audio") from exc
    if not audio:
        raise RuntimeError("provider returned empty audio")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    try:
        temporary.write_bytes(audio)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    subtitle_path = None
    if data.get("subtitle") is not None:
        subtitle_path = output.with_suffix(".subtitle.json")
        subtitle_path.write_text(json.dumps(data["subtitle"], ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "success": True,
        "model": MODEL,
        "local_path": str(output.resolve()),
        "subtitle_path": str(subtitle_path.resolve()) if subtitle_path else None,
        "duration": data.get("duration"),
        "original_duration": data.get("original_duration"),
        "format": audio_format,
        "sample_rate": sample_rate,
        "bytes": len(audio),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    prompt_input = parser.add_mutually_exclusive_group()
    prompt_input.add_argument("prompt", nargs="?", help="Scene or sound-effect description")
    prompt_input.add_argument("--prompt-file", type=Path, help="UTF-8 file containing the prompt")
    parser.add_argument("--list-voices", nargs="?", const="", metavar="QUERY", help="List preset names and IDs; optionally filter by name, ID, or scene")
    parser.add_argument("--voice", action="append", default=[], metavar="VOICE_ID", help="Repeat preset voice IDs in @音频N order")
    parser.add_argument("--output", type=Path, help="Local output path")
    parser.add_argument("--format", choices=FORMATS, default="mp3")
    parser.add_argument("--sample-rate", type=int, choices=SAMPLE_RATES, default=48000)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args(argv)
    try:
        if args.list_voices is not None:
            if args.prompt or args.prompt_file:
                raise ValueError("--list-voices cannot be combined with a generation prompt")
            print(json.dumps({"voices": list_voices(args.list_voices)}, ensure_ascii=False))
            return 0
        if args.prompt is None and args.prompt_file is None:
            parser.error("a prompt or --prompt-file is required for generation")
        if args.timeout <= 0:
            raise ValueError("--timeout must be positive")
        prompt = args.prompt_file.read_text(encoding="utf-8") if args.prompt_file else args.prompt
        payload = build_payload(prompt, args.voice, args.format, args.sample_rate)
        key = get_api_key()
        output = args.output or Path.home() / "Documents/agent-workspace/ark-seed-audio" / f"audio-{uuid.uuid4().hex[:12]}{SUFFIXES.get(args.format, '.' + args.format)}"
        data = generate(payload, key, args.timeout)
        result = save_result(data, output.expanduser(), args.format, args.sample_rate)
        result["voices"] = args.voice
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, urllib.error.URLError) as exc:
        secret = os.environ.get("ARK_SEED_AUDIO_API_KEY") or "\0"
        print(json.dumps({"success": False, "error": str(exc).replace(secret, "[REDACTED]")}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
