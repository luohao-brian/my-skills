from __future__ import annotations

import importlib.util
import json
import threading
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]


def load_script(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


IMAGE = load_script("ark_image_gen_protocol", "openclaw-skills/ark-image-gen/scripts/volc_image_gen.py")
VIDEO = load_script("ark_video_gen_protocol", "openclaw-skills/ark-video-gen/scripts/volc_video_gen.py")
STT = load_script("ark_stt_protocol", "openclaw-skills/ark-stt/scripts/volc_stt.py")
TTS = load_script("ark_tts_protocol", "openclaw-skills/ark-tts/scripts/volc_tts.py")
SEARCH = load_script("ark_search_protocol", "openclaw-skills/ark-search/scripts/web_search.py")


class ArkSkillProtocolTests(unittest.TestCase):
    def test_image_size_uses_provider_native_casing(self) -> None:
        self.assertEqual(IMAGE.normalize_size("2k"), "2K")
        self.assertEqual(IMAGE.normalize_size("4K"), "4K")
        self.assertEqual(IMAGE.normalize_size("4:3"), "2304x1728")
        self.assertEqual(IMAGE.normalize_size("3:2"), "2496x1664")
        self.assertEqual(IMAGE.normalize_size("21:9"), "3136x1344")

    def test_video_settings_and_terminal_states_match_task_contract(self) -> None:
        settings = VIDEO.build_generation_settings(
            resolution="720p",
            aspect_ratio="9:16",
            duration=15,
            generate_audio=True,
        )
        self.assertEqual(settings, {
            "generate_audio": True,
            "resolution": "720p",
            "ratio": "9:16",
            "duration": 15,
            "watermark": False,
        })
        self.assertEqual(VIDEO.TERMINAL_FAILURE_STATUSES, {"failed", "cancelled", "expired"})
        self.assertIn(-1, VIDEO.SUPPORTED_DURATIONS)
        self.assertNotIn(2, VIDEO.SUPPORTED_DURATIONS)
        self.assertEqual(VIDEO.SUPPORTED_RESOLUTIONS, ("480p", "720p"))

    def test_search_enforces_query_and_site_limits(self) -> None:
        sites = "|".join(f"{index}.example" for index in range(1, 21))
        body = SEARCH.build_body(
            "  current docs  ",
            sites=sites,
            block_hosts="one.example|two.example|three.example|four.example|five.example",
            query_rewrite=True,
        )
        self.assertEqual(body["Query"], "current docs")
        self.assertEqual(body["Filter"]["Sites"], sites)
        self.assertEqual(body["QueryControl"], {"QueryRewrite": True})
        self.assertNotIn("QueryRewrite", body["Filter"])
        self.assertNotIn("NeedSummary", body)
        with self.assertRaisesRegex(ValueError, "at most 20"):
            SEARCH.build_body("docs", sites=sites + "|21.example")
        with self.assertRaisesRegex(ValueError, "at most 5"):
            SEARCH.build_body(
                "docs",
                block_hosts="1.example|2.example|3.example|4.example|5.example|6.example",
            )
        with self.assertRaisesRegex(ValueError, "1 to 100"):
            SEARCH.build_body("x" * 101)

    def test_tts_payload_keeps_v3_subtitle_shape(self) -> None:
        payload = TTS.build_payload("hello", "voice-id", "mp3", 24000)
        params = payload["req_params"]
        self.assertEqual(params["speaker"], "voice-id")
        self.assertEqual(params["audio_params"]["format"], "mp3")
        self.assertTrue(params["audio_params"]["enable_subtitle"])
        self.assertNotIn("enable_subtitle", json.loads(params["additions"]))

    def test_stt_receives_while_audio_is_still_being_sent(self) -> None:
        class FakeWebSocket:
            def __init__(self) -> None:
                self.send_count = 0
                self.recv_count = 0
                self.receiver_waiting = threading.Event()
                self.audio_sent = threading.Event()

            def send_binary(self, _message: bytes) -> None:
                self.send_count += 1
                if self.send_count > 1:
                    if not self.receiver_waiting.wait(timeout=1):
                        raise AssertionError("audio was sent before the response reader started")
                    self.audio_sent.set()

            def recv(self) -> bytes:
                self.recv_count += 1
                if self.recv_count == 1:
                    return b"ack"
                self.receiver_waiting.set()
                if not self.audio_sent.wait(timeout=1):
                    raise AssertionError("response reader did not overlap audio sending")
                return b"final"

        def parse(raw: bytes):
            if raw == b"ack":
                return {"code": 0, "is_last_package": False, "payload": None}
            return {
                "code": 0,
                "is_last_package": True,
                "payload": {"result": {"text": "verified"}, "audio_info": {"duration": 1}},
            }

        ws = FakeWebSocket()
        with patch.object(STT, "parse_response", side_effect=parse):
            transcript, payload = STT.transcribe_stream(
                ws,
                b"x" * 640,
                audio_format="pcm",
                codec="raw",
                sample_rate=16000,
                segment_duration_ms=200,
                timeout_seconds=2,
            )

        self.assertEqual(transcript, "verified")
        self.assertEqual(payload["audio_info"]["duration"], 1)

    def test_stt_chunks_pcm_by_audio_duration(self) -> None:
        one_second_pcm = b"\x00" * (16000 * 2)
        chunks, packet_durations_ms = STT.chunk_audio(
            one_second_pcm,
            audio_format="pcm",
            sample_rate=16000,
            segment_duration_ms=200,
        )
        self.assertEqual(len(chunks), 5)
        self.assertTrue(all(len(chunk) == 6400 for chunk in chunks))
        self.assertEqual(packet_durations_ms, [200] * 5)

    def test_stt_reads_mp3_frame_duration(self) -> None:
        # MPEG-2 Layer III, 64 kbps, 16 kHz: 288 bytes and 36 ms per frame.
        frame = bytes.fromhex("fff38800") + (b"\x00" * 284)
        duration_ms = STT.mp3_duration_ms(frame * 10)
        self.assertAlmostEqual(duration_ms, 10 * 576 * 1000 / 16000, places=5)

        chunks, packet_durations_ms = STT.chunk_audio(
            frame * 10,
            audio_format="mp3",
            sample_rate=16000,
            segment_duration_ms=200,
        )
        self.assertEqual([len(chunk) for chunk in chunks], [len(frame) * 5] * 2)
        self.assertEqual(packet_durations_ms, [180, 180])

    def test_stt_rejects_unsupported_sample_rates(self) -> None:
        frame_44100 = bytes.fromhex("fffb9000") + (b"\x00" * 413)
        with self.assertRaisesRegex(ValueError, "16000"):
            STT.mp3_duration_ms(frame_44100)
        with self.assertRaisesRegex(ValueError, "16000"):
            STT.chunk_audio(b"\x00" * 48000, audio_format="pcm", sample_rate=24000)

    def test_stt_groups_ogg_pages_by_granule_duration(self) -> None:
        pre_skip = 312

        def page(granule: int, payload: bytes) -> bytes:
            header = bytearray(27)
            header[:4] = b"OggS"
            header[6:14] = granule.to_bytes(8, "little")
            header[26] = 1
            return bytes(header) + bytes([len(payload)]) + payload

        opus_head = b"OpusHead" + b"\x01\x01" + pre_skip.to_bytes(2, "little") + b"\x00" * 7
        data = b"".join([
            page(0, opus_head),
            page(pre_skip + 4800, b"a"),
            page(pre_skip + 9600, b"b"),
            page(pre_skip + 14400, b"c"),
        ])
        chunks, packet_durations_ms = STT.chunk_audio(
            data,
            audio_format="ogg",
            sample_rate=16000,
            segment_duration_ms=200,
        )
        self.assertEqual(len(chunks), 2)
        self.assertEqual(packet_durations_ms, [200, 100])
        self.assertEqual(b"".join(chunks), data)


if __name__ == "__main__":
    unittest.main()
