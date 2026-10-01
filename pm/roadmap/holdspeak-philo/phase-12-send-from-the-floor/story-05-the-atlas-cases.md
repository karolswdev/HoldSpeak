# PHILO-12-05 - The atlas cases

- **Project:** holdspeak-philo
- **Phase:** 12
- **Status:** backlog
- **Depends on:** PHILO-12-01, PHILO-12-03, PHILO-12-04
- **Unblocks:** PHILO-12-06
- **Owner:** Astra's lane (Luna, xhigh); Muad'Dib checks
- **Closure finding:** the charter's exit 7
- **Design:** `design/floor-send.md`
- **Canvas:** none

## Problem

The atlas has Send cases on document windows only (Phases 10 and 11). A regression in `Send to ▸`, the drop or the artifact send would not be caught.

## Scope

- **In:** face cases for `Send to ▸` per sendable kind at 1440 and 393 (the list at 393); the drop per kind at 1440; the tag refusals; the pushed-selection transitions (design §6); the touch list menu at 393; the artifact send (picked, SENT, PREPARED); `.op` siblings where the outcome is durable; each case through `scripts/graph_walk.py`, one case per run.
- **Out:** real sends (06).

## Acceptance criteria

- [ ] Each new face case fails on the fixed pre-feature revision `22c0acc4` (main before any Phase 12 merge; the grounding base) and passes on the phase head; each `.op` reads the hub's record and receipt.
- [ ] The Phase 7, 8, 9, 10 and 11 atlas cases still pass.

## Effort (not a promise)

PROVISIONAL: about 1 engineering day.

## Test plan

- **Rig:** the atlas runs, red on `22c0acc4` and green on the phase head; runs retained per case.

## Notes

- 2026-09-30 — round two: amended on Astra r1 RATIFY-WITH-CONDITIONS (`checks/charter-astra-r1.md`).
- 2026-09-30 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
