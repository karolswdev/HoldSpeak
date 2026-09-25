# Evidence - PHILO-6-05

- **Story:** PHILO-6-05 - The decision body at once
- **Status:** done
- **Date:** 2026-09-24

## Proof

### Captured run — 2026-09-25T03:11:29Z

- **Command:** `bash -c set -euo pipefail; export HOME=$(mktemp -d); export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; uv run pytest --collect-only -q tests/unit/test_graph_walk_first_paint.py tests/unit/test_philo_graph_atlas.py tests/unit/test_graph_walk_calibration.py; uv run pytest -q tests/unit/test_graph_walk_first_paint.py tests/unit/test_philo_graph_atlas.py tests/unit/test_graph_walk_calibration.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 705d21af76797a847f58927ac6c4a3f27d3480a4

```text
tests/unit/test_graph_walk_first_paint.py::test_first_read_paint_cannot_be_replaced_by_a_later_readable_frame[0-False-True]
tests/unit/test_graph_walk_first_paint.py::test_first_read_paint_cannot_be_replaced_by_a_later_readable_frame[200-False-False]
tests/unit/test_graph_walk_first_paint.py::test_first_read_paint_cannot_be_replaced_by_a_later_readable_frame[0-True-False]
tests/unit/test_graph_walk_first_paint.py::test_a_later_blank_cannot_hide_behind_a_good_first_paint
tests/unit/test_philo_graph_atlas.py::test_every_atlas_file_is_read
tests/unit/test_philo_graph_atlas.py::test_schema_is_a_valid_2020_12_schema
tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase3.json]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase3.json]
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
tests/unit/test_graph_walk_calibration.py::test_rig_is_versioned
tests/unit/test_graph_walk_calibration.py::test_six_calibration_cases_get_their_expected_verdicts
tests/unit/test_graph_walk_calibration.py::test_no_calibration_verdict_comes_from_the_presence_of_a_diff
tests/unit/test_graph_walk_calibration.py::test_the_wrong_target_case_records_where_the_result_landed
tests/unit/test_graph_walk_calibration.py::test_the_operation_that_never_completes_is_incomplete_not_settled
tests/unit/test_graph_walk_calibration.py::test_every_observation_carries_provenance_and_before_after
tests/unit/test_graph_walk_calibration.py::test_run_ids_are_unique_per_case_brain_viewport
tests/unit/test_graph_walk_calibration.py::test_home_under_the_owners_local_share_is_refused
tests/unit/test_graph_walk_calibration.py::test_a_temporary_home_is_accepted
tests/unit/test_graph_walk_calibration.py::test_an_unexplained_zero_diff_is_not_a_pass
tests/unit/test_graph_walk_calibration.py::test_a_window_already_open_before_the_trigger_is_not_the_trigger_opening_it
tests/unit/test_graph_walk_calibration.py::test_every_negative_control_comes_out_as_stated
tests/unit/test_graph_walk_calibration.py::test_a_refresh_with_its_handler_removed_fails
tests/unit/test_graph_walk_calibration.py::test_a_replay_identity_must_name_an_attribute_or_the_response
tests/unit/test_graph_walk_calibration.py::test_a_result_after_the_bound_is_never_a_pass
tests/unit/test_graph_walk_calibration.py::test_an_absence_needs_a_scope_that_exists
tests/unit/test_graph_walk_calibration.py::test_the_ui_vocabulary_is_closed_and_blocks_before_anything_fires
tests/unit/test_graph_walk_calibration.py::test_a_precondition_that_does_not_hold_blocks_the_case
tests/unit/test_graph_walk_calibration.py::test_a_precondition_that_holds_lets_the_case_run
tests/unit/test_graph_walk_calibration.py::test_a_words_only_case_is_blocked_and_never_a_keyerror
tests/unit/test_graph_walk_calibration.py::test_an_unreachable_case_keeps_its_reason_verbatim
tests/unit/test_graph_walk_calibration.py::test_a_captured_value_drives_a_later_step_and_the_predicate
tests/unit/test_graph_walk_calibration.py::test_an_unresolved_placeholder_is_blocked_and_never_sent
tests/unit/test_graph_walk_calibration.py::test_substitution_fills_only_identifiers
tests/unit/test_graph_walk_calibration.py::test_a_capture_without_a_value_blocks
tests/unit/test_graph_walk_calibration.py::test_a_check_step_in_setup_blocks_where_it_stands
tests/unit/test_graph_walk_calibration.py::test_a_check_step_that_holds_lets_the_case_run
tests/unit/test_graph_walk_calibration.py::test_the_step_vocabulary_is_closed_and_exported
tests/unit/test_graph_walk_calibration.py::test_a_relative_goto_resolves_against_the_hub
tests/unit/test_graph_walk_calibration.py::test_a_fixture_step_captures_from_its_own_response
tests/unit/test_graph_walk_calibration.py::test_a_trigger_identity_is_read_from_the_response_not_the_page
tests/unit/test_graph_walk_calibration.py::test_identity_display_requires_the_returned_id_to_be_the_displayed_one
tests/unit/test_graph_walk_calibration.py::test_a_row_match_reaches_a_nested_field
tests/unit/test_graph_walk_calibration.py::test_prose_in_expected_words_is_not_a_placeholder
tests/unit/test_graph_walk_calibration.py::test_a_label_only_boundary_is_refused
tests/unit/test_graph_walk_calibration.py::test_an_engine_reply_boundary_blocks_when_it_was_never_installed
tests/unit/test_graph_walk_calibration.py::test_an_engine_reply_boundary_records_the_installed_reply
tests/unit/test_graph_walk_calibration.py::test_the_replay_engine_answers_the_recorded_reply
tests/unit/test_graph_walk_calibration.py::test_the_scheduler_wait_adapter_lets_a_timer_edge_produce_the_result
tests/unit/test_graph_walk_calibration.py::test_every_new_predicate_kind_gets_its_verdict
tests/unit/test_graph_walk_calibration.py::test_a_refusal_status_is_read_from_the_triggers_own_response
tests/unit/test_graph_walk_calibration.py::test_a_row_gone_is_named_never_merely_fewer
tests/unit/test_graph_walk_calibration.py::test_protocol_field_reads_one_named_field
tests/unit/test_graph_walk_calibration.py::test_input_value_reads_the_field_not_the_dom_text
tests/unit/test_graph_walk_calibration.py::test_a_restart_is_a_real_restart_and_the_value_survives
tests/unit/test_graph_walk_calibration.py::test_any_other_cli_command_stays_blocked_with_its_name
tests/unit/test_graph_walk_calibration.py::test_a_refusal_must_name_what_is_missing
tests/unit/test_graph_walk_calibration.py::test_an_asserted_absence_is_earned_by_the_named_bound
tests/unit/test_graph_walk_calibration.py::test_the_new_kinds_are_branches_the_atlas_fence_can_read
tests/unit/test_graph_walk_calibration.py::test_a_prose_predicate_is_blocked_not_guessed
tests/unit/test_graph_walk_calibration.py::test_protocol_rows_needs_a_NEW_matching_row_not_any_change
tests/unit/test_graph_walk_calibration.py::test_a_clock_step_blocks_instead_of_claiming_the_state
tests/unit/test_graph_walk_calibration.py::test_a_fixture_step_without_a_declared_boundary_blocks
tests/unit/test_graph_walk_calibration.py::test_an_unknown_step_kind_blocks
tests/unit/test_graph_walk_calibration.py::test_a_not_applicable_case_is_recorded_not_skipped
tests/unit/test_graph_walk_calibration.py::test_the_real_j4_import_case_fires_the_upload_and_binds_the_meeting_id
tests/unit/test_graph_walk_calibration.py::test_a_placeholder_nothing_binds_blocks_before_the_trigger
tests/unit/test_graph_walk_calibration.py::test_a_placeholder_still_unbound_after_the_trigger_blocks_naming_it
tests/unit/test_graph_walk_calibration.py::test_a_clicked_verb_reads_its_identity_from_its_own_response
tests/unit/test_graph_walk_calibration.py::test_a_clicked_verb_status_is_read_by_its_declared_route
tests/unit/test_graph_walk_calibration.py::test_a_different_id_beside_unchanged_old_content_fails
tests/unit/test_graph_walk_calibration.py::test_a_longer_id_does_not_display_a_shorter_one

