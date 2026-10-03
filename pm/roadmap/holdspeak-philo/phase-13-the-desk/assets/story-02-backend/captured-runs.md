> DRAFT capture archive. The generated `Status: done` header below is a DW template default, not a story certification. PHILO-13-02 remains in-progress pending A1-F and Muad'Dib.

# Evidence - PHILO-13-02

- **Story:** PHILO-13-02 - A1 — Park, never delete
- **Status:** done
- **Date:** 2026-10-01

## Proof

### Captured run — 2026-10-02T03:31:12Z

- **Command:** `python3 .tmp/philo-13-astra/test-a1.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2ddb6b6f96f087f64a9d47d5871b02915b1e2914

```text
COMMAND uv run pytest --collect-only -q tests/unit/test_philo13_meeting_parking.py tests/unit/test_philo13_workbench_parking.py tests/unit/test_db_schema_policy.py tests/unit/test_reconcile.py tests/unit/test_db.py::TestDatabase tests/unit/test_db.py::TestTranscriptSearch tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot tests/unit/test_phase200_meeting_outcomes.py tests/unit/test_phase143_meeting_route_primitives.py tests/unit/test_meeting_import.py tests/unit/test_project_projection_services.py tests/unit/test_desk_projections.py tests/unit/test_mcp_tools.py tests/unit/test_thought_workbench_backend.py tests/unit/test_workbench_triage.py tests/unit/test_workbench_triage_kernel.py tests/unit/test_workbench_runner_migration.py tests/integration/test_phase143_workbench_route_adoption.py tests/unit/test_api_surface.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo13_astra_atlas.py
tests/unit/test_philo13_meeting_parking.py::test_repository_parks_and_restores_without_deleting_retained_work
tests/unit/test_philo13_meeting_parking.py::test_repository_park_and_restore_are_idempotent_and_unknown_stays_missing
tests/unit/test_philo13_meeting_parking.py::test_save_does_not_accidentally_unpark_a_retained_meeting
tests/unit/test_philo13_meeting_parking.py::test_service_parked_search_reads_only_the_retained_meeting
tests/unit/test_philo13_meeting_parking.py::test_parked_meeting_proposal_refusal_tells_owner_to_restore
tests/unit/test_philo13_meeting_parking.py::test_mcp_delete_verbs_return_parked_receipts_and_retain_rows
tests/unit/test_philo13_meeting_parking.py::test_real_import_route_parks_reads_retained_detail_and_restores
tests/unit/test_philo13_meeting_parking.py::test_schema_reconciles_parked_columns_additively
tests/unit/test_philo13_workbench_parking.py::test_park_hides_item_but_reopens_the_same_row_and_links
tests/unit/test_philo13_workbench_parking.py::test_normal_delete_verb_retains_real_result_and_run_links
tests/unit/test_philo13_workbench_parking.py::test_bulk_park_claimed_item_refuses_without_partial_change
tests/unit/test_philo13_workbench_parking.py::test_upsert_keeps_a_parked_item_parked
tests/unit/test_philo13_workbench_parking.py::test_workbench_payload_selects_parked_items_only_when_requested
tests/unit/test_philo13_workbench_parking.py::test_production_routes_park_bulk_reload_and_restore
tests/unit/test_philo13_workbench_parking.py::test_legacy_repository_delete_parks_and_repeats_are_idempotent
tests/unit/test_philo13_workbench_parking.py::test_runner_never_claims_a_parked_pending_item
tests/unit/test_philo13_workbench_parking.py::test_runner_skips_item_parked_after_pending_snapshot
tests/unit/test_db_schema_policy.py::test_fresh_db_is_created_at_current_version
tests/unit/test_db_schema_policy.py::test_reconcile_is_noop_on_current_db
tests/unit/test_db_schema_policy.py::test_newer_stamped_db_opens_without_error
tests/unit/test_db_schema_policy.py::test_missing_table_self_heals
tests/unit/test_db_schema_policy.py::test_missing_column_self_heals
tests/unit/test_db_schema_policy.py::test_orphan_table_and_rows_survive
tests/unit/test_db_schema_policy.py::test_v8_db_gains_model_manifests_via_reconcile
tests/unit/test_db_schema_policy.py::test_backup_database_copies_to_timestamped_sibling
tests/unit/test_db_schema_policy.py::test_backup_database_does_not_clobber
tests/unit/test_db_schema_policy.py::test_upgrade_adds_the_profiles_node_column
tests/unit/test_reconcile.py::test_reconcile_recreates_dropped_table
tests/unit/test_reconcile.py::test_reconcile_adds_provider_command_table_to_old_shape_without_touching_rows
tests/unit/test_reconcile.py::test_reconcile_adds_calendar_events_to_old_shape_without_touching_rows
tests/unit/test_reconcile.py::test_reconcile_adds_missing_column
tests/unit/test_reconcile.py::test_reconcile_adds_datetime_default_column_with_constant
tests/unit/test_reconcile.py::test_reconcile_is_idempotent
tests/unit/test_reconcile.py::test_reconcile_no_alter_on_current_db
tests/unit/test_reconcile.py::test_reconcile_widens_historical_parent_kind_check_without_row_loss
tests/unit/test_reconcile.py::test_reconcile_preserves_orphan_table
tests/unit/test_reconcile.py::test_newer_db_opens_without_error
tests/unit/test_reconcile.py::test_newer_db_opens_via_database_class
tests/unit/test_reconcile.py::test_reference_schema_contains_canonical_tables
tests/unit/test_reconcile.py::test_is_function_default_detects_datetime
tests/unit/test_reconcile.py::test_soft_deleted_decision_survives_reconcile
tests/unit/test_reconcile.py::test_clean_db_reconcile_skips_backfills
tests/unit/test_reconcile.py::test_shape_change_triggers_backup_and_backfills
tests/unit/test_reconcile.py::test_fresh_creation_does_not_back_up
tests/unit/test_reconcile.py::test_fts_shadow_tables_excluded_from_reference
tests/unit/test_reconcile.py::test_reconcile_adds_source_columns_to_existing_calendar_events
tests/unit/test_reconcile.py::test_fts_shadow_tables_not_altered
tests/unit/test_db.py::TestDatabase::test_init_creates_schema
tests/unit/test_db.py::TestDatabase::test_save_and_get_meeting
tests/unit/test_db.py::TestDatabase::test_save_meeting_with_intel
tests/unit/test_db.py::TestDatabase::test_get_nonexistent_meeting
tests/unit/test_db.py::TestDatabase::test_list_meetings
tests/unit/test_db.py::TestDatabase::test_list_meetings_with_limit
tests/unit/test_db.py::TestDatabase::test_list_meetings_date_filter
tests/unit/test_db.py::TestDatabase::test_delete_meeting
tests/unit/test_db.py::TestDatabase::test_delete_nonexistent_meeting
tests/unit/test_db.py::TestDatabase::test_get_meeting_count
tests/unit/test_db.py::TestTranscriptSearch::test_search_transcripts
tests/unit/test_db.py::TestTranscriptSearch::test_search_transcripts_no_results
tests/unit/test_db.py::TestTranscriptSearch::test_search_transcripts_multiple_results
tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot
tests/unit/test_phase200_meeting_outcomes.py::test_a_real_run_produces_proposals_through_the_drainer_and_the_bridge
tests/unit/test_phase200_meeting_outcomes.py::test_confirm_preserves_meeting_span_and_extraction_provenance
tests/unit/test_phase200_meeting_outcomes.py::test_an_unknown_owner_or_due_stays_unknown_until_the_owner_supplies_it
tests/unit/test_phase200_meeting_outcomes.py::test_edit_in_place_drops_support_keeps_the_record_and_confirm_returns_the_ids
tests/unit/test_phase200_meeting_outcomes.py::test_dismiss_returns_the_durable_state_and_writes_no_record
tests/unit/test_phase200_meeting_outcomes.py::test_a_repeated_completion_mints_no_duplicate_proposal
tests/unit/test_phase200_meeting_outcomes.py::test_a_model_retry_mints_no_duplicate_proposal_or_commitment
tests/unit/test_phase200_meeting_outcomes.py::test_a_lost_acknowledgement_replays_the_same_durable_result
tests/unit/test_phase200_meeting_outcomes.py::test_seeded_repeated_completion_after_a_confirm_mints_no_duplicate
tests/unit/test_phase200_meeting_outcomes.py::test_seeded_lost_acknowledgement_replays_the_same_result
tests/unit/test_phase200_meeting_outcomes.py::test_accept_reviewed_confirms_only_supported_rows_without_unknowns
tests/unit/test_phase200_meeting_outcomes.py::test_a_changed_transcript_proposes_again_beside_the_earlier_decisions
tests/unit/test_phase200_meeting_outcomes.py::test_supplied_owner_and_due_are_distinguishable_from_extracted
tests/unit/test_phase200_meeting_outcomes.py::test_confirm_after_the_meeting_was_deleted_is_a_named_refusal
tests/unit/test_phase200_meeting_outcomes.py::test_a_liveness_tick_racing_the_claim_does_not_refuse_the_bound_executor
tests/unit/test_phase200_meeting_outcomes.py::test_an_unpersisted_parent_shell_is_an_orphan_only_after_a_lease
tests/unit/test_phase143_meeting_route_primitives.py::test_corrected_results_are_semantic_only_and_unchanged_contracts_keep_revision
tests/unit/test_phase143_meeting_route_primitives.py::test_semantic_adapters_validate_before_returning_attempt_output
tests/unit/test_phase143_meeting_route_primitives.py::test_historical_text_adapter_keeps_v1_shape_without_reinterpreting_as_v2
tests/unit/test_phase143_meeting_route_primitives.py::test_preupgrade_frozen_route_binds_after_registry_upgrade
tests/unit/test_phase143_meeting_route_primitives.py::test_current_route_projection_uses_its_identical_frozen_definition
tests/unit/test_phase143_meeting_route_primitives.py::test_service_route_policy_never_inherits_owner_global_or_group
tests/unit/test_phase143_meeting_route_primitives.py::test_parent_route_bundle_is_atomic_replay_safe_and_budget_exact
tests/unit/test_phase143_meeting_route_primitives.py::test_aggregate_bundle_budget_debits_once_and_refuses_overallocation
tests/unit/test_phase143_meeting_route_primitives.py::test_aggregate_bundle_manifest_tamper_refuses_reconstruction
tests/unit/test_phase143_meeting_route_primitives.py::test_bundle_rollback_terminalizes_shell_and_leaves_no_partial_route
tests/unit/test_phase143_meeting_route_primitives.py::test_bundle_reconstruction_rejects_principal_evidence_tamper
tests/unit/test_phase143_meeting_route_primitives.py::test_stop_handoff_derives_complete_route_set_and_replays_durable_effect
tests/unit/test_phase143_meeting_route_primitives.py::test_stop_handoff_unknown_dispatch_keeps_displaced_work_reserved_after_delayed_egress
tests/unit/test_phase143_meeting_route_primitives.py::test_stop_handoff_known_terminal_settles_activates_and_runs_once
tests/unit/test_phase143_meeting_route_primitives.py::test_handoff_freeze_active_unwritten_or_exception_rolls_back
tests/unit/test_phase143_meeting_route_primitives.py::test_handoff_settlement_activation_faults_roll_back_together
tests/unit/test_phase143_meeting_route_primitives.py::test_handoff_concurrent_reconcile_and_dispatch_claim_are_exactly_once
tests/unit/test_phase143_meeting_route_primitives.py::test_handoff_independent_lifecycle_witness_refuses_both_mismatch_directions
tests/unit/test_phase143_meeting_route_primitives.py::test_bundle_execution_seal_refuses_late_admission_without_partial_rows
tests/unit/test_phase143_meeting_route_primitives.py::test_bundle_execution_seal_refuses_after_terminal_parent
tests/unit/test_phase143_meeting_route_primitives.py::test_bundle_execution_seal_preserves_open_and_nonbundled_admission
tests/unit/test_phase143_meeting_route_primitives.py::test_handoff_settlement_and_stop_provenance_tamper_refuse
tests/unit/test_phase143_meeting_route_primitives.py::test_new_route_and_handoff_tables_are_hostile_sync_refused[inference_route_plan_principal_evidence]
tests/unit/test_phase143_meeting_route_primitives.py::test_new_route_and_handoff_tables_are_hostile_sync_refused[inference_parent_route_bundles]
tests/unit/test_phase143_meeting_route_primitives.py::test_new_route_and_handoff_tables_are_hostile_sync_refused[inference_parent_route_bundle_members]
tests/unit/test_phase143_meeting_route_primitives.py::test_new_route_and_handoff_tables_are_hostile_sync_refused[inference_parent_stop_handoffs]
tests/unit/test_phase143_meeting_route_primitives.py::test_new_route_and_handoff_tables_are_hostile_sync_refused[inference_parent_stop_handoff_executions]
tests/unit/test_phase143_meeting_route_primitives.py::test_new_route_and_handoff_tables_are_hostile_sync_refused[inference_parent_stop_handoff_settlements]
tests/unit/test_phase143_meeting_route_primitives.py::test_bundle_uses_exact_nondefault_assignment_budget_before_shell_admission
tests/unit/test_phase143_meeting_route_primitives.py::test_bundle_refuses_assignment_policy_race_after_honest_shell_admission
tests/unit/test_phase143_meeting_route_primitives.py::test_bundle_refuses_equal_total_per_route_policy_swap
tests/unit/test_phase143_meeting_route_primitives.py::test_stop_handoff_known_inflight_receipt_settles_then_activates_once
tests/unit/test_phase143_meeting_route_primitives.py::test_handoff_effect_reference_hash_and_provider_revision_tamper_refuse[effect_sha256]
tests/unit/test_phase143_meeting_route_primitives.py::test_handoff_effect_reference_hash_and_provider_revision_tamper_refuse[evidence_ref]
tests/unit/test_phase143_meeting_route_primitives.py::test_handoff_effect_reference_hash_and_provider_revision_tamper_refuse[evidence_sha256]
tests/unit/test_phase143_meeting_route_primitives.py::test_handoff_effect_reference_hash_and_provider_revision_tamper_refuse[evidence_provider_revision]
tests/unit/test_meeting_import.py::test_happy_path_windows_timestamps_and_persistence
tests/unit/test_meeting_import.py::test_stereo_44k_is_downmixed_and_resampled_before_transcription
tests/unit/test_meeting_import.py::test_empty_windows_are_skipped_and_all_empty_refuses
tests/unit/test_meeting_import.py::test_compressed_without_ffmpeg_is_refused_honestly
tests/unit/test_meeting_import.py::test_compressed_with_ffmpeg_decodes_via_ffmpeg
tests/unit/test_meeting_import.py::test_unsupported_format_is_refused
tests/unit/test_meeting_import.py::test_intel_disabled_means_no_job_and_honest_status
tests/unit/test_meeting_import.py::test_missing_file_and_speaker_label_override
tests/unit/test_meeting_import.py::test_import_command_exits_nonzero_on_unsupported_format
tests/unit/test_project_projection_services.py::test_project_service_preserves_archive_relationship_and_meeting_validation
tests/unit/test_project_projection_services.py::test_project_service_validates_mutable_fields_and_projects_exist
tests/unit/test_project_projection_services.py::test_projection_service_validates_filters_and_persists_presentation
tests/unit/test_desk_projections.py::test_projection_index_covers_subjects_without_copying_sensitive_payloads
tests/unit/test_desk_projections.py::test_dismiss_and_acknowledge_change_projection_only
tests/unit/test_desk_projections.py::test_subject_badges_do_not_follow_drawer_filters
tests/unit/test_desk_projections.py::test_projection_pagination_has_no_silent_truncation
tests/unit/test_mcp_tools.py::test_tools_list_exposes_pipeline_mcp_tools_with_closed_schemas
tests/unit/test_mcp_tools.py::test_retired_router_tools_are_absent_from_the_catalogue
tests/unit/test_mcp_tools.py::test_retired_shapes_refuse_before_mcp_dispatch
tests/unit/test_mcp_tools.py::test_pipeline_tools_dispatch_through_mcp_protocol
tests/unit/test_thought_workbench_backend.py::test_projection_is_zero_write_coherent_and_placement_is_historical
tests/unit/test_thought_workbench_backend.py::test_unavailable_ai_projects_direct_configuration_recovery
tests/unit/test_thought_workbench_backend.py::test_cursor_forgery_refuses_before_mutation_and_legacy_absence_survives
tests/unit/test_thought_workbench_backend.py::test_atomic_answer_continue_replays_effect_and_child_with_fresh_cursor
tests/unit/test_thought_workbench_backend.py::test_composite_empty_answer_and_unready_admission_refuse_without_append
tests/unit/test_thought_workbench_backend.py::test_catalogue_has_eighteen_tools_and_workbench_original_resources
tests/unit/test_thought_workbench_backend.py::test_add_to_note_persists_exact_append_effect_and_replays_original_hub[-Mina]
tests/unit/test_thought_workbench_backend.py::test_add_to_note_persists_exact_append_effect_and_replays_original_hub[Launch ownership-M\xefna \U0001f680]
tests/unit/test_thought_workbench_backend.py::test_add_to_note_replay_rejects_forged_effect_even_with_rehashed_json
tests/unit/test_thought_workbench_backend.py::test_composite_replay_rejects_repointed_valid_action_and_child
tests/unit/test_thought_workbench_backend.py::test_historical_placement_is_closed_and_malformed_combined_proof_is_unavailable[<lambda>0]
tests/unit/test_thought_workbench_backend.py::test_historical_placement_is_closed_and_malformed_combined_proof_is_unavailable[<lambda>1]
tests/unit/test_thought_workbench_backend.py::test_historical_placement_is_closed_and_malformed_combined_proof_is_unavailable[<lambda>2]
tests/unit/test_thought_workbench_backend.py::test_historical_placement_is_closed_and_malformed_combined_proof_is_unavailable[<lambda>3]
tests/unit/test_thought_workbench_backend.py::test_historical_placement_is_closed_and_malformed_combined_proof_is_unavailable[<lambda>4]
tests/unit/test_thought_workbench_backend.py::test_terminal_reducer_is_closed_and_scheduler_loss_is_retryable[owner_answered-owner_terminal-False]
tests/unit/test_thought_workbench_backend.py::test_terminal_reducer_is_closed_and_scheduler_loss_is_retryable[thought_completed-owner_terminal-False]
tests/unit/test_thought_workbench_backend.py::test_terminal_reducer_is_closed_and_scheduler_loss_is_retryable[scheduler_lost_before_dispatch-retryable-True]
tests/unit/test_thought_workbench_backend.py::test_terminal_reducer_is_closed_and_scheduler_loss_is_retryable[provider_unavailable-retryable-True]
tests/unit/test_thought_workbench_backend.py::test_terminal_reducer_is_closed_and_scheduler_loss_is_retryable[restart_bound_outcome_unknown-indeterminate-False]
tests/unit/test_thought_workbench_backend.py::test_terminal_reducer_is_closed_and_scheduler_loss_is_retryable[ask_result_unpublished-indeterminate-False]
tests/unit/test_thought_workbench_backend.py::test_terminal_reducer_is_closed_and_scheduler_loss_is_retryable[refinement_result_invalid-integrity-False]
tests/unit/test_thought_workbench_backend.py::test_terminal_reducer_is_closed_and_scheduler_loss_is_retryable[unknown_terminal_code-integrity-False]
tests/unit/test_thought_workbench_backend.py::test_terminal_write_sites_and_dynamic_ingress_use_the_closed_vocabulary
tests/unit/test_thought_workbench_backend.py::test_duplicate_dispatch_and_cancellation_callbacks_are_continuity_noops
tests/unit/test_thought_workbench_backend.py::test_continuation_refusal_returns_fresh_workbench_without_answer_leak
tests/unit/test_thought_workbench_backend.py::test_dispatch_hook_refuses_replaced_host_epoch_for_initial_and_composite_child
tests/unit/test_thought_workbench_backend.py::test_default_same_id_readiness_change_refuses_initial_and_composite_before_writes
tests/unit/test_thought_workbench_backend.py::test_process_only_cursor_race_returns_fresh_workbench_and_one_cas_retry_saves_draft
tests/unit/test_thought_workbench_backend.py::test_missing_local_model_path_refuses_initial_and_composite_with_fresh_workbench_zero_writes[None]
tests/unit/test_thought_workbench_backend.py::test_missing_local_model_path_refuses_initial_and_composite_with_fresh_workbench_zero_writes[/definitely/missing/holdspeak-model.gguf]
tests/unit/test_workbench_triage.py::TestWorkbenchTriageCodec::test_parse_valid_accept
tests/unit/test_workbench_triage.py::TestWorkbenchTriageCodec::test_parse_valid_reject
tests/unit/test_workbench_triage.py::TestWorkbenchTriageCodec::test_parse_valid_rework
tests/unit/test_workbench_triage.py::TestWorkbenchTriageCodec::test_parse_invalid_action
tests/unit/test_workbench_triage.py::TestWorkbenchTriageCodec::test_parse_missing_fields
tests/unit/test_workbench_triage.py::TestTriageAcceptDB::test_accept_changes_artifact_to_draft
tests/unit/test_workbench_triage.py::TestTriageAcceptDB::test_accepted_artifact_visible_in_run_list
tests/unit/test_workbench_triage.py::TestTriageRejectDB::test_reject_archives_artifact_and_dismisses_item
tests/unit/test_workbench_triage.py::TestTriageRejectDB::test_rejected_artifact_hidden_from_run_list
tests/unit/test_workbench_triage.py::TestTriageRejectDB::test_rejected_artifact_still_in_db
tests/unit/test_workbench_triage.py::TestTriageReworkDB::test_rework_resets_item_to_pending
tests/unit/test_workbench_triage.py::TestTriageReworkDB::test_rework_cycle_allows_new_triage
tests/unit/test_workbench_triage.py::TestDoubleTriage::test_double_accept_fails
tests/unit/test_workbench_triage.py::TestTriageWithoutArtifact::test_no_artifact_id
tests/unit/test_workbench_triage_kernel.py::test_workbench_triage_codec_registered
tests/unit/test_workbench_triage_kernel.py::test_triage_parse_accept
tests/unit/test_workbench_triage_kernel.py::test_triage_parse_reject
tests/unit/test_workbench_triage_kernel.py::test_triage_parse_rework
tests/unit/test_workbench_triage_kernel.py::test_triage_parse_rejects_invalid_action
tests/unit/tes
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-10-02T03:32:58Z

