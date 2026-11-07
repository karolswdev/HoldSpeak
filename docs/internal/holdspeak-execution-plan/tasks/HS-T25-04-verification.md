# HS-T25-04 · Prove review changes hold the right merge

**Independent verification brief; requires assigned test authority/environment.** Depends on accepted G25 and [T25-02](HS-T25-02-review-observations.md)/[T25-03](HS-T25-03-review-admission.md) completion reports. Parent: [HS-S25](../stories/HS-S25-current-person-review.md).

## Mandatory context

[Safety](../AGENT_START.md#authority-and-checkout-safety); story [matrix](../stories/HS-S25-current-person-review.md#acceptance-matrix), [policy limits](../stories/HS-S25-current-person-review.md#g25-local-policy-choices), [rollback](../stories/HS-S25-current-person-review.md#rollback-and-stops); [V25](../VALIDATION.md#v25-current-person-review-verification); [I16/I18/I21/I22/I24](../INVARIANTS.md); current guides and predecessor reports.

## Procedure

1. Recheck source drift, accepted policy, five-file production ownership and fake-provider isolation. No schema/cadence/lock/identity-matching expansion may be hidden in the patch. Assert existing rigs use task-owned local Git remotes and no fallback gh/provider process.
2. Collect and run exact V25 suites. Inspect the actual composed test: raw latestReviews must pass real receipt normalization and real observer before runner/service eligibility. A hand-written new launch field or FakeGitHub.sweep alone is not producer proof.
3. Independently run approval → hold → newer changes → other hold clears → zero merge sequence, plus dedup, approval recovery, malformed/missing/legacy/unavailable and same-second source/direct ordering cases. Count feedback attempts separately from delivery. Keep history and current evidence distinct.
4. Call owner Merge before a Program tick and direct runner merge with a changed local projection. Verify URL identity binding and zero new commands on every blocked case. A durable person-gated GitHub request marker suppresses repeat/reconstruction; do not interpret a sequential pass as concurrent/crash at-most-once proof.
5. Verify meaningful review-only change reaches existing Program frames and refreshed wait/report/Your turn output without false approval, dismissal, never-reviewed, Ask/Send or request-cancellation claims. Preserve requirements and other gate/local/final-delivery behavior.
6. Inspect final stored facts, launch evidence, requested versus observed merge state and named rollback behavior. Run current integration-owner checks as assigned after final edits. Report each C25 row passed/failed/blocked, source/fake/live limits and remaining policy decisions using the [completion report](../COMPLETION_REPORT_TEMPLATE.md).

## Conditional joint handoff

If both slices and their joint proof are assigned, give T32-04 the accepted policy, final producer/observer and admission results, and exact shared-rig option in the completion report. Verify the [review-to-delivery gate](../VALIDATION.md#review-to-delivery-integration-gate) with that reviewer; T32-02 owns its case, not this independent verification task. It supplements rather than replaces V25's nine-suite union. Do not add S25 approval to final delivery or claim a queued step request is Done. Without the joint assignment, record this crossing as unexercised rather than block standalone S25.

## Exit and stops

No live provider, owner repository, installed gh effect or physical UI/device is needed for focused proof. Missing safe tooling or an omitted required test is blocked, not passed. Independent verification does not silently fix code or broaden scope. A reversal cannot undo remote effects or erase historical approvals; do not run old latch-reading code over unfinished affected gates without an approved safe hold/reconciliation. No staging, push, merge or deploy follows from this report.