143 tests collected in 0.19s
........................................................................ [ 50%]
.......................................................................  [100%]
143 passed in 99.83s (0:01:39)
```

### Captured run — 2026-09-25T03:16:29Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); cd web; npm exec -- vitest list src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx src/desk/__tests__/philo301DecisionNoLoss.test.tsx src/desk/__tests__/philo301RetryKept.test.tsx src/desk/__tests__/writeReceiptGuard.test.ts src/desk/components/__tests__/writeReceipts.test.tsx --maxWorkers=1; npm exec -- vitest run src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx src/desk/__tests__/philo301DecisionNoLoss.test.tsx src/desk/__tests__/philo301RetryKept.test.tsx src/desk/__tests__/writeReceiptGuard.test.ts src/desk/components/__tests__/writeReceipts.test.tsx --maxWorkers=1; npm run build; npm run typecheck`
- **Cwd:** .
- **Exit code:** 2
- **Index-tree:** 705d21af76797a847f58927ac6c4a3f27d3480a4

```text
src/desk/components/__tests__/writeReceipts.test.tsx > HS-132-06 workbench write receipts > names a refused ADD ITEM and keeps the typed instruction
src/desk/components/__tests__/writeReceipts.test.tsx > HS-132-06 workbench write receipts > re-issues the refused add when RETRY is pressed
src/desk/components/__tests__/writeReceipts.test.tsx > HS-132-06 workbench write receipts > names a refused DISMISS ITEM
src/desk/components/__tests__/writeReceipts.test.tsx > HS-132-06 workbench write receipts > names a refused RE-RUN ITEM
src/desk/components/__tests__/writeReceipts.test.tsx > HS-132-06 workbench write receipts > names a refused RETRY MINT
src/desk/components/__tests__/writeReceipts.test.tsx > HS-132-06 workbench write receipts > names a refused RUN
src/desk/components/__tests__/writeReceipts.test.tsx > HS-132-06 workbench write receipts > names a refused DROP TO WORK and a malformed drop
src/desk/components/__tests__/writeReceipts.test.tsx > HS-132-06 workbench write receipts > stays quiet when the hub takes the write
src/desk/components/__tests__/writeReceipts.test.tsx > HS-132-06 desk-floor write receipts > names a refused SEED DESK on the empty floor
src/desk/components/__tests__/writeReceipts.test.tsx > HS-132-06 desk-floor write receipts > names a refused CREATE NOTE on the empty floor
src/desk/components/__tests__/writeReceipts.test.tsx > HS-132-06 desk-floor write receipts > keeps a landed create quiet
src/desk/components/__tests__/writeReceipts.test.tsx > HS-132-06 populated-floor write receipts > names a refused floor-menu create in the system bar, and retries
src/desk/components/__tests__/writeReceipts.test.tsx > HS-132-06 populated-floor write receipts > prints one receipt only: a nearer line silences the system bar
src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx > PHILO-6-05 decision body fences > rolls a failed save back to the prior body before a slow refresh resolves
src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx > PHILO-6-05 decision body fences > keeps the prior body when a refused save's refresh fails
src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx > PHILO-6-05 decision body fences > negative control: a held pullout prop stays stale after the store write
src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx > PHILO-6-05 decision body fences > does not reproduce when the production host derives the object from items
src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx > PHILO-6-05 decision body fences > keeps an optimistic body when a pre-write refresh resolves
src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx > PHILO-6-05 decision body fences > keeps an optimistic body when a refresh starts during a pending write
src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx > PHILO-6-05 decision body fences > does not let an older refusal roll back or receipt a newer decision write
src/desk/__tests__/philo301DecisionNoLoss.test.tsx > PHILO-3-01 no data loss on an immediate reopen > save -> close -> reopen inside the marker -> Done keeps the text
src/desk/__tests__/philo301RetryKept.test.tsx > PHILO-3-01 a read failure never takes a pending write's Retry > create fails, read fails, both recover, Retry creates the record
src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > flags a write caught into an empty block
src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > flags a bare apiRequest swallow with a named binding
src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > passes a write that reports into the receipt channel
src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > ignores bare catches that guard no write
src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps the debt ledger pointed at real files
src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > leaves the wired surfaces with no swallowed write at all
npm notice
npm notice New minor version of npm available! 11.6.2 -> 11.20.0
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.20.0
npm notice To update run: npm install -g npm@11.20.0
npm notice

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-6-b/web


 Test Files  5 passed (5)
      Tests  29 passed (29)
   Start at  21:16:34
   Duration  6.29s (transform 2.00s, setup 227ms, import 2.94s, tests 1.83s, environment 911ms)


> holdspeak-web@0.0.1 build
> vite build

vite v7.3.6 building client environment for production...
transforming...
✓ 1690 modules transformed.
rendering chunks...
[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-6-b/web/src/features/project-room/api.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-6-b/web/src/features/project-room/prepare/usePrepareController.ts but also statically imported by /Users/karol/dev/tools/wt-philo-6-b/web/src/features/project-room/ProjectRoomCore.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/features/project-room/RoomPeopleSection.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/features/project-room/useProjectRoomController.ts, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/shell.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/window/Dock.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/store/compositorSlice.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/features/concierge/useConciergeController.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/features/project-room/prepare/usePrepareController.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/pages/cores/SettingsCore.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/pages/cores/dictation/SpeakFace.tsx but also statically imported by /Users/karol/dev/tools/wt-philo-6-b/web/src/App.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/components/AmbientLayer.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/chair/ChairHome.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/AttentionDrawer.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/DeskStartActions.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/FirstWords.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/GlassDropLayer.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/Pullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/RecordOrb.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/SurfaceWindows.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/SystemShade.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/TrustWindow.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/ArtifactPullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/ChainPullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/CoderPullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/DecisionPullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/DirectoryPullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/KbPullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/MeetingPullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/NotePullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/WorkflowPullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/shared/CapabilitySection.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/views/BriefView.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/views/FollowThroughView.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/surface/citations.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/features/project-room/ProjectRoomCore.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/features/project-room/RoomPeopleSection.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/features/project-room/door/useDoorController.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/features/project-room/prepare/PreparePosture.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/features/project-room/recall/RecallFace.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/features/project-room/useProjectRoomController.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/pages/cores/CommandsCore.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/pages/cores/CompanionCore.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/pages/cores/HistoryCore.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/pages/cores/LiveCore.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/pages/cores/PeopleCore.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/pages/cores/RuntimeDocsCore.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/pages/cores/SettingsCore.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/pages/cores/SetupCore.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/pages/cores/dictation/DictationSections.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/pages/cores/dictation/Readiness.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/pages/cores/history/ArtifactsLibrary.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/pages/cores/history/DoorSection.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/pages/cores/history/ImportSection.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/pages/cores/history/MeetingReview.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/store.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/shell.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/shell.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/features/concierge/useConciergeController.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/features/concierge/useConciergeController.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/features/concierge/useConciergeController.ts but also statically imported by /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/DeskApp.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/chair/ChairHome.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/AskPanel.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/DeskChrome.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/DeskFilingStrip.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/DeskListView.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/DeskMenuBar.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/DeskStartActions.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/DeskWindow.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/EmptyDesk.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/FirstWords.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/GroundingSection.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/InfoWindow.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/InlineEditor.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/InterviewPanel.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/NewWorkbenchChooser.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/Pullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/RecordOrb.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/RepoWindow.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/RoadmapWindow.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/ScheduleCreateWindow.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/SessionPullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/SurfaceWindows.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/ThreadComposer.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/WorkbenchTemplatePicker.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/WorkbenchWindow.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/ZoneWindow.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/window/Dock.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/window/Expose.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/window/RoomActions.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/window/windowCommands.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/window/windowRegistry.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/gl/WorldStage.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/gl/atmosphereActivity.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/gl/engine.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/infoContract.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/intelligenceNavigation.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/keymap.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/newThought.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/ArtifactPullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/ChainPullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/CoderPullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/DecisionPullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/DirectoryPullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/KbPullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/MeetingPullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/NotePullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/ThreadPullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/WorkflowPullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/editors/KbEditor.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/editors/NoteEditor.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/editors/RecipeEditor.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/editors/WorkflowEditor.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/editors/useDebouncedSave.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/shared/CapabilitySection.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/shared/ThreadsSection.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/views/DecisionsView.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/useDeskChangedRefresh.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/features/project-room/ProjectRoomCore.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/features/project-room/door/useDoorController.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/pages/cores/ChangePlacesCore.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/pages/cores/WorkbenchesHomeCore.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/pages/cores/settingsPrefs.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/threads.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/shell.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/surface/citations.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/verbRegistry.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/verbRegistry.ts but also statically imported by /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/callLoopWiring.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/CallChip.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/DeskToolInspector.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/DeskToolShelf.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/hooks/useChatImport.ts, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/RecipePullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/ThreadPullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/shared/ThreadsSection.tsx, dynamic import will not move module into another chunk.

[plugin vite:reporter] 
(!) /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/steering.ts is dynamically imported by /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/shell.ts but also statically imported by /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/MissionControlConveyor.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/components/SessionPullout.tsx, /Users/karol/dev/tools/wt-philo-6-b/web/src/desk/pullouts/CoderPullout.tsx, dynamic import will not move module into another chunk.

computing gzip size...
../holdspeak/static/_built/index.html                                                     0.90 kB │ gzip:   0.44 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-700-normal-DMty7AZE.woff2      4.20 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-400-normal-C190GLew.woff2          4.23 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-500-normal-JpySY46c.woff2          4.28 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-600-normal-DUi7WF5p.woff2      4.31 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-500-normal-BmEvtly_.woff2      4.32 kB
../holdspeak/static/_built/assets/inter-vietnamese-400-normal-DMkecbls.woff2              4.97 kB
../holdspeak/static/_built/assets/inter-vietnamese-600-normal-Cc8MFFhd.woff2              5.10 kB
../holdspeak/static/_built/assets/inter-vietnamese-500-normal-DOriooB6.woff2              5.11 kB
../holdspeak/static/_built/assets/inter-greek-ext-400-normal-DGGRlc-M.woff2               5.26 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-400-normal-BEIGL1Tu.woff2       5.33 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-500-normal-DmUKJPL_.woff2       5.36 kB
../holdspeak/static/_built/assets/jetbrains-mono-vietnamese-400-normal-CqNFfHCs.woff      5.37 kB
../holdspeak/static/_built/assets/inter-greek-ext-500-normal-C4iEst2y.woff2               5.43 kB
../holdspeak/static/_built/assets/inter-greek-ext-600-normal-DRtmH8MT.woff2               5.43 kB
../holdspeak/static/_built/assets/jetbrains-mono-vietnamese-500-normal-DNRqzVM1.woff      5.48 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-700-normal-Duxec5Rn.woff       5.59 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-400-normal-B9oWc5Lo.woff           5.66 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-600-normal-D6zpsUhD.woff       5.70 kB
../holdspeak/static/_built/assets/space-grotesk-vietnamese-500-normal-BTqKIpxg.woff       5.72 kB
../holdspeak/static/_built/assets/jetbrains-mono-greek-500-normal-D7SFKleX.woff           5.72 kB
../holdspeak/static/_built/assets/inter-vietnamese-400-normal-Bbgyi5SW.woff               6.50 kB
../holdspeak/static/_built/assets/inter-vietnamese-500-normal-mJboJaSs.woff               6.60 kB
../holdspeak/static/_built/assets/inter-vietnamese-600-normal-BuLX-rYi.woff               6.64 kB
../holdspeak/static/_built/assets/jetbrains-mono-cyrillic-400-normal-ugxPyKxw.woff        6.98 kB
../holdspeak/static/_b
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-09-25T03:19:34Z

- **Command:** `bash -c set -euo pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); cd web; npm exec -- vitest run src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx src/desk/__tests__/philo301DecisionNoLoss.test.tsx src/desk/__tests__/philo301RetryKept.test.tsx src/desk/__tests__/writeReceiptGuard.test.ts src/desk/components/__tests__/writeReceipts.test.tsx --maxWorkers=1; npm run typecheck; npm run build -- --logLevel error`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 705d21af76797a847f58927ac6c4a3f27d3480a4

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-6-b/web


 Test Files  5 passed (5)
      Tests  29 passed (29)
   Start at  21:19:34
   Duration  5.73s (transform 1.75s, setup 207ms, import 2.61s, tests 1.74s, environment 834ms)

npm notice
npm notice New minor version of npm available! 11.6.2 -> 11.20.0
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.20.0
npm notice To update run: npm install -g npm@11.20.0
npm notice

> holdspeak-web@0.0.1 typecheck
> tsc --noEmit


> holdspeak-web@0.0.1 build
> vite build --logLevel error
```

