"""RSS and Atom adapter."""

from __future__ import annotations

from typing import Any
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


def fetch_rss(source: dict[str, Any], window: dict[str, Any] | None = None) -> list[dict[str, str]]:
    payload = fetch_text(str(source["url"]))
    root = ET.fromstring(payload)
    items: list[dict[str, str]] = []

    for entry in root.findall("./channel/item"):
        items.append(
            {
                "title": _text(entry, "title"),
                "source_url": _text(entry, "link"),
                "published_at": first_text(_text(entry, "pubDate"), _text(entry, "published"), _text(entry, "updated")),
                "summary_basis": first_text(_text(entry, "description"), _text(entry, f"{CONTENT}encoded"), _text(entry, "summary")),
            }
        )

    for entry in root.findall(f"{ATOM}entry"):
        items.append(
            {
                "title": _text(entry, f"{ATOM}title"),
                "source_url": _atom_link(entry),
                "published_at": first_text(_text(entry, f"{ATOM}updated"), _text(entry, f"{ATOM}published")),
                "summary_basis": first_text(_text(entry, f"{ATOM}summary"), _text(entry, f"{ATOM}content")),
            }
        )

    return items