- **Command:** `python3 .tmp/philo-13-astra/test-a1.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2ddb6b6f96f087f64a9d47d5871b02915b1e2914

```text
COMMAND uv run pytest --collect-only -q tests/unit/test_philo13_meeting_parking.py tests/unit/test_philo13_workbench_parking.py tests/unit/test_db_schema_policy.py tests/unit/test_reconcile.py tests/unit/test_db.py::TestDatabase tests/unit/test_db.py::TestTranscriptSearch tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot tests/unit/test_phase200_meeting_outcomes.py tests/unit/test_phase143_meeting_route_primitives.py tests/unit/test_meeting_import.py tests/unit/test_project_projection_services.py tests/unit/test_desk_projections.py tests/unit/test_mcp_tools.py tests/unit/test_thought_workbench_backend.py tests/unit/test_workbench_triage.py tests/unit/test_workbench_triage_kernel.py tests/unit/test_workbench_runner_migration.py tests/integration/test_phase143_workbench_route_adoption.py tests/unit/test_api_surface.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo13_astra_atlas.py
FULL OUTPUT .tmp/philo-13-astra/a1-final-collection.txt
plicable_case_carries_one_trigger]
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

334 tests collected in 1.88s

COMMAND uv run pytest -q tests/unit/test_philo13_meeting_parking.py tests/unit/test_philo13_workbench_parking.py tests/unit/test_db_schema_policy.py tests/unit/test_reconcile.py tests/unit/test_db.py::TestDatabase tests/unit/test_db.py::TestTranscriptSearch tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot tests/unit/test_phase200_meeting_outcomes.py tests/unit/test_phase143_meeting_route_primitives.py tests/unit/test_meeting_import.py tests/unit/test_project_projection_services.py tests/unit/test_desk_projections.py tests/unit/test_mcp_tools.py tests/unit/test_thought_workbench_backend.py tests/unit/test_workbench_triage.py tests/unit/test_workbench_triage_kernel.py tests/unit/test_workbench_runner_migration.py tests/integration/test_phase143_workbench_route_adoption.py tests/unit/test_api_surface.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo13_astra_atlas.py
FULL OUTPUT .tmp/philo-13-astra/a1-final-run.txt
........................................................................ [ 21%]
........................................................................ [ 43%]
........................................................................ [ 64%]
.....F....F............................................................. [ 86%]
...........................F..............F...                           [100%]
=================================== FAILURES ===================================
______ test_atlas_validates_against_its_schema[atlas-phase13-astra.json] _______

