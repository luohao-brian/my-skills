---
name: ai-labs-tracker
description: 追踪 OpenAI、Anthropic 和 Google DeepMind 三家 AI 实验室的最新动态。当用户需要获取 OpenAI、Anthropic、Google Gemini 三家公司最新动态、AI 行业月报、技术更新汇总时使用此技能。
---

# AI Labs Tracker

追踪 OpenAI、Anthropic 和 Google DeepMind 三家公司过去一个月内的最新动态，生成结构化的追踪报告。

## 追踪周期

- 默认追踪周期：**过去 30 天**
- 可调整范围：7 天 / 30 天 / 90 天

## 目标公司

1. **OpenAI** - GPT 系列模型、ChatGPT、API 平台
2. **Anthropic** - Claude 系列模型、Anthropic API
3. **Google DeepMind** - Gemini 系列模型、Google AI 服务

## 信息源

三家公司的官方信息源列表详见 [references/sources.md](references/sources.md)

## 内容分类标准

每条动态按以下三类之一进行分类：

### 1. 产品发布 (Product Release)
- 新产品/功能的正式发布
- 重大版本更新（如 GPT-4、Claude 3、Gemini 2.0）
- 面向消费者的应用上线

### 2. 技术与工程 (Technology & Engineering)
- API 更新与变更日志
- 性能优化与基础设施改进
- 开发者工具与 SDK 更新
- 定价策略调整

### 3. 前沿研究 (Frontier Research)
- 学术论文发布
- 模型能力突破（推理、多模态、长上下文等）
- 安全研究与对齐技术
- 开源代码/数据集发布

## 输出格式

每条记录按以下格式输出：

```
### [分类] Title
- **Link**: URL
- **Date**: YYYY-MM-DD
- **Summary**: 2-3 句话概括核心内容
```

## 搜索工具建议

| 场景 | 推荐工具 | 说明 |
|------|----------|------|
| 海外官网/博客 | `my-fetch` + 代理 | 抓取 OpenAI、Anthropic、DeepMind 官方博客 |
| 新闻聚合搜索 | `volc-websearch` | 搜索补充性行业报道 |
| 国内访问 | `web_fetch` | 抓取国内镜像或翻译内容 |

### 代理配置（抓取海外站点时）

```
--http-proxy="http://192.168.1.128:8888" \
--https-proxy="http://192.168.1.128:8888" \
--no_proxy="127.0.0.1,localhost,192.168.*.*,10.*.*.*,100.64.*.*,172.*.*.*"
```

## 报告模板

完整报告结构参考 [references/template.md](references/template.md)

## 工作流程

1. 确定追踪周期（默认过去 30 天）
2. 依次访问三家公司的官方信息源
3. 筛选目标时间范围内的动态
4. 按分类标准整理内容
5. 按模板格式生成报告