### Captured run — 2026-09-25T03:20:13Z

- **Command:** `bash -c set -euo pipefail; export HOME=$(mktemp -d); export HOLDSPEAK_EVIDENCE_WRITE=1; export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export PYTHONPATH="$PWD"; .venv/bin/python scripts/graph_walk.py run --case case.closure.chain.s4_saved_content --brain astra --viewport 393 --engine real --no-build --out docs/internal/philo/phase-6/body/green-s4-393`
- **Cwd:** .
- **Exit code:** 2
- **Index-tree:** 705d21af76797a847f58927ac6c4a3f27d3480a4

```text
usage: graph_walk.py run [-h] --atlas ATLAS --case CASE
                         --brain {muaddib,astra} --viewport {1440,393}
                         [--engine {real,replayed,none}] [--out OUT]
                         [--no-build] [--headless]
graph_walk.py run: error: the following arguments are required: --atlas
```

### Captured run — 2026-09-25T03:20:39Z

- **Command:** `bash -c set -euo pipefail; export HOME=$(mktemp -d); export HOLDSPEAK_EVIDENCE_WRITE=1; export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export PYTHONPATH="$PWD"; .venv/bin/python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s4_saved_content --brain astra --viewport 393 --engine real --no-build --out docs/internal/philo/phase-6/body/green-s4-393`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 705d21af76797a847f58927ac6c4a3f27d3480a4

