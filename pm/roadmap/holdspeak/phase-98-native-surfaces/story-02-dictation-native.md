# HS-98-02 — Dictation, native

- **Project:** holdspeak
- **Phase:** 98
- **Status:** done
- **Depends on:** HS-98-01
- **Unblocks:** HS-98-09

## Problem

Dictation is the flagship surface and the biggest core (1,048 lines) —
and it is a web page in a window: `page-grid` spans, `Panel` cards,
`data-row` journal dumps, permanent button rows. The surface the owner
meets first must be the reference native surface.

## Scope

- In:
  - `DictationCore` re-composed entirely in the surface kit: verb bar
    (record/replay primaries), journal as dense honest rows (humanized
    times, revealed row verbs for replay/correct), review/correction
    flow as a `SurfaceSplit` detail, settings clusters as sections;
  - container-driven forms: wide = split journal/detail, narrow = one
    column;
  - zero forbidden page classes; Dictation leaves the guard allowlist;
  - every verb and flow that exists today still exists — re-craft,
    not de-feature (the walk's dictation leg must pass unmodified in
    intent).
- Out:
  - dictation backend/API changes; other cores.

## Acceptance criteria

- [ ] DictationCore off the allowlist; guard green.
- [ ] The existing dictation walk leg passes on the production bundle
      (real voice path).
- [ ] Window-resize reflow shown in shots at 1440 viewport; phone
      sheet form at 393.
- [ ] `npm run check` + python suite green; no new token allow-list
      entries.

## Test plan

- Existing dictation vitest + walk leg; reflow + before/after shots;
  `npm run check`.

## Evidence required

- Before/after shots, walk output, guard output, suite output.
