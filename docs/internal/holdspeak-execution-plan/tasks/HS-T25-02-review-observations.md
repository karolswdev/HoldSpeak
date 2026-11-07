# HS-T25-02 · Preserve usable review observations through the launch

**Conditional implementation brief; execution not authorized.** Depends on [HS-T00](HS-T00-baseline.md), [HS-T25-01](HS-T25-01-contract.md) and accepted G25-A. Parent: [HS-S25](../stories/HS-S25-current-person-review.md).

## Mandatory context

[Safety](../AGENT_START.md#authority-and-checkout-safety); story [receipt design](../stories/HS-S25-current-person-review.md#existing-receipts-retain-review-evidence), [matrix](../stories/HS-S25-current-person-review.md#acceptance-matrix) and [rollback](../stories/HS-S25-current-person-review.md#rollback-and-stops); [V25](../VALIDATION.md#v25-current-person-review-verification); [I16/I18/I21/I22](../INVARIANTS.md); current scoped guides.

## Ownership and procedure

Production edits only `holdspeak/delivery/pr_receipts.py` and `holdspeak/delivery/follow_through.py`. V25 names three editable producer suites. Existing ledger implementation, provider fields/query cadence, source registry and terminal closure behavior are read-only.

1. Establish current focused baseline and producer counterexamples. Add review-specific completeness without turning whole PR/CI/merged data into failure. Preserve existing summary fields and body limits. Valid empty differs from missing/null/non-list/malformed/unknown-author data; aggregate approval is never person evidence.
2. Implement the accepted successful-read association within current receipt cache/rows. A source-success envelope and its row must identify the same raw read; direct reads use their own successful identity. Do not use second-resolution timestamps or cache-wide source status alone for direct reads. Identity tokens denote local reads, not a provider revision or request-start order.
3. Persist latest applied attempt quality separately from last complete matching review snapshot in existing follow-through JSON. Both sweep and direct poll update it, including read failure/target absence. Increment local application identity under existing observer serialization; preserve provider timestamps separately. Failed/stale source rows cannot become fresh success or erase last successful evidence.
4. Bind to actual launch/source/PR URL+number/head provenance. Keep original selection guards, discovery/terminal behavior and unrelated fields. No matching row in a bounded list is target-unavailable, not no approval or dismissal. Malformed review metadata must not hide a truthful observed merge/close from existing consumers.
5. Test source/direct applications in both orders, same-second observations, direct cache mutation, failure after approval/change, missing target, malformed row and recovery. Inject all provider/process calls; no actual gh or remote call. Preserve poll bounds and exact observer effects.
6. Hand T25-03 the new projection contract, old/legacy compatibility meaning, actual tests and data examples. Metadata-only preparation does not claim the person-review feature complete; do not enable a partially implemented consumer path.

## Acceptance and rollback

Prove C25-01/02/03 and producer preservation parts of C25-13 using V25. Return [completion report](../COMPLETION_REPORT_TEMPLATE.md) with real normalization/observer evidence and honest fake-provider limits. Stop if a strict existing consumer rejects additions, a third production owner is necessary or application order cannot be established within the accepted contract. Rollback must coordinate with the new consumer; never erase historic launch/PR evidence or resume old admission over unverified gates.
