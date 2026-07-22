# Repository Guidelines

## 项目概览

这是一个面向 OpenClaw / 本地 Agent 的 skills 和插件源码仓库。当前按用途分成三类：

- `info-track/`：信息追踪和简报编排类规则型 skills
- `hermes-plugins/`：Hermes 插件源码
- `openclaw-skills/`：OpenClaw skills，采用 Markdown + references/templates/scripts 的渐进式加载实现

仓库不再维护 Rust workspace、预编译 CLI、tarball bundle 或 `dist/` 产物。

## 当前目录结构

- `info-track/ai-news/`：中文版 AI 新闻简报
- `info-track/ai-community-pulse/`：AI 社区与生态热点日报
- `info-track/ai-labs-tracker/`：AI 厂商产品、工程与研究动态追踪
- `info-track/ai-tech-blogs/`：Hubwiz、QingkeAI 技术博客聚合
- `info-track/ai-oss-models/`：Hugging Face AI 开源模型与数据集更新
- `hermes-plugins/hermes-ark-plugin/`：Hermes Ark 多模态插件
- `openclaw-skills/ark-tts/`：火山 Ark TTS
- `openclaw-skills/ark-stt/`：火山 Ark STT
- `openclaw-skills/ark-image-gen/`：火山 Ark 图像生成
- `openclaw-skills/ark-video-gen/`：火山 Ark 视频生成
- `openclaw-skills/ark-vision/`：Ark Agent Plan 图片理解
- `openclaw-skills/ark-search/`：Ark Agent Plan 搜索
- `openclaw-skills/ark-data-pro/`：Ark Agent Plan 专业数据集
- `openclaw-skills/ark-viking/`：OpenViking 知识浏览、语义召回与 RAG 上下文组装
- `openclaw-skills/volc-search/`：火山引擎 WebSearch
- `openclaw-skills/popular-web-designs/`：通用 HTML/CSS 网站设计模板库
- `openclaw-skills/ppt-master/`：SVG/PPTX 演示文稿生成、转换与多层视觉校验
- `docs/OPENCLAW-SKILL.md`：本仓库采用的 OpenClaw skill 规范摘要
- `scripts/verify-all.sh`：仓库级静态验证

## 工作方式

- 如果任务是新增或修改某个 skill，先读对应目录下的 `SKILL.md`。
- 如果用户要找某个 skill，先在仓库根目录下查找 `*/ */SKILL.md` 或 `*/SKILL.md`，再确认路径，不要凭记忆猜。
- 如果任务涉及 OpenClaw metadata、触发描述、homepage、依赖或安装方式，优先修改对应 `SKILL.md`。
- 如果任务涉及火山 Ark 调用、签名、输出 JSON 或错误处理，修改对应 `openclaw-skills/<skill>/scripts/*.py`。
- 如果任务涉及 Hermes provider 行为，修改 `hermes-plugins/hermes-ark-plugin/`。
- 如果任务涉及 skill 标准或前台展示字段，先参考 `docs/OPENCLAW-SKILL.md`，并以 `../openclaw/docs/tools/skills.md` 当前实现为准。

## 渐进式加载约定

- `SKILL.md` 只保留触发说明、必读文件、最小命令和执行合同。
- 细节放在 `references/`，按需加载。
- 模板资源放在 `templates/`；确定性实现放在 `scripts/`，以 Python 脚本为主。
- 不要把长 API 文档、迁移过程、历史背景或维护者解释写进 `SKILL.md`。
- 不要新增 Rust crate、预编译二进制、`cli/`、`dist/` 或 bundle 脚本。

## OpenClaw Skill 约定

- 每个 skill 目录至少包含 `SKILL.md`。
- `metadata` 必须保持为单行 JSON。
- `description` 要同时说明“做什么”和“什么时候用”，因为 OpenClaw 会直接拿它做触发和 UI 展示。
- `homepage` 优先指向 `my-skills` 仓库内对应目录。
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
- Python 依赖优先通过 `metadata.openclaw.install` 的 `uv` installer 声明。
- 运行命令使用 `{baseDir}` 引用当前 skill 目录。

## Skill 文案与规则写法

- Skill 的消费对象是运行时 agent，不是 skill 作者、维护者或人工读者。
- 规则写成动作、顺序、范围、字段、边界、失败报告和输出格式。
- 不要把作者维护决策写成 agent 行为。
- 规则型 info-track skill 不要规定具体搜索引擎、provider、fallback 工具、抓取绕路、重试顺序或查询写法。
- Rust-backed skill 已废弃；只有 Python 脚本封装的 OpenClaw skill 才在文档中写具体命令、参数和错误处理。
- 固定来源默认可信时，把它写成 agent 边界，不写成来源质量评估。
- 时间窗口类规则要写成硬边界。
- 输出格式规则要写成结构要求，不要让模型自己推断格式。

## 验证约定

按改动范围选择最小可行验证：

- skill 文案或 metadata 改动：运行 `bash scripts/verify-all.sh`
- Python 脚本改动：运行 `bash scripts/verify-all.sh`，必要时再运行对应脚本 `--help`
- Hermes 插件改动：至少运行 Python 编译检查；涉及安装/config 时再按插件 README 做本地命令验证
- 依赖真实外部凭证、真实浏览器登录态或联网服务时，当前环境无法完整验证要明确说明只做了静态检查

## 提交修改时的注意点

- 不要只改实现而忘记同步 `SKILL.md` 的命令示例、metadata、description 和 homepage。
- 不要在 skill 说明里引用不存在的脚本、二进制或旧路径。
- 不要把 README 放进 skill 目录。
- 任何新增必填环境变量，都要同步写进对应 skill 的 `metadata.openclaw.requires.env` 或正文兼容说明。
- 本仓库修改默认先给用户看 diff/summary；没有用户明确批准，不要 commit 或 push。
