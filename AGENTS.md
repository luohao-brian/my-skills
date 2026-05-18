# Repository Guidelines

## 项目概览

这是一个面向 OpenClaw / 本地 Agent 的 skills 源码仓库。当前主要包含这些技能：

- `my-fetch/`：轻量网页抓取与正文提取
- `volc-gen/`：火山引擎图片与视频生成
- `volc-speech/`：火山引擎语音合成与语音识别
- `volc-websearch/`：多搜索源网页搜索
- `ai-news/`：中文版 AI 新闻简报编排
- `ai-labs-tracker/`：追踪 OpenAI、Anthropic、Google DeepMind 最新动态
- `reddit-oss-models/`：Reddit 开源模型热门讨论 weekly 简报

仓库同时维护这些技能的：

- `SKILL.md` 和参考文档
- Rust CLI 或脚本实现
- 构建产物与分发包
- 仓库级验证脚本

## 当前目录结构

- `my-fetch/`：skill 目录，入口是 `SKILL.md`
- `volc-gen/`：skill 目录，入口是 `SKILL.md`
- `volc-speech/`：skill 目录，入口是 `SKILL.md`
- `volc-websearch/`：skill 目录，入口是 `SKILL.md`
- `ai-news/`：skill 目录，入口是 `SKILL.md`
- `ai-labs-tracker/`：skill 目录，入口是 `SKILL.md`
- `reddit-oss-models/`：skill 目录，入口是 `SKILL.md`
- `docs/OPENCLAW-SKILL.md`：本仓库采用的 OpenClaw skill 规范摘要
- `rust/`：Rust workspace
- `rust/my-fetch/`：`my-fetch` CLI
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
  - `README_AI_NEWS.md`
- skill 目录下不要放 README。skill 目录应尽量只保留运行时需要的内容。

## 工作方式

- 如果任务是新增或修改某个技能，先读对应目录下的 `SKILL.md`。
- 如果用户要找某个 skill，先在仓库根目录下匹配技能目录名，再确认该目录下存在 `SKILL.md`；不要凭记忆猜路径。
- 如果任务是调整技能元信息、触发描述、OpenClaw metadata、安装方式或首页链接，优先修改对应 skill 的 `SKILL.md`。
- 如果任务是调整 Rust CLI 参数、API 调用、签名逻辑、输出 JSON 或错误处理，修改 `rust/` 下对应 crate。
- 如果任务涉及 skill 标准或前台展示字段，先参考 `docs/OPENCLAW-SKILL.md`，并以 OpenClaw 当前实际支持的 metadata 字段为准。

## 当用户要求安装 skill 到 OpenClaw

先确认用户要装的是哪个 skill，再按下面流程执行。

### 1. 先定位目标 skill

- 在仓库根目录查找 `*/SKILL.md`
- 优先按目录名匹配用户给出的 skill 名
- 命中后，先读该 skill 的 `SKILL.md`
- 如果用户只描述功能、不知道 skill 名，先根据 `description` 和目录名判断最接近的 skill，再向用户说明你的匹配结果

当前可直接定位的 skill 目录有：

- `my-fetch/`
- `volc-gen/`
- `volc-speech/`
- `volc-websearch/`
- `ai-news/`
- `ai-labs-tracker/`
- `reddit-oss-models/`

### 2. 判断安装路径

- `my-fetch`、`volc-gen`、`volc-speech`、`volc-websearch`：先 build，再打 bundle，再安装到 OpenClaw
- `ai-news`：优先通过 GitHub 安装到 `my-cowork`
- `ai-labs-tracker`、`reddit-oss-models`：当前仓库里主要是规则型 skill，没有单独 Rust bundle；如果用户要求直接安装到 OpenClaw，先说明当前仓库未维护独立 bundle，再和用户确认要不要补本地安装流程或改成 GitHub / 技能目录安装

### 3. Rust skill 的标准安装流程

适用于：

- `my-fetch`
- `volc-gen`
- `volc-speech`
- `volc-websearch`

执行顺序：

