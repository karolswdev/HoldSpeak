# HSM-16-04 — The web Astro Desk (parity build)

- **Project:** holdspeak-mobile (build lands in the holdspeak web app, `web/src`)
- **Phase:** 16
- **Status:** todo
- **Depends on:** HSM-16-01 (the spec), HSM-16-03 (the store/API to read), holdspeak Phase 68
  (design-pattern catalog + shared Signal tokens).
- **Unblocks:** HSM-16-05 (the surface that syncs), HSM-16-06 (proof).
- **Owner:** unassigned

## Problem

The web client has no Desk. To be a mesh, the DeskOS must exist in `web/src` (Astro) at parity with the
iPad — the same metaphor, the same objects, the same gestures — built against the real API, not a
mock.

## Scope

- **In:** the DeskOS twin in `web/src`:
  - A **canvas** of objects with weight/drag/settle (a physics-ish layer — pointer drag + inertia; the
    bar need not be SpriteKit, but it must feel like objects, not a list).
  - The **object kinds** from HSM-16-01: meetings, their **spilled** outputs, models, **directories**,
    **knowledge bases** (the crystal). Tap → open (spill / window / read), long-press/right-click →
    reshape, **lasso** → select, **bundle**, **file into** (classify).
  - A **left organization pane** (Smart / Library / Directories / Knowledge) and **floating app
    windows** on the desk (meeting detail, an output reader) — the windowing model, not page nav.
  - Built on the **shared Signal tokens** (Phase 68 catalog: accent `#FF6B35`, the surface/elevation
    ramps) so the two surfaces are visibly one product. Reads real data from `/api/meetings` + the
    HSM-16-03 organization store.
- **Out:** the live-meeting lasso (its own story), Fun Mode/CoreMotion (device-only). Sync wiring is
  16-05 — this story makes the surface; 16-05 makes it flow.

## Acceptance criteria

- [ ] A `/desk` route in `web/src` renders the canvas with real meeting objects; meetings spill into
      their outputs as objects; the org pane lists Smart/Library/Directories/Knowledge.
- [ ] Lasso → bundle → File into a directory/KB works; opening a KB spills its members; the crystal
      sprite is the KB object.
- [ ] Floating windows (meeting detail / output reader) open on the desk, draggable + closeable.
- [ ] Uses the shared Signal tokens; screenshot parity vs the iPad shots is reviewed.
- [ ] `cd web && npm run build` succeeds; the route passes the preflight route sweep.

## Test plan

- `cd web && npm run build` green; load `/desk` in headless Chromium, screenshot, compare to the iPad
  DeskOS shots for parity. Source-only commit (the built bundle is gitignored — see
  [[reference_web_bundle_gitignored]]).
