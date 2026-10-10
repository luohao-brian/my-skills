from __future__ import annotations

import importlib.util
import json
import http.client
from pathlib import Path
import re
import sys
import threading
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "mcp/my-knowledge-wiki/server.py"
SPEC = importlib.util.spec_from_file_location("my_knowledge_wiki_mcp", SCRIPT)
assert SPEC and SPEC.loader
MCP = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MCP
SPEC.loader.exec_module(MCP)


class FakeClient:
    def __init__(self) -> None:
        self.calls = []

    def request(self, method, path, *, payload=None, query=None):
        self.calls.append((method, path, payload, query))
        if path == "/ontology/concepts":
            return {"nodes": [{"node_id": "math:measure", "label": "Measure", "aliases": ["测度"]}]}
        if path.startswith("/ontology/concepts/"):
            return {"focus": {"id": "math:measure"}, "nodes": [], "edges": []}
        return {"request_id": "test", "content_revision": "c1"}


class MCPTests(unittest.TestCase):
    def test_tool_list_is_stable_and_read_only(self):
        response = MCP.dispatch(FakeClient(), {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = [tool["name"] for tool in response["result"]["tools"]]
        self.assertEqual(names, ["wiki_query", "wiki_search", "wiki_retrieve", "wiki_learning", "wiki_ontology", "wiki_article", "wiki_binding", "wiki_graph"])

    def test_initialize_advertises_tools(self):
        response = MCP.dispatch(FakeClient(), {"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        self.assertEqual(response["result"]["capabilities"], {"tools": {}})
        self.assertEqual(response["result"]["protocolVersion"], "2025-11-25")

    def test_initialize_negotiates_client_version_and_notifications_have_no_response(self):
        client = FakeClient()
        response = MCP.dispatch(
            client,
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2025-06-18"}},
        )
        self.assertEqual(response["result"]["protocolVersion"], "2025-06-18")
        self.assertIsNone(MCP.dispatch(client, {"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def test_streamable_http_probe_methods(self):
        server = MCP.ThreadingHTTPServer(("127.0.0.1", 0), MCP.MCPHandler)
        server.mcp_auth = "none"
        server.mcp_key = ""
        server.client = FakeClient()
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = http.client.HTTPConnection(*server.server_address, timeout=5)
            client.request("OPTIONS", "/mcp")
            options = client.getresponse()
            self.assertEqual(options.status, 204)
            self.assertIn("POST", options.getheader("Access-Control-Allow-Methods"))
            options.read()

            client.request("POST", "/mcp", body=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"}), headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
            response = client.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(response.getheader("MCP-Protocol-Version"), "2025-11-25")
            self.assertEqual(json.loads(response.read())["result"]["protocolVersion"], "2025-11-25")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_learning_resolves_alias(self):
        client = FakeClient()
        response = MCP.dispatch(client, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "wiki_learning", "arguments": {"concept": "测度"}}})
        self.assertIn('"focus":', response["result"]["content"][0]["text"])
        self.assertEqual(client.calls[-1][1], "/ontology/concepts/math:measure")

    def test_bearer_mode_requires_mcp_key(self):
        with patch.dict(MCP.os.environ, {MCP.BACKEND_URL_ENV: "https://example.com/api/knowledge", MCP.BACKEND_KEY_ENV: "backend"}, clear=True):
            with self.assertRaisesRegex(MCP.ConfigError, "MCP_KEY"):
                MCP.load_config()

    def test_no_auth_mode_does_not_require_mcp_key(self):
        with patch.dict(MCP.os.environ, {
            MCP.BACKEND_URL_ENV: "https://example.com/api/knowledge",
            MCP.BACKEND_KEY_ENV: "backend",
            MCP.MCP_AUTH_ENV: "none",
        }, clear=True):
            config = MCP.load_config()
        self.assertEqual(config["auth"], "none")
        self.assertEqual(config["mcp_key"], "")

    def test_package_contains_no_literal_credentials_or_host_details(self):
        forbidden = re.compile(
            r"(?:sk-[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|-----BEGIN|"
            r"115\.190\.125\.25|root@|/root/|/opt/)"
        )
        for path in SCRIPT.parent.iterdir():
            if path.is_file() and path.name != "__pycache__":
                self.assertIsNone(forbidden.search(path.read_text(encoding="utf-8")), path)


if __name__ == "__main__":
    unittest.main()
