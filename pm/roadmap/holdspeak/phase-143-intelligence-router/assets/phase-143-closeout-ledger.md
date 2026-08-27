# Phase 143 closeout ledger — final record

**Write-once record.** This is Phase 143's final evidence record. It may be
amended only by an owner ruling; it is not an issue tracker and has no waived
state.

**Close source:** S1 source commit `c55062e0ff89ef8ff41f8561ea2d091961a7e568`,
source tree `8f55eece1b31ebad78732c515bbf893e1c8ccd4a`; S2/S3 are documentary
close mechanics only. The current-tree verification record is
[`evidence-story-14.md`](../evidence-story-14.md) §Captured verification:
182 final guard tests and 218 citation spot tests passed under isolated HOME.

**Status vocabulary:** **PASS**, **HELD BY OWNER RULING**, and
**DOCUMENTED CARRY** are the only non-prose dispositions below. A carry is not
a waiver. Citations name the evidence capture and its production-path test; the
Story 14 citations name the current, isolated-HOME reruns.

## 1. Kill-criteria ledger

1. **PASS — “A capability resolves a mutable profile after admission.”**
   Constitution: **V.2–4, XI.1–4** (each invocation is admitted, bounded by
   derived authority, and receipted). Frozen profile, binding, deployment, and
   policy evidence is recorded before execution; later mutation applies only to
   the next parent. Evidence: [`evidence-story-05.md:8-19,86-95`](../evidence-story-05.md)
   (tree `9350cf95…`, 16 passed) and
   [`tests/unit/test_phase143_inference_route_plans.py`](../../../../../tests/unit/test_phase143_inference_route_plans.py);
   [`evidence-story-10.md:138-151`](../evidence-story-10.md) and
   [`tests/integration/test_phase143_placement_adoption_matrix.py::test_frozen_canonical_terms_survive_assignment_mutation_then_later_admission_sees_edit`](../../../../../tests/integration/test_phase143_placement_adoption_matrix.py).
   The latter was re-run in the 218-test citation spot run.

2. **PASS — “An engine/provider adapter performs a hidden retry or fallback.”**
   Constitution: **V.2–4, XI.1–4**. The controller, not an engine or adapter,
   elects a bounded attempt; the adapter renders/transports once. Evidence:
   [`evidence-story-06.md:7-15,41-50`](../evidence-story-06.md) and
   [`tests/unit/test_phase143_inference_fallback_controller.py`](../../../../../tests/unit/test_phase143_inference_fallback_controller.py),
   [`tests/unit/test_inference_runner.py`](../../../../../tests/unit/test_inference_runner.py);
   [`evidence-story-09.md:138-156`](../evidence-story-09.md) and
   [`tests/unit/test_phase143_tool_turn_routing.py::test_reference_adapter_renders_once_dispatches_once_and_parses_one_candidate`](../../../../../tests/unit/test_phase143_tool_turn_routing.py).
   All three files were re-run in the 218-test citation spot run.

3. **PASS (Python/web shipped scope); HELD BY OWNER RULING (Swift) — “A physical model call bypasses `InferenceRunner`.”**
   Constitution: **V.2–4, XI.1–4**. The scoped PASS is the generated Python/web
   census plus real-product adoption matrix:
   [`evidence-story-10.md:138-151`](../evidence-story-10.md),
   [`tests/unit/test_phase143_inference_capability_census.py::test_phase143_physical_leaves_have_no_legacy_bypass`](../../../../../tests/unit/test_phase143_inference_capability_census.py),
   and [`tests/integration/test_phase143_placement_adoption_matrix.py::test_every_python_placement_family_uses_real_product_objects_and_runner_receipts`](../../../../../tests/integration/test_phase143_placement_adoption_matrix.py).
   The census was in the 182-test final guard run; the matrix was re-run in the
   218-test spot run. The seven Swift leaves remain held, not erased (the exact
   generated inventory in `test_phase143_inference_capability_census.py:323-343`):
   `apple/Sources/InferenceLlama/LlamaProvider.swift:124|LLM.getCompletion`,
   `apple/Sources/Providers/Inference/OpenAIEndpointProvider.swift:48|InferenceProvider.URLSession.data`,
   `apple/Sources/Providers/Inference/StructuredOutput.swift:64|Swift.complete`,
   `apple/Sources/Providers/Desktop/MeshServeWorker.swift:99|Swift.complete`,
   `apple/Sources/RuntimeCore/Companion/CoderAnswer.swift:109|Swift.complete`,
   `apple/Sources/RuntimeCore/Workbench/BlueprintInterpreter.swift:333|Swift.complete`, and
   `apple/Sources/RuntimeCore/Workbench/WorkflowRunner.swift:338|Swift.complete`.
   Per the binding disposition in [`story-14-closeout-plan.md:296-314`](story-14-closeout-plan.md),
   the owner’s web-first ruling holds those leaves for future Swift recreation;
   `hold/hs143-10-slice5-swift-bridge` is the frozen recreation seed. No
   whole-repository zero-bypass claim is made.

