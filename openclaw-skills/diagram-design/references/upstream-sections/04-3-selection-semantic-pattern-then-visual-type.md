<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `3. Selection: semantic pattern, then visual type`

## 3. Selection: semantic pattern, then visual type

When behavior, state, enforcement, or risk carries the meaning, first load [`references/semantic-patterns.md`](../../upstream/references/semantic-patterns.md) and choose one primary pattern. Then choose the nearest visual type for layout. If no pattern matches, choose the type directly.

| Behavioral trigger | Semantic pattern → nearest type |
|---|---|
| Fan-in, queue depth, finite capacity, bottleneck | **Fan-in queue / bottleneck** → Data flow |
| Repeated Question / Input / Governance / Output slots across stages | **Stage framework with semantic slots** → Process |
| Conversation or loose input becomes a structured durable artifact | **Unstructured input → structured artifact** → Data flow |
| Two rule traces need pass/fail/skipped/not-reached and first divergence | **Paired policy-evaluation traces** → Flowchart |
| Trust boundaries plus permitted/forbidden ingress or deploy paths | **Secure paved road** → Architecture |
| Controls grouped by where they are enforced | **Governance / control catalog** → Layer stack |
| Defenses compensate for prior gaps and residual risk propagates | **Compensating security layers** → Layer stack |

The pattern owns semantic primitives and its tighter budget; the type owns layout grammar. Use [`references/animation.md`](../../upstream/references/animation.md) only when motion is requested or materially clarifies ordered change; static remains the default.
