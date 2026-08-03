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
python3 {baseDir}/scripts/open_source_updates.py --output oss-candidates.json --report-output oss-report-input.json --stats
```

调用合同：

1. 仅使用可选的 `--date YYYY-MM-DD`、`--output`、`--report-output`、`--state-dir` 和 `--stats`；未指定日期时不传 `--date`。
2. 候选 JSON 遵循 [references/output-schema.md](references/output-schema.md)，最终报告遵循 [references/format.md](references/format.md)。
3. 成稿时只读取 `--report-output` 生成的紧凑 JSON，不读取 `--output` 的完整审计 JSON；报告必须覆盖 `groups` 中的全部候选，只从 `groups.notable_discoveries` 生成“本周重点新发现”。
4. 只有调用方明确提供 `--state-dir` 或 `AI_OSS_MODELS_STATE_DIR` 时才读写趋势快照；目录由调用方负责选择和管理。
5. 模型方向、规模、架构与论文只使用候选中的结构化字段，方向不按模型名推断；评测必须同时保留 model card 的测试条件和限制；解释“仓库更新”时只使用本窗口 `change_evidence`，把 model/dataset card 限定为当前状态背景。
6. `--stats` 会输出各采集阶段耗时和紧凑成稿输入字节数；性能排查以 `timings_seconds` 为准，不通过重复运行采集命令猜测进度。

## 时间窗口

- 不传 `--date`：采集截至今天的最近 7 天，并纳入仍位于 HF 全局热门池的重点衍生与本地部署模型；提供状态目录时使用趋势快照计算排名和热度变化。
- 传 `--date YYYY-MM-DD`：采集该日起连续 7 天，只使用该窗口内的发布或更新时间，不使用当前热门状态和本地趋势快照。
- 单次窗口固定为 7 天；不因候选不足改变窗口。

## 可选认证

- 公共仓库采集不要求 token。
- 读取 gated model card 前，用户必须先在对应 Hugging Face 页面登录并同意访问条款，再由运行环境通过 `HF_TOKEN` 提供该账号的只读 token。
- 不把 token 写入命令、候选 JSON、报告或仓库文件；`HUGGING_FACE_HUB_TOKEN` 仅作为兼容变量。
- GitHub 匿名 API 受限流影响时可通过 `GITHUB_TOKEN` 提供只读 token，`GH_TOKEN` 仅作为兼容变量。
