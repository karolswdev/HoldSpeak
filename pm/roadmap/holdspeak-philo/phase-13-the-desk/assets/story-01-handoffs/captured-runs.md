# Evidence - PHILO-13-01

- **Story:** PHILO-13-01 - B0 — Walk what was not walked
- **Status:** done
- **Date:** 2026-10-01

## Proof

### Captured run — 2026-10-02T01:43:33Z

- **Command:** `uv run --extra dev pytest --collect-only -q tests/unit/test_philo_graph_atlas.py tests/unit/test_philo13_astra_atlas.py tests/unit/test_philo13_graph_walk.py tests/unit/test_graph_walk_select_option.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c29d5d71eeaa57a8934f372548faf024b1899f44

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
tests/unit/test_graph_walk_select_option.py::test_select_option_sends_exact_selector_and_value_to_native_locator
tests/unit/test_graph_walk_select_option.py::test_press_with_a_selector_delivers_the_key_to_that_control
tests/unit/test_graph_walk_select_option.py::test_select_option_refuses_an_empty_target_or_value_before_page_access[-destination-slack-7]
tests/unit/test_graph_walk_select_option.py::test_select_option_refuses_an_empty_target_or_value_before_page_access[select[data-testid='slack-destination']-]
tests/unit/test_graph_walk_select_option.py::test_select_option_refuses_an_empty_target_or_value_before_page_access[   -destination-slack-7]
tests/unit/test_graph_walk_select_option.py::test_select_option_refuses_an_empty_target_or_value_before_page_access[select[data-testid='slack-destination']-   ]
tests/unit/test_graph_walk_select_option.py::test_atlas_schema_accepts_select_option_and_requires_nonempty_fields

136 tests collected in 0.22s
```

### Captured run — 2026-10-02T01:43:34Z

