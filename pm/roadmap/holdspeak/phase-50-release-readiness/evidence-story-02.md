# Evidence — HS-50-02: Safe-by-default schema policy

Write-once record of the heart of Phase 50: making `_ensure_schema` safe by
default so an upgrade can never silently destroy a user's data. The rule that
matters: no destructive schema action runs without a backup first, and a
database newer than this build is refused untouched rather than rebuilt.

## The real risk (verified against the live tree, not the brief)

The scaffold framed this as "the next schema bump silently wipes the DB." On
inspection the current `SCHEMA_SQL` is fully additive: all 34 `CREATE TABLE`
statements use `IF NOT EXISTS`, and there is no `DROP`, `DELETE`, or `TRUNCATE`
anywhere in it. So today an over-`executescript` does not literally drop tables.
The danger is latent and still real:

- **A newer DB is run by an older build with no guard.** Before this change,
  `_ensure_schema` only acted when `current < SCHEMA_VERSION`. A database stamped
  *newer* than the running build fell through to a silent no-op, and the old code
  then read and wrote a schema it does not understand. That is corruption waiting
  to happen, and it was completely unguarded.
- **No backup before any future migration.** The moment a real migration step is
  added (an `ALTER`, a data backfill, a table rebuild), the old path would have
  run it with no recoverable copy of the user's data.

Phase 50 is where the forward upgrade contract gets defined, so both holes are
closed now rather than after the first person loses data.

## What shipped (`holdspeak/db/core.py`)

`_ensure_schema` now implements the explicit four-way matrix:

- **fresh / empty** (`_read_schema_version()` returns `None`, or a stored `0`) ->
  create the schema at the current version. This is byte-identical to the
  original install path: same `_apply_schema(conn)`, no backup, no friction.
- **stored == `SCHEMA_VERSION`** -> return immediately. No backup, no rebuild.
- **stored < `SCHEMA_VERSION`** -> `backup_database()` first, log where the backup
  went, then `_apply_schema`. No destructive action without a backup.
- **stored > `SCHEMA_VERSION`** -> raise `SchemaVersionError` with a plain message
  ("written by a newer HoldSpeak ... The database was left untouched") and do not
  touch the file.

Supporting pieces:

- `_read_schema_version() -> Optional[int]` — reads `MAX(version)` from
  `schema_version`; a missing file or missing table both read as `None` (fresh).
  It does not create the file when reading.
- `backup_database(db_path) -> Path` (module-level, exported from `holdspeak.db`)
  — copies the SQLite file to a timestamped sibling `<name>.<timestamp>.bak`,
  appending a counter if that name is taken so a backup never clobbers another.
  A plain file copy is a correct backup here because it runs at startup before
  any mutation, so there is no concurrent writer. HS-50-03 builds the user-facing
  `holdspeak backup` / restore surface on top of this primitive.
- `SchemaVersionError(RuntimeError)` — a dedicated exception so callers and
  `doctor` (HS-50-04) can render the refusal cleanly.

Both new names are re-exported from `holdspeak/db/__init__.py`.

## The fresh-install path is untouched

The empty/absent-DB branch calls the same `_apply_schema(conn)` as before and
takes no backup. Every existing test that builds a temp `Database(...)` (the
`reset_database()` idiom used across the suite) still constructs at the current
version with zero friction. The full suite stays green.

## Tests (`tests/unit/test_db_schema_policy.py`)

Covers the whole matrix:
- `test_fresh_db_is_created_at_current_version` — absent file -> created at
  `SCHEMA_VERSION`.
- `test_at_version_is_a_noop` — reopening a current DB makes no backup and runs no
  rebuild (asserts `backup_database` is never called and no `.bak` appears).
- `test_older_db_is_backed_up_then_applied` — bumps `SCHEMA_VERSION` in the
  fixture (there is no representable older version while it is 1), confirms a
  backup is taken before the apply and the pre-existing row survives.
- `test_newer_db_is_refused_and_left_untouched` — a newer-stamped DB raises
  `SchemaVersionError`, the file is byte-for-byte unchanged, and no backup is
  made.
- `test_backup_database_copies_to_timestamped_sibling` /
  `test_backup_database_does_not_clobber` — the backup primitive.

```
uv run pytest -q tests/unit/test_db_schema_policy.py
-> 6 passed

uv run pytest -q -k "schema or db or database or migrat" --ignore=tests/e2e/test_metal.py
-> 126 passed, 2 skipped

uv run pytest -q --ignore=tests/e2e/test_metal.py
-> 2436 passed, 17 skipped   (was 2430; +6 from this story)
```

## Not done here (by design)

- The user-facing `holdspeak backup` command + restore + docs is HS-50-03 (this
  story exposes the `backup_database` primitive it will wrap).
- Surfacing schema state in `doctor` / `/api/setup/status` is HS-50-04 (the
  `SchemaVersionError` and the version read are the seams it will use).
- No historical migration ladder was built; there are no old versions deployed.
  This defines the forward contract only.
