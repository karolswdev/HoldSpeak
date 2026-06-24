# HSM-16-01 — The DeskObject parity & sync contract (inventory + spec)

- **Project:** holdspeak-mobile
- **Phase:** 16
- **Status:** todo
- **Depends on:** [[story-20-the-desk-object-model]] (the convention), Phase 10 sync model.
- **Unblocks:** HSM-16-02 (sync), HSM-16-04 (web), HSM-16-05 (wire).
- **Owner:** unassigned

## Problem

The iPad DeskOS exists as shipped Swift, not as a platform-neutral specification. Before we build the
web twin or design sync, we need one document that says exactly **what the Desk is** — every object
kind, every gesture, every persisted byte — and **classifies each piece of state** by the
content / organization / layout taxonomy from the phase anchor. Without it, the web port is guesswork
and the sync model risks syncing the wrong things.

## Scope

- **In:** a spec doc (this phase dir, `DESK_PARITY_AND_SYNC.md`) that inventories the shipped iPad DeskOS:
  - **Object kinds** (from `DeskObjectKind`): meeting, output, notebook, model, directory,
    knowledgeBase — each with its material, label, `open` behavior, children, `contains`.
  - **Gestures**: tap / long-press / drag / lasso / bundle / file / tidy — the invariant grammar.
  - **Persisted state** (the real `@AppStorage` keys today): `hs.desk.pinned`, `hs.desk.cardmodes`,
    `hs.desk.folders`, `hs.desk.kbs`, `hs.desk.filed` — each mapped to the taxonomy:
    - `folders`, `kbs`, `filed` → **organization** (must sync, canonical).
    - `cardmodes`, pinned, spill/expanded, positions → **layout** (per-device, does not sync as canon).
  - The **platform-neutral data shapes** the web must match and sync must carry: `Directory`,
    `KnowledgeBase`, `Membership` (object id → container id).
- **Out:** building any of it. This is the contract; 16-02/16-03/16-04 consume it.

## Acceptance criteria

- [ ] The spec exists and inventories every shipped object kind, gesture, and persisted key, traced to
      Swift `file:line`.
- [ ] Every state key is classified content / organization / layout, with the sync verdict per the
      phase taxonomy.
- [ ] The platform-neutral `Directory` / `KnowledgeBase` / `Membership` shapes are defined (the wire
      shape sync and web both target).
- [ ] Reviewed against the live iPad build (matches what shipped, not an idealized version).

## Test plan

- Documentation story: the test is tracing — every cited kind/key/file verified against the shipped
  `DeskHome.swift` / `DeskPhysicsCanvas.swift`; the taxonomy table is complete (no persisted key
  unclassified).
