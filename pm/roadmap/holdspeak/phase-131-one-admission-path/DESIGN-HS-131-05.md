# HS-131-05 design — Workbench work and memory through the admitted runner

**Status:** DRAFT — awaiting Sol ruling  
**Decision boundary:** migrate manual Workbench execution to HS-131-04's parent/child, durable-CAS, and staged-projection platform. This does not change provider dispatch, parent-controller recovery, scheduling authority, or Workbench product semantics.

## Context

Manual execution passes an authenticated principal into `WorkbenchService.run()` but drops it when it calls `run_workbench(workbench_id)` (`holdspeak/services/workbench_service.py:162-165`). The conductor then creates a native `workbench_runs` row before building an engine (`holdspeak/workbench_conductor.py:469-480`), resolves one target for the whole run (`:452-467`), and calls `intel.run_prompt` directly for each item (`:563-568`). On success it writes the item and auto-mints its Artifact before the hidden second direct model call for memory (`:569-623`); it completes the history row only at the end (`:648-662`). There is no active parent cancellation seam in this path.

HS-131-04 already provides the required platform: `ParentRunController` creates durable receipt-closed parents and `cancel_by_operation_id()` checks exact owner under lock (`holdspeak/kernel/parent_run.py:105-129,169-194`); trusted child admission atomically validates the live context, budget, owner, and epoch while recording the active tuple (`holdspeak/kernel/trusted_child.py:16-63`); and the checkpoint CAS admits a domain advance only for the exact open tuple (`holdspeak/kernel/parent_checkpoint.py:10-51`). Its Sequence/Workflow exemplar is parent start → child placement/provenance → publisher/stage → receipt → finalize → aggregate parent stage/receipt/close (`holdspeak/services/sequence_workflow_service.py:81-113`).

## 1. One manual attempt is one authenticated `workbench.run@1` parent

The existing manual owner gesture supplies the authenticated principal to the service; the service passes it to `ParentRunController.start`, never self-approves as owner. One manual attempt admits exactly one durable `workbench.run`, version 1, parent before any provider work. Its frozen input records the Workbench ID, pending-item IDs/order, Recipe ID/revision, frozen `memory_enabled` execution option, and request/idempotency key; its deadline and native attempt ID are durable.

`child_budget` is finite at admission: the number of frozen pending items plus that same number when `memory_enabled` is true. The existing no-body manual route defaults the execution option to true; a caller/service path that explicitly disables memory freezes false without a UI change. Empty/no-pending attempts may close one receipt-backed parent with zero children and retain the current skipped result.

## 2. Each provider dispatch is one distinct causally linked child

For every frozen item that reaches model generation, the conductor uses only the trusted-child runner API and creates one item child. After its successful receipt-gated item checkpoint, it may create one *distinct* memory child for that item. The memory child payload and projection name the source item child invocation/operation/receipt IDs; it is not nested in, or represented by, the item receipt. A disabled-memory attempt admits no memory child. No `intel.run_prompt` or other direct model call remains in manual execution.

Children are serial under the parent: `item:<item-id>` then, if enabled and eligible, `memory:<item-id>`. Each admission consumes one budget slot. An item failure/refusal/cancellation retains its own child receipt, uses the existing item failure state, and admits no memory child for that item; subsequent item policy remains the current Workbench loop policy.

## 3. Placement and provenance are resolved and frozen per child

Immediately before each child is built, resolve Phase-130 precedence independently: invocation override (none for this manual path) → Workbench target override → backing Recipe/Agent default → global default. Capture the resulting ready target's deployment revision before hashing the payload; later target or profile edits cannot retarget either an item or its memory writeback.

The item child genuinely executes the persisted Recipe used by the current conductor (`workbench_conductor.py:447-488`), so its origin is `SavedDefinition(ref="recipe:<recipe-id>", revision=<frozen recipe revision>)`. Its canonical payload adds frozen Workbench and item IDs/revisions, rendered prompt/input hash, skills/context facts, attempt ordinal, and deployment revision. The memory prompt is hard-coded service behavior, not an execution of that Recipe (`workbench_conductor.py:603-614`), so its origin is the hashed `ServiceContract` `holdspeak.workbench-memory@1`; its payload includes the parent/workbench/item IDs, source item child IDs, bounded source-output hash/content, prompt-contract revision, and deployment revision. Provenance records what was attempted and does not replace trusted-child liveness checks.

## 4. Model-derived Workbench writes are staged; coordination stays plain

