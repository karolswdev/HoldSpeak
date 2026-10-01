# PHILO-13-02 - A1 Park, never delete

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** backlog
- **Depends on:** the owner's ratification of this charter
- **Unblocks:** none (the park/restore verbs on Muad'Dib's faces land through a brief exchange)
- **Owner:** Astra (Luna, xhigh); Muad'Dib checks
- **Lane:** Data + truth (`../wt-philo-13-astra`, `feat/philo-13-astra`)
- **Proposal:** A1 (PROPOSAL §3, Wave A)
- **Closure finding:** `grounding/structure.md` F1 (`:284`); `grounding/faces-surfaces.md` F3 (`:190`); the owner's standing rule "never delete — park instead"
- **Canvas:** none (the verbs reuse the existing Delete position and the receipt species; any new face element goes on the C1 material)

`grounding/` = `docs/internal/philo/phase-13/grounding/`.

## Goal

Delete on a meeting or a Workbench item parks it. Restore, from the same face, brings it back whole. A truthful receipt says what happened.

## Problem

Meetings and Workbench items hard-delete. The walk deleted a meeting and read the DB: `meetings` 1 → 0, `segments` 2 → 0, `intel_snapshots` 1 → 0, `artifacts` 2 → 0; the footer said `DELETED 14:59`; no undo (`grounding/faces-surfaces.md:165`; shots `grounding/shots/surfaces/67-ledger-delete-meeting-before-pop-1440.png`, `68-…-confirm-…`, `69-…-after-…`). A Workbench item survives 8 s of client undo, then leaves the table, which has no tombstone column (`grounding/faces-surfaces.md:166`; `71b-workbench-item-confirm-pop-1440.png`, `72-workbench-item-deleted-pop-1440.png`).

| Path | The delete today (`grounding/structure.md:216-222`) |
|---|---|
| Meeting | `web/src/pages/cores/HistoryCore.tsx:456` → `DELETE /api/meetings/{id}` (`holdspeak/web/routes/meetings/crud.py:140`) → `holdspeak/services/meeting_service.py:496` → SQL DELETE (`holdspeak/db/meetings.py:1061-1065`) |
| Workbench item | `web/src/desk/components/WorkbenchWindow.tsx:1206` (single), `:1311` (bulk) → `web/src/desk/api.ts:900` → `holdspeak/web/routes/primitives/workbenches.py:134` → `holdspeak/services/workbench_service.py:218` → SQL DELETE (`holdspeak/db/workbenches.py:295-301`) |
| Workbench parent (already retained) | `holdspeak/web/routes/primitives/workbenches.py:90` → `deleted=1` (`holdspeak/db/workbenches.py:154`); a separate purge at `:166` — not this story |

## Scope

- **In:**
  - A parked state on the meeting row and on the Workbench item row (additive schema only), set by the normal Delete path; the normal reads leave parked rows out; a Parked filter shows them; Restore clears the state.
  - The meeting keeps its segments, summary (intel snapshots), artifacts and links while parked. The item keeps its run and result links.
  - The routes and services for park and restore on both kinds; single and bulk for items. Claimed items stay refused, as today.
  - A truthful receipt (`PARKED 14:59` + `Restore`, not `DELETED`), through the existing receipt species.
  - The call sites in `HistoryCore.tsx` (delete path) and `WorkbenchWindow.tsx` (removal path), which this lane owns (PROPOSAL §4). The Restore verb on any face Muad'Dib owns lands through a brief exchange, one lane at a time on the file.
  - The schema snapshot and `docs/generated/*` regenerated where routes or schema change.
- **Out:** restoring rows deleted before this story (they cannot come back); the Workbench parent purge; a general archive framework (`grounding/structure.md:224`); parking any other kind.

## Acceptance criteria

- [ ] Delete a meeting from Meetings → it is in Parked with its segments, summary and artifacts (rows read back from the DB in the run's HOME); Restore → it is back in the list with the same rows. Red on main (rows gone), green here.
- [ ] Remove a Workbench item, single and bulk → parked; after the 8 s window and after reload the row is still present and parked; Restore brings it back with its run links. Red on main (row gone at 12 s).
- [ ] No SQL DELETE on the normal path for either kind (a fence reads the SQL the service runs, or the row after the call).
- [ ] The receipt says what happened (`PARKED`, with `Restore`), never `DELETED`; every verb the library Button.
- [ ] Each proof runs producer → park → read → restore through the real routes, single and bulk, after a reload.

## Test plan

- **Focused:** service and route tests for park, the Parked read and restore, on both kinds (`HOME=$(mktemp -d) uv run pytest -q <the touched test files>`); the schema fence.
- **Atlas:** one case per kind (park → reload → restore), `scripts/graph_walk.py run`, one case per invocation, at 1440 and 393 (touch), each in a fresh HOME.
- **Shots:** Meetings and the Workbench window before, parked, restored, at 1440 and 393.

## Worker-brief scars

- **Doubles that lie:** mint the meeting and the item through the real producers; a fence that reads a `parked` field the real producer never writes proves nothing (two features shipped dead this way, HS-200-05).
- **The receipt under one branch:** the receipt shows in every branch the click leaves (park ok, park refused for a claimed item, restore ok, restore failed).
- **Never rewrite a guard to match a removal:** an existing delete fence is rehomed onto park behaviour in the same commit, not loosened.
- **Fences that name old words:** a fence that asserts `DELETED` changes with the word, in the same commit.

## Effort (not a promise)

Grounding size: not sized as a move (a prerequisite repair, `grounding/structure.md:308`). PROVISIONAL.

## Notes

- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
