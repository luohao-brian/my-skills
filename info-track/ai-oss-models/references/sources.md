# 来源与分类

## 来源

- 精确查询模型、数据集和可复现项目注册表中的 Hugging Face 仓库。
- 按 HF Trending 查询 GGUF、MLX、quantized、on-device、merge、finetune 和 adapter 衍生候选。
- 按 HF Trending 查询数据集候选。
- 查询白名单 owner 的最近更新模型，既复用为正式仓库状态，也作为发现池。
- 只为最终入选的重点旗舰、正式数据集和重点新发现读取对应 model card 或 dataset card。

## 白名单

- [model-registry.json](model-registry.json)：旗舰模型身份、角色、本地部署版本和可关联原模型。
- [reproducible-projects.json](reproducible-projects.json)：可复现项目、交付件角色和依赖。
- [dataset-registry.json](dataset-registry.json)：高质量数据集用途及关联模型。

旗舰身份、确认后的模型角色、开放程度和重点数据集只由注册表确定。发现池可按下面的重点新发现规则进入单独分节，但必须标记“待纳入注册表”，不得冒充确认后的旗舰或重点数据集。

## 入选条件

- 旗舰模型：精确 ID 位于白名单，且本窗口内发布或更新。
- 热门衍生与本地部署：本窗口内发布或更新，具有本地部署格式或 HF `base_model` 衍生关系，并满足 HF 热门条件。满足以下任一项即可入选：可关联到旗舰或本地根模型、来自本地生态发布者白名单、达到独立爆款条件、具有 `merge`、`finetune`、`adapter` 或 `quantized` 结构化关系。精确白名单仍必须满足热门条件。
- 可复现项目：项目位于白名单，且本窗口内有已登记交付件发布或更新。
- 数据集：精确 ID 位于高质量数据集白名单，本窗口内发布或更新，并满足 HF 热门条件。重点标记用于报告说明，不绕过热门条件。
- 重点新发现：模型必须来自已登记官方 owner；热门新数据集不要求精确 ID 白名单，但必须满足 HF 热门条件。

HF 热门条件：

- 热门衍生与本地部署：`trendingScore >= 4`，且 `downloads >= 2000` 或 `likes >= 20`。
- 数据集：`trendingScore >= 15`，且 `downloads >= 1000` 或 `likes >= 20`。

独立爆款条件：本地模型 `trendingScore >= 50`、`downloads >= 100000` 且 `likes >= 100`。本地生态发布者白名单位于 [model-registry.json](model-registry.json)。

正式分组按重点标记和热度排序，不按更新时间生成流水账。时间命中不是单独的入选理由。

热门衍生与本地部署模型最多 20 条。先保证 `merge`、`finetune`、`adapter`、`gguf`、`mlx`、`on-device` 和 `quantized` 类型覆盖；默认同一发布者最多 3 条，候选不足时放宽，再按重点标记和热度排序。

## 重点新发现排序

- 模型优先级依次考虑：已登记官方发布者、新发布、TrendingScore、点赞、下载量和日期。
- 先选择不同方向的最高优先级模型，再补足候选；同一发布者默认最多 2 条，同一方向默认最多 3 条，候选不足时放宽。
- 热门新数据集按 TrendingScore、新发布、日期、点赞和下载量排序，最多 5 条。
- 模型与数据集合计最多 12 条；候选充足时至少 8 条。
- 方向覆盖包括 LLM、VLM、图像、视频、语音、OCR、翻译、Embedding 和 Robotics；结构化字段不足时标为“待确认”。方向只用于展示与去重，不确认旗舰身份。

## HF 字段

- 事件：`createdAt`、`lastModified`。
- 模态：`pipeline_tag`。
- 能力：精确 tags 和模型注册表覆盖项。
- 部署：精确 tags、量化配置和模型注册表。
- 依赖：`cardData.base_model`、`base_model_relation` 和 `base_model:*` tags。
- 衍生关系：只接受 HF 结构化 `adapter`、`finetune`、`merge` 和 `quantized` 关系。
- 架构：config 和精确 tags。
- 参数量：`safetensors.total` 或 `gguf.total`。

不从模型名推断分类、参数量或依赖。缺少结构化字段时使用空值或 `unknown`。

## 可复现交付件角色

以下是本 skill 的内部白名单，不是 Hugging Face 标准 tags：

`raw-data`、`pretrain-data`、`data-pipeline`、`tokenizer`、`training-recipe`、`training-config`、`intermediate-checkpoint`、`base-checkpoint`、`sft-data`、`sft-checkpoint`、`preference-data`、`reward-model`、`aligned-checkpoint`、`eval-dataset`、`eval-harness`、`eval-results`、`deployment-artifact`。
