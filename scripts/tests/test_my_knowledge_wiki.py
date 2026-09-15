from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "openclaw-skills/my-knowledge-wiki/scripts/knowledge_query.py"
SPEC = importlib.util.spec_from_file_location("knowledge_query_skill", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
KNOWLEDGE_QUERY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = KNOWLEDGE_QUERY
SPEC.loader.exec_module(KNOWLEDGE_QUERY)


class RecordingHandler(BaseHTTPRequestHandler):
    requests: list[dict[str, object]] = []

    def _reply(self) -> None:
        if self.path == "/api/knowledge/ontology/concepts?query=DDPM&limit=20":
            value = {"nodes": [
                {"node_id": "ai:ddpm", "kind": "concept", "label": "Diffusion Model", "aliases": ["DDPM", "扩散模型"]},
            ]}
        elif self.path.startswith("/api/knowledge/ontology/concepts/ai:ddpm"):
            value = {"focus": {"id": "ai:ddpm", "label": "Diffusion Model"}, "nodes": [], "edges": []}
        else:
            value = {"request_id": "req_test", "answer": "ok"}
        payload = json.dumps(value).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length))
        self.__class__.requests.append({
            "path": self.path,
            "authorization": self.headers.get("Authorization"),
            "body": body,
        })
        self._reply()

    def do_GET(self) -> None:  # noqa: N802
        self.__class__.requests.append({
            "path": self.path,
            "authorization": self.headers.get("Authorization"),
            "body": None,
        })
        self._reply()

    def log_message(self, format: str, *args: object) -> None:
        return


class KnowledgeQuerySkillTests(unittest.TestCase):
    def setUp(self) -> None:
        RecordingHandler.requests = []
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), RecordingHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def client(self):
        port = self.server.server_address[1]
        return KNOWLEDGE_QUERY.KnowledgeClient(
            f"http://127.0.0.1:{port}/api/knowledge", "secret-token", 2,
        )

    def test_query_uses_bearer_key_and_current_answers_schema(self) -> None:
        args = KNOWLEDGE_QUERY.build_parser().parse_args(["query", "DDPM 依赖什么？"])
        result = KNOWLEDGE_QUERY.execute(args, self.client())
        self.assertEqual(result["answer"], "ok")
        request = RecordingHandler.requests[0]
        self.assertEqual(request["path"], "/api/knowledge/answers")
        self.assertEqual(request["authorization"], "Bearer secret-token")
        self.assertEqual(request["body"], {
            "question": "DDPM 依赖什么？",
            "retrieval_mode": "graph_hybrid",
            "max_citations": 8,
        })

    def test_remote_plain_http_is_rejected(self) -> None:
        with patch.dict(KNOWLEDGE_QUERY.os.environ, {
            KNOWLEDGE_QUERY.API_URL_ENV: "http://example.com/api/knowledge",
            KNOWLEDGE_QUERY.API_KEY_ENV: "secret-token",
        }, clear=True):
            with self.assertRaisesRegex(KNOWLEDGE_QUERY.QueryError, "must use HTTPS"):
                KNOWLEDGE_QUERY.load_config()

    def test_insecure_tls_requires_https_and_is_explicit(self) -> None:
        with patch.dict(KNOWLEDGE_QUERY.os.environ, {
            KNOWLEDGE_QUERY.API_URL_ENV: "https://example.com/api/knowledge",
            KNOWLEDGE_QUERY.API_KEY_ENV: "secret-token",
            KNOWLEDGE_QUERY.TLS_INSECURE_ENV: "true",
        }, clear=True):
            api_url, api_key, insecure_tls = KNOWLEDGE_QUERY.load_config()
        self.assertEqual(api_url, "https://example.com/api/knowledge")
        self.assertEqual(api_key, "secret-token")
        self.assertTrue(insecure_tls)

    def test_configured_self_signed_origin_is_insecure_by_default(self) -> None:
        with patch.dict(KNOWLEDGE_QUERY.os.environ, {
            KNOWLEDGE_QUERY.API_URL_ENV: "https://8.140.22.158/api/knowledge",
            KNOWLEDGE_QUERY.API_KEY_ENV: "secret-token",
        }, clear=True):
            api_url, api_key, insecure_tls = KNOWLEDGE_QUERY.load_config()
        self.assertEqual(api_url, "https://8.140.22.158/api/knowledge")
        self.assertEqual(api_key, "secret-token")
        self.assertTrue(insecure_tls)

    def test_configured_self_signed_origin_does_not_apply_to_other_hosts(self) -> None:
        with patch.dict(KNOWLEDGE_QUERY.os.environ, {
            KNOWLEDGE_QUERY.API_URL_ENV: "https://example.com/api/knowledge",
            KNOWLEDGE_QUERY.API_KEY_ENV: "secret-token",
        }, clear=True):
            _, _, insecure_tls = KNOWLEDGE_QUERY.load_config()
        self.assertFalse(insecure_tls)

    def test_explicit_false_overrides_configured_self_signed_origin(self) -> None:
        with patch.dict(KNOWLEDGE_QUERY.os.environ, {
            KNOWLEDGE_QUERY.API_URL_ENV: "https://8.140.22.158/api/knowledge",
            KNOWLEDGE_QUERY.API_KEY_ENV: "secret-token",
            KNOWLEDGE_QUERY.TLS_INSECURE_ENV: "false",
        }, clear=True):
            _, _, insecure_tls = KNOWLEDGE_QUERY.load_config()
        self.assertFalse(insecure_tls)

    def test_learning_resolves_concept_and_ontology_maps_to_current_routes(self) -> None:
        learning_args = KNOWLEDGE_QUERY.build_parser().parse_args(["learning", "DDPM"])
        learning = KNOWLEDGE_QUERY.execute(learning_args, self.client())
        self.assertEqual(learning["focus"]["id"], "ai:ddpm")
        ontology_args = KNOWLEDGE_QUERY.build_parser().parse_args([
            "ontology", "--domain-id", "mathematics",
        ])
        KNOWLEDGE_QUERY.execute(ontology_args, self.client())

        catalog_request, learning_request, ontology_request = RecordingHandler.requests
        self.assertEqual(catalog_request["path"], "/api/knowledge/ontology/concepts?query=DDPM&limit=20")
        self.assertEqual(learning_request["path"], "/api/knowledge/ontology/concepts/ai:ddpm?node_limit=40")
        self.assertEqual(
            ontology_request["path"],
            "/api/knowledge/ontology/map?domain_id=mathematics&node_limit=100",
        )
        self.assertEqual(ontology_request["authorization"], "Bearer secret-token")


if __name__ == "__main__":
    unittest.main()
