"""Shared adapter helpers."""

from __future__ import annotations

import html
import re
from typing import Any
from urllib.request import Request, urlopen


USER_AGENT = "Mozilla/5.0 ai-news-skill/1.0"


def fetch_text(url: str, timeout: int = 30) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def strip_html(value: str | None) -> str:
    text = re.sub(r"<script\b.*?</script>", " ", value or "", flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def first_text(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = strip_html(str(value))
        if text:
            return text
    return ""


def absolutize_url(base_url: str, url: str) -> str:
    if not url:
        return ""
    if url.startswith(("http://", "https://")):
        return url
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        match = re.match(r"^(https?://[^/]+)", base_url)
        return (match.group(1) if match else base_url.rstrip("/")) + url
    return base_url.rstrip("/") + "/" + url
