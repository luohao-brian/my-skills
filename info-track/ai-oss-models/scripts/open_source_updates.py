#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Iterable


USER_AGENT = "my-skills-ai-oss-models/2.0"
WINDOW_DAYS = 7
LOCAL_NO_PROXY = ("localhost", "127.0.0.1", "::1")
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_REGISTRY_PATH = BASE_DIR / "references" / "model-registry.json"
ECOSYSTEM_ARCHITECTURE_PATH = BASE_DIR / "references" / "ecosystem-architecture.json"
DEVELOPMENT_BASELINES_PATH = BASE_DIR / "references" / "development-baselines.json"
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
    "decision",
    "media-conditioning",
    "media-enhancement",
    "image-generation",
    "video-generation",
    "audio-generation",
    "audio-tts",
    "audio-stt",
    "ocr",
    "translation",
    "embedding",
    "robotics",
]
DERIVATIVE_FILTERS = ["gguf", "mlx", "quantized", "on-device", "merge", "finetune", "adapter", "distilled"]
ALIGNMENT_QUERY_FILTERS = ["uncensored", "abliterated", "heretic", "decensored"]
LOCAL_MODEL_FILTERS = DERIVATIVE_FILTERS + ALIGNMENT_QUERY_FILTERS
ECOSYSTEM_ARCHITECTURE = json.loads(ECOSYSTEM_ARCHITECTURE_PATH.read_text(encoding="utf-8"))
ECOSYSTEM_STAGES = [
    (ecosystem, stage)
    for ecosystem in ECOSYSTEM_ARCHITECTURE["ecosystems"]
    for stage in ecosystem["stages"]
]
MODALITY_QUERY_FILTERS: dict[str, list[str]] = {}
for _, stage in ECOSYSTEM_STAGES:
    if stage.get("query_role") and stage.get("query_filters"):
        role_filters = MODALITY_QUERY_FILTERS.setdefault(stage["query_role"], [])
        role_filters.extend(value for value in stage.get("query_filters", []) if value not in role_filters)
MODALITY_FOCUS_ROLES = (
    "media-conditioning",
    "media-enhancement",
    "image-generation",
    "video-generation",
    "audio-generation",
    "audio-tts",
    "audio-stt",
    "robotics",
)
MEDIA_DEPLOYMENT_ROLES = {
    "media-conditioning",
    "media-enhancement",
    "vlm",
    "image-generation",
    "video-generation",
    "audio-generation",
    "audio-tts",
    "audio-stt",
}
MEDIA_ECOSYSTEM_FILTERS = ["comfyui"]
MEDIA_CUSTOMIZATION_QUERY_FILTERS = list(dict.fromkeys(
    value
    for ecosystem, stage in ECOSYSTEM_STAGES
    if ecosystem["id"] == "media"
    for value in stage.get("comfyui_filters", [])
))
MEDIA_PROFILE_RUNTIME_TAGS = {"comfyui", "diffusers", "diffusion-single-file"}
MEDIA_RUNTIME_TAGS = {
    "comfyui": "comfyui",
    "diffusers": "diffusers",
    "diffusion-single-file": "diffusion-single-file",
    "mlx": "mlx",
    "onnx": "onnx",
    "tensorrt": "tensorrt",
    "transformers": "transformers",
    "vllm": "vllm",
}
MEDIA_CUSTOMIZATION_TAGS = {
    "image-upscaling": "image-enhancement",
    "image-super-resolution": "image-enhancement",
    "super-resolution": "image-enhancement",
    "image-restoration": "image-enhancement",
    "deblurring": "image-enhancement",
    "video-restoration": "video-enhancement",
    "video-super-resolution": "video-enhancement",
    "mask-generation": "segmentation-mask",
    "image-segmentation": "segmentation-mask",
    "video-segmentation": "segmentation-mask",
    "segment-anything": "segmentation-mask",
    "sam2": "segmentation-mask",
    "sam3": "segmentation-mask",
    "pose-estimation": "pose-extraction",
    "human-pose-estimation": "pose-extraction",
    "depth-estimation": "depth-map",
    "motion-extraction": "motion-extraction",
    "face-detection": "face-analysis",
    "face-landmarks": "face-analysis",
    "matting": "segmentation-mask",
    "audio-driven": "audio-driven-video",
    "audio-driven-avatar": "audio-driven-video",
    "audio-to-video": "audio-driven-video",
    "camera-control": "motion-control",
    "character-animation": "character-animation",
    "character-consistency": "identity-consistency",
    "character-replacement": "person-replacement",
    "face-swap": "face-swap",
    "faceswap": "face-swap",
    "first-last-frame-to-video": "keyframe-control",
    "identity-consistency": "identity-consistency",
    "identity-preserving": "identity-consistency",
    "image-text-to-video": "image-to-video",
    "image-to-video": "image-to-video",
    "lip-sync": "lip-sync",
    "lipsync": "lip-sync",
    "motion-control": "motion-control",
    "motion-transfer": "motion-transfer",
    "multi-shot-video": "multi-shot-video",
    "pose-control": "motion-control",
    "person-replacement": "person-replacement",
    "reference-to-video": "reference-to-video",
    "speech-to-video": "audio-driven-video",
    "subject-consistency": "identity-consistency",
    "talking-head": "talking-head",
    "video-editing": "video-editing",
    "video-effects": "video-effects",
    "video-inpainting": "video-effects",
    "video-outpainting": "video-effects",
    "video-relighting": "video-effects",
    "video-to-video": "video-editing",
    "frame-interpolation": "video-enhancement",
    "video-upscaling": "video-enhancement",
}
MEDIA_CUSTOMIZATION_LANES = {
    "image-enhancement": "media-enhancement",
    "video-enhancement": "media-enhancement",
    "segmentation-mask": "media-conditioning",
    "pose-extraction": "media-conditioning",
    "motion-extraction": "media-conditioning",
    "depth-map": "media-conditioning",
    "face-analysis": "media-conditioning",
    "image-to-video": "image-to-video",
    "reference-to-video": "image-to-video",
    "keyframe-control": "image-to-video",
    "multi-shot-video": "image-to-video",
    "character-animation": "character-animation",
    "motion-control": "character-animation",
    "motion-transfer": "character-animation",
    "identity-consistency": "character-animation",
    "audio-driven-video": "audio-driven-avatar",
    "lip-sync": "audio-driven-avatar",
    "talking-head": "audio-driven-avatar",
    "video-editing": "video-editing-effects",
    "video-effects": "video-editing-effects",
    "face-swap": "video-editing-effects",
    "person-replacement": "video-editing-effects",
}
MEDIA_WORKFLOW_PRIMARY_CAPABILITIES = {
    "image-enhancement",
    "video-enhancement",
    "segmentation-mask",
    "pose-extraction",
    "motion-extraction",
    "depth-map",
    "face-analysis",
    "face-swap",
    "image-to-video",
    "reference-to-video",
    "keyframe-control",
    "multi-shot-video",
    "character-animation",
    "motion-control",
    "motion-transfer",
    "audio-driven-video",
    "lip-sync",
    "talking-head",
    "video-editing",
    "video-effects",
    "video-enhancement",
}
LOCAL_DEPLOYMENTS = {"gguf", "mlx", "quantized", "ollama-compatible", "on-device"}
DERIVATIVE_RELATIONS = {"adapter", "finetune", "merge", "quantized", "distilled"}
LOCAL_QUERY_LIMIT = 200
GLOBAL_TRENDING_LIMIT = 500
GLOBAL_RECENT_LIMIT = 1_000
LOCAL_REPORT_MAX = 20
LOCAL_PUBLISHER_MAX = 3
LOCAL_PUBLISHER_COVERAGE_MAX = 8
LOCAL_HOT_TRENDING = 4
LOCAL_HOT_DOWNLOADS = 2_000
LOCAL_HOT_LIKES = 20
LOCAL_BREAKOUT_TRENDING = 50
LOCAL_BREAKOUT_DOWNLOADS = 100_000
LOCAL_BREAKOUT_LIKES = 100
DISCOVERY_HOT_TRENDING = 15
DISCOVERY_HOT_DOWNLOADS = 2_000
DISCOVERY_HOT_LIKES = 20
MODALITY_HOT_TRENDING = 4
MODALITY_HOT_DOWNLOADS = 500
MODALITY_HOT_LIKES = 10
MODALITY_QUERY_LIMIT = 200
MEDIA_CUSTOMIZATION_LIMIT = 12
MEDIA_OPEN_ACTIVITY_MIN = 3
MEDIA_CUSTOMIZATION_PREFETCH_LIMIT = 30
MEDIA_CUSTOMIZATION_UNKNOWN_PREFETCH_LIMIT = 12
DATASET_HOT_TRENDING = 15
DATASET_HOT_DOWNLOADS = 1_000
DATASET_HOT_LIKES = 20
DATASET_TRENDING_LIMIT = 200
DATASET_RECENT_LIMIT = 500
DATASET_OWNER_LIMIT = 100
OWNER_QUERY_LIMIT = 100
NOTABLE_DISCOVERY_MIN = 8
NOTABLE_DISCOVERY_MAX = 12
NOTABLE_DATASET_MAX = 5
NOTABLE_TRUSTED_DATASET_MAX = 3
NOTABLE_HOT_DATASET_MIN = 2
NOTABLE_OWNER_MAX = 2
CARD_EXCERPT_CHARS = 1_200
EVALUATION_EXCERPT_CHARS = 2_000
EVALUATION_CAVEAT_CHARS = 700
CARD_FETCH_WORKERS = 8
CHANGE_EVIDENCE_LIMIT = 5
SNAPSHOT_VERSION = 2
MODEL_ARTIFACT_SUFFIXES = (
    ".bin",
    ".ckpt",
    ".gguf",
    ".onnx",
    ".pt",
    ".pth",
    ".safetensors",
)
SHARDED_ARTIFACT_RE = re.compile(
    r"^(?P<prefix>.+)-(?P<index>\d{5})-of-(?P<count>\d{5})(?P<suffix>\.[^/]+)$",
    re.IGNORECASE,
)

PIPELINE_MODALITIES: dict[str, dict[str, list[str]]] = {
    "mask-generation": {"input": ["image"], "output": ["mask"]},
    "image-segmentation": {"input": ["image"], "output": ["mask"]},
    "video-segmentation": {"input": ["video"], "output": ["mask"]},
    "pose-estimation": {"input": ["image"], "output": ["pose"]},
    "human-pose-estimation": {"input": ["image"], "output": ["pose"]},
    "depth-estimation": {"input": ["image"], "output": ["depth"]},
    "motion-extraction": {"input": ["video"], "output": ["motion"]},
    "face-detection": {"input": ["image"], "output": ["face"]},
    "face-landmarks": {"input": ["image"], "output": ["landmarks"]},
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
    "image-text-to-video": {"input": ["image", "text"], "output": ["video"]},
    "first-last-frame-to-video": {"input": ["image"], "output": ["video"]},
    "reference-to-video": {"input": ["image"], "output": ["video"]},
    "audio-to-video": {"input": ["audio"], "output": ["video"]},
    "speech-to-video": {"input": ["audio"], "output": ["video"]},
    "video-to-video": {"input": ["video"], "output": ["video"]},
    "automatic-speech-recognition": {"input": ["audio"], "output": ["text"]},
    "text-to-speech": {"input": ["text"], "output": ["audio"]},
    "text-to-audio": {"input": ["text"], "output": ["audio"]},
    "video-to-audio": {"input": ["video"], "output": ["audio"]},
    "text-video-to-audio": {"input": ["text", "video"], "output": ["audio"]},
    "audio-to-audio": {"input": ["audio"], "output": ["audio"]},
    "translation": {"input": ["text"], "output": ["text"]},
    "sentence-similarity": {"input": ["text"], "output": ["text"]},
    "robotics": {"input": ["robotics"], "output": ["robotics"]},
}
MODALITY_TOKENS = {"text", "image", "video", "audio", "speech", "robotics", "mask", "pose", "depth", "motion", "face", "landmarks"}

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

AUDIO_TASK_TAGS = {
    "text-to-sfx": "text-to-sfx",
    "sound-effects": "text-to-sfx",
    "video-to-sfx": "video-to-sfx",
    "text-video-to-sfx": "text-video-to-sfx",
    "audio-inpaint": "audio-inpaint",
    "audio-inpainting": "audio-inpaint",
    "audio-continuation": "audio-continuation",
    "ambience-generation": "ambience-generation",
    "text-to-music": "music-generation",
    "music-generation": "music-generation",
    "singing-voice-conversion": "singing-conversion",
    "singing-voice-synthesis": "singing-synthesis",
}
AUDIO_TASKS = set(AUDIO_TASK_TAGS.values()) | {"song-generation"}


def audio_tasks(row: dict[str, Any], override: dict[str, Any] | None = None) -> dict[str, Any]:
    signals = [
        {"task": task, "source": "hf-tag", "value": tag}
        for tag, task in sorted(AUDIO_TASK_TAGS.items())
        if tag in lower_tags(row)
    ]
    for task in (override or {}).get("audio_tasks", []):
        signals.append({"task": task, "source": "registry", "value": row.get("id")})
    return {"tasks": sorted({signal["task"] for signal in signals}), "evidence": signals} if signals else {}

LOW_REFUSAL_TAGS = {"uncensored", "abliterated", "heretic", "decensored"}

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


def trending_snapshot_path(state_dir: str | None) -> Path | None:
    configured = (state_dir or os.getenv("AI_OSS_MODELS_STATE_DIR") or "").strip()
    if not configured:
        return None
    return Path(configured).expanduser() / "trending-snapshot.json"


def load_trending_snapshot(path: Path) -> dict[str, Any]:
    try:
        payload = load_json(path)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return {}
    if payload.get("version") not in {1, SNAPSHOT_VERSION}:
        return {}
    models = payload.get("models")
    return payload if isinstance(models, dict) else {}