4. **PASS — “An unknown/indeterminate/effectful outcome advances fallback.”**
   Constitution: **V.2–4, XI.1–4**, and **VI.1–3** (indeterminate state is
   named, never smoothed over). Evidence:
   [`evidence-story-06.md:7-15`](../evidence-story-06.md) and
   [`tests/unit/test_phase143_inference_fallback_controller.py`](../../../../../tests/unit/test_phase143_inference_fallback_controller.py);
   [`evidence-story-09.md:138-156`](../evidence-story-09.md) and
   [`tests/integration/test_phase143_tool_turn_boundaries.py::test_b4_restart_boundaries_and_stop_races_leave_no_new_egress`](../../../../../tests/integration/test_phase143_tool_turn_boundaries.py).
   Story 14 re-exercises dispatch-unknown after restart with one physical call
   and no second egress in
   [`tests/integration/test_phase143_closeout_chaos.py::test_one_restart_cross_product_preserves_frozen_recipe_receipt_library_and_assignment_truth`](../../../../../tests/integration/test_phase143_closeout_chaos.py),
   recorded in [`evidence-story-14.md`](../evidence-story-14.md). The controller
   and boundary files were re-run in the 218-test spot run; chaos was in the
   182-test final guard run.

5. **PASS — “Local→cloud fallback occurs without a saved visible boundary crossing.”**
   Constitution: **III.1–2** (the saved boundary is the only egress authority)
   and **V.2–4**. Evidence:
   [`evidence-story-06.md:22-32,63-73`](../evidence-story-06.md) and
   [`tests/unit/test_phase143_production_adoption.py::test_saved_local_to_cloud_boundary_crossing_and_unsaved_zero_egress`](../../../../../tests/unit/test_phase143_production_adoption.py).
   The test includes the available-but-unsaved cloud zero-egress control and was
   re-run in the 218-test citation spot run.

6. **PASS — “A tool-incompatible deployment can be saved or selected for required tools.”**
   Constitution: **V.2–4, XI.1–4**. Required-tool routes filter to an exact
   qualified deployment and refuse before a child when no qualified profile
   exists. Evidence: [`evidence-story-09.md:138-156`](../evidence-story-09.md)
   and [`tests/unit/test_phase143_tool_turn_routing.py::test_required_tool_routes_filter_to_exact_qualified_deployment_only`](../../../../../tests/unit/test_phase143_tool_turn_routing.py),
   [`tests/unit/test_phase143_tool_turn_routing.py::test_required_tool_preflight_refuses_without_qualified_profile_and_zero_children`](../../../../../tests/unit/test_phase143_tool_turn_routing.py);
   the real Recipe adopter is covered by
   [`tests/integration/test_phase143_placement_adoption_matrix.py::test_qualified_recipe_chat_and_agent_facade_freeze_toolturn_before_assignment_edit`](../../../../../tests/integration/test_phase143_placement_adoption_matrix.py).
   These production tests were re-run in the 218-test citation spot run.

7. **PASS — “Browser code invents capability compatibility, readiness, or fallback law.”**
   Constitution: **VI.1–3**, **VIII.3**, and **IX.1–4**. The browser renders the
   server projection and its named issues; it does not reconcile compatibility.
   Evidence: [`evidence-story-13.md:138-155`](../evidence-story-13.md) and
   [`tests/e2e/test_hs143_assignments_glass.py::test_assignments_editor_real_hub_next_run_preview_and_conflict`](../../../../../tests/e2e/test_hs143_assignments_glass.py);
   [`evidence-story-11.md:138-154`](../evidence-story-11.md) and
   [`tests/unit/test_phase143_transport_parity.py`](../../../../../tests/unit/test_phase143_transport_parity.py).
   Both test files were in the 182-test final guard run.

