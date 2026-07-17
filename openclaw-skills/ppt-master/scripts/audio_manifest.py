#!/usr/bin/env python3
"""Prepare and verify per-slide TTS tasks without calling a TTS provider.

The agent calls the TTS tool exposed by the current runtime with each task's
text and output_path. This script only manages task state and validates files.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from console_encoding import configure_utf8_stdio
from audio_duration import probe_audio_duration

configure_utf8_stdio()

VALID_STATUSES = {"Pending", "Generated", "Failed"}
SUPPORTED_AUDIO = {".mp3", ".m4a", ".wav"}


def natural_key(path: Path) -> list[object]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name)]


def spoken_text(markdown: str) -> str:
    lines: list[str] = []
    for raw in markdown.splitlines():
        if raw.lstrip().startswith("#"):
            continue
        line = raw.rstrip()
        if not line.strip():
            if lines and lines[-1] != "":
                lines.append("")
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def save_manifest(path: Path, data: dict) -> None:
    fd, temp_name = tempfile.mkstemp(prefix=f"{path.stem}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


def load_manifest(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc.msg}") from exc
    tasks = data.get("tasks") if isinstance(data, dict) else None
    if not isinstance(tasks, list) or not tasks:
        raise ValueError(f"{path}: tasks must be a non-empty array")
    seen: set[str] = set()
    for index, task in enumerate(tasks):
        prefix = f"{path}: tasks[{index}]"
        for field in ("slide", "note_path", "text", "output_path", "status"):
            value = task.get(field) if isinstance(task, dict) else None
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{prefix}.{field} must be a non-empty string")
        if task["slide"] in seen:
            raise ValueError(f"{prefix}.slide duplicates '{task['slide']}'")
        seen.add(task["slide"])
        if task["status"] not in VALID_STATUSES:
            raise ValueError(f"{prefix}.status must be one of {sorted(VALID_STATUSES)}")
        if Path(task["output_path"]).suffix.lower() not in SUPPORTED_AUDIO:
            raise ValueError(f"{prefix}.output_path must end in mp3, m4a, or wav")
        forbidden = {"provider", "backend", "model", "voice", "voice_id"}.intersection(task)
        if forbidden:
            raise ValueError(f"{prefix} contains runtime-owned fields: {', '.join(sorted(forbidden))}")
    return data


def prepare(project: Path) -> Path:
    project = project.resolve()
    notes_dir = project / "notes"
    audio_dir = project / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    note_files = sorted(
        (path for path in notes_dir.glob("*.md") if path.name != "total.md"),
        key=natural_key,
    )
    if not note_files:
        raise ValueError(f"no per-slide notes found in {notes_dir}")

    manifest_path = audio_dir / "audio_tasks.json"
    previous: dict[str, dict] = {}
    if manifest_path.exists():
        try:
            previous = {task["slide"]: task for task in load_manifest(manifest_path)["tasks"]}
        except ValueError:
            previous = {}

    tasks: list[dict] = []
    for note in note_files:
        text = spoken_text(note.read_text(encoding="utf-8"))
        if not text:
            raise ValueError(f"empty spoken text: {note}")
        old = previous.get(note.stem, {})
        old_output = Path(old.get("output_path", "")) if old.get("output_path") else None
        if old_output and old_output.suffix.lower() in SUPPORTED_AUDIO and old_output.is_file():
            output = old_output.resolve()
        else:
            output = (audio_dir / f"{note.stem}.mp3").resolve()
        status = "Generated" if output.is_file() and output.stat().st_size > 0 else "Pending"
        task = {
            "slide": note.stem,
            "note_path": str(note.resolve()),
            "text": text,
            "output_path": str(output),
            "status": status,
        }
        if status == "Generated" and old.get("duration_seconds"):
            task["duration_seconds"] = old["duration_seconds"]
        tasks.append(task)

    save_manifest(manifest_path, {"project": str(project), "tasks": tasks})
    return manifest_path


def find_task(data: dict, slide: str) -> dict:
    for task in data["tasks"]:
        if task["slide"] == slide:
            return task
    raise ValueError(f"slide not found in manifest: {slide}")


def duration_seconds(path: Path) -> float:
    value = probe_audio_duration(path)
    if value is None:
        raise ValueError(f"could not read a positive audio duration: {path}")
    return value


def record_audio(manifest_path: Path, data: dict, slide: str, source: Path) -> Path:
    task = find_task(data, slide)
    target = Path(task["output_path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != target.resolve():
        source_suffix = source.suffix.lower()
        if source_suffix not in SUPPORTED_AUDIO:
            raise ValueError("the TTS tool must return mp3, m4a, or wav audio")
        target = target.with_suffix(source_suffix)
        shutil.copy2(source, target)
        task["output_path"] = str(target.resolve())
    if not target.is_file() or target.stat().st_size == 0:
        raise ValueError(f"audio file is missing or empty: {target}")
    task["duration_seconds"] = round(duration_seconds(target), 3)
    task["status"] = "Generated"
    task.pop("last_error", None)
    save_manifest(manifest_path, data)
    return target


def verify_audio(manifest_path: Path, data: dict) -> list[str]:
    errors: list[str] = []
    changed = False
    for task in data["tasks"]:
        path = Path(task["output_path"])
        if task["status"] != "Generated":
            errors.append(f"{task['slide']}: status={task['status']}")
            continue
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"audio file is missing or empty: {path}")
            continue
        try:
            duration = round(duration_seconds(path), 3)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if task.get("duration_seconds") != duration:
            task["duration_seconds"] = duration
            changed = True
    if changed:
        save_manifest(manifest_path, data)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("project", type=Path)
    for name in ("check", "pending", "verify"):
        command = subparsers.add_parser(name)
        command.add_argument("manifest", type=Path)

    record = subparsers.add_parser("record")
    record.add_argument("manifest", type=Path)
    record.add_argument("slide")
    record.add_argument("--source", type=Path, required=True)

    failed = subparsers.add_parser("fail")
    failed.add_argument("manifest", type=Path)
    failed.add_argument("slide")
    failed.add_argument("--error", required=True)

    args = parser.parse_args()
    if args.command == "prepare":
        print(prepare(args.project))
        return 0

    manifest_path = args.manifest.resolve()
    data = load_manifest(manifest_path)
    if args.command == "check":
        print(f"OK: {len(data['tasks'])} audio task(s)")
        return 0
    if args.command == "pending":
        tasks = [task for task in data["tasks"] if task["status"] != "Generated"]
        print(json.dumps({"tasks": tasks}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "record":
        print(record_audio(manifest_path, data, args.slide, args.source.resolve()))
        return 0
    if args.command == "fail":
        task = find_task(data, args.slide)
        task["status"] = "Failed"
        task["last_error"] = args.error[:500]
        save_manifest(manifest_path, data)
        print(f"Failed: {args.slide}")
        return 0

    errors = verify_audio(manifest_path, data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: {len(data['tasks'])} narration file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
