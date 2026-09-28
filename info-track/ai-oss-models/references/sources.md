# 来源与分类

## 来源

- 精确查询模型注册表中的 Hugging Face 仓库。
- 当前运行查询 HF 全局 Trending Top 500 和最近更新 Top 1000，召回未登记 owner 的热门社区模型和未被过滤器覆盖的完整权重仓库；历史运行不查询这两个实时池。
- 当前运行额外按结构化任务查询图像/视频/音频生成、TTS、ASR、robotics、mask 生成、图片分割和深度估计的 Trending 与最近更新池，并保留 HF 官方任务内排名；这是任务级召回，不依赖模型名或发布者。`robotics` 只召回候选，VLA/动作策略身份由模型卡的输入输出和本体证据确认。历史运行不查询这些实时池。
- 当前运行查询 ComfyUI filter 的 Trending 与最近更新池，并对分割/mask、姿态/运动提取、深度、人脸检测/关键点、换脸、角色动画/动作控制、数字人/对口型、视频生成/编辑/增强等精确任务或 tags 同时查询 Trending 与最近更新池，用于补回 ComfyUI 大池 Top 200 之外的稀疏能力。请求并行执行，具体过滤器以 `ecosystem-architecture.json` 与 `diagnostics.media_ecosystem_by_filter` 为准；历史运行不查询该实时池。
- ComfyUI 媒体工作流雷达复用全局 Trending Top 500 与最近更新 Top 1000 的候选并集；按素材控制、驱动生成、编辑、画质/分辨率增强四段保持覆盖。基础权重仓可进入基础与专项模型；只有精确 `comfyui` 运行时证据的仓库才进入 ComfyUI 分节。
- 按 HF Trending 查询 GGUF、MLX、quantized、on-device、merge、finetune、adapter 和 distilled 衍生候选，并查询 uncensored、abliterated、heretic、decensored 精确 tags 形成低拒绝候选池。
- 当前运行查询已登记官方 owner、本地生态发布者和社区发布者的最近更新模型；历史运行只查询已登记官方 owner，并对注册表条目做精确查询。这一路径既复用为正式仓库状态，也作为已知社区雷达。
- 只为最终入选的基础与专项模型、热门本地模型和重点新发现读取对应 model card。
- 对最终入选的媒体模型及 ComfyUI 工作流雷达预取条目，在同一次 formal enrichment 中额外调用一次 HF model detail（`blobs=true&expand=siblings&expand=usedStorage`），一次取得仓库文件路径与尺寸，用于组件、精度和仓库占用汇总；不逐文件请求。模型卡补证后再执行最终筛选。
- 运行时、NFE/步数、蒸馏/Turbo/Lightning/LCM、offload、外部模型链接和媒体工作流能力措辞复用上述 model card 请求。若 ComfyUI 打包仓只有明确的“original model/base model”HF 链接且自身没有能力证据，可额外读取该上游模型的一张 model card，并以 `upstream-model-card` 记录来源；只跟随一层，不从仓库名猜测或递归扩散。
- 默认不递归读取依赖仓库文件列表。基础模型、VAE、编码器、vocoder、LoRA 等依赖链会被保留，但精确完整运行占用需要显式部署 bundle manifest；没有 manifest 时不得把仓库中的可选权重全部相加。
- 所有正式候选合并后共用一个 enrichment 任务池，不按报告分节串行抓取 model card 和提交历史；同一次 run 不重复采集同一正式候选。
- 从最终入选模型的 model card 提取 Evaluation、Benchmark、Leaderboard 等评测小节和以 `Benchmark` 为表头的结果表，同时提取 Limitations / Caveats 作为评测边界。

全局池、衍生过滤池和 owner 池先按仓库 ID 合并，再进行分类与去重。不能假设 HF 的 `finetune` 等过滤器会返回所有带对应 `base_model` 关系的仓库。

## 本地开发基线

- [development-baselines.json](development-baselines.json) 只登记与模型主干相关的 SFT、LoRA/QLoRA、蒸馏、DPO/GRPO 工具和小规模可抽样数据集。当前和历史运行均只精确查询这些项目的 GitHub 仓库状态及 HF 数据集状态；不查询全站热门数据集或大规模预训练工程。
- 工具与数据的 `pushed_at` / `lastModified` 只产生窗口事件；工具额外读一次 GitHub 最新提交，若提交日期在窗口内则保留标题与链接。没有提交或数据文件差异证据时不写具体新增功能。训练入口写官方支持方法和样本格式，单卡可行性按模型规模、精度、序列长、分辨率/帧数、batch、梯度累积和工具文档核对。L20/5090 仅作资源量级参考。

