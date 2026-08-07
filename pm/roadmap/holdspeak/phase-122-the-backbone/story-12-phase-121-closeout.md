# HS-122-12 — Phase 121 closeout

- **Project:** holdspeak
- **Phase:** 122
- **Status:** done
- **Depends on:** HS-122-09 (walk harness)
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Phase 121's story 12 (the keyboard-first walk) was deferred because
the walk harness didn't exist yet. Now it does. This story completes
the Phase 121 proof: a power user can drive the desk without touching
the mouse.

When this ships:

1. **Keyboard-only workflow.** Palette → fuzzy search → Enter →
   object opens. Arrows walk ledgers. Snap two windows. Reverse
   cycle. Close.

2. **Object lifecycle.** Create → rename (F2) → duplicate → file into
   zone → delete (with undo receipt) → UNDO → verify restored.

3. **Copy and export.** Copy an Ask answer → "Copied" in footer.
   Export journal → file downloads.

4. **ARIA verification.** Palette combobox, inlet autocomplete,
   press rows all keyboard-operable and screen-reader-announced.

5. **Screenshots at 1440px** capturing each workflow step.

## Acceptance criteria

- [ ] Entire workflow completes without mouse.
- [ ] No silent failures.
- [ ] ARIA patterns verified with axe or screen reader.
- [ ] Screenshots in evidence assets.

## Files in scope

- Evidence: `assets/` next to the evidence file.
- Walk harness scripts from story 09.
