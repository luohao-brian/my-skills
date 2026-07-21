#!/usr/bin/env python3

from __future__ import annotations



import argparse

import datetime as dt

import email.utils

import html

import json

import os

import re

import sys

import time

import urllib.error

import urllib.parse

import urllib.request

import xml.etree.ElementTree as ET

from dataclasses import dataclass, field

from pathlib import Path

from typing import Any, Callable

from zoneinfo import ZoneInfo



USER_AGENT = "my-skills-info-track/1.0"

MISC = "-misc"

MODEL_CATEGORIES = [
    "开放权重旗舰 / reasoning",
    "本地推理 / 量化生态",
    "真开放 / 可复现训练",
    "小模型 / 专门模型",
    "多模态 / 图像视频",
]

TRUE_OPEN_ORGS = [
    "allenai",
    "EleutherAI",
    "swiss-ai",
    "LLM360",
    "tiiuae",
]

DEFAULT_HF_API_BASES = [
    "https://huggingface.co",
    "https://hf-mirror.com",
]

@dataclass
class Item:
    title: str
    url: str
    source: str
    date: str = ""
    description: str = ""
    category: str = ""
    score: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

def fetch_text(url: str, timeout: int = 30, retries: int = 2) -> str:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                charset = resp.headers.get_content_charset() or "utf-8"
                return resp.read().decode(charset, errors="replace")
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(1 + attempt)
    raise last_error or RuntimeError(f"failed to fetch {url}")

