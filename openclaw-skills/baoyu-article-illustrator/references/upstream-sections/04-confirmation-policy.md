<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Confirmation Policy`

## Confirmation Policy

Default: **confirm before generation**.

- Explicit skill invocation, a file path, matched signals/presets, and `EXTEND.md` defaults are recommendation inputs only — none authorizes skipping confirmation.
- Do not start Step 4 or later until the user completes Step 3.
- Skip confirmation only when the current request explicitly says so ("直接生成", "不用确认", "跳过确认", "按默认出图", or equivalent). Then state the assumed type / density / style / palette / language / backend in the next user-facing update before generating.
