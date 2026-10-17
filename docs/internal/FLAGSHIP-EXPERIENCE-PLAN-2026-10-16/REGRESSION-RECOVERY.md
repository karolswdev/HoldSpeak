# Regression recovery — 2026-10-16

Owner instruction: “We need to solve them too!” This queue continues the flagship
programme through the broader failures. An inherited failure stays open until it
is reproduced, fixed and verified, or current evidence proves it already healed.
Tracking alone does not finish this work.

## Additional observed product failures

The 113-case historical CI union below does not include newly diagnosed local
product failures. These stay tracked separately rather than disappearing into
test totals:

- Send Back/edit/reopen displayed newer words above Retry for an older command.
  Reproduced at 1440/393; fixed, merged and delivered in #1236. Exact replay and
  later distinct-send file proof: [Thought and Send](THOUGHT-SEND.md).
- Failure to launch either native cleanup worker hid the unclosed device and
  released the audio floor. Both controlled variants failed before repair;
  current focused proof preserves audio and same-ID save with an unavailable
  floor. [Meeting Stop follow-up](../MEETING-STOP-NATIVE-2026-10-16/POSTMERGE-FOLLOWUP.md).
- A delayed duplicate Meeting Stop changed Saved back to Saving. Controlled
  ordering failed before repair; current proof preserves the winning Saved
  result and one DB row. The same follow-up owns delivery and full-main proof.

## Scope and evidence