1. 确认 Rust 环境可用：`rustup`、`cargo`
2. 需要 Linux bundle 时，再确认 `cargo-zigbuild` 或 `cross`
3. 在仓库根目录运行 `bash build-skill-bundle.sh`
4. 在 `dist/` 下找到目标 skill 对应平台的 tarball
5. 使用 OpenClaw 安装 tarball

常用命令：

```bash
cd /Users/bytedance/Documents/my-skills
bash build-skill-bundle.sh
openclaw plugins install /Users/bytedance/Documents/my-skills/dist/my-fetch-macos.tar.gz
```

安装时按目标平台选择文件名：

- macOS：`dist/<skill>-macos.tar.gz`
- Linux：`dist/<skill>-linux.tar.gz`

不要再让用户手工解压 `tar.gz` 到技能目录，优先用 OpenClaw 的安装命令。

### 4. `ai-news` 的推荐安装流程

`ai-news` 当前推荐直接安装到 `my-cowork`：

```bash
skills add https://github.com/luohao-brian/my-skills --skill ai-news
```

如果用户要更新：

```bash
skills update https://github.com/luohao-brian/my-skills --skill ai-news
```

### 5. 安装前后的检查点

- 安装前确认目标 skill 对应的 `SKILL.md`、二进制、bundle 路径都存在
- Rust skill 安装前，确认 `dist/` 里已经生成目标平台 tarball
- 安装后，向用户明确你安装的是哪个 skill、用的是哪个文件或命令
- 如果因为缺少 Rust、`cargo-zigbuild`、`cross`、OpenClaw CLI、外部凭证而没法完整安装，要明确卡点，不要笼统说“安装失败”

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

## Skill 文案与规则写法

- Skill 的消费对象是运行时 agent，不是 skill 作者、维护者或人工读者。`SKILL.md` 和配套文档要写成 agent 读完后能直接执行的合同：目标、输入来源、必须读取的文件、候选筛选标准、字段要求、边界、失败报告和输出格式。
- 对 agent 消费友好的规则应该回答：
  - 当前 skill 产出什么
  - agent 开始前必须读哪些文件
  - 候选或输入应满足哪些字段
  - 哪些条目可以进入最终输出
  - 字段缺失、来源不可用或覆盖不足时如何记录和报告
  - 最终结果必须长什么样
- 不要把作者维护决策写成 agent 行为。来源入口、固定清单、metadata、安装方式、默认可信来源集合由 skill 作者维护；agent 执行时只按现有 skill 合同消费这些入口，不判断某个入口是否应该保留在清单中。
- 不要把工具使用策略写进规则型 skill。不要在 `SKILL.md` 或来源文档里规定具体搜索引擎、provider、fallback 工具、抓取绕路、重试顺序或查询写法；这些由 agent 根据运行环境自行规划。只有 Rust-backed skill 或明确封装了 CLI/API 的技能，才在文档中写具体命令、参数和错误处理。
- 固定来源默认可信时，要把它写成 agent 边界，而不是来源质量评估。例如：agent 不做来源可信度排序、剔除、替换或真伪裁判，只检查字段是否满足成稿要求；字段缺失或来源不可用时记录问题。
- `SKILL.md` 里的规则要写成“模型执行时该做什么”，不要写成作者对规则的解释。
- 规则优先写成动作、顺序、范围、字段、边界，不要写成空泛态度或抽象原则。
- 不要写让模型自己脑补含义的句子，例如：
  - “主源 / 补充源 / 一级来源”
  - “适合 / 一般 / 稳定性较差 / 作为锚点”
  - “不要在脑中……”
  - “不用于替代……”
- 如果需要限制来源或入口，直接写清楚：
  - 扫哪些入口
  - 在什么场景下必须扫描
  - 这个入口预期提供哪些字段
  - 字段缺失、来源不可用或覆盖不足时怎么报告
  - 不要拿这个入口覆盖什么范围
- 来源分类只写“当前扫描范围”或“当前入口类型”，不要再引入隐含等级。
- “核对”是动作，不是来源类别。写法要落到具体检查项，例如：
  - 确认发布时间
  - 确认标题、来源 URL 和摘要所需内容是否存在
  - 确认条目是否落在目标时间窗内
