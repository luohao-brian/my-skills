# OpenClaw 技能规范参考

基于 [官方文档](https://raw.githubusercontent.com/openclaw/openclaw/main/docs/tools/skills.md) 整理，作为本项目所有技能的开发规范。

## 目录结构

每个技能是一个目录，包含 `SKILL.md` 作为入口：

```
<skill-name>/
├── SKILL.md              # 技能描述文件（必需）
├── bin/                   # 可执行文件（可选）
│   └── <binary>
└── references/            # 参考文档（可选，按需加载）
    └── *.md
```

## SKILL.md 格式

### Frontmatter（YAML）

```yaml
---
name: skill-name
description: 简要描述技能功能和触发场景
homepage: https://example.com
metadata: {"openclaw":{...}}
---
```

#### 必需字段

| 字段 | 说明 |
|------|------|
| `name` | 技能名称，小写字母、数字、连字符，最多 64 字符 |
| `description` | 技能功能描述 + 触发场景。模型根据此字段决定是否加载技能 |

#### 可选字段

| 字段 | 说明 |
|------|------|
| `homepage` | 技能相关的官方文档 URL |
| `user-invocable` | `true`（默认）/ `false`，是否在 `/` 菜单中显示 |
| `disable-model-invocation` | `true` / `false`（默认），设为 `true` 时模型不会自动加载此技能 |
| `command-dispatch` | 设为 `tool` 时，斜杠命令直接调用工具而不经过模型 |
| `command-tool` | `command-dispatch: tool` 时调用的工具名称 |
| `command-arg-mode` | `raw`（默认），将原始参数字符串转发给工具 |

### metadata 字段

**必须写成单行 JSON**，OpenClaw parser 不支持多行 metadata。

```yaml
metadata: {"openclaw":{"requires":{"bins":["curl"],"env":["API_KEY"]},"primaryEnv":"API_KEY"}}
```

#### metadata.openclaw 子字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `always` | `true` | 跳过所有门控检查，始终加载 |
| `emoji` | string | macOS Skills UI 使用的 emoji |
| `homepage` | string | 与 frontmatter `homepage` 等效 |
| `os` | string[] | 平台限制：`darwin`、`linux`、`win32` |
| `requires.bins` | string[] | 必须全部存在于 PATH |
| `requires.anyBins` | string[] | 至少一个存在于 PATH |
| `requires.env` | string[] | 环境变量必须存在，或通过 config 提供 |
| `requires.config` | string[] | `openclaw.json` 中的路径必须为 truthy |
| `primaryEnv` | string | 关联 `skills.entries.<name>.apiKey` 的环境变量 |
| `install` | object[] | 安装器列表（brew/node/go/uv/download） |

### 内容（Markdown）

Frontmatter 之后是 Markdown 指令，告诉模型如何使用这个技能。

#### 路径引用

使用 `{baseDir}` 引用技能目录路径：

```bash
{baseDir}/bin/my-tool "参数"
```

#### 参考文件引用

使用 Markdown 链接引用同目录下的文件，让模型按需加载：

```markdown
- [references/setup-guide.md](references/setup-guide.md)：配置指南
```

## description 编写规则

`description` 是模型决定是否加载技能的唯一依据，需要包含：

1. **做什么**：一句话说明功能
2. **何时用**：列出触发场景的关键词

好的示例：

```
使用火山引擎 API 联网搜索网页信息。当用户需要联网检索、查询最新资讯、搜索新闻、查官网资料时使用。
```

不好的示例：

```
Web search tool.
```

## 门控（Gating）机制

OpenClaw 在加载时过滤技能，不满足条件的技能不会进入模型上下文：

- `requires.bins`：检查宿主机 PATH（沙箱环境需额外安装）
- `requires.env`：检查环境变量是否存在，或通过 `skills.entries.<name>.env` 配置提供
- `requires.config`：检查 `openclaw.json` 中的配置路径
- `os`：检查当前平台

如果没有 `metadata.openclaw`，技能始终可用（除非被 config 禁用）。

## Token 开销

技能描述会注入系统提示词，占用 token：

- 基础开销（≥1 个技能时）：195 字符
- 每个技能：97 字符 + name + description + location 的长度
- 粗估：约 4 字符/token

保持 `description` 简洁，避免不必要的 token 消耗。

## 配置覆盖（openclaw.json）

用户可通过 `~/.openclaw/openclaw.json` 覆盖技能配置：

```json5
{
  "skills": {
    "entries": {
      "volc-gen": {
        "enabled": true,
        "apiKey": { "source": "env", "provider": "default", "id": "ARK_API_KEY" },
        "env": { "ARK_API_KEY": "..." },
        "config": { "model": "custom-model-id" }
      }
    }
  }
}
```

- `enabled: false` 禁用技能
- `env`：仅在环境变量未设置时注入
- `apiKey`：关联 `primaryEnv` 声明的变量
- `config`：自定义配置项

## 安全注意事项

- 第三方技能视为**不可信代码**，启用前应审查
- `skills.entries.*.env` 注入到宿主进程，不进入沙箱
- 技能目录发现会验证 realpath 在配置根目录内

## 参考链接

- [官方技能文档](https://docs.openclaw.ai/tools/skills)
- [GitHub 原始文档](https://raw.githubusercontent.com/openclaw/openclaw/main/docs/tools/skills.md)
- [技能配置参考](https://docs.openclaw.ai/tools/skills-config)
- [ClawHub 技能市场](https://clawhub.com)
