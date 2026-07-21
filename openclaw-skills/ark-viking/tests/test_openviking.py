from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import openviking  # noqa: E402


class FakeClient:
    def __init__(self) -> None:
        prefix = openviking.RSPRESS_ARTICLES_PREFIX
        self.root_one = prefix + "article-one.mdx"
        self.root_two = prefix + "article-two.md"
        self.title_one = self.root_one + "/文章一_-_极限与连续"
        self.title_two = self.root_two + "/文章二_-_连续函数"
        self.section_one = self.title_one + "/1._极限.md"
        self.section_two = self.title_two + "/2._连续.md"
        self.summary_one = self.title_one + "/.abstract.md"
        self.read_calls: list[str] = []

    def find(self, query: str, target_uri: str, limit: int) -> Any:
        del query, limit
        if target_uri == openviking.DEFAULT_TARGET:
            return {"result": {"resources": [
                {"uri": self.summary_one, "score": 0.9},
                {"uri": self.section_one, "score": 0.8},
                {"uri": self.section_two, "score": 0.7},
            ]}}
        if target_uri == self.root_one + "/":
            return {"result": {"resources": [
                {"uri": self.summary_one, "score": 0.91},
                {"uri": self.section_one, "score": 0.81},
            ]}}
        if target_uri == self.root_two + "/":
            return {"result": {"resources": [
                {"uri": self.section_two, "score": 0.71},
            ]}}
        return {"result": {"resources": []}}

    def ls(self, uri: str) -> Any:
        if uri == self.root_one + "/":
            return {"result": [{"uri": self.title_one, "isDir": True}]}
        if uri == self.root_two + "/":
            return {"result": [{"uri": self.title_two, "isDir": True}]}
        return {"result": []}

    def read(self, uri: str) -> Any:
        self.read_calls.append(uri)
        if uri == self.section_one:
            return {"result": {"content": "## 1. 极限\n\n极限章节正文"}}
        if uri == self.section_two:
            return {"result": {"content": "## 2. 连续\n\n连续章节正文"}}
        raise RuntimeError("not readable")


class RetrievalContractTests(unittest.TestCase):
    def test_retrieve_groups_by_article_and_separates_titles(self) -> None:
        client = FakeClient()
        result = openviking.retrieve_articles(
            client,
            "极限和连续",
            openviking.DEFAULT_TARGET,
            article_limit=2,
            sections_per_article=2,
            max_chars=1000,
            public_base_url="https://blog.example.com",
        )

        self.assertEqual(result["schema"], "openviking.article-retrieval/v1")
        self.assertEqual(len(result["articles"]), 2)
        first = result["articles"][0]
        self.assertEqual(set(first), {"relevance", "article_title", "article_url", "sections"})
        self.assertEqual(first["relevance"], 0.9)
        self.assertEqual(first["article_title"], "文章一 - 极限与连续")
        self.assertEqual(first["article_url"], "https://blog.example.com/auto/article-one.html")
        self.assertEqual(set(first["sections"][0]), {"relevance", "section_title", "content"})
        self.assertEqual(first["sections"][0]["section_title"], "1. 极限")
        self.assertIn("极限章节正文", first["sections"][0]["content"])
        self.assertNotIn(client.summary_one, client.read_calls)

    def test_limit_counts_distinct_articles(self) -> None:
        client = FakeClient()
        result = openviking.retrieve_articles(
            client,
            "极限和连续",
            openviking.DEFAULT_TARGET,
            article_limit=1,
            sections_per_article=1,
            max_chars=1000,
            public_base_url="https://blog.example.com",
        )
        self.assertEqual(len(result["articles"]), 1)
        self.assertEqual(result["articles"][0]["article_title"], "文章一 - 极限与连续")

    def test_rspress_url_uses_source_markdown_path(self) -> None:
        uri = openviking.RSPRESS_ARTICLES_PREFIX + "math/limits.mdx/文章标题/章节.md"
        metadata = openviking.rspress_metadata(uri, "https://blog.example.com/")
        self.assertEqual(metadata["source_path"], "math/limits.mdx")
        self.assertEqual(metadata["public_url"], "https://blog.example.com/auto/math/limits.html")

    def test_section_title_supports_nested_headings(self) -> None:
        self.assertEqual(openviking.section_title_from_text("## 连续的定义\n正文"), "连续的定义")
        self.assertEqual(openviking.section_title_from_text("### 结语\n正文"), "结语")


if __name__ == "__main__":
    unittest.main()
