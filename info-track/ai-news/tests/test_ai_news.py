from __future__ import annotations

import argparse
import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ai_news.py"
SPEC = importlib.util.spec_from_file_location("ai_news", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

from adapters import html_index as HTML_INDEX


TZ = timezone(timedelta(hours=8))


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


class TmtpostAdapterTests(unittest.TestCase):
    def test_current_linked_blocks_use_individual_article_urls(self) -> None:
        html = """
        <blockquote><p><a href="/agent/ai-article?id=20045"><strong>
        一、结构性而非周期性：德意志银行为何把核心总账搬上谷歌云
        </strong></a></p></blockquote>
        <p>1.德意志银行将核心财务平台迁移至谷歌云。</p>
        <p>2.AI 研究助手嵌入研究生产流程。</p>
        """

        items = HTML_INDEX._parse_tmtpost_daily(
            html,
            "https://www.tmtpost.com/8116690.html",
            "2026-08-26",
        )

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "结构性而非周期性：德意志银行为何把核心总账搬上谷歌云")
        self.assertEqual(
            items[0]["source_url"],
            "https://www.tmtpost.com/agent/ai-article?id=20045",
        )
        self.assertIn("AI 研究助手", items[0]["summary_basis"])

    def test_legacy_unlinked_blocks_keep_daily_url(self) -> None:
        html = "<blockquote>一、旧格式标题</blockquote><p>旧格式摘要。</p>"
        daily_url = "https://www.tmtpost.com/legacy.html"

        items = HTML_INDEX._parse_tmtpost_daily(html, daily_url, "2026-08-25")

        self.assertEqual(items[0]["source_url"], daily_url)
        self.assertEqual(items[0]["title"], "旧格式标题")

    def test_exact_date_selects_daily_before_parsing_child_titles(self) -> None:
        source = {"url": "https://www.tmtpost.com/user/7944025"}
        window = {
            "date": "2026-08-26",
            "start": datetime(2026, 8, 26, tzinfo=TZ),
            "end": datetime(2026, 8, 26, 23, 59, 59, tzinfo=TZ),
        }
        index_items = [
            {
                "title": "Edge AI Daily 早报（8月26日）",
                "source_url": "https://www.tmtpost.com/8116690.html",
                "published_at": "2026-08-26",
                "summary_basis": "Edge AI Daily 早报（8月26日）",
            }
        ]
        daily_html = "<blockquote>一、子条目标题不含日期</blockquote><p>完整摘要。</p>"
        with (
            mock.patch.object(HTML_INDEX, "fetch_generic_html", return_value=index_items),
            mock.patch.object(HTML_INDEX, "fetch_text", return_value=daily_html),
        ):
            items = HTML_INDEX.fetch_tmtpost(source, window)

        self.assertEqual([item["title"] for item in items], ["子条目标题不含日期"])
        self.assertFalse(MODULE.is_noise_entry(items[0], "tmtpost-edge-ai-daily", window))

    def test_exact_date_without_matching_daily_returns_no_generic_links(self) -> None:
        source = {"url": "https://www.tmtpost.com/user/7944025"}
        window = {"date": "2026-08-26"}
        stale_items = [
            {
                "title": "Edge AI Daily 早报（8月25日）",
                "source_url": "https://www.tmtpost.com/8115451.html",
                "published_at": "2026-08-26",
                "summary_basis": "Edge AI Daily 早报（8月25日）",
            }
        ]
        with mock.patch.object(HTML_INDEX, "fetch_generic_html", return_value=stale_items):
            self.assertEqual(HTML_INDEX.fetch_tmtpost(source, window), [])

    def test_rolling_window_parses_available_dailies_without_page_chrome(self) -> None:
        source = {"url": "https://www.tmtpost.com/user/7944025"}
        window = {
            "start": datetime(2026, 8, 29, 0, 30, tzinfo=TZ),
            "end": datetime(2026, 9, 1, 0, 30, tzinfo=TZ),
        }
        index_items = [
            {
                "title": "Edge AI Daily 早报（8月31日）",
                "source_url": "https://www.tmtpost.com/8122304.html",
                "published_at": "2026-09-01T00:30:00+08:00",
                "summary_basis": "Edge AI Daily 早报（8月31日）",
            },
            {
                "title": "Edge AI Daily 早报（8月29日）",
                "source_url": "https://www.tmtpost.com/8121473.html",
                "published_at": "2026-09-01T00:30:00+08:00",
                "summary_basis": "Edge AI Daily 早报（8月29日）",
            },
            {
                "title": "涉企侵权举报须知",
                "source_url": "https://www.tmtpost.com/about/reporting_notice",
                "published_at": "2026-09-01T00:30:00+08:00",
                "summary_basis": "涉企侵权举报须知",
            },
        ]
        daily_pages = {
            "https://www.tmtpost.com/8122304.html": (
                "<span>2026.08.31 08:20</span>"
                "<blockquote>一、8月31日新闻</blockquote><p>摘要。</p>"
            ),
            "https://www.tmtpost.com/8121473.html": (
                "<span>2026.08.29 08:23</span>"
                "<blockquote>一、8月29日新闻</blockquote><p>摘要。</p>"
            ),
        }
        with (
            mock.patch.object(HTML_INDEX, "fetch_generic_html", return_value=index_items),
            mock.patch.object(
                HTML_INDEX,
                "fetch_text",
                side_effect=lambda url: daily_pages[url],
            ),
        ):
            items = HTML_INDEX.fetch_tmtpost(source, window)

        self.assertEqual([item["title"] for item in items], ["8月31日新闻", "8月29日新闻"])
        self.assertEqual(items[0]["published_at"], "2026-08-31T08:20:00+08:00")
        self.assertEqual(items[1]["published_at"], "2026-08-29T08:23:00+08:00")
        self.assertNotIn("reporting_notice", {item["source_url"] for item in items})


if __name__ == "__main__":
    unittest.main()
