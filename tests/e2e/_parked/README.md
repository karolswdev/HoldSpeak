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
