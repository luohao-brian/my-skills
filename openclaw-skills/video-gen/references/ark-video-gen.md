# Ark Video Generation Reference

## Environment

Required:

- `VOLC_AGENT_PLAN_API_KEY`

Accepted compatibility fallbacks:

- `ARK_API_KEY`
- `OPENAPI_API_KEY`

Optional:

- `VOLC_ARK_BASE_URL`: defaults to `https://ark.cn-beijing.volces.com/api/plan/v3`
- `VOLC_VIDEO_MODEL_ID`: defaults to `doubao-seedance-2.0-fast`
- `VOLC_VIDEO_TIMEOUT`: defaults to `300`
- `VOLC_VIDEO_POLL_SECONDS`: defaults to `5`

## Usage

```bash
python3 {baseDir}/scripts/volc_video_gen.py "海边日落，镜头缓慢后退" --duration 5 --aspect-ratio 16:9
python3 {baseDir}/scripts/volc_video_gen.py "女孩微笑着回头" --image ./start.png --duration 5 --resolution 720p
python3 {baseDir}/scripts/volc_video_gen.py "科技产品展示动画" --audio
```

## Generation Settings

- `--duration`: clamped to 5-12 seconds.
- `--aspect-ratio`: defaults to `16:9`.
- `--resolution`: defaults to `720p`.
- `--audio`: requests generated audio when the model supports it.

The script encodes local reference images as data URLs and passes them as `image_url` content, matching the Hermes Ark plugin pattern.
