---
name: ark-video-gen
description: 使用 Ark Agent Plan（默认）或 Ark API 的 Seedance 模型创建视频。适用于文生视频、图片转视频、短视频草稿、任务轮询和返回视频 URL 的任务。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-video-gen
metadata: {"openclaw":{"skillKey":"ark-video-gen","emoji":"🎬","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-video-gen","requires":{"anyBins":["python3","python"]},"primaryEnv":"ARK_AGENT_PLAN_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"volcengine-python-sdk[ark]>=5.0.5,<6"}]}}
---

# Ark Video Generation

Use this skill to submit and poll Ark video generation tasks.

## Optional Reads

- Read [references/ark-video-gen.md](references/ark-video-gen.md) for backend details or generation settings.
- Read `scripts/volc_video_gen.py --help` only when exact flags are needed.

## Command

```bash
python3 {baseDir}/scripts/volc_video_gen.py "5 秒电影感镜头，未来城市雨夜，霓虹反光"
```

With a first-frame image:

```bash
python3 {baseDir}/scripts/volc_video_gen.py "镜头缓慢推进，人物转身" --image ./start.png
```

## Contract

1. Use Agent Plan by default. Map explicit user wording `ARK-API` or `方舟 API` to `--backend ark-api`; map `ARK-AGENT-PLAN` or `方舟 Agent Plan` to `--backend ark-agent-plan`. Never switch or retry across backends automatically. See [references/ark-video-gen.md](references/ark-video-gen.md) for credentials and models.
2. Use the selected backend's model catalog. Agent Plan defaults to `doubao-seedance-2.0-fast`; Ark API defaults to `doubao-seedance-2-5-260628`.
3. Encode duration/ratio/resolution as `--dur`, `--ratio`, and `--rs` switches for Agent Plan; send structured task fields for Ark API.
4. Validate model-specific duration and resolution before submission, then poll until success, failure, cancellation, expiry, or timeout.
5. Expect stdout JSON containing `success`, `backend`, `task_id`, `status`, `video_url`, `model`, and generation settings.
6. On timeout, use the last known task status and task id from the script output.
