# HS-T52-01 · Choose the smallest Project review boundary

**Proposed characterization/decision task; no runtime edit.** Depends on [HS-T00](HS-T00-baseline.md). Parent: [HS-S52](../stories/HS-S52-project-review-boundary.md). G52 may finish unresolved; implementation then remains blocked.

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); story [outcome](../stories/HS-S52-project-review-boundary.md#outcome-and-evidence), [alternatives](../stories/HS-S52-project-review-boundary.md#g52-alternatives-and-proposed-branch), [preservation](../stories/HS-S52-project-review-boundary.md#preserved-behavior-and-responsibilities), [matrix](../stories/HS-S52-project-review-boundary.md#acceptance-matrix); [V52](../VALIDATION.md#v52-project-review-boundary-verification); current backend/scoped instructions. Read only the exact current code and proof listed there, not all Project/Room history.

## Work

1. Revalidate the selector, its Room/Delta/resource consumers, three availability gates and runtime constructors. Identify in-tree and declared supported external/custom injection contracts. Do not equate a call spelling being accepted with preservation of a different-DB/custom query collaborator.
2. Compare A retained contract and B existing-repository selector against the same task: locate/change open-review selection, find its Room/Delta/resource shapes, identify the atomic writer and its tests. Record whether B removes the actual Project→Delta retained/call dependency without adding more unrelated context. LOC/file-count reduction is not a success metric.
3. Resolve G52-B's exact constructor contract: proposed `review_available: bool | None = None`; None infers `delta_service is not None`, explicit boolean wins. Bare construction remains unavailable. Record whether accepted compatibility is same-DB/query-only and what blocks migration for custom injection.
4. Record every composition case: held instances, missing Project, missing Delta, both absent, both held with unattached Delta, and legacy bare/fallback contexts. Preserve the current attachment law rather than quietly fixing it. Distinguish main hub capability from resource/bare Room absence.
5. Freeze the behavior matrix: selector normalization/order/limit/row/exception, 200-row proposal cap, all inner/outer fault outcomes, typed missing project, exact resource keysets, unchanged collector behavior, observer multiplicity and references. Do not decide a new error/degraded policy during refactoring.
6. Record command invariants separately for proposal acceptance/edit-accept with `create_item_in_transaction`, and whole-review acceptance/cursor/supersession. Identify the matching kernel handle's same-connection answer/terminal boundary. Existing publication rollback is a harness example, not Delta test evidence.
7. Under an assigned test environment only, collect the V52 baseline and add the allowed characterization assertions before the move. Otherwise report source assertions as inspected and test results as pending. No live provider, collector egress, browser or owner DB is needed.

## Acceptance

Return the actual G52 decision or unresolved alternative, supported-caller/compatibility map, before-change ownership/context map, exact shape/fault/composition matrix, transaction proof obligations, scoped edit budget and baseline results/blockers. If A is selected, hand off a bounded contract/test-only amendment; do not execute B's runtime task.

Use the [completion report](../COMPLETION_REPORT_TEMPLATE.md), marked characterization. No new arbitrary service protocol, module, schema or migration may be inferred from the measured class size.

## Stops and rollback

Stop for unassigned execution, source drift, unsupported custom injection, changed fault/count/admission semantics, unfamiliar partial wiring, unsafe fixture effects or absent benefit. No product rollback is intended. Preserve all unrelated checkout work and current observer/transaction behavior.
