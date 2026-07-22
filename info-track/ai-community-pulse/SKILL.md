---
name: ai-community-pulse
description: 采集并综合 AI 模型与评测、AI Agent 与开发工具、AI 系统与本地推理、芯片与算力四类社区热点，使用固定 X 账号、Reddit 子版、Bluesky Custom Feed、HN/Lobsters/LessWrong 固定入口、中文社区频道和 Polymarket 市场生成中文日报。适用于社区与生态热点补充、每日 AI 社区简报、固定频道巡检；不采集官方公告、新闻媒体、GitHub、论文或模型仓库更新。
metadata: {"openclaw":{"skillKey":"ai-community-pulse","emoji":"🌐","homepage":"https://github.com/luohao-brian/my-skills/tree/main/info-track/ai-community-pulse","requires":{"bins":["python3","opencli"]},"install":[{"id":"opencli","kind":"node","package":"@jackwener/opencli","bins":["opencli"],"label":"Install OpenCLI"}]}}
---

# AI Community Pulse

## 执行目标

生成以具体社区话题为主体的中文日报。覆盖四类主题：模型与评测、Agent 与开发工具、AI 系统与本地推理、芯片与算力。只使用 [references/channels.json](references/channels.json) 中的固定频道；平台搜索只能作为人工补充，不能替代固定频道。

本 skill 补充社区讨论、真实使用、产品扩散、工程反馈和预测市场信号。排除官方公告、新闻媒体、GitHub、论文、Hugging Face 模型与数据集；这些内容由其他 info-track skill 负责。

## 执行步骤

1. 读取 [references/channels.json](references/channels.json)，确认本轮固定频道和启用状态。
2. 采集最近 72 小时的公开与登录态来源：

```bash
python3 {baseDir}/scripts/community_pulse.py collect \
  --hours 72 \
  --output /absolute/path/community-pulse.json
```

3. 检查 JSON 中的 `sources`。`ok: false` 的登录态来源必须如实保留；不得用泛搜索结果伪装为固定频道数据。
4. 从 `candidates` 中合并同一事件或话题的重复项。保留相互独立的社区链接；不要做跨平台互动量比较、复杂打分或趋势状态推断。
5. 按 [references/brief-format.md](references/brief-format.md) 生成报告：

```bash
python3 {baseDir}/scripts/community_pulse.py render \
  --input /absolute/path/community-pulse.json \
  --output /absolute/path/community-pulse.md
```

也可以一步完成：

```bash
python3 {baseDir}/scripts/community_pulse.py run \
  --hours 72 \
  --json-output /absolute/path/community-pulse.json \
  --report-output /absolute/path/community-pulse.md
```

## 采集边界

- X、Reddit、知乎、Linux.do、B站依赖 Chrome 登录态与 OpenCLI Browser Bridge。桥接不可用时继续采集公开来源，并在来源状态中记录失败原因。
- HN、Bluesky、V2EX、Lobsters、LessWrong、Product Hunt 和 Polymarket 使用公开读取能力，不要求登录。
- X 只采固定账号；Reddit 只采固定 subreddit；Bluesky 只采固定 Custom Feed；V2EX 只采固定节点；不得用通用 Web 搜索代替。
- Polymarket 只表达市场问题、当前概率和市场链接，标题加“预测市场”；概率不能写成事实。
- 只执行只读命令。禁止发帖、评论、点赞、关注、订阅或修改账号状态。

## 时间窗口

默认窗口为运行时刻向前连续 72 小时。固定日榜或周榜没有可用发布时间时可以保留，但必须在候选中标记 `date: null`；不得伪造发布时间。

## 输出合同

采集 JSON 必须符合 [references/output-schema.md](references/output-schema.md)。最终 Markdown 必须符合 [references/brief-format.md](references/brief-format.md)，包含四个固定主题章节和“采集状态”。没有候选的主题保留章节并写“本期无入选话题”。