- 不要把历史迁移说明、过程说明、补丁背景写进 skill 主规则。`SKILL.md` 和配套文档只写当前规则。
- 不要用权重、优先级、高中低、主次来源去暗示模型跳过某类来源；如果某类来源每次都要扫，就直接写“每次都要扫描”。
- 如果某个入口只覆盖一部分内容，要直接写覆盖边界，不要写模糊结论。
  - 例：`GitHub Trending` 只看高热度开源项目和仓库变化，不用它查重点厂商、重点模型、重点产品新闻。
  - 例：`Hugging Face Blog RSS` 用于开源模型、开源工具、平台能力和社区发布。
- 如果某个固定入口不可访问、返回壳页面或 challenge，规则型 skill 里只写如何记录来源不可用和缺失字段，不要写绕路抓取策略。绕路、重试和替代查找由 agent 执行时自行规划；如果入口长期不可用，应由 skill 作者更新来源清单。
- 时间窗口类规则要写成硬边界，不要写成模糊建议。
  - 例：用户说“今天 / 最新”时，只保留目标时间窗内的条目；超出目标时间窗的条目直接删除或标记为不入稿。
- 输出格式规则要写成结构要求，不要让模型自己推断格式。
  - 例：每条新闻固定三行字段；标题、分类标题、条目标题、字段都各占一行。

## Rust 代码约定

- `rust/Cargo.toml` 是 workspace 入口；新增 Rust skill 时，把 crate 挂到这个 workspace。
- 保持命令行接口稳定；改参数时要同步更新对应 `SKILL.md`。
- API 请求、签名和响应模型尽量拆在 `api.rs`、`sign.rs`、`models.rs` 等文件里，延续现有结构。
- 除非收益明确，不要无意义地引入更重的运行时。

## 构建与打包

按用途区分常用命令，不要只罗列命令本身：

- `cargo build`
  - 作用：编译整个 Rust workspace
  - 适用场景：改了 Rust 逻辑后做最基础构建检查
- `bash rust/build.sh`
  - 作用：输出当前主机平台的 CLI 二进制到 `cli/`
  - 适用场景：需要检查本机平台二进制，或为后续 bundle 打包做准备
- `bash build-skill-bundle.sh`
  - 作用：重新构建 Rust 二进制，并把对应 skill 和二进制一起打包到 `dist/*.tar.gz`
  - 适用场景：需要把 `my-fetch`、`volc-gen`、`volc-speech`、`volc-websearch` 安装到 OpenClaw

常用命令：

```bash
cd /Users/bytedance/Documents/my-skills/rust
cargo build
```

```bash
cd /Users/bytedance/Documents/my-skills/rust
bash build.sh
```

```bash
cd /Users/bytedance/Documents/my-skills
bash build-skill-bundle.sh
```

说明：

- `rust/build.sh` 会输出 macOS 二进制到 `cli/macos/`。
- Linux 二进制依赖 `cargo-zigbuild` 或 `cross`；缺少时脚本会跳过。
- `build-skill-bundle.sh` 会重新构建 Rust 二进制，并把对应 skill 和二进制一起打包到 `dist/*.tar.gz`。

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
如果改动依赖真实外部凭证或真实浏览器登录态，当前环境无法完整验证时，要明确说明只做了静态检查或构建级验证。

## 仓库级脚本约定

- 仓库级验证脚本统一放在 `scripts/`。
- 结构按 skill 分目录，而不是单独维护 `regression/` 总目录。
- 当前结构：

```text
scripts/
├── common.sh
├── ai-news/verify.sh
├── my-fetch/verify.sh
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
- 修改仓库级验证脚本时，保持 `scripts/<skill>/verify.sh` 这种布局一致。

## 已知风险

- 仓库还处于结构调整期，未提交改动较多；做结构类修改时要先以当前文件树为准，不要依赖旧对话里的路径。
- `build-skill-bundle.sh` 会清空 `dist/` 后重建；不要假设 `dist/` 里的手工文件会被保留。
- 外部 API、浏览器登录态、MCP 授权和联网可用性都会影响运行结果；构建通过不等于线上行为正确。
