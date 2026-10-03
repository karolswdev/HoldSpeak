# PR #757 full Python failure ledger

OPEN — recorded by Astra on 2026-10-03; no story flip or merge verdict for these maintenance items.

Full run: **59 failed, 13,926 passed, 117 skipped, 4 xfailed, 4 errors** in 3,856.48 s. [Exact output](full-python.txt), [14,102 collected tests](full-collect.txt). Product revision `210b9f33240d9a5d7281cf1e5744daa8c18c39e5` with only the Zone atlas/fence and review records dirty. Isolated HOME, Node 22, browser and npm caches set; Metal excluded.

Of 63 red nodes, **37 names recur from the prior C3 ledger**, which records its own baseline reproduction. A matching name does not prove the current cause is inherited. Their current causes were not individually re-compared here; prior homes remain open. The remaining 26 were read and assigned below. A focused 14-test comparison on exact main parent `2e4b446c4df66c54b773086b19612c17c71dd1a8` reproduces **12 failures with matching causes**; two cancellation tests pass once. [Collection](baseline-unit-collect.txt), [run](baseline-unit-run.txt). No flake designation is made from one pass. The five-case glass comparison reproduces all three Dock/gadget failures with the same causes; the two editor-rail cases pass. [Collection](baseline-glass-collect.txt), [failure excerpts and run tail](baseline-glass-run-tail.txt). This makes 15 current same-cause baseline reproductions, 37 older named recurrences and 11 currently unclassified nodes.

Follow-up: Astra tracks producer/rig/fence items and Muad’Dib tracks face items. Reproduce unclassified failures under the same execution conditions before attributing them to this branch; fix genuine regressions in their named lane and update stale fixtures only against the real producer. This review does not claim a green full Python suite or complete zero-regression attribution.

## Previously recorded names

[Prior C3 ledger](../story-13-conditions/failure-ledger.md) retains the original proof and homes. Each row below means “same test name recurs”; it is not a fresh main reproduction.

| Exact node | Retained follow-up home |
|---|---|
| `tests/e2e/test_hs176_journal_glass.py::test_journal_filtered[393-852]` | HS176 Journal / 393 tab access |
| `tests/integration/test_web_history_archive.py::test_history_keeps_approval_and_export_governance` | Meetings governance / old ConfirmVerb assertion; PHILO A1 Park face |
| `tests/unit/test_decisions.py::test_meeting_delete_severs_source_without_deleting_decision` | Decision source lifecycle / PHILO A1 Park semantics |
| `tests/e2e/test_hs176_journal_glass.py::test_journal_quiet[393-852]` | HS176 Journal / 393 tab access |
| `tests/integration/test_live_action_item_triage.py::TestLiveFirstResolutionOrder::test_falls_through_to_the_saved_meeting_when_no_live_session_owns_it` | Live action-item triage / archive test double |
| `tests/integration/test_live_action_item_triage.py::TestLiveFirstResolutionOrder::test_saved_meetings_still_work_with_no_live_session_bound_at_all` | Live action-item triage / archive test double |
| `tests/unit/test_hs172_people_sources.py::TestBriefEnrichment::test_last_meeting_present` | People / B4 plain-database fixture schema |
| `tests/unit/test_interior_canon_guard.py::test_no_left_border_rails_in_web_css` | UX canon / CSS rail guard |
| `tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393` | HS176 Speak / correction and compact surface |
| `tests/integration/test_phase200_recipe_catalog.py::TestTheScheduledOwnerReallyFires::test_the_sweep_is_driven_by_a_wall_clock_loop` | Cadence / scheduled-loop source contract |
| `tests/unit/test_graph_walk_calibration.py::test_the_ui_vocabulary_is_closed_and_blocks_before_anything_fires` | Graph rig / action-vocabulary calibration fence |
| `tests/unit/test_people_brief.py::TestBriefAggregation::test_brief_linked_meetings_via_uid_chain` | People / B4 plain-database fixture schema |
| `tests/unit/test_people_brief.py::TestBriefAggregation::test_brief_unlinked_meeting_count_f11` | People / B4 plain-database fixture schema |
| `tests/unit/test_people_brief.py::TestWriteCountSpy::test_brief_writes_zero_rows_to_plain_db` | People / B4 plain-database fixture schema |
| `tests/unit/test_people_brief.py::TestCommitmentTriadUntouched::test_action_items_unchanged_after_brief` | People / B4 plain-database fixture schema |
| `tests/unit/test_phase143_inference_capability_census.py::test_phase143_every_product_runner_entrance_has_one_owner` | Phase 143 inference capability census / stale anchors and classifications |
| `tests/unit/test_phase143_inference_capability_census.py::test_phase143_shared_helpers_have_semantic_callers` | Phase 143 inference capability census / stale anchors and classifications |
| `tests/unit/test_phase200_doc_claims.py::test_registered_claim_matches_its_state[holds:UX-CANON.md:179]` | UX canon and PHILO bus coverage / registered documentation claims |
| `tests/unit/test_phase200_doc_claims.py::test_registered_claim_matches_its_state[holds:useDeskChangedRefresh.ts:15]` | UX canon and PHILO bus coverage / registered documentation claims |
| `tests/unit/test_philo3_summary_detail.py::test_summary_wire_fixture_matches_real_producer_states` | PHILO 3 Meetings / summary wire fixture |
| `tests/unit/test_philo4_01_atlas_contracts.py::test_the_reload_claim_points_at_the_quiet_branch` | PHILO 4 Brief atlas / source-branch claim |
| `tests/unit/test_phase143_routing_authority_census.py::test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer` | Phase 143 routing authority census / stale source classification |
| `tests/unit/test_philo6_01_import_badge.py::test_empty_vtt_import_leaves_import_failed_on_the_wire` | PHILO 6 Meetings / empty-import wire fixture |
| `tests/e2e/test_hs144_door_glass.py::test_hs144_door_empty_and_error_shots[1440]` | HS144 Door / error headline |
| `tests/e2e/test_hs144_door_glass.py::test_hs144_door_empty_and_error_shots[393]` | HS144 Door / error headline |
| `tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[1440-before_guard]` | PHILO 8 rig / expired undo-window outcome |
| `tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[1440-click_wait]` | PHILO 8 rig / expired undo-window outcome |
| `tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[393-before_guard]` | PHILO 8 rig / expired undo-window outcome |
| `tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[393-click_wait]` | PHILO 8 rig / expired undo-window outcome |
| `tests/e2e/test_hs201_summary_face_glass.py::test_the_summary_is_asked_for_disclosed_and_found_again` | HS201 Meetings / primary-verb count |
| `tests/e2e/test_hs171_shade_glass.py::test_shade_quiet_1440` | HS171 system shade / retained face fences |
| `tests/e2e/test_hs171_shade_glass.py::test_shade_quiet_393` | HS171 system shade / retained face fences |
| `tests/e2e/test_hs172_arrival_glass.py::TestArrivalProposals::test_arrival_confirm_fires` | HS171 system shade / retained face fences |
| `tests/e2e/test_hs176_journal_glass.py::test_journal_stream[393-852]` | HS176 Journal / 393 tab access |
| `tests/e2e/test_philo11_05b_meeting_faces_glass.py::TestMeetingFacesGlass::test_the_meeting_faces_and_slack_destinations[1440]` | PHILO 10 Send / setup and result face |
| `tests/e2e/test_hs176_journal_glass.py::test_journal_row_open[393-852]` | HS176 Journal / 393 tab access |
| `tests/e2e/test_philo304_thought_foot_reflow.py::test_the_receipt_yields_to_the_verbs[393-None]` | HS141 Thought Workbench / browser boot and compact face |

