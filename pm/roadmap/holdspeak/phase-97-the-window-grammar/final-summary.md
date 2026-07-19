# Phase 97 — The Window Grammar: final summary

**CLOSED 9/9, 2026-07-18 — scaffolded and shipped the same day**, at
machine-verifiable scope under the standing close directive. Born from
the owner's direct verdict on the Desk OS ("zero cohesion, zero UX,
zero operating-system feeling") and the same-day live screenshot + code
audit that confirmed it mechanically.

## What shipped

- **HS-97-01 — The shadow returns.** The token generator resolves
  `{refs}` embedded in composite values; a mechanical lock refuses any
  emitted declaration carrying a brace. `--desk-window-shadow` and
  `--desk-transient-shadow` are valid again — every window casts real
  elevation. The whole unresolved-reference defect class is locked.
- **HS-97-02 — A window lands well.** `placeWindow` seats every window
  whole inside the working band, seeded at its CSS home and moved off
  other title bars by a min-overlap scan; persisted rects clamp on
  open; the cascade survives only at true saturation.
- **HS-97-03 — The arrangement is sacred.** `hs.desk.panels` persists
  `{rects, order, max}`; windows rehydrate at their remembered plane;
  minimize is honestly session-scoped; the room menu wears the
  transient material; shelf furniture rides the dock band z tokens.
- **HS-97-04 — Focus and depth.** The front window alone wears the
  full elevation plus an accent keyline; rest windows quiet down;
  close animates out; minimize contracts into its dock chip and
  restore returns from it; reduced motion is instant.
- **HS-97-05 — Hands on the frame.** The snap ghost previews the
  landing tile live and the release lands exactly on it; edge resize
  (left/right/bottom + bottom-left corner); double-click maximize.
- **HS-97-06 — The switcher.** Exposé fans every open window into a
  pick grid (minimized ones as dimmed cards); Ctrl+` cycling shows a
  transient strip naming every window and the landing target.
- **HS-97-07 — One shelf, quiet chrome.** The dock is the one centered
  shelf: launchers (Desk memory, Delivery, Panes), the record orb at
  its center, a chip per open window, the overview and reset verbs.
  The four floating pills are deleted; the eyebrow is demoted; the
  stage prose is gone.
- **HS-97-08 — The physics floors, written.** DESIGN_SYSTEM.md names
  every contract as an Article VIII.2 floor tied to its walk leg; the
  add-a-surface path and the architecture locks list carry the
  grammar.
- **HS-97-09 — Closeout.** The assembled walk (all eight Phase 95 legs
  + the six-leg grammar chain) green on the production bundle with
  zero failed API responses; storm 8.3ms median / p95 10.2 / 1 layout
  event (assembled, headed); `npm run check` 279/279; full sweep
  green; final 1440/393 shots archived and looked at.

## What the closeout hardened

Running the whole OS as one chain surfaced and fixed three real
defects the per-story walks missed:

- the placement engine froze lazily-loaded windows at their Suspense
  fallback height (windows opened ~220px tall with content clipped
  outside) — the seat now comes from the CSS max-height constraint,
  capped at 78% of the band so default windows stagger their title
  bars instead of saturating the stage;
- the chrome cluster's raise rule covered only the room menu — an open
  tool shelf could sit beneath a window seated under the top-right
  cluster; `:has(.desk-tool-shelf)` now lifts it the same way;
- the walk's own furniture assumptions (hardcoded seeded-object
  titles, toggle-blind shelf clicks, bare-coordinate object taps) are
  replaced with honest helpers (`free_object`, `open_shelf`) that
  respect the new truth: windows and the dock are real geometry.

## Deferrals and riders

- The owner's live verdict rides the next UAT sitting (Campaign 13's
  desk-os-design-polish scenario now shows this grammar).
- Content re-crafting of the demoted cores ("Native Surfaces") and the
  world's object/ground treatment with object-to-window continuity
  ("The Living World") are the staged follow-up phases from the audit.
- iPad/Diorama parity ("One Grammar on Glass"): the HSM track consumes
  the token JSON (a Swift emitter is the recorded next step), one
  DioWindow container, and the no-modals sheet kill.
- Keyboard window move/resize is the recorded rider from HS-97-05.

## Numbers

Nine stories, one day. Suite at close: web 279/279 within `npm run
check` end to end; python sweep green (metal exclusion per standing
rule); storm 8.3ms median assembled with the full grammar live; token
allow-list 69 → 67 (two stale entries retired, zero added).
