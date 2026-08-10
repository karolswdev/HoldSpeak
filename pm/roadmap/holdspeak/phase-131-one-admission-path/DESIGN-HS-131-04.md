# HS-131-04 design — Sequence and Workflow through the admitted runner

**Status:** DRAFT — awaiting Sol ruling  
**Decision boundary:** this design replaces the Sequence/Workflow execution seam, not `InferenceRunner`'s dispatch, cancellation-election, receipt-closure, or egress policy. It composes with HS-131-03's stage → terminal-receipt → finalize protocol.

## Context

The current Sequence route starts a legacy `RunLifecycle` without passing its available request principal (`holdspeak/web/routes/primitives/chains.py:101-116`; the route principal helper is at `:34-35`), resolves one target for the entire chain (`:151-168`), and calls `intel.run_prompt` directly once per agent (`:173-219`). The Workflow route repeats that coarse lifecycle (`holdspeak/web/routes/primitives/workflows.py:104-140`), one target resolution (`:167-180`), and direct calls for model graph nodes (`:197-263`) or its prompt fallback (`:331-377`). It writes the final Artifact before the legacy success record (`chains.py:232-257`; `workflows.py:299-328,379-409`).

`InferenceRunner.invoke()` admits exactly one provider dispatch, claims it, grants `RUNNING -> DISPATCHING` immediately before dispatch, and writes a terminal receipt before exposing its terminal active state (`holdspeak/kernel/inference_runner.py:165-225`). Its existing broker causality check accepts a parent only when it is claimed, warranted, unrevoked, unexpired, and in scope (`holdspeak/kernel/causation.py:9-36`). HS-131-03's stager commits a projection before a successful receipt, then materializes it only after matching receipt linkage (`holdspeak/kernel/projection_stager.py:70-150`).

## 1. Parent operation is one authenticated native definition run

A POST to `/api/chains/{id}/run` or `/api/workflows/{id}/run` admits one native parent operation before execution: `sequence.run@1` or `workflow.run@1`. The route obtains the authenticated request principal, refuses absent/unauthenticated principals before creating a parent, submits/approves/claims the parent as the local executor, and creates one server-only `OuterRunContext` from that successful claim. There is exactly one parent per definition-execution request, including a definition that later has zero dispatchable model nodes.

The parent admission records: native parent-run ID; operation and correlation IDs; authenticated principal kind and identity; definition ref and persisted definition revision captured at admission; canonical input/variables snapshot; deadline; and an execution epoch. It does **not** select a provider or count as a model invocation. Its operational state is `OPEN` after claim, then either `CANCELLING` or one receipt-backed terminal state: `SUCCEEDED`, `FAILED`, `CANCELLED`, `REFUSED`, or `INDETERMINATE`. A terminal parent state is observable only after its parent receipt commits.

The parent receipt/response is a summary: definition revision, final domain result reference if successful, and ordered child invocation/operation IDs with terminal outcomes. It may project those children, but never substitutes a graph-level receipt for a child receipt. Every actual model dispatch retains its own admitted child and terminal receipt.

## 2. Definition and child provenance are immutable and explicit

At parent admission, load the Sequence/Workflow and freeze its persisted revision. For a Sequence, freeze each referenced Recipe revision before that step becomes eligible; a child uses `SavedDefinition(ref="recipe:<recipe_id>", revision=<recipe.last_modified>)`, while its canonical payload also carries `sequence_ref`, `sequence_revision`, step ordinal, and Recipe revision. This respects the runner's current saved-definition liveness authority, which presently recognizes persisted `recipe:` revisions (`holdspeak/kernel/inference_runner.py:263-264`).

For a Workflow model node (including prompt-only Workflow), use a versioned hashed `ServiceContract`: `holdspeak.workflow-node@1` or `holdspeak.workflow-prompt@1`. Its canonical payload carries `workflow_ref`, persisted workflow revision, node ID (or `prompt`), canonical node revision `sha256(canonical node definition)`, resolved input, rendered prompt, limits, and deployment revision. This avoids falsely presenting a graph node as a saved Recipe definition. A retry/fallback that really dispatches receives a new child invocation with its own attempt ordinal and the same frozen definition/node revision; it never overwrites an earlier child.

