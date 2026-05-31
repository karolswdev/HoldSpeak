# HS-25-08 — Web Egress-Posture Badge

- **Project:** holdspeak
- **Phase:** 25
- **Status:** done
- **Depends on:** HS-25-01
- **Unblocks:** HS-25-07
- **Owner:** unassigned

## Problem

HS-25-01 shipped the egress posture as data: `holdspeak doctor` prints it and the
runtime-status API exposes `intel_egress` (`{enabled, provider,
can_transmit_offmachine, egress}`). The web dashboard does not yet *render* it, so
a user watching only the browser can't see whether transcripts can leave the
machine. This is the visual surfacing that completes the "make egress posture
visible" goal — split out from HS-25-01 because it needs an Astro/Alpine change
plus a `_built/` rebuild, a different blast radius from the backend trust work.

## Scope

### In

- Render an egress badge on the runtime dashboard (`web/src/pages/index.astro`
  + `web/src/scripts/dashboard-app.js`) bound to `intel_egress` from
  `/api/runtime/status`: a clear "Local only" vs "Cloud" / "Auto → cloud
  fallback" indicator, visually distinct when `can_transmit_offmachine` is true.
- Rebuild the Astro bundle into `holdspeak/static/_built/` so the shipped wheel
  carries it.

### Out

- Backend posture computation (done in HS-25-01).
- Settings-page changes for switching provider (already exists).

## Acceptance criteria

- [x] The dashboard shows the egress posture from `intel_egress` without logs —
      a "Privacy" stat bound to `egressLabel()` (`web/src/pages/index.astro` +
      `web/src/scripts/dashboard-app.js`).
- [x] The badge is visually distinct when transcripts can leave: `🔒 Local only`
      / `🔒 Intel off` vs `☁︎ Cloud` / `☁︎ Auto → cloud`, full sentence in the
      `title` tooltip.
- [x] `_built/` rebuilt (`npm run build`) and committed; page-content test
      `test_dashboard_includes_egress_posture_badge` passes.

## Test plan

- Integration: extend `tests/integration/test_web_server.py` with a
  page-content assertion for the badge markup.
- Manual: load `/`, toggle `intel_provider` local↔cloud, confirm the badge flips.

## Notes / open questions

- Coordinate the `_built/` rebuild with the pre-existing stale-`_built` page
  tests (see HS-25-01 evidence "pre-existing failures"); this story may
  incidentally refresh built assets — keep that intentional and noted.

## Closeout

Shipped 2026-05-31. See [evidence-story-08.md](./evidence-story-08.md).

The rebuild cleared **6 of the 9** pre-existing failures (all the stale-`_built`
page-content tests). Correction to the earlier characterization: the remaining
**3** `test_activity_history` failures are **not** a "missing Safari fixture" —
the test self-creates its fixture, but with a **fixed** `visit_time` (~2026-04-29
macOS epoch). The importer prunes records older than the 30-day retention default
at import; now that real time is past that date + 30d (today 2026-05-31), the
record is pruned immediately (`imported_count==1` but 0 retained). A time-bomb in
test data, pre-existing on `main`, unrelated to Phase 25. Filed as a follow-up
(see evidence); trivial fix = use a recent/relative timestamp or freeze time.
