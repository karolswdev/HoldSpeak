# Evidence — HS-2-11 (Phase MIR-01 DoD sweep)

**Story:** [story-11-dod.md](./story-11-dod.md)
**Date:** 2026-04-26
**Status flipped:** backlog → done; **phase MIR-01 → done**

## What shipped

**No new product code.** This story shipped the spec §8.2 evidence
bundle + the spec §9.11 regression gate validation + phase tracking
doc updates that flip MIR-01 to `done`.

- `docs/evidence/phase-mir-01/20260426-0037/` — full bundle (17 files).
  Per spec §8.3:
  - All files lead with `# Captured: <ISO timestamp>` and `# Git: <commit sha>`.
  - All test logs lead with `# Command: <exact pytest invocation>`.
  - `03_traceability.md` maps every `MIR-*` requirement (32 total) to a passing artifact.
  - `99_phase_summary.md` documents outcome + 8 deferred follow-up items + DoD checklist.
- Phase tracking docs:
  - `current-phase-status.md` — HS-2-11 → done; 7 exit-criteria boxes checked.
  - `pm/roadmap/holdspeak/README.md` — phase index flips phase 2 to "done"; current phase line points at the phase 2 folder noting closure; "Last updated" bumped.

## Spec §9.11 full-regression gate

```
$ uv run python -m compileall holdspeak
compileall: PASS

$ uv run pytest -q tests/unit
770 passed, 1 skipped in 2.15s

$ uv run pytest -q tests/integration --ignore=tests/e2e/test_metal.py
191 passed, 1 skipped in 15.42s

$ uv run pytest -q tests/integration -m requires_meeting
128 passed, 64 deselected in 4.14s
```

All 4 gates PASS. The integration sweep is split into two invocations
to keep `tests/e2e/test_metal.py` (hardware-only Whisper baseline +
mic-device-required siblings that hang) out of the loop, per the
standing memory `feedback_pytest_metal_exclusion.md`.

## Bundle inventory

```
$ ls docs/evidence/phase-mir-01/20260426-0037/
00_manifest.md
01_env.txt
02_git_status.txt
03_traceability.md
10_ut_router.log         (51 cases passed in 0.43s)
10_ut_security.log       (2 cases passed in 0.03s)
20_it_routing.log        (9 cases passed in 0.54s)
20_it_synthesis.log      (11 cases passed in 0.39s)
20_it_fallback.log       (3 cases passed in 0.29s)
30_db_checks.txt         (14 cases + DDL extract; idempotent reruns)
31_migration_checks.txt  (MIR-D-005 PASS — re-run construction idempotent)
40_api_checks.log        (14 cases passed in 0.66s)
41_cli_checks.log        (7 cases passed + holdspeak intel route --help)
50_perf.txt              (median 0.0096ms over n=100 — MIR-R-001 trivially met)
60_logs_sample.txt       (MIR-O-001 + MIR-S-003 PASS)
61_metrics_sample.txt    (MIR-O-002 + MIR-O-003 PASS)
99_phase_summary.md
```

17 files, all spec §8.2 names present.

## Spec §11 DoD checklist (verified in 99_phase_summary.md)

1. ✓ Every MIR-* requirement has passing verification (`03_traceability.md`).
2. ✓ Required evidence files exist + are non-empty (`00_manifest.md`).
3. ✓ Router supports dynamic intent shifts + multi-intent windows.
4. ✓ Synthesis pass runs + stores lineage links.
5. ✓ No regressions in deferred-intel paths — full sweep clean.
6. ✓ Phase summary lists known gaps + deferred work (8 items).
7. ✓ Web UI exposes MIR-01 controls end-to-end without TUI.

## Regression sweep

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
973 passed, 12 skipped in 17.28s
```

Pass delta vs. HS-2-10: 0 (this story ships no new tests; the bundle
exercises the existing 81-case phase-2 suite plus inherited coverage
from HS-2 scaffolding through HS-2-10).

## Acceptance criteria — re-checked

All 8 checked in [story-11-dod.md](./story-11-dod.md).

## Deviations from plan

None. The phase closed clean — no real-bug discovery in this story
because real bugs were found + fixed earlier in the phase (notably
the HS-2-08 circular import). Pattern divergence from HS-1-11 (which
included a real-bug discovery during DoD) is documented in story Notes.

## Files in this commit

- `docs/evidence/phase-mir-01/20260426-0037/` (new directory, 17 files)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/story-11-dod.md` (status flip + acceptance criteria checked)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md` (story table flip + phase exit boxes + Where we are + Last updated)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/evidence-story-11.md` (this file)
- `pm/roadmap/holdspeak/README.md` (phase index flip + Current phase + Last updated)
