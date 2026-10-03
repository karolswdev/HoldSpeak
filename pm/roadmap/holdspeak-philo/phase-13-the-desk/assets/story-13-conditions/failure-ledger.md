# C3 condition-payment failure ledger

The completed isolated-HOME full Python run recorded **80 failed, 13,875 passed, 117 skipped, 4 xfailed, 2 errors**. This is not a green full suite. The table accounts for all 82 failures/errors after targeted follow-up. The test-data root in that run was incorrectly inside the worktree; the isolation control uses `/tmp` outside the owner home. No Python product source changed after the full run. The final Dock source and schema fixture are covered by the follow-ups.

Main control: `fc12a18d`; merged main `76c361537` has no intervening `holdspeak/` or `web/` product change. The first main full run hit disk exhaustion and is not a valid failure baseline. Only clean confirmed reruns are classified inherited. Exact causes, not just test names, were compared.

Full sources: `full-python.txt`, `full-python.xml`, `verification-source.json`. Main control: `main-confirmation.txt`, `main-unmatched.txt`, `baseline-audit.json`. Follow-up: `path-rerun.txt`, `seam-run.txt`, `transient-serial-1.txt`, `transient-serial-2.txt`.

| Resolution | Count |
|---|---:|
| C3-W handoff | 2 |
| fixed People read | 15 |
| fixed project wording | 2 |
| fixed schema snapshot | 1 |
| inherited | 37 |
| serial-green twice | 3 |
| test-data isolation corrected | 22 |

All retained inherited failures remain open in their named maintenance home below. Astra owns tracking the data/producer and rig fences; Muad’Dib owns face adoption. They are not waived or called green. C3-W is the explicitly assigned, unmerged face work; story 13 remains in-progress.

