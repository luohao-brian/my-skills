---
name: ai-oss-models
description: 追踪连续 7 天内主要 AI 厂商的开放模型更新、可复现训练链路与技术数据迭代、热门本地部署模型和部署方案，以及新出现的社区热点；综合 Hugging Face 与已登记 GitHub 工程仓库生成旗舰模型、开发过程、数据集、本地部署和重点发现报告。适用于开源模型生态周报、复现研究、部署选型和指定日期窗口追踪。
metadata: {"openclaw":{"skillKey":"ai-oss-models","emoji":"🧩","homepage":"https://github.com/luohao-brian/my-skills/tree/main/info-track/ai-oss-models","requires":{"bins":["python3"]}}}
---

# AI 开源模型观察

运行采集器生成候选 JSON，并按固定格式生成中文报告。

观察主线：

- 主要厂商：新基础模型、后训练模型和多模态/专项模型。
- 开放复现：预训练与后训练数据、训练 recipe/config、阶段 checkpoint、评测和部署交付件。
- 本地生态：GGUF、MLX、量化、Ollama、vLLM 与 on-device 方案。
- 开发过程：数据集、数据管线、SFT/Preference/RL 资产、训练代码和评测方法。

具体模型和发布者只作为可维护注册表与回归样本，不得在算法中为单一案例设置专属名额、名称匹配或阈值。

读取规则：

- 读取候选 JSON 前读取 [references/output-schema.md](references/output-schema.md)。
- 生成报告前读取 [references/format.md](references/format.md)。
- 需要确认分类字段时读取 [references/sources.md](references/sources.md)。

```bash
python3 {baseDir}/scripts/open_source_updates.py --output oss-candidates.json --stats
```

调用合同：

1. 仅使用可选的 `--date YYYY-MM-DD`、`--output` 和 `--stats`；未指定日期时不传 `--date`。
2. 候选 JSON 遵循 [references/output-schema.md](references/output-schema.md)，最终报告遵循 [references/format.md](references/format.md)。
3. 报告必须覆盖 `groups` 中的全部候选；只从 `groups.notable_discoveries` 生成“本周重点新发现”，不直接展开顶层 `discoveries`。

## 时间窗口

- 不传 `--date`：采集截至今天的最近 7 天，并纳入仍位于 HF 全局热门池的重点衍生与本地部署模型；本地趋势快照用于计算排名和热度变化。
- 传 `--date YYYY-MM-DD`：采集该日起连续 7 天，只使用该窗口内的发布或更新时间，不使用当前热门状态和本地趋势快照。
- 单次窗口固定为 7 天；不因候选不足改变窗口。

## 执行预算

- 采集器只为最终入选的旗舰、本地热门、重点数据集和重点新发现并发读取 model card，不为全部发现逐条抓取详情。
- 外部调度器应为完整采集和报告生成预留至少 1500 秒；采集器已复用 owner 查询结果，减少精确仓库请求。

## 可选认证

- 公共仓库采集不要求 token。
- 读取 gated model card 前，用户必须先在对应 Hugging Face 页面登录并同意访问条款，再由运行环境通过 `HF_TOKEN` 提供该账号的只读 token。
- 不把 token 写入命令、候选 JSON、报告或仓库文件；`HUGGING_FACE_HUB_TOKEN` 仅作为兼容变量。
- GitHub 匿名 API 受限流影响时可通过 `GITHUB_TOKEN` 提供只读 token，`GH_TOKEN` 仅作为兼容变量；没有 token 时采集器回退到公开 commits Atom feed。
