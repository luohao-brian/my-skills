# 报告格式

按以下结构生成 Markdown 报告。省略没有候选的分节和没有值的可选字段。

```markdown
# AI 开源模型观察｜YYYY-MM-DD — YYYY-MM-DD

本期关注：旗舰模型 N 项、热门衍生与本地部署模型 N 项、可复现项目 N 项、热门或重点数据集 N 项、重点新发现 N 项。

## 一、重点旗舰模型

### LLM

#### 1. 模型名称

- 窗口信号：新发布 | 仓库更新
- 规模：HF 结构化字段提供的权重参数量。
- 架构：MoE / Diffusion 等结构化架构类型、config 中的架构类；model card 有明确架构说明时补充一句。
- 评测表现（模型卡报告）：概括评测条件、代表性基准、对照模型和结果；有局限说明时一并写出。
- 资料：[技术论文](https://arxiv.org/abs/...) · [HF Paper](https://huggingface.co/papers/...)。
- 发布摘要：新发布时，根据 model card 用 1–2 句概括当前能力、用途和主要交付件。
- 更新摘要：仓库更新时，根据本窗口提交记录概括具体变化；证据不足时明确只能确认的文件或提交标题。
- 时间：YYYY-MM-DD
- 链接：[Hugging Face](https://huggingface.co/...)

其他模型角色使用相同字段。

## 二、热门衍生与本地部署模型

### 1. 模型名称

- 关注：当前 HF 热门或重点白名单。
- 原模型：canonical model ID
- 衍生：Merge | Finetune | Adapter | Quantized
- 部署：GGUF | MLX | Ollama | Quantized | On-device
- 规模：HF 结构化字段提供的参数量。
- 热度：TrendingScore N · 下载 N · 点赞 N；有趋势快照时可补充排名和相对上次的变化。历史运行省略。
- 窗口信号：新发布 | 仓库更新 | 当前热门
- 状态摘要：根据 model card 概括当前模型定位、用途或组成，不把当前状态写成本窗口变化。
- 评测表现（模型卡报告）：优先说明当前量化/衍生版本自身的评测设置与结果，以及相对原模型或同条件量化基线的保留率；没有同条件证据时不做跨模型比较。
- 更新摘要：仅新发布或仓库更新时写；仓库更新须以本窗口提交记录为依据。
- 变体：注册表显式声明同一 `variant_group` 后折叠出的其他仓库；没有 `metadata.variants` 时省略。
- 时间：YYYY-MM-DD
- 链接：[Hugging Face](https://huggingface.co/...)

## 三、重点可复现项目

### 1. 项目名称

- 窗口信号：本窗口内新增或更新的交付件。
- 开放范围：完整链路 | 预训练 | 后训练 | 部分交付
- 更新摘要：用 1–2 句概括本窗口交付件的实际提交；若只有依赖、CI、文档等维护性变更，直接说明，不把它包装成训练或评测能力升级。
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
- 更新摘要：仓库更新时，根据本窗口提交记录说明新增或修改了什么；提交信息只有“Update README.md”时只写“更新数据集说明文档，公开提交说明未披露更细变化”。
- 资料：[技术论文](https://arxiv.org/abs/...) · [HF Paper](https://huggingface.co/papers/...)。
- 时间：YYYY-MM-DD
- 链接：[Hugging Face](https://huggingface.co/datasets/...)

## 五、本周重点新发现

本节只展示 `groups.notable_discoveries`，模型与数据集合计 8–12 条；实际候选不足时按实展示。

### 模型

#### 1. 模型名称

- 状态：待纳入注册表
- 方向：LLM | VLM | 图像生成 | 视频生成 | 语音 | OCR | 翻译 | Embedding | Robotics | 待确认
- 窗口信号：新发布 | 仓库更新
- 规模：HF 结构化字段提供的权重参数量。
- 架构：MoE / Diffusion 等结构化架构类型、config 中的架构类；model card 有明确架构说明时补充一句。
- 评测表现（模型卡报告）：概括评测条件、代表性基准、对照模型和结果；有局限说明时一并写出。
- 资料：[技术论文](https://arxiv.org/abs/...) · [HF Paper](https://huggingface.co/papers/...)。
- 为什么关注：根据 model card 用 1–2 句概括能力、用途和主要交付件。
- 更新摘要：仅仓库更新时，根据本窗口提交记录概括具体变化。
- 时间：YYYY-MM-DD
- 链接：[Hugging Face](https://huggingface.co/...)

### 技术数据与热门新数据集

#### 1. 数据集名称

- 状态：主要厂商技术数据 | 热门新数据集 · 待纳入注册表
- 热度：TrendingScore N · 下载 N · 点赞 N；未包含 `hot` 时可省略。
- 窗口信号：新发布 | 仓库更新
- 用途与内容：根据 dataset card 用 1–2 句概括任务、数据内容或规模。
- 更新摘要：仅仓库更新时，根据本窗口提交记录概括具体变化。
- 资料：[技术论文](https://arxiv.org/abs/...) · [HF Paper](https://huggingface.co/papers/...)。
- 时间：YYYY-MM-DD
- 链接：[Hugging Face](https://huggingface.co/datasets/...)
```

