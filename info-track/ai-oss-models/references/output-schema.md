# 候选结构

采集器的完整 `--output` 用于核对来源、召回和证据；`--report-output` 保留成稿所需的 `kind`、`window`、`ecosystem_architecture`、`development_baselines` 和 `groups`。两个文件的正式候选顺序与数量一致。

```json
{
  "kind": "ai-oss-models",
  "window": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
  "ecosystem_architecture": [],
  "development_baselines": {"tools": [], "datasets": []},
  "sources": {"huggingface_models": {"ok": true, "count": 0, "selected": 0, "errors": {}}, "github_tools": {"ok": true, "count": 0, "selected": 0, "errors": {}}, "huggingface_development_datasets": {"ok": true, "count": 0, "selected": 0, "errors": {}}},
  "diagnostics": {
    "owner_candidates": 0,
    "local_filter_candidates": 0,
    "modality_query_candidates": 0,
    "modality_query_by_role": {"llm": 0, "vlm": 0, "decision": 0, "media-conditioning": 0, "media-enhancement": 0, "image-generation": 0, "video-generation": 0, "audio-generation": 0, "audio-tts": 0, "audio-stt": 0},
    "media_ecosystem_candidates": 0,
    "media_ecosystem_by_filter": {"comfyui": 0, "mask-generation": 0, "pose-estimation": 0, "face-swap": 0},
    "global_trending_candidates": 0,
    "global_recent_candidates": 0,
    "open_candidate_union": 0,
    "local_hot_before_limit": 0,
    "local_selected": 0,
    "model_discoveries": 0,
    "media_customization_selected": 0,
    "media_open_activity_selected": 0,
    "deployment_profile_models": 0,
    "deployment_profile_repository_errors": 0,
    "coverage": {
      "models_by_group_and_role": {"flagship": {}, "local": {}, "notable_discoveries": {}, "media_customization": {}},
      "unique_model_repositories": 0,
      "local_by_deployment": {},
      "media_customization_by_capability": {},
      "media_by_discovery_track": {}
    }
  },
  "groups": {
    "flagship": {"llm": [], "vlm": [], "decision": [], "media-conditioning": [], "media-enhancement": [], "image-generation": [], "video-generation": [], "audio-generation": [], "audio-tts": [], "audio-stt": [], "ocr": [], "translation": [], "embedding": [], "robotics": []},
    "local": [],
    "notable_discoveries": {"models": []},
    "media_customization": [],
    "ecosystem_baselines": {"robotics": []},
    "development": {"tools": [], "datasets": [], "opportunities": []}
  },
  "discoveries": []
}
```

`media_ecosystem_by_filter` 的实际键来自 `ecosystem-architecture.json` 的精确过滤器。`flagship` 的每个角色固定存在；当前运行可含本期无仓库更新、但仍热门或有活跃衍生引用的已登记主模型，历史 `--date` 只保留窗口发布/更新。此类条目的 `metadata.ecosystem_activity` 包含本次候选池的直接引用数、活跃衍生仓 ID 与采样来源，不能视为全站衍生总量。已登记 VLA 模型参与 `groups.flagship.robotics` 的当前热榜和活跃衍生筛选；`groups.ecosystem_baselines.robotics` 保留空数组以兼容旧输入。`groups.media_customization` 是兼容字段名，报告标题使用“ComfyUI 媒体工作流生态”。`discoveries` 是未确认模型审计池，不直接进入报告。

## 模型候选

