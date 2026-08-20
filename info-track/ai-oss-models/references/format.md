# 报告格式

按以下结构生成 Markdown 报告。省略没有候选的分节和没有值的可选字段。

```markdown
# AI 开源模型观察｜YYYY-MM-DD — YYYY-MM-DD

本期关注：旗舰模型 N 项、热门衍生与本地部署模型 N 项、可复现项目 N 项、热门或重点数据集 N 项、重点新发现 N 项。

## 一、重点旗舰模型

### LLM

#### 1. 模型名称

- 窗口信号：新发布 | 仓库更新
- 背景与用途：先用非专业读者能理解的一句话说明它是什么、主要输入输出和适合解决的问题；量化、LoRA、工作流或组件仓必须说明它是否能独立运行。
- 规模：HF 结构化字段提供的权重参数量。
- 架构：MoE / Diffusion 等结构化架构类型、config 中的架构类；model card 有明确架构说明时补充一句。
- 热度：TrendingScore N · 下载 N · 点赞 N；直接复用候选中已有的 HF 指标，字段缺失时才省略。
- 评测表现（模型卡报告）：概括评测条件、代表性基准、对照模型和结果；有局限说明时一并写出。
- 媒体部署：媒体模型有 `deployment_profile` 时，概括运行时、组件、精度、NFE/步数、加速方式和 offload；只写有证据的字段。
- 部署依赖：列出基础模型、VAE、编码器、vocoder、LoRA 等依赖链；不评估许可证。
- 占用：只有存在可确认的单次部署 bundle 时才写完整占用；未知或 `partial` 时整行省略，不展示“待确认”。
- 资料：[技术论文](https://arxiv.org/abs/...) · [HF Paper](https://huggingface.co/papers/...)。
- 发布摘要：新发布时，根据 model card 用 1–2 句概括当前能力、用途和主要交付件。
- 更新摘要：仅在提交证据包含模型权重、代码、工作流、数据或评测的实质变化时写；纯 `Update README`、文档、拼写、元数据或无信息量上传记录整行省略。
- 时间：YYYY-MM-DD
- 链接：[Hugging Face](https://huggingface.co/...)

其他模型角色（包括其他音频生成）使用相同字段。

## 二、热门衍生与本地部署模型

### 1. 模型名称

- 关注：当前 HF 热门或重点白名单。
- 背景与用途：说明它基于什么、解决什么问题、是完整模型还是量化包/LoRA/组件；不要假设读者知道原模型。
- 原模型：canonical model ID
- 衍生：Merge | Finetune | Adapter | Quantized
- 部署：GGUF | MLX | Ollama | Quantized | On-device
- 媒体部署：有 `deployment_profile` 时补充组件、运行时、精度、NFE/加速、offload 和部署依赖；仓库总量通常不展示，也不要把全部可选量化版本相加后称为运行占用。
- 对齐信号：Low-refusal · HF tags: Uncensored / Abliterated / Heretic / Decensored；仅表示发布者定位，不代表零拒绝、能力保持或安全质量。
- 规模：HF 结构化字段提供的参数量。
- 热度：TrendingScore N · 下载 N · 点赞 N；有趋势快照时可补充排名和相对上次的变化。历史运行省略。
- 窗口信号：新发布 | 仓库更新 | 当前热门
- 状态摘要：根据 model card 概括当前模型定位、用途或组成，不把当前状态写成本窗口变化。
- 评测表现（模型卡报告）：优先说明当前量化/衍生版本自身的评测设置与结果，以及相对原模型或同条件量化基线的保留率；没有同条件证据时不做跨模型比较。
- 更新摘要：仅写本窗口有用户价值的实质变化；纯 README/文档维护省略。
- 变体：注册表显式声明同一 `variant_group` 后折叠出的其他仓库；没有 `metadata.variants` 时省略。
- 时间：YYYY-MM-DD
- 链接：[Hugging Face](https://huggingface.co/...)

## 三、重点可复现项目

### 1. 项目名称

- 窗口信号：本窗口内新增或更新的交付件。
- 开放范围：完整链路 | 预训练 | 后训练 | 部分交付
- 更新摘要：只保留权重、训练代码、数据、评测或可复现流程的实质变化；若只有依赖、CI、文档等维护性变更，省略该交付件。本节若没有实质变化则整节省略。
- 工程关注：有已登记 GitHub 指标时写 star/fork；有趋势快照时补充相对上次的增量。不得把 star/fork 写成模型质量或技术升级。
- 时间：YYYY-MM-DD
- 链接：[Hugging Face](https://huggingface.co/...)

| 阶段 | 本期交付件 | 状态 | 更新摘要 |
| --- | --- | --- | --- |
| 数据 | 数据集或数据处理仓库 | 新增 / 更新 | 提交证据支持的变化 |
| 训练 | recipe、config 或训练代码 | 新增 / 更新 | 提交证据支持的变化 |
| 模型 | checkpoint 或 aligned model | 新增 / 更新 | 提交证据支持的变化 |
| 评测 | eval dataset、harness 或 results | 新增 / 更新 | 提交证据支持的变化 |
| 部署 | 部署交付件 | 新增 / 更新 | 提交证据支持的变化 |

## 四、热门或重点数据集

### 1. 数据集名称

- 关注：当前 HF 热门或重点白名单。
- 用途：预训练 | SFT | Preference | 蒸馏 | 评测
- 关联：相关模型或可复现项目。
- 规模：HF 明确提供的数据规模。
- 热度：TrendingScore N · 下载 N · 点赞 N
- 窗口信号：新发布 | 仓库更新
- 内容摘要：根据 dataset card 概括数据内容、用途和可用的精确规模。
- 更新摘要：仓库更新时，只在提交记录明确说明数据文件、结构、清洗或评测变化时写；只有 README、说明文档、元数据或无信息量上传记录时整行省略。
- 资料：[技术论文](https://arxiv.org/abs/...) · [HF Paper](https://huggingface.co/papers/...)。
- 时间：YYYY-MM-DD
- 链接：[Hugging Face](https://huggingface.co/datasets/...)

## 五、本周重点新发现

本节只展示 `groups.notable_discoveries`，模型与数据集合计 8–12 条；实际候选不足时按实展示。

### 模型

#### 1. 模型名称

- 方向：LLM | VLM | 图像生成 | 视频生成 | TTS | 音频生成 | 语音识别 | OCR | 翻译 | Embedding | Robotics | 待确认
- 背景与用途：用一句话解释模型是什么、主要任务和潜在使用场景；不展示内部注册表状态。
- 窗口信号：新发布 | 仓库更新
- 规模：HF 结构化字段提供的权重参数量。
- 架构：MoE / Diffusion 等结构化架构类型、config 中的架构类；model card 有明确架构说明时补充一句。
- 热度：TrendingScore N · 下载 N · 点赞 N；直接复用候选中已有的 HF 指标，字段缺失时才省略。
- 评测表现（模型卡报告）：概括评测条件、代表性基准、对照模型和结果；有局限说明时一并写出。
- 资料：[技术论文](https://arxiv.org/abs/...) · [HF Paper](https://huggingface.co/papers/...)。
- 为什么关注：根据 model card 用 1–2 句概括能力、用途和主要交付件。
- 更新摘要：仅仓库更新时，根据本窗口提交记录概括具体变化。
- 时间：YYYY-MM-DD
- 链接：[Hugging Face](https://huggingface.co/...)

### 技术数据与热门新数据集

#### 1. 数据集名称

- 背景与用途：说明数据内容、规模、训练/评测用途和关联模型；不要假设读者熟悉项目名，也不展示内部注册表状态。
- 热度：TrendingScore N · 下载 N · 点赞 N；未包含 `hot` 时可省略。
- 窗口信号：新发布 | 仓库更新
- 用途与内容：根据 dataset card 用 1–2 句概括任务、数据内容或规模。
- 更新摘要：仅仓库更新时，根据本窗口提交记录概括具体变化。
- 资料：[技术论文](https://arxiv.org/abs/...) · [HF Paper](https://huggingface.co/papers/...)。
- 时间：YYYY-MM-DD
- 链接：[Hugging Face](https://huggingface.co/datasets/...)

## 六、ComfyUI 后图像媒体雷达

本节只展示兼容字段 `groups.media_customization`，最多 8 条。它不重复通用图片生成/编辑模型，只回答“一张图、角色素材、音频或已有视频进入 ComfyUI 后，接下来怎样生成动作、对齐角色、驱动数字人或完成视频特效与编辑”。能力必须来自 HF 结构化任务/精确 tag 或最终入选模型的 model card 明确证据。

先用 2–4 句给出组合结论：本窗口高热与高活动集中在哪些能力路线、哪些仓库交付了可复用工作流或轻量化权重、哪些能力仍只有少量信号。不要把“进入热榜”写成“建议部署”或“建议替换现有模型”；是否进入验证由下游平台结合自身注册表和资源约束判断。

### 1. 模型名称

- 它是什么：先用非专家能理解的 1–2 句话说明模型形态、它解决的具体问题和不负责的环节；首次出现 I2V、S2V、motion transfer 等缩写时展开中文含义。
- 关注信号：复述候选自身的高 Trending、近期仓库活动、下载/点赞速度或跨日增长；没有活动密度信号时写清它是能力覆盖候选，不补猜系统价值。
- 基础场景与用法：给出 2–3 个贴近短剧、数字人、抖音/TikTok 视频的场景，并明确主要输入、输出和关键控制量，例如人物参考图、驱动视频、音频、首尾帧、mask 或提示词。不要只写抽象能力标签。
- ComfyUI 上下游：按“上游素材/预处理 → 本模型核心节点或 workflow → 下游补帧、修复/放大、调色、音频混流和编码”说明连接方式。优先引用 `comfyui_integration`、`deployment_profile.dependencies`、组件和仓库 workflow；若 `workflow_status=recommended-topology-not-validated-workflow`，必须写成“建议编排”，不能冒充已验证工作流。
- 部署信息：用一句话概括应导入的 workflow、权重加载位置和关键组件关系；仓库没有 workflow 文件时明确说“需按模型卡或社区节点自行搭建”，不要虚构节点名。
- 下载与组件：先按组件分组。只有同一组件的多档量化或 dev/distilled 版本才写“选一个，不是全部下载”；文本编码器、VAE、声码器、投影器等运行必需件必须单独列出，不能与主权重混成“全部任选一”。可选 LoRA、上采样器和补丁要标为按工作流选装。
- 热度：TrendingScore N · 下载 N · 点赞 N；直接复用候选中已有的 HF 指标，字段缺失时才省略。
- 活动密度：只复述 `activity_density.signals` 支持的事实，例如高 Trending、近期仓库活动、发布后下载/点赞速度或跨日下载/点赞/排名增长；可附带候选已有的每日速度，不合成总分，不把它解释为质量。
- 必需依赖：用自然语言说明基座、文本编码器、VAE、vocoder、upscaler 或 LoRA 依赖，以及该仓是否只提供其中一部分。
- 运行方式：只保留真正可执行的主要路径，例如 ComfyUI 或 Diffusers；不要把 tags 中所有兼容库平铺成列表。
- 加速：蒸馏 / Turbo / Lightning / LCM；有 NFE 或步数证据时同时给出。
- Offload：只列模型卡明确支持的方式。
- 占用：只有明确单个权重或完整 bundle 的大小才展示；不展示包含多套互斥权重的仓库总量。
- 窗口信号：新发布 | 仓库更新 | 当前热门。
- 时间：YYYY-MM-DD
- 链接：[Hugging Face](https://huggingface.co/...)
```

