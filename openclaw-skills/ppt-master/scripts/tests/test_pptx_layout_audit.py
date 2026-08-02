from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from pptx_layout_audit import (  # noqa: E402
    IDENTITY,
    _has_invalid_size,
    _iter_leaf_shapes,
)


class FakeShape:
    def __init__(self, name: str, left: int, top: int, width: int, height: int, kind: str = "TEXT_BOX"):
        self.name = name
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.rotation = 0.0
        self.shape_type = SimpleNamespace(name=kind)


class FakeGroup:
    def __init__(self, name: str, shapes: list[object], xfrm: object):
        self.name = name
        self.shapes = shapes
        self._element = SimpleNamespace(grpSpPr=SimpleNamespace(xfrm=xfrm))


def transform(*, off_x: int, off_y: int, ext_x: int, ext_y: int, child_x: int, child_y: int, child_w: int, child_h: int):
    return SimpleNamespace(
        off=SimpleNamespace(x=off_x, y=off_y),
        ext=SimpleNamespace(cx=ext_x, cy=ext_y),
        chOff=SimpleNamespace(x=child_x, y=child_y),
        chExt=SimpleNamespace(cx=child_w, cy=child_h),
        rot=0.0,
        flipH=False,
        flipV=False,
    )


class LayoutGeometryTests(unittest.TestCase):
    def test_group_child_is_mapped_to_slide_coordinates(self) -> None:
        child = FakeShape("child", 100, 50, 200, 100)
        group = FakeGroup(
            "group",
            [child],
            transform(
                off_x=1000,
                off_y=2000,
                ext_x=1000,
                ext_y=500,
                child_x=0,
                child_y=0,
                child_w=500,
                child_h=250,
            ),
        )
        records = list(_iter_leaf_shapes([group], transform=IDENTITY))
        self.assertEqual(records[0][1], "slide/group/child")
        self.assertEqual(records[0][2], {"x": 1200, "y": 2100, "width": 400, "height": 200})

    def test_nested_group_transform_is_composed(self) -> None:
        child = FakeShape("child", 10, 20, 30, 40)
        inner = FakeGroup(
            "inner",
            [child],
            transform(off_x=100, off_y=200, ext_x=100, ext_y=100, child_x=0, child_y=0, child_w=100, child_h=100),
        )
        outer = FakeGroup(
            "outer",
            [inner],
            transform(off_x=1000, off_y=2000, ext_x=200, ext_y=200, child_x=0, child_y=0, child_w=200, child_h=200),
        )
        box = list(_iter_leaf_shapes([outer]))[0][2]
        self.assertEqual(box, {"x": 1110, "y": 2220, "width": 30, "height": 40})

    def test_horizontal_or_vertical_connector_is_not_degenerate(self) -> None:
        horizontal = FakeShape("line", 0, 0, 100, 0, kind="LINE")
        vertical = FakeShape("line", 0, 0, 0, 100, kind="LINE")
        point = FakeShape("point", 0, 0, 0, 0, kind="LINE")
        self.assertFalse(_has_invalid_size(horizontal, {"width": 100, "height": 0}))
        self.assertFalse(_has_invalid_size(vertical, {"width": 0, "height": 100}))
        self.assertTrue(_has_invalid_size(point, {"width": 0, "height": 0}))

    def test_non_connector_with_one_zero_dimension_is_invalid(self) -> None:
        shape = FakeShape("box", 0, 0, 100, 0)
        self.assertTrue(_has_invalid_size(shape, {"width": 100, "height": 0}))


if __name__ == "__main__":
    unittest.main()