## 白名单

- [model-registry.json](model-registry.json)：旗舰模型身份、角色、本地部署版本、可关联原模型和已知社区发布者。

基础与专项模型身份及确认后的角色只由模型注册表确定。发现池可按下面的重点新发现规则进入单独分节，但不得冒充确认后的基础与专项模型。

## 入选条件

- 已登记主模型：本窗口内发布或更新直接入选。当前运行还可纳入仓库未更新的模型：自身满足对应方向的热门条件且位于 HF 全球热榜前 100 或任务榜前 20；或本次候选池里至少 3 个不同仓库通过 HF `base_model` 明确指向它，其中至少 1 个衍生仓当前仍满足热门条件。后一数字只表示本次采样候选中的直接引用，不是 HF 全站衍生总数。最多补充 8 个此类观察模型，按跨日热度上升、活跃衍生数、直接引用数和当前热度排序；不得把观察日期写成发布或更新日期。历史 `--date` 不用实时观察池。
- 热门衍生与本地部署：当前运行要求具有本地部署格式、HF `base_model` 衍生关系或精确低拒绝 tag，并满足 HF 热门条件，也可用 `trending-observed` 纳入窗口外更新但仍处于热门池的模型；HF `lora` 标签统一视为 `adapter` 衍生关系。指定历史日期时不使用实时热榜、下载、点赞或 TrendingScore，只纳入注册表中标记为重点且在窗口内发布或更新的本地模型；不自动发现未登记的历史衍生模型。
- 重点新发现：已登记官方 owner 的窗口内新模型可进入发现池；未登记 owner 的热门模型只在当前运行中从全局候选池发现，历史运行不使用这类实时热门信号。

HF 热门条件：

- 热门衍生与本地部署：`trendingScore >= 4`，且 `downloads >= 2000` 或 `likes >= 20`。
- 未登记 owner 的模型发现：`trendingScore >= 15`，且 `downloads >= 2000` 或 `likes >= 20`。
- 图像生成、视频生成、音频生成、TTS、ASR、robotics、媒体控制和画质增强任务雷达：候选必须有结构化任务证据，且 `trendingScore >= 4`，并满足 `downloads >= 500` 或 `likes >= 10`；较低阈值只作用于这些稀疏任务池，不降低 LLM/VLM 等通用发现阈值。`robotics` 入池后仍须逐项核对动作输出、模型卡和本体，不能仅凭 tag 标为 VLA。已登记 VLA 的任务热榜前 20 名，即使 TrendingScore 低于 4，只要下载达到 500 或点赞达到 10，也作为当前热门观察；本次采集到至少 3 个直接衍生且有活跃衍生时同样纳入。
- ComfyUI 媒体工作流雷达：候选必须有精确 `comfyui` tag，并满足本窗口发布/更新、媒体热门或透明高活动条件。高活动条件包括高 Trending、近期仓库活动同时达到媒体热度、发布 120 天内的高下载/点赞日均速度，或趋势快照证明的下载/点赞/排名增长；信号分开保存。已识别的结构化输出允许视频、mask、姿态、运动、深度和人脸分析产物；图片输出只允许有精确换脸或图像增强能力的候选。通用图片生成/编辑与纯文生视频不进入本节。标准 pipeline 缺失的 ComfyUI 候选最多预取 12 条模型卡，最终仍须由 model card 证明工作流能力。正式输出最多 12 条：先保留最多 3 个开放高活动发现，再补齐素材控制、图片到视频、角色动画、音频驱动和编辑/特效、画质和帧率增强等链路；同能力量化、LoRA 或 workflow 包不为凑数重复占位。

独立爆款条件：本地模型 `trendingScore >= 50`、`downloads >= 100000` 且 `likes >= 100`。已知本地部署生态发布者位于 [model-registry.json](model-registry.json)，只用于补充 owner 定向查询，不为其预留报告名额。发布者分层为 `registered-owner`、`local-ecosystem-publisher` 和 `unregistered`；分层用于召回、排序和审计，不把本地部署生态发布者升级为官方旗舰 owner。

当前运行的正式分组按重点标记和热度排序，不按更新时间生成流水账。历史运行不使用实时热度，按重点标记、窗口事件日期和仓库 ID 稳定排序。

