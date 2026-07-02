---
name: popular-web-designs
description: Browse and use 54 HTML/CSS website design templates for landing pages, dashboards, and UI prototypes in known visual styles such as Stripe, Linear, Vercel, Notion, Apple, Airbnb, and Figma. 当用户询问有哪些 HTML 设计模板、想查看模板目录，或要求按某个知名网站风格生成/改造 UI 时使用。
homepage: https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/popular-web-designs
metadata: {"openclaw":{"skillKey":"popular-web-designs","emoji":"🎨","homepage":"https://github.com/luohao-brian/my-skills/tree/main/openclaw-skills/popular-web-designs"}}
---

# Popular Web Designs

54 real-world design systems ready for use when generating HTML/CSS. Each template captures a site's complete visual language: color palette, typography hierarchy, component styles, spacing system, shadows, responsive behavior, and practical agent prompts with exact CSS values.

## Required Reads

- Read [references/catalog.md](references/catalog.md) when choosing a template.
- Read [references/workflow.md](references/workflow.md) before generating HTML/CSS from a template.
- Read exactly one relevant `templates/<site>.md` file before generating or restyling UI. Read more only when comparing multiple style directions.

## How to Use

1. Pick a design from `references/catalog.md`.
2. Read `templates/<site>.md` for that design.
3. Use the design tokens and component specs when generating HTML/CSS.
4. Use the current agent environment's available file, preview, and verification workflow.

For catalog-only requests such as "what HTML design templates are available", read `references/catalog.md`, summarize the templates by category, and stop.

Each template includes an **Implementation Notes** block at the top with:

- CDN font substitute and Google Fonts `<link>` tag.
- CSS font-family stacks for primary and monospace.
- Portable notes for applying the template in the target project or local HTML artifact.

## Source

The template content is adapted from real website design notes sourced from VoltAgent's public design-note collection and normalized for portable HTML/CSS generation.
