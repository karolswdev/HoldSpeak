# HS-144-06 — The walk and the close

- **Project:** holdspeak
- **Phase:** 144
- **Status:** in-progress
- **Depends on:** HS-144-05
- **Unblocks:** —
- **Owner:** unassigned

## Problem

The Door was chartered against the audit shots in
`assets/audit-b-shots/` — those are the before-pictures. The phase
cannot close on unit tests: the exit is a cold walk of the finished
front door against the usability bar, the full sweep against the
inherited baseline, and the honest record.

## Scope

### In

- **The cold walk** (fresh isolated HOME, real hub, no lore),
  scripted and FAILABLE, both widths + 200% zoom:
  1. Cold open: the First Sentence job appears untouched; first
     capture to visible transcript ≤3 min.
  2. The reveal lands on the Door: board + rail + counts, populated
     honestly from what exists (never fake facts).
  3. A card completes from the board — receipt visible ≤500 ms.
  4. A schedule is created from the Door in-world; its fire is
     visible on the rail.
  5. An ICS subscription (fixture feed) populates the rail; the
     egress badge is present. (Leg drops if HS-144-02 was cut.)
  6. Click-depth audit vs the before-pictures: tasks 0 clicks
     (was 1), upcoming 0 clicks (was 1+), schedule create ≤1 click
     (was 2).
  7. The doorframe repairs hold: 393px Go menu, deterministic
     `/meetings` deep-link.
  Assertion honesty per house law: AND-assert specific elements
  scoped to owning containers; byte-identical "different" shots are
  a false-positive tell. The walk never touches the owner's real
  machine state (HOME + keychain scoped; cleanup prints what it
  deletes).
- **Before/after pairs** against `assets/audit-b-shots/`, both
  widths, sent to the owner BEFORE the merge word. Beauty pass
  verdict recorded. The Tuesday question asked and answered in the
  evidence.
- **The full sweep**, detached, isolated HOME, `-n auto`, triaged
  against the 11-inherited baseline
  (`../phase-143-intelligence-router/assets/
  story-08-inherited-failure-baseline.txt`): the bar is
  baseline-exact, zero branch-new (never "green", never "broken").
  Non-baseline names: serial ×2 — green = flake (named families),
  red = REAL and fixed before the flip. After every sweep restore the
  phase-141 assets PNGs (the glass e2es clobber them).
- **The record**: evidence captured via `dw evidence capture` (run in
  background; it lawfully exits 1 on the baseline — plain contract,
  Tests-ran certified on read output), the orchestrator's triage note
  appended, `final-summary.md` written (the gate demands it at 6/6),
  README + status doc updated.

### Out

- New features; anything found becomes a fix (if branch-new) or a
  named ledger entry with an owner.

## Acceptance criteria

- [ ] All walk legs pass with honest, container-scoped assertions;
  the click-depth table shows the deltas (evidence).
- [ ] Before/after pairs delivered to the owner; the nod precedes any
  merge word.
- [ ] Full sweep captured: baseline-exact, zero branch-new, triage
  note appended.
- [ ] `final-summary.md` written; `dw check holdspeak` clean for the
  phase.

## Test plan

- The scripted walk harness (checked into `scripts/`, reusable).
- The detached full sweep per HANDOVER.md §4.6, captured through
  `dw evidence capture`.
