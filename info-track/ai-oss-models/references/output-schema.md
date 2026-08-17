# 候选结构

顶层 JSON：

```json
{
  "kind": "ai-oss-models",
  "window": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
  "sources": {
    "huggingface_models": {"ok": true, "count": 0, "selected": 0, "errors": {}},
    "huggingface_datasets": {"ok": true, "count": 0, "selected": 0, "errors": {}},
    "github_projects": {"ok": true, "count": 0, "selected": 0, "errors": {}}
  },
  "diagnostics": {
    "owner_candidates": 0,
    "local_filter_candidates": 0,
    "modality_query_candidates": 0,
    "modality_query_by_role": {"image-generation": 0, "video-generation": 0, "audio-tts": 0},
    "media_ecosystem_candidates": 0,
    "media_ecosystem_by_filter": {
      "comfyui": 0,
      "avatar": 0,
      "character-consistency": 0,
      "digital-human": 0,
      "face-swap": 0,
      "faceswap": 0,
      "identity-consistency": 0,
      "lip-sync": 0,
      "lipsync": 0,
      "person-replacement": 0,
      "talking-head": 0,
      "video-editing": 0
    },
    "global_trending_candidates": 0,
    "global_recent_candidates": 0,
    "open_candidate_union": 0,
    "local_hot_before_limit": 0,
    "local_selected": 0,
    "model_discoveries": 0,
    "media_customization_selected": 0,
    "dataset_trending_candidates": 0,
    "dataset_recent_candidates": 0,
    "dataset_official_owner_candidates": 0,
    "dataset_candidate_union": 0,
    "project_url_candidates": 0,
    "github_metric_repositories": 0,
    "deployment_profile_models": 0,
    "deployment_profile_repository_errors": 0,
    "coverage": {
      "models_by_group_and_role": {
        "flagship": {"llm": 0, "vlm": 0, "unknown": 0},
        "local": {"llm": 0, "vlm": 0, "unknown": 0},
        "notable_discoveries": {"llm": 0, "vlm": 0, "unknown": 0},
        "media_customization": {"llm": 0, "vlm": 0, "unknown": 0}
      },
      "unique_model_repositories": 0,
      "local_by_deployment": {"gguf": 0, "mlx": 0},
      "media_customization_by_capability": {"lip-sync": 0},
      "reproducible_projects": 0,
      "reproducible_by_component": {
        "data": 0,
        "training": 0,
        "model": 0,
        "evaluation": 0,
        "deployment": 0
      },
      "datasets_by_group": {
        "registered": 0,
        "notable_discoveries": 0,
        "unique_repositories": 0
      }
    }
  },
  "groups": {
    "flagship": {
      "llm": [],
      "vlm": [],
      "image-generation": [],
      "video-generation": [],
      "audio-generation": [],
      "audio-tts": [],
      "audio-stt": [],
      "ocr": [],
      "translation": [],
      "embedding": [],
      "robotics": []
    },
    "local": [],
    "reproducible": [],
    "datasets": [],
    "notable_discoveries": {
      "models": [],
      "datasets": []
    },
    "media_customization": []
  },
  "discoveries": []
}
```

正式候选包含：

```json
{
  "title": "owner/repo",
  "url": "https://huggingface.co/...",
  "summary": "候选事实摘要",
  "date": "YYYY-MM-DD",
  "event": "published",
  "source": "Hugging Face Models",
  "category": "llm",
  "metadata": {}
}
```

当前运行的热门衍生/本地部署模型和数据集的 `metadata` 包含：

```json
{
  "selection": ["hot", "priority"],
  "trendingScore": 100,
  "downloads": 10000,
  "likes": 100
}
```

模型候选还可包含发布者和当前趋势信息：

```json
{
  "publisher_tier": "unregistered",
  "trend": {
    "rank_scope": "task:text-to-speech",
    "rank": 12,
    "rank_delta": 5,
    "rankings": {
      "global": {"rank": 120, "rank_delta": 8},
      "task:text-to-speech": {"rank": 12, "rank_delta": 5}
    },
    "score_delta": 8,
    "downloads_delta": 1200,
    "likes_delta": 4,
    "signals": ["hf-task-trending", "hf-rank-rising", "hf-engagement-growing"],
    "previous_observed_at": "YYYY-MM-DD"
  }
}
```

