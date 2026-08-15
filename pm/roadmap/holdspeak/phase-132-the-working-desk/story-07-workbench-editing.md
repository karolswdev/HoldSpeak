# HS-132-07 — Workbench edits hold

- **Project:** holdspeak
- **Phase:** 132
- **Status:** backlog
- **Depends on:** HS-132-06
- **Unblocks:** none
- **Owner:** unassigned

## Problem

Four verified honesty defects in Workbench and Get Info editing:

1. **Keystroke loss (critical).** The item body textarea binds server state
   directly with a per-keystroke PUT + full refetch
   (`WorkbenchWindow.tsx:613-620`, `updateItem` :536-540); a vitest probe
   proved typed characters revert and interleaved keystrokes drop
   (`"a","b"` instead of `"a","ab"`). Every other editor uses
   `useDebouncedSave` or a local draft.
2. **Rename that does nothing.** Get Info always offers Rename
   (`InfoWindow.tsx:33-46`), but `dataSlice.ts:217-227` defines update URLs
   only for note/decision/kb/recipe/directory/workflow/project — meeting,
   artifact, chain, workbench (and more) fall through `if (!url) return;`
   silently. No backend meeting-rename route exists.
3. **Dishonest drop target.** The Workbench overlay promises "DROP TARGET ·
   ADD ITEM" for any drag (`WorkbenchWindow.tsx:1381-1390`) but accepts only
   `application/x-desk-item` (:1275-1276); files bubble to GlassDropLayer
   and mint a Meeting instead.
4. **Bare disabled RUN.** `disabled={running || !detail?.recipe_id}` with a
   static "Run this workbench now" title (`WorkbenchWindow.tsx:1360-1371`);
   the desk's own kit mandates `disabledReason` (`Surface.tsx:998-1004`).

## Scope

### In

- Item body edits through a local draft with debounced save
  (`useDebouncedSave`); no per-keystroke PUT/refetch.
- Get Info Rename honest per kind: extend the update path where the primitive
  should be renameable (including the missing backend route for meetings) or
  hide the affordance where no path exists — chosen per kind, recorded in the
  story evidence.
- Workbench dragover inspects `dataTransfer.types` and names the honest verb
  (ADD ITEM / IMPORT AS MEETING / a named refusal).
- RUN carries a `disabledReason` naming the missing agent; the runs wing's
  empty state offers the next step.

### Out

- Workbench manipulation verbs (backlog candidate AA); skill-binding
  ownership (deferred web-ownership slice).

## Acceptance criteria

- [ ] Typing at speed in an expanded item body loses zero characters; saves
  are debounced (one PUT per pause, not per keystroke).
- [ ] Rename works or is absent for every primitive kind; no silent no-op
  path remains.
- [ ] Dragging a file over a Workbench never promises ADD ITEM; each payload
  type shows its honest outcome before release.
- [ ] No bare disabled control remains in WorkbenchWindow; each names why.

## Test plan

- vitest: draft-buffer behavior (the probe from the audit, kept this time);
  rename per-kind matrix; dragover verb naming; disabledReason presence.
- Scoped backend test for the new rename route(s).
