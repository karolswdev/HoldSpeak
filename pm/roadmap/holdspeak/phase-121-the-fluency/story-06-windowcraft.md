# HS-121-06 — Windowcraft

- **Project:** holdspeak
- **Phase:** 121
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-121-12 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

Window management: no reverse cycle, no snap, no Window menu. Expose
and cycling are undiscoverable. Unchanged from the original story.

Covers: F8 (partial window keyboard), N-D5 (window verbs no menu),
N-D10 (expose undiscoverable).

## Acceptance criteria

- [ ] Ctrl+Shift+` reverse cycles.
- [ ] Snap-left, snap-right, maximize verbs in registry.
- [ ] "Window" menu in menu bar with all window verbs.
- [ ] All window verbs in palette.

## Files in scope

- `web/src/desk/verbRegistry.ts`
- `web/src/desk/components/DeskMenuBar.tsx`
- `web/src/desk/components/DeskWindow.tsx`
- `web/src/desk/keymap.ts`