def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", value)
    value = re.sub(r"(?is)<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def text_from_html(value: str) -> str:
    return clean_text(value)

def normalize_url(value: str, base: str = "") -> str:
    value = html.unescape(value or "").strip().replace("\\/", "/")
    if not value:
        return ""
    return urllib.parse.urljoin(base, value)

def extract_first(pattern: str, text: str) -> str:
    match = re.search(pattern, text, re.S | re.I)
    return clean_text(match.group(1)) if match else ""

def parse_github_trending(limit: int = 10) -> list[Item]:
    page = fetch_text("https://github.com/trending?since=weekly", timeout=45)
    items: list[Item] = []
    for article in re.findall(r'<article class="Box-row">(.*?)</article>', page, re.S):
        head = re.search(r'<h2[^>]*>\s*<a[^>]+href="(/[^/]+/[^"/]+)"[^>]*>(.*?)</a>', article, re.S)
        if not head:
            continue
        repo = re.sub(r"\s*/\s*", "/", text_from_html(head.group(2)))
        desc = extract_first(r"<p[^>]*>(.*?)</p>", article)
        star_match = re.search(r"([0-9,]+)\s+stars this week", text_from_html(article))
        stars = int(star_match.group(1).replace(",", "")) if star_match else 0
        language = extract_first(r'<span itemprop="programmingLanguage">([^<]+)</span>', article)
        text = f"{repo} {desc}".lower()
        is_ai = any(
            key in text
            for key in [
                "ai",
                "agent",
                "llm",
                "claude",
                "codex",
                "cursor",
                "model",
                "diffusion",
                "qwen",
                "neural",
                "machine learning",
                "openai",
                "deep learning",
                "coding",
                "vibe",
            ]
        )
        if not is_ai:
            continue
        items.append(
            Item(
                title=repo,
                url=normalize_url(head.group(1), "https://github.com"),
                source="GitHub Trending",
                description=desc,
                score=stars,
                metadata={"stars_this_week": stars, "language": language, "raw_description": desc},
            )
        )
    items.sort(key=lambda item: item.score, reverse=True)
    items = items[:limit]
    enrich_github_summaries(items)
    return items

def enrich_github_summaries(items: list[Item]) -> None:
    system = (
        "你是AI开发者周报编辑。只基于输入metadata生成中文简介，不要编造未给出的功能。"
        "每条简介用1句话，40到80个中文字符，说明项目解决什么问题、适合什么场景。"
        '返回严格JSON：{"items":[{"id":1,"summary":"中文简介"}]}。不要解释。'
    )
    rows = [
        {
            "id": idx + 1,
            "repo": item.title,
            "description": item.metadata.get("raw_description") or item.description,
            "language": item.metadata.get("language", ""),
            "stars_this_week": item.metadata.get("stars_this_week", 0),
        }
        for idx, item in enumerate(items)
    ]
    summaries = summarize_with_provider(system, rows, batch_size=10)
    for idx, summary in summaries.items():
        if 0 <= idx < len(items):
            items[idx].description = summary

def fetch_reddit_signals() -> list[Item]:
    signals: list[Item] = []
    from parse_rss import parse_rss as parse_reddit_rss

    for sub in ["LocalLLaMA", "unsloth"]:
        try:
            rows = parse_reddit_rss(f"https://www.reddit.com/r/{sub}/top/.rss?t=week")
        except Exception as exc:
            print(f"REDDIT_RSS_SKIPPED source=r/{sub} reason={type(exc).__name__}", file=sys.stderr)
            continue
        for row in rows:
            signals.append(
                Item(
                    title=str(row.get("title") or ""),
                    url=str(row.get("link") or ""),
                    source=f"r/{sub}",
                    date=str(row.get("published") or "")[:10],
                    description=str(row.get("content") or ""),
                    score=int(row.get("score") or 0),
                    metadata={
                        "comments": int(row.get("comments") or 0),
                        "stage": row.get("stage") or "讨论",
                        "model_info": row.get("model_info") or {},
                    },
                )
            )
    signals.sort(key=lambda item: item.score, reverse=True)
    return signals

def hf_api_bases() -> list[str]:
    raw = os.getenv("AI_WEEKLY_HF_API_BASES") or os.getenv("HF_API_BASES") or ""
    values = [value.strip().rstrip("/") for value in raw.split(",") if value.strip()]
    return values or DEFAULT_HF_API_BASES

def hf_api_urls(path: str) -> list[str]:
    parsed = urllib.parse.urlparse(path)
    if parsed.scheme and parsed.netloc and parsed.netloc != "huggingface.co":
        return [path]
    if parsed.scheme and parsed.netloc:
        suffix = urllib.parse.urlunparse(("", "", parsed.path, parsed.params, parsed.query, parsed.fragment))
    else:
        suffix = path if path.startswith("/") else "/" + path
    return [base + suffix for base in hf_api_bases()]

def hf_api(path: str, retries: int = 3) -> list[dict[str, Any]]:
    last_error: Exception | None = None
    urls = hf_api_urls(path)
    for idx, url in enumerate(urls):
        try:
            return json.loads(fetch_text(url, timeout=60, retries=retries if idx == 0 else 1))
        except Exception as exc:
            last_error = exc
            if idx < len(urls) - 1:
                print(f"HF_API_FALLBACK from={url} reason={type(exc).__name__}", file=sys.stderr)
    raise last_error or RuntimeError(f"failed to fetch Hugging Face API path {path}")

def fetch_hf_models() -> list[dict[str, Any]]:
    seen: set[str] = set()
    models: list[dict[str, Any]] = []
    for row in hf_api("https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit=80"):
        model_id = row.get("id")
        if model_id and model_id not in seen:
            seen.add(model_id)
            models.append(row)
    for org in TRUE_OPEN_ORGS:
        url = f"https://huggingface.co/api/models?author={urllib.parse.quote(org)}&sort=lastModified&direction=-1&limit=20"
        try:
            rows = hf_api(url, retries=1)
        except Exception:
            continue
        for row in rows:
            model_id = row.get("id")
            if model_id and model_id not in seen:
                row["_supplement_org"] = org
                seen.add(model_id)
                models.append(row)
    return models

def fetch_hf_datasets(limit: int = 20) -> list[Item]:
    datasets = hf_api(f"https://huggingface.co/api/datasets?sort=trendingScore&direction=-1&limit={limit}")
    items: list[Item] = []
    for row in datasets:
        dataset_id = row.get("id") or ""
        tags = [str(tag) for tag in row.get("tags", [])]
        items.append(
            Item(
                title=dataset_id,
                url=f"https://huggingface.co/datasets/{dataset_id}",
                source="Hugging Face Datasets",
                description=dataset_summary_from_metadata(dataset_id, tags, row),
                score=int(row.get("trendingScore") or 0),
                metadata={
                    "downloads": row.get("downloads") or 0,
                    "likes": row.get("likes") or 0,
                    "lastModified": row.get("lastModified") or "",
                    "tags": tags[:25],
                },
            )
        )
    enrich_dataset_summaries(items)
    return items

def dataset_summary_from_metadata(dataset_id: str, tags: list[str], row: dict[str, Any]) -> str:
    tag_set = set(tags)
    languages = [tag.split(":", 1)[1] for tag in tags if tag.startswith("language:")]
    modalities = [tag.split(":", 1)[1] for tag in tags if tag.startswith("modality:")]
    formats = [tag.split(":", 1)[1] for tag in tags if tag.startswith("format:")]
    sizes = [tag.split(":", 1)[1] for tag in tags if tag.startswith("size_categories:")]
    licenses = [tag.split(":", 1)[1] for tag in tags if tag.startswith("license:")]
    desc_parts = [f"{dataset_id.split('/')[-1]} 是 Hugging Face 上的开源数据集"]
    if modalities:
        desc_parts.append("覆盖" + "、".join(modalities[:3]) + "模态")
    elif "task_categories:text-generation" in tag_set:
        desc_parts.append("面向文本生成任务")
    elif "task_categories:question-answering" in tag_set:
        desc_parts.append("面向问答任务")
    if languages:
        desc_parts.append("语言为 " + "、".join(languages[:3]))
    if formats:
        desc_parts.append("格式为 " + "、".join(formats[:2]))
    if sizes:
        desc_parts.append("规模 " + "、".join(sizes[:2]))
    if licenses:
        desc_parts.append("协议 " + "、".join(licenses[:2]))
    downloads = int(row.get("downloads") or 0)
    likes = int(row.get("likes") or 0)
    if downloads or likes:
        desc_parts.append(f"HF 当前下载 {downloads}、点赞 {likes}")
    return "；".join(desc_parts) + "。"

def enrich_dataset_summaries(items: list[Item]) -> None:
    if not items:
        return
    system = (
        "你是开源数据集周报编辑。只基于输入metadata生成中文简介，不要编造字段、样本内容或benchmark。"
        "每条简介用1句话，45到90个中文字符，说明数据集的模态、任务、格式、规模或为什么值得关注。"
        '返回严格JSON：{"items":[{"id":1,"summary":"中文简介"}]}。不要解释。'
    )
    rows = [
        {
            "id": idx + 1,
            "dataset": item.title,
            "metadata_summary": item.description,
            "downloads": item.metadata.get("downloads", 0),
            "likes": item.metadata.get("likes", 0),
            "trendingScore": item.score,
            "lastModified": item.metadata.get("lastModified", ""),
            "tags": item.metadata.get("tags", []),
        }
        for idx, item in enumerate(items)
    ]
    summaries = summarize_with_provider(system, rows, batch_size=20)
    for idx, summary in summaries.items():
        if 0 <= idx < len(items):
            items[idx].description = summary

def provider_config() -> tuple[str, str, str]:
    endpoint = os.getenv("LLM_ENDPOINT", os.getenv("AI_NEWS_ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/plan/v3")).rstrip("/")
    model = os.getenv("LLM_COMMON", os.getenv("AI_NEWS_CLASSIFY_MODEL", "deepseek-v4-flash"))
    api_key = os.getenv("LLM_API_KEY") or os.getenv("ARK_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
    return endpoint, model, api_key

def provider_json(payload: dict[str, Any], timeout: int = 160) -> dict[str, Any]:
    endpoint, _, api_key = provider_config()
    if not api_key:
        raise RuntimeError("missing LLM_API_KEY")
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

def parse_provider_json_content(content: str) -> dict[str, Any]:
    content = (content or "").strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.I).strip()
        content = re.sub(r"\s*```$", "", content).strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0))

