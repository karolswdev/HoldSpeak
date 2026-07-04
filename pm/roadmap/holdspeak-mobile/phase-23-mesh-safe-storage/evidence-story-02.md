# Evidence — HSM-23-02 — Backup-then-apply (timestamped) before migration

**Status:** done. Built in **Equilibrium Wave 4 (2026-06-27)** alongside HSM-23-01;
recorded here on phase open (2026-07-04) with a fresh green run.

## The shipped mechanism

`apple/Sources/Providers/Storage/SQLiteStorage.swift`:

- On the upgrade arm only (`stored > 0 && stored < schemaVersion`, `:65-67`), the open
  path calls `backupBeforeMigrate` BEFORE `migrateIfNeeded`.
- `backupBeforeMigrate` (`:75-90`): copies the SQLite file to
  `<path>.<yyyyMMdd-HHmmss>.bak` (collision-suffixed `-1`, `-2`, …), best-effort and
  logged — a failed copy never blocks opening the store (the desktop `backup_database`
  safety-net rule). The timestamp format matches the desktop backup naming (`:266-274`).

## The lock

`apple/Tests/ProvidersTests/SQLiteStorageSchemaSafetyTests.swift`:

- `testOlderDatabaseIsBackedUpThenMigrated` (`:76`): seeds a real v1 DB, asserts no
  backup pre-open, exactly ONE `.bak` sibling post-open, that the backup is the
  **pre-migration** copy (`user_version` still 1), and that the v1 row survives with the
  v2 columns live.
- `testEqualVersionDatabaseIsNoOp` (`:117`): an equal-version reopen takes no new backup,
  keeps the version stamp, keeps the data.

## Fresh run on phase open (2026-07-04)

```
swift test --filter 'SQLiteStorageSchemaSafetyTests|StorageTests'
Executed 8 tests, with 0 failures (0 unexpected)
[SQLiteStorage] schema 1 < 2; backed up to …/hsm-safety-….sqlite.20260703-200136.bak before migrating
```

The backup log line above is the mechanism firing live inside the test run.

## Honest boundaries

- Best-effort by design: a failed copy logs and continues (availability over ceremony,
  the desktop rule).
- No user-facing restore flow on the iPad (the desktop CLI owns restore); the HSM-23-03
  panel will *report* the backup, not manage it.
