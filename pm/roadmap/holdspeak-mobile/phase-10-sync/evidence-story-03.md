# Evidence — HSM-10-03 — Conflict + round-trip

- **Shipped:** 2026-06-19 · **Branch:** `holdspeak-mobile/phase-10-conflict`

## The conflict policy (documented)

`SyncEngine.apply` resolves each record by comparing the incoming `last_modified`
to the local one:

- **incoming newer** → apply (live upserts; tombstone deletes; an older live record
  never resurrects a newer tombstone — no zombie re-creates).
- **incoming older** → skip (keep the newer local edit).
- **same timestamp + same content (or both tombstones)** → no-op → **idempotent**.
- **same timestamp + divergent** (both live but different, or delete-vs-edit) → a
  genuine concurrent conflict: keep local and **surface it in the `ApplyReport`**
  rather than silently dropping either side (non-destructive — the host resolves
  surfaced conflicts).

`apply` returns an `ApplyReport { applied, skipped, conflicts }`.

## Files
- `apple/Sources/RuntimeCore/Sync/SyncEngine.swift` — conflict-aware `apply`
  (+ `ApplyReport`, `Conflict`); validates every live payload against the contract
  before any write (the mobile end of "both ends").
- `holdspeak/web/routes/sync.py` — the desktop **push** now validates each record's
  `meta` (id + known kind); malformed → 422, never stored (the desktop end).

## Verification — all over the Phase-0 fixture
- Swift (`SyncConflictTests`): `testRoundTripIsIdempotent` (apply twice → applied=0,
  skipped=2, store unchanged); `testNewerWinsAndOlderIsSkipped` (LWW by time);
  `testConcurrentDivergenceSurfacedNonDestructively` (same-time divergence → conflict
  reported, local kept); `testTombstoneDoesNotResurrectOlderEdit` (older re-create
  skipped; newer resurrects). `swift test` **81/81** (6 opt-in skips).
- Python (`test_web_routes_sync.py`): `test_push_rejects_malformed_record`
  (no `meta` → 422, nothing written). `uv run pytest` → **4 passed**.

## Acceptance criteria — re-checked
- [x] Syncing the same state twice changes nothing (idempotent) — over the fixture.
- [x] A divergent edit resolves non-destructively (no edit silently lost): clear
      timestamp ordering = LWW; concurrent (same-time) divergence is surfaced in the
      report, local retained. Policy documented above; divergent case is a test.
- [x] Deletes propagate via tombstones without resurrecting on the next sync.
- [x] Every object crossing the wire validates against the contract on both ends
      (Swift decode/encode round-trip; desktop push record validation).

## Notes
- Whole-entity LWW for clearly-ordered edits (Meeting/Artifact are opaque to the
  engine); only genuinely-concurrent edits surface as conflicts. A field-level merge
  / conflict-copy store is a future enhancement if usage demands it.
- This is the policy; the **live cross-device run** is HSM-10-04 (needs the iPad).
