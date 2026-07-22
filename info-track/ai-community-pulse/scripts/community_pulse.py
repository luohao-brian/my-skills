#!/usr/bin/env python3
"""Collect fixed-channel AI community topics and render a compact brief."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo


BASE_DIR = Path(__file__).resolve().parent.parent
CHANNELS_PATH = BASE_DIR / "references" / "channels.json"
LOCAL_TZ = ZoneInfo("Asia/Shanghai")
TOPIC_ORDER = ["models", "agents", "systems", "semiconductors"]
TOPIC_HEADINGS = {
    "models": "🧠 模型与评测",
    "agents": "🤖 Agent 与开发工具",
    "systems": "🖥️ AI 系统与本地推理",
    "semiconductors": "🧱 芯片、半导体与算力",
}
USER_AGENT = "ai-community-pulse/1.0 (+fixed-channel collector)"
EXCLUDED_HOSTS = {"github.com", "www.github.com"}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def dump_json(data: dict[str, Any], path: Path | None) -> None:
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if path is None:
        print(payload, end="")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def write_text(text: str, path: Path | None) -> None:
    if path is None:
        print(text, end="")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def clean_text(value: Any, limit: int = 420) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def http_json(url: str, timeout: int = 20) -> Any:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_date(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    text = str(value).strip().replace("Z", "+00:00")
    try:
        result = datetime.fromisoformat(text)
    except ValueError:
        try:
            result = datetime.strptime(text, "%a %b %d %H:%M:%S %z %Y")
        except ValueError:
            return None
    return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result


def iso_or_none(value: Any) -> str | None:
    parsed = parse_date(value)
    return parsed.astimezone(timezone.utc).isoformat() if parsed else None


def within_window(value: Any, start: datetime, end: datetime) -> bool:
    parsed = parse_date(value)
    return parsed is None or start <= parsed <= end


def normalized_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.urlencode(
        sorted(
            (key, value)
            for key, value in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
            if not key.casefold().startswith(("utm_", "ref"))
        )
    )
    return urllib.parse.urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"), query, ""))


def excluded_url(url: str) -> bool:
    host = urllib.parse.urlsplit(url).netloc.lower().split(":", 1)[0]
    return host in EXCLUDED_HOSTS


def keyword_matches(text: str, keywords: Iterable[str]) -> bool:
    haystack = text.casefold()
    for keyword in keywords:
        needle = keyword.casefold()
        if re.fullmatch(r"[a-z0-9][a-z0-9+._/-]*", needle):
            if re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", haystack):
                return True
        elif needle in haystack:
            return True
    return False


def classify(text: str, registry: dict[str, Any], preferred: str | None = None) -> str | None:
    topics = registry["topics"]
    if preferred and keyword_matches(text, topics[preferred]["keywords"]):
        return preferred
    matches: list[tuple[int, str]] = []
    for topic in TOPIC_ORDER:
        count = sum(1 for word in topics[topic]["keywords"] if keyword_matches(text, [word]))
        if count:
            matches.append((count, topic))
    if not matches:
        return None
    matches.sort(key=lambda row: (-row[0], TOPIC_ORDER.index(row[1])))
    return matches[0][1]


def candidate(
    *, title: Any, url: Any, summary: Any, date: Any, source: str, channel: str,
    topic: str, kind: str = "community", metrics: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    clean_title = clean_text(title, 220)
    clean_url = str(url or "").strip()
    if not clean_title or not clean_url.startswith(("http://", "https://")) or excluded_url(clean_url):
        return None
    return {
        "title": clean_title,
        "url": clean_url,
        "summary": clean_text(summary or clean_title),
        "date": iso_or_none(date),
        "source": source,
        "channel": channel,
        "topic": topic,
        "kind": kind,
        "metrics": metrics or {},
    }


def opencli(args: list[str], timeout: int = 18) -> list[dict[str, Any]]:
    command = ["opencli", *args, "-f", "json"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    if result.returncode not in (0, 66):
        message = clean_text(result.stderr or result.stdout or f"exit {result.returncode}", 260)
        raise RuntimeError(message)
    if result.returncode == 66 or not result.stdout.strip():
        return []
    payload = json.loads(result.stdout)
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("items", "posts", "results", "data"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return [row for row in rows if isinstance(row, dict)]
    raise ValueError("OpenCLI output is not a list")


def browser_bridge_ready() -> tuple[bool, str | None]:
    try:
        result = subprocess.run(["opencli", "doctor"], capture_output=True, text=True, timeout=12, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    output = clean_text((result.stdout or "") + " " + (result.stderr or ""), 420)
    if "[OK] Extension" in output and "[OK] Connectivity" in output:
        return True, None
    return False, output or "OpenCLI Browser Bridge unavailable"


def add_source_status(
    statuses: dict[str, Any], source: str, ok: bool, raw: int, selected: int,
    error: str | None = None, warning: str | None = None,
) -> None:
    statuses[source] = {
        "ok": ok, "count": raw, "selected": selected, "error": error,
        **({"warning": warning} if warning else {}),
    }


def collect_bluesky(registry: dict[str, Any], start: datetime, end: datetime) -> tuple[list[dict[str, Any]], int]:
    output: list[dict[str, Any]] = []
    raw_count = 0
    successes = 0
    errors: list[str] = []
    endpoint = "https://public.api.bsky.app/xrpc/app.bsky.feed.getFeed"
    for feed in registry["bluesky_feeds"]:
        url = endpoint + "?" + urllib.parse.urlencode({"feed": feed["uri"], "limit": 35})
        try:
            payload = http_json(url)
            successes += 1
        except Exception as exc:
            errors.append(f"{feed['name']}: {str(exc) or repr(exc)}")
            continue
        rows = payload.get("feed", []) if isinstance(payload, dict) else []
        raw_count += len(rows)
        for row in rows:
            post = row.get("post", {})
            record = post.get("record", {})
            text = clean_text(record.get("text", ""), 600)
            created = record.get("createdAt") or post.get("indexedAt")
            if not within_window(created, start, end):
                continue
            topic = classify(text, registry, feed["topic"])
            if topic is None:
                continue
            author = post.get("author", {})
            handle = author.get("handle") or str(post.get("uri", "")).split("/")[2]
            rkey = str(post.get("uri", "")).rsplit("/", 1)[-1]
            item = candidate(
                title=text.split(". ", 1)[0] or text,
                url=f"https://bsky.app/profile/{handle}/post/{rkey}",
                summary=text,
                date=created,
                source="bluesky",
                channel=feed["name"],
                topic=topic,
                metrics={
                    "likes": post.get("likeCount"), "reposts": post.get("repostCount"),
                    "replies": post.get("replyCount"), "quotes": post.get("quoteCount"),
                },
            )
            if item:
                output.append(item)
    if successes == 0 and errors:
        raise RuntimeError("; ".join(errors))
    return output, raw_count


def collect_hackernews(registry: dict[str, Any], start: datetime, end: datetime) -> tuple[list[dict[str, Any]], int]:
    output: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    raw_count = 0
    root = "https://hacker-news.firebaseio.com/v0"
    feed_by_id: dict[int, str] = {}
    for feed in registry["hackernews_feeds"]:
        ids = http_json(f"{root}/{feed}.json")[:45]
        for item_id in ids:
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                feed_by_id[item_id] = feed

    def fetch_item(item_id: int) -> tuple[int, dict[str, Any] | None]:
        try:
            row = http_json(f"{root}/item/{item_id}.json")
            return item_id, row if isinstance(row, dict) else None
        except Exception:
            return item_id, None

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        rows = list(pool.map(fetch_item, feed_by_id))

    for item_id, row in rows:
        if row is None:
            continue
        raw_count += 1
        title = clean_text(row.get("title", ""))
        body = clean_text(row.get("text", ""))
        if not within_window(row.get("time"), start, end):
            continue
        topic = classify(f"{title} {body}", registry)
        if topic is None:
            continue
        item = candidate(
            title=title,
            url=f"https://news.ycombinator.com/item?id={item_id}",
            summary=body or title,
            date=row.get("time"),
            source="hackernews",
            channel=feed_by_id[item_id].replace("stories", ""),
            topic=topic,
            metrics={"points": row.get("score"), "comments": row.get("descendants")},
        )
        if item:
            output.append(item)
    return output, raw_count


def collect_v2ex(registry: dict[str, Any], start: datetime, end: datetime) -> tuple[list[dict[str, Any]], int]:
    output: list[dict[str, Any]] = []
    raw_count = 0
    successes = 0
    errors: list[str] = []
    for preferred, nodes in registry["v2ex_nodes"].items():
        for node in nodes:
            try:
                rows = http_json("https://www.v2ex.com/api/topics/show.json?" + urllib.parse.urlencode({"node_name": node}))
                successes += 1
            except Exception as exc:
                errors.append(f"{node}: {str(exc) or repr(exc)}")
                continue
            if not isinstance(rows, list):
                continue
            raw_count += len(rows)
            for row in rows[:25]:
                title = clean_text(row.get("title", ""))
                body = clean_text(row.get("content", ""))
                if not within_window(row.get("created"), start, end):
                    continue
                topic = classify(f"{title} {body}", registry, preferred)
                if topic is None:
                    continue
                item = candidate(
                    title=title,
                    url=row.get("url") or f"https://www.v2ex.com/t/{row.get('id')}",
                    summary=body or title,
                    date=row.get("created"),
                    source="v2ex",
                    channel=node,
                    topic=topic,
                    metrics={"replies": row.get("replies")},
                )
                if item:
                    output.append(item)
    if successes == 0 and errors:
        raise RuntimeError("; ".join(errors))
    return output, raw_count


def collect_opencli_public(registry: dict[str, Any], source: str) -> tuple[list[dict[str, Any]], int]:
    output: list[dict[str, Any]] = []
    raw_count = 0
    successes = 0
    errors: list[str] = []
    config_key = {"lobsters": "lobsters", "lesswrong": "lesswrong", "producthunt": "producthunt"}[source]
    for spec in registry[config_key]:
        try:
            rows = opencli([source, spec["command"], *spec.get("args", []), "--limit", "25"])
            successes += 1
        except Exception as exc:
            errors.append(f"{spec['channel']}: {str(exc) or repr(exc)}")
            continue
        raw_count += len(rows)
        for row in rows:
            title = row.get("title") or row.get("name") or row.get("topic")
            summary = row.get("summary") or row.get("tagline") or row.get("description") or title
            topic = classify(f"{title or ''} {summary or ''} {row.get('tags', '')}", registry)
            if topic is None:
                continue
            item = candidate(
                title=title,
                url=row.get("url") or row.get("link"),
                summary=summary,
                date=row.get("created_at") or row.get("date") or row.get("published_at"),
                source=source,
                channel=spec["channel"],
                topic=topic,
                kind="product" if source == "producthunt" else "community",
                metrics={key: row.get(key) for key in ("score", "comments", "karma", "rank") if row.get(key) is not None},
            )
            if item:
                output.append(item)
    if successes == 0 and errors:
        raise RuntimeError("; ".join(errors))
    return output, raw_count


def json_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []


def collect_polymarket(registry: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    config = registry["polymarket"]
    urls = ["https://gamma-api.polymarket.com/events?active=true&closed=false&limit=200&order=volume24hr&ascending=false"]
    urls += [f"https://gamma-api.polymarket.com/events?active=true&closed=false&limit=100&tag_id={tag}" for tag in config["tag_ids"]]
    urls += [f"https://gamma-api.polymarket.com/events?active=true&closed=false&limit=100&series_id={series}" for series in config["series_ids"]]
    events: dict[str, dict[str, Any]] = {}
    for url in urls:
        rows = http_json(url)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict):
                events[str(row.get("id") or row.get("slug"))] = row
    output: list[dict[str, Any]] = []
    for event in events.values():
        event_title = clean_text(event.get("title", ""))
        if not keyword_matches(event_title, config["terms"]):
            continue
        markets = event.get("markets") if isinstance(event.get("markets"), list) else []
        active_markets = [market for market in markets if not market.get("closed")]
        selected_market = max(
            active_markets or markets or [{}],
            key=lambda market: float(market.get("volume24hr") or market.get("liquidity") or 0),
        )
        title = clean_text(selected_market.get("question") or event_title)
        topic = classify(f"{event_title} {title}", registry)
        if topic is None:
            continue
        probability = None
        outcomes = json_list(selected_market.get("outcomes"))
        prices = json_list(selected_market.get("outcomePrices"))
        if len(outcomes) == len(prices) and outcomes:
            try:
                yes_index = next((i for i, outcome in enumerate(outcomes) if str(outcome).casefold() == "yes"), 0)
                probability = round(float(prices[yes_index]) * 100, 1)
            except (ValueError, TypeError):
                pass
        summary = f"当前市场概率约 {probability}%（市场定价，不是事实判断）" if probability is not None else "预测市场事件（市场定价，不是事实判断）"
        item = candidate(
            title=f"预测市场：{title}",
            url=f"https://polymarket.com/event/{event.get('slug')}",
            summary=summary,
            date=event.get("creationDate") or event.get("createdAt"),
            source="polymarket",
            channel="AI / chips fixed market universe",
            topic=topic,
            kind="prediction_market",
            metrics={
                "probability": probability,
                "volume24hr": selected_market.get("volume24hr") or event.get("volume24hr"),
                "liquidity": selected_market.get("liquidity") or event.get("liquidity"),
            },
        )
        if item:
            output.append(item)
    return output, len(events)


def row_to_generic_candidate(
    row: dict[str, Any], registry: dict[str, Any], source: str, channel: str, preferred: str | None = None,
) -> dict[str, Any] | None:
    title = row.get("title") or row.get("name") or row.get("text") or row.get("content")
    summary = row.get("summary") or row.get("description") or row.get("text") or row.get("content") or title
    topic = classify(f"{title or ''} {summary or ''}", registry, preferred)
    if topic is None:
        return None
    url = row.get("url") or row.get("link") or row.get("permalink")
    if isinstance(url, str) and url.startswith("/"):
        bases = {"reddit": "https://www.reddit.com", "twitter": "https://x.com", "bilibili": "https://www.bilibili.com", "zhihu": "https://www.zhihu.com", "linux-do": "https://linux.do"}
        url = bases.get(source, "") + url
    return candidate(
        title=title, url=url, summary=summary,
        date=row.get("created_at") or row.get("created_utc") or row.get("date") or row.get("time") or row.get("published_at"),
        source=source, channel=channel, topic=topic,
        metrics={key: row.get(key) for key in ("score", "comments", "likes", "replies", "rank") if row.get(key) is not None},
    )


def collect_browser_sources(
    registry: dict[str, Any], start: datetime | None = None, end: datetime | None = None,
) -> tuple[
    dict[str, list[dict[str, Any]]], dict[str, tuple[int, int]], dict[str, str], dict[str, str]
]:
    collected: dict[str, list[dict[str, Any]]] = defaultdict(list)
    counts: dict[str, tuple[int, int]] = {}
    errors: dict[str, str] = {}
    warnings: dict[str, str] = {}

    for source, config_key in (("twitter", "twitter_accounts"), ("reddit", "reddit_subreddits")):
        raw = selected = 0
        successful_channels = 0
        channel_errors: list[str] = []
        for preferred, channels in registry[config_key].items():
            for channel in channels:
                try:
                    args = [source, "tweets", channel, "--limit", "12"] if source == "twitter" else [source, "subreddit", channel, "--sort", "hot", "--limit", "12"]
                    rows = opencli(args, timeout=20)
                    successful_channels += 1
                    raw += len(rows)
                    for row in rows:
                        item = row_to_generic_candidate(row, registry, source, channel, preferred)
                        if item and (start is None or end is None or within_window(item.get("date"), start, end)):
                            collected[source].append(item)
                            selected += 1
                except Exception as exc:
                    channel_errors.append(f"{channel}: {str(exc) or repr(exc)}")
        if successful_channels:
            counts[source] = (raw, selected)
            if channel_errors:
                warnings[source] = clean_text("; ".join(channel_errors), 720)
        else:
            errors[source] = clean_text("; ".join(channel_errors) or "all fixed channels failed", 720)

    for source, config_key in (("zhihu", "zhihu"), ("linux-do", "linux_do"), ("bilibili", "bilibili")):
        raw = selected = 0
        successful_channels = 0
        channel_errors = []
        for spec in registry[config_key]:
            try:
                rows = opencli([source, spec["command"], *spec.get("args", []), "--limit", "25"], timeout=20)
                successful_channels += 1
                raw += len(rows)
                for row in rows:
                    item = row_to_generic_candidate(row, registry, source, spec["channel"])
                    if item and (start is None or end is None or within_window(item.get("date"), start, end)):
                        collected[source].append(item)
                        selected += 1
            except Exception as exc:
                channel_errors.append(f"{spec['channel']}: {str(exc) or repr(exc)}")
        if successful_channels:
            counts[source] = (raw, selected)
            if channel_errors:
                warnings[source] = clean_text("; ".join(channel_errors), 720)
        else:
            errors[source] = clean_text("; ".join(channel_errors) or "all fixed channels failed", 720)
    return collected, counts, errors, warnings


def deduplicate(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for item in items:
        key = normalized_url(item["url"])
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def collect_document(args: argparse.Namespace) -> dict[str, Any]:
    registry = load_json(args.channels)
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=args.hours)
    statuses: dict[str, Any] = {}
    candidates: list[dict[str, Any]] = []

    collectors = {
        "bluesky": lambda: collect_bluesky(registry, start, end),
        "hackernews": lambda: collect_hackernews(registry, start, end),
        "v2ex": lambda: collect_v2ex(registry, start, end),
        "lobsters": lambda: collect_opencli_public(registry, "lobsters"),
        "lesswrong": lambda: collect_opencli_public(registry, "lesswrong"),
        "producthunt": lambda: collect_opencli_public(registry, "producthunt"),
        "polymarket": lambda: collect_polymarket(registry),
    }
    for source, collector_fn in collectors.items():
        try:
            rows, raw = collector_fn()
            candidates.extend(rows)
            add_source_status(statuses, source, True, raw, len(rows))
        except Exception as exc:  # External sources can drift independently.
            add_source_status(statuses, source, False, 0, 0, clean_text(exc, 360))

    browser_sources = ["twitter", "reddit", "zhihu", "linux-do", "bilibili"]
    if args.skip_browser:
        for source in browser_sources:
            add_source_status(statuses, source, False, 0, 0, "browser-backed collection disabled by --skip-browser")
    else:
        ready, reason = browser_bridge_ready()
        if not ready:
            for source in browser_sources:
                add_source_status(statuses, source, False, 0, 0, reason)
        else:
            try:
                browser_rows, counts, errors, warnings = collect_browser_sources(registry, start, end)
                for source in browser_sources:
                    if source in errors:
                        add_source_status(statuses, source, False, 0, 0, errors[source])
                        continue
                    rows = browser_rows.get(source, [])
                    raw, selected = counts.get(source, (0, 0))
                    candidates.extend(rows)
                    add_source_status(statuses, source, True, raw, selected, warning=warnings.get(source))
            except Exception as exc:
                message = clean_text(exc, 360)
                for source in browser_sources:
                    if source not in statuses:
                        add_source_status(statuses, source, False, 0, 0, message)

    return {
        "window": {"start": start.isoformat(), "end": end.isoformat(), "hours": args.hours},
        "sources": statuses,
        "candidates": deduplicate(candidates),
    }


def select_diverse(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    by_source: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
    for item in items:
        by_source[item["source"]].append(item)
    result: list[dict[str, Any]] = []
    source_order = deque(sorted(by_source, key=lambda key: (key == "polymarket", key)))
    while source_order and len(result) < limit:
        source = source_order.popleft()
        queue = by_source[source]
        if queue:
            result.append(queue.popleft())
        if queue:
            source_order.append(source)
    return result


def render_markdown(data: dict[str, Any], limit_per_topic: int) -> str:
    start = parse_date(data["window"]["start"]).astimezone(LOCAL_TZ)
    end = parse_date(data["window"]["end"]).astimezone(LOCAL_TZ)
    lines = [
        f"# AI 社区与生态热点｜{end:%Y-%m-%d}",
        "",
        f"统计窗口：{start:%Y-%m-%d %H:%M} ～ {end:%Y-%m-%d %H:%M}（Asia/Shanghai）",
    ]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in data.get("candidates", []):
        grouped[item.get("topic")].append(item)

    for topic in TOPIC_ORDER:
        lines += ["", f"## {TOPIC_HEADINGS[topic]}", ""]
        selected = select_diverse(grouped.get(topic, []), limit_per_topic)
        if not selected:
            lines.append("本期无入选话题。")
            continue
        for item in selected:
            title = item["title"]
            summary = item.get("summary") or title
            label = f"{item['source']} · {item['channel']}"
            lines += [f"### {title}", "", f"摘要：{summary}", "", "社区来源：", "", f"- [{label}]({item['url']})", ""]

    successful = [name for name, row in data.get("sources", {}).items() if row.get("ok")]
    failed = [(name, row.get("error") or "unknown error") for name, row in data.get("sources", {}).items() if not row.get("ok")]
    lines += ["## 采集状态", "", f"- 成功：{', '.join(successful) if successful else '无'}"]
    if failed:
        lines.append("- 未采集：" + "；".join(f"{name}（{clean_text(error, 160)}）" for name, error in failed))
    else:
        lines.append("- 未采集：无")
    return "\n".join(lines).rstrip() + "\n"


def validate_document(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("window", "sources", "candidates"):
        if key not in data:
            errors.append(f"missing top-level field: {key}")
    for index, item in enumerate(data.get("candidates", [])):
        for key in ("title", "url", "summary", "source", "channel", "topic", "kind", "metrics"):
            if key not in item:
                errors.append(f"candidates[{index}] missing {key}")
        if item.get("topic") not in TOPIC_ORDER:
            errors.append(f"candidates[{index}] invalid topic")
    return errors


def cmd_collect(args: argparse.Namespace) -> int:
    document = collect_document(args)
    errors = validate_document(document)
    if errors:
        raise ValueError("\n".join(errors))
    dump_json(document, args.output)
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    data = load_json(args.input)
    errors = validate_document(data)
    if errors:
        raise ValueError("\n".join(errors))
    write_text(render_markdown(data, args.limit_per_topic), args.output)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    document = collect_document(args)
    errors = validate_document(document)
    if errors:
        raise ValueError("\n".join(errors))
    dump_json(document, args.json_output)
    write_text(render_markdown(document, args.limit_per_topic), args.report_output)
    return 0


def add_collection_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--hours", type=int, default=72, help="Rolling collection window in hours (default: 72).")
    parser.add_argument("--channels", type=Path, default=CHANNELS_PATH, help="Fixed channel registry JSON.")
    parser.add_argument("--skip-browser", action="store_true", help="Skip browser/login-backed sources.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect fixed-channel AI community topics.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    collect = subparsers.add_parser("collect", help="Collect candidates into JSON.")
    add_collection_args(collect)
    collect.add_argument("--output", type=Path, help="JSON output path; stdout when omitted.")
    collect.set_defaults(func=cmd_collect)

    render = subparsers.add_parser("render", help="Render collected JSON into Markdown.")
    render.add_argument("--input", type=Path, required=True)
    render.add_argument("--output", type=Path, help="Markdown output path; stdout when omitted.")
    render.add_argument("--limit-per-topic", type=int, default=12)
    render.set_defaults(func=cmd_render)

    run = subparsers.add_parser("run", help="Collect and render in one command.")
    add_collection_args(run)
    run.add_argument("--json-output", type=Path, required=True)
    run.add_argument("--report-output", type=Path, required=True)
    run.add_argument("--limit-per-topic", type=int, default=12)
    run.set_defaults(func=cmd_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
