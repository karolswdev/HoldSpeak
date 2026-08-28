# HS-145-02 — The connect-calendar affordance

- **Project:** holdspeak
- **Phase:** 145
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-145-03
- **Owner:** unassigned

## Problem

Phase 144 close-counsel concern (2): the UPCOMING rail's empty state
(`web/src/desk/chair/lanes/DoorBoardLane.tsx:253`) dead-ends at "No
future time scheduled." Calendar setup lives under Settings→Meetings
and nothing on the Door points there. The one feature that fills the
rail is undiscoverable from the rail.

## Scope

### In

- **The additive projection field** ([B2a] RULED — live read):
  `DoorService` (`holdspeak/services/door_service.py`) gains an
  optional `config_loader`; `get()` returns top-level
  `calendar_configured: bool` computed from
  `validate_calendar_subscription(config.calendar.subscription)`.
  Both compositions pass `Config.load`
  (`holdspeak/web/routes/door.py`, `holdspeak/mcp/families/door.py`)
  so HTTP and the `door.get` twin stay in parity. No new route, no
  new MCP tool, no schema migration.
- **The affordance** (charter settled design row 3): when
  `calendar_configured` is false and the rail is empty — "No calendar
  connected." + ghost **Connect calendar** button calling
  `useSurfaceWindows.getState().openSurfaceWindow("configure-settings",
  "meetings")` (the shipped scope mechanism; in-world, no modal).
  When configured and quiet: the existing message, no nag.
  `DoorProjection` type + `UpcomingRail` prop threaded; the
  `--connect` CSS modifier beside `.door-upcoming-empty`
  (`chair.css:496`). Full edit map:
  `assets/plan-door-polish.md` §Item B.
- **Guard truth:** `scripts/mcp_walk.py` door aggregate key-set
  assertion (~:263) gains `calendar_configured` in this story.

### Out

- Any change to the calendar ingest itself, the Settings Meetings
  module, or multiple-subscription support (backlog).
- The trust-destinations registry entry (named product gap, backlog;
  never a data-only fake).

## Acceptance criteria

1. `/api/door` and `door.get` both carry `calendar_configured`,
   equal, computed live (configuring a calendar flips it without a
   hub restart).
2. Empty rail + no calendar → the connect affordance; one click lands
   in Settings scoped to Meetings.
3. Empty rail + configured calendar → "No future time scheduled.",
   no connect affordance.
4. Transport parity holds (`test_door_transport_parity.py` passes
   with both sides on the same `config_loader`).

## Test plan

- `tests/unit/test_door_read_model.py` — field False on empty
  subscription, True on a valid HTTPS value.
- `tests/unit/test_door_routes.py`, `tests/unit/test_door_mcp.py` —
  aggregate key-set assertions gain the field.
- `tests/unit/test_door_transport_parity.py` — rig passes the same
  `config_loader` on both sides.
- `web/src/desk/chair/lanes/DoorBoardLane.test.tsx` — fixture gains
  the field; three new tests (shown when false+empty; quiet when
  true+empty; click opens Settings→Meetings).
- Focused: `uv run --python 3.13.11 pytest -q tests/unit/test_door_read_model.py
  tests/unit/test_door_routes.py tests/unit/test_door_mcp.py
  tests/unit/test_door_transport_parity.py` under an isolated HOME;
  `npx vitest run` on the lane test from `web/`.
