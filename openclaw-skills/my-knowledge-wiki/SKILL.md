---
name: my-knowledge-wiki
description: 查询个人 Knowledge 服务中的文章、章节与跨领域知识结构，并生成带原文引用的学习说明。适用于解释概念、追溯基础依赖、查找已有课程或 Blog，以及回答个人知识库问题。
metadata: {"openclaw":{"skillKey":"my-knowledge-wiki","emoji":"🧭","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/my-knowledge-wiki","requires":{"anyBins":["python3","python"],"env":["MY_KNOWLEDGE_WIKI_API_URL","MY_KNOWLEDGE_WIKI_API_KEY"]},"primaryEnv":"MY_KNOWLEDGE_WIKI_API_KEY"}}
---

# My Knowledge Wiki

通过只读 Knowledge API 暴露文章、章节、引用和跨领域知识结构。

## Required Reads

- 命令、scope、响应字段、快照语义和知识组织模型见 [references/query-contract.md](references/query-contract.md)。

## Commands

```bash
python3 {baseDir}/scripts/knowledge_query.py query "DDPM 依赖哪些数学知识？"
python3 {baseDir}/scripts/knowledge_query.py learning "DDPM"
python3 {baseDir}/scripts/knowledge_query.py retrieve "DDPM"
python3 {baseDir}/scripts/knowledge_query.py ontology --domain-id mathematics
```

## Interface Contract

- `query` 返回带 citation 的回答；`search` 返回候选 Section；`retrieve` 返回 Section 原文与相邻上下文；`learning` 返回焦点概念、局部关系和材料；`ontology` 返回全局导航骨架或指定领域的审校概念图。
- 服务是只读、同步请求接口，不提供异步 task、job 状态或任务管理。`request_id` 是请求 trace 标识，不是任务 ID。
- `content_revision`、`knowledge_revision` 和 `ontology_revision` 标识响应所属的内容、知识投影和 Ontology 快照；`truncated`、`degraded` 和 `warnings` 描述响应完整性或降级状态。字段定义见查询契约。
- Ontology 以 domain、meta-node、concept 和 reviewed edge 组织知识。课程、Blog、论文和技术分析是挂在概念上的 resource，不是 Ontology 节点。
- 脚本从 `MY_KNOWLEDGE_WIKI_API_URL` 和 `MY_KNOWLEDGE_WIKI_API_KEY` 读取服务地址和 Key。远程地址必须使用 HTTPS；自签名证书只能由私有运行环境显式设置 `MY_KNOWLEDGE_WIKI_TLS_INSECURE=true`，仓库不保存 endpoint。
- 成功时 stdout 是服务返回的完整 JSON。配置、网络或 HTTP 失败时 stderr 输出错误并返回非零退出码。
