# HS-71-04 — Free placement + the layout store

- **Status:** done
- **Priority:** MED
- **Depends on:** HS-71-03
- **Evidence:** [evidence-story-04.md](./evidence-story-04.md)

## Goal

Let the desk be arranged by hand, the way the iPad desk is: objects live at a
unit-space position, drag to move them, and the arrangement persists per-device.

## Scope

- A **position store**: `positions[id]` in unit space (0..1), persisted to
  `localStorage` under `hs.diorama.pos` (the web analog of the iPad's local
  `@AppStorage`; **no API, geometry never syncs** — matches the iPad contract).
- **Drag to arrange** — pointerdown on an object → drag updates its position
  (delta ÷ stage size), clamped to the usable band, live; pointerup persists.
  Guard against the drag stealing clicks meant to open the object (threshold).
- **Density-aware auto-layout** for untouched objects — the web port of
  `looseHome`: more items → more columns, and objects shrink toward a usability
  floor (`densityScale`) so a full desk spreads to the floor instead of piling.
- A quiet "tidy" affordance to reset positions to the auto-layout.

## Proof required

A Playwright drag proof: an object dragged to a new spot stays there, persists
across reload (localStorage), and does not open on drag; a screenshot of a
hand-arranged desk; a screenshot of a dense desk auto-spreading + shrinking.

## Done

Shipped and proven. `positions` (unit-space `{x,y}` per id) persist to
`localStorage["hs.diorama.pos"]` (local-only, never synced); `objUnit` uses a
saved position or `looseHome` (density-aware); `startObjDrag` is a pointer drag
(clamped, persists on release, movement threshold so a click still opens);
`tidyDesk` + a header "Tidy" button reset it. Objects enlarged for presence.
Playwright: a drag saved `{m0:{x,y}}` and persisted across reload. Route
pre-flight 2 passed; suite green. See [evidence-story-04.md](./evidence-story-04.md).
