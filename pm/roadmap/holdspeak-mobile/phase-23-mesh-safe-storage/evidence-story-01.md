# Evidence — HSM-23-01 — Refuse-newer on the iPad store

**Status:** done. Built in **Equilibrium Wave 4 (2026-06-27)**, before this phase opened
(the wave log rides `EQUILIBRIUM.md` §Wave 4, "iPad schema safety"); recorded here on
phase open (2026-07-04) with a fresh green run.

## The shipped mechanism

`apple/Sources/Providers/Storage/SQLiteStorage.swift`:

- `StorageError.tooNew(stored:build:)` (`:13`) — the typed refusal, mirroring the desktop
  `SchemaVersionError`.
- The open path reads `user_version` **before** any migrate or stamp (`:44`); if
  `stored > Self.schemaVersion` it closes the handle and throws (`:45-49`) — the DB is
  never written, never downgrade-stamped. A fresh DB reads 0 and falls through unchanged.

## The lock

`apple/Tests/ProvidersTests/SQLiteStorageSchemaSafetyTests.swift`
`testNewerDatabaseIsRefusedAndLeftUntouched` (`:44`): seeds a raw DB at
`schemaVersion + 5` with a future-only column + row, asserts the open throws `.tooNew`
with the exact stored/build pair, that `user_version` is STILL the future version
afterwards, and that the future column and its row survive byte-intact.

## Fresh run on phase open (2026-07-04)

```
swift test --filter 'SQLiteStorageSchemaSafetyTests|StorageTests'
Executed 8 tests, with 0 failures (0 unexpected)
```

(3 schema-safety + 5 storage; the run also printed the 23-02 backup line, see
[`evidence-story-02.md`](./evidence-story-02.md).)

## Honest boundaries

- The refusal is provider-layer only: the app renders it as a generic
  "Store unavailable" string today. Surfacing it honestly is **HSM-23-03**, deliberately
  a separate story.
