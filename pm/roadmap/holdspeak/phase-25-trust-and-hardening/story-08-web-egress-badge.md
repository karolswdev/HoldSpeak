# HS-25-08 — Web Egress-Posture Badge

- **Project:** holdspeak
- **Phase:** 25
- **Status:** backlog
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

- [ ] The dashboard shows the egress posture from `intel_egress` without logs.
- [ ] The badge is visually distinct when transcripts can leave the machine.
- [ ] `_built/` is rebuilt and committed; the page-content test for the badge
      passes.

## Test plan

- Integration: extend `tests/integration/test_web_server.py` with a
  page-content assertion for the badge markup.
- Manual: load `/`, toggle `intel_provider` local↔cloud, confirm the badge flips.

## Notes / open questions

- Coordinate the `_built/` rebuild with the pre-existing stale-`_built` page
  tests (see HS-25-01 evidence "pre-existing failures"); this story may
  incidentally refresh built assets — keep that intentional and noted.
