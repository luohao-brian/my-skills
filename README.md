# my-skills

这是一个面向本地 Agent / OpenClaw 生态维护的 skills 仓库。仓库同时包含：

- skills 目录：给运行时加载的 `SKILL.md` 和按需参考文档
- Rust CLI：每个 skill 对应的实际命令实现
- 平台二进制：输出到 `cli/macos/` 和 `cli/linux/`
- skill bundle：输出到 `dist/*.tar.gz`，用于安装到技能目录

当前这个仓库不是“单纯放说明文档”的仓库，而是完整的技能源码仓库。

## 当前技能

| 技能 | 目录 | CLI | 能力 |
| --- | --- | --- | --- |
| `volc-gen` | `volc-gen/` | `volc-gen` | 文生图、图生图、图生视频、任务查询 |
| `volc-speech` | `volc-speech/` | `volc-speech` | 文本转语音（TTS）、语音转文本（STT） |
| `volc-websearch` | `volc-websearch/` | `volc-websearch` | 多搜索源网页搜索，支持结构化参数层与自动选源 |

## 仓库结构

```text
my-skills/
├── volc-gen/                  # skill 入口和 references
├── volc-speech/               # skill 入口和 references
├── volc-websearch/            # skill 入口和 references
├── rust/                      # Rust workspace
│   ├── volc-gen/
│   ├── volc-speech/
│   └── volc-websearch/
├── cli/
│   ├── macos/                 # 构建后的 macOS 二进制
│   └── linux/                 # 构建后的 Linux 二进制
├── dist/                      # skill bundle 输出目录
├── build-skill-bundle.sh      # 构建并打包 skills
├── install-cli.sh             # 安装 CLI 到 /usr/local/bin
└── uninstall-cli.sh           # 从 /usr/local/bin 卸载 CLI
```

## 常用工作流

### 1. 只构建本机 Rust CLI

```bash
cd /Users/bytedance/Documents/my-skills/rust
bash build.sh
```

输出：

- macOS：`cli/macos/`
- Linux：`cli/linux/`（依赖 `cargo-zigbuild` 或 `cross`，缺失时会跳过）

### 2. 生成 skill bundle

```bash
cd /Users/bytedance/Documents/my-skills
bash build-skill-bundle.sh
```

输出：

- `dist/volc-gen-*.tar.gz`
- `dist/volc-speech-*.tar.gz`
- `dist/volc-websearch-*.tar.gz`

### 3. 安装 CLI 到 `/usr/local/bin`

```bash
cd /Users/bytedance/Documents/my-skills
./install-cli.sh
```

无权限时：

```bash
sudo ./install-cli.sh
```

卸载：

```bash
./uninstall-cli.sh
```

### 4. 安装 skill 到本地 agent 目录

如果你本地使用的是 `~/.agents/skills`：

```bash
tar xzf dist/volc-speech-macos.tar.gz -C ~/.agents/skills/
```

如果要覆盖旧版本，先删旧目录再解压。

### 5. 运行仓库级回归脚本

这些脚本只服务仓库维护，不会进入最终 skill 安装包。

静态 smoke：

```bash
cd /Users/bytedance/Documents/my-skills
bash scripts/regression/verify-all.sh
```

只跑某一个 skill：

```bash
cd /Users/bytedance/Documents/my-skills
bash scripts/regression/verify-all.sh volc-websearch
```

带真实凭证跑联调：

```bash
cd /Users/bytedance/Documents/my-skills
bash scripts/regression/verify-all.sh --live
```

也可以单独跑：

```bash
bash scripts/regression/verify-volc-gen.sh
bash scripts/regression/verify-volc-speech.sh
bash scripts/regression/verify-volc-websearch.sh
```

单独脚本需要联调时，直接追加 `--live`：

```bash
bash scripts/regression/verify-volc-websearch.sh --live
```

## skill 与 README 的关系

每个 skill 至少包含：

- `SKILL.md`：运行时入口，给 agent 看
- `references/`：按需加载的参考文档

有些 skill 还会额外带一个仓库内 `README.md`，例如 `volc-speech/README.md`。这个 README：

- 只给人看
- 不应该进入最终 skill 安装包
- 当前打包脚本已经显式排除了 `README.md`

## 环境变量策略

不同 skill 的环境变量策略不同，不要再假设整个仓库只有一套统一前缀。

### `volc-gen`

- 主要使用：`ARK_API_KEY`

### `volc-speech`

- TTS 使用：`VOLC_TTS_*`
- STT 使用：`VOLC_STT_*`
- 兼容 fallback：`VOLC_AUDIO_*` 以及旧版 demo 变量

### `volc-websearch`

- 视所选搜索源决定，常见包括：
- `TAVILY_API_KEY`
- `BOCHA_API_KEY`
- `BRAVE_API_KEY`
- `VE_ACCESS_KEY`
- `VE_SECRET_KEY`

最稳妥的做法是：以各 skill 自己的 `SKILL.md` 和 `references/setup-guide.md` 为准。

## `volc-websearch` 当前约定

`volc-websearch` 现在推荐使用统一的结构化参数层：

- `query` 只写主题
- 时间约束用 `freshness` 或 `date-after/date-before`
- 地域和语言用 `country/language`
- 站点限制用 `domain-filter`
- 搜索目标用 `intent`
- 输出形态用 `result-type`

这套参数会按 provider 能力做原生下推；当某个 provider 不支持某些字段时，CLI 会给出 warning 或透明忽略，不会偷偷把限制条件塞回 `query`。

已完成真实联网验证的链路包括：

- Tavily：时间、站点过滤、摘要输出
- Brave：地域、语言
- Bocha：中文基础搜索
- Volc：日期范围、站点过滤、摘要输出
- auto：自动选源与 fallback

更详细的支持矩阵和示例见 [volc-websearch/SKILL.md](/Users/bytedance/Documents/my-skills/volc-websearch/SKILL.md)。

## 推荐阅读顺序

如果你要维护某个 skill，建议按这个顺序看：

1. 先看对应 skill 的 `SKILL.md`
2. 再看 skill 自己的 `references/`
3. 需要改命令行为时，再看 `rust/<skill>/`
4. 需要改打包行为时，再看 `build-skill-bundle.sh`

## 当前状态

这套仓库当前已经具备：

- `volc-gen`：可构建、可打包、可安装
- `volc-speech`：可构建、可打包、可安装，TTS / STT 都做过真实联调
- `volc-websearch`：可构建、可打包、可安装，结构化参数层和 4 个 provider 均已做过真实联调

如果你只想快速定位语音能力，直接看 [volc-speech/README.md](/Users/bytedance/Documents/my-skills/volc-speech/README.md)。
