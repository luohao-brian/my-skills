# Repository Guidelines

## 项目概览

这是一个面向 OpenClaw / 本地 Agent 的 skills 源码仓库。当前包含四个主要技能：

- `volc-gen/`：火山引擎图片与视频生成
- `volc-speech/`：火山引擎语音合成与语音识别
- `volc-websearch/`：多搜索源网页搜索
- `url-to-markdown/`：浏览器渲染网页并提取正文为 markdown / json

仓库同时维护这些技能的：

- `SKILL.md` 和参考文档
- Rust CLI 或脚本实现
- 构建产物与分发包
- 仓库级验证脚本

## 当前目录结构

- `volc-gen/`：skill 目录，入口是 `SKILL.md`
- `volc-speech/`：skill 目录，入口是 `SKILL.md`
- `volc-websearch/`：skill 目录，入口是 `SKILL.md`
- `url-to-markdown/`：单目录分发 skill，入口是 `SKILL.md`
- `url-to-markdown/scripts/`：`web-fetch` 主体实现，入口是 `src/cli.ts`
- `docs/OPENCLAW-SKILL.md`：本仓库采用的 OpenClaw skill 规范摘要
- `rust/`：Rust workspace
- `rust/volc-gen/`：`volc-gen` CLI
- `rust/volc-speech/`：`volc-speech` CLI
- `rust/volc-websearch/`：`volc-websearch` CLI
- `scripts/`：仓库级验证脚本，按 skill 分目录组织
- `cli/macos/`：构建后的 macOS 二进制
- `cli/linux/`：构建后的 Linux 二进制
- `dist/`：bundle 输出目录
- `build-skill-bundle.sh`：构建并打包发布产物

## README 约定

- 根目录 `README.md` 只做索引和整体说明。
- 分技能说明统一放在根目录，例如：
  - `README_VOLC_GEN.md`
  - `README_VOLC_SPEECH.md`
  - `README_VOLC_WEBSEARCH.md`
  - `README_URL_TO_MARKDOWN.md`
- skill 目录下不要放 README。skill 目录应尽量只保留运行时需要的内容。

## 工作方式

- 如果任务是新增或修改某个技能，先读对应目录下的 `SKILL.md`。
- 如果任务是调整技能元信息、触发描述、OpenClaw metadata、安装方式或首页链接，优先修改对应 skill 的 `SKILL.md`。
- 如果任务是调整 Rust CLI 参数、API 调用、签名逻辑、输出 JSON 或错误处理，修改 `rust/` 下对应 crate。
- 如果任务是调整 `url-to-markdown` 的抓取行为、浏览器回退、MCP bridge 或 markdown 提取，修改 `url-to-markdown/scripts/src/`。
- 如果任务涉及 skill 标准或前台展示字段，先参考 `docs/OPENCLAW-SKILL.md`，并以 OpenClaw 当前实际支持的 metadata 字段为准。

## Skill 约定

- 每个 skill 目录至少包含一个 `SKILL.md` 作为入口。
- `metadata` 必须保持为单行 JSON，不要改成多行 YAML。
- `description` 要同时说明“做什么”和“什么时候用”，因为 OpenClaw 会直接拿它做技能触发和 UI 展示。
- `homepage` 优先指向 `my-skills` 仓库内对应 skill 页面，而不是外部文档首页。
- `metadata.openclaw` 只使用 OpenClaw 当前实际支持的字段，例如：
  - `skillKey`
  - `emoji`
  - `homepage`
  - `os`
  - `always`
  - `primaryEnv`
  - `requires.bins`
  - `requires.anyBins`
  - `requires.env`
  - `requires.config`
  - `install`
- 参考文档放在 skill 自己的 `references/` 目录中，按需补充，不要把无关文档堆到根目录。

## `url-to-markdown` 约定

