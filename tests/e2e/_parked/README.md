# Parked glass fences: the Floor (PHILO-17, 2026-10-10)

Owner ruling, verbatim: "Yes, everything must become one desk." The Screen is
the one desk; the spatial Floor, its desk-wide list and the Chair/Floor switch
are parked (`web/src/desk/_parked/floor/`). These fences assert only that
face, so their subject is gone. They are kept, not run (`conftest.py`).

- `test_floor_list_select_info_glass.py`: the Floor list (select, Get Info, Rename, Filed).
- `test_philo14_a0b_codex_sprite_glass.py`: the Codex sprite lit by the Floor's GL engine hover.
- `test_philo8_01_list_rename_glass.py`: zone rename on the Floor list.
- `test_philo8_01_zone_name_glass.py`: zone names and New Zone on the Floor.
- `test_philo8_03_then_guard.py`: atlas case `case.p8.delete_then_leave.gone` (leaving the Floor commits a delete).
- `test_philo8_one_delete_glass.py`: delete on the Floor and its list. Its live parts (Undo, the receipt after the desk scrolls at 393, the Workbench refusal then Park and Restore) are re-homed on the Screen and Search in `tests/e2e/test_philo8_one_delete_glass.py`.
- `test_philo9_04_desk_debts_glass.py`: the desk-wide list canvas (selection token, 12 px text, columns, row menu). Its live parts (editor and thread-composer selection contrast) are re-homed in `tests/e2e/test_philo9_04_desk_debts_glass.py`.

# Parked by the test diet: MEET lane (2026-10-11)

These browser tests were moved to cheaper successors: a Python test against the hub
(`tests/unit/test_desk_*.py`, `tests/integration/test_desk_meetings.py`) or a vitest
per app (`web/src/**/__tests__/*.app.test.tsx`). Each successor names the test it
replaces in a `replaces:` line. Overflow, clip and overlap at 1440 and 393 are fenced
by the generic desk sweep (`tests/e2e/test_desk_sweep.py`).

- test_builtin_send_folder_glass.py, test_hs14104_refinement_glass.py, test_hs14105_context_glass.py,
  test_hs14105a_default_context_glass.py, test_hs151_thread_glass.py, test_hs152_hands_glass.py,
  test_hs152_renderers_glass.py, test_hs170_meetings_glass.py, test_hs172_meeting_glass.py,
  test_hs176_journal_glass.py, test_hs200_meeting_outcomes_glass.py, test_hs201_lane_a_glass.py,
  test_hs202_02_first_use_glass.py, test_hs526_desk_memory_glass.py,
  test_philo15_09_morning_truth_glass.py, test_philo17_transcribe_glass.py,
  test_philo8_04_empty_decision_heads_glass.py, test_route_in_footer_glass.py,
  test_spoken_meeting_e2e.py (its face selector is gone), test_times_local_zone_glass.py.

# The test diet: ROOM moves (PHILO-17, 2026-10-11)

These browser tests are kept, not run. Each fact they asserted now has a
cheaper successor: a vitest file that renders the real component over the
hub's recorded answers, or a Python test against the real routes. Each
successor names the test it replaces (`replaces: tests/e2e/<file>::<test>`).

- `test_hs158_room_glass.py`, `test_hs159_interview_glass.py`, `test_hs166_jira_glass.py`, `test_hs168_sources_glass.py`: every test was already skipped (the faces were retired by HS-169).
- `test_hs163_steward_glass.py`: `web/src/features/project-room/steward/__tests__/steward.app.test.tsx`.
- `test_hs169_door_legs_glass.py`: `web/src/features/project-room/door/__tests__/newProject.app.test.tsx`, `tests/integration/test_desk_new_project.py`.
- `test_hs172_room_glass.py`, `test_hs172_room_people_glass.py`, `test_hs173_health_glass.py`, `test_philo10_01_unknown_send_face.py`: `web/src/features/project-room/__tests__/room.app.test.tsx` (+ `tests/integration/test_desk_project_room.py` for the UNKNOWN send). The helpers `test_philo10_02_nudge_unknown_glass.py` used now live in `tests/e2e/room_glass_helpers.py`.
- `test_hs200_preparation_brief_glass.py`, `test_phase200_daily_loop.py`, `test_philo15_17_merge_receipt_glass.py`, `test_philo15_21_morning_truth_glass.py`: `tests/integration/test_desk_project_room.py` + `room.app.test.tsx` and the cited Room vitest files.
- `test_philo13_02_park_glass.py`: `tests/integration/test_desk_workbenches.py`, `workbenchPark.test.tsx`, `parkRestore.test.tsx`.
- `test_philo14_a2b_paths_glass.py`: `room.app.test.tsx`, `NeedsDrawer.test.tsx`, `drawer.test.tsx`.

