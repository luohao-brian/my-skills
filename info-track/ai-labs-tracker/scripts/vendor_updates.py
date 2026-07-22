#!/usr/bin/env python3

from __future__ import annotations



import argparse

import datetime as dt

import email.utils

import html

import json

import os

import re

import sys

import time

import urllib.error

import urllib.parse

import urllib.request

import xml.etree.ElementTree as ET

from dataclasses import dataclass, field

from pathlib import Path

from typing import Any, Callable

from zoneinfo import ZoneInfo



USER_AGENT = "my-skills-info-track/1.0"

VENDOR_PRODUCT = "AI厂商产品更新"

VENDOR_BLOG = "AI厂商博客更新"

MISC = "-misc"

@dataclass
class Item:
    title: str
    url: str
    source: str
    date: str = ""
    description: str = ""
    category: str = ""
    score: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

def fetch_text(url: str, timeout: int = 30, retries: int = 2) -> str:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                charset = resp.headers.get_content_charset() or "utf-8"
                return resp.read().decode(charset, errors="replace")
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(1 + attempt)
    raise last_error or RuntimeError(f"failed to fetch {url}")

def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", value)
    value = re.sub(r"(?is)<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def text_from_html(value: str) -> str:
    return clean_text(value)

def parse_date(value: str | None, fallback_year: int | None = None) -> dt.date | None:
    text = clean_text(value or "")
    if not text:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(text)
        if parsed.tzinfo:
            parsed = parsed.astimezone(dt.timezone.utc)
        return parsed.date()
    except Exception:
        pass
    patterns = [
        (r"(20\d{2})-(\d{1,2})-(\d{1,2})", lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3)))),
        (r"(20\d{2})/(\d{1,2})/(\d{1,2})", lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3)))),
        (
            r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+20\d{2})",
            lambda m: dt.datetime.strptime(m.group(1), "%B %d, %Y").date(),
        ),
        (
            r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+20\d{2})",
            lambda m: dt.datetime.strptime(m.group(1), "%b %d, %Y").date(),
        ),
    ]
    for pattern, parser in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        try:
            parsed = parser(match)
            if isinstance(parsed, dt.date):
                return parsed
            return dt.date(*parsed)
        except Exception:
            pass
    match = re.search(r"(\d{1,2})月(\d{1,2})日", text)
    if match and fallback_year:
        return dt.date(fallback_year, int(match.group(1)), int(match.group(2)))
    return None

def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]

def child_text(node: ET.Element, name: str) -> str:
    for child in list(node):
        if local_name(child.tag) == name:
            return "".join(child.itertext())
    return ""

def normalize_url(value: str, base: str = "") -> str:
    value = html.unescape(value or "").strip().replace("\\/", "/")
    if not value:
        return ""
    return urllib.parse.urljoin(base, value)

def in_window(value: str, start: dt.date, end: dt.date) -> bool:
    parsed = parse_date(value, fallback_year=end.year)
    return bool(parsed and start <= parsed <= end)

def resolve_week_window(anchor: dt.date, *, date_is_start: bool) -> tuple[dt.date, dt.date]:
    if date_is_start:
        return anchor, anchor + dt.timedelta(days=6)
    return anchor - dt.timedelta(days=6), anchor

def parse_rss(label: str, url: str) -> list[Item]:
    root = ET.fromstring(fetch_text(url, timeout=45).encode("utf-8"))
    items: list[Item] = []
    for node in root.findall(".//item"):
        pub = child_text(node, "pubDate") or child_text(node, "published") or child_text(node, "updated")
        parsed = parse_date(pub)
        categories = [
            clean_text("".join(child.itertext()))
            for child in list(node)
            if local_name(child.tag) == "category"
        ]
        items.append(
            Item(
                title=clean_text(child_text(node, "title")),
                url=normalize_url(child_text(node, "link"), url),
                source=label,
                date=parsed.isoformat() if parsed else "",
                description=clean_text(child_text(node, "description")),
                metadata={"categories": categories},
            )
        )
    return items

