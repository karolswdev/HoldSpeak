# HS-124-10 — The walk

- **Project:** holdspeak
- **Phase:** 124
- **Status:** done
- **Depends on:** HS-124-05, HS-124-07, HS-124-08, HS-124-09
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

The walk is the proof. It exercises the observer end-to-end: service
calls produce events, events are queryable, the MCP resource works, and
the doctor check passes.

### Walk script

`scripts/desk_walk/walk_observer_124.py` — a Python script using the
walk harness from Phase 122.

### Walk steps

1. **Start isolated hub** with the walk fixture (temp DB, observer wired).
2. **Exercise 5+ distinct services** via HTTP routes:
   - `PrimitiveService.create_note` / `list_notes`
   - `WorkbenchService.create_workbench` / `list_workbenches`
   - `ProfileService.list_profiles`
   - `SettingsService.get_settings`
   - `DeskService.health`
3. **Query events** via MCP resource `pipeline://events/recent` — confirm
   all service calls appear as events.
4. **Query stats** via MCP resource `pipeline://events/stats` — confirm
   the 5 services appear with correct counts.
5. **Query by correlation** — make a correlated pair of calls, query
   `pipeline://events/correlation/{id}`, confirm both appear.
6. **Run desk doctor** — confirm `observer_wired` check passes.
7. **Timing assertion** — every event's `duration_ms` is > 0 and < 5000.
8. **Coverage assertion** — the number of distinct `service` values in
   `pipeline_events` is >= 5.

### Walk output

The walk produces a structured JSON report:

```json
{
  "walk": "observer_124",
  "steps": 8,
  "passed": 8,
  "events_recorded": 12,
  "distinct_services": 5,
  "doctor_observer_check": "healthy"
}
```

## Acceptance

- Walk script exits 0 with all steps green.
- Walk output confirms >= 5 distinct services observed.
- Doctor check passes.
- No regressions in existing walks (122, 123).

## Test plan

```bash
python scripts/desk_walk/walk_observer_124.py
uv run pytest -q tests/ -k "not metal"
```
