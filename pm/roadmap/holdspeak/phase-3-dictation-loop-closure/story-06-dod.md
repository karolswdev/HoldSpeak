# HS-3-06 — DoD sweep + phase exit

- **Project:** holdspeak
- **Phase:** 3
- **Status:** done
- **Depends on:** HS-3-01 through HS-3-05
- **Unblocks:** phase 3 closure
- **Owner:** unassigned

## Problem

Final phase-exit sweep: validate the four phase-3 exit criteria
against on-disk evidence, generate the phase summary at
`docs/evidence/phase-dir-loop-closure/<YYYYMMDD-HHMM>/`, run the
full regression, and flip the phase to `done`. Mirrors HS-1-11 and
HS-2-11.

## Scope

- **In:**
  - Generate the phase evidence bundle: `00_manifest.md`, `01_env.txt`, `02_git_status.txt`, `10_ut_*.log` (counter + cold-start unit tests), `20_it_*.log` (project-context, llama_cpp e2e, cold-start integration tests), `40_doctor_checks.log` (counters + project-context surface), `99_phase_summary.md`.
  - Run the full-regression command (`uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`) and capture in evidence.
  - Phase tracking docs: flip `current-phase-status.md` story table HS-3-06 to done; check the 6 exit-criteria boxes; bump "Last updated"; project README phase index flips phase 3 to "done"; project README "Last updated" + status updated.
- **Out:**
  - New product code — phase 3 product surface is complete as of HS-3-05.
  - Test additions beyond what the bundle captures from the existing phase-3 suite.
  - Any deferred items the phase enumerated for follow-up.

## Acceptance criteria

- [x] Evidence bundle exists at `docs/evidence/phase-dir-loop-closure/20260426-1111/` with 11 files non-empty, each leading with `# Captured: <ISO>` + `# Git: <sha>` (and where applicable `# Command: <exact>`).
- [x] All 6 phase-exit boxes in `current-phase-status.md` are checked with evidence pointers.
- [x] `99_phase_summary.md` enumerates what shipped + 8 deferred follow-up items.
- [x] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` → 1007 passed, 13 skipped (`30_full_regression.log`).
- [x] Project README phase index shows phase 3 as `done` and "Current phase" reverts to `between phases`.

## Test plan

- **Spec verification:** the exit-criteria boxes above.
- **Bundle smoke:** `ls docs/evidence/phase-dir-loop-closure/<TS>/ | wc -l` matches the expected count.
- **Regression:** the documented full-suite command.

## Notes / open questions

- Bundle path uses the timestamp at the start of the sweep, not at commit time (HS-2-11 convention).
- If the `requires_llama_cpp` integration test passes on the reference Mac during HS-3-02, capture that log in the bundle here so the closure includes proof of the cross-platform default actually running.
