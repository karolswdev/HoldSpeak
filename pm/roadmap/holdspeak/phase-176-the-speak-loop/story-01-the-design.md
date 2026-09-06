# HS-176-01 — The design

- **Project:** holdspeak
- **Phase:** 176
- **Status:** done
- **Depends on:** Phase 170 merged
- **Unblocks:** HS-176-02, HS-176-03, HS-176-04, HS-176-05
- **Owner:** unassigned

## Problem

Every face in 176 must be designed on the library at 1440 + 393 and
ratified by the owner before any build begins (UX-CANON.md rule A.2).
The Speak Loop introduces new face regions (the correction flow on the
Speak face, the journal as a live stream with filters) and modifies an
existing one (MicButton coverage across all inputs). Without artboards
these cannot be built to canon.

## Scope

- In: artboards at 1440 + 393 for:
  - The correction flow on the Speak face (tap a landed utterance →
    the correction well unfolds beneath it → type the correction →
    save; the correction chip on the utterance row shows what fired;
    the learning digest section reads honest reach numbers).
  - The journal as a live stream (utterance rows with source, target,
    latency, corrections applied, intent tag; filter tokens for
    source: dictation / browser / hotkey; a search bar; scroll to
    load older entries).
  - The MicButton placement rule: the census of ~92 text inputs
    across web/src/desk/ mapped to the placement (inside
    StringGadget, beside EditInPlace, on compound gadgets); the
    artboard shows the placement per species.
  - The learning digest section on the Speak face (count,
    corrections, reach; the empty state: "No corrections yet").
- Out: implementation; new library species (use existing ones).

## Acceptance criteria

- [ ] Artboards at 1440 + 393 on the ratified shell for every new face
      region (Article IX.2; UX-CANON.md rule E.1).
- [ ] Counsel reads the artboards before the owner (UX-CANON.md rule
      E.1).
- [ ] The owner's word on the canvas (Article IX.4).
- [ ] No prose in the artboards (Article VII.1; UX-CANON.md rule A.3).
- [ ] Every artboard uses at least three type steps (UX-CANON.md rule
      C).
- [ ] The correction flow shows the well unfold in-world, not in a
      modal (Article VII.2; UX-CANON.md rule A.4).
- [ ] The MicButton census artboard maps every uncovered input to its
      placement (Article IV.1).

## Test plan

- Unit: n/a (design-only story).
- Integration: n/a.
- Manual: counsel review of artboards; owner review on the artifact.

## Notes / open questions

- The correction well: does it unfold beneath the utterance row (like
  the Adjust well) or beside it (inline edit)? Propose the well
  beneath (consistent with the existing SurfaceWell grammar); the
  owner decides on the canvas.
- The MicButton placement for compound gadgets inside LedgerRows: does
  the mic sit inside the gadget or on the row? The artboard must show
  both options for the owner to choose.
