from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "sync-vendored-skills.py"
SPEC = importlib.util.spec_from_file_location("sync_vendored_skills", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)


class FrontmatterVersionTests(unittest.TestCase):
    def version_for(self, content: str) -> str | None:
        with tempfile.TemporaryDirectory() as directory:
            skill_file = Path(directory) / "SKILL.md"
            skill_file.write_text(content, encoding="utf-8")
            return SYNC.frontmatter_version(skill_file)

    def test_reads_top_level_version(self) -> None:
        self.assertEqual(
            self.version_for("---\nname: example\nversion: 1.2.3\n---\n"),
            "1.2.3",
        )

    def test_reads_nested_metadata_version(self) -> None:
        self.assertEqual(
            self.version_for(
                "---\nname: example\nmetadata:\n  version: \"2.6\"\n---\n"
            ),
            "2.6",
        )

    def test_ignores_version_outside_frontmatter(self) -> None:
        self.assertIsNone(
            self.version_for("---\nname: example\n---\n\nversion: not-metadata\n")
        )


if __name__ == "__main__":
    unittest.main()
