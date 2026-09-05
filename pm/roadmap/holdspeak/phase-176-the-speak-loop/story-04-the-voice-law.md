# HS-176-04 — The voice law

- **Project:** holdspeak
- **Phase:** 176
- **Status:** backlog
- **Depends on:** HS-176-01
- **Unblocks:** HS-176-05
- **Owner:** unassigned

## Problem

Article IV.1: "Every text input can be spoken into. The mic is an
affordance of the OS, not of any one feature." UX-CANON.md rule B
lists MicButton as a species that lives on every text input. Today
MicButton is on 7 surfaces (gadgets.tsx:299,357; Surface.tsx:1174;
ChairHome.tsx:540; ThreadPullout.tsx:751; NoteEditor.tsx:166;
RecipeEditor.tsx:113; DecisionsView.tsx:167) but ~92 text inputs exist
across web/src/desk/. The voice law is not satisfied: ~85 inputs lack
MicButton.

## Scope

- In:
  - A census of every text input (StringGadget, EditInPlace,
    `<input>`, `<textarea>`) across web/src/desk/ with its current
    MicButton status.
  - MicButton added to every uncovered text input, following the
    placement rule from the HS-176-01 artboard.
  - StringGadget gains MicButton by default (the gadget renders it
    unless explicitly opted out with a prop); this covers the majority
    of uncovered inputs.
  - EditInPlace gains MicButton when in edit mode.
  - A guard test: the UX-CANON scanner (scripts/ux_canon_scan.py)
    gains a rule counting text inputs without MicButton; the ceiling
    is set to 0; the ratchet prevents regression.
- Out:
  - MicButton on non-text controls (buttons, toggles, pickers).
  - Voice commands or wake-word integration (separate capabilities).
  - MicButton on inputs outside web/src/desk/ (e.g. Astro shell
    pages, if any remain).

## Acceptance criteria

- [ ] Every text input across web/src/desk/ renders MicButton
      (Article IV.1).
- [ ] The census is documented with before/after counts; the gap is 0
      after this story.
- [ ] StringGadget renders MicButton by default (Article IV.1).
- [ ] EditInPlace renders MicButton in edit mode.
- [ ] The UX-CANON scanner has a rule for uncovered text inputs; the
      ceiling is 0; the ratchet test passes.
- [ ] The face matches the HS-176-01 artboard's placement rule per
      species.

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k voice_law`
  - StringGadget renders MicButton by default.
  - EditInPlace renders MicButton in edit mode.
- Integration: the UX-CANON scanner counts uncovered text inputs; the
  count is 0.
- Manual: walk five surfaces at 1440 + 393; every visible text input
  has MicButton.

## Notes / open questions

- Some text inputs may be genuinely non-dictatable (e.g. a password
  field, a hex color picker). If any exist, they are listed in the
  guard's allowlist with reasons, as the A1 (raw button) allowlist
  does today (UX-CANON.md §E Guards).
- The MicButton placement for StringGadget inside a dense LedgerRow:
  the artboard decides whether the mic is inside the gadget (compact)
  or beside it (standard). Propose inside (consistent with the
  existing gadgets.tsx:299 placement).
