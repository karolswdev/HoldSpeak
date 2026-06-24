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
- **Capability** — the **executable, combinable** layer. Two members, treated differently on the wire:
  - **Workflows** — the Workbench's visual-programming AI programs (the node graph / blueprint). The
    **definition is portable canonical data → it syncs** (author on the iPad, run on the Mac). A
    workflow is a first-class object you **combine**: drop it onto a meeting / KB / selection and it
    **runs immediately**, producing Content (artifacts).
  - **Models** — the GGUF cartridges. A model **binary is device-local** (you do not sling gigabytes
    across the mesh; the iPad can't hold the Mac's big model). What **syncs is the model *manifest***:
    "this node has this model, with these capabilities." That lets a workflow say *run on a reasoning
    model* and the mesh **resolve the target per node** — exactly Phase-15 fluid compute (RUNS-ON:
    on-device / your Mac / endpoint). Manifest syncs; binary stays put.
- **Layout** — where a card physically sits, its presentation mode, whether it's spilled. This is
  **per-device ergonomics**, not shared truth. It does **not** sync as canon (a desk you arranged on
  the iPad is yours; the web arranges its own). At most a soft, last-write hint — never a conflict
  source.

**The cross-cutting behavior — combination/execution.** The classes are not islands: a **Workflow**
(capability) runs against an **input** (content or organization) on a **target Model** (capability,
resolved per node) and emits **Content** (artifacts). "Run a workflow immediately against something" is
the desk made productive — a drag-drop on the canvas, the same gesture as play. The Workbench already
does the non-spatial version (detail → "Run a workflow" → `generate(workflowTypes:)`); this phase makes
workflows and models first-class **DeskObjects** you combine, and makes their definitions/manifests flow
so a workflow authored on one surface runs on any node of the mesh.

**The atom under all of it — Ask AI (HSM-16-09).** The simplest, highest-value form of combine needs no
authored graph at all: **lasso context → pull "Ask AI" from a drawer → speak a prompt → a card prints
out of the shelf → keep it or bin it.** This is the gamified core of the whole DeskOS — context +
spoken intent + a physical result you judge. A workflow is just this atom *saved and chained*. It runs
**on-device today** and needs none of the mesh, which makes it the natural **lead** for the capability
work — the fastest path to felt value while 16-02..05 build the sync underneath.

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
| HSM-16-09 | **The Ask AI atom** — lasso → ask → speak → print → keep/bin (on-device, no mesh needed) | todo | capability (the atom — a lead candidate) |
| HSM-16-08 | Capability objects: workflows + models, combinable + runnable across the mesh | todo | capability (combine/execute) |
| HSM-16-06 | The cross-device proof | todo | proof (real metal) |
| HSM-16-07 | Docs catch-up (mesh + DeskObject across surfaces) | todo | docs |

*(16-08/09 are the capability layer; 09 is the atom 08 generalizes. 09 needs no sync and can lead. 06/07
stay the closing proof + docs.)*

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
