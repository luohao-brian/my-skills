#!/usr/bin/env python3
"""Verify PPT Master's pinned release plus downstream runtime boundaries."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "openclaw-skills" / "ppt-master"
DOWNSTREAM = ROOT / "scripts" / "ppt_master_downstream"
MANIFEST = DOWNSTREAM / "manifest.json"
LOCK = SKILL / "upstream.lock.json"
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


def load_json(path: Path, errors: list[str]) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{path.relative_to(ROOT)}: cannot read JSON: {exc}")
        return {}
    if not isinstance(payload, dict):
        errors.append(f"{path.relative_to(ROOT)}: top level must be an object")
        return {}
    return payload


def verify_manifest(errors: list[str]) -> None:
    manifest = load_json(MANIFEST, errors)
    lock = load_json(LOCK, errors)
    if not manifest or not lock:
        return
    if manifest.get("schema_version") != 2 or lock.get("schema_version") != 2:
        errors.append("ppt-master sync manifest and published lock must use schema_version 2")
    upstream = lock.get("upstream")
    if not isinstance(upstream, dict):
        errors.append("openclaw-skills/ppt-master/upstream.lock.json: upstream must be an object")
        return
    expected = {
        "repository": manifest.get("repository"),
        "subtree": manifest.get("subtree"),
        "release": manifest.get("release"),
        "commit": manifest.get("release_commit"),
    }
    if upstream != expected:
        errors.append("published upstream lock does not match the downstream sync manifest")
    commit = upstream.get("commit")
    if not isinstance(commit, str) or not FULL_GIT_SHA.fullmatch(commit):
        errors.append("published upstream commit must be a full Git SHA")
    for field in (
        "packaging_transforms",
        "additive_overlays",
        "core_patches",
        "subsumed_by_upstream",
        "unsupported_upstream_features",
    ):
        if lock.get(field) != manifest.get(field, []):
            errors.append(f"published {field} does not match the sync manifest")
    overlays = manifest.get("additive_overlays")
    if isinstance(overlays, list):
        for raw in overlays:
            relative = Path(str(raw))
            source = DOWNSTREAM / "overlay" / relative
            published = SKILL / relative
            if not source.is_file():
                errors.append(f"missing overlay source: {source.relative_to(ROOT)}")
            elif not published.is_file():
                errors.append(f"missing published overlay: {published.relative_to(ROOT)}")
            elif source.read_bytes() != published.read_bytes():
                errors.append(f"published overlay drifted: {relative.as_posix()}")
    patches = manifest.get("core_patches")
    if isinstance(patches, list):
        for raw in patches:
            path = DOWNSTREAM / "patches" / str(raw)
            if not path.is_file():
                errors.append(f"missing core patch: {path.relative_to(ROOT)}")


def verify_runtime_files(errors: list[str]) -> None:
    required = (
        "references/runtime.md",
        "references/runtime-directory.md",
        "references/runtime-dependencies.md",
    )
    for relative in required:
        if not (SKILL / relative).is_file():
            errors.append(f"openclaw-skills/ppt-master/{relative}: required downstream runtime file is missing")
    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    if "[`references/runtime.md`](references/runtime.md)" not in skill_text:
        errors.append("SKILL.md does not make the downstream runtime contract mandatory")
    if "metadata: {\"openclaw\":" not in skill_text:
        errors.append("SKILL.md does not contain single-line OpenClaw metadata")
    if '\"primaryEnv\":\"ARK_AGENT_PLAN_API_KEY\"' not in skill_text:
        errors.append("SKILL.md does not expose the default Agent Plan credential as primaryEnv")
    metadata_line = next(line for line in skill_text.splitlines() if line.startswith("metadata: "))
    metadata = json.loads(metadata_line.removeprefix("metadata: "))
    if "ARK_AGENT_PLAN_API_KEY" in metadata["openclaw"].get("requires", {}).get("env", []):
        errors.append("optional Agent Plan credential is required for the whole skill")
    runtime_text = (SKILL / "references" / "runtime.md").read_text(encoding="utf-8")
    for name in ("runtime-directory.md", "runtime-dependencies.md"):
        if name not in runtime_text:
            errors.append(f"runtime.md does not load {name}")
    quick_text = (SKILL / "workflows" / "profiles" / "quick-generate.md").read_text(
        encoding="utf-8"
    )
    if "\\ --dir" in quick_text:
        errors.append("Quick project initialization contains an escaped-space --dir argument")
    if (SKILL / "scripts" / "attribution_guard.py").exists():
        errors.append("unsupported upstream attribution_guard.py is present")
    for path in sorted((SKILL / "scripts").rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if re.search(r"^\s*from attribution_guard import", text, re.MULTILINE):
            errors.append(f"{path.relative_to(ROOT)}: active attribution guard import survived packaging")
        if re.search(r"^\s*require_skill_integrity\(\)\s*$", text, re.MULTILINE):
            errors.append(f"{path.relative_to(ROOT)}: active attribution guard call survived packaging")
    if list(SKILL.rglob("README.md")):
        errors.append("README.md survived progressive-loading packaging")


def verify_markdown(errors: list[str]) -> None:
    markdown_files = sorted(SKILL.rglob("*.md"))
    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"(?<!openclaw-)skills/ppt-master", text):
            line_start = text.rfind("\n", 0, match.start()) + 1
            line_end = text.find("\n", match.end())
            line = text[line_start : None if line_end < 0 else line_end]
            # runtime.md defines how to resolve the unchanged upstream help paths.
            if "https://" in line or path.name in {"upstream-source.md", "runtime.md"}:
                continue
            report(errors, path, line_number(text, match.start()), "installation-relative skills/ppt-master path")
        for match in re.finditer(r"/(?:Users|home)/[^/\s]+/", text):
            report(errors, path, line_number(text, match.start()), "non-portable local absolute path")
        for block_line, block in shell_blocks(text):
            for command in logical_commands(block):
                if "project_manager.py init" in command and "--dir" not in command:
                    report(errors, path, block_line, "project initialization must pass --dir")
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
    if not markdown_files:
        errors.append("ppt-master has no Markdown files")


def verify_patch_effects(errors: list[str]) -> None:
    exporter = (SKILL / "scripts" / "svg_to_pptx" / "pptx_package" / "cli.py").read_text(encoding="utf-8")
    if not re.search(
        r"release_quality_gate\s*=\s*\(\s*args\.quick_generate\s*"
        r"or\s*args\.source\s+in\s+\{None,\s*'output'\}\s*\)",
        exporter,
    ):
        errors.append("upstream formal release fail-closed gate is missing")
    image_gen = (SKILL / "scripts" / "image_gen.py").read_text(encoding="utf-8")
    if '"ark-agent-plan": {' not in image_gen:
        errors.append("optional Agent Plan image backend is missing")
    volcengine = (SKILL / "scripts" / "image_backends" / "backend_volcengine.py").read_text(encoding="utf-8")
    for marker in ("ARK_AGENT_PLAN_ENDPOINT", "ARK_AGENT_PLAN_API_KEY"):
        if marker not in volcengine:
            errors.append(f"Volcengine image profile patch is missing {marker}")
    notes_to_audio = (SKILL / "scripts" / "notes_to_audio.py").read_text(encoding="utf-8")
    if "backend_volcengine.SUPPORTED_PROFILES" not in notes_to_audio:
        errors.append("provider TTS bridge core patch is not active")
    tts_volcengine = (
        SKILL / "scripts" / "tts_backends" / "backend_volcengine.py"
    ).read_text(encoding="utf-8")
    for marker in ("ark-agent-plan", "ARK_AGENT_PLAN_API_KEY"):
        if marker not in tts_volcengine:
            errors.append(f"Volcengine TTS profile adapter is missing {marker}")


def main() -> int:
    errors: list[str] = []
    verify_manifest(errors)
    verify_runtime_files(errors)
    verify_markdown(errors)
    verify_patch_effects(errors)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    markdown_count = len(list(SKILL.rglob("*.md")))
    lock = load_json(LOCK, [])
    upstream = lock.get("upstream") if isinstance(lock, dict) else None
    release = upstream.get("release", "unknown") if isinstance(upstream, dict) else "unknown"
    print(f"OK: ppt-master {release} runtime contract across {markdown_count} Markdown files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
