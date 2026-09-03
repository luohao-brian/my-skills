from __future__ import annotations

import base64
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
MODULE_PATH = SCRIPTS / "tts_backends" / "backend_volcengine.py"
SPEC = importlib.util.spec_from_file_location("ppt_master_tts_volcengine", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
BACKEND = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BACKEND
SPEC.loader.exec_module(BACKEND)

import notes_to_audio


class FakeResponse:
    def __init__(self, chunks: list[str], status_code: int = 200) -> None:
        self.chunks = chunks
        self.status_code = status_code
        self.text = ""
        self.closed = False

    def iter_content(self, **_kwargs):
        yield from self.chunks

    def close(self) -> None:
        self.closed = True


class TtsProviderBridgeTests(unittest.TestCase):
    def test_selected_agent_plan_adapter_uses_its_own_credentials(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "TTS_BACKEND": "ark-api",
                "TTS_PROVIDER": "volc-ark",
                "ARK_TTS_API_KEY": "speech",
                "ARK_API_KEY": "normal-ark",
                "ARK_AGENT_PLAN_API_KEY": "plan",
            },
            clear=True,
        ):
            profile = BACKEND.resolve_profile()
        self.assertEqual(profile.name, "ark-agent-plan")
        self.assertEqual(profile.api_key, "plan")
        self.assertEqual(
            profile.base_url,
            "https://openspeech.bytedance.com/api/v3/plan/tts/unidirectional",
        )
        self.assertEqual(profile.model, "seed-tts-2.0")
        self.assertEqual(profile.provider, "volc-ark-agent-plan")

    def test_adapter_rejects_unsupported_profile(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"ARK_AGENT_PLAN_API_KEY": "plan"},
            clear=True,
        ):
            with self.assertRaisesRegex(RuntimeError, "Unsupported Agent Plan TTS profile"):
                BACKEND.resolve_profile("ark-api")

    def test_other_keys_do_not_replace_agent_plan_key(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"ARK_API_KEY": "normal-ark", "ARK_TTS_API_KEY": "speech"},
            clear=True,
        ):
            with self.assertRaisesRegex(RuntimeError, "ARK_AGENT_PLAN_API_KEY"):
                BACKEND.resolve_profile()

    def test_generate_publishes_streamed_audio(self) -> None:
        audio = b"ID3-test-audio"
        payload = (
            json_chunk({"code": 0, "data": base64.b64encode(audio).decode("ascii")})
            + json_chunk({"code": BACKEND.FINISH_CODE})
        )
        response = FakeResponse([payload[:17], payload[17:]])
        requests_module = types.SimpleNamespace(
            post=mock.Mock(return_value=response),
        )
        profile = BACKEND.TtsProfile(
            name="ark-agent-plan",
            provider="volc-ark-agent-plan",
            api_key="plan",
            base_url="https://example.invalid/tts",
            model="seed-tts-2.0",
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "slide-1.mp3"
            with mock.patch.dict(sys.modules, {"requests": requests_module}):
                BACKEND.generate("测试旁白", output, profile=profile)
            self.assertEqual(output.read_bytes(), audio)
        self.assertTrue(response.closed)
        headers = requests_module.post.call_args.kwargs["headers"]
        self.assertEqual(headers["X-Api-Key"], "plan")
        self.assertEqual(headers["X-Api-Resource-Id"], "seed-tts-2.0")

    def test_original_providers_override_configuration_without_agent_plan_key(self) -> None:
        for name in ("edge", "elevenlabs", "minimax", "qwen", "cosyvoice"):
            with self.subTest(provider=name):
                backend = getattr(notes_to_audio, f"backend_{name}")
                printer = mock.AsyncMock() if name == "edge" else mock.Mock()
                with mock.patch.dict(os.environ, {
                    "TTS_PROVIDER": "ark-agent-plan", "ELEVENLABS_API_KEY": "test-elevenlabs-key",
                }, clear=True), mock.patch.object(
                    notes_to_audio, "_load_tts_env_file"
                ), mock.patch.object(backend, "print_voices", printer), mock.patch.object(
                    sys, "argv", ["notes_to_audio.py", "--provider", name, "--list-voices"]
                ):
                    self.assertEqual(notes_to_audio.main(), 0)
                printer.assert_called_once()

    def test_unconfigured_provider_retains_edge_default(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
            notes_to_audio, "_load_tts_env_file"
        ), mock.patch.object(notes_to_audio.backend_edge, "print_voices", new_callable=mock.AsyncMock) as voices, mock.patch.object(
            sys, "argv", ["notes_to_audio.py", "--list-voices"]
        ):
            self.assertEqual(notes_to_audio.main(), 0)
        voices.assert_awaited_once()

    def test_configured_agent_plan_generates_upstream_audio_manifest(self) -> None:
        audio = b"ID3-test-audio"
        response = FakeResponse([
            json_chunk({"code": 0, "data": base64.b64encode(audio).decode("ascii")}),
            json_chunk({"code": BACKEND.FINISH_CODE}),
        ])
        requests_module = types.SimpleNamespace(post=mock.Mock(return_value=response))
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "notes").mkdir()
            (project / "notes" / "01_intro.md").write_text("# Intro\n测试旁白", encoding="utf-8")
            with mock.patch.dict(os.environ, {
                "TTS_PROVIDER": "ark-agent-plan", "ARK_AGENT_PLAN_API_KEY": "plan",
            }, clear=True), mock.patch.object(
                notes_to_audio, "_load_tts_env_file"
            ), mock.patch.object(sys, "argv", ["notes_to_audio.py", str(project)]), mock.patch.dict(
                sys.modules, {"requests": requests_module}
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(notes_to_audio.main(), 0)
            self.assertEqual((project / "audio" / "01_intro.mp3").read_bytes(), audio)
            manifest = json.loads((project / "audio" / "manifest.json").read_text())
            self.assertEqual(manifest["provider"], "ark-agent-plan")
        self.assertTrue(response.closed)

def json_chunk(value: dict[str, object]) -> str:
    import json

    return json.dumps(value, separators=(",", ":"))


if __name__ == "__main__":
    unittest.main()
