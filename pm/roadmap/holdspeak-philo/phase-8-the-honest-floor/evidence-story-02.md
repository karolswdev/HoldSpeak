# Evidence - PHILO-8-02

- **Story:** PHILO-8-02 - One delete everywhere
- **Status:** done
- **Date:** 2026-09-26

## Proof

### Captured run — 2026-09-26T17:23:30Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.lGB38oExlm PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HOLDSPEAK_EVIDENCE_WRITE=1 uv run pytest -q tests/e2e/test_philo8_one_delete_glass.py tests/e2e/test_philo7_delete_receipt_glass.py -p no:cacheprovider -n 2 -rA`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 455d78e92aea5f2d7bba90f3a44a4e47d7efe77e

```text
bringing up nodes...
bringing up nodes...

...........................                                              [100%]
==================================== PASSES ====================================
___ TestOneDelete.test_the_list_delete_key_removes_the_selected_object[393] ____
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_____ TestOneDelete.test_the_list_row_menu_delete_removes_the_object[1440] _____
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
1440: the row menu's Delete row {'top': 847, 'bottom': 875, 'vh': 900}
_ TestOneDelete.test_the_list_palette_delete_removes_the_selected_object[1440] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_____ TestOneDelete.test_the_list_row_menu_delete_removes_the_object[393] ______
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
393: the row menu's Delete row {'top': 839, 'bottom': 867, 'vh': 852}
_ TestOneDelete.test_the_list_palette_delete_removes_the_selected_object[393] __
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
___ TestOneDelete.test_the_list_delete_key_removes_the_selected_object[1440] ___
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[floor-a_left_selected-393] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor a_left_selected 393: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
__________ TestOneDelete.test_undo_on_the_list_keeps_the_object[1440] __________
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
__________ TestOneDelete.test_undo_on_the_list_keeps_the_object[393] ___________
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[floor-a_taken_out-1440] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor a_taken_out 1440: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_______ TestOneDelete.test_the_receipt_is_readable_on_a_long_list_at_393 _______
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[floor-a_taken_out-393] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor a_taken_out 393: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[floor-a_left_selected-1440] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor a_left_selected 1440: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[list-a_left_selected-1440] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list a_left_selected 1440: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[list-a_taken_out-1440] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list a_taken_out 1440: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[list-a_left_selected-393] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list a_left_selected 393: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[list-a_taken_out-393] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list a_taken_out 393: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_________ TestOneDelete.test_undo_keeps_only_the_pending_object[1440] __________
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
__________ TestOneDelete.test_undo_keeps_only_the_pending_object[393] __________
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_leaving_the_face_inside_the_window_commits_the_delete[floor-1440] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor 1440: 404; DELETE 1
_ TestOneDelete.test_leaving_the_face_inside_the_window_commits_the_delete[floor-393] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor 393: 404; DELETE 1
_ TestOneDelete.test_leaving_the_face_inside_the_window_commits_the_delete[list-393] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list 393: 404; DELETE 1
_ TestOneDelete.test_leaving_the_face_inside_the_window_commits_the_delete[list-1440] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list 1440: 404; DELETE 1
__ TestOneDelete.test_the_delete_key_on_the_chair_with_a_floor_selection[393] __
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
chair 393: 404; DELETE 1
_ TestOneDelete.test_the_delete_key_on_the_chair_with_a_floor_selection[1440] __
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
chair 1440: 404; DELETE 1
_ TestDeleteReceiptGlass.test_the_delete_receipt_is_readable_in_the_viewport[1440] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
1440: pending {'x': 533.859375, 'y': 748, 'w': 372.28125, 'h': 27} committed {'x': 650.8984375, 'y': 748, 'w': 138.203125, 'h': 27} shown 6601 ms
_ TestDeleteReceiptGlass.test_the_delete_receipt_is_readable_in_the_viewport[393] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
393: pending {'x': 12, 'y': 676, 'w': 369, 'h': 27} committed {'x': 127.3984375, 'y': 676, 'w': 138.203125, 'h': 27} shown 6280 ms
=========================== short test summary info ============================
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_delete_key_removes_the_selected_object[393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_row_menu_delete_removes_the_object[1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_palette_delete_removes_the_selected_object[1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_row_menu_delete_removes_the_object[393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_palette_delete_removes_the_selected_object[393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_delete_key_removes_the_selected_object[1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[floor-a_left_selected-393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_on_the_list_keeps_the_object[1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_on_the_list_keeps_the_object[393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[floor-a_taken_out-1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_receipt_is_readable_on_a_long_list_at_393
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[floor-a_taken_out-393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[floor-a_left_selected-1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[list-a_left_selected-1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[list-a_taken_out-1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[list-a_left_selected-393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[list-a_taken_out-393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_keeps_only_the_pending_object[1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_keeps_only_the_pending_object[393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[floor-1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[floor-393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[list-393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[list-1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_delete_key_on_the_chair_with_a_floor_selection[393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_delete_key_on_the_chair_with_a_floor_selection[1440]
PASSED tests/e2e/test_philo7_delete_receipt_glass.py::TestDeleteReceiptGlass::test_the_delete_receipt_is_readable_in_the_viewport[1440]
PASSED tests/e2e/test_philo7_delete_receipt_glass.py::TestDeleteReceiptGlass::test_the_delete_receipt_is_readable_in_the_viewport[393]
27 passed in 360.78s (0:06:00)
```