def summarize_with_provider(system_prompt: str, rows: list[dict[str, Any]], batch_size: int = 20) -> dict[int, str]:
    _, model, api_key = provider_config()
    if not api_key:
        return {}
    summaries: dict[int, str] = {}
    for start in range(0, len(rows), batch_size):
        batch = rows[start:start + batch_size]
        batch_id_to_index = {int(row["id"]): start + offset for offset, row in enumerate(batch)}
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "请为以下条目生成中文简介：\n" + json.dumps(batch, ensure_ascii=False)},
            ],
            "temperature": 0.2,
        }
        try:
            data = provider_json(payload)
            content = data["choices"][0]["message"]["content"]
            parsed = parse_provider_json_content(content)
        except Exception as exc:
            print(f"SUMMARY_SKIPPED batch={start} reason={type(exc).__name__}", file=sys.stderr)
            continue
        for row in parsed.get("items", []):
            try:
                local_id = int(row.get("id"))
            except Exception:
                continue
            summary = clean_text(str(row.get("summary") or row.get("description") or row.get("简介") or row.get("zh_summary") or ""))
            target_index = batch_id_to_index.get(local_id)
            if target_index is None and 1 <= local_id <= len(batch):
                target_index = start + local_id - 1
            if summary and target_index is not None:
                summaries[target_index] = summary
        time.sleep(0.2)
    return summaries