For **each** child actually about to dispatch, Sequence/Workflow calls the Phase-130 resolver with the applicable invocation override, then definition/capability default, then explicit global default: invocation → Workbench (when present) → Agent/capability → global. The resolver's published order is authoritative (`pm/roadmap/holdspeak/phase-130-one-truth/story-01-the-precedence-resolver.md:22-27`). Capture the resulting target as one immutable deployment revision before constructing and hashing the child payload; later target/profile edits cannot retarget it. No child is created for a skipped branch, an empty model prompt, or a pure transform.

## 3. Trusted-parent context is server-only and live-checked

`OuterRunContext` is a kernel-private, opaque carrier created only by the parent-run controller after the broker has admitted and claimed the native parent. It contains the parent operation ID, native ID, owner principal identity, execution epoch, and an identity-checked private capability. It is neither serialized into a request/response nor accepted from HTTP JSON, query, headers, WebSocket messages, or a public service method. `InvocationRequest.parent_operation_id` is not populated from caller data for these routes; the runner receives `parent_context=OuterRunContext` through a dedicated in-process child-invocation API.

Immediately before child submission, that API verifies all of: the private capability identity; the supplied caller principal equals the context owner principal; the parent operation remains `claimed`, warranted, unrevoked, and unexpired; the context epoch is still current and parent state is `OPEN`; and the broker's causality check accepts the resulting parent operation ID. The child request then carries only that verified parent operation ID to broker admission. This is stricter than relying solely on current generic causality, whose owner-parent branch does not compare owner identities (`holdspeak/kernel/causation.py:28-31`).

Refusal is synchronous, typed, and mints no child dispatch or projection:

| Attempt | Required refusal |
| --- | --- |
| Unknown/mismatched context capability or parent operation | `parent_operation_unknown` / `parent_context_invalid` |
| Parent terminal, unclaimed, revoked, or expired | `parent_operation_not_running` / `parent_operation_not_live` |
| Context owner differs from the acting authenticated principal | `parent_operation_scope_required` |
| Any client-supplied parent ID/context field | `parent_context_client_supplied` before admission |

A valid live context is the positive path: one child is admitted with `parent_operation_id == parent.operation_id`, its causal correlation equals the parent's correlation, and its receipt survives independently.

## 4. Ordering, branching, and the advancement fence remain domain-owned

Sequence code alone owns step order, input threading, output binding, retry choice, and fallback policy. Workflow code alone owns graph linearization/branch selection, pure transformations, node ordering, retry/fallback choice, and the existing domain failure policy. The runner owns only a child model dispatch; it must not interpret the graph. This preserves the current explicit model-versus-pure split (`workflows.py:205-274`) and existing fallback decision seam (`:219-252`).

The parent controller keeps a monotonic `execution_epoch` and one `active_child_invocation_id`. Before admitting a child it atomically records `(epoch, planned_step_or_node, child_id)` while parent is `OPEN`. After a successful child receipt, its projection finalizer may persist output and advance only if that exact tuple remains current and parent is still `OPEN`; otherwise it discards the staged child output from domain advancement. Cancelling, retry supersession, or selecting a fallback increments/replaces the epoch before a later child can be admitted. Thus a late child can retain a terminal receipt but cannot bind output, select a branch, or advance a Sequence/Workflow after cancellation or supersession.

## 5. Projection staging is the only path for model-derived domain writes

For every successful child, its runner publisher stages a `sequence-step-output` or `workflow-node-output` projection before the runner writes the child's success receipt. The projection contains parent/child IDs, frozen definition/node/step revisions, epoch, rendered-input hash, output, placement/deployment revision, provider facts, and proposed step/node status. The child receipt carries that exact `projection-stage:` reference. The finalizer then performs, under HS-131-03's single transaction and publication permit, the output checkpoint plus the conditional epoch/state advance described in §4.