def parse_anthropic_list(label: str, url: str, prefix: str, end: dt.date) -> list[Item]:
    page = fetch_text(url, timeout=45)
    items: list[Item] = []
    seen: set[str] = set()
    for match in re.finditer(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', page, re.S | re.I):
        href, body = match.group(1), match.group(2)
        if not (href.startswith(prefix) or href.startswith(f"https://www.anthropic.com{prefix}")):
            continue
        full_url = normalize_url(href, "https://www.anthropic.com")
        if full_url in seen:
            continue
        seen.add(full_url)
        text = text_from_html(body)
        parsed = parse_date(text, fallback_year=end.year)
        card_desc = ""
        if re.search(r"<p\b", body, flags=re.I):
            card_desc = text
        title = text
        if parsed:
            title = re.sub(r"^(Featured\s+)?", "", title).strip()
            title = re.sub(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+20\d{2}", "", title).strip()
            title = re.sub(r"^(Announcements|Product|Research|Engineering|Company|Policy|Safety)\s+", "", title).strip()
        items.append(
            Item(
                title=title or text,
                url=full_url,
                source=label,
                date=parsed.isoformat() if parsed else "",
                description=card_desc,
            )
        )
    return items

def parse_cursor_blog(end: dt.date) -> list[Item]:
    page = fetch_text("https://cursor.com/cn/blog", timeout=45)
    items: list[Item] = []
    seen: set[str] = set()
    for match in re.finditer(r'<a\s+[^>]*href=["\'](/cn/blog/[^"\']+)["\'][^>]*>(.*?)</a>', page, re.S | re.I):
        href, body = match.group(1), match.group(2)
        if "/topic/" in href or href == "/cn/blog":
            continue
        full_url = normalize_url(href, "https://cursor.com")
        if full_url in seen:
            continue
        seen.add(full_url)
        text = text_from_html(body)
        parsed = parse_date(text, fallback_year=end.year)
        if not parsed:
            continue
        title = extract_first(
            r'<p\b[^>]*class=["\'][^"\']*text-theme-text[^"\']*text-pretty[^"\']*["\'][^>]*>(.*?)</p>',
            body,
        )
        if not title:
            title = text
            title = re.sub(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+20\d{2}\s*·\s*", "", title).strip()
            title = re.sub(r"^(产品|研究|公司|客户案例|创意)\s+", "", title).strip()
            title = re.sub(r"\s+[\w .'-]{2,80}\s+\d+\s+分钟(?:\s+.*)?$", "", title).strip()
        items.append(
            Item(
                title=title,
                url=full_url,
                source="Cursor Blog",
                date=parsed.isoformat(),
                description=title,
            )
        )
    return items

def parse_claude_blog(start: dt.date, end: dt.date) -> list[Item]:
    url = "https://claude.com/blog"
    page = fetch_text(url, timeout=45)
    items: list[Item] = []
    seen: set[str] = set()
    pattern = re.compile(
        r'<div\s+fs-list-field=["\']heading["\'][^>]*>(.*?)</div>'
        r'.*?<div\s+fs-list-fieldtype=["\']date["\']\s+fs-list-field=["\']date["\'][^>]*>(.*?)</div>'
        r'.*?<a\b[^>]*href=["\'](/blog/[^"\']+)["\']',
        re.S | re.I,
    )
    for match in pattern.finditer(page):
        title = clean_text(match.group(1))
        parsed = parse_date(match.group(2), fallback_year=end.year)
        full_url = normalize_url(match.group(3), url)
        if not title or not parsed or not (start <= parsed <= end) or full_url in seen:
            continue
        seen.add(full_url)
        _, description = fetch_page_meta(full_url)
        items.append(
            Item(
                title=title,
                url=full_url,
                source="Claude Blog",
                date=parsed.isoformat(),
                description=description or title,
            )
        )
    return items

def extract_first(pattern: str, text: str) -> str:
    match = re.search(pattern, text, re.S | re.I)
    return clean_text(match.group(1)) if match else ""

def extract_meta(page: str, names: list[str]) -> str:
    meta_tags: list[dict[str, str]] = []
    attribute_pattern = re.compile(
        r'([:\w-]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\')',
        re.S,
    )
    for tag in re.findall(r'<meta\b[^>]*>', page, re.I):
        attributes: dict[str, str] = {}
        for match in attribute_pattern.finditer(tag):
            attributes[match.group(1).lower()] = match.group(2) if match.group(2) is not None else match.group(3)
        meta_tags.append(attributes)
    for name in names:
        for attributes in meta_tags:
            if attributes.get("property") != name and attributes.get("name") != name:
                continue
            value = clean_text(attributes.get("content", ""))
            if value:
                return value
    return ""

def fetch_page_meta(url: str) -> tuple[str, str]:
    try:
        page = fetch_text(url, timeout=25, retries=1)
    except Exception:
        return "", ""
    title = extract_meta(page, ["og:title", "twitter:title"])
    if not title:
        title = extract_first(r"<title[^>]*>(.*?)</title>", page)
    title = re.sub(r"\s*[·|-]\s*Cursor\s*$", "", title).strip()
    description = extract_meta(page, ["og:description", "description", "twitter:description"])
    return title, description

def provider_config() -> tuple[str, str, str]:
    endpoint = os.getenv("LLM_ENDPOINT", os.getenv("AI_NEWS_ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/plan/v3")).rstrip("/")
    model = os.getenv("LLM_COMMON", os.getenv("AI_NEWS_CLASSIFY_MODEL", "deepseek-v4-flash"))
    api_key = os.getenv("LLM_API_KEY") or os.getenv("ARK_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
    return endpoint, model, api_key

def provider_json(payload: dict[str, Any], timeout: int = 160) -> dict[str, Any]:
    endpoint, _, api_key = provider_config()
    if not api_key:
        raise RuntimeError("missing LLM_API_KEY")
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

def parse_provider_json_content(content: str) -> dict[str, Any]:
    content = (content or "").strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.I).strip()
        content = re.sub(r"\s*```$", "", content).strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0))

def rewrite_with_provider(system_prompt: str, rows: list[dict[str, Any]], batch_size: int = 20) -> dict[int, dict[str, str]]:
    _, model, api_key = provider_config()
    if not api_key:
        return {}
    rewrites: dict[int, dict[str, str]] = {}
    for start in range(0, len(rows), batch_size):
        batch = rows[start:start + batch_size]
        batch_id_to_index = {int(row["id"]): start + offset for offset, row in enumerate(batch)}
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "请改写以下条目：\n" + json.dumps(batch, ensure_ascii=False)},
            ],
            "temperature": 0.2,
        }
        try:
            data = provider_json(payload)
            content = data["choices"][0]["message"]["content"]
            parsed = parse_provider_json_content(content)
        except Exception as exc:
            print(f"REWRITE_SKIPPED batch={start} reason={type(exc).__name__}", file=sys.stderr)
            continue
        for row in parsed.get("items", []):
            try:
                local_id = int(row.get("id"))
            except Exception:
                continue
            title = clean_text(str(row.get("title") or row.get("标题") or row.get("zh_title") or ""))
            summary = clean_text(str(row.get("summary") or row.get("description") or row.get("摘要") or row.get("zh_summary") or ""))
            target_index = batch_id_to_index.get(local_id)
            if target_index is None and 1 <= local_id <= len(batch):
                target_index = start + local_id - 1
            if (title or summary) and target_index is not None:
                rewrites[target_index] = {"title": title, "summary": summary}
        time.sleep(0.2)
    return rewrites

