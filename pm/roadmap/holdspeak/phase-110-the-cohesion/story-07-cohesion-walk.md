# HS-110-07 - The cohesion walk

- **Project:** holdspeak
- **Phase:** 110
- **Status:** backlog
- **Depends on:** HS-110-01 through HS-110-06
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Every preceding story changes a surface. The bar: **a live walk on
the real populated desk proving the whole system speaks one visual
language — outside the windows AND inside them.**

## The walk

On the real hub, both viewports (1440 and 393):

1. **Empty desk** — the crosshatch backdrop, the solid menu bar with
   mono type, the solid dock taskbar with pixel-art launcher sprites.
   No frosted glass anywhere. No animated glows.

2. **Populated desk** (≥10 objects) — icons grid-snapped (from the
   first attempt), the backdrop invisible under population, badges
   readable.

3. **A window open** — opaque solid body, beveled title bar, rectangular
   gadgets (always visible, not revealed on hover), mono title text,
   2px corners. The window sits ON the desk as a solid surface, not
   floating in glass above it.

4. **Window interior** — open Settings: grouped-inset containers with
   2px corners, visible scrollbar, mono section labels, no aerogel
   blur. Open a meeting: artifact receipts are solid bordered insets,
   not frosted cards.

5. **Focused vs. unfocused windows** — front window has
   `--border-strong` and `--surface-3` title bar with accent bottom
   edge; rest windows have `--border` and `--surface-2` title bar.
   No shadow difference.

6. **The dock** — pixel-art launchers in etched slots, running
   indicator as accent bottom border, front chip highlighted, RecordOrb
   with its glow.

7. **Menu bar hover** — Workbench-style inverted highlight (accent fill,
   dark text) on menu items.

8. **Drag an icon** — fluid drag, grid snap on release.

## The cohesion audit

| Element | Before | After | Verdict |
|---------|--------|-------|---------|
| Window fill | 58% translucent glass | solid `--surface-1` | — |
| Window corners | 18px | 2px | — |
| Window gadgets | traffic-light circles | rectangular beveled buttons | — |
| Window depth | Gaussian shadow | bevel + border color | — |
| Title bar font | Space Grotesk 15px | JetBrains Mono 12px | — |
| Dock material | frosted glass pill | solid beveled strip | — |
| Dock launchers | Unicode glyphs | pixel-art sprites | — |
| Menu bar | frosted glass | solid beveled strip | — |
| Menu hover | subtle wash | inverted highlight | — |
| Backdrop | gradient + glow | flat floor + crosshatch | — |
| Interior receipts | aerogel blur | solid bordered inset | — |
| Interior corners | 10-12px | 2px | — |
| Scrollbars | 6px overlay pills | 8px always-visible | — |
| Section labels | Inter 11px | JetBrains Mono 10px | — |

**Zero `backdrop-filter`** in the shipped tree. No frosted glass
anywhere on the desk.

## Docs

- **ICON-DISCIPLINE.md** — already updated with system chrome section;
  verify it matches the shipped sprites.
- **WEB_DESK.md** — update any references to "vibrancy" or "frosted
  glass" or "traffic lights."
- **ARCHITECTURE_BACKEND_RUNTIME.md** — if the desk chrome section
  names specific implementations, update.

## Test plan

- The cohesion audit table is filled with verdicts — every row passes.
- The screenshot walk is captured as evidence.
- `grep -r 'backdrop-filter' web/src/` returns zero hits in desk CSS.
- The full test suite passes.
