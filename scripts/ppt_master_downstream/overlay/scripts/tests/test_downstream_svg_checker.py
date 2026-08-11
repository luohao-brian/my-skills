from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import downstream_svg_checker as checker  # noqa: E402


class DownstreamSvgCheckerTests(unittest.TestCase):
    def _svg(self, body: str) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "P01.svg"
        path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">'
            + body
            + "</svg>",
            encoding="utf-8",
        )
        return temporary, path

    @staticmethod
    def _available() -> SimpleNamespace:
        return SimpleNamespace(
            discovery="test",
            available=True,
            quality="normal",
            has_emphasis_face=True,
        )

    def test_implicit_ea_default_is_blocking_even_when_installed(self) -> None:
        temporary, path = self._svg(
            '<text id="stats" font-family="Menlo">中文 / 42%</text>'
        )
        self.addCleanup(temporary.cleanup)
        with patch.object(checker, "assess_font_family", return_value=self._available()):
            findings = checker.check_svg(path)
        issue = next(item for item in findings if item["code"] == "missing-explicit-ea-face")
        self.assertEqual(issue["element"], "#stats")
        self.assertEqual(issue["source_stack"], "Menlo")
        self.assertEqual(issue["resolved_ea"], "Microsoft YaHei")

    def test_mixed_script_checks_latin_and_ea_faces(self) -> None:
        temporary, path = self._svg(
            '<text font-family="Menlo, PingFang SC">中文 / research</text>'
        )
        self.addCleanup(temporary.cleanup)
        seen: list[str] = []

        def assess(family: str) -> SimpleNamespace:
            seen.append(family)
            return self._available()

        with patch.object(checker, "assess_font_family", side_effect=assess):
            self.assertEqual(checker.check_svg(path), [])
        self.assertEqual(seen, ["Menlo", "PingFang SC"])

    def test_named_auxiliary_role_uses_its_own_band(self) -> None:
        temporary, path = self._svg(
            '<g font-family="Arial, PingFang SC" font-size="15" '
            'data-pptx-text-role="footnote">'
            '<text>第一条补充说明</text><text>第二条补充说明</text>'
            '<text>第三条补充说明</text></g>'
        )
        self.addCleanup(temporary.cleanup)
        typography = {
            "font_family": "Arial, PingFang SC",
            "body": "24",
            "footnote": "16",
        }
        with patch.object(checker, "assess_font_family", return_value=self._available()):
            self.assertEqual(checker.check_svg(path, typography=typography), [])


if __name__ == "__main__":
    unittest.main()
