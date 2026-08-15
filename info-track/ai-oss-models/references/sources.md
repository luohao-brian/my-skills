# 来源与分类

## 来源

- 精确查询模型、数据集和可复现项目注册表中的 Hugging Face 仓库。
- 当前运行查询 HF 全局 Trending Top 500 和最近更新 Top 1000，召回未登记 owner 的热门社区模型和未被过滤器覆盖的完整权重仓库；历史运行不查询这两个实时池。
- 当前运行额外按结构化任务查询图像生成、视频生成和 TTS 的 Trending 与最近更新池，并保留 HF 官方任务内排名；这是模态级召回漏斗，不依赖模型名或发布者。历史运行不查询这些实时池。
- 当前运行查询 ComfyUI filter 的 Trending 与最近更新池，并对 digital-human、talking-head、lip-sync、face-swap、person-replacement、identity-consistency、video-editing 精确 tags 各查询一次最近更新池，用于补回 ComfyUI 大池 Top 200 之外的稀疏能力。共 9 个列表请求并行执行；历史运行不查询该实时池。
- 按 HF Trending 查询 GGUF、MLX、quantized、on-device、merge、finetune 和 adapter 衍生候选，并查询 uncensored、abliterated、heretic、decensored 精确 tags 形成低拒绝候选池。
- 当前运行的数据集同时查询 HF Trending、最近更新和已登记主要厂商 owner；历史运行只查询已登记 owner 和精确注册表 ID，避免实时热度倒灌。
- 当前运行查询已登记官方 owner、本地生态发布者和社区发布者的最近更新模型；历史运行只查询已登记官方 owner，并对注册表条目做精确查询。这一路径既复用为正式仓库状态，也作为已知社区雷达。
- 使用已认证的 `gh api` 查询可复现项目注册表中已登记 GitHub 仓库的本窗口提交，追踪训练 recipe、数据管线和评测代码更新；GitHub 子目录链接必须使用 `path` 过滤提交，不用仓库级 `pushed_at` 代替子目录证据。
- 当前运行通过 `gh api` 读取已登记 GitHub 工程的 star/fork，并在提供状态目录时计算增量；不从模型卡任意发现或猜测 GitHub 仓库。star/fork 只表达工程关注和采用信号，不证明模型质量或本窗口技术变化。
- 只为最终入选的重点旗舰、本地热门、正式数据集和重点新发现读取对应 model card 或 dataset card。
- 对最终入选的媒体模型及 ComfyUI 媒体定制雷达条目，在同一次 formal enrichment 中额外调用一次 HF model detail（`blobs=true&expand=siblings&expand=usedStorage`），一次取得仓库文件路径与尺寸，用于组件、精度和仓库占用汇总；不逐文件请求。
- 运行时、NFE/步数、蒸馏/Turbo/Lightning/LCM、offload、外部模型链接和媒体定制措辞复用上述 model card 请求，不增加请求次数。
- 默认不递归读取依赖仓库文件列表。基础模型、VAE、编码器、vocoder、LoRA 等依赖链会被保留，但精确完整运行占用需要显式部署 bundle manifest；没有 manifest 时不得把仓库中的可选权重全部相加。
- 所有正式候选合并后共用一个 enrichment 任务池，不按报告分节串行抓取 model card 和提交历史；同一次 run 不重复采集同一正式候选。
- 从最终入选模型的 model card 提取 Evaluation、Benchmark、Leaderboard 等评测小节和以 `Benchmark` 为表头的结果表，同时提取 Limitations / Caveats 作为评测边界。
- 对最终入选的 HF `repository-updated` 候选读取本窗口提交历史；对可复现项目的已更新 HF/GitHub 交付件读取提交标题和链接，供成稿解释具体变化。

全局池、衍生过滤池和 owner 池先按仓库 ID 合并，再进行分类与去重。不能假设 HF 的 `finetune` 等过滤器会返回所有带对应 `base_model` 关系的仓库。

## 白名单

- [model-registry.json](model-registry.json)：旗舰模型身份、角色、本地部署版本、可关联原模型和已知社区发布者。
- [reproducible-projects.json](reproducible-projects.json)：可复现项目、交付件角色和依赖。
- [dataset-registry.json](dataset-registry.json)：高质量数据集用途及关联模型。

旗舰身份、确认后的模型角色、开放程度和重点数据集只由注册表确定。发现池可按下面的重点新发现规则进入单独分节，但必须标记“待纳入注册表”，不得冒充确认后的旗舰或重点数据集。

## 入选条件

