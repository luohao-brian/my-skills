---
name: ark-vision
description: 使用 Ark Agent Plan 多模态理解模型识别和分析图片，适合需要读取截图、照片、图表、票据、界面或其他本地/远程图片内容并返回文本结论时使用。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-vision
metadata: {"openclaw":{"skillKey":"ark-vision","emoji":"👁️","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-vision","requires":{"anyBins":["python3","python"],"env":["ARK_AGENT_PLAN_API_KEY"]},"primaryEnv":"ARK_AGENT_PLAN_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"requests>=2.32,<3"}]}}
---

# Ark Agent Plan Vision

Use Ark Agent Plan image-understanding models to inspect images and return text analysis for the calling agent.

## Required Reads

- Read [references/ark-vision.md](references/ark-vision.md) before image analysis.
- Read `scripts/vision_analyze.py --help` only when exact flags are needed.

## Credential Boundary

This skill only supports Agent Plan API key authentication:

- `ARK_AGENT_PLAN_API_KEY`

Run `scripts/vision_analyze.py` for every image-understanding request. The script calls Ark Agent Plan Responses API directly with `input_image` plus `input_text`.

## Command

```bash
python3 {baseDir}/scripts/vision_analyze.py ./screenshot.png "总结这张截图里的关键信息"
python3 {baseDir}/scripts/vision_analyze.py https://example.com/chart.png "提取图表里的趋势和主要数字"
python3 {baseDir}/scripts/vision_analyze.py ./receipt.jpg "识别商家、日期、总金额和明细" --json
```

## Parameters

- `image`: local image path, remote URL, or data URL.
- `question`: question or extraction instruction for the image.
- `--model`: defaults to `doubao-seed-2.0-lite`.
- `--json`: print structured JSON instead of plain analysis text.
- `--raw`: include the raw provider response in JSON output.
- `--timeout N`: defaults to `120`.

## Result Handling

1. Treat stdout as the image-analysis result.
2. Treat non-zero exit or stderr JSON as a failed skill call.
3. After a failed call, surface the script error to the calling context. Retry only when the user request requires another attempt, another image, or another model.
