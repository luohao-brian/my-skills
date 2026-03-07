# volc CLI 用法

`volc` 是用于调用火山引擎 Ark API 的命令行工具，支持文生图、图生图、图生视频和任务查询。

## 命令格式

```bash
volc <command> [args...]
```

## 子命令

### 1. 文生图 (t2i)

```bash
# 用法: volc t2i <提示词> [尺寸]
volc t2i "一只赛博朋克风格的猫，霓虹灯背景" "2K"
```

### 2. 图生图 (i2i)

```bash
# 用法: volc i2i <提示词> <图片URL> [尺寸]
volc i2i "转换成梵高油画风格" "https://example.com/cat.jpg"
```

### 3. 图生视频 (i2v)

```bash
# 用法: volc i2v <描述> <图片URL>
volc i2v "让这只猫眨眼睛并转头" "https://example.com/cat.jpg"
```

### 4. 任务查询 (query / list)

```bash
# 列出最近任务
volc query

# 查询第 2 页
volc query 2

# 查询指定任务详情
volc query "cgt-2026xxxx-xxxxx"
```
