> Archive of exact DW output. The generated header below says done by default; the actual story remains in-progress. This archive is not closing certification. See lane-01-astra.md.

# Evidence - PHILO-13-01

- **Story:** PHILO-13-01 - B0 — Walk what was not walked
- **Status:** done
- **Date:** 2026-10-01

## Proof

### Captured run — 2026-10-02T02:20:36Z

- **Command:** `uv run pytest -q --collect-only tests/unit/test_philo_graph_atlas.py tests/unit/test_philo13_astra_atlas.py tests/unit/test_philo13_graph_walk.py tests/unit/test_philo13_fixture_rig.py tests/unit/test_philo13_repository_fixture.py tests/unit/test_graph_walk_select_option.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
tests/unit/test_philo_graph_atlas.py::test_every_atlas_file_is_read
tests/unit/test_philo_graph_atlas.py::test_schema_is_a_valid_2020_12_schema
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase10.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase10.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase11-slack.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase11-slack.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase11.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase11.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase12-source.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase12-source.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase13-astra.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase13-astra.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase3.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase3.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase7.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase7.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase8.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase8.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase9-steward.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase9-steward.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase9.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase9.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas.json]
tests/unit/test_philo_graph_atlas.py::test_ids_are_unique
tests/unit/test_philo_graph_atlas.py::test_every_case_state_id_resolves
tests/unit/test_philo_graph_atlas.py::test_every_case_reference_inside_the_atlas_resolves
tests/unit/test_philo_graph_atlas.py::test_every_clock_a_case_uses_is_declared
tests/unit/test_philo_graph_atlas.py::test_every_applicable_case_carries_one_trigger
tests/unit/test_philo_graph_atlas.py::test_no_timer_edge_is_triggered_by_a_substitute_button
tests/unit/test_philo_graph_atlas.py::test_every_api_setup_step_exists_in_the_generated_openapi
tests/unit/test_philo_graph_atlas.py::test_every_fixture_step_exists_and_hashes_as_claimed
tests/unit/test_philo_graph_atlas.py::test_every_phase1_reference_resolves_to_a_record
tests/unit/test_philo_graph_atlas.py::test_every_selected_job_has_an_applicable_case_except_j8
tests/unit/test_philo_graph_atlas.py::test_every_brief_family_is_present
tests/unit/test_philo_graph_atlas.py::test_quiet_is_never_an_attention_state
tests/unit/test_philo_graph_atlas.py::test_face_cases_carry_both_ruled_viewports
tests/unit/test_philo_graph_atlas.py::test_unexercised_states_name_a_mechanism_and_a_cost
tests/unit/test_philo_graph_atlas.py::test_source_commit_is_the_revision_the_atlas_was_derived_from
tests/unit/test_philo_graph_atlas.py::test_every_applicable_predicate_is_a_kind_the_rig_implements
tests/unit/test_philo_graph_atlas.py::test_every_predicate_observes_a_selector_or_a_route
tests/unit/test_philo_graph_atlas.py::test_protocol_predicates_ask_for_a_new_row
tests/unit/test_philo_graph_atlas.py::test_every_case_keeps_its_human_sentence
tests/unit/test_philo_graph_atlas.py::test_operation_siblings_use_headless_reads_and_canonical_steps
tests/unit/test_philo_graph_atlas.py::test_named_pair_observations_bind_their_read_arguments
tests/unit/test_philo_graph_atlas.py::test_all_handled_operation_maps_items_by_decision_source
tests/unit/test_philo_graph_atlas.py::test_breakage_cases_use_evening_wrapper_and_shelf_old_item
tests/unit/test_philo_graph_atlas.py::test_every_ui_action_is_one_the_rig_implements
tests/unit/test_philo_graph_atlas.py::test_every_boundary_names_its_substitution
tests/unit/test_philo_graph_atlas.py::test_summary_cases_use_the_retained_architect_import_fixture
tests/unit/test_philo_graph_atlas.py::test_summary_run_cases_have_one_run_trigger
tests/unit/test_philo_graph_atlas.py::test_summary_running_reads_the_claimed_job_wire_status
tests/unit/test_philo_graph_atlas.py::test_summary_queued_reads_the_run_admission_response
tests/unit/test_philo_graph_atlas.py::test_protocol_status_can_require_top_level_integer_body_fields
tests/unit/test_philo_graph_atlas.py::test_summary_preconditions_do_not_require_future_or_consumed_run_state
tests/unit/test_philo_graph_atlas.py::test_summary_state_reads_do_not_require_a_new_row_after_setup_run
tests/unit/test_philo_graph_atlas.py::test_summary_manual_retry_requires_failed_producer_and_current_route
tests/unit/test_philo_graph_atlas.py::test_summary_planned_host_cases_check_real_text_and_control_ownership
tests/unit/test_philo_graph_atlas.py::test_summary_failure_cases_retain_reply_at_the_provider_boundary
tests/unit/test_philo_graph_atlas.py::test_summary_imports_wait_for_real_completion_and_retain_title
tests/unit/test_philo_graph_atlas.py::test_summary_arrival_observations_name_the_rendered_states
tests/unit/test_philo_graph_atlas.py::test_summary_models_window_closes_before_arrival_steps
tests/unit/test_philo_graph_atlas.py::test_summary_restart_proof_retains_summary_receipt_and_identity
tests/unit/test_philo_graph_atlas.py::test_summary_microphone_cases_keep_the_lawful_blocked_boundary
tests/unit/test_philo_graph_atlas.py::test_summary_cases_do_not_claim_the_old_pangram
tests/unit/test_philo_graph_atlas.py::test_summary_stop_cases_require_a_real_active_meeting
tests/unit/test_philo_graph_atlas.py::test_the_two_schemas_agree_on_the_case_contract
tests/unit/test_philo_graph_atlas.py::test_every_case_validates_against_the_graph_case_schema
tests/unit/test_philo_graph_atlas.py::test_the_graph_predicate_enum_does_not_outrun_the_rig
tests/unit/test_philo_graph_atlas.py::test_a_case_without_a_predicate_is_unreachable_with_a_reason
tests/unit/test_philo_graph_atlas.py::test_every_council_reading_names_its_sources
tests/unit/test_philo_graph_atlas.py::test_no_precondition_check_compares_two_snapshots
tests/unit/test_philo_graph_atlas.py::test_every_precondition_check_observes_a_selector_or_a_route
tests/unit/test_philo_graph_atlas.py::test_no_check_asserts_the_result_the_trigger_must_produce
tests/unit/test_philo_graph_atlas.py::test_every_protocol_field_path_with_a_placeholder_is_a_json_pointer
tests/unit/test_philo_graph_atlas.py::test_no_step_acts_on_a_root_placeholder
tests/unit/test_philo_graph_atlas.py::test_navigation_steps_carry_no_selector
tests/unit/test_philo_graph_atlas.py::test_every_click_and_fill_names_a_control
tests/unit/test_philo_graph_atlas.py::test_every_desk_face_case_crosses_the_gate_first
tests/unit/test_philo_graph_atlas.py::test_no_gate_case_crosses_the_gate_in_setup
tests/unit/test_philo_graph_atlas.py::test_gate_cases_check_the_gate_not_the_desk
tests/unit/test_philo_graph_atlas.py::test_every_captured_id_names_the_field_it_reads
tests/unit/test_philo_graph_atlas.py::test_same_day_generate_again_binds_returned_displayed_and_retained
tests/unit/test_philo_graph_atlas.py::test_no_populated_brief_case_reads_the_headline
tests/unit/test_philo_graph_atlas.py::test_the_brief_recipe_fence_refuses_its_mutations
tests/unit/test_philo_graph_atlas.py::test_the_populated_brief_predicate_needs_the_minted_row
tests/unit/test_philo_graph_atlas.py::test_j11_kept_verifies_the_saved_words_in_the_store
tests/unit/test_philo_graph_atlas.py::test_same_day_same_id_fails_a_different_id_by_machine
tests/unit/test_philo_graph_atlas.py::test_j10_retention_is_proven_after_another_reload
tests/unit/test_philo_graph_atlas.py::test_summary_failure_settings_reach_the_real_drainer_after_restart
tests/unit/test_philo_graph_atlas.py::test_summary_no_engine_absence_is_read_inside_the_existing_meetings_scope
tests/unit/test_philo_graph_atlas.py::test_summary_reload_reads_the_same_already_persisted_summary
tests/unit/test_philo_graph_atlas.py::test_summary_terminal_cases_read_durable_meeting_not_active_queue[case.j6.run_summary.intel_ready-/intel_job/status]
tests/unit/test_philo_graph_atlas.py::test_summary_terminal_cases_read_durable_meeting_not_active_queue[case.j6.run_summary.host_named-/run_receipt/attempts/0/host]
tests/unit/test_philo_graph_atlas.py::test_no_assignment_op_reads_refusal_code_separately_from_error
tests/unit/test_philo_graph_atlas.py::test_thought_op_save_starts_from_different_working_text
tests/unit/test_philo_graph_atlas.py::test_philo603_cases_use_the_real_summary_producer_and_surface_slots
tests/unit/test_philo_graph_atlas.py::test_philo603_placement_fence_rejects_fixed_card_and_overlap
tests/unit/test_philo_graph_atlas.py::test_philo603_placement_fence_accepts_flow_card_with_nine_point_clearance
tests/unit/test_philo_graph_atlas.py::test_philo603_placement_fence_checks_every_matching_clear_target
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_case_state_id_resolves]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_case_reference_inside_the_atlas_resolves]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_clock_a_case_uses_is_declared]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_applicable_case_carries_one_trigger]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_face_cases_carry_both_ruled_viewports]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_applicable_predicate_is_a_kind_the_rig_implements]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_predicate_observes_a_selector_or_a_route]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_source_reference_lands_on_its_symbol]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_case_keeps_its_human_sentence]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_ui_action_is_one_the_rig_implements]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_boundary_names_its_substitution]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_no_precondition_check_compares_two_snapshots]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_precondition_check_observes_a_selector_or_a_route]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_no_check_asserts_the_result_the_trigger_must_produce]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_no_step_acts_on_a_root_placeholder]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_navigation_steps_carry_no_selector]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_desk_face_case_crosses_the_gate_first]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_captured_id_names_the_field_it_reads]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_ids_are_unique]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_validates_against_schema_and_openapi
tests/unit/test_philo13_astra_atlas.py::test_phase13_case_and_sibling_manifest_is_local
tests/unit/test_philo13_astra_atlas.py::test_phase13_shared_semantic_guards_show_red_then_green
tests/unit/test_philo13_astra_atlas.py::test_phase13_shared_operation_count_excludes_only_phase13_files
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_declares_touch_when_nested_trigger_then_uses_it
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_records_pointer_adapter_at_desktop_width
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_records_touch_adapter_and_uses_native_tap
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_guarded_touch_blocks_before_synthetic_delivery
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_real_playwright_tap_emits_touch_pointer_events
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_real_playwright_click_emits_mouse_pointer_events
tests/unit/test_philo13_fixture_rig.py::test_repository_fixture_binds_scalars_and_restarts_the_owned_hub
tests/unit/test_philo13_fixture_rig.py::test_ingest_coder_fixture_uses_real_cli_and_records_question
tests/unit/test_philo13_fixture_rig.py::test_set_input_files_dispatches_native_path_and_records_hash
tests/unit/test_philo13_fixture_rig.py::test_file_chooser_dispatch_uses_native_click_at_both_widths[1440-ui-pointer]
tests/unit/test_philo13_fixture_rig.py::test_file_chooser_dispatch_uses_native_click_at_both_widths[393-ui-touch]
tests/unit/test_philo13_fixture_rig.py::test_real_browser_file_chooser_accepts_detached_input_at_both_widths[1440]
tests/unit/test_philo13_fixture_rig.py::test_real_browser_file_chooser_accepts_detached_input_at_both_widths[393]
tests/unit/test_philo13_fixture_rig.py::test_set_input_files_refuses_a_path_outside_owned_roots
tests/unit/test_philo13_fixture_rig.py::test_hub_environment_and_teardown_never_use_inherited_tmux_socket
tests/unit/test_philo13_fixture_rig.py::test_repository_router_passes_fixture_to_real_builder
tests/unit/test_philo13_fixture_rig.py::test_real_hub_reads_repository_and_coder_producers
tests/unit/test_philo13_repository_fixture.py::test_repository_fixture_uses_real_registry_collector_dossier_and_dw
tests/unit/test_philo13_repository_fixture.py::test_repository_fixture_refuses_reuse_and_symlinked_home
tests/unit/test_graph_walk_select_option.py::test_select_option_sends_exact_selector_and_value_to_native_locator
tests/unit/test_graph_walk_select_option.py::test_press_with_a_selector_delivers_the_key_to_that_control
tests/unit/test_graph_walk_select_option.py::test_select_option_refuses_an_empty_target_or_value_before_page_access[-destination-slack-7]
tests/unit/test_graph_walk_select_option.py::test_select_option_refuses_an_empty_target_or_value_before_page_access[select[data-testid='slack-destination']-]
tests/unit/test_graph_walk_select_option.py::test_select_option_refuses_an_empty_target_or_value_before_page_access[   -destination-slack-7]
tests/unit/test_graph_walk_select_option.py::test_select_option_refuses_an_empty_target_or_value_before_page_access[select[data-testid='slack-destination']-   ]
tests/unit/test_graph_walk_select_option.py::test_atlas_schema_accepts_select_option_and_requires_nonempty_fields

149 tests collected in 0.31s
```