def classify_with_provider(system_prompt: str, rows: list[dict[str, Any]], allowed: list[str], batch_size: int = 25) -> dict[int, str]:
    _, model, api_key = provider_config()
    if not api_key:
        return {}
    out: dict[int, str] = {}
    for start in range(0, len(rows), batch_size):
        batch = rows[start:start + batch_size]
        batch_id_to_index = {int(row["id"]): start + offset for offset, row in enumerate(batch)}
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "请分类以下条目：\n" + json.dumps(batch, ensure_ascii=False)},
            ],
            "temperature": 0,
        }
        try:
            data = provider_json(payload)
            content = data["choices"][0]["message"]["content"]
            parsed = parse_provider_json_content(content)
        except Exception as exc:
            print(f"CLASSIFY_SKIPPED batch={start} reason={type(exc).__name__}", file=sys.stderr)
            continue
        for row in parsed.get("items", []):
            try:
                local_id = int(row.get("id"))
            except Exception:
                continue
            category = str(row.get("category") or "").strip()
            if category not in allowed:
                category = MISC
            target_index = batch_id_to_index.get(local_id)
            if target_index is None and 1 <= local_id <= len(batch):
                target_index = start + local_id - 1
            if target_index is not None:
                out[target_index] = category
        time.sleep(0.2)
    return out

