# AI 新闻候选审阅

你只基于候选 JSON 中的 `title`、`summary_basis`、`source_url`、`published_at` 补全字段，不新增事实，不扩展来源。

对每条 `needs_model_review=true` 的候选：

1. 判断是否入稿；不入稿时写入 `excluded` 并说明 reason。
2. 从固定分类中选择一个 `category`。
3. 写一条中文 `zh_summary`，只概括候选已有事实。
4. 将可入稿候选的 `needs_model_review` 改为 `false`。

固定分类：

- 模型 / 研究
- Agent / 开发者工具
- 技术博客 / 工程实践
- 产品 / 应用
- 商业 / 融资
- 安全 / 治理
