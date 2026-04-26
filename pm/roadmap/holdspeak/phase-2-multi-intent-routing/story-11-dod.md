# HS-2-11 — Step 10: Full regression gate + DoD

- **Project:** holdspeak
- **Phase:** 2
- **Status:** done
- **Depends on:** HS-2-02 through HS-2-10
- **Unblocks:** phase exit (MIR-01 closure)
- **Owner:** unassigned

## Problem

Spec §9.11 + §11 — final phase-exit sweep: validate every `MIR-*`
requirement against the §7.2 matrix, generate the spec §8.2 evidence
bundle at `docs/evidence/phase-mir-01/<YYYYMMDD-HHMM>/`, write the
phase summary documenting outcome + deferred items, run the §9.11
full-regression command set, and flip the phase to `done`. Mirrors
HS-1-11 in DIR-01.

## Scope

- **In:**
  - Generate complete spec §8.2 evidence bundle at `docs/evidence/phase-mir-01/20260426-0037/` with all 17 required files: `00_manifest.md`, `01_env.txt`, `02_git_status.txt`, `03_traceability.md` (full MIR-* matrix), `10_ut_router.log` (51 cases), `10_ut_security.log` (2 cases), `20_it_routing.log` (9 cases), `20_it_synthesis.log` (11 cases), `20_it_fallback.log` (3 cases), `30_db_checks.txt` (14 cases + DDL extract), `31_migration_checks.txt`, `40_api_checks.log` (14 cases), `41_cli_checks.log` (7 cases + --help), `50_perf.txt` (n=100 routing-per-window timing), `60_logs_sample.txt` (MIR-O-001 + MIR-S-003), `61_metrics_sample.txt` (MIR-O-002 + MIR-O-003), `99_phase_summary.md`.
  - Run the spec §9.11 full-regression command set: `uv run python -m compileall holdspeak`, `uv run pytest -q tests/unit`, `uv run pytest -q tests/integration`, `uv run pytest -q tests/integration -m requires_meeting`. All four must pass.
  - Phase tracking docs: flip `phase-2-multi-intent-routing/current-phase-status.md` story table HS-2-11 to done; check the 7 exit-criteria boxes; bump "Last updated"; project README phase index flips phase 2 to "done"; project README "Last updated" + "Current phase" updated to reflect closure.
- **Out:**
  - New product code. The phase-2 product surface is complete as of HS-2-10.
  - Test additions beyond what the bundle captures from the existing 81-test phase-2 suite.
  - Any of the 8 deferred items in `99_phase_summary.md`'s "Gaps + deferred items" — those belong in follow-up stories, not in HS-2-11.

## Acceptance criteria

- [x] All 17 spec §8.2 files exist + are non-empty in `docs/evidence/phase-mir-01/20260426-0037/`.
- [x] Each evidence file leads with `# Captured: <ISO timestamp>` and `# Git: <commit sha>` per spec §8.3 rule 2.
- [x] Each test log leads with `# Command: <exact command>` per spec §8.3 rule 1.
- [x] `03_traceability.md` maps every `MIR-F-*`, `MIR-D-*`, `MIR-A-*`, `MIR-R-*`, `MIR-O-*`, `MIR-S-*` requirement to its evidence artifact + verification method.
- [x] `99_phase_summary.md` lists what shipped (10 commits, ~5.7k lines, 81 new tests) and explicitly enumerates 8 deferred follow-up items.
- [x] Spec §11 DoD items 1–7 explicitly checked + addressed in `99_phase_summary.md`.
- [x] Spec §9.11 verification gate — all 4 commands pass:
  - `uv run python -m compileall holdspeak` → PASS
  - `uv run pytest -q tests/unit` → 770 passed, 1 skipped
  - `uv run pytest -q tests/integration --ignore=tests/e2e/test_metal.py` → 191 passed, 1 skipped
  - `uv run pytest -q tests/integration -m requires_meeting` → 128 passed, 64 deselected
- [x] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` → 973 passed, 12 skipped, 0 failed in 17.28s. Pass delta vs. HS-2-10: 0 (this story ships no new tests; the bundle exercises the existing suite from HS-2-02..10).

## Test plan

- **Spec §9.11 verification gate:** the 4-command set above.
- **Bundle smoke:** `ls docs/evidence/phase-mir-01/20260426-0037/ | wc -l` → 17.
- **Regression:** `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- Bundle path uses the timestamp at the start of the sweep
  (`20260426-0037`), not at commit time.
- The §9.11 integration sweep was split into two invocations
  (one excluding `tests/e2e/test_metal.py`, one with the
  `requires_meeting` mark) because the metal-tagged path includes
  hardware-only tests that hang on missing mic devices — documented
  in the standing memory `feedback_pytest_metal_exclusion.md`. Both
  invocations passed.
- The deferred items in `99_phase_summary.md` are not bugs or
  oversights — each is a deliberate scope boundary documented in
  its originating story (HS-2-06, HS-2-08, HS-2-09, HS-2-10).
- HS-1-11 (DIR-01 DoD) included real-bug discovery via end-to-end
  execution. HS-2-11 doesn't repeat that pattern because real bugs
  *were* found earlier in the phase (notably the circular import
  in HS-2-08 and 4 minor test-construction mistakes across
  HS-2-04..07), each fixed in its originating commit. The phase
  closes with a clean slate, not a scramble.