8. **PASS — “Config and the assignment store remain competing authority after migration.”**
   Constitution: **V.2–4, XI.1–4**. One-way marker and post-marker-refusal
   proofs leave the assignment store as authority; a frozen run never reads
   Config to retarget. Evidence: [`evidence-story-04.md:8-18,34-42`](../evidence-story-04.md)
   and [`tests/unit/test_phase143_inference_assignments.py::test_migration_marker_is_one_way_hash_bound_and_requires_durable_assignments`](../../../../../tests/unit/test_phase143_inference_assignments.py);
   [`evidence-story-10.md:138-151`](../evidence-story-10.md) and
   [`tests/unit/test_phase143_routing_authority_census.py::test_phase143_placement_adopters_have_zero_python_resolution_forks`](../../../../../tests/unit/test_phase143_routing_authority_census.py).
   The census was in the 182-test final guard run.

9. **PASS — “The default UI grows one permanent row per capability or becomes a matrix.”**
   Constitution: **VIII.3** and **IX.1–4**. The server projects exactly seven
   assignment rows and the real hub confirms 1440, 393, 200%, keyboard,
   screen-reader, reduced-motion, target, and overflow facts. Evidence:
   [`story-13-capability-assignments-experience.md:45-57,84-101`](../story-13-capability-assignments-experience.md)
   and [`tests/e2e/test_hs143_assignments_glass.py::test_assignments_overview_real_hub`](../../../../../tests/e2e/test_hs143_assignments_glass.py).
   Story 14’s ready-barrier repair and isolated-HOME rerun are recorded in
   [`story-14-chaos-glass-closeout.md:42-58`](../story-14-chaos-glass-closeout.md)
   and [`evidence-story-14.md`](../evidence-story-14.md); the full glass file was
   in the 182-test final guard run.

10. **PASS — “HTTP/MCP/Desk produce different assignment, plan, attempt, or receipt truth.”**
    Constitution: **V.2–4, XI.1–4**. HTTP and MCP compose the same application
    methods; Desk is the real web owner surface over HTTP, not a third router.
    Evidence: [`evidence-story-11.md:138-154`](../evidence-story-11.md) and
    [`tests/unit/test_phase143_transport_parity.py::test_transport_parity_vectors`](../../../../../tests/unit/test_phase143_transport_parity.py),
    [`tests/unit/test_phase143_transport_parity.py::test_assignment_set_committed_effect_replay_is_identical_but_not_a_projection`](../../../../../tests/unit/test_phase143_transport_parity.py);
    Desk’s real-hub path is in
    [`tests/e2e/test_hs143_assignments_glass.py::test_assignments_editor_real_hub_next_run_preview_and_conflict`](../../../../../tests/e2e/test_hs143_assignments_glass.py).
    Both files were in the 182-test final guard run.

11. **PASS — “Sync import starts/resumes inference or rewrites hub-local assignments.”**
    Constitution: **III.1–2, V.2–4, VI.1–3, XI.1–4**. Router-shaped v2 sync
    bytes refuse before merge, pull omits the bucket, and v1 cannot mint v2
    authority. Evidence: [`evidence-story-11.md:138-154`](../evidence-story-11.md)
    and [`tests/unit/test_phase143_inference_assignments.py::test_assignment_authority_is_hub_local_and_hostile_sync_refuses`](../../../../../tests/unit/test_phase143_inference_assignments.py);
    the recovered production composition re-checks this in
    [`tests/integration/test_phase143_closeout_chaos.py::test_one_restart_cross_product_preserves_frozen_recipe_receipt_library_and_assignment_truth`](../../../../../tests/integration/test_phase143_closeout_chaos.py).
    Chaos was in the 182-test final guard run.

