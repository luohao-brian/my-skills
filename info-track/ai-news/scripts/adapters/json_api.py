"""JSON API adapters."""

from __future__ import annotations

from typing import Any
import json

from .common import fetch_text, first_text


def fetch_tensorfeed_json(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    payload = json.loads(fetch_text(str(source["url"])))
    articles = payload.get("articles", payload if isinstance(payload, list) else [])
    items: list[dict[str, str]] = []
    if not isinstance(articles, list):
        return items

    for article in articles:
        if not isinstance(article, dict):
            continue
        items.append(
            {
                "title": first_text(article.get("title")),
                "source_url": first_text(article.get("url"), article.get("link")),
                "published_at": first_text(article.get("publishedAt"), article.get("published_at"), article.get("date")),
                "summary_basis": first_text(article.get("snippet"), article.get("summary"), article.get("description")),
            }
        )

    return items
