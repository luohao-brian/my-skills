---
name: volc-gen
description: 调用火山引擎 Ark API 进行内容生成的技能。支持文生图、图生图和图生视频。
---

# volc-gen

调用火山引擎 Ark API 进行内容生成的技能。支持文生图、图生图和图生视频。

## 前置要求

1.  **环境变量**: 必须设置 `ARK_API_KEY`。
    ```bash
    export ARK_API_KEY="your-api-key"
    ```
2.  **工具**: 系统需安装 `jq`。

## 功能列表

### 1. 文生图 (Text-to-Image)

根据文本提示词生成图片。

- **命令**: `t2i`
- **参数**:
    - `prompt` (string): 提示词。
    - `size` (string, optional): 图片尺寸，默认为 "2K"。
- **示例**:
    ```bash
    ./volc-gen/bin/volc t2i "一只赛博朋克风格的猫"
    ```

### 2. 图生图 (Image-to-Image)

基于一张输入图片和提示词生成新图片。

- **命令**: `i2i`
- **参数**:
    - `prompt` (string): 修改指令或描述。
    - `image_url` (string): 参考图片的 URL。
    - `size` (string, optional): 图片尺寸，默认为 "2K"。
- **示例**:
    ```bash
    ./volc-gen/bin/volc i2i "变成油画风格" "https://example.com/image.png"
    ```

### 3. 图生视频 (Image-to-Video)

让图片动起来。该命令会自动提交任务并轮询状态，直到生成完成或超时。

- **命令**: `i2v`
- **参数**:
    - `text` (string): 动作描述。
    - `image_url` (string): 起始图片的 URL。
- **示例**:
    ```bash
    ./volc-gen/bin/volc i2v "女孩微笑着回头" "https://example.com/start.png"
    ```

### 4. 查询与列表 (Query & List)

查询指定生成任务的详情，或列出历史任务列表。

- **命令**: `query` (别名 `list`)
- **参数**:
    - 无参数: 列出最近的任务（第 1 页，默认 10 条）。
    - `page` (number): 指定页码列出任务。
    - `page` `size` (number): 指定页码和每页数量。
    - `task_id` (string): 查询指定任务 ID 的详细信息。

- **示例**:
    ```bash
    # 列出最近任务
    ./volc-gen/bin/volc query
    
    # 列出第 2 页任务
    ./volc-gen/bin/volc query 2
    
    # 查询特定任务详情
    ./volc-gen/bin/volc query "cgt-2025xxxx"
    ```

## 注意事项

- 视频生成可能需要几分钟时间，请耐心等待。
- 确保 API Key 有对应模型的调用权限。