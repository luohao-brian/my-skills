# Ark Video Generation Reference

## Environment

Required:

- `ARK_AGENT_PLAN_API_KEY`

The script reads only `ARK_AGENT_PLAN_API_KEY` for authentication.

Optional:

- `VOLC_ARK_BASE_URL`: defaults to `https://ark.cn-beijing.volces.com/api/plan/v3`
- `VOLC_VIDEO_MODEL_ID`: defaults to `doubao-seedance-2.0-fast`
- `VOLC_VIDEO_TIMEOUT`: defaults to `300`
- `VOLC_VIDEO_POLL_SECONDS`: defaults to `5`

## Usage

```bash
python3 {baseDir}/scripts/volc_video_gen.py "海边日落，镜头缓慢后退" --duration 5 --aspect-ratio 16:9
python3 {baseDir}/scripts/volc_video_gen.py "女孩微笑着回头" --image ./start.png --duration 5 --resolution 720p
python3 {baseDir}/scripts/volc_video_gen.py "科技产品展示动画" --no-audio
```

## Generation Settings

- `--duration`: clamped to 5-12 seconds.
- `--aspect-ratio`: defaults to `16:9`.
- `--resolution`: defaults to `720p`.
- Audio generation is requested by default when the model supports it.
- `--no-audio`: disables generated audio.

The script encodes local reference images as data URLs and passes them as `image_url` content, matching the Hermes Ark plugin pattern.
