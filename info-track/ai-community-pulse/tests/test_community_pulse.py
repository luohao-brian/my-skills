from __future__ import annotations

import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "community_pulse.py"
SPEC = importlib.util.spec_from_file_location("community_pulse", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CommunityPulseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = MODULE.load_json(MODULE.CHANNELS_PATH)

    def test_linux_do_local_date_is_parsed_in_shanghai_timezone(self) -> None:
        parsed = MODULE.parse_date("8/16/2026, 9:34:53 PM")
        self.assertEqual(parsed.astimezone(timezone.utc).isoformat(), "2026-08-16T13:34:53+00:00")

    def test_undated_rows_require_explicit_snapshot_permission(self) -> None:
        start = datetime(2026, 8, 15, tzinfo=timezone.utc)
        end = datetime(2026, 8, 17, tzinfo=timezone.utc)
        self.assertFalse(MODULE.date_allowed(None, start, end))
        self.assertTrue(MODULE.date_allowed(None, start, end, allow_undated=True))

    def test_linux_do_created_field_reaches_candidate_date(self) -> None:
        item = MODULE.row_to_generic_candidate(
            {
                "title": "Local LLM inference engine update",
                "created": "8/16/2026, 9:34:53 PM",
                "url": "https://linux.do/t/topic/1",
            },
            self.registry,
            "linux-do",
            "latest",
        )
        self.assertEqual(item["date"], "2026-08-16T13:34:53+00:00")

    def test_content_score_beats_channel_preference(self) -> None:
        topic = MODULE.classify(
            "A new LLM benchmark for reasoning models",
            self.registry,
            preferred="agents",
        )
        self.assertEqual(topic, "models")

    def test_harness_and_inference_terms_fill_weak_topic_gaps(self) -> None:
        self.assertEqual(
            MODULE.classify("DeepSeek Harness desktop deployment", self.registry),
            "agents",
        )
        self.assertEqual(MODULE.classify("DSH desktop client", self.registry), "agents")
        self.assertEqual(
            MODULE.classify("Local LLM inference engine adds speculative decoding", self.registry),
            "systems",
        )

    def test_producthunt_category_rows_obey_window(self) -> None:
        registry = dict(self.registry)
        registry["producthunt"] = [
            {"command": "posts", "channel": "ai-agents", "topic": "agents"}
        ]
        rows = [
            {
                "name": "Recent Agent",
                "tagline": "AI agent harness",
                "date": "2026-08-16",
                "url": "https://www.producthunt.com/products/recent-agent",
            },
            {
                "name": "Old Agent",
                "tagline": "AI agent harness",
                "date": "2026-08-01",
                "url": "https://www.producthunt.com/products/old-agent",
            },
        ]
        with mock.patch.object(MODULE, "opencli", return_value=rows):
            selected, raw = MODULE.collect_opencli_public(
                registry,
                "producthunt",
                datetime(2026, 8, 15, tzinfo=timezone.utc),
                datetime(2026, 8, 17, tzinfo=timezone.utc),
            )
        self.assertEqual(raw, 2)
        self.assertEqual([row["title"] for row in selected], ["Recent Agent"])

    def test_lesswrong_rss_preserves_date_and_deduplicates_later(self) -> None:
        registry = dict(self.registry)
        registry["lesswrong"] = [
            {"channel": "frontpage", "url": "https://www.lesswrong.com/feed.xml?view=frontpage"}
        ]
        payload = b"""<?xml version='1.0'?>
        <rss><channel><item>
          <title>New LLM benchmark</title>
          <link>https://www.lesswrong.com/posts/example/new-llm-benchmark</link>
          <description>A reasoning model evaluation.</description>
          <pubDate>Sun, 16 Aug 2026 12:00:00 GMT</pubDate>
        </item></channel></rss>"""
        with mock.patch.object(MODULE, "http_bytes", return_value=payload):
            selected, raw = MODULE.collect_lesswrong(
                registry,
                datetime(2026, 8, 15, tzinfo=timezone.utc),
                datetime(2026, 8, 17, tzinfo=timezone.utc),
            )
        self.assertEqual(raw, 1)
        self.assertEqual(selected[0]["source"], "lesswrong")
        self.assertEqual(selected[0]["date"], "2026-08-16T12:00:00+00:00")

    def test_source_diagnostics_use_deduplicated_candidates(self) -> None:
        statuses = {"reddit": {"ok": True}}
        items = [
            {"source": "reddit", "channel": "a", "topic": "agents"},
            {"source": "reddit", "channel": "b", "topic": "systems"},
        ]
        MODULE.add_source_diagnostics(statuses, items, self.registry)
        self.assertEqual(statuses["reddit"]["channels_configured"], 35)
        self.assertEqual(statuses["reddit"]["deduplicated"], 2)
        self.assertEqual(statuses["reddit"]["channels_with_candidates"], 2)
        self.assertEqual(statuses["reddit"]["topics"]["agents"], 1)

    def test_explicit_proxy_is_process_scoped_and_enables_node_fetch(self) -> None:
        with (
            mock.patch.dict(MODULE.os.environ, {"NODE_OPTIONS": "--trace-warnings"}, clear=True),
            mock.patch.object(MODULE.urllib.request, "install_opener") as install_opener,
        ):
            MODULE.configure_proxy(
                "http://127.0.0.1:8080",
                "http://127.0.0.1:8080",
                "internal.example",
            )
            self.assertEqual(MODULE.os.environ["HTTP_PROXY"], "http://127.0.0.1:8080")
            self.assertEqual(MODULE.os.environ["HTTPS_PROXY"], "http://127.0.0.1:8080")
            self.assertEqual(
                MODULE.os.environ["NO_PROXY"],
                "localhost,127.0.0.1,::1,internal.example",
            )
            self.assertIn("--trace-warnings", MODULE.os.environ["NODE_OPTIONS"])
            self.assertIn("--use-env-proxy", MODULE.os.environ["NODE_OPTIONS"])
            self.assertEqual(MODULE.os.environ["NODE_NO_WARNINGS"], "1")
            install_opener.assert_called_once()


if __name__ == "__main__":
    unittest.main()
