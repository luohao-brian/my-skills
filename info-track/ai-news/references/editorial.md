# 事件审核与成稿

`editorial.py prepare` 把 `collect` 的候选写入 `events.json`。按同一原文链接、规范化后相同的标题合并；两个聚合来源若共享原文链接且中英文标题有至少两个相同的具体英文锚点，也合并。聚合日报共享落地页不能单凭 URL 合并。`group_links` 记录每个合并对及原因。`review_priority` 只表示来源结构，不能当作新闻价值或事实可信度。

## 审核顺序

1. 阅读 `sources` 的运行状态。失败或零命中与“没有新闻”分开报告。
2. 检查 `group_links`；误并时拆开事件并保留来源。检查相似但未自动合并的跨语言标题及同一发布的不同报道；确认后合并成员。一个事件只刊载一次，不同的后续进展可分别刊载。
3. 默认保留去重后的事件；与 AI 无关、明显误采或无有效内容的事件可填 `review.decision=reject`。不要把来源篇数、AIHOT 的精选结果或来源角色当成新闻价值或事实可信度。材料不足时保持 `pending`，不补全缺失事实。
4. 对 `select` 事件核对原文，填写 `category`、中文 `title_zh`、中文 `summary_zh`、`verified_url`，并建议填写 `evidence_note` 记录核对到的事实或冲突。五个常用栏目之外，可用新的小写 `category` 键并填写 `category_label` 扩展栏目。`verified_url` 必须是事件成员的原文或条目链接。先写已确认动作及阶段，再写原文支持的细节；保留“拟、称、测试、已上线”等区别。摘要不能加入来源未支持的数字、效果或因果。
5. AIHOT 是聚合来源：保留其 `url` 条目链接、`original_url` 原文链接与 `original_source`。其条目和它转述的原文是同一条信息链，不能算两份独立佐证。优先核对 `original_url`；只核对 AIHOT 条目时，在摘要中将事实限定为 AIHOT 的转述。
6. 运行 `editorial.py summary-queue --input events.json --limit 25 --out summary-queue.json`。队列按事件分批给出采集文本和来源链接，相同原文链接只保留内容较完整的一份；`complete_excerpt` 仅供定位，不能直接当成成稿。先从已采集文本提炼一句，文本截断或缺少关键结果时再打开原文。同一事件只写一次摘要，不重复读取每个转载页。填写 `review.display_summary` 和对应的 `review.display_summary_source_url`；后者必须是该事件成员的链接。每批写回事件 JSON 后重跑队列，直到 `total` 为零。然后运行 `editorial.py render --all-events` 输出完整的一页简报：每个动态栏目只出现一次，栏目内中文条目靠前，组内全部来源链接保留。标题暂分到“其他动态”的事件须核对内容，填写现有 `review.category`，或填写新键和 `category_label` 扩展栏目；未归类时成稿报出事件 ID。若需要只发布逐项核验的简报，完成所有事件审核后运行不带 `--all-events` 的严格 `render`；仍有 `pending` 或入选事件缺核验字段时命令失败。

每条摘要以“主体 + 动作 + 关键结果或限制”为核心，只留一句；避免只重复标题、只写背景、堆数字或引用来源的导语。摘要在输出时保留来源支持的完整短句：含中文最多 100 字符，其他最多 180 字符，不裁切句子。`summary-queue` 依据当前事件数据生成，不使用固定标题或事件 ID；同一事件的多个来源一起提供给 Agent，避免重复读页。来源摘要被截断、含元数据或缺少关键结果时再核对原文。无法核对时停止完整页渲染并报告事件 ID，不生成空摘要。`display_summary` 只是展示文案，不表示原文已逐项核验。来源标题过短、缺少项目名时，核对来源后填写 `review.display_title`。使用“报道称”等归属词保留消息状态。

`render --allow-partial` 只用于输出已核验事件样例，显示尚未审核的事件数。

## 事件结构

每个 `events[]` 包含 `event_id`、`members[]`、`representative_article_id`、`review_priority` 和 `review`。`members[]` 保留每条来源候选及其 `article_id`。`review` 的默认值如下：

```json
{"decision":"pending","category":"","title_zh":"","summary_zh":"","verified_url":""}
```

`category` 的常用值是 `model_research`、`agent_tools`、`products`、`business`、`safety_governance`。新栏目填写小写键和 `category_label`。未核验候选可以不填栏目，成稿器按标题暂分。审核时可以修正事件成员，但同一原始候选不得放进两个事件。

对于确认相同的两个事件，写 `pairs.json`：`[["e_...", "e_..."]]`，然后运行 `python3 {baseDir}/scripts/editorial.py merge --input events.json --pairs pairs.json --out merged-events.json`。合并记录写入 `group_links`，必须在填写审核决定前运行。

AIHOT 的公开 API 允许个人非商业、公益非商业和组织内部使用；对外商业产品或公开镜像须按其[公开使用规则](https://aihot.news/terms)取得授权。保留 API 返回的 AIHOT 条目链接和第三方原文归属。
