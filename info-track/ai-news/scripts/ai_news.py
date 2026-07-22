#!/usr/bin/env python3
"""Executable collector for the ai-news skill."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from adapters import ADAPTERS as FETCHERS  # noqa: E402


TZ = timezone(timedelta(hours=8))
REQUIRED_TOP_LEVEL = ["window", "sources", "candidates"]
REQUIRED_CANDIDATE_FIELDS = [
    "title",
    "url",
    "summary",
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
        out.parent.mkdir(parents=True, exist_ok=True)
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

    end = datetime.now(TZ)
    start = end - timedelta(hours=72)
    return {"start": start, "end": end, "label": "最近72小时"}


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
    text = re.sub(r"\s+GMT$", " +0000", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+UTC$", " +0000", text, flags=re.IGNORECASE)
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M %z",
        "%d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
        "%b %d, %Y",
        "%B %d, %Y",
    ):
        try:
            parsed = datetime.strptime(text, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=TZ)
            return parsed.astimezone(TZ)
        except ValueError:
            pass
    return None


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("&#8217;", "'")).strip()


def is_noisy_summary(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in ("article url:", "comments url:", "points:"))


def is_noise_entry(item: dict[str, str], source_id: str, window: dict[str, Any]) -> bool:
    title = item.get("title", "").strip()
    url = item.get("source_url", "").strip()
    lowered_url = url.lower()
    lowered_title = title.lower()

    if not url.startswith(("http://", "https://")):
        return True
    if any(token in lowered_url for token in ["javascript:", "mailto:", "beian.miit.gov.cn", "12377.cn"]):
        return True
    if re.search(r"[\w.+-]+@[\w.-]+", title):
        return True
    if any(token in title for token in ["ICP备", "公网安备", "iOS & Android", "创投家CLUB", "网上有害信息举报"]):
        return True
    if title.startswith("Edge AI Daily 早报"):
        return True
    if title.startswith("Hex 2077 AI资讯"):
        return True
    if title.startswith((">>", "Skip to ", "Try Claude", "Start building")):
        return True
    if re.match(r"^\d+\s*天前", title):
        return True
    if source_id == "tmtpost-edge-ai-daily" and window.get("date"):
        month = int(str(window["date"])[5:7])
        day = int(str(window["date"])[8:10])
        if f"{month}月{day}日" not in title:
            return True
    if lowered_title in {"research", "product", "announcements", "policy"}:
        return True
    return False


def resolve_fetcher(source: dict[str, Any]):
    source_id = str(source.get("id", ""))
    kind = str(source.get("kind", ""))
    if kind == "rss":
        return FETCHERS["rss"]
    if kind == "json":
        return FETCHERS["tensorfeed_json"]
    if source_id == "anthropic-news":
        return FETCHERS["anthropic"]
    if source_id == "tmtpost-edge-ai-daily":
        return FETCHERS["tmtpost"]
    if source_id == "maomu-news":
        return FETCHERS["maomu"]
    if source_id == "xiaohu-daily":
        return FETCHERS["xiaohu"]
    if source_id == "hex2077":
        return FETCHERS["hex2077"]
    return FETCHERS["html"]


def collect_data(args: argparse.Namespace) -> dict[str, Any]:
    registry = load_json(BASE_DIR / "references" / "sources.json")
    sources = registry.get("sources", [])
    if not isinstance(sources, list):
        raise ValueError("references/sources.json must contain sources[]")
    window = build_window(args)

    candidates: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []

    for source in sources:
        source_id = str(source["id"])
        source_name = str(source["name"])
        fetcher = resolve_fetcher(source)

        try:
            raw_items = fetcher(source, window)
        except Exception as exc:  # pragma: no cover - network sources drift.
            source_rows.append(
                {
                    "source_id": source_id,
                    "name": source_name,
                    "ok": False,
                    "raw": 0,
                    "candidates": 0,
                    "error": str(exc),
                }
            )
            continue

        source_candidate_count = 0
        for raw in raw_items:
            item = {key: clean_text(str(raw.get(key, "") or "")) for key in ["title", "source_url", "published_at", "summary_basis"]}
            required_missing = [key for key in ["title", "source_url", "published_at", "summary_basis"] if not item[key]]
            if required_missing:
                continue

            published = parse_datetime(item["published_at"])
            if published is None:
                continue
            if is_noise_entry(item, source_id, window):
                continue
            if is_noisy_summary(item["summary_basis"]):
                continue
            if published < window["start"] or published > window["end"]:
                continue

            candidates.append(
                {
                    "title": item["title"],
                    "url": item["source_url"],
                    "summary": item["summary_basis"],
                }
            )
            source_candidate_count += 1

        source_rows.append(
            {
                "source_id": source_id,
                "name": source_name,
                "ok": True,
                "raw": len(raw_items),
                "candidates": source_candidate_count,
                "error": None,
            }
        )

    return {
        "window": serialize_window(window),
        "candidates": candidates,
        "_sources": source_rows,
    }


def public_document(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "window": data["window"],
        "sources": {
            row["source_id"]: {
                "ok": row["ok"],
                "count": row["candidates"],
                "error": row["error"],
            }
            for row in data["_sources"]
        },
        "candidates": data["candidates"],
    }


def collect_document(args: argparse.Namespace) -> dict[str, Any]:
    return public_document(collect_data(args))


def validate_document(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_TOP_LEVEL:
        if field not in data:
            errors.append(f"missing top-level field: {field}")
    if errors:
        return errors

    if not isinstance(data["candidates"], list):
        errors.append("candidates must be a list")
    if not isinstance(data["sources"], dict):
        errors.append("sources must be an object")

    for index, candidate in enumerate(data.get("candidates", [])):
        for field in REQUIRED_CANDIDATE_FIELDS:
            if field not in candidate:
                errors.append(f"candidates[{index}] missing {field}")
            elif not candidate.get(field):
                errors.append(f"candidates[{index}] has empty {field}")
        url = str(candidate.get("url", "") or "")
        if not url.startswith(("http://", "https://")):
            errors.append(f"candidates[{index}] has invalid url")
        if is_noisy_summary(str(candidate.get("summary", ""))):
            errors.append(f"candidates[{index}] contains uncleaned aggregator summary")

    return errors


def validate_sources() -> list[str]:
    errors: list[str] = []
    registry = load_json(BASE_DIR / "references" / "sources.json")
    sources = registry.get("sources", [])
    if not isinstance(sources, list):
        return ["sources.json must contain sources[]"]
    seen: set[str] = set()
    for index, source in enumerate(sources):
        for field in ["id", "name", "kind", "url"]:
            if field not in source:
                errors.append(f"sources[{index}] missing {field}")
        source_id = str(source.get("id", ""))
        if source_id in seen:
            errors.append(f"repeated source id: {source_id}")
        seen.add(source_id)
    return errors


def format_candidate(item: dict[str, Any]) -> str:
    title = str(item.get("title", ""))
    summary = str(item.get("summary", ""))
    url = str(item.get("url", ""))
    return f"### {title}\n摘要：{summary}\n来源链接：{url}"


def render_markdown(data: dict[str, Any]) -> str:
    errors = validate_document(data)
    if errors:
        raise ValueError("invalid ai-news document:\n" + "\n".join(errors))

    candidates = data["candidates"]
    rendered_items = [format_candidate(item) for item in candidates]
    range_note = f"候选数量：{len(candidates)}"
    sections = [range_note, *rendered_items]

    body = "\n\n".join(sections).strip()
    rendered = f"# AI 新闻候选｜{data['window']['label']}\n\n{body}"
    return rendered.rstrip() + "\n"


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


def cmd_verify_sources(args: argparse.Namespace) -> int:
    document = collect_data(args)
    registry = load_json(BASE_DIR / "references" / "sources.json")
    source_min_raw: dict[str, int] = {}
    for source in registry.get("sources", []):
        if isinstance(source, dict):
            verify = source.get("verify", {})
            if isinstance(verify, dict) and "minRaw" in verify:
                source_min_raw[str(source.get("id"))] = int(verify["minRaw"])
    if args.out:
        dump_json(public_document(document), args.out)
    errors = validate_document(public_document(document))
    for row in document["_sources"]:
        raw_count = int(row.get("raw", 0))
        if row.get("ok") is not True:
            errors.append(f"source {row.get('source_id')} failed: {row.get('error')}")
        min_raw = source_min_raw.get(str(row.get("source_id")), args.min_raw)
        if raw_count < min_raw:
            errors.append(f"source {row.get('source_id')} raw_count={raw_count} < {min_raw}")

    if errors:
        print("AI_NEWS_SOURCE_VERIFY_FAILED", file=sys.stderr)
        for row in document["_sources"]:
            print(
                f"{row['source_id']}\tok={row.get('ok')}\traw={row.get('raw')}\t"
                f"candidates={row.get('candidates')}\terror={row.get('error')}",
                file=sys.stderr,
            )
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    for row in document["_sources"]:
        print(
            f"{row['source_id']}\tok={row.get('ok')}\traw={row.get('raw')}\t"
            f"candidates={row.get('candidates')}"
        )
    return 0


def add_hidden_subparser(subparsers: argparse._SubParsersAction, name: str) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(name, help=argparse.SUPPRESS)
    subparsers._choices_actions = [action for action in subparsers._choices_actions if action.dest != name]
    return parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect and render AI news candidates.")
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="{collect,render}")

    collect = subparsers.add_parser("collect", help="Collect candidate news into JSON.")
    collect.add_argument("--date", help="Target local natural day, YYYY-MM-DD.")
    collect.add_argument("--out", type=Path, help="Write JSON to this path instead of stdout.")
    collect.set_defaults(func=cmd_collect)

    validate = add_hidden_subparser(subparsers, "validate")
    validate.add_argument("--input", type=Path, help="Candidate JSON to validate.")
    validate.set_defaults(func=cmd_validate)

    render = subparsers.add_parser("render", help="Render a candidate JSON file to readable markdown.")
    render.add_argument("--input", type=Path, required=True, help="Candidate JSON to render.")
    render.set_defaults(func=cmd_render)

    run = add_hidden_subparser(subparsers, "run")
    run.add_argument("--date", help="Target local natural day, YYYY-MM-DD.")
    run.set_defaults(func=cmd_run)

    verify_sources = add_hidden_subparser(subparsers, "verify-sources")
    verify_sources.add_argument("--date", help="Target local natural day, YYYY-MM-DD.")
    verify_sources.add_argument("--min-raw", type=int, default=0, help="Default minimum raw items required per source.")
    verify_sources.add_argument("--out", type=Path, help="Write collected JSON to this path.")
    verify_sources.set_defaults(func=cmd_verify_sources)

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
