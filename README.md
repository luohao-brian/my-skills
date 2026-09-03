# my-skills

这里放自维护的 skill、Hermes 插件，以及当前使用的上游 skill 清单。

当前环境共使用 **76 个 skill**：

| 来源 | 数量 | 维护方式 |
| --- | ---: | --- |
| 直接使用上游 | 57 | 随对应 CLI 或从上游仓库安装，本仓库不保存副本 |
| 本地维护版本 | 19 | 交付源码位于本仓库，由本仓库校验和发布 |

分类以实际使用的版本为准。入口、运行时适配、服务提供方、文档或资源有本地改动，就列入“本地维护版本”；未经修改则列入“直接使用上游”。

## 直接使用上游的 skill（57）

OpenCLI、Office CLI、Lark CLI 和 HyperFrames 会在安装 CLI 时一并安装，仓库地址见分组标题。Archify、AL Site 和 AL Sandbox 单独安装，仓库地址见名称链接。本仓库不保存这些 skill 的副本。

### [OpenCLI](https://github.com/jackwener/opencli)（随 CLI 安装，7）

- `opencli-usage`
- `smart-search`
- `opencli-browser`
- `opencli-browser-sitemap`
- `opencli-adapter-author`
- `opencli-autofix`
- `opencli-sitemap-author`

### [Office CLI](https://github.com/iOfficeAI/OfficeCLI)（随 CLI 安装，1）

- `officecli`

### [Lark CLI](https://github.com/larksuite/cli)（随 CLI 安装，27）

- `lark-approval`
- `lark-apps`
- `lark-attendance`
- `lark-base`
- `lark-calendar`
- `lark-contact`
- `lark-doc`
- `lark-drive`
- `lark-event`
- `lark-im`
- `lark-mail`
- `lark-markdown`
- `lark-minutes`
- `lark-note`
- `lark-okr`
- `lark-openapi-explorer`
- `lark-shared`
- `lark-sheets`
- `lark-skill-maker`
- `lark-slides`
- `lark-task`
- `lark-vc`
- `lark-vc-agent`
- `lark-whiteboard`
- `lark-wiki`
- `lark-workflow-meeting-summary`
- `lark-workflow-standup-report`

### 架构图（1）

