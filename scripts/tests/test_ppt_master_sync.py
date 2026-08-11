from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "ppt_master_sync.py"
SPEC = importlib.util.spec_from_file_location("ppt_master_sync", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)


class PublishTests(unittest.TestCase):
    def test_publish_replaces_target_and_removes_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root / "stage"
            target = root / "ppt-master"
            stage.mkdir()
            target.mkdir()
            (stage / "new.txt").write_text("new", encoding="utf-8")
            (target / "old.txt").write_text("old", encoding="utf-8")

            SYNC._publish(stage, target)

            self.assertFalse(stage.exists())
            self.assertEqual((target / "new.txt").read_text(encoding="utf-8"), "new")
            self.assertFalse((target / "old.txt").exists())
            self.assertFalse((root / ".ppt-master.sync-backup").exists())


if __name__ == "__main__":
    unittest.main()