```text
PASS: live
BRAIN: astra
SOURCE: e8ad402219fd64e3438ff6c9c6376a8ef48d29ef dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-CvfCFuGX.js'] hub=http://127.0.0.1:54787 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-hr4gr_ko/.local/share/holdspeak/holdspeak.db engine=real
JOB: a1
VERDICT: pass terminal=settled
EVIDENCE: ['docs/internal/philo/phase-6/body/green-s4-393/20260925T032039Z-case.closure.chain.s4_saved_content-astra-393/before.png', 'docs/internal/philo/phase-6/body/green-s4-393/20260925T032039Z-case.closure.chain.s4_saved_content-astra-393/after.png', 'docs/internal/philo/phase-6/body/green-s4-393/20260925T032039Z-case.closure.chain.s4_saved_content-astra-393/framed.png']
NOTE: framing is a separate scroll after the raw observation; it does not change the verdict or completion time
NOTE: predicate: 'Keep summary retrieval on the local desk' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 437, 'w': 363, 'h': 82}
```

### Captured run — 2026-09-25T03:21:31Z

- **Command:** `bash -c set -euo pipefail; export HOME=$(mktemp -d); export HOLDSPEAK_EVIDENCE_WRITE=1; export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export PYTHONPATH="$PWD"; .venv/bin/python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase3.json --case case.closure.chain.s4_saved_content --brain astra --viewport 1440 --engine real --no-build --out docs/internal/philo/phase-6/body/green-s4-1440`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 705d21af76797a847f58927ac6c4a3f27d3480a4

