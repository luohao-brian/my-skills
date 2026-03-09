---
name: volc-gen
description: 调用火山引擎 Ark API 生成图片和视频。支持文生图(t2i)、图生图(i2i)、图生视频(i2v)。当用户需要生成图片、编辑图片风格或将图片转为视频时使用。
metadata: {"openclaw":{"requires":{"env":["ARK_API_KEY"]},"primaryEnv":"ARK_API_KEY"}}
---

# 火山引擎内容生成

调用火山引擎 Ark API 进行内容生成，支持文生图、图生图和图生视频。

## 文生图 (t2i)

根据文本提示词生成图片。

```bash
{baseDir}/bin/volc-gen t2i "一只赛博朋克风格的猫"
{baseDir}/bin/volc-gen t2i "山水画风格的城市天际线" --size 2K
```

- `prompt`（必需）：提示词
- `--size`（可选）：图片尺寸，默认 "2K"

## 图生图 (i2i)

基于输入图片和提示词生成新图片。

```bash
{baseDir}/bin/volc-gen i2i "变成油画风格" "https://example.com/image.png"
{baseDir}/bin/volc-gen i2i "增加雪景效果" "https://example.com/photo.jpg" --size 2K
```

- `prompt`（必需）：修改指令或描述
- `image_url`（必需）：参考图片的 URL
- `--size`（可选）：图片尺寸，默认 "2K"

## 图生视频 (i2v)

将图片转为视频。命令会自动提交任务并轮询状态，直到生成完成或超时（4 分钟）。

```bash
{baseDir}/bin/volc-gen i2v "女孩微笑着回头" "https://example.com/start.png"
```

- `text`（必需）：动作描述
- `image_url`（必需）：起始图片的 URL

## 查询任务 (query)

查询生成任务详情或列出历史任务。

```bash
# 列出最近任务
{baseDir}/bin/volc-gen query

# 列出第 2 页，每页 20 条
{baseDir}/bin/volc-gen query 2 20

# 查询特定任务详情
{baseDir}/bin/volc-gen query "cgt-2025xxxx"
```

## 注意事项

- 确保 `ARK_API_KEY` 已设置且有对应模型的调用权限
