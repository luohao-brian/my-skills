<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Exporting to PNG / SVG`

### Exporting to PNG / SVG

When the user asks to export, save, rasterize, or convert a generated diagram to `.png` or `.svg`, load [`references/export.md`](../../upstream/references/export.md) and follow the procedure there. Run the packaged helpers `scripts/export_svg.py` and `scripts/export_png.py`; the reference owns their arguments and availability checks. Both formats deliver the diagram only (the `<svg>` node) — editorial wrappers like cards and headers are dropped by design. Export is **manual** — never produce export files unprompted.

For an imported diagram, pixel dimensions come from the `viewBox` × scale factor, so its size decision belongs to §11, not to export. For any diagram that needs an exact frame (an OG card or a slide image), see [`export.md` § Sizing the export](../../upstream/references/export.md).