```json
{
  "title": "owner/repo",
  "url": "https://huggingface.co/owner/repo",
  "summary": "候选事实摘要",
  "date": "YYYY-MM-DD",
  "event": "published | repository-updated | trending-observed | derivatives-observed | engagement-observed | capability-observed",
  "source": "Hugging Face Models",
  "category": "media-conditioning",
  "metadata": {
    "selection": ["hot", "priority"],
    "role": "media-conditioning",
    "ecosystem_paths": [{"ecosystem": "media", "stage": "conditioning", "source": "hf-pipeline_tag", "value": "mask-generation"}],
    "canonical_model": "owner/base",
    "canonical_model_trace": {"status": "resolved", "canonical_model": "owner/base", "root_model": "owner/base", "declared_canonical": "owner/base", "matches_declaration": true, "hops": [{"from": "owner/quantized", "to": "owner/base", "relation": "quantized", "source": "hf-tag", "evidence": "base_model:quantized:owner/base"}]},
    "modalities": {"input": ["image"], "output": ["mask"], "signals": [{"source": "pipeline_tag", "value": "mask-generation"}]},
    "architecture": "unknown",
    "architecture_classes": ["ExampleModel"],
    "scale": {"parameters": 0, "source": "safetensors.total", "inherited": false},
    "papers": [{"id": "2606.19348", "arxiv_url": "https://arxiv.org/abs/2606.19348", "hf_paper_url": "https://huggingface.co/papers/2606.19348"}],
    "card": {"ok": true, "excerpt": "模型卡当前状态摘要"},
    "change_evidence": {"ok": true, "commits": [{"title": "Add model weights", "date": "YYYY-MM-DD"}]}
  }
}
```

字段缺失时省略，不能把示例零值写进报告。`event=repository-updated` 只证明 HF 仓库时间戳变化；具体改动须由 `change_evidence.commits` 支持。`card.excerpt` 只说明当前能力，不证明窗口内变化。`card` 可另含 `architecture_excerpt` 和 `evaluation`；评测的 `source=model-card` 表示发布方自述，需同时读 `caveats`。`architecture_classes` 直接来自 config，论文只来自精确 `arxiv:` tag。

热门衍生与本地模型可包含：

```json
{
  "derivation": ["adapter", "finetune", "merge", "quantized", "distilled"],
  "deployment": ["gguf", "mlx", "quantized", "ollama-compatible", "on-device"],
  "base_model_dependencies": [{"repo_id": "owner/base", "relation": "adapter", "source": "hf-tag", "evidence": "base_model:adapter:owner/base"}],
  "variants": [],
  "trendingScore": 100,
  "downloads": 10000,
  "likes": 100,
  "trend": {"rank_scope": "task:mask-generation", "rank": 12, "rank_delta": 5, "score_delta": 8, "downloads_delta": 1200, "likes_delta": 4, "signals": ["hf-rank-rising"], "previous_observed_at": "YYYY-MM-DD"}
}
```

`canonical_model_trace.hops` 从当前仓逐跳指向上游，每跳保存 HF cardData 或精确 tag 来源；同一跳的全部原始信号保留在 `signals`。`canonical_model` 是路径中验证过的衍生线主模型；`root_model` 是已取得结构化父链的最远唯一终点，二者可能不同。`status=resolved` 表示链在已获取的 HF 字段中到达唯一终点；`ambiguous`、`conflicting-relations`、`cycle`、`depth-limit` 不产出唯一主模型。`parent-unavailable` 可以保留已经由当前仓直接证实的 `canonical_model`，但没有 `root_model`。`declared_canonical` 留存注册表或筛选阶段的原声明；`matches_declaration=false` 表示声明不在追溯路径上，不能悄悄覆盖证据。完整审计 JSON 另有各状态计数和父仓获取错误。`selection` 的 `hot`、`priority`、`trusted-publisher`、`global-discovery`、`pending-registry`、`derivative`、`low-refusal` 等值是召回原因；`groups.local` 是采集入口，不是一级模型类别。历史运行只纳入注册表中的重点本地模型，省略实时热度与趋势。只有注册表明确声明 `variant_group` 时才折叠同发布者变体。

低拒绝模型还可带 `alignment.profile=low-refusal` 和精确 HF tag 信号。只识别 `uncensored`、`abliterated`、`heretic`、`decensored`；这是发布者定位，不证明能力或质量。

音频细分任务由 `metadata.audio_tasks.tasks` 记录，并附精确 tag 或注册表来源。`text-to-audio`、`video-to-audio` 只给输入输出方向，不自动证明歌曲、音效或 Foley。决策模型的 `role=decision` 与原生 `choice`、`score`、`noul`、JEV 协议兼容、语义正确率是不同证据，报告分别说明。

