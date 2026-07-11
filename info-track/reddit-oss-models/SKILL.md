---
name: reddit-oss-models
description: 监控 Reddit 的 r/LocalLLaMA 和 r/unsloth 的本周热门 RSS，筛选与开源模型直接相关的帖子，生成中文 weekly 简报。当用户需要获取开源模型最新动态、热门模型讨论、或 Reddit 社区热帖时使用此技能。
homepage: https://github.com/luohao-brian/my-skills/tree/main/info-track/reddit-oss-models
metadata: {"openclaw":{"skillKey":"reddit-oss-models","emoji":"🧵","homepage":"https://github.com/luohao-brian/my-skills/tree/main/info-track/reddit-oss-models"}}
---

# Reddit 开源模型监控

监控 Reddit 的 r/LocalLLaMA 和 r/unsloth 的本周热门 RSS，筛选与开源模型直接相关的帖子，生成中文 weekly 简报。

## 数据源

- https://www.reddit.com/r/LocalLLaMA/top/.rss?t=week
- https://www.reddit.com/r/unsloth/top/.rss?t=week

## 筛选规则

只保留与开源模型直接相关的热门帖子。

**排除内容：**
- 纯吐槽帖
- 纯工具报错帖
- 纯情绪帖
- 与开源模型无直接关系的帖子

**合并规则：**
- 如果同一模型一周内有多条相关热帖，允许保留，但总结时要合并主题，避免重复表述

## 输出要求

生成 weekly 开源模型热帖 Top 10。

**每条热帖包含：**
1. 帖子标题
2. subreddit（r/LocalLLaMA 或 r/unsloth）
3. 帖子链接
4. 核心内容摘要
5. 流程摘要 - 说明这条帖子反映了模型从发布、适配、量化、训练到本地可用的哪一步

**最后追加两部分：**

### 1. 本周讨论主题总结

总结这周最热的开源模型、大家主要在讨论什么、这些讨论反映出什么趋势。

### 2. 可用入口整理

按模型汇总可用入口，优先给出：
- LM Studio 入口
- Unsloth 入口
- 官网 / 官方模型页入口

## 写作要求

- 输出中文，结构清晰，可直接转发
- 不要只写一句话摘要，要写出核心内容和流程摘要
- 链接尽量直接给到帖子原链接、模型页或文档页
- 如果某个入口没有确认到，明确写"未确认"，不要猜测或编造
- 如果本周高质量帖子不足 10 条，就输出实际能确认的数量，并说明原因，不要凑数

## 使用流程

1. 读取两个数据源的 RSS 内容，提取热门帖子。
2. 合并两个 subreddit 的帖子并按热度排序。
3. 应用筛选和合并规则。
4. 生成中文简报。
