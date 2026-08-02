from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from svg_to_pptx.drawingml.utils import (  # noqa: E402
    parse_font_family,
    resolve_text_run_fonts,
)


class FontResolutionTests(unittest.TestCase):
    def test_arial_unicode_ms_is_an_east_asian_face(self) -> None:
        resolved = parse_font_family("Arial Unicode MS, Arial, sans-serif")
        self.assertEqual(resolved["latin"], "Arial")
        self.assertEqual(resolved["ea"], "Arial Unicode MS")

    def test_cjk_run_pins_all_slots_to_the_east_asian_face(self) -> None:
        resolved = resolve_text_run_fonts(
            "模型 / research",
            {"latin": "Arial", "ea": "Arial Unicode MS"},
        )
        self.assertEqual(
            resolved,
            {
                "latin": "Arial Unicode MS",
                "ea": "Arial Unicode MS",
                "cs": "Arial Unicode MS",
            },
        )

    def test_explicit_target_installed_pingfang_is_preserved(self) -> None:
        resolved = parse_font_family("PingFang SC, Arial, sans-serif")
        self.assertEqual(resolved["latin"], "Arial")
        self.assertEqual(resolved["ea"], "PingFang SC")


if __name__ == "__main__":
    unittest.main()