### Captured run — 2026-10-02T02:20:37Z

- **Command:** `uv run pytest -q tests/unit/test_philo_graph_atlas.py tests/unit/test_philo13_astra_atlas.py tests/unit/test_philo13_graph_walk.py tests/unit/test_philo13_fixture_rig.py tests/unit/test_philo13_repository_fixture.py tests/unit/test_graph_walk_select_option.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
........................................................................ [ 48%]
..................................F..................................... [ 96%]
.....                                                                    [100%]
=================================== FAILURES ===================================
_ test_phase13_atlas_keeps_the_shared_graph_fences[test_every_predicate_observes_a_selector_or_a_route] _

fence = <function test_every_predicate_observes_a_selector_or_a_route at 0x10b6833d0>

    @pytest.mark.parametrize("fence", GENERAL, ids=lambda fence: fence.__name__)
    def test_phase13_atlas_keeps_the_shared_graph_fences(fence) -> None:
>       fence(_atlas())

tests/unit/test_philo13_astra_atlas.py:68: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

atlas = {'atlas_version': 'phase13-astra-b0', 'cases': [{'applicability': 'applicable', 'completion_bound_s': 30, 'edge_ids': ... 'source': 'datetime.datetime.now() inside the hub process', 'status': 'available', ...}], 'council_readings': [], ...}

    def test_every_predicate_observes_a_selector_or_a_route(atlas: dict) -> None:
        """observe_at is a CSS selector, or `protocol: METHOD /path` (the rig's
        PROTOCOL_PREFIX). Anything else is prose the rig cannot aim at."""
        prefix = _rig().PROTOCOL_PREFIX
        problems: list[str] = []
        for case in atlas["cases"]:
            if "predicate" not in case["expected"]:
                continue
            where = case["expected"]["observe_at"]
            if isinstance(where, dict) and where.get("kind") == "op":
                continue
            if where.startswith(prefix):
                method, _, path = where[len(prefix) :].strip().partition(" ")
                if not path.startswith("/"):
                    problems.append(f"{case['id']}: {where!r} names no route path")
                if method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                    problems.append(f"{case['id']}: {where!r} names no HTTP method")
                continue
            if not _is_css_selector(where):
                problems.append(f"{case['id']}: observe_at {where!r} is not a selector")
>       assert not problems, problems
E       AssertionError: ['case.p13.calendar.snapshot_window: observe_at \'[role="region"][aria-label="Calendar snapshot"]\' is not a selector'...13.coder.pullout: observe_at \'.desk-pullout.is-card:has-text("Should I run the full suite now?")\' is not a selector']
E       assert not ['case.p13.calendar.snapshot_window: observe_at \'[role="region"][aria-label="Calendar snapshot"]\' is not a selector'...13.coder.pullout: observe_at \'.desk-pullout.is-card:has-text("Should I run the full suite now?")\' is not a selector']

tests/unit/test_philo_graph_atlas.py:449: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_predicate_observes_a_selector_or_a_route]
1 failed, 148 passed in 11.70s
```

