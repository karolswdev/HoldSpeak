# PHILO-2-05 - The live pass, Astra

- **Project:** holdspeak-philo
- **Phase:** 2
- **Status:** done
- **Depends on:** PHILO-2-01
- **Unblocks:** see the phase status doc
- **Owner:** Astra (Luna xhigh); Muad'Dib checks

## Problem

Same brief as story 04, run independently by the other brain, on the same single versioned `scripts/graph_walk.py` (interface-specific trigger adapters permitted; shared rig preparation and calibration finish before either live pass). What is compared is the observation per case, sealed before either brain reads the other's.

## Scope

- **In:** what the acceptance criteria name, and only that; the one brief (`docs/internal/philo/briefs/graph-audit-brief.md`) is the contract.
- **Out:** fixing the product (Phase 3), correcting docs before the council (story 07), anything on the owner's desk.

## Acceptance criteria

- [x] Independent live graph, §9 report, JOBS block, immutable observations and shots at `docs/internal/philo/graph/live-astra.json` + `live-astra.md` + `observations/astra/`; every unexercised case names its reason. Story 04's runtime and calibration contract applies with the explicit lane amendments below. Muad'Dib's check is deferred by the sealing law.
- [x] Neither brain reads the other's live output before delivering its own.

## Test plan

- **Unit:** as story 04.
- **Integration:** as story 04.
- **Manual / device:** none.

## Notes / open questions

Sealing law (brief §§6–7, 9): this pass's report is sealed (committed on its own branch) before its author reads any other pass; shared schema, fixture recipes and rig calibration are preparation, not shared findings. Every run records source revision and dirty-tree status, contract versions, runtime provenance and unexercised cases with reasons.

The roots lens applies to every criterion: the owner works ninety percent of his day on the desk; the interfaces guide him; Workbench 2.0+ on steroids (Tenet 6). A finding that does not cost him on a Tuesday ranks last.

## Lane and sealing amendments — 2026-09-22

The owner's lane instruction and `docs/internal/philo/briefs/live-pass-lane-brief.md`
require this independent pass committed and its PR opened before cross-reading.
The graph-audit brief §§6 and 9 require all four pass outputs sealed before
cross-checking. The immediate Muad'Dib-check clause is therefore deferred to
PHILO-2-06. Completion of this story means an independent live audit is sealed,
not that the other brain has ratified it or that the owner jobs all passed.

The specific lane runtime law reserves the real LAN engine for J6. Other
engine-dependent cases require a recorded reply or an explicit BLOCKED result.
The J6 runtime atlas changes only the seven declared address fills to the exact
`http://192.168.1.43:8080/v1` specified by that law. The shared atlas and rig are
unchanged. A missing `openai` dependency in the first J6 attempt was paid by
installing the repository's declared `test` extra; the original attempt remains
in the evidence. No recipe, selector, predicate, or finished state was repaired.

This audit-only lane uses the brief's scoped schema/atlas fence, calibration,
serial real-hub rig and artifact validator. No full product suite or broad
regression verdict is claimed. Device and time states outside the rig's safe
boundary remain unexercised with their mechanisms named. Product code and
Phase 1 metadata are unchanged. Failed and blocked raw results are audit data,
with ranked findings assigned to PHILO-2-06 and its Phase 3 scope.

No other-brain pass artifact, observation directory, branch or worktree was
opened. A required PMO search incidentally exposed a one-line other-pass status
summary in the shared tracker; the report discloses this independence limit.
A worker process-cleanup check also exposed a sibling process pathname. Neither incidental exposure was used as evidence or as a source of findings; no sibling process was contacted.

A J10 worker launched one phone run before its desktop run exited. Both
records are preserved and excluded from strict serial proof; Astra stopped
the overlap and reran both widths serially before proceeding. The incident
ledger and report name the affected runs and replacements. This seal does
not claim an exception-free execution history.
