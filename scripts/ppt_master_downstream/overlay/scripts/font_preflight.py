#!/usr/bin/env python3
"""Cross-platform PowerPoint font availability and quality preflight."""

from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from functools import lru_cache


LEGACY_COVERAGE_FONTS = frozenset({
    "arial unicode",
    "arial unicode ms",
    "lucida sans unicode",
})
EMPHASIS_STYLE_TOKENS = (
    "bold",
    "semibold",
    "demibold",
    "heavy",
    "black",
    "extrabold",
    "ultrabold",
)


def normalize_family(value: str) -> str:
    return re.sub(r"[^0-9a-z]+", "", value.casefold())


@dataclass(frozen=True)
class FontRecord:
    family: str
    face: str
    style: str


@dataclass(frozen=True)
class FontAssessment:
    requested: str
    available: bool
    matched_families: tuple[str, ...]
    has_emphasis_face: bool
    discovery: str
    quality: str
    issues: tuple[str, ...]


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _macos_records() -> tuple[FontRecord, ...]:
    result = _run(["atsutil", "fonts", "-list"])
    if result.returncode:
        return ()
    records: list[FontRecord] = []
    for raw in result.stdout.splitlines():
        name = raw.strip()
        if not name or name.startswith("ATSU"):
            continue
        style = ""
        lowered = name.casefold()
        for token in EMPHASIS_STYLE_TOKENS + ("medium", "regular", "light", "thin"):
            if token in lowered:
                style = token
                break
        records.append(FontRecord(family=name, face=name, style=style))
    return tuple(records)


def _fontconfig_records() -> tuple[FontRecord, ...]:
    result = _run(["fc-list", "-f", "%{family}\t%{style}\n"])
    if result.returncode:
        return ()
    records: list[FontRecord] = []
    for raw in result.stdout.splitlines():
        family_text, _, style = raw.partition("\t")
        for family in family_text.split(","):
            family = family.strip()
            if family:
                records.append(FontRecord(family=family, face=family, style=style.strip()))
    return tuple(records)


def _windows_records() -> tuple[FontRecord, ...]:
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if not powershell:
        return ()
    command = (
        "$paths=@('HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts',"
        "'HKCU:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts');"
        "$paths|%{if(Test-Path $_){(Get-ItemProperty $_).PSObject.Properties|"
        "%{if($_.Name -notmatch '^PS'){ $_.Name }}}}"
    )
    result = _run([powershell, "-NoProfile", "-Command", command])
    if result.returncode:
        return ()
    records: list[FontRecord] = []
    for raw in result.stdout.splitlines():
        name = re.sub(r"\s*\((?:TrueType|OpenType)\)\s*$", "", raw.strip(), flags=re.I)
        if name:
            records.append(FontRecord(family=name, face=name, style=name))
    return tuple(records)


@lru_cache(maxsize=1)
def discover_font_records() -> tuple[str, tuple[FontRecord, ...]]:
    system = platform.system()
    if system == "Darwin" and shutil.which("atsutil"):
        records = _macos_records()
        if records:
            return "atsutil", records
    if shutil.which("fc-list"):
        records = _fontconfig_records()
        if records:
            return "fontconfig", records
    if system == "Windows":
        records = _windows_records()
        if records:
            return "windows-registry", records
    return "unavailable", ()


def _record_matches(requested: str, record: FontRecord) -> bool:
    wanted = normalize_family(requested)
    family = normalize_family(record.family)
    face = normalize_family(record.face)
    if wanted in {family, face}:
        return True
    style_suffixes = EMPHASIS_STYLE_TOKENS + (
        "medium",
        "regular",
        "italic",
        "light",
        "thin",
        "ultralight",
    )
    for candidate in (face, family):
        if candidate.startswith(wanted):
            suffix = candidate[len(wanted) :]
            if any(suffix.startswith(token) for token in style_suffixes):
                return True
    return False


@lru_cache(maxsize=128)
def assess_font_family(requested: str) -> FontAssessment:
    discovery, records = discover_font_records()
    matches = tuple(record for record in records if _record_matches(requested, record))
    matched_families = tuple(sorted({record.family for record in matches}, key=str.casefold))
    emphasis = any(
        any(token in f"{record.face} {record.style}".casefold() for token in EMPHASIS_STYLE_TOKENS)
        for record in matches
    )
    normalized = re.sub(r"\s+", " ", requested.strip().casefold())
    issues: list[str] = []
    quality = "normal"
    if normalized in LEGACY_COVERAGE_FONTS:
        quality = "legacy-coverage"
        issues.append(
            "legacy Unicode coverage face; do not use as a generated title/body font because CJK stroke weight and native bold support are weak"
        )
    if discovery == "unavailable":
        issues.append("no supported host font-discovery command is available")
    elif not matches:
        issues.append("requested family was not found exactly; viewer substitution would be nondeterministic")
    return FontAssessment(
        requested=requested,
        available=bool(matches),
        matched_families=matched_families,
        has_emphasis_face=emphasis,
        discovery=discovery,
        quality=quality,
        issues=tuple(issues),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify concrete PowerPoint font families on the current target host."
    )
    parser.add_argument("--family", action="append", required=True, help="Concrete family; repeat for every title/body/script face.")
    parser.add_argument("--require-emphasis", action="store_true", help="Require a real bold/semibold face for every requested family.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--allow-legacy-coverage", action="store_true", help="Allow a legacy Unicode coverage face after an explicit user decision.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    assessments = [assess_font_family(value) for value in dict.fromkeys(args.family)]
    failures: list[str] = []
    for assessment in assessments:
        if assessment.discovery == "unavailable":
            failures.append(f"{assessment.requested}: font discovery unavailable")
        elif not assessment.available:
            failures.append(f"{assessment.requested}: unavailable")
        if assessment.quality == "legacy-coverage" and not args.allow_legacy_coverage:
            failures.append(f"{assessment.requested}: legacy coverage font")
        if args.require_emphasis and assessment.available and not assessment.has_emphasis_face:
            failures.append(f"{assessment.requested}: no real bold/semibold face")

    payload = {
        "status": "failed" if failures else "passed",
        "assessments": [asdict(item) for item in assessments],
        "failures": failures,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for assessment in assessments:
            match = ", ".join(assessment.matched_families) or "none"
            print(
                f"{assessment.requested}: available={assessment.available} "
                f"emphasis={assessment.has_emphasis_face} quality={assessment.quality} "
                f"via={assessment.discovery} matches={match}"
            )
            for issue in assessment.issues:
                print(f"  warning: {issue}")
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
