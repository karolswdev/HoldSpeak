# HS-98-01 — The surface idiom

- **Project:** holdspeak
- **Phase:** 98
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-98-02..07

## Problem

There is no desk-native way to build window content. Cores compose
Signal `Panel` cards on `page-grid` — a page grammar with its own
chrome, reflowing on viewport media queries. Nothing in the codebase
lets a core say "a dense list on the window material that reflows with
the window". Until that idiom exists, every re-crafted core would
invent its own, and fourteen private idioms is how we got here.

## Scope

- In:
  - the idiom SPECCED first: a "The surface idiom" section in
    `docs/internal/DESIGN_SYSTEM.md` naming the six rules (one
    material, window-as-viewport, denser scale, honest rows, verbs
    have homes, one state grammar) in token vocabulary;
  - surface density tokens in `web/design-tokens.json` (component
    layer: row height, paddings, section gap, body/label sizes) —
    generated, gated, never raw literals;
  - the kit `web/src/desk/surface/` + `surface.css`: `SurfaceSection`
    (hairline + quiet label, no card), `SurfaceRows`/`SurfaceRow`
    (dense list rows, hover wash, revealed row verbs, title + detail
    slots), `SurfaceVerbs` (one sticky verb bar), `SurfaceState`
    (loading/empty/error, one quiet treatment), `SurfaceSplit`
    (master–detail that collapses by container width), `MetricStrip`;
  - `.desk-surface-body` becomes a size container
    (`container-type: inline-size`); the kit reflows via `@container`
    only;
  - formatters: `humanTime`, `humanValue` (omit unknowns, de-snake
    labels) shared by all cores;
  - the seam guard `tests/unit/test_native_surfaces_guard.py`:
    forbidden page-grammar tokens (`page-grid`, `span-`, `data-list`,
    `data-row`, `signal-eyebrow`, `Panel`, `button-row`, `code-block`,
    `metric`, `dialog-form`) in `web/src/pages/cores/`, with a
    per-file allowlist seeded at today's truth that only shrinks;
  - one core proven in the kit end to end as the reference: Cadence
    (smallest real core with lists, verbs, and states) converts here.
- Out:
  - the other thirteen cores (HS-98-02..07); CSS pruning (HS-98-07).

## Acceptance criteria

- [ ] DESIGN_SYSTEM.md section lands BEFORE the kit commit history
      shows core conversions; every value a token name.
- [ ] Kit components render from component tokens only; `npm run
      tokens:gate` green with no new allow-list entries.
- [ ] `.desk-surface-body` is a container; resizing the WINDOW (not
      the viewport) reflows CadenceCore between wide and narrow forms,
      shown in shots.
- [ ] CadenceCore contains zero forbidden page classes and no Signal
      `Panel`; the seam guard is green with Cadence absent from the
      allowlist and fails on a planted `page-grid` in a core.
- [ ] `npm run check` + python suite green.

## Test plan

- vitest for kit components and formatters; the seam guard (plant
  test); container reflow proven by Playwright shots at two WINDOW
  widths on one viewport; `npm run check`.

## Evidence required

- Spec diff, kit listing, guard output including the plant, reflow
  shots, suite output.
