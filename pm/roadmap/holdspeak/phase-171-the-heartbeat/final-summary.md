# Phase 171 — The Heartbeat: final summary (DRAFT — stacked on 170; closes on his word)

## What shipped

- **The design (01):** settled-design-heartbeat.md + twelve boards (the
  shade with PROJECTS · quiet · 393; the notification with the swallowed
  state labelled; the dock badge; ⌘K PROJECTS; Rhythm's cadence row ·
  running · quiet · generating · 393; the hub row). Canvas
  https://claude.ai/code/artifact/82c55045-4a19-4990-a8b5-569b91eb8647.
  Counsel RATIFY-W-C — the rulings: one count everywhere (badge = shade
  caption = notification), muted Rooms dimmed with `MUTED` and out of
  every count; the single aggregate builder; the short caption; the
  click action deferred to the bundle; `Generate now` disabled while
  generating; ⌘K capped at 10.
- **The wire (02 · 03 · 05 · 06):** one setting in `cadence_policies`
  (`heartbeat`: sweep every N min · quiet hours · notify off/edge/every ·
  content · mutes); the scheduler stamps `next_evaluation_at`; a THIRD
  conductor loop `HoldSpeakHeartbeat` with its own failure boundary runs
  `evaluate_due` on the cadence (the seam nothing ever called before),
  refreshes the aggregate and writes one `heartbeat.sweep` receipt;
  `run-now`; the needs-you aggregate behind a stale-while-refresh cache
  (`computedAt · stale · sweepId`; the arrival's read is O(1) — Article V);
  the notifier (count-only body, the edge rule, quiet hours held and
  receipted; macOS via `osascript` from the presence child — the click
  target waits for the bundle; Linux via libnotify); the brief regenerates
  once a day before any push; MCP `heartbeat` family (201 tools / 36
  families).
- **The faces (04 · 07 · 02/06):** _filled at build_ — the shade's PROJECTS
  section + the dock badge; PROJECTS in ⌘K; Rhythm's cadence row + the
  brief row + NOTIFY with the mutes; the hub's Rhythm row.
- **The docs (09):** _filled at build_.
- **The walk (08):** `tests/e2e/live171_walk.py` — _filled at the walk_: a
  sweep of his real Rooms receipted; the shade, the badge, ⌘K and Rhythm
  on his desk; a banner at a real edge is his to see.

## Found live, paid in the phase

- _filled at build_

## The suite

- _filled at close_

## What the owner owes the phase

1. His word on 170 (PR #553) — this phase is stacked on it.
2. His word on this canvas and his walk: a notification he receives.
3. His three answers: the notification's click target; one flat interval
   or active/idle; whether mute hides a Room from the shade (ruled for V0:
   dimmed and shown, out of every count — his to overrule).