- [`archify`](https://github.com/tt-a1i/archify)

### [HyperFrames](https://github.com/heygen-com/hyperframes)（随 CLI 安装，19）

- `hyperframes`
- `hyperframes-core`
- `hyperframes-cli`
- `hyperframes-animation`
- `hyperframes-creative`
- `hyperframes-keyframes`
- `hyperframes-registry`
- `media-use`
- `general-video`
- `motion-graphics`
- `faceless-explainer`
- `embedded-captions`
- `talking-head-recut`
- `music-to-video`
- `product-launch-video`
- `pr-to-video`
- `remotion-to-hyperframes`
- `slideshow`
- `figma`

### AL Site 与 Sandbox（2）

- [`al-site`](https://github.com/2B-AL/al-site-skill)
- [`al-sandbox`](https://github.com/2B-AL/al-sandbox-skill)

## 本地维护的 skill（19）

以下目录是部署输入。功能、依赖声明、运行时适配和验证规则都随本仓库版本发布。

### AI 信息追踪（5）

| Skill | 源码 | 用途 |
| --- | --- | --- |
| `ai-community-pulse` | [`info-track/ai-community-pulse/`](info-track/ai-community-pulse/) | AI 社区与生态热点日报 |
| `ai-labs-tracker` | [`info-track/ai-labs-tracker/`](info-track/ai-labs-tracker/) | AI 厂商产品、API、工程与研究动态 |
| `ai-news` | [`info-track/ai-news/`](info-track/ai-news/) | 中文 AI 新闻简报 |
| `ai-oss-models` | [`info-track/ai-oss-models/`](info-track/ai-oss-models/) | 开放模型、数据集与本地部署动态 |
| `ai-tech-blogs` | [`info-track/ai-tech-blogs/`](info-track/ai-tech-blogs/) | 中文 AI 技术博客聚合 |

### Ark（8）

| Skill | 源码 | 用途 |
| --- | --- | --- |
| `ark-search` | [`openclaw-skills/ark-search/`](openclaw-skills/ark-search/) | 网页和图片搜索 |
| `ark-data-pro` | [`openclaw-skills/ark-data-pro/`](openclaw-skills/ark-data-pro/) | 金融、企业和学术专业数据查询 |
| `ark-file` | [`openclaw-skills/ark-file/`](openclaw-skills/ark-file/) | 多模态文件上传、查询、等待和删除 |
| `ark-image-gen` | [`openclaw-skills/ark-image-gen/`](openclaw-skills/ark-image-gen/) | Seedream 图片生成 |
| `ark-video-gen` | [`openclaw-skills/ark-video-gen/`](openclaw-skills/ark-video-gen/) | Seedance 视频生成 |
| `ark-tts` | [`openclaw-skills/ark-tts/`](openclaw-skills/ark-tts/) | 文本转语音 |
| `ark-stt` | [`openclaw-skills/ark-stt/`](openclaw-skills/ark-stt/) | 语音转文字 |
| `ark-vision` | [`openclaw-skills/ark-vision/`](openclaw-skills/ark-vision/) | 图片与视频理解 |

### 设计与演示（6）

| Skill | 源码 | 维护方式 |
| --- | --- | --- |
| `popular-web-designs` | [`openclaw-skills/popular-web-designs/`](openclaw-skills/popular-web-designs/) | 本地模板库 |
| `guizang-ppt-skill` | [`openclaw-skills/guizang-ppt-skill/`](openclaw-skills/guizang-ppt-skill/) | 本地实现 |
| `ppt-master` | [`openclaw-skills/ppt-master/`](openclaw-skills/ppt-master/) | 固定上游发布版本，加确定性打包转换、运行时覆盖层和少量补丁 |
| `baoyu-article-illustrator` | [`openclaw-skills/baoyu-article-illustrator/`](openclaw-skills/baoyu-article-illustrator/) | 固定上游快照，加本地入口与渐进式加载封装 |
| `baoyu-infographic` | [`openclaw-skills/baoyu-infographic/`](openclaw-skills/baoyu-infographic/) | 固定上游快照，加本地入口与渐进式加载封装 |
| `diagram-design` | [`openclaw-skills/diagram-design/`](openclaw-skills/diagram-design/) | 固定上游快照，加本地入口与渐进式加载封装 |

## 不在 76 个标准部署项中的组件

仓库还保留两个独立组件，但它们不属于上面的默认 skill 集：

| 组件 | 路径 | 说明 |
| --- | --- | --- |
| `volc-search` | [`openclaw-skills/volc-search/`](openclaw-skills/volc-search/) | 火山引擎 WebSearch 的独立实现 |
| `hermes-ark-plugin` | [`hermes-plugins/hermes-ark-plugin/`](hermes-plugins/hermes-ark-plugin/) | Hermes Ark 多模态 provider 插件，不是 skill |

## 仓库结构

```text
info-track/                 AI 信息追踪 skills
openclaw-skills/            本地维护的 OpenClaw skills
hermes-plugins/             Hermes 插件
docs/                       本仓库的 skill 包规范
scripts/                    同步与验证脚本
```

每个 skill 以 `SKILL.md` 为入口。详细规则放在 `references/`，可复用资源放在 `templates/`，确定性实现放在 `scripts/`。完整包格式见 [`docs/OPENCLAW-SKILL.md`](docs/OPENCLAW-SKILL.md)。

## 上游同步

### Baoyu 与 Diagram Design

三个上游派生 skill 使用各自的 `UPSTREAM.json` 固定仓库、commit、源码路径和版本。`upstream/` 保存未修改的快照，`references/upstream-sections/` 由上游 `SKILL.md` 机械生成。

比较指定上游 ref：

```bash
python3 scripts/sync-vendored-skills.py all --ref <tag-or-commit>
```

确认差异后更新快照：

```bash
python3 scripts/sync-vendored-skills.py all --ref <tag-or-commit> --apply
```

### PPT Master

PPT Master 使用 `scripts/ppt_master_downstream/manifest.json` 固定上游发布版本。发布目录由上游整树、确定性打包转换、附加覆盖层和小型补丁队列重新生成。

本地 diff 以最小化为目标：保留打包、调用方工作目录、运行时依赖和方舟 Agent Plan 接入适配；PPT 创作、字体转换、质量检查与导出流程沿用上游。新增本地改动前先确认上游是否已提供所需能力，避免维护第二套制作或验收规则。

检查当前发布目录是否可以由 manifest 完整重建：

```bash
python3 scripts/ppt_master_sync.py --check
```

重新生成本地发布目录：

```bash
python3 scripts/ppt_master_sync.py
```

## Python 依赖

仓库根目录只包含验证脚本的公共依赖。每个可执行 skill 的 `requirements.txt` 或 `SKILL.md` 中的 `metadata.openclaw.install` 才是该组件的依赖声明。

使用 `uv` 创建隔离环境，例如：

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r openclaw-skills/ppt-master/requirements.txt
```

不要把依赖安装到 skill 目录或系统 Python。

## 验证

所有改动先运行仓库基础检查：

```bash
bash scripts/verify-repo.sh
```

按改动范围追加专项检查：

```bash
bash scripts/verify-ark-skills.sh
bash scripts/verify-guizang-ppt-skill.sh
bash scripts/verify-guizang-ppt-skill.sh --visual
PYTHON_BIN="$HOME/Documents/hermes-workspace/.venv/bin/python" bash scripts/verify-ppt-master.sh
```

基础检查覆盖 skill frontmatter、metadata JSON、仓库 JSON、Python/JavaScript/Shell 语法以及 `uv.lock` 一致性。专项检查负责组件行为。真实 API、浏览器、PowerPoint 和视觉结果需要在具备对应能力的运行环境中验证。
