# Ark Vision Reference

## Environment

Required:

- `ARK_AGENT_PLAN_API_KEY`

The script reads only `ARK_AGENT_PLAN_API_KEY` for authentication.

Optional:

- `VOLC_ARK_BASE_URL`: defaults to `https://ark.cn-beijing.volces.com/api/plan/v3`
- `VOLC_VISION_MODEL_ID`: defaults to `doubao-seed-2.0-lite`

## API Boundary

Use Ark Agent Plan Responses API directly:

```text
POST https://ark.cn-beijing.volces.com/api/plan/v3/responses
Authorization: Bearer $ARK_AGENT_PLAN_API_KEY
```

The request body uses one user message containing:

- `{"type":"input_image","image_url":"..."}`
- `{"type":"input_text","text":"..."}`

Do not configure or call an MCP server or Hermes plugin for this skill.

## Model

Default model:

- `doubao-seed-2.0-lite`

Use exact Ark model IDs. Do not shorten this to ambiguous aliases such as `doubao-seed-lite` unless a current provider response or official model list confirms that alias is accepted.

Official references:

- Ark image understanding: `https://www.volcengine.com/docs/82379/1362931`
- Ark model list: `https://www.volcengine.com/docs/82379/1330310`
- Agent Plan OpenClaw setup: `https://www.volcengine.com/docs/82379/2183190`

## Usage

```bash
python3 {baseDir}/scripts/vision_analyze.py ./ui.png "这个界面里有哪些按钮？"
python3 {baseDir}/scripts/vision_analyze.py ./chart.png "提取图表标题、坐标轴和主要趋势" --json
python3 {baseDir}/scripts/vision_analyze.py "data:image/png;base64,..." "图片里是什么？" --timeout 60
```

## Output

Plain mode prints only the analysis text.

JSON mode prints:

```json
{
  "success": true,
  "type": "vision",
  "analysis": "图片主体是...",
  "model": "doubao-seed-2.0-lite",
  "image": "./ui.png"
}
```

On failure, the script writes JSON to stderr with `success:false`, `error`, and `model`.
