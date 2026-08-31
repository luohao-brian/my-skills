---
name: ark-image-gen
description: 使用 Ark Agent Plan（默认）或 Ark API 的 Seedream 模型创建图片。适用于文生图、参考图生图、封面、海报草图和需要返回本地图片路径的任务。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-image-gen
metadata: {"openclaw":{"skillKey":"ark-image-gen","emoji":"🎨","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ark-image-gen","requires":{"anyBins":["python3","python"]},"primaryEnv":"ARK_AGENT_PLAN_API_KEY","install":[{"id":"python-deps","kind":"uv","package":"requests>=2.32,<3"}]}}
---

# Ark Image Generation

通过 Ark 调用 Seedream，并将生成结果保存到本地。

## Optional Reads

- 用户只给出简单想法、需要编写或优化提示词时，读取
  [references/prompt-design.md](references/prompt-design.md)。用户已经提供可直接提交的完整提示词时原样使用。
- 需要确认后端、模型、尺寸、组图或输出字段时，读取
  [references/ark-image-gen.md](references/ark-image-gen.md)。
- 只有需要精确参数时才运行 `scripts/volc_image_gen.py --help`。

## Command

```bash
python3 {baseDir}/scripts/volc_image_gen.py "一只可爱的小狗坐在草地上，抬头看向镜头，周围是自然的户外环境。" --aspect-ratio 1:1 --resolution 2K
```

With a reference image:

```bash
python3 {baseDir}/scripts/volc_image_gen.py "保留主体，改成水彩风格" --image ./input.png
```

Multiple outputs with a Lite model:

```bash
python3 {baseDir}/scripts/volc_image_gen.py "生成三张连贯组图，使用同一只小狗，分别表现坐下、奔跑和趴着休息，保持角色形象和画面风格一致。" --max-images 3
```

Layer decomposition with Pro:

```bash
python3 {baseDir}/scripts/volc_image_gen.py --backend ark-api --model doubao-seedream-5-0-pro-260628 --image ./poster.png --layer-decomposition
```

## Contract

1. Agent Plan is the default. Map explicit user wording `ARK-API` or `方舟 API` to `--backend ark-api`; map `ARK-AGENT-PLAN` or `方舟 Agent Plan` to `--backend ark-agent-plan`. Never switch or retry across backends automatically.
2. Compile an incomplete user request before calling the script. Preserve explicit user details. Add only the missing subject behavior and environment needed to make the request executable; add style, color, lighting, composition, use, or visible text only when the user specifies them. Pass the compiled text as the positional prompt.
3. Use `--aspect-ratio` and `--resolution` for dimensions. Repeat `--image` in input order for references. Use `--max-images` only with a Lite model; `--count` remains a deprecated alias. The number is an API maximum, so the prompt must also state the requested image count.
4. Use only models listed for the selected backend. Lite supports 2K/3K/4K and coherent multi-image output. Pro is Ark API-only, generates one image, and supports 1K/1.5K/2K for normal output. `seed` is not a Pro parameter.
5. For Pro layer decomposition, pass exactly one `--image` with `--layer-decomposition`; the request uses `image`, `layer_decomposition: true`, and `size`. Do not use `layer_image` or `layer_size`.
6. Reference images use HTTP(S) URL or image Base64. A local image is encoded as Base64. Ark Files API `file_id` is not an image-generation URL and must not be placed in `--image`; use `ark-file` only for a separate `ark-vision` analysis step.
7. Expect stdout JSON with `success`, `backend`, `images`, `local_path`, `remote_url`, `model`, `count`, `aspect_ratio`, `resolution`, `size`, `usage`, and `request_id`. A response with no downloaded local image is a failed call.
