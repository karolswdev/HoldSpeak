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
