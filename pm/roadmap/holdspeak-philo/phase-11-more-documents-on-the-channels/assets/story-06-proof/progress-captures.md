# Progress captures - PHILO-11-06

- **Story:** PHILO-11-06 - The atlas cases for the new kinds and Slack
- **Status:** in-progress — part 1, no story flip
- **Date:** 2026-09-30

The DW capture command created the default evidence header. These captures are parked as progress proof because story 06 remains in progress; the canonical paired evidence file will ship with the part 2 done flip. Captured commands and output below are unchanged.

## Proof

### Captured run — 2026-09-30T14:05:19Z

- **Command:** `bash pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-06-proof/verify_tests.sh .tmp/philo11-06/atlas-collect-r1.log --collect-only -q tests/unit/test_philo_graph_atlas.py tests/unit/test_philo3_summary_round2_atlas.py tests/unit/test_philo4_01_atlas_contracts.py tests/unit/test_philo4_04_atlas_contracts.py tests/unit/test_philo7_atlas.py tests/unit/test_philo8_atlas.py tests/unit/test_philo9_atlas.py tests/unit/test_philo9_04_atlas.py tests/unit/test_philo10_atlas.py tests/unit/test_philo11_atlas.py tests/unit/test_philo11_walk_harness.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6ad4e32315dfb4808aec92c2441ddc28faef3267

```text
Isolated HOME: /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//philo11-atlas-tests.a8DfOl
Basetemp: /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//philo11-atlas-tests.a8DfOl/pytest
tests/unit/test_philo10_atlas.py::test_every_admitted_write_twin_reads_its_kernel_receipt_with_its_actor
tests/unit/test_philo10_atlas.py::test_every_face_case_without_a_twin_is_excluded_with_a_reason
tests/unit/test_philo10_atlas.py::test_the_pairs_read_the_same_values
tests/unit/test_philo10_atlas.py::test_one_dispatch_is_counted_at_the_runner_where_the_runner_answers_a_send
tests/unit/test_philo10_atlas.py::test_every_email_case_boots_the_memory_key_store_before_a_key_is_saved
tests/unit/test_philo10_atlas.py::test_the_email_edge_records_before_it_answers_and_never_the_key
tests/unit/test_philo10_atlas.py::test_every_runner_script_is_retained_and_answers_by_argv_prefix
tests/unit/test_philo10_atlas.py::test_no_trigger_is_optional_and_no_optional_step_is_the_outcome
tests/unit/test_philo10_atlas.py::test_a_timed_window_is_one_gesture
tests/unit/test_philo10_atlas.py::test_every_new_face_case_says_what_main_showed
tests/unit/test_philo10_atlas.py::test_cli_calls_counts_by_prefix_across_processes
tests/unit/test_philo10_atlas.py::test_protocol_reads_count_names_an_exact_number_of_rows
tests/unit/test_philo10_atlas.py::test_the_recording_runner_records_before_it_answers
tests/unit/test_philo10_atlas.py::test_the_copier_keeps_each_run_in_its_own_directory
tests/unit/test_philo10_atlas.py::test_the_copier_refuses_to_reuse_a_label
tests/unit/test_philo10_atlas.py::test_the_copier_refuses_a_run_that_is_not_its_own[shared-run-dir]
tests/unit/test_philo10_atlas.py::test_the_copier_refuses_a_run_that_is_not_its_own[batch-keyed]
tests/unit/test_philo10_atlas.py::test_the_copier_refuses_a_run_that_is_not_its_own[wrong-case]
tests/unit/test_philo10_atlas.py::test_the_copier_refuses_an_observation_of_another_case_or_width
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[base-dce3afa9]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[base-merged]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[p10-final]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[p10-merged]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[p789-dce3afa9]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[p789-merged]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[red-98ea2cfa]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[s5-dce3afa9-a1]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[s5-dce3afa9-a2]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[s5-dce3afa9-a3]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[s5-merged-a1]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[s5-merged-a2]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[s5-merged-a3]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[serial-merged]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[words-merged]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[words-red-dce3afa9]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[../story-07-shots/p10-all-r2]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[../story-07-shots/resend-r2]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_case_state_id_resolves-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_case_state_id_resolves-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_case_reference_inside_the_atlas_resolves-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_case_reference_inside_the_atlas_resolves-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_clock_a_case_uses_is_declared-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_clock_a_case_uses_is_declared-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_applicable_case_carries_one_trigger-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_applicable_case_carries_one_trigger-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_face_cases_carry_both_ruled_viewports-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_face_cases_carry_both_ruled_viewports-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_applicable_predicate_is_a_kind_the_rig_implements-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_applicable_predicate_is_a_kind_the_rig_implements-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_predicate_observes_a_selector_or_a_route-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_predicate_observes_a_selector_or_a_route-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_source_reference_lands_on_its_symbol-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_source_reference_lands_on_its_symbol-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_case_keeps_its_human_sentence-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_case_keeps_its_human_sentence-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_ui_action_is_one_the_rig_implements-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_ui_action_is_one_the_rig_implements-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_boundary_names_its_substitution-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_boundary_names_its_substitution-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_no_precondition_check_compares_two_snapshots-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_no_precondition_check_compares_two_snapshots-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_precondition_check_observes_a_selector_or_a_route-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_precondition_check_observes_a_selector_or_a_route-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_no_check_asserts_the_result_the_trigger_must_produce-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_no_check_asserts_the_result_the_trigger_must_produce-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_no_step_acts_on_a_root_placeholder-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_no_step_acts_on_a_root_placeholder-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_navigation_steps_carry_no_selector-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_navigation_steps_carry_no_selector-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_desk_face_case_crosses_the_gate_first-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_desk_face_case_crosses_the_gate_first-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_captured_id_names_the_field_it_reads-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_captured_id_names_the_field_it_reads-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_ids_are_unique-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_ids_are_unique-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_validate_against_schema_and_openapi[atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_validate_against_schema_and_openapi[atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_atlas_has_one_headless_case_for_each_new_source_kind
tests/unit/test_philo11_atlas.py::test_each_source_uses_real_producer_preview_prepare_send_and_durable_reads
tests/unit/test_philo11_atlas.py::test_meeting_cases_use_import_and_engine_replay_boundary
tests/unit/test_philo11_atlas.py::test_meeting_decision_and_record_are_confirmed_by_real_proposal_route
tests/unit/test_philo11_atlas.py::test_long_slack_refusal_keeps_integer_limits_and_zero_history
tests/unit/test_philo11_atlas.py::test_posted_slack_proof_has_no_provider_identity_fields
tests/unit/test_philo11_walk_harness.py::test_plan_expands_face_widths_and_headless_operations_in_file_order
tests/unit/test_philo11_walk_harness.py::test_reading_is_one_physical_tsv_line
tests/unit/test_philo11_walk_harness.py::test_observation_validation_requires_the_declared_source_provenance
tests/unit/test_philo11_walk_harness.py::test_observation_validation_rejects_a_db_outside_the_hub_home
tests/unit/test_philo11_walk_harness.py::test_not_applicable_observation_is_valid_before_a_hub_exists
tests/unit/test_philo11_walk_harness.py::test_retention_keeps_every_serial_run_and_refuses_reuse
tests/unit/test_philo11_walk_harness.py::test_retention_refuses_a_table_that_does_not_name_the_observation
tests/unit/test_philo11_walk_harness.py::test_retention_refuses_a_multiline_tsv_row_instead_of_merging_it
tests/unit/test_philo11_walk_harness.py::test_archive_red_script_uses_archive_revision_and_astra
tests/unit/test_philo11_walk_harness.py::test_graph_walk_can_be_told_the_revision_of_an_extracted_archive
tests/unit/test_philo11_walk_harness.py::test_integer_facts_check_the_json_type_not_only_equality[39000-39000-True]
tests/unit/test_philo11_walk_harness.py::test_integer_facts_check_the_json_type_not_only_equality[39000.0-39000-False]
tests/unit/test_philo11_walk_harness.py::test_integer_facts_check_the_json_type_not_only_equality[39000-39000-False]
tests/unit/test_philo11_walk_harness.py::test_integer_facts_check_the_json_type_not_only_equality[True-1-False]
tests/unit/test_philo11_walk_harness.py::test_integer_facts_check_the_json_type_not_only_equality[False-0-False]

406 tests collected in 0.51s

Complete pytest log: .tmp/philo11-06/atlas-collect-r1.log
Exit code: 0
```

### Captured run — 2026-09-30T14:08:32Z

- **Command:** `bash pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-06-proof/verify_tests.sh .tmp/philo11-06/atlas-tests-r1.log -q tests/unit/test_philo_graph_atlas.py tests/unit/test_philo3_summary_round2_atlas.py tests/unit/test_philo4_01_atlas_contracts.py tests/unit/test_philo4_04_atlas_contracts.py tests/unit/test_philo7_atlas.py tests/unit/test_philo8_atlas.py tests/unit/test_philo9_atlas.py tests/unit/test_philo9_04_atlas.py tests/unit/test_philo10_atlas.py tests/unit/test_philo11_atlas.py tests/unit/test_philo11_walk_harness.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6ad4e32315dfb4808aec92c2441ddc28faef3267

```text
Isolated HOME: /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//philo11-atlas-tests.HQsESV
Basetemp: /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//philo11-atlas-tests.HQsESV/pytest
........................................................................ [ 17%]
........................................................................ [ 35%]
........................................................................ [ 53%]
........................................................................ [ 70%]
........................................................................ [ 88%]
..............................................                           [100%]
406 passed in 6.21s

Complete pytest log: .tmp/philo11-06/atlas-tests-r1.log
Exit code: 0
```

### Captured run — 2026-09-30T14:21:23Z

- **Command:** `.venv/bin/python pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-06-proof/rig_run.py p11-head-r1 docs/internal/philo/graph/atlas-phase11.json docs/internal/philo/graph/atlas-phase11-slack.json`
- **Cwd:** .
- **Exit code:** 2
- **Index-tree:** 6ad4e32315dfb4808aec92c2441ddc28faef3267

```text
11 runs, strictly sequential; out /Users/karol/dev/tools/wt-philo-11-06/.tmp/philo11-06/p11-head-r1
[1/11] case.p11.document.monday_brief.op op: starting
atlas-phase11.json	case.p11.document.monday_brief.op	op	pass	2.882	2.34	predicate: all 20 facts hold: the trigger outcome holds; the trigger send.state holds; the trigger send.channel holds; observe_at sends holds; observe_at sends.0.file_path holds; observe_at sends.0.proof.path holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_a	case.p11.document.monday_brief.op--op/20260930T142123Z-case.p11.document.monday_brief.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[2/11] case.p11.document.desk_decision.op op: starting
atlas-phase11.json	case.p11.document.desk_decision.op	op	pass	2.876	2.34	predicate: all 20 facts hold: the trigger outcome holds; the trigger send.state holds; the trigger send.channel holds; observe_at sends holds; observe_at sends.0.file_path holds; observe_at sends.0.proof.path holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_a	case.p11.document.desk_decision.op--op/20260930T142126Z-case.p11.document.desk_decision.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[3/11] case.p11.document.meeting_summary.op op: starting
HARNESS ERROR: case.p11.document.meeting_summary.op--op/20260930T142129Z-case.p11.document.meeting_summary.op-astra-1440: provenance has no hub HOME and db path
RETENTION ERROR: 2/11 rows; errors=1
```

### Captured run — 2026-09-30T14:21:36Z

- **Command:** `bash pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-06-proof/verify_tests.sh .tmp/philo11-06/atlas-tests-r2.log -q tests/unit/test_philo_graph_atlas.py tests/unit/test_philo3_summary_round2_atlas.py tests/unit/test_philo4_01_atlas_contracts.py tests/unit/test_philo4_04_atlas_contracts.py tests/unit/test_philo7_atlas.py tests/unit/test_philo8_atlas.py tests/unit/test_philo9_atlas.py tests/unit/test_philo9_04_atlas.py tests/unit/test_philo10_atlas.py tests/unit/test_philo11_atlas.py tests/unit/test_philo11_walk_harness.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6ad4e32315dfb4808aec92c2441ddc28faef3267

```text
Isolated HOME: /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//philo11-atlas-tests.J0NGPc
Basetemp: /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//philo11-atlas-tests.J0NGPc/pytest
........................................................................ [ 17%]
........................................................................ [ 35%]
........................................................................ [ 52%]
........................................................................ [ 70%]
........................................................................ [ 88%]
.................................................                        [100%]
409 passed in 6.83s

Complete pytest log: .tmp/philo11-06/atlas-tests-r2.log
Exit code: 0
```

### Captured run — 2026-09-30T14:22:42Z

- **Command:** `.venv/bin/python pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-06-proof/rig_run.py p11-head-r2 docs/internal/philo/graph/atlas-phase11.json docs/internal/philo/graph/atlas-phase11-slack.json`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 6ad4e32315dfb4808aec92c2441ddc28faef3267

```text
11 runs, strictly sequential; out /Users/karol/dev/tools/wt-philo-11-06/.tmp/philo11-06/p11-head-r2
[1/11] case.p11.document.monday_brief.op op: starting
atlas-phase11.json	case.p11.document.monday_brief.op	op	pass	2.916	2.42	predicate: all 20 facts hold: the trigger outcome holds; the trigger send.state holds; the trigger send.channel holds; observe_at sends holds; observe_at sends.0.file_path holds; observe_at sends.0.proof.path holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_a	case.p11.document.monday_brief.op--op/20260930T142242Z-case.p11.document.monday_brief.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[2/11] case.p11.document.desk_decision.op op: starting
atlas-phase11.json	case.p11.document.desk_decision.op	op	pass	2.898	2.39	predicate: all 20 facts hold: the trigger outcome holds; the trigger send.state holds; the trigger send.channel holds; observe_at sends holds; observe_at sends.0.file_path holds; observe_at sends.0.proof.path holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_a	case.p11.document.desk_decision.op--op/20260930T142245Z-case.p11.document.desk_decision.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[3/11] case.p11.document.meeting_summary.op op: starting
atlas-phase11.json	case.p11.document.meeting_summary.op	op	pass	3.557	2.44	predicate: all 20 facts hold: the trigger outcome holds; the trigger send.state holds; the trigger send.channel holds; observe_at sends holds; observe_at sends.0.file_path holds; observe_at sends.0.proof.path holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_a	case.p11.document.meeting_summary.op--op/20260930T142247Z-case.p11.document.meeting_summary.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[4/11] case.p11.document.meeting_digest.op op: starting
atlas-phase11.json	case.p11.document.meeting_digest.op	op	pass	3.551	2.44	predicate: all 20 facts hold: the trigger outcome holds; the trigger send.state holds; the trigger send.channel holds; observe_at sends holds; observe_at sends.0.file_path holds; observe_at sends.0.proof.path holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_a	case.p11.document.meeting_digest.op--op/20260930T142251Z-case.p11.document.meeting_digest.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[5/11] case.p11.document.meeting_followup.op op: starting
atlas-phase11.json	case.p11.document.meeting_followup.op	op	pass	3.532	2.40	predicate: all 20 facts hold: the trigger outcome holds; the trigger send.state holds; the trigger send.channel holds; observe_at sends holds; observe_at sends.0.file_path holds; observe_at sends.0.proof.path holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_a	case.p11.document.meeting_followup.op--op/20260930T142255Z-case.p11.document.meeting_followup.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[6/11] case.p11.document.meeting_decision.op op: starting
atlas-phase11.json	case.p11.document.meeting_decision.op	op	blocked	2.323	2.37	BLOCKED: POST /api/inference/assignments/set answered 400, wanted 200: {"code":"inference_assignment_incompatible","message":"Assignment contains an incompatible model."}	case.p11.document.meeting_decision.op--op/20260930T142258Z-case.p11.document.meeting_decision.op-astra-1440	1	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[7/11] case.p11.document.decision_record.op op: starting
atlas-phase11.json	case.p11.document.decision_record.op	op	blocked	2.269	2.37	BLOCKED: POST /api/inference/assignments/set answered 400, wanted 200: {"code":"inference_assignment_incompatible","message":"Assignment contains an incompatible model."}	case.p11.document.decision_record.op--op/20260930T142300Z-case.p11.document.decision_record.op-astra-1440	1	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[8/11] case.p11.slack.posted.op op: starting
atlas-phase11-slack.json	case.p11.slack.posted.op	op	pass	2.905	2.26	predicate: all_of: op_facts: all 17 facts hold: the trigger outcome holds; observe_at sends holds; observe_at sends.0.id holds; observe_at sends.0.state holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_at sends.0.proof.url is absent; observe_at sends.0.proof.	case.p11.slack.posted.op--op/20260930T142303Z-case.p11.slack.posted.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[9/11] case.p11.slack.failed.op op: starting
atlas-phase11-slack.json	case.p11.slack.failed.op	op	pass	2.893	2.26	predicate: all_of: op_facts: all 12 facts hold: the trigger outcome holds; observe_at sends holds; observe_at sends.0.id holds; observe_at sends.0.state holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_at sends.0.proof.url is absent; observe_at sends.0.proof.	case.p11.slack.failed.op--op/20260930T142306Z-case.p11.slack.failed.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[10/11] case.p11.slack.unknown.op op: starting
atlas-phase11-slack.json	case.p11.slack.unknown.op	op	pass	2.886	2.16	predicate: all_of: op_facts: all 12 facts hold: the trigger outcome holds; observe_at sends holds; observe_at sends.0.id holds; observe_at sends.0.state holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_at sends.0.proof.url is absent; observe_at sends.0.proof.	case.p11.slack.unknown.op--op/20260930T142308Z-case.p11.slack.unknown.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[11/11] case.p11.slack.too_large.op op: starting
atlas-phase11-slack.json	case.p11.slack.too_large.op	op	pass	2.917	2.16	predicate: all_of: op_facts: all 9 facts hold: the trigger code holds; the trigger limit holds; the trigger size holds; op read #0 (kernel.receipt.read) objects.0.operation.name holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.r	case.p11.slack.too_large.op--op/20260930T142311Z-case.p11.slack.too_large.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
TOTAL 11 runs: 9 pass, 2 not pass
```

### Captured run — 2026-09-30T14:25:06Z

- **Command:** `.venv/bin/python pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-06-proof/rig_run.py p11-head-r3 docs/internal/philo/graph/atlas-phase11.json docs/internal/philo/graph/atlas-phase11-slack.json`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 6ad4e32315dfb4808aec92c2441ddc28faef3267

```text
11 runs, strictly sequential; out /Users/karol/dev/tools/wt-philo-11-06/.tmp/philo11-06/p11-head-r3
[1/11] case.p11.document.monday_brief.op op: starting
atlas-phase11.json	case.p11.document.monday_brief.op	op	pass	2.891	1.99	predicate: all 20 facts hold: the trigger outcome holds; the trigger send.state holds; the trigger send.channel holds; observe_at sends holds; observe_at sends.0.file_path holds; observe_at sends.0.proof.path holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_a	case.p11.document.monday_brief.op--op/20260930T142506Z-case.p11.document.monday_brief.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[2/11] case.p11.document.desk_decision.op op: starting
atlas-phase11.json	case.p11.document.desk_decision.op	op	pass	2.909	1.91	predicate: all 20 facts hold: the trigger outcome holds; the trigger send.state holds; the trigger send.channel holds; observe_at sends holds; observe_at sends.0.file_path holds; observe_at sends.0.proof.path holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_a	case.p11.document.desk_decision.op--op/20260930T142509Z-case.p11.document.desk_decision.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[3/11] case.p11.document.meeting_summary.op op: starting
atlas-phase11.json	case.p11.document.meeting_summary.op	op	pass	3.565	1.84	predicate: all 20 facts hold: the trigger outcome holds; the trigger send.state holds; the trigger send.channel holds; observe_at sends holds; observe_at sends.0.file_path holds; observe_at sends.0.proof.path holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_a	case.p11.document.meeting_summary.op--op/20260930T142512Z-case.p11.document.meeting_summary.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[4/11] case.p11.document.meeting_digest.op op: starting
atlas-phase11.json	case.p11.document.meeting_digest.op	op	pass	3.56	1.84	predicate: all 20 facts hold: the trigger outcome holds; the trigger send.state holds; the trigger send.channel holds; observe_at sends holds; observe_at sends.0.file_path holds; observe_at sends.0.proof.path holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_a	case.p11.document.meeting_digest.op--op/20260930T142516Z-case.p11.document.meeting_digest.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[5/11] case.p11.document.meeting_followup.op op: starting
atlas-phase11.json	case.p11.document.meeting_followup.op	op	pass	3.523	1.85	predicate: all 20 facts hold: the trigger outcome holds; the trigger send.state holds; the trigger send.channel holds; observe_at sends holds; observe_at sends.0.file_path holds; observe_at sends.0.proof.path holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_a	case.p11.document.meeting_followup.op--op/20260930T142519Z-case.p11.document.meeting_followup.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[6/11] case.p11.document.meeting_decision.op op: starting
atlas-phase11.json	case.p11.document.meeting_decision.op	op	blocked	77.159	4.72	BLOCKED: precondition not met: {'kind': 'protocol_field', 'path': 'proposals', 'nonempty': True} at 'protocol: GET /api/meetings/d294a0b7/follow-through-proposals' — proposals is empty	case.p11.document.meeting_decision.op--op/20260930T142523Z-case.p11.document.meeting_decision.op-astra-1440	1	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[7/11] case.p11.document.decision_record.op op: starting
atlas-phase11.json	case.p11.document.decision_record.op	op	blocked	77.267	3.87	BLOCKED: precondition not met: {'kind': 'protocol_field', 'path': 'proposals', 'nonempty': True} at 'protocol: GET /api/meetings/41c5a6fd/follow-through-proposals' — proposals is empty	case.p11.document.decision_record.op--op/20260930T142640Z-case.p11.document.decision_record.op-astra-1440	1	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[8/11] case.p11.slack.posted.op op: starting
atlas-phase11-slack.json	case.p11.slack.posted.op	op	pass	2.927	3.87	predicate: all_of: op_facts: all 17 facts hold: the trigger outcome holds; observe_at sends holds; observe_at sends.0.id holds; observe_at sends.0.state holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_at sends.0.proof.url is absent; observe_at sends.0.proof.	case.p11.slack.posted.op--op/20260930T142757Z-case.p11.slack.posted.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[9/11] case.p11.slack.failed.op op: starting
atlas-phase11-slack.json	case.p11.slack.failed.op	op	pass	2.897	3.80	predicate: all_of: op_facts: all 12 facts hold: the trigger outcome holds; observe_at sends holds; observe_at sends.0.id holds; observe_at sends.0.state holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_at sends.0.proof.url is absent; observe_at sends.0.proof.	case.p11.slack.failed.op--op/20260930T142800Z-case.p11.slack.failed.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[10/11] case.p11.slack.unknown.op op: starting
atlas-phase11-slack.json	case.p11.slack.unknown.op	op	pass	2.929	3.57	predicate: all_of: op_facts: all 12 facts hold: the trigger outcome holds; observe_at sends holds; observe_at sends.0.id holds; observe_at sends.0.state holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_at sends.0.proof.url is absent; observe_at sends.0.proof.	case.p11.slack.unknown.op--op/20260930T142803Z-case.p11.slack.unknown.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[11/11] case.p11.slack.too_large.op op: starting
atlas-phase11-slack.json	case.p11.slack.too_large.op	op	pass	2.889	3.57	predicate: all_of: op_facts: all 9 facts hold: the trigger code holds; the trigger limit holds; the trigger size holds; op read #0 (kernel.receipt.read) objects.0.operation.name holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.r	case.p11.slack.too_large.op--op/20260930T142806Z-case.p11.slack.too_large.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
TOTAL 11 runs: 9 pass, 2 not pass
```

### Captured run — 2026-09-30T14:31:18Z

- **Command:** `.venv/bin/python pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-06-proof/rig_run.py p11-head-r5 docs/internal/philo/graph/atlas-phase11.json docs/internal/philo/graph/atlas-phase11-slack.json`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6ad4e32315dfb4808aec92c2441ddc28faef3267

```text
11 runs, strictly sequential; out /Users/karol/dev/tools/wt-philo-11-06/.tmp/philo11-06/p11-head-r5
[1/11] case.p11.document.monday_brief.op op: starting
atlas-phase11.json	case.p11.document.monday_brief.op	op	pass	2.894	5.23	predicate: all 20 facts hold: the trigger outcome holds; the trigger send.state holds; the trigger send.channel holds; observe_at sends holds; observe_at sends.0.file_path holds; observe_at sends.0.proof.path holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_a	case.p11.document.monday_brief.op--op/20260930T143118Z-case.p11.document.monday_brief.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[2/11] case.p11.document.desk_decision.op op: starting
atlas-phase11.json	case.p11.document.desk_decision.op	op	pass	2.971	5.23	predicate: all 20 facts hold: the trigger outcome holds; the trigger send.state holds; the trigger send.channel holds; observe_at sends holds; observe_at sends.0.file_path holds; observe_at sends.0.proof.path holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_a	case.p11.document.desk_decision.op--op/20260930T143121Z-case.p11.document.desk_decision.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[3/11] case.p11.document.meeting_summary.op op: starting
atlas-phase11.json	case.p11.document.meeting_summary.op	op	pass	3.609	4.89	predicate: all 20 facts hold: the trigger outcome holds; the trigger send.state holds; the trigger send.channel holds; observe_at sends holds; observe_at sends.0.file_path holds; observe_at sends.0.proof.path holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_a	case.p11.document.meeting_summary.op--op/20260930T143124Z-case.p11.document.meeting_summary.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[4/11] case.p11.document.meeting_digest.op op: starting
atlas-phase11.json	case.p11.document.meeting_digest.op	op	pass	3.59	4.66	predicate: all 20 facts hold: the trigger outcome holds; the trigger send.state holds; the trigger send.channel holds; observe_at sends holds; observe_at sends.0.file_path holds; observe_at sends.0.proof.path holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_a	case.p11.document.meeting_digest.op--op/20260930T143128Z-case.p11.document.meeting_digest.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[5/11] case.p11.document.meeting_followup.op op: starting
atlas-phase11.json	case.p11.document.meeting_followup.op	op	pass	4.12	4.66	predicate: all 20 facts hold: the trigger outcome holds; the trigger send.state holds; the trigger send.channel holds; observe_at sends holds; observe_at sends.0.file_path holds; observe_at sends.0.proof.path holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_a	case.p11.document.meeting_followup.op--op/20260930T143131Z-case.p11.document.meeting_followup.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[6/11] case.p11.document.meeting_decision.op op: starting
atlas-phase11.json	case.p11.document.meeting_decision.op	op	pass	17.968	4.21	predicate: all 20 facts hold: the trigger outcome holds; the trigger send.state holds; the trigger send.channel holds; observe_at sends holds; observe_at sends.0.file_path holds; observe_at sends.0.proof.path holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_a	case.p11.document.meeting_decision.op--op/20260930T143135Z-case.p11.document.meeting_decision.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[7/11] case.p11.document.decision_record.op op: starting
atlas-phase11.json	case.p11.document.decision_record.op	op	pass	18.178	3.15	predicate: all 20 facts hold: the trigger outcome holds; the trigger send.state holds; the trigger send.channel holds; observe_at sends holds; observe_at sends.0.file_path holds; observe_at sends.0.proof.path holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_a	case.p11.document.decision_record.op--op/20260930T143153Z-case.p11.document.decision_record.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[8/11] case.p11.slack.posted.op op: starting
atlas-phase11-slack.json	case.p11.slack.posted.op	op	pass	2.89	3.15	predicate: all_of: op_facts: all 17 facts hold: the trigger outcome holds; observe_at sends holds; observe_at sends.0.id holds; observe_at sends.0.state holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_at sends.0.proof.url is absent; observe_at sends.0.proof.	case.p11.slack.posted.op--op/20260930T143212Z-case.p11.slack.posted.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[9/11] case.p11.slack.failed.op op: starting
atlas-phase11-slack.json	case.p11.slack.failed.op	op	pass	2.902	2.97	predicate: all_of: op_facts: all 12 facts hold: the trigger outcome holds; observe_at sends holds; observe_at sends.0.id holds; observe_at sends.0.state holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_at sends.0.proof.url is absent; observe_at sends.0.proof.	case.p11.slack.failed.op--op/20260930T143214Z-case.p11.slack.failed.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[10/11] case.p11.slack.unknown.op op: starting
atlas-phase11-slack.json	case.p11.slack.unknown.op	op	pass	2.919	2.97	predicate: all_of: op_facts: all 12 facts hold: the trigger outcome holds; observe_at sends holds; observe_at sends.0.id holds; observe_at sends.0.state holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_at sends.0.proof.url is absent; observe_at sends.0.proof.	case.p11.slack.unknown.op--op/20260930T143217Z-case.p11.slack.unknown.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
[11/11] case.p11.slack.too_large.op op: starting
atlas-phase11-slack.json	case.p11.slack.too_large.op	op	pass	2.903	2.90	predicate: all_of: op_facts: all 9 facts hold: the trigger code holds; the trigger limit holds; the trigger size holds; op read #0 (kernel.receipt.read) objects.0.operation.name holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.r	case.p11.slack.too_large.op--op/20260930T143220Z-case.p11.slack.too_large.op-astra-1440	0	8a6b807d6682d9446d9b75216bbd3844d203cdcc	true
TOTAL 11 runs: 11 pass, 0 not pass
```

### Captured run — 2026-09-30T14:32:38Z

- **Command:** `zsh pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-06-proof/red_main.sh p11-red-332d-r1`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 6ad4e32315dfb4808aec92c2441ddc28faef3267

```text
11 runs, strictly sequential; out /Users/karol/dev/tools/wt-philo-11-06/.tmp/philo11-06/p11-red-332d-r1
[1/11] case.p11.slack.posted.op op: starting
atlas-phase11-slack.json	case.p11.slack.posted.op	op	blocked	2.721	3.54	BLOCKED: POST /api/channels/slack-webhooks answered 404, wanted 200: {"detail":"Not Found"}	case.p11.slack.posted.op--op/20260930T143245Z-case.p11.slack.posted.op-astra-1440	1	332d91586bdbd7fe40e3c2c00851a46adc4650e4	true
[2/11] case.p11.slack.failed.op op: starting
atlas-phase11-slack.json	case.p11.slack.failed.op	op	blocked	1.647	3.54	BLOCKED: POST /api/channels/slack-webhooks answered 404, wanted 200: {"detail":"Not Found"}	case.p11.slack.failed.op--op/20260930T143248Z-case.p11.slack.failed.op-astra-1440	1	332d91586bdbd7fe40e3c2c00851a46adc4650e4	true
[3/11] case.p11.slack.unknown.op op: starting
atlas-phase11-slack.json	case.p11.slack.unknown.op	op	blocked	1.65	3.54	BLOCKED: POST /api/channels/slack-webhooks answered 404, wanted 200: {"detail":"Not Found"}	case.p11.slack.unknown.op--op/20260930T143250Z-case.p11.slack.unknown.op-astra-1440	1	332d91586bdbd7fe40e3c2c00851a46adc4650e4	true
[4/11] case.p11.slack.too_large.op op: starting
atlas-phase11-slack.json	case.p11.slack.too_large.op	op	blocked	1.677	3.33	BLOCKED: POST /api/channels/slack-webhooks answered 404, wanted 200: {"detail":"Not Found"}	case.p11.slack.too_large.op--op/20260930T143251Z-case.p11.slack.too_large.op-astra-1440	1	332d91586bdbd7fe40e3c2c00851a46adc4650e4	true
[5/11] case.p11.document.monday_brief.op op: starting
atlas-phase11.json	case.p11.document.monday_brief.op	op	blocked	1.678	3.33	BLOCKED: capture_as 'digest': no value at 'payload_digest' in the decoded response of operation 'channel.preview'	case.p11.document.monday_brief.op--op/20260930T143253Z-case.p11.document.monday_brief.op-astra-1440	1	332d91586bdbd7fe40e3c2c00851a46adc4650e4	true
[6/11] case.p11.document.desk_decision.op op: starting
atlas-phase11.json	case.p11.document.desk_decision.op	op	blocked	1.665	3.33	BLOCKED: capture_as 'digest': no value at 'payload_digest' in the decoded response of operation 'channel.preview'	case.p11.document.desk_decision.op--op/20260930T143255Z-case.p11.document.desk_decision.op-astra-1440	1	332d91586bdbd7fe40e3c2c00851a46adc4650e4	true
[7/11] case.p11.document.meeting_summary.op op: starting
atlas-phase11.json	case.p11.document.meeting_summary.op	op	blocked	2.36	3.39	BLOCKED: capture_as 'digest': no value at 'payload_digest' in the decoded response of operation 'channel.preview'	case.p11.document.meeting_summary.op--op/20260930T143256Z-case.p11.document.meeting_summary.op-astra-1440	1	332d91586bdbd7fe40e3c2c00851a46adc4650e4	true
[8/11] case.p11.document.meeting_digest.op op: starting
atlas-phase11.json	case.p11.document.meeting_digest.op	op	blocked	2.311	3.39	BLOCKED: capture_as 'digest': no value at 'payload_digest' in the decoded response of operation 'channel.preview'	case.p11.document.meeting_digest.op--op/20260930T143259Z-case.p11.document.meeting_digest.op-astra-1440	1	332d91586bdbd7fe40e3c2c00851a46adc4650e4	true
[9/11] case.p11.document.meeting_followup.op op: starting
atlas-phase11.json	case.p11.document.meeting_followup.op	op	blocked	2.331	3.43	BLOCKED: capture_as 'digest': no value at 'payload_digest' in the decoded response of operation 'channel.preview'	case.p11.document.meeting_followup.op--op/20260930T143301Z-case.p11.document.meeting_followup.op-astra-1440	1	332d91586bdbd7fe40e3c2c00851a46adc4650e4	true
[10/11] case.p11.document.meeting_decision.op op: starting
atlas-phase11.json	case.p11.document.meeting_decision.op	op	blocked	16.789	3.12	BLOCKED: capture_as 'digest': no value at 'payload_digest' in the decoded response of operation 'channel.preview'	case.p11.document.meeting_decision.op--op/20260930T143303Z-case.p11.document.meeting_decision.op-astra-1440	1	332d91586bdbd7fe40e3c2c00851a46adc4650e4	true
[11/11] case.p11.document.decision_record.op op: starting
atlas-phase11.json	case.p11.document.decision_record.op	op	blocked	16.718	2.95	BLOCKED: capture_as 'digest': no value at 'payload_digest' in the decoded response of operation 'channel.preview'	case.p11.document.decision_record.op--op/20260930T143320Z-case.p11.document.decision_record.op-astra-1440	1	332d91586bdbd7fe40e3c2c00851a46adc4650e4	true
TOTAL 11 runs: 0 pass, 11 not pass
```

### Captured run — 2026-09-30T14:33:52Z

- **Command:** `bash pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-06-proof/verify_tests.sh .tmp/philo11-06/full-r1.log -q -n auto --ignore=tests/e2e/test_metal.py --junitxml=.tmp/philo11-06/full-r1.xml`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 6ad4e32315dfb4808aec92c2441ddc28faef3267

```text
Isolated HOME: /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//philo11-atlas-tests.QubN37
Basetemp: /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//philo11-atlas-tests.QubN37/pytest
    ? '.' + el.className.trim().split(/\s+/)

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:439: SyntaxWarning: invalid escape sequence '\('
    const m = /rgba?\(([^)]+)\)/.exec(s || '');

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_philo9_03_room_face_glass.py:807: SyntaxWarning: invalid escape sequence '\s'
    face = row.evaluate("""r => ({text: r.innerText.replace(/\s+/g, ' ').trim(),

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_hs141_models_setup_glass.py:21: HS-170: Settings -> Models module PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge (web/src/features/concierge/ConciergeCore.tsx, open-concierge window)
SKIPPED [1] tests/e2e/test_hs142_model_acquisition_glass.py:26: HS-170: Model Library front-door PARKED (HS-170-03, settled-design-four-faces.md Face 3); download-verify-add now at the Concierge's preset Download (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs143_assignments_glass.py:18: HS-170: Settings -> Assignments PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge's THE SET section + Adjust well (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs143_model_library_glass.py:19: HS-170: ModelLibraryCore PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge's FOUND section (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:42: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/e2e/test_workbench_walk.py:47: no hub listening at http://localhost:8778
SKIPPED [1] tests/unit/test_mesh_discovery.py:21: could not import 'zeroconf': No module named 'zeroconf'
SKIPPED [1] tests/e2e/test_dictation_enrichment_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation enrichment e2e
SKIPPED [1] tests/e2e/test_dictation_journal_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation journal e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:44: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:52: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [12] tests/e2e/test_dogfood_plumbing_e2e.py:66: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:85: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:95: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/unit/test_dictation_session_admission.py:497: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:924: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:993: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:1175: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:1196: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2242: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2494: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2534: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [2] tests/unit/test_dictation_session_admission.py:2548: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_dictation_session_admission.py:2588: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_delta_schema.py:640: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/integration/test_rails_observer_live.py:37: no rail events on this machine to summarize
SKIPPED [1] tests/integration/test_rails_observer_live.py:72: no rail events on this machine
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo11-atlas-tests.QubN37/xdist-gw4/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo11-atlas-tests.QubN37/xdist-gw4/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
SKIPPED [1] tests/unit/test_hs166_walk_fixes.py:183: No proposals generated
SKIPPED [1] tests/unit/test_dictation_grammars.py:91: could not import 'llama_cpp': No module named 'llama_cpp'
SKIPPED [1] tests/unit/test_github_provider.py:526: gh CLI not authenticated or not installed
SKIPPED [1] tests/unit/test_github_provider.py:537: gh CLI not authenticated or not installed
SKIPPED [1] tests/integration/test_update_drafter_live_43.py:110: live .43 model proof is opt-in: set HOLDSPEAK_UAT_LIVE_43=1 (runs a real model call on the LAN endpoint)
SKIPPED [1] tests/unit/test_interview_service.py:237: QUARANTINED #694: it drives project.setup.finalize through the thread's bound dispatch to assert the continuation refusal; finalize is CONFIG (the owner's press), no longer in the section, so the call is refused as unavailable before the continuation check. BACKLOG row 'Interview setup continuation after #694'.
SKIPPED [1] tests/uat/test_induction_integration_43.py:107: live .43 model proof is opt-in: set HOLDSPEAK_UAT_LIVE_43=1 (it runs a real extraction on the LAN model and takes minutes)
SKIPPED [1] tests/uat/test_induction_integration_43.py:118: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [1] tests/uat/test_mesh_dispatch.py:85: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:84: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:139: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:169: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/unit/test_phase143_speech_lifecycle_adoption.py:207: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [2] tests/e2e/test_hs14104_refinement_glass.py:59: superseded by the Thought Workbench real-path glass
SKIPPED [2] tests/e2e/test_hs14105_context_glass.py:110: superseded by the Thought Workbench real-path glass
SKIPPED [2] tests/e2e/test_hs14105a_default_context_glass.py:100: superseded by the Thought Workbench real-path glass
SKIPPED [1] tests/unit/test_project_room_schema.py:390: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_project_updates_schema.py:576: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/e2e/test_hs145_door_polish_glass.py:182: HS-170: door-board scroll-hint PARKED (HS-170-04); the arrival has no horizontal-scroll viewport -- capability intentionally gone
SKIPPED [1] tests/e2e/test_hs147_one_tap_glass.py:159: HS-170: door-rail one-tap arm PARKED (HS-170-04); per-event RECORD THIS gone; Schedule + Cancel at the arrival's capture bar covered by test_hs144_door_glass::test_upcoming_rail_schedule_create_round_trip_and_form_cancel
SKIPPED [1] tests/unit/test_watch_graduation_schema.py:493: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_web_runtime.py:269: this machine resolves the llama_cpp dictation engine but 'llama_cpp' is not installed (it is an optional extra)
SKIPPED [1] tests/e2e/test_hs156_front_door_glass.py:553: HS-170: front-door pack cards PARKED (HS-170-03); capability now at the Concierge's FOUND section (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs156_front_door_glass.py:619: HS-170: front-door candidate picker PARKED (HS-170-03); capability now at the Concierge's picker ChoiceCards (ConciergeCore.tsx)
SKIPPED [2] tests/e2e/test_hs158_room_glass.py:172: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs158_room_glass.py:233: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs158_room_glass.py:282: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs159_interview_glass.py:150: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:397: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:462: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); blank leg ported to test_hs169_door_legs_glass.py
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:555: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); abandon leg ported to test_hs169_door_legs_glass.py
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:268: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:519: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:671: HS-169-07 retired the interview entry point this leg used for project creation; evaluation/delta review is a live capability noted in the close ledger for re-pointing
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:919: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs161_github_glass.py:1088: gh CLI not authenticated or not installed (skip-clean)
SKIPPED [2] tests/e2e/test_hs166_jira_glass.py:328: HS-169-07 retired the interview + Jira wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs166_jira_walk.py:1637: acli jira auth status failed (exit 1): ✗ Error: unauthorized: use 'acli jira auth login' to authenticate
SKIPPED [2] tests/e2e/test_hs168_connections_glass.py:319: gh auth status failed (exit 1): You are not logged into any GitHub hosts. To log in, run: gh auth login
SKIPPED [2] tests/e2e/test_hs168_sources_glass.py:279: HS-169-02 retired the Sources step (ProgressPlan, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs168_sources_glass.py:365: HS-169-02 retired the Sources step (ProgressPlan, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [10] tests/e2e/test_meeting_transcription.py: Mock meeting fixture not found: /Users/karol/dev/tools/wt-philo-11-06/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_mermaid_renders.py:118: mermaid renderer unavailable in this env: eer-core/lib/puppeteer/node/PuppeteerNode.js:124:16)
    at async run (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:1090:19)
    at async cli (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:493:3)
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo11-atlas-tests.QubN37/xdist-gw2/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_grounding_rails_live.py:35: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:54: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:71: holdspeak not in the project map on this machine
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[1440-1200] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[393-900] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[1440-1200] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[393-900] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
FAILED tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
FAILED tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440 - AssertionEr...
FAILED tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393 - AssertionErr...
FAILED tests/unit/test_philo10_face_words.py::test_every_emitted_code_has_a_face_word
4 failed, 13628 passed, 117 skipped, 4 xfailed, 19 warnings in 3576.27s (0:59:36)

Complete pytest log: .tmp/philo11-06/full-r1.log
Exit code: 1
```

### Captured run — 2026-09-30T15:34:36Z

- **Command:** `bash pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-06-proof/verify_tests.sh .tmp/philo11-06/serial-reds-r1.log -q -rA --junitxml=.tmp/philo11-06/serial-reds-r1.xml tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440 tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393 tests/unit/test_philo10_face_words.py::test_every_emitted_code_has_a_face_word`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 6ad4e32315dfb4808aec92c2441ddc28faef3267

```text
Isolated HOME: /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//philo11-atlas-tests.AOaxTl
Basetemp: /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//philo11-atlas-tests.AOaxTl/pytest
F..F                                                                     [100%]
=================================== FAILURES ===================================
__________________ test_no_test_writes_into_tracked_evidence ___________________

    def test_no_test_writes_into_tracked_evidence() -> None:
        offenders = []
        for path in sorted(TESTS.rglob("*.py")):
            rel = path.relative_to(REPO).as_posix()
            if rel in ALLOWLIST:
                continue
            source = path.read_text(encoding="utf-8")
            if "pm/roadmap" not in source or not WRITE_RE.search(source):
                continue
            lines = _anchored_lines(ast.parse(source, filename=rel))
            if lines:
                offenders.append(f"{rel}:{lines[0]}")
>       assert not offenders, (
            f"EVIDENCE-WRITE: {len(offenders)} test file(s) build a pm/roadmap path and write files; "
            "use tests._evidence.evidence_dir(\"<rel>\") for the write dir:\n  " + "\n  ".join(offenders)
        )
E       AssertionError: EVIDENCE-WRITE: 1 test file(s) build a pm/roadmap path and write files; use tests._evidence.evidence_dir("<rel>") for the write dir:
E           tests/unit/test_philo11_walk_harness.py:20
E       assert not ['tests/unit/test_philo11_walk_harness.py:20']

tests/unit/test_evidence_scratch_guard.py:76: AssertionError
___________________ test_every_emitted_code_has_a_face_word ____________________

    def test_every_emitted_code_has_a_face_word() -> None:
>       assert codes.missing() == []
E       AssertionError: assert [('unknown', ...:slack'), ...] == []
E         
E         Left contains 20 more items, first extra item: ('unknown', 'ack_missing')
E         Use -v to get more diff

tests/unit/test_philo10_face_words.py:25: AssertionError
=============================== warnings summary ===============================
tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:260: SyntaxWarning: invalid escape sequence '\s'
    ? '.' + el.className.trim().split(/\s+/)

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:439: SyntaxWarning: invalid escape sequence '\('
    const m = /rgba?\(([^)]+)\)/.exec(s || '');

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_philo9_03_room_face_glass.py:807: SyntaxWarning: invalid escape sequence '\s'
    face = row.evaluate("""r => ({text: r.innerText.replace(/\s+/g, ' ').trim(),

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
==================================== PASSES ====================================
_____________________________ test_speak_loop_1440 _____________________________
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_____________________________ test_speak_loop_393 ______________________________
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
PASSED tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440
PASSED tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393
FAILED tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
FAILED tests/unit/test_philo10_face_words.py::test_every_emitted_code_has_a_face_word
2 failed, 2 passed, 3 warnings in 16.06s

Complete pytest log: .tmp/philo11-06/serial-reds-r1.log
Exit code: 1
```

### Captured run — 2026-09-30T15:35:21Z

- **Command:** `bash pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-06-proof/verify_tests.sh .tmp/philo11-06/serial-reds-r2.log -q -rA --junitxml=.tmp/philo11-06/serial-reds-r2.xml tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440 tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393 tests/unit/test_philo10_face_words.py::test_every_emitted_code_has_a_face_word`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 6ad4e32315dfb4808aec92c2441ddc28faef3267

```text
Isolated HOME: /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//philo11-atlas-tests.Epy1sK
Basetemp: /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//philo11-atlas-tests.Epy1sK/pytest
F..F                                                                     [100%]
=================================== FAILURES ===================================
__________________ test_no_test_writes_into_tracked_evidence ___________________

    def test_no_test_writes_into_tracked_evidence() -> None:
        offenders = []
        for path in sorted(TESTS.rglob("*.py")):
            rel = path.relative_to(REPO).as_posix()
            if rel in ALLOWLIST:
                continue
            source = path.read_text(encoding="utf-8")
            if "pm/roadmap" not in source or not WRITE_RE.search(source):
                continue
            lines = _anchored_lines(ast.parse(source, filename=rel))
            if lines:
                offenders.append(f"{rel}:{lines[0]}")
>       assert not offenders, (
            f"EVIDENCE-WRITE: {len(offenders)} test file(s) build a pm/roadmap path and write files; "
            "use tests._evidence.evidence_dir(\"<rel>\") for the write dir:\n  " + "\n  ".join(offenders)
        )
E       AssertionError: EVIDENCE-WRITE: 1 test file(s) build a pm/roadmap path and write files; use tests._evidence.evidence_dir("<rel>") for the write dir:
E           tests/unit/test_philo11_walk_harness.py:20
E       assert not ['tests/unit/test_philo11_walk_harness.py:20']

tests/unit/test_evidence_scratch_guard.py:76: AssertionError
___________________ test_every_emitted_code_has_a_face_word ____________________

    def test_every_emitted_code_has_a_face_word() -> None:
>       assert codes.missing() == []
E       AssertionError: assert [('unknown', ...:slack'), ...] == []
E         
E         Left contains 20 more items, first extra item: ('unknown', 'ack_missing')
E         Use -v to get more diff

tests/unit/test_philo10_face_words.py:25: AssertionError
=============================== warnings summary ===============================
tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:260: SyntaxWarning: invalid escape sequence '\s'
    ? '.' + el.className.trim().split(/\s+/)

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:439: SyntaxWarning: invalid escape sequence '\('
    const m = /rgba?\(([^)]+)\)/.exec(s || '');

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_philo9_03_room_face_glass.py:807: SyntaxWarning: invalid escape sequence '\s'
    face = row.evaluate("""r => ({text: r.innerText.replace(/\s+/g, ' ').trim(),

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
==================================== PASSES ====================================
_____________________________ test_speak_loop_1440 _____________________________
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_____________________________ test_speak_loop_393 ______________________________
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
PASSED tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440
PASSED tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393
FAILED tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
FAILED tests/unit/test_philo10_face_words.py::test_every_emitted_code_has_a_face_word
2 failed, 2 passed, 3 warnings in 14.83s

Complete pytest log: .tmp/philo11-06/serial-reds-r2.log
Exit code: 1
```

### Captured run — 2026-09-30T15:36:37Z

- **Command:** `bash pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-06-proof/verify_tests.sh .tmp/philo11-06/atlas-collect-final.log --collect-only -q tests/unit/test_philo_graph_atlas.py tests/unit/test_philo3_summary_round2_atlas.py tests/unit/test_philo4_01_atlas_contracts.py tests/unit/test_philo4_04_atlas_contracts.py tests/unit/test_philo7_atlas.py tests/unit/test_philo8_atlas.py tests/unit/test_philo9_atlas.py tests/unit/test_philo9_04_atlas.py tests/unit/test_philo10_atlas.py tests/unit/test_philo11_atlas.py tests/unit/test_philo11_walk_harness.py tests/unit/test_evidence_scratch_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6ad4e32315dfb4808aec92c2441ddc28faef3267

```text
Isolated HOME: /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//philo11-atlas-tests.Du8slm
Basetemp: /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//philo11-atlas-tests.Du8slm/pytest
tests/unit/test_philo10_atlas.py::test_the_email_edge_records_before_it_answers_and_never_the_key
tests/unit/test_philo10_atlas.py::test_every_runner_script_is_retained_and_answers_by_argv_prefix
tests/unit/test_philo10_atlas.py::test_no_trigger_is_optional_and_no_optional_step_is_the_outcome
tests/unit/test_philo10_atlas.py::test_a_timed_window_is_one_gesture
tests/unit/test_philo10_atlas.py::test_every_new_face_case_says_what_main_showed
tests/unit/test_philo10_atlas.py::test_cli_calls_counts_by_prefix_across_processes
tests/unit/test_philo10_atlas.py::test_protocol_reads_count_names_an_exact_number_of_rows
tests/unit/test_philo10_atlas.py::test_the_recording_runner_records_before_it_answers
tests/unit/test_philo10_atlas.py::test_the_copier_keeps_each_run_in_its_own_directory
tests/unit/test_philo10_atlas.py::test_the_copier_refuses_to_reuse_a_label
tests/unit/test_philo10_atlas.py::test_the_copier_refuses_a_run_that_is_not_its_own[shared-run-dir]
tests/unit/test_philo10_atlas.py::test_the_copier_refuses_a_run_that_is_not_its_own[batch-keyed]
tests/unit/test_philo10_atlas.py::test_the_copier_refuses_a_run_that_is_not_its_own[wrong-case]
tests/unit/test_philo10_atlas.py::test_the_copier_refuses_an_observation_of_another_case_or_width
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[base-dce3afa9]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[base-merged]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[p10-final]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[p10-merged]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[p789-dce3afa9]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[p789-merged]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[red-98ea2cfa]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[s5-dce3afa9-a1]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[s5-dce3afa9-a2]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[s5-dce3afa9-a3]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[s5-merged-a1]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[s5-merged-a2]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[s5-merged-a3]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[serial-merged]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[words-merged]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[words-red-dce3afa9]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[../story-07-shots/p10-all-r2]
tests/unit/test_philo10_atlas.py::test_every_claimed_run_keeps_its_own_observation[../story-07-shots/resend-r2]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_case_state_id_resolves-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_case_state_id_resolves-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_case_reference_inside_the_atlas_resolves-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_case_reference_inside_the_atlas_resolves-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_clock_a_case_uses_is_declared-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_clock_a_case_uses_is_declared-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_applicable_case_carries_one_trigger-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_applicable_case_carries_one_trigger-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_face_cases_carry_both_ruled_viewports-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_face_cases_carry_both_ruled_viewports-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_applicable_predicate_is_a_kind_the_rig_implements-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_applicable_predicate_is_a_kind_the_rig_implements-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_predicate_observes_a_selector_or_a_route-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_predicate_observes_a_selector_or_a_route-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_source_reference_lands_on_its_symbol-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_source_reference_lands_on_its_symbol-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_case_keeps_its_human_sentence-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_case_keeps_its_human_sentence-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_ui_action_is_one_the_rig_implements-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_ui_action_is_one_the_rig_implements-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_boundary_names_its_substitution-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_boundary_names_its_substitution-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_no_precondition_check_compares_two_snapshots-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_no_precondition_check_compares_two_snapshots-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_precondition_check_observes_a_selector_or_a_route-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_precondition_check_observes_a_selector_or_a_route-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_no_check_asserts_the_result_the_trigger_must_produce-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_no_check_asserts_the_result_the_trigger_must_produce-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_no_step_acts_on_a_root_placeholder-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_no_step_acts_on_a_root_placeholder-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_navigation_steps_carry_no_selector-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_navigation_steps_carry_no_selector-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_desk_face_case_crosses_the_gate_first-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_desk_face_case_crosses_the_gate_first-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_captured_id_names_the_field_it_reads-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_every_captured_id_names_the_field_it_reads-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_ids_are_unique-atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_keep_the_general_graph_fences[test_ids_are_unique-atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_validate_against_schema_and_openapi[atlas-phase11.json]
tests/unit/test_philo11_atlas.py::test_phase11_atlases_validate_against_schema_and_openapi[atlas-phase11-slack.json]
tests/unit/test_philo11_atlas.py::test_atlas_has_one_headless_case_for_each_new_source_kind
tests/unit/test_philo11_atlas.py::test_each_source_uses_real_producer_preview_prepare_send_and_durable_reads
tests/unit/test_philo11_atlas.py::test_meeting_cases_use_import_and_engine_replay_boundary
tests/unit/test_philo11_atlas.py::test_meeting_decision_and_record_are_confirmed_by_real_proposal_route
tests/unit/test_philo11_atlas.py::test_long_slack_refusal_keeps_integer_limits_and_zero_history
tests/unit/test_philo11_atlas.py::test_posted_slack_proof_has_no_provider_identity_fields
tests/unit/test_philo11_walk_harness.py::test_plan_expands_face_widths_and_headless_operations_in_file_order
tests/unit/test_philo11_walk_harness.py::test_reading_is_one_physical_tsv_line
tests/unit/test_philo11_walk_harness.py::test_observation_validation_requires_the_declared_source_provenance
tests/unit/test_philo11_walk_harness.py::test_observation_validation_rejects_a_db_outside_the_hub_home
tests/unit/test_philo11_walk_harness.py::test_not_applicable_observation_is_valid_before_a_hub_exists
tests/unit/test_philo11_walk_harness.py::test_retention_keeps_every_serial_run_and_refuses_reuse
tests/unit/test_philo11_walk_harness.py::test_retention_refuses_a_table_that_does_not_name_the_observation
tests/unit/test_philo11_walk_harness.py::test_retention_refuses_a_multiline_tsv_row_instead_of_merging_it
tests/unit/test_philo11_walk_harness.py::test_archive_red_script_uses_archive_revision_and_astra
tests/unit/test_philo11_walk_harness.py::test_graph_walk_can_be_told_the_revision_of_an_extracted_archive
tests/unit/test_philo11_walk_harness.py::test_engine_replay_serves_model_discovery_on_loopback
tests/unit/test_philo11_walk_harness.py::test_cli_queue_meeting_intelligence_uses_the_real_db_producer
tests/unit/test_philo11_walk_harness.py::test_cli_queue_meeting_intelligence_refuses_owner_or_missing_meeting
tests/unit/test_philo11_walk_harness.py::test_integer_facts_check_the_json_type_not_only_equality[39000-39000-True]
tests/unit/test_philo11_walk_harness.py::test_integer_facts_check_the_json_type_not_only_equality[39000.0-39000-False]
tests/unit/test_philo11_walk_harness.py::test_integer_facts_check_the_json_type_not_only_equality[39000-39000-False]
tests/unit/test_philo11_walk_harness.py::test_integer_facts_check_the_json_type_not_only_equality[True-1-False]
tests/unit/test_philo11_walk_harness.py::test_integer_facts_check_the_json_type_not_only_equality[False-0-False]
tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
tests/unit/test_evidence_scratch_guard.py::test_allowlist_files_exist

411 tests collected in 0.48s

Complete pytest log: .tmp/philo11-06/atlas-collect-final.log
Exit code: 0
```

### Captured run — 2026-09-30T15:36:39Z

- **Command:** `bash pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-06-proof/verify_tests.sh .tmp/philo11-06/atlas-tests-final.log -q tests/unit/test_philo_graph_atlas.py tests/unit/test_philo3_summary_round2_atlas.py tests/unit/test_philo4_01_atlas_contracts.py tests/unit/test_philo4_04_atlas_contracts.py tests/unit/test_philo7_atlas.py tests/unit/test_philo8_atlas.py tests/unit/test_philo9_atlas.py tests/unit/test_philo9_04_atlas.py tests/unit/test_philo10_atlas.py tests/unit/test_philo11_atlas.py tests/unit/test_philo11_walk_harness.py tests/unit/test_evidence_scratch_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6ad4e32315dfb4808aec92c2441ddc28faef3267

```text
Isolated HOME: /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//philo11-atlas-tests.wr5Hio
Basetemp: /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//philo11-atlas-tests.wr5Hio/pytest
........................................................................ [ 17%]
........................................................................ [ 35%]
........................................................................ [ 52%]
........................................................................ [ 70%]
........................................................................ [ 87%]
...................................................                      [100%]
=============================== warnings summary ===============================
tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:260: SyntaxWarning: invalid escape sequence '\s'
    ? '.' + el.className.trim().split(/\s+/)

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:439: SyntaxWarning: invalid escape sequence '\('
    const m = /rgba?\(([^)]+)\)/.exec(s || '');

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_philo9_03_room_face_glass.py:807: SyntaxWarning: invalid escape sequence '\s'
    face = row.evaluate("""r => ({text: r.innerText.replace(/\s+/g, ' ').trim(),

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
411 passed, 3 warnings in 7.11s

Complete pytest log: .tmp/philo11-06/atlas-tests-final.log
Exit code: 0
```
