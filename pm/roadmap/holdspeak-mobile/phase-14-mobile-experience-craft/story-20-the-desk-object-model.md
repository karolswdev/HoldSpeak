# HSM-14-20 — The DeskObject model: one convention every primitive obeys

- **Project:** holdspeak-mobile
- **Phase:** 14
- **Status:** in-progress — opened 2026-06-24. Grows out of HSM-14-19 ([[story-19-the-desk]]), where the
  desk grew real objects (meetings, their spilled outputs, models) but each kind was minted ad-hoc with
  string-prefix hacks (`model:`, `out:`, `open:`). The owner called the debt: there should be **one
  documented convention** so the hard work is reused, not re-typed — and HoldSpeak's **knowledge base**
  should be a first-class primitive, not an afterthought. This doc is that convention; the build makes the
  code obey it and lands the **Knowledge Base** object as the proof.
- **Depends on:** HSM-14-19 (the Desk shell, the physics canvas, the spill/lasso/file machinery).
- **Owner:** unassigned

## The thesis

Everything on the desk is a **DeskObject**. A meeting, a summary, an action item, a model cartridge, a
directory, a knowledge base, a transcript line — all the *same kind of thing* to the OS: a typed,
material object you can fling, lasso, group, file, open. The differences between them are **declared, not
coded**: each kind fills in the same small set of facets, and the OS does the rest. Add a new primitive =
declare its facets. That is the whole point.

## A DeskObject — the facets every kind declares

| Facet | What it answers | Examples |
|---|---|---|
| **id** | stable identity, namespaced by kind | `meeting:<uuid>`, `out:sum:<mid>`, `kb:<name>` |
| **kind** | which primitive this is | `meeting`, `output`, `model`, `directory`, `knowledgeBase`, `kbEntry` |
| **material** | sprite (bespoke PixelLab), tint, default presentation | cassette / cartridge / sticky-note / crystal |
| **label** | title + subtitle shown on the card | "Incident review", "3 speakers" |
| **open** | what a **tap** does | `.spill`, `.window(app)`, `.read` |
| **children** | what it spills, if it spills | a meeting → its outputs; a KB → its entries |
| **contains** | can it hold other objects (be filed into)? | directory: yes; KB: yes; meeting: no |
| **provenance** | where its data lives | a `Meeting` record, an `Artifact` row, the KB store |
| **egress** | trust scope (reuse the egress badge) | local / local+cloud / cloud→target |

A kind that fills these in gets the entire desk for free: physics, the three presentation modes
(full/half/header via long-press), lasso-select, Bundle, File-into, windowing, persistence.

## The universal grammar — gestures mean the same thing on every object

These are **invariant** across kinds. Documenting them is half the convention's value: a user learns the
desk once.

