# Evidence - HS-147-01

- **Story:** HS-147-01 - The link (schema + arm verb, server side)
- **Status:** done
- **Date:** 2026-08-28

## Proof

### Captured run — 2026-08-29T05:43:30Z

- **Command:** `bash -c HOME_REAL=$HOME; HOME=$(mktemp -d) uv run --python 3.13.11 pytest -q tests/unit/test_event_linked_arm.py tests/unit/test_scheduled_recording_conductor.py tests/unit/test_scheduled_recording_mcp.py tests/unit/test_scheduled_recording_routes.py tests/unit/test_door_mcp.py tests/unit/test_door_read_model.py tests/unit/test_door_routes.py tests/unit/test_door_transport_parity.py tests/unit/test_db_schema_policy.py tests/unit/test_phase143_scheduled_route_terms.py tests/unit/test_phase143_routing_authority_census.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f14eb3ef0244841e9e02d26982e55d43d49db185

```text
........................................................................ [ 46%]
........................................................................ [ 92%]
............                                                             [100%]
156 passed in 39.19s
```

## Orchestrator triage note (2026-08-29)

Verified beyond the builder's word: the D2 computation read line by
line (fromisoformat/astimezone only — the ISO-offset law holds;
remainder rule + 480 cap + max(1,·); 60s lead; fire-now for
in-progress), the manual path still validates cron (the MCP
`required` loosening is safe — `_validate_cron("")` refuses), and
the lifecycle test rides the REAL conductor with fakes only at the
meeting-fn seam (stub law satisfied). 156 focused tests re-run by
the orchestrator and read from file.

**Deviation rulings (orchestrator tie-breaker):**
- `calendar_event_not_found` surfaces as the house
  `NotFound("calendar_event", id)` (code `not_found` + entity kind)
  rather than a bespoke literal code — ACCEPTED; the house
  entity-refusal shape IS the named refusal here.
- Dummy cron `"0 0 1 1 *"` on event-linked one-shots — ACCEPTED;
  the conductor drives one-shots by `next_fire_at` and
  `_advance_after_terminal` disables before any cron evaluation.
  The comment in the service says exactly this.
- Injectable clock + `CalendarEventRepository.get()` — clean new
  seams, no concerns.

**Branch-new fallout caught and healed in this commit:** the
builder's report called the routing-authority census failure
"pre-existing, about calendar_snapshot_service.py which I did not
touch" — WRONG attribution: it was fallout of HS-147-05 (shipped
mid-flight in `9c897b5a`), which removed the HS-146-07
resolve_placement fallback the census had deliberately registered.
The two dead entries are now RETIRED with an HS-147-05 attribution
comment (deliberate deregistration, not drift); census 10/10 green.
The lesson: a lane brief that excludes guard files must name the
orchestrator as the guard-owner — recorded for the next brief.
