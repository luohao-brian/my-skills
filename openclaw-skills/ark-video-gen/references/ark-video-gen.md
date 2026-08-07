# Ark Video Generation Reference

## API Boundary

- Environment: `ARK_AGENT_PLAN_API_KEY`
- Endpoint: `https://ark.cn-beijing.volces.com/api/plan/v3`
- Model: `doubao-seedance-2.0-fast`
- Official create task contract: https://www.volcengine.com/docs/82379/1520757
- Official get task contract: https://www.volcengine.com/docs/82379/1521309?lang=zh

The script reads no other environment variable. Task timeout and polling are
fixed implementation details.

## Usage

```bash
python3 {baseDir}/scripts/volc_video_gen.py "海边日落，镜头缓慢后退" --duration 5 --aspect-ratio 16:9
python3 {baseDir}/scripts/volc_video_gen.py "女孩微笑着回头" --image ./start.png --duration 5 --resolution 720p
python3 {baseDir}/scripts/volc_video_gen.py "科技产品展示动画" --audio
```

## Generation Settings

- `--duration`: accepts `4`-`15` seconds or `-1` for smart duration; other values fail before submission.
- `--aspect-ratio`: accepts `16:9`, `4:3`, `1:1`, `3:4`, `9:16`, `21:9`, or `adaptive`; defaults to `16:9`.
- `--resolution`: accepts `480p` or `720p` for the fixed Fast model; defaults to `720p`.
- `--audio`: requests generated audio when the model supports it.

The script encodes local reference images as data URLs and passes them as `image_url` content.
It sends `duration`, `ratio`, `resolution`, `watermark`, and `generate_audio`
as provider-native top-level task request fields instead of embedding control flags in the prompt.
It treats `succeeded`, `failed`, `cancelled`, and `expired` as terminal provider states.
