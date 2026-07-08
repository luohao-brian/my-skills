"""HTML index adapters.

These parsers intentionally return conservative candidates from visible links
and metadata. Source-specific pages can be refined here without changing the
agent-facing skill contract.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any
import re

from .common import absolutize_url, fetch_text, first_text, strip_html


LINK_RE = re.compile(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL)
TIME_RE = re.compile(r"<time\b[^>]*(?:datetime=[\"']([^\"']+)[\"'])?[^>]*>(.*?)</time>", re.IGNORECASE | re.DOTALL)
META_DESC_RE = re.compile(
    r"<meta\b[^>]*(?:name|property)=[\"'](?:description|og:description)[\"'][^>]*content=[\"']([^\"']+)[\"']",
    re.IGNORECASE,
)
TITLE_RE = re.compile(r"<title\b[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def _page_description(html: str) -> str:
    match = META_DESC_RE.search(html)
    if match:
        return strip_html(match.group(1))
    match = TITLE_RE.search(html)
    if match:
        return strip_html(match.group(1))
    return ""


def _visible_times(html: str) -> list[str]:
    values: list[str] = []
    for datetime_value, text_value in TIME_RE.findall(html):
        value = first_text(datetime_value, text_value)
        if value:
            values.append(value)
    return values


def _fallback_published_at(window: dict[str, Any] | None) -> str:
    if not window:
        return ""
    if window.get("date"):
        return str(window["date"])
    end = window.get("end")
    if hasattr(end, "isoformat"):
        return end.isoformat(timespec="seconds")
    return ""


def fetch_generic_html(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    url = str(source["url"])
    html = fetch_text(url)
    description = _page_description(html)
    times = _visible_times(html)
    fallback_date = _fallback_published_at(window)
    items: list[dict[str, str]] = []

    for index, (href, body) in enumerate(LINK_RE.findall(html)):
        title = strip_html(body)
        if len(title) < 8:
            continue
        items.append(
            {
                "title": title,
                "source_url": absolutize_url(url, href),
                "published_at": times[min(index, len(times) - 1)] if times else fallback_date,
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
                "published_at": fallback_date,
                "summary_basis": description,
            }
        )

    return items


def fetch_anthropic(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    url = str(source["url"])
    html = fetch_text(url)
    items: list[dict[str, str]] = []
    article_re = re.compile(r"<article\b.*?</article>", re.IGNORECASE | re.DOTALL)
    href_re = re.compile(r"<a\b[^>]*href=[\"']([^\"']+)[\"']", re.IGNORECASE)
    title_re = re.compile(r"<h[1-4]\b[^>]*>(.*?)</h[1-4]>", re.IGNORECASE | re.DOTALL)
    date_re = re.compile(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}", re.IGNORECASE)
    body_re = re.compile(r"<p\b[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)

    for article in article_re.findall(html):
        href_match = href_re.search(article)
        title_match = title_re.search(article)
        date_match = date_re.search(article)
        if not href_match or not title_match or not date_match:
            continue
        summary_match = body_re.search(article)
        title = strip_html(title_match.group(1))
        if not title:
            continue
        items.append(
            {
                "title": title,
                "source_url": absolutize_url(url, href_match.group(1)),
                "published_at": date_match.group(0),
                "summary_basis": strip_html(summary_match.group(1)) if summary_match else title,
            }
        )

    return items or fetch_generic_html(source, window)


def fetch_tmtpost(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    items = fetch_generic_html(source, window)
    date = _date_from_window(window)
    target = ""
    if date:
        month = int(date[5:7])
        day = int(date[8:10])
        target = f"{month}月{day}日"

    daily_items = [
        item
        for item in items
        if "Edge AI Daily" in item["title"]
        and item["source_url"].endswith(".html")
        and (not target or target in item["title"])
    ]
    if not daily_items:
        return items

    daily = daily_items[0]
    try:
        html = fetch_text(daily["source_url"])
    except Exception:
        return daily_items
    parsed = _parse_tmtpost_daily(html, daily["source_url"], daily.get("published_at") or date)
    return parsed or daily_items


def fetch_maomu(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    return fetch_generic_html(source, window)


def fetch_xiaohu(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    dates = _dates_from_window(window)
    all_items: list[dict[str, str]] = []
    for date in dates:
        dated_url = str(source.get("date_url", source["url"])).replace("{YYYY-MM-DD}", date)
        try:
            html = fetch_text(dated_url)
        except Exception:
            continue
        if "<title>404" in html[:500]:
            continue
        items = _parse_xiaohu_daily(html, dated_url, date)
        if items:
            all_items.extend(items)
        else:
            dated = dict(source)
            dated["url"] = dated_url
            dated_window = dict(window or {})
            dated_window["date"] = date
            try:
                all_items.extend(fetch_generic_html(dated, dated_window))
            except Exception:
                pass
    if all_items:
        return all_items

    base_url = str(source["url"])
    try:
        html = fetch_text(base_url)
    except Exception:
        return []
    date_link_re = re.compile(r'href="(\d{4}-\d{2}-\d{2})/?"')
    found_dates = date_link_re.findall(html)
    for date in found_dates[:3]:
        dated_url = str(source.get("date_url", source["url"])).replace("{YYYY-MM-DD}", date)
        try:
            daily_html = fetch_text(dated_url)
        except Exception:
            continue
        items = _parse_xiaohu_daily(daily_html, dated_url, date)
        if items:
            return items
    return fetch_generic_html(source, window)


def fetch_hex2077(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    url = str(source["url"])
    dates = _dates_from_window(window)
    if dates:
        items: list[dict[str, str]] = []
        date = dates[0]
        dated = dict(source)
        for candidate_date in dates:
            dated["url"] = (
                str(source.get("date_url", source["url"]))
                .replace("{YYYY-MM-DD}", candidate_date)
                .replace("{YYYY-MM}", candidate_date[:7])
            )
            url = str(dated["url"])
            try:
                html = fetch_text(url)
            except Exception:
                continue
            date = candidate_date
            items = _parse_hex2077_article(html, url, date)
            if not items:
                dated_window = dict(window or {})
                dated_window["date"] = date
                items = fetch_generic_html(dated, dated_window)
            if items:
                break
    else:
        html = fetch_text(url)
        items = _parse_hex2077_article(html, url, "")
        if not items:
            items = fetch_generic_html(source, window)
    filtered = [
        item
        for item in items
        if not item["source_url"].startswith("https://hex2077.dev/docs/")
        and item["source_url"] != "https://hex2077.dev/"
        and not item["title"].startswith(">>")
    ]
    if filtered:
        return filtered
    html = fetch_text(url)
    description = _page_description(html)
    if not description:
        return items[:1]
    published_at = date
    return [
        {
            "title": f"Hex 2077 AI资讯 {published_at}".strip(),
            "source_url": url,
            "published_at": published_at,
            "summary_basis": description,
        }
    ]


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
        start = block.end()
        end = blocks[index + 1].start() if index + 1 < len(blocks) else len(html)
        segment = html[start:end]
        paragraphs = [strip_html(value) for value in paragraph_re.findall(segment)]
        paragraphs = [value for value in paragraphs if value]
        summary = " ".join(paragraphs[:3]).strip() or title
        items.append(
            {
                "title": title,
                "source_url": url,
                "published_at": published_at,
                "summary_basis": summary,
            }
        )

    return items


def _parse_hex2077_article(html: str, url: str, published_at: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    li_re = re.compile(r"<li\b[^>]*>\s*<p\b[^>]*>(.*?)</p>\s*</li>", re.IGNORECASE | re.DOTALL)
    strong_re = re.compile(r"<strong\b[^>]*>(.*?)</strong>", re.IGNORECASE | re.DOTALL)
    href_re = re.compile(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL)

    for body in li_re.findall(html):
        strong_match = strong_re.search(body)
        href_match = href_re.search(body)
        if not strong_match or not href_match:
            continue
        title = strip_html(strong_match.group(1))
        summary = strip_html(strong_re.sub("", body, count=1))
        link_text = strip_html(href_match.group(2))
        summary = summary.replace(link_text, "").strip(" 。")
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


def _parse_xiaohu_daily(html: str, url: str, published_at: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    theme_item_re = re.compile(
        r'<div class="theme-item"><a\s+href="([^"]+)"[^>]*>(.*?)</a>\s*(?:<span class="score-pill[^"]*">(\d+)</span>)?</div>',
        re.DOTALL,
    )
    headline_re = re.compile(r'<div class="headline-title">(.*?)</div>', re.DOTALL)
    theme_desc_re = re.compile(r'<div class="theme-desc">(.*?)</div>', re.DOTALL)
    section_re = re.compile(r'<div class="section-title">(.*?)</div>', re.DOTALL)

    theme_descs = [strip_html(m) for m in theme_desc_re.findall(html)]
    sections = [strip_html(m) for m in section_re.findall(html)]
    headlines = [strip_html(m) for m in headline_re.findall(html)]

    for index, (href, body, _score) in enumerate(theme_item_re.findall(html)):
        title = strip_html(body)
        if len(title) < 8:
            continue
        section_idx = min(index // 5, max(len(sections) - 1, 0)) if sections else 0
        desc_idx = min(index // 10, max(len(theme_descs) - 1, 0)) if theme_descs else 0
        summary_parts = []
        if section_idx < len(sections):
            summary_parts.append(sections[section_idx])
        if desc_idx < len(theme_descs):
            summary_parts.append(theme_descs[desc_idx])
        summary = " | ".join(summary_parts) if summary_parts else title
        items.append(
            {
                "title": title,
                "source_url": absolutize_url(url, href),
                "published_at": published_at,
                "summary_basis": summary,
            }
        )

    return items
