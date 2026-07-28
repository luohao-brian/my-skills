#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Iterable


USER_AGENT = "my-skills-ai-oss-models/2.0"
WINDOW_DAYS = 7
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_REGISTRY_PATH = BASE_DIR / "references" / "model-registry.json"
PROJECT_REGISTRY_PATH = BASE_DIR / "references" / "reproducible-projects.json"
DATASET_REGISTRY_PATH = BASE_DIR / "references" / "dataset-registry.json"

DEFAULT_HF_API_BASES = ["https://huggingface.co", "https://hf-mirror.com"]
MODEL_EXPAND = [
    "cardData",
    "config",
    "createdAt",
    "downloads",
    "gguf",
    "lastModified",
    "library_name",
    "likes",
    "pipeline_tag",
    "safetensors",
    "tags",
    "trendingScore",
]

FLAGSHIP_ROLES = [
    "llm",
    "vlm",
    "image-generation",
    "video-generation",
    "audio-tts",
    "audio-stt",
    "ocr",
    "translation",
    "embedding",
    "robotics",
]
DERIVATIVE_FILTERS = ["gguf", "mlx", "quantized", "on-device", "merge", "finetune", "adapter"]
LOCAL_DEPLOYMENTS = {"gguf", "mlx", "quantized", "ollama-compatible", "on-device"}
DERIVATIVE_RELATIONS = {"adapter", "finetune", "merge", "quantized"}
LOCAL_QUERY_LIMIT = 200
LOCAL_REPORT_MAX = 20
LOCAL_PUBLISHER_MAX = 3
LOCAL_HOT_TRENDING = 4
LOCAL_HOT_DOWNLOADS = 2_000
LOCAL_HOT_LIKES = 20
LOCAL_BREAKOUT_TRENDING = 50
LOCAL_BREAKOUT_DOWNLOADS = 100_000
LOCAL_BREAKOUT_LIKES = 100
DATASET_HOT_TRENDING = 15
DATASET_HOT_DOWNLOADS = 1_000
DATASET_HOT_LIKES = 20
OWNER_QUERY_LIMIT = 100
NOTABLE_DISCOVERY_MIN = 8
NOTABLE_DISCOVERY_MAX = 12
NOTABLE_DATASET_MAX = 5
NOTABLE_OWNER_MAX = 2
CARD_EXCERPT_CHARS = 1_600
CARD_FETCH_WORKERS = 12

PIPELINE_MODALITIES: dict[str, dict[str, list[str]]] = {
    "text-generation": {"input": ["text"], "output": ["text"]},
    "image-text-to-text": {"input": ["text", "image"], "output": ["text"]},
    "image-to-text": {"input": ["image"], "output": ["text"]},
    "video-text-to-text": {"input": ["text", "video"], "output": ["text"]},
    "audio-text-to-text": {"input": ["text", "audio"], "output": ["text"]},
    "any-to-any": {
        "input": ["text", "image", "video", "audio"],
        "output": ["text", "image", "video", "audio"],
    },
    "text-to-image": {"input": ["text"], "output": ["image"]},
    "image-to-image": {"input": ["image"], "output": ["image"]},
    "text-to-video": {"input": ["text"], "output": ["video"]},
    "image-to-video": {"input": ["image"], "output": ["video"]},
    "video-to-video": {"input": ["video"], "output": ["video"]},
    "automatic-speech-recognition": {"input": ["audio"], "output": ["text"]},
    "text-to-speech": {"input": ["text"], "output": ["audio"]},
    "text-to-audio": {"input": ["text"], "output": ["audio"]},
    "translation": {"input": ["text"], "output": ["text"]},
    "sentence-similarity": {"input": ["text"], "output": ["text"]},
    "robotics": {"input": ["robotics"], "output": ["robotics"]},
}

CAPABILITY_TAGS = {
    "reasoning": "reasoning",
    "coding": "coding",
    "code": "coding",
    "tool-use": "tool-use",
    "function-calling": "tool-use",
    "function_calling": "tool-use",
    "ocr": "ocr",
    "document": "document",
    "document-understanding": "document",
    "translation": "translation",
    "text-to-speech": "tts",
    "automatic-speech-recognition": "stt",
    "sentence-similarity": "embedding",
}

