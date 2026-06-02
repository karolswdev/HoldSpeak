# Evidence — HS-31-04 (squash the migration ladder)

**Shipped:** 2026-06-02. The 18-version migration ladder is gone; the schema is built
from one canonical `SCHEMA_SQL` and the dev DB was rebuilt fresh.

## What changed

- **`_apply_schema` ladder deleted.** The method held an `if from_version >= 1:` block
  with ~558 lines of v2→v17 migrations (the source of every duplicate `CREATE TABLE` —
  `speakers`, `intent_windows`, etc. created in both the ladder and `SCHEMA_SQL`). That
  block ran **only for existing DBs**; fresh builds (`from_version=0`) always skipped it and
  built from `SCHEMA_SQL` alone. So the ladder was dead code for new databases — deleted.
- `_apply_schema(self, conn)` now just runs `executescript(SCHEMA_SQL)`, seeds the
  privacy-settings row, and stamps the version. The `from_version` parameter is gone (caller
  `_ensure_schema` updated).
- **`SCHEMA_VERSION` reset 18 → 1.** History starts fresh; future schema changes add
  migration steps from here.
- **Duplicate `CREATE TABLE`s removed** — they lived only in the ladder; `SCHEMA_SQL` itself
  has each table exactly once (verified: zero internal dups).
- `core.py`: **1224 → 666 lines** (−558).

## Schema parity (the safety net)

- Captured the pre-squash fresh-build `sqlite_master` (79 objects, schema_version 18).
- After the squash, a fresh build produces **79 objects, byte-identical `sqlite_master`** —
  only the `schema_version` *value* differs (1 vs 18, intended; not part of `sqlite_master`).
- Committed `tests/fixtures/db_schema_canonical.txt` (the 79-object snapshot) +
  `test_fresh_schema_matches_canonical_snapshot` — any future schema change must update the
  snapshot in the same commit, keeping the schema honest now that there's no version ladder.

## Dev DB

Per the chosen approach (drop & recreate): the author's
`~/.local/share/holdspeak/holdspeak.db` (was `schema_version=18`) was **deleted and recreated
fresh at `schema_version=1`**. No data preserved (greenfield dev data).

## Tests ran

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **2063 passed, 14 skipped**
  (+1 vs prior: the new snapshot test). Output read.
- `uv run ruff check holdspeak/db/` → **All checks passed!**

## Decisions

- **No upgrade path preserved** (greenfield): an existing pre-squash v18 DB is not migrated
  in place — it's rebuilt. The `_ensure_schema` guard (`current_version < SCHEMA_VERSION`)
  means a stale v18 file would simply skip re-application; the dev DB was dropped instead.
- **Snapshot test over a re-derived ladder:** the honest guard is a committed `sqlite_master`
  snapshot, not a reconstructed migration history.
