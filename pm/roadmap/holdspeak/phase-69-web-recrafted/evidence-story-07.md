# Evidence — HS-69-07: The Queue HUD (shell + store)

**Date:** 2026-06-30
**Verdict:** done. The always-on Queue HUD pill expands into a live job ledger,
fed by the shared runtime-bus — proven in a screenshot.

## What shipped (substrate wave, confirmed)

- `web/src/scripts/runtime-bus.js` — the shared, lazily-opened `/ws` bus the
  shell components subscribe to (alongside the dashboard's own socket).
- `web/src/scripts/queue-hud.js` — the store + DOM render: jobs derived from
  `intel_status` (the "intel" job) and `runtime_activity` (the "runtime" job);
  done/failed jobs linger then prune; the collapsed pill shows the urgency
  beacon + summary; the expanded ledger renders signal-card `.qh-row`s (with
  `hs-materialize`).
- `web/src/components/QueueHud.astro` — mounted in AppLayout (top-center), rides
  every route, hidden when nothing runs.

## Proof

- **`screenshots/queue-hud.png`** (a route-mocked `/api/state` with a running
  intel job + a transcribing runtime): the collapsed pill reads **"2 working"**;
  expanded, the ledger shows **Transcribing · HOLD-TO-TALK** and **Meeting
  intelligence · ENDPOINT · "Summarizing the meeting"** as signal-card rows with
  the bolt orb + WORKING chips (`queue rows: 2`).
- Honest gaps (documented in the module header): no per-job % (an indeterminate
  shimmer bar), only two concurrent jobs derivable from the coarse frames — both
  described, not faked.
