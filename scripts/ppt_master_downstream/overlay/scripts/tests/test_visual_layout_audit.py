from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from visual_layout_audit import (  # noqa: E402
    _derived_viewports,
    _discover_preview_url,
    _parse_viewports,
    _server_log_tail,
    preview_server,
)


class ViewportTests(unittest.TestCase):
    def test_auto_viewports_cover_four_equivalence_classes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            svg = Path(directory) / "slide.svg"
            svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720"/>', encoding="utf-8")
            self.assertEqual(
                _derived_viewports(svg),
                [(1280, 720), (858, 482), (1600, 720), (1280, 900)],
            )

    def test_explicit_viewports_remain_supported(self) -> None:
        self.assertEqual(_parse_viewports("1024x768,720x1280"), [(1024, 768), (720, 1280)])


class PreviewServerTests(unittest.TestCase):
    def test_discovers_healthy_server_for_same_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            lock = project / "live_preview" / "lock.json"
            lock.parent.mkdir()
            lock.write_text('{"pid": 42, "port": 6060}\n', encoding="utf-8")
            health = {
                "status": "ok",
                "service": "live_preview",
                "project": str(project),
            }
            with mock.patch("visual_layout_audit._read_json", return_value=health):
                self.assertEqual(_discover_preview_url(project), "http://127.0.0.1:6060")

    def test_ignores_server_for_another_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            lock = project / "live_preview" / "lock.json"
            lock.parent.mkdir()
            lock.write_text('{"pid": 42, "port": 6060}\n', encoding="utf-8")
            health = {
                "status": "ok",
                "service": "live_preview",
                "project": str(project / "other"),
            }
            with mock.patch("visual_layout_audit._read_json", return_value=health):
                self.assertIsNone(_discover_preview_url(project))

    def test_preview_context_reuses_discovered_server_without_spawning(self) -> None:
        project = Path("/tmp/ppt-master-layout-audit-test").resolve()
        with (
            mock.patch(
                "visual_layout_audit._discover_preview_url",
                return_value="http://127.0.0.1:6060",
            ),
            mock.patch("visual_layout_audit.subprocess.Popen") as popen,
        ):
            with preview_server(project, None) as url:
                self.assertEqual(url, "http://127.0.0.1:6060")
            popen.assert_not_called()

    def test_server_log_tail_decodes_and_limits_output(self) -> None:
        with tempfile.TemporaryFile(mode="w+b") as log:
            log.write(("prefix\n" + "x" * 20 + "\nport conflict\n").encode())
            self.assertEqual(_server_log_tail(log, limit=14), "port conflict")


if __name__ == "__main__":
    unittest.main()
