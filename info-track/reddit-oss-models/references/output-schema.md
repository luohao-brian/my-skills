# 分组输出与周报格式

顶层 JSON：

```json
{
  "kind": "ai-open-source-updates",
  "groups": {
    "reddit": [],
    "github_trending": [],
    "huggingface_models": {"分类名": []},
    "huggingface_datasets": []
  }
}
```

每条候选统一包含 `title`、`url`、`summary`、`date`、`source`、`category`、`score`、`metadata`。不同分组的 `score` 不可直接横向比较。

最终报告依次输出：

1. Reddit 开源模型热帖。
2. GitHub Weekly AI / Agent / LLM Trending。
3. Hugging Face 开源模型，按固定模型分类分节。
4. Hugging Face 开源数据集。
5. 本周主题总结与可用入口。

每条记录固定使用：

```markdown
### 1. 标题

- 来源：GitHub Trending
- 摘要：一句中文摘要。
- 时间：YYYY-MM-DD
- 链接：[原文](https://example.com)
```

来源没有明确日期时可以省略“时间”，其余字段顺序不变。