The aggregate final result follows the same sequence: stage `sequence-run-result` or `workflow-run-result` against the native parent, commit the successful parent receipt with that exact stage reference, then finalize one result/artifact/parent-summary projection. A failed, refused, cancelled, or indeterminate child/parent receipt discards its matching stage and produces no successful output/result projection. Parent cancellation intent, active-child registry, admission metadata, and non-authoritative run-frame diagnostics remain plain persistence/in-memory coordination. Pure-computation scratch remains ordinary in-process computation until included in a receipt-gated aggregate projection. No model output, step/node completion, graph advancement, fallback binding, run result, or Artifact is written directly before its matching receipt.

## 6. Cancellation closes admission before it reaches dispatch

Cancelling a parent atomically changes its context from `OPEN` to `CANCELLING`, increments its epoch, and freezes new-child admission. It then invokes `runner.cancel(active_child_invocation_id)` through the broker-owned shared runner under the same authenticated principal. The runner's existing cancellation election owns adapter cancellation and writes its cancellation child receipt before the cancellation disposition is observable (`holdspeak/kernel/inference_runner.py:71-143`).

If cancellation wins before child `PUBLISHING`, no child output stage exists. If it arrives after a child staged successfully, the runner truthfully reports `completed`; that child may finalize only if its epoch was still current before cancellation won. Once cancellation has advanced the parent epoch, all late output finalizers fail their conditional advance and cannot mutate domain state. The parent becomes terminal `CANCELLED` only after its own terminal receipt. Each active child always retains its own terminal receipt, including failed cancellation/indeterminate disposition cases.

## 7. Failure semantics preserve the existing definition outcome

A child `failed`, `refused`, `cancelled`, or `indeterminate` receipt remains durable and visible through its child linkage. Sequence stops with its existing step failure outcome. Workflow applies the node's existing failure policy: halt when unhandled; otherwise records the existing skipped/fallback domain status and continues only through a newly eligible epoch. A fallback that invokes a model is a new admitted child; a fallback/pure value that does not dispatch is not. Neither outcome mapper nor parent summary may convert a child failure into a missing receipt or an invented successful output.

## 8. Response and sync-test migration

The legacy Sequence/Workflow response contract is replaced by an admitted parent summary plus receipt-linked child facts and the finalized result/artifact shape. The legacy helper explicitly asserts one legacy invocation/correlation ID and one attempt (`tests/unit/test_web_routes_primitives.py:35-46`); HS-131-04 removes its Sequence/Workflow uses and introduces an admitted parent/children assertion: authenticated parent operation, artifact/result projection linkage, exact child cardinality, causal parent IDs, frozen revisions, terminal receipts, and placement/deployment facts. `_assert_admitted_run` shows the intended receipt-owned rather than legacy-correlation direction (`:49-58`).

`test_ipad_synced_graph_workflow_runs_on_the_hub` remains a Python-contract test: its pushed graph is input, not an instruction to edit Swift (`tests/integration/test_primitive_framework_sync.py:590-607`). Its present isolated-HOME failure is before graph execution: `this_machine` is unavailable because its model file is absent, yielding 409 at the route target-readiness branch; the test currently only patches the old configured-intel builder (`:611-625`). Repair the fixture in Python by registering an explicit ready canonical inference target and its exact deployment revision in the test database, then inject the runner engine/adapter at the admitted deployment-revision seam. Preserve the pushed Swift-encoded graph bytes, assert two model children (the fixture expects two model operations and one pure `keep_if`, `:628-641`), their parent/revision linkage, and the finalized Artifact. No Swift source change is permitted.

## 9. Non-changes

This story does not change Sequence or Workflow semantics, editors, graph format, sync wire format, `capability_ref`, model/pure node classification, or placement policy. It does not make skipped/pure computation nodes consequential model invocations. It does not alter runner state-machine policy, provider adapter behavior, or replace child receipts with a parent receipt.

## Invariants

