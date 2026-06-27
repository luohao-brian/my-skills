#!/usr/bin/env python3
"""Executable workflow for the ai-news skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from adapters import ADAPTERS  # noqa: E402


TZ = timezone(timedelta(hours=8))
CATEGORIES = [
    "模型 / 研究",
    "Agent / 开发者工具",
    "技术博客 / 工程实践",
    "产品 / 应用",
    "商业 / 融资",
    "安全 / 治理",
]
REQUIRED_TOP_LEVEL = ["window", "source_coverage", "candidates", "excluded", "missing"]
REQUIRED_CANDIDATE_FIELDS = [
    "id",
    "title",
    "published_at",
    "published_display",
    "source_url",
    "source_id",
    "summary_basis",
    "category",
    "zh_summary",
    "needs_model_review",
]
AI_KEYWORDS = [
    "ai",
    "artificial intelligence",
    "llm",
    "model",
    "agent",
    "openai",
    "anthropic",
    "gemini",
    "deepmind",
    "claude",
    "chatgpt",
    "gpt",
    "llama",
    "qwen",
    "diffusion",
    "生成式",
    "人工智能",
    "模型",
    "大模型",
    "智能体",
    "推理",
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def dump_json(data: dict[str, Any], out: Path | None) -> None:
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    if out:
        out.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)


def parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=TZ)


def build_window(args: argparse.Namespace) -> dict[str, Any]:
    if getattr(args, "date", None):
        start = parse_date(args.date)
        end = start + timedelta(days=1) - timedelta(seconds=1)
        return {"start": start, "end": end, "label": args.date, "date": args.date}

    window = getattr(args, "window", None) or "72h"
    match = re.fullmatch(r"(\d+)h", window)
    if not match:
        raise ValueError("--window must use Nh format, for example 72h")
    hours = int(match.group(1))
    end = datetime.now(TZ)
    start = end - timedelta(hours=hours)
    return {"start": start, "end": end, "label": f"最近{hours}小时"}


def serialize_window(window: dict[str, Any]) -> dict[str, str]:
    return {
        "start": window["start"].isoformat(timespec="seconds"),
        "end": window["end"].isoformat(timespec="seconds"),
        "label": str(window["label"]),
    }


def parse_datetime(value: str) -> datetime | None:
    text = (value or "").strip()
    if not text:
        return None
    candidates = [text, text.replace("Z", "+00:00")]
    for candidate in candidates:
        try:
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=TZ)
            return parsed.astimezone(TZ)
        except ValueError:
            pass
    try:
        parsed = parsedate_to_datetime(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=TZ)
        return parsed.astimezone(TZ)
    except (TypeError, ValueError):
        return None


def is_ai_related(item: dict[str, str]) -> bool:
    text = f"{item.get('title', '')} {item.get('summary_basis', '')}".lower()
    return any(keyword.lower() in text for keyword in AI_KEYWORDS)


def classify(item: dict[str, str], coverage: list[str]) -> str:
    text = f"{item.get('title', '')} {item.get('summary_basis', '')}".lower()
    if any(word in text for word in ["funding", "raises", "acquires", "ipo", "融资", "收购"]):
        return "商业 / 融资"
    if any(word in text for word in ["safety", "policy", "copyright", "regulation", "安全", "治理", "监管"]):
        return "安全 / 治理"
    if any(word in text for word in ["agent", "sdk", "developer", "tool", "ide", "智能体", "开发者", "工具"]):
        return "Agent / 开发者工具"
    if any(word in text for word in ["paper", "research", "benchmark", "model", "llm", "模型", "研究", "评测"]):
        return "模型 / 研究"
    if any(word in text for word in ["engineering", "infrastructure", "训练", "推理", "工程"]):
        return "技术博客 / 工程实践"
    return coverage[0] if coverage else "产品 / 应用"


def make_summary(item: dict[str, str]) -> str:
    basis = item.get("summary_basis", "").strip()
    title = item.get("title", "").strip()
    source = basis or title
    source = re.sub(r"\s+", " ", source)
    if len(source) > 160:
        source = source[:157].rstrip() + "..."
    return source or title


def stable_id(item: dict[str, str]) -> str:
    seed = f"{item.get('source_url', '')}|{item.get('title', '')}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def dry_run_document(window: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    first = sources[0]
    second = sources[1] if len(sources) > 1 else sources[0]
    published = window["start"] + timedelta(hours=10)
    return {
        "window": serialize_window(window),
        "source_coverage": [
            {
                "source_id": first["id"],
                "name": first["name"],
                "status": "ok",
                "raw_count": 1,
                "candidate_count": 1,
                "missing_reason": None,
            },
            {
                "source_id": second["id"],
                "name": second["name"],
                "status": "partial",
                "raw_count": 1,
                "candidate_count": 0,
                "missing_reason": "missing published_at",
            },
        ],
        "candidates": [
            {
                "id": "dry-run-agent-platform",
                "title": "OpenAI 发布 Agent 平台更新",
                "published_at": published.isoformat(timespec="seconds"),
                "published_display": published.strftime("%Y-%m-%d %H:%M"),
                "source_url": "https://example.com/openai-agent-platform",
                "source_id": first["id"],
                "summary_basis": "OpenAI released an update to its agent platform with improved tool orchestration and developer controls.",
                "category": "Agent / 开发者工具",
                "zh_summary": "OpenAI 发布 Agent 平台更新，重点改进工具编排和开发者控制能力，面向复杂自动化工作流。",
                "needs_model_review": False,
            }
        ],
        "excluded": [
            {
                "title": "Unrelated consumer gadget launch",
                "source_url": "https://example.com/gadget",
                "source_id": first["id"],
                "reason": "not_ai_related",
            }
        ],
        "missing": [
            {
                "source_id": second["id"],
                "url": str(second["url"]),
                "missing_fields": ["published_at"],
                "reason": "missing_required_fields",
            }
        ],
    }


def collect_document(args: argparse.Namespace) -> dict[str, Any]:
    registry = load_json(BASE_DIR / "references" / "sources.json")
    sources = registry.get("sources", [])
    if not isinstance(sources, list):
        raise ValueError("references/sources.json must contain sources[]")
    window = build_window(args)
    if getattr(args, "dry_run", False):
        return dry_run_document(window, sources)

    candidates: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    seen: set[str] = set()

    for source in sources:
        source_id = str(source["id"])
        source_name = str(source["name"])
        adapter_name = str(source["adapter"])
        adapter = ADAPTERS.get(adapter_name)
        if adapter is None:
            coverage.append(
                {
                    "source_id": source_id,
                    "name": source_name,
                    "status": "failed",
                    "raw_count": 0,
                    "candidate_count": 0,
                    "missing_reason": f"unknown adapter: {adapter_name}",
                }
            )
            continue

        try:
            raw_items = adapter(source, window)
        except Exception as exc:  # pragma: no cover - network sources drift.
            print(f"[ai-news] {source_id} failed: {exc}", file=sys.stderr)
            coverage.append(
                {
                    "source_id": source_id,
                    "name": source_name,
                    "status": "failed",
                    "raw_count": 0,
                    "candidate_count": 0,
                    "missing_reason": str(exc),
                }
            )
            continue

        source_candidate_count = 0
        source_missing_reason = None
        for raw in raw_items:
            item = {key: str(raw.get(key, "") or "").strip() for key in ["title", "source_url", "published_at", "summary_basis"]}
            required_missing = [key for key in ["title", "source_url", "published_at", "summary_basis"] if not item[key]]
            if required_missing:
                missing.append(
                    {
                        "source_id": source_id,
                        "url": item.get("source_url") or str(source["url"]),
                        "missing_fields": required_missing,
                        "reason": "missing_required_fields",
                    }
                )
                source_missing_reason = "missing required fields"
                continue

            published = parse_datetime(item["published_at"])
            if published is None:
                missing.append(
                    {
                        "source_id": source_id,
                        "url": item["source_url"],
                        "missing_fields": ["published_at"],
                        "reason": "unparseable_published_at",
                    }
                )
                source_missing_reason = "unparseable published_at"
                continue
            if published < window["start"] or published > window["end"]:
                excluded.append({**item, "source_id": source_id, "reason": "outside_window"})
                continue
            if not is_ai_related(item):
                excluded.append({**item, "source_id": source_id, "reason": "not_ai_related"})
                continue

            item_id = stable_id(item)
            if item_id in seen:
                excluded.append({**item, "source_id": source_id, "reason": "duplicate"})
                continue
            seen.add(item_id)

            category = classify(item, list(source.get("coverage", [])))
            candidates.append(
                {
                    "id": item_id,
                    "title": item["title"],
                    "published_at": published.isoformat(timespec="seconds"),
                    "published_display": published.strftime("%Y-%m-%d %H:%M"),
                    "source_url": item["source_url"],
                    "source_id": source_id,
                    "summary_basis": item["summary_basis"],
                    "category": category,
                    "zh_summary": make_summary(item),
                    "needs_model_review": False,
                }
            )
            source_candidate_count += 1

        status = "ok" if source_candidate_count else "partial" if source_missing_reason else "ok"
        coverage.append(
            {
                "source_id": source_id,
                "name": source_name,
                "status": status,
                "raw_count": len(raw_items),
                "candidate_count": source_candidate_count,
                "missing_reason": source_missing_reason,
            }
        )

    return {
        "window": serialize_window(window),
        "source_coverage": coverage,
        "candidates": candidates,
        "excluded": excluded,
        "missing": missing,
    }


def validate_document(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_TOP_LEVEL:
        if field not in data:
            errors.append(f"missing top-level field: {field}")
    if errors:
        return errors

    if not isinstance(data["source_coverage"], list):
        errors.append("source_coverage must be a list")
    if not isinstance(data["candidates"], list):
        errors.append("candidates must be a list")
    if not isinstance(data["excluded"], list):
        errors.append("excluded must be a list")
    if not isinstance(data["missing"], list):
        errors.append("missing must be a list")

    for index, coverage in enumerate(data.get("source_coverage", [])):
        for field in ["source_id", "name", "status", "raw_count", "candidate_count", "missing_reason"]:
            if field not in coverage:
                errors.append(f"source_coverage[{index}] missing {field}")
        if coverage.get("status") not in {"ok", "partial", "failed", "skipped"}:
            errors.append(f"source_coverage[{index}] has invalid status")

    for index, candidate in enumerate(data.get("candidates", [])):
        for field in REQUIRED_CANDIDATE_FIELDS:
            if field not in candidate:
                errors.append(f"candidates[{index}] missing {field}")
        if candidate.get("category") not in CATEGORIES:
            errors.append(f"candidates[{index}] has invalid category")
        if candidate.get("needs_model_review") is False:
            for field in ["title", "published_at", "published_display", "source_url", "summary_basis", "zh_summary"]:
                if not candidate.get(field):
                    errors.append(f"candidates[{index}] missing render field {field}")

    return errors


def validate_sources() -> list[str]:
    errors: list[str] = []
    registry = load_json(BASE_DIR / "references" / "sources.json")
    sources = registry.get("sources", [])
    if not isinstance(sources, list):
        return ["sources.json must contain sources[]"]
    seen: set[str] = set()
    for index, source in enumerate(sources):
        for field in ["id", "name", "kind", "url", "adapter", "coverage"]:
            if field not in source:
                errors.append(f"sources[{index}] missing {field}")
        source_id = str(source.get("id", ""))
        if source_id in seen:
            errors.append(f"duplicate source id: {source_id}")
        seen.add(source_id)
        adapter = source.get("adapter")
        if adapter not in ADAPTERS:
            errors.append(f"sources[{index}] unknown adapter: {adapter}")
        coverage = source.get("coverage")
        if not isinstance(coverage, list) or not coverage:
            errors.append(f"sources[{index}] coverage must be a non-empty list")
        elif any(category not in CATEGORIES for category in coverage):
            errors.append(f"sources[{index}] contains invalid coverage category")
    return errors


def render_markdown(data: dict[str, Any]) -> str:
    errors = validate_document(data)
    if errors:
        raise ValueError("invalid ai-news document:\n" + "\n".join(errors))

    brief_template = (BASE_DIR / "templates" / "brief.md.tpl").read_text(encoding="utf-8")
    item_template = (BASE_DIR / "templates" / "item.md.tpl").read_text(encoding="utf-8")
    sections: list[str] = []

    for category in CATEGORIES:
        items = [
            item
            for item in data["candidates"]
            if item.get("category") == category and item.get("needs_model_review") is False
        ]
        if not items:
            continue
        sections.append(f"## {category_heading(category)}")
        for item in items:
            sections.append(item_template.format(**item))

    rendered = brief_template.format(date_label=data["window"]["label"], sections="\n\n".join(sections).strip())
    return rendered.rstrip() + "\n"


def category_heading(category: str) -> str:
    icons = {
        "模型 / 研究": "🧠",
        "Agent / 开发者工具": "🛠️",
        "技术博客 / 工程实践": "🧪",
        "产品 / 应用": "🚀",
        "商业 / 融资": "💼",
        "安全 / 治理": "🛡️",
    }
    return f"{icons[category]} {category}"


def cmd_collect(args: argparse.Namespace) -> int:
    document = collect_document(args)
    dump_json(document, args.out)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    errors = validate_sources()
    if args.input:
        errors.extend(validate_document(load_json(args.input)))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    print(render_markdown(load_json(args.input)), end="")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    document = collect_document(args)
    errors = validate_document(document)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(render_markdown(document), end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect, validate, and render AI news briefs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect = subparsers.add_parser("collect", help="Collect candidate news into JSON.")
    collect.add_argument("--date", help="Target local natural day, YYYY-MM-DD.")
    collect.add_argument("--window", default="72h", help="Rolling time window, for example 72h.")
    collect.add_argument("--dry-run", action="store_true", help="Use deterministic offline fixture data.")
    collect.add_argument("--out", type=Path, help="Write JSON to this path instead of stdout.")
    collect.set_defaults(func=cmd_collect)

    validate = subparsers.add_parser("validate", help="Validate sources and optionally a candidate JSON file.")
    validate.add_argument("--input", type=Path, help="Candidate JSON to validate.")
    validate.set_defaults(func=cmd_validate)

    render = subparsers.add_parser("render", help="Render a validated candidate JSON file to markdown.")
    render.add_argument("--input", type=Path, required=True, help="Candidate JSON to render.")
    render.set_defaults(func=cmd_render)

    run = subparsers.add_parser("run", help="Collect and render a markdown brief.")
    run.add_argument("--date", help="Target local natural day, YYYY-MM-DD.")
    run.add_argument("--window", default="72h", help="Rolling time window, for example 72h.")
    run.add_argument("--dry-run", action="store_true", help="Use deterministic offline fixture data.")
    run.set_defaults(func=cmd_run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
