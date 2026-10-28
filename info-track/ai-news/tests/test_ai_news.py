from __future__ import annotations

import argparse
import gzip
import importlib.util
import io
import json
import multiprocessing
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ai_news.py"
SPEC = importlib.util.spec_from_file_location("ai_news", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

from adapters import common as COMMON
from adapters import html_index as HTML_INDEX
from adapters import aihot as AIHOT
from adapters import rss as RSS


TZ = timezone(timedelta(hours=8))


class AiNewsDiagnosticsTests(unittest.TestCase):
    def test_added_rss_sources_and_36kr_pubdate(self) -> None:
        registry = json.loads((SCRIPT.parents[1] / "references" / "sources.json").read_text())
        sources = {source["id"]: source for source in registry["sources"]}
        self.assertEqual(sources["qbitai"]["url"], "https://www.qbitai.com/feed")
        self.assertEqual(sources["36kr"]["url"], "https://www.36kr.com/feed")

        published_at = "2026-10-28 13:58:42  +0800"
        expected = datetime(2026, 10, 28, 13, 58, 42, tzinfo=TZ)
        self.assertEqual(RSS._parse_datetime(published_at), expected)
        self.assertEqual(MODULE.parse_datetime(published_at), expected)

    def test_36kr_rss_filters_available_items_within_window(self) -> None:
        payload = """<rss><channel>
          <item><title>窗口内</title><link>https://36kr.com/p/1</link>
            <pubDate>2026-10-28 13:58:42  +0800</pubDate><description>来源摘要</description></item>
          <item><title>窗口外</title><link>https://36kr.com/p/2</link>
            <pubDate>2026-10-24 13:58:42  +0800</pubDate><description>旧摘要</description></item>
        </channel></rss>"""
        window = {
            "start": datetime(2026, 10, 25, tzinfo=TZ),
            "end": datetime(2026, 10, 28, 15, tzinfo=TZ),
        }
        source = {"url": "https://www.36kr.com/feed"}
        with mock.patch.object(RSS, "fetch_text", return_value=payload) as fetch:
            rows = RSS.fetch_rss(source, window)

        fetch.assert_called_once_with(source["url"])
        self.assertEqual([row["title"] for row in rows], ["窗口内"])

    def test_default_sources_exclude_hex2077_daily_digest(self) -> None:
        registry = json.loads((SCRIPT.parents[1] / "references" / "sources.json").read_text())
        self.assertNotIn("hex2077", {source["id"] for source in registry["sources"]})
        self.assertTrue(
            {"openai-news", "anthropic-news", "google-ai-blog", "deepmind-blog"}.isdisjoint(
                {source["id"] for source in registry["sources"]}
            )
        )

    def test_maomu_current_card_markup_keeps_article_time_and_source(self) -> None:
        html = """
        <article class="news-entry">
          <div class="news-entry-time"><time dateTime="2026-10-28T06:20:38.000Z">14:20</time></div>
          <div class="news-entry-body">
            <a class="news-entry-link" href="https://example.com/news/1">
              <div class="news-entry-copy"><h3>新的 AI 新闻标题</h3><p>来源提供的摘要。</p></div>
            </a>
            <div class="news-entry-meta"><span>来源</span><a href="https://example.com/news/1">原媒体</a></div>
          </div>
        </article>
        """
        with mock.patch.object(HTML_INDEX, "fetch_text", return_value=html):
            rows = HTML_INDEX.fetch_maomu({"url": "https://maomu.com/news"})

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "新的 AI 新闻标题")
        self.assertEqual(rows[0]["source_url"], "https://example.com/news/1")
        self.assertEqual(rows[0]["published_at"], "2026-10-28T06:20:38.000Z")
        self.assertEqual(rows[0]["summary_basis"], "来源提供的摘要。 原媒体")

    def test_maomu_missing_news_cards_reports_parser_failure(self) -> None:
        with mock.patch.object(HTML_INDEX, "fetch_text", return_value="<html><body>new layout</body></html>"):
            with self.assertRaisesRegex(ValueError, "cards not found"):
                HTML_INDEX.fetch_maomu({"url": "https://maomu.com/news"})

    def test_hex_parser_keeps_linked_words_in_summary(self) -> None:
        html = '<li><strong>安全研究新进展</strong>据<a href="https://example.com/report">报告</a>，报告披露了研究方法。</li>'
        rows = HTML_INDEX._parse_hex2077_article(html, "https://hex2077.dev/docs/2026-09/2026-09-29/", "2026-09-29")
        self.assertEqual(rows[0]["summary_basis"], "据报告，报告披露了研究方法")

    def test_aihot_pages_keep_original_attribution_and_window(self) -> None:
        start = datetime(2026, 9, 29, tzinfo=TZ)
        window = {"start": start, "end": start + timedelta(days=1)}
        source = {"url": "https://aihot.news/api/v1/items"}
        pages = [
            {"items": [{"id": "1", "title": "News one", "summary": "Summary one", "publishedAt": "2026-09-29T10:00:00+08:00", "links": {"aihot": "https://aihot.news/items/1", "original": "https://example.com/one"}, "source": {"name": "Original source"}}], "page": {"hasMore": True, "nextCursor": "next"}},
            {"items": [{"id": "2", "title": "Old news", "summary": "Old", "publishedAt": "2026-09-28T10:00:00+08:00", "links": {"aihot": "https://aihot.news/items/2", "original": "https://example.com/two"}}], "page": {"hasMore": False, "nextCursor": None}},
        ]
        with (mock.patch.object(AIHOT, "fetch_text", side_effect=[json.dumps(p) for p in pages]) as fetch,
              mock.patch.object(AIHOT, "datetime") as date):
            date.now.return_value = datetime(2026, 9, 30, tzinfo=TZ)
            date.fromisoformat.side_effect = datetime.fromisoformat
            rows = AIHOT.fetch_aihot(source, window)
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["original_url"], "https://example.com/one")
        self.assertEqual(rows[0]["source_url"], "https://aihot.news/items/1")

    def test_aihot_old_window_fails_explicitly(self) -> None:
        start = datetime(2026, 9, 1, tzinfo=TZ)
        with mock.patch.object(AIHOT, "datetime") as date:
            date.now.return_value = datetime(2026, 9, 30, tzinfo=TZ)
            with self.assertRaisesRegex(ValueError, "last 7 days"):
                AIHOT.fetch_aihot({"url": "https://aihot.news/api/v1/items"}, {"start": start, "end": start + timedelta(days=1)})
















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
        self.assertEqual(document["sources"]["official-feed"]["window_candidates"], 1)
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
        self.assertEqual(document["diagnostics"]["by_source_role"]["media"]["window_candidates"], 1)

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

    def test_render_folds_cross_source_exact_duplicates(self) -> None:
        document = {
            "window": {"label": "test"},
            "sources": {},
            "candidates": [
                {"title": "Story A", "url": "https://example.com/daily?utm_source=media", "summary": "Direct report."},
                {"title": "Story A", "url": "https://example.com/daily?utm_source=aggregator", "summary": "Aggregator copy."},
                {"title": "Story B", "url": "https://example.com/daily", "summary": "Separate story."},
            ],
        }

        rendered = MODULE.render_markdown(document)

        self.assertIn("新闻条目数：2", rendered)
        self.assertEqual(rendered.count("### Story A"), 1)
        self.assertIn("Direct report.", rendered)
        self.assertNotIn("Aggregator copy.", rendered)
        self.assertIn("### Story B", rendered)

    @unittest.skipUnless("fork" in multiprocessing.get_all_start_methods(), "requires forked source worker")
    def test_source_worker_returns_result_larger_than_pipe_buffer(self) -> None:
        rows = [{"summary_basis": "x" * 131_072}]
        source = {"id": "large-result", "timeout_seconds": 3}
        with (
            mock.patch.dict(MODULE.__dict__, {"__name__": "__main__"}),
            mock.patch.object(MODULE, "resolve_fetcher", return_value=lambda _source, _window: rows),
        ):
            actual, timeout = MODULE._fetch_source_with_timeout(None, source, {})

        self.assertEqual(actual, rows)
        self.assertEqual(timeout, 3)

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


