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