Reuse the HS-131-04 stager and parent checkpoint protocol. An item child publisher stages `workbench-item-output` before its success receipt; finalization, in the stager transaction, verifies the exact `(epoch, planned_node, child)` tuple and only then writes `workbench_items.result/status/completed_at`, receipt/operation linkage, and any output-derived Artifact/mint record. A stale successful child remains a receipt-linked checkpoint with `advanced=false`, never an item result or Artifact.

A memory child similarly stages `workbench-memory-writeback`, referencing its source item receipt; only its successful receipt and matching CAS may append the memory observation with operation/receipt IDs. The parent success path stages `workbench-run-result` before the parent receipt and then finalizes the completed `workbench_runs` attempt/history summary, ordered child links, counts, egress facts, and parent operation/receipt IDs. A parent stage after a crash is recovered by the existing stager; an abandoned parent follows HS-131-04 reconciliation to one indeterminate receipt, with no successful attempt summary.

Plain persistence remains limited to pre-dispatch item claiming, frozen attempt/admission metadata, active-child/lease coordination, non-authoritative progress events, and failure/cancellation diagnostics. It must not expose model output, memory, an output-derived Artifact, or a completed history result before its linked receipt.

## 5. Cancellation is parent-scoped and closes advancement

The manual cancellation endpoint/service uses `ParentRunController.cancel_by_operation_id(principal, parent_operation_id)`, not a Workbench ID lookup. Its existing locked owner check means a request cannot cross Workbenches, and its state/epoch transition closes new trusted-child admission before it cancels the recorded active child (`holdspeak/kernel/parent_run.py:169-194`). Repeated cancellation returns the existing disposition; it never changes a terminal child or parent receipt.

If cancellation wins before an item child checkpoint, no item output or memory child/write exists. If item checkpoint finalization wins first, its output and receipt-linked Artifact remain truthful; cancellation then prevents the memory admission, or cancels the active memory child. If cancellation wins first, the checkpoint CAS rejects late advancement, so no late item output, Artifact, or memory write occurs. In either interleaving child terminal receipts remain durable. The parent closes `CANCELLED` only with its immutable terminal receipt.

## 6. Existing walk coverage moves from visual continuity to receipt truth

`tests/e2e/test_workbench_walk.py` is currently a screenshot-only desk/configuration walk (`:53-117`), not an execution/cancellation proof. Its existing cases continue to prove no UI redesign. HS-131-05 adds focused execution cases there for one item, enabled/disabled memory, cancellation at both boundaries, and history receipt linkage; they drive the production route/service with a deterministic provider only at the deployment adapter boundary, not by bypassing admission or staging.

## 7. Non-changes

Scheduled Workbench authority and bounded delegated schedules remain HS-131-06. This story does not redesign the Workbench UI, Agent/skill ownership, memory model, recall prompt, or writeback wording. It reuses HS-131-04 recovery, trusted-context, receipt, and projection mechanisms rather than adding adversarial-hardening machinery.

## Invariants

1. Every manual Workbench attempt has exactly one authenticated, receipt-closed `workbench.run@1` parent.
2. Every actual item or memory provider dispatch has exactly one admitted child and terminal receipt; memory is a distinct child and disabled memory has none.
3. Each child is causally parent-linked and records frozen origin, per-child Phase-130 placement, and immutable deployment revision.
4. Item output, output-derived Artifact, memory, and completed attempt/history are visible only through matching receipt-gated projections.
5. Parent cancellation is owner-scoped and idempotent, fences admission and late writes with the durable epoch CAS, and never alters terminal receipts.
6. Manual Workbench provider work has no direct dispatch path outside the admitted runner.

## Test matrix

| Acceptance criterion / invariant | Planned focused proof |
| --- | --- |
| One authenticated manual parent | `tests/unit/test_workbench_runner_migration.py::test_manual_attempt_creates_one_authenticated_workbench_parent` |
| One item child and terminal receipt per item call | `tests/unit/test_workbench_runner_migration.py::test_each_item_provider_call_has_one_admitted_child_and_receipt` |
| Distinct causal memory child | `tests/unit/test_workbench_runner_migration.py::test_memory_writeback_is_a_distinct_child_linked_to_its_item_child` |
| Disabled memory has no child | `tests/unit/test_workbench_runner_migration.py::test_memory_disabled_admits_no_memory_child` |
| Per-child precedence, origin, frozen deployment | `tests/unit/test_workbench_runner_migration.py::test_item_and_memory_children_freeze_provenance_and_per_child_placement` |
| Receipt-gated native projections/history | `tests/unit/test_workbench_runner_migration.py::test_item_memory_artifact_and_attempt_history_are_receipt_gated` |
| Cancel before item completion | `tests/unit/test_workbench_runner_migration.py::test_cancel_before_item_checkpoint_leaves_no_item_or_memory_write` |
| Cancel after item, before/during memory | `tests/unit/test_workbench_runner_migration.py::test_cancel_after_item_preserves_item_and_fences_memory_late_write` |
| Idempotent, owner-scoped cancellation and immutable receipts | `tests/unit/test_workbench_runner_migration.py::test_repeated_or_foreign_parent_cancel_cannot_cross_workbenches_or_mutate_receipts` |
| No manual direct model path | `tests/unit/test_workbench_runner_migration.py::test_manual_workbench_uses_only_trusted_runner_children` |
| Production route walk of item, memory, cancel, and linkage | `tests/e2e/test_workbench_walk.py::test_manual_run_receipt_linkage_and_cancellation_boundaries` |

