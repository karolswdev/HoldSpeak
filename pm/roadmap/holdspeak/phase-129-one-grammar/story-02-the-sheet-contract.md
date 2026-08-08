# HS-129-02 — The sheet contract at ≤720px

- **Project:** holdspeak
- **Phase:** 129
- **Status:** in-progress
- **Depends on:** HS-129-01
- **Unblocks:** HS-129-11
- **Owner:** unassigned

## The thesis (the bar)

The compact sheet is a window form, not an escape from the window contract.
Today `dock.css:173-187` puts `overflow: auto` on the entire `.is-sheet`
window shell, so every sheet scrolls its head and foot away with the content
(audit A §4: "fails the contract globally") — even windows whose desktop
composition is correct.

### What changes

1. The `.is-sheet` rule stops scrolling the shell: the sheet keeps the flex
   column, `.desk-surface-body`/`.desk-pullout-body` remains the one scroll
   owner, and the foot stays pinned above the sheet's bottom edge.
2. Sheet-specific geometry (top offset, rounded top corners, backdrop)
   survives untouched — this story changes scroll ownership only.
3. Every sheet form re-verified: Speak, Settings (root + a category face),
   Meetings, Intelligence (three views), and one pullout kind.

## Acceptance criteria

1. At 393×852, head and foot of each verified sheet remain visible while the
   body scrolls; no sheet scrolls its own title bar off-screen.
2. Audit B's four mobile baseline shots re-taken: no regression in reachable
   content (a sheet that previously exposed content only by shell-scrolling
   must still expose all content, now via body scroll).
3. No desktop (>720px) behavior change.

## Test plan

- Web: a sheet-mode contract test (shell not scrollable, body scrollable).
- Walk: Playwright at 393×852 — the four audit-B mobile surfaces plus one
  pullout, each scrolled top/middle/bottom, footer bounding-box asserted.
