# Evidence — HSM-10-01 — Sync provider + object model

- **Shipped:** 2026-06-19
- **Branch:** `holdspeak-mobile/phase-10-sync-object-model`
- **Owner:** unassigned

## Files touched

- `apple/Sources/Contracts/Sync.swift` — the sync object model: `SyncKind`,
  `SyncMetadata` (id/kind/last_modified/deleted), `Synced<T>` (envelope; payload is
  the unmodified entity, `nil` ⇔ tombstone), `ChangeSet` (meetings/artifacts).
- `apple/Sources/Providers/Providers.swift` — `ISyncProvider` fleshed to
  `push(_:)`/`pull()`; new `ISyncStore` (modified-time + tombstone surface).
- `apple/Sources/Providers/Storage/SQLiteStorage.swift` — schema **v2**:
  `modified_at` + `deleted` columns (nullable `json` for tombstones), a guarded
  v1→v2 migration, `ISyncStore` impl (`allMeetings`/`allArtifacts`/`tombstones`,
  `save…(modifiedAt:)`, `delete…(at:)`), and `deleted=0` filters on the loads.
- `apple/Sources/RuntimeCore/Sync/SyncEngine.swift` — `snapshot(of:)`,
  `apply(_:to:)` (validates every payload against the contract before any write),
  `sync(local:via:)`.
- `apple/Tests/RuntimeCoreTests/SyncEngineTests.swift` (6 tests),
  `apple/Tests/ProvidersTests/StorageTests.swift` (schema-version test → v2).
- `pm/roadmap/holdspeak-mobile/contracts/SERIALIZATION-CONTRACT.md` — §11 records
  the sync envelope as an additive contract addition (the story's escalation).

## Verification

`cd apple && swift test` → **55 executed, 3 skipped (opt-in live), 0 failures.**
The Phase-4 storage tests still pass through the v2 migration (round-trip +
crash-recovery + atomicity intact). New sync tests:

```
SyncEngineTests:
  testSnapshotApplyRoundTrip          # seed A -> snapshot -> apply to B; exact contract back; modified_at carried
  testRoundTripAcrossJSONProvider     # A -> JSON wire (encoder) -> decode -> apply to B; entities match
  testSyncFlowDependsOnlyOnProviderSeam  # engine.sync(local:via:) over a fake provider; store intact
  testTombstonePropagatesDelete       # delete in A propagates; B loses the entity; tombstone recorded
  testApplyIsIdempotent               # apply same change-set twice -> one row, unchanged
  testMalformedChangeSetRejectedAtWire# a schema-invalid meeting is rejected by the contract decoder
```

## Acceptance criteria — re-checked

- [x] `ISyncProvider` exists; the Runtime Core depends on the interface (a fake
  JSON-relay provider drives the flow), not a concrete transport.
- [x] The sync object set is the Phase-0 entities; sync metadata is carried in a
  contract-layer envelope (payload = the real entity), not bolted onto each entity.
- [x] A change-set is produced from the Phase-4 store and applied to it, both in
  contract objects (`snapshot`/`apply` over `ISyncStore`/`SQLiteStorage`).
- [x] Applying validates every object against the Phase-0 contract before it
  touches the store (encode→decode through the shared coder = the schema; the wire
  decode rejects malformed payloads — `testMalformedChangeSetRejectedAtWire`).

## Deviations / notes

- Sync metadata is an **additive envelope** (`Synced`/`SyncMetadata`/`ChangeSet`),
  not new fields on the entities — recorded in SERIALIZATION-CONTRACT §11. This is
  the resolution of the story's "escalate to HSM-0-03" note.
- The envelope's **JSON Schema + the Python-side mirror** are deferred to HSM-10-02
  (the transport story that introduces the desktop sync API); HSM-10-01 is the
  Swift object model + engine, host-proven.
- Conflict policy / full idempotency across divergent edits is **HSM-10-03**; this
  story's `apply` is straight upsert-by-carried-`last_modified`.
