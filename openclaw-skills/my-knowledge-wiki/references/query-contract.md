# Query Contract

## Environment

```bash
export MY_KNOWLEDGE_WIKI_API_URL="https://<host>/api/knowledge"
export MY_KNOWLEDGE_WIKI_API_KEY="<token returned once by host apikey create>"
# 仅用于用户明确接受的自签名 HTTPS
export MY_KNOWLEDGE_WIKI_TLS_INSECURE="true"
```

`MY_KNOWLEDGE_WIKI_API_URL` 指向 Knowledge API 公网前缀。正式远程服务必须使用 HTTPS；只有 `localhost`、`127.0.0.1` 和 `::1` 可以使用 HTTP。

`MY_KNOWLEDGE_WIKI_TLS_INSECURE=true` 只跳过该 Skill 的 HTTPS 证书校验，适用于明确声明为 `self-signed` 的 Host。不要把它作为公开证书错误或网络错误的通用降级。

API Key 由 `codex-rspress-admin` 管理端创建。默认 scope 已覆盖本 skill 的全部命令：

```bash
codex-rspress-admin host apikey create --host <host> --name my-knowledge-wiki
```

Key 创建或轮换时只显示一次明文。把它放进 Agent 运行环境，不写进仓库、shell history 示例或用户产物。

## Commands and scopes

| Command | Current API | Required scope | Use |
| --- | --- | --- | --- |
| `query` | `POST /answers` | `rag:read` | 生成带服务端 citation 的知识库回答 |
| `learning` | `GET /ontology/nodes` + `GET /ontology/nodes/{node_id}/learning-view` | `ontology:read` | 按概念名解析节点并返回跨领域先修结构与节点文章 |
| `retrieve` | `POST /retrieve` | `search:read` | 读取命中 Section 和相邻 Leaf 上下文 |
| `search` | `POST /search` | `search:read` | 检查候选文章与命中摘要 |
| `ontology` | `GET /ontology/graph` | `ontology:read` | 查询规范 Ontology 节点与先修边 |

常用参数通过 `python3 {baseDir}/scripts/knowledge_query.py <command> --help` 查看。

## Result handling

- `query` 的 `answer` 是服务生成或抽取的回答；引用事实时保留 `citations`。
- `retrieve` 的 `articles[].sections[]` 是理解原文结构的主要输入。
- `learning` 返回当前 snapshot 已有的知识节点、自然语言关系和挂在各节点下的文章；空节点表示当前没有对应文章，不表示学习状态。
- `ontology` 返回规范结构。它表达知识位置和先修，不表达某篇文章声称的事实。
- HTTP `401` 表示 Key 无效，`403` 表示 scope 不足，`429` 表示配额耗尽，`503` 表示服务繁忙。它们都不是空结果。
