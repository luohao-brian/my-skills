from __future__ import annotations

import base64
import importlib.util
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
    def test_profile_is_fixed_to_agent_plan(self) -> None:
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

    def test_explicit_non_agent_plan_profile_is_rejected(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"ARK_AGENT_PLAN_API_KEY": "plan"},
            clear=True,
        ):
            with self.assertRaisesRegex(RuntimeError, "fixed to ark-agent-plan"):
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

def json_chunk(value: dict[str, object]) -> str:
    import json

    return json.dumps(value, separators=(",", ":"))


if __name__ == "__main__":
    unittest.main()
