# HS-147-07 — The walk and the close

- **Project:** holdspeak
- **Phase:** 147
- **Status:** ready
- **Depends on:** HS-147-02, HS-147-03, HS-147-04, HS-147-05, HS-147-06
- **Unblocks:** —
- **Owner:** unassigned

## Problem

The exit story: prove the whole loop cold on the real product, run
the full suites, and close honestly. The walk story cannot be
closed by unit tests alone and cannot be waived.

## Scope

### In

- Extend `scripts/door_walk_hs144.py` with the one-tap leg: seed a
  calendar source with a near-future event → the rail shows RECORD
  THIS → tap → ARMED chip → (fast-forwarded or near-time) fire →
  countdown broadcast visible → meeting exists with
  `calendar_event_id` → its origin line on the Meetings surface →
  CANCEL? leg on a second event. Isolated HOME, both widths,
  fresh browser context per surface, wait for content; run from
  repo root. Error leg mandatory (a refusal on the row is a shot).
- Full sweep the CI way (`-n auto`, isolated HOME with
  `PLAYWRIGHT_BROWSERS_PATH`/`npm_config_cache` resolved from the
  real HOME first, exclude `tests/e2e/test_metal.py`); triage
  against the Phase 143 inherited baseline
  (`phase-143-intelligence-router/assets/
  story-08-inherited-failure-baseline.txt`) — verdict vocabulary
  "baseline-exact, zero branch-new"; readable log + dw capture as a
  PAIR; flake families serial ×2, recurrence beyond = DIAGNOSE.
- `git checkout --` the phase-141/143/144/145/146/147 asset dirs
  after every glass run.
- The usability bar (cold-run gates): the tap gives visible
  feedback ≤500 ms; the armed state is findable at a glance; the
  captured meeting findable in ≤60 s.
- Shot exhibit for the owner: before (audit-walk-shots) / after
  pairs, both widths, cross-read (times and counts must agree
  across shots of one flow). The owner sees shots BEFORE merge —
  standing law.
- `final-summary.md` before the last flip; close counsel pass
  (fresh opus, pointers to artifacts, the Tuesday question asked);
  the consolidated ledger owner-visible.

### Out

- The merge itself (owner's word); the real-vision-model probe
  (still a named backlog moment).

## Acceptance criteria

1. The extended cold walk passes end to end twice, exercising tap /
   armed / cancel / fire / provenance legs with assertions scoped
   to the owning containers.
2. Full sweep verdict recorded: baseline-exact, zero branch-new (or
   every non-baseline name diagnosed and dispositioned).
3. The shot exhibit is cross-read clean and delivered to the owner;
   a flinch is a redo.
4. Close counsel verdict recorded next to the orchestrator's; every
   concern fixed or ledgered by name.

## Test plan

`scripts/door_walk_hs144.py` (extended, run twice), the full suite
via the CI-shaped command with `-n auto`, `dw evidence capture` on
the walk + sweep, the shot exhibit under `assets/`.
