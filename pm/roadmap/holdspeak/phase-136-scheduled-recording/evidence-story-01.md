# Evidence - HS-136-01

- **Story:** HS-136-01 - The scheduled-capture spine
- **Status:** done
- **Date:** 2026-08-16

## Proof

### Captured run — 2026-08-17T05:26:10Z

- **Command:** `uv run pytest -q tests/unit/test_scheduled_recording_conductor.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** aa3378a2430b6447e44d9cd1d519adfdec811c3e

```text
..............................................                           [100%]
46 passed in 9.15s
```

## Orchestrator verification (the done call)

- **Full suite, the way CI sees it** (isolated HOME, `-n auto`,
  `--ignore=tests/e2e/test_metal.py`): **5879 passed, 47 skipped, 0
  failed** (222s). Run after the fix round on a quiet tree. An earlier
  run before the fix round showed 6 schema-bump bookkeeping fails (the
  v60→v61 version pins + the stale canonical snapshot) and 1 confirmed
  pre-existing xdist flake (`test_promotion_cancellation...`, 3/3 green
  serial → BACKLOG Candidate Z); the 6 were fixed, the flake did not
  recur.
- **Adversarial verification** (fresh read-only opus-worker, verdict
  SHIP-WITH-FIXES): every real-bite axis HELD — restart auto-stop
  durability (deadline persisted before observable + boot reconcile),
  the manual-capture collision gated by the voice floor with graceful
  refusal, the existing-DB additive upgrade of the new table (no 59→60
  repeat), catch-up strictly-future (no storm), mic TOCTOU, and dedupe.
  Its findings were folded in this same story: an honest auto-stop
  receipt on stop-failure (Article VI.1), a corrected `_fire_lock`
  concurrency comment, a start-failure→refused test, and honest DST
  test names (the DST fall-back double-hour is accepted as standard
  cron semantics per owner ruling, noted in `holdspeak/cron.py`, not
  mitigated).