字段规则：

- `窗口信号` 只写候选和 HF 页面支持的事实，不把 `lastModified` 扩写为版本发布。
- `当前热门` 只表示观察日仍满足热门条件，不写成“本周发布”“本周更新”或“热度上升”；只有 `metadata.trend` 的非空增量才能支持趋势变化表述。
- `关注` 按候选的 `selection` 写为“HF 热门”“HF 热门 · 重点白名单”或“重点白名单”；历史运行不写实时热度与趋势变化。
- `方向` 只根据 `metadata.modalities` 和 `metadata.role_evidence` 写；没有完整结构化输入/输出时保留“待确认”，不根据模型名或 model card 宣传语猜测。
- 正式数据集含 `technical-artifact` 时可写“重点技术资产”，不把它描述成 HF 热门；重点新发现含 `trusted-publisher` 但不含 `hot` 时写“主要厂商技术数据”。
- 参数规模只使用 HF 结构化字段，不从模型名推断。
- 参数规模写成“HF 权重参数量”，避免把仓库权重总量误写成激活参数量或整个多模块系统的总规模；`scale.inherited` 为 `true` 时注明继承自原模型。
- 架构类型只使用 `metadata.architecture`、`metadata.architecture_classes` 和 `card.architecture_excerpt`；架构类是实现类名，不自行扩写成论文中的结构结论。
- 论文链接只使用 `metadata.papers`，同时给出 arXiv 与 HF Paper；没有结构化 `arxiv:` tag 时省略，不按模型名搜索补猜。
- 评测只使用 `card.evaluation` 中的模型卡证据，写成“模型卡报告”或“发布方报告”，不包装成独立第三方结论。
- 评测摘要优先回答四项：评测对象/量化版本、评测工具与硬件或推理模式、覆盖的能力类别、最有说明力的结果与同条件基线。原文缺少某项时不补猜。
- `card.evaluation.caveats` 包含“未完整评测”、内部基准、小样本、未发布 harness、仅验证单一量化版本等边界时，必须在同一条“评测表现”中说明。
- 只有同一模型卡明确声明相同评测工具、数据、解码和评分设置时才比较模型或量化版本；不同模型卡的分数不得直接横比。
- HF 热门由 TrendingScore、下载和点赞支持；评测结果用于解释模型的技术吸引力，不得无来源写成热度的因果原因。
- 没有明确原模型时省略“原模型”。
- 没有结构化衍生关系或本地部署格式时，分别省略“衍生”或“部署”；不得从仓库名猜测。
- `lastModified` 命中时间窗口时只确定“仓库更新”；具体变更只从 `change_evidence.commits` 概括。
- 可复现项目表格只列本窗口内新增或更新的阶段。
- GitHub 子目录交付件只有该路径在本窗口有提交时才列为更新；同仓库其他路径的提交不得倒灌。
- `change_evidence.ok` 为 `false` 或提交列表为空时，不猜测具体变化；写“只能确认仓库时间戳更新，未取得可核验的提交摘要”。
- 提交标题宽泛时保持证据粒度，例如只写“更新 README”或“上传文件”；不得用 model card 的当前内容反推该提交新增了什么。
- `card.excerpt` 必须改写成中文摘要，不长段引用；只写片段明确支持的能力、用途和交付件。
- 仓库更新时，model/dataset card 只提供当前背景或状态摘要，不得据此声称这些能力、数据或交付件在本窗口新增。
- `card.ok` 为 `false` 或片段缺少证据时省略“本期看点”“为什么关注”或“用途与内容”，不根据名称推断。
- 最终报告不展示采集状态、原始 tags、分类过程或顶层发现池。
- 热门衍生/本地部署模型最多 20 条，只折叠注册表显式声明同一 `variant_group` 的变体，再覆盖最多 8 个不同发布者，并保证 Merge、Finetune、Adapter、GGUF、MLX、On-device 和 Quantized 类型覆盖。当前运行最后按 TrendingScore、重点标记、点赞和下载量排序；历史运行按重点标记、窗口事件日期和仓库 ID 排序。数据集按主要厂商/重点技术资产和可用热度排序。

全部分节为空时输出：

```markdown
# AI 开源模型观察｜YYYY-MM-DD — YYYY-MM-DD

本时间窗口内没有热门或重点的模型与数据集更新。
```