def classify_vendor_items(items: list[Item]) -> None:
    system = (
        "你是AI周报条目分类器。分类只能是：AI厂商产品更新、AI厂商博客更新、-misc。"
        "AI厂商产品更新：产品发布、功能更新、客户案例、商业合作、订阅、企业落地、搜索、Workspace、Codex/Cursor产品功能。"
        "AI厂商博客更新：技术博客、研究、工程实践、模型研究、agent harness、科学研究、系统架构。"
        '返回严格JSON：{"items":[{"id":1,"category":"AI厂商产品更新"}]}。不要解释。'
    )
    rows = [
        {
            "id": idx + 1,
            "source": item.source,
            "title": item.title[:500],
            "description": item.description[:500],
            "source_categories": item.metadata.get("categories", []),
        }
        for idx, item in enumerate(items)
    ]
    classified = classify_with_provider(system, rows, [VENDOR_PRODUCT, VENDOR_BLOG, MISC])
    for idx, category in classified.items():
        if 0 <= idx < len(items):
            items[idx].category = category
    for item in items:
        if not item.category:
            text = f"{item.source} {item.title} {item.description}".lower()
            if any(key in text for key in ["research", "engineering", "研究", "技术", "model", "agent harness", "science"]):
                item.category = VENDOR_BLOG
            else:
                item.category = VENDOR_PRODUCT

def rewrite_vendor_items(items: list[Item]) -> None:
    system = (
        "你是AI产品与技术周报编辑。请把厂商新闻/技术博客条目的标题和摘要改写成简洁中文。"
        "只基于输入内容，不要添加未给出的事实。标题保留核心事件，20到45个中文字符。"
        "摘要用1句话，45到95个中文字符，说明更新内容和意义。"
        '返回严格JSON：{"items":[{"id":1,"title":"中文标题","summary":"中文摘要"}]}。不要解释。'
    )
    rows = [
        {
            "id": idx + 1,
            "source": item.source,
            "title": item.title,
            "description": item.description,
            "date": item.date,
            "url": item.url,
            "source_categories": item.metadata.get("categories", []),
        }
        for idx, item in enumerate(items)
    ]
    rewritten = rewrite_with_provider(system, rows, batch_size=20)
    for idx, values in rewritten.items():
        if 0 <= idx < len(items):
            if values.get("title"):
                items[idx].title = values["title"]
            if values.get("summary"):
                items[idx].description = values["summary"]

def dedupe_items(items: list[Item]) -> list[Item]:
    out: list[Item] = []
    seen: set[str] = set()
    for item in items:
        key = item.url or item.title
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out