1. Every Sequence/Workflow execution has exactly one authenticated, receipt-closed native parent operation.
2. Every actual model dispatch has exactly one admitted, causally linked child and terminal child receipt; skipped and pure nodes have none.
3. Each child records a frozen definition/node/step revision and immutable deployment revision resolved by Phase-130 precedence at that child.
4. A parent link can originate only from a live, server-created `OuterRunContext` owned by the same authenticated principal.
5. Parent cancellation/supersession prevents new admission and prevents late output from advancing domain state, while preserving child receipts.
6. Model-derived checkpoints, advancement, results, and Artifacts are visible only through a successful receipt-gated projection finalization.
7. Existing Sequence/Workflow failure/fallback semantics decide domain continuation without deleting or replacing a failed/refused child receipt.

## Test matrix

| Invariant / acceptance criterion | Planned focused proof |
| --- | --- |
| One authenticated parent; no unprincipalized route dispatch | `tests/unit/test_sequence_workflow_runner_migration.py::test_sequence_and_workflow_create_one_authenticated_native_parent` and `::test_unauthenticated_sequence_or_workflow_refuses_before_parent_or_child` |
| Three-step Sequence = parent + three children + three receipts | `tests/unit/test_sequence_workflow_runner_migration.py::test_three_step_sequence_has_three_admitted_children_and_terminal_receipts` |
| Actual Workflow model nodes, retries, and fallbacks each get children; skipped/pure nodes get none | `tests/unit/test_sequence_workflow_runner_migration.py::test_workflow_child_cardinality_covers_model_retry_fallback_skip_and_pure_nodes` |
| Parent link, exact revisions, frozen deployment per child | `tests/unit/test_sequence_workflow_runner_migration.py::test_child_causation_definition_node_and_deployment_revisions_are_immutable` |
| Phase-130 precedence is resolved separately for every child | `tests/unit/test_sequence_workflow_runner_migration.py::test_each_child_resolves_phase130_placement_then_freezes_deployment_revision` |
| Positive trusted-parent path | `tests/unit/test_sequence_workflow_runner_migration.py::test_live_outer_context_admits_causally_linked_child` |
| Wrong/dead/foreign parents refuse | `tests/unit/test_sequence_workflow_runner_migration.py::test_outer_context_refuses_wrong_parent`, `::test_outer_context_refuses_dead_parent`, and `::test_outer_context_refuses_foreign_principal_parent` |
| Forged/client parent input refuses | `tests/unit/test_sequence_workflow_runner_migration.py::test_client_supplied_or_forged_parent_context_is_refused` |
| Ordering/branch ownership and late-output advancement fence | `tests/unit/test_sequence_workflow_runner_migration.py::test_late_or_superseded_child_output_cannot_advance_sequence_or_graph` |
| Parent cancellation stops new children, cancels active child, blocks late mutations, preserves receipts | `tests/unit/test_sequence_workflow_runner_migration.py::test_parent_cancel_fences_admission_and_late_output_while_child_receipts_survive` |
| Child failure/refusal preserves receipt and drives current stop/fallback/halt result | `tests/unit/test_sequence_workflow_runner_migration.py::test_child_non_success_preserves_receipt_and_applies_existing_domain_policy` |
| Stage → receipt → finalize for step/node output and final artifact | `tests/unit/test_sequence_workflow_runner_migration.py::test_model_derived_sequence_workflow_writes_are_receipt_gated` |
| Legacy route assertions migrate to parent/child admitted shape | `tests/unit/test_web_routes_primitives.py::test_run_chain_threads_steps`, `::test_run_workflow_prompt`, and `::test_run_workflow_linear_graph_runs_in_order` |
| Synced graph runs with canonical Python target/revision, two children, and no Swift edit | `tests/integration/test_primitive_framework_sync.py::test_ipad_synced_graph_workflow_runs_on_the_hub` |

## Open questions for Sol

1. Ratify `sequence.run@1`/`workflow.run@1` as the native parent operation names and the `OuterRunContext` capability boundary, or require a different kernel-native parent codec/name.
2. Ratify the provenance split: Sequence child uses the actual Recipe `SavedDefinition`; Workflow node/prompt uses the named hashed service contracts because graph nodes are not saved Recipes.
3. Ratify that parent success also uses a projection stage tied to the native parent receipt, rather than allowing direct aggregate Artifact/result persistence after all child receipts.

## Sol ruling