## ComfyUI 媒体工作流候选

`metadata.media_customization` 只在有精确任务、tag 或模型卡证据时出现。环节映射如下：

| `lanes` | `capabilities` 示例 | 实际产物及下游 |
| --- | --- | --- |
| `media-conditioning` | `segmentation-mask`, `pose-extraction`, `motion-extraction`, `depth-map`, `face-analysis` | mask、关键点、运动、深度或人脸框，供动画与编辑使用 |
| `image-to-video` | `image-to-video`, `reference-to-video`, `keyframe-control` | 视频片段，供后期编辑使用 |
| `character-animation` | `character-animation`, `motion-transfer`, `motion-control` | 受动作或姿态控制的视频 |
| `audio-driven-avatar` | `audio-driven-video`, `lip-sync`, `talking-head` | 语音驱动的角色视频 |
| `video-editing-effects` | `face-swap`, `person-replacement`, `video-editing`, `video-effects` | 替换或修补后的帧/视频 |
| `media-enhancement` | `image-enhancement`, `video-enhancement` | 清晰度、分辨率或帧率增强后的图像/视频 |

```json
{
  "media_customization": {
    "lanes": ["media-conditioning"],
    "capabilities": ["segmentation-mask"],
    "signals": [{"capability": "segmentation-mask", "source": "hf-pipeline_tag", "value": "mask-generation"}]
  },
  "comfyui_integration": {
    "input_modalities": ["image"],
    "output_modalities": ["mask"],
    "upstream": ["source-image-or-video", "select-subject-or-control-region"],
    "core": {"runtime": "comfyui", "capabilities": ["segmentation-mask"], "components": [], "dependencies": []},
    "downstream": ["mask-pose-depth-or-motion-control", "animation-or-editing-workflow"],
    "workflow_files": [],
    "topology_source": "capability-template",
    "workflow_status": "recommended-topology-not-validated-workflow"
  },
  "activity_density": {"high_activity": true, "signals": ["high-trending"], "repository_age_days": 3, "downloads_per_day": 2000.0, "likes_per_day": 10.0},
  "discovery_tracks": ["open-activity"]
}
```

`hf-pipeline_tag` 和 `hf-tag` 是 HF 结构化任务或精确标签；`model-card` 是当前仓自述；`upstream-model-card` 是 ComfyUI 打包仓明确链接的一层原模型自述，须保留 `repo_id`。没有结构化任务的候选必须有模型卡证据。`topology_source=capability-template` 只给建议连接；`workflow_files` 只证明仓库交付了 JSON 工作流文件，不代表当前环境已运行。分割等控制模型输出不会自动带补帧、音频混流或视频编码。

每个正式模型候选都采集 `deployment_profile`，可包含 `runtimes`、按文件归类的 `components`、最多 32 个 `artifact_options`、`workflow_files`、`precisions`、`acceleration.methods/steps/step_evidence`、`offload`、`media_specs.evidence`、`dependencies`、`footprint` 和 `repository_files_ok`。`media_specs.evidence` 只保存模型卡中同时出现分辨率、倍率或 fps 数值和任务词的原句；按原句区分输入与输出，不能把两者颠倒。`components` 和 `footprint.repository_bytes` 覆盖仓库全部权重，可能包含互斥精度；不能当成单次部署显存。报告从 `artifact_options` 选当前仓实际交付的主权重或组件文件，注明精度、分片和备选关系；不能把仓库大小或参数量当作权重文件大小。`artifact_options` 中 `required_all=true` 的分片必须一并下载。没有完整 bundle manifest 时，`complete_runtime_bytes=null` 且状态为 `partial` 或 `unknown`。外部依赖只记录，不递归估算占用。

