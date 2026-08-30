<!-- GENERATED FILE: do not edit. Source: ../../upstream/SKILL.md -->

Source section: `Mandatory connector rules`

### Mandatory connector rules

These six rules are **non-negotiable**. Run the pre-output checklist (§9) to verify before producing any diagram.

1. **Rounded right-angle (orthogonal) connectors are mandatory.** Never use diagonal `<line>` or straight slanted paths between nodes that don't share an x or y axis. Every bend must be a quarter-arc with `r=8` (or `r=6` minimum for tight layouts). See `references/type-architecture.md` for the elbow-path formula. Reserve plain straight `<line>` only for connections whose endpoints share the same x or y coordinate. Diagonal connectors are an automatic fail.

2. **Label-to-connector margin: 6–10px gap, always.** A label must never sit *on* its arrow — the connector must remain visible. Place the label centered above (or beside, for vertical segments) the line with a **minimum 6px gap** between the bottom of the label's mask rect and the connector stroke. The opaque mask rect prevents the arrow from bleeding through, but the *visible* gap between mask edge and line preserves the reader's ability to trace the connection. If the label is large enough that 6px feels cramped, push it to 8–10px. Never let the mask rect touch or overlap the stroke.

3. **No overlapping connectors.** Two connectors must never share the same stroke path, run parallel on top of each other, or be drawn on top of each other for any segment. When two orthogonal arrows must cross at a single point, apply the **bridge / hop** primitive (see `references/type-architecture.md` § Crossing arrows). When two arrows naturally want to overlap, offset their routing by ≥12px so each line is independently traceable. If you find yourself stacking connectors, redesign the layout — it means two nodes are too close, or the diagram is over budget (split into overview + detail).

4. **Shared edge → fan the attach points.** When two or more connectors enter or exit the *same edge* of a box, each must have its own distinct attach point along that edge — **no two connectors may share a single point on a box**. Spread the attach points evenly along the edge with **≥12px** between adjacent points (8px minimum for very small boxes). Routing rules:
   - For N connectors on an edge of length L, attach point `k` (1..N) sits at offset `L * k / (N + 1)` from the edge's leading corner.
   - When the connectors fan out to destinations on different sides, route each one orthogonally from its own attach point — no merging strokes near the box.
   - When two parallel connectors run in the same direction, keep them ≥12px apart along their entire length, not just at the attach point. Each arrow must remain independently traceable end-to-end.

   No connector may hide another. If you can't tell two arrows apart at a glance, the layout has failed.

5. **A connector must not pass behind a box that isn't its source or destination — except when the box is geometrically unavoidable on a direct orthogonal path.** Reroute around intervening boxes by default. The only legitimate exception is when a cross-cutting node (e.g., a footer service, a horizontal layer bar) physically sits between the connector's source and destination on the only straight path between them — for example, a `METRICS` arrow exiting an `Observability` footer bar and rising into a zone above must cross the `Active Directory` footer bar that sits between them. In that exception:
   - The stroke must be **dashed** (e.g., `stroke-dasharray="4,3"`) to signal "transit, not interaction" — it tells the reader the intervening box is not an endpoint.
   - The label sits at the **visible end** of the connector (typically near the source) so it doesn't fall behind the intervening box.
   - No marker (arrowhead) may land on the intervening box's edge — the marker resolves at the true destination only.

   When in doubt, reroute. The exception exists for the narrow case where rerouting is geometrically impossible, not as a shortcut to avoid layout work.

6. **A label mask must not overlap a node drawn after it.** Rule 2 keeps the label off its own connector; this one keeps it off the boxes. Because nodes are painted after labels, a mask that lands partly inside a node is covered by the node fill and the text renders as a fragment sitting on the node border. Place the label on a segment of the connector that runs through open canvas — for a connector leaving a node's right edge, that means clearing the node's `x + width` before the mask starts. A mask fully *inside* a node is a badge chip and is fine; a mask overlapping a zone container is fine too, since zones are painted first. From a repository checkout, verify with `python3 <repo-root>/scripts/verify-geometry.py <file>`.
