# HS-10-05 - HoldSpeak identity layer

- **Project:** holdspeak
- **Phase:** 10
- **Status:** done
- **Depends on:** HS-10-02, HS-10-03
- **Unblocks:** HS-10-06, HS-10-07, HS-10-08, HS-10-09
- **Owner:** unassigned

## Problem

The current frontend has no visual identity — nothing about it says
"local, private, hold-to-talk." It reads as a generic dark dashboard
shell. The user's actual experience of the product (press a key, hold
to speak, release to commit) has no echo in the UI. This is the gap
between "functional" and "has character."

## Scope

- **In:**
  - App mark — a small, monochrome SVG that lives in the TopNav and
    favicon. Conveys a hold/keycap motif. Self-hosted; no external
    asset references.
  - Hold-to-talk visual motif — a reusable SVG/CSS waveform-or-keycap
    fragment used in: the runtime dashboard idle state, the `/`
    favicon variation when active, and the empty state of `/history`.
  - `LocalPill.astro` — a specialized Pill variant rendering the
    "local-only" privacy status; sits in the TopNav right slot and
    next to import/connector controls. Has a single tooltip explaining
    what local-only means in HoldSpeak.
  - Focus-ring grammar — a single token-driven ring style applied
    consistently across all interactive components (extends HS-10-03).
  - Favicon and `apple-touch-icon` regenerated from the mark.
- **Out:**
  - Marketing/landing page, hero illustrations, animated splash.
  - A logotype with custom letterforms — the wordmark stays in the UI
    type face.
  - Anything dynamic in the favicon beyond a two-state variant.

## Acceptance Criteria

- [x] App mark renders crisply at 16, 24, and 32px in the live nav.
- [x] `LocalPill` is used consistently in the TopNav and at every
  data-import / connector / deletion control across the four rebuilt
  routes (verified in HS-10-06..09 acceptance, listed here for
  traceability).
- [x] Focus rings on Button, ListRow, link, and form controls share a
  single style — no per-component drift.
- [x] Favicon and apple-touch-icon ship in `holdspeak/static/` after a
  clean `npm run build`.

## Test Plan

- Manual visual review across the components gallery.
- Browser tab favicon check in Chrome and Safari.
- Keyboard-only sweep of the gallery confirming the focus ring is
  uniform.

## Notes

The identity layer is small on purpose — over-designing it produces
the marketing-shell feel `style-handoff.md` explicitly warns against.
Restraint here is the point.
