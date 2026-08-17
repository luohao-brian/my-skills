from __future__ import annotations

import argparse
import importlib.util
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ai_news.py"
SPEC = importlib.util.spec_from_file_location("ai_news", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AiNewsDiagnosticsTests(unittest.TestCase):
    def test_canonical_url_removes_tracking_without_losing_location(self) -> None:
        self.assertEqual(
            MODULE.canonical_url("https://Example.com/news/item/?utm_source=x&id=1#part"),
            "https://example.com/news/item?id=1",
        )

    def test_collect_preserves_source_provenance(self) -> None:
        registry = {
            "sources": [
                {
                    "id": "official-feed",
                    "name": "Official Feed",
                    "kind": "rss",
                    "role": "official",
                    "url": "https://example.com/feed.xml",
                }
            ]
        }
        row = {
            "title": "New model",
            "source_url": "https://example.com/news/model",
            "published_at": "2026-08-16T08:00:00+08:00",
            "summary_basis": "A model was released.",
        }
        rows = [row, dict(row)]
        args = argparse.Namespace(date="2026-08-16")
        with (
            mock.patch.object(MODULE, "load_json", return_value=registry),
            mock.patch.object(MODULE, "resolve_fetcher", return_value=lambda source, window: rows),
        ):
            document = MODULE.collect_document(args)

        candidate = document["candidates"][0]
        self.assertEqual(candidate["source_id"], "official-feed")
        self.assertEqual(candidate["source_role"], "official")
        self.assertEqual(candidate["published_at"], "2026-08-16T08:00:00+08:00")
        self.assertEqual(document["sources"]["official-feed"]["raw"], 2)
        self.assertEqual(document["sources"]["official-feed"]["selected"], 1)
        self.assertEqual(document["sources"]["official-feed"]["exact_duplicate_rows"], 1)

    def test_diagnostics_distinguish_rows_from_unique_urls(self) -> None:
        data = {
            "window": {"label": "test"},
            "_sources": [
                {
                    "source_id": "a",
                    "name": "A",
                    "kind": "rss",
                    "role": "media",
                    "ok": True,
                    "raw": 2,
                    "candidates": 1,
                    "exact_duplicates": 0,
                    "error": None,
                },
                {
                    "source_id": "b",
                    "name": "B",
                    "kind": "rss",
                    "role": "aggregator",
                    "ok": True,
                    "raw": 2,
                    "candidates": 1,
                    "exact_duplicates": 0,
                    "error": None,
                },
            ],
            "candidates": [
                {"title": "A", "url": "https://example.com/item?utm_source=a", "summary": "x", "source_id": "a"},
                {"title": "A", "url": "https://example.com/item?utm_source=b", "summary": "x", "source_id": "b"},
            ],
        }
        document = MODULE.public_document(data)
        self.assertEqual(document["diagnostics"]["candidate_rows"], 2)
        self.assertEqual(document["diagnostics"]["unique_articles"], 1)
        self.assertEqual(document["diagnostics"]["unique_urls"], 1)
        self.assertEqual(document["diagnostics"]["exact_duplicate_rows"], 1)
        self.assertEqual(document["diagnostics"]["shared_url_rows"], 1)
        self.assertEqual(document["diagnostics"]["by_source_role"]["media"]["selected"], 1)

    def test_old_candidate_shape_remains_renderable(self) -> None:
        document = {
            "window": {"label": "test"},
            "sources": {},
            "candidates": [{"title": "A", "url": "https://example.com/a", "summary": "B"}],
        }
        self.assertEqual(MODULE.validate_document(document), [])

    def test_shared_digest_url_does_not_merge_different_titles(self) -> None:
        first = {"title": "Story A", "url": "https://example.com/daily", "summary": "A"}
        second = {"title": "Story B", "url": "https://example.com/daily", "summary": "B"}
        self.assertNotEqual(MODULE.article_key(first), MODULE.article_key(second))

    def test_explicit_proxy_overrides_inherited_scheme_settings(self) -> None:
        inherited = {
            "HTTP_PROXY": "http://old.example:8080",
            "http_proxy": "http://old.example:8080",
        }
        with (
            mock.patch.dict(MODULE.os.environ, inherited, clear=True),
            mock.patch.object(MODULE.urllib.request, "install_opener") as install_opener,
        ):
            MODULE.configure_proxy(None, "http://127.0.0.1:8080", "example.cn")
            self.assertNotIn("HTTP_PROXY", MODULE.os.environ)
            self.assertNotIn("http_proxy", MODULE.os.environ)
            self.assertEqual(MODULE.os.environ["HTTPS_PROXY"], "http://127.0.0.1:8080")
            self.assertEqual(
                MODULE.os.environ["NO_PROXY"],
                "localhost,127.0.0.1,::1,example.cn",
            )
            install_opener.assert_called_once()


if __name__ == "__main__":
    unittest.main()
