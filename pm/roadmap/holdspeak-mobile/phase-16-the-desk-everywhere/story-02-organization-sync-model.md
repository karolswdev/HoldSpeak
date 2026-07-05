# HSM-16-02 — The organization sync model (design + contract additions)

- **Project:** holdspeak-mobile
- **Phase:** 16
- **Status:** done (2026-07-04 resume survey — pre-paid: `SyncKind.kb`/`.directory`/`.membership` shipped in `apple/Sources/Contracts/Sync.swift` with identity+membership canonical and geometry per-device, exactly this story's design call; locked by the Phase-23-04 round-trip matrix)
- **Depends on:** HSM-16-01 (the shapes), Phase 10 (`Sync.swift`).
- **Unblocks:** HSM-16-03 (hub), HSM-16-05 (wire).
- **Owner:** unassigned

## Problem

The sync object model (`SyncKind` / `Synced<>` / `ChangeSet`) carries Meetings and Artifacts only. The
organization layer — Directories, Knowledge Bases, and the membership/classification that puts objects
in them — has no representation on the wire, so it cannot leave the device that created it.

## Scope

- **In:**
  - Extend `SyncKind` with `directory`, `knowledgeBase`, `membership` (organization) **and `workflow`,
    `modelManifest` (capability)** — additive, mirroring the HSM-10-01 principle: sync the real entities
    in a thin `Synced` envelope, never a parallel schema.
  - Define the contract entities (`Directory`, `KnowledgeBase`, `Membership`, **`Workflow`** definition,
    **`ModelManifest`** entry) in `Sources/Contracts`, and widen `ChangeSet` to carry them.
  - **Capability nuance (decided in the phase taxonomy):** a **workflow definition** is portable data
    and syncs in full. A **model** does NOT: only its **manifest** (node id, model id, capabilities,
    context limit) syncs — the GGUF binary stays device-local. So `modelManifest` is a small
    capability advertisement per node, not the file; the binary is never a `Synced` payload.
  - **Conflict + identity policy:** containers keyed by stable id (not display name — names are
    editable); membership is the assignment `objectId → containerId`, last-writer-wins by
    `lastModified`; deletes are tombstones (a removed KB propagates as a tombstone, its memberships
    tombstone with it).
  - **The hub is canonical:** the desktop holds the source of truth; devices reconcile against it
    (design how the iPad's current `@AppStorage` map and the web's store both project onto these
    entities).
  - A short design doc (this phase dir) + the Swift contract additions (host-tested, like HSM-10-01).
- **Out:** the desktop endpoints (16-03), the wiring (16-05). Layout state stays out of sync entirely
  (per 16-01).

## Acceptance criteria

- [ ] `SyncKind` + `ChangeSet` carry directories, knowledge bases, memberships, **workflow definitions,
      and model manifests** as `Synced` envelopes; the entity structs are pure (sync header rides
      outside). The GGUF binary is provably never a sync payload (only the manifest).
- [ ] The conflict/identity/tombstone policy is written down and unit-tested (a rename, a re-file, and
      a delete each reconcile deterministically).
- [ ] The "desktop is canonical, devices reconcile" model is specified, including how the iPad's
      existing `hs.desk.folders/kbs/filed` migrate onto id-keyed entities.
- [ ] `swift test` green for the new contract + reconcile tests.

## Test plan

- Unit: encode/decode round-trip for each new `Synced` kind; a reconcile suite (rename wins by time,
  re-file moves membership, delete tombstones cascade) — host-run via `swift test`.
