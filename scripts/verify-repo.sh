#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
NODE_BIN="${NODE_BIN:-node}"

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "$1 is required"
}

[[ -x "$PYTHON_BIN" ]] || require_command "$PYTHON_BIN"

# Repository-wide deterministic invariants only. Component behavior belongs in
# scripts/verify-<component>.sh and is intentionally not imported here.
"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path.cwd()
COLLECTIONS = (ROOT / "info-track", ROOT / "openclaw-skills")
errors: list[str] = []
skill_files: list[Path] = []


def report(path: Path, message: str) -> None:
    errors.append(f"{path.relative_to(ROOT)}: {message}")


for collection in COLLECTIONS:
    if not collection.is_dir():
        report(collection, "skill collection is missing")
        continue
    for skill_dir in sorted(
        path
        for path in collection.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    ):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            report(skill_file, "missing")
        else:
            skill_files.append(skill_file)

for path in skill_files:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        report(path, f"cannot read as UTF-8: {exc}")
        continue

    lines = text.splitlines()
    if not lines or lines[0] != "---":
        report(path, "must start with YAML frontmatter delimiter '---'")
        continue
    try:
        closing = lines.index("---", 1)
    except ValueError:
        report(path, "frontmatter has no closing '---' delimiter")
        continue

    frontmatter = lines[1:closing]
    fields: dict[str, str] = {}
    for line in frontmatter:
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):(?:[ \t]*(.*))$", line)
        if not match:
            continue
        key, value = match.groups()
        if key in fields:
            report(path, f"duplicate frontmatter field: {key}")
        fields[key] = value.strip()

    for key in ("name", "description", "metadata"):
        if not fields.get(key):
            report(path, f"frontmatter field '{key}' is required and must be single-line")

    expected_name = path.parent.name
    if fields.get("name") and fields["name"] != expected_name:
        report(path, f"name must match directory: expected {expected_name!r}")

    metadata_text = fields.get("metadata")
    if metadata_text:
        try:
            metadata = json.loads(metadata_text)
        except json.JSONDecodeError as exc:
            report(path, f"metadata is not valid JSON: {exc.msg}")
        else:
            if not isinstance(metadata, dict):
                report(path, "metadata must be a JSON object")
            else:
                openclaw = metadata.get("openclaw")
                if not isinstance(openclaw, dict):
                    report(path, "metadata.openclaw must be a JSON object")
                elif openclaw.get("skillKey") != expected_name:
                    report(path, f"metadata.openclaw.skillKey must equal {expected_name!r}")

json_files = sorted(
    path
    for collection in COLLECTIONS
    for path in collection.rglob("*.json")
    if path.is_file()
)
for path in json_files:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        report(path, f"invalid JSON: {exc}")

if errors:
    for error in errors:
        print(f"FAIL: {error}")
    raise SystemExit(1)

print(f"OK: {len(skill_files)} skill manifests and {len(json_files)} JSON files")
PY

# Parse Python without importing component dependencies or writing __pycache__
# directories into the worktree.
"$PYTHON_BIN" - <<'PY'
from pathlib import Path

roots = [Path("hermes-plugins"), Path("info-track"), Path("openclaw-skills"), Path("scripts")]
files = [path for root in roots for path in root.rglob("*.py") if "__pycache__" not in path.parts]
for path in files:
    source = path.read_text(encoding="utf-8")
    compile(source, str(path), "exec")
print(f"OK: {len(files)} Python files parsed")
PY

while IFS= read -r -d '' script; do
  bash -n "$script"
done < <(find hermes-plugins info-track openclaw-skills scripts -type f -name '*.sh' -print0)
printf 'OK: shell syntax\n'

if find hermes-plugins info-track openclaw-skills -type f \( -name '*.js' -o -name '*.mjs' \) -print -quit | grep -q .; then
  [[ -x "$NODE_BIN" ]] || require_command "$NODE_BIN"
  while IFS= read -r -d '' script; do
    "$NODE_BIN" --input-type=module --check <"$script" >/dev/null
  done < <(find hermes-plugins info-track openclaw-skills -type f \( -name '*.js' -o -name '*.mjs' \) -print0)
  printf 'OK: JavaScript syntax\n'
fi

if [[ -f pyproject.toml || -f uv.lock ]]; then
  [[ -f pyproject.toml && -f uv.lock ]] || fail "pyproject.toml and uv.lock must either both exist or both be absent"
  require_command uv
  uv lock --check >/dev/null
  printf 'OK: uv lock is current\n'
fi

printf 'OK: repository baseline verification passed\n'
