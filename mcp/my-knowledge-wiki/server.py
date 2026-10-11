#!/usr/bin/env python3
"""Read-only MCP adapter for the my-knowledge-wiki REST API.

The server exposes MCP discovery, initialize, tools/list and tools/call over
POST /mcp. ChatGPT uses the no-auth deployment mode; the optional bearer mode
reuses the same read-only key as the Knowledge API.
"""

from __future__ import annotations

import json
import ipaddress
import math
import socket
import os
import ssl
import sys
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen


BACKEND_URL_ENV = "MY_KNOWLEDGE_WIKI_API_URL"
BACKEND_KEY_ENV = "MY_KNOWLEDGE_WIKI_API_KEY"
MCP_KEY_ENV = "MY_KNOWLEDGE_WIKI_MCP_KEY"
MCP_AUTH_ENV = "MY_KNOWLEDGE_WIKI_MCP_AUTH"
PUBLIC_ENABLED_ENV = "MCP_PUBLIC_ENABLED"
TLS_INSECURE_ENV = "MY_KNOWLEDGE_WIKI_TLS_INSECURE"
HOST_ENV = "MY_KNOWLEDGE_WIKI_MCP_HOST"
PORT_ENV = "MY_KNOWLEDGE_WIKI_MCP_PORT"
TIMEOUT_ENV = "MY_KNOWLEDGE_WIKI_MCP_TIMEOUT"
RATE_LIMIT_ENV = "MCP_PUBLIC_RPM"
TUNNEL_RATE_LIMIT_ENV = "MCP_TUNNEL_RPM"
MAX_INFLIGHT_ENV = "MCP_MAX_INFLIGHT"
MAX_BATCH_ENV = "MCP_MAX_BATCH"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
# Keep the legacy handshake transport, but negotiate the versions supported by
# current Streamable HTTP clients instead of always downgrading them to the
# oldest version. The wire format used by this adapter is compatible with
# these three handshake-era revisions.
LATEST_PROTOCOL_VERSION = "2025-11-25"
DEFAULT_PROTOCOL_VERSION = "2025-03-26"
SUPPORTED_PROTOCOL_VERSIONS = {
    "2025-11-25",
    "2025-06-18",
    "2025-03-26",
}
MCP_PATH = "/mcp"


class ConfigError(RuntimeError):
    pass


class BackendError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None,
                 headers: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.headers = headers or {}


class MCPAdmissionError(RuntimeError):
    def __init__(self, message: str, *, status_code: int,
                 headers: dict[str, str] | None = None,
                 code: int = -32029) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.headers = headers or {}
        self.code = code


class MCPAdmission:
    """Bound the local MCP process for public HTTPS and tunnel ingress."""

    def __init__(self, public_rpm: int, tunnel_rpm: int, max_inflight: int, max_batch: int) -> None:
        self.public_rpm = public_rpm
        self.tunnel_rpm = tunnel_rpm
        self.max_batch = max_batch
        self._inflight = threading.BoundedSemaphore(max_inflight)
        self._lock = threading.Lock()
        self._request_times: dict[tuple[str, str], deque[float]] = {}

    @staticmethod
    def client_key(handler: BaseHTTPRequestHandler) -> tuple[str, str]:
        # Listener ownership determines ingress; user-supplied ingress/forwarded
        # headers on the tunnel listener never create a new budget.
        ingress = getattr(handler.server, "ingress", "tunnel")
        client = "shared" if ingress == "tunnel" else handler.headers.get("X-Real-IP", handler.client_address[0])
        if ingress == "public":
            try:
                client = str(ipaddress.ip_address(client))
            except ValueError:
                client = handler.client_address[0]
        return ingress, client

    def charge(self, handler: BaseHTTPRequestHandler, cost: int) -> dict[str, str]:
        if cost > self.max_batch:
            raise MCPAdmissionError("MCP batch exceeds configured maximum", status_code=400, code=-32600)
        ingress, client = self.client_key(handler)
        limit = self.public_rpm if ingress == "public" else self.tunnel_rpm
        now = time.monotonic()
        key = (ingress, client)
        with self._lock:
            # Bound cardinality as well as the number of timestamps per client.
            if len(self._request_times) >= 4096:
                self._request_times = {k: v for k, v in self._request_times.items() if v and v[-1] > now - 60}
            if key not in self._request_times and len(self._request_times) >= 4096:
                raise MCPAdmissionError("MCP client capacity reached", status_code=503, code=-32003,
                                        headers={"Retry-After": "60"})
            values = self._request_times.setdefault(key, deque())
            while values and values[0] <= now - 60:
                values.popleft()
            reset = max(1, math.ceil(60 - (now - values[0]))) if values else 60
            rate = {"RateLimit-Limit": str(limit),
                    "RateLimit-Remaining": str(max(0, limit - len(values))),
                    "RateLimit-Reset": str(reset)}
            if len(values) + cost > limit:
                raise MCPAdmissionError(f"MCP {ingress} rate limit exceeded", status_code=429,
                                        headers={**rate, "Retry-After": str(reset)})
            for _ in range(cost):
                values.append(now)
            rate["RateLimit-Remaining"] = str(max(0, limit - len(values)))
        return rate

    def acquire(self, handler: BaseHTTPRequestHandler, cost: int) -> dict[str, str]:
        rate = self.charge(handler, cost)
        if not self._inflight.acquire(blocking=False):
            raise MCPAdmissionError("MCP concurrency limit reached", status_code=503,
                                    headers={**rate, "Retry-After": "1"}, code=-32003)
        return rate

    def release(self) -> None:
        self._inflight.release()


class BoundedMCPServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 32

    def __init__(self, address, handler, *, ingress, admission, workers=16, read_timeout=10):
        super().__init__(address, handler)
        self.ingress = ingress
        self.admission = admission
        self.read_timeout = read_timeout
        self._workers = threading.BoundedSemaphore(workers)

    def process_request(self, request, client_address):
        request.settimeout(self.read_timeout)
        if not self._workers.acquire(blocking=False):
            try:
                request.sendall(b"HTTP/1.1 503 Service Unavailable\r\nRetry-After: 1\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
            except OSError:
                pass
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self._workers.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._workers.release()


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
    public_enabled = _bool_env(PUBLIC_ENABLED_ENV)
    if insecure and parsed.scheme != "https":
        raise ConfigError(f"{TLS_INSECURE_ENV} requires an HTTPS backend URL")
    try:
        port = int(os.getenv(PORT_ENV, "8080"))
        timeout = float(os.getenv(TIMEOUT_ENV, "30"))
        public_rpm = int(os.getenv(RATE_LIMIT_ENV, "60"))
        tunnel_rpm = int(os.getenv(TUNNEL_RATE_LIMIT_ENV, "30"))
        max_inflight = int(os.getenv(MAX_INFLIGHT_ENV, "8"))
        max_batch = int(os.getenv(MAX_BATCH_ENV, "8"))
        public_port = int(os.getenv("MCP_PUBLIC_PORT", "8081"))
        workers = int(os.getenv("MCP_MAX_WORKERS", "16"))
        read_timeout = float(os.getenv("MCP_READ_TIMEOUT", "10"))
    except ValueError as exc:
        raise ConfigError(f"invalid MCP port or timeout: {exc}") from None
    if (not 1 <= port <= 65535 or timeout <= 0 or public_rpm < 1 or tunnel_rpm < 1
            or max_inflight < 1 or max_batch < 1 or workers < 1 or read_timeout <= 0
            or not 1 <= public_port <= 65535 or (public_enabled and public_port == port)):
        raise ConfigError("MCP port must be 1..65535 and timeout must be positive")
    host = os.getenv(HOST_ENV, "127.0.0.1")
    if host not in LOCAL_HOSTS:
        raise ConfigError("MCP must bind to loopback")
    return {
        "backend_url": backend_url,
        "backend_key": backend_key,
        "mcp_key": mcp_key,
        "auth": auth,
        "public_enabled": public_enabled,
        "insecure": insecure,
        "host": host,
        "port": port,
        "timeout": timeout,
        "public_rpm": public_rpm,
        "tunnel_rpm": tunnel_rpm,
        "max_inflight": max_inflight,
        "max_batch": max_batch,
        "public_port": public_port,
        "workers": workers,
        "read_timeout": read_timeout,
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
            headers = {
                name: value
                for name, value in (
                    ("RateLimit-Limit", exc.headers.get("RateLimit-Limit")),
                    ("RateLimit-Remaining", exc.headers.get("RateLimit-Remaining")),
                    ("RateLimit-Reset", exc.headers.get("RateLimit-Reset")),
                    ("Retry-After", exc.headers.get("Retry-After")),
                )
                if value
            }
            raise BackendError(
                f"Knowledge API returned HTTP {exc.code}: {detail}",
                status_code=exc.code,
                headers=headers,
            ) from None
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

    def handle_one_request(self) -> None:
        self._admitted = False
        self._rate_headers = {}
        try:
            super().handle_one_request()
        finally:
            if self._admitted and getattr(self.server, "admission", None) is not None:
                self.server.admission.release()


    def _common_headers(self, protocol_version: str = LATEST_PROTOCOL_VERSION) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Expose-Headers", "MCP-Protocol-Version, MCP-Session-Id, Retry-After, RateLimit-Limit, RateLimit-Remaining, RateLimit-Reset")
        self.send_header("MCP-Protocol-Version", protocol_version)

    def _send(self, status: int, payload: dict[str, Any], *, allow: str | None = None,
              protocol_version: str = LATEST_PROTOCOL_VERSION,
              stream: bool = False, headers: dict[str, str] | None = None) -> None:
        encoded = json.dumps(payload, ensure_ascii=False)
        data = (f"data: {encoded}\n\n" if stream else encoded).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/event-stream" if stream else "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        if allow:
            self.send_header("Allow", allow)
        self._common_headers(protocol_version)
        for name, value in (headers if headers is not None else getattr(self, "_rate_headers", {})).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def _send_empty(self, status: int, *, protocol_version: str = LATEST_PROTOCOL_VERSION,
                    headers: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self._common_headers(protocol_version)
        for name, value in (headers if headers is not None else getattr(self, "_rate_headers", {})).items():
            self.send_header(name, value)
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
        self.send_header("Access-Control-Expose-Headers", "MCP-Protocol-Version, MCP-Session-Id, Retry-After, RateLimit-Limit, RateLimit-Remaining, RateLimit-Reset")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/healthz", "/"}:
            self._send(200, {"ok": True, "service": "my-knowledge-wiki-mcp"})
            return
        if self.path in {
            "/.well-known/oauth-protected-resource/mcp",
            "/.well-known/oauth-protected-resource",
        }:
            # This connector intentionally has no OAuth/DCR flow.  A plain 404
            # lets tunnel-client classify the target as an unauthenticated MCP
            # server; returning the generic 405 here is treated as malformed
            # OAuth metadata and keeps tunnel readiness degraded.
            self._send_empty(404)
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
        response: dict[str, Any] | list[dict[str, Any]] | None = None
        response_status = 200
        response_headers: dict[str, str] = dict(self._rate_headers)
        protocol_version = DEFAULT_PROTOCOL_VERSION
        stream = False
        empty_response = False
        request: Any = None
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 2_000_000:
                raise ValueError("invalid request body")
            request = json.loads(self.rfile.read(length))
            messages = request if isinstance(request, list) else [request]
            if not messages or not all(isinstance(message, dict) for message in messages):
                raise ValueError("invalid JSON-RPC message")
            protocol_version = negotiate_protocol_version(messages, self.headers.get("MCP-Protocol-Version"))
            cost = len(messages)
            admission = getattr(self.server, "admission", None)
            if admission is not None:
                response_headers = admission.acquire(self, cost)
                self._rate_headers = response_headers
                self._admitted = True
                self.log_message(
                    "mcp ingress=%s client=%s cost=%s rpc_methods=%s protocol=%s accept=%s",
                    *admission.client_key(self), cost,
                    ",".join(str(message.get("method", "")) for message in messages),
                    protocol_version,
                    self.headers.get("Accept", ""),
                )
            responses = [
                response
                for message in messages
                for response in [dispatch(self.server.client, message, protocol_version)]  # type: ignore[attr-defined]
                if response is not None
            ]
            # A notification has no JSON-RPC response. Streamable HTTP returns
            # 202 when a POST contains only notifications/responses.
            if not responses:
                response_status = 202
                empty_response = True
            else:
                response = responses[0] if not isinstance(request, list) else responses
                # ChatGPT's connector creation probe sends an Accept header
                # containing both JSON and SSE, but validates the special
                # server/discover response as a plain JSON document. Keep
                # normal MCP calls streamable while making discovery
                # unambiguously application/json on that mixed Accept path.
                discovery_only = (
                    not isinstance(request, list)
                    and request.get("method") == "server/discover"
                )
                stream = (
                    "text/event-stream" in self.headers.get("Accept", "").lower()
                    and not discovery_only
                )
        except (ValueError, json.JSONDecodeError) as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": str(exc)}}
            protocol_version = DEFAULT_PROTOCOL_VERSION
            stream = False
            response_status = 400
        except MCPAdmissionError as exc:
            response = {"jsonrpc": "2.0", "id": request.get("id") if isinstance(request, dict) else None,
                        "error": {"code": exc.code, "message": str(exc)}}
            response_status = exc.status_code
            response_headers = exc.headers
            stream = False
        except BackendError as exc:
            response = {"jsonrpc": "2.0", "id": request.get("id") if isinstance(request, dict) else None,
                        "error": {"code": -32029 if exc.status_code == 429 else -32000, "message": str(exc)}}
            response_status = exc.status_code if exc.status_code in {429, 503} else 502
            response_headers = exc.headers
            stream = False
        except Exception as exc:  # errors are returned without secrets
            response = {"jsonrpc": "2.0", "id": request.get("id") if isinstance(locals().get("request"), dict) else None, "error": {"code": -32000, "message": str(exc)}}
            protocol_version = DEFAULT_PROTOCOL_VERSION
            stream = False
            response_status = 502
        if empty_response:
            self._send_empty(response_status, protocol_version=protocol_version, headers=response_headers)
        else:
            self._send(response_status, response or {}, protocol_version=protocol_version,
                       stream=stream, headers=response_headers)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} {fmt % args}", file=sys.stderr)


def negotiate_protocol_version(messages: list[dict[str, Any]], header: str | None) -> str:
    """Return the version shared with the client for this HTTP request."""
    initialize = next((message for message in messages if message.get("method") == "initialize"), None)
    requested = ((initialize or {}).get("params") or {}).get("protocolVersion")
    requested = requested or header
    if requested in SUPPORTED_PROTOCOL_VERSIONS:
        return requested
    return LATEST_PROTOCOL_VERSION


def dispatch(client: KnowledgeClient, request: dict[str, Any],
             protocol_version: str | None = None) -> dict[str, Any] | None:
    if request.get("jsonrpc") != "2.0" or "method" not in request:
        return {"jsonrpc": "2.0", "id": request.get("id"), "error": {"code": -32600, "message": "invalid JSON-RPC request"}}
    request_id = request.get("id")
    method = request["method"]
    params = request.get("params") or {}
    protocol_version = protocol_version or negotiate_protocol_version([request], None)
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"protocolVersion": protocol_version, "capabilities": {"tools": {}}, "serverInfo": {"name": "my-knowledge-wiki", "version": "1.0.0"}}}
    if method == "server/discover":
        return {"jsonrpc": "2.0", "id": request_id, "result": {
            "resultType": "complete",
            "supportedVersions": sorted(SUPPORTED_PROTOCOL_VERSIONS, reverse=True),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "my-knowledge-wiki", "version": "1.0.0"},
            "_meta": {"io.modelcontextprotocol/serverInfo": {"name": "my-knowledge-wiki", "version": "1.0.0"}},
            "instructions": "Read-only access to the Knowledge Wiki through search, retrieval, learning, ontology, article, binding, and graph tools.",
            "ttlMs": 3600000,
            "cacheScope": "public",
        }}
    if method == "notifications/initialized":
        return None
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
    admission = MCPAdmission(config["public_rpm"], config["tunnel_rpm"], config["max_inflight"], config["max_batch"])
    servers = []
    try:
        listeners = [("tunnel", config["port"])]
        if config["public_enabled"]:
            listeners.append(("public", config["public_port"]))
        for ingress, port in listeners:
            server = BoundedMCPServer((config["host"], port), MCPHandler, ingress=ingress,
                                      admission=admission, workers=config["workers"], read_timeout=config["read_timeout"])
            servers.append(server)
            server.mcp_key = config["mcp_key"]
            server.mcp_auth = config["auth"]
            server.client = KnowledgeClient(config)
        thread = None
        if len(servers) > 1:
            thread = threading.Thread(target=servers[1].serve_forever, daemon=True)
            thread.start()
        print(f"MCP tunnel={config['port']} public={config['public_port'] if config['public_enabled'] else 'disabled'} workers={config['workers']}", flush=True)
        servers[0].serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        for server in servers:
            server.shutdown()
        for server in servers:
            server.server_close()
        if thread is not None:
            thread.join(timeout=2)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ConfigError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
