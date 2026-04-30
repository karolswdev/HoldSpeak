# HS-12-01 - Workbench token map + pixel UI font

- **Project:** holdspeak
- **Phase:** 12
- **Status:** done
- **Depends on:** HS-10-02 (design tokens), HS-10-13 (phase 10 done)
- **Unblocks:** HS-12-02 (component voice pass)
- **Owner:** unassigned

## Problem

Phase 10's `tokens.css` landed a competent dark theme that doesn't
read as *workbench*. The palette, radius scale, and UI font choice
together produce a generic SaaS feel; the user's anchor reference
(Amiga Workbench 1.3) needs the actual Workbench palette + a pixel
UI font to come through at all.

## Scope

- **In:**
  - Replatform `web/src/styles/tokens.css` to the Workbench
    palette: blue canvas, white raised surface, black 1 px
    hairline, orange accent. Status tones (success/warn/danger)
    re-mapped to readable hues against the blue canvas.
  - Set every `--radius-*` token to `0` (or remove the rounded
    pill exception case-by-case in HS-12-02).
  - Self-host a pixel UI font (Topaz-style or VT323) under
    `web/src/styles/`; wire `--font-ui` to it. Keep body / code
    on JetBrains Mono.
  - Sanity-pass on `--duration-*` tokens — Workbench feels
    discrete, so very short transitions are right; verify the
    existing 120/220/360 ms scale fits.
  - Update the `prefers-reduced-motion` block as needed.
- **Out:**
  - Component-level changes (those land in HS-12-02).
  - Stripe title bar pattern (explicitly skipped per phase scope).
  - Light theme tokens (still deferred).

## Acceptance Criteria

- [x] `tokens.css` loads only Workbench-palette colour values; no
  legacy cyan accent left.
- [x] All `--radius-*` tokens are `0`, except a documented
  exception list (initially: none).
- [x] `--font-ui` resolves to the new self-hosted pixel font;
  fallback chain ends at `system-ui` for safety.
- [x] `/design/check` page renders cleanly under the new tokens —
  no "white-on-white" or "blue-on-blue" contrast failures.
- [x] No external font CDN added; everything stays local.

## Test Plan

- Visual diff `/design/check` and `/design/components` before /
  after.
- `prefers-reduced-motion: reduce` still flattens motion.
- Build: `npm run build` clean.

## Notes

The font choice matters. Options in priority order:

1. **Topaz** (the actual Workbench bitmap font, freely available
   as a TTF/WOFF rebuild) — most authentic, slightly fragile at
   non-1×.
2. **VT323** — terminal-style pixel font from Google Fonts (we
   self-host it, no CDN); more legible at modern body sizes.
3. **PrintChar21** — Apple II font; reads similarly but loses
   the Workbench specificity.

HS-12-01 picks one and lands the file in
`web/public/_fonts/` (or equivalent) with the `@font-face` rule
in `tokens.css`.
