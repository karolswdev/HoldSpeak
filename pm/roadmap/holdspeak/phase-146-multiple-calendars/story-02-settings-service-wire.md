# HS-146-02 — Settings service + wire

- **Project:** holdspeak
- **Phase:** 146
- **Status:** in-progress
- **Depends on:** HS-146-01
- **Unblocks:** HS-146-03
- **Owner:** unassigned

## Problem

The settings wire validates and projects exactly one subscription
(`settings_service.py:902-912` validation, :127-129 the
`_calendar_subscription` derived fact) and the Door's
`calendar_configured` reads the single key (`door_service.py:60-68`).

## Scope

### In (settled design rows 4–5 wire half, 7)

- Validation accepts `{calendar: {sources: [...]}}` — each entry's
  url through `validate_calendar_subscription`, malformed entries
  refused by name; ids preserved, missing ids minted server-side.
- Derived fact `_calendar_sources: [{id, kind, host,
  refresh_seconds, egress, label}]` (replaces
  `_calendar_subscription`; stripped on write at the same seam).
- `DoorService._calendar_configured()` = ≥1 enabled valid source.
- MCP settings family description text (`mcp/families/settings.py:28`)
  tells the sources truth.
- The e2e/walk seeds that POST the old wire shape flip in this
  commit if story 01 kept them alive (risk register row 1).

### Out

- The list editor UI (03); rail provenance (04).

## Acceptance criteria

1. settings_update with two sources persists both; invalid url in
   one entry refuses the write with a named error, in-flow.
2. `_calendar_sources` reports per-source kind/host/egress truth.
3. `calendar_configured` true with one enabled valid source among
   disabled/invalid ones; false when all disabled or none.
4. Transport parity on the door aggregate holds (same config_loader
   both sides).

## Test plan

`tests/unit/test_door_read_model.py` (configured semantics),
settings validation units (extend the existing settings service test
file found in tests/unit), `tests/unit/test_door_transport_parity.py`.
