#!/usr/bin/env python3
"""Query the read-only codex-rspress-admin Knowledge API."""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen


API_URL_ENV = "MY_KNOWLEDGE_WIKI_API_URL"
API_KEY_ENV = "MY_KNOWLEDGE_WIKI_API_KEY"
TLS_INSECURE_ENV = "MY_KNOWLEDGE_WIKI_TLS_INSECURE"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


class QueryError(RuntimeError):
    """A configuration or HTTP failure safe to show without secrets."""


def load_config() -> tuple[str, str, bool]:
    api_url = os.getenv(API_URL_ENV, "").strip().rstrip("/")
    api_key = os.getenv(API_KEY_ENV, "").strip()
    if not api_url:
        raise QueryError(f"missing {API_URL_ENV}")
    if not api_key:
        raise QueryError(f"missing {API_KEY_ENV}")

    parsed = urlsplit(api_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise QueryError(f"{API_URL_ENV} must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password:
        raise QueryError(f"{API_URL_ENV} must not contain credentials")
    if parsed.scheme != "https" and parsed.hostname not in LOCAL_HOSTS:
        raise QueryError(f"{API_URL_ENV} must use HTTPS for a remote host")
    if parsed.query or parsed.fragment:
        raise QueryError(f"{API_URL_ENV} must not contain a query or fragment")
    insecure_value = os.getenv(TLS_INSECURE_ENV, "").strip().lower()
    if insecure_value not in {"", "0", "false", "no", "1", "true", "yes"}:
        raise QueryError(f"{TLS_INSECURE_ENV} must be true or false")
    insecure_tls = insecure_value in {"1", "true", "yes"}
    if insecure_tls and parsed.scheme != "https":
        raise QueryError(f"{TLS_INSECURE_ENV} requires an HTTPS API URL")
    return api_url, api_key, insecure_tls


class KnowledgeClient:
    def __init__(self, api_url: str, api_key: str, timeout: float, insecure_tls: bool = False) -> None:
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.ssl_context = ssl._create_unverified_context() if insecure_tls else None

    def request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
    ) -> Any:
        url = self.api_url + path
        if query:
            encoded = urlencode({key: value for key, value in query.items() if value is not None})
            if encoded:
                url += "?" + encoded
        body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = Request(
            url,
            data=body,
            method=method,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "my-knowledge-wiki-skill/1",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout, context=self.ssl_context) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            detail = _problem_detail(raw).replace(self.api_key, "<redacted>")
            raise QueryError(f"Knowledge API returned HTTP {exc.code}: {detail}") from None
        except (URLError, TimeoutError) as exc:
            reason = getattr(exc, "reason", exc)
            raise QueryError(f"Knowledge API request failed: {reason}") from None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise QueryError("Knowledge API returned a non-JSON response") from None


def _problem_detail(raw: str) -> str:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return raw[:300] or "empty response"
    if isinstance(value, dict):
        for key in ("detail", "title", "error"):
            if value.get(key):
                return str(value[key])[:300]
    return "request rejected"


def positive_int(minimum: int, maximum: int):
    def parse(value: str) -> int:
        number = int(value)
        if number < minimum or number > maximum:
            raise argparse.ArgumentTypeError(f"must be between {minimum} and {maximum}")
        return number
    return parse


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--timeout", type=float, default=30.0, help="request timeout in seconds")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query My Knowledge Wiki through the read-only Knowledge API")
    subparsers = parser.add_subparsers(dest="command", required=True)

    query = subparsers.add_parser("query", help="answer a question with source citations")
    query.add_argument("question")
    query.add_argument("--retrieval-mode", choices=("keyword", "semantic", "vector", "hybrid", "graph_hybrid"), default="graph_hybrid")
    query.add_argument("--max-citations", type=positive_int(1, 20), default=8)
    add_common(query)

    for name, help_text in (("retrieve", "return full matching sections"), ("search", "return matching articles and excerpts")):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("text")
        command.add_argument("--mode", choices=("keyword", "semantic", "vector", "hybrid"), default="hybrid")
        command.add_argument("--limit", type=positive_int(1, 100), default=10)
        if name == "retrieve":
            command.add_argument("--sections-per-article", type=positive_int(1, 10), default=3)
        add_common(command)

    learning = subparsers.add_parser("learning", help="return one concept's cross-domain knowledge structure and articles")
    learning.add_argument("concept")
    learning.add_argument("--node-limit", type=positive_int(1, 100), default=40)
    add_common(learning)

    ontology = subparsers.add_parser("ontology", help="read the canonical ontology graph")
    ontology.add_argument("--domain-id", default="")
    ontology.add_argument("--node-limit", type=positive_int(1, 100), default=100)
    add_common(ontology)
    return parser


def execute(args: argparse.Namespace, client: KnowledgeClient) -> Any:
    if args.command == "query":
        return client.request("POST", "/answers", payload={
            "question": args.question,
            "retrieval_mode": args.retrieval_mode,
            "max_citations": args.max_citations,
        })
    if args.command in {"retrieve", "search"}:
        payload: dict[str, Any] = {"query": args.text, "mode": args.mode, "limit": args.limit}
        if args.command == "retrieve":
            payload["sections_per_article"] = args.sections_per_article
        return client.request("POST", f"/{args.command}", payload=payload)
    if args.command == "learning":
        catalog = client.request("GET", "/ontology/nodes", query={"query": args.concept, "limit": 20})
        nodes = catalog.get("nodes", []) if isinstance(catalog, dict) else []
        requested = args.concept.strip().casefold()
        exact = [node for node in nodes if requested in {
            str(node.get("node_id", "")).casefold(), str(node.get("label", "")).casefold(),
        }]
        alias_exact = [node for node in nodes if requested in {
            str(alias).casefold() for alias in node.get("aliases", [])
        }]
        concept_alias_exact = [node for node in alias_exact if node.get("kind") == "concept"]
        label_matches = [node for node in nodes if requested and requested in str(node.get("label", "")).casefold()]
        alias_matches = [node for node in nodes if requested and any(
            requested in str(alias).casefold() for alias in node.get("aliases", [])
        )]
        matches = exact or concept_alias_exact or alias_exact or label_matches or alias_matches
        if not matches:
            raise QueryError(f"ontology concept not found: {args.concept}")
        if len(matches) > 1:
            labels = "、".join(str(node.get("label")) for node in matches[:5])
            raise QueryError(f"ontology concept is ambiguous: {labels}")
        node_id = str(matches[0].get("node_id") or "")
        if not node_id:
            raise QueryError("Knowledge API returned an ontology node without node_id")
        return client.request("GET", f"/ontology/nodes/{quote(node_id, safe=':-._~')}/learning-view", query={
            "node_limit": args.node_limit,
        })
    return client.request("GET", "/ontology/graph", query={
        "domain_id": args.domain_id or None,
        "node_limit": args.node_limit,
    })


def main() -> int:
    args = build_parser().parse_args()
    if args.timeout <= 0:
        raise QueryError("timeout must be greater than zero")
    api_url, api_key, insecure_tls = load_config()
    result = execute(args, KnowledgeClient(api_url, api_key, args.timeout, insecure_tls))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, QueryError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
