# Phase-3 evidence bundle manifest

- **Phase:** 3 — Dictation Loop Closure (DIR-01 deferred items)
- **Captured:** 2026-04-26 (timestamp `20260426-1111` at the start of the sweep)
- **Git HEAD at sweep:** `3f36046` (HS-3-05) — DoD commit lands directly after this bundle is staged.

## Files

| File | Contents |
|---|---|
| `00_manifest.md` | This file. |
| `01_env.txt` | `uname -a`, Python version, uv version. |
| `02_git_status.txt` | `git log -10 --oneline` + `git status --short`. |
| `10_ut_project_root.log` | `tests/unit/test_project_detector_cwd.py` — 8 passed. (HS-3-01) |
| `10_ut_runtime_counters.log` | `tests/unit/test_runtime_counters.py` — 15 passed (9 counter + 6 cold-start). (HS-3-04, HS-3-05) |
| `10_ut_doctor.log` | `tests/unit/test_doctor_command.py` — 26 passed (incl. 3 project-context + 2 counter + relevant pre-existing). (HS-3-02, HS-3-04, HS-3-05) |
| `20_it_project_context.log` | `tests/integration/test_dictation_project_context.py` — 4 passed. (HS-3-02) |
| `20_it_cold_start.log` | `tests/integration/test_dictation_cold_start_cap.py` — 2 passed. (HS-3-05) |
| `20_it_llama_cpp_e2e.log` | `tests/integration/test_dictation_llama_cpp_e2e.py` — 1 SKIPPED (gated on `llama-cpp-python` + GGUF; both absent on dev box; runs on reference Mac). (HS-3-03) |
| `30_full_regression.log` | `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` — 1007 passed, 13 skipped. |
| `40_doctor_run.log` | `uv run holdspeak doctor` against this checkout. |
| `99_phase_summary.md` | What shipped, exit-criteria mapping, deferred items. |

## Sweep cadence note

Per the standing `feedback_pytest_metal_exclusion` memory, the
full-regression log uses `--ignore=tests/e2e/test_metal.py`; the
metal-tagged path hangs without an interactive mic device.

Per the standing `feedback_no_validation_spikes` memory, no
benchmark numbers ship in this bundle. The bundle proves the
pipeline runs end-to-end (gated tests + integration tests +
unit tests) but does not assert latency targets. Latency is
the user's dogfood-time concern.