| Exact test | Resolution and proof | Follow-up home |
|---|---|---|
| `tests/e2e/test_hs176_journal_glass.py::test_journal_filtered[393-852]` | inherited — baseline-audit.json: same confirmed assertion/cause on main | HS176 Journal / 393 tab access |
| `tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot` | fixed schema snapshot — schema-focused.txt + seam-rerun.xml | C3 condition payment / this ledger |
| `tests/integration/test_web_history_archive.py::test_history_keeps_approval_and_export_governance` | inherited — baseline-audit.json: same confirmed assertion/cause on main | Meetings governance / old ConfirmVerb assertion; PHILO A1 Park face |
| `tests/unit/test_delivery_read_model.py::TestDeliveryRoutes::test_register_source_by_path_and_typed_refusal` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/unit/test_decisions.py::test_meeting_delete_severs_source_without_deleting_decision` | inherited — baseline-audit.json: same confirmed assertion/cause on main | Decision source lifecycle / PHILO A1 Park semantics |
| `tests/unit/test_delivery_registry.py::TestSourceAndWorktreeIdentity::test_non_repo_is_a_typed_pathfree_refusal` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/unit/test_delivery_registry.py::TestV1MapImport::test_dead_map_rows_do_not_break_the_import` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/unit/test_dictation_cli.py::test_blocks_ls_prints_loaded_block_ids` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/unit/test_dictation_cli.py::test_blocks_ls_reports_empty_when_no_blocks_file` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/unit/test_dictation_cli.py::test_blocks_show_prints_block_spec` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/unit/test_dictation_cli.py::test_blocks_ls_outside_a_project_uses_global_file` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/e2e/test_hs176_journal_glass.py::test_journal_quiet[393-852]` | inherited — baseline-audit.json: same confirmed assertion/cause on main | HS176 Journal / 393 tab access |
| `tests/integration/test_live_action_item_triage.py::TestLiveFirstResolutionOrder::test_falls_through_to_the_saved_meeting_when_no_live_session_owns_it` | inherited — baseline-audit.json: same confirmed assertion/cause on main | Live action-item triage / archive test double |
| `tests/integration/test_live_action_item_triage.py::TestLiveFirstResolutionOrder::test_saved_meetings_still_work_with_no_live_session_bound_at_all` | inherited — baseline-audit.json: same confirmed assertion/cause on main | Live action-item triage / archive test double |
| `tests/unit/test_dw_counterpart_contract.py::TestWorktreeTruth::test_non_repo_root_neither_writes_nor_raises` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/e2e/test_hs176_journal_glass.py::test_journal_live_frame_obeys_the_active_filter` | serial-green twice — transient-serial-1.xml + transient-serial-2.xml; main-unmatched also passed | HS176 Journal / 393 tab access |
| `tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393` | inherited — baseline-audit.json: same confirmed assertion/cause on main | HS176 Speak / correction and compact surface |
| `tests/integration/test_phase200_recipe_catalog.py::TestTheScheduledOwnerReallyFires::test_the_sweep_is_driven_by_a_wall_clock_loop` | inherited — baseline-audit.json: same confirmed assertion/cause on main | Cadence / scheduled-loop source contract |
| `tests/unit/test_graph_walk_calibration.py::test_the_ui_vocabulary_is_closed_and_blocks_before_anything_fires` | inherited — baseline-audit.json: same confirmed assertion/cause on main | Graph rig / action-vocabulary calibration fence |
| `tests/integration/test_web_dictation_blocks_api.py::TestStarterTemplates::test_create_from_template_with_dry_run_global` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/unit/test_interior_canon_guard.py::test_no_left_border_rails_in_web_css` | inherited — baseline-audit.json: same confirmed assertion/cause on main | UX canon / CSS rail guard |
| `tests/unit/test_people_brief.py::TestBriefAggregation::test_brief_linked_meetings_via_uid_chain` | inherited — baseline-audit.json: same confirmed assertion/cause on main | People / B4 plain-database fixture schema |
| `tests/unit/test_people_brief.py::TestBriefAggregation::test_brief_unlinked_meeting_count_f11` | inherited — baseline-audit.json: same confirmed assertion/cause on main | People / B4 plain-database fixture schema |
| `tests/unit/test_people_brief.py::TestWriteCountSpy::test_brief_writes_zero_rows_to_plain_db` | inherited — baseline-audit.json: same confirmed assertion/cause on main | People / B4 plain-database fixture schema |
| `tests/unit/test_people_brief.py::TestCommitmentTriadUntouched::test_action_items_unchanged_after_brief` | inherited — baseline-audit.json: same confirmed assertion/cause on main | People / B4 plain-database fixture schema |
| `tests/unit/test_hs172_people_sources.py::TestBriefEnrichment::test_last_meeting_present` | inherited — baseline-audit.json: same confirmed assertion/cause on main | People / B4 plain-database fixture schema |
| `tests/integration/test_web_dictation_readiness_api.py::test_readiness_disabled_no_project_reports_next_actions` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/unit/test_phase200_doc_claims.py::test_registered_claim_matches_its_state[holds:UX-CANON.md:179]` | inherited — baseline-audit.json: same confirmed assertion/cause on main | UX canon and PHILO bus coverage / registered documentation claims |
| `tests/unit/test_phase200_doc_claims.py::test_registered_claim_matches_its_state[holds:useDeskChangedRefresh.ts:15]` | inherited — baseline-audit.json: same confirmed assertion/cause on main | UX canon and PHILO bus coverage / registered documentation claims |
| `tests/integration/test_web_dry_run_api.py::test_dry_run_no_project_still_runs_pipeline` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/unit/test_philo3_summary_detail.py::test_summary_wire_fixture_matches_real_producer_states` | inherited — baseline-audit.json: same confirmed assertion/cause on main | PHILO 3 Meetings / summary wire fixture |
| `tests/unit/test_phase143_routing_authority_census.py::test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer` | inherited — baseline-audit.json: same confirmed assertion/cause on main | Phase 143 routing authority census / stale source classification |
| `tests/unit/test_phase143_inference_capability_census.py::test_phase143_every_product_runner_entrance_has_one_owner` | inherited — baseline-audit.json: same confirmed assertion/cause on main | Phase 143 inference capability census / stale anchors and classifications |
| `tests/unit/test_philo4_01_atlas_contracts.py::test_the_reload_claim_points_at_the_quiet_branch` | inherited — baseline-audit.json: same confirmed assertion/cause on main | PHILO 4 Brief atlas / source-branch claim |
| `tests/unit/test_phase143_inference_capability_census.py::test_phase143_shared_helpers_have_semantic_callers` | inherited — baseline-audit.json: same confirmed assertion/cause on main | Phase 143 inference capability census / stale anchors and classifications |
| `tests/e2e/test_hs141_thought_workbench_glass.py::test_thought_workbench_real_glass[1440]` | fixed People read — seam-rerun.xml: readiness-gated request passed | HS141 Thought Workbench / browser boot and compact face |
| `tests/e2e/test_hs141_thought_workbench_glass.py::test_thought_workbench_real_glass[393]` | fixed People read — seam-rerun.xml: readiness-gated request passed | HS141 Thought Workbench / browser boot and compact face |
| `tests/unit/test_philo6_01_import_badge.py::test_empty_vtt_import_leaves_import_failed_on_the_wire` | inherited — baseline-audit.json: same confirmed assertion/cause on main | PHILO 6 Meetings / empty-import wire fixture |
| `tests/e2e/test_hs144_door_glass.py::test_hs144_door_populated_glass_action_refusal_and_shots` | serial-green twice — transient-serial-1.xml + transient-serial-2.xml; main-unmatched also passed | HS144 Door / error headline |
| `tests/unit/test_philo13_needs_you_fixture.py::test_seed_accepts_existing_empty_hub_and_refuses_oracle_reseed` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/unit/test_philo13_needs_you_fixture.py::test_export_reads_same_real_ids_and_mutates_a1_through_http_route` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/unit/test_philo13_needs_you_fixture.py::test_dedup_probe_mints_same_title_door_and_room_rows_through_real_routes` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/unit/test_philo13_needs_you_fixture.py::test_cli_stdout_is_json_and_export_keeps_seed_ids` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/unit/test_philo13_needs_you_route.py::test_summary_attention_filters_before_pagination_and_excludes_parked_and_old_job_leaves` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/unit/test_philo13_needs_you_route.py::test_cached_needs_you_route_rebuilds_after_real_action_item_status_mutation` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/unit/test_philo13_needs_you_route.py::test_completed_meeting_action_does_not_hide_same_title_overdue_milestone` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/e2e/test_hs144_door_glass.py::test_hs144_door_empty_and_error_shots[1440]` | inherited — seam-rerun.xml reaches same Door headline assertion as baseline-audit.json after People fix | HS144 Door / error headline |
| `tests/unit/test_philo7_file_and_find.py::test_a_fresh_cold_root_passes_with_the_retained_codex_config[owner-owner]` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/unit/test_philo7_file_and_find.py::test_a_fresh_cold_root_passes_with_the_retained_codex_config[agent-agent_granted]` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/unit/test_philo7_file_and_find.py::test_a_fresh_claude_cold_root_passes[owner]` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/unit/test_philo7_file_and_find.py::test_a_fresh_claude_cold_root_passes[agent]` | test-data isolation corrected — path-rerun.xml: passed outside the worktree and owner home | C3 condition payment / this ledger |
| `tests/e2e/test_hs144_door_glass.py::test_hs144_door_empty_and_error_shots[393]` | inherited — seam-rerun.xml reaches same Door headline assertion as baseline-audit.json after People fix | HS144 Door / error headline |
| `tests/e2e/test_hs144_door_glass.py::test_upcoming_rail_real_hub_states_and_dimensions` | fixed People read — seam-rerun.xml: readiness-gated request passed | HS144 Door / error headline |
| `tests/e2e/test_hs144_door_glass.py::test_upcoming_rail_schedule_create_round_trip_and_form_cancel` | fixed People read — seam-rerun.xml: readiness-gated request passed | HS144 Door / error headline |
| `tests/e2e/test_hs144_door_glass.py::test_go_menu_is_usable_at_393` | fixed People read — seam-rerun.xml: readiness-gated request passed | HS144 Door / error headline |
| `tests/e2e/test_hs144_door_glass.py::test_meetings_settings_calendar_glass_and_egress_fact` | fixed People read — seam-rerun.xml: readiness-gated request passed | HS144 Door / error headline |
| `tests/e2e/test_hs144_door_glass.py::test_meetings_deep_link_waits_for_registered_surface_x15` | fixed People read — seam-rerun.xml: readiness-gated request passed | HS144 Door / error headline |
| `tests/e2e/test_hs145_door_polish_glass.py::test_hs145_connect_calendar_affordance_and_quiet_state` | fixed People read — seam-rerun.xml: readiness-gated request passed | C3 condition payment / this ledger |
| `tests/e2e/test_hs152_hands_glass.py::test_deny_shows_tool_denied_row` | serial-green twice — transient-serial-1.xml + transient-serial-2.xml; main-unmatched also passed | C3 condition payment / this ledger |
| `tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[1440-before_guard]` | inherited — baseline-audit.json: same confirmed assertion/cause on main | PHILO 8 rig / expired undo-window outcome |
| `tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[1440-click_wait]` | inherited — baseline-audit.json: same confirmed assertion/cause on main | PHILO 8 rig / expired undo-window outcome |
| `tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[393-before_guard]` | inherited — baseline-audit.json: same confirmed assertion/cause on main | PHILO 8 rig / expired undo-window outcome |
| `tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[393-click_wait]` | inherited — baseline-audit.json: same confirmed assertion/cause on main | PHILO 8 rig / expired undo-window outcome |
| `tests/e2e/test_hs201_12_thought_note_glass.py::test_thought_note_is_one_clean_note[1440]` | fixed People read — seam-rerun.xml: readiness-gated request passed | C3 condition payment / this ledger |
| `tests/e2e/test_hs201_12_thought_note_glass.py::test_thought_note_is_one_clean_note[393]` | fixed People read — seam-rerun.xml: readiness-gated request passed | C3 condition payment / this ledger |
| `tests/e2e/test_hs201_one_thing_glass.py::TestQuietDesk::test_cold_arrival_is_quiet[1440]` | fixed People read — seam-rerun.xml: readiness-gated request passed | C3 condition payment / this ledger |
| `tests/e2e/test_hs201_one_thing_glass.py::TestQuietDesk::test_cold_arrival_is_quiet[393]` | fixed People read — seam-rerun.xml: readiness-gated request passed | C3 condition payment / this ledger |
| `tests/e2e/test_hs201_summary_face_glass.py::test_the_summary_is_asked_for_disclosed_and_found_again` | inherited — baseline-audit.json: same confirmed assertion/cause on main | HS201 Meetings / primary-verb count |
| `tests/e2e/test_hs171_shade_glass.py::test_shade_quiet_1440` | inherited — baseline-audit.json: same confirmed assertion/cause on main | HS171 system shade / retained face fences |
| `tests/e2e/test_hs171_shade_glass.py::test_shade_quiet_393` | inherited — baseline-audit.json: same confirmed assertion/cause on main | HS171 system shade / retained face fences |
| `tests/e2e/test_hs172_arrival_glass.py::TestArrivalProposals::test_arrival_confirm_fires` | inherited — baseline-audit.json: same confirmed assertion/cause on main | HS171 system shade / retained face fences |
| `tests/e2e/test_hs175_rhythm_brief_glass.py::TestRhythmWeeklyBrief::test_rhythm_brief_row_with_calendar` | fixed People read — seam-rerun.xml: readiness-gated request passed | C3 condition payment / this ledger |
| `tests/e2e/test_hs175_rhythm_brief_glass.py::TestRhythmWeeklyBrief::test_brief_this_week_section` | fixed People read — seam-rerun.xml: readiness-gated request passed | C3 condition payment / this ledger |
| `tests/e2e/test_hs175_rhythm_brief_glass.py::TestRhythmMondayBrief::test_no_calendar_monday_brief` | fixed People read — seam-rerun.xml: readiness-gated request passed | C3 condition payment / this ledger |
| `tests/e2e/test_hs176_journal_glass.py::test_journal_stream[393-852]` | inherited — baseline-audit.json: same confirmed assertion/cause on main | HS176 Journal / 393 tab access |
| `tests/e2e/test_hs176_journal_glass.py::test_journal_row_open[393-852]` | inherited — baseline-audit.json: same confirmed assertion/cause on main | HS176 Journal / 393 tab access |
| `tests/e2e/test_philo11_05b_meeting_faces_glass.py::TestMeetingFacesGlass::test_the_meeting_faces_and_slack_destinations[1440]` | inherited — baseline-audit.json: same confirmed assertion/cause on main | PHILO 10 Send / setup and result face |
| `tests/e2e/test_philo13_03_needs_you_glass.py::TestOneNeedsYou::test_one_number_everywhere_and_done_moves_all_three[1440]` | fixed project wording — seam-rerun.xml: unchanged A2 rendered fence passed | C3 condition payment / this ledger |
| `tests/e2e/test_philo13_03_needs_you_glass.py::TestOneNeedsYou::test_one_number_everywhere_and_done_moves_all_three[393]` | fixed project wording — seam-rerun.xml: unchanged A2 rendered fence passed | C3 condition payment / this ledger |
| `tests/e2e/test_philo13_06_open_glass.py::TestOneOpenGrammar::test_j1_and_j3_open_in_their_own_windows[1440]` | C3-W handoff — full-python.xml: Intelligence button repeatedly outside viewport at 1440 | Muad’Dib / PHILO-13-13 C3-W / Dock overflow; explicit owner exclusion |
| `tests/e2e/test_philo13_18_type_floor_glass.py::TestTheTypeFloor::test_no_readable_text_under_12px[1440]` | C3-W handoff — full-python.xml: Intelligence button repeatedly outside viewport at 1440 | Muad’Dib / PHILO-13-13 C3-W / Dock overflow; explicit owner exclusion |
| `tests/e2e/test_philo304_thought_foot_reflow.py::test_the_receipt_yields_to_the_verbs[393-None]` | inherited — baseline-audit.json: same confirmed assertion/cause on main | HS141 Thought Workbench / browser boot and compact face |

## Final web suite

The full web run before the last two Dock seams passed 3,149 tests. The final run passed 3,152 of 3,153; `src/pages/cores/__tests__/peopleReopenLens.philo1306.test.tsx` → `Prep → Now → the same open again lands on Prep` failed its immediate Now assertion. It passes twice in isolation (`web-serial-1.txt`, `web-serial-2.txt`), and passed in the earlier full run. Classification (c): intermittent People lens timing; follow-up home PHILO-13-06 People open grammar. No People face source or baseline allowlist changed. `web-final-baseline.txt` honestly reports this one branch-new test name; it is not a green full-web report.
