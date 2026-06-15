---
name: image-gen
description: 使用火山引擎 Ark Seedream 图像生成接口创建或参考图片生成新图。适用于文生图、轻量图生图、封面图、海报草图、视觉资产生成和需要返回本地图片路径的任务。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/image-gen
metadata: {"openclaw":{"skillKey":"image-gen","emoji":"🎨","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/image-gen","requires":{"anyBins":["python3","python"],"env":["VOLC_AGENT_PLAN_API_KEY"]},"primaryEnv":"VOLC_AGENT_PLAN_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"requests>=2.32,<3"}]}}
---

# Volcengine Ark Image Generation

Use this skill to call Ark image generation from Python. Keep the entrypoint light and load details only when needed.

## Required Reads

- Read [references/ark-image-gen.md](references/ark-image-gen.md) before generation.
- Read `scripts/volc_image_gen.py --help` only when exact flags are needed.

## Command

```bash
python3 {baseDir}/scripts/volc_image_gen.py "一张 16:9 的未来城市海报" --size 16:9
```

With a reference image:

```bash
python3 {baseDir}/scripts/volc_image_gen.py "保留主体，改成水彩风格" --image ./input.png
```

## Contract

1. Require `VOLC_AGENT_PLAN_API_KEY`; compatibility fallbacks are accepted by the script.
2. Save generated image bytes locally whenever the provider returns bytes or a URL.
3. Return JSON containing `success`, `local_path`, `remote_url` when available, `model`, `prompt`, and `size`.
4. If the provider returns unsupported fields or no image, report the raw response summary.
