# README_REDDIT_OSS_MODELS

`reddit-oss-models` 是一个面向 Reddit 社区的 weekly 编排型 skill，用于监控 `r/LocalLLaMA` 和 `r/unsloth` 的本周热门 RSS，筛选与开源模型直接相关的帖子，并生成中文周报。

## 目录与入口

- skill：[`/Users/bytedance/Documents/my-skills/reddit-oss-models/SKILL.md`](/Users/bytedance/Documents/my-skills/reddit-oss-models/SKILL.md)
- RSS 解析脚本：[`/Users/bytedance/Documents/my-skills/reddit-oss-models/scripts/parse_rss.py`](/Users/bytedance/Documents/my-skills/reddit-oss-models/scripts/parse_rss.py)

## 适合什么时候用

- 想快速了解本周开源模型社区最热讨论
- 想筛出和模型发布、适配、量化、训练、本地部署直接相关的 Reddit 热帖
- 想把社区热帖整理成可转发的中文周报

## 能力范围

- 扫描 `r/LocalLLaMA` 和 `r/unsloth` 两个 RSS
- 过滤掉纯吐槽、纯报错、纯情绪类帖子
- 为每条帖子补充 subreddit、链接、摘要和流程阶段
- 汇总“本周主题总结”和“可用入口整理”

## 运行依赖

这个 skill 的关键依赖不是 Rust，而是浏览器访问路径：

- 必须优先使用 `agent-browser` 连接 host browser
- 不要把普通 headless 浏览器当主路径
- 如果 Reddit 对普通抓取有限制，继续走 host browser / CDP 路径

如果只是在本地验证 RSS 解析逻辑，可以单独查看解析脚本。

## 数据源

- `https://www.reddit.com/r/LocalLLaMA/top/.rss?t=week`
- `https://www.reddit.com/r/unsloth/top/.rss?t=week`

## 使用提醒

- 先读 RSS 内容本身，不要扩展成无关网页漫游
- 同一模型一周内如果有多条帖子，成稿时要合并主题，避免重复表述
- 没确认到模型入口时，明确写“未确认”，不要猜
- 如果高质量帖子不足 10 条，就输出实际确认到的数量

## 验证建议

当前仓库还没有为 `reddit-oss-models` 提供单独的仓库级 `verify.sh`。改动这个 skill 时，建议至少做这些检查：

- 确认 [`SKILL.md`](/Users/bytedance/Documents/my-skills/reddit-oss-models/SKILL.md) 里的浏览器要求和输出规则没有漂移
- 确认 [`parse_rss.py`](/Users/bytedance/Documents/my-skills/reddit-oss-models/scripts/parse_rss.py) 仍能识别模型关键词、排除噪声帖子
- 如果环境允许，实际访问一次 RSS，检查摘要和阶段分类是否还合理
