# HS-125-01 — Wire SQLiteObserver into production composition

- **Project:** holdspeak
- **Phase:** 125
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-125-02 through HS-125-10
- **Owner:** unassigned

## The thesis (the bar)

Phase 124 built the observer infrastructure: `@observe_service`
decorates all 33 service classes, `SQLiteObserver` persists events to
`pipeline_events`, and `EventQueryService` queries them. But route
factories and `holdspeak/mcp/tools.py` currently construct services
without injecting a real observer — they fall back to `NullObserver`,
leaving `pipeline_events` incomplete in production.

This story wires one shared `SQLiteObserver(db._connection)` into
both the FastAPI route composition and the MCP tool dispatch, so every
real HTTP and MCP call records a pipeline event.

### What changes

1. **Route factories** — the `_svc()` helper (or equivalent) in route
   modules passes a shared `SQLiteObserver` to every service it
   constructs.
2. **MCP dispatch** — `holdspeak/mcp/tools.py` constructs services
   with the same shared observer.
3. No new tables, no schema bump. The infrastructure exists; this
   story plugs it in.

### What does NOT change

- The `@observe_service` decorator (Phase 124, stable).
- The `PipelineObserver` protocol (Phase 124, stable).
- Test fixtures — tests may use `NullObserver` or `SQLiteObserver`
  as they choose.

## Acceptance criteria

1. An HTTP `POST /api/notes` (or any route that calls
   `PrimitiveService.create_note`) produces a row in `pipeline_events`
   with the correct service, method, principal, and correlation ID.
2. An MCP tool call (e.g. `desk.snapshot`) produces a row in
   `pipeline_events` with the correct service, method, and principal.
3. `EventQueryService.recent()` returns events from both HTTP and MCP
   origins.
4. No performance regression: observer overhead stays under 5ms per
   call (measured in the walk).

## Test plan

- Unit: construct a route-factory service with `SQLiteObserver`,
  call a method, assert `pipeline_events` row exists.
- Unit: construct an MCP-dispatch service with `SQLiteObserver`,
  call a tool, assert `pipeline_events` row exists.
- Integration: `uv run pytest -q -k "observer"` — existing Phase 124
  observer tests still pass.
