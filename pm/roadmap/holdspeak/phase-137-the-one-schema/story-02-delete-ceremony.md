# HS-137-02 — Delete the ceremony

- **Project:** holdspeak
- **Phase:** 137
- **Status:** done
- **Depends on:** HS-137-01
- **Unblocks:** HS-137-04
- **Owner:** unassigned

## Problem

With the reconcile in place (HS-137-01), the migration chain and the
version-integer plumbing are dead weight. Remove them.

## Scope

### In

- **Delete `holdspeak/db/migrations.py`** (1061 lines) entirely. Its only
  production importer is `core.py` (the old `_ensure_schema`, already
  rewired in HS-137-01). Its `_apply_seeds_and_backfills` moved into the
  reconcile in HS-137-01 — confirm nothing else imports from it (grep),
  then remove the file and the import.
- **`holdspeak/db/__init__.py`:** drop the `SchemaVersionError` export;
  drop or demote `SCHEMA_VERSION` (informational only) and
  `read_schema_version` (delete, or keep purely as a diagnostic that
  nothing gates on).
- **`restore_database`** (`core.py:94-113`): its "is this a real
  HoldSpeak DB" probe reads the `schema_version` table
  (`core.py:101`); change the probe to check for a known always-present
  table (e.g. `meetings`).
- **The doctor** (`holdspeak/commands/doctor.py:62-116`,
  `_check_database`): stop comparing the DB version to the build version;
  report DB readability + table count (or that the reconcile succeeded)
  instead.

### Out

- Test rewrites (HS-137-03) — but do not leave production code that fails
  to import; if a test imports `SchemaVersionError`/`read_schema_version`,
  HS-137-03 fixes the test, not this story re-adding the symbol.

## Acceptance criteria

- [ ] `holdspeak/db/migrations.py` is deleted; no production import of it
  remains (grep clean).
- [ ] `SchemaVersionError` is gone from `core.py` and `__init__.py`.
- [ ] `restore_database` validates a backup without reading
  `schema_version`.
- [ ] The doctor's DB check no longer compares versions and passes
  against a reconciled DB.
- [ ] `holdspeak` imports cleanly and a fresh DB opens (smoke).

## Test plan

- `uv run pytest -q tests/ -k "doctor or restore or test_db"` — the
  doctor + restore + db-open smoke. Broken migration-chain tests are
  HS-137-03's to remove; note any that fail here so 03 clears them.
