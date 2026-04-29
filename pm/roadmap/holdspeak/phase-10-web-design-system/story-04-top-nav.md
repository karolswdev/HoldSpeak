# HS-10-04 - Unified TopNav and route identity

- **Project:** holdspeak
- **Phase:** 10
- **Status:** done
- **Depends on:** HS-10-03
- **Unblocks:** HS-10-06, HS-10-07, HS-10-08, HS-10-09
- **Owner:** unassigned

## Problem

The five existing pages each implement navigation differently — some
have a top bar, some have inline tabs, some have nothing. Users moving
between `/`, `/activity`, `/history`, and `/dictation` cannot build a
mental model of "where am I" because the spatial frame keeps changing.

## Scope

- **In:**
  - `web/src/components/TopNav.astro` — left-aligned app mark + product
    name, center route links, right-aligned local/private indicator
    slot and overflow.
  - Route identity: each page passes a `current` prop; the matching
    nav link reads as selected (visible + announced).
  - A shared layout file (`web/src/layouts/AppLayout.astro`) that
    composes `TopNav` + `<slot/>` + an optional secondary toolbar slot
    for per-page actions.
  - Narrow-viewport behavior: nav collapses to a compact menu without
    horizontal overflow.
  - Skip-to-content link, keyboard reachable, visible on focus.
- **Out:**
  - Sub-navigation inside any individual route (those belong to the
    rebuild stories).
  - A separate "settings" route — current `/history`-served settings
    surface stays where it is until HS-10-08.
  - User account UI (there is no account; this is a local tool).

## Acceptance Criteria

- [x] `TopNav` renders identically (no positional shift) across the
  design-check route and the components gallery.
- [x] Selected-route styling is correct for every legitimate `current`
  value.
- [x] Skip-to-content works with keyboard only.
- [x] Narrow-viewport nav has no horizontal scroll at 360px wide.
- [x] Screen reader announces the selected nav item as current.

## Test Plan

- Manual viewport sweep at 360, 768, 1024, 1440px.
- Keyboard-only navigation of the nav.
- VoiceOver pass on macOS confirming `aria-current="page"` is
  announced.

## Notes

Resist building a "settings dropdown" or "user menu" here — neither
exists in HoldSpeak's product model. The nav stays utilitarian.
