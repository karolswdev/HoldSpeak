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
