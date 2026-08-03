---
name: ark-image-gen
description: 使用 Ark Agent Plan Seedream 图像生成接口创建或参考图片生成新图。适用于文生图、轻量图生图、封面图、海报草图、视觉资产生成和需要返回本地图片路径的任务。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-image-gen
metadata: {"openclaw":{"skillKey":"ark-image-gen","emoji":"🎨","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-image-gen","requires":{"anyBins":["python3","python"],"env":["ARK_AGENT_PLAN_API_KEY"]},"primaryEnv":"ARK_AGENT_PLAN_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"requests>=2.32,<3"}]}}
---

# Ark Agent Plan Image Generation

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

1. The script reads only `ARK_AGENT_PLAN_API_KEY` and uses the fixed Agent Plan endpoint and `doubao-seedream-5.0-lite` model.
2. Use `--size` for output dimensions, `--image` for a local/data-URL reference, and `--output` for the desired local path; the script corrects its suffix to the returned media type.
3. Expect stdout JSON with `success`, `local_path`, `remote_url`, `model`, `prompt`, and `size`.
4. A response with no image is a failed call.
