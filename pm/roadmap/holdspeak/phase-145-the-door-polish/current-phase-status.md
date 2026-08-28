# Phase 145 — The Door Polish

**Status:** in progress (0/3).

**Last updated:** 2026-08-28.

## Owner mandate

At the Phase 144 handover (2026-08-28) the owner was shown the short
menu the handover prescribed and picked **the Door polish pass**: the
two close-counsel concerns, dispositioned at the 144 close as
"LEDGERED for the next usability/beauty pass (polish, not defects)":

1. the 393 board's horizontal scroll has no visual hint that more
   columns exist;
2. calendar setup is not discoverable from the Door itself — a
   "connect calendar" affordance on the empty rail.

Small, high-joy. The owner's other two Phase-144 gates stay open and
are NOT this phase's business: the shot verdicts and the merge word
for the 144 branch line (main is still at `ab79c702`; this phase
stacks on `feat/hs144-06-walk-close` as `feat/hs145-door-polish`).

The standing charter questions apply: *will you use this on a tired
Tuesday?* and *does this operate with joy?*

## Evidence base

- The Phase 144 close-counsel verdict (RATIFY-WITH-CONCERNS, the two
  concerns named), recorded in
  `../phase-144-the-dashboard-door/current-phase-status.md` §decision
  log.
- [`assets/plan-door-polish.md`](./assets/plan-door-polish.md) — the
  read-only opus plan (2026-08-28): verified anchors, the settled
  designs, the edit maps, the focused test plan, the guard risks.

## Settled design (orchestrator-ruled; the owner may overrule any row)

Per the ceremony budget, the plan's two [ORCH-CALL]s were ruled the
same day; no counsel round was spent on the charter:

1. **[A1] Scroll hint = scroll listener + `data-scroll-hint`
   attribute, RULED.** Pure-CSS scroll-driven animation fails the
   repo's Safari 15.4 floor; a small rAF-throttled listener on the
   one viewport div sets `none|right|left|both` and CSS sticky
   pseudo-elements paint `--surface-1` edge gradients. The hint is
   ABSENT whenever nothing clips (the normal 1440 case) and never
   lies at either end of the scroll range.
2. **[B2a] `calendar_configured` freshness = live config read, RULED.**
   `DoorService` gains an optional `config_loader`; `get()` computes
   the new top-level additive `calendar_configured` boolean from
   `validate_calendar_subscription(config.calendar.subscription)` at
   read time. Both compositions (web route, MCP `door.get`) pass
   `Config.load` — the affordance dies the moment the owner connects
   a calendar, no restart. No schema migration; no new route; no new
   MCP tool.
3. **Affordance grammar.** When `calendar_configured` is false and
   the rail is empty: "No calendar connected." + a ghost
   **Connect calendar** button that opens the existing Settings
   window scoped to the Meetings module
   (`openSurfaceWindow("configure-settings", "meetings")` — the
   shipped alias mechanism, no new store action, no modal). When a
   calendar IS configured and quiet: the existing "No future time
   scheduled." stands — configured is never nagged.
4. **Guard truth.** `scripts/mcp_walk.py`'s door aggregate key-set
   assertion gains `calendar_configured` in the same story that adds
   the field; the 135 tool count and the api-surface manifest do not
   move (verified in the plan).

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-145-01 | The board scroll hint | ready | [story-01](./story-01-board-scroll-hint.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-145-02 | The connect-calendar affordance | ready | [story-02](./story-02-connect-calendar.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-145-03 | Shots and the close | ready | [story-03](./story-03-shots-and-close.md) | [evidence-story-03](./evidence-story-03.md) |

## Risk register

- **Both stories edit the same file pair** (`DoorBoardLane.tsx`,
  `chair.css`) — one builder works them sequentially in one lane;
  no parallel-tree collision is possible.
- **Transport parity** (`test_door_transport_parity.py`) breaks if
  the two sides of the rig receive different `config_loader`s — the
  test change is named in the story, not left to be discovered.
- **The walk baseline**: sweeps are judged against the Phase 143
  inherited-failure baseline, verdict vocabulary
  "baseline-exact, zero branch-new".

## Decision log

- 2026-08-28 — Phase chartered on the owner's menu pick. Plan worker
  report archived; [A1] and [B2a] ruled as recorded in the settled
  design.
