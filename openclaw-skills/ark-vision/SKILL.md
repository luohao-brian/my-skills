---
name: ark-vision
description: 使用 Ark Agent Plan（默认）或 Ark API 的多模态模型分析图片、视频和 PDF。适用于读取截图、照片、图表、票据、界面、远程或本地视频、PDF，以及消费 Ark Files API 的 file_id。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-vision
metadata: {"openclaw":{"skillKey":"ark-vision","emoji":"👁️","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-vision","requires":{"anyBins":["python3","python"]},"primaryEnv":"ARK_AGENT_PLAN_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"requests>=2.32,<3"}]}}
---

# Ark Vision

Analyze local or remote images, videos, PDFs, and Ark file IDs.

## Optional Reads

- Read [references/ark-vision.md](references/ark-vision.md) for backend, request, or JSON output details.
- Read `scripts/vision_analyze.py --help` only when exact flags are needed.

## Backend

Use Agent Plan by default. Map explicit user wording `ARK-API` or `方舟 API` to `--backend ark-api`; map `ARK-AGENT-PLAN` or `方舟 Agent Plan` to `--backend ark-agent-plan`. Never switch or retry across backends automatically. See [references/ark-vision.md](references/ark-vision.md) for credentials and models.

## File Routing

For a local image, video, or PDF that should be reused, or that is too large to inline, use `ark-file` with `ARK_API_KEY` first, wait for `active`, then pass its `file_id` here. The same-account `file_id` works with either inference backend; this does not switch the selected inference backend. If `ARK_API_KEY` is unavailable, small local media can use the script's bounded data-URL path.

## Command

```bash
python3 {baseDir}/scripts/vision_analyze.py ./screenshot.png "总结这张截图里的关键信息"
python3 {baseDir}/scripts/vision_analyze.py https://example.com/chart.png "提取图表里的趋势和主要数字"
python3 {baseDir}/scripts/vision_analyze.py ./receipt.jpg "识别商家、日期、总金额和明细" --json
python3 {baseDir}/scripts/vision_analyze.py ./clip.mp4 "总结视频中的动作和变化"
python3 {baseDir}/scripts/vision_analyze.py https://example.com/clip.mp4 "总结视频中的动作和变化"
python3 {baseDir}/scripts/vision_analyze.py file-20260101000000-example "总结这份 PDF" --media-type pdf
```

## Parameters

- `media`: local path, remote URL, media data URL, or Ark `file_id`.
- `question`: question or extraction instruction for the media.
- `--media-type`: use `image`, `video`, or `pdf` when a URL or `file_id` is ambiguous. With `ARK_API_KEY`, file metadata normally resolves it automatically.
- `--json`: print structured JSON instead of plain analysis text.
- `--raw`: include the raw provider response in JSON output.
- `--backend`: use `ark-agent-plan` by default or `ark-api` when explicitly requested.
- `--model`: select a Lite or Mini model from the chosen backend's catalog.

## Result Handling

1. Treat stdout as the media-analysis result.
2. Treat non-zero exit or stderr JSON as a failed skill call.
3. After a failed call, surface the script error. Retry only when the user request requires another attempt or another input.
