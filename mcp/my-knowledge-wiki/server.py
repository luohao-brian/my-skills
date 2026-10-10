#!/usr/bin/env python3
"""Read-only MCP adapter for the my-knowledge-wiki REST API.

The server exposes the MCP JSON-RPC methods initialize, tools/list and
tools/call over POST /mcp.  ChatGPT uses the no-auth deployment mode; the
optional bearer mode reuses the same read-only key as the Knowledge API.
"""

from __future__ import annotations

import json
import os
import ssl
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen


BACKEND_URL_ENV = "MY_KNOWLEDGE_WIKI_API_URL"
BACKEND_KEY_ENV = "MY_KNOWLEDGE_WIKI_API_KEY"
MCP_KEY_ENV = "MY_KNOWLEDGE_WIKI_MCP_KEY"
MCP_AUTH_ENV = "MY_KNOWLEDGE_WIKI_MCP_AUTH"
TLS_INSECURE_ENV = "MY_KNOWLEDGE_WIKI_TLS_INSECURE"
HOST_ENV = "MY_KNOWLEDGE_WIKI_MCP_HOST"
PORT_ENV = "MY_KNOWLEDGE_WIKI_MCP_PORT"
TIMEOUT_ENV = "MY_KNOWLEDGE_WIKI_MCP_TIMEOUT"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
PROTOCOL_VERSION = "2025-03-26"
MCP_PATH = "/mcp"


class ConfigError(RuntimeError):
    pass


class BackendError(RuntimeError):
    pass


def _bool_env(name: str) -> bool:
    value = os.getenv(name, "").strip().lower()
    if value not in {"", "0", "false", "no", "1", "true", "yes"}:
        raise ConfigError(f"{name} must be true or false")
    return value in {"1", "true", "yes"}


