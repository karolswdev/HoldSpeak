# PHILO-11-06 - The atlas cases for the new kinds and Slack

- **Project:** holdspeak-philo
- **Phase:** 11
- **Status:** backlog
- **Depends on:** PHILO-11-01, PHILO-11-02, PHILO-11-05
- **Unblocks:** PHILO-11-07
- **Owner:** Astra's lane (Luna, xhigh); Muad'Dib checks
- **Closure finding:** the charter's exit 7
- **Design:** `design/document-sources.md`
- **Canvas:** none

## Problem

The atlas has Send cases for the update only (`docs/internal/philo/graph/atlas-phase10.json`). A regression on a new kind or on Slack would not be caught.

## Scope

- **In:** for each new kind with a face seat, cases for picked, SENT and PREPARED at 1440 and 393 (`meeting_decision`: `.op` cases only, design §6a); the three failure transitions (design §6b); for Slack, POSTED, FAILED, UNKNOWN and the long-document refusal, through a recording HTTPS edge in the rig's hub (the Phase 10 story 07 pattern); `.op` siblings where the outcome is durable; each case through `scripts/graph_walk.py`, one case per run.
- **Out:** real sends (07).

## Acceptance criteria

- [ ] Each new face case fails on main and passes on the phase head; each `.op` reads the hub's record and receipt.
- [ ] The Phase 7, 8, 9 and 10 atlas cases still pass.

## Effort (not a promise)

PROVISIONAL: about 1 engineering day.

## Test plan

- **Rig:** the atlas runs, red on main and green on the phase head; runs retained per case.

## Notes

- 2026-09-29 — round two: amended on Astra r1 RATIFY-WITH-CONDITIONS (`checks/charter-astra-r1.md`).
- 2026-09-29 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