### Captured run — 2026-10-02T02:21:41Z

- **Command:** `uv run pytest -q tests/unit/test_philo_graph_atlas.py tests/unit/test_philo13_astra_atlas.py tests/unit/test_philo13_graph_walk.py tests/unit/test_philo13_fixture_rig.py tests/unit/test_philo13_repository_fixture.py tests/unit/test_graph_walk_select_option.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
........................................................................ [ 48%]
........................................................................ [ 96%]
.....                                                                    [100%]
149 passed in 11.32s
```

### Captured run — 2026-10-02T02:22:07Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.chain.pullout --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-01/chain-1440-r1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:54928 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-rsfykh6c/.local/share/holdspeak/holdspeak.db engine=none
JOB: j3
VERDICT: blocked terminal=None
EVIDENCE: ['.tmp/graph-walk/philo-13-01/chain-1440-r1/20261002T022207Z-case.p13.chain.pullout-astra-1440/blocked.png']
NOTE: BLOCKED: precondition not met: {'kind': 'protocol_field', 'path': 'arrival_required', 'value': False} at 'protocol: GET /api/setup/status' — arrival_required = True, wanted False
```

### Captured run — 2026-10-02T02:22:46Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.chain.pullout --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-01/chain-1440-r2`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:55270 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-8g13fdgd/.local/share/holdspeak/holdspeak.db engine=none
JOB: j3
VERDICT: blocked terminal=None
EVIDENCE: ['.tmp/graph-walk/philo-13-01/chain-1440-r2/20261002T022246Z-case.p13.chain.pullout-astra-1440/blocked.png']
NOTE: BLOCKED: ui step wait_for on '.desk-pullout[aria-label="Atlas B0 Sequence"]' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
Call log:
  - waiting for locator(".desk-pullout[aria-label=\"Atlas B0 Sequence\"]").first to be hidden
    25 × locator resolved to visible <div tabindex="
```

### Captured run — 2026-10-02T02:23:49Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.chain.pullout --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-01/chain-1440-r3`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:55727 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-p9vrm_y7/.local/share/holdspeak/holdspeak.db engine=none
JOB: j3
VERDICT: blocked terminal=None
EVIDENCE: ['.tmp/graph-walk/philo-13-01/chain-1440-r3/20261002T022349Z-case.p13.chain.pullout-astra-1440/blocked.png']
NOTE: BLOCKED: ui step wait_for on '.desk-pullout[aria-label="Atlas B0 Sequence"]' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
Call log:
  - waiting for locator(".desk-pullout[aria-label=\"Atlas B0 Sequence\"]").first to be hidden
    13 × locator resolved to visible <div tabindex="
```

### Captured run — 2026-10-02T02:24:35Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.chain.pullout --brain astra --viewport 393 --engine none --no-build --out .tmp/graph-walk/philo-13-01/chain-393-r1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:55967 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-rnzubelk/.local/share/holdspeak/holdspeak.db engine=none
JOB: j3
VERDICT: blocked terminal=None
EVIDENCE: ['.tmp/graph-walk/philo-13-01/chain-393-r1/20261002T022435Z-case.p13.chain.pullout-astra-393/blocked.png']
NOTE: BLOCKED: ui step wait_for on '.desk-pullout[aria-label="Atlas B0 Sequence"]' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
Call log:
  - waiting for locator(".desk-pullout[aria-label=\"Atlas B0 Sequence\"]").first to be hidden
    20 × locator resolved to visible <div tabindex="
```

