# 报告格式

按以下结构生成 Markdown 报告。省略没有候选的分节和没有值的可选字段。

```markdown
# AI 开源模型观察｜YYYY-MM-DD — YYYY-MM-DD

本期关注：旗舰模型 N 项、热门或重点本地模型 N 项、可复现项目 N 项、热门或重点数据集 N 项。

## 一、重点旗舰模型

### LLM

#### 1. 模型名称

- 窗口信号：新发布 | 仓库更新
- 属性：架构、参数规模和主要能力。
- 时间：YYYY-MM-DD
- 链接：[Hugging Face](https://huggingface.co/...)

其他模型角色使用相同字段。

## 二、热门本地部署模型

### 1. 模型名称

- 关注：当前 HF 热门或重点白名单。
- 原模型：canonical model ID
- 部署：GGUF | MLX | Ollama | Quantized | On-device
- 规模：HF 结构化字段提供的参数量。
- 热度：TrendingScore N · 下载 N · 点赞 N
- 窗口信号：新发布 | 仓库更新
- 时间：YYYY-MM-DD
- 链接：[Hugging Face](https://huggingface.co/...)

## 三、重点可复现项目

### 1. 项目名称

- 窗口信号：本窗口内新增或更新的交付件。
- 开放范围：完整链路 | 预训练 | 后训练 | 部分交付
- 时间：YYYY-MM-DD
- 链接：[Hugging Face](https://huggingface.co/...)

| 阶段 | 本期交付件 | 状态 |
| --- | --- | --- |
| 数据 | 数据集或数据处理仓库 | 新增 / 更新 |
| 训练 | recipe、config 或训练代码 | 新增 / 更新 |
| 模型 | checkpoint 或 aligned model | 新增 / 更新 |
| 评测 | eval dataset、harness 或 results | 新增 / 更新 |
| 部署 | 部署交付件 | 新增 / 更新 |

## 四、热门或重点数据集

### 1. 数据集名称

- 关注：当前 HF 热门或重点白名单。
- 用途：预训练 | SFT | Preference | 蒸馏 | 评测
- 关联：相关模型或可复现项目。
- 规模：HF 明确提供的数据规模。
- 热度：TrendingScore N · 下载 N · 点赞 N
- 窗口信号：新发布 | 仓库更新
- 时间：YYYY-MM-DD
- 链接：[Hugging Face](https://huggingface.co/datasets/...)
```

字段规则：

- `窗口信号` 只写候选和 HF 页面支持的事实，不把 `lastModified` 扩写为版本发布。
- `关注` 按候选的 `selection` 写为“HF 热门”或“HF 热门 · 重点白名单”。
- 参数规模只使用 HF 结构化字段，不从模型名推断。
- 没有明确原模型时省略“原模型”。
- `lastModified` 命中时间窗口时只写“仓库更新”，不推断具体变更。
- 可复现项目表格只列本窗口内新增或更新的阶段。
- 最终报告不展示采集状态、原始 tags、分类过程或待确认候选。
- 本地模型和数据集按重点标记、TrendingScore、点赞和下载量排序。

全部分节为空时输出：

```markdown
# AI 开源模型观察｜YYYY-MM-DD — YYYY-MM-DD

本时间窗口内没有热门或重点的模型与数据集更新。
```
