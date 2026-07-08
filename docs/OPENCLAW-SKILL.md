# OpenClaw Skill 规范摘要

本仓库以 `../openclaw/docs/tools/skills.md` 的当前实现为准。

## 目录

每个 skill 是一个目录，至少包含：

```text
<skill-name>/
├── SKILL.md
├── references/
└── scripts/
```

OpenClaw 支持在 skill root 下保留一层分组目录，例如：

```text
openclaw-skills/ark-tts/SKILL.md
info-track/ai-news/SKILL.md
```

## SKILL.md Frontmatter

必须包含：

```yaml
---
name: skill-name
description: 简要描述技能功能和触发场景
metadata: {"openclaw":{"emoji":"🔧"}}
---
```

要求：

- `name` 使用小写字母、数字和连字符。
- `description` 同时写清楚做什么、什么时候用。
- `metadata` 必须是单行 JSON。
- `homepage` 可作为独立字段，也可写在 `metadata.openclaw.homepage`。

## metadata.openclaw

当前常用字段：

| 字段 | 说明 |
| --- | --- |
| `skillKey` | UI 或发布侧使用的稳定 key |
| `emoji` | macOS Skills UI 展示 |
| `homepage` | Website 链接 |
| `os` | 平台过滤 |
| `always` | 跳过门控 |
| `primaryEnv` | 关联 `skills.entries.<name>.apiKey` 的环境变量 |
| `requires.bins` | PATH 上必须全部存在 |
| `requires.anyBins` | PATH 上至少存在一个 |
| `requires.env` | 必需环境变量 |
| `requires.config` | 必需 OpenClaw config 路径 |
| `install` | 依赖安装器 |

Python 依赖优先使用 `uv` installer：

```yaml
metadata: {"openclaw":{"requires":{"anyBins":["python3","python"],"env":["ARK_AGENT_PLAN_API_KEY"]},"primaryEnv":"ARK_AGENT_PLAN_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"requests>=2.32,<3"}]}}
```

## 渐进式加载

- `SKILL.md`：只写触发、必读文件、最小命令、执行合同和失败边界。
- `references/`：写详细参数、环境变量、输出字段、provider 注意事项。
- `scripts/`：放确定性 Python 实现。

不要把长 API 文档、历史迁移说明、补丁背景或维护者解释写进主规则。

## 路径

在命令里使用 `{baseDir}` 引用当前 skill 目录：

```bash
python3 {baseDir}/scripts/tool.py --help
```

## 本仓库边界

- 不新增 Rust workspace。
- 不维护 `cli/` 预编译二进制。
- 不维护 `dist/` bundle tarball。
- OpenClaw skill 实现采用 Markdown + Python。
