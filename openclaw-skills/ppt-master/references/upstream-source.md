# Upstream Source

This skill derives its core workflow and scripts from [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) at commit `6b42a6a652f9d6e9fc0c81e634c9fdfe771eee10` (2026-07-31). The machine-readable baseline and reviewed exclusions live in `../upstream.lock.json`.

The OpenClaw distribution keeps the upstream `LICENSE`, attribution, and sponsor files. It intentionally overlays:

- single-line OpenClaw metadata and `{baseDir}` script references;
- absolute runtime-workspace project roots instead of repository-local `projects/`;
- runtime-neutral image/TTS manifests instead of bundled provider backends;
- browser SVG and exported-PPTX audits used by the local release gate;
- target-host font discovery, explicit SVG-to-PowerPoint typeface parity, and
  a role-aware readability gate that prevents body copy from silently falling
  into footnote/source-size bands.

Upstream commits after this baseline add an independent-identity guard that forbids these integration points. They are not applied to this OpenClaw package because doing so would break its declared runtime contract.

For every upstream review, run this from the `my-skills` repository root:

```bash
python3 scripts/ppt_master_upstream.py --fail-on-new
```

The planner reconstructs an effective upstream tree with recorded exclusions removed, then compares the canonical baseline, the local OpenClaw overlay, and that effective tree. Apply `safe_upstream` paths mechanically; review every `conflict`; preserve `local_overlay` paths and every `required_local_contracts` item. After integration, run `bash scripts/verify-all.sh`, the font/readability regression tests, and the documented PowerPoint render review before advancing `reviewed_through`.