def trending_scopes(
    rows_or_scopes: list[dict[str, Any]] | dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    if isinstance(rows_or_scopes, list):
        return {"global": rows_or_scopes}
    return rows_or_scopes


def previous_scope_ranks(old: dict[str, Any]) -> dict[str, int]:
    ranks = old.get("ranks")
    if isinstance(ranks, dict):
        return {
            str(scope): int(rank)
            for scope, rank in ranks.items()
            if isinstance(rank, int)
        }
    rank = old.get("rank")
    return {"global": int(rank)} if isinstance(rank, int) else {}


def snapshot_is_mature(previous_observed_at: str, current_observed_at: str) -> bool:
    previous_date = iso_date(previous_observed_at)
    current_date = iso_date(current_observed_at)
    return bool(previous_date and current_date and previous_date < current_date)


def annotate_trending_deltas(
    rows_or_scopes: list[dict[str, Any]] | dict[str, list[dict[str, Any]]],
    previous: dict[str, Any],
    current_observed_at: str | None = None,
) -> None:
    previous_models = previous.get("models") or {}
    previous_observed_at = previous.get("observed_at") or ""
    current_observed_at = current_observed_at or dt.date.today().isoformat()
    use_previous = snapshot_is_mature(previous_observed_at, current_observed_at)
    scopes = trending_scopes(rows_or_scopes)
    current_by_id: dict[str, dict[str, Any]] = {}
    for scope, rows in scopes.items():
        for rank, row in enumerate(rows, start=1):
            model_id = str(row.get("id") or "")
            if not model_id:
                continue
            current = current_by_id.setdefault(model_id, {"row": row, "ranks": {}, "instances": []})
            current["ranks"][scope] = rank
            current["instances"].append(row)

    for model_id, current in current_by_id.items():
        row = current["row"]
        ranks = current["ranks"]
        old = previous_models.get(model_id) if use_previous and isinstance(previous_models, dict) else None
        old = old if isinstance(old, dict) else {}
        old_ranks = previous_scope_ranks(old)
        rankings = {
            scope: {
                "rank": rank,
                "rank_delta": old_ranks.get(scope) - rank if scope in old_ranks else None,
            }
            for scope, rank in ranks.items()
        }
        preferred_scope = "global" if "global" in ranks else min(ranks, key=ranks.get)
        signals = [
            "hf-global-trending" if scope == "global" else "hf-task-trending"
            for scope in ranks
        ]
        if any(
            isinstance(value.get("rank_delta"), int) and value["rank_delta"] > 0
            for value in rankings.values()
        ):
            signals.append("hf-rank-rising")
        score_delta = (
            float(row.get("trendingScore") or 0) - float(old.get("trendingScore") or 0)
            if old
            else None
        )
        downloads_delta = (
            int(row.get("downloads") or 0) - int(old.get("downloads") or 0)
            if old
            else None
        )
        likes_delta = (
            int(row.get("likes") or 0) - int(old.get("likes") or 0)
            if old
            else None
        )
        if any(value is not None and value > 0 for value in (score_delta, downloads_delta, likes_delta)):
            signals.append("hf-engagement-growing")
        trend = {
            "rank_scope": preferred_scope,
            "rank": ranks[preferred_scope],
            "rank_delta": rankings[preferred_scope]["rank_delta"],
            "rankings": rankings,
            "score_delta": score_delta,
            "downloads_delta": downloads_delta,
            "likes_delta": likes_delta,
            "signals": list(dict.fromkeys(signals)),
            "previous_observed_at": previous_observed_at or None,
        }
        for scoped_row in current["instances"]:
            scoped_row["_trend"] = trend


def annotate_github_deltas(
    metrics: dict[str, dict[str, Any]],
    previous: dict[str, Any],
    current_observed_at: str | None = None,
) -> None:
    previous_github = previous.get("github") or {}
    previous_observed_at = previous.get("observed_at") or ""
    current_observed_at = current_observed_at or dt.date.today().isoformat()
    use_previous = snapshot_is_mature(previous_observed_at, current_observed_at)
    for repo_url, current in metrics.items():
        old = previous_github.get(repo_url) if use_previous and isinstance(previous_github, dict) else None
        old = old if isinstance(old, dict) else {}
        stars_delta = int(current.get("stars") or 0) - int(old.get("stars") or 0) if old else None
        forks_delta = int(current.get("forks") or 0) - int(old.get("forks") or 0) if old else None
        signals: list[str] = []
        if stars_delta is not None and stars_delta > 0:
            signals.append("github-stars-growing")
        if forks_delta is not None and forks_delta > 0:
            signals.append("github-forks-growing")
        current["trend"] = {
            "stars_delta": stars_delta,
            "forks_delta": forks_delta,
            "signals": signals,
            "previous_observed_at": previous_observed_at or None,
        }


def write_trending_snapshot(
    path: Path,
    rows_or_scopes: list[dict[str, Any]] | dict[str, list[dict[str, Any]]],
    observed_at: str,
    github_metrics: dict[str, dict[str, Any]] | None = None,
) -> None:
    scopes = trending_scopes(rows_or_scopes)
    models: dict[str, dict[str, Any]] = {}
    for scope, rows in scopes.items():
        for rank, row in enumerate(rows, start=1):
            model_id = str(row.get("id") or "")
            if not model_id:
                continue
            model = models.setdefault(
                model_id,
                {
                    "ranks": {},
                    "trendingScore": row.get("trendingScore") or 0,
                    "downloads": row.get("downloads") or 0,
                    "likes": row.get("likes") or 0,
                },
            )
            model["ranks"][scope] = rank
    payload = {
        "version": SNAPSHOT_VERSION,
        "observed_at": observed_at,
        "models": models,
        "github": {
            repo_url: {
                "stars": row.get("stars") or 0,
                "forks": row.get("forks") or 0,
            }
            for repo_url, row in (github_metrics or {}).items()
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def write_trending_snapshot_safely(
    path: Path,
    rows_or_scopes: list[dict[str, Any]] | dict[str, list[dict[str, Any]]],
    observed_at: str,
    github_metrics: dict[str, dict[str, Any]] | None = None,
) -> bool:
    try:
        write_trending_snapshot(path, rows_or_scopes, observed_at, github_metrics)
    except OSError as exc:
        print(
            f"HF_TREND_SNAPSHOT_SKIPPED reason={type(exc).__name__}",
            file=sys.stderr,
        )
        return False
    return True


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
    for role, entries in models.get("ecosystem_baseline_models", {}).items():
        if role not in FLAGSHIP_ROLES:
            raise ValueError(f"invalid ecosystem baseline role: {role}")
        for entry in entries:
            model_id = str(entry.get("id") or "")
            if not model_id or model_id in seen_models:
                raise ValueError(f"duplicate or empty ecosystem baseline model: {model_id}")
            if entry.get("family") not in family_ids:
                raise ValueError(f"unknown family for ecosystem baseline {model_id}")
            seen_models.add(model_id)
    for model_id, override in models.get("model_overrides", {}).items():
        unknown = set(override.get("audio_tasks", [])) - AUDIO_TASKS
        if unknown:
            raise ValueError(f"invalid audio tasks for {model_id}: {sorted(unknown)}")
    for project in projects.get("projects", []):
        if project.get("openness") not in OPENNESS_LEVELS:
            raise ValueError(f"invalid openness for project {project.get('id')}")
        artifacts = project.get("artifacts", [])
        artifact_ids = [str(artifact.get("id") or "") for artifact in artifacts]
        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError(f"duplicate artifact id in project {project.get('id')}")
        known_artifact_ids = set(artifact_ids)
        for artifact in artifacts:
            if artifact.get("role") not in ARTIFACT_ROLES:
                raise ValueError(f"invalid artifact role in project {project.get('id')}")
            missing_dependencies = set(artifact.get("depends_on", [])) - known_artifact_ids
            if missing_dependencies:
                missing = ", ".join(sorted(str(value) for value in missing_dependencies))
                raise ValueError(
                    f"unknown artifact dependency in project {project.get('id')}: {missing}"
                )
    seen_datasets: set[str] = set()
    for entry in datasets.get("datasets", []):
        dataset_id = str(entry["id"])
        if dataset_id in seen_datasets:
            raise ValueError(f"duplicate registered dataset: {dataset_id}")
        if not set(entry.get("roles", [])) <= ARTIFACT_ROLES:
            raise ValueError(f"invalid dataset role for {dataset_id}")
        seen_datasets.add(dataset_id)


def validate_ecosystem_baselines(
    architecture: dict[str, Any], development: dict[str, Any]
) -> None:
    ecosystems = architecture.get("ecosystems") or []
    ecosystem_ids = [str(entry.get("id") or "") for entry in ecosystems]
    if len(ecosystem_ids) != len(set(ecosystem_ids)) or not all(ecosystem_ids):
        raise ValueError("duplicate or empty ecosystem id")
    for ecosystem in ecosystems:
        stages = ecosystem.get("stages") or []
        stage_ids = [str(stage.get("id") or "") for stage in stages]
        if len(stage_ids) != len(set(stage_ids)) or not all(stage_ids):
            raise ValueError(f"duplicate or empty stage in {ecosystem['id']}")
        for stage in stages:
            if set(stage.get("upstream") or []) - set(stage_ids):
                raise ValueError(f"unknown upstream stage in {ecosystem['id']}/{stage['id']}")
            role = stage.get("query_role")
            if role and role not in FLAGSHIP_ROLES:
                raise ValueError(f"unknown query role in {ecosystem['id']}/{stage['id']}")
    for kind in ("tools", "datasets"):
        entries = development.get(kind) or []
        ids = [str(entry.get("id") or "") for entry in entries]
        if len(ids) != len(set(ids)) or not all(ids):
            raise ValueError(f"duplicate or empty development {kind} id")
        for entry in entries:
            if set(entry.get("domains") or []) - set(ecosystem_ids):
                raise ValueError(f"unknown development domain for {entry['id']}")
    experiment_ids: set[str] = set()
    for entry in development.get("local_experiments") or []:
        experiment_id = str(entry.get("id") or "")
        if not experiment_id or experiment_id in experiment_ids:
            raise ValueError(f"duplicate or empty local experiment id: {experiment_id}")
        if entry.get("method") not in {"sft", "offline-response-distillation", "rlvr-grpo", "decision-sft", "decision-rlvr", "video-t2v-lora", "video-ic-lora", "audio-sfx-lora", "audio-music-lora"}:
            raise ValueError(f"invalid local experiment method: {experiment_id}")
        if not all(entry.get(key) for key in ("model_id", "dataset_id", "dataset_config", "dataset_split", "required_columns", "tools", "evidence")):
            raise ValueError(f"incomplete local experiment: {experiment_id}")
        if entry.get("max_parameters") is None and entry.get("method") not in {"video-t2v-lora", "video-ic-lora"}:
            raise ValueError(f"missing local experiment parameter cap: {experiment_id}")
        if entry.get("max_parameters") is not None and (not isinstance(entry["max_parameters"], int) or entry["max_parameters"] <= 0):
            raise ValueError(f"invalid local experiment parameter cap: {experiment_id}")
        if entry.get("dataset_manifest") and not entry.get("model_weight_path"):
            raise ValueError(f"missing video training checkpoint: {experiment_id}")
        for tool in entry["tools"]:
            if not all(tool.get(key) for key in ("project", "component", "role", "evidence")):
                raise ValueError(f"incomplete local experiment tool: {experiment_id}")
        experiment_ids.add(experiment_id)


def hf_api_bases() -> list[str]:
    raw = os.getenv("AI_OSS_HF_API_BASES") or os.getenv("HF_API_BASES") or ""
    values = [value.strip().rstrip("/") for value in raw.split(",") if value.strip()]
    return values or DEFAULT_HF_API_BASES


def proxy_url(value: str) -> str:
    cleaned = value.strip()
    parsed = urllib.parse.urlsplit(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise argparse.ArgumentTypeError("proxy must be an http:// or https:// URL")
    return cleaned


def configure_proxy(
    http_proxy: str | None,
    https_proxy: str | None,
    no_proxy: str | None,
) -> None:
    """Apply explicit proxy settings only to this process and gh children."""
    if not any((http_proxy, https_proxy, no_proxy)):
        return

    for scheme, value in (("http", http_proxy), ("https", https_proxy)):
        for key in (f"{scheme}_proxy", f"{scheme.upper()}_PROXY"):
            if value:
                os.environ[key] = value
            elif http_proxy or https_proxy:
                os.environ.pop(key, None)

    bypass = [*LOCAL_NO_PROXY]
    bypass.extend(part.strip() for part in (no_proxy or "").split(",") if part.strip())
    bypass_value = ",".join(dict.fromkeys(bypass))
    os.environ["no_proxy"] = bypass_value
    os.environ["NO_PROXY"] = bypass_value
    urllib.request.install_opener(urllib.request.build_opener())


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
            if isinstance(exc, urllib.error.HTTPError) and exc.code in {400, 401, 403, 404}:
                break
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


def fetch_development_tool(repo_id: str) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo_id):
        raise ValueError("invalid GitHub repository id")
    row = json.loads(fetch_text(f"https://api.github.com/repos/{repo_id}", retries=0))
    if not isinstance(row, dict) or not row.get("full_name"):
        raise TypeError(f"unexpected GitHub response for {repo_id}")
    try:
        commits = json.loads(fetch_text(f"https://api.github.com/repos/{repo_id}/commits?per_page=1", retries=0))
        if isinstance(commits, list) and commits:
            commit = commits[0]
            details = commit.get("commit") or {}
            row["_latest_commit"] = {
                "title": str(details.get("message") or "").splitlines()[0],
                "date": str((details.get("committer") or {}).get("date") or "")[:10],
                "url": str(commit.get("html_url") or ""),
            }
    except Exception:
        pass
    return row


def development_updates(
    baseline: dict[str, Any], start: dt.date, end: dt.date
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    """Check a small, explicit local-development baseline instead of broad dataset search."""
    tool_specs = {str(item["id"]): item for item in baseline["tools"]}
    dataset_specs = {str(item["id"]): item for item in baseline["datasets"]}
    with ThreadPoolExecutor(max_workers=2) as executor:
        tool_future = executor.submit(fetch_many, tool_specs, fetch_development_tool, 6)
        dataset_future = executor.submit(fetch_many, dataset_specs, fetch_dataset, 6)
        tool_rows, tool_errors = tool_future.result()
        dataset_rows, dataset_errors = dataset_future.result()
    items: dict[str, list[dict[str, Any]]] = {"tools": [], "datasets": []}
    for repo_id, row in tool_rows.items():
        spec = tool_specs[repo_id]
        published = iso_date(row.get("created_at"))
        pushed = iso_date(row.get("pushed_at"))
        event = ("published", published) if published and start <= published <= end else (
            ("repository-updated", pushed) if pushed and start <= pushed <= end else None
        )
        if event:
            latest_commit = row.get("_latest_commit") or {}
            latest_commit_date = iso_date(latest_commit.get("date"))
            items["tools"].append({
                "title": repo_id,
                "url": spec["url"],
                "date": event[1].isoformat(),
                "event": event[0],
                "category": "development-tool",
                "metadata": {
                    "domains": spec["domains"], "methods": spec["methods"],
                    "entry": spec["entry"], "evidence": spec["evidence"],
                    "stars": row.get("stargazers_count"),
                    "change_evidence": {
                        "ok": True,
                        "commits": [latest_commit],
                    } if latest_commit_date and start <= latest_commit_date <= end else {},
                },
            })
    for repo_id, row in dataset_rows.items():
        spec = dataset_specs[repo_id]
        event = event_in_window(row, start, end)
        if event:
            items["datasets"].append({
                "title": repo_id,
                "url": spec["evidence"],
                "date": event[1],
                "event": event[0],
                "category": "development-dataset",
                "metadata": {"domains": spec["domains"], "methods": spec["methods"], "sample_unit": spec["sample_unit"], "downloads": row.get("downloads"), "likes": row.get("likes")},
            })
    for rows in items.values():
        rows.sort(key=lambda item: (item["date"], item["title"]), reverse=True)
    return items, {
        "github_tools": source_status(tool_rows, tool_errors, len(items["tools"])),
        "huggingface_development_datasets": source_status(dataset_rows, dataset_errors, len(items["datasets"])),
    }


def fetch_dataset_columns(dataset_id: str, config: str, split: str) -> list[str]:
    query = urllib.parse.urlencode(
        {"dataset": dataset_id, "config": config, "split": split}
    )
    row = json.loads(
        fetch_text(
            f"https://datasets-server.huggingface.co/first-rows?{query}",
            retries=0,
        )
    )
    if not isinstance(row, dict):
        raise TypeError("unexpected Hugging Face dataset first-rows response")
    return [str(value.get("name")) for value in row.get("features") or [] if value.get("name")]


def development_opportunities(
    baseline: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Verify evergreen small-model training pairs independently of update dates."""
    specs = baseline.get("local_experiments") or []
    if not specs:
        return [], source_status({}, {}, 0)
    model_ids = [str(spec["model_id"]) for spec in specs]
    dataset_ids = [str(spec["dataset_id"]) for spec in specs]
    with ThreadPoolExecutor(max_workers=3) as executor:
        models_future = executor.submit(fetch_many, model_ids, fetch_model, 4)
        datasets_future = executor.submit(fetch_many, dataset_ids, fetch_dataset, 4)
        files_future = executor.submit(fetch_many, model_ids, fetch_model_repository_files, 4)
        model_rows, model_errors = models_future.result()
        dataset_rows, dataset_errors = datasets_future.result()
        file_rows, file_errors = files_future.result()
    opportunities: list[dict[str, Any]] = []
    errors = {
        **{f"model:{key}": value for key, value in model_errors.items()},
        **{f"dataset:{key}": value for key, value in dataset_errors.items()},
        **{f"files:{key}": value for key, value in file_errors.items()},
    }
    for spec in specs:
        experiment_id = str(spec["id"])
        model_id = str(spec["model_id"])
        dataset_id = str(spec["dataset_id"])
        model = model_rows.get(model_id)
        dataset = dataset_rows.get(dataset_id)
        if model is None or dataset is None:
            errors[experiment_id] = "model-or-dataset-unavailable"
            continue
        parameters = (model.get("safetensors") or {}).get("total")
        if spec.get("max_parameters") and (not isinstance(parameters, int) or parameters > spec["max_parameters"]):
            errors[experiment_id] = "model-scale-unverified-or-too-large"
            continue
        try:
            manifest = spec.get("dataset_manifest")
            if manifest:
                manifest_url = f"https://huggingface.co/datasets/{dataset_id}/resolve/main/{urllib.parse.quote(manifest)}"
                samples = json.loads(fetch_text(manifest_url, retries=0))
                if not isinstance(samples, list) or not samples or not all(isinstance(row, dict) for row in samples):
                    raise ValueError("invalid media manifest")
                columns = sorted(set.intersection(*(set(row) for row in samples)))
                paths = {row.get("rfilename") for row in dataset.get("siblings") or []}
                for row in samples:
                    for field in spec.get("media_columns") or []:
                        if row.get(field) not in paths:
                            raise ValueError("media path missing from repository")
            else:
                columns = fetch_dataset_columns(
                    dataset_id,
                    str(spec["dataset_config"]),
                    str(spec["dataset_split"]),
                )
                if spec.get("media_columns"):
                    query = urllib.parse.urlencode({
                        "dataset": dataset_id,
                        "config": spec["dataset_config"],
                        "split": spec["dataset_split"],
                    })
                    preview = json.loads(fetch_text(
                        f"https://datasets-server.huggingface.co/first-rows?{query}",
                        retries=0,
                    ))
                    features = {row.get("name"): row.get("type") for row in preview.get("features") or []}
                    for field in spec["media_columns"]:
                        if (features.get(field) or {}).get("_type") != "Audio":
                            raise ValueError("audio feature unavailable")
        except Exception as exc:
            errors[experiment_id] = f"dataset-schema-{type(exc).__name__}"
            continue
        missing = sorted(set(spec["required_columns"]) - set(columns))
        if missing:
            errors[experiment_id] = "missing-columns:" + ",".join(missing)
            continue
        repository = file_rows.get(model_id) or {}
        artifact_files = [
            row for row in repository.get("files") or []
            if str(row.get("path") or "").lower().endswith(MODEL_ARTIFACT_SUFFIXES)
        ]
        options = [
            option for option in build_artifact_options(artifact_files)
            if option.get("component") == "model-weights" or (
                spec.get("model_weight_path") and option.get("path") == spec["model_weight_path"]
            )
        ]
        options = [
            option for option in options
            if option.get("bytes", 0) > 0
            and option.get("complete", True)
        ]
        weight_path = spec.get("model_weight_path")
        if weight_path:
            options = [option for option in options if weight_path in (option.get("path"), *(option.get("paths") or []))]
        main_weight = max(options, key=lambda value: int(value["bytes"])) if options else None
        if main_weight is None:
            errors[experiment_id] = "model-main-weight-unavailable"
            continue
        opportunities.append(
            {
                "id": experiment_id,
                "method": spec["method"],
                "model": {
                    "id": model_id,
                    "url": f"https://huggingface.co/{model_id}",
                    "parameters": parameters,
                    "main_weight": main_weight,
                },
                "dataset": {
                    "id": dataset_id,
                    "url": f"https://huggingface.co/datasets/{dataset_id}",
                    "config": spec["dataset_config"],
                    "split": spec["dataset_split"],
                    "columns": columns,
                    "required_columns": spec["required_columns"],
                    "sample_unit": spec["sample_unit"],
                    "downloads": dataset.get("downloads"),
                    "likes": dataset.get("likes"),
                },
                "signal": spec["signal"],
                "local_scope": spec["local_scope"],
                "preparation": spec.get("preparation"),
                "resource_evidence": spec.get("resource_evidence"),
                "tools": spec["tools"],
                "evidence": spec["evidence"],
                "status": "metadata-verified-runtime-unmeasured",
            }
        )
    return opportunities, source_status(
        {item["id"]: item for item in opportunities}, errors, len(opportunities)
    )


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


def ecosystem_paths(
    row: dict[str, Any], role: str, override: dict[str, Any] | None = None
) -> list[dict[str, str]]:
    """Map exact task evidence to the shared ecosystem graph."""
    pipeline = str(row.get("pipeline_tag") or "").lower()
    tags = lower_tags(row)
    audio_stage_by_task = {
        "song-generation": "song",
        "music-generation": "song",
        "text-to-sfx": "sound-effect",
        "ambience-generation": "sound-effect",
        "video-to-sfx": "video-foley",
        "text-video-to-sfx": "video-foley",
        "audio-inpaint": "audio-edit",
        "audio-continuation": "audio-edit",
        "singing-conversion": "singing-conversion",
        "singing-synthesis": "singing-synthesis",
    }
    registered_audio_tasks = set((override or {}).get("audio_tasks", []))
    derivative_roles = {
        "llm-vlm": {"llm", "vlm"},
        "media": {"image-generation", "video-generation", "media-conditioning", "media-enhancement"},
        "speech": {"audio-tts", "audio-stt"},
        "decision": {"decision"},
        "music": {"audio-generation"},
        "embodied": {"robotics"},
    }
    paths: list[dict[str, str]] = []
    for ecosystem, stage in ECOSYSTEM_STAGES:
        if stage["id"] == "local-derivative" and role not in derivative_roles[ecosystem["id"]]:
            continue
        evidence: tuple[str, str] | None = None
        if pipeline in stage.get("pipeline_tags", []):
            evidence = ("hf-pipeline_tag", pipeline)
        else:
            matched = sorted(tags & set(stage.get("tags", [])))
            if matched:
                evidence = ("hf-tag", matched[0])
        if not evidence and ecosystem["id"] == "music":
            task = next(
                (task for task in sorted(registered_audio_tasks) if audio_stage_by_task.get(task) == stage["id"]),
                None,
            )
            if task:
                evidence = ("registry", task)
        if not evidence and stage.get("query_role") == role and not any(
            path["ecosystem"] == ecosystem["id"] for path in paths
        ):
            evidence = ("registered-role", role)
        if evidence:
            paths.append({
                "ecosystem": ecosystem["id"],
                "stage": stage["id"],
                "source": evidence[0],
                "value": evidence[1],
            })
    return paths


def modality_tokens(value: str) -> list[str]:
    aliases = {"speech": "audio"}
    return list(
        dict.fromkeys(
            aliases.get(token, token)
            for token in value.lower().split("-")
            if token in MODALITY_TOKENS
        )
    )


def pipeline_modalities(value: str) -> dict[str, list[str]]:
    normalized = value.strip().lower()
    known = PIPELINE_MODALITIES.get(normalized)
    if known:
        return {"input": list(known["input"]), "output": list(known["output"])}
    if normalized.count("-to-") != 1 or ":" in normalized or "/" in normalized:
        return {"input": [], "output": []}
    raw_input, raw_output = normalized.split("-to-", 1)
    inputs = modality_tokens(raw_input)
    outputs = modality_tokens(raw_output)
    if not inputs or not outputs:
        return {"input": [], "output": []}
    return {"input": inputs, "output": outputs}


def modality_evidence(row: dict[str, Any]) -> dict[str, Any]:
    pipeline_tag = str(row.get("pipeline_tag") or "").lower()
    candidates: list[tuple[str, str]] = []
    if pipeline_tag:
        candidates.append(("pipeline_tag", pipeline_tag))
    candidates.extend(("tag", tag) for tag in sorted(lower_tags(row)) if tag != pipeline_tag)
    inputs: list[str] = []
    outputs: list[str] = []
    signals: list[dict[str, str]] = []
    for source, value in candidates:
        modalities = pipeline_modalities(value)
        if not modalities["input"] and not modalities["output"]:
            continue
        inputs.extend(modalities["input"])
        outputs.extend(modalities["output"])
        signals.append({"source": source, "value": value})
    return {
        "input": sorted(set(inputs)),
        "output": sorted(set(outputs)),
        "signals": signals,
    }


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


def structured_base_model_signals(row: dict[str, Any]) -> list[dict[str, str]]:
    """Retain each HF lineage assertion with its original source and relation."""
    card = row.get("cardData") or {}
    default_relation = str(card.get("base_model_relation") or "base_model")
    raw = card.get("base_model")
    values = raw if isinstance(raw, list) else [raw] if raw else []
    signals: list[dict[str, str]] = []
    for value in values:
        repo_id = str(value or "").strip()
        if re.fullmatch(r"[^/:\s]+/[^/:\s]+", repo_id):
            signals.append({"repo_id": repo_id, "relation": default_relation,
                            "source": "hf-card-data", "evidence": "cardData.base_model"})
    for raw_tag in row.get("tags") or []:
        tag = str(raw_tag)
        if not tag.startswith("base_model:"):
            continue
        value = tag.removeprefix("base_model:")
        parts = value.split(":", 1)
        relation, repo_id = (parts[0], parts[1]) if len(parts) == 2 and parts[0] in BASE_MODEL_RELATIONS | {"distilled"} else (default_relation, value)
        if re.fullmatch(r"[^/:\s]+/[^/:\s]+", repo_id):
            signals.append({"repo_id": repo_id, "relation": relation,
                            "source": "hf-tag", "evidence": tag})
    return list({(s["repo_id"], s["relation"], s["source"]): s for s in signals}.values())


def observed_canonical_references(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Count distinct, unambiguous direct HF base_model references in the sampled pool."""
    children: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        child_id = str(row.get("id") or "")
        parents = {signal["repo_id"] for signal in structured_base_model_signals(row)}
        if not child_id or len(parents) != 1:
            continue
        parent_id = next(iter(parents))
        if parent_id != child_id:
            children.setdefault(parent_id, {})[child_id] = row
    return {
        parent_id: {
            "direct_references_observed": len(by_id),
            "active_derivatives_observed": sum(
                bool(row.get("_trend") and is_hot_local(row))
                for row in by_id.values()
            ),
            "active_derivative_ids": [
                child_id for child_id, row in sorted(
                    by_id.items(),
                    key=lambda value: (
                        int(value[1].get("trendingScore") or 0),
                        int(value[1].get("likes") or 0),
                        value[0],
                    ),
                    reverse=True,
                )
                if row.get("_trend") and is_hot_local(row)
            ][:8],
            "reference_source": "sampled-hf-base-model",
        }
        for parent_id, by_id in children.items()
    }


def canonical_model_trace(
    model_id: str,
    model_rows: dict[str, dict[str, Any]],
    declared_canonical: str | None = None,
    max_depth: int = 4,
) -> dict[str, Any]:
    """Trace typed HF base-model edges; stop rather than guess across gaps."""
    hops: list[dict[str, Any]] = []
    current = model_id
    visited = {model_id}
    for _ in range(max_depth):
        row = model_rows.get(current)
        if row is None:
            status = "parent-unavailable"
            break
        signals = structured_base_model_signals(row)
        parents = sorted({signal["repo_id"] for signal in signals})
        if len(parents) > 1:
            return {"status": "ambiguous", "canonical_model": None, "root_model": None,
                    "declared_canonical": declared_canonical,
                    "matches_declaration": None, "hops": hops, "alternatives": signals}
        if not parents:
            status = "resolved" if hops else "no-structured-parent"
            break
        parent = parents[0]
        edge = [signal for signal in signals if signal["repo_id"] == parent]
        typed_relations = {signal["relation"] for signal in edge if signal["relation"] != "base_model"}
        if len(typed_relations) > 1:
            return {"status": "conflicting-relations", "canonical_model": None, "root_model": None,
                    "declared_canonical": declared_canonical,
                    "matches_declaration": None, "hops": hops, "alternatives": edge}
        chosen = next((signal for signal in edge if signal["relation"] in typed_relations and signal["source"] == "hf-tag"), None)
        chosen = chosen or next((signal for signal in edge if signal["relation"] in typed_relations), edge[0])
        hops.append({"from": current, "to": parent, "relation": chosen["relation"],
                     "source": chosen["source"], "evidence": chosen["evidence"],
                     "signals": edge})
        if parent in visited:
            status = "cycle"
            break
        visited.add(parent)
        current = parent
    else:
        status = "depth-limit"
    root_model = current if status == "resolved" else None
    if not hops and declared_canonical and declared_canonical != model_id:
        status = "registry-only" if status == "no-structured-parent" else status
    path_nodes = [model_id] + [hop["to"] for hop in hops]
    matches_declaration = (
        declared_canonical in path_nodes if declared_canonical else None
    )
    if status in {"cycle", "ambiguous", "conflicting-relations", "depth-limit"}:
        canonical = None
    elif declared_canonical and matches_declaration:
        canonical = declared_canonical
    elif declared_canonical:
        canonical = None
    elif hops and hops[0]["relation"] in DERIVATIVE_RELATIONS:
        canonical = hops[0]["to"]
    else:
        canonical = None
    return {"status": status, "canonical_model": canonical,
            "root_model": root_model,
            "declared_canonical": declared_canonical,
            "matches_declaration": matches_declaration,
            "hops": hops}


def attach_canonical_traces(
    items: list[dict[str, Any]],
    model_rows: dict[str, dict[str, Any]],
    fetch_missing: bool = True,
    max_depth: int = 4,
) -> dict[str, str]:
    """Fetch only selected models' structured ancestors and attach auditable paths."""
    rows = dict(model_rows)
    frontier = {str(item.get("title") or "") for item in items}
    expanded: set[str] = set()
    fetch_errors: dict[str, str] = {}
    for _ in range(max_depth):
        targets: set[str] = set()
        for model_id in frontier - expanded:
            row = rows.get(model_id)
            if row is not None:
                targets.update(signal["repo_id"] for signal in structured_base_model_signals(row))
        expanded.update(frontier)
        if not targets:
            break
        missing = sorted(targets - rows.keys() - fetch_errors.keys())
        if missing and fetch_missing:
            fetched, errors = fetch_many(missing, fetch_model, workers=8)
            rows.update(fetched)
            fetch_errors.update(errors)
        frontier = {target for target in targets if target in rows and target not in expanded}
        if not frontier:
            break
    for item in items:
        metadata = item.setdefault("metadata", {})
        model_id = str(item.get("title") or "")
        declared = str(metadata.get("canonical_model") or "") or None
        trace = canonical_model_trace(model_id, rows, declared, max_depth=max_depth)
        if trace["status"] == "parent-unavailable" and trace["hops"]:
            parent = trace["hops"][-1]["to"]
            if parent in fetch_errors:
                trace["fetch_error"] = fetch_errors[parent]
        metadata["canonical_model_trace"] = trace
        if trace["canonical_model"]:
            metadata["canonical_model"] = trace["canonical_model"]
        else:
            metadata.pop("canonical_model", None)
    return fetch_errors


def derivation_facets(row: dict[str, Any]) -> list[str]:
    values = {
        relation
        for _, relation in base_model_links(row)
        if relation in DERIVATIVE_RELATIONS
    }
    if lower_tags(row) & {"adapter", "lora"}:
        values.add("adapter")
    if lower_tags(row) & {"distilled", "distillation"}:
        values.add("distilled")
    return sorted(values)


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
    values.update(runtime for tag, runtime in MEDIA_RUNTIME_TAGS.items() if tag in tags)
    return sorted(values)


def media_customization_facet(row: dict[str, Any]) -> dict[str, Any]:
    signals: list[dict[str, str]] = [
        {
            "capability": MEDIA_CUSTOMIZATION_TAGS[tag],
            "source": "hf-tag",
            "value": tag,
        }
        for tag in sorted(lower_tags(row) & set(MEDIA_CUSTOMIZATION_TAGS))
    ]
    for signal in modality_evidence(row)["signals"]:
        modalities = pipeline_modalities(str(signal["value"]))
        inputs = set(modalities["input"])
        outputs = set(modalities["output"])
        capability = ""
        if "video" in outputs and "image" in inputs:
            capability = "image-to-video"
        elif "video" in outputs and "audio" in inputs:
            capability = "audio-driven-video"
        elif "video" in outputs and "video" in inputs:
            capability = "video-editing"
        elif "mask" in outputs and inputs & {"image", "video"}:
            capability = "segmentation-mask"
        elif "pose" in outputs and inputs & {"image", "video"}:
            capability = "pose-extraction"
        elif "motion" in outputs and "video" in inputs:
            capability = "motion-extraction"
        elif "depth" in outputs and inputs & {"image", "video"}:
            capability = "depth-map"
        elif outputs & {"face", "landmarks"} and inputs & {"image", "video"}:
            capability = "face-analysis"
        if capability:
            signals.append(
                {
                    "capability": capability,
                    "source": f"hf-{signal['source']}",
                    "value": str(signal["value"]),
                }
            )
    if not signals:
        return {}
    return merge_customization_signals({"signals": signals})


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
    return "unknown"


def architecture_classes(row: dict[str, Any]) -> list[str]:
    values = (row.get("config") or {}).get("architectures") or []
    if isinstance(values, str):
        values = [values]
    return [str(value) for value in values if value]


def paper_links(row: dict[str, Any]) -> list[dict[str, str]]:
    paper_ids: list[str] = []
    for raw_tag in row.get("tags", []):
        tag = str(raw_tag)
        if not tag.lower().startswith("arxiv:"):
            continue
        paper_id = tag.split(":", 1)[1].strip()
        if paper_id and paper_id not in paper_ids:
            paper_ids.append(paper_id)
    return [
        {
            "id": paper_id,
            "arxiv_url": f"https://arxiv.org/abs/{urllib.parse.quote(paper_id, safe='./-')}",
            "hf_paper_url": f"https://huggingface.co/papers/{urllib.parse.quote(paper_id, safe='./-')}",
        }
        for paper_id in paper_ids
    ]


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
    pipeline = str(row.get("pipeline_tag") or "").lower()
    if pipeline in CAPABILITY_TAGS:
        values.add(CAPABILITY_TAGS[pipeline])
    values.update(str(value) for value in (override or {}).get("capabilities", []))
    return sorted(values)


def alignment_facet(row: dict[str, Any]) -> dict[str, Any]:
    """Preserve exact publisher tags without inferring alignment from a model ID."""
    signals = [
        {"source": "hf-tag", "value": tag}
        for tag in sorted(lower_tags(row) & LOW_REFUSAL_TAGS)
    ]
    if not signals:
        return {}
    return {"profile": "low-refusal", "signals": signals}


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


def publisher_tier(model_id: str, registry: dict[str, Any]) -> str:
    owner = model_id.split("/", 1)[0]
    registered_owners = {str(entry["owner"]) for entry in registry.get("families", [])}
    if owner in registered_owners:
        return "registered-owner"
    if owner in {str(value) for value in registry.get("local_publishers", [])}:
        return "local-ecosystem-publisher"
    return "unregistered"


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
    modality_signals = modality_evidence(row)
    modality_inherited_from: str | None = None
    if (
        inherited
        and not modality_signals["input"]
        and not modality_signals["output"]
    ):
        inherited_signals = modality_evidence(inherited)
        if inherited_signals["input"] or inherited_signals["output"]:
            modality_signals = {
                "input": inherited_signals["input"],
                "output": inherited_signals["output"],
                "signals": [
                    {
                        **signal,
                        "source": f"base_model.{signal.get('source') or 'structured'}",
                    }
                    for signal in inherited_signals["signals"]
                ],
            }
            modality_inherited_from = str(inherited.get("id") or "") or None
    return {
        "model_id": model_id,
        "track": record.get("track"),
        "role": record.get("role"),
        "family": family_id or None,
        "canonical_model": canonical,
        "modalities": {
            "input": modality_signals["input"],
            "output": modality_signals["output"],
        },
        "role_evidence": {
            "pipeline_tag": row.get("pipeline_tag")
            or ((inherited or {}).get("pipeline_tag") if modality_inherited_from else "")
            or "",
            "task_signals": modality_signals["signals"],
            "inherited_from": modality_inherited_from,
        },
        "capabilities": capability_facets(row, override),
        "ecosystem_paths": ecosystem_paths(row, str(record.get("role") or model_role(row)), override),
        "audio_tasks": audio_tasks(row, override),
        "media_customization": media_customization_facet(row),
        "alignment": alignment_facet(row),
        "deployment": deployment,
        "stage": stage_facets(row),
        "architecture": architecture_facet(row),
        "architecture_classes": architecture_classes(row),
        "scale": scale_facet(row, inherited),
        "papers": paper_links(row),
        "license": (row.get("cardData") or {}).get("license") or "unknown",
        "openness": {
            "level": family.get("openness", "unknown"),
            "evidence": family.get("evidence", []),
        },
        "base_models": list(dict.fromkeys(signal["repo_id"] for signal in structured_base_model_signals(row))),
        "base_model_dependencies": structured_base_model_signals(row),
        "derivation": derivation_facets(row),
        "pipeline_tag": row.get("pipeline_tag") or "",
        "downloads": row.get("downloads") or 0,
        "likes": row.get("likes") or 0,
        "trendingScore": row.get("trendingScore") or 0,
        "createdAt": row.get("createdAt") or "",
        "lastModified": row.get("lastModified") or "",
        "publisher_tier": record.get("publisher_tier") or publisher_tier(model_id, registry),
        "variant_group": override.get("variant_group") or record.get("variant_group"),
        "trend": row.get("_trend") or {},
        "selection": record.get("selection", []),
        "pending_registry": bool(record.get("pending_registry")),
        "embodied_subtype": record.get("subtype"),
        "ecosystem_activity": record.get("ecosystem_activity") or {},
    }


ROLE_LABELS = {
    "media-conditioning": "媒体控制信号模型",
    "media-enhancement": "清晰度与分辨率增强模型",
    "llm": "旗舰 LLM",
    "vlm": "旗舰 VLM / 多模态模型",
    "decision": "结构化决策模型",
    "image-generation": "图像生成模型",
    "video-generation": "视频生成模型",
    "audio-generation": "音频生成模型",
    "audio-tts": "语音合成模型",
    "audio-stt": "语音识别模型",
    "ocr": "OCR 模型",
    "translation": "翻译模型",
    "embedding": "Embedding 模型",
    "robotics": "机器人动作模型",
}


def event_label(event: str) -> str:
    return {
        "published": "新发布",
        "repository-updated": "仓库更新",
        "trending-observed": "当前热门",
        "derivatives-observed": "当前衍生活跃",
        "engagement-observed": "当前站内关注",
        "capability-observed": "专项能力参照",
    }.get(event, event)


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
        signal_text = (
            f"截至 {date} 仍处于 HF 热门"
            if event_name == "trending-observed"
            else f"本窗口内发生{event_label(event_name)}"
        )
        if canonical:
            summary = f"{model_id.split('/')[-1]} 是 {canonical} 的热门或重点本地部署版本，{signal_text}。"
        else:
            summary = f"{model_id.split('/')[-1]} 是热门衍生或本地部署模型，{signal_text}。"
    elif track == "discovery":
        source_label = (
            "已登记官方发布者"
            if record.get("publisher_tier") == "registered-owner"
            else "全局热门候选发布者"
        )
        summary = (
            f"{model_id.split('/')[-1]} 来自{source_label}，"
            f"本窗口内发生{event_label(event_name)}，待纳入注册表确认。"
        )
    elif track == "ecosystem-baseline":
        summary = f"{model_id.split('/')[-1]} 是持续观察的机器人模型基线，当前元数据核于 {date}。"
    elif event_name in {"trending-observed", "derivatives-observed", "engagement-observed", "capability-observed"}:
        summary = f"{model_id.split('/')[-1]} 是已登记主模型，截至 {date} {event_label(event_name)}。"
    else:
        summary = f"{model_id.split('/')[-1]} 是白名单中的{ROLE_LABELS.get(role, role)}，本窗口内发生{event_label(event_name)}。"
    item = {
        "title": model_id,
        "url": f"https://huggingface.co/{model_id}",
        "summary": summary,
        "date": date,
        "event": event_name,
        "source": "Hugging Face Models",
        "category": role if track in {"flagship", "discovery", "ecosystem-baseline"} else "local",
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

    with ThreadPoolExecutor(max_workers=len(LOCAL_MODEL_FILTERS)) as executor:
        results = executor.map(query, LOCAL_MODEL_FILTERS)
        for result in results:
            for row in result:
                model_id = str(row.get("id") or "")
                if model_id:
                    rows.setdefault(model_id, row)
    return list(rows.values())


def query_modality_candidates() -> tuple[
    list[dict[str, Any]],
    dict[str, int],
    dict[str, str],
    dict[str, list[dict[str, Any]]],
]:
    """Query generative-media and speech task pools that are sparse globally."""
    rows: dict[str, dict[str, Any]] = {}
    role_ids = {role: set() for role in MODALITY_QUERY_FILTERS}
    trending_by_pipeline: dict[str, dict[str, dict[str, Any]]] = {
        pipeline: {}
        for pipelines in MODALITY_QUERY_FILTERS.values()
        for pipeline in pipelines
    }
    errors: dict[str, str] = {}

    def query(
        role: str,
        pipeline: str,
        sort: str,
    ) -> tuple[str, str, str, list[dict[str, Any]], str | None]:
        params = [
            ("filter", pipeline),
            ("sort", sort),
            ("direction", "-1"),
            ("limit", str(MODALITY_QUERY_LIMIT)),
        ]
        try:
            result = hf_api(expanded_model_query(params), retries=0)
        except Exception as exc:
            return role, pipeline, sort, [], type(exc).__name__
        return role, pipeline, sort, result if isinstance(result, list) else [], None

    queries = [
        (role, pipeline, sort)
        for role, pipelines in MODALITY_QUERY_FILTERS.items()
        for pipeline in pipelines
        for sort in ("trendingScore", "lastModified")
    ]
    with ThreadPoolExecutor(max_workers=min(12, len(queries))) as executor:
        results = executor.map(lambda values: query(*values), queries)
        for role, pipeline, sort, result, error in results:
            if error:
                errors[f"modality:{role}:{pipeline}:{sort}"] = error
                continue
            for row in result:
                model_id = str(row.get("id") or "")
                if not model_id:
                    continue
                rows.setdefault(model_id, row)
                role_ids[role].add(model_id)
                if sort == "trendingScore":
                    trending_by_pipeline[pipeline].setdefault(model_id, row)
    counts = {role: len(model_ids) for role, model_ids in role_ids.items()}
    return (
        list(rows.values()),
        counts,
        errors,
        {
            f"task:{pipeline}": list(pipeline_rows.values())
            for pipeline, pipeline_rows in trending_by_pipeline.items()
        },
    )


def query_media_ecosystem_candidates() -> tuple[list[dict[str, Any]], dict[str, int], dict[str, str]]:
    """Query local media runtimes whose repositories may omit a standard pipeline tag."""
    rows: dict[str, dict[str, Any]] = {}
    query_filters = MEDIA_ECOSYSTEM_FILTERS + MEDIA_CUSTOMIZATION_QUERY_FILTERS
    counts = {value: 0 for value in query_filters}
    errors: dict[str, str] = {}

    def query(value: str, sort: str) -> tuple[str, str, list[dict[str, Any]], str | None]:
        params = [
            ("filter", value),
            ("sort", sort),
            ("direction", "-1"),
            ("limit", str(MODALITY_QUERY_LIMIT)),
        ]
        try:
            result = hf_api(expanded_model_query(params), retries=0)
        except Exception as exc:
            return value, sort, [], type(exc).__name__
        return value, sort, result if isinstance(result, list) else [], None

    queries = [
        (value, sort)
        for value in query_filters
        for sort in ("trendingScore", "lastModified")
    ]
    seen_by_filter = {value: set() for value in query_filters}
    with ThreadPoolExecutor(max_workers=min(12, len(queries) or 1)) as executor:
        for value, sort, result, error in executor.map(lambda values: query(*values), queries):
            if error:
                errors[f"media-ecosystem:{value}:{sort}"] = error
                continue
            for row in result:
                model_id = str(row.get("id") or "")
                if not model_id:
                    continue
                rows.setdefault(model_id, row)
                seen_by_filter[value].add(model_id)
    counts.update({value: len(model_ids) for value, model_ids in seen_by_filter.items()})
    return list(rows.values()), counts, errors


def query_global_models() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    errors: dict[str, str] = {}

    def query(sort: str, limit: int) -> tuple[str, list[dict[str, Any]], str | None]:
        params = [
            ("sort", sort),
            ("direction", "-1"),
            ("limit", str(limit)),
        ]
        try:
            result = hf_api(expanded_model_query(params), retries=0)
        except Exception as exc:
            return sort, [], type(exc).__name__
        return sort, result if isinstance(result, list) else [], None

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(query, "trendingScore", GLOBAL_TRENDING_LIMIT),
            executor.submit(query, "lastModified", GLOBAL_RECENT_LIMIT),
        ]
        results = [future.result() for future in futures]

    by_sort = {sort: rows for sort, rows, _ in results}
    for sort, _, error in results:
        if error:
            errors[f"global:{sort}"] = error
    return by_sort.get("trendingScore", []), by_sort.get("lastModified", []), errors


def popularity_values(row: dict[str, Any]) -> tuple[float, int, int]:
    return (
        float(row.get("trendingScore") or 0),
        int(row.get("downloads") or 0),
        int(row.get("likes") or 0),
    )


def is_hot_local(row: dict[str, Any]) -> bool:
    trending, downloads, likes = popularity_values(row)
    if model_role(row) == "robotics":
        task_ranks = (row.get("_trend") or {}).get("rankings") or {}
        if any(
            scope == "task:robotics"
            and isinstance(value.get("rank"), int)
            and value["rank"] <= 20
            for scope, value in task_ranks.items()
        ) and (downloads >= MODALITY_HOT_DOWNLOADS or likes >= MODALITY_HOT_LIKES):
            return True
    if model_role(row) in MODALITY_FOCUS_ROLES:
        return trending >= MODALITY_HOT_TRENDING and (
            downloads >= MODALITY_HOT_DOWNLOADS or likes >= MODALITY_HOT_LIKES
        )
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


def is_hot_discovery(row: dict[str, Any]) -> bool:
    trending, downloads, likes = popularity_values(row)
    if model_role(row) in MODALITY_FOCUS_ROLES:
        return trending >= MODALITY_HOT_TRENDING and (
            downloads >= MODALITY_HOT_DOWNLOADS or likes >= MODALITY_HOT_LIKES
        )
    return trending >= DISCOVERY_HOT_TRENDING and (
        downloads >= DISCOVERY_HOT_DOWNLOADS or likes >= DISCOVERY_HOT_LIKES
    )


def is_hot_media_discovery(row: dict[str, Any]) -> bool:
    trending, downloads, likes = popularity_values(row)
    return trending >= MODALITY_HOT_TRENDING and (
        downloads >= MODALITY_HOT_DOWNLOADS or likes >= MODALITY_HOT_LIKES
    )


def media_activity_density(
    row: dict[str, Any],
    event: tuple[str, str] | None,
    observed_on: dt.date,
) -> dict[str, Any]:
    """Expose transparent activity signals instead of an opaque composite score."""
    trending, downloads, likes = popularity_values(row)
    created = iso_date(row.get("createdAt"))
    age_days = max(1, (observed_on - created).days + 1) if created else None
    downloads_per_day = round(downloads / age_days, 1) if age_days and age_days <= 120 else None
    likes_per_day = round(likes / age_days, 2) if age_days and age_days <= 120 else None
    trend = row.get("_trend") or {}
    signals: list[str] = []
    if trending >= DISCOVERY_HOT_TRENDING:
        signals.append("high-trending")
    if event and trending >= MODALITY_HOT_TRENDING and (
        downloads >= MODALITY_HOT_DOWNLOADS or likes >= MODALITY_HOT_LIKES
    ):
        signals.append("recent-repository-activity")
    if downloads_per_day is not None and downloads_per_day >= 1_000:
        signals.append("high-download-velocity")
    if likes_per_day is not None and likes_per_day >= 5:
        signals.append("high-like-velocity")
    if int(trend.get("downloads_delta") or 0) >= 1_000:
        signals.append("downloads-growing")
    if int(trend.get("likes_delta") or 0) >= 10:
        signals.append("likes-growing")
    if int(trend.get("rank_delta") or 0) >= 10:
        signals.append("rank-rising")
    return {
        "high_activity": bool(signals),
        "signals": signals,
        "repository_age_days": age_days,
        "downloads_per_day": downloads_per_day,
        "likes_per_day": likes_per_day,
    }


def local_signal(
    row: dict[str, Any],
    start: dt.date,
    end: dt.date,
    include_persistent_hot: bool = True,
) -> tuple[str, str] | None:
    event = event_in_window(row, start, end)
    if event:
        return event
    if include_persistent_hot and is_hot_local(row):
        return "trending-observed", end.isoformat()
    return None


def watched_flagship_items(
    flagship: dict[str, dict[str, Any]],
    model_rows: dict[str, dict[str, Any]],
    references: dict[str, dict[str, Any]],
    registry: dict[str, Any],
    start: dt.date,
    end: dt.date,
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Keep active canonical lines visible when their own repository is unchanged."""
    ranked: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    for model_id, record in flagship.items():
        row = model_rows.get(model_id)
        if row is None or event_in_window(row, start, end):
            continue
        activity = references.get(model_id) or {}
        trend = row.get("_trend") or {}
        ranks = trend.get("rankings") or {}
        global_rank = (ranks.get("global") or {}).get("rank")
        task_rank = min(
            (int(value["rank"]) for scope, value in ranks.items()
             if scope.startswith("task:") and isinstance(value.get("rank"), int)),
            default=None,
        )
        own_hot = is_hot_local(row) and (
            isinstance(global_rank, int) and global_rank <= 100
            or isinstance(task_rank, int) and task_rank <= 20
            or bool({"hf-rank-rising", "hf-engagement-growing"} & set(trend.get("signals") or []))
        )
        audio_engagement = (
            record.get("role") == "audio-generation"
            and bool((registry.get("model_overrides") or {}).get(model_id, {}).get("audio_tasks"))
            and int(row.get("likes") or 0) >= 50
        )
        registered_audio_tasks = set(
            (registry.get("model_overrides") or {}).get(model_id, {}).get("audio_tasks") or []
        )
        multimodal_audio_reference = (
            record.get("role") == "audio-generation"
            and {"text-to-sfx", "video-to-sfx"} <= registered_audio_tasks
            and bool({"music-generation", "song-generation"} & registered_audio_tasks)
        )
        ref_count = int(activity.get("direct_references_observed") or 0)
        active_children = activity.get("active_derivative_ids") or []
        derivative_activity = ref_count >= 3 and bool(active_children)
        if not own_hot and not audio_engagement and not multimodal_audio_reference and not derivative_activity:
            continue
        event_name = (
            "trending-observed" if own_hot else
            "engagement-observed" if audio_engagement else
            "capability-observed" if multimodal_audio_reference else "derivatives-observed"
        )
        selection = ["canonical-watch"]
        if own_hot:
            selection.append("current-hot")
        if audio_engagement:
            selection.append("current-engagement")
        if multimodal_audio_reference:
            selection.append("multimodal-audio-reference")
        if derivative_activity:
            selection.append("active-derivatives")
        item = model_item(
            row,
            {**record, "selection": selection, "ecosystem_activity": activity},
            registry,
            (event_name, end.isoformat()),
        )
        score = (
            bool({"hf-rank-rising", "hf-engagement-growing"} & set(trend.get("signals") or [])),
            len(active_children),
            ref_count,
            int(row.get("trendingScore") or 0),
            model_id,
        )
        ranked.append((score, item))
    return [item for _, item in sorted(ranked, key=lambda value: value[0], reverse=True)[:limit]]


def registered_local_selection(
    row: dict[str, Any],
    event: tuple[str, str] | None,
    priority: bool,
    include_current_hot: bool,
) -> list[str] | None:
    if event is None:
        return None
    if include_current_hot:
        if not is_hot_local(row):
            return None
        return (["priority"] if priority else []) + ["hot"]
    return ["priority"] if priority else None


def model_role(row: dict[str, Any], default: str = "unknown") -> str:
    pipeline = str(row.get("pipeline_tag") or "")
    capabilities = set(capability_facets(row))
    enhancement_tags = {"image-upscaling", "image-super-resolution", "super-resolution", "image-restoration", "deblurring", "video-upscaling", "video-super-resolution", "video-restoration", "frame-interpolation"}
    if lower_tags(row) & enhancement_tags:
        return "media-enhancement"
    if "ocr" in capabilities:
        return "ocr"
    if {"typed-decisions", "structured-prediction"} <= lower_tags(row):
        return "decision"
    if pipeline == "translation":
        return "translation"
    if pipeline == "sentence-similarity":
        return "embedding"
    if pipeline == "robotics":
        return "robotics"
    if pipeline == "any-to-any":
        return "vlm"
    modalities = modality_evidence(row)
    inputs = set(modalities["input"])
    outputs = set(modalities["output"])
    if outputs & {"mask", "pose", "motion", "depth", "face", "landmarks"}:
        return "media-conditioning"
    if "video" in outputs:
        return "video-generation"
    if "image" in outputs:
        return "image-generation"
    if pipeline == "text-to-speech" or "tts" in capabilities:
        return "audio-tts"
    if "audio" in outputs:
        return "audio-generation"
    if "robotics" in outputs or "robotics" in inputs:
        return "robotics"
    if outputs == {"text"} and inputs & {"image", "video"}:
        return "vlm"
    if outputs == {"text"} and "audio" in inputs:
        return "audio-stt"
    if outputs == {"text"} and "text" in inputs:
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
    roots: set[str] = set()
    for _ in range(max_depth):
        next_frontier: list[dict[str, Any]] = []
        for current in frontier:
            links = base_model_links(current)
            if len({base_id for base_id, _ in links}) > 1:
                return None
            for base_id, _ in links:
                if base_id in root_ids:
                    roots.add(base_id)
                    continue
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
    if len(roots) == 1:
        root = next(iter(roots))
        return root, model_rows.get(root)
    return None


def local_discovery_items(
    rows: list[dict[str, Any]],
    registry: dict[str, Any],
    model_rows: dict[str, dict[str, Any]],
    start: dt.date,
    end: dt.date,
    known_ids: set[str],
    include_persistent_hot: bool = True,
) -> list[dict[str, Any]]:
    if not include_persistent_hot:
        return []
    flagship = flagship_index(registry)
    baseline_records = {
        str(entry["id"]): {**entry, "role": role}
        for role, entries in registry.get("ecosystem_baseline_models", {}).items()
        for entry in entries
    }
    root_ids = (set(flagship)
                | {str(entry["id"]) for entries in registry.get("ecosystem_baseline_models", {}).values()
                   for entry in entries}
                | {str(value) for value in registry.get("local_roots", [])})
    local_publishers = {str(value) for value in registry.get("local_publishers", [])}
    items: list[dict[str, Any]] = []
    for row in rows:
        model_id = str(row.get("id") or "")
        if not model_id or model_id in known_ids:
            continue
        event = local_signal(row, start, end, include_persistent_hot)
        deployment = set(deployment_facets(row))
        derivation = set(derivation_facets(row))
        alignment = alignment_facet(row)
        if (
            not event
            or not (
                deployment & LOCAL_DEPLOYMENTS
                or derivation & DERIVATIVE_RELATIONS
                or alignment
            )
            or not is_hot_local(row)
        ):
            continue
        matched = find_local_root(row, root_ids, model_rows)
        canonical, inherited = matched if matched else (None, None)
        if inherited is None:
            direct_links = base_model_links(row)
            if len({base_id for base_id, _ in direct_links}) == 1:
                base_id, relation = direct_links[0]
                base_row = model_rows.get(base_id)
                if base_row is not None:
                    inherited = base_row
                    if relation in DERIVATIVE_RELATIONS:
                        canonical = base_id
        publisher = model_id.split("/", 1)[0]
        trusted_publisher = publisher in local_publishers
        breakout = is_breakout_local(row)
        derivative = bool(derivation & DERIVATIVE_RELATIONS)
        low_refusal = bool(alignment)
        if (
            canonical is None
            and not trusted_publisher
            and not breakout
            and not derivative
            and not low_refusal
        ):
            continue
        base_record = flagship.get(str(canonical or ""), baseline_records.get(str(canonical or ""), {}))
        selection = ["hot"]
        if canonical:
            selection.append("flagship-lineage")
        if trusted_publisher:
            selection.append("trusted-publisher")
        if publisher in local_publishers:
            selection.append("local-ecosystem-publisher")
        if breakout:
            selection.append("breakout")
        if derivative:
            selection.append("derivative")
        if low_refusal:
            selection.append("low-refusal")
        if media_customization_facet(row):
            selection.append("media-customization")
        inherited_role = model_role(inherited, default="llm") if inherited else "llm"
        role = base_record.get("role") or model_role(row, default=inherited_role)
        if role in MODALITY_FOCUS_ROLES:
            selection.append("modality-radar")
        record = {
            "id": model_id,
            "track": "local",
            "role": role,
            "family": base_record.get("family"),
            "canonical": canonical,
            "selection": selection,
            "publisher_tier": publisher_tier(model_id, registry),
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
    allow_unregistered_hot: bool = True,
) -> list[dict[str, Any]]:
    owner_family_candidates: dict[str, list[str]] = {}
    for entry in registry.get("families", []):
        owner_family_candidates.setdefault(str(entry["owner"]), []).append(str(entry["id"]))
    owner_families = {
        owner: family_ids[0]
        for owner, family_ids in owner_family_candidates.items()
        if len(family_ids) == 1
    }
    registered_owners = set(owner_family_candidates)
    items: list[dict[str, Any]] = []
    for row in rows:
        model_id = str(row.get("id") or "")
        event = event_in_window(row, start, end)
        if not model_id or model_id in known_ids or not event:
            continue
        owner = model_id.split("/", 1)[0]
        registered_owner = owner in registered_owners
        if not registered_owner and (
            not allow_unregistered_hot or not is_hot_discovery(row)
        ):
            continue
        if not registered_owner and (
            set(deployment_facets(row)) & LOCAL_DEPLOYMENTS
            or set(derivation_facets(row)) & DERIVATIVE_RELATIONS
        ):
            continue
        role = model_role(row)
        selection = ["pending-registry"]
        if registered_owner:
            selection.append("trusted-publisher")
        else:
            selection.extend(["hot", "global-discovery"])
        if role in MODALITY_FOCUS_ROLES:
            selection.append("modality-radar")
        if media_customization_facet(row):
            selection.append("media-customization")
        record = {
            "id": model_id,
            "track": "discovery",
            "role": role,
            "family": owner_families.get(owner),
            "selection": selection,
            "pending_registry": True,
            "publisher_tier": publisher_tier(model_id, registry),
        }
        items.append(
            model_item(row, record, registry, event)
        )
    return sorted(items, key=notable_model_sort_key, reverse=True)


def media_customization_items(
    rows: list[dict[str, Any]],
    registry: dict[str, Any],
    start: dt.date,
    end: dt.date,
    include_current_hot: bool = True,
) -> list[dict[str, Any]]:
    """Build a bounded prefetch pool for the ComfyUI media workflow radar."""
    items: list[dict[str, Any]] = []
    for row in rows:
        facet = media_customization_facet(row)
        modalities = modality_evidence(row)
        structured_inputs = set(modalities["input"])
        structured_outputs = set(modalities["output"])
        model_id = str(row.get("id") or "")
        if (
            not model_id
            or "comfyui" not in set(deployment_facets(row))
        ):
            continue
        # Conditioning outputs and explicit face-swap editing belong in the
        # workflow. Generic image generation/editing remains in the model radar.
        workflow_outputs = {"video", "mask", "pose", "motion", "depth", "face", "landmarks"}
        image_workflow = bool({"face-swap", "image-enhancement"} & set(facet.get("capabilities") or []))
        if structured_outputs and not (structured_outputs & workflow_outputs or ("image" in structured_outputs and image_workflow)):
            continue
        if structured_outputs and not (structured_inputs & {"image", "audio", "video"}):
            continue
        if structured_outputs and not facet:
            continue
        event = event_in_window(row, start, end)
        activity = media_activity_density(row, event, end)
        hot = include_current_hot and (
            is_hot_media_discovery(row) or bool(activity.get("high_activity"))
        )
        if not event and hot:
            event = ("trending-observed", end.isoformat())
        if not event:
            continue
        role = model_role(row)
        selection = ["media-workflow", "pending-registry"]
        if hot:
            selection.append("hot")
        if activity.get("high_activity"):
            selection.append("open-activity")
        selection.append("comfyui-ecosystem")
        record = {
            "id": model_id,
            "track": "discovery",
            "role": role,
            "selection": selection,
            "pending_registry": True,
            "publisher_tier": publisher_tier(model_id, registry),
        }
        item = model_item(row, record, registry, event)
        item["metadata"]["activity_density"] = activity
        items.append(item)
    items.sort(key=notable_model_sort_key, reverse=True)
    confirmed = [
        item
        for item in items
        if ((item.get("metadata") or {}).get("media_customization") or {}).get(
            "capabilities"
        )
    ]
    unknown = [
        item
        for item in items
        if not ((item.get("metadata") or {}).get("modalities") or {}).get("signals")
        and not ((item.get("metadata") or {}).get("media_customization") or {}).get(
            "capabilities"
        )
    ][:MEDIA_CUSTOMIZATION_UNKNOWN_PREFETCH_LIMIT]
    prefetched: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    confirmed_limit = MEDIA_CUSTOMIZATION_PREFETCH_LIMIT - len(unknown)
    balanced_confirmed: list[dict[str, Any]] = []
    balanced_ids: set[str] = set()
    for lane in (
        "media-conditioning",
        "image-to-video",
        "character-animation",
        "audio-driven-avatar",
        "video-editing-effects",
        "media-enhancement",
    ):
        candidate = next(
            (
                item
                for item in confirmed
                if item["title"] not in balanced_ids
                and lane
                in set(
                    ((item.get("metadata") or {}).get("media_customization") or {}).get(
                        "lanes", []
                    )
                )
            ),
            None,
        )
        if candidate is not None:
            balanced_confirmed.append(candidate)
            balanced_ids.add(str(candidate["title"]))
    for item in confirmed:
        if len(balanced_confirmed) >= confirmed_limit:
            break
        if item["title"] in balanced_ids:
            continue
        balanced_confirmed.append(item)
        balanced_ids.add(str(item["title"]))
    for item in balanced_confirmed + unknown:
        if item["title"] in seen_ids:
            continue
        prefetched.append(item)
        seen_ids.add(item["title"])
        if len(prefetched) >= MEDIA_CUSTOMIZATION_PREFETCH_LIMIT:
            break
    return sorted(prefetched, key=notable_model_sort_key, reverse=True)


def build_comfyui_integration_guidance(item: dict[str, Any]) -> dict[str, Any]:
    """Describe a capability-based ComfyUI topology without claiming validation."""
    metadata = item.get("metadata") or {}
    customization = metadata.get("media_customization") or {}
    lanes = set(customization.get("lanes") or [])
    modalities = metadata.get("modalities") or {}
    profile = metadata.get("deployment_profile") or {}
    upstream: list[str] = []
    downstream: list[str] = []
    if "media-conditioning" in lanes:
        upstream.extend(["source-image-or-video", "select-subject-or-control-region"])
        downstream.extend(["mask-pose-depth-or-motion-control", "animation-or-editing-workflow"])
    if "image-to-video" in lanes:
        upstream.extend(["source-image", "resize-crop-or-pad", "image-or-vision-encoder"])
    if "character-animation" in lanes:
        upstream.extend(["character-reference", "pose-motion-or-camera-control"])
    if "audio-driven-avatar" in lanes:
        upstream.extend(
            [
                "portrait-or-reference-video",
                "audio-cleanup-and-model-required-resampling",
            ]
        )
    if "video-editing-effects" in lanes:
        upstream.extend(["source-image-or-video", "optional-mask-reference-or-control-signal"])
    if "media-enhancement" in lanes:
        upstream.extend(["source-image-or-video", "target-resolution-or-frame-rate"])
        downstream.extend(["quality-check-at-original-and-output-size", "final-export"])
    output_modalities = set(modalities.get("output") or [])
    if "video" in output_modalities or (not output_modalities and lanes - {"media-conditioning"}):
        downstream.extend(
            [
                "frame-interpolation-if-needed",
                "video-upscale-or-restoration",
                "audio-mux",
                "video-encode",
            ]
        )
    elif "image" in output_modalities and "video-editing-effects" in lanes:
        downstream.extend(["face-blend-or-restoration", "image-export-or-video-frame-reassembly"])
    return {
        "input_modalities": list(modalities.get("input") or []),
        "output_modalities": list(modalities.get("output") or []),
        "upstream": list(dict.fromkeys(upstream)),
        "core": {
            "runtime": "comfyui",
            "capabilities": list(customization.get("capabilities") or []),
            "components": [
                str(component.get("type") or "")
                for component in profile.get("components") or []
                if component.get("type")
            ],
            "dependencies": [
                str(dependency.get("repo_id") or "")
                for dependency in profile.get("dependencies") or []
                if dependency.get("repo_id")
            ],
        },
        "downstream": list(dict.fromkeys(downstream)),
        "workflow_files": list(profile.get("workflow_files") or []),
        "topology_source": "capability-template",
        "workflow_status": (
            "repository-workflow-present"
            if profile.get("workflow_files")
            else "recommended-topology-not-validated-workflow"
        ),
    }


def attach_media_discovery_tracks(item: dict[str, Any]) -> dict[str, Any]:
    """Expose independent community activity without comparing a consumer registry."""
    metadata = dict(item.get("metadata") or {})
    activity = metadata.get("activity_density") or {}
    tracks = ["open-activity"] if activity.get("high_activity") else []
    metadata["discovery_tracks"] = tracks
    selection = list(metadata.get("selection") or [])
    selection.extend(track for track in tracks if track not in selection)
    metadata["selection"] = selection
    return {**item, "metadata": metadata}


def finalize_media_customization_items(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Keep verified ComfyUI workflow capabilities and balance activity and lanes."""
    eligible: list[dict[str, Any]] = []
    for item in items:
        metadata = item.get("metadata") or {}
        customization = metadata.get("media_customization") or {}
        capabilities = set(customization.get("capabilities") or [])
        profile = metadata.get("deployment_profile") or {}
        runtimes = set(profile.get("runtimes") or metadata.get("deployment") or [])
        signals = customization.get("signals") or []
        outputs = set((metadata.get("modalities") or {}).get("output") or [])
        if "comfyui" not in runtimes or not capabilities:
            continue
        workflow_outputs = {"video", "mask", "pose", "motion", "depth", "face", "landmarks"}
        image_workflow = "image" in outputs and bool({"face-swap", "image-enhancement"} & capabilities)
        if outputs and not (outputs & workflow_outputs or image_workflow):
            continue
        if not outputs and not (capabilities & MEDIA_WORKFLOW_PRIMARY_CAPABILITIES):
            continue
        if not outputs and not any(
            signal.get("source") in {"model-card", "upstream-model-card"}
            for signal in signals
        ):
            continue
        metadata["comfyui_integration"] = build_comfyui_integration_guidance(item)
        eligible.append(
            attach_media_discovery_tracks({**item, "metadata": metadata})
        )

    eligible.sort(key=notable_model_sort_key, reverse=True)
    eligible.sort(
        key=lambda item: (
            -len(
                ((item.get("metadata") or {}).get("activity_density") or {}).get(
                    "signals", []
                )
            ),
        )
    )
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    covered_lanes: set[str] = set()
    covered_capabilities: set[str] = set()

    def add(item: dict[str, Any]) -> None:
        customization = (item.get("metadata") or {}).get("media_customization") or {}
        selected.append(item)
        selected_ids.add(str(item["title"]))
        covered_lanes.update(customization.get("lanes") or [])
        covered_capabilities.update(customization.get("capabilities") or [])

    # Reserve space for transparent high-activity discoveries. Remaining slots
    # preserve capability-lane breadth without knowledge of any consumer system.
    open_added = 0
    for item in eligible:
        if item["title"] in selected_ids:
            continue
        tracks = set((item.get("metadata") or {}).get("discovery_tracks") or [])
        if "open-activity" not in tracks:
            continue
        add(item)
        open_added += 1
        if open_added >= MEDIA_OPEN_ACTIVITY_MIN or len(selected) >= MEDIA_CUSTOMIZATION_LIMIT:
            break

    for item in eligible:
        if item["title"] in selected_ids:
            continue
        lanes = set(
            ((item.get("metadata") or {}).get("media_customization") or {}).get(
                "lanes", []
            )
        )
        if lanes - covered_lanes:
            add(item)
        if len(selected) >= MEDIA_CUSTOMIZATION_LIMIT:
            break

    # Then add only models that contribute a capability not represented above.
    for item in eligible:
        if len(selected) >= MEDIA_CUSTOMIZATION_LIMIT:
            break
        if item["title"] in selected_ids:
            continue
        capabilities = set(
            ((item.get("metadata") or {}).get("media_customization") or {}).get(
                "capabilities", []
            )
        )
        if capabilities - covered_capabilities:
            add(item)
    return selected[:MEDIA_CUSTOMIZATION_LIMIT]


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


def query_dataset_candidates(
    owners: list[str],
    include_global: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, int], dict[str, str]]:
    specs: list[tuple[str, dict[str, str]]] = []
    if include_global:
        specs.extend(
            [
                (
                    "global:trending",
                    {
                        "sort": "trendingScore",
                        "direction": "-1",
                        "limit": str(DATASET_TRENDING_LIMIT),
                    },
                ),
                (
                    "global:recent",
                    {
                        "sort": "lastModified",
                        "direction": "-1",
                        "limit": str(DATASET_RECENT_LIMIT),
                    },
                ),
            ]
        )
    specs.extend(
        (
            f"owner:{owner}",
            {
                "author": owner,
                "sort": "lastModified",
                "direction": "-1",
                "limit": str(DATASET_OWNER_LIMIT),
            },
        )
        for owner in owners
    )

    def query(spec: tuple[str, dict[str, str]]) -> tuple[str, list[dict[str, Any]], str | None]:
        key, params = spec
        query_string = urllib.parse.urlencode({**params, "full": "true"})
        try:
            result = hf_api("/api/datasets?" + query_string, retries=0)
        except Exception as exc:
            return key, [], type(exc).__name__
        return key, result if isinstance(result, list) else [], None

    rows: dict[str, dict[str, Any]] = {}
    counts = {"trending": 0, "recent": 0, "official_owner": 0}
    errors: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=min(12, len(specs) or 1)) as executor:
        for key, result, error in executor.map(query, specs):
            if error:
                errors[f"dataset:{key}"] = error
                continue
            if key == "global:trending":
                counts["trending"] = len(result)
            elif key == "global:recent":
                counts["recent"] = len(result)
            else:
                counts["official_owner"] += len(result)
            for row in result:
                dataset_id = str(row.get("id") or "")
                if dataset_id:
                    rows.setdefault(dataset_id, row)
    counts["union"] = len(rows)
    return list(rows.values()), counts, errors


def dataset_item(row: dict[str, Any], record: dict[str, Any], event: tuple[str, str]) -> dict[str, Any]:
    dataset_id = str(row.get("id") or record["id"])
    event_name, date = event
    uses = [str(value) for value in record.get("uses", [])]
    use_text = "、".join(uses) if uses else "开放数据"
    pending_registry = bool(record.get("pending_registry"))
    if pending_registry:
        discovery_kind = (
            "HF 热门新数据集"
            if "hot" in record.get("selection", [])
            else "已登记官方发布者的新数据集"
        )
        summary = (
            f"{dataset_id.split('/')[-1]} 是本窗口命中的{discovery_kind}，"
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
            "papers": paper_links(row),
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
    trusted_owners: set[str],
    start: dt.date,
    end: dt.date,
    allow_hot_discovery: bool = True,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for row in rows:
        dataset_id = str(row.get("id") or "")
        event = event_in_window(row, start, end)
        owner = dataset_id.split("/", 1)[0]
        hot = allow_hot_discovery and is_hot_dataset(row)
        trusted_owner = owner in trusted_owners
        if not dataset_id or dataset_id in known_ids or not event or not (hot or trusted_owner):
            continue
        selection = ["pending-registry"]
        if hot:
            selection.append("hot")
        if trusted_owner:
            selection.append("trusted-publisher")
        record = {
            "id": dataset_id,
            "selection": selection,
            "pending_registry": True,
        }
        items.append(dataset_item(row, record, event))
    return sorted(items, key=notable_dataset_sort_key, reverse=True)


def strip_live_popularity(items: Iterable[dict[str, Any]]) -> None:
    for item in items:
        metadata = item.get("metadata") or {}
        for key in ("trendingScore", "downloads", "likes", "trend"):
            metadata.pop(key, None)


def native_trend_sort_key(metadata: dict[str, Any]) -> tuple[Any, ...]:
    trend = metadata.get("trend") or {}
    signals = set(trend.get("signals") or [])
    rankings = trend.get("rankings") or {}
    global_ranking = rankings.get("global") or {}
    global_rank = (
        int(global_ranking["rank"])
        if isinstance(global_ranking, dict) and isinstance(global_ranking.get("rank"), int)
        else 1_000_000
    )
    task_ranks = [
        int(value["rank"])
        for scope, value in rankings.items()
        if str(scope).startswith("task:")
        if isinstance(value, dict) and isinstance(value.get("rank"), int)
    ]
    best_task_rank = min(task_ranks) if task_ranks else 1_000_000

    def rank_tier(rank: int) -> int:
        return 3 if rank <= 10 else 2 if rank <= 50 else 1 if rank <= 200 else 0

    return (
        "hf-rank-rising" in signals,
        "hf-engagement-growing" in signals,
        rank_tier(global_rank),
        rank_tier(best_task_rank),
        -global_rank,
        -best_task_rank,
    )


def notable_model_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    metadata = item.get("metadata") or {}
    selection = metadata.get("selection") or []
    return (
        *native_trend_sort_key(metadata),
        "trusted-publisher" in selection,
        int(metadata.get("trendingScore") or 0),
        int(metadata.get("likes") or 0),
        int(metadata.get("downloads") or 0),
        item.get("event") == "published",
        item.get("date", ""),
        item.get("title", ""),
    )


def notable_dataset_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    metadata = item.get("metadata") or {}
    return (
        "trusted-publisher" in (metadata.get("selection") or []),
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


def select_diverse_datasets(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    ranked = sorted(items, key=notable_dataset_sort_key, reverse=True)
    selected: list[dict[str, Any]] = []
    selected_titles: set[str] = set()
    owner_counts: dict[str, int] = {}

    def add(item: dict[str, Any], owner_cap: int | None) -> bool:
        title = str(item.get("title") or "")
        owner = title.split("/", 1)[0]
        if not title or title in selected_titles:
            return False
        if owner_cap is not None and owner_counts.get(owner, 0) >= owner_cap:
            return False
        selected.append(item)
        selected_titles.add(title)
        owner_counts[owner] = owner_counts.get(owner, 0) + 1
        return True

    for item in ranked:
        selection = (item.get("metadata") or {}).get("selection") or []
        if "trusted-publisher" in selection:
            add(item, 1)
        if len(selected) >= min(limit, NOTABLE_TRUSTED_DATASET_MAX):
            break

    for item in ranked:
        selection = (item.get("metadata") or {}).get("selection") or []
        hot_count = sum(
            "hot" in ((entry.get("metadata") or {}).get("selection") or [])
            for entry in selected
        )
        if hot_count >= NOTABLE_HOT_DATASET_MIN:
            break
        if "hot" in selection:
            add(item, 2)

    for owner_cap in (1, 2, None):
        for item in ranked:
            add(item, owner_cap)
            if len(selected) >= limit:
                return selected
    return selected


def select_notable_discoveries(
    models: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    selected_models = select_diverse_models(models, NOTABLE_DISCOVERY_MAX)
    total = len(selected_models)
    if total < NOTABLE_DISCOVERY_MIN:
        missing = NOTABLE_DISCOVERY_MIN - total
        selected_titles = {str(item.get("title") or "") for item in selected_models}
        extra_models = [
            item
            for item in sorted(models, key=notable_model_sort_key, reverse=True)
            if str(item.get("title") or "") not in selected_titles
        ][:missing]
        selected_models.extend(extra_models)
    return {"models": selected_models}


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
        line = re.sub(r"\\([\\`*_{}\[\]()#+.!-])", r"\1", line)
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


def normalize_heading(value: str) -> str:
    value = value.replace("\\-", "-").strip().lower()
    value = re.sub(r"[*_`]+", "", value)
    return re.sub(r"\s+", " ", value).strip(" :")


def compact_markdown_evidence(text: str, limit: int) -> str:
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    output: list[str] = []
    for raw_line in text.splitlines():
        line = html.unescape(raw_line).strip()
        line = re.sub(r"\\([\\`*_{}\[\]()#+.!-])", r"\1", line)
        line = re.sub(r"^#{1,6}\s+", "", line)
        line = re.sub(r"^[-*+]\s+", "", line)
        line = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", line)
        line = re.sub(r"\s+", " ", line).strip()
        if not line or re.fullmatch(r"\|?\s*:?-+:?\s*(?:\|\s*:?-+:?\s*)+\|?", line):
            continue
        if line.startswith("|") and line.endswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            line = " | ".join(cell for cell in cells if cell)
        if line and (not output or output[-1] != line):
            output.append(line)
    excerpt = "\n".join(output).strip()
    if len(excerpt) > limit:
        excerpt = excerpt[:limit].rsplit(" ", 1)[0].rstrip() + "…"
    return excerpt


def markdown_section(text: str, heading_match: Callable[[str], bool]) -> str:
    lines = text.splitlines()
    for index, raw_line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", raw_line.strip())
        if not match or not heading_match(normalize_heading(match.group(2))):
            continue
        level = len(match.group(1))
        section: list[str] = []
        for candidate in lines[index + 1 :]:
            next_heading = re.match(r"^(#{1,6})\s+", candidate.strip())
            if next_heading and len(next_heading.group(1)) <= level:
                break
            section.append(candidate)
        return "\n".join(section)
    return ""


def extract_architecture_excerpt(text: str) -> str:
    lines = text.splitlines()
    for target_heading in ["architecture overview", "model architecture", "architecture"]:
        for index, raw_line in enumerate(lines):
            match = re.match(r"^(#{2,4})\s+(.+?)\s*$", raw_line.strip())
            if not match or normalize_heading(match.group(2)) != target_heading:
                continue
            level = len(match.group(1))
            section: list[str] = []
            for candidate in lines[index + 1 :]:
                next_heading = re.match(r"^(#{1,6})\s+", candidate.strip())
                if next_heading and len(next_heading.group(1)) <= level:
                    break
                section.append(candidate)
            excerpt = extract_card_excerpt("\n".join(section))
            if excerpt:
                return excerpt
    return ""


def is_evaluation_heading(value: str) -> bool:
    return bool(
        re.search(r"\b(?:evaluation|eval results?|benchmarks?|benchmark results?|leaderboard)\b", value)
    )


def extract_benchmark_table_context(text: str) -> str:
    lines = text.splitlines()
    for index, raw_line in enumerate(lines):
        line = raw_line.strip().lower()
        if not line.startswith("|") or not re.search(r"\bbenchmark\b", line):
            continue
        start = max(0, index - 3)
        end = index
        while end < len(lines) and (not lines[end].strip() or lines[end].lstrip().startswith("|")):
            end += 1
        while end < len(lines) and not re.match(r"^#{1,6}\s+", lines[end].strip()):
            end += 1
        return "\n".join(lines[start:end])
    return ""


def extract_evaluation_evidence(text: str) -> dict[str, str]:
    section = markdown_section(text, is_evaluation_heading)
    if not section:
        section = extract_benchmark_table_context(text)
    excerpt = compact_markdown_evidence(section, EVALUATION_EXCERPT_CHARS) if section else ""
    caveat_section = markdown_section(
        text,
        lambda value: bool(re.search(r"\b(?:limitations?|caveats?)\b", value)),
    )
    caveats = (
        compact_markdown_evidence(caveat_section, EVALUATION_CAVEAT_CHARS)
        if caveat_section
        else ""
    )
    result: dict[str, str] = {}
    if excerpt:
        result["source"] = "model-card"
        result["excerpt"] = excerpt
    if caveats:
        result["caveats"] = caveats
    return result


def extract_media_deployment_evidence(text: str) -> dict[str, Any]:
    lower = text.lower()
    runtimes = {
        runtime
        for token, runtime in {
            "audio.cpp": "audio.cpp",
            "comfyui": "comfyui",
            "diffusers": "diffusers",
            "llama.cpp": "llama.cpp",
            "mlx": "mlx",
            "onnx": "onnx",
            "sglang": "sglang",
            "tensorrt": "tensorrt",
            "transformers": "transformers",
            "vllm": "vllm",
        }.items()
        if token in lower
    }
    precision_patterns = {
        "awq": r"\bawq\b",
        "bf16": r"\bbf16\b|bfloat16",
        "fp4": r"\b(?:fp4|mxfp4|nvfp4)\b",
        "fp8": r"\b(?:fp8|mxfp8)\b",
        "gptq": r"\bgptq\b",
        "int4": r"\bint4\b|\b4-bit\b",
        "int8": r"\bint8\b|\b8-bit\b",
        "q3": r"\bq3(?:_[a-z0-9]+)?\b",
        "q4": r"\bq4(?:_[a-z0-9]+)?\b",
        "q5": r"\bq5(?:_[a-z0-9]+)?\b",
        "q6": r"\bq6(?:_[a-z0-9]+)?\b",
        "q8": r"\bq8(?:_[a-z0-9]+)?\b",
    }
    precisions = {
        precision
        for precision, pattern in precision_patterns.items()
        if re.search(pattern, lower, flags=re.IGNORECASE)
    }
    acceleration_patterns = {
        "distilled": r"\bdistill(?:ed|ation)?\b",
        "lightning": r"\blightning\b",
        "lcm": r"\blcm\b",
        "turbo": r"\bturbo\b",
    }
    acceleration = {
        value
        for value, pattern in acceleration_patterns.items()
        if re.search(pattern, lower, flags=re.IGNORECASE)
    }
    step_values: set[int] = set()
    step_evidence: list[dict[str, Any]] = []
    for raw_line in text.splitlines():
        line = html.unescape(raw_line).strip()
        if not re.search(r"\b(?:nfe|inference|sampling|denois|distill|turbo|lightning|steps?)\b", line, re.I):
            continue
        values = {
            int(value)
            for value in re.findall(r"\b(\d{1,2})\s*(?:-|\s)?(?:steps?|nfe)\b", line, re.I)
            if 0 < int(value) <= 64
        }
        for value in sorted(values):
            step_values.add(value)
            if len(step_evidence) < 8:
                step_evidence.append(
                    {
                        "value": value,
                        "source": "model-card",
                        "evidence": compact_markdown_evidence(line, 180),
                    }
                )
    offload_patterns = {
        "cpu-offload": r"\bcpu[ _-]?offload\b|enable_model_cpu_offload",
        "device-map": r"\bdevice_map\b",
        "low-vram": r"\blow[ _-]?vram\b",
        "model-offload": r"\bmodel[ _-]?offload\b|offload_mode",
        "sequential-cpu-offload": r"\bsequential[ _-]?cpu[ _-]?offload\b|enable_sequential_cpu_offload",
    }
    offload = {
        value
        for value, pattern in offload_patterns.items()
        if re.search(pattern, lower, flags=re.IGNORECASE)
    }
    media_spec_evidence = [
        {
            "source": "model-card",
            "evidence": compact_markdown_evidence(html.unescape(line).strip(), 180),
        }
        for line in text.splitlines()
        if re.search(r"\b(?:resolution|upscal(?:e|ing)|super[ -]?resolution|frame[ -]?rate|fps|deblur|restoration)\b", line, re.I)
        and re.search(r"\b\d{3,4}\s*[x×]\s*\d{3,4}\b|\b\d{3,4}p\b|\b[248]x\b|\b\d{1,3}\s*fps\b", line, re.I)
    ][:8]
    customization_patterns = {
        "segmentation-mask": r"\b(?:segment anything|SAM 2|SAM 3|image segmentation|video segmentation|mask generation|object mask|video object segmentation)\b",
        "pose-extraction": r"\b(?:pose estimation|pose extraction|extract(?:s|ing)? (?:human |body )?pose|body keypoints)\b",
        "motion-extraction": r"\b(?:motion extraction|extract(?:s|ing)? (?:human |body )?motion|motion capture)\b",
        "depth-map": r"\b(?:depth estimation|depth map)\b",
        "face-analysis": r"\b(?:face detection|facial landmarks|face landmarks|face analysis)\b",
        "image-to-video": r"\bimage[ -]to[ -]video\b|\bi2v\b",
        "reference-to-video": r"\breference[ -]to[ -]video\b|\breference image(?:s)?[^\n]{0,80}\bvideo\b",
        "keyframe-control": r"\bfirst[ -](?:and|/)[ -]?last[ -]frame\b|\bstart[ -](?:and|/)[ -]?end[ -]frame\b",
        "character-animation": r"\bcharacter animation\b|\bhuman animation\b|\banimat(?:e|ing)[^\n]{0,40}\bcharacter\b",
        "motion-control": r"\b(?:camera|pose|trajectory|motion)[ -]control\b|\bcontrollable motion\b",
        "motion-transfer": r"\bmotion transfer\b|\btransfer(?:s|ring)?[^\n]{0,40}\bmotion\b",
        "audio-driven-video": r"\b(?:audio|speech)[ -](?:driven|to)[ -](?:avatar|video)\b|\bdriven by (?:the )?audio\b",
        "face-swap": r"\bface[ -]?swap(?:ping)?\b",
        "identity-consistency": r"\b(?:identity|character|subject)[ -]?(?:preserv(?:ing|ation)|consisten(?:cy|t))\b",
        "lip-sync": r"\blip[ -]?sync(?:hronization)?\b",
        "person-replacement": r"\b(?:person|character|human)[ -]?replacement\b|\breplace (?:a |the )?(?:person|character|human)\b",
        "talking-head": r"\btalking[ -]?head\b",
        "video-editing": r"\bvideo editing\b|\bvideo[ -]to[ -]video\b",
        "video-effects": r"\bvideo effects?\b|\bvideo (?:inpainting|outpainting|relighting)\b|\b(?:video|frames?)[^\n]{0,40}(?:background|object) replacement\b|\b(?:background|object) replacement[^\n]{0,40}(?:video|frames?)\b",
        "video-enhancement": r"\bframe interpolation\b|\bvideo upscal(?:e|ing)\b|\bvideo enhancement\b",
        "image-enhancement": r"\b(?:image|photo)[ -]?(?:upscal(?:e|ing)|super[ -]?resolution|restoration)\b|\b(?:deblur(?:ring)?|denois(?:e|ing)) (?:image|photo)\b",
    }
    customization_signals = [
        {
            "capability": capability,
            "source": "model-card",
            "value": match.group(0).lower(),
        }
        for capability, pattern in customization_patterns.items()
        for match in [re.search(pattern, text, flags=re.IGNORECASE)]
        if match
    ]

    dependency_cues = re.compile(
        r"\b(?:base model|original model|checkpoint|download|required?|requires?|need|text encoder|"
        r"vision encoder|image encoder|vae|vocoder|upscaler|lora|model file|weights?)\b",
        re.IGNORECASE,
    )
    dependencies: list[dict[str, str]] = []
    seen_dependencies: set[str] = set()
    reserved_hf_path_roots = {
        "blog",
        "blogs",
        "collections",
        "datasets",
        "docs",
        "models",
        "papers",
        "spaces",
        "tasks",
    }
    for raw_line in text.splitlines():
        if not dependency_cues.search(raw_line):
            continue
        for match in re.finditer(
            r"https?://(?:www\.)?huggingface\.co/(?!datasets/|spaces/)([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)",
            raw_line,
        ):
            repo_id = match.group(1).rstrip(".,;:)]}")
            if repo_id.split("/", 1)[0].lower() in reserved_hf_path_roots:
                continue
            if repo_id in seen_dependencies:
                continue
            seen_dependencies.add(repo_id)
            relation = "model-card-reference"
            line_lower = raw_line.lower()
            for token, candidate in [
                ("original model", "base_model"),
                ("text encoder", "text-encoder"),
                ("vision encoder", "vision-encoder"),
                ("image encoder", "vision-encoder"),
                ("audio vae", "audio-vae"),
                ("video vae", "video-vae"),
                ("vae", "vae"),
                ("vocoder", "vocoder"),
                ("upscaler", "upscaler"),
                ("lora", "adapter"),
                ("base model", "base_model"),
            ]:
                if token in line_lower:
                    relation = candidate
                    break
            dependencies.append(
                {
                    "repo_id": repo_id,
                    "relation": relation,
                    "source": "model-card",
                }
            )

    referenced_files: set[str] = set()
    for value in re.findall(
        r"[A-Za-z0-9_.+/-]+\.(?:bin|ckpt|gguf|onnx|pt|pth|safetensors)",
        text,
        flags=re.IGNORECASE,
    ):
        normalized = value.rstrip(".,;:)]}")
        if "huggingface.co/" in normalized:
            normalized = normalized.rsplit("/", 1)[-1]
        normalized = normalized.removeprefix("./")
        if not normalized or normalized.startswith(("-", "_")):
            continue
        referenced_files.add(normalized)
    return {
        "runtimes": sorted(runtimes),
        "precisions": sorted(precisions),
        "acceleration_methods": sorted(acceleration),
        "steps": sorted(step_values),
        "step_evidence": step_evidence,
        "offload": sorted(offload),
        "media_specs": {"evidence": media_spec_evidence} if media_spec_evidence else {},
        "dependencies": dependencies,
        "referenced_files": sorted(referenced_files)[:64],
        "customization": {
            "capabilities": sorted(
                {signal["capability"] for signal in customization_signals}
            ),
            "signals": customization_signals,
        }
        if customization_signals
        else {},
    }


def artifact_precision(path: str) -> list[str]:
    lower = path.lower()
    patterns = {
        "awq": r"(?:^|[/_.-])awq(?:[/_.-]|$)",
        "bf16": r"(?:^|[/_.-])(?:bf16|bfloat16)(?:[/_.-]|$)",
        "fp4": r"(?:^|[/_.-])(?:fp4|mxfp4|nvfp4)(?:[/_.-]|$)",
        "fp8": r"(?:^|[/_.-])(?:fp8|mxfp8)(?:[/_.-]|$)",
        "gptq": r"(?:^|[/_.-])gptq(?:[/_.-]|$)",
        "int4": r"(?:^|[/_.-])int4(?:[/_.-]|$)",
        "int8": r"(?:^|[/_.-])int8(?:[/_.-]|$)",
        "q3": r"(?:^|[/_.-])q3(?:_[a-z0-9]+)?(?:[/_.-]|$)",
        "q4": r"(?:^|[/_.-])q4(?:_[a-z0-9]+)?(?:[/_.-]|$)",
        "q5": r"(?:^|[/_.-])q5(?:_[a-z0-9]+)?(?:[/_.-]|$)",
        "q6": r"(?:^|[/_.-])q6(?:_[a-z0-9]+)?(?:[/_.-]|$)",
        "q8": r"(?:^|[/_.-])q8(?:_[a-z0-9]+)?(?:[/_.-]|$)",
    }
    return sorted(
        precision for precision, pattern in patterns.items() if re.search(pattern, lower)
    )


def artifact_component(path: str) -> str:
    lower = path.lower()
    if "lora" in lower or "adapter" in lower:
        return "adapter"
    if "audio_vae" in lower or "audio-vae" in lower:
        return "audio-vae"
    if "video_vae" in lower or "video-vae" in lower:
        return "video-vae"
    if "vae" in lower:
        return "vae"
    if "vocoder" in lower:
        return "vocoder"
    if "text_encoder" in lower or "text-encoder" in lower:
        return "text-encoder"
    if any(value in lower for value in ("vision_encoder", "image_encoder", "visual_encoder")):
        return "vision-encoder"
    if "upscal" in lower:
        return "upscaler"
    if "projector" in lower or "mmproj" in lower:
        return "projector"
    if any(value in lower for value in ("diffusion_model", "transformer", "unet")):
        return "transformer"
    return "model-weights"


def fetch_model_repository_files(repo_id: str) -> dict[str, Any]:
    quoted_id = urllib.parse.quote(repo_id, safe="/")
    query = urllib.parse.urlencode(
        [("blobs", "true"), ("expand", "siblings"), ("expand", "usedStorage")]
    )
    try:
        payload = hf_api(f"/api/models/{quoted_id}?{query}", retries=1)
        if not isinstance(payload, dict):
            raise TypeError("unexpected Hugging Face model detail response")
    except Exception as exc:
        return {"ok": False, "files": [], "error": type(exc).__name__}
    files = [
        {
            "path": str(row.get("rfilename") or ""),
            "size": int(row.get("size") or 0),
        }
        for row in payload.get("siblings", [])
        if row.get("rfilename")
    ]
    return {
        "ok": True,
        "files": files,
        "used_storage": int(payload.get("usedStorage") or 0),
    }


def merge_customization_signals(*values: dict[str, Any]) -> dict[str, Any]:
    signals: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for value in values:
        for signal in (value or {}).get("signals", []):
            key = (
                str(signal.get("capability") or ""),
                str(signal.get("source") or ""),
                str(signal.get("value") or ""),
            )
            if not key[0] or key in seen:
                continue
            seen.add(key)
            merged_signal = {
                "capability": key[0],
                "source": key[1],
                "value": key[2],
            }
            if signal.get("repo_id"):
                merged_signal["repo_id"] = str(signal["repo_id"])
            signals.append(merged_signal)
    if not signals:
        return {}
    capabilities = sorted({signal["capability"] for signal in signals})
    return {
        "lanes": sorted(
            {
                MEDIA_CUSTOMIZATION_LANES[capability]
                for capability in capabilities
                if capability in MEDIA_CUSTOMIZATION_LANES
            }
        ),
        "capabilities": capabilities,
        "signals": signals,
    }


def build_artifact_options(
    artifact_files: list[dict[str, Any]],
    limit: int = 32,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    order: list[tuple[str, ...]] = []
    for row in artifact_files:
        path = str(row.get("path") or "")
        match = SHARDED_ARTIFACT_RE.match(path)
        if match:
            key = (
                "sharded",
                match.group("prefix"),
                match.group("count"),
                match.group("suffix"),
            )
        else:
            key = ("file", path)
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(row)

    options: list[dict[str, Any]] = []
    for key in order:
        rows = grouped[key]
        if key[0] == "file":
            row = rows[0]
            path = str(row.get("path") or "")
            options.append(
                {
                    "path": path,
                    "bytes": int(row.get("size") or 0),
                    "component": artifact_component(path),
                    "precisions": artifact_precision(path),
                }
            )
        else:
            _, prefix, raw_count, suffix = key
            shard_count = int(raw_count)
            indexed_rows = sorted(
                rows,
                key=lambda row: int(
                    SHARDED_ARTIFACT_RE.match(str(row.get("path") or "")).group("index")
                ),
            )
            present_indices = {
                int(
                    SHARDED_ARTIFACT_RE.match(str(row.get("path") or "")).group("index")
                )
                for row in indexed_rows
            }
            first_path = str(indexed_rows[0].get("path") or "")
            options.append(
                {
                    "path_pattern": (
                        f"{prefix}-{{00001..{shard_count:05d}}}-of-"
                        f"{shard_count:05d}{suffix}"
                    ),
                    "bytes": sum(int(row.get("size") or 0) for row in indexed_rows),
                    "component": artifact_component(first_path),
                    "precisions": sorted(
                        {
                            precision
                            for row in indexed_rows
                            for precision in artifact_precision(str(row.get("path") or ""))
                        }
                    ),
                    "file_count": len(indexed_rows),
                    "shard_count": shard_count,
                    "required_all": True,
                    "complete": present_indices == set(range(1, shard_count + 1)),
                }
            )
        if len(options) >= limit:
            break
    return options


def build_media_deployment_profile(
    metadata: dict[str, Any],
    repository: dict[str, Any],
    card_evidence: dict[str, Any],
) -> dict[str, Any]:
    files = repository.get("files") or []
    artifact_files = [
        row
        for row in files
        if str(row.get("path") or "").lower().endswith(MODEL_ARTIFACT_SUFFIXES)
    ]
    workflow_files = sorted(
        str(row.get("path") or "")
        for row in files
        if str(row.get("path") or "").lower().endswith(".json")
        and (
            re.search(
                r"(?:^|/)(?:workflows?|examples?)/",
                str(row.get("path") or ""),
                re.I,
            )
            or re.search(
                r"(?:^|[/_.-])workflow(?:[/_.-]|$)",
                str(row.get("path") or ""),
                re.I,
            )
        )
    )
    component_rows: dict[str, dict[str, Any]] = {}
    file_precisions: set[str] = set()
    file_acceleration: set[str] = set()
    file_steps: set[int] = set()
    file_step_evidence: list[dict[str, Any]] = []
    for row in artifact_files:
        path = str(row.get("path") or "")
        lower_path = path.lower()
        component = artifact_component(path)
        precisions = artifact_precision(path)
        file_precisions.update(precisions)
        for token, method in {
            "distill": "distilled",
            "lightning": "lightning",
            "lcm": "lcm",
            "turbo": "turbo",
        }.items():
            if token in lower_path:
                file_acceleration.add(method)
        for value in re.findall(r"(?:^|[/_.-])(\d{1,2})[-_]?steps?(?:[/_.-]|$)", lower_path):
            step = int(value)
            if not 0 < step <= 64:
                continue
            file_steps.add(step)
            if len(file_step_evidence) < 8:
                file_step_evidence.append(
                    {"value": step, "source": "hf-repository-file", "evidence": path}
                )
        summary = component_rows.setdefault(
            component,
            {"type": component, "file_count": 0, "bytes": 0, "precisions": set()},
        )
        summary["file_count"] += 1
        summary["bytes"] += int(row.get("size") or 0)
        summary["precisions"].update(precisions)
    components = [
        {
            "type": row["type"],
            "file_count": row["file_count"],
            "bytes": row["bytes"],
            "precisions": sorted(row["precisions"]),
            "source": "hf-repository-files",
        }
        for row in component_rows.values()
    ]
    artifact_options = build_artifact_options(artifact_files)
    dependencies: list[dict[str, str]] = []
    seen_dependencies: set[tuple[str, str]] = set()
    current_id = str(metadata.get("model_id") or "")
    for dependency in list(metadata.get("base_model_dependencies") or []) + list(
        card_evidence.get("dependencies") or []
    ):
        repo_id = str(dependency.get("repo_id") or "")
        relation = str(dependency.get("relation") or "model-card-reference")
        if not repo_id or repo_id == current_id or (repo_id, relation) in seen_dependencies:
            continue
        seen_dependencies.add((repo_id, relation))
        dependencies.append(
            {
                "repo_id": repo_id,
                "relation": relation,
                "source": str(dependency.get("source") or "unknown"),
            }
        )
    runtimes = sorted(
        set(metadata.get("deployment") or [])
        & (set(MEDIA_RUNTIME_TAGS.values()) | {"gguf", "ollama-compatible"})
        | set(card_evidence.get("runtimes") or [])
    )
    # A model card may mention mutually exclusive precision variants. Treat these
    # as references, not as a complete runtime manifest, unless a future registry
    # entry explicitly declares a deployable bundle.
    referenced_files = list(card_evidence.get("referenced_files") or [])
    known_paths = {str(row.get("path") or "") for row in files}
    matched_references = [
        path
        for path in referenced_files
        if path in known_paths or any(candidate.endswith("/" + path) for candidate in known_paths)
    ]
    unresolved_references = [
        path for path in referenced_files if path not in matched_references
    ]
    complete_runtime_status = "partial" if artifact_files or dependencies else "unknown"
    profile = {
        "runtimes": runtimes,
        "components": sorted(components, key=lambda value: value["type"]),
        "artifact_options": artifact_options,
        "workflow_files": workflow_files,
        "precisions": sorted(file_precisions | set(card_evidence.get("precisions") or [])),
        "acceleration": {
            "methods": sorted(
                file_acceleration
                | set(card_evidence.get("acceleration_methods") or [])
            ),
            "steps": sorted(file_steps | set(card_evidence.get("steps") or [])),
            "step_evidence": (
                list(card_evidence.get("step_evidence") or []) + file_step_evidence
            )[:8],
        },
        "offload": list(card_evidence.get("offload") or []),
        "media_specs": card_evidence.get("media_specs") or {},
        "dependencies": dependencies,
        "footprint": {
            "repository_bytes": sum(int(row.get("size") or 0) for row in files),
            "artifact_bytes": sum(int(row.get("size") or 0) for row in artifact_files),
            "artifact_file_count": len(artifact_files),
            "complete_runtime_bytes": None,
            "complete_runtime_status": complete_runtime_status,
            "referenced_files": referenced_files,
            "unresolved_referenced_files": unresolved_references,
            "source": "hf-repository-files+model-card",
        },
        "customization": merge_customization_signals(
            metadata.get("media_customization") or {},
            card_evidence.get("customization") or {},
        ),
        "repository_files_ok": bool(repository.get("ok")),
    }
    return {
        key: value
        for key, value in profile.items()
        if value not in (None, "", [], {})
    }


def fetch_card(repo_id: str, repo_type: str) -> dict[str, Any]:
    prefix = "datasets/" if repo_type == "dataset" else ""
    quoted_id = urllib.parse.quote(repo_id, safe="/")
    card_url = f"https://huggingface.co/{prefix}{repo_id}/blob/main/README.md"
    last_error: Exception | None = None
    for base in hf_api_bases():
        raw_url = f"{base}/{prefix}{quoted_id}/raw/main/README.md"
        try:
            text = fetch_text(raw_url, timeout=15, retries=2, accept="text/markdown,text/plain")
            excerpt = extract_card_excerpt(text)
            if excerpt:
                result = {"url": card_url, "excerpt": excerpt, "ok": True}
                architecture_excerpt = extract_architecture_excerpt(text)
                if architecture_excerpt:
                    result["architecture_excerpt"] = architecture_excerpt
                if repo_type == "model":
                    evaluation = extract_evaluation_evidence(text)
                    if evaluation.get("excerpt"):
                        result["evaluation"] = evaluation
                    result["_deployment_evidence"] = extract_media_deployment_evidence(text)
                return result
        except Exception as exc:
            last_error = exc
    return {
        "url": card_url,
        "excerpt": "",
        "ok": False,
        "error": type(last_error).__name__ if last_error else "EmptyCard",
    }


def fetch_hf_change_evidence(
    repo_id: str,
    repo_type: str,
    start: dt.date,
    end: dt.date,
) -> dict[str, Any]:
    api_type = "datasets" if repo_type == "dataset" else "models"
    quoted_id = urllib.parse.quote(repo_id, safe="/")
    try:
        payload = hf_api(f"/api/{api_type}/{quoted_id}/commits/main", retries=2)
        if not isinstance(payload, list):
            raise TypeError("unexpected Hugging Face commit response")
    except Exception as exc:
        return {
            "source": "Hugging Face commit history",
            "ok": False,
            "commits": [],
            "error": type(exc).__name__,
        }
    prefix = "datasets/" if repo_type == "dataset" else ""
    commits: list[dict[str, str]] = []
    for row in payload:
        date = iso_date(row.get("date"))
        commit_id = str(row.get("id") or "")
        if not date or not start <= date <= end or not commit_id:
            continue
        title = str(row.get("title") or row.get("message") or "").strip().splitlines()[0]
        commits.append(
            {
                "id": commit_id,
                "title": title or "未提供提交说明",
                "date": date.isoformat(),
                "url": f"https://huggingface.co/{prefix}{repo_id}/commit/{commit_id}",
            }
        )
        if len(commits) >= CHANGE_EVIDENCE_LIMIT:
            break
    return {"source": "Hugging Face commit history", "ok": True, "commits": commits}


def needs_artifact_profile(item: dict[str, Any]) -> bool:
    # File sizes are a report field for every formal model, including LLM,
    # speech and decision checkpoints. The profile also carries media-only
    # details when the repository provides them.
    return str(item.get("repo_type") or "model") == "model"


def enrich_items_with_cards(
    items: list[dict[str, Any]],
    start: dt.date | None = None,
    end: dt.date | None = None,
) -> list[dict[str, Any]]:
    copied = [{**item, "metadata": dict(item.get("metadata") or {})} for item in items]

    def enrich(item: dict[str, Any]) -> dict[str, Any]:
        repo_type = str(item.get("repo_type") or "model")
        repo_id = str(item.get("title") or "")
        card = fetch_card(repo_id, repo_type)
        deployment_evidence = card.pop("_deployment_evidence", {})
        metadata = item.get("metadata") or {}
        if (
            repo_type == "model"
            and "comfyui" in set(metadata.get("deployment") or [])
            and not (metadata.get("media_customization") or {}).get("capabilities")
            and not (deployment_evidence.get("customization") or {}).get("capabilities")
        ):
            # Some ComfyUI packaging repositories contain only an explicit link
            # to the original model. Follow one declared base-model link so the
            # capability comes from the upstream model card, never from names.
            for dependency in deployment_evidence.get("dependencies") or []:
                if dependency.get("relation") != "base_model":
                    continue
                upstream_id = str(dependency.get("repo_id") or "")
                if not upstream_id:
                    continue
                upstream_card = fetch_card(upstream_id, "model")
                upstream_evidence = upstream_card.get("_deployment_evidence") or {}
                upstream_customization = upstream_evidence.get("customization") or {}
                upstream_signals = [
                    {
                        **signal,
                        "source": "upstream-model-card",
                        "repo_id": upstream_id,
                    }
                    for signal in upstream_customization.get("signals") or []
                ]
                if upstream_signals:
                    deployment_evidence["customization"] = merge_customization_signals(
                        deployment_evidence.get("customization") or {},
                        {"signals": upstream_signals},
                    )
                    break
        item["metadata"]["card"] = card
        if needs_artifact_profile(item):
            repository = fetch_model_repository_files(repo_id)
            item["metadata"]["deployment_profile"] = build_media_deployment_profile(
                item["metadata"], repository, deployment_evidence
            )
            merged_customization = (
                item["metadata"]["deployment_profile"].get("customization") or {}
            )
            if merged_customization:
                item["metadata"]["media_customization"] = merged_customization
        if item.get("event") == "repository-updated" and start and end:
            item["metadata"]["change_evidence"] = fetch_hf_change_evidence(
                repo_id, repo_type, start, end
            )
        return item

    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for item in copied:
        key = (str(item.get("repo_type") or "model"), str(item.get("title") or ""))
        unique.setdefault(key, item)
    unique_items = list(unique.values())
    with ThreadPoolExecutor(max_workers=min(CARD_FETCH_WORKERS, len(unique_items) or 1)) as executor:
        enriched_unique = list(executor.map(enrich, unique_items))
    enriched_by_key = {
        (str(item.get("repo_type") or "model"), str(item.get("title") or "")): item
        for item in enriched_unique
    }
    results: list[dict[str, Any]] = []
    for item in copied:
        key = (str(item.get("repo_type") or "model"), str(item.get("title") or ""))
        evidence_metadata = (enriched_by_key[key].get("metadata") or {})
        metadata = dict(item.get("metadata") or {})
        for evidence_key in ("card", "deployment_profile", "change_evidence"):
            if evidence_key in evidence_metadata:
                metadata[evidence_key] = evidence_metadata[evidence_key]
        merged_customization = merge_customization_signals(
            metadata.get("media_customization") or {},
            evidence_metadata.get("media_customization") or {},
        )
        if merged_customization:
            metadata["media_customization"] = merged_customization
        results.append({**item, "metadata": metadata})
    return results


def enrich_formal_groups(
    flagship_groups: dict[str, list[dict[str, Any]]],
    local_items: list[dict[str, Any]],
    notable_discoveries: dict[str, list[dict[str, Any]]],
    media_customization: list[dict[str, Any]],
    start: dt.date,
    end: dt.date,
) -> tuple[
    dict[str, list[dict[str, Any]]],
    list[dict[str, Any]],
    dict[str, list[dict[str, Any]]],
    list[dict[str, Any]],
]:
    batches: list[tuple[str, str | None, list[dict[str, Any]]]] = [
        ("flagship", role, rows) for role, rows in flagship_groups.items()
    ]
    batches.extend(
        [
            ("local", None, local_items),
            ("notable", "models", notable_discoveries["models"]),
            ("media-customization", None, media_customization),
        ]
    )
    flattened = [item for _, _, rows in batches for item in rows]
    enriched = enrich_items_with_cards(flattened, start, end)

    enriched_flagship = {role: [] for role in flagship_groups}
    enriched_local: list[dict[str, Any]] = []
    enriched_notable = {"models": []}
    enriched_media_customization: list[dict[str, Any]] = []
    cursor = 0
    for group, key, rows in batches:
        batch = enriched[cursor : cursor + len(rows)]
        cursor += len(rows)
        if group == "flagship" and key is not None:
            enriched_flagship[key] = batch
        elif group == "local":
            enriched_local = batch
        elif group == "notable" and key is not None:
            enriched_notable[key] = batch
        elif group == "media-customization":
            enriched_media_customization = batch
    return (
        enriched_flagship,
        enriched_local,
        enriched_notable,
        enriched_media_customization,
    )


def huggingface_repo_from_url(value: str) -> tuple[str, str] | None:
    parsed = urllib.parse.urlparse(value)
    if (parsed.hostname or "").lower() not in {"huggingface.co", "www.huggingface.co"}:
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 3 and parts[0] == "datasets":
        return "dataset", "/".join(parts[1:3])
    if len(parts) >= 2 and parts[0] not in {"collections", "spaces"}:
        return "model", "/".join(parts[:2])
    return None


def github_repo_api_url(value: str) -> str | None:
    parsed = urllib.parse.urlparse(value)
    if (parsed.hostname or "").lower() not in {"github.com", "www.github.com"}:
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        return None
    repo = parts[1].removesuffix(".git")
    return f"https://api.github.com/repos/{parts[0]}/{repo}"


def github_artifact_spec(value: str) -> dict[str, str] | None:
    api_url = github_repo_api_url(value)
    if not api_url:
        return None
    parsed = urllib.parse.urlparse(value)
    parts = [part for part in parsed.path.split("/") if part]
    owner = parts[0]
    repo = parts[1].removesuffix(".git")
    branch = ""
    path = ""
    if len(parts) >= 4 and parts[2] == "tree":
        branch = parts[3]
        path = "/".join(parts[4:])
    return {
        "api_url": api_url,
        "api_path": f"repos/{owner}/{repo}",
        "web_url": f"https://github.com/{owner}/{repo}",
        "branch": branch,
        "path": path,
    }


def gh_available() -> bool:
    return shutil.which("gh") is not None


def gh_api(endpoint: str, params: dict[str, str] | None = None) -> Any:
    command = ["gh", "api", "--method", "GET", endpoint]
    for key, value in (params or {}).items():
        command.extend(["-f", f"{key}={value}"])
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.returncode != 0:
        raise RuntimeError("authenticated gh api request failed")
    return json.loads(completed.stdout)


def query_github_metrics(
    registry: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    specs: dict[str, dict[str, str]] = {}
    for project in registry.get("projects", []):
        for artifact in project.get("artifacts", []):
            if artifact.get("repo_type") != "url":
                continue
            spec = github_artifact_spec(str(artifact.get("id") or ""))
            if spec:
                specs[spec["web_url"]] = spec

    def fetch(
        entry: tuple[str, dict[str, str]],
    ) -> tuple[str, dict[str, Any] | None, str | None]:
        web_url, spec = entry
        try:
            if not gh_available():
                raise FileNotFoundError("gh is required for GitHub metrics")
            payload = gh_api(spec["api_path"])
            if not isinstance(payload, dict):
                raise TypeError("unexpected GitHub repository response")
            return web_url, {
                "url": web_url,
                "stars": int(payload.get("stargazers_count") or 0),
                "forks": int(payload.get("forks_count") or 0),
                "open_issues": int(payload.get("open_issues_count") or 0),
                "pushed_at": str(payload.get("pushed_at") or ""),
            }, None
        except Exception as exc:
            return web_url, None, type(exc).__name__

    metrics: dict[str, dict[str, Any]] = {}
    errors: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=min(8, len(specs) or 1)) as executor:
        for web_url, payload, error in executor.map(fetch, specs.items()):
            if error:
                errors[f"github-metrics:{web_url}"] = error
            elif payload is not None:
                metrics[web_url] = payload
    return metrics, errors


def query_project_urls(
    registry: dict[str, Any],
    start: dt.date,
    end: dt.date,
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    specs: dict[str, dict[str, str]] = {}
    for project in registry.get("projects", []):
        for artifact in project.get("artifacts", []):
            if artifact.get("repo_type") != "url":
                continue
            artifact_url = str(artifact.get("id") or "")
            spec = github_artifact_spec(artifact_url)
            if spec:
                specs[artifact_url] = spec

    def fetch(entry: tuple[str, dict[str, str]]) -> tuple[str, dict[str, Any] | None, str | None]:
        artifact_url, spec = entry
        params = {
            "since": f"{start.isoformat()}T00:00:00Z",
            "until": f"{end.isoformat()}T23:59:59Z",
            "per_page": str(CHANGE_EVIDENCE_LIMIT),
        }
        if spec["branch"]:
            params["sha"] = spec["branch"]
        if spec["path"]:
            params["path"] = spec["path"]
        try:
            if not gh_available():
                raise FileNotFoundError("gh is required for path-filtered GitHub commits")
            payload = gh_api(spec["api_path"] + "/commits", params)
            if not isinstance(payload, list):
                raise TypeError("unexpected GitHub commits response")
        except Exception as exc:
            if spec["path"] or gh_available():
                return artifact_url, None, type(exc).__name__
            try:
                feed_text = fetch_text(
                    spec["web_url"] + "/commits.atom",
                    retries=0,
                    accept="application/atom+xml,application/xml",
                )
                feed = ET.fromstring(feed_text)
                namespace = "{http://www.w3.org/2005/Atom}"
                entry_node = feed.find(namespace + "entry")
                updated = entry_node.findtext(namespace + "updated") if entry_node is not None else ""
                date = iso_date(updated)
                if not updated or not date or not start <= date <= end:
                    raise ValueError("missing Atom updated timestamp")
                title = entry_node.findtext(namespace + "title") if entry_node is not None else ""
                link_node = entry_node.find(namespace + "link") if entry_node is not None else None
                link = link_node.get("href", "") if link_node is not None else ""
                change_evidence = {
                    "source": "GitHub Atom commit history",
                    "ok": True,
                    "commits": [
                        {
                            "id": link.rstrip("/").split("/")[-1],
                            "title": re.sub(r"\s+", " ", str(title or "")).strip()
                            or "未提供提交说明",
                            "date": date.isoformat(),
                            "url": link,
                        }
                    ],
                }
                return artifact_url, {
                    "id": artifact_url,
                    "createdAt": "",
                    "lastModified": updated,
                    "url": spec["web_url"],
                    "change_evidence": change_evidence,
                }, None
            except Exception:
                return artifact_url, None, type(exc).__name__
        commits: list[dict[str, str]] = []
        for row in payload:
            commit = row.get("commit") or {}
            committer = commit.get("committer") or {}
            author = commit.get("author") or {}
            date = iso_date(committer.get("date") or author.get("date"))
            if not date or not start <= date <= end:
                continue
            message = str(commit.get("message") or "").strip()
            commits.append(
                {
                    "id": str(row.get("sha") or ""),
                    "title": message.splitlines()[0] if message else "未提供提交说明",
                    "date": date.isoformat(),
                    "url": str(row.get("html_url") or spec["web_url"]),
                }
            )
        if not commits:
            return artifact_url, None, None
        change_evidence = {
            "source": "GitHub commit history",
            "ok": True,
            "path": spec["path"] or None,
            "commits": commits,
        }
        return artifact_url, {
            "id": artifact_url,
            "createdAt": "",
            "lastModified": commits[0]["date"],
            "url": spec["web_url"],
            "change_evidence": change_evidence,
        }, None

    rows: dict[str, dict[str, Any]] = {}
    errors: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=min(8, len(specs) or 1)) as executor:
        for artifact_url, payload, error in executor.map(fetch, specs.items()):
            if error:
                errors[artifact_url] = error
            elif payload is not None:
                rows[artifact_url] = payload
    return rows, errors


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
            elif repo_type == "url":
                resolved = huggingface_repo_from_url(str(artifact.get("id") or ""))
                if resolved and resolved[0] == "model":
                    models.append(resolved[1])
                elif resolved and resolved[0] == "dataset":
                    datasets.append(resolved[1])
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
    url_rows: dict[str, dict[str, Any]],
    start: dt.date,
    end: dt.date,
    github_metrics: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    github_metrics = github_metrics or {}
    items: list[dict[str, Any]] = []
    for project in registry.get("projects", []):
        changed: list[dict[str, Any]] = []
        for artifact in project.get("artifacts", []):
            artifact_id = str(artifact.get("id") or "")
            repo_type = str(artifact.get("repo_type") or "")
            resolved = huggingface_repo_from_url(artifact_id) if repo_type == "url" else None
            effective_type, repo_id = resolved if resolved else (repo_type, artifact_id)
            row = (
                model_rows.get(repo_id)
                if effective_type == "model"
                else dataset_rows.get(repo_id)
                if effective_type == "dataset"
                else url_rows.get(artifact_id)
                if repo_type == "url"
                else None
            )
            if row is None:
                continue
            event = event_in_window(row, start, end)
            if not event:
                continue
            prefix = "datasets/" if effective_type == "dataset" else ""
            artifact_url = (
                str(row.get("url") or artifact_id)
                if repo_type == "url" and not resolved
                else f"https://huggingface.co/{prefix}{repo_id}"
            )
            github_spec = github_artifact_spec(artifact_id) if repo_type == "url" else None
            github = github_metrics.get(github_spec["web_url"], {}) if github_spec else {}
            changed.append(
                {
                    "id": repo_id,
                    "repo_type": effective_type,
                    "role": artifact.get("role"),
                    "depends_on": artifact.get("depends_on", []),
                    "event": event[0],
                    "date": event[1],
                    "url": artifact_url,
                    **(
                        {"change_evidence": row["change_evidence"]}
                        if row.get("change_evidence")
                        else {}
                    ),
                    **({"github": github} if github else {}),
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
                "source": "Hugging Face / GitHub",
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
    def project_signal_key(item: dict[str, Any]) -> tuple[Any, ...]:
        github_rows = [
            artifact.get("github") or {}
            for artifact in (item.get("metadata") or {}).get("artifacts", [])
            if artifact.get("github")
        ]
        github_signals = {
            signal
            for github in github_rows
            for signal in (github.get("trend") or {}).get("signals", [])
        }
        return (
            bool(github_signals & {"github-stars-growing", "github-forks-growing"}),
            max((int(github.get("stars") or 0) for github in github_rows), default=0),
            max((int(github.get("forks") or 0) for github in github_rows), default=0),
            item["date"],
            item["title"],
        )

    return sorted(items, key=project_signal_key, reverse=True)


def enrich_project_change_evidence(
    items: list[dict[str, Any]],
    start: dt.date,
    end: dt.date,
) -> list[dict[str, Any]]:
    copied: list[dict[str, Any]] = []
    for item in items:
        metadata = dict(item.get("metadata") or {})
        metadata["artifacts"] = [dict(artifact) for artifact in metadata.get("artifacts", [])]
        copied.append({**item, "metadata": metadata})

    targets = [
        artifact
        for item in copied
        for artifact in item["metadata"].get("artifacts", [])
        if artifact.get("event") == "repository-updated"
        and artifact.get("repo_type") in {"model", "dataset"}
        and not artifact.get("change_evidence")
    ]

    def enrich(artifact: dict[str, Any]) -> None:
        artifact["change_evidence"] = fetch_hf_change_evidence(
            str(artifact.get("id") or ""),
            str(artifact.get("repo_type") or "model"),
            start,
            end,
        )

    with ThreadPoolExecutor(max_workers=min(CARD_FETCH_WORKERS, len(targets) or 1)) as executor:
        list(executor.map(enrich, targets))
    return copied


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


def sort_local_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(item: dict[str, Any]) -> tuple[Any, ...]:
        metadata = item.get("metadata") or {}
        signals = set((metadata.get("trend") or {}).get("signals") or [])
        return (
            "hf-rank-rising" in signals,
            "hf-engagement-growing" in signals,
            int(metadata.get("trendingScore") or 0),
            "priority" in (metadata.get("selection") or []),
            int(metadata.get("likes") or 0),
            int(metadata.get("downloads") or 0),
            item.get("date", ""),
            item.get("title", ""),
        )

    return sorted(
        items,
        key=key,
        reverse=True,
    )


def github_snapshot_metrics(
    registry: dict[str, Any],
    current: dict[str, dict[str, Any]],
    previous: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    registered_urls = {
        spec["web_url"]
        for project in registry.get("projects", [])
        for artifact in project.get("artifacts", [])
        if artifact.get("repo_type") == "url"
        for spec in [github_artifact_spec(str(artifact.get("id") or ""))]
        if spec
    }
    previous_github = previous.get("github") or {}
    return {
        repo_url: current.get(repo_url)
        or (
            previous_github.get(repo_url)
            if isinstance(previous_github, dict)
            else None
        )
        for repo_url in registered_urls
        if current.get(repo_url)
        or (isinstance(previous_github, dict) and previous_github.get(repo_url))
    }


def local_variant_key(item: dict[str, Any]) -> str:
    metadata = item.get("metadata") or {}
    variant_group = str(metadata.get("variant_group") or "").strip()
    if variant_group:
        publisher = str(item.get("title") or "").split("/", 1)[0]
        return f"explicit:{publisher}:{variant_group}"
    return str(item.get("title") or "")


def collapse_local_variants(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in sort_local_items(items):
        groups.setdefault(local_variant_key(item), []).append(item)
    collapsed: list[dict[str, Any]] = []
    for variants in groups.values():
        representative = variants[0]
        if len(variants) > 1:
            representative["metadata"]["variants"] = [
                {
                    "id": variant.get("title"),
                    "url": variant.get("url"),
                    "deployment": (variant.get("metadata") or {}).get("deployment") or [],
                    "downloads": (variant.get("metadata") or {}).get("downloads") or 0,
                    "likes": (variant.get("metadata") or {}).get("likes") or 0,
                    "trendingScore": (variant.get("metadata") or {}).get("trendingScore") or 0,
                }
                for variant in variants
            ]
        collapsed.append(representative)
    return sort_local_items(collapsed)


def select_popular_derivatives(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sort_local_items(items)
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

    covered_publishers: set[str] = set()
    for item in ranked:
        publisher = str(item.get("title") or "").split("/", 1)[0]
        if not publisher or publisher in covered_publishers:
            continue
        if add(item):
            covered_publishers.add(publisher)
        if len(covered_publishers) >= LOCAL_PUBLISHER_COVERAGE_MAX:
            break

    covered_roles = {
        str((item.get("metadata") or {}).get("role") or "") for item in selected
    }
    for item in ranked:
        role = str((item.get("metadata") or {}).get("role") or "")
        if role and role not in covered_roles and add(item):
            covered_roles.add(role)
        if len(selected) >= LOCAL_REPORT_MAX:
            return sort_local_items(selected)

    for facet in ["merge", "finetune", "adapter", "gguf", "mlx", "on-device", "quantized"]:
        for item in ranked:
            if facet in facets(item) and add(item):
                break
        if len(selected) >= LOCAL_REPORT_MAX:
            return sort_local_items(selected)

    for item in ranked:
        add(item)
        if len(selected) >= LOCAL_REPORT_MAX:
            return sort_local_items(selected)

    for item in ranked:
        add(item, enforce_publisher_cap=False)
        if len(selected) >= LOCAL_REPORT_MAX:
            break
    return sort_local_items(selected)


def source_status(rows: dict[str, Any], errors: dict[str, str], selected: int) -> dict[str, Any]:
    return {
        "ok": bool(rows) or not errors,
        "count": len(rows) + len(errors),
        "selected": selected,
        "errors": errors,
    }


def report_model_role(item: dict[str, Any]) -> str:
    category = str(item.get("category") or "")
    if category in FLAGSHIP_ROLES:
        return category
    metadata = item.get("metadata") or {}
    role = str(metadata.get("role") or "")
    if role in FLAGSHIP_ROLES:
        return role
    role_evidence = metadata.get("role_evidence") or {}
    pipeline_tag = metadata.get("pipeline_tag") or role_evidence.get("pipeline_tag") or ""
    return model_role({"pipeline_tag": pipeline_tag}, default="unknown")


def count_by_model_role(items: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts = {role: 0 for role in FLAGSHIP_ROLES}
    counts["unknown"] = 0
    for item in items:
        role = report_model_role(item)
        counts[role if role in counts else "unknown"] += 1
    return counts


def count_metadata_values(items: Iterable[dict[str, Any]], *path: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value: Any = item.get("metadata") or {}
        for key in path:
            value = value.get(key) if isinstance(value, dict) else None
        for entry in value if isinstance(value, list) else []:
            label = str(entry)
            counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))


def count_metadata_scalar(items: Iterable[dict[str, Any]], *path: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value: Any = item.get("metadata") or {}
        for key in path:
            value = value.get(key) if isinstance(value, dict) else None
        if value in (None, ""):
            continue
        label = str(value)
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items()))


def coverage_diagnostics(groups: dict[str, Any]) -> dict[str, Any]:
    flagship_items = [item for rows in groups["flagship"].values() for item in rows]
    local_items = groups["local"]
    notable_models = groups["notable_discoveries"]["models"]
    media_items = groups.get("media_customization", [])
    model_groups = {
        "flagship": flagship_items,
        "local": local_items,
        "notable_discoveries": notable_models,
        "media_customization": media_items,
    }
    model_titles = {
        str(item.get("title") or "")
        for items in model_groups.values()
        for item in items
        if item.get("title")
    }
    return {
        "models_by_group_and_role": {
            name: count_by_model_role(items) for name, items in model_groups.items()
        },
        "unique_model_repositories": len(model_titles),
        "local_by_deployment": count_metadata_values(local_items, "deployment"),
        "media_customization_by_capability": count_metadata_values(
            media_items, "media_customization", "capabilities"
        ),
        "media_by_discovery_track": count_metadata_values(
            media_items, "discovery_tracks"
        ),
    }


def compact_change_evidence(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if not value:
        return None
    return {
        "ok": bool(value.get("ok")),
        "commits": [
            {
                key: commit[key]
                for key in ("title", "date")
                if commit.get(key) not in (None, "")
            }
            for commit in value.get("commits", [])
        ],
    }


def compact_card(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if not value:
        return None
    result: dict[str, Any] = {"ok": bool(value.get("ok"))}
    for key in ("excerpt", "architecture_excerpt"):
        if value.get(key):
            result[key] = value[key]
    evaluation = value.get("evaluation") or {}
    if evaluation.get("excerpt"):
        result["evaluation"] = {
            key: evaluation[key]
            for key in ("excerpt", "caveats")
            if evaluation.get(key)
        }
    return result


def report_item(item: dict[str, Any]) -> dict[str, Any]:
    result = {
        key: item[key]
        for key in ("title", "url", "date", "event", "category", "repo_type")
        if item.get(key) not in (None, "")
    }
    metadata = item.get("metadata") or {}
    compact_metadata: dict[str, Any] = {}
    if item.get("category") == "reproducible":
        for key in ("scope", "openness"):
            if metadata.get(key) not in (None, "", [], {}):
                compact_metadata[key] = metadata[key]
        artifacts = []
        for artifact in metadata.get("artifacts", []):
            compact_artifact = {
                key: artifact[key]
                for key in ("id", "role", "depends_on", "event", "date", "url", "github")
                if artifact.get(key) not in (None, "", [], {})
            }
            change_evidence = compact_change_evidence(artifact.get("change_evidence"))
            if change_evidence:
                compact_artifact["change_evidence"] = change_evidence
            artifacts.append(compact_artifact)
        compact_metadata["artifacts"] = artifacts
    else:
        keys = (
            "selection",
            "domains",
            "methods",
            "entry",
            "sample_unit",
            "evidence",
            "stars",
            "uses",
            "roles",
            "related_models",
            "related_projects",
            "size",
            "role",
            "family",
            "canonical_model",
            "canonical_model_trace",
            "capabilities",
            "ecosystem_paths",
            "modalities",
            "role_evidence",
            "audio_tasks",
            "media_customization",
            "comfyui_integration",
            "activity_density",
            "discovery_tracks",
            "alignment",
            "deployment",
            "deployment_profile",
            "base_model_dependencies",
            "architecture",
            "architecture_classes",
            "scale",
            "papers",
            "derivation",
            "variants",
            "trendingScore",
            "downloads",
            "likes",
            "trend",
            "pending_registry",
            "embodied_subtype",
            "ecosystem_activity",
        )
        for key in keys:
            if metadata.get(key) not in (None, "", [], {}):
                compact_metadata[key] = metadata[key]
        card = compact_card(metadata.get("card"))
        if card:
            compact_metadata["card"] = card
        change_evidence = compact_change_evidence(metadata.get("change_evidence"))
        if change_evidence:
            compact_metadata["change_evidence"] = change_evidence
    result["metadata"] = compact_metadata
    return result


def build_report_payload(payload: dict[str, Any]) -> dict[str, Any]:
    groups = payload["groups"]
    return {
        "kind": payload["kind"],
        "window": payload["window"],
        "ecosystem_architecture": payload.get("ecosystem_architecture", []),
        "development_baselines": payload.get("development_baselines", {}),
        "groups": {
            "flagship": {
                role: [report_item(item) for item in items]
                for role, items in groups["flagship"].items()
            },
            "local": [report_item(item) for item in groups["local"]],
            "notable_discoveries": {
                "models": [
                    report_item(item) for item in groups["notable_discoveries"]["models"]
                ],
            },
            "media_customization": [
                report_item(item) for item in groups.get("media_customization", [])
            ],
            "ecosystem_baselines": {
                role: [report_item(item) for item in items]
                for role, items in groups.get("ecosystem_baselines", {}).items()
            },
            "development": {
                **{
                    kind: [report_item(item) for item in groups.get("development", {}).get(kind, [])]
                    for kind in ("tools", "datasets")
                },
                "opportunities": groups.get("development", {}).get("opportunities", []),
            },
        },
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


def emit_compact_payload(payload: dict[str, Any], output: str) -> int:
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    path = Path(output).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(path)
    return len(text.encode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect registered and notable Hugging Face model updates in a fixed 7-day window."
    )
    parser.add_argument("--date", help="Window start date, YYYY-MM-DD")
    parser.add_argument("--output", help="Write candidate JSON to this path; stdout when omitted")
    parser.add_argument(
        "--report-output",
        help="Write a compact groups-only JSON projection for report generation",
    )
    parser.add_argument(
        "--state-dir",
        help="Optional caller-owned directory for the current trending snapshot",
    )
    parser.add_argument(
        "--http-proxy",
        type=proxy_url,
        help="HTTP proxy URL for this collection process only",
    )
    parser.add_argument(
        "--https-proxy",
        type=proxy_url,
        help="HTTPS proxy URL for this collection process only",
    )
    parser.add_argument(
        "--no-proxy",
        help="Comma-separated hosts that bypass the explicit proxy; localhost is always included",
    )
    parser.add_argument("--stats", action="store_true", help="Print group counts to stderr")
    args = parser.parse_args()

    configure_proxy(args.http_proxy, args.https_proxy, args.no_proxy)

    if args.output and args.report_output:
        output_path = Path(args.output).expanduser().resolve()
        report_path = Path(args.report_output).expanduser().resolve()
        if output_path == report_path:
            parser.error("--output and --report-output must use different paths")
    run_started = time.perf_counter()
    timings: dict[str, float] = {}

    try:
        start, end = parse_window(args.date)
    except ValueError as exc:
        parser.error(str(exc))
    include_current_hot = args.date is None
    observed_at = dt.datetime.now(dt.timezone.utc).isoformat()

    model_registry = load_json(MODEL_REGISTRY_PATH)
    development_baselines = load_json(DEVELOPMENT_BASELINES_PATH)
    validate_registries(model_registry, {"projects": []}, {"datasets": []})
    validate_ecosystem_baselines(ECOSYSTEM_ARCHITECTURE, development_baselines)
    flagship = flagship_index(model_registry)
    local = local_index(model_registry)
    official_owners = list(
        dict.fromkeys(str(entry["owner"]) for entry in model_registry.get("families", []))
    )
    owners = list(official_owners)
    if include_current_hot:
        owners = list(
            dict.fromkeys(
                owners
                + [str(value) for value in model_registry.get("local_publishers", [])]
            )
        )

    snapshot_path = trending_snapshot_path(args.state_dir)
    previous_snapshot = (
        load_trending_snapshot(snapshot_path)
        if args.date is None and snapshot_path is not None
        else {}
    )

    phase_started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=6) as executor:
        owner_future = executor.submit(query_owner_models, owners, start)
        development_future = executor.submit(development_updates, development_baselines, start, end)
        opportunity_future = (
            executor.submit(development_opportunities, development_baselines)
            if include_current_hot else None
        )
        local_future = executor.submit(query_local_candidates) if include_current_hot else None
        modality_future = executor.submit(query_modality_candidates) if include_current_hot else None
        media_ecosystem_future = (
            executor.submit(query_media_ecosystem_candidates) if include_current_hot else None
        )
        global_future = executor.submit(query_global_models) if include_current_hot else None
        owner_rows_list, owner_coverage, owner_errors = owner_future.result()
        local_candidates = local_future.result() if local_future else []
        modality_candidates, modality_query_counts, modality_errors, modality_trending_scopes = (
            modality_future.result()
            if modality_future
            else ([], {role: 0 for role in MODALITY_QUERY_FILTERS}, {}, {})
        )
        media_ecosystem_candidates, media_ecosystem_counts, media_ecosystem_errors = (
            media_ecosystem_future.result()
            if media_ecosystem_future
            else (
                [],
                {
                    value: 0
                    for value in (
                        MEDIA_ECOSYSTEM_FILTERS + MEDIA_CUSTOMIZATION_QUERY_FILTERS
                    )
                },
                {},
            )
        )
        global_trending, global_recent, global_errors = (
            global_future.result() if global_future else ([], [], {})
        )
        development_items, development_sources = development_future.result()
        if opportunity_future:
            opportunities, opportunity_source = opportunity_future.result()
            development_items["opportunities"] = opportunities
            development_sources["local_training_opportunities"] = opportunity_source
        else:
            development_items["opportunities"] = []
    timings["candidate_queries"] = time.perf_counter() - phase_started

    model_trending_scopes = {"global": global_trending, **modality_trending_scopes}
    annotate_trending_deltas(model_trending_scopes, previous_snapshot, observed_at)
    trend_by_model_id = {
        str(row.get("id") or ""): row.get("_trend") or {}
        for rows in model_trending_scopes.values()
        for row in rows
        if row.get("id") and row.get("_trend")
    }
    open_candidate_rows = {
        str(row.get("id") or ""): row
        for row in (
            owner_rows_list
            + local_candidates
            + modality_candidates
            + media_ecosystem_candidates
            + global_recent
            + global_trending
        )
        if row.get("id")
    }
    for model_id, row in open_candidate_rows.items():
        if model_id in trend_by_model_id:
            row["_trend"] = trend_by_model_id[model_id]
    open_candidates = list(open_candidate_rows.values())
    cached_model_rows = {
        str(row.get("id") or ""): row
        for row in open_candidates
        if row.get("id")
    }
    baseline_registry = model_registry.get("ecosystem_baseline_models", {})
    baseline_specs = {
        str(entry["id"]): {**entry, "role": role, "track": "flagship"}
        for role, entries in baseline_registry.items()
        for entry in entries
    }
    relevant_model_ids = list(flagship) + list(local) + (list(baseline_specs) if include_current_hot else [])
    requested_model_ids: list[str] = []
    for model_id in dict.fromkeys(relevant_model_ids):
        if model_id in cached_model_rows:
            continue
        owner = model_id.split("/", 1)[0]
        if owner_coverage.get(owner) is True:
            continue
        requested_model_ids.append(model_id)

    phase_started = time.perf_counter()
    exact_model_rows, exact_model_errors = fetch_many(requested_model_ids, fetch_model)
    timings["exact_fetches"] = time.perf_counter() - phase_started

    model_rows = {**cached_model_rows, **exact_model_rows}
    canonical_references = observed_canonical_references(open_candidates) if include_current_hot else {}
    model_errors = {
        **owner_errors,
        **modality_errors,
        **media_ecosystem_errors,
        **global_errors,
        **exact_model_errors,
    }

    phase_started = time.perf_counter()
    flagship_groups: dict[str, list[dict[str, Any]]] = {role: [] for role in FLAGSHIP_ROLES}
    monitored_flagships = {
        **flagship,
        **(baseline_specs if include_current_hot else {}),
    }
    for model_id, record in monitored_flagships.items():
        row = model_rows.get(model_id)
        event = event_in_window(row or {}, start, end)
        if row is not None and event:
            flagship_groups[record["role"]].append(model_item(
                row,
                {**record, "ecosystem_activity": canonical_references.get(model_id) or {}},
                model_registry,
                event,
            ))
    if include_current_hot:
        audio_flagships = {
            model_id: record for model_id, record in flagship.items()
            if record.get("role") == "audio-generation"
        }
        other_flagships = {
            model_id: record for model_id, record in flagship.items()
            if record.get("role") != "audio-generation"
        }
        for monitored, limit in (
            (other_flagships, 8),
            (audio_flagships, len(audio_flagships)),
            (baseline_specs, len(baseline_specs)),
        ):
            for item in watched_flagship_items(
                monitored, model_rows, canonical_references, model_registry, start, end, limit
            ):
                flagship_groups[str((item.get("metadata") or {}).get("role"))].append(item)

    ecosystem_baselines: dict[str, list[dict[str, Any]]] = {
        role: [] for role in baseline_registry
    }

    local_items: list[dict[str, Any]] = []
    for model_id, record in local.items():
        row = model_rows.get(model_id)
        event = local_signal(row or {}, start, end, include_current_hot)
        priority = bool(record.get("priority", True))
        selection = registered_local_selection(
            row or {},
            event,
            priority,
            include_current_hot,
        )
        if row is None or selection is None:
            continue
        assert event is not None
        inherited = model_rows.get(str(record.get("canonical") or ""))
        local_items.append(
            model_item(
                row,
                {**record, "selection": selection},
                model_registry,
                event,
                inherited,
            )
        )

    known_ids = set(flagship) | set(local) | set(baseline_specs)
    local_items.extend(
        local_discovery_items(
            open_candidates,
            model_registry,
            model_rows,
            start,
            end,
            known_ids,
            include_current_hot,
        )
    )
    local_items = list({item["title"]: item for item in local_items}.values())

    model_discoveries = model_discovery_items(
        open_candidates,
        known_ids,
        model_registry,
        start,
        end,
        allow_unregistered_hot=include_current_hot,
    )
    if not include_current_hot:
        for rows in flagship_groups.values():
            strip_live_popularity(rows)
        strip_live_popularity(local_items)
        strip_live_popularity(model_discoveries)
    discoveries = sorted(
        model_discoveries,
        key=lambda item: (item.get("date", ""), item.get("title", "")),
        reverse=True,
    )
    notable_discoveries = select_notable_discoveries(
        model_discoveries,
    )
    media_radar_rows = list(
        {
            str(row.get("id") or ""): row
            for row in media_ecosystem_candidates + global_trending + global_recent
            if row.get("id")
        }.values()
    )
    media_customization = media_customization_items(
        media_radar_rows,
        model_registry,
        start,
        end,
        include_current_hot,
    )
    notable_model_ids = {
        str(item.get("title") or "") for item in notable_discoveries["models"]
    }
    local_items = [
        item for item in local_items if str(item.get("title") or "") not in notable_model_ids
    ]

    flagship_groups = {role: sort_items(rows) for role, rows in flagship_groups.items()}
    local_items = select_popular_derivatives(collapse_local_variants(local_items))
    timings["selection"] = time.perf_counter() - phase_started
    phase_started = time.perf_counter()
    (
        flagship_groups,
        local_items,
        notable_discoveries,
        media_customization,
    ) = enrich_formal_groups(
        flagship_groups,
        local_items,
        notable_discoveries,
        media_customization,
        start,
        end,
    )
    media_customization = finalize_media_customization_items(media_customization)
    primary_ids = {
        str(item.get("title") or "")
        for rows in list(flagship_groups.values()) + [local_items, notable_discoveries["models"]]
        for item in rows
    }
    media_customization = [
        item for item in media_customization
        if str(item.get("title") or "") not in primary_ids
    ]
    formal_model_items = [
        item
        for rows in list(flagship_groups.values())
        + list(ecosystem_baselines.values())
        + [local_items, notable_discoveries["models"], media_customization]
        for item in rows
    ]
    lineage_fetch_errors = attach_canonical_traces(formal_model_items, model_rows)
    timings["formal_enrichment"] = time.perf_counter() - phase_started
    flagship_count = sum(len(rows) for rows in flagship_groups.values())
    notable_model_count = len(notable_discoveries["models"])
    profiled_model_items = [
        item
        for rows in list(flagship_groups.values())
        + list(ecosystem_baselines.values())
        + [local_items, notable_discoveries["models"], media_customization]
        for item in rows
        if (item.get("metadata") or {}).get("deployment_profile")
    ]
    profiled_model_items = list(
        {str(item.get("title") or ""): item for item in profiled_model_items}.values()
    )
    deployment_profile_errors = sum(
        not bool(
            ((item.get("metadata") or {}).get("deployment_profile") or {}).get(
                "repository_files_ok"
            )
        )
        for item in profiled_model_items
    )

    selected_groups = {
        "flagship": flagship_groups,
        "local": local_items,
        "notable_discoveries": notable_discoveries,
        "media_customization": media_customization,
        "ecosystem_baselines": ecosystem_baselines,
        "development": development_items,
    }
    architecture_summary = [
        {
            "id": ecosystem["id"],
            "label": ecosystem["label"],
            "stages": [
                {key: stage[key] for key in ("id", "label", "input", "output", "upstream") if key in stage}
                for stage in ecosystem["stages"]
            ],
        }
        for ecosystem in ECOSYSTEM_ARCHITECTURE["ecosystems"]
    ]
    payload = {
        "kind": "ai-oss-models",
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "ecosystem_architecture": architecture_summary,
        "development_baselines": development_baselines,
        "sources": {
            "huggingface_models": source_status(
                model_rows,
                model_errors,
                flagship_count + len(local_items) + notable_model_count,
            ),
            **development_sources,
        },
        "diagnostics": {
            "owner_candidates": len(owner_rows_list),
            "local_filter_candidates": len(local_candidates),
            "modality_query_candidates": len(modality_candidates),
            "modality_query_by_role": modality_query_counts,
            "media_ecosystem_candidates": len(media_ecosystem_candidates),
            "media_ecosystem_by_filter": media_ecosystem_counts,
            "global_trending_candidates": len(global_trending),
            "global_recent_candidates": len(global_recent),
            "open_candidate_union": len(open_candidates),
            "local_hot_before_limit": (
                len(
                    [
                        row
                        for row in open_candidates
                        if is_hot_local(row)
                        and local_signal(row, start, end, include_current_hot)
                    ]
                )
                if include_current_hot
                else 0
            ),
            "local_selected": len(local_items),
            "model_discoveries": len(model_discoveries),
            "media_customization_selected": len(media_customization),
            "media_open_activity_selected": sum(
                "open-activity"
                in set((item.get("metadata") or {}).get("discovery_tracks") or [])
                for item in media_customization
            ),
            "deployment_profile_models": len(profiled_model_items),
            "deployment_profile_repository_errors": deployment_profile_errors,
            "canonical_trace_statuses": dict(Counter(
                ((item.get("metadata") or {}).get("canonical_model_trace") or {}).get("status", "missing")
                for item in formal_model_items
            )),
            "canonical_trace_fetch_errors": lineage_fetch_errors,
            "coverage": coverage_diagnostics(selected_groups),
        },
        "groups": selected_groups,
        "discoveries": discoveries,
    }
    emit_payload(payload, args.output)
    report_output_bytes = 0
    if args.report_output:
        report_output_bytes = emit_compact_payload(
            build_report_payload(payload),
            args.report_output,
        )
    if args.date is None and global_trending and snapshot_path is not None:
        write_trending_snapshot_safely(
            snapshot_path,
            model_trending_scopes,
            observed_at,
        )

    timings["total"] = time.perf_counter() - run_started
    if args.stats:
        print(
            json.dumps(
                {
                    "window": payload["window"],
                    "flagship": {role: len(rows) for role, rows in flagship_groups.items()},
                    "local": len(local_items),
                    "notable_discoveries": {
                        "models": notable_model_count,
                        "total": notable_model_count,
                    },
                    "discoveries": len(discoveries),
                    "exact_model_queries": len(requested_model_ids),
                    "report_output_bytes": report_output_bytes,
                    "timings_seconds": {
                        key: round(value, 3) for key, value in timings.items()
                    },
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
