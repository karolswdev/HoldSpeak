# HS-156-05 - Plain words: the jargon purge and the UX-evidence checklist

- **Project:** holdspeak
- **Phase:** 156
- **Status:** backlog
- **Depends on:** HS-156-04
- **Unblocks:** HS-156-07
- **Owner:** unassigned

## Problem

"catalog · available", schema-speak statuses, and unexplained
"Needs attention" are why the co-creator got lost. Every string on the
door path must say what a manager needs next (settled design D4;
POSITIONING voice rules).

## Scope

- **In:** the wording pass over the Models surface's door path and
  list rows: statuses describe state + next step in human words ("not
  downloaded", "downloading · 34%", "ready", "server unreachable —
  check it"); group labels audited against POSITIONING; the concierge
  UX-evidence log (`assets/concierge-ux-evidence.md`, copied into this
  phase) turned into a numbered checklist — every item marked FIXED
  (with the story/test) or RECORDED (with the reason). A product-copy
  fence extension covering the new strings.
- **Out:** renaming backend schema fields; touching non-Models rooms.

## Acceptance criteria

- [ ] The UX-evidence checklist ships in this story's evidence with zero unaddressed items (each FIXED or RECORDED).
- [ ] The copy fence (test_product_copy or a sibling) covers the door strings; no banned jargon on the door path (a greppable deny-list test: "catalog", "no_assignment", raw capability ids in door-path UI strings).
- [ ] vitest snapshot of the row/status wording states.

## Test plan

- **Unit:** the deny-list fence + vitest wording states.
- **Integration:** covered by 03's glass (shots show the final words).
- **Manual / device:** story 05.

## Notes / open questions

- Council checklist item: retire the `desk-tokens.css` import shim after an import census (one token source).

- No prose novels: plain ≠ wordy; one line beats a paragraph everywhere.
