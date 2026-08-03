# HS-113-14 - Object lifecycle

- **Project:** holdspeak
- **Phase:** 113
- **Status:** backlog
- **Depends on:** HS-113-01
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Objects on the Desk must have a complete lifecycle: create, edit,
move, file, and DELETE. Today there is no way to delete an object
— things created by accident persist forever. There is no global
undo — filing and editing are irreversible. An OS without delete
and undo is not an OS.

**Articles served:** V (consent is the spine — deletion is an
armed act), VII (the interface serves — destructive verbs are
visible and confirmation-gated), VIII (native-grade craft —
Delete key works).

## Ground (from the behavioral audit)

- `web/src/desk/verbRegistry.ts` — there is no `object.delete`
  verb. No delete in the verb registry at all.
- `web/src/desk/floorMenu.ts` — the object context menu has
  Open, Get Info, Ask, Edit. No Delete option.
- `web/src/desk/store.ts` — no `deletePrimitive` function.
  `resetDesk` exists but it nukes everything.
- Backend routes — `DELETE /api/notes/{id}`,
  `DELETE /api/decisions/{id}`, `DELETE /api/recipes/{id}`, etc.
  exist as soft-delete endpoints. The backend is ready.
- No global undo mechanism exists anywhere in the codebase.

## Method

1. **Delete verb** — register `object.delete` in the verb
   registry:
   - Label: "Delete"
   - Group: "danger"
   - Key: Backspace (when a desk object is selected, NOT when
     typing in an input — the key handler must check
     `document.activeElement`)
   - Ghost: "Select an object first" when nothing is selected
   - Action: calls `deletePrimitive(id, kind)`

2. **`deletePrimitive` in the store** — add to `store.ts`:
   - Confirmation gate: `window.confirm("Delete {title}?")` or
     a Desk-native confirm pattern if one exists
   - Calls `DELETE /api/{kind-endpoint}/{id}` (map kind to
     endpoint: note→notes, decision→decisions, recipe→recipes,
     kb→kbs, workflow→workflows, directory→directories)
   - Closes any open pullout/editor for that object
   - Refreshes the desk

3. **Context menu** — add "Delete" to the object menu in
   `floorMenu.ts`, at the bottom, separated from other items.

4. **Undo for the last delete** — a simple one-level undo:
   - After delete, show a transient receipt in the dock area:
     "Deleted {title} · UNDO" (auto-dismisses after 8s)
   - Clicking UNDO calls the create endpoint with the deleted
     object's data (which was captured before deletion)
   - This is not a full undo system — it's a one-level "oops"
     for the most destructive action

5. **Delete key guard** — the Backspace/Delete key binding must
   NOT fire when the user is typing in an input, textarea, or
   CodeMirror editor. Check `document.activeElement.tagName`
   and the presence of `.cm-editor` in the focus chain.

## Test plan

- Unit: `object.delete` verb appears in the object context menu.
- Unit: clicking Delete shows confirmation dialog.
- Unit: confirming deletion calls the DELETE API endpoint.
- Unit: the desk refreshes after deletion — the object is gone.
- Unit: open pullout for a deleted object is closed.
- Unit: Backspace on a selected desk object triggers delete.
- Unit: Backspace while typing in an input does NOT trigger
  delete.
- Unit: undo receipt appears after deletion, clicking UNDO
  restores the object.
- Screenshot walk: object context menu with Delete at the
  bottom, undo receipt in the dock area.
