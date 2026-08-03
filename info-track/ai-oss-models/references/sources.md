# 来源与分类

## 来源

- 精确查询模型、数据集和可复现项目注册表中的 Hugging Face 仓库。
- 当前运行查询 HF 全局 Trending Top 500 和最近更新 Top 1000，召回未登记 owner 的热门社区模型和未被过滤器覆盖的完整权重仓库；历史运行不查询这两个实时池。
- 按 HF Trending 查询 GGUF、MLX、quantized、on-device、merge、finetune 和 adapter 衍生候选。
- 当前运行的数据集同时查询 HF Trending、最近更新和已登记主要厂商 owner；历史运行只查询已登记 owner 和精确注册表 ID，避免实时热度倒灌。
- 当前运行查询已登记官方 owner、本地生态发布者和社区发布者的最近更新模型；历史运行只查询已登记官方 owner，并对注册表条目做精确查询。这一路径既复用为正式仓库状态，也作为已知社区雷达。
- 查询可复现项目注册表中已登记 GitHub 仓库的 `pushed_at`，追踪训练 recipe、数据管线和评测代码更新；GitHub 子目录链接按所属仓库更新信号处理。
- 只为最终入选的重点旗舰、本地热门、正式数据集和重点新发现读取对应 model card 或 dataset card。

全局池、衍生过滤池和 owner 池先按仓库 ID 合并，再进行分类与去重。不能假设 HF 的 `finetune` 等过滤器会返回所有带对应 `base_model` 关系的仓库。

## 白名单

- [model-registry.json](model-registry.json)：旗舰模型身份、角色、本地部署版本、可关联原模型和已知社区发布者。
- [reproducible-projects.json](reproducible-projects.json)：可复现项目、交付件角色和依赖。
- [dataset-registry.json](dataset-registry.json)：高质量数据集用途及关联模型。

旗舰身份、确认后的模型角色、开放程度和重点数据集只由注册表确定。发现池可按下面的重点新发现规则进入单独分节，但必须标记“待纳入注册表”，不得冒充确认后的旗舰或重点数据集。

## 入选条件

- 旗舰模型：精确 ID 位于白名单，且本窗口内发布或更新。
- 热门衍生与本地部署：当前运行要求具有本地部署格式或 HF `base_model` 衍生关系并满足 HF 热门条件，也可用 `trending-observed` 纳入窗口外更新但仍处于热门池的模型。指定历史日期时不使用实时热榜、下载、点赞或 TrendingScore，只纳入注册表中标记为重点且在窗口内发布或更新的本地模型；不自动发现未登记的历史衍生模型。
- 可复现项目：项目位于白名单，且本窗口内有已登记交付件发布或更新。
- 数据集：精确 ID 位于技术数据注册表且本窗口内发布或更新时，重点、关联可复现项目或明确技术角色可以作为入选理由，不要求同时进入 HF 热榜；未登记 owner 的发现仍需满足热门条件。
- 重点新发现：已登记官方 owner 的窗口内新模型或数据集可进入发现池；未登记 owner 的热门模型和数据集只在当前运行中从全局候选池发现，历史运行不使用这类实时热门信号。

HF 热门条件：

- 热门衍生与本地部署：`trendingScore >= 4`，且 `downloads >= 2000` 或 `likes >= 20`。
- 未登记 owner 的模型发现：`trendingScore >= 15`，且 `downloads >= 2000` 或 `likes >= 20`。
- 数据集：`trendingScore >= 15`，且 `downloads >= 1000` 或 `likes >= 20`。

独立爆款条件：本地模型 `trendingScore >= 50`、`downloads >= 100000` 且 `likes >= 100`。已知本地部署生态发布者位于 [model-registry.json](model-registry.json)，只用于补充 owner 定向查询，不为其预留报告名额。发布者分层为 `registered-owner`、`local-ecosystem-publisher` 和 `unregistered`；分层用于召回、排序和审计，不把本地部署生态发布者升级为官方旗舰 owner。

