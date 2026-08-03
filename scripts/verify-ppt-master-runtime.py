#!/usr/bin/env python3
"""Verify portable runtime-path and media boundaries for ppt-master."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "openclaw-skills" / "ppt-master"
FORBIDDEN = (
    "${SKILL_DIR}",
    "image_gen.py",
    "notes_to_audio.py",
    "IMAGE_BACKEND",
    "image_backends",
    "tts_backends",
)
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
FULL_GIT_SHA = re.compile(r"[0-9a-f]{40}")


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def report(errors: list[str], path: Path, line: int, message: str) -> None:
    errors.append(f"{path.relative_to(ROOT)}:{line}: {message}")


def logical_commands(block: str) -> list[str]:
    commands: list[str] = []
    current = ""
    for raw in block.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        current = f"{current} {stripped}".strip()
        if current.endswith("\\"):
            current = current[:-1].rstrip()
            continue
        commands.append(current)
        current = ""
    if current:
        commands.append(current)
    return commands


def shell_blocks(text: str) -> list[tuple[int, str]]:
    blocks: list[tuple[int, str]] = []
    active = False
    include = False
    start_line = 0
    lines: list[str] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        if not active:
            opening = re.fullmatch(r"```([^`]*)", raw.strip())
            if opening:
                active = True
                include = opening.group(1).strip() in {"", "bash", "sh", "shell", "zsh"}
                start_line = number
                lines = []
            continue
        if raw.strip() == "```":
            if include:
                blocks.append((start_line, "\n".join(lines)))
            active = False
            include = False
            lines = []
            continue
        if include:
            lines.append(raw)
    return blocks


def verify_upstream_lock(errors: list[str]) -> None:
    path = SKILL / "upstream.lock.json"
    try:
        lock = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{path.relative_to(ROOT)}: cannot read upstream lock: {exc}")
        return

    if lock.get("repository") != "https://github.com/hugohe3/ppt-master.git":
        errors.append(f"{path.relative_to(ROOT)}: unexpected upstream repository")
    if lock.get("subtree") != "skills/ppt-master":
        errors.append(f"{path.relative_to(ROOT)}: unexpected upstream subtree")
    for field in ("base_commit", "reviewed_through"):
        value = lock.get(field)
        if not isinstance(value, str) or not FULL_GIT_SHA.fullmatch(value):
            errors.append(f"{path.relative_to(ROOT)}: {field} must be a full Git commit SHA")

    exclusions = lock.get("excluded_commits")
    if not isinstance(exclusions, list):
        errors.append(f"{path.relative_to(ROOT)}: excluded_commits must be a list")
        return
    commits: list[str] = []
    for index, item in enumerate(exclusions):
        if not isinstance(item, dict):
            errors.append(f"{path.relative_to(ROOT)}: excluded_commits[{index}] must be an object")
            continue
        commit = item.get("commit")
        reason = item.get("reason")
        if not isinstance(commit, str) or not FULL_GIT_SHA.fullmatch(commit):
            errors.append(f"{path.relative_to(ROOT)}: excluded_commits[{index}].commit must be a full Git SHA")
        else:
            commits.append(commit)
        if not isinstance(reason, str) or not reason.strip():
            errors.append(f"{path.relative_to(ROOT)}: excluded_commits[{index}].reason is required")
    if len(commits) != len(set(commits)):
        errors.append(f"{path.relative_to(ROOT)}: excluded commit SHAs must be unique")


def main() -> int:
    errors: list[str] = []
    verify_upstream_lock(errors)
    markdown_files = sorted(SKILL.rglob("*.md"))
    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            for match in re.finditer(re.escape(token), text):
                report(errors, path, line_number(text, match.start()), f"stale runtime/provider reference: {token}")
        for match in re.finditer(r"(?<!openclaw-)skills/ppt-master", text):
            line_start = text.rfind("\n", 0, match.start()) + 1
            line_end = text.find("\n", match.end())
            line = text[line_start : None if line_end < 0 else line_end]
            if "禁止假设" not in line:
                report(errors, path, line_number(text, match.start()), "installation-relative skills/ppt-master path")

        for block_line, block in shell_blocks(text):
            for command in logical_commands(block):
                if "project_manager.py init" in command and "--dir" not in command:
                    report(
                        errors,
                        path,
                        block_line,
                        "project initialization must pass --dir <absolute-projects-root>",
                    )
                script_match = re.search(r"\bpython3?\s+([^\s]+/scripts/[^\s]+)", command)
                if script_match and not script_match.group(1).lstrip("\"'").startswith("{baseDir}/scripts/"):
                    report(errors, path, block_line, f"script command must use {{baseDir}}: {command}")

        for match in MARKDOWN_LINK.finditer(text):
            target = match.group(1).strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:", "#", "{")):
                continue
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(SKILL.resolve())
            except ValueError:
                report(errors, path, line_number(text, match.start()), f"link escapes skill directory: {target}")
                continue
            if not resolved.exists():
                report(errors, path, line_number(text, match.start()), f"broken relative link: {target}")

    for removed in (
        "scripts/image_gen.py",
        "scripts/notes_to_audio.py",
        "scripts/image_backends",
        "scripts/tts_backends",
        "scripts/update_repo.py",
    ):
        if (SKILL / removed).exists():
            errors.append(f"openclaw-skills/ppt-master/{removed}: excluded upstream component is present")

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"OK: ppt-master runtime contract across {len(markdown_files)} Markdown files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
