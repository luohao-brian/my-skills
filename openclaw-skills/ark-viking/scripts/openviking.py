#!/usr/bin/env python3
"""Read-only OpenViking CLI for agent retrieval."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Iterable
from urllib.parse import quote, unquote

import requests


DEFAULT_URL = "https://api.vikingdb.cn-beijing.volces.com/openviking"
DEFAULT_TARGET = "viking://resources/codex-rspress-admin/public/"
DEFAULT_RSPRESS_PUBLIC_BASE_URL = "http://8.140.22.158"
RSPRESS_ARTICLES_PREFIX = "viking://resources/codex-rspress-admin/public/articles/"


class Client:
    def __init__(self, base_url: str, api_key: str) -> None:
        if not api_key:
            raise RuntimeError("ARK_AGENT_PLAN_OPENVIKING_API_KEY is required")
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        })

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        timeout = kwargs.pop("timeout", 120)
        response = self.session.request(method, self.base_url + path, timeout=timeout, **kwargs)
        if response.status_code >= 400:
            raise RuntimeError(f"{method} {path} failed ({response.status_code}): {response.text[:1000]}")
        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError as exc:
            raise RuntimeError(f"{method} {path} returned non-JSON data") from exc

    def health(self) -> Any:
        return self.request("GET", "/health", timeout=30)

    def status(self) -> Any:
        return self.request("GET", "/api/v1/system/status", timeout=30)

    def ls(self, uri: str) -> Any:
        return self.request("GET", "/api/v1/fs/ls", params={"uri": uri})

    def stat(self, uri: str) -> Any:
        return self.request("GET", "/api/v1/fs/stat", params={"uri": uri})

    def read(self, uri: str) -> Any:
        return self.request("GET", "/api/v1/content/read", params={"uri": uri})

    def find(self, query: str, target_uri: str, limit: int) -> Any:
        return self.request(
            "POST",
            "/api/v1/search/find",
            json={"query": query, "target_uri": target_uri, "limit": limit},
        )


def iter_hits(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if isinstance(value.get("uri"), str):
            yield value
        for child in value.values():
            yield from iter_hits(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_hits(child)


def content_text(payload: Any) -> str:
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        for key in ("content", "text", "result"):
            value = payload.get(key)
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                nested = content_text(value)
                if nested:
                    return nested
    return json.dumps(payload, ensure_ascii=False)


def rspress_metadata(uri: str, public_base_url: str) -> dict[str, str | None]:
    if not uri.startswith(RSPRESS_ARTICLES_PREFIX):
        return {"source_path": None, "public_url": None}
    relative_uri = uri[len(RSPRESS_ARTICLES_PREFIX):]
    first_part = relative_uri.split("/", 1)[0].lower()
    if first_part in {".abstract.md", ".overview.md"}:
        return {"source_path": None, "public_url": None}
    source_parts: list[str] = []
    for encoded_part in relative_uri.split("/"):
        part = unquote(encoded_part)
        source_parts.append(part)
        if part.lower().endswith((".md", ".mdx")):
            suffix_length = 4 if part.lower().endswith(".mdx") else 3
            source_parts[-1] = part[:-suffix_length]
            public_path = "/auto/" + "/".join(quote(item, safe="-._~") for item in source_parts) + ".html"
            source_parts[-1] = part
            return {
                "source_path": "/".join(source_parts),
                "public_url": public_base_url.rstrip("/") + public_path,
            }
    return {"source_path": None, "public_url": None}


def source_resource_uri(uri: str) -> str | None:
    if not uri.startswith(RSPRESS_ARTICLES_PREFIX):
        return None
    relative_uri = uri[len(RSPRESS_ARTICLES_PREFIX):]
    first_part = relative_uri.split("/", 1)[0].lower()
    if first_part in {".abstract.md", ".overview.md"}:
        return None
    encoded_parts: list[str] = []
    for encoded_part in relative_uri.split("/"):
        encoded_parts.append(encoded_part)
        if unquote(encoded_part).lower().endswith((".md", ".mdx")):
            return RSPRESS_ARTICLES_PREFIX + "/".join(encoded_parts)
    return None


def enrich_rspress_metadata(value: Any, public_base_url: str) -> Any:
    if isinstance(value, dict):
        enriched = {key: enrich_rspress_metadata(child, public_base_url) for key, child in value.items()}
        if isinstance(enriched.get("uri"), str):
            enriched.update(rspress_metadata(enriched["uri"], public_base_url))
        return enriched
    if isinstance(value, list):
        return [enrich_rspress_metadata(child, public_base_url) for child in value]
    return value


def section_title_from_text(text: str) -> str | None:
    body = text
    if body.startswith("---\n"):
        frontmatter_end = body.find("\n---\n", 4)
        if frontmatter_end >= 0:
            frontmatter = body[4:frontmatter_end]
            title_match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', frontmatter, re.MULTILINE)
            if title_match:
                return title_match.group(1).strip()
            body = body[frontmatter_end + 5:]
    heading = re.search(r"^#{1,6}\s+(.+?)\s*$", body, re.MULTILINE)
    if heading:
        return heading.group(1).strip()
    return None


def fallback_article_title(source_path: str | None) -> str | None:
    if source_path:
        stem = re.sub(r"\.(?:md|mdx)$", "", source_path.rsplit("/", 1)[-1], flags=re.IGNORECASE)
        return re.sub(r"[-_]+", " ", stem).strip() or None
    return None


def display_name_from_uri(uri: str) -> str | None:
    name = unquote(uri.rstrip("/").rsplit("/", 1)[-1])
    name = re.sub(r"\.(?:md|mdx)$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"_+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name or None


def article_title(client: Client, root_uri: str, source_path: str | None) -> str | None:
    root = root_uri.rstrip("/")
    try:
        entries = list(iter_hits(client.ls(root + "/")))
    except RuntimeError:
        entries = []
    for entry in entries:
        entry_uri = entry.get("uri")
        if not entry.get("isDir") or not isinstance(entry_uri, str):
            continue
        if entry_uri.rstrip("/").rsplit("/", 1)[0] != root:
            continue
        title = display_name_from_uri(entry_uri)
        if title:
            return title
    return fallback_article_title(source_path)


def is_generated_summary_uri(uri: str) -> bool:
    return uri.rstrip("/").rsplit("/", 1)[-1].lower() in {".abstract.md", ".overview.md"}


def is_section_uri(uri: str) -> bool:
    if is_generated_summary_uri(uri):
        return False
    root_uri = source_resource_uri(uri)
    if not root_uri or uri.rstrip("/") == root_uri.rstrip("/"):
        return False
    name = unquote(uri.rstrip("/").rsplit("/", 1)[-1]).lower()
    return name.endswith((".md", ".mdx"))


def relevance_value(hit: dict[str, Any]) -> float:
    score = hit.get("score")
    return float(score) if isinstance(score, (int, float)) else float("-inf")


def collect_article_candidates(found: Any, public_base_url: str) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for hit in iter_hits(found):
        uri = hit.get("uri")
        if not isinstance(uri, str):
            continue
        source = rspress_metadata(uri, public_base_url)
        source_path = source["source_path"]
        root_uri = source_resource_uri(uri)
        if not source_path or not source["public_url"] or not root_uri:
            continue
        candidate = grouped.setdefault(source_path, {
            "source_path": source_path,
            "root_uri": root_uri,
            "article_url": source["public_url"],
            "relevance": hit.get("score"),
            "hits": [],
        })
        candidate["hits"].append(hit)
        if relevance_value(hit) > relevance_value({"score": candidate["relevance"]}):
            candidate["relevance"] = hit.get("score")
    return sorted(grouped.values(), key=lambda item: relevance_value({"score": item["relevance"]}), reverse=True)


def relevant_sections(
    client: Client,
    query: str,
    candidate: dict[str, Any],
    sections_per_article: int,
    max_chars: int,
) -> list[dict[str, Any]]:
    search_limit = max(sections_per_article * 4, 8)
    hits = list(candidate["hits"])
    try:
        scoped = client.find(query, candidate["root_uri"].rstrip("/") + "/", search_limit)
        hits.extend(iter_hits(scoped))
    except RuntimeError:
        pass

    unique_hits: dict[str, dict[str, Any]] = {}
    for hit in hits:
        uri = hit.get("uri")
        if not isinstance(uri, str) or not is_section_uri(uri):
            continue
        if rspress_metadata(uri, "")["source_path"] != candidate["source_path"]:
            continue
        previous = unique_hits.get(uri)
        if previous is None or relevance_value(hit) > relevance_value(previous):
            unique_hits[uri] = hit

    sections: list[dict[str, Any]] = []
    ordered_hits = sorted(unique_hits.values(), key=relevance_value, reverse=True)
    for hit in ordered_hits:
        if len(sections) >= sections_per_article:
            break
        uri = hit["uri"]
        try:
            text = content_text(client.read(uri)).strip()
        except RuntimeError:
            continue
        if not text:
            continue
        sections.append({
            "relevance": hit.get("score"),
            "section_title": section_title_from_text(text) or display_name_from_uri(uri),
            "content": text[:max_chars],
        })
    return sections


def retrieve_articles(
    client: Client,
    query: str,
    target_uri: str,
    article_limit: int,
    sections_per_article: int,
    max_chars: int,
    public_base_url: str,
) -> dict[str, Any]:
    candidate_limit = max(article_limit * 8, 20)
    found = client.find(query, target_uri, candidate_limit)
    candidates = collect_article_candidates(found, public_base_url)
    articles = []
    for candidate in candidates:
        if len(articles) >= article_limit:
            break
        sections = relevant_sections(client, query, candidate, sections_per_article, max_chars)
        if not sections:
            continue
        articles.append({
            "relevance": candidate["relevance"],
            "article_title": article_title(client, candidate["root_uri"], candidate["source_path"]),
            "article_url": candidate["article_url"],
            "sections": sections,
        })
    return {
        "schema": "openviking.article-retrieval/v1",
        "query": query,
        "articles": articles,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Read and retrieve OpenViking knowledge")
    root.add_argument("--base-url", default=os.environ.get("ARK_AGENT_PLAN_OPENVIKING_BASE_URL", DEFAULT_URL))
    root.add_argument(
        "--public-base-url",
        default=os.environ.get("ARK_VIKING_RSPRESS_PUBLIC_BASE_URL", DEFAULT_RSPRESS_PUBLIC_BASE_URL),
    )
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor")
    for name in ("ls", "stat", "read"):
        command = commands.add_parser(name)
        command.add_argument("uri")
    find_command = commands.add_parser("find")
    find_command.add_argument("query")
    find_command.add_argument("--target-uri", default=DEFAULT_TARGET)
    find_command.add_argument("--limit", type=int, default=5, help="maximum raw search hits")
    retrieve_command = commands.add_parser("retrieve")
    retrieve_command.add_argument("query")
    retrieve_command.add_argument("--target-uri", default=DEFAULT_TARGET)
    retrieve_command.add_argument("--limit", type=int, default=5, help="maximum distinct articles")
    retrieve_command.add_argument("--sections-per-article", type=int, default=3)
    retrieve_command.add_argument("--max-chars", type=int, default=6000, help="maximum characters per section")
    return root


def main() -> int:
    args = parser().parse_args()
    client = Client(args.base_url, os.environ.get("ARK_AGENT_PLAN_OPENVIKING_API_KEY", ""))
    if args.command == "doctor":
        output = {"health": client.health(), "status": client.status()}
    elif args.command == "ls":
        output = enrich_rspress_metadata(client.ls(args.uri), args.public_base_url)
    elif args.command == "stat":
        output = enrich_rspress_metadata(client.stat(args.uri), args.public_base_url)
    elif args.command == "read":
        output = client.read(args.uri)
    elif args.command == "find":
        output = enrich_rspress_metadata(client.find(args.query, args.target_uri, args.limit), args.public_base_url)
    else:
        if args.limit < 1 or args.sections_per_article < 1 or args.max_chars < 1:
            raise RuntimeError("retrieve limits must be positive integers")
        output = retrieve_articles(
            client,
            args.query,
            args.target_uri,
            args.limit,
            args.sections_per_article,
            args.max_chars,
            args.public_base_url,
        )
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (requests.RequestException, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
