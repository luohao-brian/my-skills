from __future__ import annotations

import argparse
import gzip
import importlib.util
import io
import json
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
import editorial as EDITORIAL


TZ = timezone(timedelta(hours=8))


class AiNewsDiagnosticsTests(unittest.TestCase):
    def test_default_sources_exclude_hex2077_daily_digest(self) -> None:
        registry = json.loads((SCRIPT.parents[1] / "references" / "sources.json").read_text())
        self.assertNotIn("hex2077", {source["id"] for source in registry["sources"]})

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

    def test_editorial_groups_original_link_but_not_shared_digest(self) -> None:
        original = {"title": "Introducing a new model", "url": "https://example.com/model", "summary": "Model released", "source_id": "official", "source": "Official", "source_role": "official", "published_at": "2026-09-29T10:00:00+08:00"}
        aihot = {"title": "某公司发布新模型", "url": "https://aihot.news/items/1", "original_url": "https://example.com/model", "summary": "该公司发布模型", "source_id": "aihot", "source": "AIHOT", "source_role": "aggregator", "published_at": "2026-09-29T10:00:00+08:00"}
        digest_a = {"title": "Unrelated news A", "url": "https://digest.example/daily", "summary": "A", "source_id": "digest", "source": "Digest", "source_role": "aggregator", "published_at": "2026-09-29T10:00:00+08:00"}
        digest_b = {"title": "Unrelated news B", "url": "https://digest.example/daily", "summary": "B", "source_id": "digest", "source": "Digest", "source_role": "aggregator", "published_at": "2026-09-29T10:00:00+08:00"}
        aihot_digest_a = {**digest_a, "title": "Unrelated news C", "url": "https://aihot.news/items/a", "original_url": "https://digest.example/daily"}
        aihot_digest_b = {**digest_b, "title": "Unrelated news D", "url": "https://aihot.news/items/b", "original_url": "https://digest.example/daily"}
        doc = {"window": {"label": "test"}, "sources": {}, "candidates": [original, aihot, digest_a, digest_b, aihot_digest_a, aihot_digest_b]}
        prepared = EDITORIAL.prepare_document(doc)
        self.assertEqual(len(prepared["events"]), 5)
        self.assertEqual(sorted(len(e["members"]) for e in prepared["events"]), [1, 1, 1, 1, 2])
        singles = [e["event_id"] for e in prepared["events"] if len(e["members"]) == 1]
        merged = EDITORIAL.merge_reviewed_events(prepared, [singles[:2]])
        self.assertEqual(len(merged["events"]), 4)
        self.assertEqual(merged["group_links"][-1]["reason"], "manual_same_event")

    def test_bilingual_aggregator_titles_share_specific_anchors(self) -> None:
        english = {"title": "NVIDIA Kumo Tabular sets a new benchmark", "url": "https://feed.example/item", "source_role": "aggregator"}
        chinese = {"title": "NVIDIA 发布 Kumo Tabular 表格模型", "url": "https://aihot.news/items/kumo", "original_url": "https://feed.example/item", "source_role": "aggregator"}
        self.assertEqual(EDITORIAL.same_event(english, chinese), (True, "same_original_url_bilingual"))
        chinese["title"] = "NVIDIA 发布其他产品"
        self.assertEqual(EDITORIAL.same_event(english, chinese), (False, ""))

    def test_all_events_keeps_pending_and_puts_chinese_first(self) -> None:
        doc = {"window": {"label": "test"}, "events": [
            {"event_id": "en", "members": [{"title": "English release", "summary": "The company released a product.", "url": "https://example.com/en", "source": "English", "source_role": "media", "published_at": "2026-09-30T10:00:00+08:00"}], "review": {"decision": "pending", "display_summary": "The company released a product.", "display_summary_source_url": "https://example.com/en"}},
            {"event_id": "zh", "members": [{"title": "中文发布", "summary": "公司发布了一款产品。", "url": "https://example.com/zh", "source": "中文", "source_role": "aggregator", "published_at": "2026-09-29T10:00:00+08:00"}], "review": {"decision": "pending", "display_summary": "公司发布了一款产品。", "display_summary_source_url": "https://example.com/zh"}},
        ]}
        output = EDITORIAL.render_all_events(doc)
        self.assertTrue(output.startswith("# AI 新闻简报｜test\n"))
        self.assertIn("收录 2 条资讯", output)
        self.assertLess(output.index("\n### 中文发布"), output.index("\n### English release"))
        self.assertEqual(output.count("\n### "), 2)
        self.assertIn("[English](https://example.com/en)", output)
        self.assertEqual(output.count("\n摘要："), 2)
        self.assertNotIn("未逐项核验", output)

    def test_all_events_aligns_reviewed_and_pending_headings(self) -> None:
        item = {"title": "New model", "url": "https://example.com/model", "summary": "A model was released", "source_id": "official", "source": "Official", "source_role": "official", "published_at": "2026-09-29T10:00:00+08:00"}
        pending = {"title": "中文模型动态", "url": "https://example.com/product", "summary": "该公司介绍了模型更新。", "source_id": "media", "source": "Media", "source_role": "media", "published_at": "2026-09-29T09:00:00+08:00"}
        doc = EDITORIAL.prepare_document({"window": {"label": "test"}, "sources": {}, "candidates": [item, pending]})
        selected = next(e for e in doc["events"] if e["members"][0]["url"] == item["url"])
        selected["review"] = {"decision": "select", "category": "model_research", "title_zh": "发布新模型", "summary_zh": "原文称已发布新模型。", "verified_url": item["url"]}
        pending_event = next(e for e in doc["events"] if e is not selected)
        pending_event["review"].update({"display_summary": "该公司介绍了模型更新。", "display_summary_source_url": pending["url"]})
        output = EDITORIAL.render_all_events(doc)
        self.assertIn("\n## 🧠 模型 / 研究（2）\n\n### 发布新模型\n摘要：", output)
        self.assertIn("\n### 中文模型动态\n摘要：该公司介绍了模型更新。", output)
        self.assertEqual(output.count("\n## 🧠 模型 / 研究"), 1)
        self.assertEqual(output.count("\n### "), 2)

    def test_all_events_requires_a_complete_summary(self) -> None:
        doc = {"window": {"label": "test"}, "events": [
            {"event_id": "short", "members": [{"title": "Research update", "summary": "A clipped description...", "url": "https://example.com/item", "source": "Example", "published_at": "2026-09-30T10:00:00+08:00"}], "review": {"decision": "pending"}},
        ]}
        with self.assertRaisesRegex(ValueError, "source-backed editorial summaries required for: short"):
            EDITORIAL.render_all_events(doc)
        self.assertEqual(EDITORIAL.summary_queue(doc)[0]["sources"][0]["url"], "https://example.com/item")
        doc["events"][0]["review"]["display_summary"] = "The report describes a product update."
        with self.assertRaisesRegex(ValueError, "display_summary_source_url must be a member link"):
            EDITORIAL.render_all_events(doc)
        doc["events"][0]["review"]["display_summary_source_url"] = "https://example.com/item"
        self.assertIn("The report describes a product update.", EDITORIAL.render_all_events(doc))

    def test_summary_queue_reuses_one_collected_text_per_original_url(self) -> None:
        url = "https://example.com/research"
        doc = {"events": [{"event_id": "one", "members": [
            {"title": "Research", "url": url, "summary": "Short."},
            {"title": "研究", "url": "https://aihot.news/items/1", "original_url": url,
             "summary": "研究团队提出新方法，并公布了评估结果。"},
        ], "review": {"decision": "pending"}}]}
        item = EDITORIAL.summary_queue(doc)[0]
        self.assertEqual(len(item["sources"]), 1)
        self.assertEqual(item["sources"][0]["complete_excerpt"], "研究团队提出新方法，并公布了评估结果。")

    def test_all_events_requires_category_review_for_unknown_title(self) -> None:
        doc = {"window": {"label": "test"}, "events": [{
            "event_id": "unclear", "members": [{"title": "A cryptic headline", "url": "https://example.com/item"}],
            "review": {"decision": "pending", "display_summary": "文章讨论一款 AI 产品的实际使用体验。",
                       "display_summary_source_url": "https://example.com/item"},
        }]}
        with self.assertRaisesRegex(ValueError, "category review required for: unclear"):
            EDITORIAL.render_all_events(doc)
        doc["events"][0]["review"]["category"] = "products"
        self.assertIn("## 🚀 产品 / 应用（1）", EDITORIAL.render_all_events(doc))

    def test_fixed_category_cannot_hide_dynamic_category_hint(self) -> None:
        doc = {"window": {"label": "test"}, "events": [{
            "event_id": "benchmark", "members": [{"title": "Agent benchmark results", "url": "https://example.com/benchmark"}],
            "review": {"decision": "pending", "category": "model_research",
                       "display_summary": "研究团队发布智能体基准，并公布评测结果。",
                       "display_summary_source_url": "https://example.com/benchmark"},
        }]}
        self.assertEqual(EDITORIAL.category_review_queue(doc)[0]["suggested_category"], "evaluation")
        with self.assertRaisesRegex(ValueError, "dynamic category candidates require review"):
            EDITORIAL.render_all_events(doc)
        doc["events"][0]["review"]["category"] = "evaluation"
        self.assertIn("## 📊 评测 / 基准（1）", EDITORIAL.render_all_events(doc))
        doc["events"][0]["review"]["category"] = "model_research"
        doc["events"][0]["review"]["category_reviewed"] = True
        self.assertIn("## 🧠 模型 / 研究（1）", EDITORIAL.render_all_events(doc))

    def test_long_source_summary_is_not_clipped_into_a_fragment(self) -> None:
        source = "1." + "牛津大学宣布与 OpenAI 合作数字化馆藏，官方公告称便利研究者查阅；" * 3 + "报道还援引内部纪要。"
        result = EDITORIAL.short_summary(source)
        self.assertEqual(result, "")
        self.assertEqual(EDITORIAL.short_summary("arXiv:2609.31784v1 Announce Type: new Abstract: Open-weight models are often released, fine-tuned, and…"), "")
        self.assertEqual(EDITORIAL.short_summary("arXiv:2609.31784v1 Announce Type: new Abstract: The method compares model checkpoints. Longer notes follow..."), "The method compares model checkpoints.")

    def test_editorial_summary_keeps_two_complete_sentences(self) -> None:
        summary = "研究团队发布新方法，并公开评估结果。第二句说明该结果仅在所用测试集上成立。"
        self.assertEqual(EDITORIAL.editorial_summary(summary), summary)
        self.assertEqual(EDITORIAL.editorial_summary("研究团队介绍了方法。" * 25), "")
        self.assertEqual(EDITORIAL.editorial_summary("研究团队介绍了方法，结论尚未写完…"), "")

    def test_both_render_modes_keep_reviewed_second_sentence(self) -> None:
        summary = "研究团队发布新方法，并公开评估结果。第二句说明该结果仅在所用测试集上成立。"
        doc = {"window": {"label": "test"}, "events": [{
            "event_id": "study", "members": [{"title": "Study", "url": "https://example.com/study", "source": "Example"}],
            "review": {"decision": "select", "category": "model_research", "title_zh": "新方法",
                       "summary_zh": summary, "verified_url": "https://example.com/study"},
        }]}
        for output in (EDITORIAL.render_report(doc), EDITORIAL.render_all_events(doc)):
            self.assertIn("摘要：" + summary, output)

    def test_pending_title_keeps_project_identity_and_review_override(self) -> None:
        github = {"title": "逆向技能包登上开源趋势榜。", "url": "https://github.com/zhaoxuya520/reverse-skill"}
        event = {"members": [github], "review": {"decision": "pending"}}
        self.assertTrue(EDITORIAL._pending_title(event, github).startswith("reverse-skill："))
        event["review"]["display_title"] = "reverse-skill：逆向技能路由包"
        self.assertEqual(EDITORIAL._pending_title(event, github), "reverse-skill：逆向技能路由包")

    def test_pending_category_recognizes_science_and_safety_titles(self) -> None:
        for title, expected in (
            ("Anthropic Says It Discovered a Crispr-Like System. Now What?", "science"),
            ("OpenAI被曝排查数万起失控事件。", "safety_governance"),
            ("AI工程学习库星标近六万。", "opensource"),
        ):
            url = "https://github.com/rohitg00/ai-engineering-from-scratch" if "学习库" in title else "https://example.com/item"
            event = {"members": [{"title": title, "url": url}], "review": {"decision": "pending"}}
            self.assertEqual(EDITORIAL._pending_category(event)[0], expected)

    def test_reviewed_report_accepts_new_category_with_label(self) -> None:
        item = {"title": "Chip update", "url": "https://example.com/chip", "summary": "New chip", "source_id": "official", "source": "Official", "source_role": "official", "published_at": "2026-09-29T10:00:00+08:00"}
        doc = EDITORIAL.prepare_document({"window": {"label": "test"}, "sources": {}, "candidates": [item]})
        doc["events"][0]["review"] = {"decision": "select", "category": "compute", "category_label": "🧩 芯片 / 算力", "title_zh": "芯片更新", "summary_zh": "发布新芯片。", "verified_url": "https://example.com/chip"}
        report = EDITORIAL.render_report(doc)
        self.assertIn("## 🧩 芯片 / 算力", report)

    def test_report_needs_reviewed_evidence(self) -> None:
        item = {"title": "New model", "url": "https://example.com/model", "summary": "A model was released", "source_id": "official", "source": "Official", "source_role": "official", "published_at": "2026-09-29T10:00:00+08:00"}
        doc = {"window": {"label": "test"}, "sources": {}, "candidates": [item]}
        prepared = EDITORIAL.prepare_document(doc)
        with self.assertRaisesRegex(ValueError, "unreviewed events"):
            EDITORIAL.render_report(prepared)
        self.assertIn("简报样例", EDITORIAL.render_report(prepared, allow_partial=True))
        prepared["events"][0]["review"] = {"decision": "select", "category": "model_research", "title_zh": "发布新模型", "summary_zh": "原文称已发布新模型。", "verified_url": "https://example.com/model"}
        self.assertIn("发布新模型", EDITORIAL.render_report(prepared))
        prepared["events"][0]["review"]["verified_url"] = "https://invented.example/nope"
        with self.assertRaisesRegex(ValueError, "not a member link"):
            EDITORIAL.render_report(prepared)

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
