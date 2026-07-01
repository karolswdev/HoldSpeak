# Evidence — HS-71-04: Free placement + the layout store

**Date:** 2026-07-01
**Verdict:** done. The desk is arranged by hand now, the way the iPad desk is:
objects live at a unit-space position, drag to move them, and the arrangement
persists per-device. Objects also grew for more presence.

## What shipped

- **`web/src/scripts/desk-app.js`**:
  - `positions` (unit-space `{x,y}` per object id) + `loadPositions()` /
    `savePositions()` — persisted to `localStorage["hs.diorama.pos"]`, the web
    analog of the iPad's local `positions`. **Local-only, never synced** (matches
    the iPad contract; no API).
  - `objUnit(o,i,n)` — a saved drag position when present, else `looseHome` (the
    density-aware grid: more items → more columns, per-object jitter, clamped to a
    usable band). `objStyle` now reads it.
  - `startObjDrag(o,i,n,$event)` — a pointer drag that updates the object's unit
    position live (delta ÷ stage rect, clamped `0.04..0.96`) and persists on
    release; tracks movement (>4px) so a plain click (open, HS-71-06) is not
    swallowed. `justDragged(o)` exposes the drag-vs-click verdict.
  - `tidyDesk()` — clears saved positions back to the auto-layout.
- **`web/src/pages/desk.astro`**:
  - the object gains `@pointerdown="startObjDrag(...)"` + a `dragging` class
    (grab/grabbing cursor; the float freezes while dragging so it doesn't fight
    the pointer); `touch-action: none` for touch drag.
  - a **"Tidy"** header button (shown only when positions exist) resets the layout.
  - objects enlarged for presence (sprite 76→88px, lift 84→96px, footprint
    112→128px) and the world row height bumped to match.

## Proof

- **Drag persistence (Playwright):** dragging the first object saved
  `{"m0":{"x":0.31,"y":0.29}}` to `localStorage["hs.diorama.pos"]`, and the
  position **persisted across a full reload** (`persisted after reload: yes`).
  The drag did not open the object (movement threshold).
- **`screenshots/04-arranged.png`** — a hand-arranged 11-object desk with the
  larger objects and the dragged cassette repositioned; the "Tidy" control
  present in the header.
- **Tests:** route pre-flight **2 passed** (zero page errors on `/desk`); full
  suite **3045 passed, 37 skipped**; build green.
