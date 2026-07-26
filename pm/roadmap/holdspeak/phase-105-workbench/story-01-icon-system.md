# HS-105-01 - The icon system — handles, not mascots

- **Project:** holdspeak
- **Phase:** 105
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-105-02, HS-105-03, HS-105-07
- **Owner:** unassigned

## The verdict (the bar)

The owner, on the current world layer: large lamp-like icons "that
don't do shit and just make it look bad." The reference: Workbench
2.0 icons — pixel art, yes, but ~small-footprint, palette-locked,
one light source, and above all DUAL-STATE (a distinct selected
image) and INFORMATIVE (a drawer told you it was a drawer; a disk
wore its state). The current sprites are single-state illustrations
at mascot scale whose only message is their category.

## Problem

An icon is a live handle; the desk's objects are pictures. Three
concrete failures: (1) scale — the sprite footprint is illustration-
sized, so five objects fill a screen and forty would be chaos; (2)
statelessness — a KB with 14 members, an agent whose endpoint circuit
is open (HS-103-04 serves this today), a note edited an hour ago,
and their untouched twins render identically; (3) no rendered state
images — selection is a ring bolted on, and armed/stale/needs-you
have no visual grammar at the object at all.

## Recipe

1. **The footprint contract first.** One uniform icon cell: a fixed
   sprite box (target 48px art in a 64px cell at 1x world zoom,
   tuned in the sitting), label beneath in the existing type scale,
   badge anchors at fixed corners. Declared as constants in the
   scene model (`web/src/desk/gl/sceneModel.ts`), not per-kind
   improvisation. Every primitive kind renders in the SAME cell —
   uniformity is the OS feeling; the cell IS the spec atom.
2. **State images, not overlays-only.** Each icon ships as a state
   set: rest, selected (a real second image in the Workbench
   tradition — inverted/lit, not just a ring), and dimmed/stale.
   Transient marks (armed ring, needs-you) stay overlays. The
   texture pipeline (`textures.ts` / `sprites.ts`) loads the set;
   the engine picks by object state from the store — no component
   ever composes state ad hoc.
3. **Badges are data the hub already serves.** At rest: member/item
   counts on containers and KBs (`kbs[].member_ids.length` — the
   desk KB is a membership bag, DISTINCT from Project Facts, per the
   `KBRecord` docstring and the Phase-47 rule), a freshness tick
   (edited-recently), the egress mark where a profile leaves the
   device, the open-circuit mark from endpoint health, needs-you
   from Attention. Counts and marks ONLY — a badge that needs a
   sentence is a card's job (Article VII). Each badge names its
   source route in the contract so the Swift recreation inherits the
   mapping, not the guesswork. **Start from the audited source map
   in [research-badge-source-map.md](./research-badge-source-map.md)**
   (static audit, 2026-07-25, spot-verified): it marks each
   kind × badge SOURCE (exact route + field, file:line) or ABSENT —
   an ABSENT badge is dropped or gets a real new hub field, never
   fabricated client-side. Notable ABSENTs it proves: per-profile
   open-circuit (only the global `endpoint-health` doctor section
   exists — a structured per-target row is the new-field candidate),
   per-object sync state, and any "fact count" on a desk KB.
4. **Palette discipline over charm.** The icon palette derives from
   the Phase-96 token set (a locked ramp per material family, one
   light source, no per-icon color freedom). Regenerate the existing
   set through the Pixellab pipeline under these constraints; the
   deliverable includes the WRITTEN icon discipline (cell, ramp,
   light, state-set requirements) checked in beside the tokens so
   the next icon cannot regress the system.
5. **A density gate.** The proof isn't five objects — it's forty.
   Seed a dense desk (extend a UAT seed manifest) and verify the
   grid holds: labels don't collide, badges stay legible, selection
   reads at a glance, both viewports.
6. **Kill the dead air.** With the footprint fixed, default-arrange
   new/seeded objects on the world's grid (the arrangement stays
   sacred — this touches only defaults and snapshot, never a
   user-placed position).

## Out of scope

- New primitive kinds; drop-onto behavior (HS-105-02); zone window
  views (HS-105-03); any chrome change.

## Acceptance

- Every existing primitive kind renders in the uniform cell with a
  real selected-state image and correct at-rest badges fed by live
  routes (proven against a staged hub with the states induced, not
  mocked: a KB with members, an open circuit surfaced through a
  structured field, a needs-you item).
- The forty-object density walk passes headed at 1440 + 393.
- The icon discipline document exists and the tokens gate covers the
  icon ramp.
- No regression in the click grammar or arrangement persistence
  (the HS-101/103-01 walks re-run green).

## Test plan

- **Unit:** state-image selection from store state; badge
  source-mapping table; cell-layout math.
- **Integration:** the scene model rendering the seeded dense world;
  badge routes wired.
- **Live (evidence):** the headed walks above; every screenshot
  read before any flip.

## Chef's notes

- Do the footprint before ANY art. Regenerating pretty sprites into
  an undisciplined cell reproduces the mascot problem at higher
  resolution.
- The selected-state image is the single highest feel-per-line item
  in this phase: it is the difference between "the OS acknowledged
  me" and "a ring appeared near a drawing."
- When a badge is tempting but has no live route behind it, drop
  the badge, not the honesty. A decorative badge is the lamp again,
  smaller.
