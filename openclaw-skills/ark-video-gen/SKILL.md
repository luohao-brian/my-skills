---
name: ark-video-gen
description: 使用 Ark Agent Plan（默认）或 Ark API 的 Seedance 模型创建视频。适用于文生视频、首尾帧生视频、图片/视频/音频参考、多镜头与声音提示词、任务轮询和恢复。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-video-gen
metadata: {"openclaw":{"skillKey":"ark-video-gen","emoji":"🎬","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-video-gen","requires":{"anyBins":["python3","python"]},"primaryEnv":"ARK_AGENT_PLAN_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"volcengine-python-sdk[ark]>=5.0.5,<6"}]}}
---

# Ark Video Generation

通过 Ark 调用 Seedance，轮询任务并将视频保存到本地。

## Optional Reads

- 用户只给出简单想法、需要编写或优化提示词、有多镜头、参考素材或声音要求时，读取
  [references/prompt-design.md](references/prompt-design.md)。用户已经提供可直接提交的完整提示词时原样使用。
- 需要确认后端、模型、素材角色、参数边界、任务恢复或输出字段时，读取
  [references/ark-video-gen.md](references/ark-video-gen.md)。
- 只有需要精确参数时才运行 `scripts/volc_video_gen.py --help`。

## Command

```bash
python3 {baseDir}/scripts/volc_video_gen.py "一只可爱的小狗面向镜头，轻轻摇动尾巴。中景固定镜头，小狗保持清晰居中，动作自然连贯。"
```

首帧生视频：

```bash
python3 {baseDir}/scripts/volc_video_gen.py "保持图片1中的人物外形和场景。人物转身看向镜头，镜头缓慢推进。" --first-frame ./start.png
```

多图参考：

```bash
python3 {baseDir}/scripts/volc_video_gen.py "使用图片1中小狗的外形，参考图片2中的草地环境。小狗向镜头跑来，镜头平稳后退跟拍。" --reference-image ./dog.png --reference-image ./field.png
```

## Contract

1. Agent Plan is the default. Map explicit user wording `ARK-API` or `方舟 API` to `--backend ark-api`; map `ARK-AGENT-PLAN` or `方舟 Agent Plan` to `--backend ark-agent-plan`. Never switch or retry across backends automatically.
2. Compile an incomplete request before calling the script. Preserve explicit details; add only the missing visible action, scene or camera description needed to make a video request executable. Pass the compiled text as the positional prompt. The script does not rewrite it.
3. Agent Plan defaults to `doubao-seedance-2.0-fast`; Ark API defaults to `doubao-seedance-2-5-260628`. Use only models listed for the selected backend.
4. Pass duration, ratio, resolution and audio as structured CLI parameters. Do not append `--dur`, `--ratio` or `--rs` to the prompt. Seedance 2.x does not use `seed` or `camera_fixed`.
5. Use `--first-frame` and `--last-frame` for strict frames. Repeat `--reference-image`, `--reference-video` and `--reference-audio` in the same order used by the prompt. Strict-frame mode and reference mode are mutually exclusive.
6. Music `()`, sound effects `<>`, or dialogue `{}` in a Seedance 2.5 prompt require `--audio`; subtitles `【】` do not require audio.
7. Use `--dry-run` to validate the compiled prompt and payload without credentials or submission. On timeout, use `--resume-task TASK_ID` with the original backend; never create a replacement task automatically.
8. Expect stdout JSON with `success`, `backend`, `task_id`, `status`, remote and local video locations, actual generation settings, usage, request ID, and warnings. A download failure does not erase a successful remote result.
