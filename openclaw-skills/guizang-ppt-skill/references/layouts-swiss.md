# Swiss Layouts

本文件负责选版式与说明使用边界，不再重复维护 22 份长 HTML 示例。

实际代码骨架位于 `templates/swiss-golden-slides.html`，每个版式都由 `<!-- Sxx START -->` / `<!-- Sxx END -->` 标记；完整可运行样张位于 `assets/swiss-golden.html`。版式、动效和必需 class 的机器契约位于 `references/swiss-contract.json`。

## 使用顺序

1. 先读 `references/swiss-layout-lock.md`。
2. 按内容形状从下表选择 `S01-S22`。
3. 从 `templates/swiss-golden-slides.html` 复制对应标记区间。
4. 只替换文案、数据、图片和允许调整的 inline 尺寸，不改 `data-layout`、`data-animate` 与必需 class。
5. 用 `scripts/create-deck.mjs` 组装，再运行 `scripts/validate-swiss-deck.mjs`。

## 共同设计边界

- 一页只使用一个 accent 色；保持直角、纯色、无阴影。
- 顶部标题默认左对齐。只有 S01、S03、S09、S10 和 ASCII 首尾页允许中心或强分屏叙事。
- 中文大标题字重不低于 300；`.t-meta` 只放英文、数字和短 meta。
- 每页内容最低处避开底部 `8vh` 导航安全区。
- SVG 只画几何，不写 `<text>`；标签使用 HTML。
- 本地图片写 `data-image-slot`。先确定槽位和比例，再生成或适配图片。
- 不要把数据版式用于纯概念，也不要为填满图表编造数值。

## 22 个登记版式

| ID | 内容形状 | Recipe | 必需结构 |
| --- | --- | --- | --- |
| S01 | 索引封面 / 主题起手 | `hero` | `.canvas-card` |
| S02 | 2-5 个带量化数据的时间节点 | `progression` | `.timeline-v` `.tl-node` |
| S03 | 一句中心论断 | `statement` | `.canvas-card` + 分词 `<span>` |
| S04 | 6 个等权概念 | `grid-reveal` | `.sub-grid-3-2` `.sub-card` |
| S05 | 3 个层级或阶段 | `stack-build` | `.stack-row` `.stack-block` |
| S06 | 4 项可比量化数据 | `measure-up` | `.bar-towers` `.bar-tower` `.body-block.h-N` |
| S07 | 5-10 项排名或占比 | `bar-grow` | 每条数据独立一个 `.h-bar-chart` |
| S08 | 正好两项 Before/After | `duo-mirror` | `.duo-compare` `.col` `.vrule` |
| S09 | 点阵装饰的一句论断 | `statement` | `.dot-mat` / `.ring-mat` |
| S10 | 整套 deck 的分屏收束 | `split-statement` | `.split-half` `.half` |
| S11 | 4-7 步线性流程 | `timeline-walk` | `.timeline-h` `.tl-row` `.th-node` |
| S12 | 阶段性宣言 + 通栏结论 | `manifesto` | `.manifesto-top` `.ink-banner-full` |
| S13 | 3 个对等力量 / 原则 | `three-forces` | `.three-forces` `.force-card` |
| S14 | 3-5 步闭环 | `loop-form` | `.loop-diagram` `.loop-steps` `.loop-svg` |
| S15 | 8-12 个同类项 + 汇总值 | `matrix-fill` | `.matrix-fill` `.matrix-cell` |
| S16 | 6 条短讯 / tips | `field-notes` | `.brief-grid` `.brief-card` |
| S17 | 严格三层嵌套系统 | `system-diagram` | `.system-diagram` `.sys-stage` `.sys-label` |
| S18 | 3 个论点 + 各自量化支撑 | `why-now` | `.why-now-grid` `.why-col` |
| S19 | 4 个等权特性 | `four-cards` | `.four-cards` `.fc-col` |
| S20 | 3-5 行账单式 KPI | `stacked-ledger` | `.stacked-ledger` `.ledger-row` |
| S21 | 产品规格 / benchmark | `tech-spec` | `.tech-spec` `.spec-kpi-grid` `.spec-bars` |
| S22 | 21:9 主图 + 三项 KPI | `image-hero` | `.image-hero-body` `.image-hero-stats` |

