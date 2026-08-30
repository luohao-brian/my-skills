#!/usr/bin/env python3
"""Regression tests for the downstream image-provider bridge."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import image_gen  # noqa: E402
from image_backends import backend_volcengine  # noqa: E402


class ImageProviderBridgeTests(unittest.TestCase):
    def test_agent_plan_is_the_fixed_image_backend(self) -> None:
        with patch.dict(os.environ, {"ARK_AGENT_PLAN_API_KEY": "test-plan-key"}, clear=True):
            _, backend_name = image_gen._resolve_backend()
            profile = backend_volcengine._resolve_profile()

        self.assertEqual(backend_name, "volcengine")
        self.assertEqual(profile["provider"], "volc-ark-agent-plan")
        self.assertEqual(profile["profile"], "ark-agent-plan")
        self.assertEqual(profile["api_key"], "test-plan-key")
        self.assertEqual(profile["base_url"], backend_volcengine.ARK_AGENT_PLAN_ENDPOINT)
        self.assertEqual(profile["model"], backend_volcengine.ARK_AGENT_PLAN_MODEL)

    def test_backend_and_provider_environment_cannot_switch_profile(self) -> None:
        env = {
            "IMAGE_BACKEND": "ark-api",
            "IMAGE_GEN_PROVIDER": "volc-ark",
            "ARK_API_KEY": "normal-ark-key",
            "ARK_AGENT_PLAN_API_KEY": "test-plan-key",
        }
        with patch.dict(os.environ, env, clear=True):
            _, backend_name = image_gen._resolve_backend()
            profile = backend_volcengine._resolve_profile()

        self.assertEqual(backend_name, "volcengine")
        self.assertEqual(profile["provider"], "volc-ark-agent-plan")
        self.assertEqual(profile["profile"], "ark-agent-plan")
        self.assertEqual(profile["api_key"], "test-plan-key")

    def test_normal_ark_key_cannot_replace_agent_plan_key(self) -> None:
        env = {"ARK_API_KEY": "normal-ark-key"}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(ValueError, "ARK_AGENT_PLAN_API_KEY"):
                backend_volcengine._resolve_profile()

    def test_agent_plan_uses_cowork_native_size_contract(self) -> None:
        self.assertEqual(
            backend_volcengine._resolve_size("16:9", "1K"),
            "2848x1600",
        )
        self.assertEqual(
            backend_volcengine._resolve_url(backend_volcengine.ARK_AGENT_PLAN_ENDPOINT),
            "https://ark.cn-beijing.volces.com/api/plan/v3/images/generations",
        )


if __name__ == "__main__":
    unittest.main()
