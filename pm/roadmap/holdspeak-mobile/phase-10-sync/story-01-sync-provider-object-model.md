# HSM-10-01 — Sync provider + object model

- **Project:** holdspeak-mobile
- **Phase:** 10
- **Status:** done (2026-06-19 — `ChangeSet`/`Synced` object model + `ISyncStore`
  (SQLite schema v2: modified-time + tombstones) + RuntimeCore `SyncEngine`
  snapshot/apply/round-trip; `swift test` 55/55 incl. 6 sync tests. See
  [evidence-01](./evidence-story-01.md).)
- **Depends on:** HSM-0-04, HSM-4-01
- **Unblocks:** HSM-10-02, HSM-10-03, HSM-10-04
- **Owner:** unassigned

## Problem

Cross-device continuity needs a transport-agnostic seam and a clear answer to
"what syncs." The charter names the objects (Meetings, Actions, Artifacts), and
those are already the Phase-0 contracts — so the sync object model should be the
contracts, not a parallel sync schema that can drift.

## Scope

- **In:** the `ISyncProvider` abstraction (Layer 3) the Runtime Core depends on;
  the sync object model defined as the Phase-0 contract entities (Meetings,
  Actions, Artifacts) with whatever sync metadata they need (ids, last-modified,
  tombstones) carried per the contract; the change-set concept (what to push/pull).
- **Out:** the transport itself (HSM-10-02). Conflict resolution (HSM-10-03). The
  continuity gate (HSM-10-04). A new sync-only schema (sync uses the contracts).

## Acceptance criteria

- [ ] `ISyncProvider` exists and the Runtime Core depends on the interface, not a
      concrete transport (a fake provider drives the sync flow in tests).
- [ ] The sync object set is the Phase-0 contract entities; sync metadata
      (id/last-modified/tombstone) is carried within the contract, not bolted on.
- [ ] A change-set can be produced from the local store (Phase 4) and applied to
      it, both expressed in contract objects.
- [ ] Applying a change-set validates every object against the Phase-0 schemas
      before it touches the store.

## Test plan

- Unit: produce a change-set from a seeded store, apply it to an empty store via a
  fake provider → stores match; every object schema-valid on apply.
- Manual: n/a (transport + device proof come later).

## Notes / open questions

- Sync metadata (last-modified, tombstones for deletes) may need a Phase-0
  contract addition — if so, escalate to HSM-0-03, don't add a sync-only side
  field (phase risk: contract drift).
- Reuse HSM-0-04 fixtures as the test objects so sync is exercised on the same
  golden payloads both runtimes already round-trip.