### Captured run — 2026-10-02T02:26:02Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.chain.pullout --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-01/chain-1440-r4`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:56749 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-ym9i4v8i/.local/share/holdspeak/holdspeak.db engine=none
JOB: j3
VERDICT: blocked terminal=None
EVIDENCE: ['.tmp/graph-walk/philo-13-01/chain-1440-r4/20261002T022602Z-case.p13.chain.pullout-astra-1440/blocked.png']
NOTE: BLOCKED: ui step wait_for on '.desk-pullout[aria-label="Atlas B0 Sequence"]' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
Call log:
  - waiting for locator(".desk-pullout[aria-label=\"Atlas B0 Sequence\"]").first to be hidden
    13 × locator resolved to visible <div tabindex="
```

### Captured run — 2026-10-02T02:26:50Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.chain.pullout --brain astra --viewport 393 --engine none --no-build --out .tmp/graph-walk/philo-13-01/chain-393-r2`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:57014 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-naezhb7s/.local/share/holdspeak/holdspeak.db engine=none
JOB: j3
VERDICT: blocked terminal=None
EVIDENCE: ['.tmp/graph-walk/philo-13-01/chain-393-r2/20261002T022651Z-case.p13.chain.pullout-astra-393/blocked.png']
NOTE: BLOCKED: ui step wait_for on '.desk-pullout[aria-label="Atlas B0 Sequence"]' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
Call log:
  - waiting for locator(".desk-pullout[aria-label=\"Atlas B0 Sequence\"]").first to be hidden
    20 × locator resolved to visible <div tabindex="
```

### Captured run — 2026-10-02T02:30:23Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.roadmap.window --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-01/roadmap-1440-r1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:58137 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-30o9w206/.local/share/holdspeak/holdspeak.db engine=none
JOB: j1
VERDICT: blocked terminal=None
EVIDENCE: ['.tmp/graph-walk/philo-13-01/roadmap-1440-r1/20261002T023023Z-case.p13.roadmap.window-astra-1440/blocked.png']
NOTE: BLOCKED: ui step wait_for on '.desk-roadmap-phase-row' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
Call log:
  - waiting for locator(".desk-roadmap-phase-row").first to be visible
```

### Captured run — 2026-10-02T02:31:04Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.roadmap.window --brain astra --viewport 393 --engine none --no-build --out .tmp/graph-walk/philo-13-01/roadmap-393-r1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:58229 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-is49kvqt/.local/share/holdspeak/holdspeak.db engine=none
JOB: j1
VERDICT: blocked terminal=None
EVIDENCE: ['.tmp/graph-walk/philo-13-01/roadmap-393-r1/20261002T023104Z-case.p13.roadmap.window-astra-393/blocked.png']
NOTE: BLOCKED: ui step wait_for on '.desk-roadmap-phase-row' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
Call log:
  - waiting for locator(".desk-roadmap-phase-row").first to be visible
```

### Captured run — 2026-10-02T02:31:38Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.repository.window --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-01/repository-1440-r1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:58324 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-3m2zhr2y/.local/share/holdspeak/holdspeak.db engine=none
JOB: j1
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-01/repository-1440-r1/20261002T023138Z-case.p13.repository.window-astra-1440/before.png', '.tmp/graph-walk/philo-13-01/repository-1440-r1/20261002T023138Z-case.p13.repository.window-astra-1440/after.png']
NOTE: predicate: 'atlas_repository.py' in observe_at text
```

### Captured run — 2026-10-02T02:32:57Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.repository.window --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-01/repository-1440-r2`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:58504 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-5odksdfk/.local/share/holdspeak/holdspeak.db engine=none
JOB: j1
VERDICT: fail terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-01/repository-1440-r2/20261002T023257Z-case.p13.repository.window-astra-1440/before.png', '.tmp/graph-walk/philo-13-01/repository-1440-r2/20261002T023257Z-case.p13.repository.window-astra-1440/after.png']
NOTE: predicate: the text scope is outside the viewport: {'width': 1440, 'height': 900}
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['attrs', 'document_text_len', 'document_text_sha256', 'focus', 'focus_label', 'rect', 'target_present', 'text', 'values', 'visible', 'windows']).
```

### Captured run — 2026-10-02T02:34:06Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.repository.window --brain astra --viewport 393 --engine none --no-build --out .tmp/graph-walk/philo-13-01/repository-393-r1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:58660 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-x7ual_4i/.local/share/holdspeak/holdspeak.db engine=none
JOB: j1
VERDICT: fail terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-01/repository-393-r1/20261002T023406Z-case.p13.repository.window-astra-393/before.png', '.tmp/graph-walk/philo-13-01/repository-393-r1/20261002T023406Z-case.p13.repository.window-astra-393/after.png']
NOTE: predicate: a covering element owns hit points: [{'x': 391, 'y': 264, 'owned': False, 'owner': 'div#desk-next > div.desk-listmode > section.desk-list-face'}]
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['attrs', 'document_text_len', 'document_text_sha256', 'focus', 'focus_label', 'rect', 'target_present', 'text', 'values', 'visible', 'windows']).
```

### Captured run — 2026-10-02T02:35:17Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.repository.window --brain astra --viewport 393 --engine none --no-build --out .tmp/graph-walk/philo-13-01/repository-393-r2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:58827 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-1udj2osy/.local/share/holdspeak/holdspeak.db engine=none
JOB: j1
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-01/repository-393-r2/20261002T023517Z-case.p13.repository.window-astra-393/before.png', '.tmp/graph-walk/philo-13-01/repository-393-r2/20261002T023517Z-case.p13.repository.window-astra-393/after.png']
NOTE: predicate: 'atlas_repository.py' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 446, 'w': 363, 'h': 164}
```

### Captured run — 2026-10-02T02:35:52Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.repository.window --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-01/repository-1440-r3`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:58923 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-x9g8m1ph/.local/share/holdspeak/holdspeak.db engine=none
JOB: j1
VERDICT: fail terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-01/repository-1440-r3/20261002T023553Z-case.p13.repository.window-astra-1440/before.png', '.tmp/graph-walk/philo-13-01/repository-1440-r3/20261002T023553Z-case.p13.repository.window-astra-1440/after.png']
NOTE: predicate: the text scope is outside the viewport: {'width': 1440, 'height': 900}
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['attrs', 'document_text_len', 'document_text_sha256', 'focus', 'focus_label', 'rect', 'target_present', 'text', 'values', 'visible', 'windows']).
```

### Captured run — 2026-10-02T02:37:09Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.delivery.dossier_window --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-01/dossier-1440-r1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:59062 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-kh63oyke/.local/share/holdspeak/holdspeak.db engine=none
JOB: j4
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-01/dossier-1440-r1/20261002T023709Z-case.p13.delivery.dossier_window-astra-1440/before.png', '.tmp/graph-walk/philo-13-01/dossier-1440-r1/20261002T023709Z-case.p13.delivery.dossier_window-astra-1440/after.png']
NOTE: predicate: 'ATLAS-1-01' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 426, 'y': 54, 'w': 420, 'h': 794}
```

