---
name: ark-viking
description: 查询和读取 OpenViking 知识库。用于按 Viking URI 浏览资源、语义检索博客或文档，以及为 Agent 返回匹配正文和可点击的 Rspress 原文链接；不用于写入、同步或删除知识库数据。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-viking
metadata: {"openclaw":{"skillKey":"ark-viking","emoji":"🧭","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-viking","requires":{"anyBins":["python3","python"],"env":["ARK_AGENT_PLAN_OPENVIKING_API_KEY"]},"primaryEnv":"ARK_AGENT_PLAN_OPENVIKING_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"requests>=2.32,<3"}]}}
---

# Ark Viking

使用 OpenViking 只读 API 浏览、检索和读取知识。所有调用都通过 `{baseDir}/scripts/openviking.py`。

## Required Reads

- 需要确认 HTTP 接口、参数或环境变量时，读取 [references/api-contract.md](references/api-contract.md)。
- 需要解释 `retrieve` 输出、生成 Rspress 原文链接或组装回答上下文时，读取 [references/rag-contract.md](references/rag-contract.md)。
- 需要精确 CLI 参数时，运行 `python3 {baseDir}/scripts/openviking.py --help` 或对应子命令的 `--help`。

## Credential Boundary

只读取 `ARK_AGENT_PLAN_OPENVIKING_API_KEY`。不接受命令行凭证，不读取或复用 `ARK_AGENT_PLAN_API_KEY`。

## Operation Selection

1. 已知文件 URI：使用 `read`。
2. 已知目录 URI：使用 `ls`。
3. 只需召回结果：使用 `find`。
4. 需要回答用户并提供原文来源：使用 `retrieve`。
5. 首次调用或接口异常：使用 `doctor`。

博客默认范围是 `viking://resources/codex-rspress-admin/public/`。只有用户明确指定其他范围时才覆盖。

## Agent Retrieval Flow

Agent 必须按以下链路使用 `retrieve`：

```text
用户查询 -> OpenViking 语义匹配 -> contexts[].content -> contexts[].public_url
```

1. 把用户问题原样或等价改写后传给 `retrieve`。
2. 只根据 `contexts[].content` 生成回答；用 `title` 和 `abstract` 组织结果。
3. 把同一 context 的 `public_url` 作为该内容的“原文链接”。
4. 不向用户展示内部 `uri`，除非用户明确要求诊断或资源位置。
5. `content` 为空或 `public_url` 为 `null` 时不得伪造正文或链接。

## Commands

```bash
python3 {baseDir}/scripts/openviking.py doctor
python3 {baseDir}/scripts/openviking.py ls viking://resources/codex-rspress-admin/public/
python3 {baseDir}/scripts/openviking.py read viking://resources/codex-rspress-admin/public/articles/example.md
python3 {baseDir}/scripts/openviking.py find 'Agent 上下文管理' --limit 8
python3 {baseDir}/scripts/openviking.py retrieve 'Agent 上下文管理' --limit 5
```

## Execution Contract

1. 回答只使用 `retrieve` 实际返回的 `contexts[].content`。
2. 面向用户展示标题、摘要、相关内容和 `public_url`；`uri` 仅用于内部读取和追溯，用户明确要求时才展示。
3. Rspress 链接必须由资源 URI 中的源 Markdown 路径确定性生成，不得从标题、摘要或 OpenViking 分段名猜测。
4. 空结果不补写不存在的知识；没有 `public_url` 时明确说明无法映射，不伪造链接。
5. 不调用写入、同步、删除或重建 API。
6. stdout 是 JSON；stderr 或非零退出码表示调用失败。
