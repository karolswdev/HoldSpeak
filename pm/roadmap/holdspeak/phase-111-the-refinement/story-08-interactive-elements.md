# HS-111-08 - Interactive elements

- **Project:** holdspeak
- **Phase:** 111
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-111-10
- **Owner:** unassigned

## The thesis (the bar)

Every control type across all programs — toggles, selects, inputs,
tabs, pills, buttons, badges — must come from one kit and speak one
language. Stories 01–07 rethink rooms; this story guarantees the
furniture matches across them. The bar: **one gadget kit, defined
once in the shared styles/components, used everywhere: beveled
buttons, sunken inputs, rectangular check/toggle gadgets, etched
tabs and badges. No stray rounded control survives.**

## Owner-commissioned doctrine riders (2026-08-01)

- **Roving focus is kit law** (doctrine P0 F3, principle 3): every
  SurfaceLedger/GadgetTable/menu/grid is ONE Tab stop with arrow
  keys walking rows inside (a 100-row archive must never be 100 Tab
  presses); Home/End jump; focus visibly rides the full-width band.
  One kit fix inherits into Meetings, Journal, Agents, needs-you.
- **Destructive verbs arm** (doctrine P0 F4, principle 6): the
  GadgetTable row `×` currently deletes with NO confirm
  (gadgets.tsx:387-395) — every destructive kit verb gets the arming
  two-step (× → FORGET?/DELETE?) as the kit default, matching
  SecretRow; full undo is a separate chartered story (doctrine §3),
  not this one.

## Method (phase canon)

1. **Audit.** An agent inventories every control instance across all
   programs and diffs it against the kit; files every one-off.
2. **Rethink.** Define the canonical kit (states: rest, hover,
   active, focus, disabled) in the token/component layer.
3. **Implement** in `web/src` — replace one-offs with kit controls.
4. **Prove** with live screenshots showing the same control rendering
   identically in different programs.

## Test plan

- A grep/audit pass finds no rounded-pill toggles or off-kit
  border-radius on controls.
- Focus, hover, active, and disabled states are defined for every
  control in the kit and render per the bevel grammar.
- The same select/toggle/tab looks identical in Settings, Speak, and
  Meetings.
- Screenshot proof at both viewports.
