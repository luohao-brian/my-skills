# README_URL_TO_MARKDOWN

`url-to-markdown` 是单目录分发的网页抓取 skill，本地实现主体在 [`/Users/hluo/Documents/my-skills/url-to-markdown/scripts`](/Users/hluo/Documents/my-skills/url-to-markdown/scripts)。

## 当前实现

- 默认先用无头后台浏览器抓取
- 检测到登录、验证码、风控或内容缺失时，自动切到用户日常 Chrome
- 日常 Chrome 通过本地 MCP bridge 按需启动并短时常驻
- CLI 主入口为 [`/Users/hluo/Documents/my-skills/url-to-markdown/scripts/src/cli.ts`](/Users/hluo/Documents/my-skills/url-to-markdown/scripts/src/cli.ts)

## 上游记录

- 上游仓库：[JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills)
- 上游 skill 路径：`skills/baoyu-url-to-markdown`
- 当前本地已改造成 `url-to-markdown` + `web-fetch`

## OpenClaw Metadata 设计

当前这个 skill 按 `openclaw` 的实际解析规则设计为：

- `name`: `url-to-markdown`
- `skillKey`: `url-to-markdown`
- `homepage`: `my-skills` 仓库中的 skill 页面
- `always`: 不设置，等价于 `false`
- `supportedOs`: 通过 `metadata.openclaw.os = ["darwin","linux"]`
- `requiresBins`: 不设置
- `requiresAnyBins`: `["bun","npx"]`
- `requiresConfig`: 不设置
- `primaryEnv`: 不设置。这个 skill 没有必填 API key
- `envConfigs`: 不设置。运行时默认不要求用户注入环境变量
- `installSteps`: 提供一个 `brew` 安装 `bun` 的入口，方便 Skills UI 做一键安装

对应原因：

- `skillMdPath` 不需要手写，OpenClaw 会从实际加载到的 `SKILL.md` 路径生成
- `skillKey` 显式写死，是为了后续即使描述或显示名称变化，配置入口仍然稳定
- `requiresAnyBins` 比 `requiresBins` 更合适，因为本地支持 `bun` 直跑，也支持 `npx -y bun`
- 不声明 `primaryEnv` / `requires.env`，是因为当前 skill 设计目标就是“开箱即用”，而不是依赖 API key
- `install` 目前只放 `bun`，因为这是最直接的运行时依赖；`npx` 属于 Node 运行时附带能力，不单独做 skill installer

## 运行入口

- skill：[`/Users/hluo/Documents/my-skills/url-to-markdown/SKILL.md`](/Users/hluo/Documents/my-skills/url-to-markdown/SKILL.md)
- CLI：[`/Users/hluo/Documents/my-skills/url-to-markdown/scripts/src/cli.ts`](/Users/hluo/Documents/my-skills/url-to-markdown/scripts/src/cli.ts)
- MCP bridge：[`/Users/hluo/Documents/my-skills/url-to-markdown/scripts/mcp-bridge.mjs`](/Users/hluo/Documents/my-skills/url-to-markdown/scripts/mcp-bridge.mjs)

## 本地运行

```bash
cd /Users/hluo/Documents/my-skills/url-to-markdown/scripts
bun install --frozen-lockfile
bun ./src/cli.ts https://example.com
```

## 安装方式

这个 skill 当前不走根仓库 Rust bundle，直接复制整个目录即可：

```bash
cp -R /Users/hluo/Documents/my-skills/url-to-markdown ~/.agents/skills/
```