**Verdict: RATIFIED WITH AMENDMENTS.** The parent/child split, per-child placement and provenance, domain-owned graph semantics, and two-level projection protocol are the right architecture. The draft is not implementable as written at its two hardest boundaries: its trusted-parent check is separated from broker admission by a revocation race, and it creates durable parent runs without specifying how an abandoned parent is closed after process death. The following amendments are binding.

### Binding amendments

1. **Make trusted-parent admission one atomic kernel act and close the owner-parent loophole.** Replace the §3 “verify, then submit” sequence with one controller-to-broker child-admission operation performed under the same database write transaction that (a) identity-checks the private capability, (b) compares the acting principal's kind and identity with the parent owner, (c) re-reads the parent claim, warrant, revocation, expiry, durable run state, and execution epoch, (d) inserts the child operation with the parent's correlation, and (e) records `(epoch, planned_step_or_node, child_invocation_id)` as the active tuple. Cancellation and supersession must update that same durable parent row under the same write lock. The generic causality rule must no longer treat an `owner` parent as sufficient authority for an arbitrary principal: a direct `InvocationRequest.parent_operation_id` must require exact parent-principal identity, while delegated continuation remains available only through its existing explicit continuation-identity rule. No check made solely in Python before `broker.submit()` satisfies this amendment.

2. **Constrain `OuterRunContext` as an unexportable, scoped capability rather than an alternate public credential.** The context is created only after the one parent has been admitted and claimed; it is identity-compared, not value-compared; it has no public constructor or codec; and its capability material must never enter JSON, logs, exceptions, stages, receipts, persistence, or returned objects. It is bound to one parent controller, owner principal, native parent ID, and current execution epoch. Reuse by that controller for successive children is intentional, but cross-parent use, use after epoch replacement, use by another principal, and use after terminalization all refuse without minting a child. The existing general `InferenceRunner.invoke()` must not become a way around this boundary: Sequence/Workflow callers use only the trusted child API, and direct owner-parent IDs receive the identity-and-liveness enforcement in amendment 1.

3. **Persist the parent controller state and give abandoned runs an authoritative recovery path.** Parent run identity, frozen definition revision/input, deadline, epoch, planned node, active child ID, ordered admitted-child ledger, and `OPEN`/`CANCELLING`/terminal state must be durable; an in-memory active-child registry alone is insufficient. Startup and periodic reconciliation must first reconcile any receipt-backed child stage for the recorded epoch, then detect `OPEN` or `CANCELLING` parents whose local execution lease no longer exists, prevent further admission, and close each such parent exactly once with an `indeterminate` parent receipt. It must not silently resume graph code, mint a replacement parent, or manufacture success. A receipt-backed child checkpoint finalized before that closure remains truthful partial progress; child receipts remain independently queryable; no final run result or Artifact exists. Parent and child native IDs/idempotency keys must make recovery and request replay unable to duplicate either level.

4. **Make advancement and cancellation a durable compare-and-swap, and define both race winners.** Every child output materializer must perform its domain checkpoint and graph advance in the projection stager's one `BEGIN IMMEDIATE` transaction only when the durable parent row is `OPEN` and its exact `(epoch, planned_step_or_node, child_invocation_id)` still matches; it then consumes or replaces that tuple in the same transaction. Cancellation, retry supersession, and model fallback selection increment the epoch and invalidate the tuple transactionally before another child can be admitted. If child finalization wins first, that completed checkpoint may remain and cancellation stops the next admission; if cancellation/supersession wins first, the successful child stage finalizes as a receipt-linked stale/no-advance result and must not bind output or branch state. These rules apply equally when cancellation races the runner's `PUBLISHING` state and when fallback selection races a late successful child; no code path may advance from a cached pre-transaction liveness check.

