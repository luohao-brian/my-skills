# 候选结构

顶层 JSON：

```json
{
  "kind": "ai-oss-models",
  "window": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
  "sources": {
    "huggingface_models": {"ok": true, "count": 0, "selected": 0, "errors": {}},
    "huggingface_datasets": {"ok": true, "count": 0, "selected": 0, "errors": {}}
  },
  "groups": {
    "flagship": {
      "llm": [],
      "vlm": [],
      "image-generation": [],
      "video-generation": [],
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
    }
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

热门衍生/本地部署模型和数据集的 `metadata` 包含：

```json
{
  "selection": ["hot", "priority"],
  "trendingScore": 100,
  "downloads": 10000,
  "likes": 100
}
```

热门衍生/本地部署模型还包含 `derivation` 和 `deployment`：

```json
{
  "derivation": ["merge", "finetune", "adapter", "quantized"],
  "deployment": ["gguf", "mlx", "quantized", "ollama-compatible", "on-device"]
}
```

热门衍生/本地部署模型和数据集的 `selection` 必须包含 `hot`；模型还可包含 `priority`、`flagship-lineage`、`trusted-publisher`、`breakout` 或 `derivative`。时间命中但不满足热门条件的条目不进入正式分组。`groups.local` 为兼容字段名，报告标题使用“热门衍生与本地部署模型”。

`groups.notable_discoveries` 是从发现池自动选出的成稿候选：

- 模型来自已登记官方发布者，`selection` 包含 `trusted-publisher` 和 `pending-registry`。
- 数据集满足 HF 热门条件，`selection` 包含 `hot` 和 `pending-registry`。
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

`card.excerpt` 只用于概括能力、用途和交付件，不代表该内容在本窗口发生变更。`ok` 为 `false` 时不根据仓库名补写能力。

`event` 使用：

- `published`：`createdAt` 位于窗口内。
- `repository-updated`：`lastModified` 位于窗口内。
- `artifact-updated`：可复现项目有交付件位于窗口内。

顶层 `discoveries` 是全部待确认模型和热门新数据集的审计池，不直接进入最终报告；其中入选成稿的条目会以完整结构复制到 `groups.notable_discoveries`。

最终报告遵循 [format.md](format.md)。