热门衍生与本地部署模型最多 20 条。只有 [model-registry.json](model-registry.json) 的 `model_overrides.<repo>.variant_group` 显式声明同组时，才把同一发布者下的仓库折叠为一个代表条目及 `variants`；`base_model` 相同不足以证明社区模型的训练、合并或用途相同。先覆盖最多 8 个不同发布者，再保证 `merge`、`finetune`、`adapter`、`distilled`、`gguf`、`mlx`、`on-device` 和 `quantized` 类型覆盖；默认同一发布者最多 3 条，候选不足时放宽。排序先看可用的 HF 排名/互动增量证据，再用 TrendingScore、重点标记、点赞和下载量作稳定次序。发布者覆盖对官方、已知社区和新发布者使用同一规则，不给具体名单预留名额。

## 重点新发现排序

- 模型优先级依次考虑：HF 官方排名上升、HF 互动指标增长、官方全局排名档位、任务内排名档位、已登记官方发布者、TrendingScore、点赞、下载量、新发布和日期。全局榜用于跨方向排序，任务榜用于同层补强与稀疏方向召回，不把不同任务的名次数值换算成统一分数；首次快照没有增量时不虚构增长。
- 不为图像生成、视频生成、音频生成、TTS 或 ASR 无条件预留名额；候选先满足各自召回条件，再与其他方向一起按官方排名与可核验增量选取。
- 不先按方向均分候选；同一发布者默认最多 2 条，同一方向默认最多 3 条，候选不足时放宽，两个上限只用于防止单一来源刷屏。
- 模型最多 12 条；候选充足时至少 8 条。
- 方向覆盖以 LLM/VLM、图像/视频、TTS/ASR、Decision、Music、具身动作六条主干为中心，同时保留 OCR、翻译和 Embedding 注册模型；结构化字段不足时标为“待确认”。方向只用于展示与去重，不确认旗舰身份。

## HF 字段

- 事件：`createdAt`、`lastModified`。
- 模态：优先解析 `pipeline_tag`，再合并可解析为完整输入/输出的任务 tags；标准固定任务使用已知 I/O，组合任务按 `<输入模态>-to-<输出模态>` 泛化解析。
- 能力：精确 tags 和模型注册表覆盖项。
- 音频任务：`audio_tasks` 只从 `text-to-sfx`、`sound-effects`、`video-to-sfx`、`text-video-to-sfx`、`audio-inpaint`、`audio-continuation`、`ambience-generation`、`music-generation`、`text-to-music`、`singing-voice-conversion`、`singing-voice-synthesis` 等精确 tags 或已核对的注册表覆盖项赋值，并保留来源。`text-to-audio`、`video-to-audio` 和 `text-video-to-audio` 只提供输入输出方向，不自动赋予歌曲、音效或同步能力。已登记且经模型卡核对的音频专项模型在本期无仓库事件时，若 Hugging Face 点赞至少 50，可标记“当前站内关注”；只有任务热榜或趋势证据时才写“仍在热榜”或“热度上升”。
- 决策任务：已登记的 NeoHorse-Jev、Kev、OpenJev 与 Laya 用注册表确认角色；未登记模型仅在 `typed-decisions` 与 `structured-prediction` 两个精确 tags 同时存在时归入结构化决策。原生 `choice`、`score`、`noul` 与 JEV 协议兼容、语义评测分别核对。
- 部署：精确 tags、量化配置和模型注册表。
- 媒体运行时：精确 `comfyui`、`diffusers`、`diffusion-single-file`、`mlx`、`onnx`、`tensorrt`、`transformers`、`vllm` tags，并用最终入选模型的 model card 补充明确运行方式。
- 媒体组件与精度：最终入选模型的 HF sibling 文件路径、文件尺寸和 model card；文件路径按 transformer/UNet、VAE、文本/视觉编码器、vocoder、adapter、projector、upscaler 等部署组件归类。
- NFE 与加速：从 model card 中同时含 inference/sampling/denoise/distill/turbo/lightning/NFE 语境的步数，以及明确的 distilled、turbo、lightning、LCM 表述提取；最终媒体仓库的权重文件名若精确包含 `4step`、`8step`、`distilled`、`turbo`、`lightning` 或 `lcm`，也保留文件路径作为结构化证据，不依赖仓库名。
- 清晰度与帧率：只保留 model card 同一行出现超分/分辨率/帧率/修复任务词与 `宽×高`、`1080p`、倍率或 fps 数值的短证据；由报告按原句解释输入、输出和适用素材，不从仓库名、文件大小或通用 pipeline 推断画质提升。
- 媒体工作流能力：素材控制接受 `image/video -> mask/pose/motion/depth/face/landmarks` 的结构化任务或精确 tags；驱动生成接受 `image/audio/video -> video`、首尾帧/参考图/多镜头控制、角色动画、动作迁移、数字人、对口型；编辑收尾接受明确的换脸、人物替换、视频局部重绘、补帧和放大。标准 pipeline 缺失时，最终候选可用 model card 的明确措辞补充；不得从模型名推断。
- 依赖：`cardData.base_model`、`base_model_relation`、`base_model:*` tags，以及最终媒体模型卡中带 required/checkpoint/encoder/VAE/vocoder/LoRA 等依赖语境的 HF 模型链接。排除 docs、collections、datasets、spaces 等非模型页面。
- `canonical_model` 追溯：只用 HF `cardData.base_model` 和精确 `base_model:*` tag 构成血缘边；对正式入选模型按需查询缺失的父仓，最多追溯 4 跳。每跳记录 `from`、`to`、relation、source 和原始证据。模型卡中的一般依赖链接只用于运行组件，不进入 canonical 血缘。`canonical_model` 是路径中验证过的衍生线主模型，最远终点另记 `root_model`。多父分叉、冲突关系和循环不宣布唯一主模型；父仓不可读时可保留已由当前仓证实的主模型，但不宣布终点。注册表 `canonical` 是可核对的声明，不替代 HF 血缘。
- 衍生关系：只接受 HF 结构化 `adapter`、`finetune`、`merge` 和 `quantized` 关系；`distilled` 仅由精确 HF tag 标记，未关联基座时不能补猜师生关系。
- 对齐信号：只接受 HF 精确 `uncensored`、`abliterated`、`heretic`、`decensored` tags，归一为 `alignment.profile=low-refusal` 并保留原 tag 证据；不从模型 ID 或自然语言介绍推断，也不作为质量或安全结论。
- 架构：只在 config 含明确 expert 字段或精确 tags 支持时标记 MoE，在精确 `diffusers` tag 支持时标记 Diffusion；普通 config 的存在不足以证明 Dense，其余情况使用 `unknown`。
- 架构类：读取 `config.architectures`；model card 存在明确 Architecture 小节时保留短证据片段。
- 参数量：`safetensors.total` 或 `gguf.total`。
- 论文：只读取精确 `arxiv:` tag，并构造对应 arXiv 与 HF Paper 链接。
- 评测：只保留 model card 明确报告的设置、基准、对照项、分数和限制；model card 结果属于发布方自述，不自动视为独立复现。
- 证据片段在采集阶段有长度上限，保留开头的设置、代表性表格和 limitations/caveats；成稿不得因片段截断而补猜后续结果。

