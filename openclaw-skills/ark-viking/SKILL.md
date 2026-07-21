---
name: ark-viking
description: 检索和读取 OpenViking 只读知识库，并按文章返回相关度、文章标题、原文链接及相关章节正文。用于查找博客或文档、回答需要原文依据的问题，或按 Viking URI 浏览资源；不用于写入、同步或删除数据。
metadata: {"openclaw":{"skillKey":"ark-viking","emoji":"🧭","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-viking","requires":{"anyBins":["python3","python"],"env":["ARK_AGENT_PLAN_OPENVIKING_API_KEY"]},"primaryEnv":"ARK_AGENT_PLAN_OPENVIKING_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"requests>=2.32,<3"}]}}
---

# Ark Viking

通过 `{baseDir}/scripts/openviking.py` 只读访问 OpenViking。

## 操作

1. 需要文章级检索结果：运行 `retrieve`。
2. 只查看原始语义命中：运行 `find`。
3. 已知目录 URI：运行 `ls`。
4. 已知文件 URI：运行 `read`。
5. 首次调用或接口异常：运行 `doctor`。

博客默认检索范围为 `viking://resources/codex-rspress-admin/public/`。仅在用户指定其他范围时传入 `--target-uri`。

## 文章检索

```bash
python3 {baseDir}/scripts/openviking.py retrieve '查询内容' --limit 3
```

`--limit` 表示不同文章的最大数量。输出必须包含每篇文章的相关度、文章标题、文章链接及相关章节正文。

使用或展示 `retrieve` 结果前，读取 [references/retrieval-contract.md](references/retrieval-contract.md)。需要确认接口、环境变量或底层命令时，读取 [references/api-contract.md](references/api-contract.md)。需要完整参数时运行对应子命令的 `--help`。

## 边界

- 只根据 `articles[].sections[].content` 回答内容问题。
- 不把章节标题当作文章标题。
- 不把 `.abstract.md` 或 `.overview.md` 当作章节正文。
- 不展示内部 Viking URI，除非用户明确要求诊断。
- 不伪造缺失的标题、正文或链接。
- 不调用写入、同步、删除或重建接口。
- stdout 为 JSON；stderr 或非零退出码表示失败。
