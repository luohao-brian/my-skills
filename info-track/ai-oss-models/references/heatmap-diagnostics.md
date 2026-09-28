# 覆盖诊断与热力图

覆盖图回答六条模型主干、本地衍生、ComfyUI 工作流和本地开发入口各有哪些候选。VLA 主干基线是当前状态参照，不计入窗口模型数。所有计数来自完整 `--output` 的 `diagnostics` 和 `groups`。

## 诊断顺序

1. 分别看 `sources.huggingface_models`、`github_tools`、`huggingface_development_datasets` 的 `ok`、`count`、`selected`、`errors`。三者是不同实体，不比较入选率。
2. 看 `owner_candidates`、`local_filter_candidates`、`modality_query_candidates`、`media_ecosystem_candidates`、全局 Trending 和最近更新池。查询池会重叠；只有 `open_candidate_union` 是去重的模型候选并集。
3. 看 `coverage.models_by_group_and_role`。列使用 `llm`、`vlm`、`decision`、`media-conditioning`、`media-enhancement`、图像、视频、音频、TTS、ASR 等固定方向；结构化证据不足时保留 `unknown`。
4. 看 `coverage.unique_model_repositories` 得到跨分节去重数。`flagship`、`local`、`notable_discoveries`、`media_customization` 可以包含同一仓库，不能把行总数直接相加。
5. 看 `media_customization_by_capability` 与各候选的 `media_customization.lanes`，确认素材控制、图生视频、角色动画、音频驱动和编辑收尾是否被覆盖。另看 `media_open_activity_selected` 与 `activity_density.signals`，不要把活动条件解释为模型质量。
6. 看 `groups.development` 的工具和数据集窗口事件，再按 `development_baselines` 的方法检查 SFT、蒸馏、DPO/GRPO 是否有训练入口。基线数量和窗口更新数分开显示。
7. 看 `canonical_trace_statuses` 和 `canonical_trace_fetch_errors`，区分已追溯到结构化终点、无父仓字段、多父分叉和父仓读取失败。再从候选 `canonical_model_trace.hops` 检查衍生线主模型与更远 `root_model`；注册表声明与路径不一致时列为核对项，不自动改写成一致。

## 可用图表

- 召回漏斗：查询通道 → 去重候选并集 → 四个正式分节的入选数。
- 模型覆盖矩阵：行是 `flagship | local | notable_discoveries | media_customization`；列是结构化模型方向。每行标注样本量，小于 5 的行标“小样本”。
- 本地部署矩阵：行是本地模型；列是 GGUF、MLX、量化、Ollama-compatible、on-device、ComfyUI、Diffusers 等已有 `deployment` 值。
- ComfyUI 工作流矩阵：行是候选模型；前六列是 `media-conditioning`、`image-to-video`、`character-animation`、`audio-driven-avatar`、`video-editing-effects`、`media-enhancement`；再按具体能力展开 mask、姿态、运动、深度、人脸分析、换脸、对口型、超分和补帧等。活动信号用独立布尔列展示，不合成颜色强度。
- 本地开发矩阵：行是精确登记的工具或数据集；列是 SFT、LoRA/QLoRA、蒸馏、DPO/GRPO 和所属模型主干。窗口更新单独标记，不把“项目支持方法”解释为“当前单卡已跑通”。

采集失败单独显示失败状态，不绘制为零覆盖。不从模型名称补齐未知方向或能力，不将 TrendingScore、下载和点赞跨任务相加。
