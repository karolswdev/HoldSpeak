# Phase 16 — The Desk, Everywhere (web parity + mesh sync)

**Status:** in-progress (opened 2026-06-24, on the owner's direct instruction after the iPad DeskOS
landed: *"take a fucking five steps back… create a phase that will look at everything we've just
delivered and look for parity with the web client in Astro… and design for synchronization with the
desktop. This is all a mesh system, so everything has to flow back and forth. Knowledge bases, stuff
like that."*)

**Last updated:** 2026-06-24 (**opened.** Authored directly from the instruction. Grounds in three
existing arcs: the **DeskObject convention** ([[story-20-the-desk-object-model]] / HSM-14-20), the
**sync object model** (Phase 10 — `SyncKind` / `Synced<>` / `ChangeSet` in
`apple/Sources/Contracts/Sync.swift`), and **the Mesh** (Phase 15 — `HTTPDesktopClient` pairing, the
desktop as hub, one approval+egress contract). Leads with **HSM-16-01 (the parity & sync contract)** —
the platform-neutral spec everything else is measured against.)

## Why this phase exists

We just built a rich DeskOS on **one** surface (the iPad): objects with physics, the spill of a
meeting into its parts, lasso → bundle → file, floating app windows, and **knowledge bases** — all
governed by one documented convention (the DeskObject). But HoldSpeak is **a mesh, not an iPad app**.
Two things are missing and they are the whole point:

1. **Parity.** The web client (Astro, `web/src`) has none of the DeskOS. The Desk was declared canon
   for **both** surfaces ([[story-19-the-desk]]); right now only one exists. A mesh with one good
   surface is a demo, not a product.
2. **Flow.** Nothing we built **moves between devices.** A knowledge base created on the iPad lives in
   that iPad's `@AppStorage` and dies there. The desktop — the hub that owns the big models, the
   canonical store, the pipeline — has no idea it exists. For a *personal intelligence mesh*, the
   organization layer (KBs, directories, classifications) **must** flow desktop ↔ iPad ↔ web.

This phase makes the Desk a mesh citizen: one convention, three surfaces, one canonical organization
that syncs.

## The load-bearing design call (decided here, refined in 16-01/16-02)

Not everything on the desk is the same *kind* of data, and conflating them would make sync wrong:

- **Content** — Meetings, Artifacts. The canonical record. **Already syncs** (Phase 10). We extend, not
  redo.
- **Organization** — Directories, Knowledge Bases, and **membership/classification** (which object
  belongs to which container). This is **shared, canonical, must-sync** data. A KB and its contents are
  the same on every surface. *(New: HSM-16-02 adds it to the sync model; the desktop is the hub.)*
- **Layout** — where a card physically sits, its presentation mode, whether it's spilled. This is
  **per-device ergonomics**, not shared truth. It does **not** sync as canon (a desk you arranged on
  the iPad is yours; the web arranges its own). At most a soft, last-write hint — never a conflict
  source.

Getting this taxonomy right is the difference between a mesh that feels coherent and one that fights
the user. It is the spine of the whole phase.

## Stories

| ID | Title | Status | Thrust |
|---|---|---|---|
| HSM-16-01 | The DeskObject parity & sync contract (inventory + spec) | todo | the baseline both thrusts measure against |
| HSM-16-02 | The organization sync model (design + contract additions) | todo | sync (design-first) |
| HSM-16-03 | The desktop hub surface for organization | todo | sync (hub) |
| HSM-16-04 | The web Astro Desk (parity build) | todo | parity (the big build) |
| HSM-16-05 | Wire the mesh — organization flows back and forth | todo | sync (wire) |
| HSM-16-06 | The cross-device proof | todo | proof (real metal) |
| HSM-16-07 | Docs catch-up (mesh + DeskObject across surfaces) | todo | docs |

## Where we are

Just opened. The iPad DeskOS (HSM-14-19/20) is live on the device: objects, spill, lasso, directories,
windows, the KB primitive on a documented convention. Nothing of it is on the web or syncs yet — that
is exactly this phase. Next action: author/close **HSM-16-01** (the parity & sync contract), since both
the web build and the sync design are measured against it.

## Relationship to the rest of the roadmap

- **Phase 10 (sync)** — we extend `SyncKind`/`ChangeSet`, mirroring HSM-10-01's principle (sync the
  real entities in a thin envelope, never a parallel schema). We do not re-found sync.
- **Phase 15 (the mesh)** — we reuse the hub framing, `HTTPDesktopClient`, and the one
  approval+egress contract. The organization layer becomes another thing the mesh carries.
- **holdspeak Phase 68 (web convergence)** — its design-pattern catalog + shared Signal tokens are the
  raw material for HSM-16-04; this phase is the DeskOS-specific port the catalog was preparing for.
