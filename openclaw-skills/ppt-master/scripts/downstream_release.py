#!/usr/bin/env python3
"""Fail-closed downstream release orchestrator for the SVG-to-PPTX route."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent
SCHEMA = "ppt-master.downstream-release-report.v1"


@dataclass(frozen=True)
class StageFailure(RuntimeError):
    stage: str
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    def __str__(self) -> str:
        detail = self.stderr.strip() or self.stdout.strip() or "no diagnostic output"
        return f"{self.stage} failed with exit {self.returncode}: {detail}"


def _run_stage(stage: str, command: list[str]) -> dict[str, object]:
    result = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
    record = {
        "stage": stage,
        "command": command,
        "returncode": result.returncode,
        "status": "passed" if result.returncode == 0 else "failed",
    }
    if result.returncode:
        raise StageFailure(
            stage=stage,
            command=tuple(command),
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    record["stdout"] = result.stdout
    return record


def _report_path(project: Path) -> Path:
    return project / "validation" / "downstream_release_report.json"


def _write_report(project: Path, payload: dict[str, object]) -> None:
    path = _report_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _export(project: Path, exporter_args: list[str]) -> int:
    quick = "--quick-generate" in exporter_args
    if "--quiet" in exporter_args or "-q" in exporter_args:
        print("FAIL: downstream release export does not allow --quiet", file=sys.stderr)
        return 2
    python = sys.executable
    stages: list[dict[str, object]] = []
    payload: dict[str, object] = {
        "schema": SCHEMA,
        "status": "running",
        "project": str(project),
        "stages": stages,
    }
    try:
        upstream_quality = [
            python,
            str(SCRIPTS_DIR / "svg_quality_checker.py"),
            str(project),
            "--stage",
            "final",
            "--json",
        ]
        downstream_quality = [
            python,
            str(SCRIPTS_DIR / "downstream_svg_checker.py"),
            str(project),
        ]
        if quick:
            upstream_quality.append("--quick-generate")
            downstream_quality.append("--quick-generate")
        stages.append(_run_stage("upstream-svg-quality", upstream_quality))
        stages.append(_run_stage("downstream-font-readability", downstream_quality))
        visual_report = project / "validation" / "downstream_visual_layout_report.json"
        stages.append(_run_stage(
            "browser-layout",
            [
                python,
                str(SCRIPTS_DIR / "visual_layout_audit.py"),
                str(project),
                "--report",
                str(visual_report),
            ],
        ))
        export_record = _run_stage(
            "upstream-export",
            [python, str(SCRIPTS_DIR / "svg_to_pptx.py"), str(project), *exporter_args],
        )
        stages.append(export_record)
        stdout = str(export_record.get("stdout") or "")
        matches = re.findall(r"^\s*\[PPTX\]\s+(.+?)\s*$", stdout, flags=re.MULTILINE)
        if len(matches) != 1:
            raise StageFailure(
                stage="upstream-export-receipt",
                command=tuple([python, str(SCRIPTS_DIR / "svg_to_pptx.py"), str(project), *exporter_args]),
                returncode=1,
                stdout=stdout,
                stderr=f"expected one [PPTX] receipt, found {len(matches)}",
            )
        pptx_path = Path(matches[0]).expanduser()
        if not pptx_path.is_absolute():
            pptx_path = (project / pptx_path).resolve()
        if not pptx_path.is_file():
            raise StageFailure(
                stage="upstream-export-receipt",
                command=tuple(),
                returncode=1,
                stdout=stdout,
                stderr=f"reported PPTX does not exist: {pptx_path}",
            )
        stages.append(_run_stage(
            "pptx-delivery",
            [python, str(SCRIPTS_DIR / "pptx_delivery_check.py"), str(pptx_path)],
        ))
        stages.append(_run_stage(
            "pptx-layout",
            [python, str(SCRIPTS_DIR / "pptx_layout_audit.py"), str(pptx_path)],
        ))
        downstream_svg_report = json.loads(
            (project / "validation" / "downstream_svg_report.json").read_text(encoding="utf-8")
        )
        payload.update({
            "status": "passed",
            "source_fingerprint": downstream_svg_report.get("source_fingerprint"),
            "output": str(pptx_path),
        })
        _write_report(project, payload)
        print(f"[DOWNSTREAM-RELEASE] status=passed pptx={pptx_path} report={_report_path(project)}")
        return 0
    except (OSError, json.JSONDecodeError, StageFailure) as exc:
        payload.update({"status": "failed", "error": str(exc)})
        if isinstance(exc, StageFailure):
            payload["failed_stage"] = exc.stage
            payload["failed_command"] = list(exc.command)
            payload["exit_code"] = exc.returncode
        _write_report(project, payload)
        print(f"FAIL: {exc}", file=sys.stderr)
        print(f"[DOWNSTREAM-RELEASE] status=failed report={_report_path(project)}", file=sys.stderr)
        return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run every downstream release gate around the upstream exporter."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    export = subparsers.add_parser("export", help="Validate, export, and audit one SVG-route project")
    export.add_argument("project_path", type=Path)
    export.add_argument(
        "exporter_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed to svg_to_pptx.py after an optional -- separator",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project = args.project_path.expanduser().resolve()
    if not project.is_dir():
        print(f"FAIL: project directory does not exist: {project}", file=sys.stderr)
        return 2
    exporter_args = list(args.exporter_args)
    if exporter_args[:1] == ["--"]:
        exporter_args.pop(0)
    return _export(project, exporter_args)


if __name__ == "__main__":
    raise SystemExit(main())
