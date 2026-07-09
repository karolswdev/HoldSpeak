# HSU-2-05 — The matrix + the review sitting

- **Project:** holdspeak-uat
- **Phase:** 2
- **Status:** backlog
- **Depends on:** HSU-2-02, HSU-2-03, HSU-2-04
- **Owner:** unassigned

## Problem

Three sweeps produce rows; the phase's promise is a *matrix the two of
us have walked together*. This story consolidates, reconciles, and —
the beat that cannot be delegated — puts the whole inventory in front
of the owner for the ranking pass that decides what Phase 3 authors
first, at what depth, and what is consciously skipped.

## Scope

- In:
  - **Consolidation** — merge/reconcile the three sweeps in
    `uat/features.yaml` v2: key collisions resolved, cross-domain
    duplicates folded, the handoff arcs cross-linked to their
    component rows, ledger validation green.
  - **The recipe worklist** — the aggregated
    needed-but-not-yet-built state recipes, deduplicated, each naming
    the capabilities that wait on it (`uat/RECIPE-WORKLIST.md`).
  - **The review sitting** — owner + agent walk the matrix (the
    guided site's ledger/coverage view if convenient, the YAML if
    not) and rank every capability: `must-test` / `should-test` /
    `spot-check` / `skip` (the deferred-decision default; the owner
    may amend the vocabulary at the sitting). Skips are as explicit
    as musts. Disagreements between the ranking and the parity claim
    (a `must-test` capability that is `n/a` on a claimed surface) are
    recorded as roadmap gaps for the HS/HSM backlogs.
  - **The Phase 3 handoff** — the authorship backlog derived from the
    ranked matrix (must-tests first, grouped by shared recipes so
    staging cost is paid once), recorded in this phase's
    final-summary.
- Out: authoring scenarios, building recipes, product changes.

## Acceptance criteria

- [ ] `uat/features.yaml` v2 validates; zero `unknown` cells; zero
      unranked rows; every needed recipe appears in the worklist with
      its dependent capabilities.
- [ ] The review sitting happened jointly (the ranking's git history
      shows the owner's amendments, same discipline as the charter);
      every `skip` and every parity gap is explicit.
- [ ] Parity gaps surfaced by the ranking are filed to the HS/HSM
      backlogs through the normal gate.
- [ ] The final summary records the Phase 3 authorship backlog and
      closes the phase against its exit criteria.

## Test plan

- Unit: ledger validation suite green on the consolidated file.
- Integration: n/a.
- Manual / device: the review sitting itself — owner-gated.

## Notes / open questions

- The Phase 3 pack skeleton is already drafted in
  [`../PHASE-3-PLAN.md`](./PHASE-3-PLAN.md) (five packs grouped by
  shared staged world, must-tests first, three-surface with the
  iPhone leg as the open information). The review sitting *ranks and
  amends* that skeleton into committed Phase 3 scope — it does not
  author it from nothing.
- Grouping the Phase 3 backlog by shared recipes is deliberate: a
  sitting's cost is dominated by staging, and the matrix should buy
  each staged world several scenarios.
