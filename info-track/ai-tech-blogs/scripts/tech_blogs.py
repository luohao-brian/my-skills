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

def parse_halo_datetime(value: str) -> dt.datetime | None:
    text = (value or "").strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    text = re.sub(r"\.(\d{6})\d+([+-]\d\d:\d\d)$", r".\1\2", text)
    try:
        return dt.datetime.fromisoformat(text).astimezone(ZoneInfo("Asia/Shanghai"))
    except Exception:
        return None

def normalize_url(value: str, base: str = "") -> str:
    value = html.unescape(value or "").strip().replace("\\/", "/")
    if not value:
        return ""
    return urllib.parse.urljoin(base, value)

def extract_first(pattern: str, text: str) -> str:
    match = re.search(pattern, text, re.S | re.I)
    return clean_text(match.group(1)) if match else ""

def parse_hubwiz_week(start: dt.date, end: dt.date) -> list[Item]:
    items: list[Item] = []
    seen: set[str] = set()
    page_num = 1
    while True:
        url = "https://www.hubwiz.com/blog/" if page_num == 1 else f"https://www.hubwiz.com/blog/page/{page_num}/"
        page = fetch_text(url, timeout=45)
        cards = re.findall(r'<article\b[^>]*class=["\'][^"\']*post-card[^"\']*["\'][^>]*>(.*?)</article>', page, re.S | re.I)
        if not cards:
            if page_num == 1:
                raise ValueError("Hubwiz response contains no post cards")
            break
        stop = False
        for card in cards:
            href = extract_first(r'<a\b[^>]*class=["\'][^"\']*post-card-content-link[^"\']*["\'][^>]*href=["\']([^"\']+)["\']', card)
            if not href:
                href = extract_first(r'<a\b[^>]*href=["\'](/blog/[^"\']+)["\']', card)
            full_url = normalize_url(href, "https://www.hubwiz.com")
            if not full_url or full_url in seen:
                continue
            date_text = extract_first(r'<time\b[^>]*datetime=["\']([^"\']+)["\']', card)
            parsed = parse_date(date_text, fallback_year=end.year)
            if parsed and parsed < start:
                stop = True
                break
            if not parsed or parsed > end:
                continue
            seen.add(full_url)
            items.append(
                Item(
                    title=extract_first(r'<h2\b[^>]*class=["\'][^"\']*post-card-title[^"\']*["\'][^>]*>(.*?)</h2>', card),
                    url=full_url,
                    source="Hubwiz",
                    date=parsed.isoformat(),
                    description=extract_first(r'<section\b[^>]*class=["\'][^"\']*post-card-excerpt[^"\']*["\'][^>]*>(.*?)</section>', card),
                    category=extract_first(r'<div\b[^>]*class=["\'][^"\']*post-card-primary-tag[^"\']*["\'][^>]*>(.*?)</div>', card),
                )
            )
        if stop or 'rel="next"' not in page:
            break
        page_num += 1
    return items

def parse_qingke_week(start: dt.date, end: dt.date) -> list[Item]:
    url = "https://qingkeai.online/apis/api.content.halo.run/v1alpha1/posts?page=1&size=1000&sort=spec.publishTime,desc"
    data = json.loads(fetch_text(url, timeout=45))
    rows = data.get("items")
    if not isinstance(rows, list):
        raise ValueError("QingkeAI response contains no items list")
    items: list[Item] = []
    for row in rows:
        spec = row.get("spec") or {}
        status = row.get("status") or {}
        published = parse_halo_datetime(spec.get("publishTime", ""))
        if not published:
            continue
        parsed = published.date()
        if parsed < start:
            break
        if parsed > end:
            continue
        categories = [
            category.get("spec", {}).get("displayName", "")
            for category in row.get("categories", [])
            if category.get("spec", {}).get("displayName")
        ]
        tags = [
            tag.get("spec", {}).get("displayName", "")
            for tag in row.get("tags", [])
            if tag.get("spec", {}).get("displayName")
        ]
        permalink = normalize_url(status.get("permalink", ""), "https://qingkeai.online")
        items.append(
            Item(
                title=clean_text(spec.get("title", "")),
                url=permalink,
                source="QingkeAI",
                date=parsed.isoformat(),
                description=clean_text(status.get("excerpt", "")),
                category=", ".join(categories),
                metadata={
                    "tags": tags,
                    "stats": row.get("stats") or {},
                    "source_api": url,
                },
            )
        )
    return items

def resolve_week_window(anchor: dt.date, *, date_is_start: bool) -> tuple[dt.date, dt.date]:
    if date_is_start:
        return anchor, anchor + dt.timedelta(days=6)
    return anchor - dt.timedelta(days=6), anchor


def dedupe_items(items: list[Item]) -> list[Item]:
    selected: list[Item] = []
    seen_urls: set[str] = set()
    for item in items:
        key = item.url.strip()
        if key and key in seen_urls:
            continue
        if key:
            seen_urls.add(key)
        selected.append(item)
    selected.sort(key=lambda item: (item.date, item.source, item.title), reverse=True)
    return selected

def fetch_tech_blog_items(
    start: dt.date,
    end: dt.date,
) -> tuple[list[Item], dict[str, dict[str, Any]]]:
    source_items: dict[str, list[Item]] = {}
    source_status: dict[str, dict[str, Any]] = {}
    for source, fetcher in {
        "Hubwiz": lambda: parse_hubwiz_week(start, end),
        "QingkeAI": lambda: parse_qingke_week(start, end),
    }.items():
        try:
            source_items[source] = fetcher()
        except Exception as exc:
            source_items[source] = []
            source_status[source] = {"ok": False, "count": 0, "selected": 0, "error": type(exc).__name__}
            print(f"TECH_BLOG_FETCH_SKIPPED source={source} reason={type(exc).__name__}", file=sys.stderr)
        else:
            source_status[source] = {
                "ok": True,
                "count": len(source_items[source]),
                "selected": 0,
                "error": None,
            }
    selected = dedupe_items([item for rows in source_items.values() for item in rows])
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
    parser = argparse.ArgumentParser(description="Collect Hubwiz and QingkeAI technical blog posts.")
    parser.add_argument("--date", help="Window start date, YYYY-MM-DD; omit for the recent period ending today")
    parser.add_argument("--output", help="Write candidate JSON to this path; stdout when omitted")
    parser.add_argument("--stats", action="store_true", help="Print source statuses to stderr")
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
    items, source_status = fetch_tech_blog_items(start, end)
    payload = {
        "kind": "ai-tech-blogs",
        "window": {"start": start.isoformat(), "end": end.isoformat(), "period": "1w"},
        "sources": source_status,
        "items": [item_to_dict(item) for item in items],
    }
    emit_payload(payload, args.output)
    if args.stats:
        print(json.dumps(source_status, ensure_ascii=False, sort_keys=True), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