def classify_with_provider(system_prompt: str, rows: list[dict[str, Any]], allowed: list[str], batch_size: int = 25) -> dict[int, str]:
    _, model, api_key = provider_config()
    if not api_key:
        return {}
    out: dict[int, str] = {}
    for start in range(0, len(rows), batch_size):
        batch = rows[start:start + batch_size]
        batch_id_to_index = {int(row["id"]): start + offset for offset, row in enumerate(batch)}
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "请分类以下条目：\n" + json.dumps(batch, ensure_ascii=False)},
            ],
            "temperature": 0,
        }
        try:
            data = provider_json(payload)
            content = data["choices"][0]["message"]["content"]
            parsed = parse_provider_json_content(content)
        except Exception as exc:
            print(f"CLASSIFY_SKIPPED batch={start} reason={type(exc).__name__}", file=sys.stderr)
            continue
        for row in parsed.get("items", []):
            try:
                local_id = int(row.get("id"))
            except Exception:
                continue
            category = str(row.get("category") or "").strip()
            if category not in allowed:
                category = MISC
            target_index = batch_id_to_index.get(local_id)
            if target_index is None and 1 <= local_id <= len(batch):
                target_index = start + local_id - 1
            if target_index is not None:
                out[target_index] = category
        time.sleep(0.2)
    return out

def classify_hf_models(models: list[dict[str, Any]]) -> None:
    system = (
        "你是Hugging Face开源模型分类器。分类只能是：开放权重旗舰 / reasoning、本地推理 / 量化生态、"
        "真开放 / 可复现训练、小模型 / 专门模型、多模态 / 图像视频、-misc。"
        "开放权重旗舰 / reasoning：大语言模型、MoE、reasoning、coding、agent旗舰。"
        "本地推理 / 量化生态：GGUF、quant、MLX、Ollama、推理加速、压缩。"
        "真开放 / 可复现训练：开放训练recipe、训练数据透明、OLMo、Eleuther、LLM360、SwissAI等。"
        "小模型 / 专门模型：小参数、翻译、OCR、医疗、生物、代码专项、嵌入等垂直模型。"
        "多模态 / 图像视频：VLM、图像、视频、语音、多模态生成或理解。"
        '返回严格JSON：{"items":[{"id":1,"category":"多模态 / 图像视频"}]}。不要解释。'
    )
    rows = [
        {
            "id": idx + 1,
            "model": row.get("id"),
            "pipeline_tag": row.get("pipeline_tag"),
            "likes": row.get("likes"),
            "downloads": row.get("downloads"),
            "trendingScore": row.get("trendingScore"),
            "tags": row.get("tags", [])[:30],
            "supplement_org": row.get("_supplement_org", ""),
        }
        for idx, row in enumerate(models)
    ]
    classified = classify_with_provider(system, rows, MODEL_CATEGORIES + [MISC], batch_size=20)
    for idx, category in classified.items():
        if 0 <= idx < len(models):
            models[idx]["weekly_category"] = category
    for row in models:
        model_id = str(row.get("id") or "")
        tags = " ".join(str(tag).lower() for tag in row.get("tags", []))
        pipeline = str(row.get("pipeline_tag") or "").lower()
        lower_id = model_id.lower()
        if any(key in lower_id for key in ["hrm-text", "deepseek-v4", "glm-5", "mimo-v", "ring-2", "kimi-k2", "nemotron-labs-diffusion"]):
            row["weekly_category"] = "开放权重旗舰 / reasoning"
        elif row.get("_supplement_org") or any(org.lower() in lower_id for org in ["allenai", "eleuther", "llm360", "swiss-ai", "tiiuae"]):
            row["weekly_category"] = "真开放 / 可复现训练"
        elif any(key in pipeline for key in ["text-to-video", "image-to-video", "video-to-video"]):
            row["weekly_category"] = "多模态 / 图像视频"
        elif "gguf" in tags or "quant" in tags or "mlx" in tags or "ollama" in tags or "4-bit" in tags or "8-bit" in tags:
            row["weekly_category"] = "本地推理 / 量化生态"
        elif any(key in pipeline for key in ["translation", "automatic-speech-recognition", "speaker-diarization", "text-to-speech"]) or any(key in tags for key in ["translation", "ocr", "embedding", "medical", "biology", "speaker-diarization", "text-to-speech", "tts"]):
            row["weekly_category"] = "小模型 / 专门模型"
        elif any(key in pipeline for key in ["text-to-video", "image", "video"]) or any(key in tags for key in ["multimodal", "image", "video", "vision"]):
            row["weekly_category"] = "多模态 / 图像视频"
        elif any(key in tags for key in ["text-generation", "reasoning", "conversational"]) or any(key in lower_id for key in ["deepseek", "qwen", "glm", "mimo", "nemotron"]):
            row["weekly_category"] = "开放权重旗舰 / reasoning"
        elif not row.get("weekly_category"):
            row["weekly_category"] = MISC