- **Command:** `uv run --extra dev pytest -q tests/unit/test_philo_graph_atlas.py tests/unit/test_philo13_astra_atlas.py tests/unit/test_philo13_graph_walk.py tests/unit/test_graph_walk_select_option.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c29d5d71eeaa57a8934f372548faf024b1899f44

```text
........................................................................ [ 52%]
................................................................         [100%]
136 passed in 2.02s
```

### Captured run — 2026-10-02T01:43:57Z

- **Command:** `uv run --extra dev pytest -q tests/unit/test_philo_graph_atlas.py::test_operation_siblings_use_headless_reads_and_canonical_steps`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** c29d5d71eeaa57a8934f372548faf024b1899f44

```text
F                                                                        [100%]
=================================== FAILURES ===================================
________ test_operation_siblings_use_headless_reads_and_canonical_steps ________

    def test_operation_siblings_use_headless_reads_and_canonical_steps() -> None:
        """Operation siblings prove the same durable result through the hub.
    
        Their observation is an operation object, so the rig can call a durable
        read after the trigger.  A refusal must observe that retained read while
        the trigger's own refusal record remains the only mutating result.
        """
        siblings = [
            case
            for path in ATLAS_FILES
            for case in json.loads(path.read_text())['cases']
            if case['id'].endswith('.op') or case['id'].endswith('.op.replayed')
        ]
        # PHILO-13 B0 owns its own atlas count; semantic checks still use siblings.
        legacy_siblings = [
            case
            for path in ATLAS_FILES
            if not path.name.startswith("atlas-phase13-")
            for case in json.loads(path.read_text())['cases']
            if case['id'].endswith('.op') or case['id'].endswith('.op.replayed')
        ]
        # Historical pre-Phase-13 total is 69; the unfiltered list remains the
        # semantic subject, including both Phase 13 atlases. H-B0b count anchor.
        assert len(legacy_siblings) == 69
        sibling_ids = {case["id"] for case in siblings}
        assert READ_REFUSAL_SIBLINGS <= sibling_ids
        mutating = {
            'decision.create', 'decision.update', 'meeting.import',
            'meeting.summary.run', 'brief.generate', 'brief.shelf.write',
            'thought.create', 'thought.save',
            # PHILO-7-03: the desk slice's writes.
            'note.create', 'zone.create', 'zone.file', 'zone.unfile',
            'kb.create', 'kb.member.add', 'kb.member.remove',
            'decision.supersede', 'decision.delete',
            # PHILO-8-03: the rename the list's name field writes.
            'zone.update',
            # PHILO-9-05: the Room's delivery record.
            'project.mark_update_delivered',
            # PHILO-10-05: the Send's admitted writes.
            'channel.save_destination', 'channel.prepare', 'channel.send', 'channel.discard',
        }
        readable = {
            'decision.read', 'decision.list', 'meeting.list', 'meeting.read',
            'brief.latest', 'brief.shelf.read', 'thought.read',
            'thought.workbench.read', 'thought.list',
            'note.read', 'note.list', 'zone.read', 'zone.list', 'zone.members',
            'kb.read', 'kb.list', 'kb.members', 'kernel.receipt.read',
            # PHILO-9-05: the Room's update list.
            'project.list_updates',
            # PHILO-10-05: the Send's reads.
            'channel.destinations', 'channel.sends',
        }
        problems: list[str] = []
        for case in siblings:
            expected = case['expected']
            observation = expected.get('observe_at')
            if not isinstance(observation, dict) or observation.get('kind') != 'op':
                problems.append(f"{case['id']}: expected.observe_at is not an op object")
                continue
            if observation.get('name') not in readable:
                problems.append(f"{case['id']}: observation re-fires {observation.get('name')!r}")
            predicate = expected.get('predicate') or {}
            predicate_kind = predicate.get('kind')
            # PHILO-10-05: an op predicate, or all_of an op_facts and the
            # recording runner's count (cli_calls): both hub-side, never a face.
            parts = [p.get('kind') for p in predicate.get('predicates', [])] if predicate_kind == 'all_of' else []
            if predicate_kind not in {'op_field', 'op_refusal', 'op_facts'} and not (
                    parts and 'op_facts' in parts and set(parts) <= {'op_facts', 'cli_calls'}):
                problems.append(f"{case['id']}: predicate is not an op predicate")
            for read in expected.get('reads', []):
                if read.get('kind') != 'op' or read.get('name') not in readable:
                    problems.append(f"{case['id']}: expected read is not durable: {read}")
            for step in _acts(case):
                if step.get('kind') == 'ui':
                    problems.append(f"{case['id']}: operation sibling carries a UI step")
            trigger = case.get('trigger') or {}
            if trigger.get('kind') == 'op' and trigger.get('name') not in mutating:
                if case["id"] not in READ_REFUSAL_SIBLINGS or trigger.get("name") not in readable:
                    problems.append(f"{case['id']}: trigger is not a producer operation")
>       assert not problems, '\n'.join(problems)
E       AssertionError: case.p13.directory.zone_window.op: observation re-fires 'zone.create'
E       assert not ["case.p13.directory.zone_window.op: observation re-fires 'zone.create'"]

tests/unit/test_philo_graph_atlas.py:548: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_philo_graph_atlas.py::test_operation_siblings_use_headless_reads_and_canonical_steps
1 failed in 0.36s
```

### Captured run — 2026-10-02T01:43:58Z

- **Command:** `uv run --extra dev pytest -q tests/unit/test_philo_graph_atlas.py::test_operation_siblings_use_headless_reads_and_canonical_steps`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c29d5d71eeaa57a8934f372548faf024b1899f44

```text
.                                                                        [100%]
1 passed in 0.31s
```

### Captured run — 2026-10-02T01:44:24Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.directory.zone_window.op --brain astra --viewport 1440 --engine none --headless --no-build --out .tmp/graph-walk/philo-13-01/handoff-zone-op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c29d5d71eeaa57a8934f372548faf024b1899f44

```text
PASS: live
BRAIN: astra
SOURCE: 27b915538b792f4a80d0cf1c46a0600cb68756e3 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-ChQW1Esz.js'] hub=http://127.0.0.1:59620 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-rzsrroq2/.local/share/holdspeak/holdspeak.db engine=none
JOB: j1
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: placeholder(s) ['zone_id'] are bound by the trigger's own `capture_as`; `expected` is resolved after it fires (fields naming them are not read before the trigger)
NOTE: predicate: all 4 facts hold: observe_at directory.id holds; observe_at directory.name holds; op read #0 (zone.list) <root> holds; the trigger operation_id is absent
```
