# PHILO-10-05 - The atlas cases for Send

- **Project:** holdspeak-philo
- **Phase:** 10
- **Status:** done
- **Depends on:** PHILO-10-01 through PHILO-10-04
- **Unblocks:** PHILO-10-06
- **Owner:** Astra (Luna); Muad'Dib checks
- **Closure finding:** the charter's exit 7
- **Canvas:** none

## Problem

The atlas has no case for a send. A regression in a Send state would not be caught.

## Scope

- **In:** one atlas case per Send state at 1440 and 393 (the matrix), each with an `.op` sibling where the outcome is durable (SENT, UNKNOWN, a prepared send, a saved destination); the file channel's case runs a real write on the isolated HOME; the remote channels' cases use the recording runner (egress is not run in the atlas, as Phase 9's probe cases); transitions for a restart during `dispatching` (UNKNOWN, one dispatch), a replay of the same key, a destination changed after prepare (REFUSED, the row stays prepared), Send and Discard together (one wins), and receipts that survive the face's branch change (away and back); the Phase 7, 8 and 9 cases rerun.
- **Out:** real remote sends (story 06).

## Acceptance criteria

- [x] Each new face case fails on main and passes on the phase head; each `.op` reads the hub's record and receipt. (Main before Phase 10, `98ea2cfa`: 0 of 42 runs pass — 2 fail, 25 blocked at the absent `/api/channels/*` routes, 15 not run (the hub cannot install the recording runner: no `channel_cli`). The phase head `dce3afa9` + this story: 42 of 42 pass, every face case at 1440 and 393; each of the 12 `.op` twins reads `kernel.receipt.read` with the owner as actor. `evidence-story-05.md`.)
- [x] The Phase 7, 8 and 9 atlas cases still pass. (97 runs: 95 pass in the parallel batch and the same 2 block before (main `dce3afa9`, its own rig) and after, under load 17–29; both pass serially (`serial-merged`, 4 of 4). Zero pass→not-pass. The base atlas: one pass→blocked, `case.closure.chain.s5_next_day_brief_more_opened` 1440, the inherited input-precondition defect already in the BACKLOG (PHILO-9-05 follow-ups): 1 of 3 serial attempts pass after, 0 of 3 before.)

## Effort (not a promise)

PROVISIONAL: about 1 engineering day.

## Test plan

- **Rig:** the atlas runs, red on main and green on the phase head; runs retained per case.

## Notes

- 2026-09-29 — BUILT by the Fedaykin lane (branch `feat/philo-10-05`; Muad'Dib's brief, not the Luna lane the table proposed). `docs/internal/philo/graph/atlas-phase10.json`: 15 face cases (every matrix state but Manual, which is Phase 9's `case.p9.update.delivered_row`, plus the transitions) and 12 `.op` twins. The rig gains a recording runner at the CLI process edge (boundary `cli_runner`), `{hub_home}`, the `cli_calls` predicate, `protocol_reads` `count` and the `scroll_into_view` ui action (`scripts/graph_walk.py`). Census, runs, equivalence, reds and fences: `evidence-story-05.md`.

- 2026-09-28 — round two: amended on Codex Astra r1 DO-NOT-RATIFY (`checks/charter-astra-r1.md`); bound by `design/send-lifecycle.md`.
- 2026-09-28 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