字段规则：

- `窗口信号` 只写候选和 HF 页面支持的事实，不把 `lastModified` 扩写为版本发布。
- `当前热门` 只表示观察日仍满足热门条件，不写成“本周发布”“本周更新”或“热度上升”；只有 `metadata.trend` 的非空增量才能支持趋势变化表述。
- `关注` 按候选的 `selection` 写为“HF 热门”“HF 热门 · 重点白名单”或“重点白名单”；历史运行不写实时热度与趋势变化。
- `对齐信号` 只根据 `metadata.alignment.signals` 写；保留具体 HF tag，并明确这是发布者定位信号。不得把 `low-refusal`、`uncensored`、`abliterated` 或 `heretic` 写成能力、安全或质量加分，也不得声称一定零拒绝。
- `方向` 只根据 `metadata.modalities` 和 `metadata.role_evidence` 写；没有完整结构化输入/输出时保留“待确认”，不根据模型名或 model card 宣传语猜测。
- 正式数据集含 `technical-artifact` 时可写“重点技术资产”，不把它描述成 HF 热门；重点新发现含 `trusted-publisher` 但不含 `hot` 时写“主要厂商技术数据”。
- 参数规模只使用 HF 结构化字段，不从模型名推断。
- 参数规模写成“HF 权重参数量”，避免把仓库权重总量误写成激活参数量或整个多模块系统的总规模；`scale.inherited` 为 `true` 时注明继承自原模型。
- 架构类型只使用 `metadata.architecture`、`metadata.architecture_classes` 和 `card.architecture_excerpt`；架构类是实现类名，不自行扩写成论文中的结构结论。
- 论文链接只使用 `metadata.papers`，同时给出 arXiv 与 HF Paper；没有结构化 `arxiv:` tag 时省略，不按模型名搜索补猜。
- 评测只使用 `card.evaluation` 中的模型卡证据，写成“模型卡报告”或“发布方报告”，不包装成独立第三方结论。
- 评测摘要优先回答四项：评测对象/量化版本、评测工具与硬件或推理模式、覆盖的能力类别、最有说明力的结果与同条件基线。原文缺少某项时不补猜。
- 单条评测摘要控制在 1–2 句，代表性结果通常不超过 4 个；不复写完整 leaderboard。状态摘要和更新摘要各控制在 1 句，同一事实不在多个字段重复。
- ComfyUI 条目必须包含“它是什么 + 基础场景与用法 + ComfyUI 上下游”；读者不需要预先认识模型、缩写或 ComfyUI 节点。组件关系已经在“部署信息”或“下载与组件”中说明时，不再重复生成“必需依赖”。
- `card.evaluation.caveats` 包含“未完整评测”、内部基准、小样本、未发布 harness、仅验证单一量化版本等边界时，必须在同一条“评测表现”中说明。
- 只有同一模型卡明确声明相同评测工具、数据、解码和评分设置时才比较模型或量化版本；不同模型卡的分数不得直接横比。
- HF 热门由 TrendingScore、下载和点赞支持；评测结果用于解释模型的技术吸引力，不得无来源写成热度的因果原因。
- 模型候选只要已有 `trendingScore`、`downloads` 或 `likes` 就统一生成“热度”；不得因模型位于旗舰、新发现或 ComfyUI 分节而漏掉，也不得为缺失指标补零。
- 没有明确原模型时省略“原模型”。
- 没有结构化衍生关系或本地部署格式时，分别省略“衍生”或“部署”；不得从仓库名猜测。
- `deployment_profile.runtimes`、精度、NFE/步数、加速和 offload 只使用 HF tags、仓库文件名或 model card 明确证据；不要从模型名补猜。
- `repository_bytes` 是仓库文件总量，可能包含多个互斥精度和可选组件；不得写成显存、内存或完整运行占用。
- `artifact_options[].required_all=true` 表示同一权重的索引分片 bundle；报告必须说明完整下载 `path_pattern` 覆盖的全部分片。`complete=false` 时不得把该 bundle 写成可直接部署。
- `complete_runtime_status` 不是 `complete` 时，不计算或展示一个看似精确的完整占用；缺失原因留在审计 JSON，正式报告不展示占位提示。
- 正式报告中直接省略 `complete_runtime_status=partial/unknown` 对应的“完整运行占用”提示；这些状态保留在 JSON 供部署审计，不占用户阅读版面。
- `change_evidence` 的提交标题若仅为 `Update README`、文档、拼写、元数据或其他不能说明能力变化的维护项，不生成“更新摘要”。只有明确权重、代码、工作流、数据或评测变化时才展示。
- `pending_registry` 是内部维护字段，正式报告永不展示“待纳入注册表”。
- ComfyUI 仓库总大小若由多套量化或 dev/distilled 互斥权重相加而成，不展示仓库总量；用 `artifact_options[].component` 区分主网络候选与必须搭配的编码器/VAE/声码器，不能把不同组件写成互斥选择。
- `media_customization` 只按 `signals` 写能力。`source=hf-pipeline_tag` / `hf-tag` 是结构化任务或标签，`source=model-card` 是当前仓发布方自述，`source=upstream-model-card` 是当前 ComfyUI 打包仓明确链接的原模型自述；它们都不等同于实际工作流验证。`comfyui_integration.topology_source=capability-template` 只是基于能力类别给出的通用上下游建议；只有 `workflow_files` 能证明仓库交付了工作流文件，也仍不代表当前环境已实际运行验证。
- `discovery_tracks=open-activity` 只表示候选独立满足透明活动条件；没有该值不代表能力弱或不值得验证。报告不读取任何下游模型注册表，也不输出“已覆盖 / 缺 variant / 系统缺口”等消费方状态。
- `activity_density` 不提供综合评分。`repository_age_days` 仅用于计算发布 120 天内的下载/点赞日均速度；`downloads-growing`、`likes-growing` 和 `rank-rising` 只有跨日至少两次趋势快照时才会出现。
- 媒体部署依赖链只用于私有部署规划，本报告不评价或汇总许可证链。
- `lastModified` 命中时间窗口时只确定“仓库更新”；具体变更只从 `change_evidence.commits` 概括。
- 可复现项目表格只列本窗口内新增或更新的阶段。
- GitHub 子目录交付件只有该路径在本窗口有提交时才列为更新；同仓库其他路径的提交不得倒灌。
- `change_evidence.ok` 为 `false` 或提交列表为空时，不猜测具体变化；写“只能确认仓库时间戳更新，未取得可核验的提交摘要”。
- 提交标题宽泛时保持证据粒度，例如只写“更新 README”或“上传文件”；不得用 model card 的当前内容反推该提交新增了什么。
- `card.excerpt` 必须改写成中文摘要，不长段引用；只写片段明确支持的能力、用途和交付件。
- 仓库更新时，model/dataset card 只提供当前背景或状态摘要，不得据此声称这些能力、数据或交付件在本窗口新增。
- `card.ok` 为 `false` 或片段缺少证据时省略“本期看点”“为什么关注”或“用途与内容”，不根据名称推断。
- 最终报告不展示采集状态、与报告字段无关的原始 tags、分类过程或顶层发现池；`metadata.alignment.signals` 是可展示的结构化证据。如额外生成覆盖热力图，遵守 [heatmap-diagnostics.md](heatmap-diagnostics.md)，并与正式报告正文分离。
- 最终报告以覆盖完整候选和证据边界为优先，不追求固定篇幅；没有评测、架构、论文或提交证据的可选字段直接省略，不用空话补齐行数。
- 热门衍生/本地部署模型最多 20 条，只折叠注册表显式声明同一 `variant_group` 的变体，再覆盖最多 8 个不同发布者，并保证 Merge、Finetune、Adapter、GGUF、MLX、On-device 和 Quantized 类型覆盖。当前运行先按可用的 HF 排名/互动增量证据，再按 TrendingScore、重点标记、点赞和下载量稳定排序；历史运行按重点标记、窗口事件日期和仓库 ID 排序。数据集按主要厂商/重点技术资产和可用热度排序。

全部分节为空时输出：

```markdown
# AI 开源模型观察｜YYYY-MM-DD — YYYY-MM-DD

本时间窗口内没有热门或重点的模型与数据集更新。
```
