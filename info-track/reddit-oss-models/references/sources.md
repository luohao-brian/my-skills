# 开源更新来源与分类

## 来源

- Reddit weekly RSS：`r/LocalLLaMA`、`r/unsloth`。
- GitHub：`https://github.com/trending?since=weekly`，仅保留 AI、Agent、LLM、模型、生成式 AI 和开发工具相关仓库。
- Hugging Face Models：按 `trendingScore` 获取，并补充 AllenAI、EleutherAI、Swiss AI、LLM360、TII 等真开放组织的近期模型。
- Hugging Face Datasets：按 `trendingScore` 获取热门数据集。

可通过 `AI_WEEKLY_HF_API_BASES` 或 `HF_API_BASES` 指定逗号分隔的 Hugging Face API 基址；默认依次尝试 `huggingface.co` 与 `hf-mirror.com`。

## 模型分类

- `开放权重旗舰 / reasoning`：通用大模型、MoE、reasoning、coding 和 Agent 旗舰模型。
- `本地推理 / 量化生态`：GGUF、quant、MLX、Ollama、推理加速与压缩。
- `真开放 / 可复现训练`：开放训练 recipe、数据透明或可复现训练生态。
- `小模型 / 专门模型`：翻译、OCR、语音、医疗、生物、代码专项和 embedding 等。
- `多模态 / 图像视频`：VLM、图像、视频、语音及多模态生成或理解。
- `-misc`：无法可靠归入上述类别；最终周报丢弃。
