---
name: guizang-ppt-skill
description: 生成和迭代单文件 HTML 横向演示文稿，支持电子杂志风与瑞士国际主义风，并提供版式契约、静态校验、视觉检查和安全组装脚本。当用户要制作网页 PPT、演讲 slides、杂志风或 Swiss Style deck，或要检查现有 guizang HTML deck 时使用。
metadata: {"openclaw":{"skillKey":"guizang-ppt-skill","emoji":"📐","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/guizang-ppt-skill","requires":{"bins":["node"]}}}
---

# Guizang HTML PPT

生成单文件横向翻页 HTML deck。保留两套互斥视觉系统：

- Style A：电子杂志 × 电子墨水，适合叙事、行业观察和人文分享。
- Style B：瑞士国际主义，适合科技产品、数据汇报和结构化方法论。

来源：本 skill 基于歸藏维护的 [guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill)；上游基线为 `82fe5ae`。来源信息只用于识别，不要写入生成的 deck。

## Required Reads

先确定风格，再只加载对应资料。

### Style A

1. 读 `assets/template.html`。
2. 读 `references/themes.md` 选择主题。
3. 读 `references/layouts.md` 选择布局。
4. 需要组件细节时读 `references/components.md`。

### Style B

1. 读 `references/swiss-layout-lock.md` 和 `references/swiss-contract.json`。
2. 读 `assets/template-swiss.html` 的 `<style>` 与 `RECIPES`。
3. 读 `references/themes-swiss.md` 和 `references/layouts-swiss.md`。
4. 需要地图时再读 `references/swiss-map-component.md`。

处理图片或截图时按需读 `references/image-prompts.md` 和 `references/screenshot-framing.md`。交付前读 `references/checklist.md`。

## 缺少输入或工具时

- 用户没选风格时，先问：`选电子杂志风（Style A）还是瑞士国际主义（Style B）？` 风格确定后再读取对应模板。受众、页数、主题色没有写时，从原始材料和用途推断，并把采用的值写进页面规划；不要逐项追问。
- 需要用户回答时直接提问；不要为不同模型、IDE 或运行产品写不同分支。
- 需要新配图或重绘截图时，先看本轮工具列表中是否有图像生成或编辑工具。有则按该工具的参数调用；没有则复用用户素材或 skill 资产，并在交付说明中列出仍缺的图片。

## Workflow

1. 先确定 Style A/B，再明确受众、时长、原始素材、图片需求、主题色和硬约束。风格未定时使用上面的固定问句；其余未提供项按上面的默认规则处理。
2. 先列 `页码 → 版式 → 选择原因 → 图片槽位 → data-animate`。Style B 的正文页只能使用 `S01-S22`；实验版式必须得到用户明确许可。
3. 从对应 layouts 复制骨架。不要混用 Style A/B 类名，不要发明未在模板 CSS 中定义的类。
4. 先把所有 `<section>` 放入独立的 `slides.html`，再用安全组装脚本生成最终 deck，避免误删模板底部运行时：

```bash
node {baseDir}/scripts/create-deck.mjs \
  --style swiss \
  --title "演示标题" \
  --slides ./slides.html \
  --output ./ppt/index.html
```

Style A 将 `--style swiss` 改成 `--style magazine`。

5. Style B 必须运行静态校验：

```bash
node {baseDir}/scripts/validate-swiss-deck.mjs ./ppt/index.html
```

6. 运行四视口视觉审计。检查项：元素重叠、页面/容器越界、底部安全区、内容只挤在局部。CSS class 与 recipe 仍由上一步检查：

```bash
node {baseDir}/scripts/visual-check-swiss.mjs ./ppt/index.html --output ./ppt/visual-check
```

按退出码处理：

- `0`：通过。
- `1`：修复页面问题，再运行一次。
- `2`：缺少 Playwright 或浏览器。原样报告错误；不要安装软件，不要改成单视口检查。

7. 在浏览器逐页检查标题层级、底部导航安全区、深色背景对比度、图片裁切、动画终态和 ESC 索引页。

## Style B Contract

- 每页必须写 `data-layout` 和 `data-animate`；组合必须匹配 `references/swiss-contract.json`。
- `data-animate` 必须是模板 `RECIPES` 的真实键名。未知 recipe 是错误，不得依赖 fallback fade。
- HTML class 必须在模板 CSS 或 deck 自己的 `<style>` 中存在。校验器会拒绝未定义 class。
- 模板运行时、`SLIDES_START/SLIDES_END` 标记、导航、低功耗模式和脚本尾部必须保留。
- 本地图片必须存在并写 `data-image-slot`。S22 主图固定为 `s22-hero-21x9`。
- SVG 只画几何，不放可见 `<text>`；文字标签使用 HTML。
- 中文大标题使用 `var(--sans),var(--sans-zh)`，字重不低于 300；`.t-meta` 只放英文/数字 meta。
- 深色或 accent 背景上的文字必须显式使用可读反色。
- 禁止非零圆角、阴影和内容层渐变；所有正文内容避开底部 `8vh` 导航安全区。

## Output Contract

- 输出可直接打开的单 HTML deck，图片使用相对路径。
- 替换所有 `[必填]` 占位符。
- Style B 以静态校验通过为最低交付条件；截图检查不可用时明确说明只完成静态验证。
- 不把维护说明、来源、赞助或校验日志写进 deck 页面。
