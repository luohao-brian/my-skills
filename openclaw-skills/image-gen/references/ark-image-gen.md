# Ark Image Generation Reference

## Environment

Required:

- `VOLC_AGENT_PLAN_API_KEY`

Accepted compatibility fallbacks:

- `ARK_API_KEY`
- `OPENAPI_API_KEY`

Optional:

- `VOLC_ARK_BASE_URL`: defaults to `https://ark.cn-beijing.volces.com/api/plan/v3`
- `VOLC_IMAGE_MODEL_ID`: defaults to `doubao-seedream-5.0-lite`
- `VOLC_IMAGE_SIZE`: defaults to `2K`

## Usage

```bash
python3 {baseDir}/scripts/volc_image_gen.py "极简产品海报" --size 1:1
python3 {baseDir}/scripts/volc_image_gen.py "赛博朋克街景" --size 16:9 --output-dir ./outputs/images
python3 {baseDir}/scripts/volc_image_gen.py "改成油画风格" --image ./source.png --size 4:3
```

## Size

Use provider-native values when known. The script accepts both common aspect labels and explicit provider size strings:

- `1:1`
- `3:4`
- `4:3`
- `16:9`
- `9:16`
- `21:9`
- `2K`

The default is `2K`, matching the Hermes Ark plugin.

## Output

The script prints JSON:

```json
{
  "success": true,
  "type": "image",
  "local_path": "outputs/images/ark_image_20260615_120000.png",
  "remote_url": "https://...",
  "model": "doubao-seedream-5.0-lite",
  "size": "2K"
}
```