# Parked by the test diet: AGENTS lane (PHILO-17, 2026-10-11)

Owner, 2026-10-11: the browser suite takes hours; move each check to the
cheapest tier that proves it. Each file below has successors in Python (a hub
route or service) or vitest (the real component with the hub's real answers).
Each successor names the test it replaces in a `replaces:` line; search for
the file name to find them. Seed helpers that live tests still import moved to
`tests/e2e/agents_lane_rig.py`, `conductor_rig.py`, `settings_rig.py`,
`open_rig.py` and `engine_stub_rig.py`.

- `test_agents_roster_glass.py`, `test_conductor_r1_gate_row_glass.py`,
  `test_philo14_c2_lane_glass.py`, `test_philo14_c4_conductor_glass.py`,
  `test_philo14_a0c_list_sprites_glass.py`, `test_philo15_20_raw_approve_glass.py`:
  `tests/integration/test_desk_agents_wire.py`, `web/src/desk/__tests__/agents.app.test.tsx`,
  `conductor.app.test.tsx`, `needs-you.app.test.tsx`.
- `test_hs170_settings_hub_glass.py`, `test_hs172_settings_meetings_glass.py`,
  `test_hs174_remote_settings_glass.py`, `test_hs200_runtime_identity_glass.py`,
  `test_philo9_b1_connections_glass.py`: `tests/integration/test_desk_settings.py`,
  `test_desk_connections.py`, `web/src/desk/__tests__/settings.app.test.tsx`,
  `connections.app.test.tsx`.
- `test_hs156_front_door_glass.py`, `test_hs201_09_connect_engine_glass.py`,
  `test_meaning_search_row_glass.py`, `test_phase200_readiness_glass.py`,
  `test_philo17_speech_glass.py`: `tests/unit/test_desk_runs_on.py`,
  `tests/integration/test_desk_runs_on_hub.py`, `test_desk_runs_on_meaning_search.py`,
  `web/src/desk/__tests__/runs-on.app.test.tsx`, `speech.app.test.tsx`.
- `test_hs172_people_glass.py`, `test_philo13_06_open_glass.py`,
  `test_philo13_09_prep_glass.py`: `tests/integration/test_desk_chair.py`,
  `web/src/desk/__tests__/people.app.test.tsx`, and the People vitest files they name.
- `test_hs141_models_setup_glass.py`, `test_hs142_model_acquisition_glass.py`,
  `test_hs143_assignments_glass.py`, `test_hs143_model_library_glass.py`: they
  skipped at import (their faces were parked in HS-170-03) and asserted nothing.
- `test_voice_typing_flow.py`: it tested a pipeline class defined inside the
  test file, not product code.

Relocated whole (they never opened a browser): `test_dogfood_plumbing_e2e.py`
is `tests/unit/test_dogfood_fixtures.py`; the five `test_hs201_*` backend files
are in `tests/integration/`.

# Parked by push 2 of the test diet: lane e2e-low-2 (2026-10-12)

Each file below is kept, not run. Its successor is named; a check with no
successor says why.

- `test_hs202_05_first_use_type_floor.py`: the 12 px floor and the faint and
  ember contrast on the first-use screens. Successor: the desk sweep's `floor`
  and `contrast` fences (`test_desk_sweep.py`), which read every window at 1440
  and 393 with the same reader, now in `tests/e2e/type_floor_rig.py`. Its 44 px
  hit contract on the live screens at 393 has no sweep fence; the kit's 44 px
  target is `tests/e2e/test_kit_glass.py`.
- `test_meeting_transcription.py`: a real-metal Whisper and LLM run on
  `tests/fixtures/mock_meeting.wav`, which is gitignored and on no machine, so
  every test skipped. Real Whisper is `tests/e2e/test_metal.py`.
- `test_memory_faces_glass.py`: every fact has a successor:
  `tests/unit/test_desk_memory.py`, `web/src/desk/__tests__/memory.app.test.tsx`
  and `web/src/desk/__tests__/memoryChanges.test.tsx` (the bus and the
  discarded refresh).
- `test_philo9_06_seen_collector.py`: it fenced the face collector of the
  Phase 9 closing-run script `scripts/philo9_room_job.py`, a history script
  whose own unit test is parked.
- `test_philo13_11_folded_word_reader.py`, `test_philo13_18_scroll_reach_reader.py`:
  moved whole to `tests/e2e/test_sweep_readers_glass.py`.
- `test_p16_kit_verb_glass.py`: moved whole to `tests/e2e/test_kit_glass.py`.
- `test_philo304_thought_foot_reflow.py`: moved to `tests/e2e/test_thought_glass.py`
  (the 600 px window and 393; 700 px and the default width only relax the 600 px bound).

# Parked by the test diet, push 2: lane e2e-low-1 (2026-10-12)

Each check has a successor, or the PR that parked it says why it has none.

- `test_hs154_call_glass.py`: `tests/unit/test_tts_route.py`, `tests/unit/test_desk_ask_ai.py`,
  `web/src/desk/__tests__/askai.app.test.tsx`, `settings.app.test.tsx` (each names it in `replaces:`).
- `test_hs174_rhythm_runs_on_glass.py`: `web/src/pages/cores/__tests__/rhythm.app.test.tsx`;
  the 393 leg (a shot and the clean check) is the sweep's Rhythm case at 393.
- `test_hs175_arrival_glass.py`: `web/src/desk/__tests__/chair.app.test.tsx`, `tests/unit/test_desk_chair.py`.
- `test_hs175_rhythm_brief_glass.py`: `web/src/pages/cores/__tests__/rhythm.app.test.tsx`.
- `test_hs175_settings_meetings_glass.py`: `web/src/desk/__tests__/settings.app.test.tsx`,
  `web/src/pages/cores/__tests__/SettingsCalendar.test.tsx`.
- `test_hs176_speak_glass.py`, `test_hs176_loop_glass.py`: `tests/unit/test_desk_speak.py`,
  `web/src/desk/__tests__/speak.app.test.tsx`; the Learned row's geometry at 393 is kept in
  `tests/e2e/test_speak_glass.py`.
- `test_dictation_enrichment_e2e.py`, `test_dictation_journal_e2e.py`: opt-in proofs against a live
  LLM that no suite ran. The same proof runs by hand: `scripts/dictation_enrichment_demo.py`,
  `scripts/journal_e2e_demo.py`. The journal row is `tests/unit/test_db_dictation_journal.py`.
- `test_dictation_learning_digest_spoken_e2e.py`: opt-in (macOS `say` and Whisper). The digest is
  `tests/unit/test_dictation_learning_digest.py` and
  `tests/integration/test_web_dictation_learning_digest.py`.
- `test_hs202_05_button_hit_ownership.py`, `test_hs202_05_disabled_stays_distinct.py`: moved whole
  (T4: `elementFromPoint` and a real pointer; the cascade's computed colours) into the library
  Button's file, `tests/e2e/test_kit_glass.py`. `OWNERSHIP_JS`, `PROBES` and `_overlap` are
  imported from there now.

# Parked by the diet, push 2: lane e2e-high-1 (2026-10-12)

Owner, 2026-10-12: "we've been trimming some fat on useless testing. I need
that to be pushed and pushed more." Each file below is parked because every
check in it has a successor (a hub test, a vitest file, or the desk sweep) or
proved nothing. The PR that parks a file has the table: check, verdict,
successor.

- `test_hs145_door_polish_glass.py`: the scroll hint always skipped (its board
  is parked, HS-170-04); the calendar offer is `tests/unit/test_desk_calendar.py`
  and `web/src/desk/__tests__/needsYou.app.test.tsx`.
- `test_hs200_continuity_glass.py`: `tests/unit/test_desk_memory.py` and
  `web/src/desk/__tests__/memory.app.test.tsx`; fit and the 393 filter strip
  are the sweep's.
- `test_palette_memory_glass.py`, `test_palette_two_line_glass.py`:
  `tests/unit/test_desk_palette.py`, `palette.app.test.tsx`,
  `paletteMemory.test.tsx`, `paletteTwoLine.test.tsx`; the in-shelf and 4.5:1
  plate facts are the sweep's `palette` fence.
- `test_philo13_04_faces_glass.py`: `philo13FacesDoNotLie.test.tsx`,
  `railSummaryStored.philo13.test.tsx`, `retryKeepsNewerWords.test.tsx`,
  `recordingSlice.test.ts`, `tests/integration/test_desk_capture.py`. Its
  `_outcome_meeting` seed now lives in `scripts/philo13_meetings_headline_fixture.py`.
- `test_philo13_08_decide_glass.py`: `tests/integration/test_desk_meetings.py`,
  `decision.app.test.tsx`, `philo1308Decide.test.tsx`.
- `test_hs162_update_glass.py`: `tests/integration/test_update_routes.py`,
  `UpdatePosture.test.tsx` (draft, edit, save, publish, copy Markdown, no engine).
- `test_hs169_room_glass.py`: `room169.test.tsx`; overlap, clip and fit are the
  sweep's; its pixel ratios pinned an old beauty round.
# Parked by push 2 of the test diet: lane e2e-low-2, part 2 (2026-10-12)

- `test_philo7_delete_receipt_glass.py`: moved to `tests/e2e/test_screen_glass.py`
  (the Delete key, the receipt's box and its 6 s linger).
- `test_philo8_one_delete_screen_glass.py` (was `tests/e2e/test_philo8_one_delete_glass.py`;
  renamed because the Floor version is already parked under that name): the
  long desk at 393 moved to `tests/e2e/test_screen_glass.py`; Undo keeps the
  object is `web/src/desk/__tests__/deleteReceipt.test.tsx` ("undo keeps the
  object"); the Workbench Park after a refusal is
  `web/src/desk/components/__tests__/workbenchPark.test.tsx` ("a refused Park
  frees the item ...").
- `test_philo7_02_grant_glass.py`: four checks were already
  `web/src/desk/__tests__/settings.app.test.tsx`; remote OFF with a LIVE grant
  is now there too, on a recorded answer (`grant-remote-off-live.json`,
  `tests/integration/test_desk_settings.py`); the minimally scrolled verb
  moved to `tests/e2e/test_settings_glass.py`. The expired grant on a row with
  no credential has no vitest of its own (the recorder holds no such state);
  its hub half is `tests/unit/test_desk_grant_lifecycle.py` (F5).
- `test_philo14_c2_lane_actions_glass.py` (8 tests, a real tmux):
  `web/src/desk/lane/__tests__/laneWindow.c2.test.tsx` holds every face fact
  (the lane's own session after Panes, the refused stale wait, ARM FIRST,
  Stop, the stopped receipt, unread collections, the Re-brief receipt,
  Approve); the hub halves are `tests/integration/test_desk_agents_wire.py`
  (a cleared or unnamed wait is refused; an owner stop ends the launch and its
  wait; the gate decides), `tests/unit/test_philo15_codex_launch_truth.py`,
  `tests/unit/test_philo14_c0_launch_lane.py` (not_read, no secret) and
  `tests/unit/test_web_routes_coders_steer.py` (unarmed 409, delivery). The
  12 px at 393 check is `tests/unit/test_philo13_18_type_floor_static.py`.
# Parked by the diet, push 2: lane e2e-high-1, app files (2026-10-12)

The checks that need a real browser moved into one file per app; the
originals are parked here, whole.

- `test_hs153_practice_glass.py` -> `tests/e2e/test_askai_glass.py` (slash
  keys, the focused Deny, the annotation selection). Mode tabs:
  `ModeTabs.test.tsx`, `tests/unit/test_thread_practice_route.py`; /compact:
  `threadCompaction.test.tsx`, `tests/unit/test_thread_compaction.py`; /todo:
  `tests/unit/test_thread_todo.py` (its Door card chip is parked).
- `test_hs170_concierge_glass.py` -> `tests/e2e/test_runs_on_glass.py` (the
  drag cases). The non-drag cases: `web/src/features/runson/__tests__/runsOn.test.tsx`.
- `test_new_verbs_open_glass.py` -> `tests/e2e/test_creation_glass.py` (whole).
- `test_hs201_12_thought_note_glass.py`, `test_hs141_thought_workbench_glass.py`
  -> `tests/e2e/test_thought_glass.py`. The draft-append leg:
  `ThoughtWorkspaceWindow.test.tsx`.

# Push 2, lane e2e-low-1 A: the shade, the deck, receipts, coverage (2026-10-12)

- `test_hs171_command_deck_glass.py`: `web/src/desk/__tests__/palette.app.test.tsx`
  (the PROJECTS limit, filter and press), `oneNumberFaces.test.tsx` (badge and
  order on the real producers' desk), `tests/integration/test_project_routes_characterization.py`
  (archived Rooms); fit, 393 and egress are the desk sweep's palette case.
- `test_hs171_shade_glass.py`: `oneNumberFaces.test.tsx` (Projects rows, MUTED,
  Open opens the Room), `web/src/desk/__tests__/bell.app.test.tsx` (quiet desk,
  the Brief row, the 5 s poll that stops on close), `tests/unit/test_needs_you.py`
  (the cache). The Dock badge legs were stale (the Dock draws no needs-you badge).
- `test_hs174_receipts_glass.py`: `bell.app.test.tsx` (the shade's REMOTE chip,
  over `web/src/test/wire/desk-projections.remote-receipt.wire.json`),
  `web/src/features/project-room/__tests__/room.app.test.tsx` (History ▸ Writes,
  over `room-wires/receipts174.json`), `tests/unit/test_reach_wire.py`.
- `test_hs200_coverage_glass.py`: the arrival legs were already in
  `tests/unit/test_desk_needs_you.py`, `tests/integration/test_attention_coverage.py`,
  `needsYou.app.test.tsx`, `NeedsDrawer.test.tsx` and `arrivalCoverage.test.tsx`;
  the shade leg is `web/src/desk/components/__tests__/shadeCoverage.test.tsx` and
  `web/src/desk/components/window/Dock.test.tsx` (the Missed launcher).
# Parked by push 2 of the test diet: lane e2e-high-2 (PHILO-17, 2026-10-12)

Owner, 2026-10-12: "we've been trimming some fat on useless testing. I need that
to be pushed and pushed more." A browser test stays only for drag, focus, keys,
touch, hover or an exact geometry relation, in ONE file per app. Each kept test
names the test it replaces in a `replaces:` line; the PR that parked a file has
one row per retired check.

- `test_philo13_13_dock_glass.py`: kept legs in `tests/e2e/test_dock_glass.py`.
- `test_philo13_14_palette_glass.py`: every leg has a vitest or hub successor
  (`palette.philo1314.test.tsx`, `palette.app.test.tsx`, `tests/unit/test_desk_palette_send.py`).
- `test_philo13_15_send_to_glass.py`: kept legs in `tests/e2e/test_send_glass.py`.
- `test_philo13_16_capture_glass.py`: kept legs in `tests/e2e/test_thought_glass.py`.
- `test_philo13_17_phone_desk_glass.py`, `test_philo13_18_strip_escape_glass.py`:
  kept legs in `tests/e2e/test_windows_glass.py`.
- `test_philo13_18_editor_wrap_glass.py`: moved whole to `tests/e2e/test_room_glass.py`.
- `test_philo13_18_type_floor_glass.py`: the desk sweep (`floor`, `clipped`,
  `overlap`), which now also opens the Chair's Brief, The week and Capture.
- `test_philo14_a1_fresh_arrival_glass.py`: `needsChair.app.test.tsx`, `tests/unit/test_desk_windows.py`.
- `test_philo14_a1c_aftercare_capture_glass.py`: moved whole to `tests/e2e/test_chair_glass.py`.
- `test_philo14_b2_material_glass.py`: the material at rest is the desk sweep's
  `material` fence (its reader is `tests/e2e/material_rig.py` now); the pressed
  Button and the held filter strip are in `tests/e2e/test_settings_glass.py`.
- `test_philo14_a2_drawer_glass.py`: the Project drawer is parked (PHILO-17 U30,
  `web/src/lib/primitives.ts`: "no product opener names it"); its face is fenced
  in `web/src/desk/drawer/__tests__/drawer.test.tsx`, and the Needs-you Project
  button opening the Room in `web/src/desk/__tests__/openGrammar.philo1306.test.tsx`.
- `test_philo14_b1_object_species_glass.py`: moved whole to `tests/e2e/test_components_glass.py`.
- `test_philo14_c3_drop_to_hand_glass.py`: the real drag is in `tests/e2e/test_conductor_glass.py`;
  every other leg is in `web/src/desk/hand/__tests__/hand.test.tsx`.
- `test_philo15_04_small_gaps_glass.py`: `parked.app.test.tsx`, `firstrun.app.test.tsx`,
  `tests/integration/test_desk_firstrun.py`.
- `test_philo15_11_phone_menus_glass.py`: the fit is in `tests/e2e/test_menus_glass.py`; the rows in
  `phoneRing.test.tsx` and `phoneKeycaps.philo1511.test.tsx`.
- `test_philo15_12_ugly_glass.py`: its rig is `tests/e2e/fit_rig.py`; B22 in `test_meetings_glass.py`,
  B27 in `test_runs_on_glass.py`, B24 in `test_today_glass.py`; the rest in `philo15Ugly.test.tsx`,
  `systemSprites.test.ts` and the desk sweep.
- `test_philo15_16_project_repo_glass.py`: the Project drawer is parked (U30); the hand's clone and
  flip in `hand.test.tsx`, Add to Project in `addToProject.test.tsx`, the repository in
  `tests/unit/test_project_repository.py` and `room.app.test.tsx`.
- `test_philo15_19_brief_day_glass.py`: the 1440 walk is in `tests/e2e/test_chair_glass.py`; the
  rows' words in `tests/unit/test_monday_brief_service.py` (B58, B59, B73).
- `test_philo17_doors_glass.py`: D6 and D7 in `tests/e2e/test_menus_glass.py`; the menus in
  `DeskMenuBar.test.tsx` and `menus.app.test.tsx`; the doors' windows in the desk sweep.
# Parked by push 2 of the test diet: lane e2e-low-2, part 3 (2026-10-12)

Every check below already had a cheaper successor; the browser file still ran
beside it.

- `test_philo10_04_send_face_glass.py` (12 tests): the Send face is
  `web/src/desk/surface/send/__tests__/SendWell.test.tsx` and
  `web/src/features/channels/__tests__/SendWell.test.tsx` (no destination, the
  pick and preview, SAVED with the path, one send for a double click, FAILED,
  UNKNOWN, PREPARED first, a lost answer keeps the key, unread reads named,
  history and list chips, SENDING); the destinations group, the remote forms
  and email setup are `web/src/desk/__tests__/destinations.app.test.tsx`; the
  Add destination door is `windowSend.philo1315.test.tsx`. The hub side is
  `tests/unit/test_channel_send_contract.py` (file states, destination changed
  and parked, prepare), `test_philo10_send_restart.py` (board 25, unknown after
  a restart), `test_philo10_cli_channels.py` (GitHub, Jira, Confluence),
  `test_philo10_email_channel.py`, `tests/integration/test_desk_send.py` (the
  held acli lock) and `test_desk_destinations.py`.
- `test_philo11_05b_meeting_faces_glass.py`: `web/src/features/channels/__tests__/slackDestination.test.tsx`,
  `tests/integration/test_slack_channel.py`, `tests/integration/test_desk_settings.py`
  (no legacy Slack row) and the SendWell vitest files above (the wells, G2 over the limit).
- `test_philo15_18_rest_of_day_glass.py` (6 tests): `web/src/desk/__tests__/restOfDay.philo1518.test.tsx`
  (B31, B33, B36, B40, B56), `connections.app.test.tsx`, `settings.app.test.tsx`,
  `firstrun/__tests__/OneScreen.test.tsx` and `conductor/__tests__/conductor.test.tsx`
  (B34/B35 Install hooks with its receipt). The Conductor row title's ellipsis
  is the sweep's `clipped` fence; the Project drawer it also read is parked (PHILO-17 U30).
- `test_philo17_autoflow_glass.py`: `tests/unit/test_finish_defaults.py::test_an_import_with_an_engine_queues_its_summary`,
  `tests/integration/test_desk_meetings.py` (the run reaches the summary and its
  receipt) and `meetings.app.test.tsx` ("an open record ... catches up ... on the
  hub's frame").
- `test_philo17_conductor_plates_glass.py`: `web/src/desk/conductor/__tests__/conductor.test.tsx`
  (the ask plate, Answer opens the lane, Approve on the plate, a cut call opens
  the lane) and `tests/integration/test_desk_agents_wire.py` (the gate decides).
- `test_philo4_02_generated_clearance.py`: no successor, because the sticky
  capture bar it fenced left the Brief in PHILO-13-11 (the capture bar is its
  own window); the Brief row now sits in an ordinary scroller.
# Parked by the diet, push 2: lane e2e-high-1, app files 2 (2026-10-12)

- `test_finish_face_polish_glass.py` (and its `finish_polish_1px.png`): its
  rig is `tests/e2e/finish_rig.py`; the Dock pages leg is
  `tests/e2e/test_dock_glass.py`, the Chair zoom leg `test_chair_glass.py`,
  the Processes leg `test_processes_glass.py`, the Roadmap rows leg
  `test_roadmap_glass.py`. The palette legs are `paletteSendNoise.test.ts`
  and `builtinFolder.test.tsx`; the roadmap ref `roadmapRef.test.ts`; the
  SEND well, calendar and paths legs were already `SendWell.test.tsx`,
  `CalendarSnapshotReviewCore.test.tsx` and `tests/unit/test_face_paths_short.py`.
- `test_philo13_01_dock_tap_glass.py` -> `tests/e2e/test_dock_glass.py` (whole).
- `test_hs200_voice_custody_glass.py` -> `tests/e2e/test_speak_glass.py` (the
  geometry walk); the wire test is `tests/unit/test_desk_speak.py`.
- `test_phase16_agent_words_glass.py` -> `tests/e2e/test_agents_glass.py` (the
  393 ellipsis); the render leg is `AgentWords.test.tsx`.
- `test_hs200_attention_glass.py`, `test_philo13_03_needs_you_glass.py` ->
  `tests/e2e/test_needs_you_glass.py` (the 393 long row; one number). The
  rest: `tests/unit/test_attention.py`, `NeedsDrawer.test.tsx`,
  `arrivalAttention.test.tsx`, `meetingsHeadline.philo1303.test.ts`.
# Parked by the diet, push 2: lane e2e-high-1, the Room (2026-10-12)

- `test_hs160_delta_glass.py`, `test_hs168_window_wings_glass.py`,
  `test_hs200_people_preparation_glass.py`, `test_hs200_task_resume_glass.py`
  -> `tests/e2e/test_room_glass.py` (the keyboard review loop, the wings
  geometry, People's return focus, the unfinished-asks container rule, roving
  keys and full-list geometry); the Thread composer legs of the task-resume
  file -> `tests/e2e/test_askai_glass.py`. The rest: `tests/unit/test_frozen_review.py`,
  `roomPeople200.test.tsx`, `taskResume.test.tsx`, `room200TaskResume.test.tsx`,
  `tests/unit/test_phase200_task_resume.py`.