## Open questions for Sol

1. Ratify `workbench.run` version 1 and the parent snapshot/budget of one item slot plus one optional memory slot per frozen item.
2. Ratify the provenance split: `SavedDefinition` for Recipe-backed item work and `holdspeak.workbench-memory@1` for the hard-coded memory prompt.
3. Ratify the narrow, default-true frozen `memory_enabled` service execution option as the no-UI way to meet the disabled-memory contract.

## Sol ruling

**Verdict: RATIFIED WITH AMENDMENTS.** The design covers the chartered acceptance criteria one-to-one once the three amendments below are applied. The current conductor performs exactly one item generation and, after each successful item generation, exactly one memory generation; it has no retry or multi-generation branch, so the proposed `N + (memory_enabled ? N : 0)` budget is correct.

### Binding amendments

1. Register `workbench.run@1` as a supported parent kind end to end. `ParentRunController.start()` and `ParentRunCodec` currently admit only `sequence` and `workflow`; implementation must add `workbench` to that existing parent platform and register its codec before the service can start the parent promised by §1. This is an extension of the shipped mechanism, not a parallel controller.

2. Make the frozen parent deadline an execution fence, not metadata. Cap every child dispatch by the parent's remaining time; when the deadline expires, transition/fence the parent through the existing epoch-changing cancellation/terminal path, stop queued admission, and cancel the active child. A child completing after expiry must fail the same checkpoint CAS as a child completing after explicit cancellation. Without this, an already-active provider can finish and project output after the promised deadline.

3. Gate the parent `workbench-run-result` projection on the winning parent receipt. If cancellation wins after the completed-result stage is written but before the parent closes, that stage must not finalize a completed history row; it must be discarded or remain non-advanced, while the native attempt records the `CANCELLED` receipt and resolvable child links. Conversely, if success/failure close wins first, later cancellation returns that terminal disposition. Every terminal native attempt/history read—including cancelled and failed attempts—must resolve the parent operation/receipt and admitted child invocation/receipt links; only the winning non-cancelled receipt may expose its completed aggregate.

### Answers to the open questions

1. **Ratified, subject to amendments 1 and 2.** `workbench.run@1` is the right parent, and one item slot plus one optional memory slot per frozen item matches the actual serial loop. There is no conductor retry or extra generation to budget.
2. **Ratified.** The item call renders and executes the persisted Recipe's system prompt, skills, standing context, and Recipe-selected placement default, so `SavedDefinition` is truthful. The separate hard-coded writeback prompt is service behavior and correctly uses hashed `holdspeak.workbench-memory@1` provenance.
3. **Ratified.** A frozen, default-true `memory_enabled` service option preserves current manual behavior and provides an honest no-memory path without inventing UI.

### Recorded notes for the owner's sitting

- The shipped trusted-child capability, owner/epoch checks, finite budget, and checkpoint CAS are sufficient for this single-user yolo-mode story; no additional adversarial-hardening layer is warranted.
- The existing conductor resolves one target before the loop. The design intentionally changes that to per-child Phase-130 resolution and frozen deployment revision; this is required placement truth, not a Workbench behavior redesign.
- Item output, auto-minted Artifact state, memory observation, and completed aggregate are all model-derived and are correctly assigned to receipt-gated staging. Claims, progress events, and failure/cancellation diagnostics may remain plain.

### Required test additions

- Add a focused proof that `workbench.run@1` is registered and accepted by the shipped parent controller for an authenticated principal.
- Add a deadline race test with an active deterministic provider: expiry advances the epoch, blocks queued/memory admission, cancels the active child, and rejects its late item/memory/Artifact projection.
- Extend the parent cancellation-boundary test to pause after `workbench-run-result` staging but before parent close, let cancellation win, and prove no completed history aggregate appears while the cancelled attempt still resolves its parent and child receipts.
