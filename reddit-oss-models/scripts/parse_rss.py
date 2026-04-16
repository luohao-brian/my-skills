#!/usr/bin/env python3
"""
Reddit RSS parser for open-source model posts.

Reads one or more RSS feeds, filters for open-source model topics,
and prints either a short parse preview or a Chinese markdown summary.
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse
from urllib.request import urlopen
import xml.etree.ElementTree as ET


MODEL_KEYWORDS = [
    "model",
    "llm",
    "gpt",
    "llama",
    "mistral",
    "qwen",
    "deepseek",
    "yi",
    "baichuan",
    "chatglm",
    "gemma",
    "phi",
    "mixtral",
    "unsloth",
    "finetune",
    "training",
    "quantize",
    "quantization",
    "gguf",
    "awq",
    "gptq",
    "exl2",
    "hqq",
    "lora",
    "qlora",
    "local",
    "run locally",
    "inference",
    "benchmark",
    "performance",
    "release",
    "update",
    "new model",
]

EXCLUDE_KEYWORDS = [
    "help",
    "error",
    "bug",
    "crash",
    "stuck",
    "slow",
    "frustrated",
    "why is",
    "how do i",
    "beginner question",
    "basic question",
    "rant",
    "complaint",
    "issue with",
    "not working",
]

MODEL_PATTERNS = [
    r"(llama[-\s]?\d+(?:\.\d+)*)",
    r"(mistral[-\s]?\d+(?:\.\d+)*)",
    r"(qwen[-\s]?\d+(?:\.\d+)*)",
    r"(gemma[-\s]?\d+(?:\.\d+)*)",
    r"(phi[-\s]?\d+(?:\.\d+)*)",
    r"(yi[-\s]?\d+(?:\.\d+)*)",
    r"(deepseek[-\s]?\w+)",
]


def strip_html(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text or "")).strip()


def is_model_related(title: str, content: str) -> bool:
    text = f"{title} {content}".lower()
    has_model_keyword = any(keyword in text for keyword in MODEL_KEYWORDS)
    has_exclude_keyword = any(keyword in text for keyword in EXCLUDE_KEYWORDS)
    return has_model_keyword and not has_exclude_keyword


def extract_model_info(content: str) -> Dict[str, str | None]:
    info: Dict[str, str | None] = {
        "model_name": None,
        "lm_studio": None,
        "unsloth": None,
        "official_link": None,
    }

    content_lower = content.lower()

    for pattern in MODEL_PATTERNS:
        match = re.search(pattern, content_lower)
        if match:
            info["model_name"] = match.group(0).upper()
            break

    lm_studio_match = re.search(r"(https?://(?:www\.)?lmstudio\.ai/\S+)", content, re.IGNORECASE)
    if lm_studio_match:
        info["lm_studio"] = lm_studio_match.group(0)

    unsloth_match = re.search(r"(https?://(?:www\.)?unsloth\.ai/\S+)", content, re.IGNORECASE)
    if unsloth_match:
        info["unsloth"] = unsloth_match.group(0)

    hf_match = re.search(r"(https?://huggingface\.co/\S+)", content, re.IGNORECASE)
    if hf_match:
        info["official_link"] = hf_match.group(0)

    github_match = re.search(r"(https?://github\.com/\S+)", content, re.IGNORECASE)
    if github_match and not info["official_link"]:
        info["official_link"] = github_match.group(0)

    return info


def classify_stage(content: str) -> str:
    content_lower = content.lower()

    if any(keyword in content_lower for keyword in ["release", "released", "announcing", "new model"]):
        return "发布"
    if any(keyword in content_lower for keyword in ["adapter", "adapt", "support", "compatible"]):
        return "适配"
    if any(keyword in content_lower for keyword in ["quantize", "quantization", "gguf", "awq", "gptq"]):
        return "量化"
    if any(keyword in content_lower for keyword in ["train", "finetune", "lora", "qlora", "training"]):
        return "训练"
    if any(keyword in content_lower for keyword in ["run locally", "inference", "benchmark", "test"]):
        return "本地可用"
    return "讨论"


def detect_subreddit(feed_title: str, source: str) -> str:
    title = (feed_title or "").strip()
    if title:
        return title
    parsed = urlparse(source)
    match = re.search(r"/r/([^/]+)/", parsed.path)
    if match:
        return f"r/{match.group(1)}"
    return Path(source).name or "unknown"


def text_of(node: ET.Element | None, path: str) -> str:
    if node is None:
        return ""
    found = node.find(path)
    if found is None or found.text is None:
        return ""
    return found.text.strip()


def load_xml(source: str) -> ET.Element:
    parsed = urlparse(source)
    if parsed.scheme in ("http", "https"):
        with urlopen(source, timeout=30) as response:
            payload = response.read()
        return ET.fromstring(payload)
    return ET.parse(source).getroot()


def first_nonempty(*values: str) -> str:
    for value in values:
        if value:
            return value
    return ""


def parse_rss(source: str) -> List[Dict[str, object]]:
    root = load_xml(source)
    channel = root.find("./channel")
    subreddit = detect_subreddit(text_of(channel, "title"), source)
    posts: List[Dict[str, object]] = []

    for entry in root.findall("./channel/item"):
        title = text_of(entry, "title")
        content = strip_html(first_nonempty(text_of(entry, "description"), text_of(entry, "summary")))
        post = {
            "title": title,
            "subreddit": subreddit,
            "link": text_of(entry, "link"),
            "content": content,
            "score": 0,
            "comments": 0,
            "published": first_nonempty(text_of(entry, "pubDate"), text_of(entry, "published")),
        }

        if is_model_related(title, content):
            post["model_info"] = extract_model_info(content)
            post["stage"] = classify_stage(content)
            posts.append(post)

    return posts


def merge_posts(*groups: List[Dict[str, object]]) -> List[Dict[str, object]]:
    all_posts: List[Dict[str, object]] = []
    for group in groups:
        all_posts.extend(group)
    all_posts.sort(key=lambda item: (int(item.get("score", 0)), int(item.get("comments", 0))), reverse=True)
    return all_posts


def generate_summary(posts: List[Dict[str, object]]) -> str:
    if not posts:
        return "本周未找到与开源模型直接相关的热门帖子。"

    output = [f"# 本周开源模型热帖 Top {min(len(posts), 10)}\n"]

    for index, post in enumerate(posts[:10], 1):
        model_info = post["model_info"]
        assert isinstance(model_info, dict)

        content = str(post["content"])
        summary = content[:200] + "..." if len(content) > 200 else content
        output.append(f"\n## {index}. {post['title']}")
        output.append(f"\n**来源：** {post['subreddit']}")
        output.append(f"**链接：** {post['link']}")
        output.append(f"**热度：** {post['score']} 👍")
        output.append(f"**核心内容：** {summary.strip()}")
        output.append(f"**流程阶段：** {post['stage']}")

        entry_points = []
        if model_info.get("lm_studio"):
            entry_points.append(f"LM Studio: {model_info['lm_studio']}")
        if model_info.get("unsloth"):
            entry_points.append(f"Unsloth: {model_info['unsloth']}")
        if model_info.get("official_link"):
            entry_points.append(f"官方: {model_info['official_link']}")

        if entry_points:
            output.append("**可用入口：**")
            for entry_point in entry_points:
                output.append(f"  - {entry_point}")
        else:
            output.append("**可用入口：** 未确认")

        output.append("---")

    output.append("\n## 本周讨论主题总结")

    models_mentioned = sorted(
        {
            str(post["model_info"].get("model_name"))
            for post in posts
            if isinstance(post.get("model_info"), dict) and post["model_info"].get("model_name")
        }
    )
    if models_mentioned:
        output.append(f"\n**热门模型：** {', '.join(models_mentioned)}")

    stage_counts: Dict[str, int] = {}
    for post in posts:
        stage = str(post["stage"])
        stage_counts[stage] = stage_counts.get(stage, 0) + 1

    output.append("\n**讨论焦点：**")
    for stage, count in sorted(stage_counts.items(), key=lambda item: item[1], reverse=True):
        output.append(f"  - {stage}: {count} 条")

    output.append("\n## 可用入口整理\n")

    model_entries: Dict[str, Dict[str, str | None]] = {}
    for post in posts:
        model_info = post.get("model_info")
        if not isinstance(model_info, dict):
            continue
        model_name = str(model_info.get("model_name") or "其他")
        model_entries.setdefault(model_name, model_info)

    for model_name, info in sorted(model_entries.items()):
        output.append(f"\n### {model_name}")
        output.append(f"- LM Studio: {info['lm_studio'] or '未确认'}")
        output.append(f"- Unsloth: {info['unsloth'] or '未确认'}")
        output.append(f"- 官方: {info['official_link'] or '未确认'}")

    return "\n".join(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse Reddit RSS feeds for open-source model discussions.")
    parser.add_argument("sources", nargs="+", help="RSS URL or local XML file path")
    parser.add_argument("--summary", action="store_true", help="Print markdown summary instead of a short parse preview")
    args = parser.parse_args()

    groups = [parse_rss(source) for source in args.sources]
    posts = merge_posts(*groups)

    if args.summary:
        print(generate_summary(posts))
        return 0

    joined = ", ".join(args.sources)
    print(f"Parsed {len(posts)} model-related posts from {joined}")
    for post in posts[:5]:
        print(f"  - {str(post['title'])[:60]}... (score: {post['score']}, comments: {post['comments']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
