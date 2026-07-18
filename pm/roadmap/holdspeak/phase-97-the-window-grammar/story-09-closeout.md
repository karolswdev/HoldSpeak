# HS-97-09 — Closeout: the grammar walk

- **Project:** holdspeak
- **Phase:** 97
- **Status:** backlog
- **Depends on:** HS-97-01, HS-97-02, HS-97-03, HS-97-04, HS-97-05, HS-97-06, HS-97-07, HS-97-08
- **Unblocks:** —

## Problem

Article IX: nothing is done because its code merged. The grammar ships
when it walks — the whole window grammar, on the production bundle, at
real viewports, with the storm inside the envelope and the screenshots
looked at.

## Scope

- In:
  - `scripts/desk_gl_walk.py` gains a `grammar` walk: placement
    sequence, reload-order persistence, focus depth, close/minimize
    motion states, snap ghost, edge resize, double-click maximize,
    exposé, the switcher strip, the one dock's launchers — all against
    the production bundle;
  - the assembled walk chain (Phase 95's eight walks + grammar) green;
  - the storm re-run inside the Phase 95 envelope;
  - fresh 1440/393 shots archived and LOOKED AT;
  - the full python sweep green (metal exclusion per standing rule);
  - the phase closed: statuses flipped, final-summary written, README
    updated, PR to main merged on green.
- Out:
  - the owner's live verdict (rides the next UAT sitting alongside
    Campaign 13's design-polish scenario).

## Acceptance criteria

- [ ] The grammar walk passes end to end on the production bundle with
      zero failed API responses.
- [ ] The assembled Phase 95 walks still pass (the floor held).
- [ ] Storm median within the Phase 95 envelope; shots archived.
- [ ] Full sweep green; `npm run check` green; PR merged on green.

## Test plan

- `uv run python scripts/desk_gl_walk.py grammar` (+ the assembled
  chain); the storm; `uv run pytest -q --ignore=tests/e2e/test_metal.py`;
  `npm run check`.

## Evidence required

- Walk transcripts, storm numbers, shot paths, sweep tail, PR link.
