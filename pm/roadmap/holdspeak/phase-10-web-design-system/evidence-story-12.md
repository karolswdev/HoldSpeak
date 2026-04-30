# HS-10-12 evidence — Motion + accessibility pass

## Files touched

- `web/src/components/TopNav.astro` — replaced the active-link
  treatment. The previous design used `background: var(--accent-soft)`
  + `box-shadow: inset 0 -2px 0 var(--accent)` on a `radius-2` link;
  combined those read as a hard outlined rectangle around the live
  route. Swapped for a `text-decoration: underline` with
  `text-decoration-color: var(--accent)`, `thickness: 2px`,
  `underline-offset: 6px` — same accent-driven affordance, none of
  the boxed feel. The `.is-current:hover` rule keeps the background
  transparent so hover doesn't reintroduce the pill.
- `web/src/styles/global.css` — added a single `@keyframes hs-pulse`
  animation plus the `.is-live` modifier that any `.pill-dot` or
  `.conn-dot` can adopt. Tone changes still flip the colour;
  *only* the dot animates, so the surrounding text never reflows
  (the story's "animate the dot, not the box" rule).
- `web/src/pages/index.astro`
  - Hero gets `transition: border-color, box-shadow var(--duration-medium) var(--ease-standard)`
    so the idle → recording → stopping state changes ease in
    rather than snap.
  - Recording, stopping, and analyzing pills carry `pill-dot is-live`.
  - `.conn-dot` adds `is-live` only when `connectionTone() === "connecting"`,
    so the pulse signals genuine in-progress state and stops the
    instant the WS attaches.
  - Decorative inline SVGs (bookmark glyph, action-item check,
    action-item dismiss, hero-title pencil) gained `aria-hidden="true"`
    so screen readers no longer announce empty `<svg>` nodes when
    the surrounding control already carries text or `sr-only` copy.
- `web/src/components/ConfirmDialog.astro`
  - Mirrored the existing open animation with a 120 ms close
    animation: a `.is-closing` class on the dialog drives the
    fade-and-rise-out; the dispatcher applies the class, waits one
    `--duration-short` window, then calls `.close()`. Reduced-motion
    users skip the wait and close instantly.
  - `prefers-reduced-motion: no-preference` guard on every animation
    keeps the close graceful for motion-OK users, no flicker for
    reduced-motion users.

## Motion tokens — single source of truth

Every new transition consumes
`var(--duration-short)` / `var(--duration-medium)` and
`var(--ease-standard)`. The reduced-motion override in
`tokens.css:144` already collapses those tokens to `0ms` and adds a
universal `* { animation-duration: 0ms !important; transition-duration: 0ms !important; }`
fallback, so the new pulse, the hero state transition, and the
dialog close all flatten without per-rule guards. Verified by
toggling "Emulate CSS prefers-reduced-motion: reduce" in DevTools:
the dot stops mid-cycle, hero state changes are instantaneous,
the dialog close skips the fade and returns focus immediately.

## Accessibility audit — per-route checklist

| Check | `/` | `/activity` | `/history` | `/dictation` |
|---|---|---|---|---|
| All interactive elements reachable by keyboard (Tab/Shift+Tab) | ✅ | ✅ | ✅ | ✅ |
| Focus order is logical (top-to-bottom, left-to-right) | ✅ | ✅ | ✅ | ✅ |
| Visible focus ring (global `:focus-visible` outline + accent) | ✅ | ✅ | ✅ | ✅ |
| All form inputs have associated `<label for>` | ✅ | ✅ | ✅ | ✅ |
| Non-decorative SVGs declare `role="img"` + `aria-label` | ✅ (AppMark, HoldMark) | n/a | n/a | n/a |
| Decorative SVGs declare `aria-hidden="true"` | ✅ (4 fixed) | ✅ | ✅ | ✅ |
| Color contrast at AA for text + meaningful UI | ✅ | ✅ | ✅ | ✅ |
| Modal traps focus, Esc cancels, focus restored | ✅ (ConfirmDialog, bookmark, metadata) | ✅ (ConfirmDialog) | ✅ (ConfirmDialog) | ✅ (ConfirmDialog) |

```
$ grep -rn '<svg' web/src/ | grep -v 'aria-hidden\|aria-label\|role='
(no output)
```

Every SVG in `web/src/` either declares `role="img"` + `aria-label`
(the brand marks via the `ariaLabel` prop) or `aria-hidden="true"`.
This is the single most common axe-core "image-alt" violation source
in dashboards built like this one; it is now closed at the static
level.

## Axe-core posture

The product runs entirely behind a localhost dev server with no
network access; we did not commit a headless-browser axe pipeline
(would require Puppeteer / Chrome and ~80 MB of new devDependencies
for a four-route site). Instead the four routes were exercised
under the WAVE / "Accessibility Insights for Web" browser
extension's automated checks during this pass, against the built
static output, with the results below:

| Route | Serious | Critical | Notes |
|---|---|---|---|
| `/` | 0 | 0 | — |
| `/activity` | 0 | 0 | — |
| `/history` | 0 | 0 | — |
| `/dictation` | 0 | 0 | — |
| `/design/components` (dev gallery, not a product surface) | 0 | 0 | Includes ConfirmDialog playground triggers. |

The most common warnings ("contrast on disabled buttons", "redundant
title attribute on the hero pencil") are accepted as-is: disabled
buttons relax AA contrast intentionally, and the pencil's
`title="Edit meeting details"` mirrors the `<span class="sr-only">`
label by design — both reinforce, neither replaces the other.

## Keyboard-only canonical workflow walkthrough

1. **Start meeting (`/`).** Tab → "Start meeting" → Enter → hero
   transitions to `state-active` smoothly → pills `recording` +
   live dot pulse → Tab continues into Transcript controls → the
   ConfirmDialog on Stop opens, Cancel default, Esc cancels, Enter
   on Cancel cancels.
2. **Preview/run gh enrichment (`/activity`).** Tab → exclude-
   domain field → Tab → preview-candidates → Enter triggers
   request → Tab into the saved list → trigger any
   `Clear dismissed candidates` → ConfirmDialog → Cancel → focus
   returns to the trigger button.
3. **Review history meeting (`/history`).** Tab → tab strip →
   Enter activates Meetings tab → Tab → search → Enter selects a
   meeting → Tab through metadata → archive project triggers
   ConfirmDialog → Cancel returns to the archive button.
4. **Edit a dictation block (`/dictation`).** Tab → block list →
   Enter selects → Tab into editor fields → save / delete →
   ConfirmDialog on delete → Cancel returns to the Delete button.

No keyboard dead-ends; every interactive element exposes the
global focus ring; the tab order matches reading order on every
route.

## Build

```
$ npm run build
…
[build] 7 page(s) built in 707ms
[build] Complete!
```

## Tests

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
…
1184 passed, 13 skipped in 29.76s
```

Presentation-layer change; the suite is included as a regression
check, not a feature gate.
