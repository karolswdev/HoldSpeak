# HSM-17-08 — The first-class Recipe experience (in-world, no modals)

- **Project:** holdspeak-mobile
- **Phase:** 17
- **Status:** done (2026-07-04 — born as the owner's rider mandate on the Recipe rename and shipped the
  same evening; see `evidence-story-08.md`)
- **Depends on:** HSM-17-01 (the Recipe rename), the desk's in-world presentation canon (the migrating
  pull-out; the no-modals law).
- **Unblocks:** the web authoring slice (filed).
- **Owner:** ratified verbatim: *"And an absolutely super high fidelity modern UX experience. It's got to
  be first class."*

## Problem

The Recipe surfaces were rich in content but wrong in presentation: the builder, chat, chain sheet and
chain builder all presented as dimmed-scrim centered cards — exactly the modal pattern the desk's law
forbids for create/edit. The chain builder also lagged the recipe builder's felt richness.

## The design

One presentation primitive, `DioAtelierPanel`: the desk stays visible and alive behind a right-docked
panel over a transparent tap-away catcher. Depth from shadow and a gradient hairline, never darkness;
edge-slide entry. All four surfaces ride it. The chain builder gains a live pipeline strip (avatars
flowing with arrows as steps are added and reordered). The chain relay stays full-bleed by design: a
transient run payoff, not an editing surface.

## Acceptance criteria

- [x] No Recipe create/edit surface dims the desk; every one is a docked in-world panel with the desk
      visible and alive behind it. (All four converted; screenshots show the glaring coder behind both
      builders.)
- [x] The chain builder reads as rich as the recipe builder. (The live pipeline strip; avatar steps;
      mics were already on every input.)
- [x] The chat keeps its integrity guards (cannot dismiss while thinking).
- [x] Simulator-proven with screenshots; presentation-only (no wire/model changes).
- [ ] Walked on the cabled iPad in HSM-17-06 with the rest of the phase's device beats.

## Test plan

- Simulator: the builder and chain-builder shots with desk content behind them (taken).
- Device: the panel feel (springs, tap-away, the pipeline strip) rides the 17-06 walk.
