# HS-200-08: Establish repeatable live-model quality evaluation

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-01, HS-200-03, HS-200-06
- **Unblocks:** HS-200-16, HS-200-18, HS-200-20, HS-200-40
- **Owner:** unassigned
- **Gate:** G1
- **Trace:** AA-IVW-006; AA-NFR-007; AC-33; C2, C12

## Problem

Successful fixture tools and a final prompt change do not establish useful recommendations or faithful extraction.

## Scope

Create a versioned scenario corpus, deterministic invariant checks, live-model runner, and human scoring protocol.

Implementation seams: Existing architect-assistant live proof; model runner; new tests/fixtures/phase200 and evaluation driver.

Out: Claims about untested models or fabricated owner usefulness.

## Acceptance criteria

- [ ] The corpus contains at least thirty episodes across Interview, meeting extraction, and grounded brief/update work.
- [ ] Cases include corrected facts, repeated questions, absent sources, stale decisions, irrelevant citations, and uncertain dates or owners.
- [ ] Training examples and held-out acceptance episodes are separated before prompt tuning.
- [ ] Reports identify model, route, build, context, failures, support judgments, latency, and review effort.
- [ ] LLM judging is supplementary. Critical factual failures require source inspection and cannot be averaged away.

## Test plan

Run the deterministic corpus without network, then evaluate the selected real route with synthetic content. Retain failed trials and repeat a subset to expose variability.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G1](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