### Captured run — 2026-09-26T17:29:53Z

- **Command:** `uv run python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 05986a69fe560beab58feaad993a5f81f8ffcba3

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

BRANCH-NEW (1):
  BRANCH-NEW: src/desk/components/FirstWords.test.tsx > FirstWords > retries typed Keep with one client note id without forging an onboarding exit

Suite totals: 2887 passed, 1 failed, 0 skipped

VERDICT: BRANCH-NEW FAILURES: 1
```

### Captured run — 2026-09-26T17:30:46Z

- **Command:** `uv run python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5838ed9d39339ad1ba5ef4ba2c6129020f052b00

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2888 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-26T17:31:28Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.XnRjsQbQTv PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright bash -c for vp in 1440 393; do uv run python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase7.json --case case.p7.decision_delete.gone --brain muaddib --viewport $vp --no-build --out .tmp/graph-walk/philo8-02 | grep -E "VERDICT|NOTE" || exit 1; done`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** dd3810d5a9289693e33e604d8fc14ae1fcdbb6bb

```text
VERDICT: pass terminal=settled
NOTE: predicate: 'Removal committed' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 651, 'y': 748, 'w': 138, 'h': 27}
VERDICT: pass terminal=settled
NOTE: predicate: 'Removal committed' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 127, 'y': 628, 'w': 138, 'h': 27}
```

### Captured run — 2026-09-26T17:32:23Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.XnRjsQbQTv uv run pytest -q tests/unit/test_design_system_guard.py tests/unit/test_desk_no_exit_guard.py tests/unit/test_doc_drift_guard.py tests/unit/test_frontend_density_guard.py tests/unit/test_interior_canon_guard.py tests/unit/test_native_surfaces_guard.py tests/unit/test_page_cores_guard.py tests/unit/test_phase200_canon_guard.py tests/unit/test_web_null_read_guard.py tests/unit/test_web_vocabulary_guard.py tests/unit/test_philo_graph_reference.py tests/unit/test_philo7_atlas.py tests/unit/test_philo_graph_atlas.py -p no:cacheprovider`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c9d19ca218860910332004df87055c8d623a3dac

```text
........................................................................ [ 36%]
........................................................................ [ 72%]
......................................................                   [100%]
198 passed in 9.58s
```

### Captured run — 2026-09-26T17:35:00Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.0kOYpxLg9G PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_philo8_one_delete_glass.py tests/e2e/test_philo7_delete_receipt_glass.py -p no:cacheprovider -n 2 -rA`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3f79bd67852da210694c290ac59b084d7d381537