`rank_delta > 0` 表示 `rank_scope` 对应的官方榜单排名上升；`rankings` 分别保留全局或 `task:<pipeline_tag>` 榜单。首次观察、上次快照没有该仓库，或两次运行仍在同一 UTC 自然日时，各增量为 `null`。`signals` 是可核验的来源标签，不是综合分或质量结论。`diagnostics` 只用于检查召回漏斗，不进入最终报告。

`diagnostics.coverage` 是正式入选结果的热力图投影：模型按展示分组和结构化方向计数，本地模型另按部署格式计数，媒体定制按精确能力信号计数，可复现项目按交付链组件计数。一个模型可能同时进入媒体定制与其他展示分组，因此分组单元格不可相加；使用 `unique_model_repositories` 读取跨分组去重总数。

热门衍生/本地部署模型还包含 `derivation` 和 `deployment`：

```json
{
  "derivation": ["merge", "finetune", "adapter", "quantized"],
  "deployment": ["gguf", "mlx", "quantized", "ollama-compatible", "on-device"]
}
```

模型存在 HF 精确低拒绝 tags 时还包含 `alignment`：

```json
{
  "alignment": {
    "profile": "low-refusal",
    "signals": [
      {"source": "hf-tag", "value": "uncensored"},
      {"source": "hf-tag", "value": "heretic"}
    ]
  }
}
```

只识别 `uncensored`、`abliterated`、`heretic` 和 `decensored` 精确 tags，不从仓库名或 model card 文案推断。该字段表示发布者声明的低拒绝定位，不证明零拒绝、能力保持或安全质量。命中时当前热门本地候选的 `selection` 还包含 `low-refusal`。

只有注册表通过 `model_overrides.<repo>.variant_group` 显式声明同组时，同一发布者下的多个仓库才折叠为一个代表条目，并在 `metadata.variants` 中列出仓库 ID、链接、部署格式和热度指标。不同发布者不跨发布者折叠；仅有相同 `base_model` 不触发折叠。

当前运行的热门衍生/本地部署模型 `selection` 必须包含 `hot`，还可包含 `priority`、`flagship-lineage`、`trusted-publisher`、`local-ecosystem-publisher`、`breakout`、`derivative` 或 `low-refusal`。历史运行只纳入注册表中的重点本地模型，`selection` 包含 `priority` 且不包含 `hot`，metadata 省略实时 `trendingScore`、`downloads`、`likes` 和 `trend`。正式数据集可由 `hot`、`priority` 或 `technical-artifact` 入选；`technical-artifact` 表示注册表确认其属于数据、训练、偏好、评测等开发链路。`groups.local` 为兼容字段名，报告标题使用“热门衍生与本地部署模型”。

`groups.notable_discoveries` 是从发现池自动选出的成稿候选：

- 模型来自已登记官方发布者时，`selection` 包含 `trusted-publisher` 和 `pending-registry`；当前运行中未登记 owner 的热门模型包含 `hot`、`global-discovery` 和 `pending-registry`。
- 当前运行中未登记 owner 的数据集须满足 HF 热门条件，`selection` 包含 `hot` 和 `pending-registry`；已登记主要厂商 owner 的窗口内新数据集可包含 `trusted-publisher` 和 `pending-registry`，不强制包含 `hot`。历史运行只保留后一类已登记 owner 发现。
- 模型与数据集合计最多 12 条，数据集最多 5 条；候选充足时至少 8 条。
- `repo_type` 为 `model` 或 `dataset`，`metadata.pending_registry` 为 `true`；方向分类是暂定展示字段，不等于旗舰身份确认。

重点旗舰模型、正式数据集和重点新发现还可包含：

```json
{
  "metadata": {
    "card": {
      "url": "https://huggingface.co/.../blob/main/README.md",
      "excerpt": "model card 的短证据片段",
      "ok": true
    }
  }
}
```

模型的结构化技术字段还包含：

