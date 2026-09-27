# PHILO-9-05 - The atlas cases for the Room

- **Project:** holdspeak-philo
- **Phase:** 9
- **Status:** backlog
- **Depends on:** PHILO-9-01, PHILO-9-02, PHILO-9-03, PHILO-9-04
- **Unblocks:** PHILO-9-06
- **Owner:** Astra (Luna); Muad'Dib checks
- **Closure finding:** Phase 7 exit 4 and Phase 8 exit 5 (the method); `docs/internal/philo/phase-9/grounding/README.md`
- **Canvas:** none

## Problem

The atlas has no case for a project, the Room, the steward or the list face repair. The grounding walked the job with lane probes, not atlas cases (`docs/internal/philo/phase-9/grounding/probes/`).

## Scope

- **In:** face cases at 1440 and 393, with an `.op` sibling where the outcome is durable, for: the Room opened from a meeting's project button; a milestone shown and health turned; the steward counts equal to the run; RECEIPTS as writes; the Steward verb unobscured at 393; the update list's words; the selection contrast; the list face at 393 (columns, text size, plural, the row menu in view); and `.op` cases for each admitted project write that read its kernel receipt (as Q1 rules). The ids and the file are fixed here against `docs/internal/philo/graph/atlas.schema.json`. The general atlas fences applied to the new file (Phase 8 law).
- **Out:** any product change (a failing case goes back to its story).

## Acceptance criteria

- [ ] Every new face case fails on main and passes on the phase head at 1440 and 393; each `.op` sibling passes headless and reads its receipt with the actor.
- [ ] The Phase 7 and Phase 8 atlas cases still pass; the atlas counts over the named files are reported at the phase head.
- [ ] Real and replayed runs are retained apart.

## Effort (not a promise)

PROVISIONAL: about 1 engineering day.

## Test plan

- **Integration:** `scripts/graph_walk.py run --atlas <file> --case <id> --viewport 1440|393 --engine none` for each case, `--out` under this phase's assets; the Phase 7 and Phase 8 atlas re-run.

## Notes

- 2026-09-27 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
