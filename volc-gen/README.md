# volc-gen Skill

这是一个用于调用火山引擎（Volcengine）Ark API 进行内容生成的 Agent Skill。它集成了文生图、图生图和图生视频的生成能力，并支持任务状态查询。

## 🚀 安装

本 Skill 通过 `skills` CLI 工具进行管理。

### 1. 本地安装

如果你已经下载了本项目的源码，可以通过以下命令将本地目录注册为全局 Skill：

```bash
# 假设你在 content-gen 目录下
npx skills add ./volc-gen -g
```

* `-g`: 表示全局安装，使其在所有 Agent 会话中可用。

### 2. 验证安装

安装完成后，检查是否出现在列表中：

```bash
npx skills list -g
```

## 🛠️ 配置要求

在使用之前，请确保满足以下环境要求：

1.  **系统依赖**: 必须安装 `jq` 和 `curl`。
    *   **macOS**: `brew install jq curl`
    *   **Linux**: `sudo apt-get install jq curl`

2.  **环境变量**: 设置火山引擎 API Key。
    ```bash
    export ARK_API_KEY="your-volcengine-api-key"
    ```
    建议将此行添加到你的 `~/.zshrc` 或 `~/.bashrc` 文件中以持久生效。

## 📖 使用指南

### 1. 文生图 (Text-to-Image)
```bash
# 用法: volc t2i <提示词> [尺寸]
volc t2i "一只赛博朋克风格的猫，霓虹灯背景" "2K"
```

### 2. 图生图 (Image-to-Image)
```bash
# 用法: volc i2i <提示词> <图片URL> [尺寸]
volc i2i "转换成梵高油画风格" "https://example.com/cat.jpg"
```

### 3. 图生视频 (Image-to-Video)
该命令会自动提交任务并轮询状态，直到视频生成完毕。
```bash
# 用法: volc i2v <描述> <图片URL>
volc i2v "让这只猫眨眼睛并转头" "https://example.com/cat.jpg"
```

### 4. 查询与列表 (Query & List)
```bash
# 列出最近的任务 (默认第1页)
volc query

# 列出指定页的任务 (例如第2页)
volc query 2

# 查询特定任务的详细状态
volc query "cgt-2026xxxx-xxxxx"
```

## 🗑️ 卸载

如果不再需要该 Skill，可以运行：

```bash
npx skills remove volc-gen -g
```
