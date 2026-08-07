# HS-121-07 — Universal object verbs

- **Project:** holdspeak
- **Phase:** 121
- **Status:** backlog
- **Depends on:** HS-121-04 (safe hands — delete needs undo)
- **Unblocks:** HS-121-12 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

No delete verb anywhere. Rename only for zones. No duplicate. No
move/file via command. Zone context verbs are a parallel species.
Unchanged from the original story.

Covers: N-D1 (delete), N-D2 (rename), N-D3 (duplicate), N-D4 (file),
N-D6 (zone verbs species).

## Acceptance criteria

- [ ] object.delete, object.rename, object.duplicate, object.file
      in the verb registry.
- [ ] All four in Object menu, context menu, and palette.
- [ ] Delete uses useUndoReceipt.
- [ ] Zone verbs derive from registry, not floorMenu.ts locals.

## Files in scope

- `web/src/desk/verbRegistry.ts`
- `web/src/desk/floorMenu.ts`
- `web/src/desk/store.ts`
- `web/src/desk/components/DeskMenuBar.tsx`