```text
PASS: live
BRAIN: astra
SOURCE: e8ad402219fd64e3438ff6c9c6376a8ef48d29ef dirty=True
CONTRACT: rig=1.3.0 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-CvfCFuGX.js'] hub=http://127.0.0.1:54944 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-km5q9lui/.local/share/holdspeak/holdspeak.db engine=real
JOB: a1
VERDICT: pass terminal=settled
EVIDENCE: ['docs/internal/philo/phase-6/body/green-s4-1440/20260925T032131Z-case.closure.chain.s4_saved_content-astra-1440/before.png', 'docs/internal/philo/phase-6/body/green-s4-1440/20260925T032131Z-case.closure.chain.s4_saved_content-astra-1440/after.png', 'docs/internal/philo/phase-6/body/green-s4-1440/20260925T032131Z-case.closure.chain.s4_saved_content-astra-1440/framed.png']
NOTE: framing is a separate scroll after the raw observation; it does not change the verdict or completion time
NOTE: predicate: 'Keep summary retrieval on the local desk' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 1037, 'y': 219, 'w': 370, 'h': 82}
```

### Captured run — 2026-09-25T03:23:54Z

- **Command:** `python3 docs/internal/philo/phase-6/body/verify_transition.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 705d21af76797a847f58927ac6c4a3f27d3480a4

```text
393 red: FAIL; first read 10.8 ms readable; first blank 159.1 ms; 3600 read-mode frames
393 green: PASS; first read 10.8 ms readable; first blank none; 129 read-mode frames
1440 red: FAIL; first read 10.1 ms readable; first blank 77.3 ms; 3600 read-mode frames
1440 green: PASS; first read 10.4 ms readable; first blank none; 129 read-mode frames
```

### Captured run — 2026-09-25T03:28:36Z

- **Command:** `bash -c set -euo pipefail; export HOME=$(mktemp -d); uv run pytest --collect-only -q tests/unit/test_api_surface.py tests/unit/test_philo_architecture.py; uv run pytest -q tests/unit/test_api_surface.py tests/unit/test_philo_architecture.py; python3 scripts/philo_graph_reference.py --check; python3 scripts/philo_api_reference.py --check; python3 scripts/philo_boundary_census.py --check; python3 scripts/generate_capability_docs.py --check; test -z "$(git status --porcelain -- pm/roadmap/holdspeak/)"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4748a9e2f3938928aa6e798514a49c91d864aea7

