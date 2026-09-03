from __future__ import annotations

import importlib.util
import contextlib
import io
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


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
    def test_missing_preview_server_reports_a_runnable_start_command(self) -> None:
        scripts = ROOT / "openclaw-skills" / "ppt-master" / "scripts"
        with patch.object(sys, "path", [str(scripts), *sys.path]):
            import visual_review
        playwright = types.ModuleType("playwright.sync_api")
        playwright.sync_playwright = object()
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            sys.modules, {"playwright.sync_api": playwright}
        ), patch.object(sys, "argv", ["visual_review.py", directory]), contextlib.redirect_stderr(io.StringIO()) as error:
            self.assertEqual(visual_review.main(), 2)
        self.assertIn(str(scripts / "svg_editor" / "server.py"), error.getvalue())
        self.assertIn("start it with:", error.getvalue())

    def test_project_directory_remains_optional_in_upstream_cli(self) -> None:
        scripts = ROOT / "openclaw-skills" / "ppt-master" / "scripts"
        with patch.object(sys, "path", [str(scripts), *sys.path]):
            from project_management.cli import build_parser
        parser = build_parser()
        self.assertIsNone(parser.parse_args(["init", "demo"]).dir)
        self.assertEqual(parser.parse_args(["init", "demo", "--dir", "workspace"]).dir, "workspace")

    def test_portable_paths_preserves_code_data_and_markdown_whitespace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            script = stage / "preview.py"
            script_source = "hint = f'python3 skills/ppt-master/server.py {42}'\n"
            script.write_text(script_source, encoding="utf-8")
            manifest = stage / "manifest.json"
            manifest_source = '{"scan": ["skills/ppt-master/**/*.md"]}\n'
            manifest.write_text(manifest_source, encoding="utf-8")
            guide = stage / "guide.md"
            guide.write_text("python3 skills/ppt-master/server.py  \n`~/.agents/skills/ppt-master/.env`\n\n", encoding="utf-8")

            SYNC._portable_paths(stage)

            self.assertEqual(script.read_text(), script_source)
            self.assertEqual(manifest.read_text(), manifest_source)
            namespace = {}
            exec(script.read_text(), namespace)
            self.assertEqual(namespace["hint"], "python3 skills/ppt-master/server.py 42")
            self.assertEqual(guide.read_text(), "python3 {baseDir}/server.py  \n`{baseDir}/.env`\n\n")

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


if __name__ == "__main__":
    unittest.main()
