# Evidence — HSM-4-03 — Versioning policy

- **Shipped:** 2026-06-18
- **Commit:** Phase-4 close bundle on `main` (see commit message)
- **Owner:** unassigned

## Files touched

- `apple/Sources/Providers/Storage/SQLiteStorage.swift` — `schemaVersion: Int32 = 1`
  written to `PRAGMA user_version` at open; `userVersion()` reads it back.
- `apple/Tests/ProvidersTests/StorageTests.swift` — `testSchemaVersionIsOne`.

## The policy

- The mobile DB ships at **`SCHEMA_VERSION = 1`** (greenfield: no installs, no
  users, nothing to migrate from — no migration ladder, no compat shims).
- **`SCHEMA_VERSION` is independent of the wire `contract_version`** (`0.1.0`,
  HSM-0-03): a contract bump never forces a DB bump with no storage change, and
  vice-versa. This is the desktop near-miss (Phase 50) deliberately avoided.
- Trigger that ends greenfield discipline: the first TestFlight / public install
  base — at which point a real migration path is owed.

## Verification artifacts

`cd apple && swift test` → 18 tests, 0 failures:

```
testSchemaVersionIsOne passed   # userVersion() == SQLiteStorage.schemaVersion == 1
```

## Acceptance criteria — re-checked

- [x] DB ships at `SCHEMA_VERSION = 1` (asserted) with the greenfield posture
  stated (no migrations/shims).
- [x] `SCHEMA_VERSION` ↔ `contract_version` recorded as independent.
- [x] The trigger that ends greenfield discipline is named.

## Deviations from plan

None.

## Follow-ups

A migration path (and a backup-before-migrate posture, mirroring desktop Phase 50)
when there is a real install base.
