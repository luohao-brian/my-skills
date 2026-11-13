<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Confirmation Policy`

## Confirmation Policy

Default: **confirm before generation**.

- Explicit skill invocation, a file path, a matched keyword shortcut, `EXTEND.md` defaults, and the documented default combination are recommendation inputs only — none authorizes skipping confirmation.
- Do not start Step 5 or Step 6 until the user confirms the combination/aspect/language/backend choices.
- Skip confirmation only when the current request explicitly says so: `--no-confirm`, "直接生成", "不用确认", "跳过确认", "按默认出图", or equivalent. Then state the assumed combination/aspect/language/backend in the next user-facing update before generating.
