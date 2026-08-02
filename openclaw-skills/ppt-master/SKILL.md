---
name: ppt-master
description: 将 PDF、DOCX、PPTX、网页、Markdown、新闻或主题资料生成可编辑 SVG/PPTX 演示文稿，也可填充模板、美化既有 PPTX、添加动画与旁白。用户要求创建、制作、优化、检查或导出 PPT/演示文稿，提到 ppt-master，或需要 SVG 页面与 PowerPoint 互转时使用。
metadata: {"openclaw":{"skillKey":"ppt-master","emoji":"📊","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ppt-master","requires":{"anyBins":["python3","python"]}}}
---

# PPT Master

PPT Master 是路由式演示文稿工作流。SVG 生成路线以完整页面 SVG 为设计真相来源，经过静态、浏览器和 PPTX 包级检查后发布。

## 必读顺序

1. 始终读取 [`references/openclaw-runtime.md`](references/openclaw-runtime.md)，确定外部项目目录、依赖、媒体能力和发布门禁。
2. 读取 [`workflows/routing.md`](workflows/routing.md)，只选择一个顶层路线。
3. 按路由读取对应 authority：
   - 新建或重构演示：[`workflows/generate-pptx.md`](workflows/generate-pptx.md)
   - 创建复用模板：[`workflows/create-template.md`](workflows/create-template.md)
   - 填充原生 PPTX：[`workflows/template-fill-pptx.md`](workflows/template-fill-pptx.md)
   - 原生增强 PPTX：[`workflows/native-enhance-pptx.md`](workflows/native-enhance-pptx.md)
4. 只读取所选路线明确触发的 profile、stage、governance 和 reference，不预加载其他路线。

## OpenClaw 执行边界

- 使用 `{baseDir}` 解析本 skill 内脚本、模板和 reference；禁止假设 cwd 中存在 `skills/ppt-master`，也不要拼接安装目录绝对路径。
- 初始化时必须向 `project_manager.py init` 传 `--dir <absolute-projects-root>`。项目、预览、备份和导出写入用户指定目录；未指定时写入当前运行时 workspace 下的独立目录。禁止写入 `{baseDir}` 或本源码仓库。
- AI 配图与旁白通过当前 Agent 已有的工具或 skill 执行；先发现并读取真实接口，再把 PPT Master 的语义请求映射过去。PPT Master 不绑定 Agent、provider、模型、密钥或运行时配置。先读 [`references/runtime-media.md`](references/runtime-media.md)。
- SVG 页面由当前主执行者逐页手工创作；不得用脚本批量生成页面，也不得把页面创作委派给另一个执行者。
- `svg_output/` 是 SVG 路线完整的可见页面设计源。模板和 design spec 只能约束页面，不能补充 SVG 中缺失的可见内容。
- 用户已经确认的画布、页数、受众、风格、配色、字体、图片策略和动画/旁白结果必须写入项目工件；`spec_lock.md` 与其他说明冲突时以 lock 为准。

## 最小主流程

```text
资料标准化 → 外部项目初始化 → 路由/模板决定 → 策略与 spec_lock
→ 配图准备 → 逐页 SVG → 静态与浏览器检查 → notes/后处理
→ PPTX 导出 → 包结构与几何检查 → 视觉复核 → 交付
```

默认使用 16:9；用户未指定页数、受众或视觉方向时，从材料与用途推断并写入设计工件后继续。只有缺少不可替代的源文件/模板/品牌资产、要求冲突，或操作会移动/覆盖用户原件时才暂停询问。

## 交付合同

最终报告必须包含：项目和 PPTX 的绝对路径、页面数与画布、模板选择依据、图片/旁白能力实际使用情况、确定性门禁结果、仍保留 warning 的理由，以及因凭证、字体、浏览器或本机 Office 能力而未验证的范围。
