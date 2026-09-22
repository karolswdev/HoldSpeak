# PHILO-2-01 - The rulebook and the state atlas

- **Project:** holdspeak-philo
- **Phase:** 2
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** see the phase status doc
- **Owner:** both brains (co-authored; the other checks)

## Problem

Three audits measured properties and callers; the owner's sitting found two dead basics in two clicks: an edge with no effect (a receipt's Open) and a state with no face (an empty brief). Nothing in the tree defines the chain a verb must close, or the states a face must render. Without one rulebook, two passes cannot be compared and a council cannot rule.

## Scope

- **In:** what the acceptance criteria name, and only that; the one brief (`docs/internal/philo/briefs/graph-audit-brief.md`) is the contract.
- **Out:** fixing the product (Phase 3), correcting docs before the council (story 07), anything on the owner's desk.

## Acceptance criteria

- [ ] `docs/internal/philo/briefs/graph-audit-brief.md` is the ONE brief both brains run, verbatim (this story ratifies it; it is drafted at charter).
- [ ] The four definitions (edge, interface, connection, action) and the four questions are pinned with examples from the sitting.
- [ ] The outcome law (brief §3) is stated: a diff is evidence to inspect, not a success criterion; an enabled action that promises a change and produces neither it nor an intelligible refusal is a finding; an unexplained zero diff is unresolved, never pass; reads and presentation owe no receipt (Article XI.5).
- [ ] The state atlas (brief §4) lists REACHABLE cases, each with a stable id, source evidence, edge ids, preconditions, a production setup recipe, fixture and clock settings, expected transition and presentation, and execution limits; derived from Phase 1 lifecycle/failure records and producer code, never a Cartesian product; `quiet` is not an attention_state.
- [ ] The first-use candidates (brief §5) are mapped to job, starting state, trigger, expected result and source of priority, ordered by SITTING-07.md; THE OWNER SELECTS the set and his selection is recorded here; the number is whatever he selects.
- [ ] The graph schema (brief §8) is delivered as a machine-validatable JSON Schema joining Phase 1 record ids: root provenance, nodes, links with relations, cases, observations (one per run/case/brain/pass/viewport, never overwritten), claim reviews, findings and resolutions; verdicts pass/fail/blocked/not-run/not-applicable.
- [ ] Findings have three bins (product defect; doc drift; tooling debt) and one ranking: cost to the owner on a Tuesday.

## Test plan

- **Unit:** `tests/unit/test_philo_graph_schema.py` — the JSON Schema validates a worked example graph and rejects: an unresolved link endpoint, an observation without provenance, a finding without a bin, a case without an expected-result predicate; the atlas file validates against its own schema (no phrase-presence tests).
- **Integration:** n/a.
- **Manual / device:** the owner reads the brief once and says whether the twenty are his twenty.

## Notes / open questions

The roots lens applies to every criterion: the owner works ninety percent of his day on the desk; the interfaces guide him; Workbench 2.0+ on steroids (Tenet 6). A finding that does not cost him on a Tuesday ranks last.