方向分类只使用上述结构化模态证据：精确 typed-decision tags 先归入结构化决策；mask、姿态、运动、深度或人脸分析输出归入媒体控制；精确超分、修复或补帧 tag 归入媒体增强，视频输出归入视频生成，图像输出归入图像生成；只有 `text-to-speech` 或等价结构化 TTS 能力归入语音合成，其他音频输出归入音频生成；纯文本输出先识别视觉输入，再识别音频输入和文本输入。`any-to-any` 保留为通用多模态方向。不得用模型 ID、owner 或自然语言名称补分类。

## 当前热门与趋势快照

- `trending-observed` 只在未传 `--date` 的当前运行中使用，表示仓库在观察日仍位于热门池，不表示当日发布或更新。`derivatives-observed` 表示原模型仓库没有更新，但本次候选池中至少 3 个衍生仓明确引用它，且其中至少 1 个当前热门。单次快照只能说明“当前仍热门/衍生活跃”；只有跨日快照的排名或互动指标正增量才能写“上升/增长”，不能用两个同日运行结果冒充趋势。
- 当前运行在调用方提供 `--state-dir` 或 `AI_OSS_MODELS_STATE_DIR` 时，把 HF 全局与任务内 Trending 排名、TrendingScore、下载量、点赞量， 保存到该目录的 `trending-snapshot.json`；下一次使用同一目录运行时，在模型 `metadata.trend` 中给出对应增量。
- 同一 UTC 自然日内重复运行会刷新快照，但不产生排名或互动增长信号，避免把分钟级榜单抖动解释成趋势；至少跨日的连续快照才计算增量。
- 未提供状态目录时不读写持久状态，趋势增量为空。快照不写入候选 JSON、报告或技能仓库。
- 指定 `--date` 的历史回测既不查询实时全局热门池，也不读写快照；候选 metadata 省略当前下载、点赞、TrendingScore 和趋势字段，防止当前社区热度影响历史召回、排序或展示。

不从模型名推断分类、参数量或依赖。缺少结构化字段时使用空值或 `unknown`。
