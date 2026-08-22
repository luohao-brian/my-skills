# Ark Vision Reference

## Backends

| `--backend` | Credential | Endpoint | Model |
| --- | --- | --- | --- |
| `ark-agent-plan` (default) | `ARK_AGENT_PLAN_API_KEY` | `https://ark.cn-beijing.volces.com/api/plan/v3/chat/completions` | `doubao-seed-2.0-lite` |
| `ark-api` | `ARK_API_KEY` | `https://ark.cn-beijing.volces.com/api/v3/chat/completions` | `doubao-seed-2-0-lite-260428` |

Endpoints and models are fixed. The script does not fall back between backends.

Each backend also supports its Mini variant (`doubao-seed-2.0-mini` or
`doubao-seed-2-0-mini-260428`) through `--model`.

The request uses OpenAI-compatible Chat Completions with one user message and:

- `{"type":"image_url","image_url":{"url":"..."}}` for images
- `{"type":"video_url","video_url":{"url":"..."}}` for remote video URLs
- `{"type":"text","text":"..."}`

## Usage

```bash
python3 {baseDir}/scripts/vision_analyze.py ./ui.png "这个界面里有哪些按钮？"
python3 {baseDir}/scripts/vision_analyze.py ./ui.png "这个界面里有哪些按钮？" --backend ark-api
python3 {baseDir}/scripts/vision_analyze.py ./chart.png "提取图表标题、坐标轴和主要趋势" --json
python3 {baseDir}/scripts/vision_analyze.py "data:image/png;base64,..." "图片里是什么？"
python3 {baseDir}/scripts/vision_analyze.py https://example.com/clip.mp4 "总结视频中的动作和变化"
```

## Output

Plain mode prints only the analysis text.

JSON mode prints:

```json
{
  "success": true,
  "type": "vision",
  "backend": "ark-agent-plan",
  "media_type": "image",
  "analysis": "图片主体是...",
  "model": "doubao-seed-2.0-lite",
  "image": "./ui.png"
}
```

On failure, the script writes JSON to stderr with `success:false`, `error`, and `model`.
