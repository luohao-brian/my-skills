<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Confirmation Policy`

## Confirmation Policy

Default behavior: **confirm before generation**.

- Treat explicit skill invocation, a file path, a matched keyword shortcut, `EXTEND.md` defaults, and the documented default combination as **recommendation inputs only**. None of them authorizes skipping confirmation.
- Do **not** start Step 5 or Step 6 until the user confirms the combination/aspect/language/backend choices.
- Skip confirmation only when the current request explicitly says to do so, for example: `--no-confirm`, "直接生成", "不用确认", "跳过确认", "按默认出图", or equivalent wording.
- If confirmation is skipped explicitly, state the assumed combination/aspect/language/backend in the next user-facing update before generating.
