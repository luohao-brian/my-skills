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


class PackagingTransformTests(unittest.TestCase):
    def test_project_init_inserts_dir_before_line_continuation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            workflow = stage / "workflow.md"
            workflow.write_text(
                "```bash\n"
                "python3 {baseDir}/scripts/project_manager.py init demo \\\n"
                "  --format wide --quick-generate\n"
                "```\n",
                encoding="utf-8",
            )

            SYNC._portable_project_init(stage)

            transformed = workflow.read_text(encoding="utf-8")
            self.assertIn(
                "project_manager.py init demo --dir <absolute-projects-root> \\",
                transformed,
            )
            self.assertNotIn("\\ --dir", transformed)

    def test_release_routes_reference_runtime_owner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            quick = stage / "workflows" / "profiles" / "quick-generate.md"
            default = stage / "workflows" / "generate-pptx.md"
            quick.parent.mkdir(parents=True)
            quick.write_text(
                "```bash\n"
                "python3 {baseDir}/scripts/svg_to_pptx.py <project_path> --quick-generate --with-notes  # Speaker Notes enabled\n"
                "python3 {baseDir}/scripts/svg_to_pptx.py <project_path> --quick-generate --no-notes    # Speaker Notes disabled\n"
                "```\n",
                encoding="utf-8",
            )
            default.write_text(
                "| Effective decision | Command |\n"
                "|---|---|\n"
                "| Speaker Notes `enabled` | `python3 {baseDir}/scripts/svg_to_pptx.py <project_path>` |\n"
                "| Speaker Notes `disabled` | `python3 {baseDir}/scripts/svg_to_pptx.py <project_path> --no-notes` |\n",
                encoding="utf-8",
            )

            SYNC._downstream_release_command_owner(stage)

            for route in (quick, default):
                transformed = route.read_text(encoding="utf-8")
                self.assertIn("formal-svg-route-publication", transformed)
                self.assertNotIn("python3 {baseDir}/scripts/svg_to_pptx.py", transformed)


if __name__ == "__main__":
    unittest.main()
