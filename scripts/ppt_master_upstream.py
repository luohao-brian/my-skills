#!/usr/bin/env python3
"""Plan a repeatable three-way sync of the local ppt-master subtree."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SKILL = ROOT / "openclaw-skills" / "ppt-master"
DEFAULT_MANIFEST = DEFAULT_SKILL / "upstream.lock.json"
IGNORED_LOCAL_NAMES = {".DS_Store", "__pycache__"}


class SyncError(RuntimeError):
    """A sync plan could not be constructed safely."""


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    state: str


@dataclass(frozen=True)
class Plan:
    baseline: str
    reviewed_through: str
    target: str
    commits: tuple[Commit, ...]
    files: Mapping[str, tuple[str, ...]]
    excluded_raw_paths: tuple[str, ...]

    def to_json(self) -> dict[str, object]:
        return {
            "baseline": self.baseline,
            "reviewed_through": self.reviewed_through,
            "target": self.target,
            "commits": [commit.__dict__ for commit in self.commits],
            "files": {key: list(value) for key, value in self.files.items()},
            "excluded_raw_paths": list(self.excluded_raw_paths),
        }


def run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SyncError(f"git {' '.join(args)} failed: {detail}")
    return result


def resolve_commit(repo: Path, revision: str) -> str:
    return run_git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}").stdout.strip()


def is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    return run_git(repo, "merge-base", "--is-ancestor", ancestor, descendant, check=False).returncode == 0


def load_manifest(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SyncError(f"cannot read manifest {path}: {exc}") from exc
    required = ("repository", "subtree", "base_commit", "reviewed_through", "excluded_commits")
    missing = [key for key in required if key not in data]
    if missing:
        raise SyncError(f"manifest is missing: {', '.join(missing)}")
    if not isinstance(data["excluded_commits"], list):
        raise SyncError("manifest excluded_commits must be a list")
    return data


def git_tree(repo: Path, revision: str, subtree: str) -> dict[str, tuple[str, str]]:
    prefix = subtree.rstrip("/") + "/"
    output = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "-r", "-z", revision, "--", subtree],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if output.returncode:
        raise SyncError(output.stderr.decode(errors="replace").strip())
    result: dict[str, tuple[str, str]] = {}
    for record in output.stdout.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, object_type, object_id = metadata.decode("ascii").split()
        path = raw_path.decode("utf-8", errors="surrogateescape")
        if object_type != "blob" or not path.startswith(prefix):
            continue
        result[path[len(prefix) :]] = (mode, object_id)
    return result


def git_blob_id(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def filesystem_tree(root: Path) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in IGNORED_LOCAL_NAMES for part in relative.parts):
            continue
        if path.is_symlink():
            data = os.readlink(path).encode("utf-8", errors="surrogateescape")
            result[relative.as_posix()] = ("120000", git_blob_id(data))
        elif path.is_file():
            mode = "100755" if path.stat().st_mode & stat.S_IXUSR else "100644"
            result[relative.as_posix()] = (mode, git_blob_id(path.read_bytes()))
    return result


def classify_files(
    baseline: Mapping[str, tuple[str, str]],
    local: Mapping[str, tuple[str, str]],
    upstream: Mapping[str, tuple[str, str]],
) -> dict[str, tuple[str, ...]]:
    groups: dict[str, list[str]] = {
        "unchanged": [],
        "safe_upstream": [],
        "local_overlay": [],
        "converged": [],
        "conflict": [],
    }
    for path in sorted(set(baseline) | set(local) | set(upstream)):
        base_value = baseline.get(path)
        local_value = local.get(path)
        upstream_value = upstream.get(path)
        if local_value == base_value and upstream_value == base_value:
            state = "unchanged"
        elif local_value == base_value:
            state = "safe_upstream"
        elif upstream_value == base_value:
            state = "local_overlay"
        elif local_value == upstream_value:
            state = "converged"
        else:
            state = "conflict"
        groups[state].append(path)
    return {key: tuple(value) for key, value in groups.items()}


def list_commits(
    repo: Path,
    baseline: str,
    reviewed_through: str,
    target: str,
    excluded: set[str],
) -> tuple[Commit, ...]:
    raw = run_git(repo, "log", "--reverse", "--format=%H%x09%s", f"{baseline}..{target}").stdout
    commits: list[Commit] = []
    for line in raw.splitlines():
        sha, subject = line.split("\t", 1)
        if sha in excluded:
            state = "excluded"
        elif is_ancestor(repo, sha, reviewed_through):
            state = "reviewed"
        else:
            state = "new"
        commits.append(Commit(sha=sha, subject=subject, state=state))
    return tuple(commits)


def effective_upstream_tree(
    repo: Path,
    baseline: str,
    subtree: str,
    commits: Iterable[Commit],
    temp_root: Path,
) -> dict[str, tuple[str, str]]:
    selected = [commit.sha for commit in commits if commit.state != "excluded"]
    if not selected:
        return git_tree(repo, baseline, subtree)

    candidate = temp_root / "effective-upstream"
    clone = subprocess.run(
        ["git", "clone", "--quiet", "--shared", "--no-checkout", str(repo), str(candidate)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if clone.returncode:
        raise SyncError(f"cannot create temporary candidate: {clone.stderr.strip()}")
    run_git(candidate, "checkout", "--quiet", "--detach", baseline)
    for sha in selected:
        result = run_git(
            candidate,
            "-c",
            "user.name=ppt-master-upstream",
            "-c",
            "user.email=ppt-master-upstream@local.invalid",
            "cherry-pick",
            "--no-commit",
            sha,
            check=False,
        )
        if result.returncode:
            conflicts = run_git(candidate, "diff", "--name-only", "--diff-filter=U", check=False).stdout.strip()
            detail = conflicts or result.stderr.strip() or result.stdout.strip()
            raise SyncError(f"cannot replay upstream commit {sha}: {detail}")
    return filesystem_tree(candidate / subtree)


def build_plan(
    manifest: Mapping[str, object],
    skill_dir: Path,
    upstream_repo: Path,
    target_revision: str,
    temp_root: Path,
) -> Plan:
    baseline = resolve_commit(upstream_repo, str(manifest["base_commit"]))
    reviewed = resolve_commit(upstream_repo, str(manifest["reviewed_through"]))
    target = resolve_commit(upstream_repo, target_revision)
    if not is_ancestor(upstream_repo, baseline, target):
        raise SyncError("configured baseline is not an ancestor of the upstream target")
    if not is_ancestor(upstream_repo, reviewed, target):
        raise SyncError("reviewed_through is not an ancestor of the upstream target")

    excluded_items = manifest["excluded_commits"]
    assert isinstance(excluded_items, list)
    excluded = {str(item["commit"]) for item in excluded_items if isinstance(item, dict) and "commit" in item}
    commits = list_commits(upstream_repo, baseline, reviewed, target, excluded)
    seen = {commit.sha for commit in commits}
    unknown_exclusions = sorted(excluded - seen)
    if unknown_exclusions:
        raise SyncError(f"excluded commits are outside the configured range: {', '.join(unknown_exclusions)}")

    base_tree = git_tree(upstream_repo, baseline, str(manifest["subtree"]))
    raw_target_tree = git_tree(upstream_repo, target, str(manifest["subtree"]))
    effective_tree = effective_upstream_tree(
        upstream_repo,
        baseline,
        str(manifest["subtree"]),
        commits,
        temp_root,
    )
    local_tree = filesystem_tree(skill_dir)
    files = classify_files(base_tree, local_tree, effective_tree)
    excluded_raw_paths = tuple(
        sorted(path for path in set(raw_target_tree) | set(effective_tree) if raw_target_tree.get(path) != effective_tree.get(path))
    )
    return Plan(
        baseline=baseline,
        reviewed_through=reviewed,
        target=target,
        commits=commits,
        files=files,
        excluded_raw_paths=excluded_raw_paths,
    )


def print_plan(plan: Plan, detail_limit: int) -> None:
    print(f"baseline:         {plan.baseline}")
    print(f"reviewed through: {plan.reviewed_through}")
    print(f"upstream target:  {plan.target}")
    print("commits:")
    if not plan.commits:
        print("  none")
    for commit in plan.commits:
        print(f"  [{commit.state:8}] {commit.sha[:12]} {commit.subject}")
    print("file plan (excluded commits removed):")
    for state in ("safe_upstream", "conflict", "local_overlay", "converged", "unchanged"):
        paths = plan.files[state]
        print(f"  {state:14} {len(paths)}")
        if state in {"safe_upstream", "conflict"}:
            for path in paths[:detail_limit]:
                print(f"    {path}")
            if len(paths) > detail_limit:
                print(f"    ... {len(paths) - detail_limit} more")
    print(f"paths changed only by excluded commits: {len(plan.excluded_raw_paths)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare an upstream baseline, the local OpenClaw overlay, and current GitHub upstream."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--skill-dir", type=Path, default=DEFAULT_SKILL)
    parser.add_argument("--upstream-repo", type=Path, help="Use an existing upstream clone instead of a temporary clone.")
    parser.add_argument("--target", default="origin/main", help="Upstream revision to inspect (default: origin/main).")
    parser.add_argument("--no-fetch", action="store_true", help="Do not fetch the existing --upstream-repo first.")
    parser.add_argument("--json-output", type=Path, help="Write the complete machine-readable plan to this path.")
    parser.add_argument("--detail-limit", type=int, default=30)
    parser.add_argument("--fail-on-new", action="store_true", help="Exit 2 when unreviewed upstream commits exist.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifest = load_manifest(args.manifest.resolve())
        with tempfile.TemporaryDirectory(prefix="ppt-master-upstream-") as temp_name:
            temp_root = Path(temp_name)
            if args.upstream_repo:
                upstream_repo = args.upstream_repo.expanduser().resolve()
                if not args.no_fetch:
                    run_git(upstream_repo, "fetch", "--quiet", "origin")
            else:
                upstream_repo = temp_root / "upstream"
                clone = subprocess.run(
                    [
                        "git",
                        "clone",
                        "--quiet",
                        "--filter=blob:none",
                        "--no-checkout",
                        str(manifest["repository"]),
                        str(upstream_repo),
                    ],
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                if clone.returncode:
                    raise SyncError(f"cannot clone upstream: {clone.stderr.strip()}")
            plan = build_plan(manifest, args.skill_dir.resolve(), upstream_repo, args.target, temp_root)
        print_plan(plan, max(0, args.detail_limit))
        if args.json_output:
            args.json_output.write_text(json.dumps(plan.to_json(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if args.fail_on_new and any(commit.state == "new" for commit in plan.commits):
            return 2
        return 0
    except SyncError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
