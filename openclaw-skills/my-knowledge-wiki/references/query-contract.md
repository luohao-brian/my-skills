# Query Contract

## Environment

```bash
export MY_KNOWLEDGE_WIKI_API_URL="https://<host>/api/knowledge"
export MY_KNOWLEDGE_WIKI_API_KEY="<token returned once by host apikey create>"
```

`MY_KNOWLEDGE_WIKI_API_URL` 指向 Knowledge API 公网前缀。正式远程服务必须使用 HTTPS；只有 `localhost`、`127.0.0.1` 和 `::1` 可以使用 HTTP。

明确接受的自签名服务以完整 origin 写入 `config.json` 的 `tls_insecure_origins`。当前默认只允许 `https://8.140.22.158` 跳过证书校验；路径和其他 origin 不继承该权限。`MY_KNOWLEDGE_WIKI_TLS_INSECURE=true|false` 可在临时诊断时显式覆盖默认值。不要把跳过校验作为公开证书错误或网络错误的通用降级。

API Key 由 `codex-rspress-admin` 管理端创建。默认 scope 已覆盖本 skill 的全部命令：

```bash
codex-rspress-admin host apikey create --host <host> --name my-knowledge-wiki
```

Key 创建或轮换时只显示一次明文。把它放进 Agent 运行环境，不写进仓库、shell history 示例或用户产物。

## Commands and scopes

| Command | Current API | Required scope | Use |
| --- | --- | --- | --- |
| `query` | `POST /answers` | `rag:read` | 生成带服务端 citation 的知识库回答 |
| `learning` | `GET /ontology/concepts` + `GET /ontology/concepts/{node_id}` | `ontology:read` | 按概念名解析概念并返回跨领域关系与学习材料 |
| `retrieve` | `POST /retrieve` | `search:read` | 读取命中 Section 和相邻 Leaf 上下文 |
| `search` | `POST /search` | `search:read` | 检查候选文章与命中摘要 |
| `ontology` | `GET /ontology/map` | `ontology:read` | 查询当前有学习材料覆盖的概念图 |

常用参数通过 `python3 {baseDir}/scripts/knowledge_query.py <command> --help` 查看。

## Result handling

- `query` 的 `answer` 是服务生成或抽取的回答；引用事实时保留 `citations`。
- `retrieve` 的 `articles[].sections[]` 是理解原文结构的主要输入。
- `learning` 返回当前 snapshot 已有的具体概念、自然语言关系，以及挂在概念下的课程或 publication。
- `ontology` 只返回已有学习材料覆盖的概念。它表达知识位置和经审校关系，不表达某篇文章声称的事实。
- HTTP `401` 表示 Key 无效，`403` 表示 scope 不足，`429` 表示配额耗尽，`503` 表示服务繁忙。它们都不是空结果。
