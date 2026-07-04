# Evidence — HSM-17-08: the first-class Recipe experience (in-world, no modals)

**Date:** 2026-07-04. The owner's mandate, delivered with the rename it rode in
on: *"an absolutely super high fidelity modern UX experience. It's got to be
first class."*

## What shipped

- **`DioAtelierPanel`** — the Recipe surfaces' presentation: the desk STAYS
  VISIBLE and alive behind a right-docked panel over a transparent tap-away
  catcher. Never a dimming scrim (the no-modals law, which the old
  `Color.black.opacity(0.62)` shells violated on all four surfaces). Depth
  comes from shadow and a gradient hairline, not darkness; entry is an
  edge-slide with the desk's springs.
- **Converted**: the Recipe builder, the Recipe chat, the chain run sheet, and
  the chain builder. The chat keeps its cannot-dismiss-while-thinking guard.
- **The chain builder elevated**: a LIVE pipeline strip under the header — the
  chain assembles under your fingers as avatars flowing left-to-right with
  arrows, updating on every add/reorder — bringing it up to the recipe
  builder's felt richness. Voice mics were already on every input.
- **Deliberately kept**: `DioChainRelay` (the gamified run visualization)
  remains a full-bleed moment — it is a transient payoff, not an editing
  surface, and the no-modals law is about create/edit.

## Proofs (screenshots/)

- **`hsm-17-08-builder-inworld.png`** — the Recipe builder docked right, the
  desk fully visible behind it: the glaring waiting coder alive on the left,
  no scrim. Presets, the mic'd describe field, the step header.
- **`hsm-17-08-chainbuilder-inworld.png`** — the chain builder with the live
  pipeline strip (Scout → Critic, pixel avatars), numbered reorderable steps,
  the add-a-recipe chips, the desk breathing behind it.

## Remaining elevation (filed, not silently dropped)

The web desk can run recipes but not author them (no builder, no chains
surface) — the flattest surface in the inventory, filed as the next elevation
slice alongside the rich event stream.

## Builds

Simulator app build **SUCCEEDED**; the conversion is presentation-only (no
model, wire, or route changes), so the suites are unaffected by construction —
the Swift package suite stayed green at 465/9/0.
