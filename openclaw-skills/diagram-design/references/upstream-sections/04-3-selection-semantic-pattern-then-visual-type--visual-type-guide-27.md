<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Visual-type guide (27)`

### Visual-type guide (27)

| If you're showing… | Use | Reference |
|---|---|---|
| Components + connections in a system | **Architecture** | [type-architecture.md](../../upstream/references/type-architecture.md) |
| Legacy IT landscape grouped by phase/department; documents the *before* state in modernization proposals | **IT current-state** | [type-it-state.md](../../upstream/references/type-it-state.md) |
| Decision logic with branches | **Flowchart** | [type-flowchart.md](../../upstream/references/type-flowchart.md) |
| Time-ordered messages between actors | **Sequence** | [type-sequence.md](../../upstream/references/type-sequence.md) |
| States + transitions + guards | **State machine** | [type-state.md](../../upstream/references/type-state.md) |
| Entities + fields + relationships | **ER / data model** | [type-er.md](../../upstream/references/type-er.md) |
| Events positioned in time | **Timeline** | [type-timeline.md](../../upstream/references/type-timeline.md) |
| Cross-functional process with handoffs | **Swimlane** | [type-swimlane.md](../../upstream/references/type-swimlane.md) |
| Two-axis positioning / prioritization | **Quadrant** | [type-quadrant.md](../../upstream/references/type-quadrant.md) |
| Multiple entities scored across 3–5 quantitative criteria | **Radar / Spider** | [type-radar.md](../../upstream/references/type-radar.md) |
| Reinforcing cycle / flywheel where the last step feeds the first and a shared hub accumulates state | **Loop** | [type-loop.md](../../upstream/references/type-loop.md) |
| Hierarchy through containment / scope | **Nested** | [type-nested.md](../../upstream/references/type-nested.md) |
| Parent → children relationships | **Tree** | [type-tree.md](../../upstream/references/type-tree.md) |
| Human/agent/team ownership, reporting, routing, escalation | **Org chart** | [type-org-chart.md](../../upstream/references/type-org-chart.md) |
| Stacked abstraction levels | **Layer stack** | [type-layers.md](../../upstream/references/type-layers.md) |
| Overlap between sets | **Venn** | [type-venn.md](../../upstream/references/type-venn.md) |
| Ranked hierarchy or conversion drop-off | **Pyramid / funnel** | [type-pyramid.md](../../upstream/references/type-pyramid.md) |
| Quantitative comparison across categories | **Bar chart** | [type-bar.md](../../upstream/references/type-bar.md) |
| Continuous trends over time | **Line chart** | [type-line.md](../../upstream/references/type-line.md) |
| Tasks and phases on a timeline | **Gantt** | [type-gantt.md](../../upstream/references/type-gantt.md) |
| Distribution and correlation between two variables | **Scatter plot** | [type-scatter.md](../../upstream/references/type-scatter.md) |
| End-to-end data stack on a container cluster | **High-Level** | [type-high-level.md](../../upstream/references/type-high-level.md) |
| Multi-actor sequential process with data handoffs | **Process** | [type-process.md](../../upstream/references/type-process.md) |
| Multi-tier data storage with quality levels and access policies | **Medallion** | [type-medallion.md](../../upstream/references/type-medallion.md) |
| Role-scoped data flow: who does what at each pipeline step | **Data flow** | [type-data-flow.md](../../upstream/references/type-data-flow.md) |
| Integration topology of a data platform — sources → core → consumers | **DP integration** | [type-dp-integration.md](../../upstream/references/type-dp-integration.md) |
| Per-role / per-component access permissions matrix | **DP security matrix** | [type-dp-security-matrix.md](../../upstream/references/type-dp-security-matrix.md) |

Rules of thumb:

- If a 3-column table communicates the same thing, pick the table.
- If two types seem useful, pick the dominant axis; a semantic pattern may add behavior-specific primitives, not a second layout grammar.
- If you're past the complexity budget (§7), split into an overview + detail.

**Always load the chosen `references/type-*.md` before drawing.** When routed above, also load `semantic-patterns.md`; when animation is chosen, load `animation.md`.