12. **PASS — “A receipt cannot explain primary, attempts, fallback reason, actual model, boundary, and terminal outcome without reading current settings.”**
    Constitution: **V.2–4, XI.1–4**, and **VI.1–3**. The closeout run freezes a
    Recipe route, mutates its assignment after admission, restarts once, and
    reads the durable route/tool receipt and reconstructed plan: primary profile,
    ordinal, purpose/fallback reason, boundary, receipt hash, route-plan hash,
    and terminal result all remain readable without Config/current-profile
    resolution. Evidence: [`evidence-story-14.md`](../evidence-story-14.md) and
    [`tests/integration/test_phase143_closeout_chaos.py::test_one_restart_cross_product_preserves_frozen_recipe_receipt_library_and_assignment_truth`](../../../../../tests/integration/test_phase143_closeout_chaos.py),
    re-run in the 182-test final guard run. This is the required one-restart
    production composition, not a SIGKILL theatre harness.

## 2. Exit-criterion cross-links

1. **PASS — “Every production inference call site belongs to one versioned capability.”**
   Evidence: kill rows 1 and 3; [`evidence-story-10.md:138-151`](../evidence-story-10.md);
   [`tests/unit/test_phase143_inference_capability_census.py`](../../../../../tests/unit/test_phase143_inference_capability_census.py),
   final-run PASS in [`evidence-story-14.md`](../evidence-story-14.md). The Swift
   scope is the explicit HELD record in row 3, not a fabricated zero.
2. **PASS — “Every execution freezes one immutable route plan before first egress.”**
   Evidence: kill rows 1 and 12; [`evidence-story-05.md:8-19,86-95`](../evidence-story-05.md);
   [`tests/integration/test_phase143_closeout_chaos.py`](../../../../../tests/integration/test_phase143_closeout_chaos.py).
3. **PASS (Python/web shipped scope); HELD BY OWNER RULING (Swift) — “Every physical generation remains a separately admitted `InferenceRunner` / `inference.invoke@1` child.”**
   Evidence: kill row 3; [`tests/unit/test_one_path_cardinality.py`](../../../../../tests/unit/test_one_path_cardinality.py)
   and the capability census, both final-run PASS in
   [`evidence-story-14.md`](../evidence-story-14.md). The exact Swift hold and
   frozen bridge are row 3’s owner-ruling record.
4. **PASS — “Ordered fallback advances only for a closed eligible disposition and its receipt explains every leg, child, boundary, and terminal outcome.”**
   Evidence: kill rows 2, 4, 5, and 12; [`evidence-story-06.md:7-15`](../evidence-story-06.md);
   [`tests/integration/test_phase143_tool_turn_boundaries.py`](../../../../../tests/integration/test_phase143_tool_turn_boundaries.py);
   Story 14 chaos receipt reconstruction.
5. **PASS — “Config/profile/subject legacy pointers have one-way migrations and no competing authority remains after each family crosses.”**
   Evidence: kill row 8; [`evidence-story-04.md:34-42`](../evidence-story-04.md);
   [`tests/unit/test_phase143_subject_pointer_migration.py`](../../../../../tests/unit/test_phase143_subject_pointer_migration.py);
   final routing-authority census in [`evidence-story-14.md`](../evidence-story-14.md).
6. **PASS — “Adding/downloading/connecting a model changes zero assignments.”**
   Evidence: [`evidence-story-12.md:138-154`](../evidence-story-12.md);
   [`tests/unit/test_phase143_inference_assignments.py::test_adding_a_profile_leaves_assignment_bytes_identical`](../../../../../tests/unit/test_phase143_inference_assignments.py);
   Story 14’s durable Model Library replay and assignment-head byte identity in
   [`tests/integration/test_phase143_closeout_chaos.py`](../../../../../tests/integration/test_phase143_closeout_chaos.py).
7. **PASS — “Model Library and bounded Assignments glass pass at 1440, 393, and 200% zoom with keyboard/screen-reader/reduced-motion proof.”**
   Evidence: [`story-12-model-library-providers.md:90-109`](../story-12-model-library-providers.md)
   and [`story-13-capability-assignments-experience.md:84-101`](../story-13-capability-assignments-experience.md);
   [`tests/e2e/test_hs143_assignments_glass.py`](../../../../../tests/e2e/test_hs143_assignments_glass.py),
   final-run PASS in [`evidence-story-14.md`](../evidence-story-14.md). The owner-shot
   disposition is recorded in §3 below.
