<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Confirmation Policy`

## Confirmation Policy

Default behavior: **confirm before generation**.

- Treat explicit skill invocation, a file path, matched signals/presets, and `EXTEND.md` defaults as **recommendation inputs only**. None of them authorizes skipping confirmation.
- Do **not** start Step 4 or later until the user completes Step 3.
- Skip confirmation only when the current request explicitly says to do so, for example: "直接生成", "不用确认", "跳过确认", "按默认出图", or equivalent wording.
- If confirmation is skipped explicitly, state the assumed type / density / style / palette / language / backend in the next user-facing update before generating.