- 旗舰模型：精确 ID 位于白名单，且本窗口内发布或更新。
- 热门衍生与本地部署：当前运行要求具有本地部署格式、HF `base_model` 衍生关系或精确低拒绝 tag，并满足 HF 热门条件，也可用 `trending-observed` 纳入窗口外更新但仍处于热门池的模型；HF `lora` 标签统一视为 `adapter` 衍生关系。指定历史日期时不使用实时热榜、下载、点赞或 TrendingScore，只纳入注册表中标记为重点且在窗口内发布或更新的本地模型；不自动发现未登记的历史衍生模型。
- 可复现项目：项目位于白名单，且本窗口内有已登记交付件发布或更新。
- 数据集：精确 ID 位于技术数据注册表且本窗口内发布或更新时，重点、关联可复现项目或明确技术角色可以作为入选理由，不要求同时进入 HF 热榜；未登记 owner 的发现仍需满足热门条件。
- 重点新发现：已登记官方 owner 的窗口内新模型或数据集可进入发现池；未登记 owner 的热门模型和数据集只在当前运行中从全局候选池发现，历史运行不使用这类实时热门信号。

HF 热门条件：

- 热门衍生与本地部署：`trendingScore >= 4`，且 `downloads >= 2000` 或 `likes >= 20`。
- 未登记 owner 的模型发现：`trendingScore >= 15`，且 `downloads >= 2000` 或 `likes >= 20`。
- 图像生成、视频生成、TTS 和 ASR 模态雷达：候选必须有结构化任务证据，且 `trendingScore >= 4`，并满足 `downloads >= 500` 或 `likes >= 10`；较低阈值只作用于这些稀疏任务池，不降低 LLM/VLM 等通用发现阈值。
- 数据集：`trendingScore >= 15`，且 `downloads >= 1000` 或 `likes >= 20`。

独立爆款条件：本地模型 `trendingScore >= 50`、`downloads >= 100000` 且 `likes >= 100`。已知本地部署生态发布者位于 [model-registry.json](model-registry.json)，只用于补充 owner 定向查询，不为其预留报告名额。发布者分层为 `registered-owner`、`local-ecosystem-publisher` 和 `unregistered`；分层用于召回、排序和审计，不把本地部署生态发布者升级为官方旗舰 owner。

当前运行的正式分组按重点标记和热度排序，不按更新时间生成流水账。历史运行不使用实时热度，按重点标记、窗口事件日期和仓库 ID 稳定排序。

热门衍生与本地部署模型最多 20 条。只有 [model-registry.json](model-registry.json) 的 `model_overrides.<repo>.variant_group` 显式声明同组时，才把同一发布者下的仓库折叠为一个代表条目及 `variants`；`base_model` 相同不足以证明社区模型的训练、合并或用途相同。先覆盖最多 8 个不同发布者，再保证 `merge`、`finetune`、`adapter`、`gguf`、`mlx`、`on-device` 和 `quantized` 类型覆盖；默认同一发布者最多 3 条，候选不足时放宽。排序先看可用的 HF 排名/互动增量证据，再用 TrendingScore、重点标记、点赞和下载量作稳定次序。发布者覆盖对官方、已知社区和新发布者使用同一规则，不给具体名单预留名额。

## 重点新发现排序

- 模型优先级依次考虑：HF 官方排名上升、HF 互动指标增长、官方全局排名档位、任务内排名档位、已登记官方发布者、TrendingScore、点赞、下载量、新发布和日期。全局榜用于跨方向排序，任务榜用于同层补强与稀疏方向召回，不把不同任务的名次数值换算成统一分数；首次快照没有增量时不虚构增长。
- 不为图像生成、视频生成、TTS 或 ASR 无条件预留名额；候选先满足各自召回条件，再与其他方向一起按官方排名与可核验增量选取。
- 不先按方向均分候选；同一发布者默认最多 2 条，同一方向默认最多 3 条，候选不足时放宽，两个上限只用于防止单一来源刷屏。
- 热门新数据集按 TrendingScore、新发布、日期、点赞和下载量排序，最多 5 条。
- 已登记主要厂商 owner 的新技术数据集可以在未达到热榜阈值时进入发现池，并优先于未登记 owner 的同热度候选；仍须标记 `pending-registry`。
- 模型与数据集合计最多 12 条；候选充足时至少 8 条。
- 方向覆盖包括 LLM、VLM、图像、视频、TTS、其他音频生成、语音识别、OCR、翻译、Embedding 和 Robotics；结构化字段不足时标为“待确认”。方向只用于展示与去重，不确认旗舰身份。

## HF 字段

