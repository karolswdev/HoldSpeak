# HS-82-02 — The bridge: `/api/missioncontrol/*` relays the three documents

- **Project:** holdspeak
- **Phase:** 82
- **Status:** backlog
- **Depends on:** HS-82-01 (the design pins the routes, the argv
  allow-list, and the ingress schema checks).
- **Unblocks:** HS-82-03, HS-82-04.

## Problem

The Desk island reads only same-origin `/api/*` routes — the feed
cannot enter through the browser, and the §5 contract forbids
entering through anything but the dw CLI. The bridge is the whole
gap: three read-only routes that shell to `dw state --json`,
`dw sessions --json`, and `dw events --json` for each rails repo
the project map names, and relay the documents untouched.

## The design

Per HS-82-01's pins: a FastAPI router under
`holdspeak/web/routes/`, argv built from a fixed allow-list (the
repo's own `.githooks/dw` first, installed `dw --root` second —
the pack's recorded decision, reused), subprocess with timeout and
`stdin=DEVNULL`, no shell. Ingress checks: `feed_schema` 1 /
`sessions_schema` 1 pass through; any other version returns a
typed `compatibility` error payload; a dead or absent dw CLI
returns a typed `unavailable` payload. No caching beyond the
design's polling stance; no mutation of the documents — the Desk
receives what the rails said, byte-honest.

## Test plan

- Unit: route tests with a fixture dw CLI (a script emitting
  canned documents) — pass-through, compatibility refusal on a
  bumped schema, unavailable on a missing CLI, timeout behavior.
- No live network, no real rails repo required in CI.
