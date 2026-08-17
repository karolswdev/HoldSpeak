# HS-137-01 — The declarative reconcile + open path

- **Project:** holdspeak
- **Phase:** 137
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-137-02, HS-137-03, HS-137-04
- **Owner:** unassigned

## Problem

`_ensure_schema` (`holdspeak/db/core.py:162-185`) gates DB open on a
version integer: fresh → run the chain; current → no-op; newer → raise
`SchemaVersionError` (this is what refuses the owner's own v63 DB);
older → backup + run the chain. The chain is `run_migrations`
(`holdspeak/db/migrations.py`, 1061 lines). Replace all of it with one
declarative reconcile.

## Scope

### In (invariants A1–A5)

- **`reconcile_schema(conn)`** (in `holdspeak/db/schema.py` or a new
  `holdspeak/db/reconcile.py`):
  1. `conn.executescript(SCHEMA_SQL)` — creates any missing
     table/index/trigger (all already `IF NOT EXISTS`). (A3 tables)
  2. Introspect each canonical table: parse the column list from
     `SCHEMA_SQL`, `PRAGMA table_info(<table>)` for the live columns, and
     `ALTER TABLE <t> ADD COLUMN <col> <def>` for each missing one. (A3
     columns) Use a **constant** default for the ALTER when the canonical
     default is a function like `(datetime('now'))` — existing rows have
     no value; new INSERTs still get the function default from the table
     definition. (A4)
  3. Run the idempotent seeds/backfills carried from
     `migrations.py:_apply_seeds_and_backfills` (`backfill_decisions`,
     `rebuild_memory_index`, the privacy seed).
  - ADD ONLY — never DROP a table/column, never DELETE a row (A1); leave
    orphan tables untouched.
- **Rewire the open path:** replace the `_ensure_schema` body
  (`core.py:162-185`) with an unconditional `reconcile_schema(conn)` — no
  version read, no `SchemaVersionError`, no backup-on-upgrade. (A5)
- **Delete `SchemaVersionError`** (`core.py:42-43`) and its raise.
- **Keep `backup_database`** available as an explicit user command; just
  do not auto-trigger it on open.
- The `schema_version` table may remain as an informational stamp
  (written, never read to gate) OR be dropped — pick the simpler; nothing
  may branch on it.

### Out

- Deleting `migrations.py` and the export/doctor cleanup (HS-137-02).
- Test deletion/rewrite (HS-137-03).
- The real-DB proof (HS-137-04).
- `_migrate_renames` / the non-additive historical rebuilds: NOT carried
  — they are gated ≤ v57 and the live DB already applied them; only a
  very old backup would need them (accepted caveat).

## Acceptance criteria

- [ ] `reconcile_schema` creates a missing table on open (A3, test).
- [ ] `reconcile_schema` adds a missing column on open, including a
  `datetime('now')`-default column via a constant ALTER default (A3/A4,
  test).
- [ ] Running it on a current DB is a clean no-op (A2, test).
- [ ] It never drops an orphan table or any row (A1, test: seed an extra
  table + rows, reconcile, assert both survive).
- [ ] Opening a DB stamped "newer" than the code no longer raises (A5,
  test).
- [ ] The open path uses the reconcile unconditionally; `SchemaVersionError`
  is gone.

## Test plan

- `uv run pytest -q tests/ -k "reconcile or schema_policy or test_db"`
  — the reconcile unit tests + the existing shape/snapshot test.
- Scoped only; the real-v63-DB proof rides HS-137-04.
