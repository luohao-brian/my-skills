# 来源与分类

## 来源

- 精确查询模型、数据集和可复现项目注册表中的 Hugging Face 仓库。
- 按 HF Trending 查询 GGUF、MLX、quantized 和 on-device 本地部署候选。
- 按 HF Trending 查询数据集候选。
- 查询白名单 owner 的最近更新模型作为 `discoveries`。

## 白名单

- [model-registry.json](model-registry.json)：旗舰模型身份、角色、本地部署版本和可关联原模型。
- [reproducible-projects.json](reproducible-projects.json)：可复现项目、交付件角色和依赖。
- [dataset-registry.json](dataset-registry.json)：高质量数据集用途及关联模型。

旗舰身份、模型角色、开放程度和重点数据集只由注册表确定。`discoveries` 不自动进入正式分组。

## 入选条件

- 旗舰模型：精确 ID 位于白名单，且本窗口内发布或更新。
- 本地部署：本窗口内发布或更新，具有本地部署格式，满足 HF 热门条件，并满足以下一项：可沿 HF `base_model` 关联到旗舰白名单、来自本地生态发布者白名单、达到独立爆款条件。精确本地模型白名单仍必须满足热门条件。
- 可复现项目：项目位于白名单，且本窗口内有已登记交付件发布或更新。
- 数据集：精确 ID 位于高质量数据集白名单，本窗口内发布或更新，并满足 HF 热门条件。重点标记用于报告说明，不绕过热门条件。

HF 热门条件：

- 本地部署：`trendingScore >= 20`，且 `downloads >= 10000` 或 `likes >= 50`。
- 数据集：`trendingScore >= 15`，且 `downloads >= 1000` 或 `likes >= 20`。

独立爆款条件：本地模型 `trendingScore >= 50`、`downloads >= 100000` 且 `likes >= 100`。本地生态发布者白名单位于 [model-registry.json](model-registry.json)。

正式分组按重点标记和热度排序，不按更新时间生成流水账。时间命中不是单独的入选理由。

## HF 字段

- 事件：`createdAt`、`lastModified`。
- 模态：`pipeline_tag`。
- 能力：精确 tags 和模型注册表覆盖项。
- 部署：精确 tags、量化配置和模型注册表。
- 依赖：`cardData.base_model`、`base_model_relation` 和 `base_model:*` tags。
- 架构：config 和精确 tags。
- 参数量：`safetensors.total` 或 `gguf.total`。

不从模型名推断分类、参数量或依赖。缺少结构化字段时使用空值或 `unknown`。

## 可复现交付件角色

以下是本 skill 的内部白名单，不是 Hugging Face 标准 tags：

`raw-data`、`pretrain-data`、`data-pipeline`、`tokenizer`、`training-recipe`、`training-config`、`intermediate-checkpoint`、`base-checkpoint`、`sft-data`、`sft-checkpoint`、`preference-data`、`reward-model`、`aligned-checkpoint`、`eval-dataset`、`eval-harness`、`eval-results`、`deployment-artifact`。
