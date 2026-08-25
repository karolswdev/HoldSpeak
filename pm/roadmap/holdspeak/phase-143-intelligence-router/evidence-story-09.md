# Evidence - HSEGHS001HS104-143-09

- **Story:** HSEGHS001HS104-143-09 - Tool Capability Foundation and Safe Routing
- **Status:** done
- **Date:** 2026-08-24

## Proof

### Captured run — 2026-08-25T03:37:06Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright npm_config_cache=$HOME_REAL/.npm uv run --python 3.13.11 pytest -q -n auto --ignore=tests/e2e/test_metal.py 2>&1 | tail -120`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 395f845be67d9cced57182802cd4adb8627d2e05

```text
        monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: _FakeIntel())
        monkeypatch.setattr(
            "holdspeak.intel.providers._configured_engine", lambda: _FakeIntel()
        )
    
        resp = client.post(f"/api/workflows/{wid}/run", json={"input": "the meeting"})
>       assert resp.status_code == 200
E       assert 409 == 200
E        +  where 409 = <Response [409 Conflict]>.status_code

tests/unit/test_web_routes_primitives.py:666: AssertionError
______________________ test_run_chain_engine_error_is_502 ______________________
[gw4] darwin -- Python 3.13.11 /Users/karol/dev/tools/HoldSpeak/.venv/bin/python3

client = <starlette.testclient.TestClient object at 0x118808050>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x1191e9be0>

    def test_run_chain_engine_error_is_502(client: TestClient, monkeypatch) -> None:
        a1 = _make_agent(client, "A1", "{input}")
        cid = client.post("/api/chains", json={"name": "C", "steps": [a1]}).json()["chain"]["id"]
    
        from holdspeak.intel.models import MeetingIntelError
    
        class _Boom:
            active_provider = None
    
            def run_prompt(self, **kwargs):
                raise MeetingIntelError("no model")
    
        # HS-131-13: the admitted `this_machine` child builds `MeetingIntel` from
        # its FROZEN revision, so the same double goes on the engine class too.
        monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: _Boom())
        monkeypatch.setattr(
            "holdspeak.intel.providers._configured_engine", lambda: _Boom()
        )
        resp = client.post(f"/api/chains/{cid}/run", json={"input": "x"})
>       assert resp.status_code == 502
E       assert 409 == 502
E        +  where 409 = <Response [409 Conflict]>.status_code

tests/unit/test_web_routes_primitives.py:433: AssertionError
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/e2e/test_workbench_walk.py:46: no hub listening at http://localhost:8778
SKIPPED [1] tests/e2e/test_dictation_enrichment_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation enrichment e2e
SKIPPED [1] tests/e2e/test_dictation_journal_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation journal e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:44: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:52: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [12] tests/e2e/test_dogfood_plumbing_e2e.py:66: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:85: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:95: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [2] tests/e2e/test_hs14104_refinement_glass.py:58: superseded by the Thought Workbench real-path glass
SKIPPED [2] tests/e2e/test_hs14105_context_glass.py:109: superseded by the Thought Workbench real-path glass
SKIPPED [2] tests/e2e/test_hs14105a_default_context_glass.py:99: superseded by the Thought Workbench real-path glass
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.6XPhMHvcDy/xdist-gw1/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_grounding_rails_live.py:35: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:54: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:71: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_rails_observer_live.py:37: no rail events on this machine to summarize
SKIPPED [1] tests/integration/test_rails_observer_live.py:72: no rail events on this machine
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.6XPhMHvcDy/xdist-gw2/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.6XPhMHvcDy/xdist-gw2/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
SKIPPED [1] tests/uat/test_induction_integration_43.py:107: live .43 model proof is opt-in: set HOLDSPEAK_UAT_LIVE_43=1 (it runs a real extraction on the LAN model and takes minutes)
SKIPPED [1] tests/uat/test_induction_integration_43.py:118: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [1] tests/uat/test_mesh_dispatch.py:85: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [10] tests/e2e/test_meeting_transcription.py: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_mermaid_renders.py:101: mermaid renderer unavailable in this env: core/lib/esm/puppeteer/node/BrowserLauncher.js:55:28)
    at async run (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:862:19)
    at async cli (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:374:3)
FAILED tests/unit/test_ask_grounding_claims.py::test_flags_an_unsupported_claim_and_not_a_supported_one
FAILED tests/unit/test_ask_grounding_claims.py::test_no_grounding_claims_when_no_context_material
FAILED tests/unit/test_ask_runner_migration.py::test_ask_uses_versioned_contract_hash_runner_and_staged_projection
FAILED tests/unit/test_capability_invocations.py::test_failed_run_keeps_input_and_grounding_for_retry
FAILED tests/uat/test_build_ledger.py::test_committed_ledger_is_up_to_date - ...
FAILED tests/unit/test_doc_drift_guard.py::test_no_user_facing_doc_leaks_roadmap_vocabulary
FAILED tests/unit/test_engine_off_the_loop.py::test_ask_runs_the_engine_off_the_loop
FAILED tests/unit/test_engine_off_the_loop.py::test_recipe_run_and_chat_run_the_engine_off_the_loop
FAILED tests/unit/test_engine_off_the_loop.py::test_chain_runs_the_engine_off_the_loop
FAILED tests/unit/test_engine_off_the_loop.py::test_workflow_runs_the_engine_off_the_loop
FAILED tests/unit/test_hs13103_remaining_obligations.py::test_real_migrated_ask_cancellation_after_stage_is_completed_and_not_duplicated
FAILED tests/unit/test_hs13103_remaining_obligations.py::test_ask_v1_contract_shape_hash_guards_service_payload_drift
FAILED tests/unit/test_hs13103_remaining_obligations.py::test_ask_v1_golden_field_names_and_schema_version_are_exact
FAILED tests/unit/test_kernel_effect_fence.py::test_kernel_broker_modules_stay_within_line_budget
FAILED tests/unit/test_kernel_effect_fence.py::test_kernel_broker_has_zero_driver_specific_conditionals
FAILED tests/unit/test_interior_canon_guard.py::test_no_left_border_rails_in_web_css
FAILED tests/unit/test_inference_setup_capability_truth.py::test_first_and_repeated_reads_do_not_mutate_database_or_config
FAILED tests/unit/test_product_copy.py::test_primary_copy_has_no_prohibited_operational_drift
FAILED tests/unit/test_placement_provenance.py::test_ask_global_placement - h...
FAILED tests/unit/test_product_language.py::test_primary_ui_has_no_new_unqualified_ambiguous_terms
FAILED tests/unit/test_placement_provenance.py::test_sequence_run_placement
FAILED tests/unit/test_residual_service_admission.py::test_a_cancelled_cadence_parent_never_publishes_its_late_draft
FAILED tests/unit/test_placement_provenance.py::test_workflow_run_placement
FAILED tests/unit/test_placement_provenance.py::test_cadence_get_loop_llm_placement
FAILED tests/unit/test_run_artifacts.py::test_agent_run_persists_and_responds_with_artifact_id
FAILED tests/unit/test_run_frames.py::test_agent_run_frames_running_then_ready
FAILED tests/unit/test_run_frames.py::test_agent_run_error_frame_on_502 - ass...
FAILED tests/unit/test_run_frames.py::test_chain_and_workflow_bracket_the_whole_run
FAILED tests/unit/test_sequence_workflow_runner_migration.py::test_sequence_and_workflow_create_one_authenticated_native_parent
FAILED tests/unit/test_sequence_workflow_runner_migration.py::test_three_step_sequence_has_three_admitted_children_and_terminal_receipts
FAILED tests/unit/test_recipe_runner_migration.py::test_recipe_run_and_root_chat_use_exact_saved_revision_and_stages
FAILED tests/unit/test_sequence_workflow_runner_migration.py::test_workflow_child_cardinality_covers_model_retry_fallback_skip_and_pure_nodes
FAILED tests/unit/test_sequence_workflow_runner_migration.py::test_child_causation_definition_node_and_deployment_revisions_are_immutable
FAILED tests/unit/test_sequence_workflow_runner_migration.py::test_each_child_resolves_phase130_placement_then_freezes_deployment_revision
FAILED tests/unit/test_sequence_workflow_runner_migration.py::test_parent_cancel_fences_admission_and_late_output_while_child_receipts_survive
FAILED tests/unit/test_sequence_workflow_runner_migration.py::test_model_derived_sequence_workflow_writes_are_receipt_gated
FAILED tests/unit/test_web_null_read_guard.py::test_product_components_do_not_mutate_global_dom_or_inject_html
FAILED tests/unit/test_web_routes_primitives.py::test_run_agent_invokes_engine
FAILED tests/unit/test_sequence_workflow_runner_migration.py::test_parent_child_replay_is_idempotent_across_restart
FAILED tests/unit/test_web_routes_primitives.py::test_run_workflow_prompt - a...
FAILED tests/unit/test_web_routes_primitives.py::test_run_agent_includes_input_source
FAILED tests/unit/test_web_routes_primitives.py::test_run_chain_threads_steps
FAILED tests/unit/test_web_routes_primitives.py::test_run_workflow_linear_graph_runs_in_order
FAILED tests/unit/test_web_routes_primitives.py::test_run_agent_input_source_accepts_ipad_card_alias
FAILED tests/unit/test_sequence_workflow_runner_migration.py::test_sequence_child_refuses_recipe_revision_changed_after_planning
FAILED tests/unit/test_web_routes_primitives.py::test_run_workflow_engine_error_is_502
FAILED tests/unit/test_web_routes_primitives.py::test_run_agent_engine_error_is_502
FAILED tests/unit/test_web_routes_primitives.py::test_run_workflow_web_authored_graph_runs
FAILED tests/unit/test_web_routes_primitives.py::test_run_chain_engine_error_is_502
49 failed, 6532 passed, 53 skipped in 462.36s (0:07:42)
```

### Orchestrator triage note (2026-08-25)

The captured run is the full CI-style suite at the story's final tree
(`1658974e`), with `set -o pipefail` so the exit code (1) truthfully
reflects pytest while `tail -120` preserves the FAILED list and
summary. Verdict, triaged against
`assets/story-08-inherited-failure-baseline.txt` (the main baseline at
`89d232f3`): **6532 passed / 49 failed / 53 skipped — ZERO
branch-new**; every failure is in the inherited baseline. Across the
Story 09 arc the suite grew 6511 → 6533 at its peak, and all six
construction sweeps triaged to zero branch-new (three of them without
even a flake candidate). Verification legs per the paired-model law:
Terra built all nine slices; opus audited both gates — Part A ("PART A
SOUND — gate may close") and Part B, clause-by-clause against the
ruled fallback table ("PART B SOUND — story may close") — with five
safe ledger notes total and zero findings. The design was already
ruled canon (proposals/inference-catalog-and-context-policy.md +
architecture-contract §Tool-bearing fallback); all ten open
implementation choices were decided by the orchestrator as tie-breaker
(plan §7); no counsel rounds were spent.
