# Regression recovery — 2026-10-16

Owner instruction: “We need to solve them too!” This queue continues the flagship
programme through the broader failures. An inherited failure stays open until it
is reproduced, fixed and verified, or current evidence proves it already healed.
Tracking alone does not finish this work.

## Scope and evidence

- [Prior tape](https://github.com/karolswdev/HoldSpeak/actions/runs/38897233198): 100 failed cases.
- [Brief/source tape](https://github.com/karolswdev/HoldSpeak/actions/runs/38950387547): 103 failed cases.
- [Daily-work tape](https://github.com/karolswdev/HoldSpeak/actions/runs/38957119404): 106 failed cases.
- Union: **110 distinct cases**. Four appear only in earlier tapes; absence is not closure.
- Recovery baseline: `2669d98f2` (#1224). Its [full run](https://github.com/karolswdev/HoldSpeak/actions/runs/38961799415) is in progress.
- Two producer cases were already verified by #1224. Every other case below needs current evidence.

Working tree: `/Users/karol/dev/tools/wt-regression-recovery-20261016`.
Astra owns the queue, integration and verification. Sol HIGH workers own the three
disjoint investigation/implementation groups. Root serializes isolated test and
browser jobs. The serving density bundle stays frozen during verification.

## Fix groups

| Group | Established cause or open question | Next proof |
| --- | --- | --- |
| Runtime and producers | Journal sequence race across stores; platform-only memory score precision; timezone-dependent Brief fixtures; two stale wire fixtures; restart last-known recall unresolved | Focused baseline, deterministic race/rollback checks, exact producer readbacks, preserved memory ranks/content, restart row observation |
| Guards and copy | Shallow nightly history; copy scanner parses callback arrows as visible text; genuine recovery copy/Context labels; missing LAN effect admission; static SQL and concern-budget debt; stale glyph and scratch links | Exact guards plus tests for each changed seam; preserve guard thresholds and actual recovery behavior |
| Browser journeys | Old Go/Dock/window selectors and retired interactions; duplicate unscoped boards; persistent hub windows; remaining geometry/timing candidates | Current-source build, representative reproductions, repaired journeys with original action/result/return assertions, all affected cases |

## Case queue

States are evidence-based. “Observed” refers to the linked CI tape, not a claim
that the same failure was reproduced locally. A test update must follow a proved
product contract; no skips, blanket retries, threshold increases or broad exemptions.

| ID | Group | Case | State / next verification |
| --- | --- | --- | --- |
| R001 | Browser journeys | `tests/e2e/test_agents_glass.py::test_a_compact_line_at_393_keeps_its_ellipsis_in_the_box[long-id]` | Observed in latest completed tape; focused reproduction queued |
| R002 | Browser journeys | `tests/e2e/test_agents_glass.py::test_a_compact_line_at_393_keeps_its_ellipsis_in_the_box[unbreakable-4000]` | Observed in latest completed tape; focused reproduction queued |
| R003 | Browser journeys | `tests/e2e/test_askai_glass.py::test_a_refused_send_reads_as_refused[1440]` | Observed in latest completed tape; focused reproduction queued |
| R004 | Browser journeys | `tests/e2e/test_askai_glass.py::test_a_refused_send_reads_as_refused[393]` | Observed in latest completed tape; focused reproduction queued |
| R005 | Browser journeys | `tests/e2e/test_askai_glass.py::test_the_ref_chip_x_paints_no_hover_background[1440]` | Observed in latest completed tape; focused reproduction queued |
| R006 | Browser journeys | `tests/e2e/test_askai_glass.py::test_the_ref_chip_x_paints_no_hover_background[393]` | Observed in latest completed tape; focused reproduction queued |
| R007 | Browser journeys | `tests/e2e/test_chair_glass.py::TestTheCardInCapture1440::test_card_in_meetings_does_not_move_capture` | Observed in latest completed tape; focused reproduction queued |
| R008 | Browser journeys | `tests/e2e/test_chair_glass.py::TestTheCardInCapture1440::test_closed_capture_opens_and_holds_the_whole_card` | Observed in latest completed tape; focused reproduction queued |
| R009 | Browser journeys | `tests/e2e/test_chair_glass.py::TestTheCardInCapture1440::test_moved_capture_keeps_its_rect_and_the_card_scrolls_whole` | Observed in latest completed tape; focused reproduction queued |
| R010 | Browser journeys | `tests/e2e/test_chair_glass.py::TestTheCardInCapture1440::test_resized_capture_keeps_its_rect_and_the_card_scrolls_whole` | Observed in latest completed tape; focused reproduction queued |
| R011 | Browser journeys | `tests/e2e/test_chair_glass.py::TestTheChairAsWindows::test_the_chair_as_windows[1440]` | Observed in latest completed tape; focused reproduction queued |
| R012 | Browser journeys | `tests/e2e/test_chair_glass.py::TestTheChairAsWindows::test_the_chair_as_windows[393]` | Observed in latest completed tape; focused reproduction queued |
| R013 | Browser journeys | `tests/e2e/test_creation_glass.py::TestEveryNewVerbOpensItsWindow::test_a_new_verb_opens_its_window_at_once[1440-chair]` | Observed in latest completed tape; focused reproduction queued |
| R014 | Browser journeys | `tests/e2e/test_creation_glass.py::TestEveryNewVerbOpensItsWindow::test_a_new_verb_opens_its_window_at_once[393-chair]` | Reproduced on current bundle; journey repair in progress |
| R015 | Browser journeys | `tests/e2e/test_creation_glass.py::TestEveryNewVerbOpensItsWindow::test_two_quick_presses_make_one_record[393]` | Observed in latest completed tape; focused reproduction queued |
| R016 | Browser journeys | `tests/e2e/test_desk_glass.py::TestDeskDebtsGlass::test_the_editor_selection_is_readable[1440]` | Observed in latest completed tape; focused reproduction queued |
| R017 | Browser journeys | `tests/e2e/test_desk_glass.py::TestDeskDebtsGlass::test_the_editor_selection_is_readable[393]` | Observed in latest completed tape; focused reproduction queued |
| R018 | Browser journeys | `tests/e2e/test_desk_glass.py::TestDeskDebtsGlass::test_the_thread_composer_selection_is_readable[1440]` | Observed in latest completed tape; focused reproduction queued |
| R019 | Browser journeys | `tests/e2e/test_desk_glass.py::TestDeskDebtsGlass::test_the_thread_composer_selection_is_readable[393]` | Observed in latest completed tape; focused reproduction queued |
| R020 | Browser journeys | `tests/e2e/test_desk_glass.py::TestObjectVerbsOnTheChair::test_1440_object_menu_f2_and_right_click` | Observed in latest completed tape; focused reproduction queued |
| R021 | Browser journeys | `tests/e2e/test_desk_glass.py::TestObjectVerbsOnTheChair::test_393_right_click_opens_the_object_menu` | Observed in latest completed tape; focused reproduction queued |
| R022 | Browser journeys | `tests/e2e/test_desk_glass.py::TestOneDesk::test_window_delete_keeps_undo_in_view_with_a_chair_window_open[393]` | Observed in latest completed tape; focused reproduction queued |
| R023 | Browser journeys | `tests/e2e/test_desk_glass.py::test_receipt_verbs_own_their_areas[1440]` | Observed in latest completed tape; focused reproduction queued |
| R024 | Browser journeys | `tests/e2e/test_desk_glass.py::test_receipt_verbs_own_their_areas[393]` | Observed in latest completed tape; focused reproduction queued |
| R025 | Browser journeys | `tests/e2e/test_desk_sweep.py::test_every_window_holds_the_fences[surface-cadence-1440]` | Observed in earlier tape only; current reproduction queued |
| R026 | Browser journeys | `tests/e2e/test_desk_sweep.py::test_every_window_holds_the_fences[surface-settings@models-393]` | Passed focused current-bundle run; intermittent CI motion remains under review |
| R027 | Browser journeys | `tests/e2e/test_dock_glass.py::TestDockGlass::test_the_phone_shelf_seats_and_pages_by_touch` | Observed in latest completed tape; focused reproduction queued |
| R028 | Browser journeys | `tests/e2e/test_dock_glass.py::TestDockPagesOnWholeIcons::test_the_phone_dock_pages_on_whole_icons` | Observed in latest completed tape; focused reproduction queued |
| R029 | Browser journeys | `tests/e2e/test_dock_glass.py::TestDockTap393::test_a_tap_on_a_paged_dock_presses_that_icon_393[into-view]` | Observed in latest completed tape; focused reproduction queued |
| R030 | Browser journeys | `tests/e2e/test_dock_glass.py::TestDockTap393::test_a_tap_on_a_paged_dock_presses_that_icon_393[more]` | Observed in latest completed tape; focused reproduction queued |
| R031 | Browser journeys | `tests/e2e/test_dock_glass.py::TestDockTap393::test_a_tap_on_a_paged_dock_presses_that_icon_393[swipe]` | Observed in latest completed tape; focused reproduction queued |
| R032 | Browser journeys | `tests/e2e/test_first_use_smoke.py::test_first_use_fence[1440-900]` | Reproduced on current bundle; journey repair in progress |
| R033 | Browser journeys | `tests/e2e/test_first_use_smoke.py::test_first_use_fence[393-852]` | Observed in latest completed tape; focused reproduction queued |
| R034 | Browser journeys | `tests/e2e/test_frame_glass.py::TestTheFrame::test_the_frame[393]` | Observed in latest completed tape; focused reproduction queued |
| R035 | Browser journeys | `tests/e2e/test_frame_glass.py::TestTheGadgets::test_gadgets_393` | Observed in latest completed tape; focused reproduction queued |
| R036 | Browser journeys | `tests/e2e/test_frame_glass.py::TestTitleBarB::test_title_bar_b[393]` | Observed in latest completed tape; focused reproduction queued |
| R037 | Browser journeys | `tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_j9_through_the_real_hub[1440]` | Observed in latest completed tape; focused reproduction queued |
| R038 | Browser journeys | `tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_j9_through_the_real_hub[393]` | Observed in latest completed tape; focused reproduction queued |
| R039 | Browser journeys | `tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_the_real_atlas[case.j9.shade_receipt_open.rhythm_face]` | Observed in latest completed tape; focused reproduction queued |
| R040 | Browser journeys | `tests/e2e/test_kit_glass.py::test_every_verb_is_one_plate_height[393]` | Observed in latest completed tape; focused reproduction queued |
| R041 | Browser journeys | `tests/e2e/test_meetings_glass.py::TestOneMeetingOneWindow::test_one_meeting_opens_in_one_window_from_every_door[1440]` | Observed in latest completed tape; focused reproduction queued |
| R042 | Browser journeys | `tests/e2e/test_menus_glass.py::TestDoors::test_a_room_falls_to_its_dock_tile_and_comes_back[393]` | Observed in latest completed tape; focused reproduction queued |
| R043 | Browser journeys | `tests/e2e/test_menus_glass.py::TestDoors::test_ask_ai_comes_back_after_capture_393` | Observed in latest completed tape; focused reproduction queued |
| R044 | Browser journeys | `tests/e2e/test_menus_glass.py::TestSharedControlsAreSpecies::test_menus_dock_and_wings[393-852]` | Observed in latest completed tape; focused reproduction queued |
| R045 | Browser journeys | `tests/e2e/test_room_glass.py::TestRoomFaceGlass::test_a_refusal_and_a_lost_answer_are_named_and_retry_stays_with_its_update[1440]` | Observed in latest completed tape; focused reproduction queued |
| R046 | Browser journeys | `tests/e2e/test_room_glass.py::TestRoomFaceGlass::test_a_refusal_and_a_lost_answer_are_named_and_retry_stays_with_its_update[393]` | Observed in latest completed tape; focused reproduction queued |
| R047 | Browser journeys | `tests/e2e/test_room_glass.py::TestRoomFaceGlass::test_copy_then_mark_delivered_twice_reads_back_two_rows[1440]` | Observed in latest completed tape; focused reproduction queued |
| R048 | Browser journeys | `tests/e2e/test_room_glass.py::TestRoomFaceGlass::test_copy_then_mark_delivered_twice_reads_back_two_rows[393]` | Observed in latest completed tape; focused reproduction queued |
| R049 | Browser journeys | `tests/e2e/test_room_glass.py::TestRoomFaceGlass::test_the_update_list_words_fit_each_lifecycle[1440]` | Observed in latest completed tape; focused reproduction queued |
| R050 | Browser journeys | `tests/e2e/test_room_glass.py::TestRoomFaceGlass::test_the_update_list_words_fit_each_lifecycle[393]` | Observed in latest completed tape; focused reproduction queued |
| R051 | Browser journeys | `tests/e2e/test_room_glass.py::test_the_update_draft_wraps[1440]` | Reproduced on current bundle; journey repair in progress |
| R052 | Browser journeys | `tests/e2e/test_room_glass.py::test_the_update_draft_wraps[393]` | Observed in latest completed tape; focused reproduction queued |
| R053 | Browser journeys | `tests/e2e/test_runs_on_glass.py::TestTheRunsOnFooter::test_the_runs_on_receipt_never_runs_into_undo[393]` | Observed in latest completed tape; focused reproduction queued |
| R054 | Browser journeys | `tests/e2e/test_runs_on_glass.py::test_astra_review_real_producer[lost_update]` | Observed in latest completed tape; focused reproduction queued |
| R055 | Browser journeys | `tests/e2e/test_runs_on_glass.py::test_astra_review_real_producer[meeting_undo]` | Observed in latest completed tape; focused reproduction queued |
| R056 | Browser journeys | `tests/e2e/test_runs_on_glass.py::test_astra_review_real_producer[stale_confirmation]` | Observed in latest completed tape; focused reproduction queued |
| R057 | Browser journeys | `tests/e2e/test_runs_on_glass.py::test_runs_on_find_on_lan_found_then_use_it_real_scanner[desktop]` | Observed in latest completed tape; focused reproduction queued |
| R058 | Browser journeys | `tests/e2e/test_runs_on_glass.py::test_runs_on_find_on_lan_found_then_use_it_real_scanner[phone]` | Observed in latest completed tape; focused reproduction queued |
| R059 | Browser journeys | `tests/e2e/test_runs_on_glass.py::test_runs_on_switchboard[desktop]` | Reproduced on current bundle; journey repair in progress |
| R060 | Browser journeys | `tests/e2e/test_runs_on_glass.py::test_runs_on_switchboard[phone]` | Observed in latest completed tape; focused reproduction queued |
| R061 | Browser journeys | `tests/e2e/test_screen_glass.py::TestScreenDeleteGlass::test_the_delete_receipt_is_readable_in_the_viewport[393]` | Observed in latest completed tape; focused reproduction queued |
| R062 | Browser journeys | `tests/e2e/test_screen_glass.py::TestScreenDeleteGlass::test_the_receipt_is_readable_on_a_long_desk_at_393` | Observed in latest completed tape; focused reproduction queued |
| R063 | Browser journeys | `tests/e2e/test_send_glass.py::TestSendGlass::test_room_pick_when_the_update_read_fails[1440]` | Observed in earlier tape only; current reproduction queued |
| R064 | Browser journeys | `tests/e2e/test_settings_glass.py::test_a_held_filter_strip_is_flat[1440]` | Observed in latest completed tape; focused reproduction queued |
| R065 | Browser journeys | `tests/e2e/test_settings_glass.py::test_a_held_filter_strip_is_flat[393]` | Observed in latest completed tape; focused reproduction queued |
| R066 | Browser journeys | `tests/e2e/test_settings_glass.py::test_summary_controls_own_the_row_height[1440]` | Reproduced on current bundle; journey repair in progress |
| R067 | Browser journeys | `tests/e2e/test_settings_glass.py::test_summary_controls_own_the_row_height[393]` | Observed in latest completed tape; focused reproduction queued |
| R068 | Browser journeys | `tests/e2e/test_speak_glass.py::test_the_learned_row_wraps_without_overlap_at_393` | Observed in latest completed tape; focused reproduction queued |
| R069 | Browser journeys | `tests/e2e/test_thought_glass.py::TestTheThoughtOpensAtOnce::test_one_press_one_window_every_key[1440]` | Observed in latest completed tape; focused reproduction queued |
| R070 | Browser journeys | `tests/e2e/test_thought_glass.py::TestTheThoughtSends::test_write_a_thought_then_send_it_to_a_folder[1440]` | Observed in earlier tape only; current reproduction queued |
| R071 | Browser journeys | `tests/e2e/test_thought_glass.py::TestTheThoughtSends::test_write_a_thought_then_send_it_to_a_folder[393]` | Observed in latest completed tape; focused reproduction queued |
| R072 | Browser journeys | `tests/e2e/test_thought_glass.py::test_thought_workbench_real_glass[1440]` | Observed in earlier tape only; current reproduction queued |
| R073 | Browser journeys | `tests/e2e/test_today_glass.py::TestTheTodayWindowSize::test_today_opens_at_its_size_and_keeps_the_size_he_sets` | Reproduced on current bundle; journey repair in progress |
| R074 | Browser journeys | `tests/e2e/test_windows_glass.py::TestCloseMeansGone::test_a_meeting_resolved_as_deleted_closes_its_card[1440]` | Observed in latest completed tape; focused reproduction queued |
| R075 | Browser journeys | `tests/e2e/test_windows_glass.py::TestCloseMeansGone::test_a_meeting_resolved_as_deleted_closes_its_card[393]` | Observed in latest completed tape; focused reproduction queued |
| R076 | Browser journeys | `tests/e2e/test_windows_glass.py::TestCloseMeansGone::test_every_opener_closes_to_the_desk[393]` | Observed in latest completed tape; focused reproduction queued |
| R077 | Browser journeys | `tests/e2e/test_windows_glass.py::TestCloseMeansGone::test_the_closed_intelligence_window_does_not_swallow_retry[393]` | Observed in latest completed tape; focused reproduction queued |
| R078 | Browser journeys | `tests/e2e/test_windows_glass.py::TestHubWindows::test_one_desk_two_views` | Observed in latest completed tape; focused reproduction queued |
| R079 | Browser journeys | `tests/e2e/test_windows_glass.py::TestTheDeskRemembers::test_windows_places_and_drafts_return_after_a_reload[1440]` | Observed in latest completed tape; focused reproduction queued |
| R080 | Browser journeys | `tests/e2e/test_windows_glass.py::TestTheDeskRemembers::test_windows_places_and_drafts_return_after_a_reload[393]` | Observed in latest completed tape; focused reproduction queued |
| R081 | Browser journeys | `tests/e2e/test_windows_glass.py::TestThePhoneDesk::test_the_phone_desk_393` | Observed in latest completed tape; focused reproduction queued |
| R082 | Browser journeys | `tests/e2e/test_windows_glass.py::TestWindowNamesOnGlass::test_the_project_room_is_named_by_its_project_and_393_shows_the_name[393]` | Observed in latest completed tape; focused reproduction queued |
| R083 | Browser journeys | `tests/e2e/test_windows_glass.py::TestWindowsOpenWell::test_windows_open_clear_and_come_back` | Observed in latest completed tape; focused reproduction queued |
| R084 | Browser journeys | `tests/e2e/test_windows_glass.py::test_escape_closes_the_strip_menu_not_the_window` | Reproduced on current bundle; journey repair in progress |
| R085 | Runtime and producers | `tests/integration/test_desk_chair.py::test_the_rows_the_chair_opens_carry_their_objects` | Verified in #1224; producer and consumer checks passed |
| R086 | Runtime and producers | `tests/integration/test_desk_firstrun.py::test_a_lan_box_as_default_keeps_the_speech_download` | Focused check passes after fix; awaiting delivery |
| R087 | Runtime and producers | `tests/integration/test_face_wire_fences.py::test_honest_faces_and_arrival_reads` | Verified in #1224; producer and consumer checks passed |
| R088 | Runtime and producers | `tests/integration/test_face_wire_fences.py::test_parked_reads` | Focused check passes after fix; awaiting delivery |
| R089 | Runtime and producers | `tests/memory_bench/test_memory_bench.py::test_an_engine_that_fails_or_has_no_vectors_changes_nothing` | Focused check passes after fix; awaiting delivery |
| R090 | Runtime and producers | `tests/memory_bench/test_memory_bench.py::test_no_engine_answer_equals_the_search_before_the_index` | Focused check passes after fix; awaiting delivery |
| R091 | Runtime and producers | `tests/unit/test_agent_hand.py::test_hand_launches_a_minted_decision_record_with_a_bounded_session_name` | Delivered in #1225; new concurrency/error regressions and quick checks pass |
| R092 | Guards and copy | `tests/unit/test_decisions.py::test_pre_fix_route_answers_500_on_create` | Full-history checkout fix prepared; local historical assertions pass; CI verification pending |
| R093 | Guards and copy | `tests/unit/test_density_guard.py::test_runtime_modules_stay_single_concern` | Focused check passes after fix; awaiting delivery |
| R094 | Runtime and producers | `tests/unit/test_desk_memory.py::test_the_decision_chain_and_the_carry_survive_a_hub_restart` | Passed local focused run; CI cause still open |
| R095 | Guards and copy | `tests/unit/test_doc_drift_guard.py::test_no_live_doc_has_a_dangling_relative_link` | Focused check passes after fix; awaiting delivery |
| R096 | Guards and copy | `tests/unit/test_graph_reference.py::test_council_revision_holds_the_resolutions_the_join_read` | Full-history checkout fix prepared; local historical assertions pass; CI verification pending |
| R097 | Guards and copy | `tests/unit/test_kernel_effect_fence.py::test_effect_ledger_is_complete_and_current` | Reproduced locally; fix in progress |
| R098 | Runtime and producers | `tests/unit/test_memory_engine.py::test_an_engine_failure_ends_the_tick_and_recall_stays_whole` | Focused check passes after fix; awaiting delivery |
| R099 | Runtime and producers | `tests/unit/test_memory_engine.py::test_no_assignment_means_no_engine_and_todays_recall` | Focused check passes after fix; awaiting delivery |
| R100 | Runtime and producers | `tests/unit/test_memory_slice3_facts.py::test_an_engine_failure_ends_the_pass_and_charges_no_source` | Focused check passes after fix; awaiting delivery |
| R101 | Runtime and producers | `tests/unit/test_memory_slice3_facts.py::test_no_engine_the_jobs_wait_and_recall_is_unchanged` | Focused check passes after fix; awaiting delivery |
| R102 | Runtime and producers | `tests/unit/test_memory_slice4_observations.py::test_no_engine_nothing_is_called_and_recall_is_unchanged` | Focused check passes after fix; awaiting delivery |
| R103 | Runtime and producers | `tests/unit/test_memory_slice5_pages.py::test_no_page_engine_nothing_is_called_written_or_changed` | Focused check passes after fix; awaiting delivery |
| R104 | Runtime and producers | `tests/unit/test_monday_brief_outcome_words.py::test_failed_operations_make_no_success_line` | Reproduced under UTC; fixed and verified (52 checks); awaiting delivery |
| R105 | Guards and copy | `tests/unit/test_phase143_surface_fallback_census.py::test_private_backend_route_and_recovery_decisions_are_classified` | Focused check passes after fix; awaiting delivery |
| R106 | Guards and copy | `tests/unit/test_philo13_18_type_floor_static.py::test_every_glyph_exemption_is_still_a_live_declaration` | Focused check passes after fix; awaiting delivery |
| R107 | Runtime and producers | `tests/unit/test_philo6_02_brief_truth.py::test_the_real_producer_brief` | Reproduced under UTC; fixed and verified (52 checks); awaiting delivery |
| R108 | Guards and copy | `tests/unit/test_product_copy.py::test_primary_copy_has_no_prohibited_operational_drift` | Reproduced locally; fix in progress |
| R109 | Guards and copy | `tests/unit/test_product_language.py::test_primary_ui_has_no_new_unqualified_ambiguous_terms` | Reproduced locally; fix in progress |
| R110 | Guards and copy | `tests/unit/test_static_sql_matches_schema.py::test_unchecked_statements_are_named_counted_and_do_not_grow` | Focused check passes after fix; awaiting delivery |

## Delivery log

- [#1225](https://github.com/karolswdev/HoldSpeak/pull/1225) merged `f6871e8df`: journal allocation/error-release fix.
  Postmerge review RATIFY. Idle-hub delivery build `6e3600ca4e4d1251`, PID 28926;
  health, Desk, Conductor and Models return 200. Broader recovery stays active.
- Local collection selected all 26 nonbrowser cases. Focused baseline: **10 failed,
  16 passed** (13.39 s). CI-specific causes remain open where local tests passed.
  Current-source browser bundle built; eight representative cases: **7 failed, 1 passed**
  (57.30 s). The Models motion case passed; the seven journey failures reproduced.
- Journal regressions: all three fail against the original function. Runtime/static
  batch: **547 passed, 2 existing model-dependent skips, 1 existing expected failure**
  (14.71 s). No skip/expected-failure policy was changed.
- Brief producer fixtures: original UTC run reproduced both failures; timezone-pinned
  versions pass **52 checks** under UTC, preserving exact stored payload equality.
- Journal-only delivery is being checked separately; other recovery fixes remain in
  the working tree until their own delivery checks pass.
- Restart probe: catalogue module fixture followed by restart passes (2 checks);
  durable row is present before/after reboot and both stores use the current DB.
  The original CI-only restart failure remains open.
