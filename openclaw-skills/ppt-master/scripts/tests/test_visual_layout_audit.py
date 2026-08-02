from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from visual_layout_audit import _derived_viewports, _parse_viewports  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