class DatedAnchorParserTests(unittest.TestCase):
    ANTHROPIC_LIST_HTML = """
    <html><body><ul>
      <li><a class="PublicationList-module__listItem" href="/news/claude-discovers-novel-enzyme-system">
        <div class="PublicationList-module__meta">
          <time class="PublicationList-module__date">Sep 23, 2026</time>
          <span class="PublicationList-module__subject">Science</span>
        </div>
        <span class="PublicationList-module__title">Claude discovers a novel enzyme system</span>
      </a></li>
      <li><a class="PublicationList-module__listItem" href="/news/enterprise-frontier-safeguards">
        <div class="PublicationList-module__meta">
          <time class="PublicationList-module__date">Sep 18, 2026</time>
          <span class="PublicationList-module__subject">Announcements</span>
        </div>
        <span class="PublicationList-module__title">Enterprise frontier safeguards</span>
      </a></li>
      <li><a class="PublicationList-module__listItem" href="/news/undated-announcement">Undated announcement</a></li>
    </ul></body></html>
    """

    def test_anthropic_list_structure_yields_dated_items(self) -> None:
        with mock.patch.object(HTML_INDEX, "fetch_text", return_value=self.ANTHROPIC_LIST_HTML):
            items = HTML_INDEX.fetch_anthropic({"id": "anthropic-news", "url": "https://www.anthropic.com/news"})

        self.assertEqual(len(items), 2)
        first = items[0]
        self.assertEqual(first["title"], "Claude discovers a novel enzyme system")
        self.assertEqual(first["published_at"], "Sep 23, 2026")
        self.assertEqual(
            first["source_url"],
            "https://www.anthropic.com/news/claude-discovers-novel-enzyme-system",
        )
        self.assertEqual(first["summary_basis"], first["title"])

    def test_dated_anchor_parser_skips_items_without_dates(self) -> None:
        with mock.patch.object(HTML_INDEX, "fetch_text", return_value=self.ANTHROPIC_LIST_HTML):
            items = HTML_INDEX.fetch_dated_anchors(
                {"url": "https://www.anthropic.com/news"},
                href_prefix="/news/",
                date_patterns=(r"Sep\s+\d{1,2},\s+20\d{2}",),
            )

        self.assertEqual(len(items), 2)
        self.assertNotIn("undated-announcement", {item["source_url"] for item in items})

    def test_zero_parsed_links_trigger_markup_drift_warning(self) -> None:
        html = "<html><body>" + "".join(
            f'<a href="/news/item-{index}">undated item {index}</a>' for index in range(6)
        ) + "</body></html>"
        stderr = io.StringIO()
        with (
            mock.patch.object(HTML_INDEX, "fetch_text", return_value=html),
            mock.patch("sys.stderr", stderr),
        ):
            items = HTML_INDEX.fetch_dated_anchors(
                {"url": "https://www.anthropic.com/news"},
                href_prefix="/news/",
                source_id="anthropic-news",
            )

        self.assertEqual(items, [])
        self.assertIn("markup may have changed", stderr.getvalue())

    def test_generic_html_does_not_invent_dates_from_page_chrome(self) -> None:
        html = (
            "<html><body><time>2026-09-27T08:00:00+08:00</time>"
            '<a href="/first">first sufficiently long title</a>'
            '<a href="/second">second sufficiently long title</a>'
            "</body></html>"
        )
        with mock.patch.object(HTML_INDEX, "fetch_text", return_value=html):
            items = HTML_INDEX.fetch_generic_html(
                {"url": "https://example.com/news"}, {"date": "2026-09-26"}
            )

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["published_at"], "")
        self.assertEqual(items[1]["published_at"], "")

    def test_resolve_fetcher_is_kind_driven(self) -> None:
        self.assertIs(MODULE.resolve_fetcher({"id": "a", "kind": "rss"}), MODULE.FETCHERS["rss"])
        self.assertIs(
            MODULE.resolve_fetcher({"id": "b", "kind": "anthropic_list"}),
            MODULE.FETCHERS["anthropic_list"],
        )
        self.assertIs(
            MODULE.resolve_fetcher({"id": "c", "kind": "tmtpost_daily"}),
            MODULE.FETCHERS["tmtpost_daily"],
        )
        with self.assertRaises(ValueError):
            MODULE.resolve_fetcher({"id": "d", "kind": "nope"})

    def test_validate_sources_rejects_unknown_kind(self) -> None:
        registry = {
            "sources": [
                {"id": "x", "name": "X", "kind": "nope", "role": "media", "url": "https://example.com"}
            ]
        }
        with mock.patch.object(MODULE, "load_json", return_value=registry):
            errors = MODULE.validate_sources()

        self.assertTrue(any("unknown kind" in error for error in errors))


