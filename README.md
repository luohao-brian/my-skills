# my-skills

本仓库是面向 OpenClaw / 本地 Agent 的 skills 源码仓库。这里既维护各个 skill 的 `SKILL.md` 与参考文档，也维护 Rust CLI、验证脚本和 bundle 打包流程。

## 技能索引

| 技能 | 目录 | 实现入口 | 说明 |
| --- | --- | --- | --- |
| `my-fetch` | `my-fetch/` | `rust/my-fetch/` | 轻量网页抓取与正文提取 |
| `volc-gen` | `volc-gen/` | `rust/volc-gen/` | 火山引擎图片与视频生成 |
| `volc-speech` | `volc-speech/` | `rust/volc-speech/` | 火山引擎 TTS / STT |
| `volc-websearch` | `volc-websearch/` | `rust/volc-websearch/` | 多搜索源网页搜索 |
| `ai-news` | `ai-news/` | `ai-news/SKILL.md` | 中文 AI 新闻简报编排 |
| `ai-labs-tracker` | `ai-labs-tracker/` | `ai-labs-tracker/SKILL.md` | 追踪 OpenAI、Anthropic、Google DeepMind 最新动态 |
| `reddit-oss-models` | `reddit-oss-models/` | `reddit-oss-models/SKILL.md` | 监控 Reddit 开源模型热门讨论并生成周报 |

## 分技能说明

- [README_MY_FETCH.md](/Users/bytedance/Documents/my-skills/README_MY_FETCH.md)
- [README_VOLC_GEN.md](/Users/bytedance/Documents/my-skills/README_VOLC_GEN.md)
- [README_VOLC_SPEECH.md](/Users/bytedance/Documents/my-skills/README_VOLC_SPEECH.md)
- [README_VOLC_WEBSEARCH.md](/Users/bytedance/Documents/my-skills/README_VOLC_WEBSEARCH.md)
- [README_AI_NEWS.md](/Users/bytedance/Documents/my-skills/README_AI_NEWS.md)
- [README_AI_LABS_TRACKER.md](/Users/bytedance/Documents/my-skills/README_AI_LABS_TRACKER.md)
- [README_REDDIT_OSS_MODELS.md](/Users/bytedance/Documents/my-skills/README_REDDIT_OSS_MODELS.md)

## 安装方式

### 1. 先准备构建环境

`my-fetch`、`volc-gen`、`volc-speech`、`volc-websearch` 都依赖 Rust CLI，因此安装前先准备：

- Rust 工具链：`rustup`、`cargo`
- macOS 或 Linux 对应目标工具链
- 如果要产出 Linux bundle，额外准备 `cargo-zigbuild` 或 `cross`

常见准备命令：

```bash
rustup --version
cargo --version
```

### 2. Rust 类技能先构建 bundle，再通过 OpenClaw 安装

适用技能：

- `my-fetch`
- `volc-gen`
- `volc-speech`
- `volc-websearch`

先在仓库根目录构建 bundle：

```bash
cd /Users/bytedance/Documents/my-skills
bash build-skill-bundle.sh
```

构建完成后，会在 [`dist/`](/Users/bytedance/Documents/my-skills/dist) 生成对应平台的 `.tar.gz` bundle。再通过 OpenClaw 安装，例如：

```bash
openclaw plugins install /Users/bytedance/Documents/my-skills/dist/my-fetch-macos.tar.gz
openclaw plugins install /Users/bytedance/Documents/my-skills/dist/volc-gen-macos.tar.gz
```

如果当前机器是 Linux，就安装对应的 `*-linux.tar.gz`。

### 3. 纯编排 skill 推荐直接从 GitHub 安装

`ai-news` 当前推荐直接安装到 `my-cowork`：

```bash
skills add https://github.com/luohao-brian/my-skills --skill ai-news
```

这个路径适合不需要单独 Rust 二进制、主要依赖规则编排和已有工具能力的 skill。

## 构建与验证

下面这些命令不是简单罗列，而是按用途区分：

| 命令 | 作用 | 适用场景 | 依赖 |
| --- | --- | --- | --- |
| `cd /Users/bytedance/Documents/my-skills/rust && cargo build` | 编译整个 Rust workspace | 改了 Rust 代码后，先做最基础的构建检查 | Rust 工具链 |
| `cd /Users/bytedance/Documents/my-skills/rust && bash build.sh` | 产出当前主机平台的 CLI 二进制到 `cli/` | 需要检查可分发二进制，或准备后续打包 | Rust 工具链；Linux 全平台构建时还需要 `cargo-zigbuild` 或 `cross` |
| `cd /Users/bytedance/Documents/my-skills && bash build-skill-bundle.sh` | 先编译，再把 skill 目录和二进制一起打成 bundle | 准备通过 OpenClaw 安装 `my-fetch`、`volc-gen`、`volc-speech`、`volc-websearch` | Rust 工具链、`tar`、`rsync` |
| `cd /Users/bytedance/Documents/my-skills && bash scripts/verify-all.sh` | 跑仓库级默认验证 | 提交前做静态检查、帮助确认已有脚本覆盖的 skill 没被改坏 | Bash；部分检查会调用 Cargo |
| `cd /Users/bytedance/Documents/my-skills && bash scripts/verify-all.sh my-fetch` | 只跑单个 skill 的验证 | 改动范围集中在某一个 skill 时，缩小验证成本 | 对应 skill 的验证脚本和依赖 |
| `cd /Users/bytedance/Documents/my-skills && bash scripts/verify-all.sh --live` | 跑带真实联网/真实服务探测的验证 | 需要确认联网行为、第三方 API、真实 URL 可用性时使用 | 网络、真实环境变量或外部服务可用性 |

说明：

- `scripts/verify-all.sh` 当前默认覆盖 `my-fetch`、`volc-gen`、`volc-speech`、`volc-websearch`、`ai-news`
- `ai-labs-tracker` 和 `reddit-oss-models` 目前以文档和规则编排为主，暂无单独仓库级 `verify.sh`

## 目录约定

- skill 目录只保留运行时需要的内容，例如 `SKILL.md`、`references/`、源码和脚本
- 仓库级说明统一放在根目录 `README.md` 和 `README_<SKILL>.md`
- 调整技能元信息、触发描述、homepage、安装方式时，优先同步更新对应 skill 的 `SKILL.md`
- 调整 Rust CLI 参数、输出、API 调用和错误处理时，修改 `rust/` 下对应 crate
