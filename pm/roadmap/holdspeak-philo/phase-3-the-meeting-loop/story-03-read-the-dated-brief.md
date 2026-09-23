# PHILO-3-03 - Read the dated brief with that decision

- **Project:** holdspeak-philo
- **Phase:** 3
- **Status:** backlog
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

- [ ] A brief load failure is distinct from absence, with a Retry that reads again; the period and generated date are on the face.
- [ ] A new producer-day's brief contains the recorded decision; same-day regeneration keeps the same id (the protocol sibling stays green).
- [ ] The minimum verified producer-clock boundary exists for the case (no machine clock change; the mechanism named in the atlas' clocks).
- [ ] Closure evidence: generate an empty brief → record the decision (A1) → cross the producer-day boundary → the dated brief with the decision, at both widths; the failure branch shot.

## Effort (council estimate, not a promise)

1–3 days incl. the clock boundary and case repair

## Test plan

- **Unit:** fences that fail pre-fix for every repaired seam.
- **Integration:** the rig case(s) named above, run through `scripts/graph_walk.py`, observations retained.
- **Manual / device:** the owner's sitting on the finished chain.
