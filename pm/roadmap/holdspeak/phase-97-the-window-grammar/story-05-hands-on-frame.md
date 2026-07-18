# HS-97-05 — Hands on the frame

- **Project:** holdspeak
- **Phase:** 97
- **Status:** backlog
- **Depends on:** HS-97-02
- **Unblocks:** HS-97-09

## Problem

The frame under the user's hands is thinner than the chrome implies.
Snap tiles exist but are computed silently on release — no ghost shows
where the window will land, so the feature is undiscoverable. Resize
lives in one bottom-right grip; every other edge is dead. The title bar
ignores the double-click every OS answers with maximize.

## Scope

- In:
  - a snap ghost: while a head drag is inside a snap region, a
    translucent tile preview renders at the exact target rect
    (`snapForPointer` already computes it), disappearing when the
    pointer leaves the region;
  - edge resize: left/right/bottom edges and both bottom corners resize
    (pointer cursors included); the head stays drag-only;
  - double-click on the head toggles maximize/restore (buttons inside
    the head keep their own clicks);
  - unit tests for the new resize math and the ghost's region logic.
- Out:
  - top-edge resize (the head is the handle); keyboard window
    move/resize (recorded as a rider).

## Acceptance criteria

- [ ] Dragging a window into a snap region shows the ghost tile at the
      landing rect; releasing lands exactly on it; leaving the region
      hides it (walk-proven with a mid-drag screenshot).
- [ ] A window resizes from the left edge, right edge, bottom edge, and
      both bottom corners, respecting minima and clamps.
- [ ] Double-click on the head maximizes; again restores.
- [ ] Web suite + guards green.

## Test plan

- vitest for edge-resize math; walk legs for ghost, edges, double-click;
  `npm run check`.

## Evidence required

- Mid-drag ghost shot, resize walk output, suite output.