### Captured run — 2026-10-02T02:37:43Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.delivery.dossier_window --brain astra --viewport 393 --engine none --no-build --out .tmp/graph-walk/philo-13-01/dossier-393-r1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:59143 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-t3dc8oql/.local/share/holdspeak/holdspeak.db engine=none
JOB: j4
VERDICT: fail terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-01/dossier-393-r1/20261002T023743Z-case.p13.delivery.dossier_window-astra-393/before.png', '.tmp/graph-walk/philo-13-01/dossier-393-r1/20261002T023743Z-case.p13.delivery.dossier_window-astra-393/after.png']
NOTE: predicate: a covering element owns hit points: [{'x': 2, 'y': 365, 'owned': False, 'owner': 'div#delivery-board > div.desk-pullout-body.desk-surface-body'}, {'x': 2, 'y': 520, 'owned': False, 'owner': 'div#delivery-board > div.desk-pullout-body.desk-surface-body'}, {'x': 2, 'y': 675, 'owned': False, 'owner': 'div#delivery-board > footer.surface-footer'}]
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['attrs', 'document_text_len', 'document_text_sha256', 'focus', 'focus_label', 'rect', 'target_present', 'text', 'visible', 'windows']).
```

### Captured run — 2026-10-02T02:39:15Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.coder.pullout --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-01/coder-1440-r1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:59251 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-tkn1p7p2/.local/share/holdspeak/holdspeak.db engine=none
JOB: j3
VERDICT: blocked terminal=None
EVIDENCE: ['.tmp/graph-walk/philo-13-01/coder-1440-r1/20261002T023915Z-case.p13.coder.pullout-astra-1440/blocked.png']
NOTE: BLOCKED: ui step wait_for on '.desk-pullout.is-card:has-text("Should I run the full suite now?")' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
Call log:
  - waiting for locator(".desk-pullout.is-card:has-text(\"Should I run the full suite now?\")").first to be hidden
    13 × locator resolved to vi
```

### Captured run — 2026-10-02T02:40:04Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.coder.pullout --brain astra --viewport 393 --engine none --no-build --out .tmp/graph-walk/philo-13-01/coder-393-r1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:59376 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-yygouz5_/.local/share/holdspeak/holdspeak.db engine=none
JOB: j3
VERDICT: blocked terminal=None
EVIDENCE: ['.tmp/graph-walk/philo-13-01/coder-393-r1/20261002T024004Z-case.p13.coder.pullout-astra-393/blocked.png']
NOTE: BLOCKED: ui step wait_for on '.desk-pullout.is-card:has-text("Should I run the full suite now?")' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
Call log:
  - waiting for locator(".desk-pullout.is-card:has-text(\"Should I run the full suite now?\")").first to be hidden
    20 × locator resolved to vi
```

### Captured run — 2026-10-02T02:40:40Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.calendar.snapshot_window --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-01/calendar-1440-r1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:59487 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-fatilz1l/.local/share/holdspeak/holdspeak.db engine=none
JOB: j1
VERDICT: blocked terminal=None
EVIDENCE: ['.tmp/graph-walk/philo-13-01/calendar-1440-r1/20261002T024040Z-case.p13.calendar.snapshot_window-astra-1440/blocked.png']
NOTE: BLOCKED: ui step click on '.prefs-hub [role="button"][aria-label="Meetings"]' failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.
Call log:
  - waiting for locator(".prefs-hub [role=\"button\"][aria-label=\"Meetings\"]").first
```

### Captured run — 2026-10-02T02:42:10Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.calendar.snapshot_window --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-01/calendar-1440-r2`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:59614 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-j_s5hz0m/.local/share/holdspeak/holdspeak.db engine=none
JOB: j1
VERDICT: blocked terminal=None
EVIDENCE: ['.tmp/graph-walk/philo-13-01/calendar-1440-r2/20261002T024211Z-case.p13.calendar.snapshot_window-astra-1440/blocked.png']
NOTE: BLOCKED: ui step wait_for on '[aria-label="Week of"]' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
Call log:
  - waiting for locator("[aria-label=\"Week of\"]").first to be visible
```

### Captured run — 2026-10-02T02:42:48Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.calendar.snapshot_window --brain astra --viewport 393 --engine none --no-build --out .tmp/graph-walk/philo-13-01/calendar-393-r1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:59697 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-4s_c4nyj/.local/share/holdspeak/holdspeak.db engine=none
JOB: j1
VERDICT: blocked terminal=None
EVIDENCE: ['.tmp/graph-walk/philo-13-01/calendar-393-r1/20261002T024248Z-case.p13.calendar.snapshot_window-astra-393/blocked.png']
NOTE: BLOCKED: ui step wait_for on '[aria-label="Week of"]' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
Call log:
  - waiting for locator("[aria-label=\"Week of\"]").first to be visible
```

### Captured run — 2026-10-02T02:43:29Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.delivery.terminal_window --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-01/terminal-1440-r1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:59771 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-df3mrjm5/.local/share/holdspeak/holdspeak.db engine=none
JOB: j4
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-01/terminal-1440-r1/20261002T024329Z-case.p13.delivery.terminal_window-astra-1440/before.png', '.tmp/graph-walk/philo-13-01/terminal-1440-r1/20261002T024329Z-case.p13.delivery.terminal_window-astra-1440/after.png']
NOTE: predicate: 'Atlas terminal' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 234, 'y': 54, 'w': 620, 'h': 794}
```

### Captured run — 2026-10-02T02:44:12Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.delivery.terminal_window --brain astra --viewport 393 --engine none --no-build --out .tmp/graph-walk/philo-13-01/terminal-393-r1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:59889 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-2skbz6b3/.local/share/holdspeak/holdspeak.db engine=none
JOB: j4
VERDICT: fail terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-01/terminal-393-r1/20261002T024412Z-case.p13.delivery.terminal_window-astra-393/before.png', '.tmp/graph-walk/philo-13-01/terminal-393-r1/20261002T024412Z-case.p13.delivery.terminal_window-astra-393/after.png']
NOTE: predicate: a covering element owns hit points: [{'x': 2, 'y': 50, 'owned': False, 'owner': 'div#delivery-board > header.desk-pullout-head.desk-window-handle'}, {'x': 2, 'y': 363, 'owned': False, 'owner': 'div#delivery-board > div.desk-pullout-body.desk-surface-body'}, {'x': 2, 'y': 675, 'owned': False, 'owner': 'div#delivery-board > footer.surface-footer'}]
NOTE: a nonzero diff with the wrong result is a finding, not a pass (changed: ['attrs', 'document_text_len', 'document_text_sha256', 'focus', 'focus_label', 'rect', 'target_present', 'text', 'values', 'visible', 'windows']).
```

