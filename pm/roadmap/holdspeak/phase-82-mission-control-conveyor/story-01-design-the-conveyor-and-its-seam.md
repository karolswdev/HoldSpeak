# HS-82-01 — Design: the conveyor and its consumption seam

- **Project:** holdspeak
- **Phase:** 82
- **Status:** done — see [`evidence-story-01.md`](./evidence-story-01.md).
- **Depends on:** nothing (the Delivery Workbench substrate is
  shipped and frozen: their Phase 13 stories 02–04).
- **Unblocks:** HS-82-02..05.

## Problem

Two repos are finishing one experience, and the contract already
exists — on their side. Delivery Workbench's
`docs/mission-control.md` §5 pins what any client may consume:
the state feed (`dw state --json`, `feed_schema` 1), the
correlation document (`dw sessions --json`, `sessions_schema` 1),
and the event log (`dw events --json`) — via the dw CLI, never by
scraping `pm/roadmap` or importing dw internals; every client
declares the schema versions it was proven against, and drift is a
compatibility note on the client, not a silent break. What is NOT
designed anywhere is the Desk's side: how the three documents
reach a React island whose one architectural rule is "every read
is a same-origin `/api/*` route", what the conveyor actually looks
like, and how a Desk approval reaches the Phase-12 connector.
Guessing any of that in the implementation stories is how two
clients fossilize two accidents — the exact failure their design
story exists to prevent, and ours does too.

## The design

Produce the phase's design section (this story amends
`current-phase-status.md` and writes `docs/internal/MISSION_CONTROL_DESK.md`)
pinning, with the verified/cited/decided discipline:

- **The bridge shape** — FastAPI router `/api/missioncontrol/`
  with `state`, `sessions`, `events` routes; each shells to the dw
  CLI of a configured rails repo (repo set = the existing
  `~/.holdspeak/delivery_workbench.json` project map, the pack's
  own config), read-only, allow-listed argv, timeouts, and
  schema-check at ingress: `feed_schema` 1 and `sessions_schema` 1
  accepted, anything else relayed as a typed compatibility error
  the UI renders honestly.
- **The declared field list** — which correlation fields the Desk
  renders (`key`, `agent`, `correlation`, `stories`,
  `awaiting_response`, `stale`, `tmux.session`) and the promise to
  treat everything else as opaque.
- **The conveyor UX** — phases as the belt (their feed's
  per-project `phases` array exists precisely for this), stories
  as items with status + evidence marks, the next actionable story
  visually distinct, warnings visible, gate refusals rendered as
  first-class moments (rule id shown verbatim), never terminal
  noise.
- **The approval leg's route** — a Desk approval builds a
  `dw_action` fields payload for the actuator pack's deterministic
  path and executes through the gated connector
  (`dw_story_writer`, two argv shapes); the Desk never builds
  argv, never bypasses the proposal→approval envelope, and renders
  a dw refusal as the stack working.
- **Polling stance** — the bridge polls the CLI on request (the
  feed is "the cheapest thing a consumer can poll"); no daemon, no
  file-watcher in v1; cadence and caching decided here.

## Test plan

- Docs: the design doc exists, claims carry their marks, and the
  four implementation stories cite the sections they implement
  (re-pinned in the same commit that lands this story's evidence).
- The schema declarations match what `dw state --json` and
  `dw sessions --json` emit on this desk, verified live, versions
  recorded.
