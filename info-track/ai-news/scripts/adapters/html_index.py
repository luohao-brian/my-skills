"""HTML index adapters.

These parsers intentionally return conservative candidates from visible links
and metadata. Source-specific pages can be refined here without changing the
agent-facing skill contract.
"""

from __future__ import annotations

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


def fetch_generic_html(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    url = str(source["url"])
    html = fetch_text(url)
    description = _page_description(html)
    times = _visible_times(html)
    items: list[dict[str, str]] = []

    for index, (href, body) in enumerate(LINK_RE.findall(html)):
        title = strip_html(body)
        if len(title) < 8:
            continue
        items.append(
            {
                "title": title,
                "source_url": absolutize_url(url, href),
                "published_at": times[min(index, len(times) - 1)] if times else "",
                "summary_basis": description or title,
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


def fetch_anthropic(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    return fetch_generic_html(source, window)


def fetch_tmtpost(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    return fetch_generic_html(source, window)


def fetch_maomu(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    return fetch_generic_html(source, window)


def fetch_xiaohu(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    if window and window.get("date"):
        dated = dict(source)
        dated["url"] = str(source.get("date_url", source["url"])).replace("{YYYY-MM-DD}", str(window["date"]))
        return fetch_generic_html(dated, window)
    return fetch_generic_html(source, window)


def fetch_hex2077(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    if window and window.get("date"):
        date = str(window["date"])
        dated = dict(source)
        dated["url"] = (
            str(source.get("date_url", source["url"]))
            .replace("{YYYY-MM-DD}", date)
            .replace("{YYYY-MM}", date[:7])
        )
        return fetch_generic_html(dated, window)
    return fetch_generic_html(source, window)