```text
tests/unit/test_api_surface.py::test_committed_manifest_matches_the_live_app
tests/unit/test_api_surface.py::test_committed_markdown_matches_the_manifest
tests/unit/test_api_surface.py::test_clients_only_call_served_routes
tests/unit/test_api_surface.py::test_manifest_is_not_vacuous
tests/unit/test_api_surface.py::test_extractors_see_the_real_call_sites
tests/unit/test_api_surface.py::test_committed_openapi_matches_reference_app
tests/unit/test_philo_architecture.py::test_valid_metadata_resolves_python_symbols_and_test_nodes
tests/unit/test_philo_architecture.py::test_invalid_metadata_reports_path_node_enum_and_egress
tests/unit/test_philo_architecture.py::test_duplicate_ids_and_snapshot_drift_are_errors
tests/unit/test_philo_architecture.py::test_generation_and_coverage_are_deterministic_and_do_not_promote_paths
tests/unit/test_philo_architecture.py::test_typescript_token_and_test_title_fallback_is_static
tests/unit/test_philo_architecture.py::test_coverage_requires_assertion_and_execution_on_same_test
tests/unit/test_philo_architecture.py::test_explicit_api_reference_checks_method_and_route
tests/unit/test_philo_architecture.py::test_requirement_catalogue_checks_its_own_source_references
tests/unit/test_philo_architecture.py::test_existing_build_copy_is_not_source_evidence

15 tests collected in 0.16s
...............                                                          [100%]
15 passed in 2.32s
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
API reference checked
Boundary candidate census checked
Architecture documentation checked (10 outputs).
```

### Captured run — 2026-09-25T03:32:01Z

- **Command:** `bash -c set -euo pipefail; export HOME=$(mktemp -d); export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; cd web; npm exec -- vitest run src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx --maxWorkers=1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4748a9e2f3938928aa6e798514a49c91d864aea7

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-6-b/web


 Test Files  1 passed (1)
      Tests  7 passed (7)
   Start at  21:32:01
   Duration  1.51s (transform 608ms, setup 56ms, import 870ms, tests 344ms, environment 164ms)

npm notice
npm notice New minor version of npm available! 11.6.2 -> 11.20.0
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.20.0
npm notice To update run: npm install -g npm@11.20.0
npm notice
```