def score_model(row: dict[str, Any]) -> int:
    if row.get("_supplement_org"):
        modified = str(row.get("lastModified") or row.get("createdAt") or "")
        recent_bonus = 5_000_000 if modified.startswith("2026") else 0
        return recent_bonus + int(row.get("trendingScore") or 0) * 1_000_000 + min(int(row.get("downloads") or 0), 100_000)
    return int(row.get("trendingScore") or 0) * 1_000_000 + int(row.get("downloads") or 0)

def model_to_item(row: dict[str, Any]) -> Item:
    model_id = row.get("id") or ""
    tags = [str(tag) for tag in row.get("tags", [])]
    license_tag = next((tag for tag in tags if tag.startswith("license:")), "")
    pipeline = str(row.get("pipeline_tag") or "")
    pipeline_names = {
        "translation": "机器翻译",
        "text-generation": "文本生成",
        "image-to-text": "图像理解 / OCR",
        "text-to-speech": "语音合成",
        "automatic-speech-recognition": "语音识别",
        "speaker-diarization": "说话人分离",
        "text-to-image": "图像生成",
        "text-to-video": "视频生成",
        "image-to-video": "图生视频",
        "sentence-similarity": "文本向量 / 相似度",
        "feature-extraction": "特征提取 / embedding",
    }
    task_name = pipeline_names.get(pipeline, pipeline.replace("-", " ") if pipeline else "模型")
    desc_parts = [f"{model_id.split('/')[-1]} 是面向{task_name}场景的开源模型"]
    if row.get("_supplement_org"):
        desc_parts.append(f"来自 {row.get('_supplement_org')} 等真开放/可复现训练生态")
    if license_tag:
        desc_parts.append(f"协议为 {license_tag.removeprefix('license:')}")
    downloads = int(row.get("downloads") or 0)
    likes = int(row.get("likes") or 0)
    if downloads or likes:
        desc_parts.append(f"HF 当前下载 {downloads}、点赞 {likes}")
    return Item(
        title=model_id,
        url=f"https://huggingface.co/{model_id}",
        source="Hugging Face Models",
        description="；".join(desc_parts) + "。",
        score=int(row.get("trendingScore") or 0),
        metadata={
            "downloads": row.get("downloads") or 0,
            "likes": row.get("likes") or 0,
            "createdAt": row.get("createdAt") or "",
            "lastModified": row.get("lastModified") or "",
            "tags": tags[:20],
        },
    )