- 这是单目录分发 skill，安装时直接复制整个 `url-to-markdown/` 目录。
- 不再使用 `vendor/` 机制；`web-fetch` 主体直接位于 `url-to-markdown/scripts/`。
- CLI 入口是 `url-to-markdown/scripts/src/cli.ts`。
- 默认行为是：
  - 先走无头后台浏览器
  - 命中登录、验证码、风控或正文缺失时，再自动切到用户日常 Chrome
  - 日常 Chrome 通过 `mcp-bridge.mjs` 按需启动并短时常驻
- 除非确实新增了必填配置，否则不要再给这个 skill 增加新的环境变量门槛。

## Rust 代码约定

- `rust/Cargo.toml` 是 workspace 入口；新增 Rust skill 时，把 crate 挂到这个 workspace。
- 保持命令行接口稳定；改参数时要同步更新对应 `SKILL.md`。
- API 请求、签名和响应模型尽量拆在 `api.rs`、`sign.rs`、`models.rs` 等文件里，延续现有结构。
- 除非收益明确，不要无意义地引入更重的运行时。

## 构建与打包

常用命令：

```bash
cd /Users/hluo/Documents/my-skills/rust
cargo build
```

```bash
cd /Users/hluo/Documents/my-skills/rust
bash build.sh
```

```bash
cd /Users/hluo/Documents/my-skills
bash build-skill-bundle.sh
```

说明：

- `rust/build.sh` 会输出 macOS 二进制到 `cli/macos/`。
- Linux 二进制依赖 `cargo-zigbuild` 或 `cross`；缺少时脚本会跳过。
- `build-skill-bundle.sh` 会重新构建 Rust 二进制，并把对应 skill 和二进制一起打包到 `dist/*.tar.gz`。
- `url-to-markdown` 当前按目录直接分发，不依赖根仓库的 Rust bundle。

## 验证约定

按改动范围选择最小可行验证：

- skill 文案或 metadata 改动：
  - 人工检查 `SKILL.md` frontmatter、命令路径、homepage 和 metadata 是否正确
- Rust 逻辑改动：
  - 在 `rust/` 下运行 `cargo build`
- 仓库级脚本改动：
  - 运行 `bash scripts/verify-all.sh`
- 单个 Rust skill 改动：
  - 运行对应的 `bash scripts/<skill>/verify.sh`
- `url-to-markdown` 改动：
  - `cd url-to-markdown/scripts && bun install --frozen-lockfile`
  - `bun ./src/cli.ts --help`
  - 必要时再做一个最小 URL 抓取 smoke

如果改动依赖真实外部凭证或真实浏览器登录态，当前环境无法完整验证时，要明确说明只做了静态检查或构建级验证。

## 仓库级脚本约定

- 仓库级验证脚本统一放在 `scripts/`。
- 结构按 skill 分目录，而不是单独维护 `regression/` 总目录。
- 当前结构：

```text
scripts/
├── common.sh
├── verify-all.sh
├── volc-gen/verify.sh
├── volc-speech/verify.sh
└── volc-websearch/verify.sh
```

新增 skill 的仓库级验证脚本时，优先采用：

```text
scripts/<skill>/verify.sh
```

## 提交修改时的注意点

- 不要只改实现而忘记同步 `SKILL.md` 的命令示例、metadata、描述和 homepage。
- 不要在 skill 说明里引用不存在的脚本、二进制或旧路径。
- 不要把仓库级 README 再放回 skill 目录。
- 任何新增必填环境变量，都要同步写进对应 skill 的 `metadata.openclaw.requires.env` 和正文说明。
- 修改 `url-to-markdown` 时，不要重新引入 `vendor/baoyu-fetch` 之类的旧结构。
- 修改仓库级验证脚本时，保持 `scripts/<skill>/verify.sh` 这种布局一致。

## 已知风险

- 仓库还处于结构调整期，未提交改动较多；做结构类修改时要先以当前文件树为准，不要依赖旧对话里的路径。
- `build-skill-bundle.sh` 会清空 `dist/` 后重建；不要假设 `dist/` 里的手工文件会被保留。
- 外部 API、浏览器登录态、MCP 授权和联网可用性都会影响运行结果；构建通过不等于线上行为正确。
