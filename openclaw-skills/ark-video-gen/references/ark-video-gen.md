# Ark Video Generation Reference

## Backends

| `--backend` | Credential | Endpoint | Model |
| --- | --- | --- | --- |
| `ark-agent-plan` (default) | `ARK_AGENT_PLAN_API_KEY` | `https://ark.cn-beijing.volces.com/api/plan/v3` | `doubao-seedance-2.0-fast` |
| `ark-api` | `ARK_API_KEY` | `https://ark.cn-beijing.volces.com/api/v3` | `doubao-seedance-2-5-260628` |

Agent Plan also supports `doubao-seedance-2.0`. Ark API also supports
`doubao-seedance-2-0-fast-260128`, `doubao-seedance-2-0-mini-260615`, and
`doubao-seedance-2-0-260128`. Use `--model` to select one; the script does not
fall back between backends.
Task timeout and polling are implementation details.

- Official create task contract: https://www.volcengine.com/docs/82379/1520757
- Official get task contract: https://www.volcengine.com/docs/82379/1521309?lang=zh

## Usage

```bash
python3 {baseDir}/scripts/volc_video_gen.py "海边日落，镜头缓慢后退" --duration 5 --aspect-ratio 16:9
python3 {baseDir}/scripts/volc_video_gen.py "海边日落，镜头缓慢后退" --backend ark-api
python3 {baseDir}/scripts/volc_video_gen.py "女孩微笑着回头" --image ./start.png --duration 5 --resolution 720p
python3 {baseDir}/scripts/volc_video_gen.py "科技产品展示动画" --audio
```

## Generation Settings

- `--duration`: Seedance 2.5 accepts `4`-`30` seconds or `-1`; other models accept `4`-`15` seconds or `-1`.
- `--aspect-ratio`: accepts `16:9`, `4:3`, `1:1`, `3:4`, `9:16`, `21:9`, or `adaptive`; defaults to `16:9`.
- `--resolution`: Seedance 2.5/Fast/Mini accept `480p` or `720p`; full 2.0 also accepts `1080p` and `4k`.
- `--audio`: requests generated audio when the model supports it.

The script encodes local reference images as data URLs and passes them as `image_url` content.
Ark API sends `duration`, `ratio`, `resolution`, `watermark`, and
`generate_audio` as top-level fields. Agent Plan keeps only `generate_audio`
top-level and appends `--dur`, `--ratio`, and `--rs` to the text prompt.
It treats `succeeded`, `failed`, `cancelled`, and `expired` as terminal provider states.
