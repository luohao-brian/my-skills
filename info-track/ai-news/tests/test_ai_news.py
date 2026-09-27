from __future__ import annotations

import argparse
import gzip
import importlib.util
import io
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

    def test_generic_html_falls_back_when_times_run_out(self) -> None:
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
        self.assertEqual(items[0]["published_at"], "2026-09-27T08:00:00+08:00")
        self.assertEqual(items[1]["published_at"], "2026-09-26")

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


class MaomuTimelineTests(unittest.TestCase):
    MAOMU_HTML = """
    <html><body>
      <div class="news-tag" style="margin:20px 0;"><span>今日 - 2026-09-27</span></div>
      <ul class="ant-timeline news-list hidden-sm-and-down">
        <li class="ant-timeline-item"><div class="ant-timeline-item-content">
          <div class="ant-row"><div class="ant-col ant-col-19">
            <div class="news-time"><span>08:53</span></div>
            <a class="dark:text-white" target="_blank" href="https://www.36kr.com/p/4000927879319685">
              <h3 class="title line-clamp-2">管住AI，成了一门新生意</h3>
              <div class="desc text-gray-500 line-clamp-2">三类玩家，掘金AI安全。</div>
              <div class="source-name text-gray-500">来源： <span>36氪</span></div>
            </a>
          </div></div>
        </div></li>
        <li class="ant-timeline-item"><div class="ant-timeline-item-content">
          <div class="ant-row"><div class="ant-col ant-col-19">
            <div class="news-time"><span>07:59</span></div>
            <a target="_blank" href="https://www.tmtpost.com/8153235.html">
              <h3 class="title line-clamp-2">Edge AI Daily 早报（9月27日）</h3>
              <div class="desc text-gray-500 line-clamp-2">OpenAI发布持久化智能体。</div>
              <div class="source-name text-gray-500">来源： <span>钛媒体</span></div>
            </a>
          </div></div>
        </div></li>
      </ul>
      <div class="news-tag" style="margin:20px 0;"><span>2026-09-26</span></div>
      <ul class="ant-timeline news-list hidden-sm-and-down">
        <li class="ant-timeline-item"><div class="ant-timeline-item-content">
          <div class="news-time"><span>23:44</span></div>
          <a target="_blank" href="https://www.ithome.com/1/007/444.htm">
            <h3 class="title line-clamp-2">Anthropic Claude 刷新物理学世界纪录</h3>
            <div class="desc text-gray-500 line-clamp-2">单挑基于杨振宁理论 9 圈难题。</div>
            <div class="source-name text-gray-500">来源： <span>IT之家</span></div>
          </a>
        </div></li>
      </ul>
      <a class="news-item" target="_blank" href="https://www.36kr.com/p/3991444838857731">
        <div class="news-day">6天前 输出token永久免费的旧闻</div>
      </a>
    </body></html>
    """

    def test_timeline_items_get_exact_datetimes(self) -> None:
        with mock.patch.object(HTML_INDEX, "fetch_text", return_value=self.MAOMU_HTML):
            items = HTML_INDEX.fetch_maomu({"url": "https://maomu.com/news"})

        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]["published_at"], "2026-09-27T08:53:00+08:00")
        self.assertEqual(items[0]["title"], "管住AI，成了一门新生意")
        self.assertEqual(items[0]["summary_basis"], "三类玩家，掘金AI安全。 来源： 36氪")
        self.assertEqual(items[2]["published_at"], "2026-09-26T23:44:00+08:00")

    def test_sidebar_day_ago_entries_are_excluded(self) -> None:
        with mock.patch.object(HTML_INDEX, "fetch_text", return_value=self.MAOMU_HTML):
            items = HTML_INDEX.fetch_maomu({"url": "https://maomu.com/news"})

        self.assertNotIn("3991444838857731", {item["source_url"] for item in items})

    def test_groups_without_iso_date_are_skipped(self) -> None:
        html = (
            '<html><body>'
            '<div class="news-tag"><span>昨日推荐</span></div>'
            '<div class="news-time"><span>12:00</span></div>'
            '<a href="https://example.com/x"><h3 class="title">没有日期的分组标题</h3></a>'
            '<div class="news-tag"><span>2026-09-27</span></div>'
            '<div class="news-time"><span>08:00</span></div>'
            '<a href="https://example.com/y"><h3 class="title">今天的热门新闻标题</h3></a>'
            "</body></html>"
        )
        with mock.patch.object(HTML_INDEX, "fetch_text", return_value=html):
            items = HTML_INDEX.fetch_maomu({"url": "https://maomu.com/news"})

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["published_at"], "2026-09-27T08:00:00+08:00")
        self.assertEqual(items[0]["source_url"], "https://example.com/y")


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
