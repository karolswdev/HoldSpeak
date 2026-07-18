# HS-97-06 — The switcher

- **Project:** holdspeak
- **Phase:** 97
- **Status:** backlog
- **Depends on:** HS-97-04
- **Unblocks:** HS-97-09

## Problem

With several windows open there is no way to see them all at once, and
the one cycling affordance (Ctrl+`) is invisible — it reorders the
stack with no feedback about what was chosen or what else exists. An OS
answers "where is everything?" with an exposé and "next window" with a
visible switcher.

## Scope

- In:
  - exposé: a shell verb + keyboard entry fans every open window into a
    non-overlapping pick grid (transforms on the real shells,
    compositor-only; minimized windows join the grid dimmed); click or
    Enter focuses the pick and everything returns; Escape cancels;
  - the visible switcher: Ctrl+` keeps cycling, and while cycling a
    transient strip names the open windows (glyph + title) with the
    landing target highlighted, fading after the cycle settles;
  - reduced-motion: exposé snaps without the fan animation;
  - both entries reachable by keyboard and announced to AT.
- Out:
  - live window thumbnails beyond the real shells; cross-space/virtual
    desktops.

## Acceptance criteria

- [ ] Exposé fans 3+ windows (including one minimized) into a
      non-overlapping grid, click focuses, Escape cancels — walk-proven
      with an in-exposé screenshot.
- [ ] Ctrl+` shows the switcher strip naming every open window with the
      target highlighted; it fades after settling.
- [ ] Reduced-motion honored; axe stays clean.
- [ ] Web suite + guards green; storm envelope holds.

## Test plan

- vitest for grid layout math; walk legs for exposé and the strip;
  `npm run check`; the storm.

## Evidence required

- In-exposé and switcher shots, walk output, suite output.
