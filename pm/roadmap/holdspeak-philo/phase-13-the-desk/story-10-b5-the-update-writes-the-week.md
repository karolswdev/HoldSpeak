# PHILO-13-10 - B5 The update writes the week

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** done
- **Depends on:** the owner's ratification of this charter
- **Unblocks:** none
- **Owner:** Astra (Luna, xhigh); Muad'Dib checks
- **Lane:** Data + truth (`../wt-philo-13-10-astra`, `feat/philo-13-10-astra`)
- **Proposal:** B5 (PROPOSAL §3, Wave B); Muad'Dib's ruling, PROPOSAL §5 (not forked)
- **Closure finding:** `grounding/faces-jobs.md` F6 (`:172`), move 6 (`:157`), fork 4 (`:190`)
- **Canvas:** none (the draft's text; the Room face is unchanged)

`grounding/` = `docs/internal/philo/phase-13/grounding/`.

## Goal

The deterministic update draft reads the project's week (linked meetings, their decisions and owned actions) with no engine. He edits; he does not write.

## Problem

For a project with a summarized meeting, a decision and two owned actions, the deterministic draft says `No focus items … No decisions in this window … No upcoming actions … All sources consulted successfully` (`grounding/faces-jobs.md:99`; `grounding/shots/jobs/J4-04-draft-1440.png`). The composer reads Room items, not the week's meetings (`holdspeak/services/project_update_service.py:13-24`, `:315-318`). He typed the week by hand: 111 characters (`grounding/faces-jobs.md:100`). Meetings link to a project through `POST /api/projects/{id}/meetings/{mid}` (`grounding/faces-jobs.md:157`).

## Scope

- **In:** the deterministic composer also reads the project's linked meetings (summary, action items with owners) and linked decisions, each line with its claim ref (`grounding/faces-jobs.md:190`). No engine. "All sources consulted" only when they were.
- **Out:** model drafts (engine off); the Room face; revision pile-up (`grounding/faces-jobs.md` F15, not in PROPOSAL r2; BACKLOG if he asks).

## Acceptance criteria

- [x] On the grounding week, the draft for the project lists its linked meeting's summary, its decision and its two owned actions, each with its ref. Red on main (`J4-04`).
- [x] 111 typed characters → 0 to reach a publishable draft; he edits.
- [x] No engine call is made (the fence runs with no engine assigned).
- [x] The meeting, decision and actions are minted through the real producers and linked through the real route.

## Test plan

- **Atlas file:** `docs/internal/philo/graph/atlas-phase13-astra.json` (this lane's only atlas file; `--atlas` per run, `scripts/graph_walk.py:6507`); its count fence in `tests/unit/test_philo13_astra_atlas.py`.
- **Focused:** `project_update_service` tests over a real-producer week (`HOME=$(mktemp -d) uv run pytest -q <the touched test files>`).
- **Atlas:** one case (Room → Draft update → the draft lists the week), at 1440 and 393 (touch), one case per `scripts/graph_walk.py run` invocation, with an `.op` sibling reading the stored draft.
- **Shots:** the Room's Update posture with the draft, both widths.

## Worker-brief scars

- **Doubles that lie:** the linked meeting's summary and actions come from the real producer (the Phase 11 rig `mint` pattern), not a stubbed source list.
- **Fences that name old words:** fences that assert `No decisions in this window` on a project with decisions change in the same commit.

## Effort (not a promise)

Grounding size: M (`grounding/faces-jobs.md:157`). PROVISIONAL.

## Notes

- 2026-10-03 — Closed after #739 (`573969dbf`) and Muad'Dib's recorded PASS. Current-main `23a6c137f` rerun: 242 scoped tests, actual 1440/393 native-touch draft cases and stored-draft operation sibling pass. C8 healed editor wrapping. [Closure, ledger and limits](close-10-astra.md); [canonical evidence](evidence-story-10.md). The dispatch authorizes self-merge on scoped proof.

- 2026-10-01 — r2: Astra charter check r1 (DO-NOT-RATIFY) paid; see the status file, "Round two".
- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.

- 2026-10-03 — B5 candidate implemented and verified; UNCHECKED — awaiting Muad'Dib. [Lane report](lane-10-astra.md). The editor line-wrap limitation is recorded, not waived.
