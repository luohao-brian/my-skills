"""Ark BigASR provider for Hermes' native transcription dispatcher."""

from __future__ import annotations

import gzip
import json
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from agent.transcription_provider import TranscriptionProvider

PROTOCOL_VERSION = 0b0001
CLIENT_FULL_REQUEST = 0b0001
CLIENT_AUDIO_ONLY_REQUEST = 0b0010
SERVER_FULL_RESPONSE = 0b1001
SERVER_ERROR_RESPONSE = 0b1111
FLAG_POS_SEQUENCE = 0b0001
FLAG_NEG_WITH_SEQUENCE = 0b0011
SERIALIZATION_JSON = 0b0001
COMPRESSION_GZIP = 0b0001
SAMPLE_RATE = 16000
PACKET_DURATION_MS = 200
PACKET_BYTES = SAMPLE_RATE * 2 * PACKET_DURATION_MS // 1000


def _header(message_type: int, flags: int) -> bytes:
    return bytes([
        (PROTOCOL_VERSION << 4) | 0x01,
        (message_type << 4) | flags,
        (SERIALIZATION_JSON << 4) | COMPRESSION_GZIP,
        0,
    ])


def _full_request(seq: int) -> bytes:
    payload = {
        "user": {"uid": "hermes-ark-plugin"},
        "audio": {"format": "pcm", "codec": "raw", "rate": SAMPLE_RATE, "bits": 16, "channel": 1},
        "request": {"model_name": "bigmodel", "enable_itn": True, "enable_punc": True},
    }
    compressed = gzip.compress(json.dumps(payload, ensure_ascii=False).encode())
    return _header(CLIENT_FULL_REQUEST, FLAG_POS_SEQUENCE) + seq.to_bytes(4, "big", signed=True) + len(compressed).to_bytes(4, "big") + compressed


def _audio_request(seq: int, chunk: bytes, is_last: bool) -> bytes:
    flags = FLAG_NEG_WITH_SEQUENCE if is_last else FLAG_POS_SEQUENCE
    sequence = -seq if is_last else seq
    compressed = gzip.compress(chunk)
    return _header(CLIENT_AUDIO_ONLY_REQUEST, flags) + sequence.to_bytes(4, "big", signed=True) + len(compressed).to_bytes(4, "big") + compressed


def _parse_payload(payload: bytes) -> dict[str, Any] | None:
    if not payload:
        return None
    try:
        payload = gzip.decompress(payload)
    except OSError:
        pass
    return json.loads(payload.decode("utf-8"))


def _parse_response(message: bytes) -> dict[str, Any]:
    if len(message) < 4:
        raise ValueError("invalid ASR response")
    header_size = (message[0] & 0x0F) * 4
    message_type = message[1] >> 4
    flags = message[1] & 0x0F
    cursor = header_size + (4 if flags & 0x01 else 0)
    code = 0
    payload_size = None
    if message_type == SERVER_FULL_RESPONSE:
        payload_size = int.from_bytes(message[cursor:cursor + 4], "big")
        cursor += 4
    elif message_type == SERVER_ERROR_RESPONSE:
        code = int.from_bytes(message[cursor:cursor + 4], "big", signed=True)
        cursor += 4
        payload_size = int.from_bytes(message[cursor:cursor + 4], "big")
        cursor += 4
    payload = message[cursor:cursor + payload_size] if payload_size is not None else message[cursor:]
    return {"code": code, "is_last_package": bool(flags & 0x02), "payload": _parse_payload(payload)}


def _to_pcm(file_path: str) -> bytes:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to normalize audio to 16 kHz mono PCM for Ark STT")
    completed = subprocess.run(
        [ffmpeg, "-v", "error", "-i", str(Path(file_path).expanduser()), "-f", "s16le", "-ac", "1", "-ar", str(SAMPLE_RATE), "pipe:1"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
    )
    if not completed.stdout:
        raise RuntimeError("audio normalization produced no PCM samples")
    return completed.stdout


def _transcribe_stream(ws: Any, pcm: bytes, timeout: float) -> tuple[str, dict[str, Any] | None]:
    seq = 1
    ws.send_binary(_full_request(seq))
    seq += 1
    first = _parse_response(ws.recv())
    if first["code"] != 0:
        raise RuntimeError(f"ASR full request failed: {first}")
    final_text = ""
    final_payload: dict[str, Any] | None = None
    receiver_error: list[Exception] = []
    done = threading.Event()

    def receive() -> None:
        nonlocal final_text, final_payload
        try:
            while True:
                response = _parse_response(ws.recv())
                if response["code"] != 0:
                    raise RuntimeError(f"ASR stream failed: {response}")
                payload = response["payload"]
                if payload:
                    final_payload = payload
                    text = payload.get("result", {}).get("text")
                    if text:
                        final_text = text
                if response["is_last_package"]:
                    return
        except Exception as exc:
            receiver_error.append(exc)
        finally:
            done.set()

    thread = threading.Thread(target=receive, name="ark-stt-receiver", daemon=True)
    thread.start()
    chunks = [pcm[index:index + PACKET_BYTES] for index in range(0, len(pcm), PACKET_BYTES)]
    for index, chunk in enumerate(chunks):
        if receiver_error:
            raise receiver_error[0]
        is_last = index + 1 == len(chunks)
        ws.send_binary(_audio_request(seq, chunk, is_last))
        if not is_last:
            seq += 1
            time.sleep(PACKET_DURATION_MS / 1000)
    if not done.wait(timeout):
        raise TimeoutError("ASR timed out waiting for the final response")
    if receiver_error:
        raise receiver_error[0]
    if not final_text:
        raise RuntimeError("ASR finished without returning final text")
    return final_text, final_payload


class ArkTranscribeAudioProvider(TranscriptionProvider):
    @property
    def name(self) -> str:
        return "ark"

    @property
    def display_name(self) -> str:
        return "Volcengine Ark"

    def is_available(self) -> bool:
        from ..common.config import section_api_key
        try:
            import websocket  # noqa: F401
        except Exception:
            return False
        return bool(section_api_key("transcribe_audio", speech=True)) and bool(shutil.which("ffmpeg"))

    def transcribe(
        self,
        file_path: str,
        *,
        model: Optional[str] = None,
        language: Optional[str] = None,
        **extra: Any,
    ) -> dict[str, Any]:
        from ..common.config import section, section_api_key, speech_endpoint, timeout_seconds
        import websocket

        cfg = section("transcribe_audio")
        api_key = section_api_key("transcribe_audio", speech=True)
        if not api_key:
            raise RuntimeError("Ark STT credential is not configured for the selected backend")
        resource_id = str(cfg.get("resource_id") or "volc.seedasr.sauc.duration")
        request_id = str(uuid.uuid4())
        pcm = _to_pcm(file_path)
        timeout = max(timeout_seconds("transcribe_audio", 180), 120)
        ws = websocket.create_connection(
            speech_endpoint("transcribe_audio", "stt"),
            header=[
                f"X-Api-Resource-Id: {resource_id}",
                f"X-Api-Request-Id: {request_id}",
                "X-Api-Sequence: -1",
                f"X-Api-Key: {api_key}",
            ],
            timeout=timeout,
        )
        try:
            text, payload = _transcribe_stream(ws, pcm, timeout)
        finally:
            ws.close()
        return {
            "success": True,
            "transcript": text,
            "provider": self.name,
            "duration_ms": (payload or {}).get("audio_info", {}).get("duration"),
            "language": language,
            "provider_request_id": request_id,
        }
