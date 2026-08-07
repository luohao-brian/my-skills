# Ark Image Generation Reference

## API Boundary

- Environment: `ARK_AGENT_PLAN_API_KEY`
- Endpoint: `https://ark.cn-beijing.volces.com/api/plan/v3/images/generations`
- Model: `doubao-seedream-5.0-lite`
- Official request contract: https://www.volcengine.com/docs/82379/1541523?lang=zh

The script reads no other environment variable.

## Usage

```bash
python3 {baseDir}/scripts/volc_image_gen.py "极简产品海报" --size 1:1
python3 {baseDir}/scripts/volc_image_gen.py "赛博朋克街景" --size 16:9 --output ./outputs/city.png
python3 {baseDir}/scripts/volc_image_gen.py "改成油画风格" --image ./source.png --size 4:3
```

When `--output` has a suffix that differs from the returned image bytes, the
script corrects the suffix and reports the actual path in `local_path`.

## Size

Use provider-native values when known. The script accepts common aspect labels and converts them to provider `WIDTHxHEIGHT` values:

- `1:1` -> `2048x2048`
- `3:4` -> `1728x2304`
- `4:3` -> `2304x1728`
- `3:2` -> `2496x1664`
- `2:3` -> `1664x2496`
- `16:9` -> `2848x1600`
- `9:16` -> `1600x2848`
- `21:9` -> `3136x1344`
- `2K`, `3K`, `4K` (lowercase input is normalized to the provider spelling)

The default is `2K`, matching the provider-native size format.

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
