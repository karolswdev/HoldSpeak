# Evidence — HS-31-05 (decomposition closeout)

**Shipped:** 2026-06-02. Phase 31 exit criteria confirmed; `final-summary.md` written; phase frozen.

## Final metrics (on-disk, this session)

`wc -l holdspeak/db/*.py`:

| File | Lines | | File | Lines |
|---|---|---|---|---|
| core.py (container) | 665 | | plugins.py | 814 |
| activity.py | 1553 | | projects.py | 463 |
| meetings.py | 890 | | intel.py | 394 |
| models.py | 345 | | base.py / __init__.py | 49 / 17 |
| **package total** | **5190** | | (orig `db.py`) | 5481 |

The decomposed package is **smaller** than the original single file — the migration-ladder
squash removed more than the per-file scaffolding added.

## Exit-criteria checks (commands run)

- `grep -rEc MeetingDatabase --include=*.py holdspeak tests` → **0 files** (god-class name gone).
- `Database` container has **4 methods** (`__init__`, `_connection`, `_ensure_schema`, `_apply_schema`).
- `SCHEMA_VERSION = 1`.
- `uv run ruff check holdspeak/db/` → **All checks passed!**
- Repos exposed on a fresh `Database`: `['meetings', 'intel', 'plugins', 'projects', 'activity']`.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **2063 passed, 14 skipped** (HS-31-04 run; closeout is docs-only).

## Deliverable

`final-summary.md` written (immutable); `current-phase-status.md` frozen; project README phase
index row 31 → done and the current-phase pointer moved to Phase 32. No code changed in this story.
