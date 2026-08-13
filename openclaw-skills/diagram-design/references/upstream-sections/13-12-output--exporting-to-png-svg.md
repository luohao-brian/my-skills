<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Exporting to PNG / SVG`

### Exporting to PNG / SVG

When the user asks to export, save, rasterize, or convert a generated diagram to `.png` or `.svg`, load [`references/export.md`](../../upstream/references/export.md) and follow the procedure there. Both formats deliver the diagram only (the `<svg>` node) — editorial wrappers like cards and headers are dropped by design. Export is **manual** — never produce export files unprompted.

For an imported diagram, pixel dimensions come from the `viewBox` × scale factor, so its size decision belongs to §11, not to export. For any diagram that needs an exact frame (an OG card or a 1920×1080 slide image), see [`export.md` § Sizing the export](../../upstream/references/export.md).