def load_config() -> dict[str, Any]:
    backend_url = os.getenv(BACKEND_URL_ENV, "").strip().rstrip("/")
    backend_key = os.getenv(BACKEND_KEY_ENV, "").strip()
    mcp_key = os.getenv(MCP_KEY_ENV, "").strip()
    auth = os.getenv(MCP_AUTH_ENV, "bearer").strip().lower()
    if auth not in {"none", "bearer"}:
        raise ConfigError(f"{MCP_AUTH_ENV} must be none or bearer")
    if not backend_url or not backend_key or (auth == "bearer" and not mcp_key):
        required = f"{BACKEND_URL_ENV} and {BACKEND_KEY_ENV}"
        if auth == "bearer":
            required += f", and {MCP_KEY_ENV}"
        raise ConfigError(f"{required} are required")
    parsed = urlsplit(backend_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ConfigError(f"{BACKEND_URL_ENV} must be an absolute HTTP(S) URL")
    if parsed.scheme != "https" and parsed.hostname not in LOCAL_HOSTS:
        raise ConfigError(f"{BACKEND_URL_ENV} must use HTTPS for a remote host")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ConfigError(f"{BACKEND_URL_ENV} must not contain credentials, query, or fragment")
    insecure = _bool_env(TLS_INSECURE_ENV)
    if insecure and parsed.scheme != "https":
        raise ConfigError(f"{TLS_INSECURE_ENV} requires an HTTPS backend URL")
    try:
        port = int(os.getenv(PORT_ENV, "8080"))
        timeout = float(os.getenv(TIMEOUT_ENV, "30"))
    except ValueError as exc:
        raise ConfigError(f"invalid MCP port or timeout: {exc}") from None
    if not 1 <= port <= 65535 or timeout <= 0:
        raise ConfigError("MCP port must be 1..65535 and timeout must be positive")
    return {
        "backend_url": backend_url,
        "backend_key": backend_key,
        "mcp_key": mcp_key,
        "auth": auth,
        "insecure": insecure,
        "host": os.getenv(HOST_ENV, "127.0.0.1"),
        "port": port,
        "timeout": timeout,
    }


def problem_detail(raw: str) -> str:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return raw[:300] or "empty response"
    if isinstance(value, dict):
        for key in ("detail", "title", "error"):
            if value.get(key):
                return str(value[key])[:300]
    return "request rejected"


class KnowledgeClient:
    def __init__(self, config: dict[str, Any]) -> None:
        self.base = config["backend_url"]
        self.key = config["backend_key"]
        self.timeout = config["timeout"]
        self.context = ssl._create_unverified_context() if config["insecure"] else None

    def request(self, method: str, path: str, *, payload: dict[str, Any] | None = None,
                query: dict[str, Any] | None = None) -> Any:
        url = self.base + path
        if query:
            encoded = urlencode({k: v for k, v in query.items() if v is not None})
            if encoded:
                url += "?" + encoded
        body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
        request = Request(url, data=body, method=method, headers={
            "Accept": "application/json", "Content-Type": "application/json",
            "Authorization": f"Bearer {self.key}",
            "User-Agent": "my-knowledge-wiki-mcp/1",
        })
        try:
            with urlopen(request, timeout=self.timeout, context=self.context) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = problem_detail(exc.read().decode("utf-8", errors="replace"))
            raise BackendError(f"Knowledge API returned HTTP {exc.code}: {detail}") from None
        except (URLError, TimeoutError) as exc:
            raise BackendError(f"Knowledge API request failed: {getattr(exc, 'reason', exc)}") from None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise BackendError("Knowledge API returned a non-JSON response") from None


TOOLS = [
    {"name": "wiki_query", "description": "Answer a Knowledge Wiki question with citations and revision metadata.",
     "inputSchema": {"type": "object", "properties": {"question": {"type": "string"}, "retrieval_mode": {"type": "string", "enum": ["keyword", "semantic", "vector", "hybrid", "graph_hybrid"]}, "max_citations": {"type": "integer", "minimum": 1, "maximum": 20}}, "required": ["question"]}},
    {"name": "wiki_search", "description": "Search Knowledge Wiki sections and article excerpts.",
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "mode": {"type": "string", "enum": ["keyword", "semantic", "vector", "hybrid"]}, "limit": {"type": "integer", "minimum": 1, "maximum": 100}}, "required": ["query"]}},
    {"name": "wiki_retrieve", "description": "Retrieve matching Knowledge Wiki sections and adjacent source context.",
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "mode": {"type": "string", "enum": ["keyword", "semantic", "vector", "hybrid"]}, "limit": {"type": "integer", "minimum": 1, "maximum": 100}, "sections_per_article": {"type": "integer", "minimum": 1, "maximum": 10}}, "required": ["query"]}},
    {"name": "wiki_learning", "description": "Read a concept's ontology neighborhood and learning materials.",
     "inputSchema": {"type": "object", "properties": {"concept": {"type": "string"}, "node_limit": {"type": "integer", "minimum": 1, "maximum": 100}}, "required": ["concept"]}},
    {"name": "wiki_ontology", "description": "Read the global or domain ontology graph.",
     "inputSchema": {"type": "object", "properties": {"domain_id": {"type": "string"}, "node_limit": {"type": "integer", "minimum": 1, "maximum": 100}, "full": {"type": "boolean"}}}},
    {"name": "wiki_article", "description": "Read indexed article metadata and its public URL.", "inputSchema": {"type": "object", "properties": {"article_id": {"type": "string"}}, "required": ["article_id"]}},
    {"name": "wiki_binding", "description": "Read an article's ontology bindings and Leaf evidence.", "inputSchema": {"type": "object", "properties": {"article_id": {"type": "string"}}, "required": ["article_id"]}},
    {"name": "wiki_graph", "description": "Read an article's evidence graph and source Leaves.", "inputSchema": {"type": "object", "properties": {"article_id": {"type": "string"}, "include_sources": {"type": "boolean", "default": True}}, "required": ["article_id"]}},
]

# These tools only read the Knowledge API.  The hints let clients such as
# ChatGPT present the connector as a read-only integration.
for _tool in TOOLS:
    _tool["annotations"] = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
    }


def _required(args: dict[str, Any], key: str) -> str:
    value = args.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value.strip()


def call_tool(client: KnowledgeClient, name: str, args: dict[str, Any]) -> Any:
    if name == "wiki_query":
        return client.request("POST", "/answers", payload={"question": _required(args, "question"), "retrieval_mode": args.get("retrieval_mode", "graph_hybrid"), "max_citations": args.get("max_citations", 8)})
    if name in {"wiki_search", "wiki_retrieve"}:
        payload = {"query": _required(args, "query"), "mode": args.get("mode", "hybrid"), "limit": args.get("limit", 10)}
        if name == "wiki_retrieve":
            payload["sections_per_article"] = args.get("sections_per_article", 3)
        return client.request("POST", "/search" if name == "wiki_search" else "/retrieve", payload=payload)
    if name == "wiki_learning":
        concept = _required(args, "concept")
        catalog = client.request("GET", "/ontology/concepts", query={"query": concept, "limit": 20})
        nodes = catalog.get("nodes", []) if isinstance(catalog, dict) else []
        requested = concept.casefold()
        matches = [n for n in nodes if requested in {str(n.get("node_id", "")).casefold(), str(n.get("label", "")).casefold()}]
        matches = matches or [n for n in nodes if any(requested == str(a).casefold() for a in n.get("aliases", []))]
        matches = matches or [n for n in nodes if requested in str(n.get("label", "")).casefold()]
        if not matches:
            raise ValueError(f"ontology concept not found: {concept}")
        if len(matches) > 1:
            raise ValueError("ontology concept is ambiguous")
        node_id = str(matches[0].get("node_id", ""))
        if not node_id:
            raise BackendError("Knowledge API returned an ontology node without node_id")
        return client.request("GET", f"/ontology/concepts/{quote(node_id, safe=':-._~')}", query={"node_limit": args.get("node_limit", 40)})
    if name == "wiki_ontology":
        return client.request("GET", "/ontology/map", query={"domain_id": args.get("domain_id") or None, "node_limit": args.get("node_limit", 100), "full": "true" if args.get("full", False) else None})
    article_id = quote(_required(args, "article_id"), safe=":-._~")
    if name == "wiki_article":
        return client.request("GET", f"/resources/{article_id}")
    if name == "wiki_binding":
        return client.request("GET", f"/resources/{article_id}/ontology")
    if name == "wiki_graph":
        return client.request("GET", f"/resources/{article_id}/graph", query={"include_sources": args.get("include_sources", True)})
    raise ValueError(f"unknown tool: {name}")