`references/swiss-contract.json` 是 ID、recipe 与必需 class 的唯一登记表。修改版式契约时先改 manifest，再同步模板和 golden slides，并运行 contract 验证。

## 高频错误的正确结构

### S02 Vertical Timeline

- `.tl-node` 自己就是四列 grid：`.dot`、`.yr`、`.multi`、`.desc`。
- 不要添加不存在的 `.tl-axis` 或 `.tl-body`。
- Recipe 固定为 `progression`，不是 `timeline-vertical`。

### S06 KPI Tower

- 容器使用 `.bar-towers`，单项使用 `.bar-tower`。
- 每项包含 `.cap` 和 `.body-block`；数值使用 `.nb`，标签使用 `.lbl`。
- 高度使用 `.h-1` 至 `.h-4`，或 inline `min-height`；不要写无效的 `--h`。
- Recipe 固定为 `measure-up`，不是 `tower-grow`。

### S07 Horizontal Bar

- 每条数据都是一个独立的 `.h-bar-chart`。
- 一行内部依次使用 `.row-lbl`、`.row-track > .row-fill`、`.row-val`。
- 不要把旧版 `.bar-row/.bar-fill` 与新版 `.h-bar-chart` 混用。
- Recipe 固定为 `bar-grow`，不是 `hbar-grow`。

### S11 Horizontal Timeline

- `.timeline-h` 内放一个 `.tl-row`。
- 每个节点是 `.th-node.up|down`，内部为 `.dot` 和 `.label > .yr + .name + .desc`。
- 节点数不是 5 时，在 `.tl-row` 上覆写 `grid-template-columns`。
- 不存在 `.tl-h-node`、`.tl-h-axis`、`.lbl` 这套结构。

### S22 Image Hero

- 主图固定写 `data-image-slot="s22-hero-21x9"`。
- 照片默认 `object-position:center 35%` 或 `center center`，不要用 `top center`。
- 下半区使用 `.image-hero-body` 和 `.image-hero-stats`。
- 主体必须在 21:9 中央安全区；没有真实图片和三项 KPI 时不要选 S22。

## 图片槽位

| 场景 | 槽位 | 规则 |
| --- | --- | --- |
| S22 主图 | `s22-hero-21x9` | 单张 21:9，主体居中 |
| S15 图片矩阵 | `s15-grid-21x9` | 同组统一比例与高度 |
| S16 图片小报 | `s16-brief-21x9` | 同组统一比例与 caption |

按槽位重新生成的图片使用 `.frame-img.r-21x9` 铺满；只有必须保留原始比例的截图才使用 `.fit-contain`。

## 版式选择

- 纯论断：S03 / S09 / S12。
- 3 项定性：S05 / S13；4 项定性：S19；6 项定性：S04 / S16。
- 时间：带数据用 S02；无数据的线性过程用 S11；闭环用 S14。
- 二元对照：S08。
- 数据：4 项高度比较用 S06；排名用 S07；账单 KPI 用 S20；高密度规格用 S21。
- 结构：矩阵用 S15；三层嵌套用 S17。
- 图片：单张主图用 S22；多图放入 S15/S16 的登记网格。
- 收尾：S10，每套 deck 只使用一次。

7-8 页 deck 至少使用 6 个不同 S 编号；10 页以上至少使用 8 个。不要连续 3 页使用同一主体结构。

## 实验版式

P23 Swiss Image Split 和 P24 Swiss Evidence Grid 不属于原始 22 个版式。只有用户明确要求实验结构时才可使用，并在校验时显式传入 `--allow-experimental`。默认使用 S22 或 S15/S16 的图片槽位。
