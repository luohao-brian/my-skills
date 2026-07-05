---
name: video-gen
description: 使用火山引擎 Ark Seedance 视频生成接口创建文生视频或图生视频任务。适用于短视频生成、分镜草稿、图片转视频、视频任务轮询和返回生成视频 URL 的任务。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/video-gen
metadata: {"openclaw":{"skillKey":"video-gen","emoji":"🎬","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/video-gen","requires":{"anyBins":["python3","python"],"env":["ARK_AGENT_PLAN_API_KEY"]},"primaryEnv":"ARK_AGENT_PLAN_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"volcengine-python-sdk[ark]>=5.0.5,<6"}]}}
---

# Volcengine Ark Video Generation

Use this skill to submit and poll Ark video generation tasks.

## Required Reads

- Read [references/ark-video-gen.md](references/ark-video-gen.md) before generation.
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

1. Require `ARK_AGENT_PLAN_API_KEY`; the script does not read any other API key variable.
2. Submit one task, poll until success, failure, or timeout.
3. Return JSON containing `success`, `task_id`, `status`, `video_url`, `model`, and generation settings.
4. If the provider times out, return the last known task status and task id.
