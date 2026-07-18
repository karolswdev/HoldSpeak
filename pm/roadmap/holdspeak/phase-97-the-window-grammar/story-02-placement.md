# HS-97-02 — A window lands well

- **Project:** holdspeak
- **Phase:** 97
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-97-09

## Problem

New windows pile onto the top-left corner with a 26px cascade, clipping
each other's title bars while most of the stage is empty. Placement
clamps only during drag, never on open: the audit caught the Dictation
window spawning partially off-screen left and the Delivery board
opening mostly below the viewport. An OS's first law is that a window
appears somewhere sensible, whole, and visible.

## Scope

- In:
  - an open-placement engine in the window layer: a window opening
    without a persisted rect lands fully on-viewport inside the working
    band (below the chrome, clear of the dock), positioned by a
    min-overlap scan against the already-open windows (center-weighted
    when the stage is free); the cascade survives only as the
    saturation fallback;
  - clamp-on-open for every path that produces a rect (defaults,
    persisted rects from a smaller viewport, snap tiles);
  - the Delivery board's and any other CSS-default-corner spawn made
    sane through the same engine;
  - unit tests pinning the engine (free stage centers; occupied stage
    avoids overlap; saturated stage cascades; nothing ever lands
    outside the band).
- Out:
  - focus/z changes (HS-97-04), snap preview (HS-97-05), dock
    (HS-97-07).

## Acceptance criteria

- [x] Opening 1..5 windows in sequence on a 1440x900 stage lands every
      one fully on-viewport with no title-bar overlap until the stage
      saturates — proven by a live Playwright leg with screenshots.
- [x] A persisted rect from a larger viewport is clamped whole into the
      current one on open.
- [x] The engine is pinned by unit tests; the walk leg passes on the
      production bundle.
- [x] Web suite + guards green.

## Test plan

- vitest for the engine; the new placement walk leg in
  `scripts/desk_gl_walk.py`; `npm run check`.

## Evidence required

- Engine tests, walk output, before/after shots of a 3-window open
  sequence.
