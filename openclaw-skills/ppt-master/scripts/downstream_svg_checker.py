#!/usr/bin/env python3
"""Downstream target-host font and body-readability gate for authored SVG."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from font_preflight import assess_font_family  # noqa: E402
from project_management.project_specs import parse_spec_lock  # noqa: E402
from svg_to_pptx.drawingml.utils import (  # noqa: E402
    EA_FONTS,
    is_cjk_char,
    parse_font_family,
)


SCHEMA = "ppt-master.downstream-svg-report.v1"
FONT_SIZE_TOLERANCE_PX = 2.0
SMALL_BODY_MAX_UNLABELED = 2


def _local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _element_label(element: ET.Element) -> str:
    identifier = (element.get("id") or "").strip()
    return f"#{identifier}" if identifier else f"<{_local_name(element)}>"


def _inline_style(element: ET.Element) -> dict[str, str]:
    values: dict[str, str] = {}
    for part in (element.get("style") or "").split(";"):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        values[key.strip().casefold()] = value.strip()
    return values


def _effective_value(
    element: ET.Element,
    name: str,
    parents: dict[ET.Element, ET.Element],
) -> str | None:
    current: ET.Element | None = element
    key = name.casefold()
    while current is not None:
        direct = current.get(name)
        if direct is not None and direct.strip():
            return direct.strip()
        styled = _inline_style(current).get(key)
        if styled:
            return styled
        current = parents.get(current)
    return None


def _stack_families(stack: str) -> tuple[str, ...]:
    return tuple(
        value.strip().strip("'\"")
        for value in stack.split(",")
        if value.strip().strip("'\"")
    )


def _script_flags(text: str) -> tuple[bool, bool, tuple[str, ...]]:
    east_asian = False
    latin = False
    scripts: set[str] = set()
    for char in text:
        codepoint = ord(char)
        if is_cjk_char(char):
            east_asian = True
            if 0x3040 <= codepoint <= 0x30FF or 0x31F0 <= codepoint <= 0x31FF:
                scripts.add("kana")
            elif 0x1100 <= codepoint <= 0x11FF or 0xAC00 <= codepoint <= 0xD7FF:
                scripts.add("hangul")
            else:
                scripts.add("han-or-ea")
            continue
        if unicodedata.category(char).startswith(("L", "N")):
            latin = True
            scripts.add("latin")
    return latin, east_asian, tuple(sorted(scripts))


def _is_emphasis(raw_weight: str | None) -> bool:
    value = (raw_weight or "").strip().casefold()
    if value in {"bold", "bolder", "semibold"}:
        return True
    try:
        return int(float(value)) >= 600
    except ValueError:
        return False


def _font_findings(root: ET.Element, svg_path: Path) -> list[dict[str, object]]:
    parents = {child: parent for parent in root.iter() for child in parent}
    findings: list[dict[str, object]] = []
    for element in root.iter():
        if _local_name(element).casefold() not in {"text", "tspan"}:
            continue
        fragment = re.sub(r"\s+", " ", element.text or "").strip()
        if not fragment:
            continue
        stack = _effective_value(element, "font-family", parents)
        if not stack:
            continue
        has_latin, has_ea, scripts = _script_flags(fragment)
        resolved = parse_font_family(stack)
        families = _stack_families(stack)
        explicit_ea = next((family for family in families if family in EA_FONTS), None)
        common = {
            "file": svg_path.name,
            "element": _element_label(element),
            "source_stack": stack,
            "scripts": list(scripts),
            "resolved_latin": resolved["latin"],
            "resolved_ea": resolved["ea"],
        }
        if has_ea and explicit_ea is None:
            findings.append({
                **common,
                "severity": "error",
                "code": "missing-explicit-ea-face",
                "message": "East Asian text relies on an implicit exporter default",
                "remediation": "append an installed East Asian face to the source font-family stack",
            })

        roles: list[str] = []
        if has_latin:
            roles.append("latin")
        if has_ea:
            roles.append("ea")
        weight = _effective_value(element, "font-weight", parents)
        for role in roles:
            family = resolved[role]
            assessment = assess_font_family(family)
            if assessment.discovery == "unavailable":
                findings.append({
                    **common,
                    "severity": "error",
                    "code": "font-discovery-unavailable",
                    "role": role,
                    "family": family,
                    "message": "target-host font discovery is unavailable",
                    "remediation": "run on the target host with supported font discovery before release",
                })
                continue
            if not assessment.available:
                findings.append({
                    **common,
                    "severity": "error",
                    "code": "font-not-installed",
                    "role": role,
                    "family": family,
                    "message": f"{role} face is not installed on the target host",
                    "remediation": f"select and explicitly name an installed {role} face",
                })
            if assessment.quality == "legacy-coverage":
                findings.append({
                    **common,
                    "severity": "error",
                    "code": "legacy-coverage-face",
                    "role": role,
                    "family": family,
                    "message": "legacy Unicode coverage face is not an approved generated-deck role face",
                    "remediation": "select a contemporary installed face with native role weights",
                })
            if _is_emphasis(weight) and assessment.available and not assessment.has_emphasis_face:
                findings.append({
                    **common,
                    "severity": "error",
                    "code": "synthetic-emphasis",
                    "role": role,
                    "family": family,
                    "message": "emphasized text would use a synthesized weight",
                    "remediation": "select a family with a real bold or semibold face",
                })
    return findings


def _normalized_stack(stack: str) -> tuple[str, ...]:
    return tuple(value.casefold() for value in _stack_families(stack))


def _size_value(raw: str | None) -> float | None:
    try:
        value = float((raw or "").strip().removesuffix("px"))
    except ValueError:
        return None
    return value if math.isfinite(value) and value > 0 else None


def _readability_findings(
    root: ET.Element,
    svg_path: Path,
    typography: dict[str, str],
) -> list[dict[str, object]]:
    body_size = _size_value(typography.get("body"))
    body_stack = typography.get("body_family", "").strip() or typography.get("font_family", "").strip()
    if body_size is None or not body_stack:
        return []
    parents = {child: parent for parent in root.iter() for child in parent}
    candidates: Counter[str] = Counter()
    examples: dict[str, str] = {}
    element_examples: dict[str, str] = {}
    viewbox = [part for part in re.split(r"[\s,]+", root.get("viewBox") or "") if part]
    try:
        canvas_height = float(viewbox[3]) if len(viewbox) == 4 else None
    except ValueError:
        canvas_height = None
    findings: list[dict[str, object]] = []
    for element in root.iter():
        if _local_name(element).casefold() not in {"text", "tspan"}:
            continue
        fragment = re.sub(r"\s+", " ", element.text or "").strip()
        if len(fragment) < 4:
            continue
        stack = _effective_value(element, "font-family", parents)
        if not stack or _normalized_stack(stack) != _normalized_stack(body_stack):
            continue
        size = _size_value(_effective_value(element, "font-size", parents))
        if size is None or size >= body_size - FONT_SIZE_TOLERANCE_PX:
            continue
        if _is_emphasis(_effective_value(element, "font-weight", parents)):
            continue
        role = (_effective_value(element, "data-pptx-text-role", parents) or "").strip()
        if role:
            anchor = _size_value(typography.get(role))
            if anchor is None:
                findings.append({
                    "severity": "error",
                    "code": "unknown-text-role",
                    "file": svg_path.name,
                    "element": _element_label(element),
                    "message": f"data-pptx-text-role={role!r} has no numeric typography anchor",
                    "remediation": "declare the named role in spec_lock typography or remove the role",
                })
            elif abs(size - anchor) > FONT_SIZE_TOLERANCE_PX:
                findings.append({
                    "severity": "error",
                    "code": "text-role-size-mismatch",
                    "file": svg_path.name,
                    "element": _element_label(element),
                    "message": f"{role} uses {size:g}px outside {anchor:g}px ±{FONT_SIZE_TOLERANCE_PX:g}px",
                    "remediation": "return the element to its declared typography role band",
                })
            continue
        y = _size_value(_effective_value(element, "y", parents))
        if canvas_height and y is not None and y >= canvas_height * 0.90:
            continue
        if re.search(r"(?:https?://|www\.|\b[\w.-]+\.(?:com|org|net|io|ai|cn)\b)", fragment, re.I):
            continue
        key = f"{size:g}"
        candidates[key] += 1
        examples.setdefault(key, fragment[:48])
        element_examples.setdefault(key, _element_label(element))
    for size, count in sorted(candidates.items()):
        if count <= SMALL_BODY_MAX_UNLABELED:
            continue
        findings.append({
            "severity": "error",
            "code": "body-readability-regression",
            "file": svg_path.name,
            "element": element_examples[size],
            "occurrences": count,
            "body_size": body_size,
            "observed_size": float(size),
            "message": f"recurring normal-weight body-family text uses {size}px below the {body_size:g}px body band",
            "example": examples[size],
            "remediation": "increase it to the body band or name an intentional auxiliary typography role",
        })
    return findings


def check_svg(
    svg_path: Path,
    *,
    typography: dict[str, str] | None = None,
) -> list[dict[str, object]]:
    root = ET.parse(svg_path).getroot()
    findings = _font_findings(root, svg_path)
    if typography:
        findings.extend(_readability_findings(root, svg_path, typography))
    return findings


def _fingerprint(svg_files: list[Path]) -> dict[str, object]:
    aggregate = hashlib.sha256()
    files: list[dict[str, str]] = []
    for path in svg_files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        files.append({"file": path.name, "sha256": digest})
        aggregate.update(path.name.encode())
        aggregate.update(b"\0")
        aggregate.update(digest.encode())
        aggregate.update(b"\n")
    return {
        "algorithm": "sha256",
        "digest": aggregate.hexdigest(),
        "file_count": len(files),
        "files": files,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check target-host font stacks and body readability for PPT Master SVGs."
    )
    parser.add_argument("project_path", type=Path)
    parser.add_argument("--quick-generate", action="store_true")
    parser.add_argument("--json-output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project = args.project_path.expanduser().resolve()
    svg_files = sorted((project / "svg_output").glob("*.svg"))
    if not svg_files:
        print(f"FAIL: no SVG files found in {project / 'svg_output'}", file=sys.stderr)
        return 1
    typography: dict[str, str] = {}
    if not args.quick_generate:
        lock_path = project / "spec_lock.md"
        if not lock_path.is_file():
            print(f"FAIL: missing {lock_path}", file=sys.stderr)
            return 1
        typography = parse_spec_lock(lock_path).get("typography", {})
    findings: list[dict[str, object]] = []
    for svg_path in svg_files:
        try:
            findings.extend(check_svg(svg_path, typography=typography))
        except (OSError, ET.ParseError, ValueError) as exc:
            findings.append({
                "severity": "error",
                "code": "svg-unreadable",
                "file": svg_path.name,
                "message": str(exc),
                "remediation": "repair the authored SVG and rerun the downstream checker",
            })
    blocking = [item for item in findings if item.get("severity") == "error"]
    payload = {
        "schema": SCHEMA,
        "status": "failed" if blocking else "passed",
        "project": str(project),
        "source_fingerprint": _fingerprint(svg_files),
        "summary": {"blocking": len(blocking), "findings": len(findings)},
        "findings": findings,
    }
    output = args.json_output or project / "validation" / "downstream_svg_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for finding in findings:
        print(json.dumps(finding, ensure_ascii=False, separators=(",", ":")))
    print(f"[DOWNSTREAM-SVG] status={payload['status']} blocking={len(blocking)} report={output}")
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
