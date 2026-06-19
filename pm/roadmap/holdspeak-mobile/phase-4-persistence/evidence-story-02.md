# Evidence — HSM-4-02 — Crash recovery

- **Shipped:** 2026-06-18
- **Commit:** Phase-4 close bundle on `main` (see commit message)
- **Owner:** unassigned

## Files touched

- `apple/Sources/Providers/Storage/SQLiteStorage.swift` — WAL mode
  (`PRAGMA journal_mode=WAL`), `begin()`/`commit()`/`rollback()`,
  `integrityCheck()` (`PRAGMA integrity_check`).
- `apple/Tests/ProvidersTests/StorageTests.swift` — the recovery tests.

## Verification artifacts

`cd apple && swift test` → 18 tests, 0 failures. The two crash-safety guarantees:

```
testCrashRecoveryDurability passed
  # committed write survives a connection abandoned WITHOUT close() (models a
  # crash), reopened DB == the exact Meeting, integrity_check == "ok"
testTransactionAtomicity passed
  # begin -> saveMeeting(pending) -> rollback: committed kept, uncommitted discarded
```

WAL is enabled at open; a committed write is durable across an unclean
(abandoned, unclosed) connection and the file is not corrupt; an uncommitted
write is the part a crash discards (proven via rollback).

## Acceptance criteria — re-checked

- [x] **Full recovery after crash:** a committed Meeting survives an unclean
  shutdown and reopens intact; `integrity_check` passes. WAL configured.
- [x] Mid-write safety: uncommitted work does not persist (atomicity).

## Deviations from plan

- The crash is modeled host-side (abandon an unclosed connection after commit +
  rollback for the uncommitted half). A true on-device **SIGKILL mid-write** is the
  stronger proof and is the device-pending closeout (the OS releasing a held WAL
  lock on process death is the one part an in-process test can't reproduce — see
  the HSM-2-01 sim-probe finding for why in-process abandon keeps the lock).

## Follow-ups

On-device SIGKILL-mid-recording recovery run when Tier-1 hardware is available.
