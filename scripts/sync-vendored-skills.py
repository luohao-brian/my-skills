#!/usr/bin/env python3
"""Compare or update pinned upstream snapshots for vendored skills."""

from __future__ import annotations

import argparse
import filecmp
import json
import re
import shutil
import subprocess
import tempfile
import unicodedata
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = {
    "diagram-design": ROOT / "openclaw-skills" / "diagram-design",
    "baoyu-infographic": ROOT / "openclaw-skills" / "baoyu-infographic",
    "baoyu-article-illustrator": ROOT / "openclaw-skills" / "baoyu-article-illustrator",
}


def run(*args: str, cwd: Path | None = None) -> str:
    completed = subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def load_manifest(skill_dir: Path) -> dict[str, object]:
    return json.loads((skill_dir / "UPSTREAM.json").read_text(encoding="utf-8"))


def different(left: Path, right: Path) -> bool:
    comparison = filecmp.dircmp(left, right, ignore=[".DS_Store", "__pycache__"])
    if comparison.left_only or comparison.right_only or comparison.diff_files or comparison.funny_files:
        return True
    return any(different(left / name, right / name) for name in comparison.common_dirs)


def frontmatter_version(skill_file: Path) -> str | None:
    text = skill_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    frontmatter = parts[1]
    match = re.search(
        r"(?m)^[ \t]*version:\s*[\"']?([^\"'\n#]+)",
        frontmatter,
    )
    return match.group(1).strip() if match else None


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "section"


def rewrite_links(text: str) -> str:
    pattern = re.compile(r"(\[[^\]]+\]\()([^\s)]+)(\))")

    def replace(match: re.Match[str]) -> str:
        target = match.group(2)
        if target.startswith(("http://", "https://", "#", "/", "mailto:")):
            return match.group(0)
        return f"{match.group(1)}../../upstream/{target}{match.group(3)}"

    return pattern.sub(replace, text)


def render_upstream_sections(source_skill: Path, destination: Path) -> None:
    """Mechanically split an upstream SKILL.md into H2/H3 progressive-load files."""
    lines = source_skill.read_text(encoding="utf-8").splitlines(keepends=True)
    headings: list[tuple[int, int, str]] = []
    in_fence = False
    for index, line in enumerate(lines):
        if re.match(r"^\s*```", line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = re.match(r"^(##|###)\s+(.+?)\s*$", line)
        if match:
            headings.append((index, len(match.group(1)), match.group(2)))

    staged = destination.with_name(f".{destination.name}.next")
    if staged.exists():
        shutil.rmtree(staged)
    staged.mkdir(parents=True)
    parent_slug = "overview"
    h2_index = 0
    for position, (start, level, title) in enumerate(headings):
        if level == 2:
            h2_index += 1
            parent_slug = slugify(title)
            filename = f"{h2_index:02d}-{parent_slug}.md"
        else:
            filename = f"{h2_index:02d}-{parent_slug}--{slugify(title)}.md"
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        body = rewrite_links("".join(lines[start:end]).rstrip() + "\n")
        header = (
            "<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->\n\n"
            f"Source section: `{title}`\n\n"
        )
        (staged / filename).write_text(header + body, encoding="utf-8")

    if destination.exists():
        backup = destination.with_name(f".{destination.name}.previous")
        if backup.exists():
            shutil.rmtree(backup)
        destination.rename(backup)
        staged.rename(destination)
        shutil.rmtree(backup)
    else:
        staged.rename(destination)


def package_version(checkout: Path, manifest: dict[str, object]) -> str | None:
    relative = manifest.get("package_manifest")
    if not isinstance(relative, str):
        return None
    payload = json.loads((checkout / relative).read_text(encoding="utf-8"))
    if "version" in payload:
        return str(payload["version"])
    plugins = payload.get("plugins")
    if isinstance(plugins, list) and plugins and isinstance(plugins[0], dict):
        version = plugins[0].get("version")
        return str(version) if version is not None else None
    return None


def checkout_source(manifest: dict[str, object], requested_ref: str | None, temp_root: Path) -> tuple[Path, Path, str]:
    repository = str(manifest["repository"])
    ref = requested_ref or str(manifest["commit"])
    checkout = temp_root / "checkout"
    run("git", "clone", "--quiet", "--filter=blob:none", "--no-checkout", repository, str(checkout))
    run("git", "fetch", "--quiet", "--depth=1", "origin", ref, cwd=checkout)
    run("git", "checkout", "--quiet", "--detach", "FETCH_HEAD", cwd=checkout)
    commit = run("git", "rev-parse", "HEAD", cwd=checkout)
    source = checkout / str(manifest["source_path"])
    if not (source / "SKILL.md").is_file():
        raise RuntimeError(f"upstream source is missing SKILL.md: {source}")
    return checkout, source, commit


def sync_one(name: str, requested_ref: str | None, apply: bool) -> dict[str, object]:
    skill_dir = SKILLS[name]
    manifest = load_manifest(skill_dir)
    with tempfile.TemporaryDirectory(prefix=f"sync-{name}-") as raw_temp:
        temp_root = Path(raw_temp)
        checkout, source, commit = checkout_source(manifest, requested_ref, temp_root)
        changed = different(skill_dir / "upstream", source)
        candidate_sections = temp_root / "derived" / "upstream-sections"
        render_upstream_sections(source / "SKILL.md", candidate_sections)
        local_sections = skill_dir / "references" / "upstream-sections"
        derived_changed = not local_sections.is_dir() or different(local_sections, candidate_sections)
        result: dict[str, object] = {
            "skill": name,
            "pinned_commit": manifest["commit"],
            "candidate_commit": commit,
            "changed": changed,
            "derived_changed": derived_changed,
            "applied": False,
        }
        if not apply:
            return result

        staged = skill_dir / ".upstream.next"
        if staged.exists():
            shutil.rmtree(staged)
        shutil.copytree(source, staged)
        current = skill_dir / "upstream"
        backup = skill_dir / ".upstream.previous"
        if backup.exists():
            shutil.rmtree(backup)
        current.rename(backup)
        staged.rename(current)
        shutil.rmtree(backup)

        license_source = checkout / str(manifest["license_path"])
        shutil.copy2(license_source, skill_dir / "LICENSE.upstream")
        manifest["commit"] = commit
        manifest["skill_version"] = frontmatter_version(source / "SKILL.md")
        manifest["package_version"] = package_version(checkout, manifest)
        manifest["synced_at"] = date.today().isoformat()
        (skill_dir / "UPSTREAM.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        render_upstream_sections(
            skill_dir / "upstream" / "SKILL.md",
            skill_dir / "references" / "upstream-sections",
        )
        result["applied"] = True
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", choices=["all", *SKILLS])
    parser.add_argument("--ref", help="Git ref to compare or apply; defaults to the pinned commit")
    parser.add_argument("--apply", action="store_true", help="Replace the snapshot and update UPSTREAM.json")
    parser.add_argument(
        "--refresh-derived",
        action="store_true",
        help="Regenerate progressive-load section files from the current pinned snapshot without network access",
    )
    args = parser.parse_args()
    names = list(SKILLS) if args.skill == "all" else [args.skill]
    if args.refresh_derived:
        for name in names:
            skill_dir = SKILLS[name]
            render_upstream_sections(
                skill_dir / "upstream" / "SKILL.md",
                skill_dir / "references" / "upstream-sections",
            )
        print(json.dumps({"refreshed": names}, ensure_ascii=False, indent=2))
        return 0
    results = [sync_one(name, args.ref, args.apply) for name in names]
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
