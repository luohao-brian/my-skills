---
name: ai-oss-models
description: 追踪连续 7 天内 LLM/VLM、生图/视频、TTS/ASR、Decision、Music/音效及 VLA/机器人动作策略的开放模型，关联量化、低拒绝、蒸馏、本地部署及 ComfyUI 媒体工作流；另持续核验单卡本地训练组合。综合 Hugging Face 任务、热榜、模型卡和仓库变化生成中文报告。适用于开源模型周报、个人部署与开发选型及指定日期窗口追踪。
metadata: {"openclaw":{"skillKey":"ai-oss-models","emoji":"🧩","homepage":"https://github.com/luohao-brian/my-skills/tree/main/info-track/ai-oss-models","requires":{"bins":["python3"]}}}
---

# AI 开源模型观察

运行采集器生成候选 JSON，并按固定格式生成中文报告。

观察主线：

- 基础与专项模型：已登记模型精确查询；当前运行同时查询主要厂商 owner、HF 全局 Trending Top 500/最近更新 Top 1000、图像/视频/TTS/ASR/音频生成及 robotics 结构化任务池。先确认完整权重与输入输出，再记录窗口变化、评测、运行组件和模型依赖。已登记主模型即使仓库未更新，只要仍位于当前热榜前列，或本次采集到至少 3 个明确引用它的衍生仓且其中至少 1 个仍热门，也进入报告；正文说明当前关注证据，不写成新发布。
- 衍生与本地模型：查询 GGUF、MLX、quantized、on-device、merge、finetune、adapter、distilled 及低拒绝精确 tags；对每个入选模型沿 HF `base_model` 逐跳追溯，保存每跳 relation、source、证据和终止状态。`canonical_model` 是经路径验证的衍生线主模型，最远结构化祖先另记为 `root_model`；多父分叉、关系冲突或注册表声明不在路径上时不输出已确认的 `canonical_model`。区分可运行包、量化包、LoRA 和组件仓。最多 20 条，按发布者与衍生类型保持覆盖。
- 个人部署参考：最终入选模型记录完整组件、精度、官方或实测峰值显存、上下文或媒体生成规格；可用现有 GPU 型号作资源量级参考，不据此筛掉候选，也不查询驻留状态或编排部署。仓库大小不写成运行显存。
- 结构化决策：登记 NeoHorse-Jev、Kev、OpenJev 与 Laya；分别核对 `choice`、`score`、`noul` 原生输出、JEV 接口字段、语义正确率、概率校准与本地吞吐；兼容声明不等于协议或语义验收。
- 音频：文本音效、视频/视频+文本同步 Foley、长环境声、补绘/续写、完整歌曲、歌声转换和按谱歌声合成分别记录。只用精确 tag 或已核对注册表赋予细分任务；`text-to-audio`、`video-to-audio` 只表示输入输出方向。视频 Foley 记录时长、事件同步和意外人声/音乐等验证项。已登记的歌曲、音效、Foley、歌声转换模型即使本期无仓库更新，当前任务热榜、活跃衍生引用或足够明确的站内关注仍使其进入雷达；报告用音频具体任务分节，不混入语音 TTS/ASR。
- 媒体基础生态：基础与专项模型追踪 SAM 等分割模型的图片/视频输入与 mask 输出；ComfyUI 媒体工作流追踪“分割/姿态/运动/深度/人脸分析 → 角色动画/数字人/换脸/生成 → 编辑/增强/音频”的连接。对每个节点写清输入、输出、所需上游素材和下一环节。ComfyUI 候选必须有精确运行时证据，能力来自结构化任务、精确 tag、当前 model card 或打包仓明确链接的一层上游 model card；通用文生图、通用图片编辑和无媒体链路证据的文生视频不进入本节。
- 具身 VLA：将 HF `robotics` 作为候选召回，不直接等同于 VLA。按模型卡区分视觉+语言+机器人状态→动作的 VLA 策略、联合预测动作与未来画面的 world-action 模型、仅供适配的基座及面向具体本体的完整策略。已登记的 VLA 主模型与其他任务采用相同的持续关注规则：仓库本期更新、当前任务热榜靠前，或本次采集到较多直接衍生且至少一个仍热门时进入主模型栏目；已证实的热门衍生进入衍生栏目。当前热度只在当前运行呈现，不写成新发布。记录真实输入输出、权重组件、机器人本体和开源运行入口；仅有 `robotics` 标签而缺动作输出证据时不写成 VLA。
- 生态架构：按 [references/ecosystem-architecture.json](references/ecosystem-architecture.json) 中的 LLM/VLM、图像/视频、TTS/ASR、Decision、Music、具身 VLA 六条主干查询。每条候选保存 `ecosystem_paths` 的精确任务/tag/注册表证据；架构用于召回与分类，不在报告中画跨模型生态图。SAM、Avatar、换脸、音效和超分是相关主干中的环节。
- 画质规格：图像/视频超分、修复去模糊、补帧和帧率提升单独观察；只按模型卡或结构化字段记录分辨率、倍率、帧率和画质评测，不从仓库名推断。
- 低拒绝衍生：从 HF 精确 tags 召回并标注 uncensored、abliterated、heretic 和 decensored 模型；只作为发布者定位信号，不作为质量或安全结论。
- 本地开发入口：按 [references/development-baselines.json](references/development-baselines.json) 的 `local_experiments` 持续核验小模型 SFT/离线 response 蒸馏/RLVR，以及视频和音频生成 LoRA 的模型、数据集与训练组件。文本数据核指定 split 与必需列；视频核训练 manifest 和实际素材路径；音频核音频特征与文本列。报告给出精确组合、数据转换、监督信号、工具作用和资源证据；工具仓库的日常更新留在审计 JSON。L20/5090 只是资源量级参考，不能仅凭 GPU 型号或权重文件大小宣称训练已可运行。完整预训练语料和大规模复现工程不进入此雷达。

