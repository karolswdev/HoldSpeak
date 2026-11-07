# HS-T42-01 · Settle decision scope, recovery and filing identity

**Status:** proposed characterization/decision task; no code edits. Depends on [HS-T00](HS-T00-baseline.md). Parent: [HS-S42](../stories/HS-S42-decision-filing.md).

## Mandatory context

[Agent safety](../AGENT_START.md#authority-and-checkout-safety); story [G42](../stories/HS-S42-decision-filing.md#g42-local-decisions-before-implementation), [outcomes](../stories/HS-S42-decision-filing.md#target-interaction-and-outcome-custody), [matrix](../stories/HS-S42-decision-filing.md#acceptance-matrix) and [source ownership](../stories/HS-S42-decision-filing.md#exact-source-map-and-ownership); [V42](../VALIDATION.md#v42-meeting-decision-filing-verification); [I13/I16/I17/I18/I21/I23/I25](../INVARIANTS.md); current root/web/backend instructions for the assigned test scope.

## Work

1. Trace the actual meeting helper, canonical POST and separate membership PUT, then the correction identity read and project/collection axes. Record the exact point where a canonical/source identity exists, the point where filing is acknowledged and what can still fail afterward. A generic error is not proof of no write.
2. Record the accepted G42 subset. Decide visible single-project default, multi-project choice, deliberate unfiled creation when lookup is absent/unavailable, fail-closed canonical meeting behavior and compatibility limits. No legacy capability protocol was established; do not invent one to preserve malformed-response fallback.
3. Decide correction identity and presentation: canonical current projects editable when unambiguous; retained source projects separately visible/read-only in that branch; source collection/drawer behavior unchanged. Verified legacy-only decisions retain existing filing. Multiple mappings or failed reads are not a valid fallback to source identity. Resolve canonical member-only versus all-relationship semantics and deliberate role replacement/removal; a project-ID match alone does not confirm member filing. State the read-then-write concurrency limit or explicitly scope a stronger revision contract.
4. Set the bounded receipt/draft recovery contract using the existing workspace draft mechanism and server readback. Record what survives close/reopen or reload, how a newer draft is protected and how missing/uncertain state blocks repeated creation. Do not claim cross-browser exactly-once or add a journal.
5. Inspect real producer/admission/fixture tests and record V42 baseline when test execution is assigned. Confirm the new proof uses actual canonical/source creation and admitted membership commands, not only a compatibility mock. Current legacy tests are preservation evidence, not canonical correction proof.
6. Confirm owned files, exact test budget, proposed targets and collision points. Creation and scope tasks share `decide.ts` and must be serialized. Correction may proceed independently after its own G42 subset, but shared filing-strip changes must preserve other consumers.

## Acceptance

Return accepted decisions or explicit pending alternatives, the create/file/read state table, exact identity map, scoped persistence/recovery guarantee, baseline evidence or a stated execution blocker, and owned paths. Classify existing versus proposed tests. The contract task can finish with a decision pending; dependent implementation cannot proceed.

Use the [completion report](../COMPLETION_REPORT_TEMPLATE.md). Other Program/People decisions do not gate this story. If compatibility remains unsettled, return a correction-only assignment option rather than treating the whole project as blocked.

## Stops and rollback

No product rollback should be needed. Stop for absent authority, unexplained source drift, unsafe fixture effects, unsupported identity cardinality, a required backend/history change or a new persistence subsystem. Ask for the smallest scope/decision amendment. Do not run an application, alter tests or infer owner acceptance merely to finish this task.
