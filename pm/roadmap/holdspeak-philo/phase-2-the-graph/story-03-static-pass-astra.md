# PHILO-2-03 - The static pass, Astra

- **Project:** holdspeak-philo
- **Phase:** 2
- **Status:** done
- **Depends on:** PHILO-2-01
- **Unblocks:** see the phase status doc
- **Owner:** Astra (Luna xhigh); Muad'Dib checks

## Problem

Same brief as story 02, run independently by the other brain in its own worktree. Two static graphs from one brief make the council possible: where they agree the graph is probably true; where they differ one of us missed something.

## Scope

- **In:** what the acceptance criteria name, and only that; the one brief (`docs/internal/philo/briefs/graph-audit-brief.md`) is the contract.
- **Out:** fixing the product (Phase 3), correcting docs before the council (story 07), anything on the owner's desk.

## Acceptance criteria

- [x] Independent static graph and §9 report at `docs/internal/philo/graph/static-astra.json` + `static-astra.md`; schema and source-contract evidence recorded. Other-brain check deferred by the sealing-law amendment below.
- [x] Neither brain reads the other's static output before delivering its own (the worktrees enforce it; the council reads both).

## Test plan

- **Unit:** the output validates against the schema of story 01.
- **Integration:** n/a.
- **Manual / device:** none.

## Notes / open questions

Sealing law (brief §§6–7, 9): this pass's report is sealed (committed on its own branch) before its author reads any other pass; shared schema, fixture recipes and rig calibration are preparation, not shared findings. Every run records source revision and dirty-tree status, contract versions, runtime provenance and unexercised cases with reasons.

The roots lens applies to every criterion: the owner works ninety percent of his day on the desk; the interfaces guide him; Workbench 2.0+ on steroids (Tenet 6). A finding that does not cost him on a Tuesday ranks last.

## Sealing-law amendment — 2026-09-22

The owner’s lane instruction and `static-pass-lane-brief.md` require this
independent pass to be committed and its PR opened before cross-reading.
The graph-audit brief §§6 and 9 require **all four pass outputs sealed before
cross-checking**. The immediate Muad’Dib-check clause above is therefore
deferred to PHILO-2-06. This completion means the independent static pass is
sealed, not ratified by the other brain. No check or agreement is claimed.

The static-lane ban on product processes and e2e means no full product suite,
on-glass walk or 1440/393 shots apply here. The schema fence collected and
passed 17 tests in isolated HOME; the delivered graph validator run is in the
paired evidence. Cases remain verbatim from story 01: 69 cases, 111 atlas
states and 38 distinct edges (the supplied lane brief says 37).

Nine source findings are ledgered in the pass: eight product defects for the
council/Phase 3 and one J9/J11 recipe/predicate tooling debt for shared live-pass
preparation. Fifty reviewed fields remain unresolved; the report explains
static scope and preserves J7/J8 as unverifiable-statically. No product or
Phase 1 metadata was changed.
