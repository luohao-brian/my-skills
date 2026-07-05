"""Ark implementation for Hermes `transcribe_audio`."""

from __future__ import annotations

import gzip
import json
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from agent.transcription_provider import TranscriptionProvider

ASR_PROTOCOL_VERSION_V1 = 0b0001
ASR_CLIENT_FULL_REQUEST = 0b0001
ASR_CLIENT_AUDIO_ONLY_REQUEST = 0b0010
ASR_SERVER_FULL_RESPONSE = 0b1001
ASR_SERVER_ERROR_RESPONSE = 0b1111
ASR_FLAG_POS_SEQUENCE = 0b0001
ASR_FLAG_NEG_WITH_SEQUENCE = 0b0011
ASR_SERIALIZATION_JSON = 0b0001
ASR_COMPRESSION_GZIP = 0b0001
ASR_DEFAULT_SAMPLE_RATE = 24000
ASR_DEFAULT_BITS = 16
ASR_DEFAULT_CHANNELS = 1


def _infer_audio_format(file_path: str) -> str:
    ext = Path(file_path).suffix.lower().lstrip(".")
    if ext in {"wav", "pcm", "mp3"}:
        return ext
    if ext in {"ogg", "opus"}:
        return "ogg"
    return "mp3"


def _infer_codec(audio_format: str) -> str:
    return "raw" if audio_format in {"wav", "pcm", "mp3"} else "opus"


def _build_asr_header(message_type: int, flags: int) -> bytes:
    return bytes(
        [
            (ASR_PROTOCOL_VERSION_V1 << 4) | 0x01,
            (message_type << 4) | flags,
            (ASR_SERIALIZATION_JSON << 4) | ASR_COMPRESSION_GZIP,
            0x00,
        ]
    )


def _build_full_asr_request(seq: int, audio_format: str, codec: str) -> bytes:
    payload = {
        "user": {"uid": "hermes-ark-plugin"},
        "audio": {
            "format": audio_format,
            "codec": codec,
            "rate": ASR_DEFAULT_SAMPLE_RATE,
            "bits": ASR_DEFAULT_BITS,
            "channel": ASR_DEFAULT_CHANNELS,
        },
        "request": {
            "model_name": "bigmodel",
            "enable_itn": True,
            "enable_punc": True,
        },
    }
    compressed = gzip.compress(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    return (
        _build_asr_header(ASR_CLIENT_FULL_REQUEST, ASR_FLAG_POS_SEQUENCE)
        + seq.to_bytes(4, "big", signed=True)
        + len(compressed).to_bytes(4, "big")
        + compressed
    )


def _build_audio_asr_request(seq: int, chunk: bytes, is_last: bool) -> bytes:
    flags = ASR_FLAG_NEG_WITH_SEQUENCE if is_last else ASR_FLAG_POS_SEQUENCE
    sequence = -seq if is_last else seq
    compressed = gzip.compress(chunk)
    return (
        _build_asr_header(ASR_CLIENT_AUDIO_ONLY_REQUEST, flags)
        + sequence.to_bytes(4, "big", signed=True)
        + len(compressed).to_bytes(4, "big")
        + compressed
    )


def _parse_asr_payload(payload: bytes) -> dict[str, Any] | None:
    if not payload:
        return None
    try:
        payload = gzip.decompress(payload)
    except OSError:
        pass
    return json.loads(payload.decode("utf-8"))


def _parse_asr_response(message: bytes) -> dict[str, Any]:
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
    if message_type == ASR_SERVER_FULL_RESPONSE:
        payload_size = int.from_bytes(message[cursor : cursor + 4], "big")
        cursor += 4
    elif message_type == ASR_SERVER_ERROR_RESPONSE:
        code = int.from_bytes(message[cursor : cursor + 4], "big", signed=True)
        cursor += 4
        payload_size = int.from_bytes(message[cursor : cursor + 4], "big")
        cursor += 4

    payload = message[cursor : cursor + payload_size] if payload_size is not None else message[cursor:]
    return {"code": code, "is_last_package": is_last_package, "payload": _parse_asr_payload(payload) if payload else None}


class ArkTranscribeAudioProvider(TranscriptionProvider):
    @property
    def name(self) -> str:
        return "ark"

    @property
    def display_name(self) -> str:
        return "Volcengine Ark"

    def is_available(self) -> bool:
        from ..common.config import api_key

        try:
            import websocket  # noqa: F401
        except Exception:
            return False
        return bool(api_key())

    def transcribe(
        self,
        file_path: str,
        *,
        model: Optional[str] = None,
        language: Optional[str] = None,
        **extra: Any,
    ) -> dict[str, Any]:
        from ..common.config import section, section_api_key, timeout_seconds

        try:
            import websocket

            cfg = section("transcribe_audio")
            api_key = section_api_key("transcribe_audio")
            if not api_key:
                raise RuntimeError("Ark STT API key is not configured")
            audio_path = Path(file_path).expanduser()
            audio_data = audio_path.read_bytes()
            if not audio_data:
                raise RuntimeError(f"audio file is empty: {audio_path}")

            audio_format = _infer_audio_format(str(audio_path))
            codec = _infer_codec(audio_format)
            headers = [
                f"X-Api-Resource-Id: {cfg.get('resource_id') or 'volc.seedasr.sauc.duration'}",
                f"X-Api-Connect-Id: {uuid.uuid4()}",
                f"X-Api-Key: {api_key}",
            ]
            ws = websocket.create_connection(
                str(cfg.get("base_url") or "wss://openspeech.bytedance.com/api/v3/plan/sauc/bigmodel_nostream"),
                header=headers,
                timeout=max(timeout_seconds("transcribe_audio", 180), 120),
            )
            try:
                seq = 1
                ws.send_binary(_build_full_asr_request(seq, audio_format, codec))
                seq += 1
                response = _parse_asr_response(ws.recv())
                if response["code"] != 0:
                    raise RuntimeError(f"ASR full request failed: {response}")

                segment_count = max(10, len(audio_data) // 6400)
                segment_size = max(1, len(audio_data) // segment_count)
                chunks = [audio_data[i : i + segment_size] for i in range(0, len(audio_data), segment_size)]
                for index, chunk in enumerate(chunks):
                    is_last = index + 1 == len(chunks)
                    ws.send_binary(_build_audio_asr_request(seq, chunk, is_last))
                    if not is_last:
                        seq += 1
                    time.sleep(0.2)

                final_text = ""
                final_payload = None
                while True:
                    raw = ws.recv()
                    if not raw:
                        break
                    response = _parse_asr_response(raw)
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
            finally:
                ws.close()

            if not final_text:
                raise RuntimeError("ASR finished without returning final text")
            return {
                "success": True,
                "transcript": final_text,
                "provider": self.name,
                "payload": final_payload,
            }
        except Exception as exc:
            return {
                "success": False,
                "transcript": "",
                "provider": self.name,
                "error": str(exc),
            }
