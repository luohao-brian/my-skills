---
name: ai-oss-models
description: 追踪连续 7 天内主要 AI 厂商的开放模型更新、可复现训练链路与技术数据迭代、热门本地部署及 uncensored/abliterated/heretic 等低拒绝模型信号，以及新出现的社区热点；覆盖 LLM/VLM、图像与视频生成、TTS/语音，并单独追踪 ComfyUI 图片之后的视频动画、音频驱动、特效与编辑链路。综合 Hugging Face 与已登记 GitHub 工程生成旗舰模型、开发过程、数据集、本地部署和重点发现报告。适用于开源模型生态周报、ComfyUI 视频工作流选型、低拒绝模型观察、复现研究、部署选型和指定日期窗口追踪。
metadata: {"openclaw":{"skillKey":"ai-oss-models","emoji":"🧩","homepage":"https://github.com/luohao-brian/my-skills/tree/main/info-track/ai-oss-models","requires":{"bins":["python3","gh"]}}}
---

# AI 开源模型观察

运行采集器生成候选 JSON，并按固定格式生成中文报告。

观察主线：

- 主要厂商：新基础模型、后训练模型和多模态/专项模型。
- 生成式媒体与语音：使用 HF 官方结构化任务池及任务内 Trending 排名召回 VLM、图像生成/编辑、视频生成、TTS 和 ASR；对最终入选模型补充组件、运行时、NFE/加速、精度、仓库占用、offload 和模型依赖链。
- ComfyUI 后图像媒体雷达独立于任何下游验证平台或模型注册表，从 ComfyUI Trending、最近更新、结构化媒体任务和全局池发现高热、活动密度高或跨日增长明显的新路线，并保持角色动画、音频驱动、视频编辑/特效等能力覆盖。候选必须有 ComfyUI 证据；纯文生图、纯图片编辑和无后图像能力证据的纯文生视频不进入本节。最终能力必须来自结构化任务、精确 tag、当前 model card 或打包仓明确链接的一层上游 model card，不从模型名推断。
- 开放复现：预训练与后训练数据、训练 recipe/config、阶段 checkpoint、评测和部署交付件。
- 本地生态：GGUF、MLX、量化、Ollama、vLLM 与 on-device 方案。
- 低拒绝衍生：从 HF 精确 tags 召回并标注 uncensored、abliterated、heretic 和 decensored 模型；只作为发布者定位信号，不作为质量或安全结论。
- 开发过程：数据集、数据管线、SFT/Preference/RL 资产、训练代码和评测方法。

具体模型和发布者只作为可维护注册表与回归样本，不得在算法中为单一案例设置专属名额、名称匹配或阈值。

读取规则：

- 读取候选 JSON 前读取 [references/output-schema.md](references/output-schema.md)。
- 生成报告前读取 [references/format.md](references/format.md)。
- 需要确认分类字段时读取 [references/sources.md](references/sources.md)。
- 分析召回覆盖或生成热力图时读取 [references/heatmap-diagnostics.md](references/heatmap-diagnostics.md)。

```bash
python3 {baseDir}/scripts/open_source_updates.py --output oss-candidates.json --report-output oss-report-input.json --stats
```

目标网络需要代理时，在同一次采集命令中显式传入：

```bash
python3 {baseDir}/scripts/open_source_updates.py \
  --http-proxy <proxy-url> \
  --https-proxy <proxy-url> \
  --no-proxy <comma-separated-hosts> \
  --output oss-candidates.json \
  --report-output oss-report-input.json \
  --stats
```

调用合同：

1. 仅使用可选的 `--date YYYY-MM-DD`、`--output`、`--report-output`、`--state-dir`、`--stats`、`--http-proxy`、`--https-proxy` 和 `--no-proxy`；未指定日期时不传 `--date`。
2. 候选 JSON 遵循 [references/output-schema.md](references/output-schema.md)，最终报告遵循 [references/format.md](references/format.md)。
3. 成稿时只读取 `--report-output` 生成的紧凑 JSON，不读取 `--output` 的完整审计 JSON；报告必须覆盖 `groups` 中的全部候选，只从 `groups.notable_discoveries` 生成“本周重点新发现”，从兼容字段 `groups.media_customization` 生成独立的“ComfyUI 后图像媒体雷达”。媒体条目只按候选自身的能力证据、热度、活动密度、工作流交付和部署画像解释，不读取或推断下游系统的覆盖、缺口和验证状态。每个条目都必须面向不熟悉模型的读者解释基础场景、输入输出、主要用法，以及 ComfyUI 上游输入准备、核心工作流和下游补帧/增强/音频合成/编码连接方式；仓库自带 workflow 与能力模板建议必须明确区分。
4. 只有调用方明确提供 `--state-dir` 或 `AI_OSS_MODELS_STATE_DIR` 时才读写趋势快照；快照覆盖 HF 全局与任务内排名、TrendingScore、下载、点赞，以及已登记 GitHub 工程的 star/fork。目录由调用方负责选择和管理。
5. 模型方向、规模、架构与论文只使用候选中的结构化字段，方向不按模型名推断；评测必须同时保留 model card 的测试条件和限制；解释“仓库更新”时只使用本窗口 `change_evidence`，把 model/dataset card 限定为当前状态背景。
6. `--stats` 会输出各采集阶段耗时和紧凑成稿输入字节数；性能排查以 `timings_seconds` 为准，不通过重复运行采集命令猜测进度。
7. 覆盖诊断和热力图只读取 `--output` 的完整审计 JSON 中的 `diagnostics` 与 `groups`；`--report-output` 仍只用于生成正式报告正文。
8. 代理参数只作用于本次采集进程及其 `gh api` 子进程，不持久化、不写入候选或报告 JSON，也不读取 Agent 专属代理配置；`localhost`、`127.0.0.1` 和 `::1` 始终绕过代理。需要代理时必须在唯一一次采集调用中显式传入。

## 时间窗口

- 不传 `--date`：采集截至今天的最近 7 天，并纳入仍位于 HF 全局热门池的重点衍生与本地部署模型；提供状态目录时使用趋势快照计算排名和热度变化。
- 传 `--date YYYY-MM-DD`：采集该日起连续 7 天，只使用该窗口内的发布或更新时间，不使用当前热门状态和本地趋势快照。
- 单次窗口固定为 7 天；不因候选不足改变窗口。

## 认证

- Hugging Face 公共仓库采集不要求 token。
- 读取 gated model card 前，用户必须先在对应 Hugging Face 页面登录并同意访问条款，再由运行环境通过 `HF_TOKEN` 提供该账号的只读 token。
- 不把 token 写入命令、候选 JSON、报告或仓库文件；`HUGGING_FACE_HUB_TOKEN` 仅作为兼容变量。
- 已登记 GitHub 工程的提交、star 和 fork 使用已认证的 `gh api` 采集；运行前通过 `gh auth login` 登录，不把 GitHub token 写入命令、候选 JSON、报告或仓库文件。
