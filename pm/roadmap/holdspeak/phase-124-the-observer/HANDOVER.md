# HANDOVER — Phase 124 (The Observer)

**Date:** 2026-08-06
**Author:** Opus 4.6 orchestrator session

## What shipped

Phase 124 added the observer to the service pipeline. Every public
method on every service is now instrumented: who called it, what they
asked for, what came back, how long it took, and when. Events are
stored in a local append-only SQLite table. No telemetry leaves the
machine (Article III.3).

## The numbers

| Metric | Before | After |
|--------|--------|-------|
| Observed service classes | 0 | 33 |
| Pipeline event fields | — | 13 |
| MCP resources (pipeline) | 0 | 4 |
| MCP tools (pipeline) | 0 | 1 |
| Doctor checks (observer) | 0 | 1 |

## What was built

1. **PipelineEvent** — frozen dataclass with 13 fields (event_id,
   timestamp, service, method, principal_kind, principal_identity,
   args_summary, result_summary, error, error_code, duration_ms,
   correlation_id, is_async).

2. **PipelineObserver protocol** — single `on_event` method.
   `NullObserver` for tests and default.

3. **`@observed` decorator** — wraps sync and async methods, captures
   timing/args/result/error, propagates correlation IDs via contextvars.
   Observer failures never break service calls.

4. **`@observe_service` class decorator** — introspects public methods,
   applies `@observed` to each. Skips private, static, and class methods.

5. **SQLiteObserver** — writes events to `pipeline_events` table.
   Fire-and-forget; logs warnings on failure.

6. **`pipeline_events` table** — schema v38, append-only, four indexes
   (timestamp, service+method, principal, correlation).

7. **All 33 services wired** — `@observe_service` + constructor
   `observer` kwarg on every service class.

8. **EventQueryService** — `recent()`, `stats()`, `by_correlation()`.
   NOT observed (no recursion).

9. **MCP surface** — 4 resources (`pipeline://events/recent`,
   `pipeline://events/recent/{service}`, `pipeline://events/stats`,
   `pipeline://events/correlation/{id}`) + 1 tool
   (`pipeline_events_query`).

10. **Doctor check** — `check_observer` verifies table exists,
    write/read round-trips, reports 24h event count.

## Constitutional grounding

- **Article V.2:** "Every attempt leaves a receipt." The observer makes
  this true at the application layer.
- **Article III.3:** "No telemetry." Events are local-only SQLite.
- **Article XI.5:** The observer records reads as application events,
  not kernel admissions. The distinction is preserved.

## What's on the desk for the next agent

### Immediate

1. **Route + MCP factory wiring.** The services have the `observer`
   constructor parameter but the route `_svc()` factories and MCP
   server don't pass it yet. A hub-level `SQLiteObserver` instance
   needs to be created at startup and threaded through. This is the
   last step before events flow in production.

2. **The two remaining run endpoints.** `chains.py` and `workflows.py`
   are still direct-DB (the Phase 123 handover's item 2). Extract into
   `ChainRunService` and `WorkflowRunService` — then inference calls
   are observed too.

### Future

3. **Retention policy.** The table is append-only with no cleanup.
   A janitor that prunes events older than N days.

4. **Analytics surface.** A desk window that shows the service heatmap,
   recent events, and correlation chains. The EventQueryService is the
   backend; the UI is the remaining work.

5. **Briefing generation.** "Build me a briefing from what actually
   happened" — the HANDOVER vision. Feed the event stream to a model
   and generate a natural-language summary of the desk's day.

6. **Phase 120 web evidence.** Still in the working tree, uncommitted.

7. **Phase 121 — The Fluency.** Chartered, not started.
