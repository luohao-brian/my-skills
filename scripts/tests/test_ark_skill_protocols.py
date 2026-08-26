from __future__ import annotations

import importlib.util
import json
import os
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
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
VISION = load_script("ark_vision_protocol", "openclaw-skills/ark-vision/scripts/vision_analyze.py")
SEARCH = load_script("ark_search_protocol", "openclaw-skills/ark-search/scripts/web_search.py")
PLUGIN_CLI = load_script("hermes_ark_plugin_cli", "hermes-plugins/hermes-ark-plugin/cli.py")


class ArkSkillProtocolTests(unittest.TestCase):
    def test_hermes_plugin_manifest_and_default_config(self) -> None:
        manifest = (ROOT / "hermes-plugins/hermes-ark-plugin/plugin.yaml").read_text(encoding="utf-8")
        self.assertIn("manifest_version: 2", manifest)
        self.assertIn("api_version: 1", manifest)
        self.assertIn("- tools.override", manifest)
        self.assertNotIn("requires_env:", manifest)
        self.assertNotIn("transcribe_audio\n", manifest)

        plan = PLUGIN_CLI._default_ark_entry(
            "ARK_AGENT_PLAN_API_KEY", backend="ark-agent-plan",
        )["settings"]
        api = PLUGIN_CLI._default_ark_entry(
            "ARK_AGENT_PLAN_API_KEY", backend="ark-api",
        )["settings"]
        self.assertEqual(plan["video_generate"]["model"], "doubao-seedance-2.0-fast")
        self.assertEqual(api["image_generate"]["api_key"], "${ARK_API_KEY}")
        self.assertEqual(api["text_to_speech"]["api_key"], "${ARK_TTS_X_API_KEY}")

        legacy = {
            "plugins": {
                "enabled": ["ark"],
                "entries": {
                    "ark": {
                        "api_key": "${LEGACY_PLAN_KEY}",
                        "allow_tool_override": True,
                        "image_generate": {"model": "custom-seedream"},
                    },
                },
            },
        }
        saved: list[dict] = []
        with patch.object(PLUGIN_CLI, "_load_raw_config_pair", return_value=(legacy, saved.append)):
            PLUGIN_CLI._write_ark_config(
                api_key_env="ARK_AGENT_PLAN_API_KEY",
                voice=None,
                activate_providers=False,
                overwrite=False,
                backend="ark-agent-plan",
            )
        migrated = saved[0]["plugins"]["entries"]["ark"]
        self.assertTrue(migrated["allow_tool_override"])
        self.assertEqual(migrated["settings"]["image_generate"]["model"], "custom-seedream")
        self.assertEqual(migrated["settings"]["text_to_speech"]["api_key"], "${LEGACY_PLAN_KEY}")

    def test_skill_instructions_map_user_backend_wording(self) -> None:
        for skill_name in ("ark-image-gen", "ark-video-gen", "ark-tts", "ark-stt", "ark-vision"):
            text = (ROOT / "openclaw-skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("`ARK-API` or `方舟 API` to `--backend ark-api`", text)
            self.assertIn("`ARK-AGENT-PLAN` or `方舟 Agent Plan` to `--backend ark-agent-plan`", text)

    def test_backend_defaults_models_and_credentials(self) -> None:
        modules = (IMAGE, VIDEO, TTS, STT, VISION)
        self.assertTrue(all(module.DEFAULT_BACKEND == "ark-agent-plan" for module in modules))

        self.assertEqual(IMAGE.BACKENDS["ark-agent-plan"], {
            "base_url": "https://ark.cn-beijing.volces.com/api/plan/v3",
            "api_key_env": "ARK_AGENT_PLAN_API_KEY",
            "model": "doubao-seedream-5.0-lite",
        })
        self.assertEqual(IMAGE.BACKENDS["ark-api"], {
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "api_key_env": "ARK_API_KEY",
            "model": "doubao-seedream-5-0-260128",
        })
        self.assertEqual(VIDEO.BACKENDS["ark-agent-plan"]["model"], "doubao-seedance-2.0-fast")
        self.assertEqual(VIDEO.BACKENDS["ark-api"]["model"], "doubao-seedance-2-5-260628")
        self.assertEqual(VISION.BACKENDS["ark-agent-plan"]["model"], "doubao-seed-2.0-lite")
        self.assertEqual(VISION.BACKENDS["ark-api"]["model"], "doubao-seed-2-0-lite-260428")
        self.assertEqual(VIDEO.BACKENDS["ark-api"]["base_url"], "https://ark.cn-beijing.volces.com/api/v3")
        self.assertEqual(VISION.BACKENDS["ark-api"]["base_url"], "https://ark.cn-beijing.volces.com/api/v3")
        self.assertEqual(TTS.RESOURCE_ID, "seed-tts-2.0")
        self.assertEqual(STT.RESOURCE_ID, "volc.seedasr.sauc.duration")
        self.assertEqual(TTS.BACKENDS["ark-api"]["api_key_env"], "ARK_TTS_X_API_KEY")
        self.assertEqual(STT.BACKENDS["ark-api"]["api_key_env"], "ARK_TTS_X_API_KEY")
        self.assertEqual(
            TTS.BACKENDS["ark-api"]["endpoint"],
            "https://openspeech.bytedance.com/api/v3/tts/unidirectional",
        )
        self.assertEqual(
            STT.BACKENDS["ark-api"]["endpoint"],
            "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_nostream",
        )

        with patch.dict(os.environ, {
            "ARK_AGENT_PLAN_API_KEY": "plan-key",
            "ARK_API_KEY": "ark-key",
            "ARK_TTS_X_API_KEY": "speech-key",
        }, clear=True):
            for module in modules:
                _, plan_key = module.resolve_backend("ark-agent-plan")
                _, api_key = module.resolve_backend("ark-api")
                self.assertEqual(plan_key, "plan-key")
                expected_api_key = "speech-key" if module in (TTS, STT) else "ark-key"
                self.assertEqual(api_key, expected_api_key)

    def test_backend_selection_never_falls_back_to_another_credential(self) -> None:
        with patch.dict(os.environ, {"ARK_API_KEY": "ark-key"}, clear=True):
            with self.assertRaisesRegex(ValueError, "ARK_AGENT_PLAN_API_KEY"):
                IMAGE.resolve_backend("ark-agent-plan")
        with patch.dict(os.environ, {"ARK_AGENT_PLAN_API_KEY": "plan-key"}, clear=True):
            with self.assertRaisesRegex(ValueError, "ARK_API_KEY"):
                VISION.resolve_backend("ark-api")
            with self.assertRaisesRegex(ValueError, "ARK_TTS_X_API_KEY"):
                TTS.resolve_backend("ark-api")

    def test_vision_uses_chat_completions_media_blocks(self) -> None:
        video, video_type = VISION.build_media_content("https://example.com/clip.mp4?token=x")
        self.assertEqual(video_type, "video")
        self.assertEqual(video, {
            "type": "video_url",
            "video_url": {"url": "https://example.com/clip.mp4?token=x"},
        })
        image, image_type = VISION.build_media_content("https://example.com/frame.png")
        self.assertEqual(image_type, "image")
        self.assertEqual(image, {
            "type": "image_url",
            "image_url": {"url": "https://example.com/frame.png"},
        })

    def test_image_size_uses_provider_native_casing(self) -> None:
        self.assertEqual(IMAGE.normalize_size("2k"), "2K")
        self.assertEqual(IMAGE.normalize_size("4K"), "4K")
        self.assertEqual(IMAGE.normalize_size("4:3"), "4:3")
        self.assertEqual(IMAGE.normalize_size("2048X1024"), "2048x1024")
        self.assertEqual(IMAGE.resolve_size("16:9", "3K"), "3K")

        lite = IMAGE.build_payload(
            model="doubao-seedream-5-0-260128",
            prompt="three panels",
            images=[],
            aspect_ratio="16:9",
            resolution="2K",
            count=3,
        )
        self.assertEqual(lite["size"], "2K")
        self.assertIn("画面宽高比为 16:9", lite["prompt"])
        self.assertEqual(lite["sequential_image_generation_options"], {"max_images": 3})
        self.assertNotIn("max_images", lite)
        pro = IMAGE.build_payload(
            model=IMAGE.PRO_MODEL,
            prompt="one panel",
            images=[],
            aspect_ratio="1:1",
            resolution="1.5K",
            count=1,
        )
        self.assertEqual(pro["size"], "1.5K")
        self.assertNotIn("seed", pro)
        self.assertNotIn("sequential_image_generation", pro)
        with self.assertRaisesRegex(ValueError, "1 to 1"):
            IMAGE.validate_request("ark-api", IMAGE.PRO_MODEL, "2K", 2)

        layers = IMAGE.build_payload(
            backend="ark-api",
            model=IMAGE.PRO_MODEL,
            prompt="",
            images=["https://example.com/poster.png"],
            aspect_ratio="1:1",
            resolution="auto",
            count=1,
            layer_decomposition=True,
        )
        self.assertEqual(layers["image"], "https://example.com/poster.png")
        self.assertEqual(layers["size"], "auto")
        self.assertTrue(layers["layer_decomposition"])
        self.assertNotIn("prompt", layers)
        self.assertNotIn("layer_image", layers)
        self.assertNotIn("layer_size", layers)

        with self.assertRaisesRegex(ValueError, "must not exceed 15"):
            IMAGE.validate_request(
                "ark-agent-plan",
                "doubao-seedream-5.0-lite",
                "2K",
                3,
                image_count=13,
            )
        self.assertEqual(
            IMAGE.normalize_image_input("https://example.com/reference.png"),
            "https://example.com/reference.png",
        )

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
        plan_content, plan_settings = VIDEO.build_request(
            backend="ark-agent-plan",
            model="doubao-seedance-2.0-fast",
            prompt="robot waves",
            image_url=None,
            duration=5,
            aspect_ratio="9:16",
            resolution="720p",
            generate_audio=True,
        )
        self.assertEqual(plan_content[0]["text"], "robot waves")
        self.assertEqual(plan_settings, {
            "generate_audio": True,
            "resolution": "720p",
            "ratio": "9:16",
            "duration": 5,
            "watermark": False,
        })
        self.assertNotIn("--dur", plan_content[0]["text"])
        api_content, api_settings = VIDEO.build_request(
            backend="ark-api",
            model="doubao-seedance-2-5-260628",
            prompt="robot waves",
            image_url=None,
            duration=30,
            aspect_ratio="16:9",
            resolution="1080p",
            generate_audio=False,
            output_format="mov",
            return_last_frame=True,
        )
        self.assertEqual(api_content[0]["text"], "robot waves")
        self.assertEqual(api_settings["duration"], 30)
        self.assertEqual(api_settings["resolution"], "1080p")
        self.assertEqual(api_settings["output_format"], "mov")
        self.assertTrue(api_settings["return_last_frame"])
        with self.assertRaisesRegex(ValueError, "resolutions"):
            VIDEO.validate_generation("ark-api", "doubao-seedance-2-0-fast-260128", 5, "1080p")
        with self.assertRaisesRegex(ValueError, "resolutions"):
            VIDEO.validate_generation("ark-api", "doubao-seedance-2-5-260628", 5, "4k")
        VIDEO.validate_generation("ark-api", "doubao-seedance-2-0-260128", 15, "4k")

    def test_video_material_roles_modes_and_order(self) -> None:
        frames, frame_settings = VIDEO.build_request(
            backend="ark-api",
            model="doubao-seedance-2-5-260628",
            prompt="move from first to last frame",
            first_frame="https://example.com/first.png",
            last_frame="https://example.com/last.png",
            duration=5,
            aspect_ratio="adaptive",
            resolution="720p",
            generate_audio=False,
        )
        self.assertEqual([item.get("role") for item in frames[1:]], ["first_frame", "last_frame"])
        self.assertEqual(frame_settings["ratio"], "adaptive")

        references, reference_settings = VIDEO.build_request(
            backend="ark-api",
            model="doubao-seedance-2-5-260628",
            prompt="use @图像1, @视频1 and @音频1",
            reference_images=["https://example.com/one.png", "https://example.com/two.png"],
            reference_videos=["https://example.com/motion.mp4"],
            reference_audios=["https://example.com/voice.mp3"],
            duration=10,
            aspect_ratio="16:9",
            resolution="1080p",
            generate_audio=True,
            task_type="reference",
        )
        self.assertEqual(
            [(item["type"], item.get("role")) for item in references[1:]],
            [
                ("image_url", "reference_image"),
                ("image_url", "reference_image"),
                ("video_url", "reference_video"),
                ("audio_url", "reference_audio"),
            ],
        )
        self.assertEqual(reference_settings["omni_reference_task_type"], "reference")
        self.assertTrue(reference_settings["generate_audio"])

        with self.assertRaisesRegex(ValueError, "cannot be combined"):
            VIDEO.build_request(
                backend="ark-api",
                model="doubao-seedance-2-5-260628",
                prompt="conflict",
                first_frame="https://example.com/first.png",
                reference_images=["https://example.com/reference.png"],
                duration=5,
                aspect_ratio="adaptive",
                resolution="720p",
                generate_audio=False,
            )
        with self.assertRaisesRegex(ValueError, "requires --aspect-ratio adaptive and --duration -1"):
            VIDEO.validate_generation(
                "ark-api",
                "doubao-seedance-2-5-260628",
                5,
                "720p",
                aspect_ratio="adaptive",
                reference_videos=["https://example.com/edit.mp4"],
                task_type="edit",
            )
        with self.assertRaisesRegex(ValueError, "must be combined"):
            VIDEO.validate_generation(
                "ark-agent-plan",
                "doubao-seedance-2.0-fast",
                5,
                "720p",
                reference_audios=["https://example.com/voice.mp3"],
            )

    def test_video_success_preserves_remote_result_when_download_fails(self) -> None:
        task = SimpleNamespace(
            status="succeeded",
            model="doubao-seedance-2-5-260628",
            content=SimpleNamespace(
                video_url="https://example.com/result.mp4",
                last_frame_url="https://example.com/last.png",
            ),
            duration=7,
            ratio="9:16",
            resolution="1080p",
            generate_audio=True,
            usage={"completion_tokens": 123},
            request_id="request-1",
            output_format="mp4",
        )
        with patch.object(VIDEO, "download_video", side_effect=OSError("offline")):
            result = VIDEO.task_result(
                task,
                backend="ark-api",
                task_id="task-1",
                prompt="compiled prompt",
                requested_model=None,
                output_path=None,
                download_timeout=5,
            )
        self.assertTrue(result["success"])
        self.assertIsNone(result["local_path"])
        self.assertEqual(result["video_url"], "https://example.com/result.mp4")
        self.assertEqual(result["duration"], 7)
        self.assertEqual(result["aspect_ratio"], "9:16")
        self.assertIn("download failed", result["warnings"][0])

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
        self.assertTrue(json.loads(params["additions"])["enable_subtitle"])
        self.assertEqual(params["audio_params"]["speed_ratio"], 1.0)
        segment = TTS.words_to_segment({
            "text": "official protocol",
            "words": [
                {"word": "official", "startTime": 0.125, "endTime": 0.5},
                {"word": " protocol", "startTime": 0.5, "endTime": 1.25},
            ],
        }, 0)
        self.assertEqual(segment["start_time_ms"], 125)
        self.assertEqual(segment["end_time_ms"], 1250)

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

    def test_stt_handshake_uses_new_console_request_headers(self) -> None:
        headers = STT.build_connection_headers(
            "speech-key",
            "67ee89ba-7050-4c04-a3d7-ac61a63499b3",
        )
        self.assertEqual(headers, [
            "X-Api-Resource-Id: volc.seedasr.sauc.duration",
            "X-Api-Request-Id: 67ee89ba-7050-4c04-a3d7-ac61a63499b3",
            "X-Api-Sequence: -1",
            "X-Api-Key: speech-key",
        ])

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
