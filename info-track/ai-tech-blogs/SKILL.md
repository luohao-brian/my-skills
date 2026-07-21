---
name: ai-tech-blogs
description: 从 Hubwiz 与 QingkeAI 采集近期 AI 技术博客，按固定来源配比生成中文候选列表。适用于技术博客周报、工程实践阅读清单和 AI 技术文章聚合。
metadata: {"openclaw":{"skillKey":"ai-tech-blogs","emoji":"📚","homepage":"https://github.com/luohao-brian/my-skills/tree/main/info-track/ai-tech-blogs","requires":{"anyBins":["python3","python"]}}}
---

# AI 技术博客聚合

先运行采集器，再由 agent 去重、核验并生成最终中文列表。

按需读取：

- [references/sources.md](references/sources.md)：来源、配比和筛选边界。
- [references/output-schema.md](references/output-schema.md)：候选字段和成稿格式。

```bash
python3 {baseDir}/scripts/tech_blogs.py --days 7 --limit 50 --weights Hubwiz=0.75,QingkeAI=0.25 --output tech-blog-candidates.json --stats
```

执行合同：

1. 默认窗口为最近 7 天，最多 50 篇，目标配比为 Hubwiz 75%、QingkeAI 25%。
2. 某一来源候选不足时把剩余额度给另一来源；不为凑满 50 篇扩大时间窗。
3. 按 URL、转载关系和标题主题去重；排除纯推广、导航页、无有效链接和明显非技术内容。
4. 最终列表保持 `标题 → 来源 → 摘要 → 时间 → 链接` 的字段顺序。
5. 只基于候选与原文改写中文摘要，不推测未给出的实现、指标或结论。
