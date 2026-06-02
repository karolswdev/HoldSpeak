# HS-31-04 — Squash the migration ladder

- **Project:** holdspeak
- **Phase:** 31
- **Status:** done (2026-06-02). Evidence: [evidence-story-04.md](./evidence-story-04.md).

## Goal

Delete the 18-version migration ladder. Greenfield: there are no old databases to
upgrade, so the entire `_apply_schema()` history (581 lines, `db.py:857-1438`, with
`speakers`/`intent_windows`/etc. re-`CREATE`d 2-3× across versions) collapses to a
**single canonical `CREATE TABLE` set** that builds the current (v18-equivalent)
schema in one shot. `SCHEMA_VERSION` resets to 1.

## Scope

- Replace the version ladder with one canonical schema builder: each table
  defined exactly once, producing the same `sqlite_master` a fresh v18 build does
  today (the resulting schema is what matters, not the history that built it).
- Delete the per-version migration branches and the duplicate `CREATE TABLE`s.
- Reset `SCHEMA_VERSION` to 1; the `schema_version` bookkeeping stays (for *future*
  migrations) but starts fresh.
- Rebuild the author's dev DB one-shot (drop & recreate, or export-then-recreate —
  whichever is least effort; the data is reproducible). Record what was done.

## Test plan

- **Fresh-build parity:** build a brand-new DB with the canonical schema, dump
  `sqlite_master`; compare to a pre-refactor fresh v18 build — diff must be empty
  (modulo intentional cleanup of the redundant duplicate definitions).
- Commit the fresh-build schema-snapshot test so future schema changes stay honest.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — full suite green.

## Done when

- [x] `_apply_schema()`'s 18-branch ladder is gone; one canonical schema builder remains.
- [x] Each table created exactly once; no duplicate `CREATE TABLE`.
- [x] Fresh-build `sqlite_master` matches the pre-refactor v18 schema; `SCHEMA_VERSION` = 1.
- [x] Dev DB rebuilt (drop & recreate); schema-snapshot test committed; full suite green (2063).
