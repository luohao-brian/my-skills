#!/usr/bin/env python3
"""Materialize a pinned upstream PPT Master release plus downstream adapters."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOWNSTREAM = ROOT / "scripts" / "ppt_master_downstream"
DEFAULT_MANIFEST = DOWNSTREAM / "manifest.json"
DEFAULT_TARGET = ROOT / "openclaw-skills" / "ppt-master"


class SyncError(RuntimeError):
    """The release tree could not be materialized deterministically."""


def _run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SyncError(f"{' '.join(command)} failed: {detail}")
    return result


def _load_manifest(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SyncError(f"cannot read manifest {path}: {exc}") from exc
    for field in (
        "repository",
        "subtree",
        "release",
        "release_commit",
        "packaging_transforms",
        "additive_overlays",
        "core_patches",
    ):
        if field not in data:
            raise SyncError(f"manifest is missing {field}")
    return data


def _prepare_upstream(
    manifest: dict[str, object],
    temp_root: Path,
    upstream_repo: Path | None,
) -> tuple[Path, str]:
    if upstream_repo is None:
        upstream_repo = temp_root / "upstream"
        _run([
            "git",
            "clone",
            "--quiet",
            "--filter=blob:none",
            "--no-checkout",
            str(manifest["repository"]),
            str(upstream_repo),
        ])
    else:
        upstream_repo = upstream_repo.expanduser().resolve()
    release = str(manifest["release"])
    commit = _run(
        ["git", "-C", str(upstream_repo), "rev-parse", f"{release}^{{commit}}"]
    ).stdout.strip()
    expected = str(manifest["release_commit"])
    if commit != expected:
        raise SyncError(f"{release} resolved to {commit}, expected {expected}")
    return upstream_repo, commit


def _extract_release(
    repo: Path,
    manifest: dict[str, object],
    stage: Path,
) -> None:
    subtree = str(manifest["subtree"]).strip("/")
    archive = subprocess.Popen(
        ["git", "-C", str(repo), "archive", str(manifest["release"]), subtree],
        stdout=subprocess.PIPE,
    )
    assert archive.stdout is not None
    untar = subprocess.run(
        ["tar", "-x", "-C", str(stage), "--strip-components=2"],
        stdin=archive.stdout,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    archive.stdout.close()
    archive_status = archive.wait()
    if archive_status or untar.returncode:
        raise SyncError(untar.stderr.strip() or "git archive extraction failed")


def _write_openclaw_skill(skill_path: Path) -> None:
    text = skill_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise SyncError("upstream SKILL.md has no frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise SyncError("upstream SKILL.md frontmatter is unterminated")
    body = text[end + 5 :]
    body = body.replace(
        "PPT Master is a routed presentation workflow. This entry owns global execution discipline and route selection only; each selected route owns its procedure.\n",
        "PPT Master is a routed presentation workflow. This entry owns global execution discipline and route selection only; each selected route owns its procedure.\n\n"
        "## Downstream Runtime Boundary\n\n"
        "This OpenClaw/Hermes distribution keeps upstream workflow semantics and routes while delegating environment-specific behavior to [`references/runtime.md`](references/runtime.md). The runtime contract has precedence only for project directories, target-host fonts, dependency/capability discovery, and the downstream release gate.\n",
        1,
    )
    load_pattern = re.compile(
        r"1\. Read this file\.\n"
        r"2\. Run `python3 scripts/attribution_guard\.py`.*?\n"
        r"   bypass the integrity gate\.\n"
        r"3\. Read \[`workflows/routing\.md`\]\(workflows/routing\.md\)\.\n"
        r"4\. Select exactly one top-level route and its active profile from the routing\n"
        r"   authority\.\n"
        r"5\. Read only the resulting runtime authority and its explicitly triggered\n"
        r"   supporting documents\.",
        re.DOTALL,
    )
    replacement = (
        "1. Read this file.\n"
        "2. Read [`references/runtime.md`](references/runtime.md); its Directory, Font, and Dependency contracts are mandatory for every route.\n"
        "3. Read [`workflows/routing.md`](workflows/routing.md).\n"
        "4. Select exactly one top-level route and its active profile from the routing authority.\n"
        "5. Read only the resulting runtime authority and its explicitly triggered supporting documents."
    )
    body, count = load_pattern.subn(replacement, body, count=1)
    if count != 1:
        raise SyncError("SKILL.md load-order anchor did not match")
    frontmatter = (
        "---\n"
        "name: ppt-master\n"
        "description: 将 PDF、DOCX、PPTX、网页、Markdown、新闻或主题资料生成可编辑 SVG/PPTX 演示文稿，也可填充模板、美化既有 PPTX、添加动画与旁白。用户要求创建、制作、优化、检查或导出 PPT/演示文稿，提到 ppt-master，或需要 SVG 页面与 PowerPoint 互转时使用。\n"
        "metadata: {\"openclaw\":{\"skillKey\":\"ppt-master\",\"emoji\":\"📊\",\"homepage\":\"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ppt-master\",\"primaryEnv\":\"ARK_AGENT_PLAN_API_KEY\",\"requires\":{\"anyBins\":[\"python3\",\"python\"],\"env\":[\"ARK_AGENT_PLAN_API_KEY\"]}}}\n"
        "---\n\n"
    )
    skill_path.write_text(frontmatter + body, encoding="utf-8")


def _disable_identity_guard(stage: Path) -> None:
    guard = stage / "scripts" / "attribution_guard.py"
    if not guard.is_file():
        raise SyncError("upstream attribution guard is missing; transform anchor changed")
    guard.unlink()
    import_pattern = re.compile(
        r"^\s*from attribution_guard import require_skill_integrity(?:\s+#.*)?\n",
        re.MULTILINE,
    )
    call_pattern = re.compile(r"^\s*require_skill_integrity\(\)\s*\n", re.MULTILINE)
    secondary_call_pattern = re.compile(
        r"^\s*_require_official_distribution_identity\(\)\s*\n",
        re.MULTILINE,
    )
    import_count = 0
    call_count = 0
    for path in sorted((stage / "scripts").rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        text, imports = import_pattern.subn("", text)
        text, calls = call_pattern.subn("", text)
        text, secondary_calls = secondary_call_pattern.subn("", text)
        if imports or calls or secondary_calls:
            path.write_text(text, encoding="utf-8")
        import_count += imports
        call_count += calls
    if import_count < 10 or call_count < 10:
        raise SyncError(
            f"identity transform matched only {import_count} imports and {call_count} calls"
        )


def _portable_paths(stage: Path) -> None:
    for path in sorted(stage.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".py", ".json"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        updated = text.replace("skills/ppt-master", "{baseDir}")
        if updated != text:
            path.write_text(updated, encoding="utf-8")


def _portable_project_init(stage: Path) -> None:
    fence = re.compile(r"```(?:bash|sh|shell|zsh)?\n(.*?)```", re.DOTALL)
    command = re.compile(r"^(.*project_manager\.py\s+init\b.*)$", re.MULTILINE)
    for path in sorted(stage.rglob("*.md")):
        text = path.read_text(encoding="utf-8")

        def update_fence(match: re.Match[str]) -> str:
            block = match.group(1)

            def update_command(command_match: re.Match[str]) -> str:
                line = command_match.group(1)
                if "--dir" in line:
                    return line
                return f"{line} --dir <absolute-projects-root>"

            updated = command.sub(update_command, block)
            return match.group(0).replace(block, updated, 1)

        updated = fence.sub(update_fence, text)
        if updated != text:
            path.write_text(updated, encoding="utf-8")


def _rename_readmes(stage: Path) -> None:
    readmes = sorted(stage.rglob("README.md"))
    relative_map: dict[str, str] = {}
    for source in readmes:
        relative = source.relative_to(stage).as_posix()
        target = source.with_name("_index.md")
        relative_map[relative] = target.relative_to(stage).as_posix()
        source.rename(target)
    for path in sorted(stage.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".py", ".json"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        updated = text
        for old, new in relative_map.items():
            updated = updated.replace(old, new)
            updated = updated.replace(f"{{baseDir}}/{old}", f"{{baseDir}}/{new}")
        if path.suffix.lower() == ".md":
            for old, new in relative_map.items():
                old_path = stage / old
                old_rel = Path(os.path.relpath(old_path, path.parent)).as_posix()
                new_rel = Path(os.path.relpath(stage / new, path.parent)).as_posix()
                updated = updated.replace(old_rel, new_rel)
        if updated != text:
            path.write_text(updated, encoding="utf-8")


def _rewrite_escaping_links(stage: Path, manifest: dict[str, object]) -> None:
    repository = str(manifest["repository"]).removesuffix(".git")
    release = str(manifest["release"])
    subtree = str(manifest["subtree"]).strip("/")
    link_pattern = re.compile(r"(\[[^\]]*\]\()([^)#]+)(#[^)]*)?(\))")
    for path in sorted(stage.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        relative_parent = path.relative_to(stage).parent.as_posix()

        def replace(match: re.Match[str]) -> str:
            target = match.group(2).strip()
            if not target.startswith("../"):
                return match.group(0)
            local_target = (path.parent / target).resolve()
            try:
                local_target.relative_to(stage.resolve())
                return match.group(0)
            except ValueError:
                pass
            upstream_path = posixpath.normpath(
                posixpath.join(subtree, relative_parent, target)
            )
            url = f"{repository}/blob/{release}/{upstream_path}"
            return f"{match.group(1)}{url}{match.group(3) or ''}{match.group(4)}"

        updated = link_pattern.sub(replace, text)
        if updated != text:
            path.write_text(updated, encoding="utf-8")


def _copy_overlays(stage: Path, manifest: dict[str, object]) -> None:
    overlay_root = DOWNSTREAM / "overlay"
    for raw in manifest["additive_overlays"]:
        relative = Path(str(raw))
        source = overlay_root / relative
        if not source.is_file():
            raise SyncError(f"missing additive overlay: {relative}")
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _apply_patches(stage: Path, manifest: dict[str, object]) -> None:
    for raw in manifest["core_patches"]:
        patch_path = DOWNSTREAM / "patches" / str(raw)
        if not patch_path.is_file():
            raise SyncError(f"missing core patch: {patch_path.name}")
        _run(["git", "apply", "--check", str(patch_path)], cwd=stage)
        _run(["git", "apply", str(patch_path)], cwd=stage)


def _write_provenance(stage: Path, manifest: dict[str, object], commit: str) -> None:
    lock = {
        "schema_version": 2,
        "upstream": {
            "repository": manifest["repository"],
            "subtree": manifest["subtree"],
            "release": manifest["release"],
            "commit": commit,
        },
        "packaging_transforms": manifest["packaging_transforms"],
        "additive_overlays": manifest["additive_overlays"],
        "core_patches": manifest["core_patches"],
        "subsumed_by_upstream": manifest.get("subsumed_by_upstream", []),
        "unsupported_upstream_features": manifest.get("unsupported_upstream_features", []),
    }
    (stage / "upstream.lock.json").write_text(
        json.dumps(lock, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    source = stage / "references" / "upstream-source.md"
    source.write_text(
        "# Upstream Source\n\n"
        f"This distribution materializes `{manifest['subtree']}` from "
        f"[`{manifest['release']}`]({str(manifest['repository']).removesuffix('.git')}/tree/{manifest['release']}/{manifest['subtree']}) "
        f"at commit `{commit}`.\n\n"
        "The release tree is not reconstructed by skipping commits. Deterministic packaging transforms, additive runtime adapters, and the small patch queue listed in `../upstream.lock.json` are applied to the fixed release tree. Unsupported upstream features are provenance records only and never alter Git history.\n\n"
        "Directory, Font, and Dependency behavior is owned by `runtime.md`; upstream workflow content remains authoritative everywhere else.\n",
        encoding="utf-8",
    )


def _normalize_text_whitespace(stage: Path) -> None:
    """Remove upstream/editor whitespace noise from materialized text files."""
    for path in sorted(stage.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".py", ".json"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        normalized = "\n".join(line.rstrip(" \t") for line in text.splitlines())
        normalized = normalized.rstrip("\n") + "\n"
        if normalized != text:
            path.write_text(normalized, encoding="utf-8")


def _validate_stage(stage: Path) -> None:
    if not (stage / "SKILL.md").is_file():
        raise SyncError("materialized tree has no SKILL.md")
    if (stage / "scripts" / "attribution_guard.py").exists():
        raise SyncError("identity guard survived packaging")
    if list(stage.rglob("README.md")):
        raise SyncError("README.md survived progressive-index packaging")
    for path in stage.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "require_skill_integrity" in text and path.name != "console_encoding.py":
            raise SyncError(f"identity guard reference survived in {path.relative_to(stage)}")


def _publish(stage: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = target.parent / f".{target.name}.sync-backup"
    if backup.exists():
        shutil.rmtree(backup)
    if target.exists():
        target.rename(backup)
    try:
        shutil.move(str(stage), str(target))
    except BaseException:
        if target.exists():
            shutil.rmtree(target)
        if backup.exists():
            backup.rename(target)
        raise
    if backup.exists():
        shutil.rmtree(backup)


def _tree_manifest(root: Path) -> dict[str, tuple[int, int, str | None]]:
    manifest: dict[str, tuple[int, int, str | None]] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.name == ".DS_Store":
            continue
        relative = path.relative_to(root).as_posix()
        mode = path.stat().st_mode & 0o111
        size = path.stat().st_size
        digest = (
            hashlib.sha256(path.read_bytes()).hexdigest()
            if path.suffix.lower() in {".md", ".py", ".json"}
            else None
        )
        manifest[relative] = (mode, size, digest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize a pinned upstream ppt-master release plus downstream adapters."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--upstream-repo", type=Path)
    parser.add_argument("--check", action="store_true", help="Build and compare without publishing")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifest = _load_manifest(args.manifest.resolve())
        with tempfile.TemporaryDirectory(prefix="ppt-master-sync-") as temp_name:
            temp_root = Path(temp_name)
            repo, commit = _prepare_upstream(manifest, temp_root, args.upstream_repo)
            stage = temp_root / "stage"
            stage.mkdir()
            _extract_release(repo, manifest, stage)
            _disable_identity_guard(stage)
            _portable_paths(stage)
            _portable_project_init(stage)
            _rename_readmes(stage)
            _rewrite_escaping_links(stage, manifest)
            _write_openclaw_skill(stage / "SKILL.md")
            _copy_overlays(stage, manifest)
            _apply_patches(stage, manifest)
            _write_provenance(stage, manifest, commit)
            _normalize_text_whitespace(stage)
            _validate_stage(stage)
            target = args.target.expanduser().resolve()
            if args.check:
                if not target.is_dir():
                    raise SyncError(f"published skill does not exist: {target}")
                print(
                    f"[CHECK] materialized {manifest['release']}; comparing published tree",
                    flush=True,
                )
                expected_tree = _tree_manifest(stage)
                published_tree = _tree_manifest(target)
                if expected_tree != published_tree:
                    changed = sorted(
                        path
                        for path in set(expected_tree) | set(published_tree)
                        if expected_tree.get(path) != published_tree.get(path)
                    )
                    sample = ", ".join(changed[:10])
                    suffix = "" if len(changed) <= 10 else f", ... ({len(changed)} paths)"
                    raise SyncError(
                        f"materialized release differs from the published skill: {sample}{suffix}"
                    )
                print(f"OK: {manifest['release']} materialization matches {target}")
            else:
                _publish(stage, target)
                print(f"OK: published {manifest['release']} ({commit}) to {target}")
    except SyncError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