具体模型和发布者只作为可维护注册表与回归样本，不得在算法中为单一案例设置专属名额、名称匹配或阈值。

读取规则：

- 读取候选 JSON 前读取 [references/output-schema.md](references/output-schema.md)。
- 核对候选阶段标记时读取 [references/ecosystem-architecture.json](references/ecosystem-architecture.json)；不要据此推断跨模型上下游。
- 解释本地训练方法、工具和数据集时读取 [references/development-baselines.json](references/development-baselines.json)。
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
3. 成稿以 `--report-output` 的紧凑 JSON 为候选输入，不读取 `--output` 的完整审计 JSON；解释 workflow 的用途和输入时可核对该仓模型卡、指南或 workflow 原文件。正文依次列主要厂商的主模型更新、衍生与独立专项模型、媒体与 ComfyUI 生态、本地训练候选；前三层按 LLM/VLM、图像/视频、TTS/ASR、Decision、音乐与歌曲生成、文本音效、视频 Foley、多模态音频、歌声转换等实际任务分类。“基础与专项”“热门衍生与本地”“重点新发现”“ComfyUI”仅作采集入口标记。逐条覆盖 `groups` 的全部正式模型候选，每条只出现一次。使用 `#### 序号. 模型名称` 加字段列表的原生格式，不改写为表格；写可确认且有阅读价值的基座模型、结构化输入输出、HF 参数量、当前仓主权重或组件文件大小、TrendingScore/下载/点赞。第四层只用 `groups.development.opportunities`，按 SFT、离线蒸馏、RLVR、Decision 类型化 SFT、Decision 可验证奖励、文生视频 LoRA、视频 IC-LoRA、音效 LoRA、音乐 LoRA 写精确模型与数据集组合、必需列或 manifest、训练前转换、监督/奖励信号、各工具组件职责及资源验证状态，不把普通工具提交当训练进展。Decision 数据集要分开标明训练 split、独立 test、choice/noul/score 标签或答案分布；只有确定标签且能程序核对时才写 RLVR。逐跳 `canonical_model_trace`、`root_model`、原声明和血缘冲突留在审计 JSON；正文只显示可确认且有阅读价值的基座链接，无基座时省略该字段。不生成模型生态图或按能力模板串接工作流。ComfyUI 只列候选自己的能力证据、组件及可核实的 workflow 用途、必需输入与链接；只有文件名时省略，完整路径清单留候选 JSON。
   VLA/机器人动作候选按证据归入第一层“VLA 与机器人动作策略”或第二层“VLA 衍生与本地模型”；已登记参考模型参加主模型的热榜和直接衍生引用筛选，不单列静态参考栏目。只按模型卡写动作适配基座或完整本体策略。热榜观察、衍生引用和本期发布/更新分别标注；历史 `--date` 不使用当前热榜和趋势。
4. 只有调用方明确提供 `--state-dir` 或 `AI_OSS_MODELS_STATE_DIR` 时才读写趋势快照；快照覆盖 HF 全局与任务内排名、TrendingScore、下载和点赞。目录由调用方负责选择和管理。
5. 模型方向、规模、架构与论文只使用候选中的结构化字段，方向不按模型名推断；评测必须同时保留 model card 的测试条件和限制；解释“仓库更新”时只使用本窗口 `change_evidence`，把 model card 限定为当前状态背景。
6. `--stats` 会输出各采集阶段耗时和紧凑成稿输入字节数；性能排查以 `timings_seconds` 为准，不通过重复运行采集命令猜测进度。
7. 覆盖诊断和热力图只读取 `--output` 的完整审计 JSON 中的 `diagnostics` 与 `groups`；`--report-output` 仍只用于生成正式报告正文。
8. 代理参数只作用于本次采集进程，不持久化、不写入候选或报告 JSON，也不读取 Agent 专属代理配置；`localhost`、`127.0.0.1` 和 `::1` 始终绕过代理。需要代理时必须在唯一一次采集调用中显式传入。

## 时间窗口

- 不传 `--date`：采集截至今天的最近 7 天，并纳入仍位于 HF 热门池的重点原模型、衍生与本地部署模型；提供状态目录时使用跨日趋势快照计算排名和热度变化。当前观察与本期发布/更新在输出事件中分开。
- 传 `--date YYYY-MM-DD`：采集该日起连续 7 天，只使用该窗口内的发布或更新时间，不使用当前热门状态和本地趋势快照。
- 单次窗口固定为 7 天；不因候选不足改变窗口。

## 认证

- Hugging Face 公共仓库采集不要求 token。
- 读取 gated model card 前，用户必须先在对应 Hugging Face 页面登录并同意访问条款，再由运行环境通过 `HF_TOKEN` 提供该账号的只读 token。
- 不把 token 写入命令、候选 JSON、报告或仓库文件；`HUGGING_FACE_HUB_TOKEN` 仅作为兼容变量。
