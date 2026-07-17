---
name: ppt-master
description: 将 PDF、DOCX、PPTX、网页、Markdown 或主题资料生成可编辑 SVG/PPTX 演示文稿，也可填充模板、美化既有 PPTX、添加动画与旁白。用户要求创建、制作、优化、检查或导出 PPT/演示文稿，提到 ppt-master，或需要 SVG 页面与 PowerPoint 互转时使用。
metadata: {"openclaw":{"skillKey":"ppt-master","emoji":"📊","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/ppt-master","requires":{"anyBins":["python3","python"]}}}
---

# PPT Master

把 SVG 作为页面设计源，经过静态契约检查、浏览器几何检查和原生 PPTX 检查后发布。

## 先读

1. 始终读取 `references/openclaw-runtime.md`，确定外部项目目录、依赖和发布门禁。
2. 读取 `workflows/routing.md`，按输入和用户意图选择主流程或独立 workflow。
3. 新建 SVG/PPTX 演示时读取 `references/upstream-pipeline.md`；只读取其中当前阶段直接引用的详细 reference。
4. 处理现有 PPTX、模板、动画或旁白时，只读取 routing 指定的 workflow 及其直接引用，不要预加载完整主流程。

## 缺少输入或工具时

- 用户只说“做一份 PPT”时，默认使用 16:9 画布并交付可编辑 PPTX；页数、受众和视觉方向从原始材料与用途推断，写入 `design_spec.md` 后继续。只有源文件打不开、用户点名的模板或品牌素材未提供、要求互相冲突，或下一步会移动/覆盖用户原件时，才暂停并询问。
- 需要用户回答时直接提问；不要为不同模型、IDE 或运行产品写不同分支。
- 需要搜索、读取网页、生成图片、检查浏览器页面或委派任务时，只调用本轮工具列表里真实存在的工具名。没有对应工具就执行相关 workflow 写明的替代步骤；没有替代步骤则报告哪一步未完成。
- AI 配图必须调用本轮可用的通用图片生成工具。不要选择图片 provider、模型、API 或密钥；没有图片生成工具时停止 AI 配图步骤并报告缺少该能力。
- 旁白必须调用本轮可用的通用 TTS 工具。不要选择 TTS provider、模型、音色或密钥；没有 TTS 工具时停止旁白步骤并报告缺少该能力。

## 不可破坏的边界

- 使用 `{baseDir}` 解析 skill 内脚本、模板和 references；不要假设 cwd 中存在 `skills/ppt-master`。
- 项目、截图、预览、备份和导出必须写入用户指定的绝对路径；未指定时写入仓库外的 workspace 或系统临时目录。禁止在 `{baseDir}` 或当前源码仓库创建 `projects/`、`outputs/`、`.preview/` 或导出文件。
- SVG 生成保持当前主执行者、逐页、顺序执行；每页写入前重新读取项目 `spec_lock.md`。
- `svg_output/` 是生成式路径的页面设计真相来源。模板和设计说明只能约束页面，不能补上 SVG 中缺失的可见内容。
- SVG 使用内联属性。禁止 `<style>`、`class`、外部 stylesheet 和未被转换器支持的 CSS/视觉属性。
- 用户确认过的画布、页数、受众、风格、配色、图标、字体和图片策略必须写入 `design_spec.md` 与 `spec_lock.md`；两者冲突时以 `spec_lock.md` 为准。
- 不用批处理脚本代替逐页设计。确定性脚本只负责转换、检查、后处理和导出。

## 最小主流程

```text
资料标准化 → 外部项目初始化 → 策略确认与 spec_lock → 逐页 SVG
→ 静态检查 → 浏览器多视口几何检查 → notes
→ finalize → PPTX 导出 → 原生 PPTX 几何检查
```

初始化时强制指定仓库外目录：

```bash
python3 {baseDir}/scripts/project_manager.py init <name> --format ppt169 --dir <absolute-projects-root>
```

源文件通过 `scripts/source_to_md.py` 标准化；需要归档进项目时传绝对项目路径。移动用户原件前必须确认用户确实授权移动，否则使用 `--copy`。

## 发布门禁

所有 SVG 完成后，先运行：

```bash
python3 {baseDir}/scripts/project_manager.py validate <project>
python3 {baseDir}/scripts/svg_quality_checker.py <project>
python3 {baseDir}/scripts/visual_layout_audit.py <project>
```

必须检查并处理：

- 文字或视觉元素互相遮挡；
- 元素越出 SVG 画布、浏览器窗口或容器型分组；
- `viewBox`、内联 style、字体、颜色或转换器能力不匹配；
- 多视口缩放后溢出、裁切、零尺寸或异常变形；
- 内容只挤在局部、画布利用明显不足，或紧贴多侧边缘。

任一 error 未解决不得导出。warning 必须修复、确认是有意留白/叠放，或在交付说明中记录；不得静默跳过。

通过后按顺序运行，不能合并步骤：

```bash
python3 {baseDir}/scripts/total_md_split.py <project>
python3 {baseDir}/scripts/finalize_svg.py <project>
python3 {baseDir}/scripts/svg_to_pptx.py <project>
python3 {baseDir}/scripts/pptx_layout_audit.py <project>/exports/<deck>.pptx
```

原生 PPTX 检查失败时修改 `svg_output/`，重新执行静态与浏览器检查，再 finalize/export；不要直接在导出包里掩盖源问题。

## 交付

只交付外部项目目录中的最终 PPTX、必要的预览和检查报告。报告包括：页数、画布、三个门禁的结果、仍保留的 warning 及理由、最终绝对路径。依赖浏览器、外部凭证或字体而无法完成的检查要明确标注未验证范围。
