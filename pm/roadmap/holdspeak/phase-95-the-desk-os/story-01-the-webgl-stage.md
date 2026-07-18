# HS-95-01 — The WebGL stage

- **Project:** holdspeak
- **Phase:** 95
- **Status:** ready
- **Depends on:** —
- **Unblocks:** HS-95-03 (dock composites over the stage), HS-95-10

## Problem

The desk world is DOM/CSS: zones, object sprites, drag ghosts, ambient
effects are all absolutely-positioned elements, so every pan, drag, and
hover is layout/paint work on the main thread. The only canvas in the desk
is `Stage.tsx`, a 78-line 2D-context mote background. The owner's verdict
from the live sitting: the experience is clunky and must be WebGL
accelerated with native-like feel.

## Scope

- In:
  - a WebGL-backed scene graph (PixiJS v8 or equivalent; WebGL2 required,
    WebGPU welcome where available) rendering the world layer: room
    backdrop, zones, object sprites and their states, selection/hover
    affordances, drag ghosts, ambient motes/glow;
  - a single coordinate system shared between the GPU world and the DOM
    overlay (windows, text editors) so a window can anchor to an object;
  - pointer input unified through the existing `@use-gesture` handlers
    driving the scene graph instead of element styles;
  - sprite atlas/asset pipeline for the existing `_built` desk art;
  - the DOM world renderer deleted once parity is proven (no dual
    maintenance; this product is pre-release).
- Out:
  - window content rendering (windows stay DOM, composited above);
  - new art or world semantics (same primitives, same store, same
    projections — `desk/store.ts` and `desk/projections.ts` are the truth
    the renderer draws);
  - Swift/native renderers.

## Acceptance criteria

- [ ] The world layer renders through WebGL; DevTools shows no per-frame
      layout/paint attributable to world pan, object drag, or ambient
      motion.
- [ ] Everything a desk primitive shows today (kind sprite, label, state,
      selection, zone membership, filing) renders identically from the same
      store; the desk store and projection tests pass unmodified.
- [ ] Object drag, zone drag, pan, hover, tap-to-open behave as today
      (including the 3px tap threshold contract) through the scene graph.
- [ ] A window can anchor to a world object and stay glued through pan and
      resize (shared coordinate transform proven by test).
- [ ] Sustained 60fps (median frame ≤ 16.7ms, p95 ≤ 33ms) during a scripted
      drag-and-pan storm on a desk seeded with the UAT `seeded-desk` recipe,
      measured on the production bundle via CDP tracing.
- [ ] The DOM world renderer is gone; the bundle carries one renderer.
- [ ] Phone viewport (393px) renders and interacts correctly with
      devicePixelRatio handling (no blurry sprites, no offset taps).

## Test plan

- `npm --prefix web test` — store/projection suites unmodified and green.
- New renderer unit tests: coordinate transform round-trips, scene-graph
  diffing from store snapshots, DPR handling.
- Playwright production walk driving drag/pan/open against the real hub with
  CDP tracing capturing frame timings (the performance criterion's proof).
- `uv run pytest -q tests/ -k web` — hub-served bundle smoke unaffected.

## Implementation direction

- The store stays the single source of truth; the renderer is a projection.
  Do not move state into the scene graph.
- Prefer PixiJS v8 (mature WebGL2/WebGPU, sprite batching, React interop via
  a thin custom reconciler-free mount — one canvas, imperatively synced from
  zustand subscriptions). Avoid react-three-fiber; this is 2D compositing.
- Keep the mote/glow ambience but move it into the same scene graph;
  `Stage.tsx` retires.
- Text-heavy affordances (editors, pullout content) remain DOM; only the
  world becomes GPU. The z ladder gains one documented rule: canvas at the
  bottom, windows above, chrome above windows.
- Measure with the production build only (`npm --prefix web run build`); dev
  overlays lie about frame cost.

## Evidence required

- captured test runs (web suites + new renderer tests);
- CDP frame-timing capture from the seeded-desk storm walk, with the median
  and p95 stated;
- before/after screenshots at 1440 and 393 showing parity;
- the commit removing the DOM world renderer.
