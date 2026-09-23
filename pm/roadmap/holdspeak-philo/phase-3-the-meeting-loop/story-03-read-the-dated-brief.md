# PHILO-3-03 - Read the dated brief with that decision

- **Project:** holdspeak-philo
- **Phase:** 3
- **Status:** done
- **Depends on:** PHILO-3-01, PHILO-3-02
- **Unblocks:** the meeting loop
- **Owner:** unassigned (two-brains: one owner brain, the other counsels on built)
- **Council tag:** A3

## Problem

A brief that fails to load is drawn as "No brief yet" (`ChairHome.tsx:466,1080`), the date is never on the face (`monday_brief.py:106` computes labels the face ignores), and same-day Generate returns the existing brief (`monday_brief_service.py:194`), so recording a decision after an empty brief does not prove inclusion; the next producer-day has no reachable case.

## Scope

- **In:** the owner result below and its closure evidence; the proof repairs the council named for this story.
- **Out:** everything the council deferred (COUNCIL.md, "Deferred, explicitly").

## Edges and states this story closes

edge.face.arrival_generate; edge.route.brief_generate; edge.route.brief_latest; states briefs.{absent,loading,load_failure,populated,reload_persisted,next_day}; J10

## Acceptance criteria

- [x] A brief load failure is distinct from absence, with a Retry that reads again; the period and generated date are on the face.
- [x] A new producer-day's brief contains the recorded decision; same-day regeneration keeps the same id (the protocol sibling stays green).
- [x] The minimum verified producer-clock boundary exists for the case (no machine clock change; the mechanism named in the atlas' clocks).
- [x] Closure evidence: generate an empty brief → record the decision (A1) → cross the producer-day boundary → the dated brief with the decision, at both widths; the failure branch shot.

## Effort (council estimate, not a promise)

1–3 days incl. the clock boundary and case repair

## Test plan

- **Unit:** fences that fail pre-fix for every repaired seam.
- **Integration:** the rig case(s) named above, run through `scripts/graph_walk.py`, observations retained.
- **Manual / device:** the owner's sitting on the finished chain.

## Notes

- 2026-09-23 — the producer-clock boundary: `MondayBriefService(clock=)` (default the wall clock), wired `MeetingWebServer(brief_clock=)` → `WebContext.brief_clock` → the brief router; the rig's `producer-clock` step moves it inside the rig's own hub (never the machine clock). Named in both atlases' `clock.python_wall`.
- 2026-09-23 — canvas `assets/story-03-canvas/` (the BRIEF section in four states at 1440 and 393) RATIFIED by the owner: "Ratify, build it" (published https://claude.ai/artifact/SyDd84ry8d6g8th6MbhCdq). Built as drawn: `READING…`; `BRIEF DID NOT LOAD · HTTP n` (or `NO ANSWER`) with a Retry library Button; `No brief yet` only on a null answer; `<period_label> · <generated_label>` as one 12 px line under the brief.
- 2026-09-23 — owner ruling: `case.j10.arrival_generate_again.next_day` (atlas.json) re-pointed to applicable on the producer-clock mechanism; the sealed phase-2 passes that recorded it unreachable stay history.
- 2026-09-23 — Astra's counsel (nonblocking): `holdspeak/web/routes/monday_brief.py:27` (`_period_label`) computes a Monday-to-generation label, not the stored lookback window (`period_start`..`period_end`); the date caption renders the ratified label and must not be described as proof of collection coverage.
- 2026-09-23 — Astra's counsel (blocker, paid): the populated-brief atlas fence now requires the material before the first generation of the observed producer-day; an earlier empty generation passes only across a valid `producer-clock` advance (`advance_days ≥ 1`). Mutation checks in `tests/unit/test_philo_graph_atlas.py` prove the removed, moved and invalid advance and the early empty Generate all FAIL.
