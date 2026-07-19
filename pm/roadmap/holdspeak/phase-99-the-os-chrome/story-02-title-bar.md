# HS-99-02 — The title bar is a bar

- **Project:** holdspeak
- **Phase:** 99
- **Status:** done
- **Depends on:** HS-99-01
- **Unblocks:** HS-99-08

## Problem

Our window head is a padded card row with a border-bottom and 26px
hover-dots. An OS title bar is a two-tone bar whose full-height
square controls reach the edges, whose close warns red, and whose
right-click offers the window verbs.

## Scope

- In:
  - `DeskWindowFrame` head re-crafted for the whole family (surface
    windows, pull-outs, trust window): head on `--os-head-fill` (one
    tonal step above the body), no border-bottom, full-height
    aspect-ratio-1 verb buttons flush right (padding-right 0), SVG
    glyphs replacing text glyphs, close hover = `--danger` fill with
    `--text-on-accent` via the variable-override pattern;
  - hover == focus-visible on head buttons;
  - corners square off when maximized;
  - a head context menu (right-click: Minimize/Maximize or Restore/
    Close) on the desk transient material — role=group, desk locks
    respected;
  - the Phase 97 floors intact: keyline focus, front/rest shadows,
    drag/snap/edge-resize/dblclick unchanged (walk legs re-run).
- Out:
  - dock, controls, scrollbars (their stories).

## Acceptance criteria

- [ ] All window kinds wear the new bar; shots at 1440 show two-tone
      heads with edge-flush controls and a red-hover close.
- [ ] Head context menu opens with the three verbs and executes them;
      desk locks + a11y suite green.
- [ ] Maximize squares corners; restore rounds them; frame/depth/
      placement walk legs green.
- [ ] `npm run check` + python suite green; no new allow-list entries.

## Test plan

- vitest window tests; frame/depth walk legs; shots; `npm run check`.

## Evidence required

- Before/after shots, walk output, suite output.
