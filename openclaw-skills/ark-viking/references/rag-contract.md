# RAG context contract

`retrieve` 返回：

```json
{
  "schema": "openviking.rag-context/v1",
  "query": "...",
  "target_uri": "viking://resources/.../",
  "contexts": [
    {
      "uri": "viking://resources/.../article.md",
      "source_path": "article.md",
      "public_url": "https://blog.example.com/auto/article.html",
      "title": "文章标题",
      "score": 0.82,
      "abstract": "...",
      "content": "..."
    }
  ]
}
```

使用规则：

1. 只使用 `contexts` 中实际返回的内容回答。
2. 合并多条结果时内部保留各自 URI，避免把不同来源混成一条无来源结论。
3. `content` 会受 `--max-chars` 限制；若关键段落被截断，对目标 URI 再执行 `read`。
4. 图片资源可能出现在结果中；若响应只含图片元数据或摘要，不声称已经读取到图片细节。
5. `contexts` 为空时说明知识库未召回到依据，再决定是否使用其他已授权来源。

## Rspress 原文映射

受管文章 URI 与 Rspress 页面保持以下确定性规则：

```text
viking://resources/codex-rspress-admin/public/articles/<source-relative-path>.(md|mdx)/<generated-descendant>
<->
${ARK_VIKING_RSPRESS_PUBLIC_BASE_URL}/auto/<source-relative-path>.html
```

映射步骤：

1. 只接受 `articles/` 范围内的 URI。
2. 从 `articles/` 后开始读取路径，遇到第一个以 `.md` 或 `.mdx` 结尾的 segment 时结束；这部分是源 Markdown 相对路径。
3. 对路径 segment 做一次 URL decode，只移除源文件末尾的 `.md` 或 `.mdx`。
4. 在前面添加 `/auto/`，在末尾添加 `.html`，并拼接 `ARK_VIKING_RSPRESS_PUBLIC_BASE_URL`。
5. 忽略源文件 segment 后由 OpenViking 生成的目录、分段文件、`.abstract.md` 和 `.overview.md`。

不得根据标题、摘要、召回文本或 OpenViking 生成的分段文件名构造 URL。无法提取源 Markdown 路径时，`source_path` 和 `public_url` 为 `null`。

从页面 URL 反查时，移除配置的 public base URL 和 `/auto/`，把末尾 `.html` 还原为源路径 stem，再在知识库中校验 `.md` 与 `.mdx` 候选；只接受唯一存在的候选。URL 本身不携带 Markdown 扩展名，未经知识库校验不得臆测扩展名。

## 用户输出

默认按以下顺序展示，不直接输出内部 Viking URI：

1. 标题
2. 摘要
3. 与问题相关的正文内容
4. Rspress 原文链接 `public_url`
5. 相关度（有值时）

只有用户明确要求内部资源位置或诊断检索链路时才展示 `uri`。

## Agent 使用链路

`retrieve` 是面向回答场景的单一入口：

```text
query
  -> POST /api/v1/search/find 做语义匹配
  -> 对每个命中 URI 调用 content/read
  -> 返回 title + abstract + content + public_url + score
  -> Agent 使用 content 回答，并把 public_url 作为该条内容的原文链接
```

字段必须按同一个 context 配对，禁止把 A 的 `content` 与 B 的 `public_url` 组合。一个来源被 OpenViking 拆成多个命中时，可以合并内容，但只保留同一 `source_path` 对应的原文链接。
