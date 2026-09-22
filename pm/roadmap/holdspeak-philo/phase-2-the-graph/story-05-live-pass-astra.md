# PHILO-2-05 - The live pass, Astra

- **Project:** holdspeak-philo
- **Phase:** 2
- **Status:** backlog
- **Depends on:** PHILO-2-01
- **Unblocks:** see the phase status doc
- **Owner:** Astra (Luna xhigh); Muad'Dib checks

## Problem

Same brief as story 04, run independently by the other brain, on the same single versioned `scripts/graph_walk.py` (interface-specific trigger adapters permitted; shared rig preparation and calibration finish before either live pass). What is compared is the observation per case, sealed before either brain reads the other's.

## Scope

- **In:** what the acceptance criteria name, and only that; the one brief (`docs/internal/philo/briefs/graph-audit-brief.md`) is the contract.
- **Out:** fixing the product (Phase 3), correcting docs before the council (story 07), anything on the owner's desk.

## Acceptance criteria

- [ ] Identical acceptance criteria to story 04; output at `docs/internal/philo/graph/live-astra.json` + `live-astra.md` + shots; Muad'Dib's check recorded beside it.
- [ ] Neither brain reads the other's live output before delivering its own.

## Test plan

- **Unit:** as story 04.
- **Integration:** as story 04.
- **Manual / device:** none.

## Notes / open questions

Sealing law (brief §§6–7, 9): this pass's report is sealed (committed on its own branch) before its author reads any other pass; shared schema, fixture recipes and rig calibration are preparation, not shared findings. Every run records source revision and dirty-tree status, contract versions, runtime provenance and unexercised cases with reasons.

The roots lens applies to every criterion: the owner works ninety percent of his day on the desk; the interfaces guide him; Workbench 2.0+ on steroids (Tenet 6). A finding that does not cost him on a Tuesday ranks last.
