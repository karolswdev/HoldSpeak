# HSM-10-03 — Conflict + round-trip

- **Project:** holdspeak-mobile
- **Phase:** 10
- **Status:** done (2026-06-19 — conflict-aware `SyncEngine.apply` (LWW by
  `last_modified`; same-time divergence surfaced non-destructively; tombstone
  no-resurrect; idempotent) + desktop-end push validation. See
  [evidence-03](./evidence-story-03.md).)
- **Depends on:** HSM-10-01, HSM-10-02
- **Unblocks:** HSM-10-04
- **Owner:** unassigned

## Problem

Sync that loses data is worse than no sync. Two devices can edit the same meeting
offline, and re-syncing must never duplicate rows or silently overwrite an edit.
This story defines the conflict policy and proves the round-trip is idempotent,
against the Phase-0 fixtures.

## Scope

- **In:** a non-destructive conflict policy (divergent edits merge or keep-both,
  not blind last-writer-wins for meaningful fields); idempotent round-trip (sync
  twice → no change); deletes handled via tombstones (a delete syncs, a re-create
  doesn't resurrect); all validated against the Phase-0 conformance fixtures.
- **Out:** the transport (HSM-10-02). The device gate (HSM-10-04). Real-time
  collaborative merge (this is occasional sync, not live co-editing).

## Acceptance criteria

- [ ] Syncing the same state twice changes nothing (idempotent) — tested against
      the Phase-0 fixtures.
- [ ] A divergent edit on two devices resolves non-destructively (no edit silently
      lost); the policy is documented and the divergent case is a test.
- [ ] Deletes propagate via tombstones without resurrecting on the next sync.
- [ ] Every object crossing the wire validates against the Phase-0 schemas on both
      ends.

## Test plan

- Unit: idempotency (apply change-set twice → identical store); divergent-edit
  conflict (two stores edit one meeting → both edits survive per policy);
  delete-then-sync (tombstone honored). All over the HSM-0-04 fixtures.
- Manual: a two-device divergent-edit scenario as a forward check for HSM-10-04.

## Notes / open questions

- Conflict strategy is a phase deferred decision — default to keep-both/merge for
  divergent edits, LWW only for trivially-last fields. Get the policy in writing
  before the gate.
- This is the highest-risk story in the phase (data loss); build the divergent-edit
  test first and let it drive the policy (phase stop signal: a test shows a lost
  edit).
