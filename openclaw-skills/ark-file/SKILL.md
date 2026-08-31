---
name: ark-file
description: 使用标准火山方舟 Files API 上传、列出、查询、等待和删除可供多模态模型引用的文件。适用于管理图片、视频、PDF、音频的完整生命周期，或在调用 Ark/Agent Plan 模型前把本地媒体转换为 file_id。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-file
metadata: {"openclaw":{"skillKey":"ark-file","emoji":"📁","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-file","requires":{"anyBins":["python3","python"],"env":["ARK_API_KEY"]},"primaryEnv":"ARK_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"requests>=2.32,<3"}]}}
---

# Ark File

Manage inference files with the standard Ark Files API and `ARK_API_KEY`.

## Optional Reads

- Read [references/ark-file.md](references/ark-file.md) for supported formats, lifecycle, model-consumption shapes, limits, or billing boundaries.
- Run `scripts/ark_file.py --help` only when exact flags are needed.

## Commands

```bash
python3 {baseDir}/scripts/ark_file.py upload ./document.pdf
python3 {baseDir}/scripts/ark_file.py list
python3 {baseDir}/scripts/ark_file.py retrieve file-20260101000000-example
python3 {baseDir}/scripts/ark_file.py wait file-20260101000000-example
python3 {baseDir}/scripts/ark_file.py delete file-20260101000000-example
```

## Contract

1. Use only `ARK_API_KEY` and `https://ark.cn-beijing.volces.com/api/v3/files`. Agent Plan keys cannot create or manage files.
2. Upload local `user_data` files only. The script validates the documented image, video, PDF, and audio extensions before sending bytes.
3. `upload` waits for `active` by default. Use the returned `id` only after success; use `--no-wait` only when the caller will run `wait` separately.
4. Reuse one active `file_id` across compatible Ark API and same-account Agent Plan inference calls until it expires. Do not upload the same bytes for every question.
5. Treat delete as destructive. Run it only when the user explicitly asks to delete the file or cleanup is already part of the authorized workflow.
6. Treat stdout JSON as the lifecycle result. Treat non-zero exit or stderr JSON as failure. An empty Ark list response is normalized to `data: []`.
