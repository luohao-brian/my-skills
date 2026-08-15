# Ark Vision Reference

## Backends

| `--backend` | Credential | Endpoint | Model |
| --- | --- | --- | --- |
| `ark-agent-plan` (default) | `ARK_AGENT_PLAN_API_KEY` | `https://ark.cn-beijing.volces.com/api/plan/v3/responses` | `doubao-seed-2-0-lite` |
| `ark-api` | `ARK_API_KEY` | `https://ark.cn-beijing.volces.com/api/v3/responses` | `doubao-seed-2-0-lite-260428` |

Endpoints and models are fixed. The script does not fall back between backends.

- Official Responses API quick start: https://www.volcengine.com/docs/82379/1795150?lang=zh
- Official response object: https://www.volcengine.com/docs/82379/1783703?lang=zh

The request contains one user message with `type:message` and:

- `{"type":"input_image","image_url":"..."}` for images
- `{"type":"input_video","video_url":"..."}` for remote video URLs
- `{"type":"input_text","text":"..."}`

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
  "model": "doubao-seed-2-0-lite",
  "image": "./ui.png"
}
```

On failure, the script writes JSON to stderr with `success:false`, `error`, and `model`.
