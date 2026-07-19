# HS-98-04 — The live pair

- **Project:** holdspeak
- **Phase:** 98
- **Status:** backlog
- **Depends on:** HS-98-01
- **Unblocks:** HS-98-09

## Problem

Live meeting (460 lines) and Activity (257) are the desk's moving
surfaces — transcript streaming in, runs and receipts arriving — and
both are page-grammar mini-apps. Live data deserves the densest, most
honest rows we have.

## Scope

- In:
  - `LiveCore`: transcript as the primary pane (dense rows, speaker +
    humanized time), the rail (intents, markers) as the split's second
    pane collapsing under width; record state on the verb bar;
  - `ActivityCore`: the activity feed as honest rows (what happened +
    when, humanized), metric strip for counts, revealed row verbs;
  - both off the guard allowlist.
- Out:
  - runtime bus/API changes; other cores.

## Acceptance criteria

- [ ] Both cores off the allowlist; guard green.
- [ ] Live transcript rows update from the bus unchanged (existing
      tests); the walk legs touching live/activity pass.
- [ ] Reflow shots at both window widths; `npm run check` + python
      suite green.

## Test plan

- Existing vitest for both cores; walk legs; reflow shots; `npm run
  check`.

## Evidence required

- Before/after shots, walk output, guard output, suite output.
