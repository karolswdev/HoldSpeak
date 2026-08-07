# HS-121-04 — Safe hands

- **Project:** holdspeak
- **Phase:** 121
- **Status:** backlog
- **Depends on:** HS-121-01 (useUndoReceipt), HS-121-02 (SurfaceFooter receipt slot)
- **Unblocks:** HS-121-07 (universal object verbs — delete needs undo)
- **Owner:** unassigned

## The thesis (the bar)

Zero undo infrastructure. Workbench item Remove fires immediately.
Bulk clear-done has no confirmation. `useUndoReceipt` (story 01) and
`SurfaceFooter` receipt slot (story 02) make this a wiring job.

When this ships:

1. Workbench item Remove uses `useUndoReceipt` — item hides
   immediately, DELETE deferred for 8 seconds, receipt with UNDO
   shows in the SurfaceFooter.
2. Workbench clear-done uses ConfirmVerb.
3. GadgetTable row delete (already ConfirmVerb) wired to
   `useUndoReceipt` for undo capability.

## Acceptance criteria

- [ ] Workbench item Remove shows undo receipt. UNDO restores.
- [ ] Clear-done requires ConfirmVerb.
- [ ] Receipt renders in SurfaceFooter receipt slot.

## Files in scope

- `web/src/desk/components/WorkbenchWindow.tsx`
- `web/src/desk/surface/gadgets.tsx` (GadgetTable)
