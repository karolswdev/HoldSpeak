# Parked history tests

Reads evidence archived on branch archive/evidence-2026-10-04 (see `pm/ARCHIVE.md`).

Each file here is the whole test file as it was on 2026-10-04, at its old
path under this directory. The live file in `tests/unit/` keeps every test
that does not read archived evidence. Nothing here runs
(`tests/_parked/conftest.py` stops collection).

To run one again: put its evidence back
(`git checkout archive/evidence-2026-10-04 -- <path>`), then move the test
functions back to the live file.

## Parked test functions (80, in 6 files)

- `tests/unit/test_philo10_atlas.py` :: `test_every_claimed_run_keeps_its_own_observation`
- `tests/unit/test_philo10_send_job.py` :: `test_a_file_that_does_not_read_back_is_red`
- `tests/unit/test_philo10_send_job.py` :: `test_a_fixture_written_after_the_first_session_is_red`
- `tests/unit/test_philo10_send_job.py` :: `test_a_planted_gh_token_is_red`
- `tests/unit/test_philo10_send_job.py` :: `test_a_resumed_or_shared_session_is_red`
- `tests/unit/test_philo10_send_job.py` :: `test_a_send_prepared_by_the_owner_is_red`
- `tests/unit/test_philo10_send_job.py` :: `test_an_agent_send_that_succeeded_is_red`
- `tests/unit/test_philo10_send_job.py` :: `test_an_extra_newline_on_the_far_side_is_red`
- `tests/unit/test_philo10_send_job.py` :: `test_every_retained_session_has_zero_reads_and_used_the_catalogue`
- `tests/unit/test_philo10_send_job.py` :: `test_the_agent_prepared_both_and_its_send_was_refused_with_a_receipt`
- `tests/unit/test_philo10_send_job.py` :: `test_the_face_showed_prepared_then_sent_at_both_widths`
- `tests/unit/test_philo10_send_job.py` :: `test_the_owners_press_sent_both_and_the_far_side_reads_back_the_frozen_bytes`
- `tests/unit/test_philo10_send_job.py` :: `test_the_prepared_row_reshoot_shows_heading_attribution_and_send_on_screen`
- `tests/unit/test_philo10_send_job.py` :: `test_the_retained_run_holds_no_account_data_or_gh_credential`
- `tests/unit/test_philo10_send_job.py` :: `test_the_sessions_are_isolated_and_the_fixture_came_first`
- `tests/unit/test_philo10_send_job.py` :: `test_the_tracked_ledger_names_both_real_sends_with_the_final_runs_proofs`
- `tests/unit/test_philo5_his_words.py` :: `test_retained_decision_turn_reconciles_whole`
- `tests/unit/test_philo7_file_and_find.py` :: `test_a_codex_read_of_a_repo_doc_resource_is_a_finding`
- `tests/unit/test_philo7_file_and_find.py` :: `test_a_fresh_cold_root_passes_with_the_retained_codex_config`
- `tests/unit/test_philo7_file_and_find.py` :: `test_a_repository_pointer_in_the_initial_context_is_red`
- `tests/unit/test_philo7_file_and_find.py` :: `test_a_thin_or_misplaced_reason_turns_the_check_red`
- `tests/unit/test_philo7_file_and_find.py` :: `test_a_turn_whose_only_actions_are_mcp_calls_passes`
- `tests/unit/test_philo7_file_and_find.py` :: `test_a_working_root_inside_the_repository_is_red`
- `tests/unit/test_philo7_file_and_find.py` :: `test_an_init_mutation_turns_the_check_red`
- `tests/unit/test_philo7_file_and_find.py` :: `test_an_instruction_in_the_initial_context_is_red`
- `tests/unit/test_philo7_file_and_find.py` :: `test_any_other_action_turns_the_fence_red`
- `tests/unit/test_philo7_file_and_find.py` :: `test_any_other_claude_tool_turns_the_fence_red`
- `tests/unit/test_philo7_file_and_find.py` :: `test_codex_sent_the_desk_bearer_from_the_cold_config`
- `tests/unit/test_philo7_file_and_find.py` :: `test_each_launch_mutation_turns_the_check_red`
- `tests/unit/test_philo7_file_and_find.py` :: `test_every_chosen_holdspeak_tool_is_in_the_init_tool_list`
- `tests/unit/test_philo7_file_and_find.py` :: `test_every_chosen_tool_is_in_the_sessions_tools_list`
- `tests/unit/test_philo7_file_and_find.py` :: `test_every_closing_session_has_zero_findings_and_used_holdspeak`
- `tests/unit/test_philo7_file_and_find.py` :: `test_every_record_states_the_claim_verbatim_and_no_forbidden_wording`
- `tests/unit/test_philo7_file_and_find.py` :: `test_no_retained_story04_record_holds_an_email_or_a_token`
- `tests/unit/test_philo7_file_and_find.py` :: `test_the_claude_pairing_pairs_every_call_and_refuses_a_changed_answer`
- `tests/unit/test_philo7_file_and_find.py` :: `test_the_claude_zero_read_fence_fails_on_a_real_claude_read_of_the_repository`
- `tests/unit/test_philo7_file_and_find.py` :: `test_the_closing_agent_leg_receipts_pass_the_check`
- `tests/unit/test_philo7_file_and_find.py` :: `test_the_closing_decision_carries_its_reason_read_back_durably`
- `tests/unit/test_philo7_file_and_find.py` :: `test_the_cold_sessions_pair_their_handshake`
- `tests/unit/test_philo7_file_and_find.py` :: `test_the_cold_sessions_received_the_catalogue`
- `tests/unit/test_philo7_file_and_find.py` :: `test_the_combined_fence_still_fails_on_the_phase5_codex_logs`
- `tests/unit/test_philo7_file_and_find.py` :: `test_the_init_events_show_the_one_server_and_no_api_key`
- `tests/unit/test_philo7_file_and_find.py` :: `test_the_initial_context_loaded_no_instructions`
- `tests/unit/test_philo7_file_and_find.py` :: `test_the_leak_fence_turns_red_on_a_planted_value`
- `tests/unit/test_philo7_file_and_find.py` :: `test_the_owner_shots_come_before_the_agent_files_and_show_the_reason`
- `tests/unit/test_philo7_file_and_find.py` :: `test_the_pairing_audit_pairs_every_call_and_refuses_a_changed_answer`
- `tests/unit/test_philo7_file_and_find.py` :: `test_the_phase5_run_counts_28_repository_commands_in_all`
- `tests/unit/test_philo7_file_and_find.py` :: `test_the_reason_check_is_red_on_the_thin_decision_the_owner_reviewed`
- `tests/unit/test_philo7_file_and_find.py` :: `test_the_redaction_keeps_tools_and_servers_and_drops_the_account`
- `tests/unit/test_philo7_file_and_find.py` :: `test_the_retained_claude_launch_setups_were_lawful`
- `tests/unit/test_philo7_file_and_find.py` :: `test_the_retained_cold_sessions_have_zero_findings`
- `tests/unit/test_philo7_file_and_find.py` :: `test_the_retained_initial_context_holds_no_repository_pointer`
- `tests/unit/test_philo7_file_and_find.py` :: `test_the_retained_launch_setups_were_lawful`
- `tests/unit/test_philo7_file_and_find.py` :: `test_the_zero_read_fence_fails_on_the_phase5_logs`
- `tests/unit/test_philo9_atlas.py` :: `test_every_claimed_run_keeps_its_own_observation`
- `tests/unit/test_philo9_room_job.py` :: `test_a_changed_fixture_value_or_changed_words_are_red`
- `tests/unit/test_philo9_room_job.py` :: `test_a_fixture_written_after_the_first_session_is_red`
- `tests/unit/test_philo9_room_job.py` :: `test_a_missing_or_extra_owner_write_is_red`
- `tests/unit/test_philo9_room_job.py` :: `test_a_refused_call_without_the_failed_status_does_not_pair`
- `tests/unit/test_philo9_room_job.py` :: `test_a_shell_command_in_a_retained_session_turns_the_fence_red`
- `tests/unit/test_philo9_room_job.py` :: `test_each_content_mutation_is_red`
- `tests/unit/test_philo9_room_job.py` :: `test_each_face_mutation_is_red`
- `tests/unit/test_philo9_room_job.py` :: `test_each_isolation_mutation_is_red`
- `tests/unit/test_philo9_room_job.py` :: `test_every_client_call_pairs_with_one_hub_exchange_from_the_retained_records`
- `tests/unit/test_philo9_room_job.py` :: `test_every_face_shot_is_retained`
- `tests/unit/test_philo9_room_job.py` :: `test_every_retained_session_has_zero_reads_and_used_the_catalogue`
- `tests/unit/test_philo9_room_job.py` :: `test_find_it_cold_took_project_list_after_the_discovery_repair`
- `tests/unit/test_philo9_room_job.py` :: `test_no_retained_story06_record_holds_an_email_or_a_token`
- `tests/unit/test_philo9_room_job.py` :: `test_the_agent_heard_owner_only_for_mark_delivered_after_the_repair`
- `tests/unit/test_philo9_room_job.py` :: `test_the_agent_leg_refused_then_ran_inside_the_bound`
- `tests/unit/test_philo9_room_job.py` :: `test_the_final_run_is_complete_and_labelled_for_the_owners_review`
- `tests/unit/test_philo9_room_job.py` :: `test_the_fixture_was_in_the_run_before_the_first_session`
- `tests/unit/test_philo9_room_job.py` :: `test_the_grant_row_keeps_stop_on_the_archived_project_and_its_receipt`
- `tests/unit/test_philo9_room_job.py` :: `test_the_leak_fence_turns_red_on_a_planted_value`
- `tests/unit/test_philo9_room_job.py` :: `test_the_owner_job_reads_back_every_fixture_value`
- `tests/unit/test_philo9_room_job.py` :: `test_the_redaction_at_capture_removes_a_planted_address`
- `tests/unit/test_philo9_room_job.py` :: `test_the_retained_sessions_are_isolated`
- `tests/unit/test_philo9_room_job.py` :: `test_the_room_face_shows_every_fixture_value_at_both_widths`
- `tests/unit/test_philo9_room_job.py` :: `test_the_superseded_393_items_shot_was_the_head_shot`
- `tests/unit/test_philo9_room_job.py` :: `test_the_zero_read_fence_fails_on_the_phase5_logs`
