---
name: reddit-oss-models
description: 采集 Reddit 开源模型热帖、GitHub Weekly AI/Agent/LLM Trending，以及 Hugging Face 热门开源模型和数据集，生成 AI 开源周报。适用于追踪开源模型、Agent 项目、本地推理、量化、训练生态与数据集更新。
metadata: {"openclaw":{"skillKey":"reddit-oss-models","emoji":"🧵","homepage":"https://github.com/luohao-brian/my-skills/tree/main/info-track/reddit-oss-models","requires":{"anyBins":["python3","python"]}}}
---

# AI 开源更新

运行综合采集器获取四组候选；由 agent 负责核验、主题合并和最终中文周报。

执行前按需读取：

- [references/sources.md](references/sources.md)：来源边界与模型分类规则。
- [references/output-schema.md](references/output-schema.md)：分组字段与成稿格式。

```bash
python3 {baseDir}/scripts/open_source_updates.py --reddit-limit 10 --github-limit 10 --model-max 10 --dataset-limit 20 --output oss-candidates.json --stats
```

仅需 Reddit RSS 时使用：

```bash
python3 {baseDir}/scripts/parse_rss.py 'https://www.reddit.com/r/LocalLLaMA/top/.rss?t=week' 'https://www.reddit.com/r/unsloth/top/.rss?t=week' --summary
```

执行合同：

1. 保持 Reddit、GitHub Weekly Trending、Hugging Face Models、Hugging Face Datasets 四组边界，不把不同热度口径混成统一排名。
2. Reddit 与 GitHub 默认各保留最多 10 条；数据集最多 20 条；模型每类最多 10 条。
3. 合并同一仓库、模型、数据集或同一发布事件的重复讨论；保留能体现不同流程阶段的独立帖子。
4. 剔除纯吐槽、纯求助、工具报错、无开源 AI 关系和无法确认入口的噪音。
5. 入口或事实无法确认时写“未确认”，不得猜测。

`LLM_API_KEY` 可选。存在时采集器会辅助生成中文简介和模型分类；缺失时使用来源 metadata 与确定性规则。
