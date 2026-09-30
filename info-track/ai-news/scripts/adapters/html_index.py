"""HTML index adapters.

These parsers intentionally return conservative candidates from visible links
and metadata. Source-specific pages can be refined here without changing the
agent-facing skill contract.
"""

from __future__ import annotations

import sys
from datetime import timedelta
from typing import Any
import re

from .common import absolutize_url, fetch_text, first_text, strip_html


LINK_RE = re.compile(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL)
ANCHOR_TIME_RE = re.compile(r"<time\b[^>]*>(.*?)</time>", re.IGNORECASE | re.DOTALL)
TITLE_SPAN_RE = re.compile(
    r"<span\b[^>]*class=[\"'][^\"']*title[^\"']*[\"'][^>]*>(.*?)</span>", re.IGNORECASE | re.DOTALL
)
STALE_LINK_THRESHOLD = 5
META_DESC_RE = re.compile(
    r"<meta\b[^>]*(?:name|property)=[\"'](?:description|og:description)[\"'][^>]*content=[\"']([^\"']+)[\"']",
    re.IGNORECASE,
)
TITLE_RE = re.compile(r"<title\b[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
TMTPOST_PUBLISHED_RE = re.compile(
    r"\b(\d{4})\.(\d{2})\.(\d{2})\s+(\d{1,2}):(\d{2})\b"
)


def _page_description(html: str) -> str:
    match = META_DESC_RE.search(html)
    if match:
        return strip_html(match.group(1))
    match = TITLE_RE.search(html)
    if match:
        return strip_html(match.group(1))
    return ""


def fetch_generic_html(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    url = str(source["url"])
    html = fetch_text(url)
    description = _page_description(html)
    items: list[dict[str, str]] = []

    for href, body in LINK_RE.findall(html):
        title = strip_html(body)
        if len(title) < 8:
            continue
        items.append(
            {
                "title": title,
                "source_url": absolutize_url(url, href),
                "published_at": "",
                "summary_basis": title,
            }
        )
        if len(items) >= 40:
            break

    if not items and description:
        items.append(
            {
                "title": description[:120],
                "source_url": url,
                "published_at": "",
                "summary_basis": description,
            }
        )

    return items


def fetch_dated_anchors(
    source: dict[str, Any],
    window: dict[str, Any] | None = None,
    *,
    href_prefix: str,
    date_patterns: tuple[str, ...] = (),
    source_id: str = "",
) -> list[dict[str, str]]:
    """Parse list-page items anchored on links that carry their own date.

    Each item is one <a href="prefix..."> block whose body contains a date
    (a <time> element first, then text matching date_patterns) and a title
    (a span whose class mentions "title" first, then the cleaned anchor text
    with the date removed). Items without a parseable date or a usable title
    are skipped, so a page redesign degrades to zero items instead of garbage
    rows that would short-circuit fallback parsing. When the page still has
    links under the prefix but nothing parses, a stderr warning flags the
    probable markup drift.
    """
    url = str(source["url"])
    html = fetch_text(url)
    date_res = [re.compile(pattern) for pattern in date_patterns]
    items: list[dict[str, str]] = []
    seen: set[str] = set()

    for href, body in LINK_RE.findall(html):
        if not href.startswith(href_prefix):
            continue
        full_url = absolutize_url(url, href)
        if full_url in seen:
            continue
        time_match = ANCHOR_TIME_RE.search(body)
        date_text = strip_html(time_match.group(1)) if time_match else ""
        body_text = strip_html(body)
        if not date_text:
            for date_re in date_res:
                match = date_re.search(body_text)
                if match:
                    date_text = match.group(0)
                    break
        title_match = TITLE_SPAN_RE.search(body)
        if title_match:
            title = strip_html(title_match.group(1))
        elif date_text:
            title = body_text.replace(date_text, "", 1).strip()
        else:
            title = ""
        title = re.sub(r"\s+", " ", title).strip(" ·|-")
        if not date_text or len(title) < 4:
            continue
        seen.add(full_url)
        items.append(
            {
                "title": title,
                "source_url": full_url,
                "published_at": date_text,
                "summary_basis": title,
            }
        )

    if not items and html.count(f'href="{href_prefix}') >= STALE_LINK_THRESHOLD:
        print(
            f"[ai-news] {source_id or url}: page has links under {href_prefix} "
            "but 0 parsed; markup may have changed",
            file=sys.stderr,
        )
    return items


def fetch_anthropic(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    items = fetch_dated_anchors(
        source,
        window,
        href_prefix="/news/",
        date_patterns=(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+20\d{2}",),
        source_id=str(source.get("id", "")),
    )
    return items


def fetch_tmtpost(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    items = fetch_generic_html(source, window)
    daily_items: list[tuple[dict[str, str], str]] = []
    for date in _dates_from_window(window):
        month = int(date[5:7])
        day = int(date[8:10])
        target = f"{month}月{day}日"
        daily = next(
            (
                item
                for item in items
                if "Edge AI Daily" in item["title"]
                and item["source_url"].endswith(".html")
                and target in item["title"]
            ),
            None,
        )
        if daily:
            daily_items.append((daily, date))

    parsed_items: list[dict[str, str]] = []
    for daily, date in daily_items:
        try:
            html = fetch_text(daily["source_url"])
        except Exception:
            continue
        published_at = _tmtpost_published_at(html, date)
        parsed_items.extend(_parse_tmtpost_daily(html, daily["source_url"], published_at))
    return parsed_items


def fetch_maomu(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    """Parse the maomu news timeline.

    The page groups items under date headers ("今日 - 2026-09-27" or plain
    "2026-09-26") and stamps each item with a Beijing-time HH:MM clock. Older
    sidebar entries ("N天前") carry no news-time marker and are not matched.
    Composing header date plus item clock yields exact per-item timestamps
    instead of labeling everything with the collection day.
    """
    url = str(source["url"])
    html = fetch_text(url)
    group_re = re.compile(
        r'<div\b[^>]*class=["\'][^"\']*news-tag[^"\']*["\'][^>]*>\s*<span[^>]*>([^<]+)</span>',
        re.IGNORECASE,
    )
    item_re = re.compile(
        r'class=["\']news-time["\'][^>]*>\s*<span[^>]*>(\d{1,2}:\d{2})</span>'
        r'\s*</div>'
        r'\s*<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    h3_re = re.compile(r"<h3\b[^>]*>(.*?)</h3>", re.IGNORECASE | re.DOTALL)
    desc_re = re.compile(r'<div\b[^>]*class=["\'][^"\']*desc[^"\']*["\'][^>]*>(.*?)</div>', re.IGNORECASE | re.DOTALL)
    source_re = re.compile(
        r'<div\b[^>]*class=["\'][^"\']*source-name[^"\']*["\'][^>]*>(.*?)</div>', re.IGNORECASE | re.DOTALL
    )
    iso_date_re = re.compile(r"20\d{2}-\d{2}-\d{2}")

    items: list[dict[str, str]] = []
    groups = list(group_re.finditer(html))
    for index, group in enumerate(groups):
        date_match = iso_date_re.search(group.group(1))
        if not date_match:
            continue
        day = date_match.group(0)
        segment_end = groups[index + 1].start() if index + 1 < len(groups) else len(html)
        segment = html[group.end():segment_end]
        for clock, href, body in item_re.findall(segment):
            title_match = h3_re.search(body)
            title = strip_html(title_match.group(1)) if title_match else ""
            if len(title) < 4:
                continue
            desc_match = desc_re.search(body)
            source_match = source_re.search(body)
            summary = strip_html(desc_match.group(1)) if desc_match else title
            source_name = strip_html(source_match.group(1)) if source_match else ""
            if source_name:
                summary = f"{summary} {source_name}" if summary else source_name
            hour, minute = clock.split(":")
            items.append(
                {
                    "title": title,
                    "source_url": absolutize_url(url, href),
                    "published_at": f"{day}T{int(hour):02d}:{minute}:00+08:00",
                    "summary_basis": summary,
                }
            )
    return items


def fetch_hex2077(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    dates = _dates_from_window(window)
    items: list[dict[str, str]] = []
    for date in dates:
        url = (
            str(source.get("date_url", source["url"]))
            .replace("{YYYY-MM-DD}", date)
            .replace("{YYYY-MM}", date[:7])
        )
        try:
            html = fetch_text(url)
        except Exception:
            continue
        items.extend(_parse_hex2077_article(html, url, date))
    return items


def _date_from_window(window: dict[str, Any] | None) -> str:
    if not window:
        return ""
    if window.get("date"):
        return str(window["date"])
    end = window.get("end")
    if hasattr(end, "date"):
        return end.date().isoformat()
    return ""


def _dates_from_window(window: dict[str, Any] | None) -> list[str]:
    if not window:
        return []
    if window.get("date"):
        return [str(window["date"])]
    start = window.get("start")
    end = window.get("end")
    if not hasattr(start, "date") or not hasattr(end, "date"):
        date = _date_from_window(window)
        return [date] if date else []
    current = end.date()
    first = start.date()
    dates: list[str] = []
    while current >= first:
        dates.append(current.isoformat())
        current = current - timedelta(days=1)
    return dates


def _parse_tmtpost_daily(html: str, url: str, published_at: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    block_re = re.compile(r"<blockquote\b.*?</blockquote>", re.IGNORECASE | re.DOTALL)
    paragraph_re = re.compile(r"<p\b[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)
    blocks = list(block_re.finditer(html))

    for index, block in enumerate(blocks):
        title = strip_html(block.group(0))
        title = re.sub(r"^[一二三四五六七八九十]+、\s*", "", title)
        if not title:
            continue
        href_match = LINK_RE.search(block.group(0))
        source_url = absolutize_url(url, href_match.group(1)) if href_match else url
        start = block.end()
        end = blocks[index + 1].start() if index + 1 < len(blocks) else len(html)
        segment = html[start:end]
        paragraphs = [strip_html(value) for value in paragraph_re.findall(segment)]
        paragraphs = [value for value in paragraphs if value]
        summary = " ".join(paragraphs[:3]).strip() or title
        items.append(
            {
                "title": title,
                "source_url": source_url,
                "published_at": published_at,
                "summary_basis": summary,
            }
        )

    return items


def _tmtpost_published_at(html: str, expected_date: str) -> str:
    for year, month, day, hour, minute in TMTPOST_PUBLISHED_RE.findall(html):
        date = f"{year}-{month}-{day}"
        if date == expected_date:
            return f"{date}T{int(hour):02d}:{minute}:00+08:00"
    return expected_date


def _parse_hex2077_article(html: str, url: str, published_at: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    li_re = re.compile(r"<li\b[^>]*>(.*?)</li>", re.IGNORECASE | re.DOTALL)
    strong_re = re.compile(r"<strong\b[^>]*>(.*?)</strong>", re.IGNORECASE | re.DOTALL)
    href_re = re.compile(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL)

    for body in li_re.findall(html):
        strong_match = strong_re.search(body)
        href_match = href_re.search(body)
        if not strong_match or not href_match:
            continue
        title = strip_html(strong_match.group(1))
        summary = strip_html(strong_re.sub("", body, count=1))
        summary = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff，。；：！？])", "", summary)
        summary = summary.strip(" 。")
        source_url = absolutize_url(url, href_match.group(1))
        if not title or not summary or "/docs/" in source_url:
            continue
        items.append(
            {
                "title": title,
                "source_url": source_url,
                "published_at": published_at,
                "summary_basis": summary,
            }
        )

    return items
