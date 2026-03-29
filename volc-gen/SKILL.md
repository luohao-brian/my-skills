---
name: volc-gen
description: 调用火山引擎 Ark API 生成图片和视频。支持文生图(t2i)、图生图(i2i)、图生视频(i2v)。当用户需要AI生成图片、编辑图片风格或将图片转为视频时使用。
homepage: https://github.com/luohao-brian/my-skills/tree/main/volc-gen
metadata: {"openclaw":{"requires":{"env":["ARK_API_KEY"]},"primaryEnv":"ARK_API_KEY","emoji":"🎨"}}
---

# 火山引擎内容生成

调用火山引擎 Ark API 进行内容生成，支持文生图、图生图和图生视频。

所有命令成功时默认输出 JSON，便于 agent 直接解析字段；图片生成结果会包含 `local_path` 和 `remote_url`，视频生成结果会包含 `task_id` 和 `remote_url`。

## 文生图 (t2i)

根据文本提示词生成图片。

命令会在返回远程图片 URL 的同时，将图片默认下载到当前工作目录；在 OpenClaw 会话中通常就是 `~/.openclaw/workspace/`。

```bash
{baseDir}/bin/volc-gen t2i "一只赛博朋克风格的猫"
{baseDir}/bin/volc-gen t2i "山水画风格的城市天际线" --size 16:9
{baseDir}/bin/volc-gen t2i "极简风格的产品海报" --size 1:1
```

- `prompt`（必需）：提示词
- `--size`（可选）：推荐用比例预设或显式分辨率，默认 `16:9`
- 使用建议：桌面横版内容优先 `16:9`；手机图片、短视频封面、竖版海报优先 `9:16`
- Seedream 5.0 2K 推荐尺寸：
- `1:1` = `2048x2048`
- `3:4` = `1728x2304`
- `4:3` = `2304x1728`
- `16:9` = `2848x1600`
- `9:16` = `1600x2848`
- `3:2` = `2496x1664`
- `2:3` = `1664x2496`
- `21:9` = `3136x1344`

## 图生图 (i2i)

基于输入图片和提示词生成新图片。输入图会先在本地压缩和标准化，再统一转成 Base64 Data URL 上传。

命令会在返回远程图片 URL 的同时，将图片默认下载到当前工作目录；在 OpenClaw 会话中通常就是 `~/.openclaw/workspace/`。

```bash
{baseDir}/bin/volc-gen i2i "变成油画风格" "/path/to/image.png"
{baseDir}/bin/volc-gen i2i "增加雪景效果" "data:image/png;base64,..." --size 4:3
```

- `prompt`（必需）：修改指令或描述
- `image_input`（必需）：参考图片输入，支持本地路径或 `data:image/...;base64,...`
- `--size`（可选）：输出尺寸，默认 `16:9`
- 上传策略：最长边压到 `1600px` 以内；默认转 `JPEG(q=84)`，含透明通道时保留 `PNG`

## 图生视频 (i2v)

将图片转为视频。命令会自动提交任务并轮询状态，直到生成完成或超时（4 分钟）。输入图会先在本地压缩和标准化，再统一转成 Base64 Data URL 上传。

```bash
{baseDir}/bin/volc-gen i2v "女孩微笑着回头" "/path/to/start.png"
{baseDir}/bin/volc-gen i2v "女孩微笑着回头" "data:image/png;base64,..."
```

- `text`（必需）：动作描述
- `image_input`（必需）：起始图片输入，支持本地路径或 `data:image/...;base64,...`
- 上传策略：最长边压到 `1280px` 以内；默认转 `JPEG(q=84)`，含透明通道时保留 `PNG`

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

## 环境变量

- `ARK_API_KEY`（必需）：API 访问密钥
- `VOLC_IMAGE_MODEL_ID`（可选）：生图模型 ID，默认 `doubao-seedream-5-0-260128`
- `VOLC_VIDEO_MODEL_ID`（可选）：视频模型 ID，默认 `doubao-seedance-1-5-pro-251215`