every_atlas = {'atlas_version': 'phase13-astra-wave1', 'cases': [{'applicability': 'applicable', 'completion_bound_s': 30, 'edge_ids... 'source': 'datetime.datetime.now() inside the hub process', 'status': 'available', ...}], 'council_readings': [], ...}
schema = {'$defs': {'case': {'additionalProperties': False, 'allOf': [{'if': {'properties': {...}, 'required': [...]}, 'then': ...raph/atlas.schema.json', '$schema': 'https://json-schema.org/draft/2020-12/schema', 'additionalProperties': False, ...}

    def test_atlas_validates_against_its_schema(every_atlas: dict, schema: dict) -> None:
        errors = sorted(
            Draft202012Validator(schema).iter_errors(every_atlas),
            key=lambda e: list(e.absolute_path),
        )
>       assert not errors, "\n".join(
            f"{'/'.join(str(p) for p in e.absolute_path)}: {e.message}" for e in errors[:20]
        )
E       AssertionError: cases/10/edge_ids/0: 'edge.http.delete.api_meetings_meeting_id' does not match '^edge\\.(face|route|timer|tool|cli)\\.[a-z0-9_]+$'
E         cases/10/setup/4: {'kind': 'api', 'method': 'DELETE', 'path': '/api/meetings/{meeting_id}', 'adapter': 'http-route', 'expect_status': 200} is not valid under any of the given schemas
E         cases/10/trigger: {'kind': 'api', 'method': 'POST', 'path': '/api/meetings/{meeting_id}/restore', 'adapter': 'http-route', 'expect_status': 200, 'then': [{'kind': 'ui', 'action': 'reload', 'adapter': 'ui-navigation'}]} is not valid under any of the given schemas
E         cases/11/edge_ids/0: 'edge.http.delete.api_workbenches_workbench_id_items_item_id' does not match '^edge\\.(face|route|timer|tool|cli)\\.[a-z0-9_]+$'
E         cases/11/setup/6: {'kind': 'api', 'method': 'DELETE', 'path': '/api/workbenches/{workbench_id}/items/{item_one}', 'adapter': 'http-route', 'expect_status': 200} is not valid under any of the given schemas
E         cases/11/setup/11: {'kind': 'api', 'method': 'POST', 'path': '/api/workbenches/{workbench_id}/items/{item_one}/restore', 'adapter': 'http-route', 'expect_status': 200} is not valid under any of the given schemas
E         cases/11/trigger: {'kind': 'api', 'method': 'POST', 'path': '/api/workbenches/{workbench_id}/items/restore', 'adapter': 'http-route', 'expect_status': 200, 'body': {'item_ids': ['{item_one}', '{item_two}']}, 'then': [{'kind': 'ui', 'action': 'reload', 'adapter': 'ui-navigation'}]} is not valid under any of the given schemas
E       assert not [<ValidationError: "'edge.http.delete.api_meetings_meeting_id' does not match '^edge\\\\.(face|route|timer|tool|cli)\\...{item_one}/restore', 'adapter': 'http-route', 'expect_status': 200} is not valid under any of the given schemas">, ...]

tests/unit/test_philo_graph_atlas.py:148: AssertionError
______ test_every_source_reference_lands_on_its_symbol[atlas-phase7.json] ______

every_atlas = {'atlas_version': 'phase7-desk', 'cases': [{'applicability': 'applicable', 'completion_bound_s': 45, 'edge_ids': ['edg... 'source': 'datetime.datetime.now() inside the hub process', 'status': 'available', ...}], 'council_readings': [], ...}

    def test_every_source_reference_lands_on_its_symbol(every_atlas: dict) -> None:
        """A line number is evidence, not identity (brief section 1).
    
        The cited line must still hold the cited symbol, or the reference has
        drifted and the claim behind it is no longer proven.
        """
        problems: list[str] = []
        for state in every_atlas["states"]:
            for ref in state["sources"]:
                target = REPO / ref["path"]
                if not target.is_file():
                    problems.append(f"{state['id']}: missing file {ref['path']}")
                    continue
                lines = target.read_text(errors="replace").splitlines()
                if not 1 <= ref["line"] <= len(lines):
                    problems.append(
                        f"{state['id']}: {ref['path']}:{ref['line']} is past the end of the file"
                    )
                    continue
                line = lines[ref["line"] - 1]
                if ref["symbol"] not in line:
                    problems.append(
                        f"{state['id']}: {ref['path']}:{ref['line']} no longer holds "
                        f"{ref['symbol']!r} (line reads {line.strip()[:80]!r})"
                    )
>       assert not problems, "\n".join(problems)
E       AssertionError: state.desk_presentation.p7_zone_membership: holdspeak/operations.py:1067 no longer holds 'name="zone.file"' (line reads '')
E         state.desk_presentation.p7_knowledge_membership: holdspeak/operations.py:1142 no longer holds 'name="kb.member.add"' (line reads '')
E         state.desk_presentation.p7_decision_lifecycle: holdspeak/operations.py:1232 no longer holds 'name="decision.status"' (line reads '')
E       assert not ['state.desk_presentation.p7_zone_membership: holdspeak/operations.py:1067 no longer holds \'name="zone.file"\' (line ...tion.p7_decision_lifecycle: holdspeak/operations.py:1232 no longer holds \'name="decision.status"\' (line reads \'\')']

tests/unit/test_philo_graph_atlas.py:279: AssertionError
_ test_phase13_atlas_keeps_the_shared_graph_fences[test_face_cases_carry_both_ruled_viewports] _

fence = <function test_face_cases_carry_both_ruled_viewports at 0x10ee2f110>

    @pytest.mark.parametrize("fence", GENERAL, ids=lambda fence: fence.__name__)
    def test_phase13_atlas_keeps_the_shared_graph_fences(fence) -> None:
>       fence(_atlas())

tests/unit/test_philo13_astra_atlas.py:71: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

atlas = {'atlas_version': 'phase13-astra-wave1', 'cases': [{'applicability': 'applicable', 'completion_bound_s': 30, 'edge_ids... 'source': 'datetime.datetime.now() inside the hub process', 'status': 'available', ...}], 'council_readings': [], ...}

    def test_face_cases_carry_both_ruled_viewports(atlas: dict) -> None:
        """Brief section 4: exercise each applicable face case at 1440 and 393.
    
        A case is a FACE case when its trigger is fired at the face or its
        observation location is a selector. Setup alone does not make one: a case
        observed at a route stays protocol-only even when its reproduction chain
        had to drive the desk to reach the starting state.
        """
        problems: list[str] = []
        for case in atlas["cases"]:
            if case["applicability"] != "applicable":
                continue
            where = case["expected"].get("observe_at") or ""
            if isinstance(where, dict) and where.get("kind") == "op":
                face = False
            else:
                face = (
                    case.get("trigger", {}).get("kind") == "ui"
                    or (bool(where) and not where.startswith("protocol:"))
                )
            want = [393, 1440] if face else []
            if sorted(case["viewports"]) != want:
                problems.append(
                    f"{case['id']}: {'face' if face else 'protocol-only'} case with "
                    f"viewports {case['viewports']}"
                )
>       assert not problems, problems
E       AssertionError: ['case.p13.meeting.park_restore: protocol-only case with viewports [1440, 393]', 'case.p13.workbench.park_restore: protocol-only case with viewports [1440, 393]']
E       assert not ['case.p13.meeting.park_restore: protocol-only case with viewports [1440, 393]', 'case.p13.workbench.park_restore: protocol-only case with viewports [1440, 393]']

tests/unit/test_philo_graph_atlas.py:380: AssertionError
___________ test_phase13_atlas_validates_against_schema_and_openapi ____________

    def test_phase13_atlas_validates_against_schema_and_openapi() -> None:
        atlas = _atlas()
        schema = json.loads(general.SCHEMA_PATH.read_text())
>       general.test_atlas_validates_against_its_schema(atlas, schema)

tests/unit/test_philo13_astra_atlas.py:77: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

every_atlas = {'atlas_version': 'phase13-astra-wave1', 'cases': [{'applicability': 'applicable', 'completion_bound_s': 30, 'edge_ids... 'source': 'datetime.datetime.now() inside the hub process', 'status': 'available', ...}], 'council_readings': [], ...}
schema = {'$defs': {'case': {'additionalProperties': False, 'allOf': [{'if': {'properties': {...}, 'required': [...]}, 'then': ...raph/atlas.schema.json', '$schema': 'https://json-schema.org/draft/2020-12/schema', 'additionalProperties': False, ...}

    def test_atlas_validates_against_its_schema(every_atlas: dict, schema: dict) -> None:
        errors = sorted(
            Draft202012Validator(schema).iter_errors(every_atlas),
            key=lambda e: list(e.absolute_path),
        )
>       assert not errors, "\n".join(
            f"{'/'.join(str(p) for p in e.absolute_path)}: {e.message}" for e in errors[:20]
        )
E       AssertionError: cases/10/edge_ids/0: 'edge.http.delete.api_meetings_meeting_id' does not match '^edge\\.(face|route|timer|tool|cli)\\.[a-z0-9_]+$'
E         cases/10/setup/4: {'kind': 'api', 'method': 'DELETE', 'path': '/api/meetings/{meeting_id}', 'adapter': 'http-route', 'expect_status': 200} is not valid under any of the given schemas
E         cases/10/trigger: {'kind': 'api', 'method': 'POST', 'path': '/api/meetings/{meeting_id}/restore', 'adapter': 'http-route', 'expect_status': 200, 'then': [{'kind': 'ui', 'action': 'reload', 'adapter': 'ui-navigation'}]} is not valid under any of the given schemas
E         cases/11/edge_ids/0: 'edge.http.delete.api_workbenches_workbench_id_items_item_id' does not match '^edge\\.(face|route|timer|tool|cli)\\.[a-z0-9_]+$'
E         cases/11/setup/6: {'kind': 'api', 'method': 'DELETE', 'path': '/api/workbenches/{workbench_id}/items/{item_one}', 'adapter': 'http-route', 'expect_status': 200} is not valid under any of the given schemas
E         cases/11/setup/11: {'kind': 'api', 'method': 'POST', 'path': '/api/workbenches/{workbench_id}/items/{item_one}/restore', 'adapter': 'http-route', 'expect_status': 200} is not valid under any of the given schemas
E         cases/11/trigger: {'kind': 'api', 'method': 'POST', 'path': '/api/workbenches/{workbench_id}/items/restore', 'adapter': 'http-route', 'expect_status': 200, 'body': {'item_ids': ['{item_one}', '{item_two}']}, 'then': [{'kind': 'ui', 'action': 'reload', 'adapter': 'ui-navigation'}]} is not valid under any of the given schemas
E       assert not [<ValidationError: "'edge.http.delete.api_meetings_meeting_id' does not match '^edge\\\\.(face|route|timer|tool|cli)\\...{item_one}/restore', 'adapter': 'http-route', 'expect_status': 200} is not valid under any of the given schemas">, ...]

tests/unit/test_philo_graph_atlas.py:148: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase13-astra.json]
FAILED tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase7.json]
FAILED tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_keeps_the_shared_graph_fences[test_face_cases_carry_both_ruled_viewports]
FAILED tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_validates_against_schema_and_openapi
4 failed, 330 passed in 58.70s
```

### Captured run — 2026-10-02T03:35:41Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.meeting.park_restore --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-02/meeting-1440-r1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2ddb6b6f96f087f64a9d47d5871b02915b1e2914

```text
PASS: live
BRAIN: astra
SOURCE: c7073f9cac59e898e53f425f4a437966a10aaa0b dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-BkuS9K4h.js'] hub=http://127.0.0.1:53440 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-k0z5p_ps/.local/share/holdspeak/holdspeak.db engine=none
JOB: j6
VERDICT: blocked terminal=None
EVIDENCE: ['.tmp/graph-walk/philo-13-02/meeting-1440-r1/20261002T033541Z-case.p13.meeting.park_restore-astra-1440/blocked.png']
NOTE: BLOCKED: precondition not met: {'kind': 'protocol_field', 'path': '/segments/1/text', 'value': 'Avery will check the frozen bytes before the next review.'} at 'protocol: GET /api/meetings/991bbad8?include_parked=true' — /segments/1/text = 'Blair: Avery will check the frozen bytes before the next review.', wanted 'Avery will check the frozen bytes before the next review.'
```

### Captured run — 2026-10-02T03:36:39Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.meeting.park_restore --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-02/meeting-1440-r2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2ddb6b6f96f087f64a9d47d5871b02915b1e2914

```text
PASS: live
BRAIN: astra
SOURCE: c7073f9cac59e898e53f425f4a437966a10aaa0b dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-BkuS9K4h.js'] hub=http://127.0.0.1:54028 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-n73x30rz/.local/share/holdspeak/holdspeak.db engine=none
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-02/meeting-1440-r2/20261002T033639Z-case.p13.meeting.park_restore-astra-1440/before.png', '.tmp/graph-walk/philo-13-02/meeting-1440-r2/20261002T033639Z-case.p13.meeting.park_restore-astra-1440/after.png']
NOTE: predicate: GET /api/meetings answered 200 with 1 row(s) {'id': '77565858', 'parked': False}; GET /api/meetings?parked=true answered 200 with 0 row(s) {'id': '77565858'}; GET /api/meetings/77565858 answered 200 with 1 row(s) {'text': 'Blair: Avery will check the frozen bytes before the next review.'}
```

### Captured run — 2026-10-02T03:37:53Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.meeting.park_restore --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-02/meeting-1440-r3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2ddb6b6f96f087f64a9d47d5871b02915b1e2914

```text
PASS: live
BRAIN: astra
SOURCE: c7073f9cac59e898e53f425f4a437966a10aaa0b dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-BkuS9K4h.js'] hub=http://127.0.0.1:54702 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-clzqar5b/.local/share/holdspeak/holdspeak.db engine=none
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-02/meeting-1440-r3/20261002T033753Z-case.p13.meeting.park_restore-astra-1440/before.png', '.tmp/graph-walk/philo-13-02/meeting-1440-r3/20261002T033753Z-case.p13.meeting.park_restore-astra-1440/after.png']
NOTE: predicate: GET /api/meetings answered 200 with 1 row(s) {'id': 'f375c4dc', 'parked': False}; GET /api/meetings?parked=true answered 200 with 0 row(s) {'id': 'f375c4dc'}; GET /api/meetings/f375c4dc answered 200 with 1 row(s) {'text': 'Blair: Avery will check the frozen bytes before the next review.'}
```

### Captured run — 2026-10-02T03:39:08Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.meeting.park_restore --brain astra --viewport 393 --engine none --no-build --out .tmp/graph-walk/philo-13-02/meeting-393-r1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2ddb6b6f96f087f64a9d47d5871b02915b1e2914

```text
PASS: live
BRAIN: astra
SOURCE: c7073f9cac59e898e53f425f4a437966a10aaa0b dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-BkuS9K4h.js'] hub=http://127.0.0.1:55434 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-t735qccq/.local/share/holdspeak/holdspeak.db engine=none
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-02/meeting-393-r1/20261002T033908Z-case.p13.meeting.park_restore-astra-393/before.png', '.tmp/graph-walk/philo-13-02/meeting-393-r1/20261002T033908Z-case.p13.meeting.park_restore-astra-393/after.png']
NOTE: predicate: GET /api/meetings answered 200 with 1 row(s) {'id': 'ed8e7b3c', 'parked': False}; GET /api/meetings?parked=true answered 200 with 0 row(s) {'id': 'ed8e7b3c'}; GET /api/meetings/ed8e7b3c answered 200 with 1 row(s) {'text': 'Blair: Avery will check the frozen bytes before the next review.'}
```

### Captured run — 2026-10-02T03:40:10Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.workbench.park_restore --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-02/workbench-1440-r1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2ddb6b6f96f087f64a9d47d5871b02915b1e2914

```text
PASS: live
BRAIN: astra
SOURCE: c7073f9cac59e898e53f425f4a437966a10aaa0b dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-BkuS9K4h.js'] hub=http://127.0.0.1:56112 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-t7vtsa6d/.local/share/holdspeak/holdspeak.db engine=none
JOB: j1
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-02/workbench-1440-r1/20261002T034010Z-case.p13.workbench.park_restore-astra-1440/before.png', '.tmp/graph-walk/philo-13-02/workbench-1440-r1/20261002T034010Z-case.p13.workbench.park_restore-astra-1440/after.png']
NOTE: predicate: GET /api/workbenches/workbench_f391497ff678 answered 200 with 1 row(s) {'id': 'wbi_c13009440d15', 'parked': False, 'result': 'Atlas retained result'}; GET /api/workbenches/workbench_f391497ff678 answered 200 with 1 row(s) {'id': 'wbi_2a168f162a1c', 'parked': False, 'body': 'Keep the second work body'}; GET /api/workbenches/workbench_f391497ff678?parked=true answered 200 with 0 row(s) {'id': 'wbi_c13009440d15'}; GET /api/workbenches/workbench_f391497ff678?parked=true answered 200 with 0 row(s) {'id': 'wbi_2a168f162a1c'}
```

### Captured run — 2026-10-02T03:41:16Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.workbench.park_restore --brain astra --viewport 393 --engine none --no-build --out .tmp/graph-walk/philo-13-02/workbench-393-r1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2ddb6b6f96f087f64a9d47d5871b02915b1e2914

```text
PASS: live
BRAIN: astra
SOURCE: c7073f9cac59e898e53f425f4a437966a10aaa0b dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-BkuS9K4h.js'] hub=http://127.0.0.1:56769 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-1tygh1_k/.local/share/holdspeak/holdspeak.db engine=none
JOB: j1
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-02/workbench-393-r1/20261002T034116Z-case.p13.workbench.park_restore-astra-393/before.png', '.tmp/graph-walk/philo-13-02/workbench-393-r1/20261002T034116Z-case.p13.workbench.park_restore-astra-393/after.png']
NOTE: predicate: GET /api/workbenches/workbench_0182ec00c9c7 answered 200 with 1 row(s) {'id': 'wbi_dabc8ee9db51', 'parked': False, 'result': 'Atlas retained result'}; GET /api/workbenches/workbench_0182ec00c9c7 answered 200 with 1 row(s) {'id': 'wbi_564083394dd2', 'parked': False, 'body': 'Keep the second work body'}; GET /api/workbenches/workbench_0182ec00c9c7?parked=true answered 200 with 0 row(s) {'id': 'wbi_dabc8ee9db51'}; GET /api/workbenches/workbench_0182ec00c9c7?parked=true answered 200 with 0 row(s) {'id': 'wbi_564083394dd2'}
```

### Captured run — 2026-10-02T03:43:07Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.meeting.park_restore --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-02/meeting-1440-r4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2ddb6b6f96f087f64a9d47d5871b02915b1e2914

```text
PASS: live
BRAIN: astra
SOURCE: c7073f9cac59e898e53f425f4a437966a10aaa0b dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-BkuS9K4h.js'] hub=http://127.0.0.1:57868 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-k2oj6y9q/.local/share/holdspeak/holdspeak.db engine=none
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-02/meeting-1440-r4/20261002T034308Z-case.p13.meeting.park_restore-astra-1440/before.png', '.tmp/graph-walk/philo-13-02/meeting-1440-r4/20261002T034308Z-case.p13.meeting.park_restore-astra-1440/after.png']
NOTE: predicate: GET /api/meetings answered 200 with 1 row(s) {'id': 'f9b11dca', 'parked': False}; GET /api/meetings?parked=true answered 200 with 0 row(s) {'id': 'f9b11dca'}; GET /api/meetings/f9b11dca answered 200 with 1 row(s) {'text': 'Blair: Avery will check the frozen bytes before the next review.'}
```

### Captured run — 2026-10-02T03:45:06Z

- **Command:** `python3 .tmp/philo-13-astra/test-a1.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 2ddb6b6f96f087f64a9d47d5871b02915b1e2914

```text
COMMAND uv run pytest --collect-only -q tests/unit/test_philo13_meeting_parking.py tests/unit/test_philo13_workbench_parking.py tests/unit/test_db_schema_policy.py tests/unit/test_reconcile.py tests/unit/test_db.py::TestDatabase tests/unit/test_db.py::TestTranscriptSearch tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot tests/unit/test_phase200_meeting_outcomes.py tests/unit/test_phase143_meeting_route_primitives.py tests/unit/test_meeting_import.py tests/unit/test_project_projection_services.py tests/unit/test_desk_projections.py tests/unit/test_mcp_tools.py tests/unit/test_thought_workbench_backend.py tests/unit/test_workbench_triage.py tests/unit/test_workbench_triage_kernel.py tests/unit/test_workbench_runner_migration.py tests/integration/test_phase143_workbench_route_adoption.py tests/unit/test_api_surface.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo13_astra_atlas.py
FULL OUTPUT .tmp/philo-13-astra/a1-final-collection.txt
plicable_case_carries_one_trigger]
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

335 tests collected in 1.44s

COMMAND uv run pytest -q tests/unit/test_philo13_meeting_parking.py tests/unit/test_philo13_workbench_parking.py tests/unit/test_db_schema_policy.py tests/unit/test_reconcile.py tests/unit/test_db.py::TestDatabase tests/unit/test_db.py::TestTranscriptSearch tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot tests/unit/test_phase200_meeting_outcomes.py tests/unit/test_phase143_meeting_route_primitives.py tests/unit/test_meeting_import.py tests/unit/test_project_projection_services.py tests/unit/test_desk_projections.py tests/unit/test_mcp_tools.py tests/unit/test_thought_workbench_backend.py tests/unit/test_workbench_triage.py tests/unit/test_workbench_triage_kernel.py tests/unit/test_workbench_runner_migration.py tests/integration/test_phase143_workbench_route_adoption.py tests/unit/test_api_surface.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo13_astra_atlas.py
FULL OUTPUT .tmp/philo-13-astra/a1-final-run.txt
........................................................................ [ 21%]
........................................................................ [ 42%]
........................................................................ [ 64%]
......F................................................................. [ 85%]
...........................................F...                          [100%]
=================================== FAILURES ===================================
______ test_atlas_validates_against_its_schema[atlas-phase13-astra.json] _______

every_atlas = {'atlas_version': 'phase13-astra-wave1', 'cases': [{'applicability': 'applicable', 'completion_bound_s': 30, 'edge_ids... 'source': 'datetime.datetime.now() inside the hub process', 'status': 'available', ...}], 'council_readings': [], ...}
schema = {'$defs': {'case': {'additionalProperties': False, 'allOf': [{'if': {'properties': {...}, 'required': [...]}, 'then': ...raph/atlas.schema.json', '$schema': 'https://json-schema.org/draft/2020-12/schema', 'additionalProperties': False, ...}

    def test_atlas_validates_against_its_schema(every_atlas: dict, schema: dict) -> None:
        errors = sorted(
            Draft202012Validator(schema).iter_errors(every_atlas),
            key=lambda e: list(e.absolute_path),
        )
>       assert not errors, "\n".join(
            f"{'/'.join(str(p) for p in e.absolute_path)}: {e.message}" for e in errors[:20]
        )
E       AssertionError: cases/10/setup/9: {'kind': 'ui', 'action': 'wait_for', 'selector': '.desk-dock', 'state': 'visible', 'timeout_ms': 30000, 'adapter': 'ui-navigation'} is not valid under any of the given schemas
E         cases/11/setup/10: {'kind': 'ui', 'action': 'wait_for', 'selector': '.desk-dock', 'state': 'visible', 'timeout_ms': 30000, 'adapter': 'ui-navigation'} is not valid under any of the given schemas
E         cases/11/setup/18: {'kind': 'ui', 'action': 'wait_for', 'selector': '.desk-dock', 'state': 'visible', 'timeout_ms': 30000, 'adapter': 'ui-navigation'} is not valid under any of the given schemas
E       assert not [<ValidationError: "{'kind': 'ui', 'action': 'wait_for', 'selector': '.desk-dock', 'state': 'visible', 'timeout_ms': 3...k', 'state': 'visible', 'timeout_ms': 30000, 'adapter': 'ui-navigation'} is not valid under any of the given schemas">]

tests/unit/test_philo_graph_atlas.py:148: AssertionError
___________ test_phase13_atlas_validates_against_schema_and_openapi ____________

    def test_phase13_atlas_validates_against_schema_and_openapi() -> None:
        atlas = _atlas()
        schema = json.loads(general.SCHEMA_PATH.read_text())
>       general.test_atlas_validates_against_its_schema(atlas, schema)

tests/unit/test_philo13_astra_atlas.py:77: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

every_atlas = {'atlas_version': 'phase13-astra-wave1', 'cases': [{'applicability': 'applicable', 'completion_bound_s': 30, 'edge_ids... 'source': 'datetime.datetime.now() inside the hub process', 'status': 'available', ...}], 'council_readings': [], ...}
schema = {'$defs': {'case': {'additionalProperties': False, 'allOf': [{'if': {'properties': {...}, 'required': [...]}, 'then': ...raph/atlas.schema.json', '$schema': 'https://json-schema.org/draft/2020-12/schema', 'additionalProperties': False, ...}

    def test_atlas_validates_against_its_schema(every_atlas: dict, schema: dict) -> None:
        errors = sorted(
            Draft202012Validator(schema).iter_errors(every_atlas),
            key=lambda e: list(e.absolute_path),
        )
>       assert not errors, "\n".join(
            f"{'/'.join(str(p) for p in e.absolute_path)}: {e.message}" for e in errors[:20]
        )
E       AssertionError: cases/10/setup/9: {'kind': 'ui', 'action': 'wait_for', 'selector': '.desk-dock', 'state': 'visible', 'timeout_ms': 30000, 'adapter': 'ui-navigation'} is not valid under any of the given schemas
E         cases/11/setup/10: {'kind': 'ui', 'action': 'wait_for', 'selector': '.desk-dock', 'state': 'visible', 'timeout_ms': 30000, 'adapter': 'ui-navigation'} is not valid under any of the given schemas
E         cases/11/setup/18: {'kind': 'ui', 'action': 'wait_for', 'selector': '.desk-dock', 'state': 'visible', 'timeout_ms': 30000, 'adapter': 'ui-navigation'} is not valid under any of the given schemas
E       assert not [<ValidationError: "{'kind': 'ui', 'action': 'wait_for', 'selector': '.desk-dock', 'state': 'visible', 'timeout_ms': 3...k', 'state': 'visible', 'timeout_ms': 30000, 'adapter': 'ui-navigation'} is not valid under any of the given schemas">]

tests/unit/test_philo_graph_atlas.py:148: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_philo_graph_atlas.py::test_atlas_validates_against_its_schema[atlas-phase13-astra.json]
FAILED tests/unit/test_philo13_astra_atlas.py::test_phase13_atlas_validates_against_schema_and_openapi
2 failed, 333 passed in 66.00s (0:01:05)
```

### Captured run — 2026-10-02T03:47:09Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.meeting.park_restore --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-02/meeting-1440-final`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2ddb6b6f96f087f64a9d47d5871b02915b1e2914

```text
PASS: live
BRAIN: astra
SOURCE: c7073f9cac59e898e53f425f4a437966a10aaa0b dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-BkuS9K4h.js'] hub=http://127.0.0.1:59901 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-e9o313q1/.local/share/holdspeak/holdspeak.db engine=none
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-02/meeting-1440-final/20261002T034710Z-case.p13.meeting.park_restore-astra-1440/before.png', '.tmp/graph-walk/philo-13-02/meeting-1440-final/20261002T034710Z-case.p13.meeting.park_restore-astra-1440/after.png']
NOTE: predicate: GET /api/meetings answered 200 with 1 row(s) {'id': 'e64c2be6', 'parked': False}; GET /api/meetings?parked=true answered 200 with 0 row(s) {'id': 'e64c2be6'}; GET /api/meetings/e64c2be6 answered 200 with 1 row(s) {'text': 'Blair: Avery will check the frozen bytes before the next review.'}
```

### Captured run — 2026-10-02T03:48:13Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.meeting.park_restore --brain astra --viewport 393 --engine none --no-build --out .tmp/graph-walk/philo-13-02/meeting-393-final`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2ddb6b6f96f087f64a9d47d5871b02915b1e2914

```text
PASS: live
BRAIN: astra
SOURCE: c7073f9cac59e898e53f425f4a437966a10aaa0b dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-BkuS9K4h.js'] hub=http://127.0.0.1:60536 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-fr_v0fip/.local/share/holdspeak/holdspeak.db engine=none
JOB: j6
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-02/meeting-393-final/20261002T034814Z-case.p13.meeting.park_restore-astra-393/before.png', '.tmp/graph-walk/philo-13-02/meeting-393-final/20261002T034814Z-case.p13.meeting.park_restore-astra-393/after.png']
NOTE: predicate: GET /api/meetings answered 200 with 1 row(s) {'id': 'eb02dba6', 'parked': False}; GET /api/meetings?parked=true answered 200 with 0 row(s) {'id': 'eb02dba6'}; GET /api/meetings/eb02dba6 answered 200 with 1 row(s) {'text': 'Blair: Avery will check the frozen bytes before the next review.'}
```

### Captured run — 2026-10-02T03:49:24Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.workbench.park_restore --brain astra --viewport 1440 --engine none --no-build --out .tmp/graph-walk/philo-13-02/workbench-1440-final`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2ddb6b6f96f087f64a9d47d5871b02915b1e2914

```text
PASS: live
BRAIN: astra
SOURCE: c7073f9cac59e898e53f425f4a437966a10aaa0b dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-BkuS9K4h.js'] hub=http://127.0.0.1:61333 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-qb8uw_4l/.local/share/holdspeak/holdspeak.db engine=none
JOB: j1
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-02/workbench-1440-final/20261002T034924Z-case.p13.workbench.park_restore-astra-1440/before.png', '.tmp/graph-walk/philo-13-02/workbench-1440-final/20261002T034924Z-case.p13.workbench.park_restore-astra-1440/after.png']
NOTE: predicate: GET /api/workbenches/workbench_49bba7a0c5d7 answered 200 with 1 row(s) {'id': 'wbi_504266359872', 'parked': False, 'result': 'Atlas retained result'}; GET /api/workbenches/workbench_49bba7a0c5d7 answered 200 with 1 row(s) {'id': 'wbi_92e4718baf44', 'parked': False, 'body': 'Keep the second work body'}; GET /api/workbenches/workbench_49bba7a0c5d7?parked=true answered 200 with 0 row(s) {'id': 'wbi_504266359872'}; GET /api/workbenches/workbench_49bba7a0c5d7?parked=true answered 200 with 0 row(s) {'id': 'wbi_92e4718baf44'}
```

### Captured run — 2026-10-02T03:50:47Z

- **Command:** `uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase13-astra.json --case case.p13.workbench.park_restore --brain astra --viewport 393 --engine none --no-build --out .tmp/graph-walk/philo-13-02/workbench-393-final`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2ddb6b6f96f087f64a9d47d5871b02915b1e2914

```text
PASS: live
BRAIN: astra
SOURCE: c7073f9cac59e898e53f425f4a437966a10aaa0b dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase13-astra.json
RUNTIME: build=['index-BkuS9K4h.js'] hub=http://127.0.0.1:61994 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-gbyuh_dn/.local/share/holdspeak/holdspeak.db engine=none
JOB: j1
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo-13-02/workbench-393-final/20261002T035047Z-case.p13.workbench.park_restore-astra-393/before.png', '.tmp/graph-walk/philo-13-02/workbench-393-final/20261002T035047Z-case.p13.workbench.park_restore-astra-393/after.png']
NOTE: predicate: GET /api/workbenches/workbench_4fedb0f9f0cc answered 200 with 1 row(s) {'id': 'wbi_1af6bf156707', 'parked': False, 'result': 'Atlas retained result'}; GET /api/workbenches/workbench_4fedb0f9f0cc answered 200 with 1 row(s) {'id': 'wbi_da3079175bf3', 'parked': False, 'body': 'Keep the second work body'}; GET /api/workbenches/workbench_4fedb0f9f0cc?parked=true answered 200 with 0 row(s) {'id': 'wbi_1af6bf156707'}; GET /api/workbenches/workbench_4fedb0f9f0cc?parked=true answered 200 with 0 row(s) {'id': 'wbi_da3079175bf3'}
```

### Captured run — 2026-10-02T03:54:51Z

- **Command:** `python3 .tmp/philo-13-astra/test-a1.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2ddb6b6f96f087f64a9d47d5871b02915b1e2914

```text
COMMAND uv run pytest --collect-only -q tests/unit/test_philo13_meeting_parking.py tests/unit/test_philo13_workbench_parking.py tests/unit/test_db_schema_policy.py tests/unit/test_reconcile.py tests/unit/test_db.py::TestDatabase tests/unit/test_db.py::TestTranscriptSearch tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot tests/unit/test_phase200_meeting_outcomes.py tests/unit/test_phase143_meeting_route_primitives.py tests/unit/test_meeting_import.py tests/unit/test_project_projection_services.py tests/unit/test_desk_projections.py tests/unit/test_mcp_tools.py tests/unit/test_thought_workbench_backend.py tests/unit/test_workbench_triage.py tests/unit/test_workbench_triage_kernel.py tests/unit/test_workbench_runner_migration.py tests/integration/test_phase143_workbench_route_adoption.py tests/unit/test_api_surface.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo13_astra_atlas.py
FULL OUTPUT .tmp/philo-13-astra/a1-final-collection.txt
plicable_case_carries_one_trigger]
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

335 tests collected in 1.67s

COMMAND uv run pytest -q tests/unit/test_philo13_meeting_parking.py tests/unit/test_philo13_workbench_parking.py tests/unit/test_db_schema_policy.py tests/unit/test_reconcile.py tests/unit/test_db.py::TestDatabase tests/unit/test_db.py::TestTranscriptSearch tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot tests/unit/test_phase200_meeting_outcomes.py tests/unit/test_phase143_meeting_route_primitives.py tests/unit/test_meeting_import.py tests/unit/test_project_projection_services.py tests/unit/test_desk_projections.py tests/unit/test_mcp_tools.py tests/unit/test_thought_workbench_backend.py tests/unit/test_workbench_triage.py tests/unit/test_workbench_triage_kernel.py tests/unit/test_workbench_runner_migration.py tests/integration/test_phase143_workbench_route_adoption.py tests/unit/test_api_surface.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo13_astra_atlas.py
FULL OUTPUT .tmp/philo-13-astra/a1-final-run.txt
........................................................................ [ 21%]
........................................................................ [ 42%]
........................................................................ [ 64%]
........................................................................ [ 85%]
...............................................                          [100%]
335 passed in 60.64s (0:01:00)
```
