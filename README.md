# my-skills

本仓库是面向本地 Agent / OpenClaw 的 skills 源码仓库，既包含可安装的 `SKILL.md`，也包含对应的 Rust CLI、脚本和打包逻辑。

## 技能索引

| 技能 | 目录 | 实现入口 | 说明 |
| --- | --- | --- | --- |
| `volc-gen` | `volc-gen/` | `rust/volc-gen/` | 火山引擎图片与视频生成 |
| `volc-speech` | `volc-speech/` | `rust/volc-speech/` | 火山引擎 TTS / STT |
| `volc-websearch` | `volc-websearch/` | `rust/volc-websearch/` | 多搜索源网页搜索 |
| `ai-news` | `ai-news/` | `ai-news/SKILL.md` | 中文 AI 新闻简报编排 skill |

## 分技能说明

- [README_VOLC_GEN.md](/Users/hluo/Documents/my-skills/README_VOLC_GEN.md)
- [README_VOLC_SPEECH.md](/Users/hluo/Documents/my-skills/README_VOLC_SPEECH.md)
- [README_VOLC_WEBSEARCH.md](/Users/hluo/Documents/my-skills/README_VOLC_WEBSEARCH.md)
- [README_AI_NEWS.md](/Users/hluo/Documents/my-skills/README_AI_NEWS.md)


## 目录约定

- skill 目录只保留运行时需要的内容，例如 `SKILL.md`、`references/`、源码和脚本
- 仓库级说明统一放在根目录 `README.md` 和 `README_<SKILL>.md`
- 仓库级验证脚本统一放在 `scripts/`，并按 skill 分目录组织

当前脚本结构：

```text
scripts/
├── common.sh
├── verify-all.sh
├── ai-news/verify.sh
├── volc-gen/verify.sh
├── volc-speech/verify.sh
└── volc-websearch/verify.sh
```

## 常用命令

构建 Rust CLI：

```bash
cd /Users/hluo/Documents/my-skills/rust
bash build.sh
```

打包 skill bundle：

```bash
cd /Users/hluo/Documents/my-skills
bash build-skill-bundle.sh
```

运行仓库级验证：

```bash
cd /Users/hluo/Documents/my-skills
bash scripts/verify-all.sh
```

只验证某个 skill：

```bash
cd /Users/hluo/Documents/my-skills
bash scripts/verify-all.sh volc-websearch
```

带真实凭证联调：

```bash
cd /Users/hluo/Documents/my-skills
bash scripts/verify-all.sh --live
```

## 安装说明

- `volc-gen`、`volc-speech`、`volc-websearch`：通过 `build-skill-bundle.sh` 生成 bundle 后安装
- `ai-news`：推荐通过 GitHub 安装到 `my-cowork`，命令为 `skills add https://github.com/luohao-brian/my-skills --skill ai-news`