def enrich_model_summaries(model_groups: dict[str, list[Item]]) -> None:
    items = [item for group in model_groups.values() for item in group]
    if not items:
        return
    system = (
        "你是开源模型周报编辑。只基于输入metadata生成中文简介，不要编造参数规模、架构或benchmark。"
        "每条简介用1句话，45到90个中文字符，说明模型的任务类型、生态位置或为什么值得关注。"
        '返回严格JSON：{"items":[{"id":1,"summary":"中文简介"}]}。不要解释。'
    )
    rows = [
        {
            "id": idx + 1,
            "model": item.title,
            "category": item.category,
            "metadata_summary": item.description,
            "downloads": item.metadata.get("downloads", 0),
            "likes": item.metadata.get("likes", 0),
            "trendingScore": item.score,
            "lastModified": item.metadata.get("lastModified", ""),
            "createdAt": item.metadata.get("createdAt", ""),
            "tags": item.metadata.get("tags", []),
        }
        for idx, item in enumerate(items)
    ]
    summaries = summarize_with_provider(system, rows, batch_size=20)
    for idx, summary in summaries.items():
        if 0 <= idx < len(items):
            items[idx].description = summary

def item_to_dict(item: Item) -> dict[str, Any]:
    return {
        "title": item.title,
        "url": item.url,
        "summary": item.description,
        "date": item.date,
        "source": item.source,
        "category": item.category,
        "score": item.score,
        "metadata": item.metadata,
    }


def emit_payload(payload: dict[str, Any], output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output:
        path = Path(output).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(path)
    else:
        print(text, end="")


def safe_fetch(label: str, fetcher: Callable[[], Any], fallback: Any) -> Any:
    try:
        return fetcher()
    except Exception as exc:
        print(f"OPEN_SOURCE_FETCH_SKIPPED source={label} reason={type(exc).__name__}", file=sys.stderr)
        return fallback


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect weekly Reddit, GitHub and Hugging Face open-source AI updates.")
    parser.add_argument("--github-limit", type=int, default=10)
    parser.add_argument("--dataset-limit", type=int, default=20)
    parser.add_argument("--model-max", type=int, default=10, help="Maximum models per category")
    parser.add_argument("--reddit-limit", type=int, default=10)
    parser.add_argument("--output", help="Write candidate JSON to this path; stdout when omitted")
    parser.add_argument("--stats", action="store_true", help="Print group counts to stderr")
    args = parser.parse_args()
    if min(args.github_limit, args.dataset_limit, args.model_max, args.reddit_limit) < 0:
        parser.error("limits must be non-negative")
    github = safe_fetch("github-trending", lambda: parse_github_trending(args.github_limit), [])
    reddit = safe_fetch("reddit", fetch_reddit_signals, [])[:args.reddit_limit]
    models = safe_fetch("huggingface-models", fetch_hf_models, [])
    classify_hf_models(models)
    model_groups: dict[str, list[Item]] = {}
    for category in MODEL_CATEGORIES:
        rows = [row for row in models if row.get("weekly_category") == category]
        rows.sort(key=score_model, reverse=True)
        model_groups[category] = [model_to_item(row) for row in rows[:args.model_max]]
        for item in model_groups[category]:
            item.category = category
    enrich_model_summaries(model_groups)
    datasets = safe_fetch("huggingface-datasets", lambda: fetch_hf_datasets(args.dataset_limit), [])
    payload = {
        "kind": "ai-open-source-updates",
        "groups": {
            "reddit": [item_to_dict(item) for item in reddit],
            "github_trending": [item_to_dict(item) for item in github],
            "huggingface_models": {
                category: [item_to_dict(item) for item in rows]
                for category, rows in model_groups.items()
            },
            "huggingface_datasets": [item_to_dict(item) for item in datasets],
        },
    }
    emit_payload(payload, args.output)
    if args.stats:
        counts = {
            "reddit": len(reddit),
            "github_trending": len(github),
            "huggingface_models": sum(len(rows) for rows in model_groups.values()),
            "huggingface_datasets": len(datasets),
        }
        print(json.dumps(counts, ensure_ascii=False, sort_keys=True), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
