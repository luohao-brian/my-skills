# my-skills

面向 OpenClaw / 本地 Agent 的 skills 与插件源码仓库。当前仓库按运行场景分成三类，不再维护 Rust workspace、预编译 CLI、bundle tarball 或 `dist/` 产物。

## 目录

| 类别 | 路径 | 内容 |
| --- | --- | --- |
| info-track | `info-track/` | 规则型信息追踪与中文简报 skills |
| hermes plugins | `hermes-plugins/` | Hermes 插件源码 |
| openclaw skills | `openclaw-skills/` | Markdown + references/templates/scripts 的 OpenClaw skills |

## 技能清单

### 信息追踪

| Skill | 路径 | 说明 |
| --- | --- | --- |
| `ai-news` | `info-track/ai-news/` | 中文 AI 新闻日报 |
| `ai-community-pulse` | `info-track/ai-community-pulse/` | AI 社区与生态热点日报 |
| `ai-labs-tracker` | `info-track/ai-labs-tracker/` | AI 厂商产品、工程与研究动态追踪 |
| `ai-tech-blogs` | `info-track/ai-tech-blogs/` | Hubwiz、QingkeAI 技术博客聚合 |
| `ai-oss-models` | `info-track/ai-oss-models/` | Hugging Face AI 开源模型与数据集更新 |

### Hermes 插件

| Plugin | 路径 | 说明 |
| --- | --- | --- |
| `hermes-ark-plugin` | `hermes-plugins/hermes-ark-plugin/` | Hermes Ark 多模态 provider 插件 |

### OpenClaw Skills

| Skill | 路径 | 实现 |
| --- | --- | --- |
| `ark-tts` | `openclaw-skills/ark-tts/` | Ark 文本转语音，`scripts/volc_tts.py` |
| `ark-stt` | `openclaw-skills/ark-stt/` | Ark 语音识别，`scripts/volc_stt.py` |
| `ark-image-gen` | `openclaw-skills/ark-image-gen/` | Ark Seedream 图像生成，`scripts/volc_image_gen.py` |
| `ark-video-gen` | `openclaw-skills/ark-video-gen/` | Ark Seedance 视频生成，`scripts/volc_video_gen.py` |
| `ark-vision` | `openclaw-skills/ark-vision/` | Ark Agent Plan 图片理解，`scripts/vision_analyze.py` |
| `ark-search` | `openclaw-skills/ark-search/` | Ark Agent Plan 搜索，`scripts/web_search.py` |
| `ark-data-pro` | `openclaw-skills/ark-data-pro/` | Ark Agent Plan 专业数据集，`scripts/data_pro_search.py` |
| `ark-viking` | `openclaw-skills/ark-viking/` | OpenViking 知识浏览、语义检索与 RAG 上下文组装，`scripts/openviking.py` |
| `volc-search` | `openclaw-skills/volc-search/` | 火山引擎 WebSearch，`scripts/web_search.py` |
| `popular-web-designs` | `openclaw-skills/popular-web-designs/` | 54 套可移植 HTML/CSS 设计模板，`templates/*.md` |
| `guizang-ppt-skill` | `openclaw-skills/guizang-ppt-skill/` | 单文件 HTML PPT，22 个 Swiss 版式契约、golden deck 与静态/视觉校验 |
| `ppt-master` | `openclaw-skills/ppt-master/` | SVG → 原生 PPTX 工作流，含静态契约、浏览器多视口与导出后几何校验 |

## 设计原则

OpenClaw Skills 采用渐进式加载：

1. `SKILL.md` 只保留触发元数据、必读文件、最小命令和执行合同。
2. `references/` 存放按需读取的操作细节。
3. `templates/` 存放可复用的输出或设计模板。
4. `scripts/` 存放 Skill 所需的确定性实现。

这种结构与内置 PDF/PPT Skills 的轻量入口一致：先加载短 `SKILL.md`，再按任务需要读取 reference 或脚本。

## OpenClaw 加载

OpenClaw 在配置的 Skill 根目录下支持一级分组，因此可以直接使用以下分组路径：

```text
openclaw-skills/ark-tts/SKILL.md
info-track/ai-news/SKILL.md
```

本地开发时，可以把整个仓库或某个分组目录加入 OpenClaw Skill 加载配置，也可以把需要的 Skill 目录复制到当前工作区的 `skills/` 目录。

如果不修改 Agent 的 Skill 注册表，也可以直接把 `popular-web-designs` 目录作为文件型 Skill 提供给 Agent：

```text
将 $HOME/Documents/my-skills/openclaw-skills/popular-web-designs 作为文件型设计 Skill。
先读取 SKILL.md、references/catalog.md、references/workflow.md，再读取选中的 templates/<site>.md。
把模板应用到当前 HTML/CSS/前端目标，并使用当前运行时可用的本地流程完成验证。
```

## Python 环境与依赖

README 不维护 Python 包清单。每个可执行组件自己的 `requirements.txt` 是依赖来源，依赖统一安装到 `uv` 创建的虚拟环境，不要安装到 Skill 目录或系统 Python。

以 PPT Master 为例：

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r openclaw-skills/ppt-master/requirements.txt
```

其他组件把最后一行替换成对应的 `requirements.txt`。OpenClaw 自动安装场景仍以各 `SKILL.md` 的 `metadata.openclaw.install` 为入口，但具体版本应与组件 `requirements.txt` 保持一致。

## 验证

运行仓库静态检查：

```bash
bash scripts/verify-all.sh
```

检查内容包括：

- every skill directory contains `SKILL.md`
- required frontmatter fields and valid single-line `metadata` JSON
- `name` / `metadata.openclaw.skillKey` match the skill directory
- repository JSON syntax
- Python、JavaScript 和 Shell 语法
- 组件测试与仓库工具测试
- `pyproject.toml` 与 `uv.lock` 一致性

该检查不会调用真实外部服务。涉及凭证、浏览器、PowerPoint 或实时 API 的行为验证，需要按具体 Skill 的执行合同单独运行。
