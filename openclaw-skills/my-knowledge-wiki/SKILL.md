---
name: my-knowledge-wiki
description: 查询个人 Knowledge 服务中的文章、章节与跨领域知识结构，并生成带原文引用的学习说明。适用于解释概念、追溯基础依赖、查找已有课程或 Blog，以及回答个人知识库问题。
metadata: {"openclaw":{"skillKey":"my-knowledge-wiki","emoji":"🧭","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/my-knowledge-wiki","requires":{"anyBins":["python3","python"],"env":["MY_KNOWLEDGE_WIKI_API_URL","MY_KNOWLEDGE_WIKI_API_KEY"]},"primaryEnv":"MY_KNOWLEDGE_WIKI_API_KEY"}}
---

# My Knowledge Wiki

通过只读 Knowledge API 查询个人知识库。先取得真实响应，再根据用户问题组织说明。

## Required Reads

- 需要选择命令、scope 或参数时，读取 [references/query-contract.md](references/query-contract.md)。
- 普通问答直接运行 `query`，无需预读参考文件。

## Commands

```bash
python3 {baseDir}/scripts/knowledge_query.py query "DDPM 依赖哪些数学知识？"
python3 {baseDir}/scripts/knowledge_query.py learning "DDPM"
python3 {baseDir}/scripts/knowledge_query.py retrieve "DDPM"
python3 {baseDir}/scripts/knowledge_query.py ontology --domain-id mathematics
```

## Contract

1. 脚本只从 `MY_KNOWLEDGE_WIKI_API_URL` 和 `MY_KNOWLEDGE_WIKI_API_KEY` 读取服务地址与长期 API Key。不要把 Key 放进命令、URL、输出或文件。只有用户明确接受自签名证书时，才设置 `MY_KNOWLEDGE_WIKI_TLS_INSECURE=true`；它只关闭本 Skill 的证书校验，不允许明文远程 HTTP。
2. 用户问问题时先用 `query`。需要查看某个概念跨数学、物理和 AI 的知识结构时用 `learning`；需要检查原始章节时用 `retrieve`；需要浏览完整规范骨架时用 `ontology`。
3. 回答只使用 API 返回的事实。保留 citation 的标题、公开链接、章节和 excerpt；缺少依据时明确说明知识库未覆盖。
4. Ontology 节点表示知识概念及其先修关系。课程、Blog、论文和技术分析是学习资源，不作为概念节点或先修边。
5. Stdout 是服务返回的完整 JSON；非零退出码表示查询失败。不要把失败解释成“知识库没有内容”。