`activity_density.signals` 与 `discovery_tracks` 只表示高 Trending、近期活动、日均下载/点赞速度或跨日增量等透明观察条件，不合成为质量分。正式 ComfyUI 候选必须有精确 `comfyui` 证据；只有 SAM 基础权重而没有 ComfyUI 证据的仓库留在基础模型或发现分节。

## 本地训练候选

`development_baselines.local_experiments` 登记 SFT、离线 response 蒸馏、RLVR、文生视频 LoRA、视频 IC-LoRA、音效 LoRA、音乐 LoRA 的精确模型/数据集组合。当前运行的 `groups.development.opportunities` 独立于 7 天窗口，核验模型与数据集可访问。常规数据集通过 HF dataset server 核指定 config/split 必需列；音频还核 Audio 特征；视频通过仓库 JSON manifest 核全部必需列及所引用的视频路径。它不表示本机已完成训练。结构示例：

```json
{
  "id": "small-math-rlvr",
  "method": "rlvr-grpo",
  "model": {"id": "Qwen/Qwen2.5-0.5B-Instruct", "parameters": 494032768, "main_weight": {"path": "model.safetensors", "bytes": 988097824}},
  "dataset": {"id": "trl-lib/DeepMath-103K", "config": "default", "split": "train", "required_columns": ["prompt", "solution"], "columns": ["prompt", "solution"]},
  "signal": "对生成答案运行可程序验证的数学正确率奖励",
  "tools": [{"project": "huggingface/trl", "component": "GRPOTrainer", "role": "采样生成并执行 RLVR 更新", "evidence": "https://huggingface.co/docs/trl/grpo_trainer"}],
  "local_scope": "先抽样，再测生成长度与峰值显存",
  "status": "metadata-verified-runtime-unmeasured"
}
```

`main_weight` 是实际文件或完整分片大小，不是训练显存。小模型参数量须有 HF `safetensors.total` 结构化证据且不超过登记的 `max_parameters`；视频大模型可缺此字段，但须明确 `model_weight_path` 并验证当前仓文件字节数。若必需列或媒体路径缺失、音频特征不符、参数量超出上限、权重文件不完整或上游接口不可访问，该组合不进入 `opportunities`，错误写入 `sources.local_training_opportunities.errors`。媒体组合另有 `preparation`（文件转换和预处理）与 `resource_evidence`（官方资源说明）；官方数字不得写作本机实测。指定历史 `--date` 时 `opportunities=[]`。`tools` 说明具体组件和职责，其文档证据不等于在本机成功运行。

`groups.development.tools` 和 `.datasets` 仍只收本窗口精确登记仓库的发布或更新，供审计使用：

```json
{
  "tools": [{"title": "huggingface/trl", "event": "repository-updated", "date": "YYYY-MM-DD", "category": "development-tool", "metadata": {"domains": ["llm-vlm"], "methods": ["sft", "dpo", "grpo", "distillation"], "entry": "官方训练入口", "evidence": "https://huggingface.co/docs/trl/grpo_trainer", "stars": 0}}],
  "datasets": [{"title": "HuggingFaceH4/ultrafeedback_binarized", "event": "repository-updated", "date": "YYYY-MM-DD", "category": "development-dataset", "metadata": {"domains": ["llm-vlm"], "methods": ["dpo"], "sample_unit": "chosen/rejected preference pair", "downloads": 0, "likes": 0}}]
}
```

这些窗口条目不直接进入报告第四节。工具若有本窗口 GitHub 最新提交，还可带 `metadata.change_evidence`；提交若只改 README 或没有文件差异证据，仍不能说明新增了哪种训练能力。单卡训练是否可行仍需实际测量，不能从模型参数量或工具支持 LoRA/GRPO 就推断能在 L20/5090 上训练。

## 紧凑成稿输入

`--report-output` 为单行紧凑 JSON，包含 `kind`、`window`、两份基线摘要与 `groups`。每个模型候选保留输入输出、生态阶段、任务、热度、评测、依赖、工作流和提交证据，删除抓取状态、诊断和候选摘要。完整 `--output` 用于审计和覆盖诊断；不要从紧凑输入再次删减正式候选。