MOE_CONFIG_KEYS = {"num_experts", "num_experts_per_tok", "num_local_experts", "n_routed_experts"}
BASE_MODEL_RELATIONS = {"adapter", "finetune", "merge", "quantized"}
DATA_ROLES = {"raw-data", "pretrain-data", "sft-data", "preference-data", "eval-dataset"}
TRAINING_ROLES = {"data-pipeline", "tokenizer", "training-recipe", "training-config"}
MODEL_ROLES = {
    "intermediate-checkpoint",
    "base-checkpoint",
    "sft-checkpoint",
    "reward-model",
    "aligned-checkpoint",
}
EVAL_ROLES = {"eval-dataset", "eval-harness", "eval-results"}
ARTIFACT_ROLES = {
    "raw-data",
    "pretrain-data",
    "data-pipeline",
    "tokenizer",
    "training-recipe",
    "training-config",
    "intermediate-checkpoint",
    "base-checkpoint",
    "sft-data",
    "sft-checkpoint",
    "preference-data",
    "reward-model",
    "aligned-checkpoint",
    "eval-dataset",
    "eval-harness",
    "eval-results",
    "deployment-artifact",
}
OPENNESS_LEVELS = {"weights-only", "partial-artifacts", "reproducible", "unknown"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_registries(
    models: dict[str, Any],
    projects: dict[str, Any],
    datasets: dict[str, Any],
) -> None:
    family_ids = {str(entry["id"]) for entry in models.get("families", [])}
    for entry in models.get("families", []):
        if entry.get("openness") not in OPENNESS_LEVELS:
            raise ValueError(f"invalid openness for family {entry.get('id')}")
    seen_models: set[str] = set()
    for role, entries in models.get("flagship_models", {}).items():
        if role not in FLAGSHIP_ROLES:
            raise ValueError(f"invalid flagship role: {role}")
        for entry in entries:
            model_id = str(entry["id"])
            if model_id in seen_models:
                raise ValueError(f"duplicate registered model: {model_id}")
            if entry.get("family") not in family_ids:
                raise ValueError(f"unknown family for model {model_id}")
            seen_models.add(model_id)
    for entry in models.get("local_models", []):
        model_id = str(entry["id"])
        if model_id in seen_models:
            raise ValueError(f"duplicate registered model: {model_id}")
        if entry.get("role") not in FLAGSHIP_ROLES:
            raise ValueError(f"invalid local role for model {model_id}")
        if entry.get("family") not in family_ids:
            raise ValueError(f"unknown family for model {model_id}")
        seen_models.add(model_id)
    for project in projects.get("projects", []):
        if project.get("openness") not in OPENNESS_LEVELS:
            raise ValueError(f"invalid openness for project {project.get('id')}")
        for artifact in project.get("artifacts", []):
            if artifact.get("role") not in ARTIFACT_ROLES:
                raise ValueError(f"invalid artifact role in project {project.get('id')}")
    seen_datasets: set[str] = set()
    for entry in datasets.get("datasets", []):
        dataset_id = str(entry["id"])
        if dataset_id in seen_datasets:
            raise ValueError(f"duplicate registered dataset: {dataset_id}")
        if not set(entry.get("roles", [])) <= ARTIFACT_ROLES:
            raise ValueError(f"invalid dataset role for {dataset_id}")
        seen_datasets.add(dataset_id)


def hf_api_bases() -> list[str]:
    raw = os.getenv("AI_OSS_HF_API_BASES") or os.getenv("HF_API_BASES") or ""
    values = [value.strip().rstrip("/") for value in raw.split(",") if value.strip()]
    return values or DEFAULT_HF_API_BASES


def huggingface_token() -> str:
    return (os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN") or "").strip()


def is_huggingface_host(url: str) -> bool:
    hostname = (urllib.parse.urlparse(url).hostname or "").lower()
    return hostname == "huggingface.co" or hostname.endswith(".huggingface.co")


def fetch_text(
    url: str,
    timeout: int = 30,
    retries: int = 1,
    accept: str = "application/json",
) -> str:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            headers = {"User-Agent": USER_AGENT, "Accept": accept}
            token = huggingface_token()
            if token and is_huggingface_host(url):
                headers["Authorization"] = f"Bearer {token}"
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8", errors="replace")
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(attempt + 1)
    raise last_error or RuntimeError(f"failed to fetch {url}")


def hf_api(path: str, retries: int = 1) -> Any:
    parsed = urllib.parse.urlparse(path)
    suffix = urllib.parse.urlunparse(("", "", parsed.path, parsed.params, parsed.query, parsed.fragment))
    last_error: Exception | None = None
    for base in hf_api_bases():
        url = base + suffix
        try:
            return json.loads(fetch_text(url, retries=retries))
        except Exception as exc:
            last_error = exc
            if isinstance(exc, urllib.error.HTTPError) and exc.code == 404:
                break
    raise last_error or RuntimeError(f"failed to fetch Hugging Face API path {path}")


def expanded_model_query(params: list[tuple[str, str]]) -> str:
    query = list(params)
    query.extend(("expand", field) for field in MODEL_EXPAND)
    return "/api/models?" + urllib.parse.urlencode(query)


def fetch_model(model_id: str) -> dict[str, Any]:
    path = "/api/models/" + urllib.parse.quote(model_id, safe="/")
    query = urllib.parse.urlencode([("expand", field) for field in MODEL_EXPAND])
    row = hf_api(path + "?" + query, retries=0)
    if not isinstance(row, dict):
        raise TypeError(f"unexpected model response for {model_id}")
    return row


def fetch_dataset(dataset_id: str) -> dict[str, Any]:
    path = "/api/datasets/" + urllib.parse.quote(dataset_id, safe="/")
    row = hf_api(path, retries=0)
    if not isinstance(row, dict):
        raise TypeError(f"unexpected dataset response for {dataset_id}")
    return row


def fetch_many(
    ids: Iterable[str],
    fetcher: Callable[[str], dict[str, Any]],
    workers: int = 12,
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    unique_ids = list(dict.fromkeys(value for value in ids if value))

    def fetch_one(repo_id: str) -> tuple[str, dict[str, Any] | None, str | None]:
        try:
            return repo_id, fetcher(repo_id), None
        except Exception as exc:
            return repo_id, None, type(exc).__name__

    rows: dict[str, dict[str, Any]] = {}
    errors: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for repo_id, row, error in executor.map(fetch_one, unique_ids):
            if row is not None:
                rows[repo_id] = row
            elif error:
                errors[repo_id] = error
    return rows, errors


def parse_window(value: str | None) -> tuple[dt.date, dt.date]:
    if value:
        try:
            start = dt.date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("--date must use YYYY-MM-DD") from exc
        return start, start + dt.timedelta(days=WINDOW_DAYS - 1)
    end = dt.date.today()
    return end - dt.timedelta(days=WINDOW_DAYS - 1), end


def iso_date(value: Any) -> dt.date | None:
    text = str(value or "")
    if len(text) < 10:
        return None
    try:
        return dt.date.fromisoformat(text[:10])
    except ValueError:
        return None


def event_in_window(row: dict[str, Any], start: dt.date, end: dt.date) -> tuple[str, str] | None:
    created = iso_date(row.get("createdAt"))
    modified = iso_date(row.get("lastModified"))
    if created and start <= created <= end:
        return "published", created.isoformat()
    if modified and start <= modified <= end:
        return "repository-updated", modified.isoformat()
    return None


def lower_tags(row: dict[str, Any]) -> set[str]:
    return {str(tag).lower() for tag in row.get("tags", [])}


def base_model_links(row: dict[str, Any]) -> list[tuple[str, str]]:
    card = row.get("cardData") or {}
    relation = str(card.get("base_model_relation") or "")
    raw = card.get("base_model")
    values = raw if isinstance(raw, list) else [raw] if raw else []
    links: dict[str, str] = {str(value): relation for value in values if value}
    for raw_tag in row.get("tags", []):
        tag = str(raw_tag)
        if not tag.startswith("base_model:"):
            continue
        value = tag.removeprefix("base_model:")
        parts = value.split(":", 1)
        if len(parts) == 2 and parts[0] in BASE_MODEL_RELATIONS:
            links[parts[1]] = parts[0]
        elif value:
            links.setdefault(value, relation)
    return list(links.items())


def derivation_facets(row: dict[str, Any]) -> list[str]:
    return sorted(
        {
            relation
            for _, relation in base_model_links(row)
            if relation in DERIVATIVE_RELATIONS
        }
    )


def deployment_facets(row: dict[str, Any]) -> list[str]:
    tags = lower_tags(row)
    values: set[str] = set()
    for value in ["gguf", "mlx", "quantized", "vllm", "on-device"]:
        if value in tags:
            values.add(value)
    quantization_tags = {
        "4-bit",
        "8-bit",
        "awq",
        "bitsandbytes",
        "compressed-tensors",
        "fp8",
        "gptq",
        "modelopt",
        "mxfp4",
        "mxfp8",
        "nvfp4",
    }
    if tags & quantization_tags or (row.get("config") or {}).get("quantization_config"):
        values.add("quantized")
    if "gguf" in values:
        values.update({"quantized", "ollama-compatible"})
    return sorted(values)


def contains_config_key(value: Any, keys: set[str]) -> bool:
    if isinstance(value, dict):
        return any(key in keys or contains_config_key(child, keys) for key, child in value.items())
    if isinstance(value, list):
        return any(contains_config_key(child, keys) for child in value)
    return False


def architecture_facet(row: dict[str, Any]) -> str:
    tags = lower_tags(row)
    config = row.get("config") or {}
    if contains_config_key(config, MOE_CONFIG_KEYS) or "mixture-of-experts" in tags:
        return "moe"
    if "diffusers" in tags:
        return "diffusion"
    if config:
        return "dense"
    return "unknown"


def scale_facet(row: dict[str, Any], inherited: dict[str, Any] | None = None) -> dict[str, Any]:
    for candidate, inherited_flag in [(row, False), (inherited or {}, True)]:
        gguf = candidate.get("gguf") or {}
        safetensors = candidate.get("safetensors") or {}
        if isinstance(gguf.get("total"), int) and gguf["total"] > 0:
            return {"parameters": gguf["total"], "source": "gguf.total", "inherited": inherited_flag}
        if isinstance(safetensors.get("total"), int) and safetensors["total"] > 0:
            return {
                "parameters": safetensors["total"],
                "source": "safetensors.total",
                "inherited": inherited_flag,
            }
    return {"parameters": None, "source": "unknown", "inherited": False}


def capability_facets(row: dict[str, Any], override: dict[str, Any] | None = None) -> list[str]:
    values: set[str] = set()
    for tag in lower_tags(row):
        mapped = CAPABILITY_TAGS.get(tag)
        if mapped:
            values.add(mapped)
    pipeline = str(row.get("pipeline_tag") or "")
    if pipeline in CAPABILITY_TAGS:
        values.add(CAPABILITY_TAGS[pipeline])
    values.update(str(value) for value in (override or {}).get("capabilities", []))
    return sorted(values)


def stage_facets(row: dict[str, Any]) -> list[str]:
    tags = lower_tags(row)
    values = {value for value in ["base", "instruct", "chat", "finetune", "adapter"] if value in tags}
    values.update(relation for _, relation in base_model_links(row) if relation in {"adapter", "finetune"})
    return sorted(values)


def family_index(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(entry["id"]): entry for entry in registry.get("families", [])}


def flagship_index(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for role, entries in registry.get("flagship_models", {}).items():
        for entry in entries:
            result[str(entry["id"])] = {**entry, "role": role, "track": "flagship"}
    return result


def local_index(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(entry["id"]): {**entry, "track": "local"}
        for entry in registry.get("local_models", [])
    }


def model_metadata(
    row: dict[str, Any],
    record: dict[str, Any],
    registry: dict[str, Any],
    inherited: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model_id = str(row.get("id") or record.get("id") or "")
    family_id = str(record.get("family") or "")
    family = family_index(registry).get(family_id, {})
    override = (registry.get("model_overrides") or {}).get(model_id, {})
    deployment = sorted(set(deployment_facets(row)) | set(record.get("deployment", [])))
    canonical = record.get("canonical")
    if record.get("track") == "flagship":
        canonical = canonical or model_id
    return {
        "track": record.get("track"),
        "role": record.get("role"),
        "family": family_id or None,
        "canonical_model": canonical,
        "modalities": PIPELINE_MODALITIES.get(str(row.get("pipeline_tag") or ""), {"input": [], "output": []}),
        "capabilities": capability_facets(row, override),
        "deployment": deployment,
        "stage": stage_facets(row),
        "architecture": architecture_facet(row),
        "scale": scale_facet(row, inherited),
        "license": (row.get("cardData") or {}).get("license") or "unknown",
        "openness": {
            "level": family.get("openness", "unknown"),
            "evidence": family.get("evidence", []),
        },
        "base_models": [model for model, _ in base_model_links(row)],
        "derivation": derivation_facets(row),
        "pipeline_tag": row.get("pipeline_tag") or "",
        "downloads": row.get("downloads") or 0,
        "likes": row.get("likes") or 0,
        "trendingScore": row.get("trendingScore") or 0,
        "createdAt": row.get("createdAt") or "",
        "lastModified": row.get("lastModified") or "",
        "selection": record.get("selection", []),
        "pending_registry": bool(record.get("pending_registry")),
    }


ROLE_LABELS = {
    "llm": "旗舰 LLM",
    "vlm": "旗舰 VLM / 多模态模型",
    "image-generation": "图像生成模型",
    "video-generation": "视频生成模型",
    "audio-tts": "语音合成模型",
    "audio-stt": "语音识别模型",
    "ocr": "OCR 模型",
    "translation": "翻译模型",
    "embedding": "Embedding 模型",
    "robotics": "Robotics 模型",
}


def event_label(event: str) -> str:
    return "新发布" if event == "published" else "仓库更新"


def model_item(
    row: dict[str, Any],
    record: dict[str, Any],
    registry: dict[str, Any],
    event: tuple[str, str],
    inherited: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model_id = str(row.get("id") or record["id"])
    event_name, date = event
    role = str(record.get("role") or "")
    track = str(record.get("track") or "")
    if track == "local":
        canonical = str(record.get("canonical") or "")
        if canonical:
            summary = f"{model_id.split('/')[-1]} 是 {canonical} 的热门或重点本地部署版本，本窗口内发生{event_label(event_name)}。"
        else:
            summary = f"{model_id.split('/')[-1]} 是当前热门衍生或本地部署模型，本窗口内发生{event_label(event_name)}。"
    elif track == "discovery":
        summary = (
            f"{model_id.split('/')[-1]} 来自已登记官方发布者，"
            f"本窗口内发生{event_label(event_name)}，待纳入注册表确认。"
        )
    else:
        summary = f"{model_id.split('/')[-1]} 是白名单中的{ROLE_LABELS.get(role, role)}，本窗口内发生{event_label(event_name)}。"
    item = {
        "title": model_id,
        "url": f"https://huggingface.co/{model_id}",
        "summary": summary,
        "date": date,
        "event": event_name,
        "source": "Hugging Face Models",
        "category": role if track in {"flagship", "discovery"} else "local",
        "metadata": model_metadata(row, record, registry, inherited),
    }
    if track == "discovery":
        item["repo_type"] = "model"
    return item


def query_local_candidates() -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}

    def query(value: str) -> list[dict[str, Any]]:
        params = [
            ("filter", value),
            ("sort", "trendingScore"),
            ("direction", "-1"),
            ("limit", str(LOCAL_QUERY_LIMIT)),
        ]
        try:
            result = hf_api(expanded_model_query(params), retries=0)
        except Exception as exc:
            print(f"HF_LOCAL_QUERY_SKIPPED filter={value} reason={type(exc).__name__}", file=sys.stderr)
            return []
        return result if isinstance(result, list) else []

    with ThreadPoolExecutor(max_workers=len(DERIVATIVE_FILTERS)) as executor:
        results = executor.map(query, DERIVATIVE_FILTERS)
        for result in results:
            for row in result:
                model_id = str(row.get("id") or "")
                if model_id:
                    rows.setdefault(model_id, row)
    return list(rows.values())


def popularity_values(row: dict[str, Any]) -> tuple[float, int, int]:
    return (
        float(row.get("trendingScore") or 0),
        int(row.get("downloads") or 0),
        int(row.get("likes") or 0),
    )


def is_hot_local(row: dict[str, Any]) -> bool:
    trending, downloads, likes = popularity_values(row)
    return trending >= LOCAL_HOT_TRENDING and (
        downloads >= LOCAL_HOT_DOWNLOADS or likes >= LOCAL_HOT_LIKES
    )


def is_breakout_local(row: dict[str, Any]) -> bool:
    trending, downloads, likes = popularity_values(row)
    return (
        trending >= LOCAL_BREAKOUT_TRENDING
        and downloads >= LOCAL_BREAKOUT_DOWNLOADS
        and likes >= LOCAL_BREAKOUT_LIKES
    )


def model_role(row: dict[str, Any], default: str = "unknown") -> str:
    pipeline = str(row.get("pipeline_tag") or "")
    capabilities = set(capability_facets(row))
    if "ocr" in capabilities:
        return "ocr"
    if pipeline in {"image-text-to-text", "image-to-text", "video-text-to-text", "any-to-any"}:
        return "vlm"
    if pipeline in {"text-to-image", "image-to-image"}:
        return "image-generation"
    if pipeline in {"text-to-video", "image-to-video", "video-to-video"}:
        return "video-generation"
    if pipeline in {"automatic-speech-recognition", "audio-text-to-text"}:
        return "audio-stt"
    if pipeline in {"text-to-speech", "text-to-audio"}:
        return "audio-tts"
    if pipeline == "translation":
        return "translation"
    if pipeline == "sentence-similarity":
        return "embedding"
    if pipeline == "robotics":
        return "robotics"
    if pipeline == "text-generation":
        return "llm"
    return default


def find_local_root(
    row: dict[str, Any],
    root_ids: set[str],
    model_rows: dict[str, dict[str, Any]],
    max_depth: int = 3,
) -> tuple[str, dict[str, Any] | None] | None:
    frontier = [row]
    seen = {str(row.get("id") or "")}
    for _ in range(max_depth):
        next_frontier: list[dict[str, Any]] = []
        for current in frontier:
            for base_id, _ in base_model_links(current):
                if base_id in root_ids:
                    return base_id, model_rows.get(base_id)
                if not base_id or base_id in seen:
                    continue
                seen.add(base_id)
                base = model_rows.get(base_id)
                if base is None:
                    continue
                next_frontier.append(base)
        if not next_frontier:
            break
        frontier = next_frontier
    return None


def local_discovery_items(
    rows: list[dict[str, Any]],
    registry: dict[str, Any],
    model_rows: dict[str, dict[str, Any]],
    start: dt.date,
    end: dt.date,
    known_ids: set[str],
) -> list[dict[str, Any]]:
    flagship = flagship_index(registry)
    root_ids = set(flagship) | {str(value) for value in registry.get("local_roots", [])}
    trusted_publishers = {str(value) for value in registry.get("local_publishers", [])}
    items: list[dict[str, Any]] = []
    for row in rows:
        model_id = str(row.get("id") or "")
        if not model_id or model_id in known_ids:
            continue
        event = event_in_window(row, start, end)
        deployment = set(deployment_facets(row))
        derivation = set(derivation_facets(row))
        if (
            not event
            or not (deployment & LOCAL_DEPLOYMENTS or derivation & DERIVATIVE_RELATIONS)
            or not is_hot_local(row)
        ):
            continue
        matched = find_local_root(row, root_ids, model_rows)
        canonical, inherited = matched if matched else (None, None)
        publisher = model_id.split("/", 1)[0]
        trusted_publisher = publisher in trusted_publishers
        breakout = is_breakout_local(row)
        derivative = bool(derivation & DERIVATIVE_RELATIONS)
        if canonical is None and not trusted_publisher and not breakout and not derivative:
            continue
        base_record = flagship.get(str(canonical or ""), {})
        selection = ["hot"]
        if canonical:
            selection.append("flagship-lineage")
        if trusted_publisher:
            selection.append("trusted-publisher")
        if breakout:
            selection.append("breakout")
        if derivative:
            selection.append("derivative")
        record = {
            "id": model_id,
            "track": "local",
            "role": base_record.get("role") or model_role(row, default="llm"),
            "family": base_record.get("family"),
            "canonical": canonical,
            "selection": selection,
        }
        items.append(model_item(row, record, registry, event, inherited))
    return items


def query_owner_models(
    owners: list[str],
    start: dt.date,
) -> tuple[list[dict[str, Any]], dict[str, bool], dict[str, str]]:
    rows: dict[str, dict[str, Any]] = {}
    coverage: dict[str, bool] = {}
    errors: dict[str, str] = {}

    def query(owner: str) -> tuple[str, list[dict[str, Any]], str | None]:
        params = [
            ("author", owner),
            ("sort", "lastModified"),
            ("direction", "-1"),
            ("limit", str(OWNER_QUERY_LIMIT)),
        ]
        try:
            result = hf_api(expanded_model_query(params), retries=0)
        except Exception as exc:
            return owner, [], type(exc).__name__
        return owner, result if isinstance(result, list) else [], None

    with ThreadPoolExecutor(max_workers=min(12, len(owners) or 1)) as executor:
        results = executor.map(query, owners)
        for owner, result, error in results:
            if error:
                coverage[owner] = False
                errors[f"owner:{owner}"] = error
                continue
            for row in result:
                model_id = str(row.get("id") or "")
                if model_id:
                    rows.setdefault(model_id, row)
            oldest = min(
                (iso_date(row.get("lastModified")) for row in result),
                default=None,
                key=lambda value: value or dt.date.max,
            )
            coverage[owner] = len(result) < OWNER_QUERY_LIMIT or bool(oldest and oldest < start)
    return list(rows.values()), coverage, errors


def model_discovery_items(
    rows: list[dict[str, Any]],
    known_ids: set[str],
    registry: dict[str, Any],
    start: dt.date,
    end: dt.date,
) -> list[dict[str, Any]]:
    owner_family_candidates: dict[str, list[str]] = {}
    for entry in registry.get("families", []):
        owner_family_candidates.setdefault(str(entry["owner"]), []).append(str(entry["id"]))
    owner_families = {
        owner: family_ids[0]
        for owner, family_ids in owner_family_candidates.items()
        if len(family_ids) == 1
    }
    items: list[dict[str, Any]] = []
    for row in rows:
        model_id = str(row.get("id") or "")
        event = event_in_window(row, start, end)
        if not model_id or model_id in known_ids or not event:
            continue
        owner = model_id.split("/", 1)[0]
        record = {
            "id": model_id,
            "track": "discovery",
            "role": model_role(row),
            "family": owner_families.get(owner),
            "selection": ["trusted-publisher", "pending-registry"],
            "pending_registry": True,
        }
        items.append(
            model_item(row, record, registry, event)
        )
    return sorted(items, key=notable_model_sort_key, reverse=True)


def dataset_size(row: dict[str, Any]) -> str | None:
    for tag in row.get("tags", []):
        text = str(tag)
        if text.startswith("size_categories:"):
            return text.split(":", 1)[1]
    return None


def is_hot_dataset(row: dict[str, Any]) -> bool:
    trending, downloads, likes = popularity_values(row)
    return trending >= DATASET_HOT_TRENDING and (
        downloads >= DATASET_HOT_DOWNLOADS or likes >= DATASET_HOT_LIKES
    )


def query_trending_datasets() -> list[dict[str, Any]]:
    query = urllib.parse.urlencode(
        {"sort": "trendingScore", "direction": "-1", "limit": "100", "full": "true"}
    )
    result = hf_api("/api/datasets?" + query, retries=0)
    return result if isinstance(result, list) else []


def dataset_item(row: dict[str, Any], record: dict[str, Any], event: tuple[str, str]) -> dict[str, Any]:
    dataset_id = str(row.get("id") or record["id"])
    event_name, date = event
    uses = [str(value) for value in record.get("uses", [])]
    use_text = "、".join(uses) if uses else "开放数据"
    pending_registry = bool(record.get("pending_registry"))
    if pending_registry:
        summary = (
            f"{dataset_id.split('/')[-1]} 是本窗口命中的 HF 热门新数据集，"
            "用途和交付内容需结合 dataset card 确认，待纳入注册表。"
        )
    else:
        summary = f"{dataset_id.split('/')[-1]} 是白名单中的{use_text}数据集，本窗口内发生{event_label(event_name)}。"
    item = {
        "title": dataset_id,
        "url": f"https://huggingface.co/datasets/{dataset_id}",
        "summary": summary,
        "date": date,
        "event": event_name,
        "source": "Hugging Face Datasets",
        "category": "dataset",
        "metadata": {
            "uses": uses,
            "roles": record.get("roles", []),
            "related_models": record.get("related_models", []),
            "related_projects": record.get("related_projects", []),
            "size": dataset_size(row),
            "downloads": row.get("downloads") or 0,
            "likes": row.get("likes") or 0,
            "trendingScore": row.get("trendingScore") or 0,
            "createdAt": row.get("createdAt") or "",
            "lastModified": row.get("lastModified") or "",
            "selection": record.get("selection", []),
            "pending_registry": pending_registry,
        },
    }
    if pending_registry:
        item["repo_type"] = "dataset"
    return item


def new_dataset_items(
    rows: list[dict[str, Any]],
    known_ids: set[str],
    start: dt.date,
    end: dt.date,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for row in rows:
        dataset_id = str(row.get("id") or "")
        event = event_in_window(row, start, end)
        if not dataset_id or dataset_id in known_ids or not event or not is_hot_dataset(row):
            continue
        record = {
            "id": dataset_id,
            "selection": ["hot", "pending-registry"],
            "pending_registry": True,
        }
        items.append(dataset_item(row, record, event))
    return sorted(items, key=notable_dataset_sort_key, reverse=True)


def notable_model_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    metadata = item.get("metadata") or {}
    selection = metadata.get("selection") or []
    return (
        "trusted-publisher" in selection,
        item.get("event") == "published",
        int(metadata.get("trendingScore") or 0),
        int(metadata.get("likes") or 0),
        int(metadata.get("downloads") or 0),
        item.get("date", ""),
        item.get("title", ""),
    )


def notable_dataset_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    metadata = item.get("metadata") or {}
    return (
        int(metadata.get("trendingScore") or 0),
        item.get("event") == "published",
        item.get("date", ""),
        int(metadata.get("likes") or 0),
        int(metadata.get("downloads") or 0),
        item.get("title", ""),
    )


def select_diverse_models(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    ranked = sorted(items, key=notable_model_sort_key, reverse=True)
    selected: list[dict[str, Any]] = []
    selected_titles: set[str] = set()
    owner_counts: dict[str, int] = {}
    direction_counts: dict[str, int] = {}

    def add(item: dict[str, Any]) -> bool:
        title = str(item.get("title") or "")
        owner = title.split("/", 1)[0]
        direction = str(item.get("category") or "unknown")
        if not title or title in selected_titles or owner_counts.get(owner, 0) >= NOTABLE_OWNER_MAX:
            return False
        selected.append(item)
        selected_titles.add(title)
        owner_counts[owner] = owner_counts.get(owner, 0) + 1
        direction_counts[direction] = direction_counts.get(direction, 0) + 1
        return True

    for item in ranked:
        direction = str(item.get("category") or "unknown")
        if direction_counts.get(direction, 0) == 0:
            add(item)
        if len(selected) >= limit:
            return selected

    for item in ranked:
        direction = str(item.get("category") or "unknown")
        if direction_counts.get(direction, 0) < 3:
            add(item)
        if len(selected) >= limit:
            return selected

    for item in ranked:
        title = str(item.get("title") or "")
        if title and title not in selected_titles:
            selected.append(item)
            selected_titles.add(title)
        if len(selected) >= limit:
            break
    return selected


def select_notable_discoveries(
    models: list[dict[str, Any]],
    datasets: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    selected_datasets = sorted(datasets, key=notable_dataset_sort_key, reverse=True)[:NOTABLE_DATASET_MAX]
    model_limit = max(0, NOTABLE_DISCOVERY_MAX - len(selected_datasets))
    selected_models = select_diverse_models(models, model_limit)
    total = len(selected_models) + len(selected_datasets)
    if total < NOTABLE_DISCOVERY_MIN:
        missing = NOTABLE_DISCOVERY_MIN - total
        selected_titles = {str(item.get("title") or "") for item in selected_models}
        extra_models = [
            item
            for item in sorted(models, key=notable_model_sort_key, reverse=True)
            if str(item.get("title") or "") not in selected_titles
        ][:missing]
        selected_models.extend(extra_models)
    return {"models": selected_models, "datasets": selected_datasets}


def extract_card_excerpt(text: str) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            text = parts[2]
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    paragraphs: list[str] = []
    current: list[str] = []
    for raw_line in text.splitlines():
        line = html.unescape(raw_line).strip()
        if not line or line.startswith(("#", "|", "[!", "<")):
            if current:
                paragraph = " ".join(current)
                if len(paragraph) >= 60:
                    paragraphs.append(paragraph)
                current = []
            continue
        line = re.sub(r"^[-*+]\s+", "", line)
        line = re.sub(r"\s+", " ", line)
        if line:
            current.append(line)
    if current:
        paragraph = " ".join(current)
        if len(paragraph) >= 60:
            paragraphs.append(paragraph)
    paragraphs = [
        paragraph
        for paragraph in paragraphs
        if not re.search(r"\b(?:from\s+\w+\s+import|import\s+\w+)", paragraph)
    ]
    excerpt = "\n\n".join(paragraphs[:3]).strip()
    if len(excerpt) > CARD_EXCERPT_CHARS:
        excerpt = excerpt[:CARD_EXCERPT_CHARS].rsplit(" ", 1)[0].rstrip() + "…"
    return excerpt


def fetch_card(repo_id: str, repo_type: str) -> dict[str, Any]:
    prefix = "datasets/" if repo_type == "dataset" else ""
    quoted_id = urllib.parse.quote(repo_id, safe="/")
    card_url = f"https://huggingface.co/{prefix}{repo_id}/blob/main/README.md"
    last_error: Exception | None = None
    for base in hf_api_bases():
        raw_url = f"{base}/{prefix}{quoted_id}/raw/main/README.md"
        try:
            excerpt = extract_card_excerpt(
                fetch_text(raw_url, timeout=15, retries=0, accept="text/markdown,text/plain")
            )
            if excerpt:
                return {"url": card_url, "excerpt": excerpt, "ok": True}
        except Exception as exc:
            last_error = exc
    return {
        "url": card_url,
        "excerpt": "",
        "ok": False,
        "error": type(last_error).__name__ if last_error else "EmptyCard",
    }


def enrich_items_with_cards(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    copied = [{**item, "metadata": dict(item.get("metadata") or {})} for item in items]

    def enrich(item: dict[str, Any]) -> dict[str, Any]:
        repo_type = str(item.get("repo_type") or "model")
        item["metadata"]["card"] = fetch_card(str(item.get("title") or ""), repo_type)
        return item

    with ThreadPoolExecutor(max_workers=min(CARD_FETCH_WORKERS, len(copied) or 1)) as executor:
        return list(executor.map(enrich, copied))


def artifact_specs(projects: dict[str, Any]) -> tuple[list[str], list[str]]:
    models: list[str] = []
    datasets: list[str] = []
    for project in projects.get("projects", []):
        for artifact in project.get("artifacts", []):
            repo_type = artifact.get("repo_type")
            if repo_type == "model":
                models.append(str(artifact["id"]))
            elif repo_type == "dataset":
                datasets.append(str(artifact["id"]))
    return models, datasets


def project_coverage(project: dict[str, Any]) -> dict[str, bool]:
    roles = {str(artifact.get("role") or "") for artifact in project.get("artifacts", [])}
    return {
        "data": bool(roles & DATA_ROLES),
        "training": bool(roles & TRAINING_ROLES),
        "model": bool(roles & MODEL_ROLES),
        "evaluation": bool(roles & EVAL_ROLES),
        "deployment": "deployment-artifact" in roles,
    }


def project_items(
    registry: dict[str, Any],
    model_rows: dict[str, dict[str, Any]],
    dataset_rows: dict[str, dict[str, Any]],
    start: dt.date,
    end: dt.date,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for project in registry.get("projects", []):
        changed: list[dict[str, Any]] = []
        for artifact in project.get("artifacts", []):
            repo_type = artifact.get("repo_type")
            row = model_rows.get(str(artifact.get("id"))) if repo_type == "model" else dataset_rows.get(str(artifact.get("id"))) if repo_type == "dataset" else None
            if row is None:
                continue
            event = event_in_window(row, start, end)
            if not event:
                continue
            repo_id = str(artifact["id"])
            prefix = "datasets/" if repo_type == "dataset" else ""
            changed.append(
                {
                    "id": repo_id,
                    "repo_type": repo_type,
                    "role": artifact.get("role"),
                    "depends_on": artifact.get("depends_on", []),
                    "event": event[0],
                    "date": event[1],
                    "url": f"https://huggingface.co/{prefix}{repo_id}",
                }
            )
        if not changed:
            continue
        changed.sort(key=lambda item: (item["date"], item["id"]), reverse=True)
        roles = sorted({str(item["role"]) for item in changed})
        items.append(
            {
                "title": project["name"],
                "url": project["url"],
                "summary": f"{project['name']} 在本窗口内更新了 " + "、".join(roles) + " 交付件。",
                "date": changed[0]["date"],
                "event": "artifact-updated",
                "source": "Hugging Face",
                "category": "reproducible",
                "metadata": {
                    "project": project["id"],
                    "scope": project["scope"],
                    "openness": project["openness"],
                    "coverage": project_coverage(project),
                    "artifacts": changed,
                },
            }
        )
    return sorted(items, key=lambda item: (item["date"], item["title"]), reverse=True)


def sort_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (
            item.get("date", ""),
            int((item.get("metadata") or {}).get("trendingScore") or 0),
            item.get("title", ""),
        ),
        reverse=True,
    )


def sort_popular_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (
            "priority" in ((item.get("metadata") or {}).get("selection") or []),
            int((item.get("metadata") or {}).get("trendingScore") or 0),
            int((item.get("metadata") or {}).get("likes") or 0),
            int((item.get("metadata") or {}).get("downloads") or 0),
            item.get("date", ""),
            item.get("title", ""),
        ),
        reverse=True,
    )


def select_popular_derivatives(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sort_popular_items(items)
    selected: list[dict[str, Any]] = []
    selected_titles: set[str] = set()
    publisher_counts: dict[str, int] = {}

    def facets(item: dict[str, Any]) -> set[str]:
        metadata = item.get("metadata") or {}
        return set(metadata.get("deployment") or []) | set(metadata.get("derivation") or [])

    def add(item: dict[str, Any], enforce_publisher_cap: bool = True) -> bool:
        title = str(item.get("title") or "")
        publisher = title.split("/", 1)[0]
        if not title or title in selected_titles:
            return False
        if enforce_publisher_cap and publisher_counts.get(publisher, 0) >= LOCAL_PUBLISHER_MAX:
            return False
        selected.append(item)
        selected_titles.add(title)
        publisher_counts[publisher] = publisher_counts.get(publisher, 0) + 1
        return True

    for facet in ["merge", "finetune", "adapter", "gguf", "mlx", "on-device", "quantized"]:
        for item in ranked:
            if facet in facets(item) and add(item):
                break
        if len(selected) >= LOCAL_REPORT_MAX:
            return sort_popular_items(selected)

    for item in ranked:
        add(item)
        if len(selected) >= LOCAL_REPORT_MAX:
            return sort_popular_items(selected)

    for item in ranked:
        add(item, enforce_publisher_cap=False)
        if len(selected) >= LOCAL_REPORT_MAX:
            break
    return sort_popular_items(selected)


def source_status(rows: dict[str, Any], errors: dict[str, str], selected: int) -> dict[str, Any]:
    return {
        "ok": bool(rows) or not errors,
        "count": len(rows) + len(errors),
        "selected": selected,
        "errors": errors,
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect registered and notable Hugging Face model and dataset updates in a fixed 7-day window."
    )
    parser.add_argument("--date", help="Window start date, YYYY-MM-DD")
    parser.add_argument("--output", help="Write candidate JSON to this path; stdout when omitted")
    parser.add_argument("--stats", action="store_true", help="Print group counts to stderr")
    args = parser.parse_args()

    try:
        start, end = parse_window(args.date)
    except ValueError as exc:
        parser.error(str(exc))

    model_registry = load_json(MODEL_REGISTRY_PATH)
    project_registry = load_json(PROJECT_REGISTRY_PATH)
    dataset_registry = load_json(DATASET_REGISTRY_PATH)
    validate_registries(model_registry, project_registry, dataset_registry)
    flagship = flagship_index(model_registry)
    local = local_index(model_registry)
    project_model_ids, project_dataset_ids = artifact_specs(project_registry)
    dataset_records = {str(entry["id"]): entry for entry in dataset_registry.get("datasets", [])}
    owners = list(
        dict.fromkeys(str(entry["owner"]) for entry in model_registry.get("families", []))
    )

    with ThreadPoolExecutor(max_workers=3) as executor:
        owner_future = executor.submit(query_owner_models, owners, start)
        local_future = executor.submit(query_local_candidates)
        dataset_future = executor.submit(query_trending_datasets)
        owner_rows_list, owner_coverage, owner_errors = owner_future.result()
        local_candidates = local_future.result()
        trending_datasets = dataset_future.result()

    cached_model_rows = {
        str(row.get("id") or ""): row
        for row in owner_rows_list + local_candidates
        if row.get("id")
    }
    relevant_model_ids = list(flagship) + list(local) + project_model_ids
    requested_model_ids: list[str] = []
    for model_id in dict.fromkeys(relevant_model_ids):
        if model_id in cached_model_rows:
            continue
        owner = model_id.split("/", 1)[0]
        if owner_coverage.get(owner) is True:
            continue
        requested_model_ids.append(model_id)

    trending_dataset_rows = {
        str(row.get("id") or ""): row
        for row in trending_datasets
        if row.get("id")
    }
    requested_dataset_ids = [
        dataset_id
        for dataset_id in dict.fromkeys(list(dataset_records) + project_dataset_ids)
        if dataset_id not in trending_dataset_rows
    ]

    with ThreadPoolExecutor(max_workers=2) as executor:
        model_future = executor.submit(fetch_many, requested_model_ids, fetch_model)
        dataset_exact_future = executor.submit(fetch_many, requested_dataset_ids, fetch_dataset)
        exact_model_rows, exact_model_errors = model_future.result()
        exact_dataset_rows, dataset_errors = dataset_exact_future.result()

    model_rows = {**cached_model_rows, **exact_model_rows}
    dataset_rows = {**trending_dataset_rows, **exact_dataset_rows}
    model_errors = {**owner_errors, **exact_model_errors}

    flagship_groups: dict[str, list[dict[str, Any]]] = {role: [] for role in FLAGSHIP_ROLES}
    for model_id, record in flagship.items():
        row = model_rows.get(model_id)
        event = event_in_window(row or {}, start, end)
        if row is not None and event:
            flagship_groups[record["role"]].append(model_item(row, record, model_registry, event))

    local_items: list[dict[str, Any]] = []
    for model_id, record in local.items():
        row = model_rows.get(model_id)
        event = event_in_window(row or {}, start, end)
        priority = bool(record.get("priority", True))
        if row is None or not event or not is_hot_local(row):
            continue
        inherited = model_rows.get(str(record.get("canonical") or ""))
        selection = (["priority"] if priority else []) + (["hot"] if is_hot_local(row) else [])
        local_items.append(model_item(row, {**record, "selection": selection}, model_registry, event, inherited))

    known_ids = set(flagship) | set(local)
    local_items.extend(
        local_discovery_items(local_candidates, model_registry, model_rows, start, end, known_ids)
    )
    local_items = list({item["title"]: item for item in local_items}.values())

    dataset_items: list[dict[str, Any]] = []
    for dataset_id, record in dataset_records.items():
        row = trending_dataset_rows.get(dataset_id) or dataset_rows.get(dataset_id)
        event = event_in_window(row or {}, start, end)
        priority = bool(record.get("priority"))
        if row is not None and event and is_hot_dataset(row):
            selection = (["priority"] if priority else []) + (["hot"] if is_hot_dataset(row) else [])
            dataset_items.append(dataset_item(row, {**record, "selection": selection}, event))

    reproducible_items = project_items(project_registry, model_rows, dataset_rows, start, end)
    known_dataset_ids = set(dataset_records)
    model_discoveries = model_discovery_items(
        owner_rows_list,
        known_ids | set(project_model_ids),
        model_registry,
        start,
        end,
    )
    dataset_discoveries = new_dataset_items(
        trending_datasets,
        known_dataset_ids | set(project_dataset_ids),
        start,
        end,
    )
    discoveries = sorted(
        model_discoveries + dataset_discoveries,
        key=lambda item: (item.get("date", ""), item.get("title", "")),
        reverse=True,
    )
    notable_discoveries = select_notable_discoveries(
        model_discoveries,
        dataset_discoveries,
    )

    flagship_groups = {role: sort_items(rows) for role, rows in flagship_groups.items()}
    local_items = select_popular_derivatives(local_items)
    dataset_items = sort_popular_items(dataset_items)
    flagship_groups = {
        role: enrich_items_with_cards(rows) if rows else []
        for role, rows in flagship_groups.items()
    }
    dataset_items = enrich_items_with_cards(dataset_items) if dataset_items else []
    notable_discoveries = {
        "models": enrich_items_with_cards(notable_discoveries["models"]),
        "datasets": enrich_items_with_cards(notable_discoveries["datasets"]),
    }
    flagship_count = sum(len(rows) for rows in flagship_groups.values())
    notable_model_count = len(notable_discoveries["models"])
    notable_dataset_count = len(notable_discoveries["datasets"])

    payload = {
        "kind": "ai-oss-models",
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "sources": {
            "huggingface_models": source_status(
                model_rows,
                model_errors,
                flagship_count + len(local_items) + notable_model_count,
            ),
            "huggingface_datasets": source_status(
                dataset_rows,
                dataset_errors,
                len(dataset_items) + notable_dataset_count,
            ),
        },
        "groups": {
            "flagship": flagship_groups,
            "local": local_items,
            "reproducible": reproducible_items,
            "datasets": dataset_items,
            "notable_discoveries": notable_discoveries,
        },
        "discoveries": discoveries,
    }
    emit_payload(payload, args.output)

    if args.stats:
        print(
            json.dumps(
                {
                    "window": payload["window"],
                    "flagship": {role: len(rows) for role, rows in flagship_groups.items()},
                    "local": len(local_items),
                    "reproducible": len(reproducible_items),
                    "datasets": len(dataset_items),
                    "notable_discoveries": {
                        "models": notable_model_count,
                        "datasets": notable_dataset_count,
                        "total": notable_model_count + notable_dataset_count,
                    },
                    "discoveries": len(discoveries),
                    "exact_model_queries": len(requested_model_ids),
                    "exact_dataset_queries": len(requested_dataset_ids),
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
