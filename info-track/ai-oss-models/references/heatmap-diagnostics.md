# 覆盖诊断与热力图

AI 开源模型分析回答“召回链路与正式入选结果覆盖了哪些方向和交付环节”。Hugging Face Models、Hugging Face Datasets 与 GitHub Projects 对应不同实体类型，绝对数量不能组成来源贡献排名。

## 诊断顺序

1. 先看 `sources` 的 `ok`、`count`、`selected` 和 `errors`，分别判断模型、数据集与工程交付件的采集健康；不比较三者的入选率。
2. 使用顶层 `diagnostics` 检查召回漏斗。owner、local filter、模态查询、媒体生态和全局榜单会互相重叠，只有 `open_candidate_union` 是模型候选并集，查询通道数量不得直接相加。
3. 使用 `diagnostics.coverage` 检查正式入选结果。模型方向只来自结构化字段；`unknown` 必须保留，不能按模型名称补猜。
4. `models_by_group_and_role` 的展示分组可能重叠；跨组总量使用 `unique_model_repositories`。数据集使用 `datasets_by_group.unique_repositories`。
5. 可复现项目直接使用每个项目的 `metadata.coverage` 生成“项目 × 数据/训练/模型/评测/部署”布尔矩阵；聚合计数使用 `reproducible_by_component`。
6. 媒体雷达把能力覆盖与活动密度分开看：能力矩阵说明本窗口发现了什么，`media_open_activity_selected` 和每条 `activity_density.signals` 说明哪些候选独立满足透明活动条件。两者都不表示下游系统是否已经覆盖或是否应当验证。

## 可用图表

- 召回漏斗：展示各查询通道、候选并集和正式入选数。这是流程图或漏斗图，不是来源热力图。
- 模型覆盖热力图：行是 `flagship | local | notable_discoveries | media_customization`，列是固定模型方向，单元格来自 `models_by_group_and_role`；每行单独归一化并标注样本量。
- 本地部署矩阵：行是入选本地模型，列是 GGUF、MLX、量化、Ollama-compatible、on-device、ComfyUI、Diffusers 等结构化 `deployment` 值。
- ComfyUI 后图像媒体矩阵：行是模型，列先按 `media_customization.lanes` 和具体能力展开，再用独立布尔列展示 open-activity、high-trending、recent-repository-activity、high-download-velocity、high-like-velocity、downloads-growing、likes-growing、rank-rising；不将这些信号相加为颜色强度。只使用结构化任务、精确 tag 或 model card 明确信号，不按模型名补列。
- 复现链路矩阵：行是项目，列是数据、训练、模型、评测、部署，使用布尔覆盖，不用 star 或下载量替代开放交付件。

## 禁止解释

- 不生成 Hugging Face Models、Datasets、GitHub Projects 的“来源贡献排名”或“强弱评分”。
- 不把 `count`、TrendingScore、下载、点赞、star 或 fork 跨实体相加。
- 不把查询通道的重叠候选重复计入总量。
- 不把热门、本地部署或低拒绝标签解释为模型质量、安全性或能力强弱。
- 不把媒体能力覆盖或高活动解释为下游系统缺口、升级建议或验证结论；这些判断属于消费报告的验证平台。
- 小于 5 个正式样本的行标注“小样本”；采集失败显示失败状态，不绘制为零覆盖。
