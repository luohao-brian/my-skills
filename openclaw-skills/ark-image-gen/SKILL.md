---
name: ark-image-gen
description: 使用 Ark Agent Plan（默认）或 Ark API 的 Seedream 模型创建图片。适用于文生图、参考图生图、封面、海报草图和需要返回本地图片路径的任务。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-image-gen
metadata: {"openclaw":{"skillKey":"ark-image-gen","emoji":"🎨","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-image-gen","requires":{"anyBins":["python3","python"]},"primaryEnv":"ARK_AGENT_PLAN_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"requests>=2.32,<3"}]}}
---

# Ark Image Generation

Generate images through Ark and save the result locally.

## Optional Reads

- Read [references/ark-image-gen.md](references/ark-image-gen.md) for backend details, sizes, or output fields.
- Read `scripts/volc_image_gen.py --help` only when exact flags are needed.

## Command

```bash
python3 {baseDir}/scripts/volc_image_gen.py "一张 16:9 的未来城市海报" --aspect-ratio 16:9 --resolution 2K
```

With a reference image:

```bash
python3 {baseDir}/scripts/volc_image_gen.py "保留主体，改成水彩风格" --image ./input.png
```

## Contract

1. Use Agent Plan by default. Map explicit user wording `ARK-API` or `方舟 API` to `--backend ark-api`; map `ARK-AGENT-PLAN` or `方舟 Agent Plan` to `--backend ark-agent-plan`. Never switch or retry across backends automatically. See [references/ark-image-gen.md](references/ark-image-gen.md) for credentials and models.
2. Use `--aspect-ratio` and `--resolution` for output dimensions, repeat `--image` for references, and use `--count` only with a Lite model. `--size` remains a compatibility alias.
3. Use `--model` only with a model listed for the selected backend. Seedream 5.0 Pro is Ark API-only, single-image, and supports 1K/1.5K/2K; Lite supports 2K/3K/4K and up to 15 images.
4. Expect stdout JSON with `success`, `backend`, `images`, `local_path`, `remote_url`, `model`, `count`, `aspect_ratio`, `resolution`, and `size`.
5. A response with no downloaded local image is a failed call.
