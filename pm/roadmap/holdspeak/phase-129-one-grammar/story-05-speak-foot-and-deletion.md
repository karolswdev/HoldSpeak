# HS-129-05 — One foot in Speak; the great deletion

- **Project:** holdspeak
- **Phase:** 129
- **Status:** done
- **Depends on:** HS-129-01
- **Unblocks:** HS-129-11
- **Owner:** unassigned

## The thesis (the bar)

One window, one foot. The Speak room stacks two competing feet inside its
scroller — the sticky `ReadinessLine` (`.speak-status`, speak.css:220-245,
the product's last live sticky impostor and the owner's screenshot) plus a
separate `SurfaceFooter` (Export). And the CSS still carries four dead
footer grammars that mislead every future room. Deletion before invention.

### What changes

1. Dictation (DictationCore.tsx:121-134): ONE `SurfaceFooter` through the
   HS-129-01 foot slot — readiness state (pipeline lamp/warnings + Review)
   in the egress/receipt slots, Export in the verbs slot; the last landing
   receipt stays visible. `.speak-status`'s sticky/negative-margin rules
   die; its lamp/tone content re-expressed with the shared grammar
   (audit D §1 migration guidance).
2. The great deletion (audit D §8, grep-before-delete in every case):
   `.surface-status` + its `:has()` clearance (surface.css:833-861),
   `.prefs-status` (surface.css:2239-2251), `.surface-receiptbar` root
   (surface.css:2303-2318), `.desk-pullout-foot` (pullout.css:256-285),
   `DeskWindowFooter.tsx` (uncalled), `.process-row-state`, `.glyph-chip`.
3. The live `.surface-receiptbar-*` CHILD styles (five cores +
   DeliveryBoard) move under `SurfaceFooter` slot classes
   (`.surface-footer-receipt` / `-verbs` variants); consumers updated;
   then the legacy child selectors die too.
4. `copy-receipt` / `undo-receipt` are LIVE (created programmatically —
   useCopyReceipt.ts:28-42, useUndoReceipt.ts:72-114) and must survive.

## Acceptance criteria

1. Speak shows exactly one foot, pinned, in all sizes/modes; readiness
   warnings and the Review verb remain one click away; Export remains.
2. `grep -r "surface-status\|prefs-status\|desk-pullout-foot\|DeskWindowFooter"`
   over web/src returns only this story's evidence or nothing.
3. The five receiptbar-child cores render identically (visual diff in the
   walk) through the new slot classes.
4. Undo/copy receipts still seat and animate in the foot.

## Test plan

- Web: Dictation footer composition test; a selector-liveness test guarding
  the deletions; full desk suite green; typecheck.
- Walk: Speak at default/small/maximized/sheet — one foot, pinned, body
  scrolls under it; before/after shots of the five receiptbar cores.