class FetchTextTests(unittest.TestCase):
    def test_fetch_text_decodes_gzip_content_encoding(self) -> None:
        body = b"<?xml version='1.0'?><rss><channel/></rss>"
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = gzip.compress(body)
        response.headers.get.return_value = "gzip"
        response.headers.get_content_charset.return_value = "utf-8"

        with mock.patch.object(COMMON, "urlopen", return_value=response):
            text = COMMON.fetch_text("https://example.com/feed.xml")

        self.assertEqual(text, body.decode())

    def test_fetch_text_keeps_identity_payload_untouched(self) -> None:
        body = b"<?xml version='1.0'?><rss><channel/></rss>"
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = body
        response.headers.get.return_value = ""
        response.headers.get_content_charset.return_value = "utf-8"

        with mock.patch.object(COMMON, "urlopen", return_value=response):
            text = COMMON.fetch_text("https://example.com/feed.xml")

        self.assertEqual(text, body.decode())


class Hex2077AdapterTests(unittest.TestCase):
    def test_daily_layouts_and_all_window_dates(self) -> None:
        source = {
            "url": "https://hex2077.dev/docs/",
            "date_url": "https://hex2077.dev/docs/{YYYY-MM}/{YYYY-MM-DD}/",
        }
        pages = {
            "2026-09-24": '<li><strong>新模型发布</strong>发布详情见<a href="https://example.com/new">原文</a>。</li>',
            "2026-09-23": '<li><p><strong>旧版布局</strong>详情见<a href="https://example.com/old">原文</a>。</p></li>',
        }

        def fetch(url: str) -> str:
            return pages[url.rstrip("/").rsplit("/", 1)[-1]]

        window = {
            "start": datetime(2026, 9, 23, tzinfo=TZ),
            "end": datetime(2026, 9, 24, tzinfo=TZ),
        }
        with mock.patch.object(HTML_INDEX, "fetch_text", side_effect=fetch):
            items = HTML_INDEX.fetch_hex2077(source, window)

        self.assertEqual(len(items), 2)
        self.assertEqual([item["published_at"] for item in items], ["2026-09-24", "2026-09-23"])
        self.assertEqual([item["source_url"] for item in items], ["https://example.com/new", "https://example.com/old"])


if __name__ == "__main__":
    unittest.main()