```json
{
  "metadata": {
    "architecture": "moe | diffusion | unknown",
    "architecture_classes": ["ExampleForConditionalGeneration"],
    "scale": {"parameters": 304180418494, "source": "safetensors.total", "inherited": false},
    "papers": [
      {
        "id": "2606.19348",
        "arxiv_url": "https://arxiv.org/abs/2606.19348",
        "hf_paper_url": "https://huggingface.co/papers/2606.19348"
      }
    ]
  }
}
```

`architecture_classes` 直接来自 config；`papers` 只来自精确 `arxiv:` tag。数据集也可包含同结构的 `papers`。`card` 在找到明确的 Architecture / Model Architecture / Architecture Overview 小节时还包含 `architecture_excerpt`。

模型方向的通用证据包含：

```json
{
  "metadata": {
    "modalities": {"input": ["image", "text"], "output": ["audio", "video"]},
    "role_evidence": {
      "pipeline_tag": "image-text-to-audio-video",
      "task_signals": [
        {"source": "pipeline_tag", "value": "image-text-to-audio-video"}
      ]
    }
  }
}
```

最终入选的媒体模型，以及命中 ComfyUI/diffusers 媒体运行时或媒体定制能力的模型，还可包含部署画像：

```json
{
  "metadata": {
    "media_customization": {
      "capabilities": ["talking-head", "lip-sync", "face-swap", "person-replacement"],
      "signals": [
        {"capability": "face-swap", "source": "hf-tag", "value": "face-swap"}
      ]
    },
    "deployment_profile": {
      "runtimes": ["comfyui", "diffusers"],
      "components": [
        {
          "type": "transformer",
          "file_count": 4,
          "bytes": 123,
          "precisions": ["bf16", "fp8"],
          "source": "hf-repository-files"
        }
      ],
      "artifact_options": [
        {
          "path": "distilled/model-Q4_K_M.gguf",
          "bytes": 15687639424,
          "component": "transformer",
          "precisions": ["q4"]
        },
        {
          "path_pattern": "model-{00001..00018}-of-00018.safetensors",
          "bytes": 54000000000,
          "component": "model-weights",
          "precisions": ["bf16"],
          "file_count": 18,
          "shard_count": 18,
          "required_all": true,
          "complete": true
        }
      ],
      "workflow_files": ["workflows/example-comfy-workflow.json"],
      "precisions": ["bf16", "fp8"],
      "acceleration": {
        "methods": ["distilled", "turbo"],
        "steps": [4, 8],
        "step_evidence": [
          {"value": 4, "source": "model-card", "evidence": "..."}
        ]
      },
      "offload": ["cpu-offload"],
      "dependencies": [
        {"repo_id": "owner/component", "relation": "text-encoder", "source": "model-card"}
      ],
      "footprint": {
        "repository_bytes": 123,
        "artifact_bytes": 120,
        "artifact_file_count": 4,
        "complete_runtime_bytes": null,
        "complete_runtime_status": "partial",
        "referenced_files": ["model_fp8.safetensors"],
        "unresolved_referenced_files": [],
        "source": "hf-repository-files+model-card"
      },
      "repository_files_ok": true
    },
    "base_model_dependencies": [
      {"repo_id": "owner/base", "relation": "adapter", "source": "hf-structured"}
    ]
  }
}
```

- `components` 和 `repository_bytes` 汇总当前 HF 仓库全部权重文件，可能同时包含多个可选精度或工作流，不能直接视为单次部署占用。
- `artifact_options` 保留最多 32 个独立权重选项；索引分片先合并为一个 `required_all=true` 的 bundle，并用 `complete` 标记仓库是否包含全部分片。`workflow_files` 保留仓库内名称明确包含 workflow/ComfyUI 的 JSON 工作流。这些字段复用同一次 model detail，不增加调用。
- model card 中出现的权重文件只记为 `referenced_files`，不擅自认定为全部必需文件。因此没有显式部署 bundle manifest 时，`complete_runtime_bytes` 为 `null`，`complete_runtime_status` 为 `partial` 或 `unknown`。
- `dependencies` 合并 HF 结构化 `base_model` 关系和 model card 中带依赖语境的 HF 模型链接；它描述部署组件依赖，不做许可证判断，也不递归推算依赖仓库占用。
- `media_customization` 只接受精确 HF tags，或最终入选模型的 model card 明确措辞；不从仓库名猜测换脸、换人、数字人等能力。