### Captured run — 2026-10-02T02:48:58Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.directory.zone --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-01/zone-1440-r1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:61011 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-xe42nuzg/.local/share/holdspeak/holdspeak.db engine=none
JOB: j3
VERDICT: blocked terminal=None
EVIDENCE: ['.tmp/graph-walk/philo-13-01/zone-1440-r1/20261002T024858Z-case.p13.directory.zone-astra-1440/blocked.png']
NOTE: BLOCKED: ui step focus on '[data-zone-id="dir_6f25bf942965"]' failed: TimeoutError: Locator.focus: Timeout 10000ms exceeded.
Call log:
  - waiting for locator("[data-zone-id=\"dir_6f25bf942965\"]").first
    - locator resolved to <button type="button" data-zone-id="dir_6f25bf942965" 
```

### Captured run — 2026-10-02T02:50:27Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.directory.zone --brain astra --viewport 393 --engine none --no-build --out .tmp/graph-walk/philo-13-01/zone-393-r1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:61667 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-0ipsp55o/.local/share/holdspeak/holdspeak.db engine=none
JOB: j3
VERDICT: blocked terminal=None
EVIDENCE: ['.tmp/graph-walk/philo-13-01/zone-393-r1/20261002T025027Z-case.p13.directory.zone-astra-393/blocked.png']
NOTE: BLOCKED: ui step click on '[data-zone-id="dir_f4403045b6ae"]' failed: TimeoutError: Locator.tap: Timeout 10000ms exceeded.
Call log:
  - waiting for locator("[data-zone-id=\"dir_f4403045b6ae\"]").first
    - locator resolved to <button type="button" data-zone-id="dir_f4403045b6ae" ar
```

### Captured run — 2026-10-02T02:51:01Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.info.window --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-01/info-1440-r1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:61917 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-5wwqp0k_/.local/share/holdspeak/holdspeak.db engine=none
JOB: j3
VERDICT: blocked terminal=None
EVIDENCE: ['.tmp/graph-walk/philo-13-01/info-1440-r1/20261002T025101Z-case.p13.info.window-astra-1440/blocked.png']
NOTE: BLOCKED: ui step wait_for on '.desk-info-window .desk-info-body' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
Call log:
  - waiting for locator(".desk-info-window .desk-info-body").first to be visible
```

### Captured run — 2026-10-02T02:51:56Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.info.window --brain astra --viewport 393 --engine none --no-build --out .tmp/graph-walk/philo-13-01/info-393-r1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
PASS: live
BRAIN: astra
SOURCE: b870df2d32ccf33615dab1690b8ef6b6d28c65f9 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:62369 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-3vjckqeo/.local/share/holdspeak/holdspeak.db engine=none
JOB: j3
VERDICT: blocked terminal=None
EVIDENCE: ['.tmp/graph-walk/philo-13-01/info-393-r1/20261002T025156Z-case.p13.info.window-astra-393/blocked.png']
NOTE: BLOCKED: ui step click: native touch has no right-button delivery; nothing was fired
```

### Captured run — 2026-10-02T02:52:40Z

