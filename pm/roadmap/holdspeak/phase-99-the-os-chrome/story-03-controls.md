# HS-99-03 — Controls wear the skin

- **Project:** holdspeak
- **Phase:** 99
- **Status:** done
- **Depends on:** HS-99-01
- **Unblocks:** HS-99-08

## Problem

"There's still loads of unstyled selects." Every `<select>` popup,
chevron, and option list is the browser's; date, search, file, and
number inputs are raw; the checkbox row is bare. Controls are where
the hand touches the OS — they must wear the skin.

## Scope

- In:
  - the Signal Select: `appearance: none`, drawn chevron (inline SVG
    background, token color), well-tone fill, styled `<option>`s
    (color/background inherit — the popup is as skinned as browsers
    allow);
  - date/search/number inputs: one control treatment (well tone,
    height, radius, focus) including `::-webkit-calendar-picker-indicator`
    and search-cancel styling;
  - the file input (`hs-control`): a skinned drop-zone-style row
    (button face + filename), native input visually replaced;
  - the `hs-check` checkbox row: accent-colored `accent-color` plus
    row treatment;
  - all of it in Signal/global CSS once — cores inherit; the gallery
    (ComponentsCore) shows every control;
  - the config walk leg re-proven (settings round-trip through the
    skinned controls).
- Out:
  - replacing selects with a custom popup component (recorded rider —
    browsers cap option styling; the full custom dropdown is a
    follow-up if the skinned native still offends).

## Acceptance criteria

- [ ] Zero `appearance`-default selects in any window; chevron drawn;
      options surface-colored where the browser allows.
- [ ] Date/search/file/number/checkbox all wear the treatment; the
      gallery shows them; shots at 1440/393 looked at.
- [ ] Config + meetings-filters flows green (walk legs); `npm run
      check` + python suite green.

## Test plan

- vitest gallery/control tests; config walk leg; shots; `npm run
  check`.

## Evidence required

- Before/after shots (Settings selects, Meetings filters), walk
  output, suite output.