方向分类先读取 HF 标准 `pipeline_tag`，再用能解析出完整输入/输出的任务 tags 补充；组合信号按 `<输入模态>-to-<输出模态>` 解析，不依赖模型 ID、发布者或仓库名。`text-to-speech` 归入 TTS，其他音频输出归入音频生成，避免把 voice conversion 或音乐生成误写成 TTS。无法得到完整输入和输出时保留空数组并使用“待确认”。

模型卡存在 Evaluation、Benchmark、Leaderboard 等明确小节，或存在以 `Benchmark` 为表头的结果表时，`card` 还包含：

```json
{
  "evaluation": {
    "source": "model-card",
    "excerpt": "评测设置、对照项、代表性结果和表格的紧凑证据",
    "caveats": "Limitations / Caveats 小节中的评测边界"
  }
}
```

`evaluation.excerpt` 保留表格单元格和必要上下文，供成稿提炼，不直接长段复制。`caveats` 为可选字段；出现小样本、内部基准、未完整评测、仅验证单一量化版本等说明时必须随结果一起处理。`source: model-card` 表示发布者仓库自述，不等于独立评测。

`card.excerpt` 只用于概括当前能力、用途和交付件，不代表该内容在本窗口发生变更。`ok` 为 `false` 时不根据仓库名补写能力。

`repository-updated` 候选还可包含提交证据：

```json
{
  "metadata": {
    "change_evidence": {
      "source": "Hugging Face commit history",
      "ok": true,
      "commits": [
        {
          "id": "commit sha",
          "title": "Update README.md",
          "date": "YYYY-MM-DD",
          "url": "https://huggingface.co/.../commit/..."
        }
      ]
    }
  }
}
```

可复现项目的每个 `metadata.artifacts[]` 可包含相同的 `change_evidence`；GitHub 子目录证据额外包含 `path`，且提交已经按该路径过滤。`ok: false` 或空提交列表表示只能确认仓库时间戳，不能说明具体变化。

已登记 GitHub 交付件还可包含：

```json
{
  "github": {
    "url": "https://github.com/owner/repo",
    "stars": 1200,
    "forks": 80,
    "open_issues": 12,
    "pushed_at": "ISO-8601",
    "trend": {
      "stars_delta": 50,
      "forks_delta": 4,
      "signals": ["github-stars-growing", "github-forks-growing"],
      "previous_observed_at": "YYYY-MM-DD"
    }
  }
}
```

GitHub 指标只来自 [reproducible-projects.json](reproducible-projects.json) 已登记仓库。它们表达工程关注与采用，不代替提交证据，也不证明模型质量。

`event` 使用：

- `published`：`createdAt` 位于窗口内。
- `repository-updated`：`lastModified` 位于窗口内。
- `trending-observed`：仅当前运行使用；仓库在观察日仍满足 HF 热门条件，但窗口内没有发布或更新时间。
- `artifact-updated`：可复现项目有 HF 交付件发布/更新，或已登记 GitHub 仓库的 `pushed_at` 位于窗口内。

顶层 `discoveries` 是全部待确认模型和热门新数据集的审计池，不直接进入最终报告；其中入选成稿的条目会以完整结构复制到 `groups.notable_discoveries`。

最终报告遵循 [format.md](format.md)。

## 紧凑成稿输入

传入 `--report-output <path>` 时，采集器额外写出单行紧凑 JSON。该文件只包含：

```json
{
  "kind": "ai-oss-models",
  "window": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
  "groups": {}
}
```

`groups` 的候选顺序和数量与完整审计 JSON 完全一致，但会删除顶层 `discoveries`、`diagnostics`、来源抓取状态，以及不参与成稿的候选摘要、许可证、开放度等字段。提交证据只保留 `ok`、提交标题和日期；model card 只保留 `ok`、状态摘要、架构摘要、评测证据与 caveats。

完整 `--output` 用于审计和排查召回，`--report-output` 用于模型成稿。不得为了节省上下文从紧凑输入再次删减正式候选。
