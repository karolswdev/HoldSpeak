# Evidence — HS-79-04 — the density guard locks the new shapes

**Status:** done (2026-07-03).

## The lock

`tests/unit/test_backend_density_guard.py` extended with two checks over the three
Phase-79 packages (`db/activity/`, `web/routes/system/`, `web/routes/primitives/`):

- `test_phase79_package_inits_stay_composition_only` — every package `__init__` ≤ 90
  lines (an `__init__` composes and re-exports; behavior belongs in a concern module).
- `test_phase79_package_modules_stay_single_concern` — every concern module under the
  shared 600-line budget, except `system/settings.py`, which is ONE concern (the
  settings PUT validation matrix, shipped at 701) and carries its own named budget
  (800) — raising a budget stays a reviewed decision, not a reflex.

The docstring's ledger updated: the old watch item (`routes/meetings.py`) is recorded
as resolved by Phase 72; the new named watch item is `db/core.py` (~1,266 — schema DDL
+ migrations, snapshot-pinned, a different budget conversation).

## Proven both ways

- **Red:** a fabricated 601-line `_fat_probe.py` dropped into `db/activity/` made the
  package check fail with the carve-don't-bump message; removed.
- **Green:** guard file 7/7; full unit suite **2409 passed** (the two new checks
  included).
