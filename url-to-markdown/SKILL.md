---
name: url-to-markdown
runtime: nodejs
description: Render a known URL in a browser and extract the main content as markdown or json. Use when the user wants to save an article, thread, post, or page from a specific URL, especially if JavaScript rendering or login fallback may be needed. Not for open-ended web search or broad site crawling.
homepage: https://github.com/luohao-brian/my-skills/tree/main/url-to-markdown
version: 1.60.0
metadata: {"openclaw":{"skillKey":"url-to-markdown","emoji":"📝","os":["darwin","linux"],"requires":{"anyBins":["bun","npx"]},"install":[{"id":"brew-bun","kind":"brew","formula":"bun","bins":["bun"],"label":"Install bun (brew)","os":["darwin","linux"]}]}}
---

# URL to Markdown

将网页内容抓取为高质量 markdown。当前本地实现直接把 `web-fetch` 主体放在 skill 的 `scripts/` 目录里，整个技能目录可以直接复制到 OpenClaw / Agent 的 skills 目录中使用。

## When to Use

- 已经有明确 URL，需要把网页正文转成 markdown 或 json
- 需要抓文章页、帖子页、专栏页、讨论串或单个页面内容
- 页面依赖 JavaScript 渲染，普通 HTTP 抓取不稳定
- headless 抓取失败后，希望自动回退到日常 Chrome 复用登录态

## When Not to Use

- 用户还没有 URL，只是想“搜一下最新信息”
- 需要多搜索源检索、新闻交叉验证或开放式网页搜索
- 需要批量爬整站、站点地图遍历或大规模采集
- 只是想做浏览器自动化点击、表单填写或通用网页操作

默认行为已经内置，不要求用户配置浏览器参数：

1. 默认先用 skill 自己的无头后台浏览器抓取
2. 如果检测到登录、验证码、Cloudflare 或无头抓取失败，再自动切到用户日常 Chrome
3. 日常 Chrome 模式通过 skill 内部的本地 bridge 按需启动并短时常驻，减少重复授权弹窗

## CLI Setup

底层 CLI 源码位于：

```bash
{baseDir}/scripts/src/cli.ts
```

执行前先解析运行时：

1. 自动定位 skill 目录
2. 如果 `bun` 存在，使用 `bun`
3. 否则如果 `npx` 存在，使用 `npx -y bun`
4. 在 `{baseDir}/scripts/node_modules/` 缺失时，先在 `{baseDir}/scripts/` 下执行 `bun install --frozen-lockfile`

推荐执行模式：

```bash
# 使用 bun
(cd {baseDir}/scripts && bun install --frozen-lockfile && bun ./src/cli.ts <url>)

# 或使用 npx bun
(cd {baseDir}/scripts && npx -y bun install --frozen-lockfile && npx -y bun ./src/cli.ts <url>)
```

## Defaults

这个 skill 不再要求单独配置浏览器连接参数。默认值直接内置在实现里：

- 自动保存目录：`./url-to-markdown/`
- 默认输出格式：`markdown`
- 默认先走无头后台浏览器
- 需要用户介入时自动切到日常 Chrome
- 本地 MCP bridge 自动按需启动，空闲后自动退出

如果只是把网页转成 markdown/json，通常不需要设置任何环境变量。

## Features

- Chrome CDP 渲染完整页面 JavaScript
- 默认无头后台抓取，失败后自动切到日常 Chrome
- 站点适配器：X/Twitter、YouTube、Hacker News、generic(Defuddle)
- 可检测并等待登录、验证码、Cloudflare 等交互门槛
- 默认输出 markdown，支持 `--format json`
- 可下载图片和视频到本地目录并重写 markdown 链接
- 日常 Chrome 模式带本地 bridge 复用，减少重复授权
- 支持输出调试产物

## Usage

```bash
# 默认：自动保存到 ./url-to-markdown/{domain}/{slug}/{slug}.md
(cd {baseDir}/scripts && bun ./src/cli.ts <url>)

# 保存到指定文件
(cd {baseDir}/scripts && bun ./src/cli.ts <url> --output article.md)

# 保存并下载媒体资源
(cd {baseDir}/scripts && bun ./src/cli.ts <url> --output article.md --download-media)

# JSON 输出
(cd {baseDir}/scripts && bun ./src/cli.ts <url> --format json)
```

## Options

| Option | Description |
|--------|-------------|
| `<url>` | URL to fetch |
| `--output <path>` | 输出文件路径，默认 stdout |
| `--format <type>` | `markdown`（默认）或 `json` |
| `--json` | `--format json` 的简写 |
| `--adapter <name>` | 指定适配器：`x` / `youtube` / `hn` / `generic` |
| `--headless` | 显式 headless 模式 |
| `--wait-for <mode>` | `none` / `interaction` / `force`，高级调试用 |
| `--wait-for-interaction` | `--wait-for interaction` 的别名 |
| `--wait-for-login` | `--wait-for interaction` 的别名 |
| `--timeout <ms>` | 页面加载超时，默认 30000 |
| `--interaction-timeout <ms>` | 登录/验证码等待超时，默认 600000 |
| `--interaction-poll-interval <ms>` | 轮询间隔，默认 1500 |
| `--download-media` | 下载图片/视频并重写 markdown 链接，需要配合 `--output` |
| `--media-dir <dir>` | 媒体资源目录，默认与输出文件同级 |
| `--cdp-url <url>` | 复用现有 Chrome CDP endpoint |
| `--browser-path <path>` | 自定义 Chrome / Chromium 可执行文件 |
| `--chrome-profile-dir <path>` | Chrome user data 目录 |
| `--debug-dir <dir>` | 输出调试产物 |

## Agent Quality Gate

默认 headless 抓取只能视为“初步结果”。抓取后必须检查输出 markdown 是否满足基本质量要求：

1. 标题应匹配目标页面，而不是通用壳页面
2. 正文应包含实际文章或内容，而不是导航、页脚、报错壳
3. 警惕这些失败信号：
   - `Application error`
   - `This page could not be found`
   - 登录、注册、订阅、验证壳
   - 对长文页面而言内容异常短
   - 大量框架载荷、模板或样板内容
4. 如果结果明显不完整或错误，不要因为 CLI 返回 0 就接受

恢复流程：

1. 默认先 headless 抓取
2. 立刻检查 markdown 质量
3. 如发现登录/CAPTCHA/Cloudflare 或内容明显不对，skill 会自动尝试切到日常 Chrome
4. 只有在自动恢复仍不够时，才手动使用 `--wait-for interaction` 或 `--wait-for force`

## Output Path Generation

当未显式传入 `--output` 时，CLI 会自动生成输出路径：

1. 基础目录默认是 `./url-to-markdown/`
2. 从 URL 提取域名
3. 从 URL path 生成 slug（kebab-case）
4. 输出路径结构推荐：

```text
{base_dir}/{domain}/{slug}/{slug}.md
```

这样每个 URL 都有自己的目录，媒体资源也能自然隔离。这个目录也是当前 OpenClaw 工作区下的默认保存位置。
