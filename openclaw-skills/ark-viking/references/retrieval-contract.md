# 文章检索合同

`retrieve` 返回文章级结果：

```json
{
  "schema": "openviking.article-retrieval/v1",
  "query": "用户查询",
  "articles": [
    {
      "relevance": 0.82,
      "article_title": "文章标题",
      "article_url": "https://blog.example.com/auto/article.html",
      "sections": [
        {
          "relevance": 0.76,
          "section_title": "相关章节标题",
          "content": "相关章节正文"
        }
      ]
    }
  ]
}
```

## 字段

- `articles[].relevance`：文章候选中最高的 OpenViking 命中分数。数值越大，相关度越高。
- `articles[].article_title`：文章资源根目录中的文章标题；无法取得时使用源文件名。
- `articles[].article_url`：由源 Markdown 路径确定性映射的 Rspress 原文链接。
- `articles[].sections`：该文章内与查询相关的正文章节，按相关度降序排列。
- `sections[].relevance`：该章节的 OpenViking 命中分数。
- `sections[].section_title`：从章节正文标题提取的章节标题。
- `sections[].content`：从该章节 URI 实际读取的正文，受 `--max-chars` 限制。

`--limit` 限制不同文章的数量。`--sections-per-article` 限制每篇文章的章节数量。

## 组装规则

1. 按源 Markdown 路径聚合命中，同一文章只返回一次。
2. 文章相关度取该文章候选命中的最高分。
3. 在文章资源根目录内再次检索章节。
4. 只把可读取的 `.md` 或 `.mdx` 子资源作为章节。
5. 排除 `.abstract.md` 和 `.overview.md`。
6. 文章标题、文章链接和章节必须来自同一源文章。
7. 没有可读取相关章节的文章不进入结果。

## 原文链接

仅映射以下范围：

```text
viking://resources/codex-rspress-admin/public/articles/<source-path>.(md|mdx)/...
->
${ARK_VIKING_RSPRESS_PUBLIC_BASE_URL}/auto/<source-path>.html
```

从 `articles/` 后读取源文件路径，在第一个以 `.md` 或 `.mdx` 结尾的路径段停止。忽略其后的 OpenViking 生成目录和分段文件。无法提取源路径时不生成链接。

## 展示规则

每篇文章按以下顺序展示：

1. 相关度
2. 文章标题和链接
3. 相关章节标题、章节相关度和正文内容

只根据 `sections[].content` 回答。字段为空时明确说明，不补写内容。默认不展示内部 URI。