```text
bringing up nodes...
bringing up nodes...

...........................                                              [100%]
==================================== PASSES ====================================
___ TestOneDelete.test_the_list_delete_key_removes_the_selected_object[393] ____
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_____ TestOneDelete.test_the_list_row_menu_delete_removes_the_object[1440] _____
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
1440: the row menu's Delete row {'top': 847, 'bottom': 875, 'vh': 900}
_ TestOneDelete.test_the_list_palette_delete_removes_the_selected_object[1440] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_____ TestOneDelete.test_the_list_row_menu_delete_removes_the_object[393] ______
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
393: the row menu's Delete row {'top': 839, 'bottom': 867, 'vh': 852}
_ TestOneDelete.test_the_list_palette_delete_removes_the_selected_object[393] __
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
___ TestOneDelete.test_the_list_delete_key_removes_the_selected_object[1440] ___
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[floor-a_left_selected-393] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor a_left_selected 393: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
__________ TestOneDelete.test_undo_on_the_list_keeps_the_object[1440] __________
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
__________ TestOneDelete.test_undo_on_the_list_keeps_the_object[393] ___________
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[floor-a_taken_out-1440] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor a_taken_out 1440: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_______ TestOneDelete.test_the_receipt_is_readable_on_a_long_list_at_393 _______
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[floor-a_taken_out-393] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor a_taken_out 393: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[list-a_left_selected-1440] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list a_left_selected 1440: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[floor-a_left_selected-1440] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor a_left_selected 1440: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[list-a_left_selected-393] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list a_left_selected 393: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[list-a_taken_out-1440] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list a_taken_out 1440: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[list-a_taken_out-393] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list a_taken_out 393: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_________ TestOneDelete.test_undo_keeps_only_the_pending_object[1440] __________
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_leaving_the_face_inside_the_window_commits_the_delete[floor-1440] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor 1440: 404; DELETE 1
__________ TestOneDelete.test_undo_keeps_only_the_pending_object[393] __________
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_leaving_the_face_inside_the_window_commits_the_delete[floor-393] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor 393: 404; DELETE 1
_ TestOneDelete.test_leaving_the_face_inside_the_window_commits_the_delete[list-1440] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list 1440: 404; DELETE 1
_ TestOneDelete.test_leaving_the_face_inside_the_window_commits_the_delete[list-393] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list 393: 404; DELETE 1
_ TestOneDelete.test_the_delete_key_on_the_chair_with_a_floor_selection[1440] __
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
chair 1440: 404; DELETE 1
__ TestOneDelete.test_the_delete_key_on_the_chair_with_a_floor_selection[393] __
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
chair 393: 404; DELETE 1
_ TestDeleteReceiptGlass.test_the_delete_receipt_is_readable_in_the_viewport[1440] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
1440: pending {'x': 533.859375, 'y': 748, 'w': 372.28125, 'h': 27} committed {'x': 650.8984375, 'y': 748, 'w': 138.203125, 'h': 27} shown 6605 ms
_ TestDeleteReceiptGlass.test_the_delete_receipt_is_readable_in_the_viewport[393] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
393: pending {'x': 12, 'y': 676, 'w': 369, 'h': 27} committed {'x': 127.3984375, 'y': 676, 'w': 138.203125, 'h': 27} shown 6131 ms
=========================== short test summary info ============================
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_delete_key_removes_the_selected_object[393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_row_menu_delete_removes_the_object[1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_palette_delete_removes_the_selected_object[1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_row_menu_delete_removes_the_object[393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_palette_delete_removes_the_selected_object[393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_delete_key_removes_the_selected_object[1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[floor-a_left_selected-393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_on_the_list_keeps_the_object[1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_on_the_list_keeps_the_object[393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[floor-a_taken_out-1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_receipt_is_readable_on_a_long_list_at_393
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[floor-a_taken_out-393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[list-a_left_selected-1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[floor-a_left_selected-1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[list-a_left_selected-393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[list-a_taken_out-1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[list-a_taken_out-393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_keeps_only_the_pending_object[1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[floor-1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_keeps_only_the_pending_object[393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[floor-393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[list-1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[list-393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_delete_key_on_the_chair_with_a_floor_selection[1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_delete_key_on_the_chair_with_a_floor_selection[393]
PASSED tests/e2e/test_philo7_delete_receipt_glass.py::TestDeleteReceiptGlass::test_the_delete_receipt_is_readable_in_the_viewport[1440]
PASSED tests/e2e/test_philo7_delete_receipt_glass.py::TestDeleteReceiptGlass::test_the_delete_receipt_is_readable_in_the_viewport[393]
27 passed in 363.82s (0:06:03)
```

### Captured run — 2026-09-26T17:41:20Z

- **Command:** `uv run python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0f0af5fff4d2409fe06dc04b9e916819c7a348d8

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2906 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-26T19:45:55Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.AhLBiTNQut PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HOLDSPEAK_EVIDENCE_WRITE=1 uv run pytest -q tests/e2e/test_philo8_one_delete_glass.py tests/e2e/test_philo7_delete_receipt_glass.py -p no:cacheprovider -rA`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** e8688c95ceb2059985afcedd8be1b40431909fc2

