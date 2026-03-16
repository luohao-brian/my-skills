# Repository Guidelines

## 项目概览

这是一个本地 Skills 仓库，当前主要包含两个面向 OpenClaw 的技能：

- `volc-gen/`：调用火山引擎 Ark API 进行图像/视频生成
- `volc-websearch/`：调用火山引擎联网搜索 API 获取网页结果

仓库同时维护这些技能对应的 Rust 二进制、分发产物和技能规范文档。

## 目录结构

- `volc-gen/`：技能目录，入口是 `SKILL.md`
- `volc-websearch/`：技能目录，入口是 `SKILL.md`
- `volc-websearch/references/`：该技能的按需参考文档
- `docs/OPENCLAW-SKILL.md`：本仓库编写技能时遵循的规范摘要
- `rust/`：Rust workspace
- `rust/volc-gen/`：`volc-gen` 的 CLI 实现
- `rust/volc-websearch/`：`volc-websearch` 的 CLI 实现
- `cli/macos/`：构建后的 macOS 二进制输出目录
- `cli/linux/`：构建后的 Linux 二进制输出目录
- `build-skill-bundle.sh`：构建并打包技能发布包

## 工作方式

- 如果任务是新增或修改某个技能，先看对应目录下的 `SKILL.md`，再决定是否需要改 Rust 代码或参考文档。
- 如果任务是调整技能元信息、触发描述、门控条件或安装方式，优先修改技能目录里的 `SKILL.md`。
- 如果任务是调整命令参数、API 调用、签名逻辑、输出 JSON 结构或错误处理，修改 `rust/` 下对应 crate。
- 如果任务涉及技能规范或目录约定，先参考 `docs/OPENCLAW-SKILL.md`，保持与 OpenClaw Skill 规则一致。

## 技能约定

- 每个技能目录至少包含一个 `SKILL.md` 作为入口。
- 可执行命令在 `SKILL.md` 中必须使用 `{baseDir}` 引用本技能目录下的二进制路径。
- `metadata` 必须保持为单行 JSON，不要改成多行 YAML 结构。
- `description` 需要同时说明“做什么”和“什么时候用”，因为它会直接影响技能触发。
- 参考资料放在技能自己的 `references/` 目录中，按需补充，不要把大量无关文档塞进根目录。

## Rust 代码约定

- `rust/Cargo.toml` 是 workspace 入口；新增技能的二进制实现时，把 crate 挂到这个 workspace。
- 当前两个 crate 都是简单 CLI 工具，依赖 `clap`、`serde`、`ureq` 等库；除非有明显收益，不要过度引入复杂运行时。
- 保持命令行接口稳定，改参数时要同步更新对应技能的 `SKILL.md` 示例和说明。
- API 请求、签名和响应模型尽量分层放在 `api.rs`、`sign.rs`、`models.rs` 这类文件里，延续现有结构。

## 构建与打包

常用命令：

```bash
cd rust
cargo build
```

```bash
cd rust
bash build.sh
```

```bash
bash build-skill-bundle.sh
```

说明：

- `rust/build.sh` 会输出 macOS 二进制到 `cli/macos/`。
- Linux 二进制依赖 `cargo-zigbuild` 或 `cross`；缺少时脚本会跳过 Linux 构建。
- `build-skill-bundle.sh` 会重新构建 Rust 二进制，并把技能目录内容和对应二进制一起打包到 `dist/*.tar.gz`。

## 修改后的验证

按改动范围选择最小可行验证：

- 技能说明或元信息改动：人工检查 `SKILL.md` 的 frontmatter、示例命令和引用路径
- Rust 逻辑改动：在 `rust/` 下运行 `cargo build`
- 打包流程改动：运行 `bash build-skill-bundle.sh`
- 某个技能命令改动：直接运行对应二进制做一次最小参数验证，例如 `cli/macos/volc-gen --help`

如果改动依赖真实火山引擎凭证，无法在当前环境验证时，要明确说明只完成了静态检查或构建级验证。

## 提交修改时的注意点

- 不要只改 Rust 代码而忘记同步 `SKILL.md` 的命令示例、环境变量说明和触发描述。
- 不要在技能说明里引用不存在的脚本或二进制路径。
- 不要随意修改打包产物目录约定：技能目录内容应进入归档根目录，二进制应位于归档内的 `bin/`。
- 任何新增环境变量都需要写进对应技能的 `metadata.openclaw.requires.env` 和正文说明。
- 如果新增技能，优先复用现有目录布局：`<skill>/SKILL.md`、可选 `references/`，以及 `rust/<skill>/`。

## 已知风险

- README 当前描述和仓库实际内容不完全一致；做说明类改动时，应以当前文件结构和脚本行为为准，不要盲从旧文档。
- `build-skill-bundle.sh` 会清空 `dist/` 并重建产物；如果用户在 `dist/` 放了未提交文件，不要假设它们会被保留。
- API 相关功能高度依赖外部凭证和服务可用性，构建通过不等于线上行为正确。
