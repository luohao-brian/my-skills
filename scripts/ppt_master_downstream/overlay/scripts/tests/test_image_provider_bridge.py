"""Check optional Agent Plan dispatch without changing upstream providers."""

from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import image_gen
from image_backends import backend_volcengine


class ImageProviderBridgeTests(unittest.TestCase):
    def test_cli_provider_overrides_environment_without_agent_plan_key(self) -> None:
        backend = Mock()
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"IMAGE_BACKEND": "ark-agent-plan"}, clear=True
        ), patch.object(image_gen, "_load_image_env_file"), patch.object(
            image_gen, "_load_backend", return_value=(backend, "openai")
        ) as load, patch.object(sys, "argv", [
            "image_gen.py", "test image", "--backend", "openai", "-o", directory,
        ]), contextlib.redirect_stdout(io.StringIO()):
            image_gen.main()
        load.assert_called_once_with("openai")
        backend.generate.assert_called_once()

    def test_agent_plan_request_uses_its_own_key_endpoint_and_size(self) -> None:
        response = Mock(status_code=200)
        response.json.return_value = {"data": [{"url": "https://example.invalid/image.jpeg"}]}
        env = {
            "IMAGE_BACKEND": "ark-agent-plan",
            "ARK_AGENT_PLAN_API_KEY": "test-plan-key",
            "LAS_API_KEY": "other-key",
            "VOLCENGINE_MODEL": "other-model",
            "VOLCENGINE_BASE_URL": "https://example.invalid/other-service",
        }
        with patch.dict(os.environ, env, clear=True), patch.object(
            backend_volcengine.requests, "post", return_value=response
        ) as post, patch.object(
            backend_volcengine, "download_image", return_value="result.jpeg"
        ), contextlib.redirect_stdout(io.StringIO()):
            backend, name = image_gen._resolve_backend()
            self.assertEqual(name, "ark-agent-plan")
            backend.generate("test", aspect_ratio="16:9", image_size="4K", max_retries=0)
        self.assertEqual(post.call_args.args[0], backend_volcengine.ARK_AGENT_PLAN_ENDPOINT)
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer test-plan-key")
        self.assertEqual(post.call_args.kwargs["json"]["model"], "doubao-seedream-5.0-lite")
        self.assertEqual(post.call_args.kwargs["json"]["size"], "5504x3040")

    def test_original_volcengine_configuration_needs_no_agent_plan_key(self) -> None:
        with patch.dict(os.environ, {
            "IMAGE_BACKEND": "volcengine", "ARK_API_KEY": "normal-ark-key",
        }, clear=True), patch.object(
            backend_volcengine, "_generate_image", return_value="result.jpeg"
        ) as generate:
            backend, name = image_gen._resolve_backend()
            self.assertEqual(name, "volcengine")
            backend.generate("test", max_retries=0)
        self.assertEqual(generate.call_args.kwargs["api_key"], "normal-ark-key")
        self.assertEqual(generate.call_args.kwargs["model"], backend_volcengine.DEFAULT_MODEL)
        self.assertEqual(generate.call_args.kwargs["base_url"], backend_volcengine.DEFAULT_ENDPOINT)

    def test_agent_plan_does_not_fall_back_to_other_credentials(self) -> None:
        with patch.dict(os.environ, {
            "IMAGE_BACKEND": "ark-agent-plan", "ARK_API_KEY": "normal-ark-key",
        }, clear=True), patch.object(backend_volcengine.requests, "post") as post:
            with self.assertRaisesRegex(ValueError, "ARK_AGENT_PLAN_API_KEY"):
                backend_volcengine.generate("test", max_retries=0)
        post.assert_not_called()

    def test_sizes_keep_distinct_upstream_resolutions(self) -> None:
        self.assertEqual(backend_volcengine._resolve_size("16:9", "2K"), "2848x1600")
        self.assertEqual(backend_volcengine._resolve_size("16:9", "4K"), "5504x3040")
        with self.assertRaisesRegex(ValueError, "Unsupported image size"):
            backend_volcengine._resolve_size("16:9", "1K")


if __name__ == "__main__":
    unittest.main()