5. **Keep the aggregate result behind a parent stage and specify every crash gap.** Parent success must stage exactly one `sequence-run-result` or `workflow-run-result`, commit a successful receipt whose `result_ref` is that exact stage, and only then finalize the Artifact/result/summary; direct aggregate persistence is forbidden. If the process dies before the parent stage, amendment 3 closes the parent `indeterminate`, with any finalized child checkpoints retained but no Artifact. If it dies after staging and before the parent receipt, recovery waits while the operation is genuinely live and otherwise discards the stage after the authoritative non-success/indeterminate receipt. If it dies after the success receipt and before finalization, normal stager recovery finalizes exactly once. Failed, refused, cancelled, and indeterminate parents always receive their own terminal receipt but never a successful aggregate projection. The parent summary may name ordered child outcomes only from durable child operations/receipts, never from an in-memory list.

6. **Bound cardinality before execution and make model classification closed.** A frozen parent plan must carry a finite `child_budget` derived from the frozen Sequence steps or the finite linearized Workflow plus each explicitly configured finite retry/model-fallback allowance. Every admitted child, including retry and model fallback, consumes one budget slot transactionally; exhaustion refuses the next child and drives the existing domain failure outcome. HS-131-04 must not introduce implicit retries, recursive fallback, loop execution, or a new branch executor. At the existing `linearize` plus `_MODEL_KINDS`/`_PURE_TRANSFORM_KINDS` seam, every executable node is classified exactly once as model or pure before execution; an unknown, ambiguous, cyclic, or unsupported control-flow node is refused before any child dispatch rather than guessed, skipped, or lowered to the prompt fallback. Attempt ordinals are monotonic within the frozen node/step and every real dispatch gets a distinct child ID.

7. **Freeze provenance before hashing, and never let provenance substitute for liveness.** The Sequence parent freezes its persisted Sequence revision at admission; each eligible Recipe child records the exact persisted Recipe revision used by `SavedDefinition`, and a revision change before runner admission produces the runner's saved-definition refusal rather than silently refreshing the same planned attempt. A Workflow child uses `holdspeak.workflow-node@1` or `holdspeak.workflow-prompt@1` with a canonical node hash and payload hash that include the frozen Workflow revision, node ID, rendered input, limits, attempt ordinal, and immutable deployment revision. Placement is resolved separately before each child payload is hashed. These records prove what was attempted; they do not weaken the atomic parent liveness and budget checks in amendments 1 and 6.

8. **Put the sync-test double outside admission, not in place of it.** The integration fixture must create a real ready inference target and exact deployment revision in the test database, then run the production route, parent controller, precedence resolver, trusted-child admission, broker submit/approve/claim, shared `InferenceRunner`, staging, receipt, and finalization paths. A deterministic fake may replace only provider construction/dispatch at the deployment-revision adapter boundary; it must record the exact revision and canonical payload it receives. The test must not monkeypatch the runner's `invoke`, the trusted child API, broker admission/claim/receipt, the resolver, stager, parent controller, or route service. This is an honest replacement for the obsolete configured-intel patch and proves two admitted model children plus no child for `keep_if`, not merely two calls to a fake prompt helper.

### Answers to the open questions

1. **Names and capability boundary:** Ratified as `operation.name = "sequence.run"` / `"workflow.run"` with `operation.version = 1` (the prose shorthand is `sequence.run@1` / `workflow.run@1`). `OuterRunContext` is ratified only with amendments 1 and 2: its possession is necessary, but atomic broker-side liveness, epoch, owner-identity, and active-tuple enforcement is the authority.
2. **Provenance split:** Ratified. A Sequence child is genuinely an execution of a persisted Recipe and therefore uses its exact `SavedDefinition`; a Workflow node or prompt is not a Recipe and therefore uses the named hashed `ServiceContract`. Neither side may mislabel the other merely to pass current liveness checks.
3. **Parent aggregate staging:** Required. Parent success uses a receipt-linked parent stage; direct result/Artifact persistence is not allowed. When children are finalized but no parent stage or success receipt exists, the truthful recovered state is an `indeterminate` parent with durable child receipts and any already receipt-gated partial checkpoints, but no final result or Artifact. The parent receives its own indeterminate terminal receipt through parent reconciliation.

### Named reservations for the owner's sitting

