# Evidence - HS-137-01

- **Story:** HS-137-01 - The declarative reconcile + open path
- **Status:** done
- **Date:** 2026-08-17

## Proof

### Captured run — 2026-08-17T16:00:14Z

- **Command:** `uv run pytest -q tests/unit/test_reconcile.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3c98d0fce2c2624a88d33c33a190fda45f0b4f93

```text
................                                                         [100%]
16 passed in 2.18s
```

## Orchestrator verification (the done call)
- Reconcile engine tests: 16 passed (A1–A5 + the hazard tests).
- **Adversarial pass (fresh reviewer): SHIP-WITH-FIXES → all folded.** It
  caught a BLOCKER — the migration-time backfills ran on every open,
  which would resurrect every soft-deleted decision on each launch. Fixed
  at the root: `reconcile_schema` runs data backfills ONLY when the shape
  changed (`shape_changed`); a clean open is a true no-op. Belt-and-
  suspenders in `decisions.py`: soft-deleted rows are skipped and the
  backfill UPDATE never sets `deleted`. Regression test
  `test_soft_deleted_decision_survives_reconcile`. Also folded: FTS
  shadow tables excluded from the reference diff; ISO sentinel default
  for datetime columns in ALTER; conditional pre-change backup (never on
  fresh creation — `test_fresh_creation_does_not_back_up`); atomic
  mutating phase.
- Full suite green (isolated HOME, -n auto): 5917 passed, 0 real
  failures (3 concurrency failures confirmed pre-existing flakes, 2/2
  serial → Candidate Z).
