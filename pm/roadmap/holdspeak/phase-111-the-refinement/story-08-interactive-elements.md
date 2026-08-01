# HS-111-08 - Interactive elements

- **Project:** holdspeak
- **Phase:** 111
- **Status:** backlog
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