```text
F................F.........                                              [100%]
=================================== FAILURES ===================================
_____ TestOneDelete.test_the_list_row_menu_delete_removes_the_object[1440] _____

self = <tests.e2e.test_philo8_one_delete_glass.TestOneDelete object at 0x108907b10>
width = 1440

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_list_row_menu_delete_removes_the_object(self, width: int) -> None:
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["List delete decision"])
            try:
                _to_face(page, "list", width)
>               box = _row_menu_delete(page, "List delete decision")
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/e2e/test_philo8_one_delete_glass.py:172: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_philo8_one_delete_glass.py:117: in _row_menu_delete
    item.wait_for(timeout=5_000)
.venv/lib/python3.14/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.14/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.14/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x10feeeba0>
cb = <function Channel.send.<locals>.<lambda> at 0x1110f9380>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 5000ms exceeded.
E           Call log:
E             - waiting for locator(".desk-world-menu [role=menuitem]").filter(has_text="Delete").last to be visible

.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_________ TestOneDelete.test_undo_keeps_only_the_pending_object[1440] __________

self = <tests.e2e.test_philo8_one_delete_glass.TestOneDelete object at 0x108a80e10>
width = 1440

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_undo_keeps_only_the_pending_object(self, width: int) -> None:
        """A second delete commits the first at once; Undo restores the second only."""
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
            browser, page, (a_id, b_id), errors = self._open(pw, width, ["Probe A", "Probe B"])
            try:
                _to_face(page, "floor", width)
                _select(page, "floor", a_id, "Probe A")
                page.keyboard.press("Delete")
                page.wait_for_timeout(1_000)
                _select(page, "floor", b_id, "Probe B")
                page.keyboard.press("Delete")
                _readable_receipt(page, "Removed Probe B", 5_000)
>               page.locator(".undo-receipt-btn").click()

tests/e2e/test_philo8_one_delete_glass.py:327: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.14/site-packages/playwright/sync_api/_generated.py:15637: in click
    self._sync(
.venv/lib/python3.14/site-packages/playwright/_impl/_locator.py:162: in click
    return await self._frame._click(self._selector, strict=True, **params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.14/site-packages/playwright/_impl/_frame.py:566: in _click
    await self._channel.send("click", self._timeout, locals_to_params(locals()))
.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x11ea36c50>
cb = <function Channel.send.<locals>.<lambda> at 0x127b081a0>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Locator.click: Timeout 30000ms exceeded.
E           Call log:
E             - waiting for locator(".undo-receipt-btn")

.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
==================================== PASSES ====================================
_____ TestOneDelete.test_the_list_row_menu_delete_removes_the_object[393] ______
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
393: the row menu's Delete row {'top': 839, 'bottom': 867, 'vh': 852}
___ TestOneDelete.test_the_list_delete_key_removes_the_selected_object[1440] ___
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
___ TestOneDelete.test_the_list_delete_key_removes_the_selected_object[393] ____
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_the_list_palette_delete_removes_the_selected_object[1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_the_list_palette_delete_removes_the_selected_object[393] __
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
__________ TestOneDelete.test_undo_on_the_list_keeps_the_object[1440] __________
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
__________ TestOneDelete.test_undo_on_the_list_keeps_the_object[393] ___________
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_______ TestOneDelete.test_the_receipt_is_readable_on_a_long_list_at_393 _______
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[floor-a_left_selected-1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor a_left_selected 1440: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[floor-a_left_selected-393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor a_left_selected 393: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[floor-a_taken_out-1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor a_taken_out 1440: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[floor-a_taken_out-393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor a_taken_out 393: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[list-a_left_selected-1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list a_left_selected 1440: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[list-a_left_selected-393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list a_left_selected 393: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[list-a_taken_out-1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list a_taken_out 1440: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[list-a_taken_out-393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list a_taken_out 393: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
__________ TestOneDelete.test_undo_keeps_only_the_pending_object[393] __________
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_leaving_the_face_inside_the_window_commits_the_delete[floor-1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor 1440: 404; DELETE 1
_ TestOneDelete.test_leaving_the_face_inside_the_window_commits_the_delete[floor-393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor 393: 404; DELETE 1
_ TestOneDelete.test_leaving_the_face_inside_the_window_commits_the_delete[list-1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list 1440: 404; DELETE 1
_ TestOneDelete.test_leaving_the_face_inside_the_window_commits_the_delete[list-393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list 393: 404; DELETE 1
_____ TestOneDelete.test_the_chair_withholds_delete_with_its_reason[1440] ______
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
chair 1440: 200; DELETE 0; receipt ''
______ TestOneDelete.test_the_chair_withholds_delete_with_its_reason[393] ______
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
chair 393: 200; DELETE 0; receipt ''
_ TestDeleteReceiptGlass.test_the_delete_receipt_is_readable_in_the_viewport[1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
1440: pending {'x': 533.859375, 'y': 748, 'w': 372.28125, 'h': 27} committed {'x': 650.8984375, 'y': 748, 'w': 138.203125, 'h': 27} shown 6720 ms
_ TestDeleteReceiptGlass.test_the_delete_receipt_is_readable_in_the_viewport[393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
393: pending {'x': 12, 'y': 676, 'w': 369, 'h': 27} committed {'x': 127.3984375, 'y': 676, 'w': 138.203125, 'h': 27} shown 6198 ms
=========================== short test summary info ============================
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_row_menu_delete_removes_the_object[393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_delete_key_removes_the_selected_object[1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_delete_key_removes_the_selected_object[393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_palette_delete_removes_the_selected_object[1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_palette_delete_removes_the_selected_object[393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_on_the_list_keeps_the_object[1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_on_the_list_keeps_the_object[393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_receipt_is_readable_on_a_long_list_at_393
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[floor-a_left_selected-1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[floor-a_left_selected-393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[floor-a_taken_out-1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[floor-a_taken_out-393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[list-a_left_selected-1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[list-a_left_selected-393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[list-a_taken_out-1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[list-a_taken_out-393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_keeps_only_the_pending_object[393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[floor-1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[floor-393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[list-1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[list-393]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_chair_withholds_delete_with_its_reason[1440]
PASSED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_chair_withholds_delete_with_its_reason[393]
PASSED tests/e2e/test_philo7_delete_receipt_glass.py::TestDeleteReceiptGlass::test_the_delete_receipt_
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-09-26T20:07:17Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.uZrNDtcyux PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HOLDSPEAK_EVIDENCE_WRITE=1 uv run pytest -q tests/e2e/test_philo8_one_delete_glass.py tests/e2e/test_philo7_delete_receipt_glass.py -p no:cacheprovider -n 2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f4afb88aec61e647e552d1feed8ca04893ff312f

```text
bringing up nodes...
bringing up nodes...

