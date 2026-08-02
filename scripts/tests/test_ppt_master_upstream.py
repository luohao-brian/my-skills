from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from ppt_master_upstream import classify_files, git_blob_id  # noqa: E402


class ClassifyFilesTest(unittest.TestCase):
    def test_three_way_states_include_additions_and_deletions(self) -> None:
        baseline = {
            "unchanged": ("100644", "a"),
            "safe-change": ("100644", "a"),
            "safe-delete": ("100644", "a"),
            "local-change": ("100644", "a"),
            "conflict": ("100644", "a"),
            "both-delete": ("100644", "a"),
        }
        local = {
            "unchanged": ("100644", "a"),
            "safe-change": ("100644", "a"),
            "safe-delete": ("100644", "a"),
            "local-change": ("100644", "b"),
            "local-add": ("100644", "b"),
            "conflict": ("100644", "b"),
            "same-add": ("100644", "b"),
        }
        upstream = {
            "unchanged": ("100644", "a"),
            "safe-change": ("100644", "c"),
            "local-change": ("100644", "a"),
            "conflict": ("100644", "c"),
            "upstream-add": ("100644", "c"),
            "same-add": ("100644", "b"),
        }

        result = classify_files(baseline, local, upstream)

        self.assertEqual(result["unchanged"], ("unchanged",))
        self.assertEqual(result["safe_upstream"], ("safe-change", "safe-delete", "upstream-add"))
        self.assertEqual(result["local_overlay"], ("local-add", "local-change"))
        self.assertEqual(result["converged"], ("both-delete", "same-add"))
        self.assertEqual(result["conflict"], ("conflict",))

    def test_blob_id_matches_git_blob_encoding(self) -> None:
        self.assertEqual(git_blob_id(b"test content\n"), "d670460b4b4aece5915caf5c68d12f560a9fe3e4")


if __name__ == "__main__":
    unittest.main()
