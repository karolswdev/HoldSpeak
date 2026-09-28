# PHILO-10-05 - The atlas cases for Send

- **Project:** holdspeak-philo
- **Phase:** 10
- **Status:** backlog
- **Depends on:** PHILO-10-01 through PHILO-10-04
- **Unblocks:** PHILO-10-06
- **Owner:** Astra (Luna); Muad'Dib checks
- **Closure finding:** the charter's exit 7
- **Canvas:** none

## Problem

The atlas has no case for a send. A regression in a Send state would not be caught.

## Scope

- **In:** one atlas case per Send state at 1440 and 393 (the matrix), each with an `.op` sibling where the outcome is durable (SENT, UNKNOWN, a prepared send, a saved destination); the file channel's case runs a real write on the isolated HOME; the remote channels' cases use the recording runner (egress is not run in the atlas, as Phase 9's probe cases); the Phase 7, 8 and 9 cases rerun.
- **Out:** real remote sends (story 06).

## Acceptance criteria

- [ ] Each new face case fails on main and passes on the phase head; each `.op` reads the hub's record and receipt.
- [ ] The Phase 7, 8 and 9 atlas cases still pass.

## Effort (not a promise)

PROVISIONAL: about 1 engineering day.

## Test plan

- **Rig:** the atlas runs, red on main and green on the phase head; runs retained per case.

## Notes

- 2026-09-28 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
