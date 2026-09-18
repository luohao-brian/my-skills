# Query Contract

## Environment

```bash
export MY_KNOWLEDGE_WIKI_API_URL="https://<host>/api/knowledge"
export MY_KNOWLEDGE_WIKI_API_KEY="<token returned once by host apikey create>"
```

`MY_KNOWLEDGE_WIKI_API_URL` 指向 Knowledge API 公网前缀。正式远程服务必须使用 HTTPS；只有 `localhost`、`127.0.0.1` 和 `::1` 可以使用 HTTP。

自签名 HTTPS 服务由私有运行环境设置 `MY_KNOWLEDGE_WIKI_TLS_INSECURE=true`。默认值是 `false`；仓库不保存 endpoint 或 TLS 例外。该变量只影响 `MY_KNOWLEDGE_WIKI_API_URL` 指向的当前 HTTPS 服务，不能用于远程 HTTP。

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
| `ontology` | `GET /ontology/map` | `ontology:read` | 查询跨领域导航骨架或指定领域的完整审校概念图 |

常用参数通过 `python3 {baseDir}/scripts/knowledge_query.py <command> --help` 查看。

## Execution model

所有命令都是同步、只读请求，没有异步 task 或 job 生命周期。`request_id` 用于请求关联和服务端 trace，不表示可轮询、取消或恢复的任务。

- 成功：退出码 `0`，stdout 为未经裁剪的服务 JSON。
- 配置、TLS、网络、HTTP 或响应格式错误：非零退出码，stderr 为脱敏错误，stdout 为空。
- HTTP `401` 表示 Key 无效，`403` 表示 scope 不足，`429` 表示配额耗尽，`503` 表示服务繁忙。

## Shared response envelope

| Field | Meaning |
| --- | --- |
| `request_id` | 单次 HTTP 请求的关联标识。 |
| `content_revision` | publication 内容快照标识。 |
| `knowledge_revision` | chunk、检索索引、embedding、Ontology binding、Graph 和引用阅读投影组成的知识快照标识。相同值表示响应来自同一知识事实集合。 |
| `ontology_revision` | Ontology 定义、节点和审校关系的结构版本；只出现在 Ontology 相关响应。 |
| `truncated` | 节点或关系是否因 limit 被截断；只出现在图结构响应。 |
| `degraded` | 检索是否从请求模式降级执行；只出现在检索和回答响应。 |
| `warnings` | 服务返回的降级或质量提示列表。 |
| `mode_requested` | 客户端请求的检索模式。 |
| `mode_executed` | 服务实际执行的检索模式。 |
| `took_ms` | 服务端请求耗时，单位毫秒。 |

这些字段描述响应来源、执行状态和完整性，不修改服务状态，也不承担 task management。

## Command response fields

### `query`

- `answer`：服务生成或抽取的回答。
- `citations[]`：回答引用。字段包括 `id`、`article_id`、`chunk_id`、`title`、`public_url`、`section_title` 和 `excerpt`。
- `retrieval`：检索执行摘要。字段包括 `mode_requested`、`mode_executed`、`candidate_chunks`、`context_chunks`、`graph_entities` 和 `graph_relationships`。
- 共享字段：`request_id`、`content_revision`、`knowledge_revision`、`degraded`、`warnings`。

### `search`

- `results[]`：候选 Section。字段包括 `article_id`、`chunk_id`、`section_id`、`title`、`public_url`、`section_title`、`heading_path`、`snippet`、`matched_by` 和 `scores`。
- `scores`：包含 `keyword_bm25`、`keyword_rank`、`semantic_distance`、`semantic_rank` 和 `fusion`。
- 共享字段：`request_id`、`content_revision`、`knowledge_revision`、`mode_requested`、`mode_executed`、`degraded`、`warnings`、`took_ms`。

### `retrieve`

- `query`：规范化后的查询文本。
- `articles[]`：文章级结果，字段包括 `article_id`、`title`、`public_url` 和 `sections`。
- `articles[].sections[]`：Section 原文与扩展上下文，字段包括 `section_id`、`section_title`、`chunk_id`、`content`、`start_line`、`end_line`、`matched_by`、`matched_chunk_ids`、`expanded_chunk_ids` 和 `scores`。
- 共享字段与 `search` 相同。

### `learning`

- `focus`：命中的焦点概念。
- `nodes[]`：焦点和直接邻域。字段包括 `id`、`domain_id`、`domain_label`、`kind`、`label`、`description`、`route`、`focus`、`explanation` 和 `articles`。
- `nodes[].articles[]`：挂载资源。字段包括 `article_id`、`title`、`public_url`、`brief`、`type` 和 publication 可用的 `binding_role`。
- `edges[]`：局部审校关系，字段包括 `source`、`target`、`relation` 和 `label`。
- 共享字段：`request_id`、`content_revision`、`knowledge_revision`、`ontology_revision`、`truncated`。

### `ontology`

- `nodes[]`：图节点。字段包括 `id`、`domain_id`、`domain_label`、`parent_id`、`kind`、`label`、`description`、`route`、`article_count` 和 `course_count`。
- `edges[]`：图关系，字段包括 `source`、`target` 和 `type`。
- 不带 `domain_id` 时返回稳定的跨领域导航骨架；带 `domain_id` 时返回该领域全部受审阅节点和域内关系。
- 共享字段：`request_id`、`content_revision`、`knowledge_revision`、`ontology_revision`、`truncated`。

## Knowledge organization

```text
Knowledge snapshot
├── domain
│   ├── meta-node                结构分组或导航层级
│   │   └── concept              具体知识概念
│   └── reviewed edge
│       ├── contains/member_of   层级归属
│       ├── prerequisite         有方向的前置关系
│       └── related              无前置含义的相关关系
└── resource
    ├── course
    └── publication
        └── section/chunk        citation 和原文定位
```

- domain 是顶层知识领域。
- meta-node 和 concept 都是 Ontology 节点；meta-node 提供稳定的组织尺度，concept 表示具体概念。
- course、Blog、论文和技术分析属于 resource，通过 binding 挂到概念，不作为 Ontology 节点。
- 全局 `ontology` 是跨领域 meta 导航骨架，不等于所有细粒度 concept 的并集。
- 指定 `domain_id` 的 `ontology` 是该领域的完整审校视图，可能包含尚无 resource 的节点。
- `learning` 是一个概念的局部投影：焦点、直接关系、解释和挂载资源。
- `search` 和 `retrieve` 是 publication/section 读取面；`query` 在该读取面上返回 answer 和 citation。
