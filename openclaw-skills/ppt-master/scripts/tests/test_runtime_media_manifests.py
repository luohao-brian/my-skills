from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from audio_manifest import MAX_TTS_CHARS, load_manifest as load_audio_manifest, prepare  # noqa: E402
from image_manifest import load_manifest as load_image_manifest, task_view  # noqa: E402


class RuntimeMediaManifestTests(unittest.TestCase):
    def test_image_task_is_provider_neutral(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "image_prompts.json"
            manifest.write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "filename": "hero.png",
                                "prompt": "Editorial illustration of a model launch",
                                "aspect_ratio": "16:9",
                                "status": "Pending",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            item = load_image_manifest(manifest)["items"][0]
            request = task_view(item, manifest)["capability_request"]
            self.assertEqual(request["aspect_ratio"], "16:9")
            self.assertEqual(request["count"], 1)
            self.assertNotIn("provider", request)
            self.assertNotIn("model", request)

    def test_image_manifest_rejects_provider_owned_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "image_prompts.json"
            manifest.write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "filename": "hero.png",
                                "prompt": "A hero",
                                "aspect_ratio": "16:9",
                                "status": "Pending",
                                "provider": "example",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "provider-owned"):
                load_image_manifest(manifest)

    def test_audio_prepare_enforces_portable_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            notes = project / "notes"
            notes.mkdir()
            (notes / "001.md").write_text("x" * (MAX_TTS_CHARS + 1), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exceeds runtime TTS limit"):
                prepare(project)

    def test_audio_manifest_rejects_runtime_owned_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "audio_tasks.json"
            manifest.write_text(
                json.dumps(
                    {
                        "tasks": [
                            {
                                "slide": "001",
                                "note_path": "/workspace/notes/001.md",
                                "text": "hello",
                                "output_path": "/workspace/audio/001.mp3",
                                "status": "Pending",
                                "voice": "example",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "runtime-owned"):
                load_audio_manifest(manifest)


if __name__ == "__main__":
    unittest.main()