- **Command:** `uv run pytest -q --collect-only tests/unit/test_philo_graph_atlas.py tests/unit/test_philo13_astra_atlas.py tests/unit/test_philo13_graph_walk.py tests/unit/test_philo13_fixture_rig.py tests/unit/test_philo13_repository_fixture.py tests/unit/test_graph_walk_select_option.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
tests/unit/test_philo_graph_atlas.py::test_every_atlas_file_is_read
tests/unit/test_philo_graph_atlas.py::test_schema_is_a_valid_2020_12_schema
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase10.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase10.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase11-slack.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase11-slack.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase11.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase11.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase12-source.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase12-source.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase13-astra.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase13-astra.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase3.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase3.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase7.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase7.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase8.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase8.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase9-steward.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase9-steward.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase9.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase9.json]
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas.json]
tests/unit/test_philo_graph_atlas.py::test_ids_are_unique
tests/unit/test_philo_graph_atlas.py::test_every_case_state_id_resolves
tests/unit/test_philo_graph_atlas.py::test_every_case_reference_inside_the_atlas_resolves
tests/unit/test_philo_graph_atlas.py::test_every_clock_a_case_uses_is_declared
tests/unit/test_philo_graph_atlas.py::test_every_applicable_case_carries_one_trigger
tests/unit/test_philo_graph_atlas.py::test_no_timer_edge_is_triggered_by_a_substitute_button
tests/unit/test_philo_graph_atlas.py::test_every_api_setup_step_exists_in_the_generated_openapi
tests/unit/test_philo_graph_atlas.py::test_every_fixture_step_exists_and_hashes_as_claimed
tests/unit/test_philo_graph_atlas.py::test_every_phase1_reference_resolves_to_a_record
tests/unit/test_philo_graph_atlas.py::test_every_selected_job_has_an_applicable_case_except_j8
tests/unit/test_philo_graph_atlas.py::test_every_brief_family_is_present
tests/unit/test_philo_graph_atlas.py::test_quiet_is_never_an_attention_state
tests/unit/test_philo_graph_atlas.py::test_face_cases_carry_both_ruled_viewports
tests/unit/test_philo_graph_atlas.py::test_unexercised_states_name_a_mechanism_and_a_cost
tests/unit/test_philo_graph_atlas.py::test_source_commit_is_the_revision_the_atlas_was_derived_from
tests/unit/test_philo_graph_atlas.py::test_every_applicable_predicate_is_a_kind_the_rig_implements
tests/unit/test_philo_graph_atlas.py::test_every_predicate_observes_a_selector_or_a_route
tests/unit/test_philo_graph_atlas.py::test_protocol_predicates_ask_for_a_new_row
tests/unit/test_philo_graph_atlas.py::test_every_case_keeps_its_human_sentence
tests/unit/test_philo_graph_atlas.py::test_operation_siblings_use_headless_reads_and_canonical_steps
tests/unit/test_philo_graph_atlas.py::test_named_pair_observations_bind_their_read_arguments
tests/unit/test_philo_graph_atlas.py::test_all_handled_operation_maps_items_by_decision_source
tests/unit/test_philo_graph_atlas.py::test_breakage_cases_use_evening_wrapper_and_shelf_old_item
tests/unit/test_philo_graph_atlas.py::test_every_ui_action_is_one_the_rig_implements
tests/unit/test_philo_graph_atlas.py::test_every_boundary_names_its_substitution
tests/unit/test_philo_graph_atlas.py::test_summary_cases_use_the_retained_architect_import_fixture
tests/unit/test_philo_graph_atlas.py::test_summary_run_cases_have_one_run_trigger
tests/unit/test_philo_graph_atlas.py::test_summary_running_reads_the_claimed_job_wire_status
tests/unit/test_philo_graph_atlas.py::test_summary_queued_reads_the_run_admission_response
tests/unit/test_philo_graph_atlas.py::test_protocol_status_can_require_top_level_integer_body_fields
tests/unit/test_philo_graph_atlas.py::test_summary_preconditions_do_not_require_future_or_consumed_run_state
tests/unit/test_philo_graph_atlas.py::test_summary_state_reads_do_not_require_a_new_row_after_setup_run
tests/unit/test_philo_graph_atlas.py::test_summary_manual_retry_requires_failed_producer_and_current_route
tests/unit/test_philo_graph_atlas.py::test_summary_planned_host_cases_check_real_text_and_control_ownership
tests/unit/test_philo_graph_atlas.py::test_summary_failure_cases_retain_reply_at_the_provider_boundary
tests/unit/test_philo_graph_atlas.py::test_summary_imports_wait_for_real_completion_and_retain_title
tests/unit/test_philo_graph_atlas.py::test_summary_arrival_observations_name_the_rendered_states
tests/unit/test_philo_graph_atlas.py::test_summary_models_window_closes_before_arrival_steps
tests/unit/test_philo_graph_atlas.py::test_summary_restart_proof_retains_summary_receipt_and_identity
tests/unit/test_philo_graph_atlas.py::test_summary_microphone_cases_keep_the_lawful_blocked_boundary
tests/unit/test_philo_graph_atlas.py::test_summary_cases_do_not_claim_the_old_pangram
tests/unit/test_philo_graph_atlas.py::test_summary_stop_cases_require_a_real_active_meeting
tests/unit/test_philo_graph_atlas.py::test_the_two_schemas_agree_on_the_case_contract
tests/unit/test_philo_graph_atlas.py::test_every_case_validates_against_the_graph_case_schema
tests/unit/test_philo_graph_atlas.py::test_the_graph_predicate_enum_does_not_outrun_the_rig
tests/unit/test_philo_graph_atlas.py::test_a_case_without_a_predicate_is_unreachable_with_a_reason
tests/unit/test_philo_graph_atlas.py::test_every_council_reading_names_its_sources
tests/unit/test_philo_graph_atlas.py::test_no_precondition_check_compares_two_snapshots
tests/unit/test_philo_graph_atlas.py::test_every_precondition_check_observes_a_selector_or_a_route
tests/unit/test_philo_graph_atlas.py::test_no_check_asserts_the_result_the_trigger_must_produce
tests/unit/test_philo_graph_atlas.py::test_every_protocol_field_path_with_a_placeholder_is_a_json_pointer
tests/unit/test_philo_graph_atlas.py::test_no_step_acts_on_a_root_placeholder
tests/unit/test_philo_graph_atlas.py::test_navigation_steps_carry_no_selector
tests/unit/test_philo_graph_atlas.py::test_every_click_and_fill_names_a_control
tests/unit/test_philo_graph_atlas.py::test_every_desk_face_case_crosses_the_gate_first
tests/unit/test_philo_graph_atlas.py::test_no_gate_case_crosses_the_gate_in_setup
tests/unit/test_philo_graph_atlas.py::test_gate_cases_check_the_gate_not_the_desk
tests/unit/test_philo_graph_atlas.py::test_every_captured_id_names_the_field_it_reads
tests/unit/test_philo_graph_atlas.py::test_same_day_generate_again_binds_returned_displayed_and_retained
tests/unit/test_philo_graph_atlas.py::test_no_populated_brief_case_reads_the_headline
tests/unit/test_philo_graph_atlas.py::test_the_brief_recipe_fence_refuses_its_mutations
tests/unit/test_philo_graph_atlas.py::test_the_populated_brief_predicate_needs_the_minted_row
tests/unit/test_philo_graph_atlas.py::test_j11_kept_verifies_the_saved_words_in_the_store
tests/unit/test_philo_graph_atlas.py::test_same_day_same_id_fails_a_different_id_by_machine
tests/unit/test_philo_graph_atlas.py::test_j10_retention_is_proven_after_another_reload
tests/unit/test_philo_graph_atlas.py::test_summary_failure_settings_reach_the_real_drainer_after_restart
tests/unit/test_philo_graph_atlas.py::test_summary_no_engine_absence_is_read_inside_the_existing_meetings_scope
tests/unit/test_philo_graph_atlas.py::test_summary_reload_reads_the_same_already_persisted_summary
tests/unit/test_philo_graph_atlas.py::test_summary_terminal_cases_read_durable_meeting_not_active_queue[case.j6.run_summary.intel_ready-/intel_job/status]
tests/unit/test_philo_graph_atlas.py::test_summary_terminal_cases_read_durable_meeting_not_active_queue[case.j6.run_summary.host_named-/run_receipt/attempts/0/host]
tests/unit/test_philo_graph_atlas.py::test_no_assignment_op_reads_refusal_code_separately_from_error
tests/unit/test_philo_graph_atlas.py::test_thought_op_save_starts_from_different_working_text
tests/unit/test_philo_graph_atlas.py::test_philo603_cases_use_the_real_summary_producer_and_surface_slots
tests/unit/test_philo_graph_atlas.py::test_philo603_placement_fence_rejects_fixed_card_and_overlap
tests/unit/test_philo_graph_atlas.py::test_philo603_placement_fence_accepts_flow_card_with_nine_point_clearance
tests/unit/test_philo_graph_atlas.py::test_philo603_placement_fence_checks_every_matching_clear_target
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_case_state_id_resolves]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_case_reference_inside_the_atlas_resolves]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_clock_a_case_uses_is_declared]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_applicable_case_carries_one_trigger]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_face_cases_carry_both_ruled_viewports]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_applicable_predicate_is_a_kind_the_rig_implements]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_predicate_observes_a_selector_or_a_route]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_source_reference_lands_on_its_symbol]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_case_keeps_its_human_sentence]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_ui_action_is_one_the_rig_implements]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_boundary_names_its_substitution]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_no_precondition_check_compares_two_snapshots]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_precondition_check_observes_a_selector_or_a_route]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_no_check_asserts_the_result_the_trigger_must_produce]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_no_step_acts_on_a_root_placeholder]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_navigation_steps_carry_no_selector]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_desk_face_case_crosses_the_gate_first]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_every_captured_id_names_the_field_it_reads]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_ids_are_unique]
tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_validates_against_schema_and_openapi
tests/unit/test_philo13_astra_atlas.py::test_phase13_case_and_sibling_manifest_is_local
tests/unit/test_philo13_astra_atlas.py::test_phase13_shared_semantic_guards_show_red_then_green
tests/unit/test_philo13_astra_atlas.py::test_phase13_shared_operation_count_excludes_only_phase13_files
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_declares_touch_when_nested_trigger_then_uses_it
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_records_pointer_adapter_at_desktop_width
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_records_touch_adapter_and_uses_native_tap
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_guarded_touch_blocks_before_synthetic_delivery
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_real_playwright_tap_emits_touch_pointer_events
tests/unit/test_philo13_graph_walk.py::test_ui_by_viewport_real_playwright_click_emits_mouse_pointer_events
tests/unit/test_philo13_fixture_rig.py::test_repository_fixture_binds_scalars_and_restarts_the_owned_hub
tests/unit/test_philo13_fixture_rig.py::test_ingest_coder_fixture_uses_real_cli_and_records_question
tests/unit/test_philo13_fixture_rig.py::test_set_input_files_dispatches_native_path_and_records_hash
tests/unit/test_philo13_fixture_rig.py::test_file_chooser_dispatch_uses_native_click_at_both_widths[1440-ui-pointer]
tests/unit/test_philo13_fixture_rig.py::test_file_chooser_dispatch_uses_native_click_at_both_widths[393-ui-touch]
tests/unit/test_philo13_fixture_rig.py::test_real_browser_file_chooser_accepts_detached_input_at_both_widths[1440]
tests/unit/test_philo13_fixture_rig.py::test_real_browser_file_chooser_accepts_detached_input_at_both_widths[393]
tests/unit/test_philo13_fixture_rig.py::test_set_input_files_refuses_a_path_outside_owned_roots
tests/unit/test_philo13_fixture_rig.py::test_hub_environment_and_teardown_never_use_inherited_tmux_socket
tests/unit/test_philo13_fixture_rig.py::test_hub_tmux_teardown_does_not_mislabel_permission_error_as_no_server
tests/unit/test_philo13_fixture_rig.py::test_hub_tmux_teardown_records_success_and_bounded_stderr
tests/unit/test_philo13_fixture_rig.py::test_repository_router_passes_fixture_to_real_builder
tests/unit/test_philo13_fixture_rig.py::test_real_hub_reads_repository_and_coder_producers
tests/unit/test_philo13_repository_fixture.py::test_repository_fixture_uses_real_registry_collector_dossier_and_dw
tests/unit/test_philo13_repository_fixture.py::test_repository_fixture_refuses_reuse_and_symlinked_home
tests/unit/test_graph_walk_select_option.py::test_select_option_sends_exact_selector_and_value_to_native_locator
tests/unit/test_graph_walk_select_option.py::test_press_with_a_selector_delivers_the_key_to_that_control
tests/unit/test_graph_walk_select_option.py::test_select_option_refuses_an_empty_target_or_value_before_page_access[-destination-slack-7]
tests/unit/test_graph_walk_select_option.py::test_select_option_refuses_an_empty_target_or_value_before_page_access[select[data-testid='slack-destination']-]
tests/unit/test_graph_walk_select_option.py::test_select_option_refuses_an_empty_target_or_value_before_page_access[   -destination-slack-7]
tests/unit/test_graph_walk_select_option.py::test_select_option_refuses_an_empty_target_or_value_before_page_access[select[data-testid='slack-destination']-   ]
tests/unit/test_graph_walk_select_option.py::test_atlas_schema_accepts_select_option_and_requires_nonempty_fields

151 tests collected in 0.29s
```

