# PHILO-13-11 title bar B: the captured run

Captured by `.githooks/dw evidence capture holdspeak-philo 13 11`. It is kept here and not as `evidence-story-11.md`, because story 11 stays in-progress (`dw check`: evidence for a story that is not done is an error).

### Captured run — 2026-10-03T20:30:15Z

- **Command:** `bash -c set -o pipefail; H=$(mktemp -d); HOLDSPEAK_EVIDENCE_WRITE=1 HOME=$H PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright npm_config_cache=$HOME_REAL/.npm uv run pytest -q -rA tests/e2e/test_philo13_11_titlebar_glass.py tests/unit/test_ux_canon_ratchet.py 2>&1 | tail -20; r=$?; (cd web && npx vitest run src/desk/__tests__/titleBarB.test.ts src/desk/__tests__/workbenchFrame.test.tsx 2>&1 | tail -6); v=$?; rm -rf $H; exit $((r|v))`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c4b2b3be1da7334f9a35cb8934a5bea8a487cfb3

```text
.......                                                                  [100%]
==================================== PASSES ====================================
_____________________ TestTitleBarB.test_title_bar_b[1440] _____________________
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_____________________ TestTitleBarB.test_title_bar_b[393] ______________________
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_________________________________ test_healing _________________________________
----------------------------- Captured stdout call -----------------------------
ratchet: A1 90 -> 87 -- lower the ceiling
=========================== short test summary info ============================
PASSED tests/e2e/test_philo13_11_titlebar_glass.py::TestTitleBarB::test_title_bar_b[1440]
PASSED tests/e2e/test_philo13_11_titlebar_glass.py::TestTitleBarB::test_title_bar_b[393]
PASSED tests/unit/test_ux_canon_ratchet.py::test_ratchet
PASSED tests/unit/test_ux_canon_ratchet.py::test_hard_zeros
PASSED tests/unit/test_ux_canon_ratchet.py::test_ceiling_carries_its_date_and_reason
PASSED tests/unit/test_ux_canon_ratchet.py::test_healing
PASSED tests/unit/test_ux_canon_ratchet.py::test_ds6_exempts_only_the_workbench_ink_divider
7 passed in 16.92s

 Test Files  2 passed (2)
      Tests  18 passed (18)
   Start at  14:30:34
   Duration  1.26s (transform 502ms, setup 128ms, import 702ms, tests 261ms, environment 385ms)
```
