# Evidence — HSM-4-01 — SQLite schema + stores

- **Shipped:** 2026-06-18
- **Commit:** Phase-4 close bundle on `main` (see commit message)
- **Owner:** unassigned

## Files touched

- `apple/Sources/Providers/Storage/SQLiteStorage.swift` — `IStorage` over the
  built-in `SQLite3` C API (no dependency; macOS + iOS). Tables `meetings(id,
  started_at, json)` + `artifacts(id, meeting_id, json)`; each entity stored as its
  Phase-0 contract JSON, so what reads back is exactly the contract.
- `apple/Sources/Providers/Providers.swift` — `IStorage` enriched with
  `saveArtifact` / `loadArtifacts`.
- `apple/Tests/ProvidersTests/StorageTests.swift` — round-trip tests.

## Verification artifacts

`cd apple && swift test` → **18 tests, 0 failures**. Relevant:

```
testMeetingRoundTripsThroughSQLite passed   # saveMeeting -> loadMeeting == the exact Meeting
testArtifactStore passed                    # saveArtifact -> loadArtifacts(meetingId) == [artifact]
```

The stored/loaded Meeting + Artifact are the Phase-0 fixtures decoded, persisted,
and read back to `XCTAssertEqual` — round-tripping through real SQLite.

## Acceptance criteria — re-checked

- [x] A SQLite schema exists for the meeting + artifact entities; every stored
  field is the Phase-0 contract (JSON-per-row), round-tripping a golden fixture
  with zero drift.
- [x] Read/write goes only through `IStorage`; the store is the SQLite seam.

## Deviations from plan

- v0 stores each entity as contract JSON in a keyed row (segments + action items
  ride inside the Meeting JSON), rather than fully normalized Segment/Action
  tables. Contract-faithful and greenfield-appropriate; normalization (for
  server-side-style facets) can come later without a wire change.
- No SPM dependency: used the system `SQLite3` C API directly.

## Follow-ups

Normalized segment/action tables if/when mobile needs SQL facets like desktop.
