# The DeskOS build sequence — the most logical order to build it all

> Authored 2026-06-24 on the owner's instruction: *"Build them in accordance to the most logical
> sequence of feature building."* This orders everything designed for the DeskOS (the convention, the
> Living Desk substrate, environments, the Ask atom, capability, web parity, mesh sync) by **dependency
> first, value second** — so we never build on a substrate we'll have to redo.

## The governing principle

**Substrate before surface before sync.** Build the foundation that everything renders/physics on
first; then the room and the first real function on that foundation; then the live-system depth; then —
only once the iPad experience is settled — port it to the web and wire the mesh. Porting or syncing a
*moving* design is the one thing that guarantees rework.

Sync **design** is the exception: it's cheap to author early and costs nothing to hold, so the contract
/ model can be written in parallel anytime. Sync **wiring** and the **web port** wait for a stable desk.

## The sequence

### Stage 0 — Foundation (the substrate everything sits on)
1. **The Living Desk** ([[story-22-the-living-desk]], HSM-14-22) — the fixed-angle 3D room: cards lay on
   the surface, lift on pick, fall + stack, real light/shadow. **SceneKit.** *Everything visual below
   depends on this; build it first or rebuild it later.*

### Stage 1 — The room + the first real function (both on the substrate)
2. **Desk Environments** ([[story-21-desk-environments]], HSM-14-21) — the 3 environments (Marble & Lamp,
   Walnut, Midnight Carbon) + the builder, now as real SceneKit material+light rigs. *The "holy shit"
   screenshot. Needs the 3D substrate to be meaningful.*
3. **The Ask AI atom** ([[story-09-the-ask-ai-atom]], HSM-16-09) — lasso → ask → speak → print → keep/bin.
   *Highest functional value; on-device, no mesh. Can build alongside #2 (logic + a printed card). Makes
   the desk DO something.*

### Stage 2 — The live-system depth
4. **Buildable barriers** (HSM-14-22 part 2) — pencils / erasers / clay walls that objects collide with.
   *Needs the height-physics from Stage 0. The desk becomes a space you shape.*
5. **Capability objects** ([[story-08-capability-objects]], HSM-16-08) — workflows + models as first-class
   objects with **drop-on = run**. *Generalizes the Ask atom into saved, chained programs.*

### Stage 3 — Cross-surface + mesh (once the iPad desk is settled)
6. **Sync contract + model + hub** ([[story-01-parity-and-sync-contract]] / [[story-02-organization-sync-model]]
   / [[story-03-desktop-hub-surface]], HSM-16-01/02/03) — *authorable in parallel from now; lands here.
   The desktop becomes the canonical hub for the organization + capability layers.*
7. **The web Astro Desk** ([[story-04-web-astro-desk]], HSM-16-04) — port the now-stable desk to `web/src`.
   *Port a settled design, not a moving one.*
8. **Wire the mesh** ([[story-05-wire-the-mesh]], HSM-16-05) — organization + capability flow
   desktop ↔ iPad ↔ web. *(Models never sync — manifest only. Layout stays per-device.)*
9. **The cross-device proof** ([[story-06-cross-device-proof]], HSM-16-06) — owner-witnessed, real metal.
10. **Docs catch-up** ([[story-07-docs]], HSM-16-07).

## Why this order (the dependency spine)

- Environments + barriers are **meaningless or rework** without the 3D substrate → **Living Desk is #1.**
- The Ask atom is **on-device and view-tolerant** → highest-value function, built early (Stage 1).
- Capability **generalizes** the atom → after it.
- The web port + the mesh wiring consume a **stable** iPad desk + the synced contract → last, after the
  experience stops moving. Sync *design* rides along earlier because it's cheap to hold.

## State classes (the sync taxonomy this sequence respects)

- **Content** (meetings, artifacts) — syncs (Phase 10).
- **Organization** (KBs, directories, classification) — syncs, canonical via the hub.
- **Capability** (workflow definitions; model *manifests*) — definitions sync; **model binaries never
  do** (too large — owner-confirmed).
- **Layout** (card position, the built barriers, the active environment arrangement) — per-device; a
  custom environment *composition* may sync as a small preference.
