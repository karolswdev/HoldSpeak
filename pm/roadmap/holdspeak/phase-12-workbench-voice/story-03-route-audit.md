# HS-12-03 - Per-route audit + dashboard fixes

- **Project:** holdspeak
- **Phase:** 12
- **Status:** done
- **Depends on:** HS-12-02
- **Unblocks:** HS-12-04

## Problem

After HS-12-01 + HS-12-02 land the new voice in tokens and
components, every route still has scoped page CSS that may need
its own pass. The dashboard in particular has four polish items
that surfaced during phase-10 review and were never addressed.

## Scope

- **In:**
  - `/` runtime dashboard — fix the four polish items:
    1. Oversized hero "HoldSpeak" wordmark duplicates the
       TopNav brand. Shrink the hero to ≤ 24 px or remove
       the wordmark entirely (TopNav already shows it);
       promote the meeting title or a "ready" affordance to
       that slot.
    2. Cyan-accent saturation on the primary "Start meeting"
       button — already addressed by HS-12-01 token swap;
       confirm in-context here.
    3. Duplicate "Failed to load deferred plugin jobs" toast
       — dedupe the toast layer so identical messages collapse.
    4. Idle-state copy redundancy — pick one of the three
       "press start" affordances (hero copy / side-rail
       caption / tag-chip empty state).
  - `/activity`, `/history`, `/dictation` — visual audit, fix
    only what the new voice broke. Density wins ties.
  - Capture fresh screenshots into
    `designer-handoff/screenshots/` (full set rendered through
    the running app) for review.
- **Out:**
  - New product features.
  - Component-library changes (HS-12-02 territory).
  - Workflow changes; presentation only.

## Acceptance Criteria

- [x] Hero wordmark is right-sized; brand never appears twice on
  the same screen above the fold.
- [x] Toast layer dedupes consecutive identical messages.
- [x] Idle state on `/` shows exactly one "you can start a
  meeting" affordance.
- [x] Each route's screenshot in `designer-handoff/screenshots/`
  is current.
- [x] No regressions in dense list legibility on `/activity`
  records, `/history` meetings, `/dictation` blocks.

## Test Plan

- Manual walk through every route at desktop + 390 mobile.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` stays
  green.
- DevTools `prefers-reduced-motion: reduce` toggle: animations
  collapse correctly.

## Notes

The dashboard is the front door — this story is what makes the
phase land. If the four dashboard fixes feel too small to be
worth a story by themselves, they're bundled here intentionally:
they only make sense once the new voice is in place.