8. **PASS — “HTTP/MCP parity, OWNER boundary, hub-local sync, restart, privacy, schema, API inventory, one-path census, full tests, and production build are green.”**
   Evidence: kill rows 10 and 11; 182 current isolated-HOME doc/census/one-path/API/parity/chaos/glass guards in
   [`evidence-story-14.md`](../evidence-story-14.md); production build and glass
   checks in [`story-12-model-library-providers.md:101-109`](../story-12-model-library-providers.md)
   and [`story-13-capability-assignments-experience.md:92-101`](../story-13-capability-assignments-experience.md).
   “Full tests green” is the plan’s accepted **exact-baseline/zero-branch-new**
   rule, not a raw-zero failure claim: [`story-14-closeout-plan.md:180-199,296-314`](story-14-closeout-plan.md)
   fixes the exact 11 named inherited nodes and rejects any extra node. Story 11
   records its 6677-passed/11-inherited pre-capture sweep at
   [`evidence-story-11.md:138-150`](../evidence-story-11.md).
9. **PASS — “All kill criteria in `assets/architecture-contract.md` have production-path evidence in Story 14's write-once ledger.”**
   Evidence: this twelve-row section, the cited shipped test files, and the
   current isolated-HOME verification record
   [`evidence-story-14.md`](../evidence-story-14.md). No criterion is waived.

## 3. Owner-glass record

**PASS — session record accepted by orchestrator disposition.** Constitution
**VIII.3** makes phone glass first-class; **IX.1–4** requires the real-hub walk
and owner verdict where required. The binding disposition states that this is
satisfied by the session record, not a re-ask:
[`story-14-closeout-plan.md:296-314`](story-14-closeout-plan.md). The cited
session record is Story 12’s 1440/393 shot delivery to the owner before merge
([`story-12-model-library-providers.md:90-93`](../story-12-model-library-providers.md))
and the final 200% review set ([`story-12-model-library-providers.md:101-109`](../story-12-model-library-providers.md)),
together with Story 13’s real-hub 1440/393/200% walk and final regenerated
shots ([`story-13-capability-assignments-experience.md:84-101`](../story-13-capability-assignments-experience.md)).
Both merge sequences followed delivery. No new owner ask is claimed or needed.

## 4. Inherited-failure baseline — documented carry

The current exact baseline is these 11 failed nodes and their non-router owner;
no new failed node may be called inherited without same-baseline reproduction
or an orchestrator assignment. This is the accepted close rule in
[`story-14-closeout-plan.md:180-199,296-314`](story-14-closeout-plan.md).

| Current inherited red family (11 tests) | Owner/disposition |
|---|---|
| `test_ask_grounding_claims.py::{test_flags_an_unsupported_claim_and_not_a_supported_one,test_no_grounding_claims_when_no_context_material}`; `test_ask_runner_migration.py::test_ask_uses_versioned_contract_hash_runner_and_staged_projection` | Pre-143 Ask/grounding contract ownership; carry to its owner, not router closeout. |
| `tests/uat/test_build_ledger.py::test_committed_ledger_is_up_to_date` | UAT/build-ledger ownership; documentation/build inventory drift, not runtime routing. |
| `test_interior_canon_guard.py::test_no_left_border_rails_in_web_css`; `test_product_copy.py::test_primary_copy_has_no_prohibited_operational_drift`; `test_product_language.py::test_primary_ui_has_no_new_unqualified_ambiguous_terms`; `test_web_null_read_guard.py::test_product_components_do_not_mutate_global_dom_or_inject_html` | Cross-surface web grammar/copy hygiene ownership; pre-existing unrelated violations. |
| `test_kernel_effect_fence.py::{test_kernel_broker_modules_stay_within_line_budget,test_kernel_broker_has_zero_driver_specific_conditionals}` | Kernel architecture/debt ownership; do not contort routed code to satisfy it. |
| `test_inference_setup_capability_truth.py::test_first_and_repeated_reads_do_not_mutate_database_or_config` | Inference setup legacy-read authority ownership; carry separately unless a final-tree triage identifies an actual new router change. |

## 5. Swept Story 07–13 ledger notes