def result(value: Any) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False, indent=2)}], "structuredContent": value}


class MCPHandler(BaseHTTPRequestHandler):
    server_version = "my-knowledge-wiki-mcp/1"

    def _common_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Expose-Headers", "MCP-Protocol-Version, MCP-Session-Id")
        self.send_header("MCP-Protocol-Version", PROTOCOL_VERSION)

    def _send(self, status: int, payload: dict[str, Any], *, allow: str | None = None) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        if allow:
            self.send_header("Allow", allow)
        self._common_headers()
        self.end_headers()
        self.wfile.write(data)

    def _send_empty(self, status: int) -> None:
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self._common_headers()
        self.end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802
        if self.path != MCP_PATH:
            self._send(404, {"error": "not found"})
            return
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, MCP-Protocol-Version, MCP-Session-Id")
        self.send_header("Access-Control-Expose-Headers", "MCP-Protocol-Version, MCP-Session-Id")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/healthz", "/"}:
            self._send(200, {"ok": True, "service": "my-knowledge-wiki-mcp"})
            return
        if self.path == MCP_PATH:
            # Streamable HTTP reserves GET for a server-to-client event stream.
            # This adapter is stateless and has no session stream to open.
            self._send(405, {"error": "stateless MCP does not open a GET stream"}, allow="GET, POST, DELETE")
            return
        self._send(405, {"error": "MCP uses POST /mcp"})

    def do_DELETE(self) -> None:  # noqa: N802
        if self.path == MCP_PATH:
            # There are no server-side sessions to terminate in stateless mode.
            self._send_empty(204)
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != MCP_PATH:
            self._send(404, {"error": "not found"})
            return
        if self.server.mcp_auth == "bearer":  # type: ignore[attr-defined]
            expected = self.server.mcp_key  # type: ignore[attr-defined]
            supplied = self.headers.get("Authorization", "")
            if supplied != f"Bearer {expected}":
                self._send(401, {"error": "invalid MCP credentials"})
                return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 2_000_000:
                raise ValueError("invalid request body")
            request = json.loads(self.rfile.read(length))
            response = dispatch(self.server.client, request)  # type: ignore[attr-defined]
        except (ValueError, json.JSONDecodeError) as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": str(exc)}}
        except Exception as exc:  # errors are returned without secrets
            response = {"jsonrpc": "2.0", "id": request.get("id") if isinstance(locals().get("request"), dict) else None, "error": {"code": -32000, "message": str(exc)}}
        self._send(200, response)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} {fmt % args}", file=sys.stderr)


def dispatch(client: KnowledgeClient, request: dict[str, Any]) -> dict[str, Any]:
    if request.get("jsonrpc") != "2.0" or "method" not in request:
        return {"jsonrpc": "2.0", "id": request.get("id"), "error": {"code": -32600, "message": "invalid JSON-RPC request"}}
    request_id = request.get("id")
    method = request["method"]
    params = request.get("params") or {}
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {"tools": {}}, "serverInfo": {"name": "my-knowledge-wiki", "version": "1.0.0"}}}
    if method == "notifications/initialized":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        if not isinstance(name, str):
            raise ValueError("tools/call requires params.name")
        value = call_tool(client, name, params.get("arguments") or {})
        return {"jsonrpc": "2.0", "id": request_id, "result": result(value)}
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"method not found: {method}"}}


def main() -> int:
    config = load_config()
    server = ThreadingHTTPServer((config["host"], config["port"]), MCPHandler)
    server.mcp_key = config["mcp_key"]  # type: ignore[attr-defined]
    server.mcp_auth = config["auth"]  # type: ignore[attr-defined]
    server.client = KnowledgeClient(config)  # type: ignore[attr-defined]
    print(f"my-knowledge-wiki MCP listening on {config['host']}:{config['port']}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ConfigError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
