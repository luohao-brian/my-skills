"""RSS and Atom adapter."""

from __future__ import annotations

from typing import Any
from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as ET

from .common import fetch_text, first_text


ATOM = "{http://www.w3.org/2005/Atom}"
CONTENT = "{http://purl.org/rss/1.0/modules/content/}"


def _text(node: ET.Element, path: str) -> str:
    found = node.find(path)
    if found is None or found.text is None:
        return ""
    return found.text.strip()


def _atom_link(entry: ET.Element) -> str:
    for link in entry.findall(f"{ATOM}link"):
        href = link.attrib.get("href", "")
        rel = link.attrib.get("rel", "alternate")
        if href and rel == "alternate":
            return href
    return ""


def _parse_datetime(value: str) -> datetime | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        pass
    text = text.replace(" GMT", " +0000").replace(" UTC", " +0000")
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M %z", "%d %b %Y %H:%M:%S %z"):
        try:
            parsed = datetime.strptime(text, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            pass
    return None


def _in_window(published_at: str, window: dict[str, Any] | None) -> bool:
    if not window or "start" not in window or "end" not in window:
        return True
    parsed = _parse_datetime(published_at)
    if parsed is None:
        return True
    start = window["start"]
    end = window["end"]
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone(timedelta(hours=8)))
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone(timedelta(hours=8)))
    return start.astimezone(timezone.utc) <= parsed.astimezone(timezone.utc) <= end.astimezone(timezone.utc)


def fetch_rss(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    payload = fetch_text(str(source["url"]))
    root = ET.fromstring(payload)
    items: list[dict[str, str]] = []

    for entry in root.findall("./channel/item"):
        published_at = first_text(_text(entry, "pubDate"), _text(entry, "published"), _text(entry, "updated"))
        if not _in_window(published_at, window):
            continue
        items.append(
            {
                "title": _text(entry, "title"),
                "source_url": _text(entry, "link"),
                "published_at": published_at,
                "summary_basis": first_text(
                    _text(entry, "description"),
                    _text(entry, f"{CONTENT}encoded"),
                    _text(entry, "summary"),
                    _text(entry, "title"),
                ),
            }
        )

    for entry in root.findall(f"{ATOM}entry"):
        published_at = first_text(_text(entry, f"{ATOM}updated"), _text(entry, f"{ATOM}published"))
        if not _in_window(published_at, window):
            continue
        items.append(
            {
                "title": _text(entry, f"{ATOM}title"),
                "source_url": _atom_link(entry),
                "published_at": published_at,
                "summary_basis": first_text(
                    _text(entry, f"{ATOM}summary"),
                    _text(entry, f"{ATOM}content"),
                    _text(entry, f"{ATOM}title"),
                ),
            }
        )

    return items
