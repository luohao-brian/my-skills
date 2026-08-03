# Ark Video Generation Reference

## API Boundary

- Environment: `ARK_AGENT_PLAN_API_KEY`
- Endpoint: `https://ark.cn-beijing.volces.com/api/plan/v3`
- Model: `doubao-seedance-2.0-fast`

The script reads no other environment variable. Task timeout and polling are
fixed implementation details.

## Usage

```bash
python3 {baseDir}/scripts/volc_video_gen.py "海边日落，镜头缓慢后退" --duration 5 --aspect-ratio 16:9
python3 {baseDir}/scripts/volc_video_gen.py "女孩微笑着回头" --image ./start.png --duration 5 --resolution 720p
python3 {baseDir}/scripts/volc_video_gen.py "科技产品展示动画" --audio
```

## Generation Settings

- `--duration`: accepts 5-12 seconds; other values fail before submission.
- `--aspect-ratio`: defaults to `16:9`.
- `--resolution`: defaults to `720p`.
- `--audio`: requests generated audio when the model supports it.

The script encodes local reference images as data URLs and passes them as `image_url` content.