当前运行的正式分组按重点标记和热度排序，不按更新时间生成流水账。历史运行不使用实时热度，按重点标记、窗口事件日期和仓库 ID 稳定排序。

热门衍生与本地部署模型最多 20 条。只有 [model-registry.json](model-registry.json) 的 `model_overrides.<repo>.variant_group` 显式声明同组时，才把同一发布者下的仓库折叠为一个代表条目及 `variants`；`base_model` 相同不足以证明社区模型的训练、合并或用途相同。先覆盖最多 8 个不同发布者，再保证 `merge`、`finetune`、`adapter`、`gguf`、`mlx`、`on-device` 和 `quantized` 类型覆盖；默认同一发布者最多 3 条，候选不足时放宽，最后按 TrendingScore、重点标记、点赞和下载量排序。发布者覆盖对官方、已知社区和新发布者使用同一规则，不给具体名单预留名额。

## 重点新发现排序

- 模型优先级依次考虑：已登记官方发布者、新发布、TrendingScore、点赞、下载量和日期。达到热门阈值的未登记 owner 候选必须标记 `global-discovery` 和 `pending-registry`。
- 先选择不同方向的最高优先级模型，再补足候选；同一发布者默认最多 2 条，同一方向默认最多 3 条，候选不足时放宽。
- 热门新数据集按 TrendingScore、新发布、日期、点赞和下载量排序，最多 5 条。
- 已登记主要厂商 owner 的新技术数据集可以在未达到热榜阈值时进入发现池，并优先于未登记 owner 的同热度候选；仍须标记 `pending-registry`。
- 模型与数据集合计最多 12 条；候选充足时至少 8 条。
- 方向覆盖包括 LLM、VLM、图像、视频、语音、OCR、翻译、Embedding 和 Robotics；结构化字段不足时标为“待确认”。方向只用于展示与去重，不确认旗舰身份。

## HF 字段

- 事件：`createdAt`、`lastModified`。
- 模态：`pipeline_tag`。
- 能力：精确 tags 和模型注册表覆盖项。
- 部署：精确 tags、量化配置和模型注册表。
- 依赖：`cardData.base_model`、`base_model_relation` 和 `base_model:*` tags。
- 衍生关系：只接受 HF 结构化 `adapter`、`finetune`、`merge` 和 `quantized` 关系。
- 架构：只在 config 含明确 expert 字段或精确 tags 支持时标记 MoE，在精确 `diffusers` tag 支持时标记 Diffusion；普通 config 的存在不足以证明 Dense，其余情况使用 `unknown`。
- 参数量：`safetensors.total` 或 `gguf.total`。

## 当前热门与趋势快照

- `trending-observed` 只在未传 `--date` 的当前运行中使用，表示仓库在观察日仍满足热门条件，不表示当日发布或更新。
- 当前运行在调用方提供 `--state-dir` 或 `AI_OSS_MODELS_STATE_DIR` 时，把全局 Trending 排名、TrendingScore、下载量和点赞量保存到该目录的 `trending-snapshot.json`；下一次使用同一目录运行时，在 `metadata.trend` 中给出排名与指标增量。
- 未提供状态目录时不读写持久状态，趋势增量为空。快照不写入候选 JSON、报告或技能仓库。
- 指定 `--date` 的历史回测既不查询实时全局热门池，也不读写快照；候选 metadata 省略当前下载、点赞、TrendingScore 和趋势字段，防止当前社区热度影响历史召回、排序或展示。

不从模型名推断分类、参数量或依赖。缺少结构化字段时使用空值或 `unknown`。

## 可复现交付件角色

以下是本 skill 的内部白名单，不是 Hugging Face 标准 tags：

`raw-data`、`pretrain-data`、`data-pipeline`、`tokenizer`、`training-recipe`、`training-config`、`intermediate-checkpoint`、`base-checkpoint`、`sft-data`、`sft-checkpoint`、`preference-data`、`reward-model`、`aligned-checkpoint`、`eval-dataset`、`eval-harness`、`eval-results`、`deployment-artifact`。
