# HS-97-03 — The arrangement is sacred

- **Project:** holdspeak
- **Phase:** 97
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-97-09

## Problem

Article VII.3: the user's arrangement is sacred and persists. Today
rects and maximize persist, but the z/focus order (`panelOrder`) resets
to `[]` on every reload, so the stack the user built collapses; the
`min` array is written to storage but force-restored on load, dead
state pretending to be persistence. Two smaller chrome breaches ride
along: the room menu renders as unstyled gray rows (no transient
material), and on the phone the Panes pill sits on top of the bottom
sheet's action row.

## Scope

- In:
  - `panelOrder` persisted in `hs.desk.panels` beside the rects and
    restored on load (ids without windows tolerated);
  - minimize made honest: the session-scoped design stands, so the
    `min` array stops being written to storage (the loader still
    tolerates and drops legacy entries);
  - the room menu adopts the transient tokens (material, radius,
    shadow, item hover/focus states) — no gray default rows;
  - the compact z ladder fixed so shelf pills never occlude a sheet's
    action row.
- Out:
  - new persistence surfaces; cross-device layout sync.

## Acceptance criteria

- [x] Arrange three windows, reload: rects, maximize, AND stacking
      order survive byte-identically (walk-proven, localStorage shown).
- [x] `hs.desk.panels` no longer carries a live `min` key; legacy
      payloads still load.
- [x] The room menu wears the transient material with visible hover and
      focus states (shot in evidence).
- [x] On 393x852 an open sheet's action row is fully tappable (shot +
      hit-test in the walk).
- [x] Web suite + guards green.

## Test plan

- vitest store tests for order persistence + legacy tolerance; walk
  legs for reload-order and the phone sheet; `npm run check`.

## Evidence required

- Store diff, walk output, menu + phone shots.
