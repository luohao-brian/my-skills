from __future__ import annotations

import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import font_preflight  # noqa: E402


class FontPreflightTests(unittest.TestCase):
    def tearDown(self) -> None:
        font_preflight.assess_font_family.cache_clear()
        font_preflight.discover_font_records.cache_clear()

    def test_macos_postscript_face_matches_family_and_emphasis(self) -> None:
        records = (
            font_preflight.FontRecord("PingFang SC", "PingFangSC-Regular", "regular"),
            font_preflight.FontRecord("PingFang SC", "PingFangSC-Semibold", "semibold"),
        )
        with patch.object(font_preflight, "discover_font_records", return_value=("atsutil", records)):
            assessment = font_preflight.assess_font_family("PingFang SC")
        self.assertTrue(assessment.available)
        self.assertTrue(assessment.has_emphasis_face)
        self.assertEqual(assessment.quality, "normal")

    def test_legacy_coverage_face_is_not_a_body_quality_choice(self) -> None:
        records = (font_preflight.FontRecord("Arial Unicode MS", "Arial Unicode MS", "regular"),)
        with patch.object(font_preflight, "discover_font_records", return_value=("atsutil", records)):
            assessment = font_preflight.assess_font_family("Arial Unicode MS")
        self.assertTrue(assessment.available)
        self.assertFalse(assessment.has_emphasis_face)
        self.assertEqual(assessment.quality, "legacy-coverage")

    def test_silent_substitution_is_unavailable(self) -> None:
        records = (font_preflight.FontRecord("Verdana", "Verdana", "regular"),)
        with patch.object(font_preflight, "discover_font_records", return_value=("fontconfig", records)):
            assessment = font_preflight.assess_font_family("Microsoft YaHei")
        self.assertFalse(assessment.available)
        self.assertIn("viewer substitution", assessment.issues[0])

    def test_missing_discovery_cannot_pass_cli_gate(self) -> None:
        with (
            patch.object(font_preflight, "discover_font_records", return_value=("unavailable", ())),
            patch.object(sys, "argv", ["font_preflight.py", "--family", "Example Sans", "--json"]),
            redirect_stdout(StringIO()),
        ):
            self.assertEqual(font_preflight.main(), 1)


if __name__ == "__main__":
    unittest.main()