- **Tap** → *open* (resolves to the object's `open` facet: spill / window / read).
- **Long-press** → *reshape* — cycle the card's presentation (full → half → header), saved per object.
- **Drag** → *fling* — weighted physics; the object slides and settles.
- **Lasso** (Select tool) → *select* — a loop gathers every object whose center it encloses.
- **Bundle** → *cluster* the selection into a tight pack where it sits.
- **File into** → *classify* — drop the selection into a container (directory or knowledge base).
- **Tidy** → snap the scatter into an aligned grid; pull apart to play.

## `open` — the three behaviors a tap can resolve to

1. **`.spill`** — pour this object's **children** onto the desk as their own objects, born at the parent
   and sprayed outward; tap again to collapse. *A container opening into its contents.*
   (meeting → Summary / Topics / Actions / Artifacts / Transcript; knowledge base → its entries.)
2. **`.window(app)`** — open an **app or reader window** floating on the desk: draggable, layered,
   closeable, maximizable. *An application surface.* (model manager, recorder, the notebook, an output
   reader.)
3. **`.read`** — a leaf: open this object's body in a reader window (rendered, copyable). *A document.*
   (a summary, an action item, an artifact, a transcript.)

`.spill` and `.read` are the recursion that answers "outputs aren't files": a container spills objects,
each of which reads in a window — turtles all the way down, never a buried list.

## Containment & classification — directories and knowledge bases are the same machinery

A **container** is any object whose `contains` facet is true. Filing the lasso selection into it sets
`member.container = <name>`; opening the container filters/spills its members. Today there are two
container kinds, identical underneath, different in intent and material:

- **Directory** — a neutral folder you organize by hand. Lives in the left pane's DIRECTORIES section.
- **Knowledge Base** — a *typed, first-class* container for **classified knowledge**. Lives in the
  Library as an **object** (a crystal) you open; opening it **spills its members** onto the desk. Filing
  an object into a KB **is** the act of classifying that data into the knowledge base. This is the
  HoldSpeak KB concept (the project `kb` map on the desktop/web side — see
  [[project_phase47_project_kb_legibility]]) finally made tangible: a thing you hold, fill, and open.

Because a KB reuses **filing** (to classify) and **spill** (to open), it costs almost nothing beyond its
declaration — which is exactly the convention paying off.

## Why this generalizes (the kinds we get cheaply next)

Once the registry exists, each of these is a declaration, not a project:

- **Data classification** — a "bucket" container kind; lasso mixed objects, file them into a labelled
  class; the bucket spills its class back. (KB and directory are the first two instances.)
- **Workflows** — a `workflow` kind whose `open` is `.window(WorkbenchApp)`; drop a model + a meeting on
  it to run (HSM-14-19 pillar 5).
- **Live transcript slips** — a `slip` kind on the live canvas; lasso → action ring (Extract/Tack/Note).
- **People / speakers**, **projects**, **plugin outputs** — all just kinds.

## Scope of the build

- **In:**
  1. A single typed registry — `DeskObjectKind` + its spec (material, `open`, `contains`) — that the
     card-builder and tap-dispatch consult. Retire the scattered `hasPrefix` string hacks behind it.
     Existing kinds (meeting/output/model/directory) behave **identically**; this is a consolidation.
  2. **Knowledge Base** as a first-class kind: created from the left pane; rendered as a crystal **object**
     in the Library; **opening it spills its members**; **filing the lasso selection into it classifies**
     those objects into the KB; persisted; survives relaunch.
  3. A **bespoke PixelLab crystal** sprite for the KB object (not a recycled SF glyph).
  4. This doc as the convention canon, linked from [[story-19-the-desk]].
- **Out:** the web parity of the object model (its own story); live-transcript slips; workflow-run on
  drop (HSM-14-19 step 3). Those are *instances* this convention now makes cheap, scheduled separately.

## Acceptance criteria

- [ ] This convention doc exists and is canon; [[story-19-the-desk]] links to it.
- [ ] One `DeskObjectKind` registry drives material + `open` + `contains`; the `hasPrefix` dispatch is
      gone from the call sites (consolidated into the registry). Existing behavior unchanged on device.
- [ ] A Knowledge Base can be created, appears as a crystal object in the Library, **opens by spilling its
      members**, and **accepts the lasso selection via File-into (classify)**. Persists across relaunch.
- [ ] The KB object wears a bespoke PixelLab crystal sprite.
- [ ] Device-proven on the iPad Air M4 (the app is the proof, not the Simulator — see
      [[feedback_verify_on_device_not_seeded]]).

## Test plan

- Device-arch `xcodebuild` green (the Simulator build is blocked by the swift-syntax `_SwiftSyntaxCShims`
  toolchain issue; device arch is the gate).
- On device: create a KB → it shows as a crystal in the Library → file a lasso selection of meetings +
  outputs into it (classify) → open it → those members spill onto the desk → relaunch → the KB and its
  members persist.
- Regression: meetings still spill, models still open, directories still filter, lasso/Bundle/File still
  work — the consolidation changed the plumbing, not the behavior.
