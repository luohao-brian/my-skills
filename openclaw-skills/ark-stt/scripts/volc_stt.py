#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import io
import json
import math
import os
import sys
import threading
import time
import uuid
import wave
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
# Official binary protocol and streaming-input lifecycle:
# https://www.volcengine.com/docs/6561/1354869?lang=zh
# Agent Plan exposes the same protocol through the fixed /api/v3/plan route.
BASE_URL = "wss://openspeech.bytedance.com/api/v3/plan/sauc/bigmodel_nostream"
RESOURCE_ID = "volc.seedasr.sauc.duration"
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_SEG_DURATION_MS = 200
MIN_SEG_DURATION_MS = 100
MAX_SEG_DURATION_MS = 200
REQUEST_TIMEOUT_SECONDS = 180


def api_key_value() -> str:
    return os.getenv("ARK_AGENT_PLAN_API_KEY", "").strip()


def infer_format(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    if ext in {"wav", "pcm", "mp3"}:
        return ext
    if ext in {"ogg", "opus"}:
        return "ogg"
    return "mp3"


def infer_codec(audio_format: str) -> str:
    return "raw" if audio_format in {"wav", "pcm", "mp3"} else "opus"


def wav_duration_ms(data: bytes) -> float:
    try:
        with wave.open(io.BytesIO(data), "rb") as wav_file:
            frame_rate = wav_file.getframerate()
            if frame_rate != DEFAULT_SAMPLE_RATE:
                raise ValueError(f"WAV sample rate must be {DEFAULT_SAMPLE_RATE} Hz")
            if wav_file.getnchannels() != 1:
                raise ValueError("WAV audio must be mono")
            if wav_file.getsampwidth() != 2:
                raise ValueError("WAV audio must use signed 16-bit samples")
            if wav_file.getcomptype() != "NONE":
                raise ValueError("WAV audio must use uncompressed PCM")
            return wav_file.getnframes() * 1000 / frame_rate
    except (EOFError, wave.Error) as exc:
        raise ValueError(f"invalid WAV audio: {exc}") from exc


def mp3_frame_spans(data: bytes) -> list[tuple[int, int, float]]:
    """Return MPEG Layer III frame spans after validating the 16 kHz contract."""
    mpeg1_bitrates = (0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320)
    mpeg2_bitrates = (0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160)
    base_sample_rates = (44100, 48000, 32000)
    cursor = 0
    if data.startswith(b"ID3") and len(data) >= 10:
        tag_size = sum((data[6 + index] & 0x7F) << (21 - 7 * index) for index in range(4))
        footer_size = 10 if data[5] & 0x10 else 0
        cursor = min(len(data), 10 + tag_size + footer_size)

    spans: list[tuple[int, int, float]] = []
    while cursor + 4 <= len(data):
        value = int.from_bytes(data[cursor: cursor + 4], "big")
        version_id = (value >> 19) & 0x03
        layer_id = (value >> 17) & 0x03
        bitrate_index = (value >> 12) & 0x0F
        sample_rate_index = (value >> 10) & 0x03
        if (
            value & 0xFFE00000 != 0xFFE00000
            or version_id == 1
            or layer_id != 1
            or bitrate_index in {0, 15}
            or sample_rate_index == 3
        ):
            cursor += 1
            continue

        bitrate_table = mpeg1_bitrates if version_id == 3 else mpeg2_bitrates
        bitrate = bitrate_table[bitrate_index] * 1000
        sample_rate = base_sample_rates[sample_rate_index]
        if version_id == 2:
            sample_rate //= 2
        elif version_id == 0:
            sample_rate //= 4
        padding = (value >> 9) & 0x01
        samples_per_frame = 1152 if version_id == 3 else 576
        frame_size = ((144 if version_id == 3 else 72) * bitrate // sample_rate) + padding
        if frame_size <= 4 or cursor + frame_size > len(data):
            cursor += 1
            continue
        if sample_rate != DEFAULT_SAMPLE_RATE:
            raise ValueError(f"MP3 sample rate must be {DEFAULT_SAMPLE_RATE} Hz")
        frame_end = cursor + frame_size
        spans.append((cursor, frame_end, samples_per_frame * 1000 / sample_rate))
        cursor += frame_size

    if not spans:
        raise ValueError("invalid MP3 audio: no MPEG Layer III frames found")
    return spans


def mp3_duration_ms(data: bytes) -> float:
    """Calculate MP3 duration from validated MPEG Layer III frame headers."""
    return sum(duration_ms for _, _, duration_ms in mp3_frame_spans(data))


def ogg_opus_page_spans(data: bytes) -> list[tuple[int, int, float]]:
    """Return Ogg page spans with durations derived from Opus granule positions."""
    opus_head = data.find(b"OpusHead")
    if opus_head < 0 or opus_head + 12 > len(data):
        raise ValueError("invalid Ogg Opus audio: OpusHead not found")
    pre_skip = int.from_bytes(data[opus_head + 10: opus_head + 12], "little")
    cursor = 0
    previous_samples = 0
    spans: list[tuple[int, int, float]] = []
    while cursor + 27 <= len(data):
        if data[cursor: cursor + 4] != b"OggS":
            cursor += 1
            continue
        segment_count = data[cursor + 26]
        header_end = cursor + 27 + segment_count
        if header_end > len(data):
            break
        body_size = sum(data[cursor + 27: header_end])
        page_end = header_end + body_size
        if page_end > len(data):
            break
        granule = int.from_bytes(data[cursor + 6: cursor + 14], "little")
        duration_ms = 0.0
        if granule != 0xFFFFFFFFFFFFFFFF:
            effective_samples = max(0, granule - pre_skip)
            if effective_samples >= previous_samples:
                duration_ms = (effective_samples - previous_samples) * 1000 / 48000
                previous_samples = effective_samples
        spans.append((cursor, page_end, duration_ms))
        cursor = page_end
    if not spans or previous_samples <= 0:
        raise ValueError("invalid Ogg Opus audio: final granule position not found")
    return spans


def ogg_opus_duration_ms(data: bytes) -> float:
    return sum(duration_ms for _, _, duration_ms in ogg_opus_page_spans(data))


def validate_audio_options(audio_format: str, codec: str, sample_rate: int) -> None:
    if sample_rate != DEFAULT_SAMPLE_RATE:
        raise ValueError(f"sample rate must be {DEFAULT_SAMPLE_RATE} Hz")
    expected_codec = infer_codec(audio_format)
    if codec != expected_codec:
        raise ValueError(f"{audio_format} audio requires codec {expected_codec}")


def audio_duration_ms(data: bytes, *, audio_format: str, sample_rate: int) -> float:
    normalized_format = audio_format.lower()
    if normalized_format == "pcm":
        if sample_rate != DEFAULT_SAMPLE_RATE:
            raise ValueError(f"PCM sample rate must be {DEFAULT_SAMPLE_RATE} Hz")
        if len(data) % 2:
            raise ValueError("PCM audio must contain complete signed 16-bit samples")
        # The request contract fixes raw PCM at signed 16-bit mono.
        return len(data) * 1000 / (sample_rate * 2)
    if normalized_format == "wav":
        return wav_duration_ms(data)
    if normalized_format == "mp3":
        return mp3_duration_ms(data)
    if normalized_format == "ogg":
        return ogg_opus_duration_ms(data)
    raise ValueError(f"unsupported audio format for duration-aware streaming: {audio_format}")


def group_timed_spans(
    data: bytes,
    spans: list[tuple[int, int, float]],
    *,
    target_duration_ms: int,
) -> tuple[list[bytes], list[float]]:
    """Group complete MP3 frames or Ogg pages without byte-proportional guessing."""
    chunks: list[bytes] = []
    durations: list[float] = []
    group_start = 0
    group_duration = 0.0

    for span_start, _span_end, span_duration in spans:
        if span_duration > MAX_SEG_DURATION_MS:
            raise ValueError(
                f"encoded audio unit is {span_duration:.1f} ms; remux it into pages no longer than "
                f"{MAX_SEG_DURATION_MS} ms"
            )
        projected_duration = group_duration + span_duration
        if group_duration > 0 and (
            projected_duration > MAX_SEG_DURATION_MS
            or (
                group_duration >= MIN_SEG_DURATION_MS
                and projected_duration > target_duration_ms
            )
        ):
            chunks.append(data[group_start:span_start])
            durations.append(group_duration)
            group_start = span_start
            group_duration = 0.0
        group_duration += span_duration

    if group_duration <= 0:
        raise ValueError("audio duration must be positive")
    chunks.append(data[group_start:])
    durations.append(group_duration)

    if (
        len(chunks) > 1
        and durations[-1] < MIN_SEG_DURATION_MS
        and durations[-2] + durations[-1] <= MAX_SEG_DURATION_MS
    ):
        chunks[-2] += chunks[-1]
        durations[-2] += durations[-1]
        chunks.pop()
        durations.pop()

    return chunks, durations


def chunk_audio(
    data: bytes,
    *,
    audio_format: str,
    sample_rate: int,
    segment_duration_ms: int = DEFAULT_SEG_DURATION_MS,
) -> tuple[list[bytes], list[float]]:
    if not MIN_SEG_DURATION_MS <= segment_duration_ms <= MAX_SEG_DURATION_MS:
        raise ValueError(
            f"segment duration must be {MIN_SEG_DURATION_MS}-{MAX_SEG_DURATION_MS} ms"
        )
    normalized_format = audio_format.lower()
    if normalized_format == "mp3":
        return group_timed_spans(
            data,
            mp3_frame_spans(data),
            target_duration_ms=segment_duration_ms,
        )
    if normalized_format == "ogg":
        return group_timed_spans(
            data,
            ogg_opus_page_spans(data),
            target_duration_ms=segment_duration_ms,
        )

    duration_ms = audio_duration_ms(data, audio_format=normalized_format, sample_rate=sample_rate)
    if duration_ms <= 0:
        raise ValueError("audio duration must be positive")
    segment_count = max(1, math.ceil(duration_ms / segment_duration_ms))
    boundaries = [len(data) * index // segment_count for index in range(segment_count + 1)]
    if normalized_format == "pcm":
        boundaries = [boundary - (boundary % 2) for boundary in boundaries]
        boundaries[-1] = len(data)
    chunks = [data[boundaries[index]:boundaries[index + 1]] for index in range(segment_count)]
    packet_duration_ms = duration_ms / segment_count
    return chunks, [packet_duration_ms] * segment_count


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


def transcribe_stream(
    ws: Any,
    data: bytes,
    *,
    audio_format: str,
    codec: str,
    sample_rate: int,
    segment_duration_ms: int = DEFAULT_SEG_DURATION_MS,
    timeout_seconds: float = REQUEST_TIMEOUT_SECONDS,
) -> tuple[str, dict[str, Any] | None]:
    validate_audio_options(audio_format, codec, sample_rate)
    chunks, packet_durations_ms = chunk_audio(
        data,
        audio_format=audio_format,
        sample_rate=sample_rate,
        segment_duration_ms=segment_duration_ms,
    )

    seq = 1
    ws.send_binary(full_request(seq, audio_format, codec, sample_rate))
    seq += 1
    response = parse_response(ws.recv())
    if response["code"] != 0:
        raise RuntimeError(f"ASR full request failed: {response}")

    final_text = ""
    final_payload: dict[str, Any] | None = None
    receiver_error: list[Exception] = []
    receiver_ready = threading.Event()
    receiver_done = threading.Event()

    def receive_responses() -> None:
        nonlocal final_text, final_payload
        receiver_ready.set()
        try:
            while True:
                raw = ws.recv()
                if not raw:
                    raise RuntimeError("ASR WebSocket closed before the final response")
                streamed = parse_response(raw)
                if streamed["code"] != 0:
                    raise RuntimeError(f"ASR stream failed: {streamed}")
                payload = streamed["payload"]
                if payload:
                    final_payload = payload
                    text = payload.get("result", {}).get("text")
                    if text:
                        final_text = text
                if streamed["is_last_package"]:
                    return
        except Exception as exc:
            receiver_error.append(exc)
        finally:
            receiver_done.set()

    # The service can send results while audio is still arriving. Keeping one
    # reader active prevents provider frames from backing up until the socket is
    # reset, which is what happens when the whole file is sent before recv().
    receiver = threading.Thread(target=receive_responses, name="ark-stt-receiver", daemon=True)
    receiver.start()
    if not receiver_ready.wait(timeout=1):
        raise RuntimeError("ASR receiver did not start")

    for index, chunk in enumerate(chunks):
        if receiver_error:
            raise receiver_error[0]
        is_last = index + 1 == len(chunks)
        ws.send_binary(audio_request(seq, chunk, is_last))
        if not is_last:
            seq += 1
            time.sleep(packet_durations_ms[index] / 1000)

    if not receiver_done.wait(timeout=timeout_seconds):
        raise TimeoutError("ASR timed out waiting for the final response")
    receiver.join(timeout=1)
    if receiver_error:
        raise receiver_error[0]
    if not final_text:
        raise RuntimeError("ASR finished without returning final text")
    return final_text, final_payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Transcribe local audio with Ark Agent Plan STT")
    parser.add_argument("audio_path")
    parser.add_argument("--format", choices=["wav", "pcm", "mp3", "ogg", "opus"])
    parser.add_argument("--codec", choices=["raw", "opus"])
    parser.add_argument("--sample-rate", type=int, choices=[DEFAULT_SAMPLE_RATE], default=DEFAULT_SAMPLE_RATE)
    parser.add_argument("--raw", action="store_true", help="Include the final provider payload")
    args = parser.parse_args()

    api_key = api_key_value()
    if not api_key:
        print(json.dumps({"success": False, "error": "Missing ARK_AGENT_PLAN_API_KEY"}, ensure_ascii=False), file=sys.stderr)
        return 2

    import websocket

    audio_path = Path(args.audio_path).expanduser()
    data = audio_path.read_bytes()
    if not data:
        print(json.dumps({"success": False, "error": f"Audio file is empty: {audio_path}"}, ensure_ascii=False), file=sys.stderr)
        return 2

    audio_format = (args.format or infer_format(audio_path)).lower()
    if audio_format == "opus":
        audio_format = "ogg"
    codec = (args.codec or infer_codec(audio_format)).lower()
    headers = [
        f"X-Api-Resource-Id: {RESOURCE_ID}",
        f"X-Api-Connect-Id: {uuid.uuid4()}",
        f"X-Api-Key: {api_key}",
    ]
    ws = None
    try:
        validate_audio_options(audio_format, codec, args.sample_rate)
        audio_duration_ms(data, audio_format=audio_format, sample_rate=args.sample_rate)
        ws = websocket.create_connection(BASE_URL, header=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        final_text, final_payload = transcribe_stream(
            ws,
            data,
            audio_format=audio_format,
            codec=codec,
            sample_rate=args.sample_rate,
        )
        result = {
            "success": True,
            "type": "transcript",
            "audio_path": str(audio_path),
            "transcript": final_text,
            "duration_ms": (final_payload or {}).get("audio_info", {}).get("duration"),
            "resource_id": RESOURCE_ID,
        }
        if args.raw:
            result["raw"] = final_payload
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"success": False, "error": str(exc), "audio_path": str(audio_path)}, ensure_ascii=False), file=sys.stderr)
        return 1
    finally:
        if ws is not None:
            ws.close()


if __name__ == "__main__":
    raise SystemExit(main())
