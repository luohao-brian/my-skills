from __future__ import annotations

import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from svg_quality.checker import SVGQualityChecker  # noqa: E402


class SvgBodyReadabilityTests(unittest.TestCase):
    def _result(self) -> dict:
        return {"errors": [], "warnings": [], "info": {}}

    def test_recurring_small_body_copy_is_blocking(self) -> None:
        root = ET.fromstring(
            """
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
              <g font-family="PingFang SC, Arial, sans-serif" font-size="15">
                <text x="80" y="180">第一条正文信息</text>
                <text x="80" y="220">第二条正文信息</text>
                <text x="80" y="260">第三条正文信息</text>
              </g>
            </svg>
            """
        )
        result = self._result()
        SVGQualityChecker()._check_generated_body_readability(
            root,
            Path("/tmp/deck/svg_output/P01.svg"),
            result,
            typography={
                "font_family": "PingFang SC, Arial, sans-serif",
                "body": "24",
                "footnote": "16",
            },
        )
        self.assertTrue(any("Body readability regression" in error for error in result["errors"]))

    def test_named_auxiliary_role_allows_its_own_size_band(self) -> None:
        root = ET.fromstring(
            """
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
              <g font-family="PingFang SC, Arial, sans-serif" font-size="15"
                 data-pptx-text-role="footnote">
                <text x="80" y="180">第一条补充说明</text>
                <text x="80" y="220">第二条补充说明</text>
                <text x="80" y="260">第三条补充说明</text>
              </g>
            </svg>
            """
        )
        result = self._result()
        SVGQualityChecker()._check_generated_body_readability(
            root,
            Path("/tmp/deck/svg_output/P01.svg"),
            result,
            typography={
                "font_family": "PingFang SC, Arial, sans-serif",
                "body": "24",
                "footnote": "16",
            },
        )
        self.assertEqual(result["errors"], [])


if __name__ == "__main__":
    unittest.main()
