# HS-99-06 — Interior archetypes

- **Project:** holdspeak
- **Phase:** 99
- **Status:** backlog
- **Depends on:** HS-99-02, HS-99-03
- **Unblocks:** HS-99-08

## Problem

The idiom made interiors consistent; the study shows what makes them
feel INHABITED: the two interior archetypes (a settings rail; a
toolbar/status-bar explorer) built on the tonal ladder, plus the
icon-button halo and the tint formulas.

## Scope

- In:
  - Settings: the tab strip becomes a LEFT RAIL two-pane at wide
    containers (icon + label rows, active = one tonal step up,
    `@container` collapse back to the strip when narrow);
  - Meetings: a status bar (item count, filter state) on the well
    tone at the window's foot; the archive toolbar tone-stepped;
  - the icon-button halo grammar for toolbar icon verbs;
  - hover/selected tint formulas applied to kit rows (formula tokens
    from 01 replacing the ad-hoc washes);
  - surface ladder applied to SurfaceSplit rails (detail pane one
    step off the body).
- Out:
  - new capabilities; other cores' bespoke redesigns.

## Acceptance criteria

- [ ] Settings reads as rail + panel at wide, strip at narrow (shots
      both); Meetings wears the status bar with an honest count.
- [ ] Kit rows use the tint formulas; halo on icon verbs; ladder on
      split rails.
- [ ] Config + meetings walk legs green; `npm run check` + python
      suite green.

## Test plan

- vitest; config/meetings walk legs; reflow + shots; `npm run check`.

## Evidence required

- Before/after shots, walk output, suite output.
