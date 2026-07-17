#!/usr/bin/env python3
"""Prepare and verify image-generation tasks without calling an image provider.

The agent reads Pending tasks from the manifest, calls the image-generation
tool exposed by the current runtime, then records each returned local file.
This script only manages files and manifest state; it never makes network calls.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()

VALID_STATUSES = {"Pending", "Generated", "Failed"}
REQUIRED_FIELDS = ("filename", "prompt", "aspect_ratio", "status")
FORBIDDEN_FIELDS = {"provider", "backend", "model", "api_key", "apiKey"}
IMAGE_FORMATS = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".webp": "WEBP",
}


def tool_aspect_ratio(value: str) -> str:
    """Map an exact layout ratio to the generic image tool's three directions."""
    try:
        width, height = (float(part) for part in value.split(":", 1))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid aspect_ratio '{value}'; expected W:H") from exc
    if width <= 0 or height <= 0:
        raise ValueError(f"invalid aspect_ratio '{value}'; values must be positive")
    if abs(width - height) < 1e-9:
        return "square"
    return "landscape" if width > height else "portrait"


def load_manifest(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"invalid JSON in {path}: {exc.msg} (line {exc.lineno}, col {exc.colno})"
        ) from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top level must be an object")
    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError(f"{path}: items must be a non-empty array")

    seen: set[str] = set()
    for index, item in enumerate(items):
        prefix = f"{path}: items[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{prefix} must be an object")
        forbidden = sorted(FORBIDDEN_FIELDS.intersection(item))
        if forbidden:
            raise ValueError(f"{prefix} contains provider-owned fields: {', '.join(forbidden)}")
        for field in REQUIRED_FIELDS:
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{prefix}.{field} must be a non-empty string")
        filename = item["filename"]
        candidate = Path(filename)
        if candidate.is_absolute() or candidate.name != filename or ".." in candidate.parts:
            raise ValueError(f"{prefix}.filename must be a plain filename")
        if filename in seen:
            raise ValueError(f"{prefix}.filename duplicates '{filename}'")
        seen.add(filename)
        if item["status"] not in VALID_STATUSES:
            raise ValueError(
                f"{prefix}.status must be one of {sorted(VALID_STATUSES)}"
            )
        tool_aspect_ratio(item["aspect_ratio"])
    return data


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


def task_view(item: dict, manifest_path: Path) -> dict:
    return {
        "filename": item["filename"],
        "prompt": item["prompt"],
        "aspect_ratio": tool_aspect_ratio(item["aspect_ratio"]),
        "requested_aspect_ratio": item["aspect_ratio"],
        "output_path": str((manifest_path.parent / item["filename"]).resolve()),
    }


def render_markdown(data: dict) -> str:
    lines = [
        "# Image Generation Tasks",
        "",
        "> Generated from `image_prompts.json` by `image_manifest.py render-md`.",
        "> The image tool receives `Prompt` and `Tool aspect`; the exact layout ratio remains in the manifest.",
        "",
    ]
    for index, item in enumerate(data["items"], start=1):
        lines.extend(
            [
                f"## {index}. {item['filename']}",
                "",
                f"- Status: `{item['status']}`",
                f"- Requested ratio: `{item['aspect_ratio']}`",
                f"- Tool aspect: `{tool_aspect_ratio(item['aspect_ratio'])}`",
                "",
                "**Prompt**",
                "",
                item["prompt"],
                "",
            ]
        )
        if item.get("last_error"):
            lines.extend([f"**Last error:** {item['last_error']}", ""])
    return "\n".join(lines).rstrip() + "\n"


def find_item(data: dict, filename: str) -> dict:
    for item in data["items"]:
        if item["filename"] == filename:
            return item
    raise ValueError(f"filename not found in manifest: {filename}")


def image_info(path: Path) -> tuple[int, int, str]:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"image file is missing or empty: {path}")
    try:
        from PIL import Image
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            return image.width, image.height, image.format or path.suffix.lstrip(".").upper()
    except Exception as exc:
        raise ValueError(f"invalid image file {path}: {exc}") from exc


def record_image(manifest_path: Path, data: dict, filename: str, source: Path) -> Path:
    item = find_item(data, filename)
    target = manifest_path.parent / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != target.resolve():
        try:
            from PIL import Image
        except ImportError as exc:
            raise ValueError("Pillow is required to record image-tool output") from exc
        output_format = IMAGE_FORMATS.get(target.suffix.lower())
        if output_format is None:
            raise ValueError(f"unsupported image output extension: {target.suffix}")
        with Image.open(source) as image:
            if output_format == "JPEG" and image.mode in ("RGBA", "LA", "P"):
                image = image.convert("RGB")
            image.save(target, format=output_format)
    width, height, image_format = image_info(target)
    item["status"] = "Generated"
    item["actual_width"] = width
    item["actual_height"] = height
    item["actual_format"] = image_format
    item.pop("last_error", None)
    save_manifest(manifest_path, data)
    return target


def verify_images(manifest_path: Path, data: dict) -> list[str]:
    errors: list[str] = []
    changed = False
    for item in data["items"]:
        target = manifest_path.parent / item["filename"]
        if item["status"] != "Generated":
            errors.append(f"{item['filename']}: status={item['status']}")
            continue
        try:
            width, height, image_format = image_info(target)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        actual = (item.get("actual_width"), item.get("actual_height"), item.get("actual_format"))
        if actual != (width, height, image_format):
            item["actual_width"] = width
            item["actual_height"] = height
            item["actual_format"] = image_format
            changed = True
    if changed:
        save_manifest(manifest_path, data)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("check", "pending", "render-md", "verify"):
        command = subparsers.add_parser(name)
        command.add_argument("manifest", type=Path)

    record = subparsers.add_parser("record")
    record.add_argument("manifest", type=Path)
    record.add_argument("filename")
    record.add_argument("--source", type=Path, required=True)

    failed = subparsers.add_parser("fail")
    failed.add_argument("manifest", type=Path)
    failed.add_argument("filename")
    failed.add_argument("--error", required=True)

    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    data = load_manifest(manifest_path)

    if args.command == "check":
        print(f"OK: {len(data['items'])} image task(s)")
        return 0
    if args.command == "pending":
        tasks = [task_view(item, manifest_path) for item in data["items"] if item["status"] != "Generated"]
        print(json.dumps({"tasks": tasks}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "render-md":
        output = manifest_path.with_suffix(".md")
        output.write_text(render_markdown(data), encoding="utf-8")
        print(output)
        return 0
    if args.command == "record":
        target = record_image(manifest_path, data, args.filename, args.source.resolve())
        print(target)
        return 0
    if args.command == "fail":
        item = find_item(data, args.filename)
        item["status"] = "Failed"
        item["last_error"] = args.error[:500]
        save_manifest(manifest_path, data)
        print(f"Failed: {args.filename}")
        return 0

    errors = verify_images(manifest_path, data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: {len(data['items'])} generated image(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
