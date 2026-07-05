# Evidence — HSM-16-02 (the organization sync model)

**Recorded done on the 2026-07-04 resume survey — pre-paid.**

The organization layer syncs as canonical data, exactly this story's design call:

- `apple/Sources/Contracts/Sync.swift` — `SyncKind.kb`, `SyncKind.directory` (comment in-source:
  *"the iPad 'zone': identity + nesting (geometry/paint stays local)"*), and
  `SyncKind.membership = "directory_membership"` (a primitive's home-directory edge; wire kind
  matches the hub). Identity + membership are canonical; geometry/paint stay per-device — the
  content/organization/layout split this story existed to establish.
- The `ChangeSet` decode enumerates `kbs, directories, directoryMemberships` alongside the
  content and capability kinds (one envelope, no parallel schema — the Phase-10 principle held).
- Locked cross-language by the Phase-23-04 **10-kind per-primitive push→pull round-trip matrix**
  (kb / directory / membership rows byte-faithful, golden-pinned on both sides of the wire;
  `swift test` 437/8/0 at the Phase-23 closeout, 2026-07-04).
- Hub side green on the fresh 2026-07-04 targeted run (**66 passed** — see evidence-story-01 for
  the exact command).
