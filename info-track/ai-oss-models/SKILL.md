---
name: ai-oss-models
description: 筛选连续 7 天内有动向的热门或重点 Hugging Face 开源模型、热门衍生与本地部署模型及数据集，生成旗舰、衍生模型、可复现项目、高质量数据集和重点新发现报告，并用 model card 补充能力与用途。适用于 AI 开源生态周报和指定日期窗口追踪。
metadata: {"openclaw":{"skillKey":"ai-oss-models","emoji":"🧩","homepage":"https://github.com/luohao-brian/my-skills/tree/main/info-track/ai-oss-models","requires":{"bins":["python3"]}}}
---

# AI 开源模型观察

运行采集器生成候选 JSON，并按固定格式生成中文报告。

读取规则：

- 读取候选 JSON 前读取 [references/output-schema.md](references/output-schema.md)。
- 生成报告前读取 [references/format.md](references/format.md)。
- 需要确认分类字段时读取 [references/sources.md](references/sources.md)。

```bash
python3 {baseDir}/scripts/open_source_updates.py --output oss-candidates.json --stats
```

调用合同：

1. 仅使用可选的 `--date YYYY-MM-DD`、`--output` 和 `--stats`；未指定日期时不传 `--date`。
2. 候选 JSON 遵循 [references/output-schema.md](references/output-schema.md)，最终报告遵循 [references/format.md](references/format.md)。
3. 报告必须覆盖 `groups` 中的全部候选；只从 `groups.notable_discoveries` 生成“本周重点新发现”，不直接展开顶层 `discoveries`。

## 时间窗口

- 不传 `--date`：采集截至今天的最近 7 天。
- 传 `--date YYYY-MM-DD`：采集该日起连续 7 天。
- 单次窗口固定为 7 天；不因候选不足改变窗口。

## 执行预算

- 采集器只为最终入选的重点条目并发读取 model card，不为全部发现逐条抓取详情。
- 外部调度器应为完整采集和报告生成预留至少 1500 秒；采集器已复用 owner 查询结果，减少精确仓库请求。

## 可选 Hugging Face 认证

- 公共仓库采集不要求 token。
- 读取 gated model card 前，用户必须先在对应 Hugging Face 页面登录并同意访问条款，再由运行环境通过 `HF_TOKEN` 提供该账号的只读 token。
- 不把 token 写入命令、候选 JSON、报告或仓库文件；`HUGGING_FACE_HUB_TOKEN` 仅作为兼容变量。
