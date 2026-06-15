#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = 0b0001
CLIENT_FULL_REQUEST = 0b0001
CLIENT_AUDIO_ONLY_REQUEST = 0b0010
SERVER_FULL_RESPONSE = 0b1001
SERVER_ERROR_RESPONSE = 0b1111
FLAG_POS_SEQUENCE = 0b0001
FLAG_NEG_WITH_SEQUENCE = 0b0011
SERIALIZATION_JSON = 0b0001
COMPRESSION_GZIP = 0b0001


def env_first(names: list[str]) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def infer_format(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    if ext in {"wav", "pcm", "mp3"}:
        return ext
    if ext in {"ogg", "opus"}:
        return "ogg"
    return "mp3"


def infer_codec(audio_format: str) -> str:
    return "raw" if audio_format in {"wav", "pcm", "mp3"} else "opus"


def header(message_type: int, flags: int) -> bytes:
    return bytes([
        (PROTOCOL_VERSION << 4) | 0x01,
        (message_type << 4) | flags,
        (SERIALIZATION_JSON << 4) | COMPRESSION_GZIP,
        0x00,
    ])


def full_request(seq: int, audio_format: str, codec: str, rate: int) -> bytes:
    payload = {
        "user": {"uid": "openclaw-stt"},
        "audio": {
            "format": audio_format,
            "codec": codec,
            "rate": rate,
            "bits": 16,
            "channel": 1,
        },
        "request": {
            "model_name": "bigmodel",
            "enable_itn": True,
            "enable_punc": True,
        },
    }
    compressed = gzip.compress(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    return header(CLIENT_FULL_REQUEST, FLAG_POS_SEQUENCE) + seq.to_bytes(4, "big", signed=True) + len(compressed).to_bytes(4, "big") + compressed


def audio_request(seq: int, chunk: bytes, is_last: bool) -> bytes:
    flags = FLAG_NEG_WITH_SEQUENCE if is_last else FLAG_POS_SEQUENCE
    sequence = -seq if is_last else seq
    compressed = gzip.compress(chunk)
    return header(CLIENT_AUDIO_ONLY_REQUEST, flags) + sequence.to_bytes(4, "big", signed=True) + len(compressed).to_bytes(4, "big") + compressed


def parse_payload(payload: bytes) -> dict[str, Any] | None:
    if not payload:
        return None
    try:
        payload = gzip.decompress(payload)
    except OSError:
        pass
    return json.loads(payload.decode("utf-8"))


def parse_response(message: bytes) -> dict[str, Any]:
    if len(message) < 4:
        raise ValueError("invalid ASR response")
    header_size = (message[0] & 0x0F) * 4
    message_type = message[1] >> 4
    flags = message[1] & 0x0F
    cursor = header_size
    is_last_package = bool(flags & 0x02)
    if flags & 0x01:
        cursor += 4
    code = 0
    payload_size = None
    if message_type == SERVER_FULL_RESPONSE:
        payload_size = int.from_bytes(message[cursor: cursor + 4], "big")
        cursor += 4
    elif message_type == SERVER_ERROR_RESPONSE:
        code = int.from_bytes(message[cursor: cursor + 4], "big", signed=True)
        cursor += 4
        payload_size = int.from_bytes(message[cursor: cursor + 4], "big")
        cursor += 4
    payload = message[cursor: cursor + payload_size] if payload_size is not None else message[cursor:]
    return {"code": code, "is_last_package": is_last_package, "payload": parse_payload(payload) if payload else None}


def main() -> int:
    parser = argparse.ArgumentParser(description="Transcribe local audio with Volcengine Ark STT")
    parser.add_argument("audio_path")
    parser.add_argument("--format")
    parser.add_argument("--codec")
    parser.add_argument("--sample-rate", type=int, default=int(os.getenv("VOLC_STT_SAMPLE_RATE", "24000")))
    parser.add_argument("--seg-duration-ms", type=int, default=int(os.getenv("VOLC_STT_SEG_DURATION_MS", "200")))
    parser.add_argument("--resource-id", default=os.getenv("VOLC_STT_RESOURCE_ID", "volc.seedasr.sauc.duration"))
    parser.add_argument("--base-url", default=os.getenv("VOLC_STT_BASE_URL", "wss://openspeech.bytedance.com/api/v3/plan/sauc/bigmodel_nostream"))
    parser.add_argument("--timeout", type=float, default=float(os.getenv("VOLC_STT_TIMEOUT", "180")))
    args = parser.parse_args()

    import websocket

    api_key = env_first(["VOLC_AGENT_PLAN_API_KEY", "ARK_API_KEY", "OPENAPI_API_KEY"])
    if not api_key:
        print(json.dumps({"success": False, "error": "Missing VOLC_AGENT_PLAN_API_KEY"}, ensure_ascii=False), file=sys.stderr)
        return 2

    audio_path = Path(args.audio_path).expanduser()
    data = audio_path.read_bytes()
    if not data:
        print(json.dumps({"success": False, "error": f"Audio file is empty: {audio_path}"}, ensure_ascii=False), file=sys.stderr)
        return 2

    audio_format = args.format or infer_format(audio_path)
    codec = args.codec or infer_codec(audio_format)
    headers = [
        f"X-Api-Resource-Id: {args.resource_id}",
        f"X-Api-Connect-Id: {uuid.uuid4()}",
        f"X-Api-Key: {api_key}",
    ]
    ws = None
    try:
        ws = websocket.create_connection(args.base_url, header=headers, timeout=max(args.timeout, 120))
        seq = 1
        ws.send_binary(full_request(seq, audio_format, codec, args.sample_rate))
        seq += 1
        response = parse_response(ws.recv())
        if response["code"] != 0:
            raise RuntimeError(f"ASR full request failed: {response}")

        segment_count = max(10, len(data) // 6400)
        segment_size = max(1, len(data) // segment_count)
        chunks = [data[i: i + segment_size] for i in range(0, len(data), segment_size)]
        for index, chunk in enumerate(chunks):
            is_last = index + 1 == len(chunks)
            ws.send_binary(audio_request(seq, chunk, is_last))
            if not is_last:
                seq += 1
            time.sleep(max(args.seg_duration_ms, 0) / 1000)

        final_text = ""
        final_payload = None
        while True:
            raw = ws.recv()
            if not raw:
                break
            response = parse_response(raw)
            if response["code"] != 0:
                raise RuntimeError(f"ASR stream failed: {response}")
            payload = response["payload"]
            if payload:
                final_payload = payload
                text = payload.get("result", {}).get("text")
                if text:
                    final_text = text
            if response["is_last_package"]:
                break
        if not final_text:
            raise RuntimeError("ASR finished without returning final text")
        print(json.dumps({
            "success": True,
            "type": "transcript",
            "audio_path": str(audio_path),
            "transcript": final_text,
            "resource_id": args.resource_id,
            "payload": final_payload,
        }, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"success": False, "error": str(exc), "audio_path": str(audio_path)}, ensure_ascii=False), file=sys.stderr)
        return 1
    finally:
        if ws is not None:
            ws.close()


if __name__ == "__main__":
    raise SystemExit(main())
