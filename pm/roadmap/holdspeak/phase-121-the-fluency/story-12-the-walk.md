# HS-121-12 — The walk

- **Project:** holdspeak
- **Phase:** 121
- **Status:** backlog
- **Depends on:** HS-121-01 through HS-121-11
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Every capability touched by stories 01-11 must be exercised in a
keyboard-first walk. The walk proves that a power user can drive the
desk without touching the mouse — creating, navigating, acting, and
recovering entirely from the keyboard.

When this ships, the walk covers:

1. **Kit primitives.** SurfaceFooter renders consistently everywhere.
   Empty states have action buttons. Copy receipt shows "Copied".
   Undo receipt shows countdown and UNDO works.

2. **Keyboard-only workflow.** Palette fuzzy-searches → Enter → opens.
   Arrows walk ledgers. Snap two windows. Reverse cycle. Close.

3. **Object lifecycle.** Create → rename → duplicate → file → delete
   (with undo receipt) → UNDO → verify restored.

4. **Copy and export.** Copy an Ask answer → "Copied" in footer.
   Export journal → file downloads.

5. **Recovery.** Error state → retry → success. WebSocket reconnect
   indicator visible.

6. **ARIA.** Palette announces combobox. Autocomplete announces
   combobox. Press rows keyboard-operable.

## Acceptance criteria

- [ ] Entire workflow completes without mouse.
- [ ] No silent failures.
- [ ] ARIA patterns verified with screen reader or axe audit.
- [ ] Every SurfaceFooter renders the three-slot layout.

## Test plan

- Full keyboard-only walk at 1440px against the real hub.
- Screen reader spot-check on palette and autocomplete.
- Playwright screenshots of key states.

## Files in scope

- Evidence file: screenshots in `assets/`.