...........................                                              [100%]
27 passed in 364.72s (0:06:04)
```

### Captured run — 2026-09-26T20:13:45Z

- **Command:** `uv run python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 37f63d14340071d8a332c71a6f54b6c6a76804f5

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2908 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-26T20:16:44Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.ZhLIhhkA5V PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_philo8_one_delete_glass.py tests/e2e/test_philo7_delete_receipt_glass.py tests/e2e/test_philo8_01_zone_name_glass.py tests/e2e/test_philo8_01_list_rename_glass.py -p no:cacheprovider -n 2 -rA`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 68182943d78b5427a4667535e03163a8c895f6dd

```text
bringing up nodes...
bringing up nodes...

F........................................................                [100%]
=================================== FAILURES ===================================
__________ TestOneDelete.test_undo_on_the_list_keeps_the_object[393] ___________
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python

self = <tests.e2e.test_philo8_one_delete_glass.TestOneDelete object at 0x10c792150>
width = 393

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_undo_on_the_list_keeps_the_object(self, width: int) -> None:
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["Undo list decision"])
            try:
                _to_face(page, "list", width)
                _row_menu_delete(page, "Undo list decision")
>               _readable_receipt(page, "Removed", 5_000)

tests/e2e/test_philo8_one_delete_glass.py:229: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_philo8_one_delete_glass.py:51: in _readable_receipt
    return _readable_now(page, want, timeout_ms)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/e2e/test_philo7_delete_receipt_glass.py:70: in _readable_receipt
    page.wait_for_function(
.venv/lib/python3.14/site-packages/playwright/sync_api/_generated.py:11595: in wait_for_function
    self._sync(
.venv/lib/python3.14/site-packages/playwright/_impl/_page.py:1110: in wait_for_function
    return await self._main_frame.wait_for_function(**locals_to_params(locals()))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.14/site-packages/playwright/_impl/_frame.py:878: in wait_for_function
    await self._channel.send("waitForFunction", self._timeout, params)
.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x113d2c440>
cb = <function Channel.send.<locals>.<lambda> at 0x114e699b0>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 5000ms exceeded.

.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
==================================== PASSES ====================================
_______ TestOneDelete.test_the_receipt_is_readable_on_a_long_list_at_393 _______
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_____ TestOneDelete.test_the_list_row_menu_delete_removes_the_object[1440] _____
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
1440: the row menu's Delete row {'top': 847, 'bottom': 875, 'vh': 900}
_____ TestOneDelete.test_the_list_row_menu_delete_removes_the_object[393] ______
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
393: the row menu's Delete row {'top': 839, 'bottom': 867, 'vh': 852}
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[floor-a_left_selected-1440] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor a_left_selected 1440: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
___ TestOneDelete.test_the_list_delete_key_removes_the_selected_object[1440] ___
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
___ TestOneDelete.test_the_list_delete_key_removes_the_selected_object[393] ____
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[floor-a_left_selected-393] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor a_left_selected 393: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestOneDelete.test_the_list_palette_delete_removes_the_selected_object[1440] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[floor-a_taken_out-1440] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor a_taken_out 1440: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestOneDelete.test_the_list_palette_delete_removes_the_selected_object[393] __
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[floor-a_taken_out-393] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor a_taken_out 393: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
__________ TestOneDelete.test_undo_on_the_list_keeps_the_object[1440] __________
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[list-a_left_selected-1440] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list a_left_selected 1440: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[list-a_left_selected-393] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list a_left_selected 393: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_____ TestOneDelete.test_the_chair_withholds_delete_with_its_reason[1440] ______
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
chair 1440: 200; DELETE 0; receipt ''
______ TestOneDelete.test_the_chair_withholds_delete_with_its_reason[393] ______
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
chair 393: 200; DELETE 0; receipt ''
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[list-a_taken_out-1440] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list a_taken_out 1440: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestDeleteReceiptGlass.test_the_delete_receipt_is_readable_in_the_viewport[1440] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
1440: pending {'x': 533.859375, 'y': 748, 'w': 372.28125, 'h': 27} committed {'x': 650.8984375, 'y': 748, 'w': 138.203125, 'h': 27} shown 6715 ms
_ TestOneDelete.test_two_deletes_in_one_window_both_reach_the_hub[list-a_taken_out-393] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list a_taken_out 393: selected before B ''; receipt after B 'Removed Probe B\nUndo\n08s'; {'A': 404, 'B': 404}; DELETE 2
_ TestDeleteReceiptGlass.test_the_delete_receipt_is_readable_in_the_viewport[393] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
393: pending {'x': 12, 'y': 676, 'w': 369, 'h': 27} committed {'x': 127.3984375, 'y': 676, 'w': 138.203125, 'h': 27} shown 6364 ms
___ TestZoneNameGlass.test_two_new_zone_presses_make_two_zones[1440-spatial] ___
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_________ TestOneDelete.test_undo_keeps_only_the_pending_object[1440] __________
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
____ TestZoneNameGlass.test_two_new_zone_presses_make_two_zones[1440-list] _____
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
__________ TestOneDelete.test_undo_keeps_only_the_pending_object[393] __________
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
___ TestZoneNameGlass.test_two_new_zone_presses_make_two_zones[393-spatial] ____
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_____ TestZoneNameGlass.test_two_new_zone_presses_make_two_zones[393-list] _____
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_leaving_the_face_inside_the_window_commits_the_delete[floor-1440] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor 1440: 404; DELETE 1
__ TestZoneNameGlass.test_a_name_the_owner_chose_is_skipped_not_renamed[1440] __
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
__ TestZoneNameGlass.test_a_name_the_owner_chose_is_skipped_not_renamed[393] ___
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
________ TestZoneNameGlass.test_the_chair_does_not_offer_new_zone[1440] ________
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
________ TestZoneNameGlass.test_the_chair_does_not_offer_new_zone[393] _________
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_leaving_the_face_inside_the_window_commits_the_delete[floor-393] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
floor 393: 404; DELETE 1
_ TestZoneNameGlass.test_no_stale_rename_field_after_a_face_change[1440-list-to-spatial] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_leaving_the_face_inside_the_window_commits_the_delete[list-1440] _
[gw0] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
list 1440: 404; DELETE 1
_ TestZoneNameGlass.test_no_stale_rename_field_after_a_face_change[1440-floor-chair-floor] _
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-8-02/.venv/bin/python
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_leaving_the_face_inside_the_window
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-09-26T20:41:19Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.pdKQP8U5R9 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_on_the_list_keeps_the_object -p no:cacheprovider`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 32edb902b430eee261d2cb010c4b948f01493dbd

```text
..                                                                       [100%]
2 passed in 62.09s (0:01:02)
```

### Captured run — 2026-09-26T20:42:24Z

- **Command:** `uv run python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 67deacc818fe402c0eafc59ba15988c648555b17

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2915 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```
