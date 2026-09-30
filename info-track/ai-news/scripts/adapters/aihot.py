"""AIHOT public v1 selected items as an attributed aggregator source."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode, urlsplit

from .common import fetch_text


def fetch_aihot(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    if window is None:
        raise ValueError("AIHOT requires a bounded collection window")
    start = window["start"]
    end = window["end"]
    if start < datetime.now(start.tzinfo) - timedelta(days=7):
        raise ValueError("AIHOT /api/v1/items only covers the last 7 days")

    base = str(source["url"])
    parsed = urlsplit(base)
    if parsed.scheme != "https" or parsed.netloc != "aihot.news" or parsed.path != "/api/v1/items":
        raise ValueError("AIHOT source must use https://aihot.news/api/v1/items")

    rows: list[dict[str, str]] = []
    cursor: str | None = None
    seen_cursors: set[str] = set()
    for _ in range(20):
        query = {"mode": "selected", "window": "7d", "by": "published", "limit": "100"}
        if cursor:
            query["cursor"] = cursor
        payload = json.loads(fetch_text(base + "?" + urlencode(query)))
        if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
            raise ValueError("AIHOT items response has no items[]")

        older_reached = False
        for item in payload["items"]:
            if not isinstance(item, dict):
                continue
            published_text = str(item.get("publishedAt") or "")
            try:
                published = datetime.fromisoformat(published_text.replace("Z", "+00:00"))
            except ValueError:
                continue
            if published.tzinfo is None:
                continue
            if published < start:
                older_reached = True
                continue
            if published > end:
                continue
            links = item.get("links")
            links = links if isinstance(links, dict) else {}
            aihot_url = str(links.get("aihot") or "")
            original_url = str(links.get("original") or "")
            if not aihot_url.startswith("https://aihot.news/items/"):
                continue
            original_parts = urlsplit(original_url)
            if original_parts.scheme not in {"http", "https"} or not original_parts.netloc:
                original_url = ""
            source_info = item.get("source")
            source_info = source_info if isinstance(source_info, dict) else {}
            rows.append({
                "title": str(item.get("title") or ""),
                "source_url": aihot_url,
                "published_at": published_text,
                "summary_basis": str(item.get("summary") or ""),
                "original_url": original_url,
                "original_source": str(source_info.get("name") or ""),
                "discovered_at": str(item.get("discoveredAt") or ""),
                "external_id": str(item.get("id") or ""),
            })

        if older_reached or not payload.get("page", {}).get("hasMore"):
            return rows
        cursor = payload.get("page", {}).get("nextCursor")
        if not isinstance(cursor, str) or not cursor or cursor in seen_cursors:
            raise ValueError("AIHOT pagination cursor is missing or repeated")
        seen_cursors.add(cursor)
    raise ValueError("AIHOT pagination exceeded 20 pages before the window ended")