| Source/item | Final disposition | Evidence/rationale |
|---|---|---|
| Story 07 triage/evidence. | **CLOSE-WITH-EVIDENCE.** | No open ledger item; restart, Stop, boundary, and no-post-marker-Config proofs feed kill rows 1, 2, 5, 8, and 12. |
| Story 08 full-suite failures and Story 09 full-suite failures. | **DOCUMENTED CARRY.** | Baseline-triaged, not Story 08/09 regressions; the current set is the 11-node baseline above, not an old raw count. |
| C1 checkpoint findings (ten across rounds 1–5). | **CLOSE-WITH-EVIDENCE.** | All ten fixed with committed proofs; sleep/resume/takeover are explicit sitting notes under the owner’s yolo ruling. |
| C3 audit note 1: per-pass handoff/recovery SQLite scans. | **CARRY-TO-BACKLOG IF MEASURED PAIN APPEARS.** | Single-user, cadence-bounded, no damage; candidate dirty/unsettled-count gate recorded in `story-08-c3-counsel.md:51-60`. |
| C3 audit note 2: injected fence-fault → legacy enqueue collision. | **CARRY AS FAULT-ONLY NOTE.** | Only reproduced with injected handoff failure; ruled out under the capped fault rule, not represented as a normal-action pass. |
| C3 audit notes 3/4: serial Stop cancel loop and missing unsettled-handoff index. | **CLOSE-WITH-EVIDENCE.** | Daemonised post-commit cancellation measured `stop_wall_ms=16.31`; additive index and snapshot proof landed. |
| Phase D: remote speech transport. | **CARRY-TO-BACKLOG.** | Admission refuses it honestly until an audio transport exists; future capability, not router bypass. |
| Phase D: faster-whisper constructor-inseparable load. | **DOCUMENTED NARROW EXCEPTION.** | Local-only exception honoured; production-shaped warm/cold proofs exist. |
| Phase D: continuity proof’s `Transcriber.__new__`/internal subclass. | **CARRY-TO-BACKLOG.** | Explicit proof debt, not a product failure; migration/bundle/controller continuity otherwise proven. |
| Phase E’s four receipt/execution defects and Rails migration sweep catch. | **CLOSE-WITH-EVIDENCE.** | All fixed in its one permitted round; Phase E carries no new ledger item. |
| Story 09 byte-length token reservation. | **DOCUMENTED NARROW CARRY.** | Conservative over-reservation, never under-reservation; no authority/egress expansion. |
| Story 09 any-effect replay guard under P=1 effect ceiling. | **DOCUMENTED NARROW CARRY.** | Equivalent protection under frozen ceiling; receipts/effect adoption remain tested. |
| Story 09 dispatch-unknown ownership by generic controller. | **CLOSE-WITH-EVIDENCE.** | Correct shared-controller ownership, exercised by generic and B4 boundary tests. |
| Story 09 turn-state-transition observation. | **CLOSE-WITH-EVIDENCE.** | B2 multi-step implementation makes model/tool/final/terminal states truthful. |
| Story 10 dead standalone Recipe-entry workbench tier. | **CARRY-TO-BACKLOG.** | No production transport passes it; non-routing attribution cleanup, not a false current route. |
| Story 10 seven Swift leaves. | **HELD BY OWNER RULING.** | Named in kill row 3; frozen bridge `hold/hs143-10-slice5-swift-bridge` retained. |
| Story 10 census xdist and Story 12 refinement xdist flakes. | **DOCUMENTED LOAD FLAKES.** | Serial-green evidence exists; distinct from the former genuine 393 timing race. |
| Story 12 generic `error_500` exception-string concern. | **CLOSE-WITH-EVIDENCE.** | S5 proved post-secret scrub and sentinel absence. |
| Story 12 44px assertion width coverage and reduced-motion spot check. | **CLOSE-WITH-EVIDENCE THROUGH RERUN.** | Cosmetic audit notes; real-hub paths repeated in final glass run. |
| Story 11 stale `MCP_SIDECAR` resource-count prose. | **CLOSE-WITH-EVIDENCE.** | Fixed in Story 11 close commit. |
| Story 11 `[populated-1440]` and refinement-coordinator xdist/serial-green flakes. | **DOCUMENTED LOAD FLAKES.** | Remain separate from the repaired 393 readiness race; reclassify only on serial reproduction. |

The 393 fixture’s honest note is retained: Story 14 repaired an owner-specific
server-summary readiness barrier; the test no longer depends on the generic
shell’s early existence. The evidence is the S1 progress record
[`story-14-chaos-glass-closeout.md:42-58`](../story-14-chaos-glass-closeout.md)
and the final full glass-file rerun in [`evidence-story-14.md`](../evidence-story-14.md).
