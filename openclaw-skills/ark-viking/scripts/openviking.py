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


def title_from_text(text: str) -> str | None:
    body = text
    if body.startswith("---\n"):
        frontmatter_end = body.find("\n---\n", 4)
        if frontmatter_end >= 0:
            frontmatter = body[4:frontmatter_end]
            title_match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', frontmatter, re.MULTILINE)
            if title_match:
                return title_match.group(1).strip()
            body = body[frontmatter_end + 5:]
    heading = re.search(r"^#{1,2}\s+(.+?)\s*$", body, re.MULTILINE)
    if heading:
        return heading.group(1).strip()
    return None


def fallback_title(source_path: str | None) -> str | None:
    if source_path:
        stem = re.sub(r"\.(?:md|mdx)$", "", source_path.rsplit("/", 1)[-1], flags=re.IGNORECASE)
        return re.sub(r"[-_]+", " ", stem).strip() or None
    return None


def directory_entry_order(item: dict[str, Any]) -> tuple[int, str]:
    uri = str(item.get("uri", ""))
    name = unquote(uri.rsplit("/", 1)[-1])
    overview_section = 0 if re.match(r"^\d+\._", name) else 1
    return overview_section, uri


def context_title(client: Client, uri: str, text: str, source_path: str | None) -> str | None:
    direct_title = title_from_text(text)
    if direct_title:
        return direct_title
    root_uri = source_resource_uri(uri)
    if not root_uri:
        return fallback_title(source_path)

    pending = [root_uri]
    visited: set[str] = set()
    while pending and len(visited) < 12:
        directory_uri = pending.pop(0)
        if directory_uri in visited:
            continue
        visited.add(directory_uri)
        try:
            entries = sorted(
                iter_hits(client.ls(directory_uri.rstrip("/") + "/")),
                key=directory_entry_order,
            )
        except RuntimeError:
            continue
        for entry in entries:
            entry_uri = entry.get("uri")
            if not isinstance(entry_uri, str) or entry_uri == directory_uri:
                continue
            if entry.get("isDir"):
                pending.append(entry_uri)
                continue
            if entry_uri.rsplit("/", 1)[-1] in {".abstract.md", ".overview.md"}:
                continue
            try:
                candidate_title = title_from_text(content_text(client.read(entry_uri)))
            except RuntimeError:
                continue
            if candidate_title:
                return candidate_title
    return fallback_title(source_path)


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
    for name in ("find", "retrieve"):
        command = commands.add_parser(name)
        command.add_argument("query")
        command.add_argument("--target-uri", default=DEFAULT_TARGET)
        command.add_argument("--limit", type=int, default=5)
        if name == "retrieve":
            command.add_argument("--max-chars", type=int, default=12000)
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
        found = client.find(args.query, args.target_uri, args.limit)
        contexts = []
        seen: set[str] = set()
        for hit in iter_hits(found):
            uri = hit["uri"]
            if uri in seen or len(contexts) >= args.limit:
                continue
            seen.add(uri)
            try:
                text = content_text(client.read(uri))[: args.max_chars]
            except RuntimeError as exc:
                text = ""
                hit = {**hit, "read_error": str(exc)}
            source = rspress_metadata(uri, args.public_base_url)
            contexts.append({
                "uri": uri,
                **source,
                "title": context_title(client, uri, text, source["source_path"]),
                "score": hit.get("score"),
                "abstract": hit.get("abstract") or hit.get("summary"),
                "content": text,
                **({"read_error": hit["read_error"]} if "read_error" in hit else {}),
            })
        output = {
            "schema": "openviking.rag-context/v1",
            "query": args.query,
            "target_uri": args.target_uri,
            "contexts": contexts,
        }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (requests.RequestException, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