- [Prior tape](https://github.com/karolswdev/HoldSpeak/actions/runs/38897233198): 100 failed cases.
- [Brief/source tape](https://github.com/karolswdev/HoldSpeak/actions/runs/38950387547): 103 failed cases.
- [Daily-work tape](https://github.com/karolswdev/HoldSpeak/actions/runs/38957119404): 106 failed cases.
- [Density tape](https://github.com/karolswdev/HoldSpeak/actions/runs/38961799415): **101 failed, 16,356 passed, 69 skipped, 1 expected failure**.
- [Contracts recovery tape](https://github.com/karolswdev/HoldSpeak/actions/runs/38973245716): **82 failed, 16,400 passed, 68 skipped, 1 expected failure** at #1226 (`5c26bd0fa`), before copy/runtime/browser repairs. All 82 failure names already belong to this queue.
- [Final recovery run](https://github.com/karolswdev/HoldSpeak/actions/runs/38985702250): **1 failed, 16,514 passed, 68 skipped, 1 expected failure** at #1232 (`fc02d9b8f`). The remaining failure is R071 below.
- [Runtime recovery run](https://github.com/karolswdev/HoldSpeak/actions/runs/38979062393): **78 failed, 16,434 passed, 68 skipped, 1 expected failure** at #1228 (`58a0d4552`), before the browser repairs. One additional identity is R113.
- Local full main `add3c231c` (#1237): **3 failed, 16,571 passed, 27 skipped,
  1 expected failure**, plus 3 mandatory live-bus passes. Archived trace in
  `wt-main-proof-20261016/.tmp/recovery/main-full-add3c231c.log`. Reopens R093
  and adds R114/R115. [Active follow-up](../MEETING-STOP-NATIVE-2026-10-16/MODULE-FOLLOWUP.md).
- Midnight release check adds R116: the prior-day Brief correctly becomes stale,
  contrary to a test's wall-clock-dependent fresh premise.
- Union: **116 distinct cases** across the recorded CI, local full and release
  runs (113 historical CI identities plus three newly observed local identities).
  Absence is not closure.
- Recovery baseline: `2669d98f2` (#1224). The #1228 [full run](https://github.com/karolswdev/HoldSpeak/actions/runs/38979062393) finished before the browser repairs were included; the #1232 result above supersedes it.
- Focused/quick proof and explicit retired-contract replacements remain below. The full-main run reopened R071; its local pass did not establish the loaded CI transition. [Current repair](THOUGHT-SEND.md).

Delivery source: `/Users/karol/dev/tools/wt-regression-browser-delivery-20261016`.
Earlier candidate work remains preserved in `/Users/karol/dev/tools/wt-regression-recovery-20261016`.
Astra owns the queue, integration and verification. Sol HIGH workers own the three
disjoint investigation/implementation groups. Root serializes isolated test and
browser jobs. The current serving bundle stays frozen during verification.

## Fix groups

| Group | Established cause or open question | Next proof |
| --- | --- | --- |
| Runtime and producers | Journal sequence race across stores; platform-only memory score precision; timezone-dependent Brief fixtures; two stale wire fixtures; restart cache retained a prior bare service database | Focused baseline, deterministic race/rollback checks, exact producer readbacks, preserved memory ranks/content, restart row observation |
| Guards and copy | Shallow nightly history; copy scanner parses callback arrows as visible text; genuine recovery copy/Context labels; missing LAN effect admission; static SQL and concern-budget debt; stale glyph and scratch links | Exact guards plus tests for each changed seam; preserve guard thresholds and actual recovery behavior |
| Browser journeys | Old Go/Dock/window selectors and retired interactions; duplicate unscoped boards; persistent hub windows; remaining geometry/timing candidates | Current-source build, representative reproductions, repaired journeys with original action/result/return assertions, all affected cases |

## Case queue

States are evidence-based. “Observed” refers to the linked CI tape, not a claim
that the same failure was reproduced locally. A test update must follow a proved
product contract; no skips, blanket retries, threshold increases or broad exemptions.

| ID | Group | Case | State / next verification |
| --- | --- | --- | --- |
| R001 | Browser journeys | `tests/e2e/test_agents_glass.py::test_a_compact_line_at_393_keeps_its_ellipsis_in_the_box[long-id]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R002 | Browser journeys | `tests/e2e/test_agents_glass.py::test_a_compact_line_at_393_keeps_its_ellipsis_in_the_box[unbreakable-4000]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R003 | Browser journeys | `tests/e2e/test_askai_glass.py::test_a_refused_send_reads_as_refused[1440]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R004 | Browser journeys | `tests/e2e/test_askai_glass.py::test_a_refused_send_reads_as_refused[393]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R005 | Browser journeys | `tests/e2e/test_askai_glass.py::test_the_ref_chip_x_paints_no_hover_background[1440]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R006 | Browser journeys | `tests/e2e/test_askai_glass.py::test_the_ref_chip_x_paints_no_hover_background[393]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R007 | Browser journeys | `tests/e2e/test_chair_glass.py::TestTheCardInCapture1440::test_card_in_meetings_does_not_move_capture` | Current-source 166-case browser run: passed; delivered in #1231 |
| R008 | Browser journeys | `tests/e2e/test_chair_glass.py::TestTheCardInCapture1440::test_closed_capture_opens_and_holds_the_whole_card` | Current-source 25-case follow-up: passed; delivered in #1231 |
| R009 | Browser journeys | `tests/e2e/test_chair_glass.py::TestTheCardInCapture1440::test_moved_capture_keeps_its_rect_and_the_card_scrolls_whole` | Current-source 166-case browser run: passed; delivered in #1231 |
| R010 | Browser journeys | `tests/e2e/test_chair_glass.py::TestTheCardInCapture1440::test_resized_capture_keeps_its_rect_and_the_card_scrolls_whole` | Current-source 166-case browser run: passed; delivered in #1231 |
| R011 | Browser journeys | `tests/e2e/test_chair_glass.py::TestTheChairAsWindows::test_the_chair_as_windows[1440]` | Final built browser proof: passed; delivered in #1231 |
| R012 | Browser journeys | `tests/e2e/test_chair_glass.py::TestTheChairAsWindows::test_the_chair_as_windows[393]` | Final built browser proof: passed; delivered in #1231 |
| R013 | Browser journeys | `tests/e2e/test_creation_glass.py::TestEveryNewVerbOpensItsWindow::test_a_new_verb_opens_its_window_at_once[1440-chair]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R014 | Browser journeys | `tests/e2e/test_creation_glass.py::TestEveryNewVerbOpensItsWindow::test_a_new_verb_opens_its_window_at_once[393-chair]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R015 | Browser journeys | `tests/e2e/test_creation_glass.py::TestEveryNewVerbOpensItsWindow::test_two_quick_presses_make_one_record[393]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R016 | Browser journeys | `tests/e2e/test_desk_glass.py::TestDeskDebtsGlass::test_the_editor_selection_is_readable[1440]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R017 | Browser journeys | `tests/e2e/test_desk_glass.py::TestDeskDebtsGlass::test_the_editor_selection_is_readable[393]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R018 | Browser journeys | `tests/e2e/test_desk_glass.py::TestDeskDebtsGlass::test_the_thread_composer_selection_is_readable[1440]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R019 | Browser journeys | `tests/e2e/test_desk_glass.py::TestDeskDebtsGlass::test_the_thread_composer_selection_is_readable[393]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R020 | Browser journeys | `tests/e2e/test_desk_glass.py::TestObjectVerbsOnTheChair::test_1440_object_menu_f2_and_right_click` | Current-source 166-case browser run: passed; delivered in #1231 |
| R021 | Browser journeys | `tests/e2e/test_desk_glass.py::TestObjectVerbsOnTheChair::test_393_right_click_opens_the_object_menu` | Current-source 25-case follow-up: passed; delivered in #1231 |
| R022 | Browser journeys | `tests/e2e/test_desk_glass.py::TestOneDesk::test_window_delete_keeps_undo_in_view_with_a_chair_window_open[393]` | Current-source 25-case follow-up: passed; delivered in #1231 |
| R023 | Browser journeys | `tests/e2e/test_desk_glass.py::test_receipt_verbs_own_their_areas[1440]` | Current-source 10-case final follow-up: passed; delivered in #1231 |
| R024 | Browser journeys | `tests/e2e/test_desk_glass.py::test_receipt_verbs_own_their_areas[393]` | Current-source 10-case final follow-up: passed; delivered in #1231 |
| R025 | Browser journeys | `tests/e2e/test_desk_sweep.py::test_every_window_holds_the_fences[surface-cadence-1440]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R026 | Browser journeys | `tests/e2e/test_desk_sweep.py::test_every_window_holds_the_fences[surface-settings@models-393]` | Delivered in #1227; ordinary quick GREEN and desktop/phone recovery/read-state proof pass |
| R027 | Browser journeys | `tests/e2e/test_dock_glass.py::TestDockGlass::test_the_phone_shelf_seats_and_pages_by_touch` | Current-source 166-case browser run: passed; delivered in #1231 |
| R028 | Browser journeys | `tests/e2e/test_dock_glass.py::TestDockPagesOnWholeIcons::test_the_phone_dock_pages_on_whole_icons` | Current-source 166-case browser run: passed; delivered in #1231 |
| R029 | Browser journeys | `tests/e2e/test_dock_glass.py::TestDockTap393::test_a_tap_on_a_paged_dock_presses_that_icon_393[into-view]` | Retired pager contract replaced by current four phone-door parameters (Today/Capture/Meetings/People), all pass; whole-touch ownership and window-seat return pass; delivered in #1231 |
| R030 | Browser journeys | `tests/e2e/test_dock_glass.py::TestDockTap393::test_a_tap_on_a_paged_dock_presses_that_icon_393[more]` | Retired pager contract replaced by current four phone-door parameters (Today/Capture/Meetings/People), all pass; whole-touch ownership and window-seat return pass; delivered in #1231 |
| R031 | Browser journeys | `tests/e2e/test_dock_glass.py::TestDockTap393::test_a_tap_on_a_paged_dock_presses_that_icon_393[swipe]` | Retired pager contract replaced by current four phone-door parameters (Today/Capture/Meetings/People), all pass; whole-touch ownership and window-seat return pass; delivered in #1231 |
| R032 | Browser journeys | `tests/e2e/test_first_use_smoke.py::test_first_use_fence[1440-900]` | Current-source 25-case follow-up: passed; delivered in #1231 |
| R033 | Browser journeys | `tests/e2e/test_first_use_smoke.py::test_first_use_fence[393-852]` | Current-source 25-case follow-up: passed; delivered in #1231 |
| R034 | Browser journeys | `tests/e2e/test_frame_glass.py::TestTheFrame::test_the_frame[393]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R035 | Browser journeys | `tests/e2e/test_frame_glass.py::TestTheGadgets::test_gadgets_393` | Current-source 25-case follow-up: passed; delivered in #1231 |
| R036 | Browser journeys | `tests/e2e/test_frame_glass.py::TestTitleBarB::test_title_bar_b[393]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R037 | Browser journeys | `tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_j9_through_the_real_hub[1440]` | Current-source 25-case follow-up: passed; delivered in #1231 |
| R038 | Browser journeys | `tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_j9_through_the_real_hub[393]` | Current-source 25-case follow-up: passed; delivered in #1231 |
| R039 | Browser journeys | `tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_the_real_atlas[case.j9.shade_receipt_open.rhythm_face]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R040 | Browser journeys | `tests/e2e/test_kit_glass.py::test_every_verb_is_one_plate_height[393]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R041 | Browser journeys | `tests/e2e/test_meetings_glass.py::TestOneMeetingOneWindow::test_one_meeting_opens_in_one_window_from_every_door[1440]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R042 | Browser journeys | `tests/e2e/test_menus_glass.py::TestDoors::test_a_room_falls_to_its_dock_tile_and_comes_back[393]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R043 | Browser journeys | `tests/e2e/test_menus_glass.py::TestDoors::test_ask_ai_comes_back_after_capture_393` | Current-source 166-case browser run: passed; delivered in #1231 |
| R044 | Browser journeys | `tests/e2e/test_menus_glass.py::TestSharedControlsAreSpecies::test_menus_dock_and_wings[393-852]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R045 | Browser journeys | `tests/e2e/test_room_glass.py::TestRoomFaceGlass::test_a_refusal_and_a_lost_answer_are_named_and_retry_stays_with_its_update[1440]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R046 | Browser journeys | `tests/e2e/test_room_glass.py::TestRoomFaceGlass::test_a_refusal_and_a_lost_answer_are_named_and_retry_stays_with_its_update[393]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R047 | Browser journeys | `tests/e2e/test_room_glass.py::TestRoomFaceGlass::test_copy_then_mark_delivered_twice_reads_back_two_rows[1440]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R048 | Browser journeys | `tests/e2e/test_room_glass.py::TestRoomFaceGlass::test_copy_then_mark_delivered_twice_reads_back_two_rows[393]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R049 | Browser journeys | `tests/e2e/test_room_glass.py::TestRoomFaceGlass::test_the_update_list_words_fit_each_lifecycle[1440]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R050 | Browser journeys | `tests/e2e/test_room_glass.py::TestRoomFaceGlass::test_the_update_list_words_fit_each_lifecycle[393]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R051 | Browser journeys | `tests/e2e/test_room_glass.py::test_the_update_draft_wraps[1440]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R052 | Browser journeys | `tests/e2e/test_room_glass.py::test_the_update_draft_wraps[393]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R053 | Browser journeys | `tests/e2e/test_runs_on_glass.py::TestTheRunsOnFooter::test_the_runs_on_receipt_never_runs_into_undo[393]` | Current-source 25-case follow-up: passed; delivered in #1231 |
| R054 | Browser journeys | `tests/e2e/test_runs_on_glass.py::test_astra_review_real_producer[lost_update]` | Current-source 25-case follow-up: passed; delivered in #1231 |
| R055 | Browser journeys | `tests/e2e/test_runs_on_glass.py::test_astra_review_real_producer[meeting_undo]` | Current-source 25-case follow-up: passed; delivered in #1231 |
| R056 | Browser journeys | `tests/e2e/test_runs_on_glass.py::test_astra_review_real_producer[stale_confirmation]` | Current-source 25-case follow-up: passed; delivered in #1231 |
| R057 | Browser journeys | `tests/e2e/test_runs_on_glass.py::test_runs_on_find_on_lan_found_then_use_it_real_scanner[desktop]` | Current-source 25-case follow-up: passed; delivered in #1231 |
| R058 | Browser journeys | `tests/e2e/test_runs_on_glass.py::test_runs_on_find_on_lan_found_then_use_it_real_scanner[phone]` | Current-source 25-case follow-up: passed; delivered in #1231 |
| R059 | Browser journeys | `tests/e2e/test_runs_on_glass.py::test_runs_on_switchboard[desktop]` | Current-source 25-case follow-up: passed; delivered in #1231 |
| R060 | Browser journeys | `tests/e2e/test_runs_on_glass.py::test_runs_on_switchboard[phone]` | Current-source 25-case follow-up: passed; delivered in #1231 |
| R061 | Browser journeys | `tests/e2e/test_screen_glass.py::TestScreenDeleteGlass::test_the_delete_receipt_is_readable_in_the_viewport[393]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R062 | Browser journeys | `tests/e2e/test_screen_glass.py::TestScreenDeleteGlass::test_the_receipt_is_readable_on_a_long_desk_at_393` | Current-source 166-case browser run: passed; delivered in #1231 |
| R063 | Browser journeys | `tests/e2e/test_send_glass.py::TestSendGlass::test_room_pick_when_the_update_read_fails[1440]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R064 | Browser journeys | `tests/e2e/test_settings_glass.py::test_a_held_filter_strip_is_flat[1440]` | Current-source 10-case final follow-up: passed; delivered in #1231 |
| R065 | Browser journeys | `tests/e2e/test_settings_glass.py::test_a_held_filter_strip_is_flat[393]` | Current-source 10-case final follow-up: passed; delivered in #1231 |
| R066 | Browser journeys | `tests/e2e/test_settings_glass.py::test_summary_controls_own_the_row_height[1440]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R067 | Browser journeys | `tests/e2e/test_settings_glass.py::test_summary_controls_own_the_row_height[393]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R068 | Browser journeys | `tests/e2e/test_speak_glass.py::test_the_learned_row_wraps_without_overlap_at_393` | Current-source 166-case browser run: passed; delivered in #1231 |
| R069 | Browser journeys | `tests/e2e/test_thought_glass.py::TestTheThoughtOpensAtOnce::test_one_press_one_window_every_key[1440]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R070 | Browser journeys | `tests/e2e/test_thought_glass.py::TestTheThoughtSends::test_write_a_thought_then_send_it_to_a_folder[1440]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R071 | Browser journeys | `tests/e2e/test_thought_glass.py::TestTheThoughtSends::test_write_a_thought_then_send_it_to_a_folder[393]` | Reopened by full-main #1232. A held authoritative read reproduces the premature footer assertion (1 failed); the repaired desktop/phone check proves exact buffered text and focus before actions (2 passed), with original saved-revision/file/return checks retained. [Thought send](THOUGHT-SEND.md). |
| R072 | Browser journeys | `tests/e2e/test_thought_glass.py::test_thought_workbench_real_glass[1440]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R073 | Browser journeys | `tests/e2e/test_today_glass.py::TestTheTodayWindowSize::test_today_opens_at_its_size_and_keeps_the_size_he_sets` | Current-source 166-case browser run: passed; delivered in #1231 |
| R074 | Browser journeys | `tests/e2e/test_windows_glass.py::TestCloseMeansGone::test_a_meeting_resolved_as_deleted_closes_its_card[1440]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R075 | Browser journeys | `tests/e2e/test_windows_glass.py::TestCloseMeansGone::test_a_meeting_resolved_as_deleted_closes_its_card[393]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R076 | Browser journeys | `tests/e2e/test_windows_glass.py::TestCloseMeansGone::test_every_opener_closes_to_the_desk[393]` | Final built browser proof: passed; delivered in #1231 |
| R077 | Browser journeys | `tests/e2e/test_windows_glass.py::TestCloseMeansGone::test_the_closed_intelligence_window_does_not_swallow_retry[393]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R078 | Browser journeys | `tests/e2e/test_windows_glass.py::TestHubWindows::test_one_desk_two_views` | Current-source 166-case browser run: passed; delivered in #1231 |
| R079 | Browser journeys | `tests/e2e/test_windows_glass.py::TestTheDeskRemembers::test_windows_places_and_drafts_return_after_a_reload[1440]` | Final built browser proof: passed; delivered in #1231 |
| R080 | Browser journeys | `tests/e2e/test_windows_glass.py::TestTheDeskRemembers::test_windows_places_and_drafts_return_after_a_reload[393]` | Final built browser proof: passed; delivered in #1231 |
| R081 | Browser journeys | `tests/e2e/test_windows_glass.py::TestThePhoneDesk::test_the_phone_desk_393` | Final built browser proof: passed; delivered in #1231 |
| R082 | Browser journeys | `tests/e2e/test_windows_glass.py::TestWindowNamesOnGlass::test_the_project_room_is_named_by_its_project_and_393_shows_the_name[393]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R083 | Browser journeys | `tests/e2e/test_windows_glass.py::TestWindowsOpenWell::test_windows_open_clear_and_come_back` | Current-source 166-case browser run: passed; delivered in #1231 |
| R084 | Browser journeys | `tests/e2e/test_windows_glass.py::test_escape_closes_the_strip_menu_not_the_window` | Current-source 166-case browser run: passed; delivered in #1231 |
| R085 | Runtime and producers | `tests/integration/test_desk_chair.py::test_the_rows_the_chair_opens_carry_their_objects` | Verified in #1224; producer and consumer checks passed |
| R086 | Runtime and producers | `tests/integration/test_desk_firstrun.py::test_a_lan_box_as_default_keeps_the_speech_download` | Delivered in #1226; affected checks and ordinary quick checks pass |
| R087 | Runtime and producers | `tests/integration/test_face_wire_fences.py::test_honest_faces_and_arrival_reads` | Verified in #1224; producer and consumer checks passed |
| R088 | Runtime and producers | `tests/integration/test_face_wire_fences.py::test_parked_reads` | Delivered in #1226; affected checks and ordinary quick checks pass |
| R089 | Runtime and producers | `tests/memory_bench/test_memory_bench.py::test_an_engine_that_fails_or_has_no_vectors_changes_nothing` | Delivered in #1226; affected checks and ordinary quick checks pass |
| R090 | Runtime and producers | `tests/memory_bench/test_memory_bench.py::test_no_engine_answer_equals_the_search_before_the_index` | Delivered in #1226; affected checks and ordinary quick checks pass |
| R091 | Runtime and producers | `tests/unit/test_agent_hand.py::test_hand_launches_a_minted_decision_record_with_a_bounded_session_name` | Delivered in #1225; new concurrency/error regressions and quick checks pass |
| R092 | Guards and copy | `tests/unit/test_decisions.py::test_pre_fix_route_answers_500_on_create` | Full-history checkout delivered in #1226; local assertions pass; new CI verification pending |
| R093 | Guards and copy | `tests/unit/test_density_guard.py::test_runtime_modules_stay_single_concern` | Reopened by #1237: runtime module607 exceeds unchanged600 budget. Stop completion moved into its own153-line helper, caller467; AST-equivalent body and27 focused checks pass. Full-main follow-through pending. |
| R094 | Runtime and producers | `tests/unit/test_desk_memory.py::test_the_decision_chain_and_the_carry_survive_a_hub_restart` | Delivered in #1228; 575 affected / 109 sweep / 17 canon GREEN |
| R095 | Guards and copy | `tests/unit/test_doc_drift_guard.py::test_no_live_doc_has_a_dangling_relative_link` | Delivered in #1226; affected checks and ordinary quick checks pass |
| R096 | Guards and copy | `tests/unit/test_graph_reference.py::test_council_revision_holds_the_resolutions_the_join_read` | Full-history checkout delivered in #1226; local assertions pass; new CI verification pending |
| R097 | Guards and copy | `tests/unit/test_kernel_effect_fence.py::test_effect_ledger_is_complete_and_current` | Delivered in #1228; 575 affected / 109 sweep / 17 canon GREEN |
| R098 | Runtime and producers | `tests/unit/test_memory_engine.py::test_an_engine_failure_ends_the_tick_and_recall_stays_whole` | Delivered in #1226; affected checks and ordinary quick checks pass |
| R099 | Runtime and producers | `tests/unit/test_memory_engine.py::test_no_assignment_means_no_engine_and_todays_recall` | Delivered in #1226; affected checks and ordinary quick checks pass |
| R100 | Runtime and producers | `tests/unit/test_memory_slice3_facts.py::test_an_engine_failure_ends_the_pass_and_charges_no_source` | Delivered in #1226; affected checks and ordinary quick checks pass |
| R101 | Runtime and producers | `tests/unit/test_memory_slice3_facts.py::test_no_engine_the_jobs_wait_and_recall_is_unchanged` | Delivered in #1226; affected checks and ordinary quick checks pass |
| R102 | Runtime and producers | `tests/unit/test_memory_slice4_observations.py::test_no_engine_nothing_is_called_and_recall_is_unchanged` | Delivered in #1226; affected checks and ordinary quick checks pass |
| R103 | Runtime and producers | `tests/unit/test_memory_slice5_pages.py::test_no_page_engine_nothing_is_called_written_or_changed` | Delivered in #1226; affected checks and ordinary quick checks pass |
| R104 | Runtime and producers | `tests/unit/test_monday_brief_outcome_words.py::test_failed_operations_make_no_success_line` | Delivered in #1226; affected checks and ordinary quick checks pass |
| R105 | Guards and copy | `tests/unit/test_phase143_surface_fallback_census.py::test_private_backend_route_and_recovery_decisions_are_classified` | Delivered in #1226; affected checks and ordinary quick checks pass |
| R106 | Guards and copy | `tests/unit/test_philo13_18_type_floor_static.py::test_every_glyph_exemption_is_still_a_live_declaration` | Delivered in #1226; affected checks and ordinary quick checks pass |
| R107 | Runtime and producers | `tests/unit/test_philo6_02_brief_truth.py::test_the_real_producer_brief` | Delivered in #1226; affected checks and ordinary quick checks pass |
| R108 | Guards and copy | `tests/unit/test_product_copy.py::test_primary_copy_has_no_prohibited_operational_drift` | Delivered in #1227; ordinary quick GREEN and desktop/phone recovery/read-state proof pass |
| R109 | Guards and copy | `tests/unit/test_product_language.py::test_primary_ui_has_no_new_unqualified_ambiguous_terms` | Delivered in #1227; ordinary quick GREEN and desktop/phone recovery/read-state proof pass |
| R110 | Guards and copy | `tests/unit/test_static_sql_matches_schema.py::test_unchecked_statements_are_named_counted_and_do_not_grow` | Delivered in #1226; affected checks and ordinary quick checks pass |
| R111 | Browser journeys | `tests/e2e/test_thought_glass.py::test_thought_workbench_real_glass[393]` | Current-source 166-case browser run: passed; delivered in #1231 |
| R112 | Runtime and producers | `tests/unit/test_calendar_ingest.py::TestB11BothConductors::test_event_born_row_is_armed_and_started_by_the_136_conductor` | Delivered in #1228; 575 affected / 109 sweep / 17 canon GREEN |
| R113 | Browser journeys | `tests/e2e/test_thought_glass.py::test_thought_note_long_context_and_open_well_never_clip[1440]` | Observed in #1228 full run; no failure in the subsequent #1232 full run. Current 17-case Thought-file run passes, including this retained long-context path. |
| R114 | Runtime and producers | `tests/integration/test_meeting_kill_recovery.py::test_kill_between_checkpoint_and_finalize_recovers_same_identity` | Sealing now retains recovery discovery until the final DB checkpoint. Original SIGKILL/control pair plus durability/Stop/admission coverage:97 passed; exact128,000 PCM bytes and same-ID repeated recovery retained. Full-main follow-through pending. |
| R115 | Runtime and producers | `tests/integration/test_delivery_pr_poll_real_hub.py::test_a_merge_lands_on_the_room_receipt_within_one_poll` | Deterministic read during ledger truncation reproduced the missing flight. Atomic publication passes the original real-hub case and new boundary regression (2); exact identity and poll timing retained. Full-main follow-through pending. |
| R116 | Runtime and producers | `tests/unit/test_monday_brief_service.py::test_a_brief_is_stale_after_a_new_meeting_decision_or_engine` | Controlled midnight counterfactual fails before repair. One evolving clock now covers the brief, events and real assignment producer, with persisted timestamp ordering asserted;126 service checks pass. Product daily-staleness and separate prior-day test unchanged. Full-main follow-through pending. |

## Delivery log

- [#1225](https://github.com/karolswdev/HoldSpeak/pull/1225) merged `f6871e8df`: journal allocation/error-release fix.
  Postmerge review RATIFY. Idle-hub delivery build `6e3600ca4e4d1251`, PID 28926 (since superseded by #1226);
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
- [#1226](https://github.com/karolswdev/HoldSpeak/pull/1226) merged `5c26bd0fa`: static, producer, timezone and golden-contract recovery.
  Formal Astra postmerge review RATIFY; quick **579 affected / 109 sweep / 17 canon**
  (one existing expected failure), plus 11 wire-consumer checks. Build `08b3ac3cbb13ef50`
  is live on port 8765, PID 33619; health, Desk, Conductor and Models return 200.
- Expanded browser checkpoint: **19 passed, 25 failed** (44 cases). Remaining
  failures retain their action/result/return checks and are under active repair.
  The latest tape adds R111/R112; neither is waived.
- LAN checkpoint: 44 checks passed; final transport/caller additions and authenticated
  scanner browser doubles require rerun. Commands review found duplicate-Add recovery
  and unrelated Test retry defects; fixes await execution of their regression cases.
- Restart probe: catalogue module fixture followed by restart passes (2 checks);
  durable row is present before/after reboot and both stores use the current DB.
  The original CI-only restart failure remains open.

- Later runtime proof: a direct service read before hub startup deterministically
  reproduces R094's exact missing durable recall. Each hub now owns its cache;
  **254 memory/calendar checks pass**. The exact original CI predecessor remains
  unknown. Calendar R112 now waits for capture completion and its receipt.
- Phone navigation: mounted-chrome swipe and canonical Today depth restoration
  pass **23 navigation + 11 gadget checks**; actual touch journeys pending.
- Controls checkpoint: **19 passed, 4 failed**; remaining Dock/Agents/Kit checks
  were repaired against current contracts, with Screen Delete and Thought bounds.
  Root's phone decision diagnostic proves Go/Search -> exact Decision -> Object
  submenu exposes Delete. Revised durable Delete/Undo cases await execution.
- Product gaps confirmed behind browser failures: default Chair seats overlap
  because their heights became minimums; retired aftercare effects still open
  Capture; Finished sweep receipts never acquired their promised Activity door.
  First-seat height and parked-effect fixes are ready. Activity canvas was reviewed
  at both widths; direct row buttons replace the prototype's hidden hover verbs.
  No case is closed merely by changing its selector.

- Activity Finished reader: **17 focused checks pass**; exact Rhythm/meeting
  source doors, retained failed reads, paging and stale-response protection.
  Current rebuilt browser group collected **166 cases**, including all recorded
  browser failures and the full parameter set of affected journeys; run active.
- Copy delivery quick: **4,071 web / 16 copy / 17 canon pass**; sweep **108 pass,
  1 fail**, reproducing R026's 104 px movement. TypeScript passes. The missing
  initial-read busy state is under repair; no stillness threshold is changed.

- Rebuilt integrated browser run: **149 passed, 17 failed** (225.89 s).
  Every collected case remains asserted; the remaining failures are split into
  window/settings, Desk/Chair, and setup/engine journeys. The graph receipt
  journeys pass with the real produced receipt and its exact Activity door.
- Legacy restored Chair Brief depth fallback: **18 phone-ring checks pass**;
  canonical Today is restored before falling back to the next available pane.

- R026 causal proof now isolates the speech read: its completion inserts
  **104.19 px** above the model catalogue. Models reports pending initial reads;
  **57 Runs on checks and 3 held-read browser cases pass** in the copy delivery
  tree. The ordinary quick rerun includes this fix.
- Integrated review found and repaired two phone navigation seams: restored
  legacy Brief Depth must reach canonical Today, and Capture's Dock door must
  select its Chair pane even when already open. The latter's two mounted-Dock
  regressions and the remaining 17 browser cases await the next focused run.
- Review exposed a LAN body deadline gap. Three deterministic regressions fail
  against the prior implementation because valid late data becomes a Found row.
  The patch checks expiry around bounded body reads; green verification pending.
  This does not assert a universal HTTP wall-clock bound: urllib header and
  chunk-framing reads remain governed by the socket timeout.

- Copy delivery final ordinary quick is **GREEN: 4,076 web / 16 copy /
  109 browser sweep / 17 canon**. Commands lost-response recovery and exact
  one-row readbacks pass at 1440/393. Desktop/phone sweep shots were inspected.
  Source digest equals build `f6ef8ac2099dde8b`; merge and local delivery next.

- [#1227](https://github.com/karolswdev/HoldSpeak/pull/1227) merged `e834f2c5b`:
  recovery copy, Commands readback and Models initial-read state. Formal review
  RATIFY. Build `f6ef8ac2099dde8b`, PID 63584, is live on port 8765; all four
  health/Desk/Conductor/Models checks return 200. The prior #1226 runtime is stopped.
- LAN body regression green: **59 scanner/effect/route checks pass**, including
  all three tests that failed on late accepted model data before the fix.
  Capture/Today mounted Dock regressions pass **16 checks**. The next rebuilt
  browser group collected 25 cases; execution is active.

- The next 25-case browser run finished **17 passed, 8 failed**. All 11 setup/engine
  cases and both exact Activity receipt cases pass. Remaining cases expose Go
  opener event ordering, a bare/qualified Object Open duplicate, a 16 px phone
  Chair band error, restored-window hit timing, and stale Room/Settings gestures.
  Their existing state, close, draft, hit-target and geometry assertions remain.
- Runtime ordinary quick: **572 pass, 3 fail / 109 sweep / 17 canon**. The three
  notification tests assumed enabled delivery while the isolated runner disables
  native effects. Each enabled-path test will set its own mode with its existing
  transport double; the runner remains disabled. Rerun required before merge.

- Final browser follow-up: **8 passed, 2 failed** (10 cases, 39.67 s). Phone
  work-band geometry, Go second tap, settings state and duplicate-close journey
  pass. Remaining: Room desktop focus and canonical Today/Needs front-window
  proof. Independent review also caught the inverse bare-ID decision door;
  identity deduplication will preserve the existing panel and its state.

- Runtime final ordinary quick is **GREEN: 575 affected / 109 browser sweep /
  17 canon**. Enabled-notification doubles pass with the runner still disabled.
  Desktop/phone shots inspected; source digest equals build `f6ef8ac2099dde8b`.
  Independent runtime source review found no blocking defect; merge next.

- [#1228](https://github.com/karolswdev/HoldSpeak/pull/1228) merged `58a0d4552`.
  Formal Astra postmerge review RATIFY; build `f6ef8ac2099dde8b`, PID 76313,
  is live on port 8765. Health, Desk, Conductor and Models return 200.
  Runtime recovery is delivered; browser recovery remains active.
- Go event ownership and both directions of bare/qualified record reopening
  pass **34 focused checks**. Existing window keys, saved geometry, drafts,
  collision separation and minimized restoration are preserved.

- Final type check passes; all **639 graph atlas checks pass** after naming the
  actual controls in the case selectors. Final browser proof: **10 passed, 1 failed**
  (68.47 s). All remaining prior window cases pass, including remembered drafts
  and phone front ownership. The new Activity return case passes at 1440 but
  finds Back leaves Rhythm open at 393; this added finding remains under repair.
  Actual Activity desktop/phone and returned desktop shots were inspected.

- Phone return cause confirmed by the DB-backed window read: Back cleared an
  unnecessary `service:HeartbeatService` scope rather than closing Rhythm.
  Activity now opens this unscoped face without a scope; exact meeting scopes
  remain. **17 Activity checks, type check, and both actual return cases pass**
  (9.50 s). The added strict one-Back, exact-row and nine-hit-point proof stays.

- The #1226 full tape finished: **82 failed / 16,400 passed / 68 skipped /
  1 existing expected failure**. All 82 case names are already tracked; this
  run predates #1227, #1228 and the browser batch. It adds no new case and does
  not establish the status of the repaired current head.
- Visual review found an additional Room evidence-claim ink defect: an undefined
  `--text-primary` token falls back to near-white on pale paper. A bounded repair
  to existing scoped `--text` and rendered contrast proof are in preparation.
  This local finding is separate from the 112 historical CI case identities.

- Integrated ordinary quick: **4,169 web / 180 affected / 109 sweep / 17 canon
  pass; 3 affected cases fail**. Two desktop Object-hover cases still fail to
  expose Delete; one receipt test selects two same-title records from its shared
  fixture. All three remain asserted and under repair.
- Room claim proof fails on the original bundle at **1.028:1 contrast** at both
  widths while existing wrap/line-end assertions pass. The scoped-ink fix is
  applied; rebuilt green proof and actual shots remain.

- Room claim ink is now verified at both widths: **2 pass** after both fail on
  the original colors. The same rendered claim measures **17.12:1** contrast
  with scoped ink; root inspected actual 1440/393 shots and preserved the editor
  wrapping/line-end assertions. Delivery remains coupled to the browser batch.

- The three additional Desk failures are resolved. Actual pointer observations
  prove hover opens the submenu; the desktop Delete keyboard hint changes its
  accessible name, so tests identify the exact visible verb inside that submenu.
  The shared receipt hub now uses a distinct title per width and retains the
  created source ID. **All six desktop/phone cases pass together on one worker**
  (78.77 s), with deletion, Undo, selected-row return and nine-hit checks intact.
  The ordinary integrated quick is being rerun.

- Ordinary quick is **GREEN: 4,169 web / 183 affected / 109 sweep / 17 canon**
  on build `28f31330014af5fd`. A prior attempt had a root-created missing pytest
  retention directory and ran no Python checks; after correcting the directory,
  the unmodified ordinary script completed successfully.
- Final screenshot review adds a local Activity reading defect: the phone's
  `SWEEP 2 ROOMS` title is squeezed to four characters beside outcome/egress
  chips. The exact source journey works, but visual readability is insufficient.
  Move the badges to the existing wrapping child row and retain a full-width
  title/detail; focused old/new browser proof and final verification remain.

- Activity title proof reproduces **56 px available / 109 px needed** on the
  original phone row (desktop passes). After moving badges/action into the
  existing wrapping child row, **both layout cases and both real producer
  return cases pass** (4 checks, 17.79 s); 17 Activity checks and TypeScript pass.
  Root inspected both actual corrected shots. Final ordinary quick runs against
  the last green commit `83522911b`, covering this bounded final delta.

- Final delta ordinary quick is **GREEN: 4,117 related web / 109 sweep /
  17 canon**, against last green `83522911b`. This follows the broad green
  **4,169 web / 183 affected / 109 sweep / 17 canon** run. Current source/build
  match `372447f4cba801bb`; actual corrected 1440/393 shots inspected. Merge and
  authorized idle-hub delivery are next.

- [#1231](https://github.com/karolswdev/HoldSpeak/pull/1231) merged
  `9079a4be2f3faf88de453e6544802ebec1f5426c`. Formal Astra postmerge review
  [RATIFY](https://github.com/karolswdev/HoldSpeak/pull/1231#issuecomment-6227157015).
  Browser recovery, Room ink and readable Activity titles are delivered.
  Idle-hub delivery: PID 16443, build `372447f4cba801bb`, port 8765; health,
  Desk, Conductor and Models return 200. Verified tree
  `4b1bb15dd5c3e9919a47a108508455a981791d0e` equals the merged source.
  The #1229 orbital places are preserved.
- Full-main follow-up [38985257857](https://github.com/karolswdev/HoldSpeak/actions/runs/38985257857)
  targets the #1231 merge and is queued. The #1228 tape is still in progress.
  No full-main green or owner visual acceptance is claimed.
  [Delivery record](POSTMERGE-RECOVERY.md).