### Captured run — 2026-10-02T02:52:41Z

- **Command:** `uv run pytest -q tests/unit/test_philo_graph_atlas.py tests/unit/test_philo13_astra_atlas.py tests/unit/test_philo13_graph_walk.py tests/unit/test_philo13_fixture_rig.py tests/unit/test_philo13_repository_fixture.py tests/unit/test_graph_walk_select_option.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
........................................................................ [ 47%]
................................................F....................... [ 95%]
.......                                                                  [100%]
=================================== FAILURES ===================================
_______________ test_phase13_case_and_sibling_manifest_is_local ________________

    def test_phase13_case_and_sibling_manifest_is_local() -> None:
        cases = _cases()
        assert set(cases) == EXPECTED_CASES
        assert cases["case.p13.directory.zone_window.op"]["viewports"] == []
        assert sum(case["id"].endswith(".op") for case in cases.values()) == 1
        faces = [case for case in cases.values() if not case["id"].endswith(".op")]
        assert len(faces) == 9
        for case in faces:
            assert case["viewports"] == [1440, 393]
            # A DOM-only text match passed an off-screen Repository in the real walk.
>           assert case["expected"]["kind"] == "readable_text", case["id"]
                   ^^^^^^^^^^^^^^^^^^^^^^^^
E           KeyError: 'kind'

tests/unit/test_philo13_astra_atlas.py:90: KeyError
=========================== short test summary info ============================
FAILED tests/unit/test_philo13_astra_atlas.py::test_phase13_case_and_sibling_manifest_is_local
1 failed, 150 passed in 11.21s
```

### Captured run — 2026-10-02T02:53:21Z

- **Command:** `uv run pytest -q tests/unit/test_philo_graph_atlas.py tests/unit/test_philo13_astra_atlas.py tests/unit/test_philo13_graph_walk.py tests/unit/test_philo13_fixture_rig.py tests/unit/test_philo13_repository_fixture.py tests/unit/test_graph_walk_select_option.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7c5ab0af9025170c2302d8e3256a13ba6b2eb520

```text
........................................................................ [ 47%]
........................................................................ [ 95%]
.......                                                                  [100%]
151 passed in 11.22s
```