- **Partial-progress presentation:** An indeterminate parent may retain receipt-backed child checkpoints while having no aggregate Artifact. This is the truthful storage rule; the eventual desk wording and whether those checkpoints are exposed as resumable work remain an owner-sitting decision, not permission to call the parent failed or successful.
- **Current Workflow capability remains linear:** The inspected route executes a finite linear plan and refuses unsupported control flow. This ruling does not silently add branch, loop, fan-out, or retry semantics; future support must preserve the same budget and per-dispatch admission law.
- **Kernel seam verification:** The whitelisted evidence does not include broker transaction or parent-operation codec implementations, so counsel cannot verify that the existing broker exposes the atomic transaction seam amendment 1 requires. Implementers must add that seam rather than approximating it with adjacent transactions.

### Required test-matrix additions

Retain every test already named in §“Test matrix”, and add the following focused proofs:

| Required proof | Named test |
| --- | --- |
| Atomic liveness/epoch check versus cancellation; no check-submit TOCTOU child | `tests/unit/test_sequence_workflow_runner_migration.py::test_outer_context_liveness_and_epoch_check_is_atomic_with_child_admission` |
| Current owner-parent weakness is closed for a foreign identity even with a raw parent ID | `tests/unit/test_sequence_workflow_runner_migration.py::test_direct_owner_parent_id_requires_exact_principal_identity` |
| Capability is nonserializable and rejects cross-parent, stale-epoch, and cross-principal replay without a child | `tests/unit/test_sequence_workflow_runner_migration.py::test_outer_context_is_unexportable_and_replay_scoped` |
| Empty/zero-dispatch definitions still close exactly one authenticated parent receipt | `tests/unit/test_sequence_workflow_runner_migration.py::test_zero_dispatch_definition_receipt_closes_one_parent_without_children` |
| Child-finalize-wins and cancel-wins interleavings each have one CAS winner and preserve the child receipt | `tests/unit/test_sequence_workflow_runner_migration.py::test_cancel_publish_race_has_one_durable_advancement_winner` |
| Fallback/retry supersession and late success cannot both advance or bind output | `tests/unit/test_sequence_workflow_runner_migration.py::test_fallback_supersession_fences_late_success` |
| Crash after child receipt and before advancement recovers the checkpoint once, then closes the abandoned parent indeterminate | `tests/unit/test_sequence_workflow_runner_migration.py::test_restart_reconciles_receipted_child_then_closes_parent_indeterminate` |
| Parent crash before stage, after stage, and after success receipt yields the three outcomes in amendment 5 | `tests/unit/test_sequence_workflow_runner_migration.py::test_parent_aggregate_crash_gaps_reconcile_truthfully` |
| Failed/refused/cancelled/indeterminate parent outcomes are receipt-first and publish no aggregate Artifact | `tests/unit/test_sequence_workflow_runner_migration.py::test_parent_non_success_outcomes_are_receipt_closed_without_artifact` |
| Request/recovery replay duplicates neither parent, child, stage, nor Artifact | `tests/unit/test_sequence_workflow_runner_migration.py::test_parent_child_replay_is_idempotent_across_restart` |
| Finite child budget rejects an attempted unbounded retry/fallback before another dispatch | `tests/unit/test_sequence_workflow_runner_migration.py::test_child_budget_bounds_retry_and_model_fallback_dispatches` |
| Model/pure classification is exhaustive; unknown/cyclic/control-flow plans refuse before dispatch | `tests/unit/test_sequence_workflow_runner_migration.py::test_workflow_node_classification_is_closed_before_admission` |
| Recipe mutation between planning and admission refuses the stale exact revision rather than refreshing it | `tests/unit/test_sequence_workflow_runner_migration.py::test_sequence_child_refuses_recipe_revision_changed_after_planning` |
| Sync proof crosses real admission and staging while only provider dispatch is fake and receives the exact deployment revision | `tests/integration/test_primitive_framework_sync.py::test_ipad_synced_graph_workflow_runs_on_the_hub` |

Together with the existing named matrix, these tests map every chartered criterion and all seven invariants: cardinality and model/pure exclusion; exact causation/revisions/placement; authenticated one-path admission; cancellation and late-output fencing; durable non-success receipts and existing domain policy; receipt-gated child and aggregate writes; sync-registry repair; and parent crash/restart closure.
