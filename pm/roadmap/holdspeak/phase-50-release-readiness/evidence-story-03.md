# Evidence — HS-50-03: Backup + restore

Write-once record of the user-facing backup and restore surface, built on the
`backup_database` primitive from HS-50-02. The rule that matters: a user can take
a copy of their whole database before they upgrade, and a restore can never be the
step that loses data.

## What shipped

**The primitive, upgraded** (`holdspeak/db/core.py`)
- `backup_database(db_path)` now uses SQLite's online backup API
  (`Connection.backup`) instead of a raw file copy, so the snapshot is consistent
  even if a connection is open. It still lands next to the database as
  `<name>.<timestamp>.bak` and never clobbers an existing backup (a counter is
  appended). `_timestamped_backup_path` factors out the naming.
- `restore_database(backup_path, db_path) -> Optional[Path]` — validates the
  backup is a readable HoldSpeak database (probes `schema_version`), snapshots the
  current database first (returning that safety backup), then copies the backup
  into place. Raises `ValueError` on a missing or non-database file. Both names
  are exported from `holdspeak.db`.

**The CLI** (`holdspeak/commands/backup.py`, wired in `holdspeak/main.py`)
- `holdspeak backup` — snapshots the live DB and prints where the copy went. A
  clean no-op with a helpful message when there is no database yet.
- `holdspeak restore` — with no argument, lists the backups next to the database
  (newest first). With a file argument, restores it: prompts before overwriting
  (unless `--yes`), tells the user the current DB was saved first, and prints
  where. A non-database file is rejected with a clear message and a non-zero exit;
  the live DB is left untouched.
- Both are listed in the CLI help epilog.

**Auto-backup wiring** (already from HS-50-02)
- `_ensure_schema` calls `backup_database` before applying the schema on the
  older-version path and logs the backup location, so an upgrade always leaves a
  recoverable copy. HS-50-03 is what makes that primitive a thing the user can
  also run on demand and reverse.

## Verified by hand

```
$ holdspeak backup
Backed up /Users/.../holdspeak.db
      to /Users/.../holdspeak.db.20260607-114340.bak
Keep this file to restore later with: holdspeak restore <file>

$ holdspeak restore
Available backups (newest first):
  /Users/.../holdspeak.db.20260607-114340.bak
Restore one with: holdspeak restore <file>
```

## Tests (`tests/unit/test_backup_restore_cli.py`)

- `test_backup_produces_a_readable_copy` — the backup file exists, opens, and
  carries the seeded row.
- `test_backup_with_no_database_is_a_clean_noop` — no DB -> friendly message, no
  `.bak`, exit 0.
- `test_restore_with_no_arg_lists_backups` — listing path.
- `test_restore_brings_back_old_data_and_snapshots_current` — restore brings back
  the old data and the overwritten state is snapshotted first.
- `test_restore_rejects_a_non_database_file` — junk file rejected, live DB
  untouched, exit 1.
- `test_restore_database_primitive_returns_safety_backup` — the primitive returns
  the safety backup path.
- The HS-50-02 schema test for the primitive was updated to assert a readable
  snapshot (the consistent snapshot is no longer a byte-for-byte copy).

```
uv run pytest -q tests/unit/test_backup_restore_cli.py tests/unit/test_db_schema_policy.py
-> 12 passed

uv run pytest -q --ignore=tests/e2e/test_metal.py
-> 2442 passed, 17 skipped   (was 2436; +6 from this story)
```

## Not done here (by design)

- A guarded HTTP API for backup was left out; the CLI plus the automatic
  pre-upgrade backup cover the acceptance, and a web endpoint that writes files is
  extra attack surface this phase does not need.
- The full upgrade/backup policy doc is HS-50-06; the CLI help and this evidence
  carry the immediate "how" until then.
