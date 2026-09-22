# PHILO-2-06 - The council

- **Project:** holdspeak-philo
- **Phase:** 2
- **Status:** backlog
- **Depends on:** PHILO-2-02, 03, 04, 05
- **Unblocks:** see the phase status doc
- **Owner:** both brains; the owner rules dissents

## Problem

Four passes, two static and two live, on one brief. The council reconciles them into one graph and one ranked finding list, and answers the roots question: does the product, as wired today, let the owner spend ninety percent of his day on the desk with interfaces that guide him, in the manner of Workbench 2.0+ on steroids (Tenet 6)? Where the answer is no, the outcome is codified as Philo Phase 3, the engineering phase.

## Scope

- **In:** what the acceptance criteria name, and only that; the one brief (`docs/internal/philo/briefs/graph-audit-brief.md`) is the contract.
- **Out:** fixing the product (Phase 3), correcting docs before the council (story 07), anything on the owner's desk.

## Acceptance criteria

- [ ] `docs/internal/philo/graph/COUNCIL.md`: agreements (both brains, both passes), single-brain findings with the other's reply (one round each, TWO-BRAINS §3), open dissents verbatim for the owner, and the merged `docs/generated/graph.json`.
- [ ] Findings in three bins, ranked by cost to the owner on a Tuesday; the first-use twenty ranked first; counts are diagnostics, never exits.
- [ ] The roots verdict: one page, plain words, measured against the Seven Tenets, UX-CANON and DESIGN_SYSTEM, naming where the desk stopped guiding and became plumbing.
- [ ] The Phase 3 charter draft (`pm/roadmap/holdspeak-philo/phase-3-*`): the engineering stories the council says must be built, each named by the edges and states it closes, each with its consequence record as the exit; the owner ratifies the charter, not the findings.
- [ ] Doc drift is ledgered here, corrected in story 07; product defects are ledgered here, built in Phase 3; nothing is fixed during the council.

## Test plan

- **Unit:** `docs/generated/graph.json` validates; every finding carries evidence.
- **Integration:** n/a.
- **Manual / device:** the owner reads COUNCIL.md and the Phase 3 charter and rules the dissents.

## Notes / open questions

The roots lens applies to every criterion: the owner works ninety percent of his day on the desk; the interfaces guide him; Workbench 2.0+ on steroids (Tenet 6). A finding that does not cost him on a Tuesday ranks last.
