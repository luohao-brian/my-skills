# Ark Vision Reference

## Backends

| `--backend` | Credential | Endpoint | Model |
| --- | --- | --- | --- |
| `ark-agent-plan` (default) | `ARK_AGENT_PLAN_API_KEY` | `https://ark.cn-beijing.volces.com/api/plan/v3/chat/completions` | `doubao-seed-2.0-lite` |
| `ark-api` | `ARK_API_KEY` | `https://ark.cn-beijing.volces.com/api/v3/chat/completions` | `doubao-seed-2-0-lite-260428` |

Endpoints and models are fixed. The script does not fall back between backends.

Each backend also supports its Mini variant (`doubao-seed-2.0-mini` or
`doubao-seed-2-0-mini-260428`) through `--model`.

The request uses OpenAI-compatible Chat Completions with one user message and provider-native content blocks.

- `{"type":"image_url","image_url":{"url":"..."}}` for image URL/data URL
- `{"type":"video_url","video_url":{"url":"..."}}` for video URL/data URL
- `{"type":"file","file":{"file_data":"data:application/pdf;base64,...","filename":"document.pdf"}}` for inline PDF
- `{"type":"image_url","image_url":{"file_id":"file-..."}}` for uploaded images
- `{"type":"video_url","video_url":{"file_id":"file-..."}}` for uploaded videos
- `{"type":"file","file":{"file_id":"file-..."}}` for uploaded PDFs
- `{"type":"text","text":"..."}`

The script keeps image and video inputs as distinct native media blocks. It does not turn a video into frames, an image, audio, or a transcript. This matches the latest `../my-cowork` visual/video fix: both capabilities share the request core, but media identity stays explicit.

## Input routing

| Input | Preferred transport |
| --- | --- |
| Reusable local image/video/PDF | upload with `ark-file`, wait for `active`, pass `file_id` |
| Small one-off local media | bounded data URL |
| HTTP(S) image/video | pass unchanged |
| Ambiguous signed URL | add `--media-type` |
| Agent Plan inference with uploaded file | upload using `ARK_API_KEY`, infer using `ARK_AGENT_PLAN_API_KEY` |

Agent Plan cannot call `/files`; it can consume same-account file IDs created by the standard Ark API. File upload is a transport step, not an automatic inference-backend fallback.

## Usage

```bash
python3 {baseDir}/scripts/vision_analyze.py ./ui.png "这个界面里有哪些按钮？"
python3 {baseDir}/scripts/vision_analyze.py ./ui.png "这个界面里有哪些按钮？" --backend ark-api
python3 {baseDir}/scripts/vision_analyze.py ./chart.png "提取图表标题、坐标轴和主要趋势" --json
python3 {baseDir}/scripts/vision_analyze.py "data:image/png;base64,..." "图片里是什么？"
python3 {baseDir}/scripts/vision_analyze.py ./clip.mp4 "总结视频中的动作和变化"
python3 {baseDir}/scripts/vision_analyze.py https://example.com/clip.mp4 "总结视频中的动作和变化"
python3 {baseDir}/scripts/vision_analyze.py ./document.pdf "解释文档结论"
python3 {baseDir}/scripts/vision_analyze.py file-20260101000000-example "解释这个文件" --media-type pdf
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
  "media": "./ui.png"
}
```

On failure, the script writes JSON to stderr with `success:false`, `error`, and `model`.

## Boundaries

- Local inline image limit: 20 MB.
- Local inline video/PDF limit: 50 MB. Use `ark-file` above that size.
- File IDs must be `active`. With `ARK_API_KEY`, the script retrieves metadata and rejects non-active files before inference.
- Remote URLs with no recognizable suffix need `--media-type` because signed URLs often hide the original extension.

## Official documentation

- https://docs.volcengine.com/docs/82379/1362931?lang=zh
- https://docs.volcengine.com/docs/82379/1895586?lang=zh
- https://docs.volcengine.com/docs/82379/1902647?lang=zh
- https://docs.volcengine.com/docs/82379/1885708?lang=zh
