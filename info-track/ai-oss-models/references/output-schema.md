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
    "datasets": []
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

本地部署和数据集的 `metadata` 包含：

```json
{
  "selection": ["hot", "priority"],
  "trendingScore": 100,
  "downloads": 10000,
  "likes": 100
}
```

本地部署和数据集的 `selection` 必须包含 `hot`；还可包含 `priority`、`flagship-lineage`、`trusted-publisher` 或 `breakout`。时间命中但不满足热门条件的条目不进入正式分组。

`event` 使用：

- `published`：`createdAt` 位于窗口内。
- `repository-updated`：`lastModified` 位于窗口内。
- `artifact-updated`：可复现项目有交付件位于窗口内。

`discoveries` 是白名单 owner 下的待确认模型，不进入最终报告。

最终报告遵循 [format.md](format.md)。