- 事件：`createdAt`、`lastModified`。
- 模态：优先解析 `pipeline_tag`，再合并可解析为完整输入/输出的任务 tags；标准固定任务使用已知 I/O，组合任务按 `<输入模态>-to-<输出模态>` 泛化解析。
- 能力：精确 tags 和模型注册表覆盖项。
- 部署：精确 tags、量化配置和模型注册表。
- 媒体运行时：精确 `comfyui`、`diffusers`、`diffusion-single-file`、`mlx`、`onnx`、`tensorrt`、`transformers`、`vllm` tags，并用最终入选模型的 model card 补充明确运行方式。
- 媒体组件与精度：最终入选模型的 HF sibling 文件路径、文件尺寸和 model card；文件路径按 transformer/UNet、VAE、文本/视觉编码器、vocoder、adapter、projector、upscaler 等部署组件归类。
- NFE 与加速：从 model card 中同时含 inference/sampling/denoise/distill/turbo/lightning/NFE 语境的步数，以及明确的 distilled、turbo、lightning、LCM 表述提取；最终媒体仓库的权重文件名若精确包含 `4step`、`8step`、`distilled`、`turbo`、`lightning` 或 `lcm`，也保留文件路径作为结构化证据，不依赖仓库名。
- 媒体定制：候选召回只接受精确 HF tags；最终候选可用 model card 的 digital human、talking head、lip sync、face swap、person/character replacement、identity consistency、video editing 明确措辞补充。不得从模型名推断。
- 依赖：`cardData.base_model`、`base_model_relation`、`base_model:*` tags，以及最终媒体模型卡中带 required/checkpoint/encoder/VAE/vocoder/LoRA 等依赖语境的 HF 模型链接。排除 docs、collections、datasets、spaces 等非模型页面。
- 衍生关系：只接受 HF 结构化 `adapter`、`finetune`、`merge` 和 `quantized` 关系。
- 对齐信号：只接受 HF 精确 `uncensored`、`abliterated`、`heretic`、`decensored` tags，归一为 `alignment.profile=low-refusal` 并保留原 tag 证据；不从模型 ID 或自然语言介绍推断，也不作为质量或安全结论。
- 架构：只在 config 含明确 expert 字段或精确 tags 支持时标记 MoE，在精确 `diffusers` tag 支持时标记 Diffusion；普通 config 的存在不足以证明 Dense，其余情况使用 `unknown`。
- 架构类：读取 `config.architectures`；model card 存在明确 Architecture 小节时保留短证据片段。
- 参数量：`safetensors.total` 或 `gguf.total`。
- 论文：只读取精确 `arxiv:` tag，并构造对应 arXiv 与 HF Paper 链接。
- 评测：只保留 model card 明确报告的设置、基准、对照项、分数和限制；model card 结果属于发布方自述，不自动视为独立复现。
- 证据片段在采集阶段有长度上限，保留开头的设置、代表性表格和 limitations/caveats；成稿不得因片段截断而补猜后续结果。

方向分类只使用上述结构化模态证据：视频输出归入视频生成，图像输出归入图像生成；只有 `text-to-speech` 或等价结构化 TTS 能力归入语音合成，其他音频输出归入音频生成；纯文本输出先识别视觉输入，再识别音频输入和文本输入，避免同时带视觉与音频标签的多模态模型误归 ASR。`any-to-any` 保留为通用多模态方向。不得用模型 ID、owner 或自然语言名称补分类。

## 当前热门与趋势快照

- `trending-observed` 只在未传 `--date` 的当前运行中使用，表示仓库在观察日仍满足热门条件，不表示当日发布或更新。
- 当前运行在调用方提供 `--state-dir` 或 `AI_OSS_MODELS_STATE_DIR` 时，把 HF 全局与任务内 Trending 排名、TrendingScore、下载量、点赞量，以及已登记 GitHub 工程的 star/fork 保存到该目录的 `trending-snapshot.json`；下一次使用同一目录运行时，在模型 `metadata.trend` 和项目交付件 `github.trend` 中给出对应增量。
- 同一 UTC 自然日内重复运行会刷新快照，但不产生排名或互动增长信号，避免把分钟级榜单抖动解释成趋势；至少跨日的连续快照才计算增量。
- 未提供状态目录时不读写持久状态，趋势增量为空。快照不写入候选 JSON、报告或技能仓库。
- 指定 `--date` 的历史回测既不查询实时全局热门池，也不读写快照；候选 metadata 省略当前下载、点赞、TrendingScore 和趋势字段，防止当前社区热度影响历史召回、排序或展示。

不从模型名推断分类、参数量或依赖。缺少结构化字段时使用空值或 `unknown`。

## 可复现交付件角色

以下是本 skill 的内部白名单，不是 Hugging Face 标准 tags：

`raw-data`、`pretrain-data`、`data-pipeline`、`tokenizer`、`training-recipe`、`training-config`、`intermediate-checkpoint`、`base-checkpoint`、`sft-data`、`sft-checkpoint`、`preference-data`、`reward-model`、`aligned-checkpoint`、`eval-dataset`、`eval-harness`、`eval-results`、`deployment-artifact`。
