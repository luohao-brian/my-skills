# Ark Vision Reference

## API Boundary

- Environment: `ARK_AGENT_PLAN_API_KEY`
- Endpoint: `https://ark.cn-beijing.volces.com/api/plan/v3/responses`
- Model: `doubao-seed-2.0-lite`

The script reads no other environment variable. The request contains one user
message with:

- `{"type":"input_image","image_url":"..."}`
- `{"type":"input_text","text":"..."}`

## Usage

```bash
python3 {baseDir}/scripts/vision_analyze.py ./ui.png "这个界面里有哪些按钮？"
python3 {baseDir}/scripts/vision_analyze.py ./chart.png "提取图表标题、坐标轴和主要趋势" --json
python3 {baseDir}/scripts/vision_analyze.py "data:image/png;base64,..." "图片里是什么？"
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