## Newly ledgered nodes

| Exact node | Current evidence / classification | Open follow-up home |
|---|---|---|
| `tests/e2e/test_hs175_settings_meetings_glass.py::TestSettingsCalendarSection::test_calendar_section[1440]` | Unclassified against main. Test event lacks attendees; real projection now reads it. | Calendar / #756 attendee fixture maintenance; Astra data, Muad’Dib face fixture |
| `tests/e2e/test_hs175_settings_meetings_glass.py::TestSettingsCalendarSection::test_calendar_section[393]` | Unclassified against main. Test event lacks attendees; real projection now reads it. | Calendar / #756 attendee fixture maintenance; Astra data, Muad’Dib face fixture |
| `tests/e2e/test_hs175_settings_meetings_glass.py::TestSettingsCalendarSection::test_calendar_well_unfold` | Unclassified against main. Test event lacks attendees; real projection now reads it. | Calendar / #756 attendee fixture maintenance; Astra data, Muad’Dib face fixture |
| `tests/e2e/test_hs175_settings_meetings_glass.py::TestSettingsCalendarSection::test_matched_absent_when_zero` | Unclassified against main. Test event lacks attendees; real projection now reads it. | Calendar / #756 attendee fixture maintenance; Astra data, Muad’Dib face fixture |
| `tests/unit/test_desk_locks.py::test_the_front_door_is_the_desk_with_the_guard` | Same cause reproduced on main parent. Fence requires old setup?.arrival_required source string. | Desk arrival / C5 source-fence maintenance; Astra |
| `tests/unit/test_hs175_calendar_sources.py::TestCalendarSourcesRoute::test_source_stats_from_db` | Same cause reproduced on main parent. Test event lacks attendees; real projection now reads it. | Calendar / #756 attendee fixture maintenance; Astra data, Muad’Dib face fixture |
| `tests/unit/test_hs175_calendar_sources.py::TestCalendarSourcesRoute::test_matched_this_week` | Same cause reproduced on main parent. Test event lacks attendees; real projection now reads it. | Calendar / #756 attendee fixture maintenance; Astra data, Muad’Dib face fixture |
| `tests/unit/test_hs175_calendar_sources.py::TestSourcesPayloadClocks::test_event_count_names_what_it_counts` | Same cause reproduced on main parent. Test event lacks attendees; real projection now reads it. | Calendar / #756 attendee fixture maintenance; Astra data, Muad’Dib face fixture |
| `tests/unit/test_hs175_calendar_sources.py::TestSourcesPayloadClocks::test_last_read_is_an_instant_and_a_local_clock` | Same cause reproduced on main parent. Test event lacks attendees; real projection now reads it. | Calendar / #756 attendee fixture maintenance; Astra data, Muad’Dib face fixture |
| `tests/unit/test_hs175_calendar_sources.py::TestSourcesPayloadClocks::test_matched_this_week_uses_the_local_week` | Same cause reproduced on main parent. Test event lacks attendees; real projection now reads it. | Calendar / #756 attendee fixture maintenance; Astra data, Muad’Dib face fixture |
| `tests/unit/test_hs175_calendar_sources.py::TestDstEdgeSources::test_matched_this_week_across_fall_back` | Same cause reproduced on main parent. Test event lacks attendees; real projection now reads it. | Calendar / #756 attendee fixture maintenance; Astra data, Muad’Dib face fixture |
| `tests/integration/test_web_setup_route.py::test_dashboard_owns_first_value_without_redirecting` | Same cause reproduced on main parent. Fence requires old setup?.arrival_required source string. | Desk arrival / C5 source-fence maintenance; Astra |
| `tests/unit/test_one_path_cardinality.py::test_cancellation_after_provider_return_is_one_child_one_receipt_one_physical_attempt` | Unclassified against main. Full run gets cancelled where succeeded is expected; baseline serial passes once. Unclassified. | Runner cancellation boundary; Astra |
| `tests/unit/test_philo10_atlas.py::test_the_counts_over_every_atlas_file` | Same cause reproduced on main parent. Expected counts omit atlas-h-c5.json. | Graph atlas census maintenance; Astra |
| `tests/e2e/test_hs200_coverage_glass.py::TestCoverageGlass::test_shade_coverage_1440` | Unclassified against main. Expected shade-coverage element absent; baseline attribution unverified. | HS200 coverage / shade face; Muad’Dib |
| `tests/unit/test_product_copy.py::test_primary_copy_has_no_prohibited_operational_drift` | Same cause reproduced on main parent. windowSend.tsx:279 lacks retained-work, next-action and destination facts. | PHILO 10 Send refusal copy; Muad’Dib |
| `tests/unit/test_philo9_atlas.py::test_the_counts_over_every_atlas_file` | Same cause reproduced on main parent. Expected counts omit atlas-h-c5.json. | Graph atlas census maintenance; Astra |
| `tests/unit/test_philo9_compat.py::test_the_http_routes_keep_their_envelopes_and_statuses` | Same cause reproduced on main parent. Producer adds latest_published_update_id; fixture expects updates alone. | PHILO 9 project updates envelope fence; Astra |
| `tests/unit/test_residual_service_admission.py::test_a_cancelled_cadence_parent_never_publishes_its_late_draft` | Unclassified against main. Full run has no expected discarded late-draft row; baseline serial passes once. Unclassified. | Cadence cancellation boundary; Astra |
| `tests/e2e/test_hs202_03_species_glass.py::TestSharedControlsAreSpecies::test_menus_dock_and_wings[1440-900]` | Same cause reproduced on main parent (baseline glass receipt). 1440 tab order targets Hide menus instead of More; 393 Agents overlaps More. | PHILO-13-13 C3-W / Dock species; Muad’Dib |
| `tests/e2e/test_hs202_03_species_glass.py::TestSharedControlsAreSpecies::test_menus_dock_and_wings[393-852]` | Same cause reproduced on main parent (baseline glass receipt). 1440 tab order targets Hide menus instead of More; 393 Agents overlaps More. | PHILO-13-13 C3-W / Dock species; Muad’Dib |
| `tests/e2e/test_hs163_steward_glass.py::test_dogfood_run_and_dedup[393]` | Unclassified against main. 393 shot below brittle byte-size bound; 1440 stop waits 15 s. Baseline attribution unverified. | HS163 Steward glass; Muad’Dib |
| `tests/e2e/test_hs163_steward_glass.py::test_stop_mid_run[1440]` | Unclassified against main. 393 shot below brittle byte-size bound; 1440 stop waits 15 s. Baseline attribution unverified. | HS163 Steward glass; Muad’Dib |
| `tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_a_lost_answer_and_every_unreadable_read_are_named[393]` | Unclassified against main. 393 Retry target covered; baseline attribution unverified. | PHILO 10 Send / compact lost-answer face; Muad’Dib |
| `tests/e2e/test_philo11_05b_meeting_faces_glass.py::TestMeetingFacesGlass::test_the_meeting_faces_and_slack_destinations[393]` | Unclassified against main. 393 meeting/Slack glass fails; baseline attribution unverified. | PHILO 11 Meetings / compact Send face; Muad’Dib |
| `tests/e2e/test_philo13_12_gadgets_glass.py::TestTheGadgets::test_gadgets_1440` | Same cause reproduced on main parent (baseline glass receipt). Zoomed G2 resize leaves workspace rect unchanged. | PHILO-13-12 C2 / gadget resize; Muad’Dib |
