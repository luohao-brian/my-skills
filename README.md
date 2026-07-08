# my-skills

面向 OpenClaw / 本地 Agent 的 skills 与插件源码仓库。当前仓库按运行场景分成三类，不再维护 Rust workspace、预编译 CLI、bundle tarball 或 `dist/` 产物。

## 目录

| 类别 | 路径 | 内容 |
| --- | --- | --- |
| info-track | `info-track/` | 规则型信息追踪与中文简报 skills |
| hermes plugins | `hermes-plugins/` | Hermes 插件源码 |
| openclaw skills | `openclaw-skills/` | Markdown + references/templates/scripts 的 OpenClaw skills |

## Skills

### info-track

| Skill | 路径 | 说明 |
| --- | --- | --- |
| `ai-news` | `info-track/ai-news/` | 中文 AI 新闻日报 |
| `ai-labs-tracker` | `info-track/ai-labs-tracker/` | OpenAI、Anthropic、Google DeepMind 动态追踪 |
| `reddit-oss-models` | `info-track/reddit-oss-models/` | Reddit 开源模型热门讨论 weekly |

### hermes plugins

| Plugin | 路径 | 说明 |
| --- | --- | --- |
| `hermes-ark-plugin` | `hermes-plugins/hermes-ark-plugin/` | Hermes Ark 多模态 provider 插件 |

### openclaw skills

| Skill | 路径 | 实现 |
| --- | --- | --- |
| `ark-tts` | `openclaw-skills/ark-tts/` | Ark TTS, `scripts/volc_tts.py` |
| `ark-stt` | `openclaw-skills/ark-stt/` | Ark STT, `scripts/volc_stt.py` |
| `ark-image-gen` | `openclaw-skills/ark-image-gen/` | Ark Seedream image generation, `scripts/volc_image_gen.py` |
| `ark-video-gen` | `openclaw-skills/ark-video-gen/` | Ark Seedance video generation, `scripts/volc_video_gen.py` |
| `ark-vision` | `openclaw-skills/ark-vision/` | Ark Agent Plan image understanding, `scripts/vision_analyze.py` |
| `ark-search` | `openclaw-skills/ark-search/` | Ark Agent Plan search, `scripts/web_search.py` |
| `ark-data-pro` | `openclaw-skills/ark-data-pro/` | Ark Agent Plan professional datasets, `scripts/data_pro_search.py` |
| `volc-search` | `openclaw-skills/volc-search/` | Volcengine WebSearch, `scripts/web_search.py` |
| `popular-web-designs` | `openclaw-skills/popular-web-designs/` | 54 portable HTML/CSS design templates, `templates/*.md` |

## Design

OpenClaw skills use progressive loading:

1. `SKILL.md` contains trigger metadata, required reads, minimal commands, and the execution contract.
2. `references/` contains operation-specific details.
3. `templates/` contains reusable output or design templates.
4. `scripts/` contains deterministic implementations when the skill needs executable helpers.

This mirrors the lightweight-entry pattern used by the bundled PDF/PPT skills: load a short skill first, then open references or scripts only when needed.

## OpenClaw Loading

OpenClaw supports one grouping level under configured skill roots, so this repository can be used with grouped paths such as:

```text
openclaw-skills/ark-tts/SKILL.md
info-track/ai-news/SKILL.md
```

For local development, add this repo or one of the group directories to OpenClaw skill loading config, or copy the desired skill folder into the active workspace `skills/` directory.

For agents that should use `popular-web-designs` without changing their skill registry, point them at the folder directly:

```text
Use /Users/bytedance/Documents/my-skills/openclaw-skills/popular-web-designs as a file-based design skill.
Read SKILL.md, references/catalog.md, references/workflow.md, then one selected templates/<site>.md file.
Apply the template to the current HTML/CSS/frontend target and verify with the available local workflow.
```

## Dependencies

Python dependencies are declared in root `pyproject.toml` for local `uv run` usage, and executable skills also declare runtime dependencies in `metadata.openclaw.install`:

- `requests` for TTS, image generation, and search
- `websocket-client` for STT
- `volcengine-python-sdk[ark]` for video generation

Primary Ark credential:

```bash
export ARK_AGENT_PLAN_API_KEY=...
```

Volcengine WebSearch AK/SK credentials:

```bash
export VOLCENGINE_ACCESS_KEY=...
export VOLCENGINE_SECRET_KEY=...
```

## Verification

Run the static repository checks:

```bash
bash scripts/verify-all.sh
```

The check validates:

- grouped `SKILL.md` discovery
- single-line `metadata` JSON
- referenced files and scripts
- Python syntax compilation
- absence of removed Rust / CLI / bundle directories

Live API verification requires real credentials and should be run manually per skill.