def fetch_vendor_items(
    start: dt.date,
    end: dt.date,
) -> tuple[list[Item], dict[str, dict[str, Any]]]:
    fetchers: list[tuple[str, Callable[[], list[Item]]]] = [
        ("OpenAI News", lambda: parse_rss("OpenAI News", "https://openai.com/news/rss.xml")),
        ("Google AI Blog", lambda: parse_rss("Google AI Blog", "https://blog.google/innovation-and-ai/technology/ai/rss/")),
        ("Google DeepMind", lambda: parse_rss("Google DeepMind", "https://deepmind.google/blog/rss.xml")),
        ("Interconnects AI", lambda: parse_rss("Interconnects AI", "https://www.interconnects.ai/feed")),
        ("Anthropic News", lambda: parse_anthropic_list("Anthropic News", "https://www.anthropic.com/news", "/news/", end)),
        (
            "Anthropic Engineering",
            lambda: parse_anthropic_list(
                "Anthropic Engineering",
                "https://www.anthropic.com/engineering",
                "/engineering/",
                end,
            ),
        ),
        ("Cursor Blog", lambda: parse_cursor_blog(end)),
        ("Claude Blog", lambda: parse_claude_blog(start, end)),
    ]
    candidates: list[Item] = []
    source_status: dict[str, dict[str, Any]] = {}
    for source, fetcher in fetchers:
        try:
            source_items = [item for item in fetcher() if in_window(item.date, start, end)]
        except Exception as exc:
            source_status[source] = {"ok": False, "count": 0, "selected": 0, "error": type(exc).__name__}
            print(f"FETCH_VENDOR_SKIPPED source={source} reason={type(exc).__name__}", file=sys.stderr)
            continue
        candidates.extend(source_items)
        source_status[source] = {
            "ok": True,
            "count": len(source_items),
            "selected": 0,
            "error": None,
        }
    selected = dedupe_items(candidates)
    classify_vendor_items(selected)
    rewrite_vendor_items(selected)
    selected.sort(key=lambda item: (item.date, item.source, item.title), reverse=True)
    for item in selected:
        source_status[item.source]["selected"] += 1
    return selected, source_status

def item_to_dict(item: Item) -> dict[str, Any]:
    return {
        "title": item.title,
        "url": item.url,
        "summary": item.description,
        "date": item.date,
        "source": item.source,
        "category": item.category,
        "score": item.score,
        "metadata": item.metadata,
    }


def emit_payload(payload: dict[str, Any], output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output:
        path = Path(output).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(path)
    else:
        print(text, end="")


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect weekly AI vendor product and technology updates.")
    parser.add_argument("--date", help="Window start date, YYYY-MM-DD; omit for the recent period ending today")
    parser.add_argument("--output", help="Write candidate JSON to this path; stdout when omitted")
    parser.add_argument("--stats", action="store_true", help="Print source statuses and category counts to stderr")
    args = parser.parse_args()
    try:
        if args.date:
            anchor = dt.date.fromisoformat(args.date)
            start, end = resolve_week_window(anchor, date_is_start=True)
        else:
            anchor = dt.date.today()
            start, end = resolve_week_window(anchor, date_is_start=False)
    except ValueError as exc:
        parser.error(str(exc))
    items, source_status = fetch_vendor_items(start, end)
    payload = {
        "kind": "ai-vendor-updates",
        "window": {"start": start.isoformat(), "end": end.isoformat(), "period": "1w"},
        "sources": source_status,
        "items": [item_to_dict(item) for item in items],
    }
    emit_payload(payload, args.output)
    if args.stats:
        category_counts: dict[str, int] = {}
        for item in items:
            category_counts[item.category] = category_counts.get(item.category, 0) + 1
        stats = {"sources": source_status, "categories": category_counts}
        print(json.dumps(stats, ensure_ascii=False, sort_keys=True), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
