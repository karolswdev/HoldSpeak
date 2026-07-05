# Evidence — HSM-16-05 (wire the mesh: organization flows back and forth)

**Recorded done on the 2026-07-04 resume survey — pre-paid.**

The wire is not just designed — it is proven both directions and pinned:

- **The Phase-23-04 round-trip matrix**: all 10 `SyncKind`s — kb, directory, and
  directory-membership among them — push→pull byte-faithful per primitive, golden-pinned on both
  sides of the wire (Swift-encoded fixtures fed into the hub parser and back). §11 of the
  serialization contract was rewritten to the shipping wire in the same story.
- **Live merges**: the HSM-22-01 DeskSync pass ported an iPad-authored record to a scratch hub
  live; HSM-22-04 ran the synced result on the hub against the real `.43` endpoint (real metal,
  not fixtures).
- **Conflict + offline discipline** riding underneath: LWW by `last_modified`, tombstone
  no-resurrect, idempotent apply (Phase 10), `SyncCoordinator`'s offline-safe queue.

Suites: `swift test` 437/8/0 at the Phase-23 closeout (2026-07-04); hub side **66 passed** on the
fresh 2026-07-04 targeted run (see evidence-story-01 for the exact command).
