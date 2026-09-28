"""Check downstream Ark routing and upstream LAS credential isolation."""

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
from image_backends import backend_ark, backend_ark_api, backend_ark_plan, backend_volcengine


class ImageProviderBridgeTests(unittest.TestCase):
    def test_unconfigured_image_backend_defaults_to_ark_route(self) -> None:
        with patch.dict(os.environ, {}, clear=True), patch.object(
            image_gen, "load_prefixed_env_file", return_value=None
        ):
            image_gen._load_image_env_file()
            _, name = image_gen._resolve_backend()
            self.assertEqual(name, "ark")

    def test_cli_provider_overrides_environment(self) -> None:
        backend = Mock()
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"IMAGE_BACKEND": "ark"}, clear=True
        ), patch.object(image_gen, "_load_image_env_file"), patch.object(
            image_gen, "_load_backend", return_value=(backend, "openai")
        ) as load, patch.object(sys, "argv", [
            "image_gen.py", "test image", "--backend", "openai", "-o", directory,
        ]), contextlib.redirect_stdout(io.StringIO()):
            image_gen.main()
        load.assert_called_once_with("openai")
        backend.generate.assert_called_once()

    def test_default_ark_route_uses_agent_plan_first(self) -> None:
        with patch.object(backend_ark_plan, "generate", return_value="plan.jpeg") as plan, patch.object(
            backend_ark_api, "generate"
        ) as api:
            self.assertEqual(backend_ark.generate("test", max_retries=0), "plan.jpeg")
        plan.assert_called_once()
        api.assert_not_called()

    def test_ark_route_falls_back_to_api_on_quota(self) -> None:
        with patch.object(backend_ark_plan, "generate", side_effect=RuntimeError(
            "Agent Plan image generation failed (429): AccountQuotaExceeded"
        )), patch.object(backend_ark_api, "generate", return_value="api.jpeg") as api, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(backend_ark.generate("test", model=backend_ark_plan.MODEL), "api.jpeg")
        self.assertEqual(api.call_args.kwargs["model"], backend_ark_api.MODEL)

    def test_ark_route_does_not_hide_bad_request(self) -> None:
        with patch.object(backend_ark_plan, "generate", side_effect=RuntimeError(
            "Agent Plan image generation failed (400): invalid size"
        )), patch.object(backend_ark_api, "generate") as api:
            with self.assertRaisesRegex(RuntimeError, "invalid size"):
                backend_ark.generate("test")
        api.assert_not_called()

    def test_ark_api_request_uses_own_key_endpoint_and_size(self) -> None:
        response = Mock(status_code=200)
        response.json.return_value = {"data": [{"url": "https://example.invalid/image.jpeg"}]}
        with patch.dict(os.environ, {
            "ARK_API_KEY": "normal-ark-key", "ARK_AGENT_PLAN_API_KEY": "plan-key",
            "LAS_API_KEY": "las-key",
        }, clear=True), patch.object(backend_ark_api.requests, "post", return_value=response) as post, patch.object(
            backend_ark_api, "download_image", return_value="result.jpeg"
        ), contextlib.redirect_stdout(io.StringIO()):
            backend_ark_api.generate("test", aspect_ratio="16:9", max_retries=0)
        self.assertEqual(post.call_args.args[0], backend_ark_api.ENDPOINT)
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer normal-ark-key")
        self.assertEqual(post.call_args.kwargs["json"]["model"], backend_ark_api.MODEL)
        self.assertEqual(post.call_args.kwargs["json"]["size"], "2K")
        self.assertIn("16:9", post.call_args.kwargs["json"]["prompt"])

    def test_agent_plan_request_uses_own_key_endpoint_and_size(self) -> None:
        response = Mock(status_code=200)
        response.json.return_value = {"data": [{"url": "https://example.invalid/image.jpeg"}]}
        with patch.dict(os.environ, {
            "ARK_AGENT_PLAN_API_KEY": "plan-key", "ARK_API_KEY": "normal-ark-key",
        }, clear=True), patch.object(backend_ark_plan.requests, "post", return_value=response) as post, patch.object(
            backend_ark_plan, "download_image", return_value="result.jpeg"
        ), contextlib.redirect_stdout(io.StringIO()):
            backend_ark_plan.generate("test", aspect_ratio="16:9", image_size="4K", max_retries=0)
        self.assertEqual(post.call_args.args[0], backend_ark_plan.ENDPOINT)
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer plan-key")
        self.assertEqual(post.call_args.kwargs["json"]["model"], backend_ark_plan.MODEL)
        self.assertEqual(post.call_args.kwargs["json"]["size"], "5504x3040")

    def test_ark_api_does_not_use_agent_plan_key(self) -> None:
        with patch.dict(os.environ, {"ARK_AGENT_PLAN_API_KEY": "plan-key"}, clear=True), patch.object(
            backend_ark_api.requests, "post"
        ) as post:
            with self.assertRaisesRegex(ValueError, "ARK_API_KEY"):
                backend_ark_api.generate("test", max_retries=0)
        post.assert_not_called()

    def test_las_backend_requires_las_key(self) -> None:
        with patch.dict(os.environ, {
            "IMAGE_BACKEND": "volcengine", "ARK_API_KEY": "normal-ark-key",
            "VOLCENGINE_API_KEY": "ambiguous-key",
        }, clear=True), patch.object(backend_volcengine.requests, "post") as post:
            with self.assertRaisesRegex(ValueError, "LAS_API_KEY"):
                backend_volcengine.generate("test", max_retries=0)
        post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
