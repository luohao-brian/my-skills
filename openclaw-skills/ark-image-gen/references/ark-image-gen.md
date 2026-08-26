# Ark 图片生成参数

## 后端与模型

| `--backend` | 凭证 | Endpoint | 默认模型 |
| --- | --- | --- | --- |
| `ark-agent-plan` | `ARK_AGENT_PLAN_API_KEY` | `https://ark.cn-beijing.volces.com/api/plan/v3/images/generations` | `doubao-seedream-5.0-lite` |
| `ark-api` | `ARK_API_KEY` | `https://ark.cn-beijing.volces.com/api/v3/images/generations` | `doubao-seedream-5-0-260128` |

Ark API 还可使用 `doubao-seedream-5-0-pro-260628`。脚本不在后端之间自动切换或重试。

官方资料：

- 图片生成 API：https://www.volcengine.com/docs/82379/1541523?lang=zh
- Seedream 5.0 Pro 教程：https://www.volcengine.com/docs/82379/2582774?lang=zh
- Pro 交互编辑：https://www.volcengine.com/docs/82379/2582775?lang=zh

## 普通生图

```bash
python3 {baseDir}/scripts/volc_image_gen.py "极简产品海报，画面中央放置一只白色陶瓷杯。" --aspect-ratio 1:1 --resolution 2K
python3 {baseDir}/scripts/volc_image_gen.py "生成三张连贯的城市晨景，保持地点和风格一致。" --max-images 3
python3 {baseDir}/scripts/volc_image_gen.py "单张精细产品图" --backend ark-api --model doubao-seedream-5-0-pro-260628 --resolution 1.5K
```

尺寸规则：

- Lite：`2K`、`3K`、`4K`。
- Pro 普通生图：`1K`、`1.5K`、`2K`，默认 `2K`。
- `--aspect-ratio` 支持 `1:1`、`3:4`、`4:3`、`3:2`、`2:3`、`16:9`、`9:16`、`21:9`。脚本将比例补入提示词，并把分辨率档位原样传给 `size`。
- `--size WIDTHxHEIGHT` 是兼容入口。Pro 自定义尺寸总像素范围为 921600 到 4624220，宽高比范围为 1:16 到 16:1。

组图规则：

- 只有 Lite 支持组图。
- 用 `--max-images` 设置最多返回数量，并在提示词中写明实际需要的数量与各图内容。
- 参考图数量与最多输出数量之和不得超过 15；参考图最多 14 张。
- `--count` 仅作为旧命令兼容别名。

`--web-search` 只用于 Lite。`--output-format` 支持 `png`、`jpeg`；`--response-format` 支持 `url`、`b64_json`。

`seed` 只属于旧的 Seedream 3.0 文生图接口。本脚本支持的 Lite 与 Pro 模型不发送该字段。

## 参考图

`--image` 接受本地路径、HTTP(S) URL 或 Data URL。多图按提示词中的“图一、图二……”顺序重复传入：

```bash
python3 {baseDir}/scripts/volc_image_gen.py "保留图一的主体外形，采用图二的水彩风格。" --image ./subject.png --image ./style.png
```

## Pro 图层拆分

图层拆分只使用 `image`、`layer_decomposition` 和 `size`：

```bash
python3 {baseDir}/scripts/volc_image_gen.py --backend ark-api --model doubao-seedream-5-0-pro-260628 --image ./poster.png --layer-decomposition
```

请求结构：

```json
{
  "model": "doubao-seedream-5-0-pro-260628",
  "image": "data:image/png;base64,...",
  "layer_decomposition": true,
  "size": "auto"
}
```

规则：

- 必须且只能输入一张图片。
- `prompt` 可省略；省略时自动拆分主要元素。指定对象时使用自然语言或 `<bbox>`。
- `size` 可取 `1K`、`1.5K`、`2K`、`auto`，默认 `auto`。
- 不存在 `layer_image` 或 `layer_size` 请求字段。
- 响应 `data` 同时包含底图和各图层。脚本保留 `z_index`、`bounding_box`、`name`、`description`。

## 输出

未指定 `--output` 时，图片保存到 `$HOME/Documents/hermes-workspace/images`。stdout JSON 包含首张图片路径、全部图片数组、实际返回尺寸、`usage` 和 `request_id`。返回结果没有可下载图片时，脚本按失败处理。

用 `--dry-run` 只校验并查看请求，不调用 API；本地图片内容会显示为 `<local-image-data>`。
